import sys
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from backend.app.core.config import DATABASE_URL

# Resolve database engine configurations
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific thread settings for async execution
    connect_args["check_same_thread"] = False

# Create master async database engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args if connect_args else {},
    pool_pre_ping=True
)

# Create async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Declarative base model
Base = declarative_base()

# Async Database dependency generator
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency helper yielding active transaction sessions.
    Automatically handles execution errors and clean transaction rollbacks.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def init_db():
    """Create all relational tables defined in the models module on boot."""
    async with engine.begin() as conn:
        # Import models inside function to register them on Base.metadata
        from backend.app.models.models import (
            SessionModel, QueryModel, SourceModel, ReportModel,
            CitationModel, ContradictionModel, FollowupModel,
            GraphNodeModel, GraphEdgeModel
        )
        await conn.run_sync(Base.metadata.create_all)
    print("[DATABASE] Relational schemas successfully initialized in SQLAlchemy.")
