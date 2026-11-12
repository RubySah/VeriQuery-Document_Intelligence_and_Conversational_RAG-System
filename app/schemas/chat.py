
from pydantic import BaseModel, Field

from uuid import UUID

class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=5000
    )

    session_id: UUID | None = None

    document_id: int | None = Field(
        default=None,
        gt=0
    )


class SourceResponse(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    session_id: str
    question: str
    search_query: str
    answer: str
    sources: list[SourceResponse]
