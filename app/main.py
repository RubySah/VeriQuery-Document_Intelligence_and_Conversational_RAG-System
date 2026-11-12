
from fastapi import FastAPI

app = FastAPI(
    title="Palm Mind AI - RAG Backend",
    description="Document ingestion and conversational RAG API",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Palm Mind AI RAG Backend is running",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
