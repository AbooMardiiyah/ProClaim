"""
ProClaim — Async Database Session & Base Model
"""
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.config import settings

# ── Engine ───────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


# ── Declarative Base with common timestamp columns ────────────────────────────
class Base(DeclarativeBase):
    """All ProClaim models inherit from this base."""
    pass


class TimestampMixin:
    """Adds created_at / updated_at to any model."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ── Dependency ───────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (used in dev / first run). Alembic handles production migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
