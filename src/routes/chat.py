"""Chat endpoint routes."""

import time
from fastapi import APIRouter, HTTPException
from src.schemas.models import ChatRequest, ChatResponse
from src.services.rag_service import answer_query
from src.services.supabase_service import get_document_count
from src.services.embedding_cache import get_cache_stats
from src.services.metrics_service import metrics
from src.services.websocket_manager import manager

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user query and return an AI-generated response.
    Uses RAG to retrieve context from the knowledge base.
    """
    start = time.perf_counter()
    try:
        result = await answer_query(request.message)

        elapsed_ms = (time.perf_counter() - start) * 1000
        metrics.record_query(
            query=request.message,
            response=result["response"],
            escalated=result.get("escalate", False),
            confidence=float(result.get("confidence", 0) or 0),
            context_docs=int(result.get("context_used", 0) or 0),
            response_time_ms=elapsed_ms,
        )
        await manager.broadcast({"type": "metrics", "data": metrics.snapshot()})

        return ChatResponse(
            response=result["response"],
            escalate=result.get("escalate", False),
            confidence=result.get("confidence", 0),
            context_used=result.get("context_used", 0)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    doc_count = await get_document_count()
    cache_stats = get_cache_stats()

    return {
        "status": "healthy",
        "documents_loaded": doc_count,
        "cache": cache_stats,
        "message": "RAG ChatBot is running"
    }

@router.get("/cache-stats")
async def cache_statistics():
    """Get embedding cache statistics."""
    stats = get_cache_stats()
    return {
        "embeddings_cached": stats["total_cached"],
        "cache_size_mb": stats["cache_size_mb"],
        "message": "Cached embeddings save API costs"
    }
