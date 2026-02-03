from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from app.models.schemas import DocumentUploadResponse, JobStatus
from app.database import get_db_session, set_tenant_context
from app.repositories.document_repository import DocumentRepository
from app.tasks import process_documents_task
from celery.result import AsyncResult
from uuid import UUID, uuid4
import hashlib
import os
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_tenant_id():
    """Get tenant ID from request context."""
    return "00000000-0000-0000-0000-000000000001"


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    project_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db_session)
):
    """Upload documents for processing.

    Args:
        project_id: Project UUID
        files: List of uploaded files
        db: Database session

    Returns:
        Upload response with job ID
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        job_id = str(uuid4())
        doc_repo = DocumentRepository(db)

        file_paths = []

        for file in files:
            # Read file content
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()

            # Create document record
            document = doc_repo.create_document(
                tenant_id=UUID(tenant_id),
                project_id=UUID(project_id),
                filename=file.filename,
                file_type=Path(file.filename).suffix,
                file_size_bytes=len(content),
                file_hash=file_hash,
                storage_path=""
            )

            # Save file with document ID in filename
            file_path = UPLOAD_DIR / f"{document.document_id}_{file.filename}"
            with open(file_path, "wb") as f:
                f.write(content)

            # Update storage path
            doc_repo.update_document_status(
                document.document_id,
                'pending'
            )

            file_paths.append(str(file_path))

            logger.info(f"Uploaded file {file.filename} as document {document.document_id}")

        # Queue processing task
        process_documents_task.apply_async(
            args=[job_id, tenant_id, project_id, file_paths],
            task_id=job_id
        )

        return DocumentUploadResponse(
            job_id=job_id,
            status="queued",
            message=f"Processing {len(files)} documents"
        )

    except Exception as e:
        logger.error(f"Failed to upload documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing job status.

    Args:
        job_id: Job UUID

    Returns:
        Job status with progress
    """
    try:
        task = AsyncResult(job_id)

        meta = task.info or {}
        if isinstance(meta, dict):
            progress = meta.get("progress", 0.0)
            stage = meta.get("stage", "pending")
            message = meta.get("current_file", "")
        else:
            progress = 0.0
            stage = "pending"
            message = ""

        return JobStatus(
            job_id=job_id,
            status=task.state,
            progress=progress,
            stage=stage,
            message=message
        )

    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}")
async def list_project_documents(
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """List all documents in a project.

    Args:
        project_id: Project UUID
        db: Database session

    Returns:
        List of documents
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        doc_repo = DocumentRepository(db)
        documents = doc_repo.list_documents_by_project(UUID(project_id))

        return {
            "documents": [
                {
                    "document_id": str(doc.document_id),
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "processing_status": doc.processing_status,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at.isoformat()
                }
                for doc in documents
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete a document and all its chunks.

    Args:
        document_id: Document UUID
        db: Database session

    Returns:
        Success message
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        doc_repo = DocumentRepository(db)

        # Get document to find file path
        document = doc_repo.get_document_by_id(UUID(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database
        doc_repo.delete_document(UUID(document_id))

        # Delete file from disk if it exists
        if document.storage_path:
            file_path = Path(document.storage_path)
            if file_path.exists():
                file_path.unlink()
        else:
            # Try to find file by pattern
            pattern = f"{document_id}_*"
            for file_path in UPLOAD_DIR.glob(pattern):
                file_path.unlink()
                logger.info(f"Deleted file {file_path}")

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
