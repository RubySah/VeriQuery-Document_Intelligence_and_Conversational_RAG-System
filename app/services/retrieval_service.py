from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.database.qdrant import qdrant_client
from app.core.config import settings
from app.services.embedding_service import embedding_service


def retrieve_chunks(
    question: str,
    top_k: int = 5,
    document_id: int | None = None
) -> list[dict]:

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20.")

    # 1. Convert the question into a vector.
    query_vector = embedding_service.generate_embedding(question)

    # 2. Optionally filter results by document ID.
    query_filter = None

    if document_id is not None:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )

    # 3. Search Qdrant.
    search_results = qdrant_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True
    ).points

    # 4. Format the results.
    retrieved_chunks = []

    for result in search_results:
        payload = result.payload or {}

        retrieved_chunks.append({
            "document_id": payload.get("document_id"),
            "filename": payload.get("filename"),
            "chunk_index": payload.get("chunk_index"),
            "text": payload.get("text"),
            "score": result.score
        })

    return retrieved_chunks