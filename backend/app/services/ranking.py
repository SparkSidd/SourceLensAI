from typing import List, Dict, Any
import re

class RankingEngine:
    @staticmethod
    def _calculate_jaccard_similarity(str1: str, str2: str) -> float:
        """Calculates token-based Jaccard similarity between two strings."""
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    @classmethod
    def deduplicate_and_rank(cls, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Deduplicates sources by URL and filters out semantically redundant text.
        Then ranks items based on trustworthiness, relevance, and fresh-weighting.
        """
        # 1. URL Deduplication
        seen_urls = set()
        unique_by_url = []
        for src in sources:
            url = src.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_by_url.append(src)
                
        # 2. Semantic Redundancy Filtering (Jaccard threshold = 0.70)
        filtered_sources = []
        for src in unique_by_url:
            content = src.get("content", "")
            is_redundant = False
            for existing in filtered_sources:
                existing_content = existing.get("content", "")
                similarity = cls._calculate_jaccard_similarity(content, existing_content)
                if similarity > 0.70:
                    is_redundant = True
                    # Keep the one with the higher relevance or trust
                    if (src.get("relevance_score", 0) + src.get("trust_score", 0)) > \
                       (existing.get("relevance_score", 0) + existing.get("trust_score", 0)):
                        existing["content"] = src["content"] # Update existing with better content
                        existing["title"] = src["title"]
                        existing["relevance_score"] = src["relevance_score"]
                        existing["trust_score"] = src["trust_score"]
                    break
            if not is_redundant:
                filtered_sources.append(src)
                
        # 3. Trust Score Adjustments by DomainCredibility
        for src in filtered_sources:
            src_type = src.get("source_type", "")
            url = src.get("url", "").lower()
            
            # Boost high-authority suffixes
            boost = 0.0
            if ".gov" in url or ".edu" in url:
                boost = 0.15
            elif "github.com" in url:
                boost = 0.05
            elif "arxiv.org" in url:
                boost = 0.20
            elif "wikipedia.org" in url:
                boost = 0.10
                
            # Demote opinion blogs and forums
            demotion = 0.0
            if any(w in url for w in ["reddit.com", "medium.com", "substack.com", "blogspot.com"]):
                demotion = 0.25
                src["source_type"] = "opinion"
                
            # Apply bounds
            src["trust_score"] = min(1.0, max(0.1, src.get("trust_score", 0.70) + boost - demotion))
            
            # 4. Synthesize Final Rank Score
            # Rank = 50% trust + 50% relevance
            src["rank_score"] = round((src["trust_score"] * 0.5) + (src["relevance_score"] * 0.5), 2)
            
        # Sort desc
        ranked = sorted(filtered_sources, key=lambda x: x.get("rank_score", 0), reverse=True)
        
        print(f"[RANKING ENGINE] Input sources: {len(sources)} | Deduplicated/Ranked: {len(ranked)}")
        return ranked
