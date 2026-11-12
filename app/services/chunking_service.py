import re


def fixed_size_chunking(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def paragraph_chunking(
    text: str,
    chunk_size: int = 1000
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        # Split unusually long paragraphs into smaller pieces.
        if len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(
                fixed_size_chunking(
                    paragraph,
                    chunk_size=chunk_size,
                    overlap=0
                )
            )
            continue

        if not current_chunk:
            current_chunk = paragraph

        elif len(current_chunk) + len(paragraph) + 2 <= chunk_size:
            current_chunk += "\n\n" + paragraph

        else:
            chunks.append(current_chunk)
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def create_chunks(
    text: str,
    strategy: str = "fixed",
    chunk_size: int = 1000,
    overlap: int = 150
) -> list[str]:

    if strategy == "fixed":
        return fixed_size_chunking(
            text,
            chunk_size,
            overlap
        )

    elif strategy == "paragraph":
        return paragraph_chunking(
            text,
            chunk_size
        )

    else:
        raise ValueError(
            "Invalid strategy. Choose 'fixed' or 'paragraph'."
        )