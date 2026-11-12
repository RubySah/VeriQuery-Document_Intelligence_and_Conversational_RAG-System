
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

def validate_booking_details(
    details: dict,
    timezone_name: str
) -> tuple[dict, list[str]]:

    required_fields = [
        "name",
        "email",
        "interview_date",
        "interview_time"
    ]

    cleaned = {}
    missing_fields = []

    for field in required_fields:
        value = details.get(field)

        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().lower() in {"null", "none", "unknown"}
        ):
            missing_fields.append(field)
        else:
            cleaned[field] = value.strip()

    if missing_fields:
        return cleaned, missing_fields

    if len(cleaned["name"]) > 255:
        raise ValueError("Name is too long.")

    if not re.fullmatch(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        cleaned["email"]
    ):
        raise ValueError("Invalid email address.")

    try:
        interview_date = date.fromisoformat(
            cleaned["interview_date"]
        )

        interview_time = datetime.strptime(
            cleaned["interview_time"],
            "%H:%M"
        ).time()

        timezone = ZoneInfo(timezone_name)

    except ValueError as error:
        raise ValueError(
            "Invalid interview date or time."
        ) from error

    candidate_datetime = datetime.combine(
        interview_date,
        interview_time,
        tzinfo=timezone
    )

    if candidate_datetime <= datetime.now(timezone):
        raise ValueError(
            "Interview date and time must be in the future."
        )

    cleaned["interview_date"] = interview_date.isoformat()
    cleaned["interview_time"] = interview_time.strftime("%H:%M")
    cleaned["timezone_name"] = timezone_name

    return cleaned, []
