import httpx
import re
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

class WikipediaRetriever:
    def __init__(self):
        self.source_type = "wikipedia"
        self.trust_score = 0.85

    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract short keyword phrases from a long query for better Wikipedia matching."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "what", "how", "does",
            "do", "and", "or", "of", "in", "on", "for", "to", "with", "from",
            "by", "at", "that", "this", "these", "those", "it", "its", "be",
            "has", "have", "had", "will", "would", "could", "should", "may",
            "can", "about", "into", "which", "when", "where", "why", "there",
        }
        words = re.split(r'\W+', query.lower())
        keywords = [w for w in words if w and len(w) > 2 and w not in stop_words]
        
        search_terms = []
        # Short queries work fine as-is
        if len(query.split()) <= 4:
            search_terms.append(query)
        else:
            # Use first 3 meaningful keywords together
            if len(keywords) >= 2:
                search_terms.append(" ".join(keywords[:3]))
            # Also try individual important keywords (longer ones tend to be more specific)
            for kw in keywords[:3]:
                if len(kw) > 4:
                    search_terms.append(kw)
        
        return search_terms if search_terms else [query]

    async def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Asynchronously search Wikipedia for matches and fetch introductory extracts.
        Handles long queries by extracting keyword phrases for better matching.
        """
        results = []
        seen_titles = set()
        search_terms = self._extract_search_terms(query)
        
        headers = {
            "User-Agent": "SourceLens-AI-Research-System/2.0.0 (contact: support@sourcelens.ai)"
        }
        try:
            async with httpx.AsyncClient() as client:
                for term in search_terms:
                    if len(results) >= limit:
                        break
                    
                    # 1. Search for matching titles
                    search_url = (
                        "https://en.wikipedia.org/w/api.php?"
                        "action=opensearch&"
                        f"search={urllib.parse.quote(term)}&"
                        f"limit={limit}&"
                        "namespace=0&"
                        "format=json"
                    )
                    resp = await client.get(search_url, headers=headers, timeout=8.0)
                    if resp.status_code != 200:
                        continue
                    
                    data = resp.json()
                    if len(data) < 4:
                        continue
                        
                    titles = data[1]
                    urls = data[3]
                    
                    # 2. Query page contents for matched titles
                    for title, url in zip(titles, urls):
                        if title in seen_titles or len(results) >= limit:
                            continue
                        seen_titles.add(title)
                        
                        extract_url = (
                            "https://en.wikipedia.org/w/api.php?"
                            "action=query&"
                            "prop=extracts&"
                            "exintro&"
                            "explaintext&"
                            "redirects=1&"
                            f"titles={urllib.parse.quote(title)}&"
                            "format=json"
                        )
                        extract_resp = await client.get(extract_url, headers=headers, timeout=8.0)
                        if extract_resp.status_code == 200:
                            pages = extract_resp.json().get("query", {}).get("pages", {})
                            for page_id, page_data in pages.items():
                                content = page_data.get("extract", "").strip()
                                if content:
                                    results.append({
                                        "title": title.strip(),
                                        "url": url.strip(),
                                        "content": content[:2000],
                                        "source_type": self.source_type,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "trust_score": self.trust_score,
                                        "relevance_score": 0.85
                                    })
        except Exception as e:
            print(f"[WIKIPEDIA] Query failed for query '{query}': {e}")
        return results
