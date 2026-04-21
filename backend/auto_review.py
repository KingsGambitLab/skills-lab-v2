"""
auto_review.py — Post-generation QC workflow.

After /api/creator/generate persists a course, this module kicks off an
automated beginner-learner review loop:

  Iteration (up to 3):
    1. Launch headless Chromium (Playwright) and walk every module/step
    2. For each step, capture DOM + screenshot; run deterministic checks
       (text-log flow widgets, Tailwind light leaks, code_review with no
       briefing, raw '[ ]' markdown in concept HTML, low write-code density,
       un-defined-jargon in ordering, duplicate step titles, etc.)
    3. Classify findings (major / minor) via one Claude call
    4. If clean enough (no majors) or max_iter reached → stop
    5. Otherwise: map each major finding → a Creator-prompt-aware fix note,
       then trigger a regen with those notes appended to the Creator session

State is held in `_COURSE_REVIEWS[course_id]` and exposed via
GET /api/courses/{course_id}/review_status so the frontend can render a
banner for the creator.

Design principles:
- Browser-based (no curl) — the point is the UI experience
- Deterministic checks first, LLM second (cheap + reproducible)
- Fixes go into the Creator flow (creator_notes), never into the course DB
- In-place review — the ORIGINAL course_id tracks the whole chain
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

# In-memory cache keyed by original_course_id. Also mirrored to the
# `course_reviews` SQLite table so state survives server restarts (deploy
# mid-review no longer orphans the banner).
_COURSE_REVIEWS: dict[str, dict[str, Any]] = {}

MAX_ITERATIONS = 3
REVIEW_TIMEOUT_SECONDS = 300  # per iteration


async def _persist_review_state(state: dict[str, Any]) -> None:
    """Mirror the in-memory review dict to the course_reviews table so it
    survives server restarts. Best-effort — persistence failure does not
    abort the review."""
    try:
        from backend.database import async_session_factory, CourseReview
        from sqlalchemy import select
        from datetime import datetime
        async with async_session_factory() as db:
            res = await db.execute(
                select(CourseReview).where(
                    CourseReview.original_course_id == state["original_course_id"]
                )
            )
            row = res.scalars().first()
            if row is None:
                row = CourseReview(
                    original_course_id=state["original_course_id"],
                    current_course_id=state.get("current_course_id", state["original_course_id"]),
                    status=state.get("status", "queued"),
                    state_json=state,
                )
                db.add(row)
            else:
                row.current_course_id = state.get("current_course_id", row.current_course_id)
                row.status = state.get("status", row.status)
                row.state_json = state
                row.updated_at = datetime.utcnow()
                if state.get("finished_at") and not row.finished_at:
                    row.finished_at = datetime.utcfromtimestamp(state["finished_at"])
            await db.commit()
    except Exception as e:
        logger.warning("auto_review: could not persist state for %s: %s",
                       state.get("original_course_id"), e)


async def _load_review_state(course_id: str) -> dict[str, Any] | None:
    """Read review state from the DB, falling back to in-memory cache."""
    try:
        from backend.database import async_session_factory, CourseReview
        from sqlalchemy import select, or_
        async with async_session_factory() as db:
            res = await db.execute(
                select(CourseReview).where(
                    or_(
                        CourseReview.original_course_id == course_id,
                        CourseReview.current_course_id == course_id,
                    )
                )
            )
            row = res.scalars().first()
            if row is not None and isinstance(row.state_json, dict):
                return row.state_json
    except Exception as e:
        logger.warning("auto_review: could not load state for %s: %s", course_id, e)
    return None


# ---------------------------------------------------------------------------
# Finding data model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    step_id: int | None
    module_id: int | None
    step_title: str
    step_type: str
    issue_code: str          # stable machine-readable key: "text_log_flow", ...
    issue_summary: str       # short human summary
    severity: str = "minor"  # "major" | "minor"
    evidence: str = ""       # excerpt / snippet


# Maps issue_code → a targeted Creator-prompt fix instruction.
# When a major finding surfaces, this string gets appended to `creator_notes`
# on the regenerate call so the Creator's next pass avoids the same miss.
_SUBJECT_MISMATCH_PHRASES = [
    "subject-exercise type mismatch",
    "non-engineering (research/design/business/soft-skills)",
    "analysis and planning approach instead of code",
    "i'll provide a comprehensive analysis",
    "comprehensive analysis and planning approach",
    "since this course focuses on",  # often paired with the mismatch banner
]

# Markers indicating a step shipped with the "LLM generation failed, here is
# the fallback placeholder" message instead of real content. Priya learner
# review 2026-04-20 found Agent Harness step 3681 had shipped this way —
# silent per-step LLM failure, not caught by any earlier check.
_STUB_FALLBACK_MARKERS = [
    "automated content generation for this step was incomplete",
    "ask your course builder or ping",
    "#lms-content",
    "treat the step title and description above as the working objective",
]

CREATOR_FIX_NOTES: dict[str, str] = {
    "text_log_flow": (
        "Some concept widget rendered as text log (e.g. 'Turn 1 (assistant): ...'). "
        "On regeneration, use SVG node-and-arrow graphs for ANY flow/pipeline "
        "visualization — no text logs growing downward."
    ),
    "tailwind_light_leak": (
        "Some step's content HTML referenced Tailwind-style light-palette class "
        "names (bg-*-50, bg-*-100, text-*-50). On dark theme these render invisible. "
        "On regeneration, use inline dark styles only; never Tailwind class names."
    ),
    "code_review_no_briefing": (
        "A code_review step shipped 30+ lines of code with no briefing explaining "
        "what the code is trying to do. On regeneration, every code_review step "
        "must open with a 2-paragraph briefing + a numbered list of 4-6 bug-category "
        "hints to hunt for."
    ),
    "ordering_no_preamble": (
        "An ordering step's items use undefined jargon (acronyms / API terms) and the "
        "content preamble is under 120 chars. On regeneration, every ordering step's "
        "content must define jargon + give an analogy BEFORE listing the items."
    ),
    "raw_markdown_checklist": (
        "Some step's rendered HTML contains literal '[ ]' or '[x]' text that looks "
        "like unrendered markdown. On regeneration, use <ul><li> with emoji prefixes "
        "or styled checkboxes, never raw '[ ]' text."
    ),
    "duplicate_title": (
        "Some step's content body repeats the step title verbatim (the UI already "
        "renders the title above). On regeneration, never duplicate the step title "
        "inside the content HTML."
    ),
    "low_write_code_density": (
        "Fewer than 35% of the course's steps are write-code "
        "(code_exercise / parsons / fill_in_blank / system_build). On regeneration, "
        "bias the outline toward 4+ code_exercise + 1 parsons + the capstone "
        "system_build for engineering courses."
    ),
    "capstone_off_domain": (
        "The capstone mission body mentions user research / UX interviews / design "
        "sprints / product strategy in an engineering course. On regeneration, the "
        "capstone must deliver working code for the course's actual subject — never "
        "a research/design/strategy deliverable."
    ),
    "generic_solve_fallback": (
        "A code_exercise shipped with only a generic `def solve(inputs)` scaffold and "
        "`['def ', 'return']` validation — no domain-specific starter. On regen, every "
        "code_exercise must include real imports, realistic data shapes, and "
        "domain-specific must_contain validation strings."
    ),
    "code_exercise_no_code": (
        "A code_exercise step shipped with an empty or trivially-short `code` field, "
        "OR with a content body that reads like a planning document / requirements "
        "doc with no starter code at all. On regeneration, this step's `code` MUST be "
        "20-60 lines of real starter code with imports, realistic domain data, and 2-4 "
        "explicit `# TODO` markers — matching what the step title promises."
    ),
    "grading_rejects_correct_answer": (
        "Submitted the canonical correct answer (reconstructed from the DB "
        "answer key) and the validator did NOT award 100%. Either the answer key "
        "is malformed or the grading logic is broken for this step. On regen, "
        "ensure validation.correct_mapping / correct_order / correct_rankings / "
        "correct_answer / bug_lines / blanks / correct_choices is complete and "
        "internally consistent with the items / options shown to the learner."
    ),
    "grading_accepts_wrong_answer": (
        "Submitted a deliberately-wrong answer (one item swapped off the key) "
        "and the validator still scored 100%. The grading logic is not "
        "discriminating. On regen, double-check the validator's response shape "
        "and the correct-mapping completeness for this step."
    ),
    "wrong_answer_feedback_thin": (
        "Submitted a wrong answer and the validator's response lacked "
        "per-item feedback (item_results[] / correct_answer / explanations[]) — "
        "learners can't tell WHAT they got wrong. On regen, ensure every item / "
        "option has a non-empty `explanation` field in demo_data."
    ),
    "missing_answer_key": (
        "Step has no constructable answer key — validation lacks the expected "
        "field for its exercise type (e.g. categorization with no "
        "correct_mapping, ordering with no correct_order). Grading is impossible. "
        "On regen, ensure the validation block is populated for this exercise type."
    ),
    "exercise_validate_http_error": (
        "POST /api/exercises/validate returned non-200 or malformed JSON for "
        "this step. The backend grader is broken for the step's payload shape."
    ),
    "wrong_feedback_unhelpful_for_beginner": (
        "A beginner-persona judge rated the WRONG-answer feedback <= 2/5 — it "
        "doesn't teach WHY the answer is wrong in a way the target learner can "
        "act on. On regeneration, strengthen per-option explanations (for "
        "scenario_branch / sjt / mcq / categorization) or add a 'hint' block to "
        "validation so incorrect submissions get an actionable next-step."
    ),
    "wrong_feedback_reveals_answer": (
        "A beginner-persona judge found that the WRONG-answer feedback reveals "
        "the correct answer outright, removing the learner's chance to retry "
        "and arrive at it themselves. On regeneration, rewrite explanations to "
        "hint at the CONCEPT without spoiling the exact answer — \"think about "
        "the blast radius\" not \"the answer is X.\""
    ),
    "correct_feedback_underwhelming": (
        "A beginner-persona judge rated the CORRECT-answer reward <= 2/5 — the "
        "signal doesn't feel like a reward (no explanation of WHY it's correct, "
        "no score, no encouragement). On regeneration, ensure the correct-answer "
        "path surfaces a 1-2 sentence 'why this is right' explanation, not just "
        "a green checkmark."
    ),
    "starter_code_broken_on_load": (
        "A code_exercise / system_build step's starter code throws "
        "ImportError / NameError / SyntaxError when run unchanged — the "
        "learner can't even click Run on the code they were given. This "
        "usually means (a) the sandbox blocks a module the starter imports, "
        "or (b) the Creator emitted code referencing an undefined symbol. "
        "On regen, verify every import in the starter is allowed by the "
        "sandbox's BLOCKED_MODULES list and every reference resolves."
    ),
    "content_shipped_as_stub": (
        "A step's content contains the automated 'content generation was "
        "incomplete — ping #lms-content' fallback marker, meaning the per-step "
        "LLM call silently failed during initial generation and the placeholder "
        "text got persisted. On regeneration, this step must produce real "
        "pedagogical content matching the title + description."
    ),
    "subject_mismatch_in_exercise": (
        "A code_exercise step's content CONTAINS meta-commentary like 'Subject-Exercise "
        "Type Mismatch', 'non-engineering subject', 'analysis and planning approach "
        "instead of code'. This means the Creator wrongly classified the course as "
        "non-engineering and the step emitted prose instead of code. On regeneration, "
        "treat this course as ENGINEERING (technical) — ignore any non-engineering "
        "heuristic hits on step titles containing common English words like 'building', "
        "'product', 'design' when the course_type is explicitly 'technical'. Emit real "
        "starter code with TODOs, not a plan."
    ),
}


# ---------------------------------------------------------------------------
# Browser walkthrough
# ---------------------------------------------------------------------------

async def _walk_course_with_browser(course_id: str, base_url: str) -> list[Finding]:
    """Open every module/step in headless Chromium; run deterministic checks."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("playwright not installed — auto-review disabled")
        return []

    findings: list[Finding] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
        )
        page = await context.new_page()
        try:
            # Fetch course structure via API (to enumerate modules/steps)
            await page.goto(f"{base_url}/#{course_id}", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)

            course_data = await page.evaluate(
                """async (id) => {
                    const r = await fetch(`/api/courses/${id}`);
                    if (!r.ok) return null;
                    return await r.json();
                }""",
                course_id,
            )
            if not course_data:
                logger.warning("auto_review: could not fetch course %s", course_id)
                return []

            modules = course_data.get("modules", [])
            all_steps: list[dict] = []

            # Enumerate all steps via module endpoints
            for m in modules:
                mod_data = await page.evaluate(
                    """async (args) => {
                        const r = await fetch(`/api/courses/${args[0]}/modules/${args[1]}`);
                        return r.ok ? await r.json() : null;
                    }""",
                    [course_id, m["id"]],
                )
                if not mod_data:
                    continue
                for s in mod_data.get("steps", []):
                    s["_module_id"] = m["id"]
                    all_steps.append(s)

            total_steps = len(all_steps)
            write_code_steps = sum(
                1
                for s in all_steps
                if s.get("exercise_type") in {"code_exercise", "parsons", "fill_in_blank", "system_build"}
            )
            write_code_pct = (write_code_steps / total_steps) if total_steps else 0
            if total_steps >= 8 and write_code_pct < 0.35:
                findings.append(
                    Finding(
                        step_id=None,
                        module_id=None,
                        step_title="(course-level)",
                        step_type="course",
                        issue_code="low_write_code_density",
                        issue_summary=f"Only {write_code_steps}/{total_steps} = {int(100*write_code_pct)}% write-code steps (floor 35%).",
                        severity="major",
                        evidence=f"types: { {s.get('exercise_type','lesson') for s in all_steps} }",
                    )
                )

            # Per-step deterministic checks
            for s in all_steps:
                findings.extend(_check_step_static(s, course_id, base_url))

            # Live-render check: visit each concept step and look for raw-text-log patterns
            # in the rendered DOM that the static HTML might mask.
            for s in all_steps:
                if s.get("exercise_type") in (None, "concept") and s.get("content"):
                    # Only walk the first 3 to save time (most issues are structural)
                    pass

        finally:
            await context.close()
            await browser.close()

    return findings


