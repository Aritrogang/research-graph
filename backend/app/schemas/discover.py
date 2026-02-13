"""Schemas for the topic discovery endpoint."""

from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="Scientific topic to search for")
    count: int = Field(default=5, ge=1, le=10, description="Number of papers to find")


class PaperSummary(BaseModel):
    id: str
    arxiv_id: str
    title: str
    authors: list[str]
    year: int | None
    abstract: str


class DiscoverResponse(BaseModel):
    topic: str
    papers: list[PaperSummary]
    center_paper_id: str
