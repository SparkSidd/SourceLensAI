import re
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.models import GraphNodeModel, GraphEdgeModel

class ResearchGraphMemory:
    @classmethod
    async def build_and_save_graph(
        cls, 
        db: AsyncSession, 
        session_id: str, 
        query: str, 
        domain: str, 
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract entities, build query-source-entity graph nodes & edges,
        and persist them to the database. Generates contextual related queries.
        """
        nodes = []
        edges = []

        # 1. Create Query Node
        q_id = f"q_{session_id}"
        q_node = GraphNodeModel(
            id=q_id,
            session_id=session_id,
            label="Query",
            properties={"text": query, "domain": domain}
        )
        db.add(q_node)
        nodes.append({"id": q_id, "label": "Query", "properties": {"text": query, "domain": domain}})

        # 2. Extract Entities (excluding stop words)
        words = re.findall(r'\b[A-Za-z0-9\-]{4,}\b', query)
        stop_words = {"what", "how", "why", "their", "under", "impact", "with", "from", "these", "this", "that"}
        keywords = [w.lower() for w in words if w.lower() not in stop_words][:4]

        for idx, kw in enumerate(keywords):
            ent_id = f"ent_{session_id}_{idx}"
            ent_node = GraphNodeModel(
                id=ent_id,
                session_id=session_id,
                label="Entity",
                properties={"name": kw}
            )
            db.add(ent_node)
            nodes.append({"id": ent_id, "label": "Entity", "properties": {"name": kw}})

            # Connect Query to Entity
            edge = GraphEdgeModel(
                session_id=session_id,
                source_node=q_id,
                target_node=ent_id,
                relationship="references"
            )
            db.add(edge)
            edges.append({"source": q_id, "target": ent_id, "relationship": "references"})

        # 3. Create Source Nodes & Connect
        for idx, src in enumerate(sources, start=1):
            src_id = src.get("id") or f"src_{session_id}_{idx}"
            
            src_node = GraphNodeModel(
                id=src_id,
                session_id=session_id,
                label="Source",
                properties={
                    "title": src.get("title"),
                    "url": src.get("url"),
                    "source_type": src.get("source_type")
                }
            )
            db.add(src_node)
            nodes.append({
                "id": src_id, 
                "label": "Source", 
                "properties": {
                    "title": src.get("title"), 
                    "url": src.get("url")
                }
            })

            # Query retrieved Source
            edge = GraphEdgeModel(
                session_id=session_id,
                source_node=q_id,
                target_node=src_id,
                relationship="retrieved"
            )
            db.add(edge)
            edges.append({"source": q_id, "target": src_id, "relationship": "retrieved"})

            # Check overlap between entities and source text
            content_lower = src.get("content", "").lower()
            for ent_idx, kw in enumerate(keywords):
                ent_id = f"ent_{session_id}_{ent_idx}"
                if kw in content_lower:
                    ent_edge = GraphEdgeModel(
                        session_id=session_id,
                        source_node=src_id,
                        target_node=ent_id,
                        relationship="discusses"
                    )
                    db.add(ent_edge)
                    edges.append({"source": src_id, "target": ent_id, "relationship": "discusses"})

        await db.commit()

        # 4. Generate related suggestions based on keywords
        suggestions = cls._generate_topic_suggestions(domain, keywords)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "related_suggestions": suggestions
        }

    @staticmethod
    def _generate_topic_suggestions(domain: str, keywords: List[str]) -> List[str]:
        """Generates dynamic analytical follow-up questions for the research sidebar."""
        concepts = " & ".join(keywords) if keywords else "these topics"
        
        if domain == "cybersecurity":
            return [
                f"What are the permanent perimeter mitigation plans for {concepts} exploits?",
                f"Analyze similar CVE logs released in the same quarter.",
                f"Verify memory overflow signatures of {concepts} in custom builds."
            ]
        elif domain == "academic":
            return [
                f"Identify subsequent peer-reviewed papers citing these active methodologies.",
                f"Explore alternate zero-cost proxy models in modern benchmarks.",
                f"What are the mathematical limitations of search space setups?"
            ]
        return [
            f"Compare edge latency figures of FP32 vs 8-bit integer inference.",
            f"Review industrial implementation case studies on {concepts}."
        ]

    @classmethod
    async def get_session_graph(cls, db: AsyncSession, session_id: str) -> Dict[str, Any]:
        """Fetches all graph node and edge records for a given session ID."""
        node_result = await db.execute(
            select(GraphNodeModel).where(GraphNodeModel.session_id == session_id)
        )
        nodes = node_result.scalars().all()

        edge_result = await db.execute(
            select(GraphEdgeModel).where(GraphEdgeModel.session_id == session_id)
        )
        edges = edge_result.scalars().all()

        return {
            "nodes": [{"id": n.id, "label": n.label, "properties": n.properties} for n in nodes],
            "edges": [{"source": e.source_node, "target": e.target_node, "relationship": e.relationship} for e in edges]
        }
