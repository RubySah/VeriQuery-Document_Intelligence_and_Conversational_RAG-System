from uuid import uuid5, NAMESPACE_URL

from qdrant_client.models import PointStruct
from sqlalchemy.orm import Session

from app.database.models import Document
from app.database.qdrant import qdrant_client
from app.services.document_extraction import extract_text
from app.services.chunking_service import create_chunks
from app.services.embedding_service import embedding_service
from app.core.config import settings


def ingest_document(
    db: Session,
    filename: str,
    file_bytes: bytes,
    strategy: str = "fixed"
) -> dict:

    extension = filename.lower().rsplit(".", 1)[-1]

    if extension not in {"pdf", "txt"}:
        raise ValueError("Only PDF and TXT files are supported.")

    # 1. Create the database record.
    document = Document(
        filename=filename,
        file_type=extension,
        status="processing"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        # 2. Extract text.
        extracted_text = extract_text(
            file_bytes,
            f".{extension}"
        )

        # 3. Split text into chunks.
        chunks = create_chunks(
            extracted_text,
            strategy=strategy
        )

        if not chunks:
            raise ValueError("Document produced no text chunks.")

        # 4. Generate embeddings.
        embeddings = embedding_service.generate_embeddings(chunks)

        # 5. Prepare Qdrant points.
        points = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            point_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"document-{document.id}-chunk-{index}"
                )
            )

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "document_id": document.id,
                        "filename": filename,
                        "chunk_index": index,
                        "text": chunk
                    }
                )
            )

        # 6. Store vectors in Qdrant.
        qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points
        )

        # 7. Mark document as completed.
        document.status = "completed"
        document.total_chunks = len(chunks)

        db.commit()

        return {
            "document_id": document.id,
            "filename": filename,
            "status": document.status,
            "total_chunks": len(chunks),
            "chunking_strategy": strategy
        }

    except Exception:
        db.rollback()

        failed_document = db.get(Document, document.id)

        if failed_document:
            failed_document.status = "failed"
            db.commit()

        raise