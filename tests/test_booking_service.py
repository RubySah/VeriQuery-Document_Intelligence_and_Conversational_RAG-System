from datetime import datetime, timedelta
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.dialects import postgresql

from app.schemas.booking import BookingDetails
from app.services import booking_service


TIMEZONE = "Asia/Kathmandu"


def get_future_date():
    future = datetime.now(ZoneInfo(TIMEZONE)) + timedelta(days=5)
    return future.date().isoformat()


def valid_booking_data():
    return {
        "name": "Ruby Sah",
        "email": "ruby@example.com",
        "interview_date": get_future_date(),
        "interview_time": "14:30",
        "timezone_name": TIMEZONE,
    }


def test_extraction_without_booking_request(monkeypatch):
    monkeypatch.setattr(
        booking_service,
        "extract_booking_details",
        lambda session_id, timezone_name: {
            "booking_requested": False
        }
    )

    result = booking_service.prepare_booking(
        session_id="test-session",
        timezone_name=TIMEZONE
    )

    assert result["booking_ready"] is False
    assert result["booking"] is None


def test_extraction_with_missing_fields(monkeypatch):
    monkeypatch.setattr(
        booking_service,
        "extract_booking_details",
        lambda session_id, timezone_name: {
            "booking_requested": True,
            "name": "Ruby Sah",
            "email": None,
            "interview_date": None,
            "interview_time": None,
        }
    )

    result = booking_service.prepare_booking(
        session_id="test-session",
        timezone_name=TIMEZONE
    )

    assert result["booking_ready"] is False
    assert "email" in result["missing_fields"]
    assert "interview_date" in result["missing_fields"]
    assert "interview_time" in result["missing_fields"]


def test_successful_booking_extraction(monkeypatch):
    monkeypatch.setattr(
        booking_service,
        "extract_booking_details",
        lambda session_id, timezone_name: {
            "booking_requested": True,
            **valid_booking_data(),
        }
    )

    result = booking_service.prepare_booking(
        session_id="test-session",
        timezone_name=TIMEZONE
    )

    assert result["booking_ready"] is True
    assert result["missing_fields"] == []
    assert isinstance(result["booking"], BookingDetails)
    assert result["booking"].email == "ruby@example.com"


def test_confirm_booking_success():
    db = Mock()

    db_result = Mock()
    db_result.scalar_one.return_value = 1
    db.execute.return_value = db_result

    result = booking_service.confirm_booking(
        db=db,
        session_id="test-session",
        booking_details=BookingDetails(**valid_booking_data())
    )

    assert result["booking_id"] == 1
    assert result["session_id"] == "test-session"
    assert result["status"] == "pending"

    db.execute.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()

    # Verify the generated SQL uses PostgreSQL atomic upsert.
    statement = db.execute.call_args.args[0]
    compiled_sql = str(
        statement.compile(dialect=postgresql.dialect())
    )

    assert "ON CONFLICT" in compiled_sql
    assert "uq_bookings_session_id" in compiled_sql


def test_confirm_booking_rolls_back_on_database_error():
    db = Mock()
    db.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        booking_service.confirm_booking(
            db=db,
            session_id="test-session",
            booking_details=BookingDetails(**valid_booking_data())
        )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
