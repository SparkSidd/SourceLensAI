import asyncio
from typing import List, Dict, Any

from backend.app.sources.tavily import TavilyRetriever
from backend.app.sources.wikipedia import WikipediaRetriever
from backend.app.sources.arxiv import ArxivRetriever
from backend.app.sources.github import GithubRetriever
from backend.app.sources.hackernews import HackerNewsRetriever
from backend.app.sources.rss import RssRetriever
from backend.app.streaming.feed import FeedService

class ParallelRetrievalEngine:
    def __init__(self):
        # Register instances of all specialized crawlers
        self.retrievers = {
            "tavily": TavilyRetriever(),
            "wikipedia": WikipediaRetriever(),
            "arxiv": ArxivRetriever(),
            "github": GithubRetriever(),
            "hackernews": HackerNewsRetriever(),
            "rss": RssRetriever()
        }

    async def execute_retrieval(self, query: str, active_sources: List[str], session_id: str = "") -> List[Dict[str, Any]]:
        """
        Execute routed search engines concurrently.
        Implements timeouts per task to protect pipeline latency and handles partial failures.
        """
        tasks = []
        source_keys = []
        
        for src in active_sources:
            if src in self.retrievers:
                retriever = self.retrievers[src]
                # Wrap search in an async task with individual timeout boundary
                task = asyncio.create_task(self._safe_search(src, retriever, query, session_id))
                tasks.append(task)
                source_keys.append(src)

        if not tasks:
            return []

        # Run all scheduled search queries concurrently
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        flat_results = []
        for src_key, results in zip(source_keys, results_lists):
            if isinstance(results, list):
                flat_results.extend(results)
                if session_id:
                    # Notify dynamic progress event
                    await FeedService.publish_event(
                        session_id, 
                        "status", 
                        f"Finished crawling source [{src_key.upper()}]: Retrieved {len(results)} normalized articles."
                    )
            elif isinstance(results, Exception):
                # Partial failure protection: one crashed search doesn't crash the orchestrator
                print(f"[RETRIEVER ENGINE] Task [{src_key.upper()}] crashed: {results}")
                if session_id:
                    await FeedService.publish_event(
                        session_id, 
                        "status", 
                        f"Warning: Crawler [{src_key.upper()}] failed or timed out. Bypassing node gracefully..."
                    )
                    
        print(f"[RETRIEVER ENGINE] Finished. Combined output count: {len(flat_results)} context maps.")
        return flat_results

    async def _safe_search(self, src_name: str, retriever: Any, query: str, session_id: str) -> List[Dict[str, Any]]:
        """Wraps search requests inside strict timeout constraints to ensure fast client responses."""
        try:
            if session_id:
                await FeedService.publish_event(
                    session_id, 
                    "status", 
                    f"Spawning retrieval process on crawler: [{src_name.upper()}]..."
                )
            # Enforce 10-second absolute execution limit per retriever
            results = await asyncio.wait_for(retriever.search(query), timeout=10.0)
            
            # Normalize and augment domain flags
            for r in results:
                r["domain"] = r.get("url", "").replace("https://", "").replace("http://", "").split("/")[0]
                r["citations"] = [] # Initialize empty citation mapper list
                
            return results
        except asyncio.TimeoutError:
            print(f"[RETRIEVER ENGINE] Timeout exceeded on {src_name} search.")
            raise Exception("Timeout exceeded")
        except Exception as e:
            print(f"[RETRIEVER ENGINE] Exception during {src_name} search: {e}")
            raise e
