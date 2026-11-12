import logging
from uuid import uuid5, NAMESPACE_URL

from qdrant_client.models import PointStruct, PointIdsList
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Document
from app.database.qdrant import qdrant_client
from app.services.document_extraction import extract_text
from app.services.chunking_service import create_chunks
from app.services.embedding_service import embedding_service


logger = logging.getLogger(__name__)


def ingest_document(
    db: Session,
    filename: str,
    file_bytes: bytes,
    strategy: str = "fixed"
) -> dict:
    """
    Extract, chunk, embed, and store a PDF or TXT document.

    Document metadata is stored in PostgreSQL, while
    document chunks and their embeddings are stored in Qdrant.
    """

    # 1. Validate file extension.
    extension = filename.lower().rsplit(".", 1)[-1]

    if extension not in {"pdf", "txt"}:
        raise ValueError("Only PDF and TXT files are supported.")

    # 2. Create the document record.
    document = Document(
        filename=filename,
        file_type=extension,
        status="processing"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    points = []
    vectors_stored = False

    try:
        # 3. Extract text from the uploaded document.
        extracted_text = extract_text(
            file_bytes,
            f".{extension}"
        )

        # 4. Split extracted text into chunks.
        chunks = create_chunks(
            extracted_text,
            strategy=strategy
        )

        if not chunks:
            raise ValueError(
                "Document produced no text chunks."
            )

        # 5. Generate embeddings for all chunks.
        embeddings = embedding_service.generate_embeddings(
            chunks
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding count does not match the number "
                "of document chunks."
            )

        # 6. Prepare Qdrant points.
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

        # 7. Store vectors in Qdrant.
        qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points
        )

        vectors_stored = True

        # 8. Mark document as completed in PostgreSQL.
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
        # 9. Roll back the current SQL transaction.
        db.rollback()

        # 10. Remove Qdrant vectors if they were already stored.
        if vectors_stored:
            try:
                qdrant_client.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    points_selector=PointIdsList(
                        points=[
                            point.id for point in points
                        ]
                    )
                )

            except Exception:
                logger.exception(
                    "Failed to clean up Qdrant vectors "
                    "for document %s",
                    document.id
                )

        # 11. Mark the document as failed in PostgreSQL.
        try:
            failed_document = db.get(
                Document,
                document.id
            )

            if failed_document:
                failed_document.status = "failed"
                db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to update document %s status to failed",
                document.id
            )

        # Preserve and re-raise the original exception.
        raise
