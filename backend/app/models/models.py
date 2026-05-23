from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.app.database.connection import Base

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    queries = relationship("QueryModel", back_populates="session", cascade="all, delete-orphan")
    sources = relationship("SourceModel", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="session", cascade="all, delete-orphan")

class QueryModel(Base):
    __tablename__ = "queries"

    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    domain = Column(String(100), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="queries")
    reports = relationship("ReportModel", back_populates="query")

class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    source_type = Column(String(50), default="web")
    trust_score = Column(Float, default=0.7)
    relevance_score = Column(Float, default=0.7)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="sources")
    citations = relationship("CitationModel", back_populates="source", cascade="all, delete-orphan")

class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    query_id = Column(String(50), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)
    findings = Column(JSON, nullable=True)
    perspectives = Column(JSON, nullable=True)
    contradictions = Column(JSON, nullable=True)
    limitations = Column(JSON, nullable=True)
    conclusions = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.0)
    confidence_level = Column(String(50), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="reports")
    query = relationship("QueryModel", back_populates="reports")
    citations = relationship("CitationModel", back_populates="report", cascade="all, delete-orphan")

class CitationModel(Base):
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(50), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    claim_context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("ReportModel", back_populates="citations")
    source = relationship("SourceModel", back_populates="citations")

class ContradictionModel(Base):
    __tablename__ = "contradictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    aspect = Column(Text, nullable=False)
    source_a = Column(Text, nullable=False)
    source_b = Column(Text, nullable=False)
    conflict_details = Column(Text, nullable=True)
    reconciliation_hint = Column(Text, nullable=True)

class FollowupModel(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    response_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GraphNodeModel(Base):
    __tablename__ = "graph_nodes"

    id = Column(String(100), primary_key=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(100), nullable=False)
    properties = Column(JSON, nullable=True)

class GraphEdgeModel(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    source_node = Column(String(100), nullable=False)
    target_node = Column(String(100), nullable=False)
    relationship = Column(String(100), nullable=False)

def register_models():
    """Helper method to force registration of base subclasses on application initialization."""
    pass
