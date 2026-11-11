import asyncio
import json
from typing import Any, Dict, List
from app.core.database import get_db


class SSEBroadcaster:
    """
    Asynchronous Server-Sent Events (SSE) event bus broadcasting real-time
    transaction, mandate, and settlement state changes to connected UI clients.
    """

    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=250)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        message = json.dumps({"event": event_type, "data": payload}, default=str)
        dead_queues: List[asyncio.Queue] = []
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.append(queue)
        for dq in dead_queues:
            self.unsubscribe(dq)


broadcaster = SSEBroadcaster()

__all__ = ["get_db", "broadcaster"]

