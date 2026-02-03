# Testing Guide for DDQ Agent

This guide provides step-by-step instructions for testing the complete DDQ Agent system.

## Prerequisites

1. Docker and Docker Compose installed
2. OpenAI API key (get from https://platform.openai.com/api-keys)
3. Sample documents (PDF, DOCX, or TXT files)

## Initial Setup

### 1. Start the System

```bash
# Make sure .env is configured
./setup.sh

# Or manually:
docker-compose up --build
```

Wait for all services to start (about 30-60 seconds).

### 2. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

You should see:
- api (healthy)
- worker (running)
- frontend (running)
- db (healthy)
- chromadb (running)
- redis (healthy)

### 3. Create Sample Project

```bash
docker-compose exec db psql -U ddquser -d ddqdb -f /docker-entrypoint-initdb.d/create_sample_project.sql
```

Or create via API:

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "Testing DDQ Agent"
  }'
```

## Test API Key Management

### 1. Check API Key Status (Should be unconfigured)

```bash
curl http://localhost:8000/api/v1/settings/api-keys/status
```

Expected response:
```json
{"configured": false, "provider": null, "masked_key": null}
```

### 2. Validate and Store API Key

```bash
curl -X POST http://localhost:8000/api/v1/settings/api-keys/validate \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-YOUR-ACTUAL-OPENAI-KEY-HERE"
  }'
```

Expected response:
```json
{"success": true, "message": "API key validated and saved", "provider": "openai"}
```

### 3. Verify API Key is Stored

```bash
curl http://localhost:8000/api/v1/settings/api-keys/status
```

Expected response:
```json
{
  "configured": true,
  "provider": "openai",
  "masked_key": "sk-...xyz1"
}
```

## Test Document Upload and Processing

### 1. List Projects

```bash
curl http://localhost:8000/api/v1/projects
```

Copy a `project_id` from the response.

### 2. Upload Documents

Create a test file or use existing PDF/DOCX:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "project_id=YOUR-PROJECT-ID-HERE" \
  -F "files=@/path/to/your/document.pdf"
```

Expected response:
```json
{
  "job_id": "abc123...",
  "status": "queued",
  "message": "Processing 1 documents"
}
```

### 3. Check Processing Status

```bash
curl http://localhost:8000/api/v1/documents/abc123.../status
```

Expected response (while processing):
```json
{
  "job_id": "abc123...",
  "status": "PROGRESS",
  "progress": 0.5,
  "stage": "processing",
  "message": "document.pdf"
}
```

Expected response (completed):
```json
{
  "job_id": "abc123...",
  "status": "SUCCESS",
  "progress": 1.0
}
```

### 4. List Processed Documents

```bash
curl http://localhost:8000/api/v1/documents/project/YOUR-PROJECT-ID
```

## Test Answer Generation

### 1. Generate Answer for a Question

```bash
curl -X POST http://localhost:8000/api/v1/questions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is the company name?",
    "project_id": "YOUR-PROJECT-ID-HERE"
  }'
```

Expected response:
```json
{
  "query_id": "task-123...",
  "status": "queued",
  "message": "Answer generation in progress"
}
```

### 2. Wait for Processing

Answer generation takes 10-30 seconds depending on document size.

### 3. List Questions

```bash
curl http://localhost:8000/api/v1/questions/project/YOUR-PROJECT-ID
```

Copy a `question_id` from the response.

### 4. Get Answer with Citations

```bash
curl http://localhost:8000/api/v1/answers/ANSWER-ID-HERE
```

Expected response:
```json
{
  "answer_id": "...",
  "answer_text": "The company name is XYZ Corp [1].",
  "confidence_score": 0.85,
  "retrieval_score": 0.82,
  "faithfulness_score": 0.8,
  "status": "pending_review",
  "citations": [
    {
      "citation_id": "...",
      "document_name": "document.pdf",
      "page_number": 1,
      "excerpt": "XYZ Corp is a leading provider...",
      "relevance_score": 0.92
    }
  ]
}
```

## Test Review Workflow

### 1. Approve Answer

```bash
curl -X POST http://localhost:8000/api/v1/answers/ANSWER-ID/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "review_notes": "Looks good"
  }'
```

### 2. Reject Answer

```bash
curl -X POST http://localhost:8000/api/v1/answers/ANSWER-ID/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "review_notes": "Needs more detail"
  }'
```

### 3. Edit Answer

```bash
curl -X POST http://localhost:8000/api/v1/answers/ANSWER-ID/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "edit",
    "edited_text": "The company name is XYZ Corp, founded in 2020.",
    "review_notes": "Added founding year"
  }'
```

## Test Frontend UI

### 1. Open Frontend

Navigate to http://localhost:3000

### 2. API Key Setup

You should see a modal: "API Key Required"

1. Enter your OpenAI API key (starts with `sk-`)
2. Click "Validate & Save"
3. Wait for validation (makes real API call to OpenAI)
4. On success, modal closes and dashboard appears

