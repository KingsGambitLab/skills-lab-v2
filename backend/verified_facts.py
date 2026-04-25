r"""Tech-registry for verified-facts injection + drift detection.

Per user directive 2026-04-25: "whatever you do, don't make it a one-time
fix, but it should compound over time + extensible for other tech."

This module is the SINGLE place every tech-specific verified-facts entry
lives. Adding a new tech (Kubernetes, Terraform, AWS CLI, Snowflake,
Postgres ops, …) is ONE `register_tech(...)` call — no edits to main.py,
no edits to the drift gate, no edits to the Creator prompt assembly.

## What a tech registers

Each tech declares:
  - `tech_id`         — short stable id (e.g. "claude_code", "aider", "k8s")
  - `scope_markers`   — list of substrings; if ANY appears in the course
                        title/description/source_material, the tech is
                        considered "in scope" for that course
  - `facts_block`     — string injected into the Creator prompt verbatim
                        (the verified facts the LLM must quote, not paraphrase)
  - `drift_patterns`  — list of (regex, violation_message, ignore_case) tuples
                        scanned over generated content; matches outside
                        negation context become invariant violations that
                        force a regen

## How the system uses it

  - `_llm_generate_step_content()` in main.py iterates registered techs;
    for each in-scope one, appends its `facts_block` to the prompt.
  - `_is_complete()`'s drift gate iterates registered techs; for each
    in-scope one, scans the produced content with its `drift_patterns`
    and returns False (force regen) if any violation is found.
  - `tools/regression_check.py` (CI) runs the same scan over every course
    in the catalog; non-zero exit on drift.

## How to add a new tech (the whole onboarding)

```python
register_tech(
    tech_id="kubernetes",
    scope_markers=("kubernetes", "k8s", "kubectl", "helm chart"),
    facts_block='''
KUBERNETES REFERENCE FACTS (vYYYY-MM — QUOTE VERBATIM):
- API version path: /apis/<group>/<version>/...
- `kubectl apply -f <file>` (NOT `kubectl deploy`)
- ...
''',
    drift_patterns=[
        (r"\bkubectl\s+deploy\b",
         "uses `kubectl deploy` — invented subcommand. Use `kubectl apply -f`."),
        # ...
    ],
)
```

That's it. The Creator prompt for any course mentioning Kubernetes will
now inject the facts; any drift in generated content will be caught at
gate time + during CI runs.

## Compounding

Every tech-specific drift caught in production becomes a new
`drift_patterns` entry — the registry GROWS over time. Every future
course covering that tech inherits the entire accumulated knowledge.
A junior engineer adding a course about Kafka doesn't have to re-derive
"kubectl deploy is wrong" — the gate already knows.

## Negation-aware matching (also handled here)

A drift pattern matched inside a negation context ("don't use X", "never
do X", "X is deprecated") is NOT a violation — it's pedagogically correct
to mention what NOT to use. The matcher checks ~80 chars before each
match for negation markers and skips those occurrences.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NEGATION_MARKERS: tuple[str, ...] = (
    " not ", "n't ", " avoid", " don't", " never ", "deprecated",
    "stale", "wrong", "incorrect", "invented", "fictional",
    "outdated", "old slug", "old form", "do not use", "don't use",
    " no longer ",
)


@dataclass
class TechFacts:
    """One tech's verified-facts contract."""
    tech_id: str
    scope_markers: tuple[str, ...]
    facts_block: str
    # Each pattern is (regex, violation_msg, ignore_case_for_match).
    # ignore_case=False is right for product names that should be
    # case-distinguished (e.g. lowercase `claude code` is the drift,
    # Title Case "Claude Code" is the product name and should NOT match).
    drift_patterns: list[tuple[str, str, bool]] = field(default_factory=list)


_REGISTRY: dict[str, TechFacts] = {}


def register_tech(
    *,
    tech_id: str,
    scope_markers: tuple[str, ...] | list[str],
    facts_block: str,
    drift_patterns: list[tuple[str, str, bool]] | None = None,
) -> None:
    """Register a tech's verified-facts entry. Safe to call multiple times
    per tech_id (last registration wins — supports hot-reload)."""
    _REGISTRY[tech_id] = TechFacts(
        tech_id=tech_id,
        scope_markers=tuple(scope_markers),
        facts_block=facts_block,
        drift_patterns=list(drift_patterns or []),
    )


def all_techs() -> list[TechFacts]:
    return list(_REGISTRY.values())


