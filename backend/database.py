"""
SQLAlchemy async database setup with SQLite (aiosqlite).
Upgrade path: swap DATABASE_URL to postgresql+asyncpg://... for production.
"""

import enum
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

DATABASE_URL = "sqlite+aiosqlite:///./skills_lab.db"

# SQLite: enable WAL mode + busy_timeout to avoid locks under concurrent access.
# Without these, a long-running transaction (like creator/generate's 60s LLM gather)
# blocks learners hitting /progress/complete with "database is locked" errors.
from sqlalchemy import event

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"timeout": 15},  # Wait up to 15s for locks
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Set SQLite pragmas on every connection for better concurrency."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=15000")  # 15s wait for locks
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CourseType(str, enum.Enum):
    technical = "technical"
    case_study = "case_study"
    compliance = "compliance"


class StepType(str, enum.Enum):
    concept = "concept"
    code = "code"
    exercise = "exercise"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    course_type: Mapped[str] = mapped_column(
        Enum(CourseType, native_enum=False), nullable=False, default=CourseType.technical
    )
    level: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    estimated_time: Mapped[str | None] = mapped_column(String, nullable=True)
    module_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # Soft-delete. When set, this course is hidden from /api/courses and /api/courses/{id}
    # (both return 404). Restore by setting back to NULL via /api/admin/restore_course.
    # Never hard-delete — preserves user progress, certificates, and enables recovery.
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    modules: Mapped[list["Module"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Module.position"
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(
        String, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    estimated_time: Mapped[str | None] = mapped_column(String, nullable=True)
    objectives: Mapped[list | None] = mapped_column(JSON, nullable=True)
    step_count: Mapped[int] = mapped_column(Integer, default=0)

    course: Mapped["Course"] = relationship(back_populates="modules")
    steps: Mapped[list["Step"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="Step.position"
    )


class Step(Base):
    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String, nullable=False)
    step_type: Mapped[str] = mapped_column(
        Enum(StepType, native_enum=False), nullable=False, default=StepType.concept
    )
    exercise_type: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    demo_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    module: Mapped["Module"] = relationship(back_populates="steps")
    progress_records: Mapped[list["UserProgress"]] = relationship(
        back_populates="step", cascade="all, delete-orphan"
    )
    review_schedules: Mapped[list["ReviewSchedule"]] = relationship(
        back_populates="step", cascade="all, delete-orphan"
    )


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, default="default")
    step_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("steps.id", ondelete="CASCADE"), nullable=False
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    step: Mapped["Step"] = relationship(back_populates="progress_records")


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    course_id: Mapped[str] = mapped_column(
        String, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    course: Mapped["Course"] = relationship(back_populates="certificates")


class ReviewSchedule(Base):
    __tablename__ = "review_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    step_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("steps.id", ondelete="CASCADE"), nullable=False
    )
    next_review_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    times_reviewed: Mapped[int] = mapped_column(Integer, default=0)

    step: Mapped["Step"] = relationship(back_populates="review_schedules")


class CourseReview(Base):
    """Persistence for the automated post-generation QC workflow (auto_review.py).

    Before 2026-04-20-late: review state was held in a module-level dict, wiped
    on every server restart — which meant a deploy that happened during a
    review orphaned the in-flight work and the creator's banner stuck forever.
    This table survives restarts so the banner can pick up a half-finished
    review or display a completed verdict even after the server has cycled.

    Keyed by original_course_id (the course the review was KICKED OFF on);
    current_course_id tracks the latest iteration (updated on whole-course
    regen). state_json holds the full review dict for backward compat.
    """
    __tablename__ = "course_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_course_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    current_course_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    # Full review state as JSON (iterations[], findings[], final_verdict, timing)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

async def create_tables() -> None:
    """Create all tables. Call once at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
