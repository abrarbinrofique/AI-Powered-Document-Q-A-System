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

-- Insert default tenant for development
INSERT INTO tenants (tenant_id, name, status) VALUES
    ('00000000-0000-0000-0000-000000000001'::UUID, 'default-tenant', 'active');

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
CREATE INDEX idx_documents_project ON documents(project_id);

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
CREATE INDEX idx_chunks_tenant ON document_chunks(tenant_id);

-- ========== QUESTIONS ==========
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_category VARCHAR(255),
    question_number VARCHAR(50),
    ground_truth_answer TEXT,
    response_type VARCHAR(64) DEFAULT 'text',
    status VARCHAR(64) CHECK (status IN
        ('pending', 'processing', 'draft', 'review', 'approved', 'rejected')) DEFAULT 'pending',
    display_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_questions_project ON questions(project_id);
CREATE INDEX idx_questions_tenant ON questions(tenant_id);
CREATE INDEX idx_questions_status ON questions(status);

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
CREATE INDEX idx_answers_tenant ON answers(tenant_id);

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
CREATE INDEX idx_citations_chunk ON answer_citations(chunk_id);
CREATE INDEX idx_citations_tenant ON answer_citations(tenant_id);

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
CREATE INDEX idx_versions_answer ON answer_versions(answer_id);

-- ========== ROW LEVEL SECURITY ==========
ALTER TABLE api_key_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_citations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON api_key_configs
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
CREATE POLICY tenant_isolation ON projects
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
CREATE POLICY tenant_isolation ON document_chunks
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
CREATE POLICY tenant_isolation ON questions
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
CREATE POLICY tenant_isolation ON answers
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
CREATE POLICY tenant_isolation ON answer_citations
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
