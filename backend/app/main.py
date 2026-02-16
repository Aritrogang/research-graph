"""ResearchGraph FastAPI application."""

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.discover import router as discover_router
from app.api.graph import router as graph_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Research paper citation graph with AI-powered Q&A",
    version="0.1.0",
)

origins = ["http://localhost:3000", "http://localhost:3001", "http://researchgraph-frontend:3000"]
if settings.frontend_url:
    origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return error details instead of generic 500 for debugging."""
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb[-3:]},
    )


app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(discover_router, prefix="/discover", tags=["discover"])
app.include_router(graph_router, prefix="/graph", tags=["graph"])


@app.get("/health")
async def health_check():
    key = settings.gemini_api_key
    return {
        "status": "healthy",
        "app": settings.app_name,
        "gemini_key_set": bool(key and key != ""),
        "gemini_key_prefix": key[:8] + "..." if key else "MISSING",
    }