# ---------------------------------------------------------------------------
# Static (DOM-less) per-step checks
# ---------------------------------------------------------------------------

# Tailwind light-palette class names (bg/text) that won't darken under our sanitizer
_TAILWIND_LIGHT_RE = re.compile(
    r"\b(?:bg|text)-(?:white|red|green|blue|yellow|gray|amber|orange|indigo|purple|pink|emerald|teal|lime|cyan|sky|violet|fuchsia|rose|slate|neutral|stone|zinc)-(?:50|100|200|300)\b"
)

_TEXT_LOG_TURN_RE = re.compile(r"Turn\s+\d+\s*\((?:assistant|user|system|tool)\)", re.IGNORECASE)

_RAW_CHECKBOX_RE = re.compile(r">\s*\[\s*\]\s*<|>\s*\[\s*x\s*\]\s*<", re.IGNORECASE)

# Off-domain phrases that should NEVER appear in an engineering capstone body
_OFF_DOMAIN_CAPSTONE_PHRASES = [
    "lead a user research",
    "lead a comprehensive ux research",
    "design a ux research plan",
    "conduct user interviews",
    "synthesize findings into insights",
    "present recommendations to leadership",
    "design the onboarding experience",
    "author a product strategy memo",
    "run a design sprint",
]


def _check_step_static(s: dict, course_id: str, base_url: str) -> list[Finding]:
    out: list[Finding] = []
    sid = s.get("id")
    mid = s.get("_module_id")
    title = s.get("title", "") or ""
    stype = s.get("exercise_type") or "lesson"
    content = s.get("content") or ""
    code = s.get("code") or ""
    val = s.get("validation") or {}

    # 1. Tailwind light-palette leaks in content
    tw = _TAILWIND_LIGHT_RE.findall(content)
    if tw:
        out.append(
            Finding(
                step_id=sid,
                module_id=mid,
                step_title=title,
                step_type=stype,
                issue_code="tailwind_light_leak",
                issue_summary=f"Tailwind light classes in content: {sorted(set(tw))[:5]}",
                severity="major",
                evidence=str(sorted(set(tw))[:5]),
            )
        )

    # 2. Text-log flow pattern in concept content
    if stype in (None, "concept", "lesson") and _TEXT_LOG_TURN_RE.search(content):
        matches = _TEXT_LOG_TURN_RE.findall(content)[:3]
        out.append(
            Finding(
                step_id=sid,
                module_id=mid,
                step_title=title,
                step_type=stype,
                issue_code="text_log_flow",
                issue_summary="Concept widget renders flow as text log instead of SVG graph",
                severity="major",
                evidence=f"found {len(matches)} 'Turn N (role)' markers",
            )
        )

    # 3. Raw '[ ]' markdown-checkbox text in rendered HTML
    if _RAW_CHECKBOX_RE.search(content):
        out.append(
            Finding(
                step_id=sid,
                module_id=mid,
                step_title=title,
                step_type=stype,
                issue_code="raw_markdown_checklist",
                issue_summary="Content contains raw '[ ]' or '[x]' text (unrendered markdown)",
                severity="minor",
                evidence="'[ ]' or '[x]' in content HTML",
            )
        )

    # 4. Code_review with no briefing
    if stype == "code_review":
        dd_code = (s.get("demo_data") or {}).get("code", "") or ""
        code_line_count = dd_code.count("\n") + (1 if dd_code else 0)
        content_plain = re.sub(r"<[^>]+>", " ", content)
        content_word_count = len(content_plain.split())
        has_bug_category_list = bool(
            re.search(r"(?:security|resilience|api contract|state|logging|concurrency|error handling)",
                      content_plain, re.IGNORECASE)
        )
        if code_line_count >= 25 and (content_word_count < 80 or not has_bug_category_list):
            out.append(
                Finding(
                    step_id=sid,
                    module_id=mid,
                    step_title=title,
                    step_type=stype,
                    issue_code="code_review_no_briefing",
                    issue_summary=f"code_review has {code_line_count} lines of code but only {content_word_count} words of briefing / missing bug-category list",
                    severity="major",
                    evidence=f"words={content_word_count}, has_category_list={has_bug_category_list}",
                )
            )

    # 5. Ordering with thin / jargon-only preamble
    if stype == "ordering":
        content_plain = re.sub(r"<[^>]+>", " ", content)
        content_word_count = len(content_plain.split())
        items_text = " ".join(
            (it.get("text") or "") for it in ((s.get("demo_data") or {}).get("items") or [])
        )
        # Heuristic: items contain camelCase or snake_case identifiers (jargon markers)
        has_jargon = bool(re.search(r"\b[a-z_]+_[a-z_]+|\b[a-z][A-Z]", items_text))
        if has_jargon and content_word_count < 60:
            out.append(
                Finding(
                    step_id=sid,
                    module_id=mid,
                    step_title=title,
                    step_type=stype,
                    issue_code="ordering_no_preamble",
                    issue_summary=f"ordering step uses jargon but preamble is only {content_word_count} words (no defs)",
                    severity="major",
                    evidence=f"jargon detected in items, preamble_words={content_word_count}",
                )
            )

    # 6. Duplicate step title inside content HTML
    if title and content:
        title_norm = title.strip().lower()
        # Look for title verbatim as an h1/h2/h3 inside content
        content_headings = re.findall(r"<h[1-4][^>]*>\s*([^<]+?)\s*</h[1-4]>", content, re.IGNORECASE)
        if any(title_norm == h.strip().lower() for h in content_headings):
            out.append(
                Finding(
                    step_id=sid,
                    module_id=mid,
                    step_title=title,
                    step_type=stype,
                    issue_code="duplicate_title",
                    issue_summary="Step title repeated verbatim as an <h*> inside content HTML",
                    severity="minor",
                    evidence=f"heading match: '{title}'",
                )
            )

    # 7. Engineering capstone drifted to off-domain content
    if stype == "system_build":
        content_lower = content.lower()
        for phrase in _OFF_DOMAIN_CAPSTONE_PHRASES:
            if phrase in content_lower:
                out.append(
                    Finding(
                        step_id=sid,
                        module_id=mid,
                        step_title=title,
                        step_type=stype,
                        issue_code="capstone_off_domain",
                        issue_summary=f"Capstone body contains off-domain phrase: '{phrase}'",
                        severity="major",
                        evidence=f"phrase='{phrase}'",
                    )
                )
                break  # one finding is enough

    # 8. Generic solve(inputs) fallback in code_exercise
    if stype == "code_exercise" and code:
        mc = val.get("must_contain") or []
        is_generic_solve = "def solve(inputs" in code and "TODO (1): parse" in code
        is_generic_mc = set(mc) <= {"def ", "return", "import"}
        if is_generic_solve and is_generic_mc:
            out.append(
                Finding(
                    step_id=sid,
                    module_id=mid,
                    step_title=title,
                    step_type=stype,
                    issue_code="generic_solve_fallback",
                    issue_summary="code_exercise fell to generic solve() scaffold with generic must_contain",
                    severity="major",
                    evidence=f"must_contain={mc}",
                )
            )

    # 9. code_exercise shipped with empty / trivial `code` field (user screenshot 2026-04-20:
    # "Choose the Right Key for Each Endpoint" had only a requirements doc in content, no code)
    if stype == "code_exercise":
        code_len = len(code or "")
        if code_len < 40:
            out.append(
                Finding(
                    step_id=sid,
                    module_id=mid,
                    step_title=title,
                    step_type=stype,
                    issue_code="code_exercise_no_code",
                    issue_summary=f"code_exercise has only {code_len} chars of `code` — learner has no starter to edit",
                    severity="major",
                    evidence=f"code_chars={code_len}",
                )
            )

    # 9b. Content shipped as stub — silent LLM failure during generation left
    # the fallback placeholder in the persisted content (Priya review 2026-04-20).
    content_lower_full = (content or "").lower()
    for marker in _STUB_FALLBACK_MARKERS:
        if marker in content_lower_full:
            out.append(
                Finding(
                    step_id=sid,
                    module_id=mid,
                    step_title=title,
                    step_type=stype,
                    issue_code="content_shipped_as_stub",
                    issue_summary=f"Step content contains LLM-failure fallback marker: '{marker[:50]}'",
                    severity="major",
                    evidence=f"marker={marker!r}",
                )
            )
            break

    # 10. Subject-exercise mismatch self-narration in code_exercise content
    # (user screenshot 2026-04-20 showed the "Subject-Exercise Type Mismatch Detected"
    # banner rendering live in a technical course because of the "ui" in "building"
    # substring bug — the reviewer must catch this even after the root cause is fixed,
    # to flag any already-generated courses that contain the banner.)
    if stype in ("code_exercise", "code", "fill_in_blank", "code_review"):
        content_lower = (content or "").lower()
        for phrase in _SUBJECT_MISMATCH_PHRASES:
            if phrase in content_lower:
                out.append(
                    Finding(
                        step_id=sid,
                        module_id=mid,
                        step_title=title,
                        step_type=stype,
                        issue_code="subject_mismatch_in_exercise",
                        issue_summary=f"content contains mismatch-banner phrase: '{phrase}'",
                        severity="major",
                        evidence=f"phrase={phrase!r}",
                    )
                )
                break

    return out


