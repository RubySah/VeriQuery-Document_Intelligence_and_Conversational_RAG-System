from qdrant_client import QdrantClient, models

from app.core.config import settings


qdrant_client = QdrantClient(
    url=settings.QDRANT_URL
)


def create_collection():
    collection_name = settings.QDRANT_COLLECTION

    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

        print(f"Collection '{collection_name}' created successfully!")

    else:
        print(f"Collection '{collection_name}' already exists.")


if __name__ == "__main__":
    create_collection()