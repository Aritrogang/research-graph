"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "ResearchGraph"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://researchgraph:researchgraph_secret@localhost:5432/researchgraph_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-ada-002"
    openai_chat_model: str = "gpt-4o-mini"

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Vector search settings
    similarity_threshold: float = 0.7
    max_context_chunks: int = 5

    # Storage
    paper_storage_path: str = "/app/storage/papers"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
