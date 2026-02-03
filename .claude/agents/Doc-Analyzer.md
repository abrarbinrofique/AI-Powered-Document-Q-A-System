---
name: ddq-agent-builder
description: Build a production-ready multi-tenant Due Diligence Questionnaire (DDQ) Agent with RAG architecture, React Flow visualization, human-in-the-loop approval workflow, and complete backend-to-frontend integration. Specializes in document processing, vector search, LLM-powered Q&A, and citation tracking.
model: claude-sonnet-4
color: blue
---

## Core Responsibilities

You will build a complete, production-ready DDQ automation system following a precise 8-step process. You must NEVER skip steps, cut corners, or provide temporary solutions. Quality, security, and completeness are paramount.

The system must:

✅ Support multi-tenant document indexing with complete data isolation
✅ Parse PDF/DOCX/XLSX documents into searchable chunks
✅ Generate embeddings and store in vector database (ChromaDB/Pinecone)
✅ Parse questionnaires and extract questions automatically
✅ Generate AI answers with citations and confidence scores
✅ Provide React Flow visualization of document processing pipeline
✅ Implement human-in-the-loop approval workflow
✅ Track all changes with audit trail (answer versioning)
✅ Support evaluation against ground-truth answers
✅ Deploy with Docker Compose for local development
✅ Include comprehensive error handling and logging

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ React Flow   │  │   Review     │  │   Document   │      │
│  │  Pipeline    │  │  Interface   │  │   Upload     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         └──────────────────┴──────────────────┘              │
│              React Query + Zustand + SSE                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + SSE
┌──────────────────────────┴──────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Documents   │  │  Questions   │  │   Review     │      │
│  │    API       │  │     API      │  │    API       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         └──────────────────┴──────────────────┘              │
│                   Celery Task Queue                          │
└────┬──────────────┬──────────────┬──────────────┬───────────┘
     │              │              │              │
┌────┴────┐    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐
│PostgreSQL│    │ChromaDB/│    │  Redis  │   │  Local  │
│  (RLS)   │    │Pinecone │    │ Queue   │   │ Storage │
└──────────┘    └─────────┘    └─────────┘   └─────────┘
```

---

## Required Inputs Before Starting

You require exactly FOUR files to begin:

### 1. Project Requirements Document (Markdown)
- Task description from `QUESTIONNAIRE_AGENT_TASKS.md`
- Acceptance criteria
- Expected deliverables
- API endpoint specifications

### 2. Sample Data Files
- Sample questionnaire PDF (e.g., ILPA_Due_Diligence_Questionnaire_v1.2.pdf)
- Sample company documents (PDFs, DOCX)
- These will guide the schema design and parsing logic

### 3. Technology Stack Constraints (Optional)
- Must use FastAPI for backend
- Must use React for frontend
- Database preferences (PostgreSQL required)
- Vector database choice (ChromaDB for local, Pinecone for production)

### 4. Deployment Target (Optional)
- Local development (Docker Compose)
- Cloud deployment (AWS/GCP/Azure)
- If not specified, default to local Docker Compose

**IMPORTANT:** If critical information is missing, immediately request it before proceeding.

---

## API Key Management & Security

### Critical Requirement: User Must Provide API Keys

Before the agent can process any documents or generate answers, users MUST provide:

1. **OpenAI API Key** (Required for embeddings + answer generation)
2. **Optional: Other LLM Provider Keys** (Anthropic, Cohere, etc.)

### Complete API Key Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER JOURNEY                              │
└─────────────────────────────────────────────────────────────┘
    │
    ├─▶ Opens App → No API Key Detected
    │       ↓
    ├─▶ Modal Appears: "🔑 API Key Required"
    │       ↓
    ├─▶ User enters: sk-proj-abc123...
    │       ↓
    ├─▶ Click "Validate & Save"
    │       ↓
    └─▶ Backend validates with OpenAI test request
            ↓
        ✅ Valid → Encrypt & Store → Enable Features
        ❌ Invalid → Show Error → Keep Modal Open

┌─────────────────────────────────────────────────────────────┐
│                  TECHNICAL FLOW                              │
└─────────────────────────────────────────────────────────────┘

Frontend (React)                Backend (FastAPI)              Database
─────────────────               ──────────────────             ──────────
                                                               
User Input                                                     
  └─▶ POST /api-keys/validate                                 
      api_key: "sk-..."         
                                ├─▶ Test with OpenAI          
                                │   embeddings.create()        
                                │                              
                                ├─▶ ✅ Success?                
                                │   ├─ Yes: Encrypt key       
                                │   │  └─▶ Fernet.encrypt()   
                                │   │      └─▶ INSERT INTO     api_key_configs
                                │   │          api_key_configs (encrypted_key)
                                │   │                          
                                │   └─ No: Return error        
                                │                              
                                └─▶ Return success             

Later Processing:                                              
Document Upload                                                
  └─▶ POST /documents/upload                                  
                                ├─▶ Celery Task               
                                │   └─▶ Get API key from DB   
                                │       └─▶ SELECT FROM        api_key_configs
                                │           WHERE tenant_id    
                                │                              
                                │   └─▶ Decrypt key           
                                │       └─▶ Fernet.decrypt()  
                                │                              
                                │   └─▶ Use for OpenAI        
                                │       └─▶ embeddings.create(
                                │           api_key=decrypted)
                                │                              
                                └─▶ Process document           
```

### UI Orchestration Flow

```
User Opens App
    ↓
Check if API Keys Configured
    ↓
    NO → Show "API Key Setup" Modal (BLOCKING)
    │     ├─ Input: OpenAI API Key
    │     ├─ Button: "Validate & Save"
    │     ├─ On Success: Enable app features
    │     └─ On Failure: Show error, keep blocking
    ↓
    YES → Show Dashboard
          ├─ Upload Documents (enabled)
          ├─ Generate Answers (enabled)
          └─ Settings → Manage API Keys
```

### Implementation Strategy

#### a) Frontend: API Key Input Component

**File:** `frontend/src/components/ApiKeySetup.tsx`

