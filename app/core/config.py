
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GEMINI_API_KEY: str

    DATABASE_URL: str
    REDIS_URL: str

    QDRANT_URL: str
    QDRANT_COLLECTION: str

    EMBEDDING_MODEL: str

    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
