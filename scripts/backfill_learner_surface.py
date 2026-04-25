"""Backfill `Step.learner_surface` for every existing course in the DB.

Phase 2 of the surface-aware split (2026-04-25). The new `learner_surface`
column was added in this same release; this script populates it for steps
that existed BEFORE the column was declared.

Per buddy-Opus review: this script is the ONLY place the heuristic runs at
DB-mutation time. Going forward, the Creator emits `learner_surface`
explicitly per step, and the runtime read path consults the stored value
directly. No inference at runtime ever.

Usage (from repo root, with the backend on PYTHONPATH):

    python -m scripts.backfill_learner_surface              # apply
    python -m scripts.backfill_learner_surface --dry-run    # preview
    python -m scripts.backfill_learner_surface --course created-abc  # one course

Idempotent: re-running won't change rows that are already set unless
`--overwrite` is passed (rare — only useful if you change the heuristic
itself).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter
from pathlib import Path

# Allow running as `python -m scripts.backfill_learner_surface` OR
# `python scripts/backfill_learner_surface.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from backend.database import async_session_factory, Course, Module, Step
from backend.learner_surface import classify_step, is_cli_eligible_course


async def backfill(course_id: str | None, dry_run: bool, overwrite: bool) -> dict:
    """Walk every Step in scope. Apply the heuristic. Write the field.
    Returns a counter of {value: count} written.
    """
    written = Counter()
    skipped_existing = 0
    courses_touched = 0

    async with async_session_factory() as db:
        if course_id:
            q = select(Course).where(Course.id == course_id)
        else:
            q = select(Course)
        courses = (await db.execute(q)).scalars().all()

        for course in courses:
            cli_eligible = is_cli_eligible_course(
                course_title=course.title or "",
                course_id=course.id or "",
            )

            mods = (
                await db.execute(
                    select(Module).where(Module.course_id == course.id).order_by(Module.position)
                )
            ).scalars().all()

            local_changes = 0
            for mod in mods:
                steps = (
                    await db.execute(
                        select(Step).where(Step.module_id == mod.id).order_by(Step.position)
                    )
                ).scalars().all()

                for step in steps:
                    if step.learner_surface and not overwrite:
                        skipped_existing += 1
                        continue

                    surface = classify_step(
                        exercise_type=step.exercise_type,
                        content=step.content,
                        course_cli_eligible=cli_eligible,
                    )

                    if step.learner_surface == surface and not overwrite:
                        skipped_existing += 1
                        continue

                    if not dry_run:
                        step.learner_surface = surface
                    written[surface] += 1
                    local_changes += 1

            if local_changes:
                courses_touched += 1
                eligible_marker = "[CLI]" if cli_eligible else "[web]"
                print(f"  {eligible_marker} {course.id} '{course.title[:60]}': {local_changes} steps")

        if not dry_run:
            await db.commit()

    return {
        "written": dict(written),
        "skipped_existing": skipped_existing,
        "courses_touched": courses_touched,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--course", help="restrict to one course_id (default: all courses)")
    ap.add_argument("--dry-run", action="store_true", help="preview without committing")
    ap.add_argument("--overwrite", action="store_true",
                    help="re-classify steps that already have a value (default: skip)")
    ns = ap.parse_args()

    print("=" * 60)
    print(f"backfill_learner_surface  {'(DRY RUN)' if ns.dry_run else '(LIVE)'}"
          f"{'  [overwrite]' if ns.overwrite else ''}")
    print("=" * 60)
    out = asyncio.run(backfill(ns.course, ns.dry_run, ns.overwrite))
    print()
    print(f"Courses touched: {out['courses_touched']}")
    print(f"Skipped (already set): {out['skipped_existing']}")
    print(f"Written: {out['written']}")
    if ns.dry_run:
        print("\n(dry run — no DB changes)")


if __name__ == "__main__":
    main()