```typescript
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

interface ApiKeySetupProps {
  onComplete: () => void;
  existingKey?: string;
}

export function ApiKeySetup({ onComplete, existingKey }: ApiKeySetupProps) {
  const [apiKey, setApiKey] = useState(existingKey || '');
  const [isValidating, setIsValidating] = useState(false);
  
  const validateMutation = useMutation({
    mutationFn: async (key: string) => {
      const response = await fetch('/api/v1/settings/api-keys/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          provider: 'openai',
          api_key: key 
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Invalid API key');
      }
      
      return response.json();
    },
    onSuccess: () => {
      localStorage.setItem('api_key_configured', 'true');
      onComplete();
    }
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!apiKey.startsWith('sk-')) {
      alert('Invalid OpenAI API key format. Must start with "sk-"');
      return;
    }
    
    validateMutation.mutate(apiKey);
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900">🔑 API Key Required</h2>
          <p className="text-gray-600 mt-2">
            Enter your OpenAI API key to enable document processing and answer generation.
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Get your key from{' '}
              <a 
                href="https://platform.openai.com/api-keys" 
                target="_blank"
                className="text-blue-600 hover:underline"
              >
                platform.openai.com/api-keys
              </a>
            </p>
          </div>
          
          {validateMutation.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">
                ❌ {validateMutation.error.message}
              </p>
            </div>
          )}
          
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={validateMutation.isPending || !apiKey}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {validateMutation.isPending ? 'Validating...' : 'Validate & Save'}
            </button>
          </div>
          
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">🔒 Security</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>✓ Stored encrypted in database</li>
              <li>✓ Never sent to our servers (only to OpenAI)</li>
              <li>✓ You can update/remove anytime</li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  );
}
```

#### b) Frontend: App Orchestration with Key Check

**File:** `frontend/src/App.tsx`

```typescript
import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiKeySetup } from './components/ApiKeySetup';
import { Dashboard } from './components/Dashboard';

const queryClient = new QueryClient();

function AppContent() {
  const [hasApiKey, setHasApiKey] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  
  useEffect(() => {
    // Check if API key is configured
    fetch('/api/v1/settings/api-keys/status')
      .then(res => res.json())
      .then(data => {
        setHasApiKey(data.configured);
        setIsChecking(false);
      })
      .catch(() => {
        setHasApiKey(false);
        setIsChecking(false);
      });
  }, []);
  
  if (isChecking) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }
  
  if (!hasApiKey) {
    return <ApiKeySetup onComplete={() => setHasApiKey(true)} />;
  }
  
  return <Dashboard />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
```

#### c) Backend: API Key Management Endpoints

**File:** `backend/app/api/routes/settings.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.crypto_service import CryptoService
from app.services.api_key_validator import ApiKeyValidator
from app.repositories.settings_repository import SettingsRepository

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

class ApiKeyRequest(BaseModel):
    provider: str  # openai, anthropic, cohere
    api_key: str

class ApiKeyStatus(BaseModel):
    configured: bool
    provider: str | None = None
    masked_key: str | None = None

@router.post("/api-keys/validate")
async def validate_api_key(
    request: ApiKeyRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Validate and store user's API key."""
    
    # Validate the key works
    validator = ApiKeyValidator()
    is_valid = await validator.validate(request.provider, request.api_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid API key. Please check and try again."
        )
    
    # Encrypt and store
    crypto = CryptoService()
    encrypted_key = crypto.encrypt(request.api_key)
    
    repo = SettingsRepository()
    await repo.save_api_key(
        tenant_id=tenant_id,
        provider=request.provider,
        encrypted_key=encrypted_key
    )
    
    return {
        "success": True,
        "message": "API key validated and saved",
        "provider": request.provider
    }

@router.get("/api-keys/status", response_model=ApiKeyStatus)
async def get_api_key_status(tenant_id: str = Depends(get_tenant_id)):
    """Check if API keys are configured."""
    
    repo = SettingsRepository()
    config = await repo.get_api_key_config(tenant_id)
    
    if not config:
        return ApiKeyStatus(configured=False)
    
    # Mask the key for display (show last 4 chars)
    decrypted = CryptoService().decrypt(config.encrypted_key)
    masked = f"sk-...{decrypted[-4:]}"
    
    return ApiKeyStatus(
        configured=True,
        provider=config.provider,
        masked_key=masked
    )

@router.delete("/api-keys/{provider}")
async def delete_api_key(
    provider: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Delete stored API key."""
    
    repo = SettingsRepository()
    await repo.delete_api_key(tenant_id, provider)
    
    return {"success": True, "message": f"{provider} API key deleted"}
```

#### d) Backend: API Key Validator Service

**File:** `backend/app/services/api_key_validator.py`

```python
from openai import OpenAI
from anthropic import Anthropic

class ApiKeyValidator:
    async def validate(self, provider: str, api_key: str) -> bool:
        """Validate API key by making a test request."""
        
        try:
            if provider == "openai":
                return await self._validate_openai(api_key)
            elif provider == "anthropic":
                return await self._validate_anthropic(api_key)
            else:
                return False
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False
    
    async def _validate_openai(self, api_key: str) -> bool:
        """Validate OpenAI API key."""
        try:
            client = OpenAI(api_key=api_key)
            
            # Test with minimal embedding request
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            
            return len(response.data) > 0
        except Exception as e:
            print(f"OpenAI validation error: {e}")
            return False
    
    async def _validate_anthropic(self, api_key: str) -> bool:
        """Validate Anthropic API key."""
        try:
            client = Anthropic(api_key=api_key)
            
            # Test with minimal request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return response.content is not None
        except Exception as e:
            print(f"Anthropic validation error: {e}")
            return False
```

#### e) Backend: Settings Repository

**File:** `backend/app/repositories/settings_repository.py`

```python
from sqlalchemy import select, delete
from app.models.database import ApiKeyConfig
from app.database import get_db
from uuid import UUID

class SettingsRepository:
    async def save_api_key(
        self, 
        tenant_id: str, 
        provider: str, 
        encrypted_key: str
    ):
        """Save encrypted API key to database."""
        async with get_db() as db:
            # Delete existing key for this provider
            await db.execute(
                delete(ApiKeyConfig).where(
                    ApiKeyConfig.tenant_id == UUID(tenant_id),
                    ApiKeyConfig.provider == provider
                )
            )
            
            # Insert new key
            config = ApiKeyConfig(
                tenant_id=UUID(tenant_id),
                provider=provider,
                encrypted_key=encrypted_key
            )
            db.add(config)
            await db.commit()
    
    async def get_api_key_config(self, tenant_id: str):
        """Get API key configuration for tenant."""
        async with get_db() as db:
            result = await db.execute(
                select(ApiKeyConfig).where(
                    ApiKeyConfig.tenant_id == UUID(tenant_id)
                )
            )
            return result.scalar_one_or_none()
    
    async def delete_api_key(self, tenant_id: str, provider: str):
        """Delete API key."""
        async with get_db() as db:
            await db.execute(
                delete(ApiKeyConfig).where(
                    ApiKeyConfig.tenant_id == UUID(tenant_id),
                    ApiKeyConfig.provider == provider
                )
            )
            await db.commit()
```

