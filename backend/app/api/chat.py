"""Chat endpoint: cached Q&A over research papers using RAG."""

import hashlib

import openai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
settings = get_settings()


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode()).hexdigest()


async def _get_embedding(text_input: str) -> list[float]:
    """Generate an embedding for the given text using OpenAI."""
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text_input,
    )
    return response.data[0].embedding


async def _generate_answer(question: str, context_chunks: list[str]) -> tuple[str, int]:
    """Send the question + context to GPT-4o-mini and return (answer, tokens_used)."""
    context = "\n\n---\n\n".join(context_chunks)
    prompt = (
        "Answer the question based only on the following context from a research paper. "
        "If the context does not contain enough information, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": "You are a helpful research assistant that answers questions about academic papers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0
    return answer, tokens_used


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
        # Bump hit counter in the background
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

    # ── 2. Verify paper exists ──────────────────────────────────────
    paper_check = await db.execute(
        text("SELECT id FROM papers WHERE id = :pid OR arxiv_id = :pid"),
        {"pid": paper_id},
    )
    paper_row = paper_check.first()
    if not paper_row:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")
    resolved_paper_id = str(paper_row[0])

    # ── 3. Vector search for relevant chunks ────────────────────────
    question_embedding = await _get_embedding(question)
    embedding_literal = "[" + ",".join(str(v) for v in question_embedding) + "]"

    similar_result = await db.execute(
        text(
            "SELECT id, content, 1 - (embedding <=> :qemb::vector) AS similarity "
            "FROM paper_chunks "
            "WHERE paper_id = :pid "
            "ORDER BY similarity DESC "
            "LIMIT :lim"
        ),
        {"qemb": embedding_literal, "pid": resolved_paper_id, "lim": settings.max_context_chunks},
    )
    similar_rows = similar_result.mappings().fetchall()

    if not similar_rows:
        raise HTTPException(status_code=404, detail="No chunks found for this paper. Has it been ingested?")

    context_chunks = [row["content"] for row in similar_rows]
    chunk_ids_used = [str(row["id"]) for row in similar_rows]

    # ── 4. LLM generation ──────────────────────────────────────────
    answer, tokens_used = await _generate_answer(question, context_chunks)

    # ── 5. Save to cache ───────────────────────────────────────────
    await db.execute(
        text(
            "INSERT INTO chat_cache (paper_id, question, question_hash, answer, context_chunk_ids, model_used, tokens_used) "
            "VALUES (:pid, :q, :qhash, :ans, :cids::jsonb, :model, :tokens)"
        ),
        {
            "pid": resolved_paper_id,
            "q": question,
            "qhash": q_hash,
            "ans": answer,
            "cids": str(chunk_ids_used).replace("'", '"'),
            "model": settings.openai_chat_model,
            "tokens": tokens_used,
        },
    )
    await db.commit()

    return ChatResponse(answer=answer, source="llm", context_used=context_chunks)
