from celery import shared_task
from app.celery_app import celery_app
from app.database import SessionLocal, set_tenant_context
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.answer_generator import AnswerGenerator
from app.services.confidence_scorer import ConfidenceScorer
from app.services.crypto_service import CryptoService
from app.repositories.document_repository import DocumentRepository
from app.repositories.answer_repository import AnswerRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.settings_repository import SettingsRepository
from uuid import UUID
import logging
import os

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_documents_task(self, job_id: str, tenant_id: str, project_id: str, file_paths: list):
    """Process uploaded documents: parse, chunk, embed, and store in vector DB.

    Args:
        job_id: Unique job ID
        tenant_id: Tenant UUID
        project_id: Project UUID
        file_paths: List of file paths to process
    """
    db = SessionLocal()
    try:
        set_tenant_context(db, tenant_id)

        # Initialize services
        processor = DocumentProcessor()
        vector_store = VectorStoreService()
        doc_repo = DocumentRepository(db)
        settings_repo = SettingsRepository(db)
        crypto = CryptoService()

        # Get tenant's API key
        api_key_config = settings_repo.get_api_key_config(tenant_id, "openai")
        if not api_key_config:
            raise ValueError("OpenAI API key not configured")

        api_key = crypto.decrypt(api_key_config.encrypted_key)

        total = len(file_paths)

        for idx, file_path in enumerate(file_paths):
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": idx / total,
                    "stage": "processing",
                    "current_file": os.path.basename(file_path)
                }
            )

            # Get document record
            document_id = UUID(os.path.basename(file_path).split('_')[0])
            document = doc_repo.get_document_by_id(document_id)

            if not document:
                logger.error(f"Document {document_id} not found")
                continue

            # Update status to processing
            doc_repo.update_document_status(document_id, 'processing')

            try:
                # Parse document
                chunks = processor.parse_document(file_path)

                if not chunks:
                    logger.warning(f"No chunks extracted from {file_path}")
                    doc_repo.update_document_status(document_id, 'failed')
                    continue

                # Create chunk records
                chunk_objects = doc_repo.create_chunks(
                    tenant_id=UUID(tenant_id),
                    document_id=document_id,
                    chunks=chunks
                )

                # Generate embeddings in batches (sync version for Celery)
                texts = [chunk["text"] for chunk in chunks]
                from openai import OpenAI
                client = OpenAI(api_key=api_key)

                # Batch embeddings to avoid token limit (max ~2000 chunks per batch)
                batch_size = 2000
                embeddings = []

                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch_texts)} chunks)")

                    response = client.embeddings.create(
                        model="text-embedding-3-small",
                        input=batch_texts
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)

                logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")

                # Prepare chunks with metadata for vector store
                chunks_with_meta = []
                for chunk_obj, chunk_data in zip(chunk_objects, chunks):
                    chunks_with_meta.append({
                        "chunk_id": str(chunk_obj.chunk_id),
                        "document_id": str(document_id),
                        "vector_id": chunk_obj.vector_id,
                        "text": chunk_data["text"],
                        "page_number": chunk_obj.page_number or 0,
                        "chunk_index": chunk_obj.chunk_index
                    })

                # Store in vector database
                vector_store.add_documents(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    chunks=chunks_with_meta,
                    embeddings=embeddings
                )

                # Update document status
                doc_repo.update_document_status(document_id, 'completed', len(chunks))

                logger.info(f"Processed document {document_id}: {len(chunks)} chunks")

            except Exception as e:
                logger.error(f"Failed to process document {document_id}: {e}")
                doc_repo.update_document_status(document_id, 'failed')

        return {"status": "completed", "documents": total}

    except Exception as e:
        logger.error(f"Document processing task failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def generate_answer_task(self, query_id: str, tenant_id: str, project_id: str, question_text: str):
    """Generate AI answer for a question using RAG pipeline.

    Args:
        query_id: Unique query ID
        tenant_id: Tenant UUID
        project_id: Project UUID
        question_text: Question text
    """
    db = SessionLocal()
    try:
        set_tenant_context(db, tenant_id)

        # Initialize services
        vector_store = VectorStoreService()
        generator = AnswerGenerator()
        scorer = ConfidenceScorer()
        processor = DocumentProcessor()
        settings_repo = SettingsRepository(db)
        question_repo = QuestionRepository(db)
        answer_repo = AnswerRepository(db)
        crypto = CryptoService()

        # Get tenant's API key
        api_key_config = settings_repo.get_api_key_config(tenant_id, "openai")
        if not api_key_config:
            raise ValueError("OpenAI API key not configured")

        api_key = crypto.decrypt(api_key_config.encrypted_key)

        # Create question record
        question = question_repo.create_question({
            'tenant_id': UUID(tenant_id),
            'project_id': UUID(project_id),
            'question_text': question_text,
            'status': 'pending'
        })

        # Update question status
        question_repo.update_question_status(question.question_id, 'processing')

        # Generate query embedding (sync version for Celery)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[question_text]
        )
        query_embedding = response.data[0].embedding

        # Retrieve relevant chunks
        retrieval_results = vector_store.query(
            tenant_id=tenant_id,
            project_id=project_id,
            query_embedding=query_embedding,
            top_k=5
        )

        if not retrieval_results:
            logger.warning(f"No relevant chunks found for question: {question_text}")
            retrieval_results = []

        # Generate answer (using sync API calls in Celery)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Build context for LLM
        context_text = ""
        for idx, ctx in enumerate(retrieval_results, 1):
            page_info = f"Page {ctx.get('metadata', {}).get('page_number', 'N/A')}"
            context_text += f"\n[{idx}] ({page_info})\n{ctx['text']}\n"

        prompt = f"""You are answering a due diligence questionnaire based on company documents.

Question: {question_text}

Available Context from Documents:
{context_text}

Instructions:
1. Answer the question based ONLY on the provided context
2. If the answer cannot be found in the context, say "Information not found in provided documents"
3. Include citation numbers [1], [2], etc. in your answer where you reference information
4. Be concise and factual
5. Do not make assumptions beyond what's stated in the documents

Answer:"""

        llm_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a due diligence analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        answer_text = llm_response.choices[0].message.content

        # Extract citations
        citations = []
        for idx, ctx in enumerate(retrieval_results, 1):
            if f"[{idx}]" in answer_text:
                citations.append({
                    "chunk_id": ctx.get("chunk_id"),
                    "document_id": ctx.get("metadata", {}).get("document_id"),
                    "page_number": ctx.get("metadata", {}).get("page_number"),
                    "excerpt": ctx["text"][:200] + "..." if len(ctx["text"]) > 200 else ctx["text"],
                    "relevance_score": ctx.get("score", 0.0),
                    "citation_order": idx
                })

        # Calculate simple confidence score
        scores = [r.get("score", 0.0) for r in retrieval_results]
        import numpy as np
        retrieval_conf = float(np.mean(scores)) if scores else 0.5

        confidence = {
            "overall": retrieval_conf,
            "retrieval": retrieval_conf,
            "faithfulness": 0.8,  # Simplified
            "relevancy": 0.8  # Simplified
        }

        # Save answer to database
        answer = answer_repo.create_answer(
            tenant_id=UUID(tenant_id),
            question_id=question.question_id,
            answer_text=answer_text,
            is_ai_generated=True,
            confidence_score=confidence["overall"],
            retrieval_score=confidence["retrieval"],
            faithfulness_score=confidence["faithfulness"]
        )

        # Save citations
        if citations:
            answer_repo.create_citations(
                tenant_id=UUID(tenant_id),
                answer_id=answer.answer_id,
                citations=citations
            )

        # Update question status
        question_repo.update_question_status(question.question_id, 'review')

        logger.info(f"Generated answer {answer.answer_id} for question {question.question_id}")

        return {
            "answer_id": str(answer.answer_id),
            "question_id": str(question.question_id),
            "confidence_score": confidence["overall"]
        }

    except Exception as e:
        logger.error(f"Answer generation task failed: {e}")
        raise
    finally:
        db.close()
