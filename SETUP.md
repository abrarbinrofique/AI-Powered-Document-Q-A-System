# Quick Setup Guide - Copy & Paste Commands

This is a simplified setup guide. For detailed documentation, see [README.md](README.md).

---

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ installed
- OpenAI API key

---

## Setup in 5 Minutes

### 1. Generate Encryption Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Copy the output!** You'll need it in step 3.

---

### 2. Create Environment File

```bash
cp .env.example .env
```

---

### 3. Edit .env File

Open `.env` in any text editor and replace these values:

```env
DB_PASSWORD=YourStrongPassword123!
FERNET_KEY=paste_key_from_step1_here
```

Save the file.

---

### 4. Start Everything

```bash
docker-compose up --build
```

Wait 2-3 minutes. You'll see:
```
frontend_1  | VITE ready
api_1       | Uvicorn running
```

---

### 5. Open in Browser

Go to: **http://localhost:3000**

Done! 🎉

---

## First Time Usage

1. Enter your OpenAI API key (starts with `sk-`)
2. Click "Create New Project"
3. Upload documents (PDF/DOCX/TXT)
4. Ask questions
5. Review & approve answers

---

## Useful Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose up

# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# Complete reset (deletes all data)
docker-compose down -v
```

---

## Troubleshooting

### Problem: Port already in use

```bash
# Find what's using port 3000
lsof -i :3000

# Kill it
kill -9 <PID>
```

### Problem: Services not starting

```bash
# Rebuild everything
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Problem: Need to check logs

```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs api
docker-compose logs worker
docker-compose logs frontend
```

---

## Need More Help?

See [README.md](README.md) for:
- Detailed documentation
- Architecture overview
- Development guide
- FAQ
- Production deployment

---

**That's it! You're ready to go.** 🚀
