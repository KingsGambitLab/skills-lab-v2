# Creator Flow Inventory — 2026-04-27

## 1. Backend Creator Endpoints (`/api/creator/*`)

### Core Workflow
- **POST `/api/creator/upload`** — Multipart file upload (Python/JS/Go starter code, requirements.txt, test files)
- **POST `/api/creator/fetch_url`** — Fetch course materials from external URL
- **POST `/api/creator/start`** — Kicks off question generation; returns `session_id` for polling
- **POST `/api/creator/refine`** — Creator submits answers to questions; refines outline (async, polled)
- **POST `/api/creator/generate`** — Background task: generates full course (modules + steps + content)
- **GET `/api/creator/session/{session_id}/status`** — Poll for refined outline + generation progress
- **GET `/api/creator/progress/{session_id}`** — Fetch activity feed (per-step LLM progress)
- **GET `/api/creator/sessions`** — List all creator sessions

### Per-Step Regeneration (Feature: 2026-04-20)
- **POST `/api/courses/{course_id}/steps/{step_id}/regenerate`** — Regenerate single step with optional feedback; preserves prior course context
- **POST `/api/courses/{course_id}/modules/{module_id}/regenerate`** — Regenerate all steps in a module sequentially

### LLM-Touching Helpers
- **`_llm_generate_step_content()`** — Core step generation (code, content, validation); handles Docker invariant validation & retry logic
- **`_llm_refined_outline()`** — Refines course outline based on creator's answers to questions
- **`_runtime_deps_brief(language)`** — Generates brief runtime-dependency summary per language
- **`_is_complete()`** — Validates step completeness (checks for missing fields, validation stubs)
- **Retry feedback loop** — If 2 consecutive Stage-2 attempts fail, scaffold is regenerated (Opus #8 invariant)

---

## 2. Ontology & Registry (`ontology.py`)

**Five-layer declarative system** (no free-form prompt editing):

| Layer | Registry | Elements |
|-------|----------|----------|
| **Slides** | `SLIDE_REGISTRY` | concept_card, diagram_flow, table_compare, checklist, code_read, mini_demo, … |
| **Assignments** | `ASSIGNMENT_REGISTRY` | code_exercise, code_review, code_read, system_build, mcq, … |
| **Course Modes** | `COURSE_MODE_REGISTRY` | linear, case_library, simulator_workday, drill_only, certification_track |
| **Tech Domains** | `TECH_DOMAIN_REGISTRY` | backend_python, data_sql, devops_k8s, … (with stacks + fixtures) |
| **Runtimes** | `RUNTIME_REGISTRY` | python_sandbox, docker, github_actions, vscode, terminal, sql_sqlite, yaml_schema, webcontainer |

**Grade Primitives** — assignments declare which grading primitives they use: `compile`, `hidden_tests`, `property_test`, `lint`, `must_contain`, `bug_lines`, `state_assertion`, `endpoint_probe`, `gha_workflow_check`, `artifact_flag`, `llm_rubric`, `benchmark_score`.

**Extensibility** — new types registered via `register_slide()`, `register_assignment()`, etc. in external modules; Creator prompt assembler picks them up automatically on next `/api/creator/start`.

---

## 3. Course-Asset Registry (`course_assets.py`, `course_asset_backfill.py`)

**Purpose** — Decouple course content from hardcoded GitHub repos / MCP servers. One registry entry per course.

**Structure** (`CourseAsset`):
- `slug` — short unique ID (e.g., "aie")
- `course_repo` — GitHub URL (e.g., `github.com/skills-lab-demos/<slug>-course-repo`)
- `module_branches` — dict mapping module slug → branch name (e.g., `"module-0-preflight"`)
- `mcp_servers` — list of pre-built MCP servers (name, repo URL, tools declared)
- `gha_workflow_file` — workflow file path (default: `lab-grade.yml`)

**Branch Convention** — all courses follow `module-<N>-<short_slug>` pattern across modules.

**Backfill Engine** — `backfill_course()` fills missing terminal_exercise fields (bootstrap_command, dependencies, paste_slots, step_slug, step_task) from registry post-generation.

---

## 4. Creator Dashboard Frontend (`frontend/index.html`)

**Wizard Flow** (4 steps):

1. **Step 1: Course Setup** — Upload starter code (multi-file) OR fetch from URL; set course title/subject/description
2. **Step 2: Answer Questions** — Creator submits answers (text inputs + choice pills for depth/framing); triggers refine
3. **Step 3: Review & Refine** — Display refined outline; "Refine Again" button re-runs LLM; "Generate Course" button kicks off background generation
4. **Step 4: Done** — Shows generated course link + success banner

**Publish / Review UI Status**:
- **NO dedicated "Publish" button today** — course auto-publishes on successful generation
- **Automated Reviewer Banner** (Step 4) — "Automated learner is reviewing your course"; polls `GET /api/courses/{courseId}/review_status` every 5s
- **Per-Step Regenerate Modal** — Creators can narrow-scope regen via feedback overlay (opens on Step-4 step card)
- **Edit Modal** — Direct field edit capability (no AI, post-generation polish)

---

## 5. Reviewer Harness (`backend/harness/`)

**Four agent shims** (clean-slate invariant: no answer keys, no backend internals leaked):

| Agent | Role | Invocation |
|-------|------|-----------|
| **beginner_agent** | Walks course as RL-style learner; produces streaming markdown artifact | Manual: `build_prompt()` generates prompt → hand to Agent tool; currently NOT wired into pipeline |
| **cli_walk_agent** | CLI walkthrough (terminal-focused courses) | NOT described in codebase; exists but invocation unclear |
| **vscode_walk_agent** | VS Code IDE walkthrough | NOT described in codebase; exists but invocation unclear |
| **domain_expert** | Domain validation (code correctness, terminology, depth) | NOT described in codebase; exists but invocation unclear |

**Current Status**: Beginner agent is the only explicitly wired gate (Step 1 per CLAUDE.md); others exist but are invoked manually or not yet integrated into the auto-review pipeline.

---

## 6. Queued / TODO Features (from CLAUDE.md)

| Item | Status | Details |
|------|--------|---------|
| **Creator deep-refine UI** | Queued | Let creators SEE + edit refined outline (add/remove/rename modules) before generate. Closes "M5 team-Claude silently dropped" class of bugs. |
| **Frontend Widget CSP Compliance** | Queued | Migrate `_rewriteOnclicksToDataActions` to explicit `data-action` attributes; currently uses `Function(...)`. |
| **nav-router state-bleed audit** | Deferred (production-ready) | Every step handler using `index` should capture `step.id` at render time (affects categorization, nav-race bugs). |
| **Docker-image infra** | Queued (v7) | Per-language Docker image management (currently stub). |
| **Language-config mergers** | TODO | JS/TS `_merge_package_json`, Go `_merge_go_mod`, Rust `_merge_cargo_toml`, Java/Maven `_merge_pom_xml` — all marked TODO. |
| **Python fallback removal** | Queued (v7.1) | Drop language fallback logic; all-runtime-specific. |

**NOT IN SCOPE**: Publish button, version history, live-generation-timeline, or explicit multi-agent orchestration in the Creator pipeline.