#### f) Database: Add API Key Config Table

**Add to `backend/init.sql`:**

```sql
-- ========== API KEY CONFIGURATION ==========
CREATE TABLE api_key_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- openai, anthropic, cohere
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, provider)
);
CREATE INDEX idx_api_keys_tenant ON api_key_configs(tenant_id);

-- Enable RLS
ALTER TABLE api_key_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON api_key_configs
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

#### g) Backend: Update Services to Use Tenant API Keys

**File:** `backend/app/services/document_processor.py` (Updated)**

```python
from app.repositories.settings_repository import SettingsRepository
from app.services.crypto_service import CryptoService

class DocumentProcessor:
    async def generate_embeddings(
        self, 
        texts: List[str],
        tenant_id: str,
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """Generate embeddings using tenant's API key."""
        
        # Fetch tenant's API key
        repo = SettingsRepository()
        config = await repo.get_api_key_config(tenant_id)
        
        if not config:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured. Please add your API key in Settings."
            )
        
        # Decrypt API key
        crypto = CryptoService()
        api_key = crypto.decrypt(config.encrypted_key)
        
        # Use tenant's key
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        
        return [item.embedding for item in response.data]
```

**File:** `backend/app/services/answer_generator.py` (Updated)**

```python
class AnswerGenerator:
    async def generate_answer(
        self, 
        question: str, 
        contexts: List[Dict],
        tenant_id: str
    ) -> Tuple[str, List[Dict]]:
        """Generate answer using tenant's API key."""
        
        # Fetch tenant's API key
        repo = SettingsRepository()
        config = await repo.get_api_key_config(tenant_id)
        
        if not config:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured."
            )
        
        # Decrypt and use
        crypto = CryptoService()
        api_key = crypto.decrypt(config.encrypted_key)
        
        client = OpenAI(api_key=api_key)
        
        # ... rest of generation logic
```

### Security Best Practices

#### 1. Encryption
```python
# Always encrypt API keys before storage
from cryptography.fernet import Fernet

class CryptoService:
    def __init__(self):
        self.key = os.environ["FERNET_KEY"]
        self.cipher = Fernet(self.key.encode())
    
    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
```

#### 2. Never Log API Keys
```python
# ✅ GOOD
logger.info(f"Processing with provider: {provider}")

# ❌ BAD
logger.info(f"Using API key: {api_key}")  # NEVER DO THIS
```

#### 3. Validate Before Storage
```python
# Always validate before storing
if not await validator.validate(provider, api_key):
    raise HTTPException(400, "Invalid API key")

# Only store if valid
await repo.save_api_key(tenant_id, provider, encrypted_key)
```

#### 4. Rate Limiting
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_tenant_id)

@app.post("/api-keys/validate")
@limiter.limit("5/minute")  # Limit validation attempts
async def validate_api_key(...):
    ...
```

### User Experience Considerations

#### 1. Progressive Disclosure
- Show API key setup ONLY when needed
- Don't block navigation to static pages
- Allow browsing without key, block processing

#### 2. Clear Error Messages
```typescript
// ✅ GOOD
"OpenAI API key required. Add your key in Settings to enable document processing."

// ❌ BAD
"Error: 401 Unauthorized"
```

#### 3. Easy Key Management
- Show masked key in settings: `sk-...xy12`
- One-click update
- Confirm before delete
- Test connection button

#### 4. Help & Guidance
```typescript
<div className="bg-blue-50 p-4 rounded-lg">
  <h4>Where to get your API key?</h4>
  <ol>
    <li>Go to <a href="...">platform.openai.com</a></li>
    <li>Click "Create API Key"</li>
    <li>Copy and paste here</li>
  </ol>
</div>
```

---

## Step-by-Step Implementation Process

You are an agent tasked with building a production-ready DDQ automation system. You must follow each step meticulously and reference this document whenever confused. Save progress in memory and take as much time as needed. Do not skip anything for temporary success.

---

## Step 1: Study Existing Patterns & Architecture

### a) Understand Multi-Tenant RAG Architecture

**Core Concepts:**
- **Retrieval-Augmented Generation (RAG):** Combines vector search with LLM generation
- **Multi-tenancy:** Complete data isolation per tenant
- **Citation Tracking:** Link answers back to source documents
- **Confidence Scoring:** Multi-metric validation of answers

**Key Patterns to Understand:**

1. **Row-Level Security (RLS) in PostgreSQL**
   - Every table has `tenant_id`
   - RLS policies enforce isolation
   - Set tenant context at request start: `SET app.current_tenant_id = 'tenant_uuid'`

2. **Vector Database Tenant Isolation**
   - **Pinecone:** Use namespaces per tenant (`tenant_{tenant_id}`)
   - **ChromaDB:** Use database-per-tenant or collection-per-tenant
   - NEVER use metadata filtering for tenant isolation (security risk)

3. **Document Chunking Strategy**
   - Chunk size: 400-512 tokens (optimal for retrieval)
   - Overlap: 50-100 tokens (maintains context)
   - Store metadata: document_id, page_number, section_title
   - Track character offsets for citation highlighting

4. **Async Processing Pattern**
   - Use Celery for long-running tasks (document processing, answer generation)
   - Track job status with `job_id`
   - Stream progress via Server-Sent Events (SSE)

5. **Citation Tracking Pattern**
   - Store chunks in both PostgreSQL and vector DB
   - PostgreSQL: Full chunk text + metadata
   - Vector DB: Embeddings + chunk_id reference
   - Join on chunk_id to get citation details

### b) Review Database Schema Requirements

**Core Tables:**
- `tenants` - Tenant management
- `projects` - DDQ projects
- `documents` - Source documents
- `document_chunks` - Text chunks with metadata
- `questions` - Questionnaire questions
- `answers` - Generated answers
- `answer_citations` - Links to source chunks
- `answer_versions` - Audit trail

**Critical Fields:**
- Every table needs: `tenant_id`, `created_at`, `updated_at`
- Documents need: `processing_status`, `chunk_count`
- Chunks need: `vector_id`, `page_number`, `char_offset_start/end`
- Answers need: `confidence_score`, `status`, `version`
- Citations need: `relevance_score`, `excerpt`

### c) Understand RAG Pipeline Flow

