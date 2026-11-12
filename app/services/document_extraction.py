import pymupdf


def extract_text(file_bytes: bytes, file_extension: str) -> str:
    """
    Extract text from a PDF or TXT file.
    """

    if file_extension == ".pdf":
        with pymupdf.open(stream=file_bytes, filetype="pdf") as pdf:
            pages = [
                page.get_text()
                for page in pdf
            ]

        text = "\n".join(pages)

    elif file_extension == ".txt":
        text = file_bytes.decode("utf-8-sig", errors="replace")

    else:
        raise ValueError("Unsupported file format")

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable text found in the document."
        )

    return text