import httpx
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

class HackerNewsRetriever:
    def __init__(self):
        self.source_type = "hackernews"
        self.trust_score = 0.65 # Technical discussions are moderately trusted

    async def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Asynchronously search HackerNews stories via Algolia API.
        """
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            # Fetch top technical stories matching our query
            hn_url = f"https://hn.algolia.com/api/v1/search?query={encoded_query}&tags=story"
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(hn_url, timeout=10.0)
                if resp.status_code != 200:
                    return []
                
                hits = resp.json().get("hits", [])[:limit]
                for hit in hits:
                    title = hit.get("title", "HN Post")
                    url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    points = hit.get("points", 0)
                    author = hit.get("author", "anonymous")
                    comments = hit.get("num_comments", 0)
                    created_at_str = hit.get("created_at", datetime.utcnow().isoformat())
                    
                    content = (
                        f"HackerNews Discussion Thread: '{title}'\n"
                        f"Thread Author: {author}\n"
                        f"Community Engagement: {points} points | {comments} comments\n"
                        f"Topic context: {hit.get('story_text', 'See discussion thread link.')}"
                    )
                    
                    results.append({
                        "title": f"HN: {title}",
                        "url": url,
                        "content": content,
                        "source_type": self.source_type,
                        "timestamp": created_at_str,
                        "trust_score": self.trust_score,
                        "relevance_score": 0.75
                    })
        except Exception as e:
            print(f"[HN] Stories retrieval failed: {e}")
        return results
