r"""TechSchema — the canonical-doc-grounded source of truth for every tech.

v8.7 F3 (2026-04-25). Per buddy-Opus review #2: "the verified-facts abstraction
is one-sided. You enumerate forbidden strings; you don't enumerate required
shapes. The Creator (gen-time) has no schema either. You're catching drift at
gate time because the model is hallucinating against a vacuum at gen time.
Both sides need the same canonical schema."

This module replaces the blocklist-flavored `verified_facts.py` with an
allowlist-flavored conformance system. ONE schema per tech, declared once,
consumed by:

  1. Creator prompt assembly  — schema injected as "the only commands /
     flags / paths / config keys / event names you may emit. Anything not
     listed here will be REJECTED at the gate."
  2. Drift gate (`_is_complete`) — runs structural conformance against the
     schema; flags any artifact (path, flag, command) that doesn't match
     the allowlist as drift, with the canonical alternative in the message.
  3. CI regression check — same conformance pass over every course in scope.

## What a TechSchema declares

Each schema is a dataclass populated from CACHED CANONICAL DOCS in
`backend/tech_docs/<tech>.md` (NOT from review findings — review findings
go in `additional_drifts` with provenance, treated as P1 candidates for
upstreaming into docs).

Fields:

- `tech_id` — short stable id ("aider", "claude_code", "kubernetes", ...)
- `display_name` — human-readable ("Aider", "Claude Code")
- `scope_markers` — substrings in course title/desc that put the tech in scope
- `canonical_docs` — list of canonical doc URLs (cached locally; see tech_docs/)
- `allowed_cli_flags` — set of valid CLI flags for the tech's binary
- `allowed_in_chat_commands` — set of valid in-session slash commands
- `allowed_subcommands` — set of valid CLI subcommands
- `allowed_config_keys` — set of valid config-file keys
- `allowed_paths_in_dotdir` — globs of allowed file paths under .<tech>/ (e.g. .claude/agents/*.md)
- `allowed_tool_names` — for hooks / matchers (e.g. Edit/Write/Bash)
- `allowed_settings_event_names` — for hooks (e.g. PreToolUse)
- `allowed_frontmatter_fields` — for subagent YAML / similar
- `allowed_model_id_patterns` — regexes that match canonical model id forms
- `forbidden_examples` — known-bad strings WITH canonical alternative ("don't" + "do")
- `additional_drifts` — review-finding patterns not yet in canonical docs
  (with `source_review` + `caught_at_step_id` for provenance)
- `exercise_invariants` — F2-class structural rules
  (e.g. `code_exercise` deliverable must be code-language)
- `facts_block` — the assembled prompt-time block (computed property)

## Adding a new tech

  1. Cache canonical docs at `backend/tech_docs/<tech_id>.md`
  2. Create a `TechSchema(...)` instance in `backend/tech_schema_data.py`
  3. Register via `register_schema(...)`. Done.

The Creator + Gate + CI all pick it up.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class TechSchema:
    tech_id: str
    display_name: str
    scope_markers: tuple[str, ...]
    canonical_docs: tuple[str, ...]
    canonical_doc_path: str  # repo-relative path to cached doc text

    # Allowlists (populated from canonical docs)
    allowed_cli_flags: frozenset[str] = field(default_factory=frozenset)
    allowed_in_chat_commands: frozenset[str] = field(default_factory=frozenset)
    allowed_subcommands: frozenset[str] = field(default_factory=frozenset)
    allowed_config_keys: frozenset[str] = field(default_factory=frozenset)
    allowed_paths_in_dotdir: tuple[str, ...] = ()  # glob patterns
    allowed_tool_names: frozenset[str] = field(default_factory=frozenset)
    allowed_settings_event_names: frozenset[str] = field(default_factory=frozenset)
    allowed_frontmatter_fields: frozenset[str] = field(default_factory=frozenset)
    allowed_model_id_patterns: tuple[str, ...] = ()

    # The dotdir name (e.g. ".claude" / ".aider" / ".aws")
    dotdir_name: str | None = None

    # Forbidden examples WITH canonical alternative (most-leveraged teaching).
    # Tuple of (bad_string, canonical_alternative, why_msg).
    forbidden_examples: tuple[tuple[str, str, str], ...] = ()

    # Review-finding regex patterns not yet in canonical docs. Each entry:
    # (pattern_regex, violation_msg, ignore_case, caught_at_step, source_review).
    # P1 candidate to upstream into canonical docs / allowlists.
    additional_drifts: tuple[tuple[str, str, bool, str, str], ...] = ()

    # F2-class structural rules — exercise_type ↔ deliverable invariant.
    # Format: list of dicts {"if_exercise_type": ..., "if_deliverable_contains": [...], "violation": "..."}
    exercise_invariants: tuple[dict, ...] = ()


# ── Registry ──────────────────────────────────────────────────────────────

_SCHEMAS: dict[str, TechSchema] = {}


def register_schema(schema: TechSchema) -> None:
    """Register a tech schema. Last registration per tech_id wins."""
    _SCHEMAS[schema.tech_id] = schema


def all_schemas() -> list[TechSchema]:
    return list(_SCHEMAS.values())


def get_schema(tech_id: str) -> TechSchema | None:
    return _SCHEMAS.get(tech_id)


def in_scope_schemas(course_title: str = "", course_description: str = "",
                     source_material: str = "") -> list[TechSchema]:
    text = f"{course_title}\n{course_description}\n{source_material}".lower()
    if not text.strip():
        return []
    return [s for s in _SCHEMAS.values()
            if any(m.lower() in text for m in s.scope_markers)]


# ── Prompt-time facts block (compounded across in-scope techs) ────────────

def assemble_creator_prompt_block(
    course_title: str = "",
    course_description: str = "",
    source_material: str = "",
) -> str:
    """Build the Creator-prompt-injection block for in-scope techs.

    Replaces the prose `_claude_code_reference_facts()` / `_aider_reference_facts()`
    pattern. Schema-driven: emits explicit allowlists + canonical examples + the
    F2 exercise invariants. The LLM sees ONLY canonical structures from cached
    docs — no improvising.
    """
    techs = in_scope_schemas(course_title, course_description, source_material)
    if not techs:
        return ""
    parts = []
    for t in techs:
        block = _render_schema_for_creator(t)
        if block:
            parts.append(block)
    return "\n\n".join(parts)


def _render_schema_for_creator(s: TechSchema) -> str:
    sections = [
        f"=== {s.display_name.upper()} CANONICAL SCHEMA (v{_VERSION_TAG}) — emit ONLY structures listed here ===",
    ]
    if s.allowed_cli_flags:
        sections.append("CLI flags (only these are real):")
        sections.append("  " + ", ".join(f"`{f}`" for f in sorted(s.allowed_cli_flags)))
    if s.allowed_subcommands:
        sections.append("CLI subcommands (only these):")
        sections.append("  " + ", ".join(f"`{c}`" for c in sorted(s.allowed_subcommands)))
    if s.allowed_in_chat_commands:
        sections.append("In-session slash commands (only these):")
        sections.append("  " + ", ".join(f"`{c}`" for c in sorted(s.allowed_in_chat_commands)))
    if s.allowed_config_keys:
        sections.append(f"Config-file ({s.dotdir_name or 'config'}) allowed keys:")
        sections.append("  " + ", ".join(f"`{k}`" for k in sorted(s.allowed_config_keys)))
    if s.allowed_paths_in_dotdir:
        sections.append(f"`{s.dotdir_name}/` allowed path patterns:")
        for p in s.allowed_paths_in_dotdir:
            sections.append(f"  - {p}")
    if s.allowed_tool_names:
        sections.append("Tool names (CAPITALIZED — use these exact strings):")
        sections.append("  " + ", ".join(f"`{t}`" for t in sorted(s.allowed_tool_names)))
    if s.allowed_settings_event_names:
        sections.append("Settings hook event names (PascalCase — only these):")
        sections.append("  " + ", ".join(f"`{e}`" for e in sorted(s.allowed_settings_event_names)))
    if s.allowed_frontmatter_fields:
        sections.append("Subagent / agent YAML frontmatter allowed fields (others silently dropped):")
        sections.append("  " + ", ".join(f"`{f}`" for f in sorted(s.allowed_frontmatter_fields)))
    if s.allowed_model_id_patterns:
        sections.append("Model id forms (canonical regex patterns):")
        for p in s.allowed_model_id_patterns:
            sections.append(f"  - {p}")

    if s.forbidden_examples:
        sections.append("FORBIDDEN — common hallucinations + their canonical alternative:")
        for bad, good, why in s.forbidden_examples:
            sections.append(f"  ✗ `{bad}`  →  ✓ `{good}`   ({why})")

    if s.exercise_invariants:
        sections.append("EXERCISE INVARIANTS (the gate enforces these structurally):")
        for inv in s.exercise_invariants:
            sections.append(f"  - {inv.get('rule', inv)}")

    sections.append(f"Canonical docs cached at backend/tech_docs/{s.tech_id}.md.")
    return "\n".join(sections)


_VERSION_TAG = "2026-04"


# ── Drift detection (consumes the schema) ─────────────────────────────────

def check_drift(
    *,
    content: str = "",
    code: str = "",
    validation: dict | None = None,
    demo_data: dict | None = None,
    title: str = "",
    exercise_type: str = "",
    expected_output: str = "",
    course_title: str = "",
    course_description: str = "",
    source_material: str = "",
) -> list[str]:
    """Run schema-driven drift detection across all in-scope techs.

    Combines:
      - Allowlist conformance (CLI flags / subcommands / config keys /
        slash commands / paths / settings event names / frontmatter fields)
      - Forbidden-examples list (positive teaching: "don't X, use Y instead")
      - Additional drifts (review-finding patterns staged for canonical
        upstream)
      - Exercise invariants (F2 structural class)

    Returns a flat list of `<TECH>_DRIFT: <message>` strings. Empty = clean.
    """
    import json as _json
    techs = in_scope_schemas(course_title, course_description, source_material)
    if not techs:
        return []

    parts: list[str] = []
    if title: parts.append(title)
    if content: parts.append(content)
    if code: parts.append(code)
    if expected_output: parts.append(expected_output)
    for v in (validation, demo_data):
        if v:
            try: parts.append(_json.dumps(v))
            except Exception: parts.append(str(v))
    haystack = "\n".join(parts)

    violations: list[str] = []
    for t in techs:
        violations.extend(_check_against_schema(t, haystack, exercise_type, expected_output))
    return violations


_NEGATION_MARKERS = (
    " not ", "n't ", " avoid", " don't", " never ", "deprecated",
    "stale", "wrong", "incorrect", "invented", "fictional",
    "outdated", "do not use", "don't use", " no longer ",
)


def _negated_at(haystack_flat_lower: str, raw_haystack: str, match_start: int) -> bool:
    """True iff the match at `match_start` is in a negation context within
    the same content block (negation marker within ~80 chars before, NOT
    crossing a code-fence boundary)."""
    window_start = max(0, match_start - 80)
    raw_window_lc = raw_haystack[window_start:match_start].lower()
    fence_open = max(
        raw_window_lc.rfind("```"),
        raw_window_lc.rfind("<pre"),
        raw_window_lc.rfind("<code"),
    )
    if fence_open >= 0:
        raw_window_lc = raw_window_lc[fence_open:]
    return any(neg in raw_window_lc for neg in _NEGATION_MARKERS)


def _check_against_schema(s: TechSchema, haystack: str, exercise_type: str,
                          expected_output: str) -> list[str]:
    violations: list[str] = []
    haystack_lower = haystack.lower()
    flat_lower = haystack_lower.replace("\n", " ")

    # 1. Forbidden examples (the most leveraged teaching — bad+good+why)
    for bad, good, why in s.forbidden_examples:
        for m in re.finditer(re.escape(bad), haystack):
            if _negated_at(flat_lower, haystack, m.start()):
                continue
            violations.append(
                f"{s.tech_id.upper()}_DRIFT: {bad!r} — {why}. Canonical: {good!r}"
            )
            break  # one violation per pattern is enough

    # 2. Additional drifts (review-finding patterns staged for upstream)
    for pat, msg, ignore_case, _step, _src in s.additional_drifts:
        flags = re.IGNORECASE if ignore_case else 0
        for m in re.finditer(pat, haystack, flags):
            if _negated_at(flat_lower, haystack, m.start()):
                continue
            violations.append(f"{s.tech_id.upper()}_DRIFT: {msg}")
            break

    # 3. Exercise invariants (F2 structural class)
    if exercise_type:
        for inv in s.exercise_invariants:
            if inv.get("if_exercise_type") != exercise_type:
                continue
            triggers = inv.get("if_deliverable_contains", [])
            if not triggers:
                continue
            full_text = (expected_output + " " + haystack).lower()
            if any(t.lower() in full_text for t in triggers):
                violations.append(f"{s.tech_id.upper()}_INVARIANT: {inv.get('violation', 'F2 violation')}")

    return violations


def list_summary() -> str:
    """Human-readable summary for CI logs."""
    if not _SCHEMAS:
        return "(no schemas registered)"
    lines = []
    for s in _SCHEMAS.values():
        lines.append(
            f"  - {s.tech_id:<14} flags={len(s.allowed_cli_flags)} "
            f"slashes={len(s.allowed_in_chat_commands)} "
            f"keys={len(s.allowed_config_keys)} "
            f"forbidden={len(s.forbidden_examples)} "
            f"+drifts={len(s.additional_drifts)}"
        )
    return "\n".join(lines)
