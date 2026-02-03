from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.database import Project
from uuid import UUID
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectRepository:
    """Repository for managing projects."""

    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self,
        tenant_id: UUID,
        name: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> Project:
        """Create a new project.

        Args:
            tenant_id: Tenant UUID
            name: Project name
            description: Project description (optional)
            due_date: Due date (optional)

        Returns:
            Created Project object
        """
        try:
            project = Project(
                tenant_id=tenant_id,
                name=name,
                description=description,
                due_date=due_date,
                status='draft'
            )
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"Created project {project.project_id}")
            return project
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create project: {e}")
            raise

    def get_project_by_id(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project or None
        """
        try:
            result = self.db.execute(
                select(Project).where(Project.project_id == project_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None

    def list_projects_by_tenant(self, tenant_id: UUID) -> List[Project]:
        """List all projects for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of Projects
        """
        try:
            result = self.db.execute(
                select(Project)
                .where(Project.tenant_id == tenant_id)
                .order_by(Project.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
