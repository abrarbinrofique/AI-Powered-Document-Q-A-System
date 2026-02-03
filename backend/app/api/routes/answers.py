from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.models.schemas import (
    AnswerGenerateRequest, AnswerResponse, ReviewRequest, ReviewResponse,
    QuestionBulkUpload, EvaluationResponse
)
from app.database import get_db_session, set_tenant_context
from app.repositories.answer_repository import AnswerRepository
from app.tasks import generate_answer_task
from uuid import UUID
import logging
import pandas as pd
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["answers"])


def get_tenant_id():
    """Get tenant ID from request context."""
    return "00000000-0000-0000-0000-000000000001"


@router.post("/questions/generate")
async def generate_answer(
    request: AnswerGenerateRequest,
    db: Session = Depends(get_db_session)
):
    """Generate AI answer for a question.

    Args:
        request: Question generation request
        db: Database session

    Returns:
        Query ID for tracking
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        query_id = str(UUID(int=0))  # Generate a query ID

        # Queue answer generation task
        task = generate_answer_task.apply_async(
            args=[
                query_id,
                tenant_id,
                str(request.project_id),
                request.question_text
            ]
        )

        return {
            "query_id": task.id,
            "status": "queued",
            "message": "Answer generation in progress"
        }

    except Exception as e:
        logger.error(f"Failed to queue answer generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queries/{query_id}")
async def get_query_result(
    query_id: str,
    db: Session = Depends(get_db_session)
):
    """Get answer result by query ID (task ID).

    Args:
        query_id: Query/Task UUID
        db: Database session

    Returns:
        Answer with citations or task status
    """
    try:
        from celery.result import AsyncResult

        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        # Check task status
        task = AsyncResult(query_id)

        if task.state == 'PENDING':
            return {"status": "pending", "message": "Answer generation in progress"}
        elif task.state == 'PROGRESS':
            return {"status": "processing", "message": "Generating answer..."}
        elif task.state == 'FAILURE':
            return {"status": "failed", "message": str(task.info)}
        elif task.state == 'SUCCESS':
            # Get the answer_id from task result
            result = task.result
            answer_id = result.get('answer_id')

            if not answer_id:
                raise HTTPException(status_code=404, detail="Answer ID not found in task result")

            # Fetch the actual answer
            answer_repo = AnswerRepository(db)
            answer_data = answer_repo.get_answer_with_citations(UUID(answer_id))

            if not answer_data:
                raise HTTPException(status_code=404, detail="Answer not found")

            return answer_data
        else:
            return {"status": task.state.lower(), "message": "Unknown task state"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/{question_id}/answer")
async def get_answer_by_question(
    question_id: str,
    db: Session = Depends(get_db_session)
):
    """Get answer for a specific question.

    Args:
        question_id: Question UUID
        db: Database session

    Returns:
        Answer with citations
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        answer_repo = AnswerRepository(db)
        answer_data = answer_repo.get_answer_by_question(UUID(question_id))

        if not answer_data:
            raise HTTPException(status_code=404, detail="Answer not found for this question")

        return answer_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get answer by question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/answers/{answer_id}", response_model=AnswerResponse)
