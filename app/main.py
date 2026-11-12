from fastapi import FastAPI

from app.api.documents import router as document_router


app = FastAPI(
    title="Palm Mind AI - RAG Backend",
    description="Document ingestion and conversational RAG API",
    version="1.0.0"
)


app.include_router(document_router)


@app.get("/")
def root():
    return {
        "message": "Palm Mind AI RAG Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }