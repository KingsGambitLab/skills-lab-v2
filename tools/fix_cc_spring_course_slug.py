"""One-shot fix for cc-spring's generated course (created-ebd82a5fdec6).

The Creator's /generate emitted hands_on steps with course_slug='jspring'
+ jspring-flavored starter_repo branches, despite creator_notes pointing
at cc-spring. The LLM defaulted to jspring's pattern. This tool fixes
the demo_data on each hands_on step to point at cc-spring correctly.

Per CLAUDE.md "Don't Patch Broken Generated Courses", the structural fix
is to tighten the Creator prompt + add a harness post-process to resolve
course_slug from Course.asset_slug. That's queued. This tool is the
one-shot data correction so cc-spring is usable today.

Usage:
    set -a && source .env && set +a
    python -m tools.fix_cc_spring_course_slug
        [--course-id created-ebd82a5fdec6]
        [--target-slug cc-spring]
        [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def fix(
    course_id: str,
    target_slug: str,
    *,
    dry_run: bool = False,
) -> dict:
    from sqlalchemy import select
    from backend.database import async_session_factory, Step, Module, Course
    from backend.course_assets import get_course_assets

    asset = get_course_assets(target_slug)
    if not asset:
        raise SystemExit(f"target_slug={target_slug!r} not registered in course_assets")

    fixed = 0
    skipped = 0
    untouched = 0
    failures: list[str] = []

    async with async_session_factory() as db:
        course = await db.get(Course, course_id)
        if not course:
            raise SystemExit(f"course_id={course_id} not found")
        log.info("course %s — current asset_slug=%r → target=%r",
                 course_id, course.asset_slug, target_slug)

        # Pre-check: align Course.asset_slug too (so future regens know).
        if course.asset_slug != target_slug:
            log.info("Course.asset_slug %r → %r", course.asset_slug, target_slug)
            if not dry_run:
                course.asset_slug = target_slug

        # Find all hands_on steps in this course.
        q = (
            select(Step)
            .join(Module, Module.id == Step.module_id)
            .where(Module.course_id == course_id)
            .where(Step.exercise_type == "hands_on")
            .order_by(Module.position, Step.position)
        )
        hands_on_steps = (await db.execute(q)).scalars().all()
        log.info("hands_on steps in course: %d", len(hands_on_steps))

        for step in hands_on_steps:
            dd = step.demo_data or {}
            if not isinstance(dd, dict):
                failures.append(f"step {step.id}: demo_data is not a dict")
                continue

            cur_slug = dd.get("course_slug")
            cur_nn = str(dd.get("exercise_nn", "")).zfill(2)
            cur_ex_slug = dd.get("exercise_slug")

            changes: list[str] = []
            new_dd = dict(dd)

            # Fix course_slug
            if cur_slug != target_slug:
                changes.append(f"course_slug {cur_slug!r}→{target_slug!r}")
                new_dd["course_slug"] = target_slug

            # Drop wrong starter_repo if it points at the wrong repo. The
            # launch endpoint composes the right URL from CourseAsset; the
            # demo_data starter_repo is REDUNDANT for hands_on steps and
            # was the LLM's drift mode.
            if "starter_repo" in new_dd:
                sr = new_dd["starter_repo"] or {}
                wrong = isinstance(sr, dict) and (
                    "jspring" in str(sr.get("url", ""))
                    or sr.get("ref", "").startswith("module-")
                )
                if wrong:
                    changes.append(f"drop starter_repo {sr.get('ref')!r}")
                    new_dd.pop("starter_repo", None)

            if not changes:
                untouched += 1
                continue

            label = f"step {step.id} M{step.module_id}.S{step.position} ({cur_nn}/{cur_ex_slug})"
            log.info("  fix %s: %s", label, ", ".join(changes))
            if dry_run:
                skipped += 1
                continue
            step.demo_data = new_dd
            fixed += 1

        if not dry_run:
            await db.commit()
            log.info("Committed.")

    return {
        "course_id": course_id,
        "target_slug": target_slug,
        "hands_on_steps": len(hands_on_steps),
        "fixed": fixed,
        "skipped_dry_run": skipped,
        "untouched": untouched,
        "failures": failures,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course-id", default="created-ebd82a5fdec6")
    ap.add_argument("--target-slug", default="cc-spring")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = asyncio.run(fix(
        course_id=args.course_id,
        target_slug=args.target_slug,
        dry_run=args.dry_run,
    ))
    print(json.dumps(result, indent=2, default=str))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
