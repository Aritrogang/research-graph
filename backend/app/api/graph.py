"""Graph endpoint: returns citation network as React Flow nodes/edges."""

import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse

router = APIRouter()


def _arrange_satellites(center_x: float, center_y: float, count: int, radius: float = 300) -> list[dict[str, float]]:
    """Distribute satellite nodes evenly in a circle around the center."""
    positions = []
    for i in range(count):
        angle = (2 * math.pi * i) / max(count, 1)
        positions.append({
            "x": center_x + radius * math.cos(angle),
            "y": center_y + radius * math.sin(angle),
        })
    return positions


@router.get("/{paper_id}", response_model=GraphResponse)
async def get_graph(paper_id: str, db: AsyncSession = Depends(get_db)):
    """Return citation graph for a paper as React Flow nodes and edges."""

    # Fetch the center paper
    result = await db.execute(
        text(
            "SELECT id, arxiv_id, title, authors, published_date, references, cited_by "
            "FROM papers WHERE id::text = :pid OR arxiv_id = :pid"
        ),
        {"pid": paper_id},
    )
    center = result.mappings().first()
    if not center:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")

    center_id = str(center["id"])
    ref_ids: list[str] = center["references"] or []
    cited_by_ids: list[str] = center["cited_by"] or []
    related_arxiv_ids = list(set(ref_ids + cited_by_ids))

    # Center node
    year = center["published_date"].year if center["published_date"] else "N/A"
    nodes: list[GraphNode] = [
        GraphNode(
            id=center_id,
            type="paperNode",
            position={"x": 0, "y": 0},
            data={
                "title": center["title"],
                "arxiv_id": center["arxiv_id"],
                "year": year,
                "authors": center["authors"][:3] if center["authors"] else [],
                "isCenter": True,
            },
        )
    ]
    edges: list[GraphEdge] = []

    if not related_arxiv_ids:
        return GraphResponse(nodes=nodes, edges=edges)

    # Fetch satellite papers
    satellites = await db.execute(
        text(
            "SELECT id, arxiv_id, title, authors, published_date "
            "FROM papers WHERE arxiv_id = ANY(:ids)"
        ),
        {"ids": related_arxiv_ids},
    )
    sat_rows = satellites.mappings().fetchall()
    positions = _arrange_satellites(0, 0, len(sat_rows))

    for i, sat in enumerate(sat_rows):
        sat_id = str(sat["id"])
        sat_year = sat["published_date"].year if sat["published_date"] else "N/A"
        nodes.append(
            GraphNode(
                id=sat_id,
                type="paperNode",
                position=positions[i],
                data={
                    "title": sat["title"],
                    "arxiv_id": sat["arxiv_id"],
                    "year": sat_year,
                    "authors": sat["authors"][:3] if sat["authors"] else [],
                    "isCenter": False,
                },
            )
        )

        # Determine edge direction
        if sat["arxiv_id"] in ref_ids:
            # Center paper references this satellite
            edges.append(GraphEdge(id=f"e-{center_id}-{sat_id}", source=center_id, target=sat_id))
        if sat["arxiv_id"] in cited_by_ids:
            # Satellite cites the center paper
            edges.append(GraphEdge(id=f"e-{sat_id}-{center_id}", source=sat_id, target=center_id, animated=True))

    return GraphResponse(nodes=nodes, edges=edges)
