# 🤖 DDQ Agent - AI-Powered Due Diligence Automation

> A production-ready system for automating due diligence questionnaires using RAG (Retrieval-Augmented Generation), multi-tenant architecture, and human-in-the-loop approval workflows.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Setup](#-quick-setup-copy-paste-commands)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development-without-docker)
- [Technology Stack](#️-technology-stack)
- [FAQ](#-frequently-asked-questions-faq)
- [Production Deployment](#-production-deployment)
- [Contributing](#-contributing)

---

## ✨ Features

- 🏢 **Multi-tenant Architecture** - Complete data isolation using PostgreSQL Row-Level Security
- 📄 **Smart Document Processing** - Parse PDF, DOCX, TXT files into searchable chunks
- 🔍 **Vector Search** - ChromaDB-powered semantic search with tenant isolation
- 🤖 **AI Answer Generation** - OpenAI GPT-4 powered answers with citations
- ✅ **Human-in-the-Loop** - Approve, reject, or edit AI-generated answers
- 📊 **Audit Trail** - Complete version history of all answer modifications
- 🔐 **Secure API Keys** - Fernet-encrypted storage of user OpenAI keys
- 🎨 **Modern UI** - React + TypeScript + Tailwind with 3D loading animations
- ⚡ **Real-time Updates** - Live progress tracking during processing
- 🔄 **Async Processing** - Celery-powered background jobs for scalability

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Dashboard  │  │   Document   │  │   Question   │       │
│  │             │  │    Upload    │  │  Generator   │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │    API     │  │   Celery   │  │    RAG     │            │
│  │  Routes    │  │   Worker   │  │  Service   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└───────┬──────────────┬─────────────────┬───────────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Redis   │ │   ChromaDB   │
│     (RLS)    │ │ (Queue)  │ │  (Vectors)   │
└──────────────┘ └──────────┘ └──────────────┘
```

**Flow:**
1. User uploads documents → Celery processes → Chunks stored in PostgreSQL + Vectors in ChromaDB
2. User asks question → RAG retrieves relevant chunks → OpenAI generates answer with citations
3. User reviews → Approve/Edit → Saved with version history

---

## 🚀 Quick Setup (Copy-Paste Commands)

### Prerequisites

You only need these installed:
- **Docker** and **Docker Compose** ([Install Docker](https://docs.docker.com/get-docker/))
- **Python 3.11+** (to generate encryption key)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))

---

### Step 1: Clone/Download the Project

```bash
# If using Git
git clone https://github.com/abrarbinrofique/AI-Powered-Document-Q-A-System.git
cd "Doc Analyzer"

# Or if you have a ZIP file, extract it and cd into it
```

---

### Step 2: Generate Encryption Key

Copy-paste this command to generate a Fernet encryption key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Copy the output** - you'll need it in the next step.

Example output: `a0H07YOiGE6x2hC4sBYOlsG6BosGxDDMhmXMBegXp_g=`

---

### Step 3: Create Environment File

```bash
# Copy the example file
cp .env.example .env
```

Now **edit the `.env` file** and replace the values:

```bash
# Use any text editor (nano, vim, or VS Code)
nano .env
```

Replace these two values:

```env
DB_PASSWORD=YourSecurePassword123!
FERNET_KEY=a0H07YOiGE6x2hC4sBYOlsG6BosGxDDMhmXMBegXp_g=
```

- `DB_PASSWORD`: Any strong password you want (for PostgreSQL)
- `FERNET_KEY`: Paste the key from Step 2

Save and exit (`Ctrl+X`, then `Y`, then `Enter` in nano).

---

### Step 4: Start the Application

```bash
# Start all services with Docker
docker-compose up --build
```

**Wait 2-3 minutes** for all services to start. You'll see logs from:
- PostgreSQL database
- Redis
- ChromaDB
- Backend API
- Frontend
- Celery worker

When ready, you'll see:
```
frontend_1  | VITE ready in XXX ms
api_1       | Uvicorn running on http://0.0.0.0:8000
```

---

### Step 5: Access the Application

Open your browser and go to:

**🌐 http://localhost:3000**

You should see the DDQ Agent interface!

---

### Step 6: Configure Your OpenAI API Key

1. **First time only**: You'll see a modal asking for an API key
2. Enter your OpenAI API key (starts with `sk-...`)
3. Click **"Validate & Save"**
4. The system will verify and encrypt your key

**Note**: Each user provides their own API key through the UI. Keys are encrypted and stored securely.

---

### Step 7: Create Your First Project

**Option A: Using the UI (Recommended)**

1. Click **"+ Create New Project"** button
2. Enter:
   - **Project Name**: e.g., "Q1 2024 Due Diligence"
   - **Description**: e.g., "Due diligence for Series A investors"
   - **OpenAI API Key**: Your API key (if not already configured)
3. Click **"Create Project"**

**Option B: Using API**

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2024 Due Diligence",
    "description": "Due diligence for Series A investors"
  }'
```

---

### Step 8: Upload Documents

1. **Select your project** from the dropdown
2. Go to **"📄 Upload Documents"** tab
3. Click the file input and select PDF/DOCX/TXT files
4. Click **"📤 Upload Documents"**
5. Wait for processing (you'll see a 3D animation)

**Supported formats**: PDF, DOCX, DOC, TXT

---

### Step 9: Generate Answers

1. Go to **"🤖 Generate Answers"** tab
2. Enter a question, for example:
   - "What is the company's revenue?"
   - "Who are the key executives?"
   - "What are the main risk factors?"
3. Click **"Generate Answer"**
4. Wait for AI processing (you'll see a 3D animation)
5. Review the generated answer with citations

---

### Step 10: Review & Approve Answers

1. Go to **"📚 Question History"** tab
2. Click on any question to see its answer
3. Review the answer and citations
4. Choose an action:
   - **✓ Approve**: Accept the answer
   - **✗ Reject**: Reject the answer
   - **✏️ Edit**: Modify the answer before approving

All changes are tracked in the audit trail!

---

## 🎯 That's It! You're Running!

### What You Can Access:

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **ChromaDB**: http://localhost:8001

---

## 🛑 Stop the Application

To stop all services:

```bash
# Press Ctrl+C in the terminal where docker-compose is running
# Or in a new terminal:
docker-compose down
```

To restart:

```bash
docker-compose up
```

**Your data persists** in Docker volumes, so your projects/documents remain intact!

---

## 📖 Usage Guide

### Complete Workflow Example

Here's a typical workflow for processing a DDQ:

#### 1. **Prepare Your Documents**

Gather all relevant documents:
- Company pitch deck (PDF)
- Financial statements (PDF/DOCX)
- Security policies (DOCX/TXT)
- Product documentation (PDF)
- Previous DDQ responses (DOCX)

#### 2. **Create Project & Upload**

```bash
# Create a project via UI or API
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp - Series A DDQ",
    "description": "Due diligence for Acme Corp Series A funding"
  }'
```

Upload all documents through the UI. Wait for processing (typically 30-60 seconds per document).

#### 3. **Ask Questions**

Enter questions one by one:

```
1. What is the company's current annual recurring revenue (ARR)?
2. Who are the founders and what are their backgrounds?
3. What security certifications does the company have?
4. Describe the company's data retention policy.
5. What are the top 3 business risks?
```

#### 4. **Review Generated Answers**

For each answer:
1. Read the AI-generated response
2. Check citations to verify sources
3. Look at confidence scores
4. Decide: Approve / Edit / Reject

#### 5. **Edit & Refine**

If needed, edit answers to:
- Add more context
- Clarify language
- Combine multiple sources
- Add disclaimers

#### 6. **Export Results**

Use the API to export approved answers:

```bash
# Get all approved answers for a project
curl http://localhost:8000/api/v1/projects/{project_id}/answers?status=approved
```

### Common Operations

#### Delete a Document

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}
```

#### Update API Key

1. Go to Settings (if available in UI)
2. Or use API:

```bash
curl -X POST http://localhost:8000/api/v1/settings/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-new-key-here"
  }'
```

#### View Question History

```bash
# Get all questions for a project
curl http://localhost:8000/api/v1/projects/{project_id}/questions

# Get specific answer details
curl http://localhost:8000/api/v1/answers/{answer_id}
```

### Best Practices

✅ **DO:**
- Upload high-quality, text-based documents
- Ask specific, clear questions
- Always review AI answers before approving
- Use descriptive project names
- Keep documents up-to-date

❌ **DON'T:**
- Upload scanned images without OCR
- Ask vague or ambiguous questions
- Blindly approve all answers without review
- Upload confidential data without proper security
- Ignore citation sources

---

## 📖 API Documentation

Interactive API documentation with all endpoints:

**Swagger UI**: http://localhost:8000/docs

Try out API endpoints directly from your browser!

---

## 🔒 Security Features

### API Key Management
- ✓ Users provide their own OpenAI API keys through UI
- ✓ Keys are encrypted with **Fernet** before database storage
- ✓ Keys are validated with real OpenAI request before accepting
- ✓ Keys are decrypted **only** when needed for processing
- ✓ Users can update/delete keys anytime

### Multi-Tenant Isolation
- ✓ **Row-Level Security (RLS)** on all PostgreSQL tables
- ✓ Tenant-specific ChromaDB collections
- ✓ Tenant context set on every request
- ✓ **Complete data isolation** between tenants
- ✓ Zero data leakage across projects

### Audit Trail
- ✓ All answer edits create versions
- ✓ Change tracking with timestamps
- ✓ User attribution for all changes
- ✓ Complete history of modifications

## Database Schema

The system uses 9 core tables:

1. `tenants` - Tenant management
2. `api_key_configs` - Encrypted API keys
3. `projects` - DDQ projects
4. `documents` - Source documents
5. `document_chunks` - Text chunks with metadata
6. `questions` - DDQ questions
7. `answers` - Generated answers
8. `answer_citations` - Links to source chunks
9. `answer_versions` - Audit trail

---

## 🛠️ Technology Stack

### Backend
| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | REST API framework | Latest |
| **SQLAlchemy** | ORM for PostgreSQL | 2.0+ |
| **PostgreSQL** | Primary database with RLS | 15 |
| **ChromaDB** | Vector database for embeddings | 0.4.24 |
| **Celery** | Async task queue | Latest |
| **Redis** | Message broker & cache | 7 |
| **OpenAI** | Embeddings & LLM | GPT-4/GPT-3.5 |
| **Cryptography** | API key encryption | Latest |

### Frontend
| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI framework | 18 |
| **TypeScript** | Type safety | Latest |
| **Vite** | Build tool & dev server | Latest |
| **TanStack Query** | Data fetching & caching | v5 |
| **Tailwind CSS** | Utility-first CSS | v3 |
| **Axios** | HTTP client | Latest |

---

## 💻 Development (Without Docker)

If you want to develop locally without Docker:

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- ChromaDB

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export DATABASE_URL="postgresql://ddquser:password@localhost:5432/ddqdb"
export REDIS_URL="redis://localhost:6379/0"
export FERNET_KEY="your-fernet-key-here"

# 5. Initialize database (run init.sql manually in PostgreSQL)
psql -U ddquser -d ddqdb -f init.sql

# 6. Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. In a new terminal, run Celery worker
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

Backend will run at: **http://localhost:8000**

---

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env.local

# 4. Run development server
npm run dev
```

Frontend will run at: **http://localhost:5173** (or 3000)

---

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Run specific test file
cd backend
pytest tests/test_api.py -v

# Run with coverage
cd backend
pytest --cov=app tests/
```

---

## 🏗️ Project Structure

```
Doc Analyzer/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── database.py    # Database connection
│   │   ├── celery_app.py  # Celery configuration
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   ├── init.sql           # Database schema
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.tsx        # Main app component
│   │   ├── components/    # React components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── QuestionGenerator.tsx
│   │   │   └── AnswerReview.tsx
│   │   └── index.css      # Global styles + animations
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml     # Docker orchestration
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

---

## 🚀 Production Deployment

### Security Checklist

- [ ] Use **strong passwords** (16+ characters, mixed case, numbers, symbols)
- [ ] Generate a **unique FERNET_KEY** for production
- [ ] Configure **CORS** properly (whitelist only your domains)
- [ ] Use **HTTPS** for all connections (setup SSL certificates)
- [ ] Enable **database backups** (daily automated backups)
- [ ] Set up **monitoring** for Celery workers
- [ ] Configure **rate limiting** on API endpoints
- [ ] Set up **log aggregation** (e.g., ELK stack)
- [ ] Use **environment-specific .env files**
- [ ] Enable **database connection pooling**
- [ ] Set up **health checks** for all services
- [ ] Configure **firewall rules** (restrict database access)

### Recommended Production Setup

```bash
# Use production-grade WSGI server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Use process manager for Celery
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Use NGINX as reverse proxy
# Configure SSL/TLS certificates
# Set up load balancing if needed
```

### Environment Variables for Production

```env
# Production database
DATABASE_URL=postgresql://user:password@db-host:5432/dbname

# Production Redis
REDIS_URL=redis://redis-host:6379/0

# Strong encryption key
FERNET_KEY=<generate-new-key-for-production>

# CORS origins
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Optional: Sentry for error tracking
SENTRY_DSN=your-sentry-dsn
```

---

## ❓ Frequently Asked Questions (FAQ)

### Q: Do I need my own OpenAI API key?

**A:** Yes, each user provides their own OpenAI API key through the UI. Keys are encrypted and stored securely. This ensures cost control and data privacy.

---

### Q: What file formats are supported?

**A:** Currently supported formats:
- PDF (.pdf)
- Word Documents (.docx, .doc)
- Text files (.txt)

---

### Q: How much does it cost to run?

**A:**
- **OpenAI API**: Pay-per-use (embeddings + GPT completions)
  - Embeddings: ~$0.0001 per 1K tokens
  - GPT-4: ~$0.03 per 1K tokens
- **Infrastructure**: Free for development (Docker on localhost)
- **Production**: Depends on your hosting (AWS, GCP, Azure, etc.)

---

### Q: Can I use a different LLM provider?

**A:** Currently optimized for OpenAI, but you can modify the code to support:
- Anthropic Claude
- Cohere
- Azure OpenAI
- Local models (Llama, Mistral via Ollama)

---

### Q: How is my data isolated from other users?

**A:** Multi-tenant isolation via:
1. **Row-Level Security (RLS)** on PostgreSQL tables
2. **Tenant-specific ChromaDB collections**
3. **Tenant context** set on every database query
4. **Complete data isolation** - users cannot see each other's data

---

### Q: Can I delete my data?

**A:** Yes! You can:
- Delete individual documents
- Delete projects (which deletes all associated data)
- Delete your API key
- Request complete account deletion

---

### Q: What's the maximum file size?

**A:** Default limits (can be adjusted in code):
- **Max file size**: 50 MB per file
- **Max files per upload**: 10 files
- **Total project size**: Unlimited (limited by disk space)

---

### Q: How accurate are the generated answers?

**A:** Accuracy depends on:
- **Quality of source documents** (clear, well-structured)
- **Relevance of documents** to the question
- **LLM model used** (GPT-4 > GPT-3.5)
- **Chunk size and overlap** settings

Always review generated answers before approval!

---

### Q: Can I run this offline?

**A:** Partially:
- **Frontend & Backend**: Yes, can run locally
- **OpenAI API**: No, requires internet connection
- **Alternative**: Use local LLMs (Ollama) with code modifications

---

## 📈 Roadmap

Future enhancements planned:

- [ ] Support for more file formats (Excel, CSV, HTML)
- [ ] Multi-language support (i18n)
- [ ] Advanced RAG techniques (hybrid search, re-ranking)
- [ ] Integration with Azure OpenAI
- [ ] Support for local LLMs (Ollama, LM Studio)
- [ ] Excel export of Q&A
- [ ] Batch question upload (CSV/Excel)
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

---

## 🔧 Troubleshooting

### ❌ Problem: "Cannot connect to database"

**Solution:**

```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs db

# If needed, restart just the database
docker-compose restart db
```

**Check**: Make sure `DB_PASSWORD` in `.env` is set correctly.

---

### ❌ Problem: "Invalid API key" when creating project

**Causes:**
- API key doesn't start with `sk-`
- API key is invalid or expired
- API key has no credits

**Solution:**

1. Verify your key at: https://platform.openai.com/api-keys
2. Check your usage: https://platform.openai.com/usage
3. Try entering the key again in the UI

---

### ❌ Problem: Documents stuck in "Processing" status

**Solution:**

```bash
# Check Celery worker logs
docker-compose logs worker

# Check API logs
docker-compose logs api

# Restart the worker
docker-compose restart worker
```

**Common causes:**
- API key not configured
- File format not supported (must be PDF, DOCX, or TXT)
- File too large (check backend logs for errors)

---

### ❌ Problem: Frontend shows "Cannot connect to API"

**Solution:**

```bash
# Check if backend is running
curl http://localhost:8000/health

# View API logs
docker-compose logs api

# Restart backend
docker-compose restart api
```

---

### ❌ Problem: Port already in use

**Error**: `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:**

```bash
# Find what's using the port (example: port 3000)
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yml
# Change "3000:3000" to "3001:3000" for frontend
```

---

### ❌ Problem: "FERNET_KEY is not set" error

**Solution:**

1. Make sure `.env` file exists:
   ```bash
   ls -la .env
   ```

2. Generate a new key:
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Add it to `.env`:
   ```bash
   FERNET_KEY=<your-generated-key>
   ```

4. Restart services:
   ```bash
   docker-compose down
   docker-compose up
   ```

---

### 🧹 Problem: Need to reset everything

**Complete cleanup** (removes all data):

```bash
# Stop all containers
docker-compose down

# Remove all volumes (⚠️ DELETES ALL DATA)
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
docker-compose up --build
```

---

### 📊 Useful Debug Commands

```bash
# View all container logs
docker-compose logs

# View specific service logs
docker-compose logs api
docker-compose logs worker
docker-compose logs frontend
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f api

# Check container status
docker-compose ps

# Check Docker volumes
docker volume ls

# Access PostgreSQL directly
docker-compose exec db psql -U ddquser -d ddqdb

# Access backend container shell
docker-compose exec api bash

# Check API health
curl http://localhost:8000/health

# List all projects via API
curl http://localhost:8000/api/v1/projects
```

---

### 💡 Still Having Issues?

1. **Check all services are running**:
   ```bash
   docker-compose ps
   ```
   All services should show "Up" status.

2. **View logs for errors**:
   ```bash
   docker-compose logs | grep -i error
   ```

3. **Restart everything**:
   ```bash
   docker-compose restart
   ```

4. **Full rebuild** (if nothing else works):
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This means you can:
- ✓ Use commercially
- ✓ Modify the code
- ✓ Distribute
- ✓ Use privately

---

## 💬 Support & Community

### Need Help?

1. **Check the FAQ**: [Frequently Asked Questions](#-frequently-asked-questions-faq)
2. **Read Troubleshooting**: [Troubleshooting Guide](#-troubleshooting)
3. **Check API Docs**: http://localhost:8000/docs
4. **Open an Issue**: [GitHub Issues](https://github.com/your-repo/issues)

### Contact

- **Report Bugs**: Open a GitHub issue with detailed steps to reproduce
- **Feature Requests**: Open a GitHub issue with use case description
- **Security Issues**: Email security@yourdomain.com (do not open public issues)

---

## 🌟 Star History

If you find this project useful, please consider giving it a star on GitHub! ⭐

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Celery Documentation](https://docs.celeryq.dev/)

---

<div align="center">

**Made with ❤️ for automating due diligence**

[⬆ Back to Top](#-ddq-agent---ai-powered-due-diligence-automation)

</div>
# AI-Powered-Document-Q-A-System
