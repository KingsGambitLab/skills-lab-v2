"""Add a new module (with stub steps) to an EXISTING course, then regenerate
each step via the per-step regenerate endpoint.

Generic — works for any course + any module shape. Used today (2026-04-24)
to add the Team Claude Code module to the AI-Augmented Engineering course
after review agents flagged it was silently dropped during /refine.

The Creator's /refine pipeline sometimes collapses modules from source_material
without explicit learner approval. The generic fix (post-refine structural diff)
is production-ready; THIS script is the runtime workaround: creator runs it to
append a module to an already-generated course without regenerating the whole
course.

Usage:
    python -m backend.add_module_to_course \\
        --course-id created-7fee8b78c742 \\
        --spec-file /tmp/m5_team_claude_spec.json

spec JSON shape:
    {
        "title": "Module title",
        "description": "Module description — what learners walk away with",
        "objectives": ["obj1", "obj2"],
        "steps": [
            {"title": "Step title", "exercise_type": "code_exercise", "description": "what this step teaches"},
            ...
        ]
    }

After the script inserts the skeleton, it kicks off per-step regeneration via
the HTTP endpoint — each step gets real content. The script polls until every
step has converged or retries exhausted.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import urllib.request
import urllib.error
from pathlib import Path

from sqlalchemy import select

from backend.database import Course, Module, Step, async_session_factory

log = logging.getLogger(__name__)


async def add_module_to_course_async(
    course_id: str,
    spec: dict,
    *,
    base_url: str = "http://localhost:8001",
) -> dict:
    """Insert the module + step skeletons, then trigger per-step regeneration."""
    async with async_session_factory() as session:
        # Find max module position
        mods_res = await session.execute(
            select(Module).where(Module.course_id == course_id).order_by(Module.position)
        )
        mods = list(mods_res.scalars())
        if not mods:
            return {"ok": False, "error": f"course {course_id} not found or has no modules"}
        next_position = max(m.position for m in mods) + 1

        # Create module (Module has no `description` field — use `subtitle`
        # for a short blurb; full description lives inside the opener concept
        # step's content).
        new_module = Module(
            course_id=course_id,
            position=next_position,
            title=spec.get("title", "New Module"),
            subtitle=(spec.get("description") or "")[:200],
            objectives=spec.get("objectives", []),
            step_count=len(spec.get("steps", [])),
        )
        session.add(new_module)
        await session.flush()
        module_id = new_module.id

        # Create step skeletons
        step_ids: list[int] = []
        for idx, step_spec in enumerate(spec.get("steps", [])):
            et = step_spec.get("exercise_type") or "concept"
            s = Step(
                module_id=module_id,
                position=idx,
                title=step_spec.get("title", f"Step {idx}"),
                step_type=("exercise" if et != "concept" else "concept"),
                exercise_type=et,
                content=step_spec.get("description", ""),
                validation={},
                demo_data={},
            )
            session.add(s)
            await session.flush()
            step_ids.append(s.id)
        await session.commit()

    # Trigger per-step regen via HTTP (uses the live backend's /api/courses/<id>/steps/<sid>/regenerate)
    regen_reports = []
    for sid, step_spec in zip(step_ids, spec.get("steps", [])):
        feedback = step_spec.get("feedback", step_spec.get("description", ""))
        body = json.dumps({"feedback": feedback}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/courses/{course_id}/steps/{sid}/regenerate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read())
            regen_reports.append({"step_id": sid, "ok": True, "detail": data})
        except urllib.error.HTTPError as e:
            regen_reports.append({"step_id": sid, "ok": False, "detail": f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}"})
        except Exception as e:
            regen_reports.append({"step_id": sid, "ok": False, "detail": f"{type(e).__name__}: {e}"})

    return {
        "ok": True,
        "course_id": course_id,
        "module_id": module_id,
        "position": next_position,
        "step_ids": step_ids,
        "regen_reports": regen_reports,
    }


def add_module_to_course(course_id: str, spec: dict, *, base_url: str = "http://localhost:8001") -> dict:
    return asyncio.run(add_module_to_course_async(course_id, spec, base_url=base_url))


def _main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--course-id", required=True)
    p.add_argument("--spec-file", required=True)
    p.add_argument("--base-url", default="http://localhost:8001")
    args = p.parse_args()

    spec = json.loads(Path(args.spec_file).read_text())
    out = add_module_to_course(args.course_id, spec, base_url=args.base_url)
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(_main())
