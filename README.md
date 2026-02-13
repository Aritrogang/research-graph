# ResearchGraph

A full-stack application for exploring academic paper citation networks with AI-powered Q&A. Upload papers from arXiv, visualize their citation relationships as an interactive graph, and ask questions answered directly from the paper content using RAG (Retrieval-Augmented Generation).

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐
│  Next.js 14  │─────▶│  FastAPI      │─────▶│  PostgreSQL + pgvector│
│  (port 3000) │◀─────│  (port 8000)  │◀─────│  (port 5432)         │
└──────────────┘      └──────┬───────┘      └──────────────────────┘
                             │
                             ├──▶ OpenAI API (embeddings + chat)
                             └──▶ Redis (task queue)
```

**Backend:** FastAPI, SQLAlchemy (async), pgvector, OpenAI API

**Frontend:** Next.js 14 (App Router), Tailwind CSS, React Flow, Lucide React

**Database:** PostgreSQL 16 with pgvector extension for vector similarity search

## Features

- **Citation Graph** — Interactive node-based visualization of paper relationships using React Flow. Click a node to expand its citations dynamically.
- **Paper Q&A** — Ask questions about any paper. Answers are generated from the paper's actual content using vector similarity search + GPT-4o-mini.
- **Response Caching** — Repeated questions return instantly from a cache layer, saving API costs and latency.
- **Split-Screen UI** — 65/35 layout with the graph on the left and chat on the right. Clicking a paper node switches the chat context.

## Prerequisites

- Docker and Docker Compose
- An OpenAI API key

## Quick Start

```bash
# 1. Clone and configure
git clone <repo-url> && cd research-graph
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Start all services
docker compose up --build -d

# 3. Seed the database with demo papers
pip install asyncpg
python scripts/seed.py

# 4. Open the app
open http://localhost:3000
```

## Project Structure

```
backend/
  app/
    main.py                 # FastAPI app, CORS, route registration
    db.py                   # Async SQLAlchemy session factory
    api/
      chat.py               # POST /chat — RAG pipeline with caching
      graph.py              # GET /graph/{paper_id} — citation network
    models/
      paper.py              # ORM: Paper, PaperChunk, ChatCache, IngestionJob
    schemas/
      chat.py               # ChatRequest / ChatResponse
      graph.py              # GraphNode / GraphEdge / GraphResponse
    core/
      config.py             # Pydantic Settings (env-based config)
    services/               # Business logic (ingestion, etc.)

frontend/
  src/
    app/
      layout.tsx            # Root layout
      page.tsx              # Dashboard — state orchestrator
    components/
      GraphView.tsx         # React Flow graph with expand-on-click
      PaperNode.tsx         # Custom node component (title, year, authors)
      ChatPanel.tsx         # Chat UI with source badges
    hooks/
      useChat.ts            # Chat state management, clears on paper change
    lib/
      api.ts                # Typed API client

migrations/
  init.sql                  # Full database schema (tables, indexes, functions)

scripts/
  seed.py                   # Populate DB with 5 famous CS papers
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Ask a question about a paper (cache check → vector search → LLM) |
| `GET` | `/graph/{paper_id}` | Get citation network as React Flow nodes/edges |
| `GET` | `/health` | Health check |

### POST /chat

**Request:**
```json
{
  "paper_id": "1706.03762",
  "question": "What is the Transformer architecture?"
}
```

**Response:**
```json
{
  "answer": "The Transformer is a model architecture...",
  "source": "llm",
  "context_used": ["chunk text 1", "chunk text 2"]
}
```

`source` is `"cache"` for cached responses or `"llm"` for freshly generated ones.

## Seed Papers

The seed script populates the database with these papers and their cross-references:

| Paper | arXiv ID | Year |
|-------|----------|------|
| Attention Is All You Need | 1706.03762 | 2017 |
| Deep Residual Learning for Image Recognition | 1512.03385 | 2015 |
| BERT | 1810.04805 | 2018 |
| Language Models are Few-Shot Learners (GPT-3) | 2005.14165 | 2020 |
| Neural Machine Translation by Jointly Learning to Align and Translate | 1409.0473 | 2014 |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | — |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://researchgraph:researchgraph_secret@localhost:5432/researchgraph_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend | `http://localhost:8000` |

## Development

Run services individually for local development:

```bash
# Database + Redis
docker compose up postgres redis -d

# Backend (with hot reload)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## License

MIT
