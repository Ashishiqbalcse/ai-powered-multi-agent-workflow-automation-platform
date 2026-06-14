from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[run_id].add(websocket)

    def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        if run_id in self._connections:
            self._connections[run_id].discard(websocket)
            if not self._connections[run_id]:
                self._connections.pop(run_id, None)

    async def broadcast(self, run_id: str, message: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for websocket in self._connections.get(run_id, set()):
            try:
                await websocket.send_json(jsonable_encoder(message))
            except RuntimeError:
                stale.append(websocket)

        for websocket in stale:
            self.disconnect(run_id, websocket)


websocket_manager = WebSocketManager()