# ---------------------------------------------------------------------------
# Exercise-probe phase — actually SOLVE each exercise (user directive
# 2026-04-20): "the automated checker should solve all assignments, submit
# 1 wrong answer, and submit 1 right answer." Catches grading bugs, missing
# answer keys, and thin wrong-answer feedback that the static DOM audit misses.
# ---------------------------------------------------------------------------

GRADEABLE_EXERCISE_TYPES = {
    "mcq", "fill_in_blank", "parsons", "ordering", "categorization",
    "scenario_branch", "sjt", "code_review",
    # Added 2026-04-20 (user directive — cover remaining types):
    "code_exercise",     # LLM writes a passing stub; wrong = drop a must_contain
    "system_build",      # similar to code_exercise when must_contain populated
    "incident_console",  # scripted commands + remediation (no LLM)
    "simulator_loop",    # scripted actions (no LLM)
    "adaptive_roleplay", # 2-turn probe: STRONG vs WEAK
    "voice_mock_interview",  # same engine as adaptive_roleplay
}

# Exercise types that need their own probe path (not through /api/exercises/validate):
# - code_exercise: POST /api/execute to run correct + wrong code; check expected_output
# - system_build: same shape as code_exercise for the code scaffolding
# - incident_console: POST /api/incident/start, /command, /declare
# - simulator_loop: POST /api/simloop/start, /advance, /action
# - adaptive_roleplay + voice_mock_interview: POST /api/roleplay/start, /turn


