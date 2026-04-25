"""Ontology registry for Skills Lab v2 Creator.

THE RULE: Every decision the Creator makes (slide shape, assignment type,
course mode, tech domain, runtime) is declared as a registry entry here —
not as prose in a prompt string. Creator prompts are ASSEMBLED from the
registry at call time. Adding a new type is one registry entry + (for new
runtimes) a single handler registration — never a scattershot prompt edit.

This is the spine the 2026-04-21 ontology directive asked for: slide types,
assignment types, course modes, tech domains, runtime primitives — with
extensibility as a first-class property.

---

## FIVE LAYERS

1. **SLIDE_REGISTRY**     — templated content cards (concept_card, diagram_flow,
                            table_compare, checklist, code_read, mini_demo, …)
2. **ASSIGNMENT_REGISTRY** — exercise types with grade primitives (code_exercise,
                            code_review, code_read, system_build, mcq, …)
3. **COURSE_MODE_REGISTRY** — module-shape contracts (linear, case_library,
                            simulator_workday, drill_only, certification_track)
4. **TECH_DOMAIN_REGISTRY** — canonical stacks + assignment recipes + fixture
                            pointers (backend_python, data_sql, devops_k8s, …)
5. **RUNTIME_REGISTRY**    — execution primitives the grader can dispatch to
                            (python_sandbox, docker, github_actions, vscode,
                            terminal, sql_sqlite, yaml_schema, webcontainer)

## ADDING A NEW TYPE (EXTENSIBILITY)

```python
# In your own module (e.g. backend/ontology_extensions/my_domain.py):
from backend.ontology import (
    register_slide, register_assignment, register_course_mode,
    register_tech_domain, register_runtime, SlideType, AssignmentType,
)

register_slide(SlideType(
    id="my_custom_card",
    description="...",
    html_template="<div class='...'>{{body}}</div>",
    fields={"body": "str"},
))

register_assignment(AssignmentType(
    id="my_new_exercise",
    grade_primitives=["compile", "hidden_tests"],
    ...
))
```

The Creator prompt assembler picks these up on the next `/api/creator/start`
call. No change required in `_llm_generate_step_content` or `_is_complete`.

## GRADE PRIMITIVES (the vocabulary the layered grader speaks)

Each `AssignmentType.grade_primitives` is a list drawn from:

- `compile`              — source parses (Python / JS / Go / SQL / YAML / Dockerfile)
- `hidden_tests`         — pytest/jest/go test run against learner code
- `property_test`        — Hypothesis/QuickCheck against declared properties
- `lint`                 — ruff / eslint / mypy / tsc at strict level
- `must_contain`         — legacy substring match (≤5% weight, opt-in)
- `bug_lines`            — code_review: set-match on flagged line numbers
- `state_assertion`      — assert against live cluster / DB / service state
- `endpoint_probe`       — HTTP GET learner's submitted URL, check body/status
- `gha_workflow_check`   — GitHub Actions run conclusion == "success"
- `artifact_flag`        — sha256(learner_submitted_string) == expected
- `llm_rubric`           — Haiku-scored criteria (tone, clarity, depth)
- `benchmark_score`      — held-out eval set score above threshold

Registry caps: `compile`, `hidden_tests`, `property_test`, `lint`, `must_contain`
are per-source grading; `state_assertion`, `endpoint_probe`, `gha_workflow_check`,
`artifact_flag` are per-artifact grading; `llm_rubric` and `benchmark_score` are
per-output grading. Registry enforces: every code assignment needs ≥1 cheese-proof
primitive (anything except `must_contain` alone).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1 — SLIDES (content-card templates)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SlideType:
    """A templated HTML shape the Creator can pick. LLM fills the fields; we
    own the structure + CSS. No more free-form inline-HTML widgets with
    zombie setIntervals.
    """
    id: str
    description: str
    # Templated HTML with {{field_name}} placeholders. Dark-theme palette
    # baked in. No <script> allowed inside (that's what `mini_demo` is for
    # with its own managed lifecycle).
    html_template: str
    # Field schema: field_name -> type (str / int / list[str] / list[dict]).
    fields: dict[str, str]
    # When the Creator may use this slide: on concept steps, intro cards,
    # before-exercise briefings, reflection cards.
    contexts: list[Literal["intro", "concept", "briefing", "reflection", "widget"]] = field(default_factory=lambda: ["concept"])
    # If True, the slide may embed a managed <script> with auto-teardown on
    # step navigation (see frontend widget-timer cleanup). Default False.
    allows_managed_script: bool = False


SLIDE_REGISTRY: dict[str, SlideType] = {}


def register_slide(slide: SlideType) -> SlideType:
    """Register a new slide type. Safe to call from extension modules."""
    SLIDE_REGISTRY[slide.id] = slide
    return slide


# Baseline slides every course can use. Extend from outside if needed.
register_slide(SlideType(
    id="concept_card",
    description="One titled card with heading + body paragraph. The default way to present a single concept.",
    html_template=(
        '<div style="background:#1e2538; color:#e8ecf4; border:1px solid #2a3352; '
        'border-radius:8px; padding:12px 16px; margin-bottom:10px;">'
        '<h4 style="margin:0 0 6px 0; color:#e8ecf4;">{{title}}</h4>'
        '<div style="margin:0; color:#c9d1df;">{{body}}</div>'
        '</div>'
    ),
    fields={"title": "str", "body": "html (no <script>)"},
    contexts=["concept", "intro", "briefing", "reflection"],
))

register_slide(SlideType(
    id="diagram_flow",
    description="SVG node-and-arrow graph for pipelines, state machines, request flows. Replaces text-log widgets.",
    html_template=(
        '<div style="background:#1e2538; border:1px solid #2a3352; border-radius:8px; padding:16px; margin-bottom:10px;">'
        '<h4 style="margin:0 0 10px 0; color:#e8ecf4;">{{title}}</h4>'
        '<svg viewBox="0 0 700 180" style="width:100%; height:auto;">{{svg_body}}</svg>'
        '<p style="margin:8px 0 0 0; color:#8892a8; font-size:0.88em;">{{caption}}</p>'
        '</div>'
    ),
    fields={"title": "str", "svg_body": "svg (rects + paths)", "caption": "str"},
    contexts=["concept", "briefing"],
))

register_slide(SlideType(
    id="table_compare",
    description="2-4 column comparison table. Use for when-to-use-X-vs-Y, tradeoff matrices.",
    html_template=(
        '<div style="background:#1e2538; border:1px solid #2a3352; border-radius:8px; padding:12px 16px; margin-bottom:10px;">'
        '<h4 style="margin:0 0 8px 0; color:#e8ecf4;">{{title}}</h4>'
        '<table style="width:100%; border-collapse:collapse; color:#c9d1df;">'
        '<thead>{{thead}}</thead><tbody>{{tbody}}</tbody>'
        '</table></div>'
    ),
    fields={"title": "str", "thead": "html <tr><th>…</th></tr>", "tbody": "html rows"},
    contexts=["concept", "briefing", "reflection"],
))

register_slide(SlideType(
    id="checklist",
    description="Styled bullet list with verbatim-phrase items. Use for 'before you ship' lists, verifier steps.",
    html_template=(
        '<div style="background:#1e2538; border:1px solid #2a3352; border-radius:8px; padding:12px 16px; margin-bottom:10px;">'
        '<h4 style="margin:0 0 8px 0; color:#e8ecf4;">{{title}}</h4>'
        '<ul style="margin:0; padding-left:20px; color:#c9d1df;">{{items_html}}</ul>'
        '</div>'
    ),
    fields={"title": "str", "items_html": "html <li>…</li> items"},
    contexts=["concept", "briefing", "reflection"],
))

register_slide(SlideType(
    id="code_read",
    description="Syntax-highlighted read-only code snippet with optional annotation.",
    html_template=(
        '<div style="background:#161b26; border:1px solid #2a3352; border-radius:8px; padding:12px; margin-bottom:10px;">'
        '<pre style="margin:0; color:#e8ecf4; font-family:monospace; font-size:0.9em; overflow-x:auto;">'
        '<code class="lang-{{language}}">{{code}}</code></pre>'
        '<p style="margin:8px 0 0 0; color:#8892a8; font-size:0.86em;">{{annotation}}</p>'
        '</div>'
    ),
    fields={"title": "str", "language": "str", "code": "str", "annotation": "str"},
    contexts=["concept", "briefing"],
))

register_slide(SlideType(
    id="callout_warn",
    description="Red-bordered warning/pitfall callout.",
    html_template=(
        '<div style="background:#2a1a22; color:#fca5a5; border-left:3px solid #f87171; border-radius:4px; padding:10px 14px; margin-bottom:10px;">'
        '<strong>⚠ {{title}}:</strong> <span style="color:#e8ecf4;">{{body}}</span>'
        '</div>'
    ),
    fields={"title": "str", "body": "str"},
    contexts=["concept", "briefing", "reflection"],
))

register_slide(SlideType(
    id="callout_tip",
    description="Teal-bordered tip/insight callout.",
    html_template=(
        '<div style="background:#0e2620; color:#86efac; border-left:3px solid #2dd4bf; border-radius:4px; padding:10px 14px; margin-bottom:10px;">'
        '<strong>💡 {{title}}:</strong> <span style="color:#e8ecf4;">{{body}}</span>'
        '</div>'
    ),
    fields={"title": "str", "body": "str"},
    contexts=["concept", "briefing", "reflection"],
))

register_slide(SlideType(
    id="stat_highlight",
    description="Big-number card. Use for hook stats like '47% of outages start with…'.",
    html_template=(
        '<div style="background:#1e2538; border:1px solid #2a3352; border-radius:8px; padding:16px; margin-bottom:10px; text-align:center;">'
        '<div style="font-size:2em; color:#4a7cff; font-weight:700; margin-bottom:4px;">{{value}}</div>'
        '<div style="color:#c9d1df;">{{label}}</div>'
        '<p style="margin:6px 0 0 0; color:#8892a8; font-size:0.82em;">{{source}}</p>'
        '</div>'
    ),
    fields={"value": "str", "label": "str", "source": "str"},
    contexts=["intro", "concept"],
))

register_slide(SlideType(
    id="domain_legend",
    description="Key-value card listing valid enum values. MUST be used before any fill-in-blank that expects domain-specific enum values.",
    html_template=(
        '<div style="background:#161b26; color:#e8ecf4; border:1px solid #2a3352; border-radius:6px; padding:10px 14px; margin-bottom:10px;">'
        '<h5 style="margin:0 0 6px 0; color:#2dd4bf;">📚 {{title}}</h5>'
        '<dl style="margin:0; color:#c9d1df; font-size:0.92em;">{{dl_html}}</dl>'
        '</div>'
    ),
    fields={"title": "str", "dl_html": "html <dt>/<dd> pairs"},
    contexts=["briefing"],
))

register_slide(SlideType(
    id="mini_demo",
    description="Small interactive demo widget. MUST use the frontend's managed-script wrapper so setInterval/setTimeout are cleared on step navigation. Use only when static slides cannot convey the concept.",
    html_template=(
        '<div data-managed-widget="true" style="background:#1e2538; border:1px solid #2a3352; border-radius:8px; padding:12px; margin-bottom:10px;">'
        '<h4 style="margin:0 0 8px 0; color:#e8ecf4;">{{title}}</h4>'
        '<div id="{{container_id}}" data-widget-container="true">{{initial_html}}</div>'
        '<script data-managed="true">{{script_body}}</script>'
        '</div>'
    ),
    fields={"title": "str", "container_id": "str", "initial_html": "html", "script_body": "js (null-guard required; no unbounded setInterval)"},
    contexts=["widget"],
    allows_managed_script=True,
))


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2 — ASSIGNMENTS (exercise types with grade primitives)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AssignmentType:
    """An exercise type. The Creator emits steps typed as one of these, and
    `_is_complete` + the grader dispatch off `id` + `grade_primitives`.
    """
    id: str
    description: str
    # Grade primitives (see module docstring) with per-primitive weight.
    # Cheese-proof requirement: at least one primitive MUST be in
    # {hidden_tests, property_test, state_assertion, endpoint_probe,
    #  gha_workflow_check, artifact_flag, bug_lines, benchmark_score}.
    # `must_contain` alone is insufficient.
    grade_primitives: list[str]
    grade_weights: dict[str, float] = field(default_factory=dict)
    # Required fields in demo_data / validation for _is_complete to pass.
    required_demo_data: list[str] = field(default_factory=list)
    required_validation: list[str] = field(default_factory=list)
    # Runtime primitive used to execute the learner's submission.
    runtime: str | None = None  # see RUNTIME_REGISTRY
    # How learner-facing: interactive editor, read-only display, live sim,
    # dialogic (LLM turn loop), real (actual external workflow).
    interaction_mode: Literal["static", "interactive", "simulation", "dialogic", "real_workflow"] = "interactive"
    # Reality score: simulated sandbox, shadow (no real-world effects), real
    # (actual artifacts produced — a real PR, a real deploy).
    reality_score: Literal["simulated", "shadow", "real"] = "simulated"
    # True for assignments where the learner writes code. Triggers the
    # simplified schema the 2026-04-21 directive asked for (code + type + bug_lines only).
    is_code_assignment: bool = False
    # If True, the assignment supports the LangGraph-style solution/starter
    # invariant: Creator emits a solution file alongside the starter, and
    # the generation pipeline validates solution-passes + starter-fails
    # before publish.
    supports_solution_starter_invariant: bool = False


ASSIGNMENT_REGISTRY: dict[str, AssignmentType] = {}


def register_assignment(a: AssignmentType) -> AssignmentType:
    ASSIGNMENT_REGISTRY[a.id] = a
    return a


# ---- CODE-WRITING (simplified schema per 2026-04-21 directive) ----
# "For every code assignments - we should only ask for code, type, code
# details(bug lines). Remove fill in the lines for code."
register_assignment(AssignmentType(
    id="code_exercise",
    description="Learner writes real code against a hidden test suite. Cheese-proof via hidden tests (preferred) or must_contain (legacy transition).",
    grade_primitives=["compile", "hidden_tests", "lint", "llm_rubric", "must_contain"],
    # During transition (2026-04-21 → hidden_tests rollout): accept EITHER
    # hidden_tests OR must_contain so the Creator can keep generating while the
    # hidden-tests pipeline (LangGraph solution/starter invariant) is being built.
    # Once hidden_tests is wired end-to-end, flip this to just ["hidden_tests"].
    grade_weights={"compile": 0.10, "hidden_tests": 0.55, "must_contain": 0.05, "lint": 0.15, "llm_rubric": 0.15},
    required_demo_data=["language"],
    required_validation=["any_of:hidden_tests,must_contain"],
    runtime="auto",  # resolved from demo_data.language
    interaction_mode="interactive",
    reality_score="simulated",
    is_code_assignment=True,
    supports_solution_starter_invariant=True,
))

register_assignment(AssignmentType(
    id="code_review",
    description="Learner reads code and flags buggy line numbers. Graded on set-match to Creator-chosen bug_lines.",
    grade_primitives=["bug_lines"],
    grade_weights={"bug_lines": 1.0},
    required_demo_data=["language", "code", "bugs"],
    required_validation=["bug_lines"],
    runtime=None,  # No execution — display only.
    interaction_mode="interactive",
    reality_score="simulated",
    is_code_assignment=True,
))

register_assignment(AssignmentType(
    id="code_read",
    description="Learner reads + explains code. No execution. Graded on LLM rubric of explanation quality.",
    grade_primitives=["llm_rubric"],
    grade_weights={"llm_rubric": 1.0},
    required_demo_data=["language", "code"],
    required_validation=["explanation_rubric"],
    runtime=None,
    interaction_mode="static",
    is_code_assignment=True,
))

register_assignment(AssignmentType(
    id="terminal_exercise",
    description=(
        "Learner runs commands in their OWN terminal (BYO-key: their own "
        "Anthropic / OpenRouter key + local tools) and the skillslab CLI "
        "captures + submits the output. NO copy-paste from terminal to "
        "browser. The CLI reads `validation.cli_commands` (declarative list "
        "of {cmd, expect, label}), runs each, captures stdout/stderr, "
        "checks the `expect` regex, and submits the combined output to the "
        "LMS via /api/exercises/validate where the existing rubric / "
        "must_contain grade the captured text. Zero platform LLM cost to "
        "execute the exercise itself — we only pay the rubric grader (~500 "
        "tokens). 2026-04-25 v2: TERMINAL-FIRST. The web frontend renders "
        "a 'open your skillslab CLI' pointer for terminal_exercise steps "
        "instead of a paste textarea — paste-from-browser was the artifact "
        "of a browser-only history we no longer have."
    ),
    grade_primitives=["llm_rubric", "must_contain"],
    grade_weights={"llm_rubric": 0.8, "must_contain": 0.2},
    required_demo_data=["instructions"],  # the command(s) learner should run
    # Terminal-first: cli_commands is REQUIRED (declarative list of what the
    # CLI runs + grades against). rubric / must_contain remain optional and
    # grade the captured output text. Legacy steps without cli_commands are
    # accepted but flagged for re-regen.
    required_validation=["cli_commands", "any_of:rubric,must_contain"],
    runtime=None,  # runs on learner's machine, not ours
    interaction_mode="byo_execution",
    reality_score="real",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="system_build",
    description="Learner ships a real deliverable (deploy / PR / cluster state). At least ONE real-attestation primitive required.",
    grade_primitives=["gha_workflow_check", "endpoint_check", "state_assertion", "artifact_flag"],
    grade_weights={"gha_workflow_check": 1.0},  # overridden per-instance by Creator
    required_demo_data=["phases", "checklist"],
    # Exactly ONE of these must be populated in validation. Field names match
    # what the runtime validators look for: `endpoint_check` (existing HTTP
    # probe), `gha_workflow_check` (F24), `state_assertion` (cluster_state_check),
    # `artifact_flag` (flag-submit capstone). _is_complete rejects if all four missing.
    required_validation=["any_of:gha_workflow_check,endpoint_check,state_assertion,artifact_flag"],
    runtime="auto",
    interaction_mode="real_workflow",
    reality_score="real",
    is_code_assignment=True,
    supports_solution_starter_invariant=True,
))

# ---- READ-ONLY / STATIC ----
register_assignment(AssignmentType(
    id="code",  # legacy: read-only runnable demo
    description="Read + run a demo snippet. No learner write.",
    grade_primitives=["compile"],
    grade_weights={"compile": 1.0},
    required_demo_data=["language"],
    required_validation=[],
    runtime="auto",
    interaction_mode="static",
    is_code_assignment=True,
))

# ---- NON-CODE EXERCISE TYPES (kept as-is for non-tech courses) ----
register_assignment(AssignmentType(
    id="fill_in_blank",
    description="Fill blanks in a text/config template. NOT for code — use code_exercise instead.",
    grade_primitives=["blank_match"],
    grade_weights={"blank_match": 1.0},
    required_demo_data=[],
    required_validation=["blanks"],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,  # text-only per directive
))
# NOTE (2026-04-21 directive): fill_in_blank for CODE languages is retired.
# The `_is_complete()` gate rejects FIB steps whose demo_data.language is in
# {python, sql, shell, dockerfile, yaml, go, ts, js, rust, java, ruby}. Use
# code_exercise with hidden_tests instead. FIB remains valid for text, markdown,
# config templates, and compliance-copy fill-ins.

register_assignment(AssignmentType(
    id="parsons",
    description="Assemble code lines in correct order. Max 8 lines.",
    grade_primitives=["order_match"],
    grade_weights={"order_match": 1.0},
    required_demo_data=["lines"],
    required_validation=["correct_order"],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="ordering",
    description="Order a list of process steps.",
    grade_primitives=["order_match"],
    grade_weights={"order_match": 1.0},
    required_demo_data=["items"],
    required_validation=["correct_order"],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="categorization",
    description="Classify items into categories. Token-set consistency enforced.",
    grade_primitives=["mapping_match"],
    grade_weights={"mapping_match": 1.0},
    required_demo_data=["categories", "items"],
    required_validation=["correct_mapping"],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="sjt",
    description="Situational judgment test — rank N options by quality.",
    grade_primitives=["rank_match"],
    grade_weights={"rank_match": 1.0},
    required_demo_data=["scenario", "options"],
    required_validation=["correct_rankings"],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="scenario_branch",
    description="Multi-step decision tree with consequences.",
    grade_primitives=["branch_correctness"],
    grade_weights={"branch_correctness": 1.0},
    required_demo_data=["scenario", "steps"],
    required_validation=[],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="mcq",
    description="Multiple choice. Use sparingly.",
    grade_primitives=["option_match"],
    grade_weights={"option_match": 1.0},
    required_demo_data=["question", "options"],
    required_validation=["correct_answer"],
    runtime=None,
    interaction_mode="interactive",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="concept",
    description="Teaching content only — no interaction required. Uses slide registry.",
    grade_primitives=[],
    required_demo_data=[],
    required_validation=[],
    runtime=None,
    interaction_mode="static",
    is_code_assignment=False,
))

# ---- DIALOGIC / SIMULATION (already shipped) ----
register_assignment(AssignmentType(
    id="adaptive_roleplay",
    description="TEXT roleplay with hidden-state counterparty.",
    grade_primitives=["llm_rubric", "state_trajectory"],
    grade_weights={"llm_rubric": 0.6, "state_trajectory": 0.4},
    required_demo_data=["scenario_prompt", "counterparty"],
    required_validation=[],
    runtime=None,
    interaction_mode="dialogic",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="voice_mock_interview",
    description="LIVE VOICE interview — learner speaks, AI replies via TTS.",
    grade_primitives=["llm_rubric", "state_trajectory"],
    grade_weights={"llm_rubric": 0.6, "state_trajectory": 0.4},
    required_demo_data=["scenario_prompt", "counterparty", "interview_style"],
    required_validation=[],
    runtime=None,
    interaction_mode="dialogic",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="incident_console",
    description="Scripted production-outage simulator (zero LLM cost/session).",
    grade_primitives=["incident_rubric"],
    grade_weights={"incident_rubric": 1.0},
    required_demo_data=["alert", "commands", "log_stream"],
    required_validation=["accepted_remediations"],
    runtime=None,
    interaction_mode="simulation",
    is_code_assignment=False,
))

register_assignment(AssignmentType(
    id="simulator_loop",
    description="Generic tick-based simulation primitive. REQUIRES initial_state + actions + events + win_conditions in demo_data to be runnable by /api/simloop/*.",
    grade_primitives=["sim_win_condition"],
    grade_weights={"sim_win_condition": 1.0},
    # 2026-04-24 v8.6.2 — the simloop runtime expects ALL of these in demo_data:
    #   initial_state (dict)        — what the dashboard shows on start
    #   actions (list[{id,label,...,effect?,cost_ticks?}]) — what the learner can DO each tick
    #   events (list[{id,t_offset_ms,...,effect?}])       — scheduled interruptions (manager pings / CEO email)
    #   win_conditions (list[{expression,outcome}])        — how the sim ends successfully
    # Without actions+events+win_conditions the sim is non-functional (400 from /api/simloop/start,
    # no interrupts fire, and no terminal outcome) — the beginner reviewer's v1 "simulator
    # broken" report traced to exactly this drop-fields-on-gen class.
    required_demo_data=["initial_state", "actions", "events", "win_conditions"],
    required_validation=[],
    runtime=None,
    interaction_mode="simulation",
    is_code_assignment=False,
))

# ---- NEW FORMATS FROM RESEARCH ARTIFACT (registry entries, backends stubbed) ----
# Each is registered so the ontology knows about them; backend handlers register
# themselves into RUNTIME_REGISTRY when their module is imported. Until then,
# the Creator can reference these but _is_complete gate says "runtime not ready"
# and the exercise is generated with a fallback.

register_assignment(AssignmentType(
    id="github_classroom_capstone",
    description="Real PR workflow with GHA grading + AI-reviewer comments.",
    grade_primitives=["gha_workflow_check", "llm_rubric"],
    grade_weights={"gha_workflow_check": 0.7, "llm_rubric": 0.3},
    required_demo_data=["starter_repo"],
    required_validation=["gha_workflow_check"],
    runtime="github_actions",
    interaction_mode="real_workflow",
    reality_score="real",
    is_code_assignment=True,
    supports_solution_starter_invariant=True,
))

register_assignment(AssignmentType(
    id="cluster_state_check",
    description="Grade against real K8s/Docker/DB end state after learner mutations.",
    grade_primitives=["state_assertion"],
    grade_weights={"state_assertion": 1.0},
    required_demo_data=["briefing", "cluster_template"],
    required_validation=["assertions", "solve_script"],
    runtime="ephemeral_k3d",
    interaction_mode="simulation",
    reality_score="shadow",
    is_code_assignment=True,
))

register_assignment(AssignmentType(
    id="artifact_flag_capstone",
    description="Learner harvests a per-learner-seeded secret; grader checks sha256.",
    grade_primitives=["artifact_flag"],
    grade_weights={"artifact_flag": 1.0},
    required_demo_data=["briefing", "expected_artifact_format"],
    required_validation=["artifact_hash_salt"],
    runtime="ephemeral_system",
    interaction_mode="simulation",
    reality_score="shadow",
    is_code_assignment=True,
))

register_assignment(AssignmentType(
    id="mentored_iteration",
    description="Exercism-style code review with 1-3 LLM comments per round; learner iterates.",
    grade_primitives=["llm_rubric", "iteration_efficiency"],
    grade_weights={"llm_rubric": 0.7, "iteration_efficiency": 0.3},
    required_demo_data=["task", "starter_code", "mentor_persona_prompt"],
    required_validation=["max_rounds", "rubric_tags"],
    runtime="python_sandbox",  # runs whatever language the starter is in
    interaction_mode="dialogic",
    is_code_assignment=True,
))

register_assignment(AssignmentType(
    id="property_test_grader",
    description="Hypothesis-style property tests. Randomized inputs. Cheese-proof.",
    grade_primitives=["property_test"],
    grade_weights={"property_test": 1.0},
    required_demo_data=["task", "interface_contract"],
    required_validation=["properties", "generators"],
    runtime="python_sandbox",
    interaction_mode="interactive",
    is_code_assignment=True,
    supports_solution_starter_invariant=True,
))

register_assignment(AssignmentType(
    id="benchmark_arena",
    description="Kaggle-style public/private eval. Cheese-proof.",
    grade_primitives=["benchmark_score"],
    grade_weights={"benchmark_score": 1.0},
    required_demo_data=["task", "public_eval_dataset_url"],
    required_validation=["private_eval_server", "passing_threshold"],
    runtime="benchmark_server",
    interaction_mode="interactive",
    reality_score="shadow",
    is_code_assignment=True,
))


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3 — COURSE MODES (module-shape contracts)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CourseMode:
    id: str
    description: str
    # Required module-shape invariants. Registry validates on generate.
    min_modules: int = 3
    max_modules: int = 9
    requires_capstone: bool = True
    capstone_assignment_types: list[str] = field(default_factory=list)
    # Optional runtime shell (maps to a frontend shell template).
    ui_shell: str | None = None


COURSE_MODE_REGISTRY: dict[str, CourseMode] = {}


def register_course_mode(m: CourseMode) -> CourseMode:
    COURSE_MODE_REGISTRY[m.id] = m
    return m


register_course_mode(CourseMode(
    id="linear",
    description="Classic 3-5 modules × 3-5 steps. One capstone at the end.",
    min_modules=3, max_modules=7,
    requires_capstone=True,
    capstone_assignment_types=["system_build", "github_classroom_capstone", "cluster_state_check"],
))

register_course_mode(CourseMode(
    id="case_library",
    description="N numbered cases (3-20 min each) + 1 'Full Cascade' capstone.",
    min_modules=5, max_modules=12,
    requires_capstone=True,
    capstone_assignment_types=["incident_console", "cluster_state_check", "system_build"],
))

register_course_mode(CourseMode(
    id="simulator_workday",
    description="Multi-pane workspace shell + case pack (10-workspace archetype plan).",
    min_modules=4, max_modules=10,
    requires_capstone=True,
    capstone_assignment_types=["simulator_loop", "incident_console", "adaptive_roleplay"],
    ui_shell="workday_shell",
))

register_course_mode(CourseMode(
    id="drill_only",
    description="Flat list of 10-20 short drills. No capstone.",
    min_modules=1, max_modules=2,
    requires_capstone=False,
))

register_course_mode(CourseMode(
    id="certification_track",
    description="Proctored final after 10-15 drills. Timed mode, hints disabled.",
    min_modules=5, max_modules=12,
    requires_capstone=True,
    capstone_assignment_types=["system_build", "github_classroom_capstone"],
))


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 4 — TECH DOMAINS (the master list for tech courses)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TechDomain:
    """A canonical tech domain. Enumerates the stack, the assignment recipes
    the Creator should prefer for that domain, and the runtime requirements.
    """
    id: str
    label: str
    description: str
    canonical_stack: list[str]
    # Assignment types the Creator may pick for this domain, in preference order.
    preferred_assignments: list[str]
    # Runtime primitives required. If any aren't registered yet, Creator falls
    # back to the best available (e.g. python_sandbox instead of ephemeral_k3d).
    runtimes: list[str]
    # Pointer to a fixture-library entry (starter repo URL, dataset URL, etc).
    # Used by F26 scaffold primitives.
    fixture_hints: list[str] = field(default_factory=list)


TECH_DOMAIN_REGISTRY: dict[str, TechDomain] = {}


def register_tech_domain(d: TechDomain) -> TechDomain:
    TECH_DOMAIN_REGISTRY[d.id] = d
    return d


# V1 domains — 5 prioritized + 7 placeholder. Extend via register_tech_domain().
register_tech_domain(TechDomain(
    id="backend_python",
    label="Backend Python",
    description="FastAPI / Flask / Django — async + sync servers.",
    canonical_stack=["python", "fastapi", "pytest", "pydantic", "httpx", "redis"],
    preferred_assignments=["code_exercise", "code_review", "system_build", "mentored_iteration", "property_test_grader"],
    runtimes=["python_sandbox", "docker", "github_actions"],
    fixture_hints=["skills-lab-demos/fastapi-starter", "skills-lab-demos/flowsync-50k"],
))

register_tech_domain(TechDomain(
    id="data_sql",
    label="Data & SQL",
    description="Postgres / MySQL / SQLite — migrations, EXPLAIN, tuning.",
    canonical_stack=["sql", "postgresql", "sqlite", "alembic"],
    preferred_assignments=["code_exercise", "code_review", "cluster_state_check"],
    runtimes=["sql_sqlite", "docker"],
    fixture_hints=["skills-lab-demos/pg-ecommerce-schema"],
))

register_tech_domain(TechDomain(
    id="devops_docker",
    label="DevOps — Docker",
    description="Dockerfile / compose / multi-stage builds.",
    canonical_stack=["dockerfile", "docker-compose", "bash"],
    preferred_assignments=["code_exercise", "code_review", "system_build", "github_classroom_capstone"],
    runtimes=["dockerfile_lint", "docker", "github_actions"],
    fixture_hints=["skills-lab-demos/docker-capstone"],
))

register_tech_domain(TechDomain(
    id="devops_k8s",
    label="DevOps — Kubernetes",
    description="Helm / kubectl / ArgoCD / Terraform.",
    canonical_stack=["yaml", "helm", "kubectl", "terraform"],
    preferred_assignments=["code_exercise", "cluster_state_check", "system_build", "github_classroom_capstone"],
    runtimes=["yaml_schema", "ephemeral_k3d", "github_actions"],
    fixture_hints=["skills-lab-demos/k8s-starter-manifests"],
))

register_tech_domain(TechDomain(
    id="ai_dev_tools",
    label="AI-assisted development",
    description="Claude Code / Cursor / Copilot / agentic coding workflows.",
    canonical_stack=["python", "bash", "claude-code", "git"],
    preferred_assignments=["code_exercise", "code_review", "system_build", "mentored_iteration"],
    runtimes=["python_sandbox", "terminal", "github_actions"],
    fixture_hints=["skills-lab-demos/flowsync-50k", "skills-lab-demos/velora-web"],
))

# Placeholder entries for future expansion — register_tech_domain() from an
# extension module to flesh these out.
for _id, _label, _desc, _stack, _assigns, _runtimes in [
    ("backend_node", "Backend Node/TS", "Express / NestJS / Fastify.",
     ["typescript", "node", "jest"], ["code_exercise", "code_review", "mentored_iteration"],
     ["webcontainer", "docker"]),
    ("backend_go", "Backend Go", "net/http / gin / chi.",
     ["go", "gofmt", "go-test"], ["code_exercise", "code_review", "cluster_state_check"],
     ["docker", "github_actions"]),
    ("frontend_react", "Frontend — React", "React / Next.js / Vite.",
     ["typescript", "react", "vite"], ["code_exercise", "pixel_diff_capstone", "mentored_iteration"],
     ["webcontainer"]),
    ("data_ml", "Data / ML", "Python + NumPy/Pandas/PyTorch.",
     ["python", "numpy", "pandas", "pytorch"], ["code_exercise", "property_test_grader", "benchmark_arena"],
     ["python_sandbox", "benchmark_server"]),
    ("data_analytics", "Data analytics", "dbt / Looker / Snowflake.",
     ["sql", "dbt"], ["code_exercise", "code_review", "scenario_branch"],
     ["sql_sqlite", "docker"]),
    ("ops_sre", "Ops / SRE", "Grafana / Datadog / PagerDuty.",
     ["bash", "python", "prometheus"], ["incident_console", "adaptive_roleplay", "cluster_state_check"],
     ["python_sandbox", "ephemeral_k3d"]),
    ("security_appsec", "Security — AppSec", "OWASP / CWE / semgrep.",
     ["python", "bash"], ["artifact_flag_capstone", "code_review", "scenario_branch"],
     ["python_sandbox", "ephemeral_system"]),
    ("observability", "Observability", "OpenTelemetry / Jaeger / Prometheus.",
     ["python", "otel"], ["code_exercise", "artifact_flag_capstone"],
     ["python_sandbox", "docker"]),
]:
    register_tech_domain(TechDomain(id=_id, label=_label, description=_desc,
                                     canonical_stack=_stack, preferred_assignments=_assigns,
                                     runtimes=_runtimes))


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 5 — RUNTIMES (execution primitives)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Runtime:
    id: str
    description: str
    # Availability status. Creator prefers `ready` runtimes; if the preferred
    # runtime is `stub` or `planned`, it falls back to one that is `ready`.
    status: Literal["ready", "stub", "planned"]
    # Grade primitives this runtime can support server-side.
    supported_grade_primitives: list[str]
    # A handler callable that runs the learner's code and returns
    # {output, error, execution_time}. Registered lazily by runtime modules.
    handler: Callable | None = None


RUNTIME_REGISTRY: dict[str, Runtime] = {}


def register_runtime(r: Runtime) -> Runtime:
    RUNTIME_REGISTRY[r.id] = r
    return r


def bind_runtime_handler(runtime_id: str, handler: Callable) -> None:
    """Runtime modules call this to register their execute() function.
    Called at import time from the main runtime module."""
    if runtime_id in RUNTIME_REGISTRY:
        RUNTIME_REGISTRY[runtime_id].handler = handler
        RUNTIME_REGISTRY[runtime_id].status = "ready"


# Runtimes we already have — handler bindings happen in main.py at startup
register_runtime(Runtime(
    id="python_sandbox",
    description="In-process threaded exec with starter_files scaffold support (F26).",
    status="stub",  # becomes "ready" when main.py binds the handler
    supported_grade_primitives=["compile", "hidden_tests", "property_test", "lint", "must_contain"],
))

register_runtime(Runtime(
    id="sql_sqlite",
    description="In-memory SQLite with schema_setup + seed_rows.",
    status="stub",
    supported_grade_primitives=["compile", "must_contain"],
))

register_runtime(Runtime(
    id="yaml_schema",
    description="PyYAML parse + JSON-schema validate.",
    status="stub",
    supported_grade_primitives=["compile", "must_contain"],
))

register_runtime(Runtime(
    id="dockerfile_lint",
    description="Dockerfile parser + lint hints.",
    status="stub",
    supported_grade_primitives=["compile", "must_contain"],
))

register_runtime(Runtime(
    id="shell_bash_n",
    description="bash -n syntax check.",
    status="stub",
    supported_grade_primitives=["compile", "must_contain"],
))

# New first-class runtime objects per 2026-04-21 directive:
register_runtime(Runtime(
    id="docker",
    description="Docker-in-Docker / remote Docker daemon. Build+run learner's Dockerfile, run tests in container.",
    status="planned",
    supported_grade_primitives=["compile", "hidden_tests", "state_assertion"],
))

register_runtime(Runtime(
    id="github_actions",
    description="GitHub Actions run attestation. Learner pushes branch → GHA runs lab-grade.yml → grader polls API for conclusion.",
    status="planned",  # Creator prompt ready; backend poller pending (F24 W1.5)
    supported_grade_primitives=["gha_workflow_check"],
))

register_runtime(Runtime(
    id="vscode",
    description="VS Code Server / Monaco-backed in-browser editor with LSP. Optional language servers per domain.",
    status="planned",
    supported_grade_primitives=["compile", "hidden_tests", "lint"],
))

register_runtime(Runtime(
    id="terminal",
    description="Persistent xterm + shell session per learner. Command history forwarded to grader.",
    status="planned",
    supported_grade_primitives=["state_assertion"],
))

register_runtime(Runtime(
    id="ephemeral_k3d",
    description="Per-learner k3d (K3s-in-Docker) cluster. Spin up on session, assertions via kubectl.",
    status="planned",
    supported_grade_primitives=["state_assertion"],
))

register_runtime(Runtime(
    id="ephemeral_system",
    description="Per-learner ephemeral target system (for artifact_flag capstones).",
    status="planned",
    supported_grade_primitives=["artifact_flag"],
))

register_runtime(Runtime(
    id="webcontainer",
    description="StackBlitz WebContainer in browser. Real npm install against real registry.",
    status="planned",
    supported_grade_primitives=["compile", "hidden_tests", "lint"],
))

register_runtime(Runtime(
    id="benchmark_server",
    description="Private-held-out eval server for Kaggle-style benchmarks.",
    status="planned",
    supported_grade_primitives=["benchmark_score"],
))


# ═══════════════════════════════════════════════════════════════════════════
# CREATOR PROMPT ASSEMBLER
# ═══════════════════════════════════════════════════════════════════════════

def describe_assignment_for_prompt(aid: str) -> str:
    """Render a single assignment registry entry as prompt text."""
    a = ASSIGNMENT_REGISTRY.get(aid)
    if not a:
        return f"(unknown assignment {aid})"
    lines = [
        f"- {a.id}: {a.description}",
        f"  grade_primitives: {', '.join(a.grade_primitives) or '(none — informational only)'}",
        f"  required demo_data: {', '.join(a.required_demo_data) or '(none)'}",
        f"  required validation: {', '.join(a.required_validation) or '(none)'}",
        f"  runtime: {a.runtime or 'none'} · interaction: {a.interaction_mode} · reality: {a.reality_score}",
    ]
    return "\n".join(lines)


def describe_domain_for_prompt(did: str) -> str:
    d = TECH_DOMAIN_REGISTRY.get(did)
    if not d:
        return f"(unknown domain {did})"
    return (f"- {d.id} ({d.label}): {d.description}\n"
            f"  stack: {', '.join(d.canonical_stack)}\n"
            f"  preferred assignments (in order): {', '.join(d.preferred_assignments)}\n"
            f"  runtimes: {', '.join(d.runtimes)}\n"
            f"  fixture hints: {', '.join(d.fixture_hints) or '(none)'}")


def build_creator_ontology_brief(domain_id: str | None = None) -> str:
    """Produce the ontology-grounded section of the Creator prompt. Called at
    generate time, not at module import — so newly-registered entries are
    included without restart."""
    parts = ["## ONTOLOGY (data-driven; do not invent types outside this list)"]

    parts.append("\n### Available assignment types")
    for aid in sorted(ASSIGNMENT_REGISTRY):
        parts.append(describe_assignment_for_prompt(aid))

    parts.append("\n### Code-assignment schema (2026-04-21 simplification)")
    parts.append(
        "`code_exercise` IS THE PRIMARY EXERCISE TYPE for hands-on programming courses. "
        "For every hands-on programming course, AT LEAST 40% of non-concept steps MUST be "
        "`code_exercise` where the learner writes real code — not `code_review` (read-only), "
        "not `categorization`, not `scenario_branch`. Testing / property / generator / parser / "
        "encoder / transformer / state-machine topics are ALL code_exercise candidates.\n\n"
        "For every code-writing assignment, emit these fields:\n"
        "  - `code` (the starter scaffold, 20-60 lines of real production-flavored code with 2-4 TODOs)\n"
        "  - `exercise_type` (one of: code_exercise, code_review, code_read, system_build, mentored_iteration, property_test_grader)\n"
        "  - `demo_data.language` (one of: python, sql, yaml, dockerfile, shell, go, ts, rust, java, ruby)\n"
        "  - For code_review ONLY: `demo_data.bugs` ([{line, line_content, description}])\n"
        "  - For code_exercise: `validation.hidden_tests` (pytest/jest source — PREFERRED, cheese-proof) "
        "OR `validation.must_contain` ([substrings] — LEGACY, accepted during transition). "
        "Either is fine today; hidden_tests is preferred going forward.\n"
        "BANNED for code assignments: `fill_in_blank` with a code language (use code_exercise instead); "
        "system_build without any of {gha_workflow_check, endpoint_check, state_assertion, artifact_flag}.\n"
        "Every code assignment SHOULD pair: starter does NOT already pass the tests, solution DOES pass. "
        "(LangGraph solution/starter invariant — enforced at _is_complete once hidden_tests lands end-to-end.)"
    )

    if domain_id:
        d = TECH_DOMAIN_REGISTRY.get(domain_id)
        if d:
            parts.append(f"\n### Tech domain context: {d.label}")
            parts.append(describe_domain_for_prompt(domain_id))

    parts.append("\n### Available runtimes (grade primitives per runtime)")
    for rid, r in sorted(RUNTIME_REGISTRY.items()):
        status = "✓" if r.status == "ready" else ("⏳" if r.status == "stub" else "✗")
        parts.append(f"- {status} {r.id}: {r.description} — supports {', '.join(r.supported_grade_primitives)}")

    parts.append("\n### Slide types for step.content (pick one or combine)")
    for sid, s in sorted(SLIDE_REGISTRY.items()):
        parts.append(f"- {s.id}: {s.description}")
    parts.append("If none fit, emit a `concept_card` — do NOT author free-form inline HTML with <script> blocks.")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# _is_complete GATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

# Language tokens considered "code" for the no-FIB-for-code rule.
CODE_LANGUAGES = frozenset({
    "python", "sql", "shell", "bash", "dockerfile", "yaml", "yml",
    "go", "ts", "typescript", "js", "javascript", "rust", "java",
    "ruby", "c", "cpp", "c++", "csharp", "c#", "php", "swift", "kotlin",
})


def is_code_language(lang: str | None) -> bool:
    return bool(lang) and lang.strip().lower() in CODE_LANGUAGES


def validate_step_against_ontology(
    exercise_type: str,
    demo_data: dict,
    validation: dict,
    code: str | None = None,
) -> tuple[bool, str]:
    """Central ontology gate. Returns (ok, reason_if_not_ok).

    Called from `_is_complete` at generation time. If it returns False, the
    step is regenerated. If it returns True, the step passes the ontology
    contract and moves to the runtime-specific gates.
    """
    a = ASSIGNMENT_REGISTRY.get(exercise_type)
    if not a:
        # Unknown exercise type — reject so Creator regenerates with a known one.
        return False, f"unknown exercise_type {exercise_type!r}; must be one of {sorted(ASSIGNMENT_REGISTRY)}"

    # 2026-04-21 rule: fill_in_blank with a code language is retired.
    if exercise_type == "fill_in_blank":
        lang = (demo_data or {}).get("language") or (validation or {}).get("language")
        if is_code_language(lang):
            return False, f"fill_in_blank for code languages is retired (language={lang!r}); use code_exercise instead"

    # Required demo_data fields present?
    for key in a.required_demo_data:
        if key not in (demo_data or {}):
            return False, f"{exercise_type} missing required demo_data.{key}"

    # Required validation fields present? (Supports `any_of:a,b,c` syntax.)
    for key in a.required_validation:
        if key.startswith("any_of:"):
            opts = [k.strip() for k in key[len("any_of:"):].split(",") if k.strip()]
            if not any(opt in (validation or {}) for opt in opts):
                return False, f"{exercise_type} needs at least one of validation.{{{', '.join(opts)}}}"
        else:
            if key not in (validation or {}):
                return False, f"{exercise_type} missing required validation.{key}"

    # Cheese-proof requirement for code assignments: ≥1 primitive other than must_contain.
    if a.is_code_assignment and a.grade_primitives:
        non_cheesy = [p for p in a.grade_primitives if p != "must_contain"]
        if non_cheesy and not any(p in (validation or {}) or p in (demo_data or {}) for p in non_cheesy):
            # Warning but not reject — grader falls back to must_contain with capped weight.
            pass  # soft — _is_complete caller may still accept

    return True, "ok"


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API SURFACE
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 6 — TRACK PROGRESSION (2026-04-22 v8)
# ═══════════════════════════════════════════════════════════════════════════
#
# WHY: until now the Creator picked exercise types from a flat pool filtered
# by a chain of overlapping heuristics (_is_non_engineering_subject,
# _is_cli_tool_subject, _outline_critic_pass, ENG_CAPSTONES vs CASE_CAPSTONES).
# Two systematic misses surfaced (2026-04-22):
#   1. Claude Code course — Creator picked `code_exercise` capstone when
#      `terminal_exercise` was the only right answer for a CLI-tool course.
#   2. PM AI course — Creator picked `scenario_branch` everywhere including
#      the M7 "Defend to VP Marketing" + M9 "Defend to hostile CFO" capstone
#      where `adaptive_roleplay` was explicitly promised in the course copy.
#
# User proposal: for every TRACK, declare an ordered progression
#     T1 ORIENT → T2 RECOGNIZE → T3 REASON → T4 PERFORM
# where T4 = the "real skill under pressure" tier. The Creator MUST traverse
# all four tiers, and the capstone MUST be from T4. No hardcoded module /
# step counts — only tier + type COVERAGE is enforced; shape adapts to
# content.
#
# This layer sits ALONGSIDE TECH_DOMAIN_REGISTRY (which is engineering-only)
# — TrackProgression applies universally (PM, Legal, CLI, Engineering).
#
# HOLISTIC INVARIANT: a track's tier_progression lists N exercise types.
# Every one of those N types must appear ≥1 time in the course, so learning
# traverses the full declared progression — not just a safe subset.

from typing import Optional


PEDAGOGICAL_TIER_LABELS: dict[int, str] = {
    1: "Orient — get started, no friction ('I understand what this is')",
    2: "Recognize — surface understanding ('I can spot right vs wrong from a list')",
    3: "Reason — apply under hypothesis ('I can pick the right move when options are given')",
    4: "Perform — real-skill under pressure ('I can produce the move from scratch when nothing's given')",
}


@dataclass
class TrackProgression:
    """A pedagogical progression through tiered exercise types for a course track.

    Semantically: a course in this track MUST include at least one step from
    each declared tier, every declared exercise type must appear ≥1 time,
    and the capstone (last step of last module) MUST be from a tier ≥
    `capstone_required_tier` (default 4 — the "real skill" tier).

    Registration is the ONLY edit a new track needs — the Creator prompt is
    auto-assembled from this registry, and `_is_complete()` auto-enforces
    the progression invariants.

    Adding a new track (Sales AI, Legal AI, Security AI, etc.) = one
    register_track(...) call, no prompt rewrite.
    """
    id: str
    label: str
    description: str
    # Signal phrases that select this track from a course's title+description.
    # Matched as lowercased substrings against the title+description blob.
    # An explicit track_id on /api/creator/start always wins over signals.
    match_signals: list[str]
    # {tier_number: [assignment_type_id, ...]} — 1..4 inclusive. Every listed
    # assignment_type_id MUST exist in ASSIGNMENT_REGISTRY. Same type MAY
    # appear in multiple tiers if semantically appropriate in both contexts
    # (rare — usually a type lives at one tier per track).
    tier_progression: dict[int, list[str]]
    # Capstone must be an assignment_type from a tier >= this value.
    capstone_required_tier: int = 4
    # If True: every assignment_type in tier_progression MUST appear ≥1 time
    # in the course. Enforces "holistic coverage" — learner touches every
    # pedagogical shape the track offers. Turn off for tiny primer courses.
    require_all_declared_types: bool = True
    # Minimum distinct types per tier that must appear in the course.
    # Default 1 — relax only if a track has deliberately sparse tiers.
    min_distinct_types_per_tier: int = 1


TRACK_REGISTRY: dict[str, TrackProgression] = {}


def register_track(t: TrackProgression) -> TrackProgression:
    # Defensive: every type the track references must be a known AssignmentType.
    all_types_in_progression = [tid for types in t.tier_progression.values() for tid in types]
    for tid in all_types_in_progression:
        if tid not in ASSIGNMENT_REGISTRY:
            raise ValueError(
                f"Track {t.id!r} references unknown assignment_type {tid!r}. "
                f"Register the assignment_type first, or fix the track's "
                f"tier_progression."
            )
    # Defensive: all four tiers (1..4) must be present.
    for tier in (1, 2, 3, 4):
        if tier not in t.tier_progression or not t.tier_progression[tier]:
            raise ValueError(
                f"Track {t.id!r} is missing tier {tier} in tier_progression. "
                f"Every track must declare assignment types for all 4 tiers."
            )
    TRACK_REGISTRY[t.id] = t
    return t


def get_track(track_id: str) -> Optional[TrackProgression]:
    return TRACK_REGISTRY.get(track_id)


def _lowered_blob(*parts: str) -> str:
    return " ".join(p for p in parts if p).lower()


def detect_track(
    title: str,
    description: str = "",
    *,
    explicit_track_id: Optional[str] = None,
) -> TrackProgression:
    """Pick the right track for a course.

    Policy:
      1. If `explicit_track_id` is provided AND registered, use it. Wins over
         signal detection (future: this is what the Creator wizard passes).
      2. Else, score each registered track by count of its match_signals
         that appear in title+description (lowercased substring match).
         Highest-scoring track wins.
      3. Ties broken by registration order (first wins).
      4. If no track has any signal match, fall back to the 'general' track.
    """
    if explicit_track_id and explicit_track_id in TRACK_REGISTRY:
        return TRACK_REGISTRY[explicit_track_id]
    blob = _lowered_blob(title, description)
    best: Optional[TrackProgression] = None
    best_score = -1
    for t in TRACK_REGISTRY.values():
        score = sum(1 for sig in t.match_signals if sig.lower() in blob)
        if score > best_score:
            best, best_score = t, score
    if best is None or best_score <= 0:
        # Fallback to general. Guaranteed to exist (registered below).
        return TRACK_REGISTRY["general"]
    return best


def tier_of_type_in_track(assignment_type_id: str, track: TrackProgression) -> Optional[int]:
    """Return the tier number where this assignment_type lives in the track,
    or None if the track doesn't include it."""
    for tier, type_ids in track.tier_progression.items():
        if assignment_type_id in type_ids:
            return tier
    return None


