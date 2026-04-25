"""
Pydantic v2 schemas for the Skills Lab API.
"""

from datetime import datetime

from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class CourseOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    subtitle: str | None = None
    icon: str | None = None
    description: str | None = None
    course_type: str
    level: str | None = None
    tags: list[str] | None = None
    estimated_time: str | None = None
    module_count: int = 0
    created_at: datetime


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------

class ModuleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    course_id: str
    position: int
    title: str
    subtitle: str | None = None
    icon: str | None = None
    estimated_time: str | None = None
    objectives: list[str] | None = None
    step_count: int = 0


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------

class StepOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    module_id: int
    position: int
    title: str
    step_type: str
    exercise_type: str | None = None
    # Surface-aware split (Phase 2 v8.7 2026-04-25). 'web' | 'terminal' | None.
    # Browser frontend renders a "this step is terminal-native" panel when
    # 'terminal'; CLI prints "open in browser" when 'web'. NULL = legacy
    # step (treated as 'web' by both consumers).
    learner_surface: str | None = None
    content: str | None = None
    code: str | None = None
    expected_output: str | None = None
    validation: dict | None = None
    demo_data: dict | None = None


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------

class CodeExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    # D.2 (2026-04-21): optional language-specific fixtures the frontend can
    # pass for ad-hoc runs. SQL exercises use schema_setup (DDL) + seed_rows
    # ([{"table": str, "rows": [dict]}]) to prime an in-memory SQLite DB.
    # YAML exercises use `yaml_schema` for JSON-schema validation.
    # When not provided, the runtime pulls these from step.demo_data at grade time.
    # (Renamed from `schema` on 2026-04-21 to avoid shadowing Pydantic BaseModel.schema.)
    schema_setup: str | None = None
    seed_rows: list | None = None
    yaml_schema: dict | None = None
    # F26 (2026-04-21): capstone scaffold primitives. When the exercise
    # references external filesystem state (os.walk / Path().glob / open), the
    # Creator emits `demo_data.starter_files` ([{"path": str, "contents": str}])
    # which the sandbox materializes into a tempdir and injects under the Python
    # variable named by `repo_path_var` (default "repo_path"). Without these,
    # os.walk(repo_path) walks nothing and the exercise is unsolvable.
    starter_files: list | None = None
    repo_path_var: str | None = None


class CodeExecuteResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Exercise submission
# ---------------------------------------------------------------------------

class ExerciseSubmitRequest(BaseModel):
    step_id: int
    response_data: dict
    # Client-tracked attempt counter per step. 1 = first submit. The validator
    # uses this to gate the answer-key reveal: on wrong submissions with
    # attempt_number <= 2 we strip item_results/correct_answer fields and
    # return a concept-level hint instead, so learners get a real retry loop
    # before the solution spoils the exercise. See _gate_answer_key() in main.py.
    # Shipped 2026-04-20 after Riley/Sam/Kiran agent reviews surfaced that
    # every wrong attempt across ordering/categorization/code_review spilled
    # the full answer key on attempt #1, killing the retry loop.
    attempt_number: int = 1


class ExerciseSubmitResponse(BaseModel):
    correct: bool
    score: float = Field(ge=0.0, le=1.0)
    feedback: str
    dimensions: dict | None = None
    # Post-submission answer key + per-item feedback — returned to the frontend so it can
    # render teaching feedback (which items were right/wrong, what the correct answer was,
    # and why). This is safe to send AFTER the learner has submitted; it replaces the prior
    # pattern where the frontend pre-loaded these fields at render time (leaking the answer).
    item_results: list[dict] | None = None   # per-item: {id, correct, correct_position/category/rank, explanation}
    correct_answer: dict | list | None = None  # canonical correct answer for the exercise
    explanations: list[str] | None = None     # additional teaching notes


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

class StepCompletionOut(BaseModel):
    step_id: int
    completed: bool
    score: float | None = None
    completed_at: datetime | None = None


class ModuleCompletionOut(BaseModel):
    module_id: int
    title: str
    steps_total: int
    steps_completed: int
    completion_pct: float = Field(ge=0.0, le=100.0)


class ProgressOut(BaseModel):
    user_id: str
    course_id: str
    steps: list[StepCompletionOut] = []
    modules: list[ModuleCompletionOut] = []
    course_completion_pct: float = Field(ge=0.0, le=100.0, default=0.0)


# ---------------------------------------------------------------------------
# Certificate
# ---------------------------------------------------------------------------

class CertificateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: str
    course_id: str
    issued_at: datetime
    expires_at: datetime | None = None
    score: float
    dimensions: dict | None = None


# ---------------------------------------------------------------------------
# Course Creator
# ---------------------------------------------------------------------------

