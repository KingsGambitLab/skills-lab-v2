"""Migrate an existing terminal_exercise step to the new hands_on exercise type.

Per CLAUDE.md §"BEHAVIORAL TEST HARNESS" + 2026-04-28 architectural pivot:
the LMS becomes plumbing for code-shape exercises; the course-repo's
.grading/<exercise>/{Hidden*Test.java, README.md, verify.sh} carry the
pedagogy. This tool migrates a step's exercise_type + demo_data + clears
LLM-authored grading machinery from validation.

NOT a content edit per CLAUDE.md's "Forbidden: SQL UPDATEs to adjust
course content." This is a STRUCTURAL data migration to a new exercise
type that doesn't exist in the Creator yet (chicken-and-egg). Once
Creator support for hands_on lands, future steps come from regen; this
tool exists only to prove the architecture end-to-end on existing rows.

Idempotent: re-running on a step already migrated to hands_on is a no-op.

Usage:
  python -m tools.migrate_step_to_hands_on \\
      --step-id 85115 \\
      --course-slug jspring \\
      --exercise-nn 01 \\
      --exercise-slug fix-n-plus-one \\
      [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("migrate_step_to_hands_on")


async def migrate(
    step_id: int,
    course_slug: str,
    exercise_nn: str,
    exercise_slug: str,
    *,
    dry_run: bool = False,
) -> dict:
    from sqlalchemy import select
    from backend.database import async_session_factory, Step, Module, Course
    from backend.course_assets import get_course_assets
    from backend.ontology import validate_step_against_ontology

    asset = get_course_assets(course_slug)
    if not asset:
        raise SystemExit(f"course_slug={course_slug!r} not registered in course_assets")
    if not asset.grading_runner:
        raise SystemExit(f"course {course_slug!r} has no grading_runner — register one first")
    nn_padded = str(exercise_nn).zfill(2)

    new_demo_data = {
        "course_slug": course_slug,
        "exercise_nn": nn_padded,
        "exercise_slug": exercise_slug,
    }

    # Pre-validate against the ontology gate before mutating.
    ok, reason = validate_step_against_ontology(
        "hands_on", new_demo_data, {}, code=None,
    )
    if not ok:
        raise SystemExit(f"new shape would fail ontology gate: {reason}")

    async with async_session_factory() as db:
        step = await db.get(Step, step_id)
        if not step:
            raise SystemExit(f"step_id={step_id} not found")
        mod = await db.get(Module, step.module_id)
        course = await db.get(Course, mod.course_id) if mod else None

        log.info("Found step %s in course %s (module %s)",
                 step_id, course.id if course else "?", mod.id if mod else "?")
        log.info("  current type: %s", step.exercise_type)
        log.info("  current title: %s", step.title)

        if step.exercise_type == "hands_on":
            current = step.demo_data or {}
            if (current.get("course_slug") == course_slug and
                str(current.get("exercise_nn", "")).zfill(2) == nn_padded and
                current.get("exercise_slug") == exercise_slug):
                log.info("Already migrated (idempotent no-op).")
                return {"status": "noop", "step_id": step_id}

        # Capture before-state for audit
        before = {
            "exercise_type": step.exercise_type,
            "demo_data": (step.demo_data or {}).copy() if isinstance(step.demo_data, dict) else step.demo_data,
            "validation": (step.validation or {}).copy() if isinstance(step.validation, dict) else step.validation,
            "code": step.code,
            "expected_output": step.expected_output,
        }

        log.info("Migration plan:")
        log.info("  exercise_type: %s -> hands_on", before["exercise_type"])
        log.info("  demo_data: REPLACE with %s", json.dumps(new_demo_data))
        log.info("  validation: CLEAR (was %s keys)",
                 len(before["validation"]) if isinstance(before["validation"], dict) else "non-dict")
        log.info("  code: CLEAR (was %s chars)", len(before["code"] or ""))
        log.info("  content: PRESERVE (slide/briefing stays — drag-drop / MCQ / scenario widgets)")

        if dry_run:
            log.info("--dry-run set; not committing.")
            return {"status": "dry_run", "step_id": step_id, "before": before, "after": {
                "exercise_type": "hands_on",
                "demo_data": new_demo_data,
                "validation": {},
            }}

        step.exercise_type = "hands_on"
        step.demo_data = new_demo_data
        step.validation = {}  # grading is external (run-grading.sh)
        step.code = None
        step.expected_output = None
        # task_kind no longer applies to hands_on; clear it.
        if hasattr(step, "task_kind") and step.task_kind is not None:
            step.task_kind = None
        # learner_surface stays as 'web' so the LMS browser is the slide/launchpad
        # for this step. The hands_on renderer dispatches before learner_surface
        # checks anyway (see frontend/index.html renderStep).

        await db.commit()
        log.info("Committed.")
        return {"status": "migrated", "step_id": step_id, "before": before}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step-id", type=int, required=True)
    ap.add_argument("--course-slug", required=True)
    ap.add_argument("--exercise-nn", required=True)
    ap.add_argument("--exercise-slug", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = asyncio.run(migrate(
        step_id=args.step_id,
        course_slug=args.course_slug,
        exercise_nn=args.exercise_nn,
        exercise_slug=args.exercise_slug,
        dry_run=args.dry_run,
    ))
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
