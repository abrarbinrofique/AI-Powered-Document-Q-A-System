from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.database import Question
from uuid import UUID
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class QuestionRepository:
    """Repository for managing questions."""

    def __init__(self, db: Session):
        self.db = db

    def create_question(self, question_data: dict) -> Question:
        """Create a new question.

        Args:
            question_data: Dictionary with question fields including:
                - tenant_id (UUID)
                - project_id (UUID)
                - question_text (str)
                - question_category (str, optional)
                - question_number (str, optional)
                - ground_truth_answer (str, optional)
                - display_order (int, optional)
                - status (str, optional)

        Returns:
            Created Question object
        """
        try:
            question = Question(**question_data)
            self.db.add(question)
            self.db.commit()
            self.db.refresh(question)
            logger.info(f"Created question {question.question_id}")
            return question
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create question: {e}")
            raise

    def get_question_by_id(self, question_id: UUID) -> Optional[Question]:
        """Get question by ID.

        Args:
            question_id: Question UUID

        Returns:
            Question or None
        """
        try:
            result = self.db.execute(
                select(Question).where(Question.question_id == question_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get question: {e}")
            return None

    def get_question(self, question_id: UUID) -> Optional[Question]:
        """Get question by ID (alias for get_question_by_id).

        Args:
            question_id: Question UUID

        Returns:
            Question or None
        """
        return self.get_question_by_id(question_id)

    def list_questions_by_project(self, project_id: UUID) -> List[Question]:
        """List all questions in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of Questions
        """
        try:
            result = self.db.execute(
                select(Question)
                .where(Question.project_id == project_id)
                .order_by(Question.display_order, Question.created_at)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list questions: {e}")
            return []

    def update_question_status(self, question_id: UUID, status: str) -> None:
        """Update question status.

        Args:
            question_id: Question UUID
            status: New status
        """
        try:
            self.db.execute(
                update(Question)
                .where(Question.question_id == question_id)
                .values(status=status)
            )
            self.db.commit()
            logger.info(f"Updated question {question_id} status to {status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update question status: {e}")
            raise

    def delete_question(self, question_id: UUID) -> bool:
        """Delete a question by ID.

        Args:
            question_id: Question UUID

        Returns:
            True if deleted, False otherwise
        """
        try:
            question = self.get_question_by_id(question_id)
            if not question:
                logger.warning(f"Question {question_id} not found")
                return False

            self.db.delete(question)
            self.db.commit()
            logger.info(f"Deleted question {question_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete question: {e}")
            raise
