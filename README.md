# ResearchGraph

A full-stack application for exploring academic paper citation networks with AI-powered Q&A. Upload papers from arXiv, visualize their citation relationships as an interactive graph, and ask questions answered directly from the paper content using RAG (Retrieval-Augmented Generation).

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐
│  Next.js 14  │─────▶│  FastAPI      │─────▶│  PostgreSQL + pgvector│
│  (port 3000) │◀─────│  (port 8000)  │◀─────│  (port 5432)         │
└──────────────┘      └──────┬───────┘      └──────────────────────┘
                             │
                             ├──▶ Gemini API (embeddings + chat)
                             └──▶ Redis (task queue)
```

**Backend:** FastAPI, SQLAlchemy (async), pgvector, Gemini API

**Frontend:** Next.js 14 (App Router), Tailwind CSS, React Flow, Lucide React

**Database:** PostgreSQL 16 with pgvector extension for vector similarity search

## Features

- **Citation Graph** — Interactive node-based visualization of paper relationships using React Flow. Click a node to expand its citations dynamically.
- **Paper Q&A** — Ask questions about any paper. Answers are generated from the paper's actual content using vector similarity search + Gemini 2.0 Flash.
- **Response Caching** — Repeated questions return instantly from a cache layer, saving API costs and latency.
- **Split-Screen UI** — 65/35 layout with the graph on the left and chat on the right. Clicking a paper node switches the chat context.

## Prerequisites

- Docker and Docker Compose
- A Google Gemini API key

## Quick Start

```bash
# 1. Clone and configure
git clone <repo-url> && cd research-graph
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

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
| `GEMINI_API_KEY` | Google Gemini API key (required) | — |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...@localhost:5432/researchgraph_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `FRONTEND_URL` | Vercel frontend URL for CORS (production) | — |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend | `http://localhost:8000` |

## Deployment

### Backend + Database — Render

1. Push the repo to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com) and click **New > Blueprint**.
3. Connect your repo — Render reads `render.yaml` and creates:
   - **PostgreSQL** database (Starter plan, pgvector-ready)
   - **Web service** running the FastAPI backend
4. In the Render dashboard, set the environment variables:
   - `GEMINI_API_KEY` — your Gemini API key
   - `FRONTEND_URL` — your Vercel URL (e.g. `https://research-graph.vercel.app`)
5. The first deploy runs `start.sh`, which auto-applies `migrations/init.sql`.
6. Note your Render service URL (e.g. `https://researchgraph-api.onrender.com`).

### Frontend — Vercel

1. Go to [vercel.com/new](https://vercel.com/new) and import the repo.
2. Set the **Root Directory** to `frontend`.
3. Add the environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://researchgraph-api.onrender.com`)
4. Deploy. Vercel auto-detects Next.js and builds it.

### Post-Deploy: Seed the Database

```bash
# Set DATABASE_URL to your Render external connection string
export DATABASE_URL="postgresql://researchgraph:...@...render.com:5432/researchgraph_db"
pip install asyncpg
python scripts/seed.py
```

## Development (Local)

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