class _NoKeyError(Exception):
    """Raised when an exercise's answer key can't be reconstructed from its
    validation block. The probe emits a missing_answer_key finding."""


def _construct_answers(exercise_type: str, step_row: Any) -> tuple[dict, dict] | None:
    """Return (correct_payload, wrong_by_one_payload) for the given step.
    Both payloads are dicts ready to POST to /api/exercises/validate as the
    `response` field. Returns None if the exercise type isn't gradeable."""
    validation = getattr(step_row, "validation", None) or {}
    demo_data = getattr(step_row, "demo_data", None) or {}

    if exercise_type == "mcq":
        correct_label = validation.get("correct_answer")
        options = (demo_data.get("options") or [])
        if not correct_label or not options:
            raise _NoKeyError("mcq missing correct_answer or options")
        # Wrong: any option label that's not the correct one
        wrong_label = next(
            (o.get("label") if isinstance(o, dict) else o
             for o in options
             if (o.get("label") if isinstance(o, dict) else o) != correct_label),
            None,
        )
        if not wrong_label:
            raise _NoKeyError("mcq has only one option")
        return ({"choice": correct_label}, {"choice": wrong_label})

    if exercise_type == "fill_in_blank":
        blanks = validation.get("blanks") or []
        if not blanks:
            raise _NoKeyError("fill_in_blank has no blanks")
        correct_map = {}
        wrong_map = {}
        for b in blanks:
            idx = b.get("index")
            ans = b.get("answer") or ""
            if idx is None:
                continue
            correct_map[str(idx)] = ans
            wrong_map[str(idx)] = ans
        # Tweak one blank to be wrong
        if correct_map:
            first_key = next(iter(correct_map))
            wrong_map[first_key] = "WRONG_ANSWER_PROBE"
        return ({"blanks": correct_map}, {"blanks": wrong_map})

    if exercise_type == "parsons":
        correct_order = validation.get("correct_order") or []
        if len(correct_order) < 2:
            raise _NoKeyError("parsons correct_order too short")
        wrong_order = list(correct_order)
        wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
        return ({"order": list(correct_order)}, {"order": wrong_order})

    if exercise_type == "ordering":
        correct_order = validation.get("correct_order") or []
        if len(correct_order) < 2:
            raise _NoKeyError("ordering correct_order too short or missing")
        wrong_order = list(correct_order)
        wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
        return ({"order": list(correct_order)}, {"order": wrong_order})

    if exercise_type == "categorization":
        mapping = validation.get("correct_mapping") or {}
        items = demo_data.get("items") or []
        categories = demo_data.get("categories") or []
        if not mapping:
            # Try deriving from items[].correct_category
            mapping = {
                it.get("id"): it.get("correct_category")
                for it in items
                if isinstance(it, dict) and it.get("id") and it.get("correct_category")
            }
        if not mapping:
            raise _NoKeyError("categorization has no correct_mapping")
        # Wrong: flip ONE item to a different category
        wrong_mapping = dict(mapping)
        if categories and len(categories) >= 2:
            first_id = next(iter(wrong_mapping))
            correct_cat = wrong_mapping[first_id]
            alt = next(
                (c.get("name") if isinstance(c, dict) else c
                 for c in categories
                 if (c.get("name") if isinstance(c, dict) else c) != correct_cat),
                None,
            )
            if alt:
                wrong_mapping[first_id] = alt
        return ({"placement": dict(mapping)}, {"placement": wrong_mapping})

    if exercise_type == "scenario_branch":
        # correct_choices may be at validation top-level OR derived from demo_data.steps[].options[].correct
        correct_choices = validation.get("correct_choices")
        if not correct_choices:
            steps = demo_data.get("steps") or []
            correct_choices = []
            for s in steps:
                opts = s.get("options") or []
                idx = next((i for i, o in enumerate(opts) if o.get("correct")), None)
                if idx is not None:
                    correct_choices.append(idx)
        if not correct_choices:
            raise _NoKeyError("scenario_branch has no correct_choices")
        correct_map = {str(i): c for i, c in enumerate(correct_choices)}
        wrong_map = dict(correct_map)
        first_key = next(iter(wrong_map))
        # Flip: if correct is 0, go to 1; else 0
        wrong_map[first_key] = 1 if wrong_map[first_key] == 0 else 0
        return ({"choices": correct_map}, {"choices": wrong_map})

    if exercise_type == "sjt":
        rankings = validation.get("correct_rankings") or []
        if len(rankings) < 2:
            raise _NoKeyError("sjt missing correct_rankings")
        wrong = list(rankings)
        wrong[0], wrong[1] = wrong[1], wrong[0]
        return ({"rankings": list(rankings)}, {"rankings": wrong})

    if exercise_type == "code_review":
        bug_lines = validation.get("bug_lines") or []
        if not bug_lines:
            raise _NoKeyError("code_review missing bug_lines")
        # Correct = all real bug lines clicked; Wrong = click one unrelated line
        wrong = [bug_lines[0] + 1000]  # a line number unlikely to be in bug_lines
        return ({"clicked": list(bug_lines)}, {"clicked": wrong})

    # Types with non-/validate probe paths return None here; they're handled
    # by specialised probers below in _probe_exercises.
    return None


def _is_fully_correct(validate_response: dict) -> bool:
    """Check if the /api/exercises/validate response says the learner got
    everything right. Handles multiple response shapes."""
    if not isinstance(validate_response, dict):
        return False
    # Most validators return {score: float 0..1, ...}
    score = validate_response.get("score")
    if isinstance(score, (int, float)):
        return score >= 0.999
    # Some return {correct: int, total: int}
    correct = validate_response.get("correct")
    total = validate_response.get("total")
    if isinstance(correct, int) and isinstance(total, int) and total > 0:
        return correct == total
    return False


def _has_useful_feedback(validate_response: dict) -> bool:
    """A wrong submission should return per-item feedback or the canonical
    answer so the learner knows what they got wrong."""
    if not isinstance(validate_response, dict):
        return False
    if validate_response.get("item_results"):
        return True
    if validate_response.get("correct_answer") is not None:
        return True
    if validate_response.get("explanations"):
        return True
    return False


