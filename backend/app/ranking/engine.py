import re
from typing import List, Dict, Any

class DeduplicationRankingEngine:
    @classmethod
    def deduplicate_and_rank(cls, items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Process, filter, and score collected resources based on authority, freshness, and relevance.
        """
        if not items:
            return []

        # 1. Deduplicate by URL
        seen_urls = set()
        unique_items = []
        
        for item in items:
            url = item.get("url", "").strip()
            if url:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_items.append(item)
            else:
                unique_items.append(item)

        # 2. Semantic Similarity Deduplication (Jaccard Overlap threshold: 0.70)
        filtered_items = []
        for item in unique_items:
            content_a = item.get("content", "")
            is_redundant = False
            
            for approved in filtered_items:
                content_b = approved.get("content", "")
                similarity = cls._calculate_jaccard_similarity(content_a, content_b)
                if similarity > 0.70:
                    is_redundant = True
                    # Keep the one with higher trust score
                    if item.get("trust_score", 0.7) > approved.get("trust_score", 0.7):
                        approved["content"] = item["content"]
                        approved["title"] = item["title"]
                        approved["trust_score"] = item["trust_score"]
                    break
                    
            if not is_redundant:
                filtered_items.append(item)

        # 3. Dynamic Multi-Factor Ranking
        scored_items = []
        source_diversity_tracker = {} # Keep track of how many of each source_type we have mapped
        
        for item in filtered_items:
            src_type = item.get("source_type", "web")
            relevance = item.get("relevance_score", 0.7)
            trust = item.get("trust_score", 0.7)
            
            # Trust Adjustments
            if src_type == "arxiv" or src_type == "upload":
                # Academic papers and uploads are high-trust authority items
                trust = min(1.0, trust + 0.15)
            elif src_type == "github":
                # Repository codes are highly trusted for practical examples
                trust = min(1.0, trust + 0.10)
            elif src_type == "hackernews":
                # Forum arguments are demoted in trust
                trust = max(0.40, trust - 0.15)
                
            # Compute query keyword alignment match density
            query_match = cls._compute_query_match_score(item.get("content", "") + " " + item.get("title", ""), query)
            relevance = min(1.0, relevance + (query_match * 0.15))
            
            # Diversity Factor (give slight preference to items that introduce a new source type)
            diversity_boost = 0.20 if src_type not in source_diversity_tracker else 0.0
            source_diversity_tracker[src_type] = source_diversity_tracker.get(src_type, 0) + 1
            
            # Final Score calculation: 40% Relevance, 40% Trust, 20% Diversity/Freshness
            final_score = (relevance * 0.40) + (trust * 0.40) + (diversity_boost * 0.20)
            item["trust_score"] = round(trust, 2)
            item["relevance_score"] = round(relevance, 2)
            item["ranking_score"] = round(final_score, 2)
            
            scored_items.append(item)
            
        # Sort in descending order based on composite ranking_score
        scored_items.sort(key=lambda x: x.get("ranking_score", 0.0), reverse=True)
        return scored_items

    @staticmethod
    def _calculate_jaccard_similarity(text_a: str, text_b: str) -> float:
        """Computes structural token intersection over union ratio."""
        words_a = set(re.findall(r'\b\w{3,}\b', text_a.lower()))
        words_b = set(re.findall(r'\b\w{3,}\b', text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / len(union)

    @staticmethod
    def _compute_query_match_score(text: str, query: str) -> float:
        """Scours query terms density inside text body."""
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        if not query_words:
            return 0.0
            
        text_lower = text.lower()
        matched = sum(1 for w in query_words if w in text_lower)
        return matched / len(query_words)
