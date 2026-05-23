from typing import Dict, Any, List

class SourceRouter:
    @staticmethod
    def route_sources(query_analysis: Dict[str, Any], uploaded_files_exist: bool = False) -> List[str]:
        """
        Dynamically route retrieval targets based on query domain and semantic intent classification.
        Returns a list of active retrieval system keys: 'tavily', 'arxiv', 'wikipedia', 'github', 'hackernews', 'rss'.
        """
        domain = query_analysis.get("domain", "general").lower()
        active_sources = []
        
        # Primary upload source is always included if present
        if uploaded_files_exist:
            active_sources.append("upload")
            
        # Domain-driven routing: prioritize domain-relevant sources first
        if domain == "academic":
            active_sources.extend(["arxiv", "wikipedia", "tavily"])
        elif domain == "cybersecurity":
            active_sources.extend(["tavily", "hackernews", "rss"])
        elif domain == "technical":
            active_sources.extend(["github", "hackernews", "tavily"])
        elif domain == "investigative":
            active_sources.extend(["wikipedia", "tavily", "rss"])
        elif domain == "market":
            active_sources.extend(["tavily", "rss"])
        else:
            active_sources.extend(["tavily", "wikipedia", "arxiv"])
        
        # Always include all free sources to maximize retrieval breadth
        # These are free APIs that don't require paid keys
        all_free_sources = ["wikipedia", "arxiv", "github", "hackernews"]
        for src in all_free_sources:
            if src not in active_sources:
                active_sources.append(src)
        
        # Always include tavily if available (requires key but is primary web search)
        if "tavily" not in active_sources:
            active_sources.append("tavily")
            
        # Deduplicate and return routed sources list
        unique_sources = []
        for src in active_sources:
            if src not in unique_sources:
                unique_sources.append(src)
                
        print(f"[ROUTER] Route determined for domain '{domain}'. Activated: {unique_sources}")
        return unique_sources
