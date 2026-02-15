"""Pydantic schemas for the graph endpoint."""

from typing import Any, Dict, List

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str = "paperNode"
    position: Dict[str, float]
    data: Dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
