import asyncio
import feedparser
from datetime import datetime
from typing import List, Dict, Any

class RssRetriever:
    def __init__(self):
        self.source_type = "rss"
        self.trust_score = 0.80 # Premium technology and corporate research blogs

        # Core RSS Feed targets requested by the user
        self.feed_urls = {
            "OpenAI Blog": "https://openai.com/blog/rss.xml",
            "Google DeepMind": "https://deepmind.google/blog/rss.xml",
            "Anthropic Research": "https://www.anthropic.com/index.xml",
            "Cloudflare Tech": "https://blog.cloudflare.com/rss/",
            "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
            "BleepingComputer": "https://www.bleepingcomputer.com/feed/"
        }

    async def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Asynchronously parses technology and security feeds, filtering by keyword relevance.
        """
        results = []
        tasks = []
        
        # Parallelize feed fetching across thread pools
        for blog_name, url in self.feed_urls.items():
            tasks.append(self._fetch_feed(blog_name, url, query, limit))
            
        fetched_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        for item_list in fetched_lists:
            if isinstance(item_list, list):
                results.extend(item_list)
                
        # Limit total RSS hits across all blogs
        return results[:limit * 2]

    async def _fetch_feed(self, blog_name: str, feed_url: str, query: str, limit: int) -> List[Dict[str, Any]]:
        results = []
        try:
            loop = asyncio.get_running_loop()
            # Run blocking feedparser parsing in async executor pool
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
            
            count = 0
            query_lower = query.lower()
            
            for entry in feed.entries:
                if count >= limit:
                    break
                    
                title = entry.get("title", "")
                url = entry.get("link", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                
                # Clean html tags from summary
                from bs4 import BeautifulSoup
                summary_text = BeautifulSoup(summary, "html.parser").get_text() if summary else ""
                
                # Check for query keyword match (soft matching titles or text summaries)
                words = query_lower.split()
                matched = any(w in title.lower() or w in summary_text.lower() for w in words if len(w) > 3)
                
                if matched or not query:
                    results.append({
                        "title": f"{blog_name}: {title}",
                        "url": url,
                        "content": summary_text[:600].strip() + ("..." if len(summary_text) > 600 else ""),
                        "source_type": self.source_type,
                        "timestamp": entry.get("published", datetime.utcnow().isoformat()),
                        "trust_score": self.trust_score,
                        "relevance_score": 0.80
                    })
                    count += 1
        except Exception as e:
            # Silent fallback if a specific company blog feed blocks or fails
            print(f"[RSS] Failed crawling {blog_name} feed: {e}")
        return results
