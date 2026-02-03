from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.database import Document, DocumentChunk, Project
from uuid import UUID, uuid4
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentRepository:
    """Repository for managing documents and chunks."""

    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        tenant_id: UUID,
        project_id: UUID,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        file_hash: str,
        storage_path: str
    ) -> Document:
        """Create a new document record.

        Args:
            tenant_id: Tenant UUID
            project_id: Project UUID
            filename: Original filename
            file_type: File extension
            file_size_bytes: File size in bytes
            file_hash: SHA256 hash of file
            storage_path: Path to stored file

        Returns:
            Created Document object
        """
        try:
            document = Document(
                tenant_id=tenant_id,
                project_id=project_id,
                filename=filename,
                file_type=file_type,
                file_size_bytes=file_size_bytes,
                file_hash=file_hash,
                storage_path=storage_path,
                processing_status='pending'
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            logger.info(f"Created document {document.document_id}")
            return document
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create document: {e}")
            raise

    def update_document_status(
        self,
        document_id: UUID,
        status: str,
        chunk_count: Optional[int] = None
    ) -> None:
        """Update document processing status.

        Args:
            document_id: Document UUID
            status: New status (pending, processing, completed, failed)
            chunk_count: Number of chunks (optional)
        """
        try:
            updates = {"processing_status": status}
            if chunk_count is not None:
                updates["chunk_count"] = chunk_count
            if status == "completed":
                updates["processed_at"] = datetime.utcnow()

            self.db.execute(
                update(Document)
                .where(Document.document_id == document_id)
                .values(**updates)
            )
            self.db.commit()
            logger.info(f"Updated document {document_id} status to {status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document status: {e}")
            raise

    def create_chunks(
        self,
        tenant_id: UUID,
        document_id: UUID,
        chunks: List[dict]
    ) -> List[DocumentChunk]:
        """Create document chunks in bulk.

        Args:
            tenant_id: Tenant UUID
            document_id: Document UUID
            chunks: List of chunk dictionaries

        Returns:
            List of created DocumentChunk objects
        """
        try:
            chunk_objects = []
            for chunk in chunks:
                chunk_obj = DocumentChunk(
                    chunk_id=uuid4(),
                    tenant_id=tenant_id,
                    document_id=document_id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["text"],
                    page_number=chunk.get("page_number"),
                    char_offset_start=chunk.get("char_offset_start"),
                    char_offset_end=chunk.get("char_offset_end"),
                    vector_id=str(uuid4()),  # Generate vector ID
                    token_count=chunk.get("token_count"),
                    chunk_metadata={}
                )
                chunk_objects.append(chunk_obj)

            # Use add_all instead of bulk_save_objects to keep objects in session
            self.db.add_all(chunk_objects)
            self.db.commit()

            # Refresh to get IDs and keep them attached
            for obj in chunk_objects:
                self.db.refresh(obj)

            logger.info(f"Created {len(chunk_objects)} chunks for document {document_id}")
            return chunk_objects
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create chunks: {e}")
            raise

    def get_chunk_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk by ID with document details.

        Args:
            chunk_id: Chunk UUID

        Returns:
            DocumentChunk or None
        """
        try:
            result = self.db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.chunk_id == chunk_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get chunk: {e}")
            return None

    def get_document_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document or None
        """
        try:
            result = self.db.execute(
                select(Document)
                .where(Document.document_id == document_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

    def list_documents_by_project(self, project_id: UUID) -> List[Document]:
        """List all documents in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of Documents
        """
        try:
            result = self.db.execute(
                select(Document)
                .where(Document.project_id == project_id)
                .order_by(Document.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and all its chunks.

        Args:
            document_id: Document UUID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Delete document (chunks will be cascade deleted)
            result = self.db.execute(
                select(Document)
                .where(Document.document_id == document_id)
            )
            document = result.scalar_one_or_none()

            if document:
                self.db.delete(document)
                self.db.commit()
                logger.info(f"Deleted document {document_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete document: {e}")
            raise
