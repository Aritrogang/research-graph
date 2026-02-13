"""SQLAlchemy ORM models matching the init.sql schema."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    arxiv_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[dict] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    categories: Mapped[dict] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    published_date = mapped_column(TIMESTAMP(timezone=True))
    updated_date = mapped_column(TIMESTAMP(timezone=True))
    pdf_url: Mapped[str | None] = mapped_column(Text)
    local_pdf_path: Mapped[str | None] = mapped_column(Text)
    references: Mapped[dict] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    cited_by: Mapped[dict] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    is_processed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    chunk_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    updated_at = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    chunks: Mapped[list["PaperChunk"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    cache_entries: Mapped[list["ChatCache"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class PaperChunk(Base):
    __tablename__ = "paper_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    paper: Mapped["Paper"] = relationship(back_populates="chunks")


class ChatCache(Base):
    __tablename__ = "chat_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    context_chunk_ids: Mapped[dict] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    model_used: Mapped[str | None] = mapped_column(String(64))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    hit_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    last_accessed_at = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    paper: Mapped["Paper"] = relationship(back_populates="cache_entries")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    arxiv_id: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), server_default=text("'pending'"))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at = mapped_column(TIMESTAMP(timezone=True))
    completed_at = mapped_column(TIMESTAMP(timezone=True))
    created_at = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
