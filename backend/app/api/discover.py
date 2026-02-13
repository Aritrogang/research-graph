"""Discover endpoint: search arXiv for papers on a topic and add them to the database."""

import json
import uuid

import arxiv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.discover import DiscoverRequest, DiscoverResponse, PaperSummary

router = APIRouter()


def _deterministic_id(arxiv_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, arxiv_id))


@router.post("", response_model=DiscoverResponse)
async def discover_papers(request: DiscoverRequest, db: AsyncSession = Depends(get_db)):
    """Search arXiv for papers on a topic, insert them, and build cross-references."""

    # Search arXiv
    client = arxiv.Client()
    search = arxiv.Search(
        query=request.topic,
        max_results=request.count,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = list(client.results(search))
    if not results:
        raise HTTPException(status_code=404, detail=f"No papers found for topic '{request.topic}'")

    papers_out: list[PaperSummary] = []
    arxiv_ids_in_batch: list[str] = []

    for result in results:
        aid = result.entry_id.split("/")[-1]
        # Strip version suffix (e.g. "2301.00001v2" -> "2301.00001")
        if "v" in aid:
            aid = aid.rsplit("v", 1)[0]
        arxiv_ids_in_batch.append(aid)

    # Insert each paper
    for i, result in enumerate(results):
        aid = arxiv_ids_in_batch[i]
        paper_id = _deterministic_id(aid)
        authors = [a.name for a in result.authors]
        categories = list(result.categories) if result.categories else []
        year = result.published.year if result.published else None

        # Build cross-references: other papers in this batch as references
        other_ids = [x for x in arxiv_ids_in_batch if x != aid]

        # Upsert paper
        await db.execute(
            text(
                'INSERT INTO papers (id, arxiv_id, title, abstract, authors, categories, '
                'published_date, pdf_url, "references", cited_by, is_processed) '
                "VALUES (:id, :aid, :title, :abstract, :authors::jsonb, :cats::jsonb, "
                ":pub_date, :pdf_url, :refs::jsonb, '[]'::jsonb, false) "
                "ON CONFLICT (arxiv_id) DO UPDATE SET "
                'title = EXCLUDED.title, abstract = EXCLUDED.abstract, '
                'authors = EXCLUDED.authors, "references" = EXCLUDED."references"'
            ),
            {
                "id": paper_id,
                "aid": aid,
                "title": result.title,
                "abstract": result.summary,
                "authors": json.dumps(authors),
                "cats": json.dumps(categories),
                "pub_date": result.published,
                "pdf_url": result.pdf_url,
                "refs": json.dumps(other_ids),
            },
        )

        papers_out.append(
            PaperSummary(
                id=paper_id,
                arxiv_id=aid,
                title=result.title,
                authors=authors[:3],
                year=year,
                abstract=result.summary[:300] + "..." if len(result.summary) > 300 else result.summary,
            )
        )

    await db.commit()

    return DiscoverResponse(
        topic=request.topic,
        papers=papers_out,
        center_paper_id=arxiv_ids_in_batch[0],
    )