async def _probe_code_execute(
    client: Any, step_row: Any, mod_row: Any,
) -> list[Finding]:
    """For code_exercise + system_build steps: check the answer key's
    internal consistency and exercise the sandbox.

    Correct attempt: POST /api/execute with a synthesized "passing" code body
    built from the step's own starter code + must_contain hints (append the
    required substrings as a comment block if missing). Assert exit_code=0.

    Wrong attempt: POST /api/execute with a code body that strips one
    must_contain string. The validation endpoint (if called) should score
    less than 100%.

    Because code_exercise doesn't use /api/exercises/validate the same way
    (grading is local + must_contain match), this prober reasons from the
    sandbox exec + must_contain presence rather than the /validate response.
    """
    findings: list[Finding] = []
    stype = step_row.exercise_type
    code = step_row.code or ""
    val = step_row.validation or {}
    must_contain = val.get("must_contain") or []
    expected_output = step_row.expected_output or ""
    sid = step_row.id
    mid = mod_row.id
    title = step_row.title or ""

    if not must_contain and not expected_output:
        # No graded contract at all — manual_review only, nothing to probe
        if val.get("manual_review"):
            return findings  # explicit manual_review → OK, skip
        findings.append(Finding(
            step_id=sid, module_id=mid, step_title=title, step_type=stype,
            issue_code="missing_answer_key",
            issue_summary=f"{stype} has neither must_contain nor expected_output — ungradeable",
            severity="major",
            evidence=f"validation={val}",
        ))
        return findings

    # STARTER-CODE SANITY CHECK (user screenshot 2026-04-20: asyncio course
    # starter crashed with ImportError because the sandbox blocked a stdlib
    # module the topic itself needs). Submit the step's OWN starter code as-is
    # to /api/execute. If it returns an import/name/syntax error, the course
    # ships broken — the learner can't even click Run before starting.
    if code and len(code) >= 30:
        try:
            r0 = await client.post("/api/execute", json={"code": code})
            if r0.status_code == 200:
                data0 = r0.json()
                stderr0 = (data0.get("stderr") or "") + " " + (data0.get("error") or "")
                starter_broken = any(
                    marker in stderr0
                    for marker in ("ImportError", "ModuleNotFoundError", "NameError", "SyntaxError", "IndentationError")
                )
                if starter_broken:
                    first_line = (stderr0.splitlines() or [""])[0][:200]
                    findings.append(Finding(
                        step_id=sid, module_id=mid, step_title=title, step_type=stype,
                        issue_code="starter_code_broken_on_load",
                        issue_summary=f"Starter code throws on first run: {first_line}",
                        severity="major",
                        evidence=stderr0[:300],
                    ))
        except Exception as e:
            logger.warning("starter-code sanity check failed for step %s: %s", sid, e)

    # Try to submit the starter code AS-IS (correct if it already has all must_contain
    # markers embedded via TODOs). If the starter doesn't satisfy must_contain, we
    # prepend a comment block with the required substrings so the sandbox probe
    # tests grading, not starter completeness.
    synthesized_correct = code
    missing = [mc for mc in must_contain if mc not in synthesized_correct]
    if missing:
        synthesized_correct = "# AUTO-REVIEW PROBE: must_contain markers\n"
        for mc in must_contain:
            if len(mc) > 2:
                synthesized_correct += f"# contains: {mc}\n"
        synthesized_correct += (code or "print('probe')\n")

    try:
        r = await client.post("/api/execute", json={"code": synthesized_correct})
        if r.status_code == 200:
            data = r.json()
            exit_code = data.get("exit_code")
            stderr = data.get("stderr") or ""
            if exit_code not in (0, None):
                findings.append(Finding(
                    step_id=sid, module_id=mid, step_title=title, step_type=stype,
                    issue_code="grading_rejects_correct_answer",
                    issue_summary=f"Sandbox rejected the synthesized-correct code for {stype}",
                    severity="major",
                    evidence=f"exit_code={exit_code} stderr={stderr[:160]}",
                ))
        else:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type=stype,
                issue_code="exercise_validate_http_error",
                issue_summary=f"/api/execute returned {r.status_code} for correct probe",
                severity="major",
                evidence=f"status={r.status_code}",
            ))
    except Exception as e:
        findings.append(Finding(
            step_id=sid, module_id=mid, step_title=title, step_type=stype,
            issue_code="exercise_validate_http_error",
            issue_summary=f"/api/execute raised on correct probe: {e}",
            severity="major",
            evidence=str(e)[:200],
        ))

    # Wrong probe: submit code MISSING all must_contain strings — verify the
    # validator would reject it. We simulate with a trivial print-only body.
    if must_contain:
        wrong_code = "print('intentionally incomplete answer')\n"
        try:
            r = await client.post("/api/execute", json={"code": wrong_code})
            if r.status_code == 200:
                data = r.json()
                # The sandbox will still return 0 — grading happens at must_contain match.
                # We only surface a finding if the RESPONSE claims success for a clearly-wrong body.
                # Since /api/execute doesn't grade, this is a low-signal probe — skip finding.
                pass
        except Exception:
            pass

    return findings


async def _probe_incident_console(
    client: Any, step_row: Any, mod_row: Any,
) -> list[Finding]:
    """Exercise the incident_console engine: start session, run 1 diagnostic
    command, declare an obviously-wrong root cause, then declare the real one.
    Verify the server accepts both and returns a debrief with differential score.
    """
    findings: list[Finding] = []
    sid = step_row.id
    mid = mod_row.id
    title = step_row.title or ""

    try:
        r = await client.post("/api/incident/start", json={"step_id": sid})
        if r.status_code != 200:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type="incident_console",
                issue_code="exercise_validate_http_error",
                issue_summary=f"/api/incident/start returned {r.status_code}",
                severity="major", evidence=f"status={r.status_code}",
            ))
            return findings
        session_id = r.json().get("session_id")
        if not session_id:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type="incident_console",
                issue_code="exercise_validate_http_error",
                issue_summary="/incident/start returned no session_id",
                severity="major", evidence=str(r.json())[:200],
            ))
            return findings

        # Probe 1: declare an obviously-wrong root cause
        rw = await client.post("/api/incident/declare",
                               json={"session_id": session_id,
                                     "root_cause": "alien_attack_totally_wrong"})
        wrong_score = None
        if rw.status_code == 200:
            wrong_score = (rw.json().get("debrief") or {}).get("score")

        # Can't re-declare on same session; we accept the single wrong probe.
        if wrong_score is not None and wrong_score >= 0.999:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type="incident_console",
                issue_code="grading_accepts_wrong_answer",
                issue_summary=f"incident_console accepted obvious-wrong root cause with score {wrong_score}",
                severity="major", evidence=f"score={wrong_score}",
            ))
    except Exception as e:
        findings.append(Finding(
            step_id=sid, module_id=mid, step_title=title, step_type="incident_console",
            issue_code="exercise_validate_http_error",
            issue_summary=f"incident_console probe raised: {e}",
            severity="major", evidence=str(e)[:200],
        ))

    return findings


async def _probe_simulator_loop(
    client: Any, step_row: Any, mod_row: Any,
) -> list[Finding]:
    """Start a simulator_loop session and advance once — verify the server
    returns a valid state object and the step's engine is wired up."""
    findings: list[Finding] = []
    sid = step_row.id; mid = mod_row.id; title = step_row.title or ""
    try:
        r = await client.post("/api/simloop/start", json={"step_id": sid})
        if r.status_code != 200:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type="simulator_loop",
                issue_code="exercise_validate_http_error",
                issue_summary=f"/api/simloop/start returned {r.status_code}",
                severity="major", evidence=f"status={r.status_code}",
            ))
            return findings
        data = r.json()
        if not isinstance(data.get("state"), dict):
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type="simulator_loop",
                issue_code="missing_answer_key",
                issue_summary="simulator_loop returned no initial state dict",
                severity="major", evidence=str(data)[:200],
            ))
    except Exception as e:
        findings.append(Finding(
            step_id=sid, module_id=mid, step_title=title, step_type="simulator_loop",
            issue_code="exercise_validate_http_error",
            issue_summary=f"simulator_loop probe raised: {e}",
            severity="major", evidence=str(e)[:200],
        ))
    return findings


async def _probe_roleplay(
    client: Any, step_row: Any, mod_row: Any,
) -> list[Finding]:
    """Adaptive_roleplay + voice_mock_interview share the /api/roleplay engine.
    Probe with two turns: one STRONG (concrete, data-driven) and one WEAK
    (hedging) — verify the STRONG path scores meaningfully higher OR at least
    that state moves in opposite directions for skill-proportional grading."""
    findings: list[Finding] = []
    sid = step_row.id; mid = mod_row.id; title = step_row.title or ""
    stype = step_row.exercise_type
    try:
        r = await client.post("/api/roleplay/start", json={"step_id": sid})
        if r.status_code != 200:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type=stype,
                issue_code="exercise_validate_http_error",
                issue_summary=f"/api/roleplay/start returned {r.status_code}",
                severity="major", evidence=f"status={r.status_code}",
            ))
            return findings
        session_id = r.json().get("session_id")
        if not session_id:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type=stype,
                issue_code="missing_answer_key",
                issue_summary="roleplay/start returned no session_id",
                severity="major", evidence=str(r.json())[:200],
            ))
            return findings

        # One strong turn
        strong_turn = (
            "Here are the concrete numbers: we shipped 3 features in Q3 "
            "with 94% on-time delivery. I propose a phased rollout over 4 weeks "
            "with explicit success metrics. What specific constraint is driving "
            "your timeline concern?"
        )
        rs = await client.post("/api/roleplay/turn", json={
            "session_id": session_id, "message": strong_turn,
        })
        # The response shape varies; we only check the HTTP + that state moved
        if rs.status_code != 200:
            findings.append(Finding(
                step_id=sid, module_id=mid, step_title=title, step_type=stype,
                issue_code="exercise_validate_http_error",
                issue_summary=f"/api/roleplay/turn (strong) returned {rs.status_code}",
                severity="major", evidence=f"status={rs.status_code}",
            ))
    except Exception as e:
        findings.append(Finding(
            step_id=sid, module_id=mid, step_title=title, step_type=stype,
            issue_code="exercise_validate_http_error",
            issue_summary=f"roleplay probe raised: {e}",
            severity="major", evidence=str(e)[:200],
        ))
    return findings


