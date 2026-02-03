from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.database import Answer, AnswerCitation, AnswerVersion, Question, DocumentChunk, Document
from uuid import UUID, uuid4
import logging
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class AnswerRepository:
    """Repository for managing answers and citations."""

    def __init__(self, db: Session):
        self.db = db

    def create_answer(
        self,
        tenant_id: UUID,
        question_id: UUID,
        answer_text: str,
        is_ai_generated: bool,
        confidence_score: float,
        retrieval_score: float,
        faithfulness_score: float
    ) -> Answer:
        """Create a new answer record.

        Args:
            tenant_id: Tenant UUID
            question_id: Question UUID
            answer_text: Answer text
            is_ai_generated: Whether answer is AI-generated
            confidence_score: Overall confidence score
            retrieval_score: Retrieval confidence
            faithfulness_score: Faithfulness score

        Returns:
            Created Answer object
        """
        try:
            answer = Answer(
                tenant_id=tenant_id,
                question_id=question_id,
                answer_text=answer_text,
                is_ai_generated=is_ai_generated,
                confidence_score=confidence_score,
                retrieval_score=retrieval_score,
                faithfulness_score=faithfulness_score,
                status='pending_review',
                version=1
            )
            self.db.add(answer)
            self.db.commit()
            self.db.refresh(answer)
            logger.info(f"Created answer {answer.answer_id}")
            return answer
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create answer: {e}")
            raise

    def create_citations(
        self,
        tenant_id: UUID,
        answer_id: UUID,
        citations: List[Dict]
    ) -> List[AnswerCitation]:
        """Create answer citations in bulk.

        Args:
            tenant_id: Tenant UUID
            answer_id: Answer UUID
            citations: List of citation dictionaries

        Returns:
            List of created AnswerCitation objects
        """
        try:
            citation_objects = []
            for citation in citations:
                citation_obj = AnswerCitation(
                    tenant_id=tenant_id,
                    answer_id=answer_id,
                    chunk_id=UUID(citation["chunk_id"]),
                    relevance_score=citation.get("relevance_score", 0.0),
                    citation_order=citation.get("citation_order", 1),
                    excerpt=citation.get("excerpt", "")
                )
                citation_objects.append(citation_obj)

            self.db.bulk_save_objects(citation_objects)
            self.db.commit()

            logger.info(f"Created {len(citation_objects)} citations for answer {answer_id}")
            return citation_objects
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create citations: {e}")
            raise

    def get_answer_with_citations(self, answer_id: UUID) -> Optional[Dict]:
        """Get answer with all citations and metadata.

        Args:
            answer_id: Answer UUID

        Returns:
            Dictionary with answer and citation details
        """
        try:
            # Get answer
            answer_result = self.db.execute(
                select(Answer)
                .where(Answer.answer_id == answer_id)
            )
            answer = answer_result.scalar_one_or_none()

            if not answer:
                return None

            # Get citations with chunk and document details
            citations_result = self.db.execute(
                select(AnswerCitation, DocumentChunk, Document)
                .join(DocumentChunk, AnswerCitation.chunk_id == DocumentChunk.chunk_id)
                .join(Document, DocumentChunk.document_id == Document.document_id)
                .where(AnswerCitation.answer_id == answer_id)
                .order_by(AnswerCitation.citation_order)
            )

            citations = []
            for citation, chunk, document in citations_result:
                citations.append({
                    "citation_id": citation.citation_id,
                    "document_id": document.document_id,
                    "document_name": document.filename,
                    "page_number": chunk.page_number,
                    "excerpt": citation.excerpt,
                    "relevance_score": float(citation.relevance_score) if citation.relevance_score else 0.0
                })

            return {
                "answer_id": answer.answer_id,
                "tenant_id": answer.tenant_id,
                "question_id": answer.question_id,
                "answer_text": answer.answer_text,
                "is_ai_generated": answer.is_ai_generated,
                "confidence_score": float(answer.confidence_score) if answer.confidence_score else 0.0,
                "retrieval_score": float(answer.retrieval_score) if answer.retrieval_score else 0.0,
                "faithfulness_score": float(answer.faithfulness_score) if answer.faithfulness_score else 0.0,
                "status": answer.status,
                "version": answer.version,
                "citations": citations,
                "created_at": answer.created_at,
                "updated_at": answer.updated_at
            }
        except Exception as e:
            logger.error(f"Failed to get answer with citations: {e}")
            return None

    def get_answer_by_question(self, question_id: UUID) -> Optional[Dict]:
        """Get answer for a specific question with all citations.

        Args:
            question_id: Question UUID

        Returns:
            Dictionary with answer and citation details
        """
        try:
            # Get answer for this question
            answer_result = self.db.execute(
                select(Answer)
                .where(Answer.question_id == question_id)
                .order_by(Answer.created_at.desc())
            )
            answer = answer_result.scalar_one_or_none()

            if not answer:
                return None

            # Use existing method to get full answer with citations
            return self.get_answer_with_citations(answer.answer_id)
        except Exception as e:
            logger.error(f"Failed to get answer by question: {e}")
            return None

    def update_answer_status(
        self,
        answer_id: UUID,
        status: str,
        reviewed_by: Optional[UUID] = None,
        review_notes: Optional[str] = None
    ) -> None:
        """Update answer status after review.

        Args:
            answer_id: Answer UUID
            status: New status
            reviewed_by: Reviewer UUID
            review_notes: Review notes
        """
        try:
            updates = {
                "status": status,
                "reviewed_at": datetime.utcnow()
            }
            if reviewed_by:
                updates["reviewed_by"] = reviewed_by
            if review_notes:
                updates["review_notes"] = review_notes

            self.db.execute(
                update(Answer)
                .where(Answer.answer_id == answer_id)
                .values(**updates)
            )
            self.db.commit()
            logger.info(f"Updated answer {answer_id} status to {status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update answer status: {e}")
            raise

    def create_answer_version(
        self,
        answer_id: UUID,
        version_number: int,
        content_snapshot: str,
        change_type: str,
        changed_by: Optional[UUID] = None,
        change_reason: Optional[str] = None
    ) -> AnswerVersion:
        """Create answer version for audit trail.

        Args:
            answer_id: Answer UUID
            version_number: Version number
            content_snapshot: Snapshot of content
            change_type: Type of change (edit, approve, etc.)
            changed_by: User UUID who made change
            change_reason: Reason for change

        Returns:
            Created AnswerVersion object
        """
        try:
            version = AnswerVersion(
                answer_id=answer_id,
                version_number=version_number,
                content_snapshot=content_snapshot,
                change_type=change_type,
                changed_by=changed_by,
                change_reason=change_reason
            )
            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)
            logger.info(f"Created version {version_number} for answer {answer_id}")
            return version
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create answer version: {e}")
            raise

    def update_answer_text(
        self,
        answer_id: UUID,
        new_text: str,
        changed_by: Optional[UUID] = None
    ) -> None:
        """Update answer text and create version.

        Args:
            answer_id: Answer UUID
            new_text: New answer text
            changed_by: User UUID who made change
        """
        try:
            # Get current answer
            answer_result = self.db.execute(
                select(Answer).where(Answer.answer_id == answer_id)
            )
            answer = answer_result.scalar_one_or_none()

            if not answer:
                raise ValueError(f"Answer {answer_id} not found")

            # Create version snapshot
            self.create_answer_version(
                answer_id=answer_id,
                version_number=answer.version,
                content_snapshot=answer.answer_text or "",
                change_type="edit",
                changed_by=changed_by,
                change_reason="Manual edit"
            )

            # Update answer
            self.db.execute(
                update(Answer)
                .where(Answer.answer_id == answer_id)
                .values(
                    answer_text=new_text,
                    version=answer.version + 1,
                    status="edited"
                )
            )
            self.db.commit()
            logger.info(f"Updated answer {answer_id} text")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update answer text: {e}")
            raise

    def delete_answers_by_question(self, question_id: UUID) -> int:
        """Delete all answers associated with a question.

        Args:
            question_id: Question UUID

        Returns:
            Number of answers deleted
        """
        try:
            # Get all answers for this question
            result = self.db.execute(
                select(Answer).where(Answer.question_id == question_id)
            )
            answers = result.scalars().all()

            count = len(answers)

            # Delete citations, versions, and answers
            for answer in answers:
                # Delete citations
                self.db.execute(
                    select(AnswerCitation).where(AnswerCitation.answer_id == answer.answer_id)
                ).scalars().all()
                self.db.query(AnswerCitation).filter(AnswerCitation.answer_id == answer.answer_id).delete()

                # Delete versions
                self.db.query(AnswerVersion).filter(AnswerVersion.answer_id == answer.answer_id).delete()

                # Delete answer
                self.db.delete(answer)

            self.db.commit()
            logger.info(f"Deleted {count} answer(s) for question {question_id}")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete answers: {e}")
            raise
