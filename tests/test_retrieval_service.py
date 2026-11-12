
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services import retrieval_service


def setup_retrieval_service(monkeypatch):
    qdrant = Mock()
    embeddings = Mock()

    monkeypatch.setattr(retrieval_service, "qdrant_client", qdrant)
    monkeypatch.setattr(retrieval_service, "embedding_service", embeddings)

    embeddings.generate_embedding.return_value = [0.1] * 384

    qdrant.query_points.return_value = SimpleNamespace(
        points=[
            SimpleNamespace(
                payload={
                    "document_id": 42,
                    "filename": "resume.pdf",
                    "chunk_index": 0,
                    "text": "Python developer with machine learning experience."
                },
                score=0.89
            ),
            SimpleNamespace(
                payload={
                    "document_id": 42,
                    "filename": "resume.pdf",
                    "chunk_index": 1,
                    "text": "Experience with FastAPI and SQL databases."
                },
                score=0.82
            )
        ]
    )

    return qdrant, embeddings


def test_successful_semantic_retrieval(monkeypatch):
    qdrant, embeddings = setup_retrieval_service(monkeypatch)

    results = retrieval_service.retrieve_chunks(
        question="What is the candidate's Python experience?",
        top_k=5
    )

    assert len(results) == 2
    assert results[0]["document_id"] == 42
    assert results[0]["filename"] == "resume.pdf"
    assert results[0]["chunk_index"] == 0
    assert "Python" in results[0]["text"]
    assert results[0]["score"] == 0.89

    embeddings.generate_embedding.assert_called_once_with(
        "What is the candidate's Python experience?"
    )

    qdrant.query_points.assert_called_once()


def test_retrieval_with_document_filter(monkeypatch):
    qdrant, _ = setup_retrieval_service(monkeypatch)

    retrieval_service.retrieve_chunks(
        question="Tell me about Python.",
        document_id=42
    )

    query_filter = qdrant.query_points.call_args.kwargs["query_filter"]

    assert query_filter is not None
    assert query_filter.must[0].key == "document_id"
    assert query_filter.must[0].match.value == 42


def test_empty_question_rejected(monkeypatch):
    qdrant, embeddings = setup_retrieval_service(monkeypatch)

    with pytest.raises(ValueError, match="Question cannot be empty"):
        retrieval_service.retrieve_chunks("   ")

    embeddings.generate_embedding.assert_not_called()
    qdrant.query_points.assert_not_called()


@pytest.mark.parametrize("top_k", [0, -1, 21, 100])
def test_invalid_top_k_rejected(monkeypatch, top_k):
    qdrant, embeddings = setup_retrieval_service(monkeypatch)

    with pytest.raises(ValueError, match="top_k"):
        retrieval_service.retrieve_chunks(
            question="Find relevant information",
            top_k=top_k
        )

    embeddings.generate_embedding.assert_not_called()
    qdrant.query_points.assert_not_called()


def test_empty_retrieval_results(monkeypatch):
    qdrant, _ = setup_retrieval_service(monkeypatch)

    qdrant.query_points.return_value.points = []

    results = retrieval_service.retrieve_chunks(
        question="Information not present in documents"
    )

    assert results == []


def test_retrieval_handles_missing_payload(monkeypatch):
    qdrant, _ = setup_retrieval_service(monkeypatch)

    qdrant.query_points.return_value.points = [
        SimpleNamespace(
            payload=None,
            score=0.25
        )
    ]

    results = retrieval_service.retrieve_chunks(
        question="Search for information"
    )

    assert results == [
        {
            "document_id": None,
            "filename": None,
            "chunk_index": None,
            "text": None,
            "score": 0.25
        }
    ]
