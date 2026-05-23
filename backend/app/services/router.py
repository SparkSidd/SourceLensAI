from typing import List, Dict, Any
from backend.app.services.query_engine import QueryEngine

class SourceRouter:
    @staticmethod
    def route_sources(query_analysis: Dict[str, Any], uploaded_files_exist: bool = False) -> List[str]:
        """
        Dynamically choose search targets based on the query understanding model classification.
        """
        domain = query_analysis.get("domain", "general")
        preferred = query_analysis.get("preferred_sources", ["tavily", "wikipedia"])
        
        sources_to_trigger = []
        
        # Core mappings
        if domain == "cybersecurity":
            # Security research focuses on web articles, technical code, and academic papers
            sources_to_trigger = ["tavily", "github", "arxiv"]
        elif domain == "academic":
            # Academic queries hit research repositories first
            sources_to_trigger = ["arxiv", "wikipedia", "tavily"]
        elif domain == "technical":
            # Technical questions route to code base and developer docs
            sources_to_trigger = ["github", "tavily", "wikipedia"]
        elif domain == "market_research":
            # Market updates need real-time search and general descriptions
            sources_to_trigger = ["tavily", "wikipedia"]
        elif domain == "investigative":
            # Investigative analysis seeks news, reference databases, and academic details
            sources_to_trigger = ["tavily", "wikipedia", "arxiv"]
        else:
            sources_to_trigger = ["tavily", "wikipedia"]
            
        # Ensure fallback includes the preferred sources identified by the LLM
        for p in preferred:
            if p not in sources_to_trigger:
                sources_to_trigger.append(p)
                
        # If files have been uploaded (e.g. PDFs), always include "upload"
        if uploaded_files_exist:
            sources_to_trigger.append("upload")
            
        print(f"[ROUTER] Routed query domain '{domain}' to sources: {sources_to_trigger}")
        return sources_to_trigger
