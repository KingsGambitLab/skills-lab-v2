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
# 2026-04-27 v0.1.17 — opt-in rewrite mode for bootstrap_command.
# Set via the `--rewrite-bootstrap` CLI flag. When True, _backfill_step
# overwrites existing bootstrap_command values with freshly-computed
# ones from the registry (e.g. picks up the new no-trailing-claude
# default). When False (the default), existing values are preserved
# additively as before.
_REWRITE_BOOTSTRAP: bool = False


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


# ═══════════════════════════════════════════════════════════════════════
# GRADING-RUNNER OVERLAY (2026-04-28)
# ═══════════════════════════════════════════════════════════════════════
#
# Per CLAUDE.md §"BEHAVIORAL TEST HARNESS — the test class IS the rubric":
# courses with a `grading_runner` registered in their CourseAsset get a
# harness-side post-LLM overlay that replaces the LLM-emitted cli_commands
# / rubric / must_contain fields with the generic grading-runner shape.
#
# Why post-LLM (not in the prompt): per buddy-Opus 2026-04-27 — "URL
# injection is harness-side, not LLM-prompt-side. Don't trust LLM to
# remember; gate-time enforcement, harness-side injection, never via
# prompt nag." The LLM keeps authoring narrative (briefing, instructions,
# hint); we overwrite the grading machinery deterministically.

_GRADING_OVERLAY_RUBRIC = (
    "Full credit (1.0) when the hidden grading harness emits "
    "'RESULT: PASS' (exit code 0). Zero credit (0.0) on 'RESULT: FAIL'. "
    "The harness runs real test assertions against your code (Hibernate "
    "query counts for performance bugs, MockMvc for HTTP contracts, "
    "verify scripts for config-shape exercises). The grading-result.json "
    "output details which test failed and why; check it after a fail to "
    "iterate."
)


