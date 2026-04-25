"""Scoped course migration: copy courses + their cascade from local SQLite to
any SQLAlchemy target (typically remote Postgres).

Usage:
    # 1. Dry-run (no writes; shows what WOULD migrate):
    .venv/bin/python -m tools.migrate_courses_to_target_db \\
        --source sqlite+aiosqlite:///./skills_lab.db \\
        --target postgresql+asyncpg://user:pass@host:5432/skillslab \\
        --course-ids created-698e6399e3ca created-7fee8b78c742 \\
        --dry-run

    # 2. Actually migrate (idempotent — safe to re-run):
    .venv/bin/python -m tools.migrate_courses_to_target_db \\
        --source sqlite+aiosqlite:///./skills_lab.db \\
        --target postgresql+asyncpg://user:pass@host:5432/skillslab \\
        --course-ids created-698e6399e3ca created-7fee8b78c742

What it migrates:
  - courses (rows whose id ∈ --course-ids)
  - modules (rows whose course_id ∈ --course-ids)
  - steps   (rows whose module_id ∈ scoped modules)

What it does NOT migrate:
  - users / sessions — fresh learners register on the deployed instance
  - user_progress    — keyed by step_id; would carry stale local-user progress
  - enrollments      — same; new instance starts with empty enrollments
  - course_reviews   — review-pipeline state; not relevant on production
  - certificates     — issued at completion; new instance starts empty

Why scope to those 3 tables: production multi-user state belongs to production,
not the local dev DB. We're migrating COURSE CONTENT only.

Idempotency strategy:
  - For each scoped course/module/step, the script first SELECTs by primary key
    on the target. If present, it UPDATEs; if absent, it INSERTs.
  - JSON columns are passed through unchanged (SQLAlchemy `JSON` type handles
    sqlite JSON1 → Postgres JSONB transparently).
  - Foreign keys: modules.course_id FK assumes courses are migrated FIRST;
    steps.module_id FK assumes modules are migrated FIRST. The script enforces
    this order.

Schema bootstrap on target:
  - Caller is responsible for ensuring the target DB has the schema. Easiest
    path: run `python -c "import asyncio; from backend.database import
    create_tables; asyncio.run(create_tables())"` against the target with
    DATABASE_URL set, before running this migration.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Re-use the same SQLAlchemy models so the migration matches whatever schema
# the live backend defines (avoids drift if columns are added later).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Force backend/database.py to skip its module-level engine creation by
# overriding DATABASE_URL to a clearly-invalid value before import. We don't
# actually use that engine; we make our own per --source / --target.
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from backend.database import Course, Module, Step, Base  # noqa: E402


async def _all(session, cls):
    res = await session.execute(select(cls))
    return list(res.scalars())


async def _by_pk(session, cls, pk):
    return (await session.execute(select(cls).where(cls.id == pk))).scalars().first()


def _row_dict(row, exclude=()):
    """Snapshot a SQLAlchemy ORM row as a plain dict (column names → values).
    Excludes relationship attributes + any names listed in `exclude`."""
    return {
        col.name: getattr(row, col.name)
        for col in row.__table__.columns
        if col.name not in exclude
    }


async def migrate(source_url: str, target_url: str, course_ids: list[str],
                  dry_run: bool = False) -> dict:
    src_engine = create_async_engine(source_url, echo=False)
    tgt_engine = create_async_engine(target_url, echo=False, pool_pre_ping=True)
    SrcSession = async_sessionmaker(src_engine, expire_on_commit=False)
    TgtSession = async_sessionmaker(tgt_engine, expire_on_commit=False)

    counts = {"courses": 0, "modules": 0, "steps": 0,
              "courses_inserted": 0, "courses_updated": 0,
              "modules_inserted": 0, "modules_updated": 0,
              "steps_inserted": 0, "steps_updated": 0}

    async with SrcSession() as src:
        # 1) Pull scoped courses
        scoped_courses = []
        for cid in course_ids:
            c = await _by_pk(src, Course, cid)
            if c is None:
                print(f"  ⚠ source has no course {cid!r} — skipping")
                continue
            scoped_courses.append(c)
        counts["courses"] = len(scoped_courses)

        # 2) Pull scoped modules + steps
        scoped_modules = []
        scoped_steps = []
        for c in scoped_courses:
            mods = (await src.execute(
                select(Module).where(Module.course_id == c.id)
            )).scalars().all()
            scoped_modules.extend(mods)
            for m in mods:
                steps = (await src.execute(
                    select(Step).where(Step.module_id == m.id)
                )).scalars().all()
                scoped_steps.extend(steps)
        counts["modules"] = len(scoped_modules)
        counts["steps"] = len(scoped_steps)

    if dry_run:
        print(f"\n[DRY RUN] would migrate:")
        print(f"  {counts['courses']} courses")
        print(f"  {counts['modules']} modules")
        print(f"  {counts['steps']} steps")
        for c in scoped_courses:
            print(f"   - {c.id}: {c.title}")
        return counts

    # 3) Apply to target. Order: courses → modules → steps.
    async with TgtSession() as tgt:
        for c in scoped_courses:
            existing = await _by_pk(tgt, Course, c.id)
            data = _row_dict(c)
            if existing is None:
                tgt.add(Course(**data))
                counts["courses_inserted"] += 1
            else:
                for k, v in data.items():
                    setattr(existing, k, v)
                counts["courses_updated"] += 1

        for m in scoped_modules:
            existing = await _by_pk(tgt, Module, m.id)
            data = _row_dict(m)
            if existing is None:
                tgt.add(Module(**data))
                counts["modules_inserted"] += 1
            else:
                for k, v in data.items():
                    setattr(existing, k, v)
                counts["modules_updated"] += 1

        for s in scoped_steps:
            existing = await _by_pk(tgt, Step, s.id)
            data = _row_dict(s)
            if existing is None:
                tgt.add(Step(**data))
                counts["steps_inserted"] += 1
            else:
                for k, v in data.items():
                    setattr(existing, k, v)
                counts["steps_updated"] += 1

        await tgt.commit()

    print(f"\n✅ migration complete:")
    print(f"  courses: {counts['courses_inserted']} inserted, {counts['courses_updated']} updated")
    print(f"  modules: {counts['modules_inserted']} inserted, {counts['modules_updated']} updated")
    print(f"  steps:   {counts['steps_inserted']} inserted, {counts['steps_updated']} updated")
    return counts


def _main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True,
                   help="SQLAlchemy URL of source DB (e.g. sqlite+aiosqlite:///./skills_lab.db)")
    p.add_argument("--target", required=True,
                   help="SQLAlchemy URL of target DB (e.g. postgresql+asyncpg://user:pass@host:5432/dbname)")
    p.add_argument("--course-ids", nargs="+", required=True,
                   help="Course IDs to migrate (cascading to their modules + steps)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would migrate; don't write to target")
    args = p.parse_args()
    asyncio.run(migrate(args.source, args.target, args.course_ids, dry_run=args.dry_run))


if __name__ == "__main__":
    _main()