async def get_answer(
    answer_id: str,
    db: Session = Depends(get_db_session)
):
    """Get answer with citations.

    Args:
        answer_id: Answer UUID
        db: Database session

    Returns:
        Answer with citations
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        answer_repo = AnswerRepository(db)
        answer_data = answer_repo.get_answer_with_citations(UUID(answer_id))

        if not answer_data:
            raise HTTPException(status_code=404, detail="Answer not found")

        return answer_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answers/{answer_id}/review", response_model=ReviewResponse)
async def submit_review(
    answer_id: str,
    review: ReviewRequest,
    db: Session = Depends(get_db_session)
):
    """Submit review for an answer.

    Args:
        answer_id: Answer UUID
        review: Review action and details
        db: Database session

    Returns:
        Review response
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        answer_repo = AnswerRepository(db)

        if review.action == "approve":
            answer_repo.update_answer_status(
                UUID(answer_id),
                "approved",
                review_notes=review.review_notes
            )
            message = "Answer approved"

        elif review.action == "reject":
            answer_repo.update_answer_status(
                UUID(answer_id),
                "rejected",
                review_notes=review.review_notes
            )
            message = "Answer rejected"

        elif review.action == "edit":
            if not review.edited_text:
                raise HTTPException(
                    status_code=400,
                    detail="edited_text required for edit action"
                )

            answer_repo.update_answer_text(
                UUID(answer_id),
                review.edited_text
            )
            answer_repo.update_answer_status(
                UUID(answer_id),
                "edited",
                review_notes=review.review_notes
            )
            message = "Answer edited"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {review.action}"
            )

        logger.info(f"Review submitted for answer {answer_id}: {review.action}")

        return ReviewResponse(
            status="success",
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/project/{project_id}")
async def list_project_questions(
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """List all questions in a project.

    Args:
        project_id: Project UUID
        db: Database session

    Returns:
        List of questions
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        from app.repositories.question_repository import QuestionRepository
        question_repo = QuestionRepository(db)
        questions = question_repo.list_questions_by_project(UUID(project_id))

        return {
            "questions": [
                {
                    "question_id": str(q.question_id),
                    "question_text": q.question_text,
                    "question_category": q.question_category,
                    "status": q.status,
                    "created_at": q.created_at.isoformat()
                }
                for q in questions
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/questions/bulk-upload")
async def bulk_upload_questions(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session)
):
    """Bulk upload questions from CSV or Excel file.

    Expected columns:
    - question_number (optional)
    - question_text (required)
    - question_category (optional)
    - ground_truth_answer (optional)

    Args:
        project_id: Project UUID
        file: CSV or Excel file
        db: Database session

    Returns:
        Upload summary with created questions count
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        # Read file content
        contents = await file.read()

        # Parse based on file extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload CSV or Excel file."
            )

        # Validate required column
        if 'question_text' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Missing required column: question_text"
            )

        # Import repository
        from app.repositories.question_repository import QuestionRepository
        question_repo = QuestionRepository(db)

        created_questions = []
        errors = []

        for idx, row in df.iterrows():
            try:
                question_text = str(row['question_text']).strip()
                if not question_text or question_text == 'nan':
                    errors.append(f"Row {idx + 2}: Empty question text")
                    continue

                question_data = {
                    'project_id': UUID(project_id),
                    'tenant_id': UUID(tenant_id),
                    'question_text': question_text,
                    'question_number': str(row.get('question_number', '')).strip() if 'question_number' in row else None,
                    'question_category': str(row.get('question_category', '')).strip() if 'question_category' in row else None,
                    'ground_truth_answer': str(row.get('ground_truth_answer', '')).strip() if 'ground_truth_answer' in row else None,
                    'display_order': idx + 1,
                    'status': 'pending'
                }

                # Clean None values from empty strings
                for key in ['question_number', 'question_category', 'ground_truth_answer']:
                    if question_data.get(key) in ['', 'nan', 'None']:
                        question_data[key] = None

                question = question_repo.create_question(question_data)
                created_questions.append(str(question.question_id))

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                logger.error(f"Error processing row {idx}: {e}")

        logger.info(f"Bulk upload completed: {len(created_questions)} questions created, {len(errors)} errors")

        return {
            "status": "success",
            "created_count": len(created_questions),
            "error_count": len(errors),
            "question_ids": created_questions,
            "errors": errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk upload questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answers/{answer_id}/evaluate", response_model=EvaluationResponse)
async def evaluate_answer(
    answer_id: str,
    db: Session = Depends(get_db_session)
):
    """Evaluate answer against ground truth.

    Calculates metrics:
    - BLEU score
    - ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L)
    - Semantic similarity (cosine similarity of embeddings)
    - Overall score (weighted average)

    Args:
        answer_id: Answer UUID
        db: Database session

    Returns:
        Evaluation metrics
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        # Get answer and question
        answer_repo = AnswerRepository(db)
        answer_data = answer_repo.get_answer_with_citations(UUID(answer_id))

        if not answer_data:
            raise HTTPException(status_code=404, detail="Answer not found")

        # Get question with ground truth
        from app.repositories.question_repository import QuestionRepository
        question_repo = QuestionRepository(db)
        question = question_repo.get_question(answer_data['question_id'])

        if not question or not question.ground_truth_answer:
            return EvaluationResponse(
                answer_id=UUID(answer_id),
                has_ground_truth=False,
                message="No ground truth answer available for evaluation"
            )

        # Import evaluation service
        from app.services.evaluation_service import EvaluationService
        eval_service = EvaluationService()

        # Calculate metrics
        metrics = eval_service.evaluate(
            generated_answer=answer_data['answer_text'],
            ground_truth=question.ground_truth_answer
        )

        logger.info(f"Evaluation completed for answer {answer_id}")

        return EvaluationResponse(
            answer_id=UUID(answer_id),
            has_ground_truth=True,
            metrics=metrics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evaluate answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete a question and all associated answers.

    Args:
        question_id: Question UUID
        db: Database session

    Returns:
        Success message
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        from app.repositories.question_repository import QuestionRepository
        question_repo = QuestionRepository(db)

        # First, delete any associated answers (and their citations/versions)
        answer_repo = AnswerRepository(db)
        answer_repo.delete_answers_by_question(UUID(question_id))

        # Then delete the question
        success = question_repo.delete_question(UUID(question_id))

        if not success:
            raise HTTPException(status_code=404, detail="Question not found")

        logger.info(f"Deleted question {question_id} and associated answers")

        return {"status": "success", "message": "Question deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