def in_scope_techs(course_title: str = "", course_description: str = "",
                   source_material: str = "") -> list[TechFacts]:
    """Return every registered tech whose scope_markers hit the course text."""
    text = f"{course_title}\n{course_description}\n{source_material}".lower()
    if not text.strip():
        return []
    out = []
    for tech in _REGISTRY.values():
        if any(marker.lower() in text for marker in tech.scope_markers):
            out.append(tech)
    return out


def assemble_facts_blocks(course_title: str = "", course_description: str = "",
                          source_material: str = "") -> str:
    """Concatenate every in-scope tech's facts_block. Returns "" if no tech
    matches. Caller appends this to the Creator prompt."""
    techs = in_scope_techs(course_title, course_description, source_material)
    if not techs:
        return ""
    parts = []
    for t in techs:
        parts.append(t.facts_block)
    return "\n\n".join(parts)


def _drift_match_excluding_negation(
    pattern: str, haystack: str, *, ignore_case: bool
) -> bool:
    """Return True iff `pattern` matches at least once in POSITIVE-teaching
    context (not preceded by a negation marker within ~80 chars OF THE SAME
    CONTENT BLOCK).

    Buddy-Opus 2026-04-25: prior version applied the negation skip
    BLINDLY across code-fence boundaries. So content like
        "AVOID kimi-k2-0905. Do this instead:\n```bash\ncurl --model kimi-k2-0905\n```"
    passed the gate because the negation marker (AVOID) was within 80
    chars of the bad slug INSIDE the code block — but the code block IS
    teaching the wrong thing. Fix: when computing the lookbehind window,
    truncate at the most recent code-fence boundary (``` or `<pre>` /
    `<code>` open) before the match. Inside a code block, prose negation
    doesn't reach.
    """
    flags = re.IGNORECASE if ignore_case else 0
    flat = haystack.lower().replace("\n", " ")
    for m in re.finditer(pattern, haystack, flags):
        # Find the most recent code-fence boundary before this match. If
        # one exists within the lookbehind window, the negation context
        # is sealed off — we're INSIDE a code block.
        match_start = m.start()
        window_start = max(0, match_start - 80)
        window = flat[window_start:match_start]
        # Code-fence start markers in the haystack (case-insensitive)
        fence_open_pos = -1
        for fence in ("```", "<pre", "<code"):
            idx = haystack[window_start:match_start].lower().rfind(fence)
            if idx > fence_open_pos:
                fence_open_pos = idx
        if fence_open_pos >= 0:
            # Negation must be AFTER the fence open to count
            window = window[fence_open_pos:]
        if any(neg in window for neg in NEGATION_MARKERS):
            continue
        return True
    return False


def check_drift(
    *,
    content: str = "",
    code: str = "",
    validation: dict | None = None,
    demo_data: dict | None = None,
    title: str = "",  # NEW v8.7 (2026-04-25) — step title, scanned for drift
    course_title: str = "",
    course_description: str = "",
    source_material: str = "",
) -> list[str]:
    """Scan a generated step's content for drift against EVERY in-scope
    tech's patterns. Returns a flat list of violation messages prefixed
    with the tech_id. Empty list = clean.

    Scans: title + content + code + validation (json-dumped) + demo_data.
    Adding title scan caught Kimi M6.S2 lingering `kimi-k2-latest` in
    title (body had been correctly regenerated to canonical slug, but
    title was untouched).
    """
    import json as _json
    techs = in_scope_techs(course_title, course_description, source_material)
    if not techs:
        return []

    parts: list[str] = []
    if isinstance(title, str) and title:
        parts.append(title)
    if isinstance(content, str):
        parts.append(content)
    if isinstance(code, str):
        parts.append(code)
    for v in (validation, demo_data):
        if v:
            try:
                parts.append(_json.dumps(v))
            except Exception:
                parts.append(str(v))
    haystack = "\n".join(parts)

    violations: list[str] = []
    for tech in techs:
        for pattern, msg, ignore_case in tech.drift_patterns:
            if _drift_match_excluding_negation(pattern, haystack, ignore_case=ignore_case):
                violations.append(f"{tech.tech_id.upper()}_DRIFT: {msg}")
    return violations


def list_drift_summary() -> str:
    """Human-readable summary of every registered tech + its drift coverage.
    Used by tools/regression_check.py to print what's being enforced."""
    if not _REGISTRY:
        return "(no techs registered)"
    lines = []
    for t in _REGISTRY.values():
        lines.append(f"  - {t.tech_id:<16} markers={list(t.scope_markers)[:3]}…  drifts={len(t.drift_patterns)}")
    return "\n".join(lines)
