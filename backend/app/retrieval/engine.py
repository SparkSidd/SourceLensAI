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

    async def execute_retrieval(self, queries: List[str] | str, active_sources: List[str], session_id: str = "") -> List[Dict[str, Any]]:
        """
        Execute routed search engines concurrently for one or more query variants.
        Implements timeouts per task to protect pipeline latency and handles partial failures.
        """
        if isinstance(queries, str):
            queries = [queries]
            
        tasks = []
        task_metadata = [] # List of tuples: (src, query)
        
        for query in queries:
            for src in active_sources:
                if src in self.retrievers:
                    retriever = self.retrievers[src]
                    # Wrap search in an async task with individual timeout boundary
                    task = asyncio.create_task(self._safe_search(src, retriever, query, session_id))
                    tasks.append(task)
                    task_metadata.append((src, query))

        if not tasks:
            return []

        # Run all scheduled search queries concurrently
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        flat_results = []
        source_counts = {}
        
        for (src_key, query), results in zip(task_metadata, results_lists):
            if isinstance(results, list):
                flat_results.extend(results)
                source_counts[src_key] = source_counts.get(src_key, 0) + len(results)
            elif isinstance(results, Exception):
                # Partial failure protection: one crashed search doesn't crash the orchestrator
                print(f"[RETRIEVER ENGINE] Task [{src_key.upper()}] for query '{query}' crashed: {results}")
                if session_id:
                    await FeedService.publish_event(
                        session_id, 
                        "status", 
                        f"Warning: Crawler [{src_key.upper()}] failed or timed out on query variant."
                    )
                    
        if session_id:
            summary_parts = [f"{src.upper()}: {count}" for src, count in source_counts.items()]
            await FeedService.publish_event(
                session_id, 
                "status", 
                f"Crawling completed. Sources discovered: {', '.join(summary_parts)}"
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
                    f"Spawning retrieval process on [{src_name.upper()}] for: '{query[:40]}...'..."
                )
            # Enforce 10-second absolute execution limit per retriever
            results = await asyncio.wait_for(retriever.search(query), timeout=10.0)
            
            # If search returns no results and query is long, try fallback query with simplified keywords
            if not results and len(query.split()) > 2 and src_name in ["arxiv", "github", "hackernews"]:
                simplified = self._simplify_query(query)
                if simplified != query:
                    if session_id:
                        await FeedService.publish_event(
                            session_id, 
                            "status", 
                            f"Crawler [{src_name.upper()}] found 0 matches. Retrying with key terms: '{simplified}'..."
                        )
                    results = await asyncio.wait_for(retriever.search(simplified), timeout=10.0)
            
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

    def _simplify_query(self, query: str) -> str:
        """Extracts primary technical nouns from conversational phrases for search compatibility."""
        import re
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "what", "how", "does",
            "do", "and", "or", "of", "in", "on", "for", "to", "with", "from",
            "by", "at", "that", "this", "these", "those", "it", "its", "be",
            "has", "have", "had", "will", "would", "could", "should", "may",
            "can", "about", "into", "which", "when", "where", "why", "there",
            "need", "more", "less", "low", "added", "showing", "sources", "source",
            "find", "search", "get", "tell", "explain", "describe", "latest", "new"
        }
        words = re.split(r'\W+', query.lower())
        keywords = [w for w in words if w and len(w) > 2 and w not in stop_words]
        return " ".join(keywords[:3]) if keywords else query
