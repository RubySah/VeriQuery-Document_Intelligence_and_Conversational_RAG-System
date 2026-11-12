from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_timezone_name(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Invalid timezone name.")

    return value


class BookingExtractRequest(BaseModel):
    session_id: UUID
    timezone_name: str = Field(
        default="Asia/Kathmandu",
        min_length=1,
        max_length=100
    )

    @field_validator("timezone_name")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return validate_timezone_name(value)


class BookingDetails(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    interview_date: str
    interview_time: str
    timezone_name: str = Field(
        default="Asia/Kathmandu",
        min_length=1,
        max_length=100
    )

    @field_validator("timezone_name")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return validate_timezone_name(value)


class BookingExtractResponse(BaseModel):
    booking_ready: bool
    message: str
    missing_fields: list[str] = Field(default_factory=list)
    booking: BookingDetails | None = None


class BookingConfirmRequest(BaseModel):
    session_id: UUID
    booking: BookingDetails


class BookingConfirmResponse(BaseModel):
    booking_id: int
    session_id: str
    status: str
    message: str