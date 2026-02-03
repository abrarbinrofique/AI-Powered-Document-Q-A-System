from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class AnswerGenerator:
    """Service for generating AI answers using LLM with citations."""

    async def generate_answer(
        self,
        question: str,
        contexts: List[Dict],
        api_key: str,
        model: str = "gpt-4o"
    ) -> Tuple[str, List[Dict]]:
        """Generate answer using LLM with citations.

        Args:
            question: Question text
            contexts: List of retrieved context chunks
            api_key: OpenAI API key (decrypted)
            model: LLM model name

        Returns:
            Tuple of (answer_text, citations)
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            # Build context string with numbered references
            context_text = ""
            for idx, ctx in enumerate(contexts, 1):
                page_info = f"Page {ctx['metadata'].get('page_number', 'N/A')}"
                context_text += f"\n[{idx}] ({page_info})\n{ctx['text']}\n"

            prompt = f"""You are answering a due diligence questionnaire based on company documents.

Question: {question}

Available Context from Documents:
{context_text}

Instructions:
1. Answer the question based ONLY on the provided context
2. If the answer cannot be found in the context, say "Information not found in provided documents"
3. Include citation numbers [1], [2], etc. in your answer where you reference information
4. Be concise and factual
5. Do not make assumptions beyond what's stated in the documents

Answer:"""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a due diligence analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )

            answer_text = response.choices[0].message.content

            # Extract which citations were actually used
            used_citations = []
            for idx, ctx in enumerate(contexts, 1):
                if f"[{idx}]" in answer_text:
                    used_citations.append({
                        "chunk_id": ctx.get("chunk_id"),
                        "document_id": ctx["metadata"].get("document_id"),
                        "page_number": ctx["metadata"].get("page_number"),
                        "excerpt": ctx["text"][:200] + "..." if len(ctx["text"]) > 200 else ctx["text"],
                        "relevance_score": ctx.get("score", 0.0),
                        "citation_order": idx
                    })

            logger.info(f"Generated answer with {len(used_citations)} citations")
            return answer_text, used_citations
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise
