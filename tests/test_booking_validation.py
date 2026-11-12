from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.services.booking_validation import validate_booking_details


TIMEZONE = "Asia/Kathmandu"


def get_future_booking_date():
    future = datetime.now(ZoneInfo(TIMEZONE)) + timedelta(days=5)
    return future.date().isoformat()


def valid_booking():
    return {
        "name": "Ruby Sah",
        "email": "ruby@example.com",
        "interview_date": get_future_booking_date(),
        "interview_time": "14:30",
    }


def test_valid_booking_details():
    details, missing = validate_booking_details(
        valid_booking(),
        TIMEZONE
    )

    assert missing == []
    assert details["name"] == "Ruby Sah"
    assert details["email"] == "ruby@example.com"
    assert details["interview_time"] == "14:30"
    assert details["timezone_name"] == TIMEZONE


def test_missing_required_fields():
    booking = {
        "name": "Ruby Sah",
        "email": "",
        "interview_date": None,
        "interview_time": "unknown",
    }

    details, missing = validate_booking_details(
        booking,
        TIMEZONE
    )

    assert "email" in missing
    assert "interview_date" in missing
    assert "interview_time" in missing


def test_invalid_email():
    booking = valid_booking()
    booking["email"] = "invalid-email"

    with pytest.raises(ValueError, match="Invalid email"):
        validate_booking_details(booking, TIMEZONE)


def test_past_interview_date():
    booking = valid_booking()
    booking["interview_date"] = "2000-01-01"

    with pytest.raises(ValueError, match="must be in the future"):
        validate_booking_details(booking, TIMEZONE)


def test_invalid_interview_date():
    booking = valid_booking()
    booking["interview_date"] = "20-11-2026"

    with pytest.raises(ValueError, match="Invalid interview date or time"):
        validate_booking_details(booking, TIMEZONE)


def test_invalid_interview_time():
    booking = valid_booking()
    booking["interview_time"] = "25:90"

    with pytest.raises(ValueError, match="Invalid interview date or time"):
        validate_booking_details(booking, TIMEZONE)


def test_name_exceeds_maximum_length():
    booking = valid_booking()
    booking["name"] = "A" * 256

    with pytest.raises(ValueError, match="Name is too long"):
        validate_booking_details(booking, TIMEZONE)
