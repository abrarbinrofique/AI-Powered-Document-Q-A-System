from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AnswerStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"

class QuestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"

# API Key Management
class ApiKeyRequest(BaseModel):
    provider: str = Field(..., description="openai, anthropic, cohere")
    api_key: str = Field(..., description="The API key to validate and store")

class ApiKeyStatus(BaseModel):
    configured: bool
    provider: Optional[str] = None
    masked_key: Optional[str] = None

# Document Models
class DocumentUploadResponse(BaseModel):
    job_id: str
    status: str
    message: str

class DocumentResponse(BaseModel):
    document_id: UUID
    tenant_id: UUID
    project_id: Optional[UUID] = None
    filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    processing_status: ProcessingStatus
    chunk_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

# Question Models
class QuestionCreate(BaseModel):
    project_id: UUID
    question_text: str
    question_category: Optional[str] = None
    question_number: Optional[str] = None
    ground_truth_answer: Optional[str] = None
    display_order: Optional[int] = None

class QuestionBulkUpload(BaseModel):
    project_id: UUID

class QuestionResponse(BaseModel):
    question_id: UUID
    tenant_id: UUID
    project_id: UUID
    question_text: str
    question_category: Optional[str] = None
    question_number: Optional[str] = None
    ground_truth_answer: Optional[str] = None
    status: QuestionStatus
    display_order: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Answer Models
class AnswerGenerateRequest(BaseModel):
    question_text: str
    project_id: UUID

class CitationResponse(BaseModel):
    citation_id: UUID
    document_id: UUID
    document_name: str
    page_number: Optional[int]
    excerpt: str
    relevance_score: float

class AnswerResponse(BaseModel):
    answer_id: UUID
    tenant_id: UUID
    question_id: UUID
    answer_text: Optional[str] = None
    is_ai_generated: bool = False
    confidence_score: Optional[float] = None
    retrieval_score: Optional[float] = None
    faithfulness_score: Optional[float] = None
    status: AnswerStatus
    version: int = 1
    citations: List[CitationResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Review Models
class ReviewRequest(BaseModel):
    action: str = Field(..., description="approve, reject, edit")
    edited_text: Optional[str] = None
    review_notes: Optional[str] = None

class ReviewResponse(BaseModel):
    status: str
    message: str

# Project Models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class ProjectResponse(BaseModel):
    project_id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Job Status
class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    message: Optional[str] = None
    stage: Optional[str] = None

# Evaluation Models
class EvaluationMetrics(BaseModel):
    bleu_score: Optional[float] = None
    rouge_1_f1: Optional[float] = None
    rouge_2_f1: Optional[float] = None
    rouge_l_f1: Optional[float] = None
    semantic_similarity: Optional[float] = None
    overall_score: Optional[float] = None

class EvaluationResponse(BaseModel):
    answer_id: UUID
    has_ground_truth: bool
    metrics: Optional[EvaluationMetrics] = None
    message: Optional[str] = None
