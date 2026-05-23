import uuid
from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import SourceModel, QueryModel, ReportModel, FollowupModel
from backend.app.ranking.engine import DeduplicationRankingEngine
from backend.app.synthesis.engine import GroundedSynthesisEngine
from backend.app.streaming.feed import FeedService

class FollowupMemoryLayer:
    @staticmethod
    async def process_followup(
        db: AsyncSession, 
        session_id: str, 
        followup_query: str
    ) -> Dict[str, Any]:
        """
        Processes a conversation follow-up using cached session evidence.
        Saves follow-up metrics and returns a synthesized responsive report.
        """
        # 1. Retrieve all sources saved in current session
        result = await db.execute(
            select(SourceModel).where(SourceModel.session_id == session_id)
        )
        sources = result.scalars().all()
        
        # Format database models into normalized dictionaries
        source_items = []
        for src in sources:
            source_items.append({
                "id": src.id,
                "title": src.title,
                "url": src.url,
                "content": src.content,
                "source_type": src.source_type,
                "trust_score": src.trust_score,
                "relevance_score": src.relevance_score
            })

        # Save Followup query block to database
        new_followup = FollowupModel(
            session_id=session_id,
            query=followup_query,
            response_summary=""
        )
        db.add(new_followup)
        await db.commit()

        if not source_items:
            # No existing sources, return fallback warning
            return {
                "summary": "No cached evidence sources exist in the current session workspace coordinates. Please trigger a master search first.",
                "findings": [],
                "perspectives": [],
                "contradictions": [],
                "limitations": [],
                "conclusions": []
            }

        # 2. Re-rank cached sources relative to the follow-up question
        await FeedService.publish_event(session_id, "status", "Accessing existing session clippings database...")
        ranked_sources = DeduplicationRankingEngine.deduplicate_and_rank(source_items, followup_query)

        # 3. Compile context from best matching sources
        context_blocks = []
        for idx, src in enumerate(ranked_sources[:5], start=1):
            context_blocks.append(
                f"Source [{idx}]\n"
                f"Title: {src.get('title')}\n"
                f"URL: {src.get('url')}\n"
                f"Content: {src.get('content')}\n"
            )
        context_str = "\n\n".join(context_blocks)

        # 4. Stream response synthesis from Synthesis Engine
        await FeedService.publish_event(session_id, "status", f"Re-anchored {len(ranked_sources)} source elements. Triggering follow-up synthesis...")
        
        full_response = {
            "summary": "",
            "findings": [],
            "perspectives": [],
            "contradictions": [],
            "limitations": [],
            "conclusions": []
        }

        async for chunk_str in GroundedSynthesisEngine.synthesize_stream(context_str, followup_query):
            import json
            chunk = json.loads(chunk_str)
            ev = chunk.get("event")
            
            if ev == "report_section":
                meta = chunk.get("metadata", {})
                sec = meta.get("section")
                val = meta.get("content")
                full_response[sec] = val
                
                # Relabel follow-up progress logs
                await FeedService.publish_event(
                    session_id, 
                    "report_section", 
                    f"Generated follow-up section: {sec.upper()}",
                    metadata={"section": sec, "content": val}
                )
            elif ev == "complete":
                full_response = chunk.get("report")
                
        # Update followup response summary in DB
        new_followup.response_summary = full_response.get("summary", "")[:255]
        db.add(new_followup)
        await db.commit()

        await FeedService.publish_event(
            session_id, 
            "complete", 
            "Follow-up synthesis complete.",
            metadata={
                "report": full_response,
                "confidence": {"score": 0.80, "level": "medium"}
            }
        )

        return full_response
