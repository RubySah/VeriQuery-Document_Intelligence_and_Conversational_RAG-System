import pymupdf
import pytest

from app.services.document_extraction import extract_text


def create_pdf(text: str) -> bytes:
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((50, 50), text)

    pdf_bytes = pdf.tobytes()
    pdf.close()

    return pdf_bytes


def test_extract_text_from_txt():
    content = "This is a sample document."

    result = extract_text(content.encode("utf-8"), ".txt")

    assert result == content


def test_extract_text_from_txt_with_bom():
    content = "\ufeffThis document contains a BOM."

    result = extract_text(content.encode("utf-8"), ".txt")

    assert result == "This document contains a BOM."


def test_extract_text_from_pdf():
    pdf_bytes = create_pdf("Hello from PDF document.")

    result = extract_text(pdf_bytes, ".pdf")

    assert "Hello from PDF document." in result


def test_unsupported_file_format():
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_text(b"some content", ".docx")


def test_empty_txt_file():
    with pytest.raises(ValueError, match="No readable text found"):
        extract_text(b"   ", ".txt")


def test_empty_pdf_file():
    pdf = pymupdf.open()
    pdf.new_page()  # Create a valid PDF page with no text.

    pdf_bytes = pdf.tobytes()
    pdf.close()

    with pytest.raises(ValueError, match="No readable text found"):
        extract_text(pdf_bytes, ".pdf")


def test_invalid_pdf_file():
    with pytest.raises(Exception):
        extract_text(b"not a valid pdf", ".pdf")


