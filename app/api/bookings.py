import logging

from fastapi import APIRouter, Depends, HTTPException
from google.genai.errors import ServerError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.booking import (
    BookingExtractRequest,
    BookingExtractResponse,
    BookingConfirmRequest,
    BookingConfirmResponse,
)
from app.services.booking_service import (
    prepare_booking,
    confirm_booking,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


@router.post(
    "/extract",
    response_model=BookingExtractResponse
)
def extract_booking(request: BookingExtractRequest):
    """
    Extract interview booking details from the conversation
    associated with the given session ID.

    Does not save the booking.
    The user must explicitly confirm the extracted details.
    """

    try:
        result = prepare_booking(
            session_id=str(request.session_id),
            timezone_name=request.timezone_name
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ServerError:
        logger.exception("Gemini booking extraction failed")

        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please retry."
        )

    except Exception:
        logger.exception("Booking extraction failed")

        raise HTTPException(
            status_code=500,
            detail="Booking extraction failed. Check server logs."
        )


@router.post(
    "/confirm",
    response_model=BookingConfirmResponse
)
def save_booking(
    request: BookingConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Save or update booking details after explicit user confirmation.
    """

    try:
        result = confirm_booking(
            db=db,
            session_id=str(request.session_id),
            booking_details=request.booking
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("Booking confirmation failed")

        raise HTTPException(
            status_code=500,
            detail="Booking confirmation failed. Check server logs."
        )