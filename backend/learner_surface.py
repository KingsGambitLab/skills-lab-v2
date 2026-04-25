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

# 2026-04-25 v5 — surface classification is decided by EXERCISE TYPE +
# VALIDATION SHAPE only, per user directive (verbatim, 2026-04-25):
#   1. Code assignment + Docker test cases + single file → WEB
#   2. Code assignment + GitHub Actions + multiple files → TERMINAL
#   3. Everything else → WEB
#
# Mapping to our taxonomy:
#   - terminal_exercise (cli_commands) → TERMINAL
#   - system_build with validation.gha_workflow_check → TERMINAL
#   - everything else → WEB
#
# Why this rule and not v4 (renderer-derived): v4 keyed on "did the
# renderer's stripper change the content" which is correct in principle
# but produces flapping classification when LLMs add minor styling. The
# user's structural insight: surface follows the GRADING SHAPE, not the
# look-and-feel of the briefing. Single rule, no content sniffing.
#
# `markdown_strip.has_browser_only_blocks` lives in `backend/markdown_strip.py`
# for the renderer's own use, but is no longer consulted by the classifier.


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
    content: str | None = None,
    validation: dict | None = None,
    course_cli_eligible: bool = True,
) -> str:
    """Return 'web' or 'terminal' for a single step.

    2026-04-25 v5 — three-line rule per user directive (verbatim):
      1. Code assignment + Docker test cases + single file → WEB
      2. Code assignment + GitHub Actions + multiple files → TERMINAL
      3. Everything else → WEB

    Materialized on our exercise-type taxonomy:
      - `terminal_exercise` (cli_commands runner — multi-file work in a
        real repo) → TERMINAL.
      - `system_build` WITH `validation.gha_workflow_check` (multi-file
        capstone graded by GHA) → TERMINAL.
      - Everything else (concept, mcq, categorization, scenario_branch,
        sjt, ordering, parsons, code_review, code_read, code_exercise
        with hidden_tests, system_build with endpoint_check or rubric,
        adaptive_roleplay, voice_mock_interview, simulator_loop,
        incident_console, fill_in_blank) → WEB.

    Why this rule (and not the v4 renderer-based derivation): the v4 rule
    keyed on "did the renderer's stripper change the content?" — that's
    correct in principle but produced flapping results when the LLM
    emitted minor styling. The user's structural insight: surface is
    determined by HOW THE LEARNER GRADES, not by the look-and-feel of
    the briefing content. GHA-graded multi-file work needs a real
    terminal; sandboxed Docker single-file works in the browser; reading
    + drag-drop + MCQ all work in the browser. That's it.

    `content` and `course_cli_eligible` are accepted for back-compat
    but no longer drive classification — only `exercise_type` and
    `validation` matter.
    """
    et = (exercise_type or "concept").strip().lower()

    # Rule 2: terminal_exercise is by definition multi-file repo work.
    if et == "terminal_exercise":
        return TERMINAL if course_cli_eligible else WEB

    # Rule 2 (cont.): system_build is terminal IFF graded by GHA.
    # Otherwise (endpoint_check / rubric / phases-only) it's web — the
    # learner pastes a deploy URL or markdown into the browser.
    # Use `in` check (not .get truthy) so an empty/sparse gha_workflow_check
    # block still classifies as terminal — its presence is the signal.
    if et == "system_build":
        v = validation or {}
        if "gha_workflow_check" in v and v["gha_workflow_check"] is not None:
            return TERMINAL if course_cli_eligible else WEB
        return WEB

    # Rule 3: everything else (mcq, drag-drop, scenario_branch, concept,
    # code_exercise with Docker tests, code_review, code_read, etc.) → web.
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
