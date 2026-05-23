import fitz # PyMuPDF
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class ContentExtractor:
    @staticmethod
    def extract_url_content(html_content: str) -> str:
        """
        Parses raw HTML, extracts readable main text, removes navigation,
        ads, and headers/footers, and preserves primary headings.
        """
        # Try to use trafilatura if installed, otherwise BeautifulSoup fallback
        try:
            import trafilatura
            text = trafilatura.extract(html_content, include_comments=False, include_tables=True)
            if text:
                return text
        except ImportError:
            pass
            
        # Robust BeautifulSoup fallback
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove scripts, styles, headers, footers, navigation, ads, and sidebars
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
                element.decompose()
                
            # Focus on central article/content areas if available
            article = None
            for selector in ["article", "main", "#content", ".content", ".post-content", ".article-content"]:
                found = soup.select_one(selector)
                if found:
                    article = found
                    break
                    
            target = article if article else soup
            
            # Preserve headers and paragraph text with line spacing
            lines = []
            for elem in target.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                text = elem.get_text().strip()
                if not text:
                    continue
                if elem.name.startswith("h"):
                    lines.append(f"\n## {text}\n")
                elif elem.name == "li":
                    lines.append(f"- {text}")
                else:
                    lines.append(text)
                    
            return "\n\n".join(lines)
        except Exception as e:
            print(f"[EXTRACTOR] HTML extraction failed: {e}")
            return html_content # Return raw as fallback

    @staticmethod
    def parse_pdf(pdf_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parses PDF using PyMuPDF (fitz), chunks it intelligently,
        and preserves page metadata.
        """
        chunks = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()
                if not text:
                    continue
                
                # Chunk page content or aggregate it
                # We chunk with overlap: size 1000, overlap 200
                page_chunks = ContentExtractor.chunk_text(text, chunk_size=1000, overlap=200)
                
                for idx, chunk in enumerate(page_chunks):
                    chunks.append({
                        "title": f"{filename} (Page {page_num + 1}, Chunk {idx + 1})",
                        "url": f"uploaded://{filename}#page={page_num + 1}",
                        "content": chunk,
                        "source_type": "upload",
                        "timestamp": "",
                        "trust_score": 0.95, # Uploaded primary sources are highly trusted
                        "relevance_score": 0.90
                    })
        except Exception as e:
            print(f"[EXTRACTOR] PDF parsing failed: {e}")
        return chunks

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Splits text into chunks of `chunk_size` characters with `overlap` overlap,
        attempting to break at sentence boundaries when possible.
        """
        chunks = []
        if len(text) <= chunk_size:
            return [text]
            
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
                
            # Attempt to split at a period or newline close to the end
            sub_text = text[start:end]
            split_idx = -1
            
            # Find last sentence-ending period or newline
            match = re.search(r'[\.\n]\s*', sub_text[::-1])
            if match:
                split_idx = end - match.start()
                
            # If a suitable sentence boundary is found, split there
            if split_idx != -1 and split_idx > start + (chunk_size // 2):
                chunks.append(text[start:split_idx])
                start = split_idx - overlap
            else:
                chunks.append(text[start:end])
                start = end - overlap
                
            if start < 0:
                start = 0
                
        return chunks
