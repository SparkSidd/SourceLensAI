import asyncio
from typing import Dict, List, Any
import json

class FeedService:
    # Global map of session_id -> list of subscriber queues
    _subscribers: Dict[str, List[asyncio.Queue]] = {}

    @classmethod
    def subscribe(cls, session_id: str) -> asyncio.Queue:
        """Create a new subscriber queue for the specified session."""
        queue = asyncio.Queue()
        if session_id not in cls._subscribers:
            cls._subscribers[session_id] = []
        cls._subscribers[session_id].append(queue)
        print(f"[FEED] Session {session_id}: Added new subscriber. Total: {len(cls._subscribers[session_id])}")
        return queue

    @classmethod
    def unsubscribe(cls, session_id: str, queue: asyncio.Queue):
        """Remove a subscriber queue when the client disconnects."""
        if session_id in cls._subscribers:
            try:
                cls._subscribers[session_id].remove(queue)
                print(f"[FEED] Session {session_id}: Removed subscriber. Remaining: {len(cls._subscribers[session_id])}")
                if not cls._subscribers[session_id]:
                    del cls._subscribers[session_id]
            except ValueError:
                pass

    @classmethod
    async def publish_event(cls, session_id: str, event_type: str, message: str, metadata: Any = None):
        """
        Publish a research event to all active subscriber queues for a session.
        Event Types: 'status', 'source_discovered', 'paper_indexed', 'evidence_validated', 'report_section', 'complete'
        """
        if session_id not in cls._subscribers:
            return
            
        payload = {
            "event": event_type,
            "message": message,
            "metadata": metadata or {}
        }
        
        json_payload = json.dumps(payload)
        
        # Dispatch to all queues in parallel
        for queue in cls._subscribers[session_id]:
            await queue.put(json_payload)
            
        # Give control back to event loop briefly
        await asyncio.sleep(0.01)