### 3. Select Project

1. Use dropdown to select "Sample DDQ Project" or your created project
2. Three tabs should appear: Upload Documents, Generate Answers, Review Answers

### 4. Upload Documents

1. Click "Upload Documents" tab
2. Click "Choose Files" and select PDF/DOCX/TXT files
3. Click "Upload Documents"
4. Wait for green success message

### 5. Generate Answer

1. Click "Generate Answers" tab
2. Enter a question about your documents
3. Click "Generate Answer"
4. Wait for green success message

### 6. Review Answer

1. Click "Review Answers" tab
2. Select the question from dropdown
3. View answer and citations
4. Test buttons:
   - "Approve" - marks answer as approved
   - "Reject" - marks answer as rejected
   - "Edit" - enables editing mode
   - In edit mode: "Save" updates answer, "Cancel" discards changes

## Verify Database State

### Check API Key Storage (Encrypted)

```bash
docker-compose exec db psql -U ddquser -d ddqdb -c \
  "SELECT provider, substring(encrypted_key, 1, 20) as encrypted_prefix, created_at FROM api_key_configs;"
```

### Check Documents

```bash
docker-compose exec db psql -U ddquser -d ddqdb -c \
  "SELECT filename, processing_status, chunk_count FROM documents;"
```

### Check Chunks

```bash
docker-compose exec db psql -U ddquser -d ddqdb -c \
  "SELECT COUNT(*), document_id FROM document_chunks GROUP BY document_id;"
```

### Check Answers

```bash
docker-compose exec db psql -U ddquser -d ddqdb -c \
  "SELECT substring(answer_text, 1, 50) as answer_preview, status, confidence_score FROM answers;"
```

### Check Citations

```bash
docker-compose exec db psql -U ddquser -d ddqdb -c \
  "SELECT answer_id, COUNT(*) as citation_count FROM answer_citations GROUP BY answer_id;"
```

## Verify ChromaDB

### Check Collections

```bash
curl http://localhost:8001/api/v1/collections
```

You should see collections like `tenant_..._project_...`

### Check Collection Count

```bash
curl http://localhost:8001/api/v1/collections/tenant_TENANT-ID_project_PROJECT-ID
```

## Troubleshooting

### API Key Validation Fails

1. Check OpenAI key is valid at platform.openai.com
2. Verify key starts with `sk-`
3. Check API has credits
4. View API logs: `docker-compose logs api`

### Documents Not Processing

1. Check Celery worker logs: `docker-compose logs worker`
2. Verify API key is configured
3. Check file format is supported
4. View Redis queue: `docker-compose exec redis redis-cli KEYS "*"`

### Answer Generation Fails

1. Ensure documents are processed (status = "completed")
2. Check ChromaDB has embeddings
3. View worker logs for errors
4. Verify OpenAI API key has sufficient quota

### Frontend Not Loading

1. Check frontend logs: `docker-compose logs frontend`
2. Verify API is running: `curl http://localhost:8000/health`
3. Check browser console for errors

## Clean Up

### Remove All Data

```bash
docker-compose down -v
```

This removes containers, networks, and volumes (including database and ChromaDB data).

### Keep Data, Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose up -d
```

## Performance Testing

### Bulk Document Upload

```bash
# Upload multiple files
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/documents/upload \
    -F "project_id=YOUR-PROJECT-ID" \
    -F "files=@document${i}.pdf"
done
```

### Concurrent Question Generation

```bash
# Generate multiple answers simultaneously
for i in {1..3}; do
  curl -X POST http://localhost:8000/api/v1/questions/generate \
    -H "Content-Type: application/json" \
    -d "{\"question_text\":\"Question $i?\",\"project_id\":\"YOUR-PROJECT-ID\"}" &
done
wait
```

## Security Testing

### Verify Tenant Isolation

1. Create two projects
2. Upload documents to Project A
3. Try to query documents from Project A using Project B's ID
4. Should return empty results (RLS prevents cross-tenant access)

### Verify API Key Encryption

```bash
# Check that stored key is encrypted, not plain text
docker-compose exec db psql -U ddquser -d ddqdb -c \
  "SELECT encrypted_key FROM api_key_configs LIMIT 1;"
```

The value should look like gibberish (e.g., `gAAAABm...`), not like `sk-...`

### Verify API Key Never Logged

```bash
# Check logs don't contain API keys
docker-compose logs api | grep "sk-"
docker-compose logs worker | grep "sk-"
```

Should return no results (API keys should never be logged).

## Success Criteria

The system is working correctly if:

- API key setup modal appears on first load
- API key validation works (makes real OpenAI request)
- API keys are stored encrypted in database
- Documents upload and process successfully
- Chunks are created in PostgreSQL
- Embeddings are stored in ChromaDB
- Questions generate answers with citations
- Confidence scores are calculated
- Review workflow (approve/reject/edit) works
- Answer versions are created on edit
- All data is properly isolated by tenant
- No API keys appear in logs
- Frontend and backend communicate properly
