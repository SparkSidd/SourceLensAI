import httpx
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

class GithubRetriever:
    def __init__(self):
        self.source_type = "github"
        self.trust_score = 0.80

    async def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Asynchronously search the GitHub Repositories API.
        """
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            github_url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc"
            
            headers = {
                "User-Agent": "SourceLens-AI-Research-System",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(github_url, headers=headers, timeout=10.0)
                if resp.status_code != 200:
                    return []
                
                items = resp.json().get("items", [])[:limit]
                for item in items:
                    name = item.get("full_name", "Unknown Repository")
                    desc = item.get("description", "No repository description provided.")
                    url = item.get("html_url", "https://github.com")
                    stars = item.get("stargazers_count", 0)
                    lang = item.get("language", "Code")
                    
                    content = (
                        f"GitHub Repository: {name}\n"
                        f"Primary Language: {lang}\n"
                        f"Stars Count: {stars} Github Stars\n"
                        f"Description: {desc}"
                    )
                    
                    results.append({
                        "title": f"GitHub Repo: {name}",
                        "url": url,
                        "content": content,
                        "source_type": self.source_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "trust_score": self.trust_score,
                        "relevance_score": 0.85
                    })
        except Exception as e:
            print(f"[GITHUB] Repositories query failed: {e}")
        return results
