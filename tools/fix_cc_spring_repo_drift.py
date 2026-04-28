"""Comprehensive fix: replace jspring-course-repo URLs with cc-spring's repo
on EVERY step type in the cc-spring course (created-ebd82a5fdec6).

Why this exists: the Creator's /generate emitted hands_on AND non-hands_on
steps (terminal_exercise, concept, mcq, scenario_branch, code_review) all
hardcoding jspring-course-repo URLs, despite creator_notes referencing
cc-spring. The earlier fix_cc_spring_course_slug tool only normalized
hands_on demo_data; other types still had jspring URLs in starter_repo /
content / instructions.

Per CLAUDE.md "Don't Patch Broken Generated Courses" — the structural fix
is in the Creator (post-process emits course_slug + repo URL from
Course.asset_slug, see backlog item). This tool is the one-shot data
correction so cc-spring is usable for testing today.

Operations per step:
  1. demo_data.starter_repo: if URL contains jspring-course-repo →
     rewrite to claude-code-springboot-exercises. Branch ref is reset
     to "main" (the inspiration repo's default) since the original ref
     (module-0-preflight etc.) doesn't exist on the new repo.
  2. demo_data.bootstrap_command: same URL replacement.
  3. demo_data.cli_commands[i].cmd: same URL replacement.
  4. content (HTML): same URL replacement (in <pre><code> blocks etc.)
  5. demo_data.instructions: same URL replacement.

Idempotent: safe to re-run.

Usage:
    set -a && source .env && set +a
    python -m tools.fix_cc_spring_repo_drift [--course-id ...] [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# Pattern: any github.com URL containing tusharbisht/jspring-course-repo
# (with optional .git suffix), regardless of context (in JSON/HTML/MD).
JSPRING_REPO_PATTERNS = [
    (r"https?://github\.com/tusharbisht/jspring-course-repo(?:\.git)?",
     "https://github.com/tusharbisht/claude-code-springboot-exercises"),
    (r"git@github\.com:tusharbisht/jspring-course-repo(?:\.git)?",
     "git@github.com:tusharbisht/claude-code-springboot-exercises"),
    (r"\btusharbisht/jspring-course-repo\b",
     "tusharbisht/claude-code-springboot-exercises"),
    # Bare "jspring-course-repo" token (e.g. `cd jspring-course-repo`
    # in instructions). The cloned dir from claude-code-springboot-
    # exercises will be `claude-code-springboot-exercises`, not
    # `jspring-course-repo`, so any bare reference is broken.
    (r"\bjspring-course-repo\b",
     "claude-code-springboot-exercises"),
]

# Branch refs the Creator hardcoded that don't exist on cc-spring's repo.
# These all need to be reset to a real cc-spring branch. Use "main" as the
# safe default for setup/install steps; per-exercise steps already have
# correct branches via hands_on demo_data (handled by fix_cc_spring_course_slug).
JSPRING_REF_PATTERNS = [
    (r"\b(module-[0-6]-(?:preflight|starter|claudemd|agents|hooks|mcp|capstone))\b",
     "main"),
]


def _rewrite_text(text: str) -> tuple[str, int]:
    """Apply URL + ref rewrites. Returns (new_text, num_changes)."""
    if not isinstance(text, str):
        return text, 0
    changes = 0
    out = text
    for pat, rep in JSPRING_REPO_PATTERNS + JSPRING_REF_PATTERNS:
        new = re.sub(pat, rep, out)
        if new != out:
            changes += len(re.findall(pat, out))
            out = new
    return out, changes


def _rewrite_json_value(val: Any) -> tuple[Any, int]:
    """Walk a JSON-shape value, rewriting any string contents. Returns
    (new_value, num_string_changes)."""
    total = 0
    if isinstance(val, str):
        new, n = _rewrite_text(val)
        return new, n
    if isinstance(val, list):
        out = []
        for item in val:
            new, n = _rewrite_json_value(item)
            out.append(new)
            total += n
        return out, total
    if isinstance(val, dict):
        out = {}
        for k, v in val.items():
            new, n = _rewrite_json_value(v)
            out[k] = new
            total += n
        return out, total
    return val, 0


async def fix(course_id: str, *, dry_run: bool = False) -> dict:
    from sqlalchemy import select
    from backend.database import async_session_factory, Step, Module

    fixed_steps = 0
    total_changes = 0
    untouched = 0
    field_changes: dict[str, int] = {"content": 0, "demo_data": 0, "validation": 0, "code": 0, "expected_output": 0}

    async with async_session_factory() as db:
        q = (
            select(Step)
            .join(Module, Module.id == Step.module_id)
            .where(Module.course_id == course_id)
            .order_by(Module.position, Step.position)
        )
        steps = (await db.execute(q)).scalars().all()
        log.info("course %s — scanning %d steps", course_id, len(steps))

        for step in steps:
            step_changes = 0

            # content (string HTML)
            new_content, n = _rewrite_text(step.content or "")
            if n > 0:
                field_changes["content"] += n
                step_changes += n
                if not dry_run:
                    step.content = new_content

            # code (string)
            new_code, n = _rewrite_text(step.code or "")
            if n > 0:
                field_changes["code"] += n
                step_changes += n
                if not dry_run:
                    step.code = new_code

            # expected_output (string)
            new_eo, n = _rewrite_text(step.expected_output or "")
            if n > 0:
                field_changes["expected_output"] += n
                step_changes += n
                if not dry_run:
                    step.expected_output = new_eo

            # demo_data (JSON / dict)
            if isinstance(step.demo_data, dict):
                new_dd, n = _rewrite_json_value(step.demo_data)
                if n > 0:
                    field_changes["demo_data"] += n
                    step_changes += n
                    if not dry_run:
                        step.demo_data = new_dd

            # validation (JSON / dict)
            if isinstance(step.validation, dict):
                new_v, n = _rewrite_json_value(step.validation)
                if n > 0:
                    field_changes["validation"] += n
                    step_changes += n
                    if not dry_run:
                        step.validation = new_v

            if step_changes > 0:
                fixed_steps += 1
                total_changes += step_changes
                log.info("  step %s M%s.S%s [%s] — %d rewrites",
                         step.id,
                         (step.module_id and step.position),
                         step.position,
                         step.exercise_type or "concept",
                         step_changes)
            else:
                untouched += 1

        if not dry_run:
            await db.commit()
            log.info("Committed.")

    return {
        "course_id": course_id,
        "scanned": len(steps),
        "fixed_steps": fixed_steps,
        "untouched": untouched,
        "total_string_replacements": total_changes,
        "by_field": field_changes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course-id", default="created-ebd82a5fdec6")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = asyncio.run(fix(args.course_id, dry_run=args.dry_run))
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