```
Document Upload
    ↓
Parse PDF/DOCX (PyMuPDF, python-docx)
    ↓
Split into Chunks (RecursiveCharacterTextSplitter)
    ↓
Generate Embeddings (OpenAI, sentence-transformers)
    ↓
Store in Vector DB + PostgreSQL
    ↓
[User uploads questionnaire]
    ↓
Parse Questions from PDF
    ↓
For each question:
    ├─ Generate query embedding
    ├─ Vector search (top-k chunks)
    ├─ Build context from chunks
    ├─ LLM generates answer with citations
    ├─ Calculate confidence score
    └─ Save to database
    ↓
Human reviews answer
    ├─ Approve
    ├─ Reject
    └─ Edit (creates new version)
```

---

## Step 2: Set Up Database Schema

### a) Create PostgreSQL Schema with RLS

**File:** `backend/init.sql`

**Copy the complete schema from the technical specification:**

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========== TENANT MANAGEMENT ==========
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(64) CHECK (status IN ('active', 'suspended', 'disabled')) DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== PROJECTS ==========
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(64) CHECK (status IN ('draft', 'active', 'completed', 'archived')) DEFAULT 'draft',
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);
CREATE INDEX idx_projects_tenant ON projects(tenant_id);

-- ========== DOCUMENTS ==========
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),
    storage_path VARCHAR(1000),
    processing_status VARCHAR(64) CHECK (processing_status IN 
        ('pending', 'processing', 'completed', 'failed')) DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_documents_tenant ON documents(tenant_id);
CREATE INDEX idx_documents_status ON documents(processing_status);

-- ========== DOCUMENT CHUNKS ==========
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_title VARCHAR(500),
    char_offset_start INTEGER,
    char_offset_end INTEGER,
    vector_id VARCHAR(255),
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_vector ON document_chunks(vector_id);

-- ========== QUESTIONS ==========
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_category VARCHAR(255),
    question_number VARCHAR(50),
    response_type VARCHAR(64) DEFAULT 'text',
    status VARCHAR(64) CHECK (status IN 
        ('pending', 'processing', 'draft', 'review', 'approved', 'rejected')) DEFAULT 'pending',
    display_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_questions_project ON questions(project_id);

-- ========== ANSWERS ==========
CREATE TABLE answers (
    answer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    answer_text TEXT,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2),
    retrieval_score DECIMAL(3,2),
    faithfulness_score DECIMAL(3,2),
    status VARCHAR(64) CHECK (status IN 
        ('draft', 'pending_review', 'approved', 'rejected', 'edited')) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    created_by UUID,
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_answers_question ON answers(question_id);
CREATE INDEX idx_answers_status ON answers(status);

