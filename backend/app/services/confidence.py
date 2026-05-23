from typing import List, Dict, Any

class ConfidenceAnalyzer:
    @staticmethod
    def analyze_confidence(
        sources: List[Dict[str, Any]], 
        contradictions: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate and output a robust confidence score and rating for research reports.
        """
        if not sources:
            return {
                "score": 0.0,
                "level": "low",
                "metrics": {
                    "source_count": 0,
                    "avg_trust": 0.0,
                    "diversity": 0.0,
                    "contradiction_penalty": 0.0
                },
                "explanations": ["Zero evidence sources retrieved to back the synthesis."]
            }
            
        source_count = len(sources)
        
        # 1. Avg Trust Score
        avg_trust = sum(s.get("trust_score", 0.70) for s in sources) / source_count
        
        # 2. Source Diversity
        source_types = set(s.get("source_type", "web") for s in sources)
        diversity = min(1.0, len(source_types) / 3.0) # Full diversity score if 3+ distinct types
        
        # 3. Contradiction Penalty
        contradiction_count = len(contradictions)
        penalty = min(0.4, contradiction_count * 0.15)
        
        # Calculate Weighted Confidence
        # Score = (Avg Trust * 0.5) + (Diversity * 0.2) + (min(source_count, 5)/5 * 0.3) - Penalty
        volume_score = min(5, source_count) / 5.0
        score = (avg_trust * 0.5) + (diversity * 0.2) + (volume_score * 0.3) - penalty
        score = round(max(0.1, min(1.0, score)), 2)
        
        # Level thresholds
        if score >= 0.80:
            level = "high"
        elif score >= 0.50:
            level = "medium"
        else:
            level = "low"
            
        explanations = []
        if avg_trust >= 0.85:
            explanations.append("High source credibility (academic/official documents predominate).")
        else:
            explanations.append("Moderate or low source authority detected.")
            
        if source_count >= 4:
            explanations.append("Robust evidence volume gathered across multiple pipelines.")
        else:
            explanations.append("Thin evidence volume; synthesis based on few observations.")
            
        if diversity >= 0.80:
            explanations.append("High source diversity (cross-references web, academic, and code repos).")
            
        if contradiction_count > 0:
            explanations.append(f"Detected {contradiction_count} factual contradictions, lowering semantic coherence.")
            
        return {
            "score": score,
            "level": level,
            "metrics": {
                "source_count": source_count,
                "avg_trust": round(avg_trust, 2),
                "diversity": round(diversity, 2),
                "contradiction_penalty": round(penalty, 2)
            },
            "explanations": explanations
        }
