import re
from typing import List, Dict, Any

class CitationMapper:
    @staticmethod
    def extract_citations(text: str) -> List[int]:
        """Finds all citation indexes like [1], [2], [10] in a text block."""
        matches = re.findall(r'\[(\d+)\]', text)
        return list(set(int(m) for m in matches))

    @classmethod
    def map_report_citations(
        cls, 
        report_data: Dict[str, Any], 
        attribution_map: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Processes report text sections and builds a structured citation graph.
        Returns a list of citation mappings ready for frontend rendering.
        """
        citations_graph = []
        
        # We will parse citations across different sections
        text_to_examine = []
        
        # Summary
        if "summary" in report_data and isinstance(report_data["summary"], str):
            text_to_examine.append(("summary", report_data["summary"]))
            
        # Findings
        if "findings" in report_data and isinstance(report_data["findings"], list):
            for i, find in enumerate(report_data["findings"]):
                text_to_examine.append((f"finding_{i}", find))
                
        # Perspectives
        if "perspectives" in report_data and isinstance(report_data["perspectives"], list):
            for i, pers in enumerate(report_data["perspectives"]):
                text_to_examine.append((f"perspective_{i}", pers))
                
        # Contradictions
        if "contradictions" in report_data and isinstance(report_data["contradictions"], list):
            for i, contr in enumerate(report_data["contradictions"]):
                text_to_examine.append((f"contradiction_{i}", contr))
                
        for section, content_text in text_to_examine:
            indexes = cls.extract_citations(content_text)
            for idx in indexes:
                if idx in attribution_map:
                    source_info = attribution_map[idx]
                    citations_graph.append({
                        "section": section,
                        "citation_index": idx,
                        "source_id": source_info.get("id"),
                        "title": source_info.get("title"),
                        "url": source_info.get("url"),
                        "source_type": source_info.get("source_type"),
                        "claim_context": content_text[:150] + "..." if len(content_text) > 150 else content_text
                    })
                    
        return citations_graph
