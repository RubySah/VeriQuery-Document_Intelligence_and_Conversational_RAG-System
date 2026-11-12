
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services import document_service


class FakeDocument:
    def __init__(self, **kwargs):
        self.id = 42
        self.filename = kwargs["filename"]
        self.file_type = kwargs["file_type"]
        self.status = kwargs["status"]
        self.total_chunks = 0


def setup_document_service(monkeypatch):
    db = Mock()
    qdrant = Mock()
    embeddings = Mock()

    monkeypatch.setattr(document_service, "Document", FakeDocument)
    monkeypatch.setattr(document_service, "qdrant_client", qdrant)
    monkeypatch.setattr(document_service, "embedding_service", embeddings)

    monkeypatch.setattr(
        document_service,
        "extract_text",
        lambda file_bytes, extension: "Sample extracted document text."
    )

    monkeypatch.setattr(
        document_service,
        "create_chunks",
        lambda text, strategy: ["First chunk", "Second chunk"]
    )

    embeddings.generate_embeddings.return_value = [
        [0.1] * 384,
        [0.2] * 384
    ]

    db.get.return_value = None

    return db, qdrant, embeddings


def test_successful_document_ingestion(monkeypatch):
    db, qdrant, embeddings = setup_document_service(monkeypatch)

    result = document_service.ingest_document(
        db=db,
        filename="sample.txt",
        file_bytes=b"Sample document",
        strategy="fixed"
    )

    assert result["document_id"] == 42
    assert result["filename"] == "sample.txt"
    assert result["status"] == "completed"
    assert result["total_chunks"] == 2
    assert result["chunking_strategy"] == "fixed"

    db.add.assert_called_once()
    embeddings.generate_embeddings.assert_called_once()
    qdrant.upsert.assert_called_once()

    points = qdrant.upsert.call_args.kwargs["points"]

    assert len(points) == 2
    assert points[0].payload["document_id"] == 42
    assert points[0].payload["text"] == "First chunk"
    assert points[1].payload["chunk_index"] == 1

    assert db.commit.call_count == 2


def test_unsupported_file_rejected_before_database_write():
    db = Mock()

    with pytest.raises(
        ValueError,
        match="Only PDF and TXT files are supported"
    ):
        document_service.ingest_document(
            db=db,
            filename="sample.docx",
            file_bytes=b"content"
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_failed_ingestion_marks_document_failed(monkeypatch):
    db, qdrant, embeddings = setup_document_service(monkeypatch)

    document = FakeDocument(
        filename="broken.txt",
        file_type="txt",
        status="processing"
    )
    db.get.return_value = document

    def raise_extraction_error(file_bytes, extension):
        raise ValueError("Extraction failed")

    monkeypatch.setattr(
        document_service,
        "extract_text",
        raise_extraction_error
    )

    with pytest.raises(ValueError, match="Extraction failed"):
        document_service.ingest_document(
            db=db,
            filename="broken.txt",
            file_bytes=b"broken content"
        )

    assert document.status == "failed"
    db.rollback.assert_called_once()
    assert db.commit.call_count == 2
    qdrant.upsert.assert_not_called()


def test_embedding_count_mismatch_marks_document_failed(monkeypatch):
    db, qdrant, embeddings = setup_document_service(monkeypatch)

    document = FakeDocument(
        filename="sample.txt",
        file_type="txt",
        status="processing"
    )
    db.get.return_value = document

    # Two chunks, but only one embedding.
    embeddings.generate_embeddings.return_value = [
        [0.1] * 384
    ]

    with pytest.raises(
        ValueError,
        match="Embedding count does not match"
    ):
        document_service.ingest_document(
            db=db,
            filename="sample.txt",
            file_bytes=b"Sample document"
        )

    assert document.status == "failed"
    db.rollback.assert_called_once()
    qdrant.upsert.assert_not_called()


def test_qdrant_vectors_cleaned_up_if_database_commit_fails(
    monkeypatch
):
    db, qdrant, embeddings = setup_document_service(monkeypatch)

    document = FakeDocument(
        filename="sample.txt",
        file_type="txt",
        status="processing"
    )
    db.get.return_value = document

    # First commit creates the processing record.
    # Second commit fails after Qdrant upsert.
    # Third commit saves the failed status.
    db.commit.side_effect = [
        None,
        RuntimeError("Database commit failed"),
        None
    ]

    with pytest.raises(
        RuntimeError,
        match="Database commit failed"
    ):
        document_service.ingest_document(
            db=db,
            filename="sample.txt",
            file_bytes=b"Sample document"
        )

    qdrant.upsert.assert_called_once()
    qdrant.delete.assert_called_once()

    delete_args = qdrant.delete.call_args.kwargs
    assert delete_args["collection_name"] == (
        document_service.settings.QDRANT_COLLECTION
    )

    assert document.status == "failed"
    assert db.rollback.call_count == 1
