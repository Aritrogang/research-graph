"""Pydantic schemas for the graph endpoint."""

from typing import Any

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str = "paperNode"
    position: dict[str, float]
    data: dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
