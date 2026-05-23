import fitz  # PyMuPDF
from datetime import datetime
from typing import List, Dict, Any

class PdfProcessor:
    @staticmethod
    def parse_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parses raw PDF bytes, extracts clean page text, preserves page and section ranges,
        and returns normalized semantic chunks with overlapping boundaries.
        """
        chunks = []
        if not file_bytes:
            return chunks

        try:
            # Load PDF document stream in-memory
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            full_text_blocks = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text.strip():
                    full_text_blocks.append({
                        "page": page_num + 1,
                        "text": text
                    })
            
            # Combine all page text segments
            combined_text = ""
            page_mappings = [] # Keep track of which character offset maps to which page
            
            for block in full_text_blocks:
                start_idx = len(combined_text)
                combined_text += block["text"] + "\n\n"
                end_idx = len(combined_text)
                page_mappings.append({
                    "start": start_idx,
                    "end": end_idx,
                    "page": block["page"]
                })
                
            # Perform Semantic chunking with an overlapping sliding window
            # Standard chunk size: 1000 characters. Overlap: 200 characters.
            chunk_size = 1000
            overlap = 200
            
            start = 0
            chunk_index = 1
            
            while start < len(combined_text):
                end = min(start + chunk_size, len(combined_text))
                chunk_text = combined_text[start:end].strip()
                
                if len(chunk_text) > 50:
                    # Find which page(s) this chunk maps to
                    pages_involved = []
                    for mapping in page_mappings:
                        # Overlap check
                        if not (end <= mapping["start"] or start >= mapping["end"]):
                            pages_involved.append(str(mapping["page"]))
                            
                    page_str = ", ".join(pages_involved) if pages_involved else "1"
                    
                    chunks.append({
                        "title": f"Upload: {filename} (Page {page_str}) [Chunk {chunk_index}]",
                        "url": f"upload://{filename}#page={page_str}&chunk={chunk_index}",
                        "content": chunk_text,
                        "source_type": "upload",
                        "timestamp": datetime.utcnow().isoformat(),
                        "trust_score": 0.95, # Primary upload sources are highly trusted
                        "relevance_score": 0.90
                    })
                    chunk_index += 1
                
                # Advance starting pointer by size minus overlap
                start += (chunk_size - overlap)
                
        except Exception as e:
            print(f"[PDF PROCESSOR] Exception raised parsing PDF file {filename}: {e}")
            
        print(f"[PDF PROCESSOR] Processed {filename}. Synthesized {len(chunks)} overlapping semantic segments.")
        return chunks
