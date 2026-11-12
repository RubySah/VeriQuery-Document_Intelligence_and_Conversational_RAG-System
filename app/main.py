
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.bookings import router as bookings_router


app = FastAPI(
    title="Palm Mind RAG Backend",
    description=(
        "AI-powered document intelligence with "
        "conversational RAG and interview booking."
    ),
    version="1.0.0"
)

# Register API routers.
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(bookings_router)


# Resolve homepage relative to this file.
HOMEPAGE_FILE = (
    Path(__file__).resolve().parent
    / "templates"
    / "index.html"
)


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(
        path=HOMEPAGE_FILE,
        media_type="text/html"
    )


@app.get("/health")
def health():
    return {"status": "healthy"}
