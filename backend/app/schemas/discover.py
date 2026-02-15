"""Schemas for the topic discovery endpoint."""

from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="Scientific topic to search for")
    background: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Student's background level, e.g. 'freshman in college'",
    )
    count: int = Field(default=5, ge=3, le=10, description="Number of papers to find")


class PaperSummary(BaseModel):
    id: str
    arxiv_id: str
    title: str
    authors: list[str]
    year: int | None
    abstract: str
    reading_order: int = Field(..., description="1-based reading order position")
    difficulty: str = Field(..., description="beginner, intermediate, or advanced")
    reason: str = Field(..., description="Why this paper is at this position")


class DiscoverResponse(BaseModel):
    topic: str
    background: str
    papers: list[PaperSummary]
