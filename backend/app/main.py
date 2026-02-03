from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import settings, documents, answers, projects
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DDQ Agent API",
    description="Multi-tenant Due Diligence Questionnaire Agent with RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(settings.router)
app.include_router(documents.router)
app.include_router(answers.router)
app.include_router(projects.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ddq-agent-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DDQ Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
