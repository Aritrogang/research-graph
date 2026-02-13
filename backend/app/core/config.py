"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "ResearchGraph"
    environment: str = "development"
    debug: bool = True

    # Frontend URL for CORS (set to your Vercel URL in production)
    frontend_url: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://researchgraph:researchgraph_secret@localhost:5432/researchgraph_db"

    @model_validator(mode="after")
    def fix_database_url(self):
        """Render provides postgres://, SQLAlchemy async needs postgresql+asyncpg://."""
        url = self.database_url
        if url.startswith("postgres://"):
            self.database_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            self.database_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Gemini
    gemini_api_key: str = ""
    gemini_embedding_model: str = "models/text-embedding-004"
    gemini_chat_model: str = "gemini-2.0-flash"

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