-- ========== ANSWER CITATIONS ==========
CREATE TABLE answer_citations (
    citation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    answer_id UUID NOT NULL REFERENCES answers(answer_id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(chunk_id) ON DELETE CASCADE,
    relevance_score DECIMAL(5,4),
    citation_order INTEGER,
    excerpt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_citations_answer ON answer_citations(answer_id);

-- ========== ANSWER VERSIONS ==========
CREATE TABLE answer_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID NOT NULL REFERENCES answers(answer_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_snapshot TEXT NOT NULL,
    diff_from_previous TEXT,
    change_type VARCHAR(50),
    changed_by UUID,
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(answer_id, version_number)
);

-- ========== ROW LEVEL SECURITY ==========
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_citations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation ON document_chunks
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation ON questions
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation ON answers
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation ON answer_citations
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### b) Create Pydantic Models

**File:** `backend/app/models/database.py`

```python
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

class Document(BaseModel):
    document_id: UUID
    tenant_id: UUID
    project_id: Optional[UUID] = None
    filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    storage_path: str
    processing_status: ProcessingStatus
    chunk_count: int = 0
    created_at: datetime
    
class Question(BaseModel):
    question_id: UUID
    tenant_id: UUID
    project_id: UUID
    question_text: str
    question_category: Optional[str] = None
    question_number: Optional[str] = None
    display_order: Optional[int] = None
    status: str
    created_at: datetime

class Answer(BaseModel):
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
    created_at: datetime
    updated_at: datetime

class Citation(BaseModel):
    citation_id: UUID
    document_id: UUID
    document_name: str
    page_number: Optional[int]
    excerpt: str
    relevance_score: float
```

---

## Step 3: Implement Document Processing Pipeline

### a) Create Document Parser Service

**File:** `backend/app/services/document_processor.py`

```python
import pymupdf4llm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import hashlib
import uuid

class DocumentProcessor:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
    
    def parse_document(self, file_path: str) -> List[Dict]:
        """Parse PDF/DOCX into structured chunks with metadata."""
        
        if file_path.endswith('.pdf'):
            # PyMuPDF for layout-aware extraction
            markdown = pymupdf4llm.to_markdown(file_path, page_chunks=True)
            raw_chunks = markdown
        else:
            # Unstructured for other formats
            from unstructured.partition.auto import partition
            elements = partition(filename=file_path)
            raw_chunks = [{"text": str(el), "metadata": el.metadata} 
                         for el in elements]
        
        processed_chunks = []
        chunk_index = 0
        
        for page_data in raw_chunks:
            page_text = page_data.get("text", page_data)
            page_num = page_data.get("metadata", {}).get("page_number", 1)
            
            splits = self.splitter.split_text(page_text)
            
            for split in splits:
                processed_chunks.append({
                    "chunk_index": chunk_index,
                    "text": split,
                    "page_number": page_num,
                    "char_offset_start": page_text.find(split),
                    "char_offset_end": page_text.find(split) + len(split),
                    "content_hash": hashlib.sha256(split.encode()).hexdigest()[:16],
                    "token_count": len(split.split())
                })
                chunk_index += 1
        
        return processed_chunks
    
    def generate_embeddings(self, texts: List[str], 
                          model: str = "text-embedding-3-small") -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        from openai import OpenAI
        client = OpenAI()
        
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]
```

### b) Create Vector Store Service

**File:** `backend/app/services/vector_store.py`

```python
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

class VectorStoreService:
    def __init__(self):
        self.admin_client = chromadb.AdminClient(Settings(
            is_persistent=True,
            persist_directory="./chroma_data"
        ))
    
    def get_tenant_client(self, tenant_id: str):
        """Get ChromaDB client for specific tenant."""
        tenant_name = f"tenant_{tenant_id}"
        try:
            self.admin_client.get_tenant(tenant_name)
        except:
            self.admin_client.create_tenant(tenant_name)
            self.admin_client.create_database("default", tenant_name)
        
        return chromadb.PersistentClient(
            path="./chroma_data",
            tenant=tenant_name,
            database="default"
        )
    
    def get_collection(self, tenant_id: str, project_id: str):
        """Get or create collection for project."""
        client = self.get_tenant_client(tenant_id)
        return client.get_or_create_collection(
            name=f"project_{project_id}",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, tenant_id: str, project_id: str, 
                     chunks: List[Dict], embeddings: List[List[float]]):
        """Add document chunks to vector store."""
        collection = self.get_collection(tenant_id, project_id)
        
        ids = [chunk["vector_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "page_number": chunk["page_number"]
            }
            for chunk in chunks
        ]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    
    def query(self, tenant_id: str, project_id: str, 
             query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Query vector store for similar chunks."""
        collection = self.get_collection(tenant_id, project_id)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return [
            {
                "chunk_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]  # Convert distance to similarity
            }
            for i in range(len(results["ids"][0]))
        ]
```

---

## Step 4: Implement RAG Answer Generation

### a) Create Answer Generation Service

**File:** `backend/app/services/answer_generator.py`

```python
from typing import List, Dict, Tuple
from openai import OpenAI
import json

class AnswerGenerator:
    def __init__(self):
        self.client = OpenAI()
    
    def generate_answer(self, question: str, contexts: List[Dict]) -> Tuple[str, List[Dict]]:
        """Generate answer using LLM with citations."""
        
        # Build context string with numbered references
        context_text = ""
        for idx, ctx in enumerate(contexts, 1):
            context_text += f"\n[{idx}] (Page {ctx['metadata']['page_number']})\n{ctx['text']}\n"
        
        prompt = f"""You are answering a due diligence questionnaire based on company documents.

Question: {question}

Available Context from Documents:
{context_text}

Instructions:
1. Answer the question based ONLY on the provided context
2. If the answer cannot be found in the context, say "Information not found in provided documents"
3. Include citation numbers [1], [2], etc. in your answer
4. Be concise and factual
5. Do not make assumptions beyond what's stated in the documents

Answer:"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a due diligence analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        answer_text = response.choices[0].message.content
        
        # Extract which citations were actually used
        used_citations = []
        for idx, ctx in enumerate(contexts, 1):
            if f"[{idx}]" in answer_text:
                used_citations.append({
                    "chunk_id": ctx["chunk_id"],
                    "document_id": ctx["metadata"]["document_id"],
                    "page_number": ctx["metadata"]["page_number"],
                    "excerpt": ctx["text"][:200],
                    "relevance_score": ctx["score"]
                })
        
        return answer_text, used_citations
```

### b) Create Confidence Scoring Service

**File:** `backend/app/services/confidence_scorer.py`

```python
from typing import List, Dict
import numpy as np
from openai import OpenAI

class ConfidenceScorer:
    def __init__(self):
        self.client = OpenAI()
    
    def calculate_confidence(self, retrieval_results: List[Dict],
                           answer: str, question: str) -> Dict[str, float]:
        """Calculate multi-metric confidence score."""
        
        # 1. Retrieval confidence
        scores = [r["score"] for r in retrieval_results]
        retrieval_conf = np.mean(scores) if scores else 0
        
        # 2. Coverage score
        high_relevance = sum(1 for s in scores if s > 0.7)
        coverage = high_relevance / max(len(scores), 1)
        
        # 3. Faithfulness score
        faithfulness = self._check_faithfulness(
            answer, [r["text"] for r in retrieval_results]
        )
        
        # 4. Relevancy score
        relevancy = self._check_relevancy(answer, question)
        
        # Weighted composite
        weights = {
            "retrieval": 0.25,
            "coverage": 0.15,
            "faithfulness": 0.35,
            "relevancy": 0.25
        }
        
        composite = (
            weights["retrieval"] * retrieval_conf +
            weights["coverage"] * coverage +
            weights["faithfulness"] * faithfulness +
            weights["relevancy"] * relevancy
        )
        
        return {
            "overall": round(composite, 3),
            "retrieval": round(retrieval_conf, 3),
            "coverage": round(coverage, 3),
            "faithfulness": round(faithfulness, 3),
            "relevancy": round(relevancy, 3)
        }
    
    def _check_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """Use LLM to verify answer grounding."""
        context_text = "\n---\n".join(contexts)
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """Score answer faithfulness from 0.0 to 1.0.
                1.0 = Fully supported by context
                0.5 = Partially supported
                0.0 = Unsupported claims
                Return only the numeric score."""
            }, {
                "role": "user",
                "content": f"Context:\n{context_text}\n\nAnswer:\n{answer}"
            }],
            temperature=0
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 0.5
    
    def _check_relevancy(self, answer: str, question: str) -> float:
        """Check if answer addresses the question."""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """Score answer relevancy from 0.0 to 1.0.
                1.0 = Directly answers question
                0.5 = Partially relevant
                0.0 = Not relevant
                Return only the numeric score."""
            }, {
                "role": "user",
                "content": f"Question:\n{question}\n\nAnswer:\n{answer}"
            }],
            temperature=0
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 0.5
```

---

## Step 5: Create FastAPI Endpoints

### a) Main API Routes

**File:** `backend/app/api/routes.py`

```python
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
import asyncio

app = FastAPI(title="DDQ Agent API")

# ========== PYDANTIC MODELS ==========
class DocumentUploadResponse(BaseModel):
    job_id: str
    status: str
    message: str

class QuestionRequest(BaseModel):
    question_text: str
    project_id: str

class ReviewRequest(BaseModel):
    action: str  # approve, reject, edit
    edited_text: Optional[str] = None
    review_notes: Optional[str] = None

# ========== DOCUMENT ENDPOINTS ==========
@app.post("/api/v1/documents/upload")
async def upload_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
    tenant_id: str = Depends(get_tenant_id)
):
    job_id = str(uuid.uuid4())
    
    # Save files
    file_paths = await save_files(files, tenant_id)
    
    # Queue processing task
    from app.tasks import process_documents_task
    process_documents_task.delay(job_id, tenant_id, project_id, file_paths)
    
    return DocumentUploadResponse(
        job_id=job_id,
        status="queued",
        message=f"Processing {len(files)} documents"
    )

@app.get("/api/v1/documents/{job_id}/status")
async def get_job_status(job_id: str):
    from celery.result import AsyncResult
    task = AsyncResult(job_id)
    
    return {
        "job_id": job_id,
        "status": task.state,
        "progress": task.info.get("progress", 0) if task.info else 0
    }

# ========== QUESTION/ANSWER ENDPOINTS ==========
@app.post("/api/v1/questions/generate")
async def generate_answer(
    request: QuestionRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    query_id = str(uuid.uuid4())
    
    from app.tasks import generate_answer_task
    generate_answer_task.delay(
        query_id, tenant_id, request.project_id, request.question_text
    )
    
    return {"query_id": query_id, "status": "queued"}

@app.get("/api/v1/answers/{answer_id}")
async def get_answer(answer_id: str, tenant_id: str = Depends(get_tenant_id)):
    # Fetch from database with citations
    answer = await fetch_answer_with_citations(answer_id, tenant_id)
    if not answer:
        raise HTTPException(404, "Answer not found")
    return answer

# ========== REVIEW ENDPOINTS ==========
@app.post("/api/v1/answers/{answer_id}/review")
async def submit_review(
    answer_id: str,
    review: ReviewRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    if review.action == "approve":
        await update_answer_status(answer_id, "approved")
    elif review.action == "reject":
        await update_answer_status(answer_id, "rejected")
    elif review.action == "edit":
        await create_answer_version(answer_id)
        await update_answer_text(answer_id, review.edited_text)
        await update_answer_status(answer_id, "edited")
    
    return {"status": "success"}

# ========== SSE STREAMING ==========
@app.get("/api/v1/stream/{job_id}")
async def stream_progress(job_id: str):
    async def event_generator():
        from celery.result import AsyncResult
        
        while True:
            task = AsyncResult(job_id)
            meta = task.info or {}
            
            data = {
                "job_id": job_id,
                "status": task.state,
                "progress": meta.get("progress", 0)
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            if task.state in ["SUCCESS", "FAILURE"]:
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### b) Create Celery Tasks

**File:** `backend/app/tasks.py`

```python
from celery import shared_task
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.answer_generator import AnswerGenerator
from app.services.confidence_scorer import ConfidenceScorer

@shared_task(bind=True)
def process_documents_task(self, job_id, tenant_id, project_id, file_paths):
    processor = DocumentProcessor()
    vector_store = VectorStoreService()
    
    total = len(file_paths)
    
    for idx, file_path in enumerate(file_paths):
        self.update_state(state="STARTED", meta={
            "progress": idx / total,
            "stage": "processing"
        })
        
        # Parse
        chunks = processor.parse_document(file_path)
        
        # Embed
        embeddings = processor.generate_embeddings([c["text"] for c in chunks])
        
        # Store
        vector_store.add_documents(tenant_id, project_id, chunks, embeddings)
    
    return {"status": "completed", "documents": total}

@shared_task(bind=True)
def generate_answer_task(self, query_id, tenant_id, project_id, question):
    vector_store = VectorStoreService()
    generator = AnswerGenerator()
    scorer = ConfidenceScorer()
    
    # Generate query embedding
    from app.services.document_processor import DocumentProcessor
    embeddings = DocumentProcessor().generate_embeddings([question])
    
    # Retrieve
    results = vector_store.query(tenant_id, project_id, embeddings[0], top_k=5)
    
    # Generate
    answer, citations = generator.generate_answer(question, results)
    
    # Score
    confidence = scorer.calculate_confidence(results, answer, question)
    
    # Save to database
    answer_id = save_answer_to_db(
        tenant_id, query_id, question, answer, citations, confidence
    )
    
    return {"answer_id": answer_id}
```

---

## Step 6: Build React Frontend with React Flow

### a) Install Dependencies

```bash
cd frontend
npm install @xyflow/react @tanstack/react-query zustand
```

### b) Create React Flow Pipeline Visualization

**File:** `frontend/src/components/PipelineFlow.tsx`

```typescript
import { useCallback, useEffect } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: 'upload', type: 'pipelineNode', position: { x: 0, y: 100 }, 
    data: { label: 'Upload', status: 'idle' }},
  { id: 'parse', type: 'pipelineNode', position: { x: 220, y: 100 }, 
    data: { label: 'Parse', status: 'idle' }},
  { id: 'chunk', type: 'pipelineNode', position: { x: 440, y: 100 }, 
    data: { label: 'Chunk', status: 'idle' }},
  { id: 'embed', type: 'pipelineNode', position: { x: 660, y: 100 }, 
    data: { label: 'Embed', status: 'idle' }},
  { id: 'store', type: 'pipelineNode', position: { x: 880, y: 100 }, 
    data: { label: 'Store', status: 'idle' }},
];