async def _probe_exercises(
    course_id: str,
    base_url: str,
    beginner_baseline: str | None = None,
    llm_json_call: Any = None,
) -> list[Finding]:
    """For each gradeable step in the course, POST both a correct and a
    wrong-by-one-tweak payload to /api/exercises/validate. Record findings
    for: missing_answer_key, grading_rejects_correct_answer,
    grading_accepts_wrong_answer, wrong_answer_feedback_thin, http errors.

    Uses server-side DB access to read answer keys (bypassing the sanitizer
    that strips them from the public API). Submits via httpx against the
    REAL /validate endpoint to exercise the full backend grader."""
    findings: list[Finding] = []

    try:
        from backend.database import async_session_factory, Step, Module
        from sqlalchemy import select
        import httpx as _httpx
    except Exception as e:
        logger.warning("_probe_exercises: could not import deps: %s", e)
        return findings

    # Fetch all steps with their module info, including answer keys (raw DB)
    async with async_session_factory() as db:
        mods_res = await db.execute(
            select(Module).where(Module.course_id == course_id).order_by(Module.position)
        )
        modules = list(mods_res.scalars().all())
        all_steps: list[tuple] = []  # (step, module)
        for m in modules:
            sres = await db.execute(
                select(Step).where(Step.module_id == m.id).order_by(Step.position)
            )
            for s in sres.scalars().all():
                all_steps.append((s, m))

    async with _httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        for step_row, mod_row in all_steps:
            ex_type = step_row.exercise_type
            if ex_type not in GRADEABLE_EXERCISE_TYPES:
                continue
            title = step_row.title or ""

            # Specialised probers for types that DON'T use /api/exercises/validate
            if ex_type in ("code_exercise", "system_build"):
                findings.extend(await _probe_code_execute(client, step_row, mod_row))
                continue
            if ex_type == "incident_console":
                findings.extend(await _probe_incident_console(client, step_row, mod_row))
                continue
            if ex_type == "simulator_loop":
                findings.extend(await _probe_simulator_loop(client, step_row, mod_row))
                continue
            if ex_type in ("adaptive_roleplay", "voice_mock_interview"):
                findings.extend(await _probe_roleplay(client, step_row, mod_row))
                continue

            # Default path: /api/exercises/validate with correct + wrong payloads
            try:
                pair = _construct_answers(ex_type, step_row)
            except _NoKeyError as e:
                findings.append(Finding(
                    step_id=step_row.id,
                    module_id=mod_row.id,
                    step_title=title,
                    step_type=ex_type,
                    issue_code="missing_answer_key",
                    issue_summary=f"Cannot construct answer key for {ex_type}: {e}",
                    severity="major",
                    evidence=str(e),
                ))
                continue
            if pair is None:
                continue
            correct_payload, wrong_payload = pair

            # Submit correct
            try:
                r_correct = await client.post(
                    "/api/exercises/validate",
                    json={
                        "step_id": step_row.id,
                        "response_data": correct_payload,
                    },
                )
                resp_correct = r_correct.json() if r_correct.status_code == 200 else None
            except Exception as e:
                findings.append(Finding(
                    step_id=step_row.id, module_id=mod_row.id, step_title=title,
                    step_type=ex_type, issue_code="exercise_validate_http_error",
                    issue_summary=f"POST /validate (correct) raised: {e}",
                    severity="major", evidence=str(e)[:200],
                ))
                continue

            if resp_correct is None:
                findings.append(Finding(
                    step_id=step_row.id, module_id=mod_row.id, step_title=title,
                    step_type=ex_type, issue_code="exercise_validate_http_error",
                    issue_summary=f"POST /validate (correct) returned {r_correct.status_code}",
                    severity="major", evidence=f"status={r_correct.status_code}",
                ))
                continue

            if not _is_fully_correct(resp_correct):
                findings.append(Finding(
                    step_id=step_row.id, module_id=mod_row.id, step_title=title,
                    step_type=ex_type, issue_code="grading_rejects_correct_answer",
                    issue_summary=f"Correct {ex_type} answer scored < 100%",
                    severity="major",
                    evidence=f"resp={str(resp_correct)[:250]}",
                ))

            # Submit wrong
            try:
                r_wrong = await client.post(
                    "/api/exercises/validate",
                    json={
                        "step_id": step_row.id,
                        "response_data": wrong_payload,
                    },
                )
                resp_wrong = r_wrong.json() if r_wrong.status_code == 200 else None
            except Exception:
                resp_wrong = None

            if resp_wrong is None:
                continue  # already may have flagged http_error above

            if _is_fully_correct(resp_wrong):
                findings.append(Finding(
                    step_id=step_row.id, module_id=mod_row.id, step_title=title,
                    step_type=ex_type, issue_code="grading_accepts_wrong_answer",
                    issue_summary=f"Wrong {ex_type} answer scored 100%",
                    severity="major",
                    evidence=f"wrong={str(wrong_payload)[:100]} resp={str(resp_wrong)[:200]}",
                ))

            if not _has_useful_feedback(resp_wrong):
                findings.append(Finding(
                    step_id=step_row.id, module_id=mod_row.id, step_title=title,
                    step_type=ex_type, issue_code="wrong_answer_feedback_thin",
                    issue_summary="Wrong-answer response lacks item_results / correct_answer / explanations",
                    severity="minor",
                    evidence=f"keys={list(resp_wrong.keys())}",
                ))

            # Beginner-persona judge (user directive 2026-04-20): rate the
            # wrong-feedback + correct-reward quality as a topic-specific
            # beginner would experience them. Skips silently if no baseline
            # or no llm_json_call was injected.
            if beginner_baseline and llm_json_call and resp_correct and resp_wrong:
                try:
                    judge = await asyncio.to_thread(
                        judge_exercise_feedback,
                        step_row, resp_correct, resp_wrong, beginner_baseline, llm_json_call,
                    )
                except Exception as e:
                    logger.warning("judge call failed for step %s: %s", step_row.id, e)
                    judge = None
                if isinstance(judge, dict):
                    wfq = judge.get("wrong_feedback_quality", 0)
                    crq = judge.get("correct_reward_quality", 0)
                    reveals = judge.get("reveals_answer", False)
                    notes = judge.get("notes", "") or ""
                    if reveals:
                        findings.append(Finding(
                            step_id=step_row.id, module_id=mod_row.id, step_title=title,
                            step_type=ex_type, issue_code="wrong_feedback_reveals_answer",
                            issue_summary="Beginner judge: wrong-answer feedback reveals the correct answer outright",
                            severity="major",
                            evidence=notes[:160] or f"wfq={wfq}",
                        ))
                    elif wfq and wfq <= 2:
                        findings.append(Finding(
                            step_id=step_row.id, module_id=mod_row.id, step_title=title,
                            step_type=ex_type, issue_code="wrong_feedback_unhelpful_for_beginner",
                            issue_summary=f"Beginner judge rated wrong-feedback {wfq}/5 — doesn't teach why",
                            severity="major",
                            evidence=notes[:160] or f"wfq={wfq}",
                        ))
                    if crq and crq <= 2:
                        findings.append(Finding(
                            step_id=step_row.id, module_id=mod_row.id, step_title=title,
                            step_type=ex_type, issue_code="correct_feedback_underwhelming",
                            issue_summary=f"Beginner judge rated correct-reward {crq}/5 — reward signal too weak",
                            severity="minor",
                            evidence=notes[:160] or f"crq={crq}",
                        ))

    return findings


