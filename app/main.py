from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.bookings import router as bookings_router

app = FastAPI(
    title="Palm Mind RAG Backend",
    description="Document ingestion and conversational RAG API",
    version="1.0.0"
)

app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(bookings_router)

@app.get("/")
def root():
    return {"message": "Palm Mind RAG Backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}