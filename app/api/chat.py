import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_chat

from google.genai.errors import ServerError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = process_chat(
            question=request.question,
            session_id=(
                str(request.session_id)
                if request.session_id
                else None
            ),
            document_id=request.document_id
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ServerError as error:
        logger.exception("Gemini API is temporarily unavailable")

        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please retry."
        )

    except Exception:
        logger.exception("Chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Chat processing failed. Check server logs."
        )
