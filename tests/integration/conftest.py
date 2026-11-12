
import os

import pytest


# Never silently fall back to the development .env configuration.
required_variables = [
    "TEST_DATABASE_URL",
    "TEST_REDIS_URL",
    "TEST_QDRANT_COLLECTION",
]

missing_variables = [
    name for name in required_variables
    if not os.environ.get(name)
]

if missing_variables:
    raise RuntimeError(
        "Missing integration test environment variables: "
        + ", ".join(missing_variables)
    )


# Override application settings before importing application modules.
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ["REDIS_URL"] = os.environ["TEST_REDIS_URL"]
os.environ["QDRANT_COLLECTION"] = os.environ[
    "TEST_QDRANT_COLLECTION"
]


from sqlalchemy.orm import sessionmaker
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings
from app.database.database import Base, engine
from app.database import models
from app.database.qdrant import qdrant_client
from app.services.chat_memory import chat_memory


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create tables in the dedicated integration test database.

    The database must be created separately before running tests.
    """

    if "palmind_test_db" not in settings.DATABASE_URL:
        raise RuntimeError(
            "Refusing to run integration tests against a "
            "database whose URL does not contain "
            "'palmind_test_db'."
        )

    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """
    Provide a real SQLAlchemy session.
    """

    Session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )

    db = Session()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_external_test_services():
    """
    Reset only the dedicated Redis DB and Qdrant collection
    before each integration test.
    """

    # Redis DB 1 is reserved for integration tests.
    chat_memory.redis.flushdb()

    collection = settings.QDRANT_COLLECTION

    if qdrant_client.collection_exists(collection):
        qdrant_client.delete_collection(collection)

    qdrant_client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

    yield

