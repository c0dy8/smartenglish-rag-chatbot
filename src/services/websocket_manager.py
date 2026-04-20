"""WebSocket connection manager for real-time dashboard updates."""

import asyncio
import json
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts metric updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, payload: dict):
        """Send a JSON payload to all connected clients."""
        if not self.active_connections:
            return
        message = json.dumps(payload, default=str)
        dead = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


manager = ConnectionManager()