def apply_grading_runner_overlay(
    candidate: dict,
    asset_slug: Optional[str],
    module_position: Optional[int],
    step_position: Optional[int],
) -> tuple[dict, bool]:
    """Harness-side overlay: replace the LLM's cli_commands / rubric /
    must_contain with the generic grading-runner shape when the course
    is registered with a grading_runner AND this step has an exercise-dir
    mapping.

    Args:
        candidate: the LLM-emitted step dict (mutated in place + returned).
        asset_slug: course's asset slug (e.g. "jspring"); None falls through.
        module_position: 1-indexed module position.
        step_position: 1-indexed step position.

    Returns:
        (candidate, True) if overlay applied; (candidate, False) otherwise.

    The overlay is OPT-IN: courses without `grading_runner` set keep the
    legacy LLM-rubric path. Steps not in `exercise_dirs` map (preflight,
    deprecated reflections, system_build with GHA, etc.) also pass through.
    """
    if not asset_slug or module_position is None or step_position is None:
        return candidate, False

    asset = get_course_assets(asset_slug)
    if not asset or not asset.grading_runner:
        return candidate, False

    step_key = f"M{module_position}.S{step_position}"
    exercise_dir = asset.exercise_dirs.get(step_key)
    if not exercise_dir:
        return candidate, False

    # Only overlay terminal_exercise — system_build keeps gha_workflow_check.
    if candidate.get("exercise_type") != "terminal_exercise":
        return candidate, False

    cmd = f"{asset.grading_runner} {exercise_dir}"

    validation = candidate.get("validation") or {}
    if not isinstance(validation, dict):
        validation = {}

    # Replace cli_commands with the single grading-runner invocation.
    validation["cli_commands"] = [{
        "cmd": cmd,
        # `expect` regex matches the RESULT protocol's PASS line. Until the
        # cli_commands schema gains an explicit `expect_exit_code` field,
        # this regex is the structured signal (no prose-grading drift —
        # the runner itself emits exactly "RESULT: PASS" on success).
        "expect": "RESULT: PASS",
        "label": f"Run hidden grading harness ({exercise_dir})",
    }]

    # Replace rubric with the generic grading-runner prose.
    validation["rubric"] = _GRADING_OVERLAY_RUBRIC

    # Replace must_contain with the cheap fallback marker.
    validation["must_contain"] = ["RESULT: PASS"]

    # Preserve existing hint if the LLM authored a useful one; otherwise
    # supply a generic fallback.
    if not (validation.get("hint") or "").strip():
        validation["hint"] = (
            "If the harness fails, read the FAILED: lines in stdout — they name "
            "the specific test that failed plus a one-line reason. Then check "
            "grading-result.json for full detail."
        )

    candidate["validation"] = validation

    log.info(
        "grading-runner overlay applied — slug=%s step=%s exercise=%s cmd=%s",
        asset_slug, step_key, exercise_dir, cmd,
    )
    return candidate, True


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
    # 2026-04-27 (post-Opus consult Bug X) — handle both string + dict shapes.
    # The SQLite era stored demo_data as a JSON string in TEXT columns;
    # post-PG migration the JSON column auto-deserializes to a dict.
    # Calling json.loads() on a dict raises TypeError; the prior bare
    # `except Exception: dd = {}` swallowed it silently and reset to empty —
    # wiping every pre-existing field on PG. Net damage today: template_files
    # gone on 85124/85125/85128 (authoring steps); bootstrap_command +
    # dependencies + paste_slots gone on every kimi step the backfill touched.
    # Fix: branch on type. Tighten except to typed (json.JSONDecodeError,
    # TypeError) so a similar regression dev-time would actually surface.
    if step.demo_data is None:
        dd = {}
    elif isinstance(step.demo_data, dict):
        dd = dict(step.demo_data)  # shallow copy so we don't mutate the SA attribute
    elif isinstance(step.demo_data, str):
        try:
            dd = json.loads(step.demo_data)
        except (json.JSONDecodeError, TypeError):
            dd = {}
    else:
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
    elif _REWRITE_BOOTSTRAP and mod_key:
        # 2026-04-27 v0.1.17 — opt-in mode for re-running bootstrap_command
        # against the new shape (default post_clone_cmd no longer auto-
        # appends `&& claude`). Allowed under CLAUDE.md "pure data-shape
        # migrations" exception because bootstrap_command is harness-
        # derived from the course_assets registry — not LLM course content.
        bs = build_bootstrap_command(slug, mod_key)
        if bs and bs != dd.get("bootstrap_command"):
            dd["bootstrap_command"] = bs
            changes.append("bootstrap_command (rewritten)")

    # 2026-04-27 — F26 starter_repo injection. Skip authoring steps (they
    # create files in fresh dirs, no repo needed). Skip if the step
    # already declares starter_repo or starter_files (Creator emitted).
    # For everything else: harness-resolve from the registry → inject.
    is_authoring = (
        getattr(step, "task_kind", None) == "authoring"
        or dd.get("task_kind") == "authoring"
    )
    has_scaffold = bool(dd.get("starter_repo") or dd.get("starter_files"))
    if not is_authoring and not has_scaffold and mod_key:
        a = get_course_assets(slug)
        branch = a.module_branches.get(mod_key) if a else None
        if a and branch:
            dd["starter_repo"] = {
                "url": a.course_repo,
                "ref": branch,
                "description": (
                    f"Module {mod_idx} starter — {a.title_hint}. "
                    f"Branch `{branch}` carries the planted code + team conventions."
                ),
            }
            changes.append("starter_repo")

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
                # 2026-04-27 — extend backfill scope to system_build too.
                # The capstone "push to GHA" step is system_build with a
                # validation.gha_workflow_check; it ALSO benefits from
                # starter_repo + bootstrap_command so the WebView's
                # starter-repo banner renders + the F26 gate passes.
                if (step.exercise_type or "") not in ("terminal_exercise", "system_build"):
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
        print("usage: python -m backend.course_asset_backfill <course_id> <asset_slug> [--dry-run] [--rewrite-bootstrap]")
        sys.exit(1)
    dry = "--dry-run" in sys.argv
    if "--rewrite-bootstrap" in sys.argv:
        _REWRITE_BOOTSTRAP = True
    out = backfill_course(sys.argv[1], sys.argv[2], dry_run=dry)
    print(json.dumps(out, indent=2))
