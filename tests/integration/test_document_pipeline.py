import pymupdf

from app.database.models import Document
from app.services.document_service import ingest_document
from app.services.retrieval_service import retrieve_chunks


def test_document_ingestion_and_retrieval(db_session):
    filename = "integration_test.txt"

    content = (
        "Machine learning is a branch of artificial intelligence. "
        "It enables computers to learn patterns from data. "
        "Supervised learning uses labeled training data. "
        "Unsupervised learning discovers patterns without labels."
    )

    # Step 1: Ingest a real document.
    result = ingest_document(
        db=db_session,
        filename=filename,
        file_bytes=content.encode("utf-8"),
        strategy="fixed"
    )

    assert result["status"] == "completed"
    assert result["filename"] == filename
    assert result["total_chunks"] > 0

    document_id = result["document_id"]

    # Step 2: Verify PostgreSQL metadata.
    document = db_session.get(Document, document_id)

    assert document is not None
    assert document.filename == filename
    assert document.file_type == "txt"
    assert document.status == "completed"
    assert document.total_chunks == result["total_chunks"]

    # Step 3: Retrieve chunks using a real embedding.
    chunks = retrieve_chunks(
        question="What is supervised learning?",
        top_k=3,
        document_id=document_id
    )

    assert len(chunks) > 0

    # Step 4: Verify retrieved data belongs to our document.
    for chunk in chunks:
        assert chunk["document_id"] == document_id
        assert chunk["filename"] == filename
        assert isinstance(chunk["text"], str)
        assert chunk["text"].strip()
        assert isinstance(chunk["score"], float)


def test_pdf_ingestion_and_retrieval(db_session):
    pdf = pymupdf.open()
    page = pdf.new_page()

    source_text = (
        "Artificial intelligence enables machines "
        "to perform tasks that typically require "
        "human intelligence. Machine learning is "
        "a subset of artificial intelligence."
    )

    # Use insert_textbox so text wraps within the page.
    page.insert_textbox(
        pymupdf.Rect(72, 72, 520, 300),
        source_text,
        fontsize=11
    )

    pdf_bytes = pdf.tobytes()
    pdf.close()

    # Verify that the generated PDF contains the complete text.
    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    ) as generated_pdf:
        extracted_text = generated_pdf[0].get_text()

    assert "machine learning" in extracted_text.lower()

    # Ingest the PDF.
    result = ingest_document(
        db=db_session,
        filename="ai_integration_test.pdf",
        file_bytes=pdf_bytes,
        strategy="fixed"
    )

    assert result["status"] == "completed"
    assert result["total_chunks"] >= 1

    document_id = result["document_id"]

    # Retrieve document chunks.
    chunks = retrieve_chunks(
        question="What is machine learning?",
        top_k=5,
        document_id=document_id
    )

    assert chunks

    assert all(
        chunk["document_id"] == document_id
        for chunk in chunks
    )

    retrieved_text = " ".join(
        chunk["text"] for chunk in chunks
    ).lower()

    assert "artificial intelligence" in retrieved_text
    assert "machine learning" in retrieved_text