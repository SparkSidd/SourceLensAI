import httpx
import re
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class ArxivRetriever:
    def __init__(self):
        self.source_type = "arxiv"
        self.trust_score = 0.98

    def _build_search_query(self, query: str) -> str:
        """Build a clean arXiv search query from a natural language input."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "what", "how", "does",
            "do", "and", "or", "of", "in", "on", "for", "to", "with", "from",
            "by", "at", "that", "this", "these", "those", "it", "its", "be",
            "has", "have", "had", "will", "would", "could", "should", "may",
            "can", "about", "into", "which", "when", "where", "why", "there",
            "improve", "limitations", "impact", "analyze", "analysis",
        }
        words = re.split(r'\W+', query.lower())
        keywords = [w for w in words if w and len(w) > 2 and w not in stop_words]
        
        # Use top 4 keywords joined with AND for arXiv search
        search_terms = keywords[:4]
        if not search_terms:
            search_terms = query.split()[:3]
        
        return "+AND+".join([urllib.parse.quote(t) for t in search_terms])

    async def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Asynchronously search arXiv academic archives.
        Extracts keywords from long natural language queries for better matching.
        """
        results = []
        try:
            search_query = self._build_search_query(query)
            arxiv_url = f"https://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={limit}&sortBy=relevance&sortOrder=descending"
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(arxiv_url, timeout=12.0)
                if resp.status_code != 200:
                    return []
                
                # Parse XML tree using BeautifulSoup XML parser
                soup = BeautifulSoup(resp.text, "xml")
                entries = soup.find_all("entry")
                
                for entry in entries:
                    title_elem = entry.find("title")
                    summary_elem = entry.find("summary")
                    id_elem = entry.find("id")
                    
                    title = title_elem.text if title_elem else "Unknown arXiv Title"
                    summary = summary_elem.text if summary_elem else "No summary available."
                    url = id_elem.text if id_elem else "https://arxiv.org"
                    
                    # Clean newlines and double spaces
                    title = title.replace("\n", " ").replace("  ", " ").strip()
                    summary = summary.replace("\n", " ").replace("  ", " ").strip()
                    
                    # Skip empty/placeholder entries
                    if not title or title == "Unknown arXiv Title":
                        continue
                    
                    results.append({
                        "title": title,
                        "url": url.strip(),
                        "content": summary[:2000],
                        "source_type": self.source_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "trust_score": self.trust_score,
                        "relevance_score": 0.90
                    })
        except Exception as e:
            print(f"[ARXIV] Search failed for query '{query}': {e}")
        return results
