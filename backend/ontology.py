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
    description="Generic tick-based simulation primitive.",
    grade_primitives=["sim_win_condition"],
    grade_weights={"sim_win_condition": 1.0},
    required_demo_data=["initial_state"],
    required_validation=["win_conditions"],
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

__all__ = [
    # Dataclasses
    "SlideType", "AssignmentType", "CourseMode", "TechDomain", "Runtime",
    # Registries (mutable — extensions can add entries)
    "SLIDE_REGISTRY", "ASSIGNMENT_REGISTRY", "COURSE_MODE_REGISTRY",
    "TECH_DOMAIN_REGISTRY", "RUNTIME_REGISTRY",
    # Registration helpers
    "register_slide", "register_assignment", "register_course_mode",
    "register_tech_domain", "register_runtime", "bind_runtime_handler",
    # Prompt assembly
    "build_creator_ontology_brief", "describe_assignment_for_prompt",
    "describe_domain_for_prompt",
    # Gate helpers
    "validate_step_against_ontology", "is_code_language", "CODE_LANGUAGES",
]
