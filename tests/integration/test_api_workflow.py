
import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database.models import Booking
from app.services.llm_service import llm_service


def test_complete_api_workflow(monkeypatch, db_session):
    """
    Test the complete workflow through actual HTTP endpoints:

    1. Upload a document.
    2. Ask a question using RAG.
    3. Continue the conversation.
    4. Extract interview booking details.
    5. Confirm and save the booking.
    6. Verify duplicate confirmation does not create duplicates.

    PostgreSQL, Redis, Qdrant, and embeddings are real.
    Gemini responses are mocked.
    """

    session_id = str(uuid4())

    # --------------------------------------------------
    # Mock Gemini responses only.
    # --------------------------------------------------

    def mock_generate_text(prompt: str) -> str:

        # Booking extraction prompt
        if "User messages:" in prompt and "booking_requested" in prompt:
            return json.dumps({
                "booking_requested": True,
                "name": "Ruby Sah",
                "email": "ruby@example.com",
                "interview_date": "2026-12-15",
                "interview_time": "14:30"
            })

        # Follow-up question rewriting
        if "Standalone search query:" in prompt:
            return (
                "Python programming paradigms: "
                "object-oriented and functional programming"
            )

        # RAG answer generation
        if "Retrieved document context:" in prompt:
            return (
                "According to the uploaded document, Python "
                "supports object-oriented programming and "
                "functional programming."
            )

        raise AssertionError(
            "Unexpected Gemini prompt received during test."
        )

    monkeypatch.setattr(
        llm_service,
        "generate_text",
        mock_generate_text
    )

    with TestClient(app) as client:

        # --------------------------------------------------
        # STEP 1: Upload a TXT document.
        # --------------------------------------------------

        document_content = (
            "Python is a high-level programming language. "
            "It supports object-oriented programming and "
            "functional programming. "
            "Python is widely used in data science and "
            "machine learning."
        )

        upload_response = client.post(
            "/documents/upload",
            params={"strategy": "fixed"},
            files={
                "file": (
                    "python_guide.txt",
                    document_content.encode("utf-8"),
                    "text/plain"
                )
            }
        )

        assert upload_response.status_code == 200

        uploaded_document = upload_response.json()

        assert uploaded_document["status"] == "completed"
        assert uploaded_document["total_chunks"] > 0

        document_id = uploaded_document["document_id"]

        # --------------------------------------------------
        # STEP 2: Ask the first question.
        # --------------------------------------------------

        first_chat_response = client.post(
            "/chat/",
            json={
                "question": (
                    "Which programming paradigms "
                    "does Python support?"
                ),
                "session_id": session_id,
                "document_id": document_id
            }
        )

        assert first_chat_response.status_code == 200

        first_chat = first_chat_response.json()

        assert first_chat["session_id"] == session_id
        assert first_chat["answer"]
        assert len(first_chat["sources"]) > 0

        assert (
            first_chat["sources"][0]["document_id"]
            == document_id
        )

        # --------------------------------------------------
        # STEP 3: Ask a follow-up question.
        # This verifies conversation history and rewriting.
        # --------------------------------------------------

        second_chat_response = client.post(
            "/chat/",
            json={
                "question": (
                    "I also want to book an interview. "
                    "My name is Ruby Sah and my email is "
                    "ruby@example.com. Please schedule it "
                    "for December 15, 2026 at 2:30 PM."
                ),
                "session_id": session_id,
                "document_id": document_id
            }
        )

        assert second_chat_response.status_code == 200

        second_chat = second_chat_response.json()

        assert second_chat["session_id"] == session_id
        assert second_chat["answer"]
        assert second_chat["search_query"]

        # --------------------------------------------------
        # STEP 4: Extract booking details.
        # Extraction must NOT save the booking yet.
        # --------------------------------------------------

        extraction_response = client.post(
            "/bookings/extract",
            json={
                "session_id": session_id,
                "timezone_name": "Asia/Kathmandu"
            }
        )

        assert extraction_response.status_code == 200

        extraction = extraction_response.json()

        assert extraction["booking_ready"] is True
        assert extraction["missing_fields"] == []

        booking_details = extraction["booking"]

        assert booking_details["name"] == "Ruby Sah"
        assert booking_details["email"] == "ruby@example.com"
        assert booking_details["interview_date"] == "2026-12-15"
        assert booking_details["interview_time"] == "14:30"

        # Verify extraction alone did not save a booking.
        existing_booking = (
            db_session.query(Booking)
            .filter(Booking.session_id == session_id)
            .first()
        )

        assert existing_booking is None

        # --------------------------------------------------
        # STEP 5: Explicitly confirm the booking.
        # --------------------------------------------------

        confirmation_payload = {
            "session_id": session_id,
            "booking": booking_details
        }

        confirmation_response = client.post(
            "/bookings/confirm",
            json=confirmation_payload
        )

        assert confirmation_response.status_code == 200

        confirmation = confirmation_response.json()

        assert confirmation["status"] == "pending"
        assert confirmation["session_id"] == session_id
        assert confirmation["booking_id"] > 0

        booking_id = confirmation["booking_id"]

        # --------------------------------------------------
        # STEP 6: Verify booking persistence.
        # --------------------------------------------------

        saved_booking = (
            db_session.query(Booking)
            .filter(Booking.session_id == session_id)
            .first()
        )

        assert saved_booking is not None
        assert saved_booking.id == booking_id
        assert saved_booking.name == "Ruby Sah"
        assert saved_booking.email == "ruby@example.com"
        assert saved_booking.status == "pending"

        # --------------------------------------------------
        # STEP 7: Confirm again and verify no duplicate.
        # --------------------------------------------------

        repeated_confirmation = client.post(
            "/bookings/confirm",
            json=confirmation_payload
        )

        assert repeated_confirmation.status_code == 200

        repeated_result = repeated_confirmation.json()

        assert repeated_result["booking_id"] == booking_id

        booking_count = (
            db_session.query(Booking)
            .filter(Booking.session_id == session_id)
            .count()
        )

        assert booking_count == 1
