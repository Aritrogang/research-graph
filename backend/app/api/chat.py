"""Chat endpoint: cached Q&A over research papers using RAG."""

import hashlib

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.api_core.exceptions import ResourceExhausted
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
settings = get_settings()

# Configure Gemini SDK once at module level
genai.configure(api_key=settings.gemini_api_key)


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode()).hexdigest()


def _get_embedding(text_input: str) -> list[float]:
    """Generate a 768-dim embedding using Gemini text-embedding-004."""
    result = genai.embed_content(
        model=settings.gemini_embedding_model,
        content=text_input,
        task_type="RETRIEVAL_QUERY",
    )
    return result["embedding"]


def _build_paper_context(paper_row) -> str:
    """Build a rich text context from all available paper metadata."""
    parts = []

    title = paper_row["title"] or "Unknown"
    parts.append(f"Title: {title}")

    arxiv_id = paper_row.get("arxiv_id", "")
    if arxiv_id:
        parts.append(f"arXiv ID: {arxiv_id}")

    authors = paper_row.get("authors") or []
    if authors:
        if isinstance(authors, str):
            parts.append(f"Authors: {authors}")
        else:
            parts.append(f"Authors: {', '.join(authors)}")
            parts.append(f"Number of authors: {len(authors)}")

    pub_date = paper_row.get("published_date")
    if pub_date:
        parts.append(f"Published: {pub_date}")

    categories = paper_row.get("categories") or []
    if categories:
        if isinstance(categories, str):
            parts.append(f"Categories: {categories}")
        else:
            parts.append(f"Categories: {', '.join(categories)}")

    pdf_url = paper_row.get("pdf_url")
    if pdf_url:
        parts.append(f"PDF URL: {pdf_url}")

    refs = paper_row.get("references") or []
    if refs:
        parts.append(f"Number of references: {len(refs)}")
        parts.append(f"References (arXiv IDs): {', '.join(str(r) for r in refs[:20])}")

    cited_by = paper_row.get("cited_by") or []
    if cited_by:
        parts.append(f"Cited by: {len(cited_by)} papers")

    abstract = paper_row.get("abstract") or ""
    if abstract:
        parts.append(f"\nAbstract:\n{abstract}")

    return "\n".join(parts)


def _generate_answer(question: str, context_chunks: list[str]) -> tuple[str, int]:
    """Send the question + context to Gemini and return (answer, tokens_used)."""
    context = "\n\n---\n\n".join(context_chunks)
    prompt = (
        "You are a helpful research assistant that answers questions about academic papers. "
        "You have access to the paper's full metadata including title, authors, publication date, "
        "abstract, categories, references, and more. "
        "Answer the question accurately based on the provided context. "
        "For factual questions (who wrote it, when was it published, how many references, etc.), "
        "answer directly from the metadata. "
        "For conceptual questions, provide helpful background knowledge to help the student understand. "
        "If the context doesn't fully answer the question, use your general knowledge to supplement, "
        "but clearly indicate when you're doing so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    model = genai.GenerativeModel(
        settings.gemini_chat_model,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )
    response = model.generate_content(prompt)
    tokens_used = 0
    if response.usage_metadata:
        tokens_used = (
            response.usage_metadata.prompt_token_count
            + response.usage_metadata.candidates_token_count
        )
    return response.text, tokens_used


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Ask a question about a specific paper. Returns cached answer or generates via RAG."""

    paper_id = request.paper_id
    question = request.question.strip()
    q_hash = _hash_question(question)

    # ── 1. Cache check ──────────────────────────────────────────────
    cache_result = await db.execute(
        text(
            "SELECT id, answer, context_chunk_ids "
            "FROM chat_cache "
            "WHERE paper_id = :pid AND question_hash = :qhash"
        ),
        {"pid": paper_id, "qhash": q_hash},
    )
    cached = cache_result.mappings().first()

    if cached:
        # Bump hit counter
        await db.execute(text("SELECT increment_cache_hit(:cid)"), {"cid": cached["id"]})
        await db.commit()

        # Fetch the context texts that were used
        chunk_ids = cached["context_chunk_ids"] or []
        context_used: list[str] = []
        if chunk_ids:
            chunks_result = await db.execute(
                text("SELECT content FROM paper_chunks WHERE id = ANY(:ids)"),
                {"ids": chunk_ids},
            )
            context_used = [row[0] for row in chunks_result.fetchall()]

        return ChatResponse(answer=cached["answer"], source="cache", context_used=context_used)

    # ── 2. Verify paper exists and fetch all metadata ───────────────
    paper_check = await db.execute(
        text(
            "SELECT id, arxiv_id, title, abstract, authors, categories, "
            "published_date, pdf_url, \"references\", cited_by "
            "FROM papers WHERE id::text = :pid OR arxiv_id = :pid"
        ),
        {"pid": paper_id},
    )
    paper_row = paper_check.mappings().first()
    if not paper_row:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")
    resolved_paper_id = str(paper_row["id"])

    # Build rich metadata context
    paper_meta = _build_paper_context(paper_row)

    # ── 3. Check for chunks, then vector search or metadata fallback ─
    chunk_count_result = await db.execute(
        text("SELECT COUNT(*) FROM paper_chunks WHERE paper_id = :pid"),
        {"pid": resolved_paper_id},
    )
    has_chunks = chunk_count_result.scalar() > 0

    if has_chunks:
        question_embedding = _get_embedding(question)
        embedding_literal = "[" + ",".join(str(v) for v in question_embedding) + "]"

        similar_result = await db.execute(
            text(
                "SELECT id, content, 1 - (embedding <=> CAST(:qemb AS vector)) AS similarity "
                "FROM paper_chunks "
                "WHERE paper_id = :pid "
                "ORDER BY similarity DESC "
                "LIMIT :lim"
            ),
            {"qemb": embedding_literal, "pid": resolved_paper_id, "lim": settings.max_context_chunks},
        )
        similar_rows = similar_result.mappings().fetchall()
        context_chunks = [paper_meta] + [row["content"] for row in similar_rows]
        chunk_ids_used = [str(row["id"]) for row in similar_rows]
    elif paper_row["abstract"]:
        context_chunks = [paper_meta]
        chunk_ids_used = []
    else:
        raise HTTPException(status_code=404, detail="No content found for this paper.")

    # ── 4. LLM generation ──────────────────────────────────────────
    try:
        answer, tokens_used = _generate_answer(question, context_chunks)
    except ResourceExhausted:
        return JSONResponse(
            status_code=429,
            content={"detail": "Gemini API rate limit reached. Please wait about 60 seconds and try again."},
        )

    # ── 5. Save to cache ───────────────────────────────────────────
    await db.execute(
        text(
            "INSERT INTO chat_cache (paper_id, question, question_hash, answer, context_chunk_ids, model_used, tokens_used) "
            "VALUES (:pid, :q, :qhash, :ans, CAST(:cids AS jsonb), :model, :tokens)"
        ),
        {
            "pid": resolved_paper_id,
            "q": question,
            "qhash": q_hash,
            "ans": answer,
            "cids": str(chunk_ids_used).replace("'", '"'),
            "model": settings.gemini_chat_model,
            "tokens": tokens_used,
        },
    )
    await db.commit()

    return ChatResponse(answer=answer, source="llm", context_used=context_chunks)