const initialEdges = [
  { id: 'e1', source: 'upload', target: 'parse', animated: true },
  { id: 'e2', source: 'parse', target: 'chunk' },
  { id: 'e3', source: 'chunk', target: 'embed' },
  { id: 'e4', source: 'embed', target: 'store' },
];

export function PipelineVisualization({ jobId }: { jobId?: string }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  // Subscribe to SSE updates
  useEffect(() => {
    if (!jobId) return;
    
    const eventSource = new EventSource(`/api/v1/stream/${jobId}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Update node statuses based on progress
      const stageToNode: Record<string, string> = {
        'uploading': 'upload',
        'parsing': 'parse',
        'chunking': 'chunk',
        'embedding': 'embed',
        'storing': 'store'
      };
      
      const nodeId = stageToNode[data.stage];
      if (nodeId) {
        setNodes(nds => nds.map(node => 
          node.id === nodeId 
            ? { ...node, data: { ...node.data, status: 'processing', progress: data.progress }}
            : node
        ));
      }
    };
    
    return () => eventSource.close();
  }, [jobId, setNodes]);
  
  return (
    <div className="h-[400px] border rounded-lg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
```

### c) Create Review Interface

**File:** `frontend/src/components/ReviewPanel.tsx`

```typescript
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Citation {
  citation_id: string;
  document_name: string;
  page_number: number;
  excerpt: string;
  relevance_score: number;
}

interface Answer {
  answer_id: string;
  answer_text: string;
  confidence_score: number;
  citations: Citation[];
  status: string;
}

export function ReviewPanel({ answerId, answer }: { answerId: string; answer: Answer }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(answer.answer_text);
  const queryClient = useQueryClient();
  
  const reviewMutation = useMutation({
    mutationFn: (action: { action: string; edited_text?: string }) =>
      fetch(`/api/v1/answers/${answerId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action)
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['answers'] });
    }
  });
  
  const renderAnswerWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        return (
          <sup key={i} className="text-blue-600 cursor-pointer">
            {match[1]}
          </sup>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };
  
  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Answer Panel */}
      <div className="border rounded-lg p-4">
        <div className="mb-4">
          <span className="px-3 py-1 rounded bg-green-100 text-green-800">
            {Math.round(answer.confidence_score * 100)}% Confidence
          </span>
        </div>
        
        {isEditing ? (
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            className="w-full h-64 p-2 border rounded"
          />
        ) : (
          <div className="prose">
            {renderAnswerWithCitations(answer.answer_text)}
          </div>
        )}
        
        <div className="flex gap-2 mt-4">
          {isEditing ? (
            <>
              <button
                onClick={() => {
                  reviewMutation.mutate({ action: 'edit', edited_text: editedText });
                  setIsEditing(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded"
              >
                Save
              </button>
              <button onClick={() => setIsEditing(false)} className="px-4 py-2 border rounded">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => reviewMutation.mutate({ action: 'approve' })}
                className="px-4 py-2 bg-green-600 text-white rounded"
              >
                ✓ Approve
              </button>
              <button
                onClick={() => reviewMutation.mutate({ action: 'reject' })}
                className="px-4 py-2 bg-red-600 text-white rounded"
              >
                ✗ Reject
              </button>
              <button onClick={() => setIsEditing(true)} className="px-4 py-2 border rounded">
                ✎ Edit
              </button>
            </>
          )}
        </div>
      </div>
      
      {/* Citations Panel */}
      <div className="border rounded-lg p-4">
        <h3 className="font-medium mb-4">Source Citations</h3>
        {answer.citations.map((citation, idx) => (
          <div key={citation.citation_id} className="mb-3 p-3 border rounded">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-700 rounded">
                {idx + 1}
              </span>
              <span className="font-medium">{citation.document_name}</span>
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Page {citation.page_number} • {Math.round(citation.relevance_score * 100)}% relevant
            </div>
            <p className="text-sm mt-2">{citation.excerpt}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Step 7: Create Docker Compose Setup

**File:** `docker-compose.yml`

```yaml
version: '3.9'

services:
  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ddquser:${DB_PASSWORD}@db:5432/ddqdb
      - REDIS_URL=redis://redis:6379/0
      - FERNET_KEY=${FERNET_KEY}  # For encrypting user API keys
      # Note: User API keys stored in database, not environment
    depends_on:
      - db
      - redis
      - chromadb

  worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://ddquser:${DB_PASSWORD}@db:5432/ddqdb
      - REDIS_URL=redis://redis:6379/0
      - FERNET_KEY=${FERNET_KEY}
    depends_on:
      - api

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_USER=ddquser
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=ddqdb

  chromadb:
    image: chromadb/chroma:0.6.3
    volumes:
      - chroma_data:/chroma/chroma
    ports:
      - "8001:8000"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  chroma_data:
  redis_data:
```

**Environment Variables Setup:**

Create `.env` file in project root:

```bash
# Database
DB_PASSWORD=your_secure_password_here

# Encryption key for user API keys (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FERNET_KEY=your_fernet_key_here

# Note: User OpenAI API keys are stored encrypted in database
# Users enter their own keys through the UI
```

**Generate Fernet Key:**

```bash
# Run this to generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example output: a0H07YOiGE6x2hC4sBYOlsG6BosGxDDMhmXMBegXp_g=
# Add this to .env as FERNET_KEY
```

---

## Step 8: Write Comprehensive Tests

### a) Backend Integration Tests

**File:** `backend/tests/test_rag_pipeline.py`

```python
import pytest
import asyncio
from app.services.document_processor import DocumentProcessor
from app.services.answer_generator import AnswerGenerator

@pytest.mark.asyncio
async def test_document_processing():
    """Test full document processing pipeline."""
    processor = DocumentProcessor()
    
    # Process test PDF
    chunks = processor.parse_document("tests/data/sample.pdf")
    
    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)
    assert all("page_number" in chunk for chunk in chunks)
    
    # Generate embeddings
    embeddings = processor.generate_embeddings([c["text"] for c in chunks[:5]])
    assert len(embeddings) == 5
    assert len(embeddings[0]) == 1536  # OpenAI embedding dimension

@pytest.mark.asyncio
async def test_answer_generation():
    """Test RAG answer generation."""
    generator = AnswerGenerator()
    
    question = "What is the company's revenue?"
    contexts = [
        {
            "chunk_id": "123",
            "text": "The company reported revenue of $45.2M in FY2023.",
            "metadata": {"document_id": "doc1", "page_number": 5},
            "score": 0.92
        }
    ]
    
    answer, citations = generator.generate_answer(question, contexts)
    
    assert "$45.2M" in answer or "45.2" in answer
    assert len(citations) > 0
```

### b) Frontend Component Tests

**File:** `frontend/src/components/__tests__/ReviewPanel.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ReviewPanel } from '../ReviewPanel';

describe('ReviewPanel', () => {
  const mockAnswer = {
    answer_id: '123',
    answer_text: 'Revenue was $45M [1]',
    confidence_score: 0.92,
    citations: [
      {
        citation_id: 'c1',
        document_name: 'Financial Statement',
        page_number: 5,
        excerpt: 'Total revenue: $45M',
        relevance_score: 0.95
      }
    ],
    status: 'pending_review'
  };
  
  it('renders answer with citations', () => {
    render(<ReviewPanel answerId="123" answer={mockAnswer} />);
    
    expect(screen.getByText(/Revenue was \$45M/)).toBeInTheDocument();
    expect(screen.getByText('Financial Statement')).toBeInTheDocument();
  });
  
  it('enables editing on Edit button click', () => {
    render(<ReviewPanel answerId="123" answer={mockAnswer} />);
    
    fireEvent.click(screen.getByText('✎ Edit'));
    
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });
});
```

---

## Critical Requirements Checklist

### ✅ Must Have:

1. **Multi-Tenant Isolation**
   - RLS policies on all tables
   - Tenant-specific vector namespaces/collections
   - Tenant context set on every request

2. **Document Processing**
   - Support PDF, DOCX, XLSX
   - Chunk size: 400-512 tokens
   - Overlap: 50-100 tokens
   - Metadata tracking (page, section, offsets)

3. **Vector Search**
   - Tenant isolation via namespaces (never metadata filtering)
   - Store chunk_id for citation linking
   - Top-k retrieval (k=5-10)

4. **Answer Generation**
   - RAG pipeline with LLM
   - Citation extraction and tracking
   - Confidence scoring (multi-metric)
   - Fallback for unanswerable questions

5. **React Flow Visualization**
   - Real-time status updates via SSE
   - Pipeline stages shown visually
   - Progress indicators on nodes

6. **Human Review Workflow**
   - Approve/Reject/Edit actions
   - Version history on edits
   - Citation display with highlighting
   - Confidence score visualization

7. **Database Design**
   - All 8 core tables created
   - RLS enabled
   - Proper indexes
   - Version tracking

8. **API Design**
   - Async task processing (Celery)
   - SSE for progress streaming
   - Proper error handling
   - Tenant authentication

9. **Security**
   - Row-level security
   - Encrypted sensitive data
   - Secure vector isolation
   - Input validation

10. **Testing**
    - Unit tests for services
    - Integration tests for RAG pipeline
    - Frontend component tests
    - End-to-end workflow tests

### ❌ Never Do:

- Use metadata filtering for tenant isolation (security risk)
- Store embeddings in PostgreSQL (performance issue)
- Skip citation tracking
- Ignore confidence scoring
- Deploy without RLS policies
- Use synchronous processing for large documents
- Hardcode credentials
- Skip error handling
- Ignore audit trail requirements
- Deploy without tests

---

## Validation Checklist

Before considering complete:

- [ ] **API Key Management**
- [ ] User can input OpenAI API key through UI
- [ ] API key validation working (test request to OpenAI)
- [ ] API keys stored encrypted in database
- [ ] UI blocks processing without API key
- [ ] Settings page shows masked key (`sk-...xy12`)
- [ ] User can update/delete API key
- [ ] Fernet encryption key configured in .env
- [ ] **Database & Schema**
- [ ] Database schema matches specification
- [ ] RLS policies working
- [ ] `api_key_configs` table created
- [ ] **Document Processing**
- [ ] Document parsing handles PDF/DOCX
- [ ] Chunking strategy optimized (400-512 tokens)
- [ ] Embeddings generated successfully (using user's API key)
- [ ] **Vector Store**
- [ ] Vector store has tenant isolation
- [ ] Tenant namespaces/collections working
- [ ] **RAG Pipeline**
- [ ] RAG pipeline generates answers (using user's API key)
- [ ] Citations linked to source chunks
- [ ] Confidence scoring implemented
- [ ] **Frontend**
- [ ] API key setup modal on first load
- [ ] React Flow visualization working
- [ ] SSE streaming progress updates
- [ ] Review workflow functional (approve/reject/edit)
- [ ] Settings page for API key management
- [ ] **Backend API**
- [ ] Answer versioning on edits
- [ ] All endpoints use tenant's API key (not hardcoded)
- [ ] API key validation endpoint working
- [ ] **Deployment**
- [ ] Docker Compose setup complete
- [ ] FERNET_KEY in environment variables
- [ ] .env.example file provided
- [ ] **Testing**
- [ ] All tests passing
- [ ] API key encryption tests
- [ ] API key validation tests
- [ ] **Documentation**
- [ ] Documentation written
- [ ] Setup instructions include API key generation
- [ ] Security notes about API key storage

---

## 72-Hour Implementation Timeline

### Day 1 (Hours 1-24): Backend Core
- ✅ PostgreSQL schema + RLS policies
- ✅ Pydantic models
- ✅ Document processor service
- ✅ Vector store service
- ✅ Basic API endpoints
- ✅ Celery task setup

### Day 2 (Hours 25-48): RAG Pipeline + API
- ✅ Answer generator service
- ✅ Confidence scorer service
- ✅ Complete API endpoints
- ✅ SSE streaming
- ✅ Database integration
- ✅ Citation tracking

### Day 3 (Hours 49-72): Frontend + Polish
- ✅ React Flow visualization
- ✅ Review interface
- ✅ State management (Zustand + React Query)
- ✅ Docker Compose
- ✅ Testing
- ✅ Documentation
- ✅ Bug fixes

---

## Success Criteria

System is complete when:

✅ **User can configure their OpenAI API key through UI**
✅ **API key validation works before allowing processing**
✅ **API keys stored encrypted in database**
✅ Documents upload and process successfully (using user's key)
✅ Questions generate AI answers with citations (using user's key)
✅ Confidence scores calculated accurately
✅ React Flow shows real-time progress
✅ Review workflow allows approve/reject/edit
✅ Citations link to source documents
✅ Multi-tenant isolation verified
✅ All tests pass
✅ Docker Compose starts all services
✅ Documentation covers API key setup and usage

---

## Quality Standards

Each component must be:

✅ **Production-ready:** No TODOs, no placeholders
✅ **Tested:** Unit + integration tests
✅ **Documented:** Clear README and code comments
✅ **Secure:** RLS, encryption, validation
✅ **Maintainable:** Clean code, proper logging
✅ **Scalable:** Async processing, efficient queries
✅ **Observable:** Comprehensive logging

---

## Important Notes

### Multi-Tenant Security (CRITICAL)

**Always use:**
- PostgreSQL RLS policies
- Vector database namespaces (Pinecone) or separate databases (ChromaDB)
- Tenant context on every request

**Never use:**
- Metadata filtering for tenant isolation (queries scan all data)
- Shared collections without namespaces
- Client-side tenant filtering

### Chunk Size Optimization

**Start with:**
- Chunk size: 512 tokens
- Overlap: 100 tokens
- Separator priority: `\n\n` → `\n` → `. ` → ` `

**Adjust based on:**
- Factoid questions → smaller chunks (256-400 tokens)
- Analytical questions → larger chunks (600-800 tokens)
- Document structure (paragraphs, sections)

### Citation Tracking Pattern

**Always:**
- Store chunks in PostgreSQL + vector DB
- Link via `chunk_id` and `vector_id`
- Track page numbers, offsets, excerpts
- Join tables to build complete citations

**Never:**
- Store only in vector DB (can't get full metadata)
- Lose page number tracking
- Skip excerpt extraction

### Confidence Scoring

**Include these metrics:**
- Retrieval confidence (vector similarity)
- Coverage (% of high-relevance chunks)
- Faithfulness (LLM-verified grounding)
- Relevancy (answer addresses question)

**Combine with weights:**
- Faithfulness: 35%
- Retrieval: 25%
- Relevancy: 25%
- Coverage: 15%

---

Remember: Take your time, follow patterns exactly, and build production-grade code. This is an interview project - quality matters more than speed. Focus on demonstrating:

1. Strong architectural understanding
2. Multi-tenant security awareness
3. RAG pipeline expertise
4. Full-stack integration skills
5. Production-ready code quality

Good luck! 🚀