class CreatorStartRequest(BaseModel):
    # Min length of 3 so titles like "X" surface a clean 422 at the START gate instead of
    # silently producing an incoherent course. (Chaos C1 found input validation gaps.)
    title: str = Field(min_length=3, max_length=200)
    # Bumped to 50000 chars 2026-04-21 (was 18000). The handler enforces
    # combined len(description) + len(source_material) <= 50000 AFTER Pydantic
    # accepts, so no silent truncation anywhere downstream.
    description: str = Field(min_length=10, max_length=50000)
    source_material: str | None = Field(default=None, max_length=50000)
    # Enum-validated so course_type="self_paced" or other typos return 422 at the START gate,
    # not an unstructured 500 at generate time (Chaos C1 finding).
    course_type: Literal["technical", "case_study", "compliance"]
    # Optional Creator-chosen complexity. If None, the Creator LLM decides from
    # the description; its inference becomes the course's level. Accepted values:
    # "beginner", "intermediate", "advanced".
    level: str | None = None
    # Course-shape mode. `linear` = the classic 3-5 module × 3-5 step sequence.
    # `case_library` = Emergent-style grid of N numbered case drills + 1 capstone
    # ("The Full Cascade"), each short (3-20 min), difficulty-tiered, filterable
    # by discipline / failure-mode / stack-layer. Use case_library for
    # operational / investigative roles (SRE, SOC, support eng, data analyst
    # triage, legal redline library, PM launch drills). Use linear for foundational
    # teaching-heavy onboarding (concept → exercise → reflection).
    course_mode: str | None = None   # "linear" | "case_library"
    # Creator-chosen workspace archetype for case_library courses. Picks the
    # pre-baked multi-pane simulator shell. One of: ops_infra, data_analytics,
    # security_soc, legal_contract, pm_strategy, design_ux, sales_revops,
    # finance_ledger, people_hr, executive. Only meaningful when course_mode
    # is "case_library".
    archetype: str | None = None


class CreatorQuestion(BaseModel):
    id: str
    question: str
    type: str = "text"  # "text" or "choice"
    options: list[str] | None = None


class CreatorModuleSummary(BaseModel):
    title: str
    description: str


class CreatorOutline(BaseModel):
    modules: list[CreatorModuleSummary]


class CreatorStartResponse(BaseModel):
    session_id: str
    questions: list[CreatorQuestion]
    initial_outline: CreatorOutline


class CreatorAnswerItem(BaseModel):
    question_id: str
    answer: str


class CreatorRefineRequest(BaseModel):
    session_id: str
    answers: list[CreatorAnswerItem]
    feedback: str | None = None


class CreatorStepOutline(BaseModel):
    title: str
    exercise_type: str
    description: str


class CreatorModuleOutline(BaseModel):
    title: str
    position: int = 0
    objectives: list[str]
    steps: list[CreatorStepOutline]


class CreatorRefinedOutline(BaseModel):
    modules: list[CreatorModuleOutline]


class CreatorFollowUp(BaseModel):
    id: str
    question: str


class CreatorRefineResponse(BaseModel):
    outline: CreatorRefinedOutline
    follow_up_questions: list[CreatorFollowUp] | None = None
    ready_to_generate: bool = False


class CreatorGenerateRequest(BaseModel):
    session_id: str
    outline: CreatorRefinedOutline
    creator_notes: str | None = None


# v8.6 (2026-04-24) PYDANTIC PRE-GATE — hard schema for code_exercise JSON
# emitted by Sonnet. Validates types BEFORE the 5-10s Docker invariant runs,
# so type errors (e.g. `hidden_tests=["test1","test2"]` list instead of single
# string; `language={"name":"python"}` dict instead of string) are caught in
# ~1ms instead of wasting a Docker cycle + producing an inscrutable traceback.
#
# Design intent (buddy-Opus consult #9): de-prioritized vs resilience items
# but still ship — it tightens the Sonnet→grader contract + gives the retry
# loop a clearer rejection message than ontology gate's "required field
# missing" (which doesn't distinguish missing from mistyped).
#
# `extra: allow` on every model — we constrain the fields we CARE about, but
# Creator + learner paths carry additional fields (_internal_scaffold, etc.)
# that should pass through transparently.

class CodeExerciseValidationModel(BaseModel):
    # hidden_tests is the primary grade surface — must be a real test file
    # (>=50 chars rules out "pass" or empty string) and a single string (the
    # LLM sometimes emits a list of test snippets, which breaks the runner).
    hidden_tests: str = Field(min_length=50)
    # solution_code must be a functional impl — >=20 chars rules out empty /
    # placeholder comments.
    solution_code: str = Field(min_length=20)
    # Optional fields — present in most generations but not required.
    hint: str | None = None
    requirements: str | None = None
    must_contain: list[str] | None = None
    model_config = {"extra": "allow"}


class CodeExerciseDemoDataModel(BaseModel):
    # Language string — picks the Docker runner image + test framework.
    # The LLM sometimes emits a dict here; this forces the error to surface.
    language: str = Field(min_length=1)
    model_config = {"extra": "allow"}


class CodeExerciseAssignmentModel(BaseModel):
    # Briefing HTML — rendered as the step's concept content.
    content: str = Field(min_length=50)
    # Starter code — what the learner edits.
    code: str = Field(min_length=20)
    validation: CodeExerciseValidationModel
    demo_data: CodeExerciseDemoDataModel
    model_config = {"extra": "allow"}


class CreatorGenerateResponse(BaseModel):
    course_id: str
    status: str = "generated"
    course: CourseOut
    # v8.6 (2026-04-24) DEAD-LETTER — steps whose retry loop exhausted but were
    # persisted with quality_flag="needs_author_review" instead of rolling back
    # the whole course. Creator UI reads this to show "N steps need your review"
    # with per-step regenerate buttons. Empty list = course is clean.
    # Each entry: {module_title, step_title, exercise_type, failure_reason, retry_tail}.
    needs_review_steps: list[dict] | None = None


class CreatorSessionOut(BaseModel):
    session_id: str
    title: str
    course_type: str
    status: str  # "started", "refined", "generated"
    created_at: datetime
