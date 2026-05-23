import asyncio
import json
from typing import Dict, List, Any

class FeedService:
    # Class-level registry mapping session IDs to active subscriber queues
    _subscribers: Dict[str, List[asyncio.Queue]] = {}

    @classmethod
    def subscribe(cls, session_id: str) -> asyncio.Queue:
        """
        Creates and registers a new async subscriber queue for the specified session.
        Allows immediate real-time log streaming.
        """
        queue = asyncio.Queue()
        if session_id not in cls._subscribers:
            cls._subscribers[session_id] = []
        cls._subscribers[session_id].append(queue)
        print(f"[STREAMING FEED] Active subscription added for session '{session_id}'. Total listeners: {len(cls._subscribers[session_id])}")
        return queue

    @classmethod
    def unsubscribe(cls, session_id: str, queue: asyncio.Queue):
        """
        Deregisters and closes a subscriber queue when client disconnects.
        Prevents memory leaks in long-running processes.
        """
        if session_id in cls._subscribers:
            try:
                cls._subscribers[session_id].remove(queue)
                print(f"[STREAMING FEED] Listener removed for session '{session_id}'. Active remaining: {len(cls._subscribers[session_id])}")
                if not cls._subscribers[session_id]:
                    del cls._subscribers[session_id]
            except ValueError:
                pass

    @classmethod
    async def publish_event(cls, session_id: str, event_type: str, message: str, metadata: Any = None):
        """
        Publishes a research status event package to all active listeners in the session channel.
        Events types: 'status', 'source_discovered', 'paper_indexed', 'evidence_validated', 'report_section', 'complete'.
        """
        if session_id not in cls._subscribers:
            return

        payload = {
            "event": event_type,
            "message": message,
            "metadata": metadata or {}
        }
        
        json_payload = json.dumps(payload)
        
        # Dispatch JSON payloads concurrently to all session listeners
        for queue in cls._subscribers[session_id]:
            await queue.put(json_payload)
            
        # Yield control briefly to ensure event loop schedules queue flushes
        await asyncio.sleep(0.01)