def validate_outline_against_track(
    outline: dict,
    track: TrackProgression,
) -> tuple[bool, list[str]]:
    """Check that the outline traverses the track's pedagogical progression.

    Outline shape: {"modules": [{"title": ..., "steps": [{"exercise_type": ...}, ...]}, ...]}
    Returns (ok, violations). Violations are human-readable strings the
    Creator prompt can consume to regenerate the offending step(s).

    Checks (in order):
      (a) Every declared tier (1..4) has ≥1 step whose type belongs to that tier.
      (b) If `require_all_declared_types`: every declared type appears ≥1 time.
      (c) Capstone (last step of last module) has type in tier >=
          capstone_required_tier.
      (d) Every step's exercise_type is in the track's progression (no
          off-track types — this catches e.g. a PM course emitting
          `code_exercise`).
    """
    violations: list[str] = []
    modules = outline.get("modules") or []
    if not modules:
        return False, ["outline has no modules"]

    # Flat list of (module_index, step_index, type_id)
    all_steps: list[tuple[int, int, str]] = []
    for mi, m in enumerate(modules):
        for si, s in enumerate(m.get("steps") or []):
            t = s.get("exercise_type") or s.get("type") or ""
            all_steps.append((mi, si, t))

    if not all_steps:
        return False, ["outline has no steps"]

    all_declared_types = {tid for types in track.tier_progression.values() for tid in types}
    type_to_tier = {tid: tier for tier, types in track.tier_progression.items() for tid in types}

    # (d) off-track types
    off_track = [(mi, si, t) for mi, si, t in all_steps if t not in all_declared_types]
    for mi, si, t in off_track:
        violations.append(
            f"Module {mi + 1}, Step {si + 1}: exercise_type {t!r} is not in "
            f"track {track.id!r}'s progression. Valid types: {sorted(all_declared_types)}."
        )

    # (a) tier coverage
    tiers_present = set()
    for _, _, t in all_steps:
        tier = type_to_tier.get(t)
        if tier is not None:
            tiers_present.add(tier)
    for required_tier in (1, 2, 3, 4):
        if required_tier not in tiers_present:
            types_for_tier = track.tier_progression.get(required_tier, [])
            violations.append(
                f"Tier {required_tier} ({PEDAGOGICAL_TIER_LABELS.get(required_tier, '')}) "
                f"has 0 steps. Need ≥1 step with type in {types_for_tier}."
            )

    # (b) holistic: every declared type appears
    if track.require_all_declared_types:
        types_present = {t for _, _, t in all_steps if t in all_declared_types}
        missing_types = sorted(all_declared_types - types_present)
        for t in missing_types:
            tier = type_to_tier.get(t)
            violations.append(
                f"Declared type {t!r} (tier {tier}) is not used in the course. "
                f"Track {track.id!r} requires every declared type ≥1 time."
            )

    # (c) capstone tier
    last_mi, last_si, last_type = all_steps[-1]
    capstone_tier = type_to_tier.get(last_type)
    if capstone_tier is None:
        violations.append(
            f"Capstone (Module {last_mi + 1}, Step {last_si + 1}) type {last_type!r} "
            f"is not in track {track.id!r}'s progression."
        )
    elif capstone_tier < track.capstone_required_tier:
        t4_types = track.tier_progression.get(track.capstone_required_tier, [])
        violations.append(
            f"Capstone (Module {last_mi + 1}, Step {last_si + 1}) has type "
            f"{last_type!r} at tier {capstone_tier}, but track {track.id!r} "
            f"requires capstone tier >= {track.capstone_required_tier}. Pick from: {t4_types}."
        )

    return len(violations) == 0, violations


