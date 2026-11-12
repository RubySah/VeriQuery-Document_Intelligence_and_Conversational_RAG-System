
from uuid import uuid4

from sqlalchemy import func

from app.database.models import Booking
from app.schemas.booking import BookingDetails
from app.services.booking_service import confirm_booking


def test_booking_persistence_and_duplicate_prevention(
    db_session
):
    session_id = str(uuid4())

    booking_details = BookingDetails(
        name="Integration Test User",
        email="integration@example.com",
        interview_date="2026-11-20",
        interview_time="14:30",
        timezone_name="Asia/Kathmandu"
    )

    # Step 1: Save the booking.
    first_result = confirm_booking(
        db=db_session,
        session_id=session_id,
        booking_details=booking_details
    )

    assert first_result["status"] == "pending"
    assert first_result["session_id"] == session_id

    # Step 2: Verify the record in PostgreSQL.
    booking = (
        db_session.query(Booking)
        .filter(Booking.session_id == session_id)
        .first()
    )

    assert booking is not None
    assert booking.name == "Integration Test User"
    assert booking.email == "integration@example.com"
    assert str(booking.interview_date) == "2026-11-20"
    assert str(booking.interview_time)[:5] == "14:30"
    assert booking.timezone_name == "Asia/Kathmandu"
    assert booking.status == "pending"

    original_booking_id = booking.id

    # Step 3: Confirm again with the same session ID.
    second_result = confirm_booking(
        db=db_session,
        session_id=session_id,
        booking_details=booking_details
    )

    assert second_result["booking_id"] == original_booking_id

    # Step 4: Ensure there is still only one booking.
    booking_count = (
        db_session.query(func.count(Booking.id))
        .filter(Booking.session_id == session_id)
        .scalar()
    )

    assert booking_count == 1

