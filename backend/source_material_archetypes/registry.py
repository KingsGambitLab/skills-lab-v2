"""Archetype registry — one entry per reusable course shape.

An Archetype encapsulates:
  - a short human ID + label (shown in the picker)
  - a slot contract (list of named fields the creator fills)
  - a Jinja-lite `.md.tmpl` file with {{slot}} substitution

Adding a new archetype:
  1. Drop a new `<slug>.md.tmpl` in this directory.
  2. Register an `Archetype(...)` below declaring its slots + default values.
  3. Reuse from the Creator UX via `/api/creator/archetypes`.

Design choice: we use {{slot}} substitution (NOT Jinja) on purpose. Jinja's
`{% for %}` / `{% if %}` lets creators hide conditional logic inside the
template — which makes templates opaque. Flat substitution keeps templates
readable + diffable + self-documenting. If conditional logic is ever needed,
split into two archetypes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_TMPL_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ArchetypeSlot:
    """One creator-fillable field inside an archetype template."""
    id: str                             # {{ID}} in the template; e.g. "STACK_NAME"
    label: str                          # Human-readable in the wizard
    description: str                    # Hover-help / placeholder
    example: str                        # Shown as placeholder text
    kind: str = "text"                  # text | textarea | choice
    choices: tuple[str, ...] = ()       # For kind="choice"
    default: str = ""                   # Default value, used when creator leaves blank
    required: bool = True               # Hard-require in the wizard


@dataclass(frozen=True)
class Archetype:
    """A reusable course-shape template."""
    slug: str
    label: str
    description: str                    # 1-2 sentences shown in the archetype picker
    course_type: str                    # "technical" | "case_study" | "compliance"
    course_mode: str                    # "linear" | "case_library"
    target_audience_hint: str           # "Mid-level backend engineers", "Non-coder PMs/ops", etc.
    exercise_types: tuple[str, ...]     # The primary exercise types this archetype uses
    capstone_shape: str                 # "gha_workflow_check" | "llm_rubric_paste" | "adaptive_roleplay" | "system_build_deploy"
    estimated_module_count: int
    estimated_step_count: int
    slots: tuple[ArchetypeSlot, ...] = ()
    template_file: str = ""             # Path under _TMPL_DIR; auto-inferred from slug if blank


_ARCHETYPES: dict[str, Archetype] = {}


def register_archetype(a: Archetype) -> None:
    _ARCHETYPES[a.slug] = a


def get_archetype(slug: str) -> Archetype | None:
    return _ARCHETYPES.get(slug)


def list_archetypes() -> list[Archetype]:
    return [_ARCHETYPES[k] for k in sorted(_ARCHETYPES.keys())]


def _load_template(archetype: Archetype) -> str:
    fname = archetype.template_file or f"{archetype.slug}.md.tmpl"
    path = _TMPL_DIR / fname
    if not path.exists():
        raise FileNotFoundError(f"Archetype template missing: {path}")
    return path.read_text()


# Placeholder regex: {{SLOT_ID}}. SLOT_ID is uppercase + underscore + digits.
_SLOT_RE = re.compile(r"\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}")


def materialize_archetype(
    slug: str,
    slot_values: dict[str, str],
    *,
    strict: bool = False,
) -> dict:
    """Expand an archetype's template with the given slot_values.

    Returns:
        {
            "ok": bool,
            "source_material": str,       # expanded template
            "missing_slots": list[str],   # required slots with no value
            "unknown_slots": list[str],   # keys in slot_values not in the archetype
            "unexpanded": list[str],      # {{FOO}} still present after expansion
        }

    If `strict=True`, returns ok=False when any missing/unexpanded slots exist.
    Non-strict mode leaves unexpanded `{{SLOT}}` placeholders in-place so the
    creator can fill them manually in the review step.
    """
    arch = get_archetype(slug)
    if arch is None:
        return {
            "ok": False,
            "source_material": "",
            "missing_slots": [],
            "unknown_slots": [],
            "unexpanded": [],
            "error": f"Unknown archetype slug: {slug}",
        }

    tmpl = _load_template(arch)
    declared_ids = {s.id for s in arch.slots}
    provided_ids = set(slot_values.keys())
    unknown_slots = sorted(provided_ids - declared_ids)

    # Apply defaults for missing slots
    effective: dict[str, str] = {}
    missing: list[str] = []
    for slot in arch.slots:
        val = slot_values.get(slot.id, "")
        if (val is None) or (isinstance(val, str) and not val.strip()):
            if slot.default:
                effective[slot.id] = slot.default
            elif slot.required:
                missing.append(slot.id)
                # Leave a clearly-marked TODO marker in the materialized text
                effective[slot.id] = f"[[FILL IN: {slot.label}]]"
            else:
                effective[slot.id] = ""
        else:
            effective[slot.id] = str(val)

    # Expand
    def _sub(m: re.Match) -> str:
        key = m.group(1)
        return effective.get(key, m.group(0))  # keep unknown placeholders

    expanded = _SLOT_RE.sub(_sub, tmpl)

    # Detect any {{SLOT}} still present
    unexpanded = sorted(set(_SLOT_RE.findall(expanded)))

    ok = (not unexpanded) and (not missing)
    if strict and not ok:
        return {
            "ok": False,
            "source_material": expanded,
            "missing_slots": missing,
            "unknown_slots": unknown_slots,
            "unexpanded": unexpanded,
            "error": "Unfilled slots in strict mode" if missing or unexpanded else "",
        }

    return {
        "ok": ok,
        "source_material": expanded,
        "missing_slots": missing,
        "unknown_slots": unknown_slots,
        "unexpanded": unexpanded,
    }


# ──────────────────────────────────────────────────────────────────────
# Registrations
# ──────────────────────────────────────────────────────────────────────

register_archetype(Archetype(
    slug="byok_claude_code_course",
    label="BYO-key Claude Code course (your team's repo)",
    description=(
        "Teach engineers to use Claude Code on their REAL team's repo. M0 preflight → "
        "feel-the-pain WITHOUT CLAUDE.md → write CLAUDE.md → slash commands + subagents "
        "→ hooks → MCP → GHA-graded capstone on a real production feature. BYO-key means "
        "learners use their OWN Anthropic key on their OWN machine — we never touch keys."
    ),
    course_type="technical",
    course_mode="linear",
    target_audience_hint="Mid-level backend engineers (2-5 yrs) on a specific stack",
    exercise_types=("concept", "terminal_exercise", "categorization", "scenario_branch", "code_read", "ordering", "system_build"),
    capstone_shape="gha_workflow_check",
    estimated_module_count=7,
    estimated_step_count=27,
    slots=(
        ArchetypeSlot(
            id="COURSE_TITLE",
            label="Course title",
            description="Shown in the catalog. 8-15 words. Includes the stack + the value prop.",
            example="Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows",
        ),
        ArchetypeSlot(
            id="STACK_NAME",
            label="Stack label",
            description="Short name for language + framework combo.",
            example="Java + Spring Boot",
        ),
        ArchetypeSlot(
            id="LANGUAGE",
            label="Primary language",
            description="The language the learner writes in.",
            example="Java",
        ),
        ArchetypeSlot(
            id="LANGUAGE_VERSION",
            label="Language version pin",
            description="Exact version the starter repo targets.",
            example="Java 21",
        ),
        ArchetypeSlot(
            id="FRAMEWORK",
            label="Framework",
            description="Primary web/application framework.",
            example="Spring Boot",
        ),
        ArchetypeSlot(
            id="FRAMEWORK_VERSION",
            label="Framework version pin",
            description="Exact framework version.",
            example="Spring Boot 3.3.x",
        ),
        ArchetypeSlot(
            id="BUILD_TOOL",
            label="Build tool",
            description="Maven, Gradle, npm, pnpm, poetry, cargo, go, etc.",
            example="Maven 3.9+",
        ),
        ArchetypeSlot(
            id="BUILD_CMD",
            label="Full build + test command",
            description="The single command CI runs to verify everything.",
            example="./mvnw clean verify",
        ),
        ArchetypeSlot(
            id="TEST_FRAMEWORK",
            label="Test framework",
            description="Named version.",
            example="JUnit 5.11",
        ),
        ArchetypeSlot(
            id="MOCKING_LIB",
            label="Mocking library",
            description="Named version. For languages that don't need mocks, write N/A.",
            example="Mockito 5",
            required=False,
            default="N/A",
        ),
        ArchetypeSlot(
            id="INTEGRATION_TEST_LIB",
            label="Integration-test backbone",
            description="Testcontainers, docker-compose-test, supertest, pytest-httpserver, etc.",
            example="Testcontainers (Postgres)",
        ),
        ArchetypeSlot(
            id="STARTER_REPO_URL",
            label="Starter repo URL (will be created)",
            description="Full HTTPS URL. Must match a course_assets.py entry.",
            example="https://github.com/tusharbisht/jspring-course-repo",
        ),
        ArchetypeSlot(
            id="STARTER_REPO_BASENAME",
            label="Starter repo basename (dir name after git clone)",
            description="The directory name git clone produces. Usually the last URL segment.",
            example="jspring-course-repo",
        ),
        ArchetypeSlot(
            id="CAPSTONE_FEATURE",
            label="Capstone feature (the production thing the learner ships)",
            description="1-sentence production feature with acceptance criteria.",
            example="POST /orders with Bean Validation, Idempotency-Key header, and Testcontainers integration tests",
        ),
        ArchetypeSlot(
            id="CAPSTONE_CLASS_NAMES",
            label="Capstone class/file names (comma-separated)",
            description="The named files the learner creates or edits in M6.",
            example="OrdersController.java, OrdersControllerTest.java",
        ),
        ArchetypeSlot(
            id="M1_BUG_SCENARIO",
            label="M1 planted bug — concrete 1-liner",
            description="A SUBTLE bug in the starter so learners see Claude struggle without CLAUDE.md.",
            example="N+1 query in OrderService.getRecentOrders that needs @EntityGraph or JOIN FETCH",
        ),
        ArchetypeSlot(
            id="M1_BUG_CLASS_METHOD",
            label="M1 bug class.method",
            description="The exact class.method the bug lives in.",
            example="OrderService.getRecentOrders",
        ),
        ArchetypeSlot(
            id="LEARNER_BACKGROUND",
            label="Learner background (1-2 sentences)",
            description="Experience level + what the learner already knows.",
            example="Mid-level Java backend engineer — 2-5 yrs Spring Boot experience. Comfortable with Maven (or Gradle), JUnit 5, Mockito, Spring Data JPA, Spring Web.",
        ),
        ArchetypeSlot(
            id="CLAUDE_MD_DONT_TOUCH_LIST",
            label="CLAUDE.md Don't-Touch list (comma-separated)",
            description="Files/paths the learner's CLAUDE.md will forbid Claude from editing.",
            example="application-prod.properties, db migrations, compiled artifacts",
        ),
        ArchetypeSlot(
            id="CUSTOM_AGENT_NAME",
            label="Custom subagent name (lowercase-hyphen)",
            description="The single custom subagent the learner writes in M3.",
            example="mockito-test-writer",
        ),
        ArchetypeSlot(
            id="SLASH_COMMAND_NAME",
            label="Slash command name (no leading slash)",
            description="The single slash command the learner writes in M3.",
            example="controller-review",
        ),
        ArchetypeSlot(
            id="HOOK_PRODUCTION_FILE",
            label="File to block in PreToolUse hook",
            description="The file the learner's PreToolUse hook blocks edits to.",
            example="application-prod.properties",
        ),
        ArchetypeSlot(
            id="HOOK_AUTOFORMAT_CMD",
            label="Auto-format command (PostToolUse)",
            description="Command the learner's PostToolUse hook runs after every Edit.",
            example="./mvnw spotless:apply",
        ),
        ArchetypeSlot(
            id="MCP_SLUG",
            label="MCP to consume in M5 (from course_assets.py)",
            description="Name of the pre-built MCP the learner wires up.",
            example="team-tickets",
            default="team-tickets",
        ),
        ArchetypeSlot(
            id="MCP_REPO",
            label="MCP repo URL (pre-built)",
            description="Full URL. Usually tusharbisht/aie-team-tickets-mcp is reused.",
            example="https://github.com/tusharbisht/aie-team-tickets-mcp",
            default="https://github.com/tusharbisht/aie-team-tickets-mcp",
        ),
        ArchetypeSlot(
            id="DOMAIN_NAME",
            label="Business domain / company tone",
            description="The fictional domain examples reference (e-commerce, fintech, travel, etc.).",
            example="e-commerce (users, orders, payments, inventory)",
        ),
    ),
))


# v8.6.2 TODO: register 2-3 more archetype stubs so the library pattern is
# evident (linear_concept_exercise, workday_simulator, case_library). For now
# we ship byok_claude_code_course — the first reusable archetype derived from
# jspring + aie — and add more as new course shapes land.