def build_track_progression_brief(track: TrackProgression) -> str:
    """Render the track's progression as a Creator-prompt section.

    This replaces the ad-hoc `subject_guidance` + `CODE-WRITING BACKBONE`
    + `ENG_CAPSTONES`-mention prose with a declarative tier-by-tier list.
    """
    lines = [
        f"=== TRACK: {track.label} ({track.id}) ===",
        track.description,
        "",
        "PEDAGOGICAL PROGRESSION (you MUST traverse all 4 tiers):",
    ]
    for tier in (1, 2, 3, 4):
        label = PEDAGOGICAL_TIER_LABELS.get(tier, f"Tier {tier}")
        types = track.tier_progression.get(tier, [])
        lines.append(f"  T{tier} — {label}")
        for tid in types:
            a = ASSIGNMENT_REGISTRY.get(tid)
            desc = a.description if a else "(unknown)"
            # Keep the one-liner short so the prompt doesn't balloon.
            one_liner = desc.split(".")[0][:120]
            lines.append(f"    - {tid}: {one_liner}")
    lines.append("")
    lines.append("HARD RULES for this course (enforced by _is_complete gate):")
    lines.append(f"  1. Include at least ONE step from EACH tier (T1..T4). No skipping tiers.")
    if track.require_all_declared_types:
        lines.append("  2. EVERY listed assignment_type above must appear at least ONCE in the course. Learning is holistic — learners must touch every shape the track offers.")
    lines.append(f"  3. CAPSTONE (last step of last module) MUST be a T{track.capstone_required_tier} type — the real-skill tier. No exceptions.")
    lines.append("  4. Do NOT use any exercise_type not listed above. Off-track types will be rejected.")
    lines.append("  5. Module and step COUNTS are flexible — pick whatever shape the content needs, as long as the coverage rules above are satisfied. Do not pad with filler to hit a number.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Track PROPOSER — when detect_track can't find a match, the Creator LLM
# proposes a new track on-the-fly using the existing registered tracks as
# few-shot examples (2026-04-22 user directive: "For the ones where we
# don't have this info, build it on the fly using the same data as
# examples to the agent").
# ---------------------------------------------------------------------------


def _render_tracks_as_few_shot_examples(max_examples: int = 5) -> str:
    """Render registered tracks as few-shot examples for the proposer prompt.

    Skips the 'general' fallback (not a useful example) and the track the
    caller is excluding (if any).
    """
    lines: list[str] = []
    examples_shown = 0
    for tid, track in TRACK_REGISTRY.items():
        if tid == "general":
            continue
        if examples_shown >= max_examples:
            break
        examples_shown += 1
        lines.append(f"Track id: {tid}")
        lines.append(f"  label: {track.label}")
        lines.append(f"  description: {track.description}")
        lines.append(f"  match_signals: {track.match_signals[:6]}")
        for tier in (1, 2, 3, 4):
            types = track.tier_progression.get(tier, [])
            lines.append(f"  T{tier}: {types}")
        lines.append(f"  require_all_declared_types: {track.require_all_declared_types}")
        lines.append(f"  capstone_required_tier: {track.capstone_required_tier}")
        lines.append("")
    return "\n".join(lines).strip()


def build_track_proposer_prompt(title: str, description: str = "") -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for the track proposer LLM call.

    The prompt uses existing tracks as few-shot examples + lists every
    known assignment_type so the LLM can only emit valid ids.
    """
    known_assignment_ids = sorted(
        [aid for aid, a in ASSIGNMENT_REGISTRY.items() if aid != "concept"]
    )
    # Always include concept + mcq as T1 options — the LLM shouldn't omit them.
    system_prompt = (
        "You are designing a pedagogical track for a new course on the Skills "
        "Lab v2 platform. A track is a reusable category declaring which "
        "exercise types live at each pedagogical tier (T1 Orient → T2 "
        "Recognize → T3 Reason → T4 Perform), plus detection keywords. "
        "Every course in the track MUST traverse all 4 tiers, and the "
        "CAPSTONE must be a T4 type — the 'real skill under pressure' tier. "
        "Return ONLY valid JSON matching the schema the user message requests. "
        "Use only assignment_type ids from the provided list."
    )
    user_prompt = f"""Propose a pedagogical track for this new course:

TITLE: {title}

DESCRIPTION:
{description or '(none provided)'}

TIER MEANINGS:
- T1 Orient: get started with no friction ('I understand what this is'). Default: [concept, mcq].
- T2 Recognize: surface understanding ('I can spot right vs wrong from a list'). Default: [categorization, ordering].
- T3 Reason: apply under hypothesis ('I can pick the right move when options are given').
- T4 Perform: real skill under pressure ('I can produce the move from scratch when nothing's given'). Capstone comes from here.

AVAILABLE ASSIGNMENT TYPES (use only these ids):
{known_assignment_ids}

CRITICAL: T4 MUST contain at least one of these "real-skill-under-pressure" types:
- adaptive_roleplay (text live chat with hidden-state counterparty)
- voice_mock_interview (live voice interview, browser mic)
- terminal_exercise (learner runs commands on their own machine, BYO-key)
- code_exercise (writes code against hidden tests, starter-fails invariant)
- system_build (ships a real deliverable — deploy / PR / cluster state)
- incident_console (scripted production-outage drill)
- simulator_loop (evolving state-machine simulator)

EXISTING TRACKS (few-shot examples — do not duplicate these; use them as style guides):

{_render_tracks_as_few_shot_examples(max_examples=5)}

Now propose a new track for the course above. Think about:
  1. What IS the real skill the course teaches?
  2. Where does that skill live (learner's terminal? a live conversation? code on disk? cluster state?)
  3. Which T4 type(s) actually deliver that real skill under pressure?
  4. What 5-10 lowercase SUBSTRINGS in future course titles would identify this track?

Return ONLY this JSON object:
{{
  "id": "<snake_case_id_not_matching_any_existing_track>",
  "label": "<short human-friendly title>",
  "description": "<2-3 sentences: who the track is for + what the real skill is + why T4 is what it is>",
  "match_signals": ["<lowercase substring 1>", "<lowercase substring 2>", ...],
  "tier_progression": {{
    "1": ["concept", "mcq"],
    "2": ["categorization", "ordering"],
    "3": ["<pick 2-3 from assignment list>"],
    "4": ["<pick 1-3 real-skill types>"]
  }},
  "capstone_required_tier": 4,
  "require_all_declared_types": true
}}
"""
    return system_prompt, user_prompt


def _validate_llm_track_proposal(
    payload: dict,
) -> tuple[bool, list[str]]:
    """Check an LLM-proposed track for structural + semantic validity.
    Returns (ok, errs). Used to decide whether to accept the proposal or
    fall back to the general track.
    """
    import re as _re
    errs: list[str] = []
    # Required fields
    for k in ("id", "label", "description", "match_signals", "tier_progression"):
        if k not in payload:
            errs.append(f"missing required field {k!r}")
    if errs:
        return False, errs
    # id format
    tid = payload["id"]
    if not isinstance(tid, str) or not _re.match(r"^[a-z][a-z0-9_]{2,48}$", tid):
        errs.append(f"id {tid!r} must be snake_case, 3-49 chars")
    if tid in TRACK_REGISTRY:
        errs.append(f"id {tid!r} collides with existing track (registry has: {list(TRACK_REGISTRY.keys())})")
    # match_signals shape
    if not isinstance(payload["match_signals"], list) or not payload["match_signals"]:
        errs.append("match_signals must be a non-empty list")
    # tier_progression shape
    tp = payload["tier_progression"]
    if not isinstance(tp, dict):
        errs.append("tier_progression must be a dict")
        return False, errs
    # Accept both string and int keys from JSON
    def _tier_list(tier: int) -> list[str]:
        v = tp.get(str(tier), tp.get(tier, []))
        return v if isinstance(v, list) else []
    real_skill_types = {
        "adaptive_roleplay", "voice_mock_interview", "terminal_exercise",
        "code_exercise", "system_build", "incident_console", "simulator_loop",
    }
    for tier in (1, 2, 3, 4):
        types = _tier_list(tier)
        if not types:
            errs.append(f"tier {tier} is empty")
            continue
        for t in types:
            if not isinstance(t, str) or t not in ASSIGNMENT_REGISTRY:
                errs.append(f"tier {tier} references unknown assignment_type {t!r}")
    # T4 must contain a real-skill type
    t4 = _tier_list(4)
    if not any(t in real_skill_types for t in t4):
        errs.append(
            f"T4 must include at least one real-skill-under-pressure type "
            f"(one of: {sorted(real_skill_types)}). Got: {t4}"
        )
    return (len(errs) == 0), errs


def track_from_proposal(payload: dict) -> TrackProgression:
    """Convert a validated LLM payload into a TrackProgression instance.

    Caller MUST have already run _validate_llm_track_proposal and checked ok.
    Does NOT register the track — caller decides (session-only vs. persist).
    """
    def _tier_list(tier: int) -> list[str]:
        v = payload["tier_progression"].get(str(tier), payload["tier_progression"].get(tier, []))
        return list(v) if isinstance(v, list) else []
    return TrackProgression(
        id=payload["id"],
        label=payload["label"],
        description=payload["description"],
        match_signals=[s.lower() for s in payload.get("match_signals", []) if isinstance(s, str)],
        tier_progression={
            1: _tier_list(1), 2: _tier_list(2),
            3: _tier_list(3), 4: _tier_list(4),
        },
        capstone_required_tier=int(payload.get("capstone_required_tier", 4)),
        require_all_declared_types=bool(payload.get("require_all_declared_types", True)),
        min_distinct_types_per_tier=int(payload.get("min_distinct_types_per_tier", 1)),
    )


def propose_track_via_llm(
    title: str,
    description: str,
    llm_call: "Callable[[str, str], dict | None]",
) -> Optional[TrackProgression]:
    """Propose a new track using an injected LLM callable.

    `llm_call(system_prompt, user_prompt)` must return parsed JSON (dict) or
    None on LLM failure. Kept as an injected dependency so ontology.py has
    no direct dependency on any LLM client — callers wire in their own
    (`_llm_json_call` in main.py, a mock in tests).

    Returns a validated TrackProgression, or None if the LLM failed or the
    proposal didn't validate. Does NOT register the track — caller decides.
    """
    system_prompt, user_prompt = build_track_proposer_prompt(title, description)
    try:
        payload = llm_call(system_prompt, user_prompt)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    ok, _errs = _validate_llm_track_proposal(payload)
    if not ok:
        return None
    try:
        return track_from_proposal(payload)
    except Exception:
        return None


def detect_or_propose_track(
    title: str,
    description: str = "",
    *,
    explicit_track_id: Optional[str] = None,
    llm_call: "Callable[[str, str], dict | None] | None" = None,
    allow_propose: bool = True,
    min_signal_score_for_accept: int = 1,
) -> tuple[TrackProgression, str]:
    """One-stop track resolution.

    Policy:
      1. If `explicit_track_id` given AND registered → use it (source="explicit")
      2. Else detect_track → if the match is better than general fallback, use it (source="signal")
      3. Else if `allow_propose` AND `llm_call` provided → propose via LLM
         (source="proposed"). If proposal validates, return it; otherwise
         fall through to (4).
      4. Use the `general` fallback track (source="fallback").

    Returns (track, source) where source ∈ {"explicit", "signal", "proposed", "fallback"}
    so callers can log/telemetry.

    Note: this function does NOT register a proposed track. Caller may
    choose to register it (e.g. after a course ships successfully).
    """
    if explicit_track_id and explicit_track_id in TRACK_REGISTRY:
        return TRACK_REGISTRY[explicit_track_id], "explicit"

    # Score-based detection — replicates detect_track()'s logic to know if
    # we hit a real match vs fell to general.
    blob = _lowered_blob(title, description)
    best_track: Optional[TrackProgression] = None
    best_score = -1
    for t in TRACK_REGISTRY.values():
        if t.id == "general":
            continue
        score = sum(1 for sig in t.match_signals if sig.lower() in blob)
        if score > best_score:
            best_track, best_score = t, score
    if best_track is not None and best_score >= min_signal_score_for_accept:
        return best_track, "signal"

    if allow_propose and llm_call is not None:
        proposed = propose_track_via_llm(title, description, llm_call)
        if proposed is not None:
            return proposed, "proposed"

    return TRACK_REGISTRY["general"], "fallback"


# ---------------------------------------------------------------------------
# Seed tracks — the minimum set to cover current v8 course directions.
# Each track = one register_track(...) call. Add new tracks by appending.
# ---------------------------------------------------------------------------

register_track(TrackProgression(
    id="pm_strategy",
    label="Product Management + Strategy",
    description=(
        "AI-enablement or craft courses for Product Managers and adjacent "
        "strategy roles (PMM, BizOps, Chief of Staff). Primary skill = "
        "rigorous decision-making under pressure with real stakeholders. "
        "Capstone = generate-under-pressure defense in a live chat, not a "
        "multiple-choice decision tree."
    ),
    match_signals=[
        "product manager", "product management", "for pms", " pm ", "pm:",
        "chief of staff", "product strategy", "strategy for product",
        "pmm", "product marketing", "bizops", "business operations",
        "stakeholder management", "roadmap", "prioritization",
    ],
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["scenario_branch", "sjt"],
        4: ["adaptive_roleplay", "voice_mock_interview"],
    },
    capstone_required_tier=4,
    require_all_declared_types=True,
))

register_track(TrackProgression(
    id="cli_tool_agent",
    label="CLI Tool / Agent Teaching",
    description=(
        "Courses teaching mastery of a command-line or agent tool the "
        "learner runs on their OWN machine (Claude Code, kubectl, gh CLI, "
        "terraform, docker CLI, aws CLI). Real skill lives in the learner's "
        "terminal, not in our sandbox. Capstone = terminal_exercise "
        "(BYO-execution, LLM-rubric on pasted output) or system_build "
        "(ship a real artifact like an MCP server)."
    ),
    match_signals=[
        "claude code", "claude cli", "kubectl", "docker cli", "docker command",
        "git workflow", "gh cli", "github cli", "aws cli", "gcloud cli",
        "az cli", "terraform cli", "helm cli", "shell scripting workflow",
        "command line productivity",
    ],
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["code_review", "fill_in_blank"],
        4: ["terminal_exercise", "system_build"],
    },
    capstone_required_tier=4,
    require_all_declared_types=True,
))

register_track(TrackProgression(
    id="engineering_mastery",
    label="Language / Algorithm Mastery",
    description=(
        "Hands-on coding courses where the real skill is writing production-"
        "quality code in a specific language (Go, TypeScript, Rust, Java) "
        "or against a specific algorithmic challenge. Capstone = "
        "code_exercise with hidden tests + starter-fails invariant, or "
        "system_build (ship a deployable artifact)."
    ),
    # 2026-04-23 v8.1: signal list broadened. Original list had "java programming"
    # but course titles like "Modern Java:" / "Java for Backend" didn't contain
    # that literal phrase → fell to `general` track. New list uses space-padded
    # language tokens (" java " / "java:" / "java for") so common title patterns
    # match without false-positiving on "go to market" / "java script". For
    # titles that still miss, detect_or_propose_track's LLM fallback catches it.
    match_signals=[
        # Go
        "go basics", "go programming", " go:", " go for ", "golang",
        # TypeScript
        "typescript", " ts ", " ts:",
        # Rust
        "rust programming", " rust ", "rust:", "systems programming",
        # Java
        "java programming", " java ", "java:", "java for", "modern java",
        # Python
        "python essentials", " python ", "python:", "python for",
        # Kotlin
        " kotlin ", "kotlin:", "kotlin for",
        # Swift
        " swift ", "swift:", "swift programming",
        # C++ / C#
        " c++ ", "c++:", " c# ", "c#:",
        # Ruby
        " ruby ", "ruby:", "ruby programming",
        # Scala
        " scala ", "scala:",
        # Algorithm-style
        "data structures", "algorithms", "ds&a", "leetcode",
        "competitive programming",
    ],
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["code_review", "parsons", "fill_in_blank"],
        4: ["code_exercise", "system_build"],
    },
    capstone_required_tier=4,
    require_all_declared_types=True,
))

register_track(TrackProgression(
    id="framework_build",
    label="Framework Build (FastAPI / React / Spring Boot)",
    description=(
        "Courses teaching a specific framework where the real skill = ship "
        "a running service / app. Builds on engineering_mastery with "
        "deployment + integration. Capstone = system_build (deploy to "
        "Vercel / Railway / AWS) or a ladder of code_exercise steps that "
        "build to a working service."
    ),
    match_signals=[
        "fastapi", "flask", "django", "react", "nextjs", "next.js", "vue",
        "spring boot", "express", "rails", "nestjs",
    ],
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["code_review", "code_exercise"],
        4: ["system_build"],
    },
    capstone_required_tier=4,
    require_all_declared_types=True,
))

register_track(TrackProgression(
    id="soft_skills",
    label="Soft Skills / Leadership / Communication",
    description=(
        "Non-engineering courses on communication, negotiation, leadership, "
        "hiring, difficult conversations. Real skill = navigate a hostile "
        "or high-stakes interaction live. Capstone = adaptive_roleplay or "
        "voice_mock_interview where the counterparty adapts to learner "
        "moves."
    ),
    match_signals=[
        "negotiation", "difficult conversation", "leadership", "hiring",
        "interview", "communication skills", "executive presence", "feedback",
        "managing up", "managing down", "crisis communication", "sales coaching",
    ],
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["scenario_branch", "sjt"],
        4: ["adaptive_roleplay", "voice_mock_interview"],
    },
    capstone_required_tier=4,
    require_all_declared_types=True,
))

register_track(TrackProgression(
    id="ops_sre_security",
    label="Ops / SRE / Security",
    description=(
        "Incident-response, production-ops, and security courses where the "
        "real skill = triage under pressure with an evolving system state. "
        "Capstone = incident_console (scripted drill) or simulator_loop "
        "(evolving state machine)."
    ),
    match_signals=[
        "sre", "site reliability", "incident response", "oncall", "on-call",
        "production ops", "security operations", "soc", "threat hunt",
        "kubernetes", "k8s ops", "observability",
    ],
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["scenario_branch", "code_review"],
        4: ["incident_console", "simulator_loop", "system_build"],
    },
    capstone_required_tier=4,
    require_all_declared_types=True,
))

register_track(TrackProgression(
    id="general",
    label="General (fallback)",
    description=(
        "Fallback track for courses that don't match any specialized track. "
        "Broad exercise mix; capstone = a meaty scenario_branch or "
        "adaptive_roleplay. Prefer to register a specific track if this "
        "course is part of a growing domain."
    ),
    match_signals=[],  # never matched by signal; only fallback
    tier_progression={
        1: ["concept", "mcq"],
        2: ["categorization", "ordering"],
        3: ["scenario_branch", "sjt"],
        4: ["adaptive_roleplay", "system_build"],
    },
    capstone_required_tier=4,
    require_all_declared_types=False,  # general track is permissive
))


__all__ = [
    # Dataclasses
    "SlideType", "AssignmentType", "CourseMode", "TechDomain", "Runtime",
    "TrackProgression",
    # Registries (mutable — extensions can add entries)
    "SLIDE_REGISTRY", "ASSIGNMENT_REGISTRY", "COURSE_MODE_REGISTRY",
    "TECH_DOMAIN_REGISTRY", "RUNTIME_REGISTRY", "TRACK_REGISTRY",
    # Registration helpers
    "register_slide", "register_assignment", "register_course_mode",
    "register_tech_domain", "register_runtime", "bind_runtime_handler",
    "register_track",
    # Prompt assembly
    "build_creator_ontology_brief", "describe_assignment_for_prompt",
    "describe_domain_for_prompt", "build_track_progression_brief",
    # Gate helpers
    "validate_step_against_ontology", "is_code_language", "CODE_LANGUAGES",
    "detect_track", "get_track", "validate_outline_against_track",
    "tier_of_type_in_track", "PEDAGOGICAL_TIER_LABELS",
    # LLM-on-the-fly track proposer
    "propose_track_via_llm", "detect_or_propose_track",
    "build_track_proposer_prompt", "_validate_llm_track_proposal",
    "track_from_proposal",
]
