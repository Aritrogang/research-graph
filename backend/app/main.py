"""ResearchGraph FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.graph import router as graph_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Research paper citation graph with AI-powered Q&A",
    version="0.1.0",
)

origins = ["http://localhost:3000", "http://researchgraph-frontend:3000"]
if settings.frontend_url:
    origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(graph_router, prefix="/graph", tags=["graph"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}
