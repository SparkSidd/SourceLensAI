from typing import List, Dict, Any

class ContextBuilder:
    @staticmethod
    def build_context(ranked_sources: List[Dict[str, Any]]) -> tuple[str, Dict[int, Dict[str, Any]]]:
        """
        Creates a structured, formatted context window for LLM ingestion.
        Returns:
            - context_string: The formatted markdown text.
            - attribution_map: A mapping of inline index integer -> original source dict.
        """
        context_blocks = []
        attribution_map = {}
        
        context_blocks.append("## SYSTEM RETRIEVED SOURCES AND AUTHORITATIVE CONTEXT\n")
        context_blocks.append("Use ONLY the following retrieved evidence to synthesize your findings. Cite strictly using `[1]`, `[2]`, etc.\n")
        
        for idx, src in enumerate(ranked_sources, start=1):
            source_id = src.get("id", f"src_{idx}")
            title = src.get("title", "Untitled Source")
            url = src.get("url", "https://unknown.url")
            content = src.get("content", "")
            source_type = src.get("source_type", "web").upper()
            trust_score = src.get("trust_score", 0.70)
            
            # Map index to source info
            attribution_map[idx] = {
                "id": source_id,
                "title": title,
                "url": url,
                "source_type": src.get("source_type", "web"),
                "trust_score": trust_score,
                "relevance_score": src.get("relevance_score", 0.70)
            }
            
            # Determine Trust Label
            if trust_score >= 0.90:
                trust_label = "HIGH AUTHORITY (Primary/Academic)"
            elif trust_score >= 0.75:
                trust_label = "VERIFIED SYSTEM (Authoritative Web)"
            else:
                trust_label = "LOW CONFIDENCE (Forum/Opinion)"
                
            metadata_block = (
                f"=== [Source {idx}] ===\n"
                f"TITLE: {title}\n"
                f"URL: {url}\n"
                f"SOURCE TYPE: {source_type}\n"
                f"TRUST ASSESSMENT: {trust_label} (Score: {trust_score:.2f})\n"
                f"RELEVANCE SCORE: {src.get('relevance_score', 0.70):.2f}\n"
                f"--- EVIDENCE SNIPPET ---\n"
                f"{content}\n"
                f"========================\n\n"
            )
            
            context_blocks.append(metadata_block)
            
        context_string = "".join(context_blocks)
        return context_string, attribution_map
