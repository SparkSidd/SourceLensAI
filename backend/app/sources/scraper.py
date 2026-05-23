import httpx
import re
from datetime import datetime
from typing import Dict, Any, List
from bs4 import BeautifulSoup

class WebScraper:
    @staticmethod
    async def scrape_url(url: str) -> Dict[str, Any]:
        """
        Scrape a given web URL and extract clean, boilerplate-free structured text content.
        Uses advanced BeautifulSoup selector filtering to wipe sidebars, footers, ads, and nav grids.
        """
        result = {
            "title": "",
            "headings": [],
            "content": "",
            "metadata": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=12.0, follow_redirects=True)
                if resp.status_code != 200:
                    return result
                html = resp.text

            # 1. Attempt Trafilatura Extraction dynamically if available
            try:
                import trafilatura
                downloaded = trafilatura.extract(html, include_comments=False, include_tables=True)
                if downloaded:
                    # Successfully extracted via Trafilatura
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.find("title").get_text() if soup.find("title") else ""
                    result["title"] = title.strip()
                    result["content"] = downloaded.strip()
                    return result
            except ImportError:
                pass

            # 2. Fallback to high-fidelity BeautifulSoup boilerplate sweeper
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove noise tags
            noise_selectors = [
                "nav", "header", "footer", "sidebar", "aside", "script", "style", 
                "noscript", "iframe", "form", ".ads", ".comments", "#comments", 
                ".menu", ".navigation", ".footer", ".header", ".sidebar", ".banner"
            ]
            for selector in noise_selectors:
                for element in soup.select(selector):
                    element.decompose()
            for element in soup(["script", "style", "iframe", "noscript"]):
                element.decompose()

            # Extract Title
            title = ""
            if soup.title:
                title = soup.title.get_text()
            elif soup.find("h1"):
                title = soup.find("h1").get_text()
            result["title"] = title.strip()

            # Extract Headings (h2 and h3)
            headings = []
            for h in soup.find_all(["h2", "h3"]):
                h_text = h.get_text().strip()
                if h_text and len(h_text) > 5:
                    headings.append(h_text)
            result["headings"] = headings[:8]

            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all("p"):
                p_text = p.get_text().strip()
                # Skip tiny cookie banners or empty tags
                if p_text and len(p_text) > 30:
                    paragraphs.append(p_text)

            clean_body = "\n\n".join(paragraphs)
            result["content"] = clean_body

            # Extract metadata (author, keywords, description)
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result["metadata"]["description"] = meta_desc.get("content", "").strip()

            meta_author = soup.find("meta", attrs={"name": "author"})
            if meta_author:
                result["metadata"]["author"] = meta_author.get("content", "").strip()

        except Exception as e:
            print(f"[SCRAPER] Error extracting URL {url}: {e}")
            
        return result
