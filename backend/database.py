"""
SQLAlchemy async database setup with SQLite (aiosqlite).
Upgrade path: swap DATABASE_URL to postgresql+asyncpg://... for production.
Env override: DATABASE_URL environment variable (set by production deploy
to point at Postgres).
"""

import enum
import os
import secrets
from datetime import datetime, timedelta
from typing import AsyncGenerator

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

# 2026-04-23 v8: DATABASE_URL is env-overridable so a Postgres deploy can
# flip the target without code edits. Default = local SQLite for dev.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./skills_lab.db")

# SQLite: enable WAL mode + busy_timeout to avoid locks under concurrent access.
# Without these, a long-running transaction (like creator/generate's 60s LLM gather)
# blocks learners hitting /progress/complete with "database is locked" errors.
from sqlalchemy import event

# SQLite connect_args vs Postgres: the `timeout` kwarg is SQLite-only. Detect
# and apply accordingly so the same file can run against either backend.
_IS_SQLITE = DATABASE_URL.startswith("sqlite")
if _IS_SQLITE:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"timeout": 15},  # Wait up to 15s for locks
    )
else:
    # Postgres (asyncpg): pooling is handled by SQLAlchemy.
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


if _IS_SQLITE:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        """Set SQLite pragmas on every connection for better concurrency.
        Postgres doesn't need this (has real MVCC)."""
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


class UserRole(str, enum.Enum):
    """v8 auth roles. A user picks ONE role at signup. Admin is set by DB
    flip — there's no public /register path to admin."""
    learner = "learner"
    creator = "creator"
    admin = "admin"


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

    # Lifecycle status (2026-04-21): "generating" while /api/creator/generate is
    # mid-pipeline (rows now committed per-step for SQLite concurrency, so the
    # course briefly exists in the DB but isn't complete); "ready" when gen
    # finishes; "failed" if the handler raises. Only "ready" shows in public list.
    generation_status: Mapped[str] = mapped_column(String, nullable=False, default="ready")

    # v8 auth columns (2026-04-23). Pre-user-model courses have
    # creator_user_id=NULL + is_published=True (backward-compat).
    creator_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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
    # 2026-04-25 — surface-aware split (Phase 2). Per-step declaration of
    # which surface "owns" this assignment end-to-end. Values: 'web' (browser
    # widget — drag-drop, simulator, mock interview), 'terminal' (CLI-native
    # — terminal_exercise / system_build / code_exercise on a CLI-eligible
    # course). NULL = legacy step pre-backfill; consumer treats it as 'web'
    # for safety. Buddy-Opus review insisted this be an EXPLICIT declaration,
    # not inferred at runtime — see CLAUDE.md §"Surface-aware split".
    learner_surface: Mapped[str | None] = mapped_column(String, nullable=True)

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
    # Course-progression #4 (2026-04-27): server-side attempt counter,
    # incremented on every /api/exercises/validate call. Drives per-step
    # pass-rate + dropout signals on the creator dashboard. Nullable for
    # rows created before the column existed; treat None as 0.
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    step: Mapped["Step"] = relationship(back_populates="progress_records")

    # Indices (2026-04-27): UserProgress had zero indices, every query was a
    # seq scan. Postgres dev/staging feels this on real data — every
    # /progress/complete + /exercises/validate upsert (now per-attempt
    # since #4) hits WHERE user_id = ? AND step_id = ?. The composite
    # covers that hot path and any user_id-scoped reads (get_progress,
    # creator-learners). The step_id-only index covers the reverse —
    # aggregate-stats per-step rollup that filters WHERE step_id IN (...).
    __table_args__ = (
        Index("ix_user_progress_user_step", "user_id", "step_id"),
        Index("ix_user_progress_step_id", "step_id"),
    )


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
# v8 AUTH TABLES (2026-04-23) — User / Session / Enrollment
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(
        Enum(UserRole, native_enum=False), nullable=False, default=UserRole.learner,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")

    @staticmethod
    def new_for_user(user_id: int, ttl_hours: int = 24 * 14) -> "Session":
        return Session(
            id=secrets.token_urlsafe(48),
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    course_id: Mapped[str] = mapped_column(
        String, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="enrollments")


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

async def create_tables() -> None:
    """Create all tables. Call once at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Lightweight forward-migrations for SQLite columns added after the first
    # create_all ran. `create_all` is idempotent on TABLES but does NOT backfill
    # new COLUMNS on existing tables. For a small app + SQLite, we accept this
    # idempotent ALTER pattern rather than pulling in alembic.
    await _ensure_column(
        table="courses",
        column="generation_status",
        ddl="ALTER TABLE courses ADD COLUMN generation_status VARCHAR NOT NULL DEFAULT 'ready'",
    )
    # v8 (2026-04-23) auth columns on existing courses table. Idempotent.
    await _ensure_column(
        table="courses",
        column="creator_user_id",
        ddl="ALTER TABLE courses ADD COLUMN creator_user_id INTEGER",
    )
    await _ensure_column(
        table="courses",
        column="is_published",
        ddl="ALTER TABLE courses ADD COLUMN is_published BOOLEAN NOT NULL DEFAULT 1",
    )
    await _ensure_column(
        table="courses",
        column="published_at",
        ddl="ALTER TABLE courses ADD COLUMN published_at DATETIME",
    )
    # v8.7 (2026-04-25) — per-step surface declaration. NULL until backfill
    # script runs; consumers treat NULL as 'web' for safety.
    await _ensure_column(
        table="steps",
        column="learner_surface",
        ddl="ALTER TABLE steps ADD COLUMN learner_surface VARCHAR",
    )
    # Course-progression #4 (2026-04-27) — per-step attempt counter on
    # UserProgress. Incremented by /api/exercises/validate on every
    # submission. Existing rows backfill to 0 via the DEFAULT clause.
    await _ensure_column(
        table="user_progress",
        column="attempts",
        ddl="ALTER TABLE user_progress ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0",
    )
    # Course-progression (2026-04-27) — UserProgress indices for Postgres
    # dev/staging perf. CREATE INDEX IF NOT EXISTS works on both SQLite
    # 3.8.0+ and Postgres 9.5+. Idempotent: noop on second startup.
    # New tables created by Base.metadata.create_all already include
    # these via __table_args__; this DDL backfills existing tables.
    await _run_ddl(
        "CREATE INDEX IF NOT EXISTS ix_user_progress_user_step "
        "ON user_progress (user_id, step_id)"
    )
    await _run_ddl(
        "CREATE INDEX IF NOT EXISTS ix_user_progress_step_id "
        "ON user_progress (step_id)"
    )


async def _ensure_column(*, table: str, column: str, ddl: str) -> None:
    """Add a column to an existing table if it isn't already present.

    Idempotent: re-checks the column list and skips when present.

    2026-04-26 — engine-aware after Postgres migration. Was SQLite-only
    via PRAGMA table_info; now uses the engine's introspection so the
    same migration works against both SQLite and PG.
    """
    from sqlalchemy import text, inspect
    def _existing_cols(sync_conn):
        return {c["name"] for c in inspect(sync_conn).get_columns(table)}
    async with engine.begin() as conn:
        existing = await conn.run_sync(_existing_cols)
        if column in existing:
            return
        await conn.execute(text(ddl))


async def _run_ddl(ddl: str) -> None:
    """Execute a DDL statement. Used for idempotent CREATE INDEX IF NOT
    EXISTS migrations where the IF NOT EXISTS clause itself makes the
    statement re-runnable across SQLite and Postgres."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text(ddl))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
