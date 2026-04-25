"""Surface classification — Phase 2 of the surface-aware split (2026-04-25).

The `learner_surface` field on Step is an EXPLICIT declaration in the DB, not
inferred at runtime. This module exists for two narrow purposes:

  1. **One-shot backfill** — populate `learner_surface` on every existing step
     in the DB before the new field had been declared. Run once via
     `backend/scripts/backfill_learner_surface.py`.

  2. **Creator prompt default** — when generating a new step, the LLM is told
     to declare `learner_surface` per the rules below. The prompt tightens
     the LLM's choice; this module is the canonical statement of those rules.

Per buddy-Opus review (CLAUDE.md §"Surface-aware split"): once Phase 2 ships,
NO consumer reads this module at runtime. The runtime reads `step.learner_surface`
directly. The classifier is migration scaffolding, not a fallback.

## The rules

### Always TERMINAL (regardless of course)

  terminal_exercise   — by definition the learner runs commands locally
  system_build        — capstone deploy / code-write to a real repo

### Always WEB (regardless of course)

  mcq                  — multiple-choice
  categorization       — drag-drop matching
  ordering             — drag-drop reorder
  parsons              — drag-drop code assembly
  sjt                  — situational-judgment ranking
  scenario_branch      — choose-your-adventure
  adaptive_roleplay    — text-chat counterparty
  voice_mock_interview — live mic interview (browser SpeechRecognition)
  simulator_loop       — tick-based simulation widget
  incident_console     — 4-pane SRE drill
  fill_in_blank        — labeled blanks
  code_review          — click-buggy-lines

### Course-dependent

  code_exercise   — TERMINAL on CLI-eligible courses (kimi/aie/jspring),
                    WEB elsewhere (Monaco-graded against hidden_tests)
  code_read       — TERMINAL when language='text|markdown|plaintext';
                    otherwise WEB (scrollable code reader widget)
  concept         — TERMINAL when content has no <script>;
                    WEB when content has interactive <script> widgets

A course is CLI-ELIGIBLE if it's registered in `backend/course_assets.py`
(currently kimi-eng-course-repo / aie-course-repo / jspring-course-repo).
Steps in non-eligible courses always go WEB even if they'd otherwise be
terminal-native — sending a learner to a CLI they don't have set up would
break the "complete + helpful within terminal" principle.
"""
from __future__ import annotations

import re

WEB = "web"
TERMINAL = "terminal"
VALID = (WEB, TERMINAL)

# Exercise types that are interactive widgets in the browser. The CLI cannot
# render them; they must live on web.
_ALWAYS_WEB = frozenset({
    "mcq",
    "categorization",
    "ordering",
    "parsons",
    "sjt",
    "scenario_branch",
    "adaptive_roleplay",
    "voice_mock_interview",
    "simulator_loop",
    "incident_console",
    "fill_in_blank",
    "code_review",
})

# Exercise types whose entire UX is in the terminal (commands run, files
# edited, tests executed). Browser shows a "this step is terminal-native"
# pointer panel.
_ALWAYS_TERMINAL = frozenset({
    "terminal_exercise",
    "system_build",
})

# `<script>` body is the strong signal an interactive widget lives in the
# concept content. Heuristic only used at backfill time (Creator emits the
# field explicitly going forward).
_SCRIPT_RE = re.compile(r"<script\b", re.IGNORECASE)


_TITLE_HINTS_CLI: tuple[tuple[str, ...], ...] = (
    # kimi
    ("kimi k2", "kimi+aider", "open-source ai coding", "aider"),
    # aie / claude code
    ("ai-augmented engineering", "claude code", "claude-code"),
    # jspring
    ("spring boot", "java + spring", "jspring"),
)


def is_cli_eligible_course(course_title: str = "", course_id: str = "") -> bool:
    """A course is CLI-eligible if its title matches one of the AI-enablement
    courses we ship a per-course CLI workflow for (kimi/aie/jspring) — the
    same hints the CLI's `_slug_for_course_title` uses. We also check the
    course_assets registry; if a future course registers there, it lights up
    automatically.

    The CourseAsset registry keys by slug (kimi/aie/jspring), not by LMS
    course_id (`created-...`), so we can't directly look up by id — we match
    on title instead. Course authors register the asset entry when they ship
    a CLI workflow for the course.
    """
    title = (course_title or "").lower()
    if not title:
        return False

    for hints in _TITLE_HINTS_CLI:
        if any(h in title for h in hints):
            return True

    # Future-proofing: any CourseAsset's title_hint hit is also eligible.
    try:
        from .course_assets import _COURSE_ASSETS
        for asset in _COURSE_ASSETS.values():
            hint = (asset.title_hint or "").lower()
            if hint and hint in title:
                return True
    except Exception:
        pass

    return False


def classify_step(
    *,
    exercise_type: str | None,
    content: str | None,
    course_cli_eligible: bool,
) -> str:
    """Return 'web' or 'terminal' for a single step. Pure function — caller
    is responsible for resolving `course_cli_eligible` from the course id.

    Used:
      - by `scripts/backfill_learner_surface.py` to fill the new column
      - by the Creator prompt's default-suggestion logic (so the LLM sees a
        sensible default it can override per step)

    Never called at runtime by API endpoints. The runtime reads
    step.learner_surface directly.
    """
    et = (exercise_type or "concept").strip().lower()

    if et in _ALWAYS_WEB:
        return WEB
    if et in _ALWAYS_TERMINAL:
        return TERMINAL if course_cli_eligible else WEB

    # Course-dependent: code_exercise / code_read / concept
    if et == "code_exercise":
        return TERMINAL if course_cli_eligible else WEB

    if et == "code_read":
        # Heuristic only meaningful at backfill — the Creator should declare
        # this explicitly going forward
        return TERMINAL if course_cli_eligible else WEB

    if et == "concept":
        # Has interactive widget? → web. Else terminal-friendly text.
        if content and _SCRIPT_RE.search(content):
            return WEB
        return TERMINAL if course_cli_eligible else WEB

    # Unknown exercise type — safest default is WEB (browser-grading is
    # the universal fallback)
    return WEB


def normalize(value) -> str | None:
    """Normalize a raw value (LLM string, legacy data, etc.) to a valid enum
    or None. Used by `_is_complete` to validate Creator output.
    """
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in VALID:
        return s
    # Tolerate common variants the LLM might emit
    if s in ("browser", "ui", "frontend"):
        return WEB
    if s in ("cli", "tty", "shell", "command-line"):
        return TERMINAL
    return None
