"""Discover endpoint: search arXiv for papers and build a Gemini-ordered reading path."""

import json
import re
import uuid
from typing import List

import arxiv
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.schemas.discover import DiscoverRequest, DiscoverResponse, PaperSummary

router = APIRouter()
settings = get_settings()

genai.configure(api_key=settings.gemini_api_key)


def _deterministic_id(arxiv_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, arxiv_id))


def _strip_version(entry_id: str) -> str:
    """Extract arXiv ID and strip version suffix."""
    aid = entry_id.split("/")[-1]
    if "v" in aid:
        aid = aid.rsplit("v", 1)[0]
    return aid


def _order_papers_with_gemini(
    topic: str,
    background: str,
    papers: List[dict],
) -> List[dict]:
    """Use Gemini to order papers by reading difficulty for the given background."""

    paper_descriptions = []
    for i, p in enumerate(papers, 1):
        abstract_snippet = p["abstract"][:400]
        paper_descriptions.append(
            f'{i}. [arXiv:{p["arxiv_id"]}] "{p["title"]}" ({p["year"] or "N/A"})\n'
            f"   Abstract: {abstract_snippet}..."
        )

    prompt = (
        f'You are an academic advisor. A student with the background "{background}" '
        f'wants to learn about "{topic}".\n\n'
        f"Here are {len(papers)} research papers found on this topic:\n\n"
        + "\n\n".join(paper_descriptions)
        + "\n\n"
        "Create an optimal reading path from most foundational/accessible to most "
        "advanced/specialized, considering the student's background level.\n\n"
        "Return ONLY a JSON array (no markdown, no commentary). Each element must have:\n"
        '- "arxiv_id": the paper\'s arXiv ID exactly as shown above\n'
        '- "difficulty": one of "beginner", "intermediate", "advanced"\n'
        '- "reason": one sentence explaining why this paper is at this position\n\n'
        "Order the array from first-to-read to last-to-read.\n\n"
        "Consider:\n"
        "- Foundational/survey papers should come before papers that build on them\n"
        "- The student's background determines what counts as beginner\n"
        "- Newer papers that depend on older results should come later\n"
        "- Papers introducing basic concepts before papers using advanced techniques\n"
    )

    model = genai.GenerativeModel(
        settings.gemini_chat_model,
        generation_config=genai.GenerationConfig(temperature=0.2, max_output_tokens=2048),
    )
    response = model.generate_content(prompt)
    response_text = response.text.strip()

    # Try to parse JSON from response (handle markdown code blocks)
    json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group()

    try:
        ordering = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: return papers in chronological order
        return _fallback_ordering(papers)

    # Map the ordering back to our papers
    arxiv_to_paper = {p["arxiv_id"]: p for p in papers}
    ordered = []
    seen = set()

    for i, item in enumerate(ordering):
        aid = item.get("arxiv_id", "")
        if aid in arxiv_to_paper and aid not in seen:
            seen.add(aid)
            paper = arxiv_to_paper[aid]
            paper["reading_order"] = i + 1
            paper["difficulty"] = item.get("difficulty", "intermediate")
            paper["reason"] = item.get("reason", "")
            ordered.append(paper)

    # Add any papers that Gemini missed
    for p in papers:
        if p["arxiv_id"] not in seen:
            p["reading_order"] = len(ordered) + 1
            p["difficulty"] = "intermediate"
            p["reason"] = "Not ranked by advisor"
            ordered.append(p)

    return ordered


def _fallback_ordering(papers: List[dict]) -> List[dict]:
    """Order papers chronologically (oldest first) as a fallback."""
    sorted_papers = sorted(papers, key=lambda p: p["year"] or 9999)
    for i, p in enumerate(sorted_papers):
        p["reading_order"] = i + 1
        p["difficulty"] = (
            "beginner" if i < len(sorted_papers) // 3
            else "advanced" if i >= 2 * len(sorted_papers) // 3
            else "intermediate"
        )
        p["reason"] = "Ordered by publication year"
    return sorted_papers


@router.post("", response_model=DiscoverResponse)
async def discover_papers(request: DiscoverRequest, db: AsyncSession = Depends(get_db)):
    """Search arXiv for papers on a topic, order them by difficulty, and build a reading path."""

    # ── 1. Search arXiv ──────────────────────────────────────────────
    client = arxiv.Client()
    search = arxiv.Search(
        query=request.topic,
        max_results=request.count,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = list(client.results(search))
    if not results:
        raise HTTPException(status_code=404, detail=f"No papers found for topic '{request.topic}'")

    # ── 2. Build paper list ──────────────────────────────────────────
    papers_raw: List[dict] = []
    for result in results:
        aid = _strip_version(result.entry_id)
        paper_id = _deterministic_id(aid)
        authors = [a.name for a in result.authors]
        year = result.published.year if result.published else None

        papers_raw.append({
            "id": paper_id,
            "arxiv_id": aid,
            "title": result.title,
            "authors": authors,
            "year": year,
            "abstract": result.summary,
            "categories": list(result.categories) if result.categories else [],
            "published": result.published,
            "pdf_url": result.pdf_url,
        })

    # ── 3. Order papers with Gemini ──────────────────────────────────
    try:
        ordered_papers = _order_papers_with_gemini(
            request.topic, request.background, papers_raw
        )
    except Exception:
        ordered_papers = _fallback_ordering(papers_raw)

    # ── 4. Insert papers into DB ─────────────────────────────────────
    all_arxiv_ids = [p["arxiv_id"] for p in ordered_papers]

    for paper in ordered_papers:
        other_ids = [x for x in all_arxiv_ids if x != paper["arxiv_id"]]
        await db.execute(
            text(
                'INSERT INTO papers (id, arxiv_id, title, abstract, authors, categories, '
                'published_date, pdf_url, "references", cited_by, is_processed) '
                "VALUES (:id, :aid, :title, :abstract, CAST(:authors AS jsonb), CAST(:cats AS jsonb), "
                ":pub_date, :pdf_url, CAST(:refs AS jsonb), CAST('[]' AS jsonb), false) "
                "ON CONFLICT (arxiv_id) DO UPDATE SET "
                'title = EXCLUDED.title, abstract = EXCLUDED.abstract, '
                'authors = EXCLUDED.authors, "references" = EXCLUDED."references"'
            ),
            {
                "id": paper["id"],
                "aid": paper["arxiv_id"],
                "title": paper["title"],
                "abstract": paper["abstract"],
                "authors": json.dumps(paper["authors"]),
                "cats": json.dumps(paper["categories"]),
                "pub_date": paper["published"],
                "pdf_url": str(paper["pdf_url"]) if paper["pdf_url"] else None,
                "refs": json.dumps(other_ids),
            },
        )

    await db.commit()

    # ── 5. Build response ────────────────────────────────────────────
    papers_out = [
        PaperSummary(
            id=p["id"],
            arxiv_id=p["arxiv_id"],
            title=p["title"],
            authors=p["authors"][:3],
            year=p["year"],
            abstract=p["abstract"][:500] + "..." if len(p["abstract"]) > 500 else p["abstract"],
            reading_order=p["reading_order"],
            difficulty=p["difficulty"],
            reason=p["reason"],
        )
        for p in ordered_papers
    ]

    return DiscoverResponse(
        topic=request.topic,
        background=request.background,
        papers=papers_out,
    )