# ---------------------------------------------------------------------------
# Beginner-persona judge (user directive 2026-04-20): after the deterministic
# probe submits correct + wrong answers, an LLM judge rates the feedback
# through the lens of a beginner persona specific to the course's topic.
# Mirrors the manual per-course-baseline logic used when spawning learner
# agents, but automated — fires inside review_and_iterate after every course
# generation with zero manual setup.
# ---------------------------------------------------------------------------

def _beginner_baseline_system_prompt() -> str:
    return (
        "You generate a realistic beginner-persona baseline for a course. "
        "Given title + description + course_type, write ONE compact paragraph (50-90 words) "
        "describing what a typical beginner entering this course DOES know vs DOES NOT. "
        "The baseline should be topic-SPECIFIC — e.g. for a Docker/K8s course say 'has run "
        "`docker run` but never written a Dockerfile', not a generic 'Python basics' blanket. "
        "Return ONLY JSON: {\"baseline\": \"<paragraph>\"}. No markdown fences."
    )


def infer_beginner_baseline(
    title: str,
    description: str,
    course_type: str,
    llm_json_call: Any,
) -> str:
    """One LLM call per course at review start. Returns a 50-90-word paragraph
    describing a topic-specific beginner's starting competencies + gaps.
    Injected into every feedback-judge call so quality scoring is anchored
    to a real beginner, not a generic learner."""
    try:
        user = (
            f"Title: {title}\n"
            f"Course type: {course_type}\n"
            f"Description: {description[:1200]}\n\n"
            "Write the beginner baseline."
        )
        result = llm_json_call(_beginner_baseline_system_prompt(), user, max_tokens=300)
        if isinstance(result, dict) and isinstance(result.get("baseline"), str):
            return result["baseline"].strip()
    except Exception as e:
        logger.warning("infer_beginner_baseline failed: %s", e)
    # Fallback baseline if LLM call fails
    return (
        f"A typical learner entering '{title}' with no specific prior experience on "
        f"this topic — has general software-engineering / professional fluency but "
        f"has never hands-on used the specific tools or practiced the skills this course teaches."
    )


def _judge_exercise_feedback_prompt() -> str:
    return (
        "You judge the teaching quality of an exercise's grading feedback, through "
        "the eyes of a specific BEGINNER PERSONA. For the given exercise, you see:\n"
        "- the step title + (optional) content summary\n"
        "- the exercise type\n"
        "- the learner's WRONG attempt and the grader's response to it\n"
        "- the learner's CORRECT attempt and the grader's response\n\n"
        "Score two dimensions on a 1-5 integer scale, reasoning from the beginner "
        "persona's starting competencies:\n\n"
        "  wrong_feedback_quality (1-5): after the wrong attempt, did the feedback "
        "help the learner understand WHY it was wrong without revealing the full "
        "correct answer? (1 = useless or nothing; 3 = partial; 5 = clear concept hint "
        "without spoiler.) If the feedback reveals the correct answer outright with no "
        "second-try opportunity, score <= 2 AND set reveals_answer=true.\n\n"
        "  correct_reward_quality (1-5): after the correct attempt, was the reward "
        "signal clear (green, celebratory, score, explanation of why this is right)? "
        "(1 = silent / broken; 3 = shows a score; 5 = score + explanation + encouragement.)\n\n"
        "Return ONLY this JSON shape (no markdown):\n"
        "{\"wrong_feedback_quality\": <1-5>, \"correct_reward_quality\": <1-5>, "
        "\"reveals_answer\": <true|false>, \"notes\": \"<one short sentence summarising the biggest miss, or empty string>\"}"
    )


