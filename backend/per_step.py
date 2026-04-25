"""
per_step.py — Per-step course generation + regeneration.

Until 2026-04-20 the Creator flow was a monolith: `/api/creator/generate`
produced ALL modules + ALL steps in one shot, and any edit forced a
whole-course regen (~$0.40, ~60-90s).

This module adds surgical primitives:

  POST /api/courses/{id}/steps/{sid}/regenerate   — regen one step
  POST /api/courses/{id}/modules/{mid}/regenerate — regen all steps in a
                                                    module sequentially
  PATCH /api/courses/{id}/steps/{sid}             — direct edit, no LLM

Cross-module context: each regenerated step receives a PRIOR_COURSE_CONTEXT
block in its prompt — a compact summary of every prior step's personas,
systems, code identifiers, frameworks. That way M3 Step 2 doesn't invent a
new CFO when M1 Step 1 already named one. When the user asked "share context
with generator if there are dependencies between modules" — this is it.

The primitives reuse `_llm_generate_step_content` + the same `_is_complete`
quality-floor + fallback pipeline from main.py so per-step regen is
indistinguishable in quality from initial generation.

Budget: ~$0.02 per step vs ~$0.40 per whole-course regen → 95% cheaper per
iteration. Auto-review (backend/auto_review.py) will be rewired to use this.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Anchor extraction — pulls the minimum a downstream step needs to know
# about a prior step without reading its full content.
# ---------------------------------------------------------------------------

# Proper-noun two-word pattern (e.g. "Marcus Chen", "Priya Rao", "Sarah Mitchell")
_PROPER_NOUN_RE = re.compile(r"\b([A-Z][a-z]{2,})\s+([A-Z][a-z]{2,})\b")

# Single-word branded-system name in Title-case (e.g. "VectorFlow", "SecureFlow")
_BRAND_RE = re.compile(r"\b([A-Z][a-z]+[A-Z][a-zA-Z]+)\b")

# Python/JS class + function identifiers from code bodies
_CODE_CLASS_RE = re.compile(r"^\s*class\s+(\w+)\s*[\(:]", re.MULTILINE)
_CODE_FUNC_RE = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
_CODE_JS_FUNC_RE = re.compile(r"(?:^|\s)function\s+(\w+)\s*\(|\b(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>", re.MULTILINE)

# Framework / tool keywords we care to carry forward (lowercased)
_FRAMEWORK_KEYWORDS = {
    "anthropic", "claude", "openai", "langchain", "langgraph", "llamaindex",
    "weaviate", "pinecone", "chromadb", "qdrant", "milvus", "pgvector",
    "fastapi", "flask", "django", "starlette", "uvicorn", "gunicorn",
    "react", "next.js", "vue", "svelte",
    "docker", "kubernetes", "terraform", "helm",
    "postgres", "postgresql", "mysql", "mongodb", "redis", "kafka", "sqs",
    "aws", "gcp", "azure", "vercel", "railway", "fly.io", "cloudflare",
    "pytest", "jest", "vitest", "playwright",
    "pydantic", "sqlalchemy", "alembic",
    "ralph", "react pattern", "observe-think-act", "tool_use", "stop_reason",
    "agent harness", "tool registry", "memory pattern",
}


def extract_step_anchors(step_row: Any) -> dict[str, list[str]]:
    """Pull the minimum-viable context a downstream step needs from a prior one.

    Returns {"personas": [...], "brands": [...], "code_identifiers": [...], "frameworks": [...]}.
    All lists are deduped + capped at 8 items each (keeps prompt budget tight).
    """
    content = (getattr(step_row, "content", None) or "") + " "
    code = (getattr(step_row, "code", None) or "") + " "
    demo_data = getattr(step_row, "demo_data", None) or {}
    # Also mine demo_data.scenario, demo_data.phases[].title, etc. — those carry persona context too
    dd_blob = _stringify_demo_data(demo_data)

    text_blob = content + " " + dd_blob
    code_blob = code

    personas: list[str] = []
    for m in _PROPER_NOUN_RE.finditer(text_blob):
        name = f"{m.group(1)} {m.group(2)}"
        if name not in personas and not _looks_like_framework_name(name):
            personas.append(name)

    brands: list[str] = []
    for m in _BRAND_RE.finditer(text_blob):
        b = m.group(1)
        if b not in brands and b.lower() not in _FRAMEWORK_KEYWORDS:
            brands.append(b)

    code_ids: list[str] = []
    for rx in (_CODE_CLASS_RE, _CODE_FUNC_RE):
        for m in rx.finditer(code_blob):
            g = m.group(1)
            if g and g not in code_ids and not g.startswith("_"):
                code_ids.append(g)
    for m in _CODE_JS_FUNC_RE.finditer(code_blob):
        g = m.group(1) or m.group(2)
        if g and g not in code_ids and not g.startswith("_"):
            code_ids.append(g)

    text_lower = text_blob.lower() + " " + code_blob.lower()
    frameworks = [kw for kw in _FRAMEWORK_KEYWORDS if kw in text_lower]

    return {
        "personas": personas[:8],
        "brands": brands[:8],
        "code_identifiers": code_ids[:10],
        "frameworks": frameworks[:8],
    }


def _stringify_demo_data(dd: dict | None) -> str:
    if not isinstance(dd, dict):
        return ""
    parts = []
    for k in ("scenario", "brief", "summary", "mission"):
        v = dd.get(k)
        if isinstance(v, str):
            parts.append(v)
    for phase in (dd.get("phases") or []):
        if isinstance(phase, dict):
            t = phase.get("title") or phase.get("label")
            if t:
                parts.append(t)
    for item in (dd.get("items") or []):
        if isinstance(item, dict):
            t = item.get("text") or item.get("label")
            if t:
                parts.append(str(t))
        elif isinstance(item, str):
            parts.append(item)
    return " ".join(parts)


def _looks_like_framework_name(s: str) -> bool:
    """Avoid treating 'Agent Harness' or 'Ralph Pattern' as personas."""
    return s.lower() in _FRAMEWORK_KEYWORDS


# ---------------------------------------------------------------------------
# Prior-course-context summary
# ---------------------------------------------------------------------------

async def build_prior_course_context(
    course_id: str,
    up_to_step_id: int | None,
    db: AsyncSession,
    Course: Any,
    Module: Any,
    Step: Any,
) -> str:
    """Return a compact prompt-ready summary of every step that comes BEFORE
    `up_to_step_id` in the course. Ordered by (module.position, step.position).

    When the caller regenerates step S, this summary is injected into the
    step prompt as a PRIOR_COURSE_CONTEXT block — so the LLM sees the
    personas / brands / code identifiers that were introduced earlier and
    can reuse them rather than invent fresh ones. This is the user's
    "share context with generator if there are dependencies" requirement.

    If up_to_step_id is None: summarize the entire course (useful when a new
    step is APPENDED at the end).
    """
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course = course_res.scalars().first()
    if not course:
        return ""

    mods_res = await db.execute(
        select(Module).where(Module.course_id == course_id).order_by(Module.position)
    )
    modules = list(mods_res.scalars().all())
    if not modules:
        return ""

    # Find the target step's (module_pos, step_pos) boundary
    boundary: tuple[int, int] | None = None
    target_mod_id: int | None = None
    if up_to_step_id is not None:
        target_res = await db.execute(select(Step).where(Step.id == up_to_step_id))
        target = target_res.scalars().first()
        if target:
            target_mod = next((m for m in modules if m.id == target.module_id), None)
            if target_mod:
                boundary = (target_mod.position, target.position)
                target_mod_id = target_mod.id

    # Accumulate anchors module-by-module
    rollup: dict[str, list[str]] = {
        "personas": [], "brands": [], "code_identifiers": [], "frameworks": [],
    }
    per_module_summaries: list[str] = []

    for mod in modules:
        steps_res = await db.execute(
            select(Step).where(Step.module_id == mod.id).order_by(Step.position)
        )
        steps = list(steps_res.scalars().all())
        if not steps:
            continue

        module_anchors: dict[str, list[str]] = {
            "personas": [], "brands": [], "code_identifiers": [], "frameworks": [],
        }
        included_step_titles: list[str] = []

        for s in steps:
            # Respect the boundary: skip steps at/after the target
            if boundary is not None:
                if (mod.position, s.position) >= boundary:
                    continue
            anchors = extract_step_anchors(s)
            included_step_titles.append(f"S{s.position} {s.title} [{s.exercise_type or 'lesson'}]")
            for k, lst in anchors.items():
                for v in lst:
                    if v not in module_anchors[k]:
                        module_anchors[k].append(v)
                    if v not in rollup[k]:
                        rollup[k].append(v)

        if not included_step_titles:
            continue

        mod_lines = [f"M{mod.position} \"{mod.title}\""]
        mod_lines.append("  steps: " + "; ".join(included_step_titles))
        if module_anchors["personas"]:
            mod_lines.append(f"  personas: {', '.join(module_anchors['personas'])}")
        if module_anchors["brands"]:
            mod_lines.append(f"  brands/systems: {', '.join(module_anchors['brands'])}")
        if module_anchors["code_identifiers"]:
            mod_lines.append(f"  code identifiers introduced: {', '.join(module_anchors['code_identifiers'])}")
        if module_anchors["frameworks"]:
            mod_lines.append(f"  frameworks/tools used: {', '.join(module_anchors['frameworks'])}")
        per_module_summaries.append("\n".join(mod_lines))

        # Stop after the target module (we've included everything prior to the step)
        if target_mod_id and mod.id == target_mod_id:
            break

    if not per_module_summaries:
        return ""

    header = (
        "=== PRIOR COURSE CONTEXT (preserve for continuity) ===\n"
        "This step is being generated AFTER the modules/steps summarized below. "
        "Reuse the personas, brand names, code identifiers, and frameworks listed here — "
        "DO NOT invent new ones for the same roles. If this step needs to reference a "
        "character, system, or class, pull from the names below. Only introduce a NEW "
        "name when the content genuinely needs a new entity."
    )
    body = "\n\n".join(per_module_summaries)
    totals_line = (
        "\n\nGLOBAL ANCHORS (across all prior steps):\n"
        f"  personas: {', '.join(rollup['personas'][:10]) or '(none yet)'}\n"
        f"  brands/systems: {', '.join(rollup['brands'][:10]) or '(none yet)'}\n"
        f"  code identifiers: {', '.join(rollup['code_identifiers'][:12]) or '(none yet)'}\n"
        f"  frameworks/tools: {', '.join(rollup['frameworks'][:8]) or '(none yet)'}"
    )
    return f"{header}\n\n{body}{totals_line}\n=== END PRIOR COURSE CONTEXT ===\n"


# ---------------------------------------------------------------------------
# In-memory prior-context builder (for initial generation — before persistence)
# ---------------------------------------------------------------------------

def build_prior_context_from_memory(
    already_generated: list[dict],
) -> str:
    """Mirror of `build_prior_course_context` for the initial-generation path.

    `already_generated` is a list of {module_title, module_position, step_title,
    step_position, exercise_type, content, code, demo_data, validation} dicts —
    steps that have been LLM-produced earlier in the same creator_generate call
    but not yet persisted. Returns the same PRIOR_COURSE_CONTEXT block format
    as the DB-backed version so the prompt shape is identical regardless of
    whether we're in initial-gen or per-step-regen territory.
    """
    if not already_generated:
        return ""

    # Group by module, preserving order
    from collections import OrderedDict
    by_module: "OrderedDict[tuple[int, str], list[dict]]" = OrderedDict()
    for s in already_generated:
        key = (s.get("module_position", 0), s.get("module_title", ""))
        by_module.setdefault(key, []).append(s)

    rollup = {"personas": [], "brands": [], "code_identifiers": [], "frameworks": []}
    module_blocks: list[str] = []

    for (mpos, mtitle), steps in by_module.items():
        mod_anchors = {"personas": [], "brands": [], "code_identifiers": [], "frameworks": []}
        step_titles: list[str] = []
        for s in steps:
            step_titles.append(
                f"S{s.get('step_position','?')} {s.get('step_title','')} [{s.get('exercise_type') or 'lesson'}]"
            )
            # Reuse the same per-step anchor extraction logic by wrapping in a shim
            _shim = type("StepShim", (), {
                "content": s.get("content") or "",
                "code": s.get("code") or "",
                "demo_data": s.get("demo_data") or {},
            })()
            anchors = extract_step_anchors(_shim)
            for k, lst in anchors.items():
                for v in lst:
                    if v not in mod_anchors[k]:
                        mod_anchors[k].append(v)
                    if v not in rollup[k]:
                        rollup[k].append(v)
        if not step_titles:
            continue
        lines = [f"M{mpos} \"{mtitle}\""]
        lines.append("  steps: " + "; ".join(step_titles))
        if mod_anchors["personas"]:
            lines.append(f"  personas: {', '.join(mod_anchors['personas'])}")
        if mod_anchors["brands"]:
            lines.append(f"  brands/systems: {', '.join(mod_anchors['brands'])}")
        if mod_anchors["code_identifiers"]:
            lines.append(f"  code identifiers introduced: {', '.join(mod_anchors['code_identifiers'])}")
        if mod_anchors["frameworks"]:
            lines.append(f"  frameworks/tools used: {', '.join(mod_anchors['frameworks'])}")
        module_blocks.append("\n".join(lines))

    if not module_blocks:
        return ""

    header = (
        "=== PRIOR COURSE CONTEXT (preserve for continuity) ===\n"
        "This step is being generated AFTER the modules/steps summarized below. "
        "Reuse the personas, brand names, code identifiers, and frameworks listed here — "
        "DO NOT invent new ones for the same roles. If this step needs to reference a "
        "character, system, or class, pull from the names below. Only introduce a NEW "
        "name when the content genuinely needs a new entity."
    )
    body = "\n\n".join(module_blocks)
    totals = (
        "\n\nGLOBAL ANCHORS (across all prior steps):\n"
        f"  personas: {', '.join(rollup['personas'][:10]) or '(none yet)'}\n"
        f"  brands/systems: {', '.join(rollup['brands'][:10]) or '(none yet)'}\n"
        f"  code identifiers: {', '.join(rollup['code_identifiers'][:12]) or '(none yet)'}\n"
        f"  frameworks/tools: {', '.join(rollup['frameworks'][:8]) or '(none yet)'}"
    )
    return f"{header}\n\n{body}{totals}\n=== END PRIOR COURSE CONTEXT ===\n"


# ---------------------------------------------------------------------------
# Per-step regeneration primitive
# ---------------------------------------------------------------------------

def _minimal_completeness_check(content_obj: dict | None, exercise_type: str) -> tuple[bool, str]:
    """Cheap completeness check so a bad LLM output doesn't overwrite a working
    step. We're strict about the MINIMUM each type needs — not a full content
    floor (that's main.py's _is_complete job for initial generation).

    Returns (ok, reason). If ok=False, caller should KEEP the original step
    rather than overwrite with garbage.
    """
    if not isinstance(content_obj, dict):
        return False, "llm_returned_non_dict"
    content = content_obj.get("content") or ""
    if not content or len(content) < 40:
        return False, "content_empty_or_too_short"

    ex = exercise_type or "concept"
    if ex in ("concept", "lesson", None):
        return True, "ok"
    if ex in ("code", "code_exercise"):
        code = content_obj.get("code") or ""
        if len(code) < 30:
            return False, "code_too_short"
        return True, "ok"
    if ex == "fill_in_blank":
        code = content_obj.get("code") or ""
        val = content_obj.get("validation") or {}
        blanks = val.get("blanks") or []
        if "____" not in code or not blanks:
            return False, "fill_in_blank_missing_blanks"
        return True, "ok"
    if ex == "parsons":
        dd = content_obj.get("demo_data") or {}
        lines = dd.get("lines") or []
        if len(lines) < 3:
            return False, "parsons_too_few_lines"
        return True, "ok"
    if ex == "ordering":
        dd = content_obj.get("demo_data") or {}
        items = dd.get("items") or []
        if len(items) < 3:
            return False, "ordering_too_few_items"
        return True, "ok"
    if ex == "categorization":
        dd = content_obj.get("demo_data") or {}
        cats = dd.get("categories") or []
        items = dd.get("items") or []
        mapping = (content_obj.get("validation") or {}).get("correct_mapping") or {}
        if len(cats) < 2 or len(items) < 4:
            return False, "categorization_too_small"
        # Guard the exact bug user screenshotted on 2026-04-20: items lacking
        # `correct_category` AND validation missing `correct_mapping`
        if not mapping and not all(isinstance(it, dict) and it.get("correct_category") for it in items):
            return False, "categorization_missing_answer_key"
        return True, "ok"
    if ex == "scenario_branch":
        dd = content_obj.get("demo_data") or {}
        steps = dd.get("steps") or []
        if not steps:
            return False, "scenario_branch_no_steps"
        return True, "ok"
    if ex == "sjt":
        dd = content_obj.get("demo_data") or {}
        opts = dd.get("options") or []
        if len(opts) < 3:
            return False, "sjt_too_few_options"
        return True, "ok"
    if ex == "code_review":
        dd = content_obj.get("demo_data") or {}
        code = dd.get("code") or ""
        bugs = dd.get("bugs") or []
        if len(code) < 100 or len(bugs) < 2:
            return False, "code_review_insufficient"
        return True, "ok"
    if ex == "mcq":
        dd = content_obj.get("demo_data") or {}
        opts = dd.get("options") or []
        if len(opts) < 3:
            return False, "mcq_too_few_options"
        return True, "ok"
    if ex == "system_build":
        # Capstone — the one type with a higher floor because a broken capstone
        # is the most expensive kind of regression
        dd = content_obj.get("demo_data") or {}
        phases = dd.get("phases") or []
        checklist = dd.get("checklist") or []
        if len(content) < 300 or len(phases) < 3 or len(checklist) < 4:
            return False, "system_build_capstone_insufficient"
        return True, "ok"
    # Unknown types: pass if there's content
    return True, "ok_unknown_type"


async def regenerate_single_step(
    *,
    course_id: str,
    step_id: int,
    feedback: str | None,
    db: AsyncSession,
    # Injected from main.py to avoid circular imports
    Course: Any,
    Module: Any,
    Step: Any,
    llm_generate_step_content: Any,
    darkify_html_content: Any,
    llm_enabled: Any,
    normalize_code_review_bugs: Any = None,  # D.1 fix 2026-04-21
    critic_code_review: Any = None,  # B+C critic 2026-04-21
    critic_code_exercise: Any = None,  # B+C critic 2026-04-21
    max_retries: int = 6,
) -> dict[str, Any]:
    """Regenerate one step in place, with full prior-course context.

    Returns: {ok: bool, step: {...updated fields...}, reason?: str, prior_context_chars: int}

    Pipeline:
      1. Load the step + its course.
      2. Build the prior-steps context summary (everything before this step).
      3. Build a course_context dict including prior_course_context so the LLM
         sees personas / brands / code identifiers from earlier steps.
      4. Call llm_generate_step_content with feedback appended to step_description.
      5. Minimal completeness check. Retry ONCE on failure with a sharpened
         prompt. If still bad, KEEP the original step — never overwrite with
         degraded content (unlike initial-gen fallback, per-step regen has a
         user in the loop who can try again with different feedback).
      6. Dark-theme sanitize content HTML.
      7. Persist in place — leave title + exercise_type + position untouched.
    """
    import asyncio

    step_res = await db.execute(select(Step).where(Step.id == step_id))
    step_row = step_res.scalars().first()
    if not step_row:
        return {"ok": False, "reason": "step_not_found"}

    mod_res = await db.execute(select(Module).where(Module.id == step_row.module_id))
    mod_row = mod_res.scalars().first()
    if not mod_row or mod_row.course_id != course_id:
        return {"ok": False, "reason": "step_not_in_course"}

    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course_row = course_res.scalars().first()
    if not course_row:
        return {"ok": False, "reason": "course_not_found"}

    if not llm_enabled():
        return {"ok": False, "reason": "llm_disabled_budget_exhausted"}

    prior_ctx = await build_prior_course_context(
        course_id=course_id,
        up_to_step_id=step_id,
        db=db,
        Course=Course,
        Module=Module,
        Step=Step,
    )

    course_type = getattr(course_row, "course_type", None) or "technical"
    course_context: dict[str, Any] = {
        "title": course_row.title,
        "course_type": course_type,
        "source_material": getattr(course_row, "source_material", "") or "",
        "canonical_entities": [],
        "capstone_scenario": None,
        "is_capstone_module": False,
        "prior_course_context": prior_ctx,  # NEW: shared context for dependencies
    }
    # v8.6 (2026-04-24) — language detection + pin, mirror of the fix in
    # _creator_generate_impl. Previously this path shipped NO language key,
    # so per-step regens on TS courses re-generated in Python (same bug that
    # nuked TS v12/v13). Import the detector lazily to avoid circular import
    # (per_step.py is imported by main.py before _detect_course_language
    # is defined at module top level).
    try:
        from backend.main import _detect_course_language
        _desc_text = (getattr(course_row, "description", "") or "")
        _lang = _detect_course_language(course_row.title or "", _desc_text)
        if _lang:
            course_context["language"] = _lang
            logger.info(
                "per-step regen: COURSE LANGUAGE detected + pinned: %r for course=%r",
                _lang, (course_row.title or "")[:80],
            )
        else:
            logger.warning(
                "per-step regen: COURSE LANGUAGE not detected from title+desc — "
                "GATE A will skip. Title=%r", (course_row.title or "")[:100],
            )
    except Exception as _lang_err:
        logger.warning("per-step regen: language-detection failed (soft-pass): %s", _lang_err)

    all_mods_res = await db.execute(
        select(Module).where(Module.course_id == course_id).order_by(Module.position.desc())
    )
    all_mods = list(all_mods_res.scalars().all())
    if all_mods and all_mods[0].id == mod_row.id:
        course_context["is_capstone_module"] = True

    # Reconstruct a strong step_description from the step's CURRENT content +
    # code. The outline's original description isn't persisted, but the content
    # field captures what the step is about well enough for regen seeding.
    # Without this, the LLM gets only `step_title` + `exercise_type` and tends
    # to produce sparse output that fails the completeness check.
    _strip_html = lambda s: re.sub(r"<[^>]+>", " ", s or "").strip()
    current_content_plain = _strip_html(step_row.content or "")[:900]
    current_code_head = (step_row.code or "")[:600]

    base_desc_parts: list[str] = []
    base_desc_parts.append(
        f"This step is '{step_row.title}' ({step_row.exercise_type or 'concept'}) in "
        f"module '{mod_row.title}' of the course '{course_row.title}'."
    )
    if current_content_plain:
        base_desc_parts.append(
            f"CURRENT CONTENT (regenerate a BETTER version — same subject, same deliverable shape, "
            f"higher quality): {current_content_plain}"
        )
    if current_code_head and step_row.exercise_type in ("code", "code_exercise", "fill_in_blank", "code_review"):
        base_desc_parts.append(f"CURRENT CODE HEAD: {current_code_head}")
    base_desc = "\n\n".join(base_desc_parts)

    effective_desc = base_desc
    if feedback:
        effective_desc = f"{base_desc}\n\nREGENERATION FEEDBACK (apply to the new version):\n{feedback.strip()}"

    ex_type = step_row.exercise_type or "concept"
    llm_content: dict[str, Any] | None = None
    last_reason = ""
    # v8.6 (2026-04-24) — classify the last failure so callers can tell
    # WHY a regen exhausted retries. Pre-fix: all failures returned
    # "completeness_failed_after_retries" regardless of true cause.
    # Classes: "llm_error" (exception during LLM call), "llm_returned_non_dict"
    # (bad JSON — should be near-zero post tool-use), "completeness_failed"
    # (shape/filler/placeholder check rejected), "invariant_failed" (Docker
    # solution/starter invariant rejected — the most actionable class, has
    # full retry-feedback dump reference).
    last_failure_class = ""

    for attempt in range(max_retries + 1):
        attempt_desc = effective_desc
        if attempt > 0:
            attempt_desc = effective_desc + (
                f"\n\nRETRY NOTE: previous attempt failed completeness check ({last_reason}). "
                f"Return a complete, non-placeholder response satisfying the schema for {ex_type}."
            )
        # v8.6 (2026-04-24) MIRROR COURSE-GEN RETRY-ORDER — per user directive
        # "see if 3-4-5 tries of Opus solves". Full-course retry loop in
        # _creator_generate_impl uses: attempts 2-3 Sonnet, attempts 4-7 Opus,
        # attempt 8 Opus on simplified. Per-step regen used to ALWAYS use
        # Sonnet (via default model in _llm_generate_step_content). Now:
        # first 3 attempts Sonnet, attempts 3-6 Opus at full difficulty.
        # (Per-step max_retries defaults to 6 → 7 total attempts.)
        _model_override = None
        if ex_type == "code_exercise" and attempt >= 3:
            try:
                from backend.main import _OPUS_MODEL
                _model_override = _OPUS_MODEL
                logger.info(
                    "per_step regen attempt %d: escalating to Opus (mirror of course-gen Opus×4 phase)",
                    attempt,
                )
            except ImportError:
                pass
        try:
            candidate = await asyncio.to_thread(
                llm_generate_step_content,
                course_context,
                mod_row.title,
                step_row.title,
                ex_type,
                attempt_desc,
                retry_hint="",
                model_override=_model_override,
            )
        except Exception as e:
            logger.exception("per_step regen LLM call failed on attempt %d: %s", attempt, e)
            last_reason = f"llm_error:{e}"
            last_failure_class = "llm_error"
            continue

        if not isinstance(candidate, dict):
            last_reason = "llm_returned_non_dict (tool-use should prevent this class)"
            last_failure_class = "llm_returned_non_dict"
            continue

        # D.1 (2026-04-21): for code_review, normalize bugs[].line via line_content
        # before the completeness check so regens benefit from the same anti-drift
        # fix as initial generation (main.py:5969).
        if ex_type == "code_review" and normalize_code_review_bugs and isinstance(candidate.get("demo_data"), dict):
            candidate["demo_data"] = normalize_code_review_bugs(candidate["demo_data"])
            # B+C critic (2026-04-21): LLM self-verify + find-missing pass on bugs[].
            if critic_code_review:
                try:
                    candidate["demo_data"] = critic_code_review(candidate["demo_data"])
                except Exception as e:
                    logger.warning("per_step code_review critic failed: %s", e)
            resolved_lines = [
                b.get("line") for b in candidate["demo_data"].get("bugs", [])
                if isinstance(b, dict) and isinstance(b.get("line"), int)
            ]
            if resolved_lines:
                if not isinstance(candidate.get("validation"), dict):
                    candidate["validation"] = {}
                candidate["validation"]["bug_lines"] = sorted(set(resolved_lines))

        # B+C critic (2026-04-21): code_exercise solvability + anti-gaming must_contain.
        if ex_type == "code_exercise" and critic_code_exercise:
            try:
                candidate = critic_code_exercise(candidate)
            except Exception as e:
                logger.warning("per_step code_exercise critic failed: %s", e)

        ok, reason = _minimal_completeness_check(candidate, ex_type)
        if not ok:
            last_reason = reason
            last_failure_class = "completeness_failed"
            logger.info("per_step regen attempt %d failed completeness: %s", attempt, reason)
            continue

        # v8.6 (2026-04-24) UNIFY WITH COURSE GEN — user directive post-v14:
        # "don't duplicate code for step regen". Shared invariant-check
        # helper `validate_code_exercise_invariant` in main.py encapsulates:
        # Pydantic pre-gate → hidden_tests presence → Docker invariant → raw
        # head+tail retry feedback assembly. Both this path AND the full
        # course-gen path call it — one place to maintain.
        if ex_type == "code_exercise":
            try:
                from backend.main import validate_code_exercise_invariant
                inv_ok, inv_reason = await validate_code_exercise_invariant(
                    candidate, course_context, step_row.title,
                )
                if not inv_ok:
                    last_reason = inv_reason
                    last_failure_class = "invariant_failed"
                    logger.warning(
                        "per_step regen attempt %d invariant FAIL (%d chars)",
                        attempt, len(inv_reason),
                    )
                    continue
            except ImportError:
                # Helper not present — fall back to completeness-only
                logger.warning("validate_code_exercise_invariant not importable; skipping invariant gate")

        llm_content = candidate
        break

    if llm_content is None:
        # v8.6 (2026-04-24) — return structured failure info so callers know
        # WHY the regen exhausted (previously everything was labeled
        # "completeness_failed_after_retries" regardless of root cause).
        # Classification: llm_error | llm_returned_non_dict | completeness_failed
        # | invariant_failed. Reason tail capped at 2000 chars (full version
        # is on disk under /tmp/retry_feedback/).
        _class = last_failure_class or "unknown"
        _reason_short = (last_reason or "no_reason_captured")
        if len(_reason_short) > 2000:
            _reason_short = _reason_short[:1000] + "\n[... truncated; full in /tmp/retry_feedback/ ...]\n" + _reason_short[-900:]
        return {
            "ok": False,
            "reason": f"{_class}_after_retries:{_reason_short}",
            "failure_class": _class,
            "last_reason_tail": _reason_short,
            "attempts_used": max_retries + 1,
        }

    content_html = llm_content.get("content")
    if content_html:
        content_html = darkify_html_content(content_html)

    step_row.content = content_html or step_row.content
    if "code" in llm_content:
        step_row.code = llm_content.get("code") or step_row.code
    if "expected_output" in llm_content:
        step_row.expected_output = llm_content.get("expected_output") or step_row.expected_output
    if "validation" in llm_content:
        step_row.validation = llm_content.get("validation") or step_row.validation
    if "demo_data" in llm_content:
        step_row.demo_data = llm_content.get("demo_data") or step_row.demo_data
    # Phase 2 (2026-04-25): if the regen LLM declared a fresh learner_surface
    # (because the regen touched interactivity / changed exercise_type),
    # respect it. Otherwise keep the stored value — it was already
    # canonicalized at first persist.
    if "learner_surface" in llm_content:
        try:
            from .learner_surface import normalize as _norm_surface
            _new_surface = _norm_surface(llm_content.get("learner_surface"))
            if _new_surface:
                step_row.learner_surface = _new_surface
        except Exception:
            pass  # surface module missing → keep prior value

    await db.commit()
    await db.refresh(step_row)

    return {
        "ok": True,
        "regenerated_with_feedback": bool(feedback),
        "prior_context_chars": len(prior_ctx),
        "step": {
            "id": step_row.id,
            "module_id": step_row.module_id,
            "position": step_row.position,
            "title": step_row.title,
            "exercise_type": step_row.exercise_type,
            "content": step_row.content,
            "code": step_row.code,
            "expected_output": step_row.expected_output,
            "validation": step_row.validation,
            "demo_data": step_row.demo_data,
        },
    }


# ---------------------------------------------------------------------------
# Per-module regeneration — sequential step-by-step so each regen sees the
# just-regenerated earlier steps as prior context
# ---------------------------------------------------------------------------

async def regenerate_module(
    *,
    course_id: str,
    module_id: int,
    feedback: str | None,
    db: AsyncSession,
    Course: Any,
    Module: Any,
    Step: Any,
    llm_generate_step_content: Any,
    darkify_html_content: Any,
    llm_enabled: Any,
) -> dict[str, Any]:
    """Regenerate every step in a module IN ORDER. Each regen commits before
    the next fires, so `build_prior_course_context` naturally picks up the
    freshly-regenerated upstream steps as anchors. That means M2 S3's regen
    will see the refreshed M2 S1 / S2, not the stale versions.

    Returns {ok, regenerated: [step_ids...], failed: [{step_id, reason}...]}.
    """
    mod_res = await db.execute(select(Module).where(Module.id == module_id))
    mod_row = mod_res.scalars().first()
    if not mod_row or mod_row.course_id != course_id:
        return {"ok": False, "reason": "module_not_in_course"}

    steps_res = await db.execute(
        select(Step).where(Step.module_id == module_id).order_by(Step.position)
    )
    steps = list(steps_res.scalars().all())
    if not steps:
        return {"ok": False, "reason": "module_has_no_steps"}

    regenerated: list[int] = []
    failed: list[dict] = []
    for s in steps:
        res = await regenerate_single_step(
            course_id=course_id,
            step_id=s.id,
            feedback=feedback,
            db=db,
            Course=Course,
            Module=Module,
            Step=Step,
            llm_generate_step_content=llm_generate_step_content,
            darkify_html_content=darkify_html_content,
            llm_enabled=llm_enabled,
        )
        if res.get("ok"):
            regenerated.append(s.id)
        else:
            failed.append({"step_id": s.id, "reason": res.get("reason")})

    return {"ok": True, "regenerated": regenerated, "failed": failed, "total": len(steps)}


# ---------------------------------------------------------------------------
# Direct-edit primitive (no LLM)
# ---------------------------------------------------------------------------

async def patch_step_fields(
    *,
    course_id: str,
    step_id: int,
    updates: dict[str, Any],
    db: AsyncSession,
    Course: Any,
    Module: Any,
    Step: Any,
    darkify_html_content: Any,
) -> dict[str, Any]:
    """Direct edit — no LLM call. Applies the provided `updates` dict to the
    step, dark-theme sanitizes `content` if provided, commits. Used for manual
    creator polish of a step without burning LLM budget."""
    step_res = await db.execute(select(Step).where(Step.id == step_id))
    step_row = step_res.scalars().first()
    if not step_row:
        return {"ok": False, "reason": "step_not_found"}

    mod_res = await db.execute(select(Module).where(Module.id == step_row.module_id))
    mod_row = mod_res.scalars().first()
    if not mod_row or mod_row.course_id != course_id:
        return {"ok": False, "reason": "step_not_in_course"}

    # Safelist of editable fields. v8.7 (2026-04-25): I briefly added `title`
    # to allow drift-cleanup PATCHes (e.g. removing a stale `kimi-k2-latest`
    # from a step title) without burning LLM regen budget. Buddy-Opus review
    # caught this as an invariant erosion: titles are part of the outline
    # shape; widening the general safelist quietly weakens the
    # outline-shape contract CLAUDE.md asserts. REVERTED back to the
    # content/code/expected_output/validation/demo_data set. Drift cleanup
    # for titles now goes through the explicit admin route below
    # (`patch_step_title_admin` — gated by an admin-flag header, scoped to
    # title-only, audit-logged). Future title PATCHes therefore can't be
    # hit accidentally by the author UI.
    allowed_fields = {"content", "code", "expected_output", "validation", "demo_data"}
    applied: list[str] = []
    for k, v in (updates or {}).items():
        if k not in allowed_fields:
            continue
        if k == "content" and isinstance(v, str):
            v = darkify_html_content(v)
        setattr(step_row, k, v)
        applied.append(k)

    if not applied:
        return {"ok": False, "reason": "no_valid_fields_in_updates"}

    await db.commit()
    await db.refresh(step_row)
    return {
        "ok": True,
        "applied_fields": applied,
        "step": {
            "id": step_row.id,
            "module_id": step_row.module_id,
            "position": step_row.position,
            "title": step_row.title,
            "exercise_type": step_row.exercise_type,
            "content": step_row.content,
            "code": step_row.code,
            "expected_output": step_row.expected_output,
            "validation": step_row.validation,
            "demo_data": step_row.demo_data,
        },
    }


async def patch_step_title_admin(
    *,
    course_id: str,
    step_id: int,
    new_title: str,
    db: AsyncSession,
    Course: Any,
    Module: Any,
    Step: Any,
    actor_email: str = "?",
) -> dict[str, Any]:
    """ADMIN-ONLY title patch — no LLM call. Used for narrow drift-cleanup
    (e.g. removing `kimi-k2-latest` from a step title without burning LLM
    regen budget on a 1-line fix).

    Buddy-Opus review (2026-04-25) flagged that adding `title` to the
    general PATCH safelist erodes the outline-shape invariant. This route
    keeps the carve-out narrow:
      - Admin-only (gated by header / role at the endpoint level)
      - Title-only (no other fields editable)
      - Logs the actor + before/after for audit
      - Length cap to prevent silent outline drift via essay-length titles

    The author UI's `PATCH .../steps/{id}` does NOT route here — that
    endpoint stays restricted to content/code/expected_output/validation/
    demo_data per the safelist. Title changes go through this admin path
    OR a module-level regen.
    """
    new_title = (new_title or "").strip()
    if not new_title:
        return {"ok": False, "reason": "empty_title"}
    if len(new_title) > 300:
        return {"ok": False, "reason": "title_too_long"}

    step_res = await db.execute(select(Step).where(Step.id == step_id))
    step_row = step_res.scalars().first()
    if not step_row:
        return {"ok": False, "reason": "step_not_found"}
    mod_res = await db.execute(select(Module).where(Module.id == step_row.module_id))
    mod_row = mod_res.scalars().first()
    if not mod_row or mod_row.course_id != course_id:
        return {"ok": False, "reason": "step_not_in_course"}

    old_title = step_row.title
    step_row.title = new_title
    await db.commit()
    await db.refresh(step_row)

    # Audit log — keeps a paper trail of admin title patches even though we
    # don't have a dedicated audit table yet. /tmp is fine for now; a real
    # audit table goes in the production-ready queue.
    try:
        import json as _json, time as _time
        from pathlib import Path as _Path
        log_dir = _Path("/tmp/skillslab_admin_audit")
        log_dir.mkdir(exist_ok=True)
        with open(log_dir / "title_patches.jsonl", "a") as fh:
            fh.write(_json.dumps({
                "ts": _time.time(),
                "actor": actor_email,
                "course_id": course_id, "step_id": step_id,
                "old_title": old_title, "new_title": new_title,
            }) + "\n")
    except Exception:
        pass

    return {
        "ok": True, "old_title": old_title, "new_title": new_title,
        "step": {"id": step_row.id, "title": new_title,
                 "module_id": step_row.module_id, "position": step_row.position},
    }
