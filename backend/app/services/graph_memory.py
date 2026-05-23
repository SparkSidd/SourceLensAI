from typing import List, Dict, Any
import re

class GraphMemory:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        
    def add_node(self, node_id: str, label: str, properties: Dict[str, Any]):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "properties": properties
        }
        
    def add_edge(self, source_id: str, target_id: str, relationship: str):
        self.edges.append({
            "source": source_id,
            "target": target_id,
            "relationship": relationship
        })

    def build_session_graph(
        self, 
        query: str, 
        domain: str, 
        ranked_sources: List[Dict[str, Any]], 
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Populate nodes and edges for queries, extracted entities, and research documents,
        and generate related queries suggestions.
        """
        # Reset graph state
        self.nodes = {}
        self.edges = []
        
        # 1. Add Query Node
        q_node_id = "query_1"
        self.add_node(q_node_id, "Query", {"text": query, "domain": domain})
        
        # 2. Extract Entities (simple regex noun/technical keywords matcher)
        entities = []
        keywords = re.findall(r'\b[A-Za-z0-9\-]{4,}\b', query)
        stop_words = {"what", "how", "why", "the", "and", "under", "with", "that", "these", "this", "from", "their", "impact"}
        filtered_keywords = [k for k in keywords if k.lower() not in stop_words][:4]
        
        for idx, k in enumerate(filtered_keywords):
            ent_node_id = f"entity_{idx}"
            self.add_node(ent_node_id, "Entity", {"name": k})
            self.add_edge(q_node_id, ent_node_id, "references")
            entities.append(k)
            
        # 3. Add Source Nodes and Connect
        for idx, src in enumerate(ranked_sources, start=1):
            src_node_id = f"source_{idx}"
            self.add_node(src_node_id, "Source", {
                "title": src.get("title"),
                "url": src.get("url"),
                "source_type": src.get("source_type")
            })
            self.add_edge(q_node_id, src_node_id, "retrieved")
            
            # Link entities to sources if they overlap
            for ent_idx, k in enumerate(filtered_keywords):
                ent_node_id = f"entity_{ent_idx}"
                content = src.get("content", "").lower()
                if k.lower() in content:
                    self.add_edge(src_node_id, ent_node_id, "discusses")
                    
        # 4. Generate related suggestions based on entities and domain
        related_suggestions = self._generate_related_suggestions(query, domain, entities)
        
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "related_suggestions": related_suggestions
        }

    def _generate_related_suggestions(self, query: str, domain: str, entities: List[str]) -> List[str]:
        """Generates dynamic related questions based on entities and research domains."""
        suggestions = []
        ent_str = " & ".join(entities) if entities else "these concepts"
        
        if domain == "cybersecurity":
            suggestions = [
                f"What are the permanent mitigation strategies for {ent_str} exploits?",
                f"Analyze similar CVE advisories published during the same quarter.",
                f"Verify memory overflow signatures of {ent_str} inside custom kernel builds."
            ]
        elif domain == "academic":
            suggestions = [
                f"What are the mathematical limitations of continuous search space designs?",
                f"Explore alternative zero-cost proxy equations in modern NAS benchmarks.",
                f"Identify subsequent peer-reviewed papers citing these active methodologies."
            ]
        elif domain == "technical":
            suggestions = [
                f"Examine compilation options to eliminate quantization memory alignment issues.",
                f"Compare edge latency figures of FP32 vs 8-bit integer inference on heterogeneous accelerators.",
                f"Locate open-source repos demonstrating custom runtime virtualization hooks."
            ]
        else:
            suggestions = [
                f"Detail industrial use-cases implementing {ent_str}.",
                f"Are there any open disputes or conflicting benchmarks on {ent_str}?",
                f"Synthesize market capitalization projections regarding these emerging trends."
            ]
            
        return suggestions
