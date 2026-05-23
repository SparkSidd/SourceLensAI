import asyncio
import uuid
import json
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.services.query_engine import QueryEngine
from backend.app.sources.source_router import SourceRouter
from backend.app.retrieval.engine import ParallelRetrievalEngine
from backend.app.sources.pdf_processor import PdfProcessor
from backend.app.ranking.engine import DeduplicationRankingEngine
from backend.app.synthesis.engine import GroundedSynthesisEngine
from backend.app.services.citations import CitationMapper
from backend.app.services.confidence import ConfidenceAnalyzer
from backend.app.services.contradiction import ContradictionDetector
from backend.app.memory.graph import ResearchGraphMemory
from backend.app.streaming.feed import FeedService

from backend.app.models.models import (
    SessionModel, QueryModel, SourceModel, ReportModel, CitationModel, ContradictionModel
)

class ResearchOrchestrator:
    def __init__(self):
        self.retrieval_engine = ParallelRetrievalEngine()

    async def start_research(
        self, 
        db: AsyncSession, 
        session_id: str, 
        query: str, 
        uploaded_files: List[Dict[str, Any]] = None
    ) -> str:
        """
        Main research pipeline execution flow.
        Runs intent models, queries active nodes concurrently, deduplicates, scans contradictions,
        streams synthesis chunks, and writes ORM assets.
        """
        query_id = f"q_{uuid.uuid4().hex[:8]}"
        report_id = f"rep_{uuid.uuid4().hex[:8]}"

        # 1. Initialize or get Session
        session_result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
        session_obj = session_result.scalar_one_or_none()
        if not session_obj:
            session_obj = SessionModel(
                id=session_id,
                title=query[:60] + ("..." if len(query) > 60 else "")
            )
            db.add(session_obj)
            await db.commit()

        # 2. Query Understanding intent classification
        await FeedService.publish_event(session_id, "status", "ORION: Running semantic intelligence parser...")
        await asyncio.sleep(0.3)
        
        analysis = await QueryEngine.analyze_query(query)
        domain = analysis.get("domain", "general")

        # Save query parameters
        query_obj = QueryModel(
            id=query_id,
            session_id=session_id,
            query=query,
            domain=domain
        )
        db.add(query_obj)
        await db.commit()

        await FeedService.publish_event(
            session_id,
            "status",
            f"Intent Classified. Domain: '{domain.upper()}' | Intent: '{analysis.get('research_intent', 'MEDIUM').upper()}'",
            metadata=analysis
        )

        # 3. Source Router decisions
        has_uploads = bool(uploaded_files)
        active_sources = SourceRouter.route_sources(analysis, uploaded_files_exist=has_uploads)

        await FeedService.publish_event(
            session_id,
            "status",
            f"Adaptive Source Router activated. Selected nodes: {', '.join([s.upper() for s in active_sources])}"
        )
        await asyncio.sleep(0.3)

        # 4. Spawning parallel retrievers
        retrieved_items = []
        
        # Build search variants string
        search_query = analysis.get("search_variants", [query])[0]
        retrieval_task = asyncio.create_task(
            self.retrieval_engine.execute_retrieval(search_query, [s for s in active_sources if s != "upload"], session_id)
        )

        # Check and process uploaded document buffers in parallel
        upload_items = []
        if has_uploads and uploaded_files:
            await FeedService.publish_event(session_id, "status", f"Processing {len(uploaded_files)} PDF attachments...")
            for uf in uploaded_files:
                name = uf.get("filename", "document.pdf")
                file_bytes = uf.get("content", b"")
                chunks = PdfProcessor.parse_pdf(file_bytes, name)
                upload_items.extend(chunks)
                
                await FeedService.publish_event(
                    session_id,
                    "source_discovered",
                    f"Parsed PDF upload: {name}",
                    metadata={"title": name, "source_type": "upload"}
                )

        # Wait for crawler arrays
        remote_results = await retrieval_task
        retrieved_items.extend(remote_results)
        retrieved_items.extend(upload_items)

        # Broadcast all discovered items down the SSE pipeline
        for idx, item in enumerate(retrieved_items, start=1):
            src_type = item.get("source_type", "web").upper()
            title = item.get("title", "")
            await FeedService.publish_event(
                session_id,
                "source_discovered",
                f"Source Crawled [{src_type}]: {title[:60]}...",
                metadata={"title": title, "url": item.get("url"), "source_type": item.get("source_type")}
            )
            await asyncio.sleep(0.05)

        if not retrieved_items:
            await FeedService.publish_event(session_id, "status", "Error: No relevant references retrieved. Ending run.")
            return report_id

        # 5. Jaccard & Trust Re-ranking
        await FeedService.publish_event(session_id, "status", "Running Jaccard Deduplication & Trust Ranking...")
        await asyncio.sleep(0.3)
        
        ranked_sources = DeduplicationRankingEngine.deduplicate_and_rank(retrieved_items, query)
        top_ranked = ranked_sources[:12] # Keep top 12 authoritative pages for maximized research workbench coverage

        # Persist sources to relational SQL
        attribution_map = {}
        for idx, src in enumerate(top_ranked, start=1):
            src_uuid = f"src_{uuid.uuid4().hex[:8]}"
            src["id"] = src_uuid
            attribution_map[idx] = src

            src_model = SourceModel(
                id=src_uuid,
                session_id=session_id,
                title=src.get("title"),
                url=src.get("url"),
                content=src.get("content"),
                source_type=src.get("source_type", "web"),
                trust_score=src.get("trust_score", 0.7),
                relevance_score=src.get("relevance_score", 0.7)
            )
            db.add(src_model)
            
            await FeedService.publish_event(
                session_id,
                "paper_indexed",
                f"Source Indexed [{src.get('source_type').upper()}]: {src.get('title')[:55]}...",
                metadata=src
            )
        await db.commit()

        # 6. Factual Contradiction detection
        await FeedService.publish_event(session_id, "status", "Scanning cross-references for fact gaps...")
        await asyncio.sleep(0.3)

        contradictions = await ContradictionDetector.detect_contradictions(top_ranked, query)
        for c in contradictions:
            contradiction_model = ContradictionModel(
                session_id=session_id,
                aspect=c.get("aspect", ""),
                source_a=c.get("source_a", ""),
                source_b=c.get("source_b", ""),
                conflict_details=c.get("conflict_details", ""),
                reconciliation_hint=c.get("reconciliation_hint", "")
            )
            db.add(contradiction_model)
            
            await FeedService.publish_event(
                session_id,
                "status",
                f"WARNING: Cross-reference discrepancy found: '{c.get('aspect')}'",
                metadata=c
            )
            await asyncio.sleep(0.3)
        await db.commit()

        # 7. Compile grounded context
        context_blocks = []
        for idx, src in enumerate(top_ranked, start=1):
            context_blocks.append(
                f"Source [{idx}]\n"
                f"Title: {src.get('title')}\n"
                f"URL: {src.get('url')}\n"
                f"Content: {src.get('content')}\n"
            )
        context_str = "\n\n".join(context_blocks)

        # 8. Trigger Grounded Synthesis stream
        await FeedService.publish_event(session_id, "status", "Initializing synthesis engine...")
        
        report_data = {
            "summary": "",
            "findings": [],
            "perspectives": [],
            "contradictions": [c.get("conflict_details", "") for c in contradictions],
            "limitations": [],
            "conclusions": []
        }

        async for chunk_str in GroundedSynthesisEngine.synthesize_stream(context_str, query):
            chunk = json.loads(chunk_str)
            event_type = chunk.get("event")

            if event_type == "status":
                await FeedService.publish_event(session_id, "status", chunk.get("data"))
            elif event_type == "report_section":
                meta = chunk.get("metadata", {})
                sec = meta.get("section")
                val = meta.get("content")
                
                report_data[sec] = val
                
                await FeedService.publish_event(
                    session_id,
                    "report_section",
                    f"Generated section: {sec.upper()}",
                    metadata={"section": sec, "content": val}
                )
            elif event_type == "complete":
                report_data = chunk.get("report")

        # 9. Confidence evaluation
        confidence_details = ConfidenceAnalyzer.analyze_confidence(top_ranked, report_data.get("contradictions", []))
        report_data["confidence_score"] = confidence_details.get("score")
        report_data["confidence_level"] = confidence_details.get("level")

        await FeedService.publish_event(
            session_id,
            "evidence_validated",
            f"Grounding validated. Confidence level: '{confidence_details.get('level').upper()}'",
            metadata=confidence_details
        )

        # 10. Citation Mapping
        citation_links = CitationMapper.map_report_citations(report_data, attribution_map)

        # 11. Relational Memory Graph mapping
        graph_data = await ResearchGraphMemory.build_and_save_graph(
            db, session_id, query, domain, top_ranked
        )

        # 12. Save compiled Report & Citations to SQL ORM
        report_model = ReportModel(
            id=report_id,
            session_id=session_id,
            query_id=query_id,
            summary=report_data.get("summary", ""),
            findings=report_data.get("findings", []),
            perspectives=report_data.get("perspectives", []),
            contradictions=report_data.get("contradictions", []),
            limitations=report_data.get("limitations", []),
            conclusions=report_data.get("conclusions", []),
            confidence_score=report_data.get("confidence_score", 0.0),
            confidence_level=report_data.get("confidence_level", "medium")
        )
        db.add(report_model)
        await db.commit()

        # Save individual Citations
        for link in citation_links:
            cite_model = CitationModel(
                report_id=report_id,
                source_id=link.get("source_id"),
                claim_context=link.get("claim_context", "")
            )
            db.add(cite_model)
        await db.commit()

        # 13. Publish complete payload
        await FeedService.publish_event(
            session_id,
            "complete",
            "SourceLens Research complete.",
            metadata={
                "report_id": report_id,
                "report": report_data,
                "citations": citation_links,
                "graph": graph_data,
                "confidence": confidence_details
            }
        )

        return report_id
