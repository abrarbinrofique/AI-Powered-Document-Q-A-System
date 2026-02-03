from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ProjectCreate, ProjectResponse
from app.database import get_db_session, set_tenant_context
from app.repositories.project_repository import ProjectRepository
from uuid import UUID
import logging
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def get_tenant_id():
    """Get tenant ID from request context."""
    return "00000000-0000-0000-0000-000000000001"


@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new project.

    Args:
        project: Project creation data
        db: Database session

    Returns:
        Created project
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        project_repo = ProjectRepository(db)
        created_project = project_repo.create_project(
            tenant_id=UUID(tenant_id),
            name=project.name,
            description=project.description,
            due_date=project.due_date
        )

        logger.info(f"Created project {created_project.project_id}")

        return ProjectResponse(
            project_id=created_project.project_id,
            tenant_id=created_project.tenant_id,
            name=created_project.name,
            description=created_project.description,
            status=created_project.status,
            due_date=created_project.due_date,
            created_at=created_project.created_at
        )

    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db_session)):
    """List all projects for the tenant.

    Args:
        db: Database session

    Returns:
        List of projects
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        project_repo = ProjectRepository(db)
        projects = project_repo.list_projects_by_tenant(UUID(tenant_id))

        return [
            ProjectResponse(
                project_id=p.project_id,
                tenant_id=p.tenant_id,
                name=p.name,
                description=p.description,
                status=p.status,
                due_date=p.due_date,
                created_at=p.created_at
            )
            for p in projects
        ]

    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """Get project by ID.

    Args:
        project_id: Project UUID
        db: Database session

    Returns:
        Project details
    """
    try:
        tenant_id = get_tenant_id()
        set_tenant_context(db, tenant_id)

        project_repo = ProjectRepository(db)
        project = project_repo.get_project_by_id(UUID(project_id))

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectResponse(
            project_id=project.project_id,
            tenant_id=project.tenant_id,
            name=project.name,
            description=project.description,
            status=project.status,
            due_date=project.due_date,
            created_at=project.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
