
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.genai.errors import APIError, ServerError
from redis.exceptions import RedisError

from app.api import chat as chat_api


# Create a minimal application containing only the chat router.
app = FastAPI()
app.include_router(chat_api.router)

client = TestClient(app)


@pytest.fixture
def valid_payload():
    return {
        "question": "What is Python?",
        "session_id": str(uuid4()),
        "document_id": 1
    }


def test_chat_success(monkeypatch, valid_payload):
    expected_result = {
        "session_id": valid_payload["session_id"],
        "question": "What is Python?",
        "search_query": "What is Python?",
        "answer": "Python is a programming language.",
        "sources": [
            {
                "document_id": 1,
                "filename": "python.pdf",
                "chunk_index": 0,
                "score": 0.95
            }
        ]
    }

    process_mock = lambda **kwargs: expected_result

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        process_mock
    )

    response = client.post(
        "/chat/",
        json=valid_payload
    )

    assert response.status_code == 200
    assert response.json() == expected_result


def test_chat_creates_session_when_session_id_missing(
    monkeypatch
):
    captured = {}

    def fake_process_chat(**kwargs):
        captured.update(kwargs)

        return {
            "session_id": str(uuid4()),
            "question": kwargs["question"],
            "search_query": kwargs["question"],
            "answer": "Test answer.",
            "sources": []
        }

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        fake_process_chat
    )

    response = client.post(
        "/chat/",
        json={
            "question": "What is Python?"
        }
    )

    assert response.status_code == 200
    assert captured["session_id"] is None


@pytest.mark.parametrize(
    "question",
    ["", "   "]
)
def test_chat_rejects_empty_question(question):
    response = client.post(
        "/chat/",
        json={
            "question": question
        }
    )

    assert response.status_code == 422


def test_chat_rejects_invalid_session_id():
    response = client.post(
        "/chat/",
        json={
            "question": "What is Python?",
            "session_id": "not-a-valid-uuid"
        }
    )

    assert response.status_code == 422


def test_chat_rejects_invalid_document_id():
    response = client.post(
        "/chat/",
        json={
            "question": "What is Python?",
            "document_id": -1
        }
    )

    assert response.status_code == 422


def test_chat_maps_value_error_to_400(
    monkeypatch,
    valid_payload
):
    def raise_value_error(**kwargs):
        raise ValueError("Question cannot be empty.")

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        raise_value_error
    )

    response = client.post(
        "/chat/",
        json=valid_payload
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Question cannot be empty."
    )


class FakeServerError(ServerError):
    def __init__(self):
        Exception.__init__(
            self,
            "Gemini service unavailable"
        )


class FakeAPIError(APIError):
    def __init__(self):
        Exception.__init__(
            self,
            "Gemini API request failed"
        )


def test_chat_maps_gemini_server_error_to_503(
    monkeypatch,
    valid_payload
):
    def raise_server_error(**kwargs):
        raise FakeServerError()

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        raise_server_error
    )

    response = client.post(
        "/chat/",
        json=valid_payload
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in (
        response.json()["detail"]
    )


def test_chat_maps_gemini_api_error_to_502(
    monkeypatch,
    valid_payload
):
    def raise_api_error(**kwargs):
        raise FakeAPIError()

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        raise_api_error
    )

    response = client.post(
        "/chat/",
        json=valid_payload
    )

    assert response.status_code == 502
    assert "AI provider" in response.json()["detail"]


def test_chat_maps_redis_error_to_503(
    monkeypatch,
    valid_payload
):
    def raise_redis_error(**kwargs):
        raise RedisError("Redis connection failed")

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        raise_redis_error
    )

    response = client.post(
        "/chat/",
        json=valid_payload
    )

    assert response.status_code == 503
    assert "Conversation memory" in (
        response.json()["detail"]
    )


def test_chat_maps_unexpected_error_to_500(
    monkeypatch,
    valid_payload
):
    def raise_unexpected_error(**kwargs):
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr(
        chat_api,
        "process_chat",
        raise_unexpected_error
    )

    response = client.post(
        "/chat/",
        json=valid_payload
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Chat processing failed. Check server logs."
    )
