
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


class SourceResponse(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    session_id: UUID
    question: str
    search_query: str
    answer: str
    sources: list[SourceResponse] = Field(
        default_factory=list
    )
