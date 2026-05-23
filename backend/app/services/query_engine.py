import re
import json
import google.generativeai as genai
from backend.app.core.config import SANDBOX_MODE, GEMINI_API_KEY, LLM_MODEL

if not SANDBOX_MODE:
    genai.configure(api_key=GEMINI_API_KEY)

class QueryEngine:
    @staticmethod
    def _classify_rules(query: str) -> dict:
        """Fallback rule-based classification if Gemini is offline or in Sandbox Mode."""
        query_lower = query.lower()
        
        # Determine Domain
        if any(w in query_lower for w in ["cve", "exploit", "hack", "cyber", "malware", "ransomware", "vulnerability", "phishing", "zero-day", "security"]):
            domain = "cybersecurity"
            sources = ["tavily", "arxiv", "github"]
        elif any(w in query_lower for w in ["arxiv", "paper", "study", "research", "evolution", "neural", "proof", "theorem", "quantum", "science", "physics"]):
            domain = "academic"
            sources = ["arxiv", "wikipedia", "tavily"]
        elif any(w in query_lower for w in ["git", "code", "repo", "github", "npm", "pip", "docker", "compile", "quantization", "api", "framework", "quantize"]):
            domain = "technical"
            sources = ["github", "tavily", "wikipedia"]
        elif any(w in query_lower for w in ["market", "competitor", "finance", "stock", "startup", "trend", "industry", "saas", "pricing"]):
            domain = "market"
            sources = ["tavily", "wikipedia"]
        elif any(w in query_lower for w in ["investigate", "verify", "claim", "contradict", "dispute", "fact-check", "truth"]):
            domain = "investigative"
            sources = ["tavily", "wikipedia", "arxiv"]
        else:
            domain = "general"
            sources = ["tavily", "wikipedia"]
            
        # Detect security/academic/technical focus flags
        is_academic = domain == "academic" or "paper" in query_lower or "research" in query_lower
        is_technical = domain == "technical" or "code" in query_lower or "quantization" in query_lower
        is_security = domain == "cybersecurity" or "vulnerability" in query_lower
        
        # Search variations
        words = [w for w in re.split(r'\W+', query_lower) if len(w) > 3]
        variations = []
        if len(words) >= 2:
            variations.append(" ".join(words[:3]))
            variations.append(" ".join(words[-3:]))
        variations.append(query)
        # Unique list
        variations = list(set(variations))
        
        return {
            "domain": domain,
            "research_intent": "high" if (is_academic or is_technical or is_security) else "medium",
            "preferred_sources": sources,
            "is_academic": is_academic,
            "is_technical": is_technical,
            "is_security": is_security,
            "ambiguity_detected": len(query.strip()) < 15,
            "search_variants": variations[:3],
            "semantic_expansion": f"Deep analysis of {query}",
            "retrieval_hints": f"Focus on {domain} authoritative documents and primary material."
        }

    @classmethod
    async def analyze_query(cls, query: str) -> dict:
        """Asynchronously analyzes and enriches the user's research query."""
        if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "":
            return cls._classify_rules(query)
            
        try:
            model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={"response_mime_type": "application/json"}
            )
            
            prompt = f"""
            You are the core Query Understanding Engine for SourceLens AI.
            Analyze this research query: "{query}"
            
            Provide a highly accurate classification JSON with:
            {{
              "domain": "academic" | "cybersecurity" | "technical" | "market" | "investigative" | "general",
              "research_intent": "low" | "medium" | "high",
              "preferred_sources": ["tavily", "arxiv", "wikipedia", "github"],
              "is_academic": true/false,
              "is_technical": true/false,
              "is_security": true/false,
              "ambiguity_detected": true/false,
              "search_variants": ["at least two optimized key phrases for web/academic search"],
              "semantic_expansion": "an expanded sentence reflecting the core research question and technical context",
              "retrieval_hints": "specific metadata fields, paper keywords, or code structures to look for"
            }}
            """
            
            response = await model.generate_content_async(prompt)
            data = json.loads(response.text.strip())
            return data
            
        except Exception as e:
            print(f"[QUERY ENGINE] Gemini query analysis failed: {e}. Falling back to rule-based engine.")
            return cls._classify_rules(query)
