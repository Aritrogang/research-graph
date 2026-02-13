"""Pydantic schemas for the chat endpoint."""

from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    paper_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    source: Literal["cache", "llm"]
    context_used: list[str]
