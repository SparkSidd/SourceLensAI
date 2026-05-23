import asyncio
import os
import uuid
from typing import Optional, List

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.config import WORKSPACE_DIR, SANDBOX_MODE
from backend.app.database.connection import get_db, init_db
from backend.app.orchestrator import ResearchOrchestrator
from backend.app.streaming.feed import FeedService
from backend.app.memory.graph import ResearchGraphMemory
from backend.app.memory.followup import FollowupMemoryLayer
from backend.app.models.models import SessionModel, ReportModel, SourceModel

# ──────────────────────────────────────────────
#  App Initialisation
# ──────────────────────────────────────────────
app = FastAPI(
    title="SourceLens AI — Core Intelligence Engine",
    description=(
        "Modular async multi-pipeline research orchestration backend. "
        "Grounded synthesis, citation mapping, contradiction detection, SSE streaming."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton orchestrator (holds retrieval engine instances)
orchestrator = ResearchOrchestrator()

# In-memory file cache: session_id → list of {filename, content}
session_uploads: dict = {}


# ──────────────────────────────────────────────
#  Lifecycle Events
# ──────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Initialise all SQLAlchemy ORM tables on startup."""
    await init_db()
    print("[MAIN] SourceLens AI backend ready.")


# ──────────────────────────────────────────────
#  Frontend
# ──────────────────────────────────────────────
@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve the interactive research canvas SPA."""
    frontend_path = os.path.join(WORKSPACE_DIR, "code.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    return {
        "message": "SourceLens AI is running.",
        "sandbox_mode": SANDBOX_MODE,
        "docs": "/docs",
    }


# ──────────────────────────────────────────────
#  Request Schemas
# ──────────────────────────────────────────────
class ResearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class FollowupRequest(BaseModel):
    query: str
    session_id: str


# ──────────────────────────────────────────────
#  Helper — background wrapper that creates its own DB session
# ──────────────────────────────────────────────
async def _run_research_background(session_id: str, query: str, uploaded_files: list):
    """
    Background task wrapper.
    FastAPI BackgroundTasks run outside the request's DB session scope,
    so we open a fresh session via the async session factory.
    """
    from backend.app.database.connection import SessionLocal
    async with SessionLocal() as db:
        try:
            await orchestrator.start_research(db, session_id, query, uploaded_files)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"[MAIN] Research pipeline error for session {session_id}: {e}")
        finally:
            await db.close()


async def _run_followup_background(session_id: str, query: str):
    from backend.app.database.connection import SessionLocal
    async with SessionLocal() as db:
        try:
            await FollowupMemoryLayer.process_followup(db, session_id, query)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"[MAIN] Follow-up pipeline error for session {session_id}: {e}")
        finally:
            await db.close()


# ──────────────────────────────────────────────
#  API Routes
# ──────────────────────────────────────────────

# 1. Start Research
@app.post("/research", tags=["Research"])
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger a full research pipeline run.
    Immediately returns a session_id; connect to `/stream/{session_id}` for live updates.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    uploaded_files = session_uploads.pop(session_id, [])

    background_tasks.add_task(
        _run_research_background,
        session_id=session_id,
        query=request.query,
        uploaded_files=uploaded_files,
    )

    return {
        "status": "triggered",
        "session_id": session_id,
        "stream_url": f"/stream/{session_id}",
        "sandbox_mode": SANDBOX_MODE,
        "message": "Pipeline running. Connect to SSE stream for live synthesis.",
    }


# 2. SSE Streaming
@app.get("/stream/{session_id}", tags=["Streaming"])
async def stream_session(session_id: str):
    """
    Server-Sent Events endpoint. Streams live status events, indexed sources,
    report sections, and the final compiled intelligence report.
    """
    async def event_generator():
        queue = FeedService.subscribe(session_id)
        try:
            yield (
                'data: {"event":"status","message":"SSE connection established '
                'with SourceLens Core Engine."}\n\n'
            )
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    # Send keep-alive ping every 120 s to prevent proxy timeout
                    yield ": ping\n\n"
                    continue

                yield f"data: {event}\n\n"

                if '"event": "complete"' in event or '"event":"complete"' in event:
                    break

        except asyncio.CancelledError:
            print(f"[MAIN] SSE client disconnected: {session_id}")
        finally:
            FeedService.unsubscribe(session_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# 3. Follow-Up Question
@app.post("/followup", tags=["Research"])
async def followup_research(
    request: FollowupRequest,
    background_tasks: BackgroundTasks,
):
    """
    Ask a contextual follow-up using cached session sources — no re-retrieval.
    Stream the response on `/stream/{session_id}`.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Follow-up query cannot be empty.")

    background_tasks.add_task(
        _run_followup_background,
        session_id=request.session_id,
        query=request.query,
    )

    return {
        "status": "triggered",
        "session_id": request.session_id,
        "stream_url": f"/stream/{request.session_id}",
        "message": "Follow-up synthesis queued. Stream response on SSE channel.",
    }


# 4. Upload PDF
@app.post("/upload", tags=["Documents"])
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a PDF document to attach to the next research query in the session.
    The file is cached in memory until `/research` is called with the same session_id.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    session_uploads.setdefault(session_id, []).append({
        "filename": file.filename,
        "content": content,
    })

    return {
        "status": "uploaded",
        "filename": file.filename,
        "size_kb": round(len(content) / 1024, 1),
        "message": f"'{file.filename}' cached. Trigger /research with session_id='{session_id}' to index it.",
    }


# 5. Get Session Reports
@app.get("/research/{session_id}", tags=["Reports"])
async def get_session_reports(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all synthesized reports for a session."""
    result = await db.execute(
        select(ReportModel).where(ReportModel.session_id == session_id)
    )
    reports = result.scalars().all()
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for this session.")

    return {
        "session_id": session_id,
        "reports": [
            {
                "id": r.id,
                "summary": r.summary,
                "findings": r.findings,
                "perspectives": r.perspectives,
                "contradictions": r.contradictions,
                "limitations": r.limitations,
                "conclusions": r.conclusions,
                "confidence_score": r.confidence_score,
                "confidence_level": r.confidence_level,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
    }


# 6. Get Session Sources
@app.get("/sources/{session_id}", tags=["Reports"])
async def get_session_sources(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all indexed sources for a session."""
    result = await db.execute(
        select(SourceModel).where(SourceModel.session_id == session_id)
    )
    sources = result.scalars().all()
    return {
        "session_id": session_id,
        "sources": [
            {
                "id": s.id,
                "title": s.title,
                "url": s.url,
                "content": s.content,
                "source_type": s.source_type,
                "trust_score": s.trust_score,
                "relevance_score": s.relevance_score,
            }
            for s in sources
        ],
    }


# 7. Get Session Knowledge Graph
@app.get("/graph/{session_id}", tags=["Reports"])
async def get_session_graph(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the research knowledge graph nodes and edges for a session."""
    graph = await ResearchGraphMemory.get_session_graph(db, session_id)
    return {"session_id": session_id, "graph": graph}


# 8. Research History
@app.get("/history", tags=["Reports"])
async def get_history(db: AsyncSession = Depends(get_db)):
    """Return all past research sessions."""
    result = await db.execute(select(SessionModel).order_by(SessionModel.created_at.desc()))
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ]
    }


# 9. Health Check
@app.get("/health", tags=["System"])
async def health_check():
    """Quick health check for load balancers and uptime monitors."""
    return {
        "status": "healthy",
        "sandbox_mode": SANDBOX_MODE,
        "version": "2.0.0",
    }
