import pytest

from app.services.chunking_service import (
    fixed_size_chunking,
    paragraph_chunking,
    create_chunks,
)


def test_fixed_size_chunking():
    text = "abcdefghij"

    chunks = fixed_size_chunking(
        text,
        chunk_size=5,
        overlap=2
    )

    assert chunks == ["abcde", "defgh", "ghij"]


def test_fixed_chunking_without_overlap():
    text = "abcdefghij"

    chunks = fixed_size_chunking(
        text,
        chunk_size=5,
        overlap=0
    )

    assert chunks == ["abcde", "fghij"]


def test_fixed_chunking_invalid_size():
    with pytest.raises(ValueError, match="positive"):
        fixed_size_chunking("hello", chunk_size=0)


def test_fixed_chunking_invalid_overlap():
    with pytest.raises(ValueError, match="Overlap"):
        fixed_size_chunking("hello", chunk_size=5, overlap=5)


def test_paragraph_chunking():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

    chunks = paragraph_chunking(text, chunk_size=100)

    assert len(chunks) == 1
    assert "First paragraph." in chunks[0]
    assert "Second paragraph." in chunks[0]
    assert "Third paragraph." in chunks[0]


def test_paragraph_chunking_respects_size():
    text = "First paragraph.\n\nSecond paragraph."

    chunks = paragraph_chunking(text, chunk_size=18)

    assert len(chunks) == 2
    assert chunks[0] == "First paragraph."
    assert chunks[1] == "Second paragraph."


def test_long_paragraph_is_split():
    text = "abcdefghij"

    chunks = paragraph_chunking(text, chunk_size=4)

    assert chunks == ["abcd", "efgh", "ij"]


def test_create_chunks_fixed_strategy():
    chunks = create_chunks(
        "abcdefghij",
        strategy="fixed",
        chunk_size=5,
        overlap=0
    )

    assert chunks == ["abcde", "fghij"]


def test_create_chunks_paragraph_strategy():
    chunks = create_chunks(
        "First paragraph.\n\nSecond paragraph.",
        strategy="paragraph",
        chunk_size=100
    )

    assert len(chunks) == 1


def test_invalid_chunking_strategy():
    with pytest.raises(ValueError, match="Invalid strategy"):
        create_chunks("hello", strategy="invalid")


def test_empty_text_returns_no_chunks():
    assert fixed_size_chunking("") == []
    assert paragraph_chunking("") == []
