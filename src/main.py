"""FastAPI application entry point."""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.config import Config
from src.routes import chat, metrics

Config.validate()

logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SmartEnglish RAG ChatBot",
    description="Intelligent customer support assistant with RAG + real-time analytics",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(metrics.router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SmartEnglish RAG ChatBot",
        "version": "1.1.0",
        "endpoints": {
            "chat": "POST /api/v1/chat",
            "health": "GET /api/v1/health",
            "metrics": "GET /api/v1/metrics",
            "websocket": "WS /api/v1/ws/metrics",
            "dashboard": "GET /dashboard",
            "docs": "/docs"
        }
    }


@app.get("/dashboard")
async def dashboard():
    """Serve the analytics dashboard."""
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.on_event("startup")
async def startup():
    logger.info(f"🚀 Starting SmartEnglish ChatBot in {Config.ENVIRONMENT} mode")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down SmartEnglish ChatBot")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=Config.BACKEND_HOST,
        port=Config.BACKEND_PORT,
        reload=Config.ENVIRONMENT == "development"
    )
