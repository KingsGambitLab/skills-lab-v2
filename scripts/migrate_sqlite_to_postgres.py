"""Migrate skills_lab.db (SQLite) → Postgres.

Usage:
    1. Ensure Postgres is running + a target DB exists.
    2. Set env vars:
         SOURCE_SQLITE_URL=sqlite+aiosqlite:///./skills_lab.db    # default
         TARGET_POSTGRES_URL=postgresql+asyncpg://user:pass@host:5432/db
    3. Run: `.venv/bin/python scripts/migrate_sqlite_to_postgres.py`

What it does:
    - Creates all tables on target via backend.database.Base.metadata.create_all
      (same schema — no column changes).
    - Dumps every row from source and inserts to target, preserving IDs and
      timestamps.
    - Idempotent-ish: target tables must be empty (refuses to overwrite).

What it does NOT do:
    - Change any column names or types. Schema is identical.
    - Touch the running uvicorn/celery. Run this on a stopped stack.

Backup strategy:
    Before running: `cp skills_lab.db skills_lab.db.bak-<date>`. Rollback
    is trivial — just point DATABASE_URL back at the SQLite file.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import the model classes (NOT the engine — we build our own source + target).
from backend.database import Base, Course, Module, Step, UserProgress, Certificate, ReviewSchedule, CourseReview


SOURCE_URL = os.environ.get("SOURCE_SQLITE_URL", "sqlite+aiosqlite:///./skills_lab.db")
TARGET_URL = os.environ.get("TARGET_POSTGRES_URL")


# Migration order respects foreign-key dependencies.
_MIGRATION_ORDER = [
    Course,
    Module,
    Step,
    UserProgress,
    Certificate,
    ReviewSchedule,
    CourseReview,
]


async def _ensure_target_empty(target_session: AsyncSession) -> tuple[bool, list[str]]:
    """Check that every table on target is empty before migration.
    Returns (ok, non_empty_tables).
    """
    non_empty = []
    for Model in _MIGRATION_ORDER:
        n = (await target_session.execute(select(Model).limit(1))).first()
        if n is not None:
            non_empty.append(Model.__tablename__)
    return len(non_empty) == 0, non_empty


async def _copy_table(
    source_session: AsyncSession,
    target_session: AsyncSession,
    Model,
) -> int:
    """Copy every row from source → target for one table. Returns count."""
    rows = (await source_session.execute(select(Model))).scalars().all()
    if not rows:
        return 0
    # Build fresh instances on target side to avoid sqlalchemy identity-map leaks.
    inspector = inspect(Model)
    col_names = [c.key for c in inspector.columns]
    for row in rows:
        payload = {c: getattr(row, c) for c in col_names}
        target_session.add(Model(**payload))
    await target_session.flush()
    return len(rows)


async def migrate() -> int:
    if not TARGET_URL:
        print("ERROR: TARGET_POSTGRES_URL is not set.", file=sys.stderr)
        return 1
    print(f"Source: {SOURCE_URL}")
    print(f"Target: {TARGET_URL}")
    print()

    source_engine = create_async_engine(SOURCE_URL, echo=False)
    target_engine = create_async_engine(TARGET_URL, echo=False)

    source_factory = async_sessionmaker(source_engine, expire_on_commit=False)
    target_factory = async_sessionmaker(target_engine, expire_on_commit=False)

    # 1. Create schema on target.
    print("[1/4] Creating tables on target...")
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("      done")

    # 2. Verify target is empty.
    print("[2/4] Verifying target is empty...")
    async with target_factory() as target_session:
        ok, non_empty = await _ensure_target_empty(target_session)
    if not ok:
        print(f"      REFUSED — target has non-empty tables: {non_empty}",
              file=sys.stderr)
        print("      Drop + recreate the DB to retry, or set "
              "TARGET_POSTGRES_URL to a fresh schema.", file=sys.stderr)
        return 2
    print("      done")

    # 3. Copy rows table-by-table, respecting FK order.
    print("[3/4] Copying rows...")
    counts: dict[str, int] = {}
    async with source_factory() as src, target_factory() as tgt:
        for Model in _MIGRATION_ORDER:
            n = await _copy_table(src, tgt, Model)
            counts[Model.__tablename__] = n
            print(f"      {Model.__tablename__}: {n} rows")
        await tgt.commit()

    # 4. Verification pass.
    print("[4/4] Verifying row counts match...")
    mismatches = []
    async with source_factory() as src, target_factory() as tgt:
        for Model in _MIGRATION_ORDER:
            src_n = len((await src.execute(select(Model))).scalars().all())
            tgt_n = len((await tgt.execute(select(Model))).scalars().all())
            if src_n != tgt_n:
                mismatches.append((Model.__tablename__, src_n, tgt_n))
    if mismatches:
        print("      MISMATCH:", file=sys.stderr)
        for name, s, t in mismatches:
            print(f"        {name}: source={s}, target={t}", file=sys.stderr)
        return 3
    print("      done")

    print()
    total = sum(counts.values())
    print(f"✅ Migration complete. {total} total rows copied.")
    print()
    print("NEXT STEPS:")
    print(f"  1. Update backend/database.py: DATABASE_URL = {TARGET_URL!r}")
    print("  2. Restart uvicorn + celery worker")
    print("  3. Smoke-test: GET /api/courses — confirm catalog renders")
    print("  4. Keep the .bak SQLite until a week of clean Postgres runs")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(migrate()))
