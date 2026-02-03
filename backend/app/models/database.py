from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, ForeignKey, DECIMAL, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid as uuid_pkg

Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    status = Column(String(64), default='active')
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApiKeyConfig(Base):
    __tablename__ = "api_key_configs"

    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    provider = Column(String(50), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(64), default='draft')
    due_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='SET NULL'))
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size_bytes = Column(BigInteger)
    file_hash = Column(String(64))
    storage_path = Column(String(1000))
    processing_status = Column(String(64), default='pending')
    chunk_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.document_id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    section_title = Column(String(500))
    char_offset_start = Column(Integer)
    char_offset_end = Column(Integer)
    vector_id = Column(String(255))
    token_count = Column(Integer)
    chunk_metadata = Column('metadata', JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Question(Base):
    __tablename__ = "questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False)
    question_text = Column(Text, nullable=False)
    question_category = Column(String(255))
    question_number = Column(String(50))
    ground_truth_answer = Column(Text)
    response_type = Column(String(64), default='text')
    status = Column(String(64), default='pending')
    display_order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Answer(Base):
    __tablename__ = "answers"

    answer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    answer_text = Column(Text)
    is_ai_generated = Column(Boolean, default=False)
    confidence_score = Column(DECIMAL(3, 2))
    retrieval_score = Column(DECIMAL(3, 2))
    faithfulness_score = Column(DECIMAL(3, 2))
    status = Column(String(64), default='draft')
    version = Column(Integer, default=1)
    created_by = Column(UUID(as_uuid=True))
    reviewed_by = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AnswerCitation(Base):
    __tablename__ = "answer_citations"

    citation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    answer_id = Column(UUID(as_uuid=True), ForeignKey('answers.answer_id', ondelete='CASCADE'), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey('document_chunks.chunk_id', ondelete='CASCADE'), nullable=False)
    relevance_score = Column(DECIMAL(5, 4))
    citation_order = Column(Integer)
    excerpt = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AnswerVersion(Base):
    __tablename__ = "answer_versions"

    version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    answer_id = Column(UUID(as_uuid=True), ForeignKey('answers.answer_id', ondelete='CASCADE'), nullable=False)
    version_number = Column(Integer, nullable=False)
    content_snapshot = Column(Text, nullable=False)
    diff_from_previous = Column(Text)
    change_type = Column(String(50))
    changed_by = Column(UUID(as_uuid=True))
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
