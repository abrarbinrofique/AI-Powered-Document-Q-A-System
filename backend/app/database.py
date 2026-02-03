from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ddquser:password@localhost:5432/ddqdb")

# Create engine with NullPool for proper connection management
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Database session context manager with tenant isolation."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def set_tenant_context(db: Session, tenant_id: str):
    """Set tenant context for row-level security."""
    db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

def reset_tenant_context(db: Session):
    """Reset tenant context."""
    db.execute(text("RESET app.current_tenant_id"))

def get_db_session():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