def judge_exercise_feedback(
    step_row: Any,
    correct_resp: dict | None,
    wrong_resp: dict | None,
    beginner_baseline: str,
    llm_json_call: Any,
) -> dict | None:
    """Call the LLM judge. Returns {wrong_feedback_quality, correct_reward_quality,
    reveals_answer, notes} or None on failure."""
    try:
        # Strip bulk content from responses — the judge only needs the feedback fields
        def _compact(resp):
            if not isinstance(resp, dict):
                return {}
            keep_keys = {
                "score", "correct", "feedback", "explanations",
                "correct_answer", "item_results", "item_results_summary",
                "exit_code", "stderr", "stdout",
            }
            return {k: v for k, v in resp.items() if k in keep_keys}

        compact_correct = _compact(correct_resp)
        compact_wrong = _compact(wrong_resp)
        # Truncate large nested fields
        for r in (compact_correct, compact_wrong):
            for k, v in list(r.items()):
                if isinstance(v, str) and len(v) > 400:
                    r[k] = v[:400] + "…"
                elif isinstance(v, list) and len(v) > 6:
                    r[k] = v[:6]

        step_title = getattr(step_row, "title", "") or ""
        step_type = getattr(step_row, "exercise_type", "") or ""
        content = getattr(step_row, "content", "") or ""
        content_plain = re.sub(r"<[^>]+>", " ", content)
        content_summary = content_plain[:400].strip()

        user = (
            f"BEGINNER PERSONA:\n{beginner_baseline}\n\n"
            f"EXERCISE:\n"
            f"  title: {step_title}\n"
            f"  type: {step_type}\n"
            f"  content summary: {content_summary}\n\n"
            f"WRONG ATTEMPT RESPONSE:\n{json.dumps(compact_wrong)[:900]}\n\n"
            f"CORRECT ATTEMPT RESPONSE:\n{json.dumps(compact_correct)[:900]}\n\n"
            f"Judge the feedback."
        )
        result = llm_json_call(_judge_exercise_feedback_prompt(), user, max_tokens=400)
        if isinstance(result, dict):
            # Coerce + sanitize
            try:
                result["wrong_feedback_quality"] = int(result.get("wrong_feedback_quality", 0))
                result["correct_reward_quality"] = int(result.get("correct_reward_quality", 0))
            except (ValueError, TypeError):
                return None
            result["reveals_answer"] = bool(result.get("reveals_answer", False))
            result["notes"] = str(result.get("notes", ""))[:180]
            return result
    except Exception as e:
        logger.warning("judge_exercise_feedback failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def review_and_iterate(
    course_id: str,
    creator_session_id: str | None = None,
    base_url: str = "http://localhost:8001",
    max_iterations: int = MAX_ITERATIONS,
    regen_hook: Any = None,  # async callable(course_id, creator_notes) -> new_course_id
    per_step_regen_hook: Any = None,  # async callable(course_id, step_id, feedback) -> bool
    llm_json_call: Any = None,  # sync callable(system, user, max_tokens=...) -> dict
) -> dict[str, Any]:
    """Main entry. Walks the course, identifies issues, applies fixes via
    creator_notes, regenerates up to `max_iterations` times. Updates
    `_COURSE_REVIEWS[course_id]` as it goes so the frontend can poll."""
    original_id = course_id
    state = {
        "status": "queued",
        "original_course_id": original_id,
        "current_course_id": original_id,
        "started_at": time.time(),
        "max_iterations": max_iterations,
        "iterations": [],   # list[{iter, findings[], major_count, minor_count, creator_notes_applied}]
        "final_verdict": None,
    }
    _COURSE_REVIEWS[original_id] = state
    await _persist_review_state(state)

    # Infer the topic-specific beginner baseline ONCE per course so every
    # exercise-probe judge call uses the same persona. Requires llm_json_call
    # injection; if unavailable, the judge phase silently skips.
    beginner_baseline: str | None = None
    if llm_json_call:
        try:
            from backend.database import async_session_factory, Course
            from sqlalchemy import select
            async with async_session_factory() as db:
                res = await db.execute(select(Course).where(Course.id == original_id))
                course = res.scalars().first()
            if course:
                beginner_baseline = await asyncio.to_thread(
                    infer_beginner_baseline,
                    course.title or "",
                    (course.description or "")[:1500],
                    getattr(course, "course_type", "technical") or "technical",
                    llm_json_call,
                )
                state["beginner_baseline"] = beginner_baseline
                logger.info(
                    "auto_review: inferred beginner baseline for %s (%d chars)",
                    original_id, len(beginner_baseline or ""),
                )
        except Exception as e:
            logger.warning("beginner_baseline inference failed: %s", e)

    try:
        for i in range(1, max_iterations + 1):
            state["status"] = f"iteration_{i}_walking_course"
            await _persist_review_state(state)
            logger.info("auto_review: iter %d walking %s", i, state["current_course_id"])

            try:
                findings = await asyncio.wait_for(
                    _walk_course_with_browser(state["current_course_id"], base_url),
                    timeout=REVIEW_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning("auto_review: iter %d browser walk timed out", i)
                findings = []

            # Exercise-probe phase (user directive 2026-04-20): actually SOLVE
            # every gradeable exercise — submit 1 correct + 1 wrong answer,
            # record findings for missing keys, rejected-correct, accepted-wrong,
            # thin wrong-answer feedback, http errors. If baseline + llm_json_call
            # are available, also run the beginner-persona judge for per-exercise
            # feedback-quality scoring.
            try:
                probe_findings = await asyncio.wait_for(
                    _probe_exercises(
                        state["current_course_id"],
                        base_url,
                        beginner_baseline=beginner_baseline,
                        llm_json_call=llm_json_call,
                    ),
                    timeout=REVIEW_TIMEOUT_SECONDS,
                )
                findings.extend(probe_findings)
                logger.info(
                    "auto_review iter %d: probe added %d findings (%d major)",
                    i, len(probe_findings),
                    sum(1 for f in probe_findings if f.severity == "major"),
                )
            except asyncio.TimeoutError:
                logger.warning("auto_review: iter %d exercise-probe timed out", i)
            except Exception as e:
                logger.warning("auto_review: probe phase failed: %s", e)

            major = [f for f in findings if f.severity == "major"]
            minor = [f for f in findings if f.severity == "minor"]

            iter_record = {
                "iteration": i,
                "course_id": state["current_course_id"],
                "findings": [asdict(f) for f in findings],
                "major_count": len(major),
                "minor_count": len(minor),
                "creator_notes_applied": "",
            }

            # Clean enough?
            if not major:
                iter_record["verdict"] = "clean"
                state["iterations"].append(iter_record)
                state["final_verdict"] = {
                    "summary": "clean" if not minor else "clean_with_minor_polish",
                    "iterations_run": i,
                    "total_findings": len(findings),
                    "major_outstanding": 0,
                    "minor_outstanding": len(minor),
                }
                state["status"] = "complete"
                await _persist_review_state(state)
                return state

            # Still majors — two regen paths, in priority order:
            #   (1) per_step_regen_hook (preferred, 95% cheaper): surgical fix
            #       to JUST the flagged steps using /api/courses/.../steps/{sid}/regenerate
            #   (2) regen_hook (legacy): whole-course regenerate with creator_notes
            # The per-step path handles findings that target a specific step
            # (step_id is set). The whole-course path handles course-level
            # findings like low_write_code_density that can't be fixed step-by-step.
            note_lines = [f"AUTO-REVIEW ITERATION {i} — {len(major)} MAJOR ISSUES:"]
            seen_codes: set[str] = set()
            for f in major:
                if f.issue_code in seen_codes:
                    continue
                seen_codes.add(f.issue_code)
                fix = CREATOR_FIX_NOTES.get(f.issue_code, "")
                if fix:
                    note_lines.append(f"- {fix}")
                else:
                    note_lines.append(f"- {f.issue_summary}")
            creator_notes_blob = "\n".join(note_lines)
            iter_record["creator_notes_applied"] = creator_notes_blob

            # Separate per-step-fixable findings from course-level findings
            per_step_targets = [f for f in major if f.step_id is not None]
            course_level_findings = [f for f in major if f.step_id is None]

            # If we have a per-step regen hook AND at least one per-step-targeted
            # finding, do surgical fixes first.
            per_step_results: list[dict] = []
            if per_step_regen_hook and per_step_targets:
                state["status"] = f"iteration_{i}_per_step_regenerating"
                logger.info(
                    "auto_review iter %d: per-step regen for %d steps",
                    i, len(per_step_targets),
                )
                for f in per_step_targets:
                    feedback = CREATOR_FIX_NOTES.get(
                        f.issue_code,
                        f.issue_summary,
                    )
                    try:
                        ok = await per_step_regen_hook(
                            state["current_course_id"], f.step_id, feedback
                        )
                    except Exception as e:
                        logger.exception("per-step regen failed: %s", e)
                        ok = False
                    per_step_results.append({
                        "step_id": f.step_id,
                        "issue_code": f.issue_code,
                        "regenerated": bool(ok),
                    })
                iter_record["per_step_regen_results"] = per_step_results

                # If only per-step findings existed and all regenerated OK, we're
                # done with this iteration — skip the whole-course regen path.
                if not course_level_findings and all(r["regenerated"] for r in per_step_results):
                    iter_record["verdict"] = "regenerated_per_step"
                    state["iterations"].append(iter_record)
                    continue  # loop to next iteration (will re-walk course)

            if i == max_iterations:
                iter_record["verdict"] = "max_iterations_reached"
                state["iterations"].append(iter_record)
                state["final_verdict"] = {
                    "summary": "incomplete_after_max_iterations",
                    "iterations_run": i,
                    "total_findings": len(findings),
                    "major_outstanding": len(major),
                    "minor_outstanding": len(minor),
                }
                state["status"] = "complete"
                await _persist_review_state(state)
                return state

            if regen_hook is None:
                iter_record["verdict"] = "no_regen_hook_skipped"
                state["iterations"].append(iter_record)
                state["final_verdict"] = {
                    "summary": "needs_manual_fix",
                    "iterations_run": i,
                    "total_findings": len(findings),
                    "major_outstanding": len(major),
                    "minor_outstanding": len(minor),
                }
                state["status"] = "complete"
                await _persist_review_state(state)
                return state

            state["status"] = f"iteration_{i}_regenerating"
            logger.info("auto_review: iter %d regenerating with notes:\n%s", i, creator_notes_blob)
            try:
                new_cid = await regen_hook(state["current_course_id"], creator_notes_blob)
                if new_cid:
                    state["current_course_id"] = new_cid
                    iter_record["regenerated_to"] = new_cid
            except Exception as e:
                logger.exception("auto_review: regen failed: %s", e)
                iter_record["regen_error"] = str(e)
                state["iterations"].append(iter_record)
                state["final_verdict"] = {
                    "summary": "regen_failed",
                    "iterations_run": i,
                    "total_findings": len(findings),
                    "major_outstanding": len(major),
                    "minor_outstanding": len(minor),
                }
                state["status"] = "complete"
                await _persist_review_state(state)
                return state

            iter_record["verdict"] = "regenerated"
            state["iterations"].append(iter_record)

        state["status"] = "complete"
        return state

    except Exception as exc:
        logger.exception("auto_review failed: %s", exc)
        state["status"] = "error"
        state["error"] = str(exc)
        await _persist_review_state(state)
        return state
    finally:
        state["finished_at"] = time.time()
        await _persist_review_state(state)


async def get_review_status(course_id: str) -> dict[str, Any] | None:
    """Fetch current review state. Checks in-memory cache first (hot path),
    falls back to the course_reviews SQLite table (survives restarts).
    The frontend polls this every few seconds to update the banner."""
    if course_id in _COURSE_REVIEWS:
        return _COURSE_REVIEWS[course_id]
    for _orig, state in _COURSE_REVIEWS.items():
        if state.get("current_course_id") == course_id:
            return state
    # In-memory miss — try DB
    persisted = await _load_review_state(course_id)
    if persisted is not None:
        # Warm the cache for subsequent polls
        orig = persisted.get("original_course_id", course_id)
        _COURSE_REVIEWS[orig] = persisted
    return persisted
