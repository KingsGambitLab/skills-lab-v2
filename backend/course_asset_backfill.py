"""Post-gen asset backfill for BYO-key / terminal-exercise courses.

Problem: Creator emits switching-UX fields (bootstrap_command, dependencies,
paste_slots, step_slug, step_task) inconsistently across terminal_exercise
steps — sometimes all 5 fields, sometimes none, sometimes just paste_slots.
Our frontend template handles missing fields gracefully, but the richer UX
is lost on steps that didn't emit them.

Solution: walk the generated course, find terminal_exercise steps with
missing fields, fill them from the course_assets registry using module
position → branch-key mapping. Engine-level, no course regen needed.

Usage:
    from backend.course_asset_backfill import backfill_course
    backfill_course(course_id="created-...", course_asset_slug="aie")

This is GENERIC. Any future AI-augmented / terminal-exercise-heavy course
that registers its assets in course_assets.py gets this for free. The
only per-course wiring is the slug → module-branch-keys mapping.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.course_assets import (
    CourseAsset,
    build_bootstrap_command,
    get_course_assets,
    resolve_asset,
)
from backend.database import async_session_factory, Module, Step

log = logging.getLogger(__name__)


# Default per-kind dependencies for common course stages. Overridable per-
# course via course_assets registration if needed.
_STAGE_DEFAULT_DEPS: dict[str, list[dict]] = {
    "preflight": [
        {"kind": "anthropic_api_key", "why": "Claude Code needs this to authenticate"},
        {"kind": "claude_cli",        "why": "the course runs Claude Code on your machine"},
        {"kind": "git",               "why": "to clone the course repo"},
        {"kind": "python",            "version": "3.11+", "why": "the course repo uses Python/FastAPI"},
        {"kind": "docker",            "why": "for running tests locally"},
    ],
    "core_dev": [
        {"kind": "anthropic_api_key"},
        {"kind": "claude_cli"},
        {"kind": "git_clone"},
        {"kind": "python", "version": "3.11+"},
    ],
    "capstone_gha": [
        {"kind": "anthropic_api_key"},
        {"kind": "claude_cli"},
        {"kind": "git_clone"},
        {"kind": "python", "version": "3.11+"},
        {"kind": "github_account", "why": "to fork the course repo + push branches"},
        {"kind": "github_pat", "why": "dashboard pastes the Actions run URL; read-only is enough"},
    ],
}


def _module_key_for_position(slug: str, mod_idx: int) -> Optional[str]:
    """Resolve a module's position-based key from the course's asset
    registry. Convention: registry keys are ordered by module. First
    registered key → M0/preflight, second → M1, etc.
    """
    a = get_course_assets(slug)
    if not a:
        return None
    keys = list(a.module_branches.keys())
    if 0 <= mod_idx < len(keys):
        return keys[mod_idx]
    return None


def _infer_stage_kind(mod_idx: int, step_title: str) -> str:
    """Heuristic mapping: M0 → preflight, M4/M6 capstones (which ship via
    GHA) → capstone_gha, otherwise core_dev. Creators can override by
    setting their own `dependencies` explicitly in the step.
    """
    t = (step_title or "").lower()
    if mod_idx == 0:
        return "preflight"
    if "gha" in t or "github actions" in t or "lab-grade" in t or "ship" in t and "gha" in t:
        return "capstone_gha"
    return "core_dev"


def _backfill_step(step: Step, slug: str, mod_idx: int, step_idx: int) -> tuple[dict, list[str]]:
    """Return updated demo_data (dict) + list of human-readable change notes.
    Only modifies missing fields. Never overrides Creator-emitted values.
    """
    try:
        dd = json.loads(step.demo_data) if step.demo_data else {}
    except Exception:
        dd = {}
    if not isinstance(dd, dict):
        dd = {}
    changes: list[str] = []

    # step_slug — standard "M<N>.S<M>" shape
    if not dd.get("step_slug"):
        dd["step_slug"] = f"M{mod_idx}.S{step_idx}"
        changes.append("step_slug")
    # step_task — default to step title
    if not dd.get("step_task"):
        dd["step_task"] = step.title or ""
        changes.append("step_task")

    # Module-key for bootstrap command resolution
    mod_key = _module_key_for_position(slug, mod_idx)

    if not dd.get("bootstrap_command") and mod_key:
        bs = build_bootstrap_command(slug, mod_key)
        if bs:
            dd["bootstrap_command"] = bs
            changes.append("bootstrap_command")

    if not dd.get("dependencies"):
        stage = _infer_stage_kind(mod_idx, step.title or "")
        dd["dependencies"] = list(_STAGE_DEFAULT_DEPS.get(stage, []))
        changes.append(f"dependencies[{stage}]")

    # paste_slots — generic default when missing. Per-step customization
    # should come from the Creator; only fall back here.
    if not dd.get("paste_slots"):
        dd["paste_slots"] = [
            {"id": "prompts",    "label": "Your prompts",       "hint": "Copy the first few prompts you sent to Claude Code"},
            {"id": "final_diff", "label": "Final diff",          "hint": "git diff HEAD"},
            {"id": "transcript", "label": "Session transcript",  "hint": "Key turns from your Claude Code session"},
        ]
        changes.append("paste_slots")

    return dd, changes


async def backfill_course_async(course_id: str, asset_slug: str, *, dry_run: bool = False) -> dict:
    """Walk a course + fill missing terminal_exercise switching-UX fields."""
    assets = get_course_assets(asset_slug)
    if not assets:
        return {"ok": False, "error": f"no assets registered for slug '{asset_slug}'"}

    report = {"course_id": course_id, "asset_slug": asset_slug, "steps": [], "dry_run": dry_run}
    async with async_session_factory() as session:  # type: AsyncSession
        # Load modules in order
        mods_res = await session.execute(
            select(Module).where(Module.course_id == course_id).order_by(Module.position)
        )
        mods = list(mods_res.scalars())
        for mod_idx, mod in enumerate(mods):
            steps_res = await session.execute(
                select(Step).where(Step.module_id == mod.id).order_by(Step.position)
            )
            for step_idx, step in enumerate(steps_res.scalars()):
                if (step.exercise_type or "") != "terminal_exercise":
                    continue
                new_dd, changes = _backfill_step(step, asset_slug, mod_idx, step_idx)
                if changes:
                    report["steps"].append({
                        "step_id": step.id,
                        "module_idx": mod_idx,
                        "step_idx": step_idx,
                        "title": step.title,
                        "filled": changes,
                    })
                    if not dry_run:
                        # SQLAlchemy's JSON column auto-encodes. Assign the
                        # dict directly; do NOT json.dumps() (would double-encode).
                        step.demo_data = new_dd
                        session.add(step)
        if not dry_run:
            await session.commit()
    return report


def backfill_course(course_id: str, asset_slug: str, *, dry_run: bool = False) -> dict:
    """Sync wrapper for CLI use."""
    import asyncio
    return asyncio.run(backfill_course_async(course_id, asset_slug, dry_run=dry_run))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python -m backend.course_asset_backfill <course_id> <asset_slug> [--dry-run]")
        sys.exit(1)
    dry = "--dry-run" in sys.argv
    out = backfill_course(sys.argv[1], sys.argv[2], dry_run=dry)
    print(json.dumps(out, indent=2))
