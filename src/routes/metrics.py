"""Metrics & real-time dashboard routes."""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.metrics_service import metrics
from src.services.websocket_manager import manager
from src.services.supabase_service import get_document_count

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """Return full metrics snapshot."""
    snap = metrics.snapshot()
    snap["documents_loaded"] = await get_document_count()
    return snap


@router.get("/metrics/topics")
async def get_topics():
    """Return topic frequency map."""
    return {"topics": metrics.snapshot()["top_topics"]}


@router.get("/metrics/history")
async def get_history():
    """Return historical time-series data."""
    return {"history": metrics.snapshot()["history"]}


@router.get("/metrics/alerts")
async def get_alerts():
    """Return recent escalation alerts."""
    return {"alerts": metrics.snapshot()["escalation_alerts"]}


@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket):
    """Push real-time metric updates every 2s + on every new query."""
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "metrics", "data": metrics.snapshot()})
        while True:
            await asyncio.sleep(2)
            await websocket.send_json({"type": "metrics", "data": metrics.snapshot()})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
