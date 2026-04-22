# Creator-Integration Plan — Ontology Layer + Grading Overhaul

**Date**: 2026-04-21
**Inputs synthesized**:
- `/reviews/swe_assignment_review_2026-04-21.md` (27 exercises eval'd, 3 systemic bugs)
- `/reviews/creative_capstone_research_2026-04-21.md` (11 novel formats, 4 refinement bundles)
- User directive (2026-04-21): "add an ontology layer for course creator. All types of slides, assignments, courses... a master list that supports majority of tech courses to begin with."
- Already shipped: F26 (`starter_files` / `starter_repo` scaffold primitives — backend done). F24 (`gha_workflow_check` — Creator prompt + CLAUDE.md docs done; backend/frontend pending).

---

## 1. Framing — what the two reviews actually say

The SWE review's one-line summary: **"The content quality is not the problem; the grading infrastructure is."** Briefings read well, scenarios are vivid, scaffolds are production-flavored — but:

- `code_exercise` grading caps at 60% because `must_contain` × `expected_output` can't distinguish real code from token-spam (step 349: real solution and `print()`-hack both score 60%).
- **5 of 5 `system_build` capstones are 0% reachable** — `endpoint_check.url` is always a placeholder, empty string, or unreachable.
- **40% of Python exercises fail on first import** (bcrypt, confluent_kafka, psycopg2, opentelemetry not in sandbox).
- Parsons is globally broken (payload key mismatch, 0% on every attempt).

The research agent's finding: the fix is **not more prompt tightening**. It's a structural re-shape of how grading signals compose + where content conventions live. And that re-shape is exactly where the ontology layer belongs — it becomes the data-not-prose source of truth the Creator builds from.

---

## 2. The ontology — a four-layer registry

Today the Creator is guided by ~3000 lines of prose prompts in `backend/main.py` that list 16 exercise types, 10 workspace archetypes, and N rules per type. **None of that is machine-readable.** The Creator LLM picks from menus it rebuilds from prose every generation. That's why:
- Plurality drift (F19) happens — categories don't match mapping values.
- Capstone-genre leaks happen — a Docker course emits a UX strategy doc.
- `must_contain` tokens reference internal-test magic numbers — nobody checks the token set is sane.
- New exercise types require a 10-place prompt edit.

**The ontology fix**: one registry file (`backend/ontology.py`) that declares every Creator decision as structured data. The Creator prompt is then assembled FROM the registry. Adding a new slide type = one registry entry, not a scattershot prose edit.

### Layer 1 — Slide ontology (content-card shapes)

Every `step.content` field gets a `slide_type` tag. The Creator picks from a closed menu; each type has a canonical HTML skeleton the runtime renders. No more free-form HTML generation per step.

| slide_type | Shape | When to use |
|---|---|---|
| `concept_card` | 1-3 styled cards, heading + body + optional code inline | Explain a single concept |
| `diagram_flow` | SVG node-and-arrow graph, CSS-animated current-step highlight | Pipelines / state machines / request flow |
| `diagram_architecture` | SVG box layout (cluster / service / DB / queue) | System shape |
| `table_compare` | 2-4 column comparison table | When-to-use-X-vs-Y |
| `timeline` | Horizontal step bar with milestones | Sequences / roadmaps |
| `checklist` | Styled `<ul>` with verbatim-phrase items | "Before you ship" lists |
| `code_read` | Syntax-highlighted read-only snippet + annotations | Walkthroughs |
| `callout_warn` | Red-border box with icon | Common pitfalls |
| `callout_tip` | Teal-border box | Non-obvious tricks |
| `mini_demo` | Small scripted widget (button → see effect) | "Try it" moments |
| `quote_source` | Block quote + citation | Grounding against canonical doc |
| `stat_highlight` | Big-number card | "47% of outages start with…" |
| `domain_legend` | Key-value card listing valid enum values | Fixes Maya's fill-in-blank-with-enum problem |

Creator picks 1-3 slide_types per step (per exercise_type's guidelines). Runtime renders from templates. **Directly fixes**: the recurring dark-theme violations, the text-log-instead-of-SVG bug, the raw-`[ ]`-markdown bug. All three recurring bugs stop being possible because free-form HTML is replaced with templated rendering.

### Layer 2 — Assignment ontology (the 16 types, re-axised)

Current state: 16 exercise types enumerated in CLAUDE.md — but they mix three orthogonal axes (the research agent surfaced this). Re-factor into a triple every exercise declares:

```python
# backend/ontology.py
ASSIGNMENT_REGISTRY = {
    "code_exercise": Assignment(
        interaction_mode="interactive",
        grade_primitives=["compile", "behavior_test", "property_test", "lint", "llm_rubric", "must_contain"],
        default_grade_weights={"compile": 0.10, "behavior_test": 0.50, "property_test": 0.20,
                                "lint": 0.10, "llm_rubric": 0.10},
        reality_score="simulated",
        sandbox_requirements=["python_sandbox"],
        fixture_requirements_re=r"\bos\.walk\(|\bPath\(|\bopen\(",  # F26 trigger
    ),
    "cluster_state_check": Assignment(  # NEW (research Proposal 1)
        interaction_mode="simulation",
        grade_primitives=["state_assertion"],
        reality_score="real",
        sandbox_requirements=["ephemeral_k3d", "assertion_runner"],
    ),
    "github_classroom_capstone": Assignment(  # NEW (research Proposal 6, extends F24)
        interaction_mode="real_workflow",
        grade_primitives=["gha_workflow_check", "ai_review_resolved", "merge_clean"],
        reality_score="real",
        sandbox_requirements=["github_oauth", "skills_lab_demos_org"],
    ),
    # ... 20+ entries
}
```

Every generated step validates against the registry: if `grade_primitives` is empty, `_is_complete()` rejects. If `sandbox_requirements` aren't satisfied by the current deployment, the Creator picks a different assignment type. **Directly fixes**: the 5-of-5 capstone URL failures (can't emit `system_build` without at least one real grade primitive), plurality drift in categorization (registry enforces token-set consistency).

### Layer 3 — Course-mode ontology

Today: prose description of `linear` vs `case_library` with an implicit `simulator_workday` in the north-star. Make it a closed enum with per-mode contracts:

| course_mode | Module shape | Required primitives |
|---|---|---|
| `linear` | 3-5 modules × 3-5 steps | 1 capstone at the end |
| `case_library` | N numbered cases (3-20 min each) + 1 "Full Cascade" capstone | Case IDs, difficulty tiers, stack-layer tags |
| `simulator_workday` | 1-2 workspace shells + case pack | Archetype, pane states, Slack-prompt schedule |
| `certification_track` | 10-15 drills + proctored final | Timed mode, no hints |
| `drill_only` | Flat list of 10-20 short drills, no capstone | Per-drill target minute |

Creator's step 1 picks `course_mode` explicitly (today it's inferred). Each mode has a module-shape validator.

### Layer 4 — Domain ontology (the master list for tech courses)

**This is the "master list that supports majority of tech courses" you asked for.** 12-domain taxonomy, each with canonical stack, typical assignment recipes, sandbox requirements, fixture library pointer:

| Domain | Canonical stack | Primary assignment recipes | Sandbox / runtime |
|---|---|---|---|
| **backend_python** | FastAPI / Flask / Django, async + sync | code_exercise (async/sync), code_review (security/perf), system_build (deploy to Railway), live_dev_workspace | python_sandbox + WebContainer (Pyodide) |
| **backend_node** | Express / NestJS / Fastify, TS | code_exercise, code_review, live_dev_workspace, github_classroom_capstone | WebContainer |
| **backend_go** | net/http / gin / chi | code_exercise, code_review, cluster_state_check | WebContainer + docker-in-docker |
| **frontend_react** | React / Next.js / Vite | pixel_diff_capstone, live_dev_workspace, code_review | WebContainer |
| **data_sql** | Postgres / MySQL, migrations, EXPLAIN | code_exercise (SQL), code_review (migrations), cluster_state_check (DB state) | in-memory SQLite + ephemeral Postgres |
| **data_ml** | Python, NumPy, Pandas, scikit-learn, PyTorch | benchmark_arena, property_test_grader, code_exercise | Pyodide + held-out eval server |
| **data_analytics** | dbt / Looker / Snowflake | SQL exercises, scenario_branch, code_review (dbt models) | in-memory SQLite + dbt CLI mock |
| **devops_k8s** | Helm / kubectl / ArgoCD / Terraform | cluster_state_check, github_classroom_capstone (GHA), code_exercise (YAML) | ephemeral k3d |
| **devops_docker** | Dockerfile / compose / multi-stage | code_exercise (dockerfile lint), github_classroom_capstone | dockerfile linter + GHA |
| **ops_sre** | Grafana / Datadog / PagerDuty | incident_console, chaos_hypothesis_drill, adaptive_roleplay | simulated console + scripted log stream |
| **security_appsec** | OWASP / CWE / semgrep | artifact_flag_capstone, code_review (CVE), scenario_branch | ephemeral target + flag checker |
| **security_soc** | Splunk / SIEM / IOC | incident_console (SOC queue), code_review, artifact_flag_capstone | scripted SIEM |
| **ai_dev_tools** | Claude Code / Cursor / Copilot | code_exercise, system_build, mentored_iteration | python_sandbox + starter_files (F26) |
| **observability** | OpenTelemetry / Jaeger / Prometheus | code_exercise (instrumentation), artifact_flag_capstone (span-ID flag) | OTel sandbox + span collector |

**Creator step 1 UX change**: the template picker (currently 50 role-based starters) gets a parallel "or pick a tech domain" view. Domain selection auto-populates the course-mode, assignment recipes, and sandbox requirements. **Creator no longer invents; it picks from a structured menu.**

### Where the layers connect

```
Domain (backend_python)
  ├─ implies course_mode candidates: linear, case_library
  ├─ implies assignment recipes: [code_exercise, code_review, system_build, live_dev_workspace]
  ├─ implies sandbox requirements: [python_sandbox, webcontainer]
  ├─ implies fixture library: flowsync (50K-line FastAPI+Redis repo)
  └─ implies slide_types for concepts: [concept_card, diagram_architecture, code_read]

When Creator generates a step:
  1. Pick assignment_type from domain's recipe list
  2. Registry tells us: required grade_primitives, must_have demo_data fields
  3. Registry picks slide_types for content
  4. Fixture library provides starter_files (F26) when needed
  5. _is_complete() validates against registry's contract

When the step renders to learner:
  1. Frontend reads slide_type per content block → renders from template
  2. Frontend reads validation_contract (self-describing schema from §5 of research) → knows payload shape
  3. Grader runs grade_primitives per registry → produces scoresheet
```

---

## 3. Creator-journey walkthrough with the ontology live

Let me trace what the creator UX looks like AFTER the ontology lands. Current flow has 4 steps (Setup / Questions / Review / Done); the ontology changes the substance of steps 1-3 without changing the shape.

### Step 1 — Setup (currently: title + description + files + URLs)

Additions:
- **Domain picker** (new): 12 domains from Layer 4, one-click selects stack + recipes + fixtures. User can also skip → LLM infers.
- **Course mode picker** (new — exposes what's already computed): linear / case_library / simulator_workday / drill_only. Default inferred from domain.
- **Archetype picker** (existing, now driven by domain): domain `ops_sre` → only `ops_infra` archetype offered, etc.

Visual: the existing 50-template list becomes "Start from a template (role-shaped)" | "Start from a domain (stack-shaped)" | "Start from scratch."

### Step 2 — Clarifying questions (currently: LLM-authored Qs)

Additions:
- **Fixture picker** (new): "Your course references a codebase — pick one from the library: [flowsync (50K LOC) / velora-web (Next.js+PG) / cartflow-search (Python+FAISS) / custom URL]." Creator then emits `starter_repo` from Layer 4 / Domain registry, or `starter_files` inline.
- Questions themselves stay LLM-authored but the LLM sees the domain + course_mode + archetype as **context** (not inferred from scratch every time).

### Step 3 — Review outline

Additions:
- **Assignment type badges** per step: shows `[code_exercise — behavior_test + lint]` instead of just `code_exercise`. Creator can see what grade primitives will apply.
- **Ontology violations warning**: "Step M3S1 emitted `system_build` but no `gha_workflow_check` / `endpoint_check` / `cluster_state_check` configured — will fail `_is_complete()`. Regenerate?"
- **Fixture status**: "Step M1S2 references `repo_path` — `starter_files` (3 files, 4.2KB) will be materialized. ✓"

Creator approves → generate proceeds.

### Step 4 — Done (unchanged)

Auto-review banner, course lands in catalog.

---

## 4. Week 1 / Month 1 / Quarter 1 ship plan

### Week 1 — Ontology MVP + Grader overhaul (the "it stops shipping cheese" milestone)

**W1.1 — Build `backend/ontology.py`.** All 4 layers declared as Python data structures. Creator prompt rewritten to ASSEMBLE from the registry (the current ~3000 lines of hardcoded prompt become ~800 lines of prompt-template + registry-to-prose rendering). Per-domain subsections of the prompt are generated, not hand-written. **Fixes**: plurality drift, capstone-genre leaks, prompt-rot.

**W1.2 — Layered grader signal stack for `code_exercise`** (research W1.1 + SWE rec #1). Replace `must_contain × expected_output` with: compile (10%) + hidden pytest (50%) + Hypothesis properties (20%) + ruff/mypy (10%) + Haiku idiom rubric (10%). **Fixes**: the 60% cap, the cheese test (step 349). Creator emits `hidden_tests` instead of `must_contain`; legacy `must_contain` becomes a ≤5%-weight opt-in signal.

**W1.3 — Parsons + self-describing payload schema** (research W1.4 + §5). `GET /step/{id}` returns `validation_contract` block with exact payload shape + example. Frontend + third-party review agents read it. **Fixes**: the 0%-on-any-parsons bug (one integration test: solve → expect 1.0).

**W1.4 — Sandbox mock-module expansion** (research §5 short-term + SWE rec #3). Add `bcrypt`, `confluent_kafka`, `kafka-python`, `psycopg2-binary`, `opentelemetry-*`, full `httpx`. **Fixes**: 4 of 11 sample courses fail on first import today.

**W1.5 — F24/F26 frontend finish** (resume the paused work). `demo_data.starter_repo` → clone-link banner. `demo_data.starter_files` → "pre-seeded files" banner. `validation.gha_workflow_check` → "paste your GHA run URL" widget + backend GitHub-API poller. **Fixes**: step 452 FlowSync repo missing + all 5 capstones by giving them a real grader.

**W1.6 — `mentored_iteration` (research Proposal 7).** Reuse `adaptive_roleplay` turn engine; new UI component; Haiku-powered senior-reviewer persona leaves ≤3 code comments per round. **Fixes**: Theme A (cheese gets redirected, not scored).

**W1.7 — `property_test_grader` (research Proposal 11).** Hypothesis + DSL. For algorithmic exercises. Cheese-proof by construction.

**End-of-week state**: no more ungradable capstones, no more 60% cap, Parsons works, 40% → 15% import-fail rate. Creator runs against a data-driven registry.

### Month 1 — New runtime primitives

**M1.1 — `live_dev_workspace` (research Proposal 3).** WebContainer iframe for JS/TS + Pyodide for Python. Real `npm install` against real registry. Retires the mock-module treadmill. **Fixes**: 40% → ~5% import fail rate.

**M1.2 — `github_classroom_capstone` (research Proposal 6).** Extends the W1.5 `gha_workflow_check`: OAuth-mediated fork, AI-review bot, PR-merge gate. **Real portfolio-grade artifacts** at the end of every engineering course.

**M1.3 — `benchmark_arena` pilot (research Proposal 2).** Ship ONE — CartFlow retrieval — as the public/private eval proof-of-concept. Other data courses follow if pattern sticks.

**M1.4 — `artifact_flag_capstone` (research Proposal 4).** Per-learner seeded secret. Zero-cheese. First use: security courses (which today have no capstone format at all).

**M1.5 — Creator ontology refinements.** Haiku 2nd-pass on code_review bug lists (research Refinement 1 for code_review). FIB `alternatives` mandate (research Refinement 1 for fill_in_blank). `_is_complete()` structural rules for `system_build` (must have one of: gha_workflow_check / endpoint_check+URL / cluster_state_check / artifact_flag / local_cli_verifier).

**M1.6 — Fixture library v1** (research §5 realism). 3 reference repos on `skills-lab-demos` GitHub org: `flowsync` (50K), `velora-web` (20K), `cartflow-search` (10K). Each with planted bugs + design smells. Domain registry references them.

**End-of-month state**: zero ungradable capstones; three new cheese-proof formats live; one portfolio-grade workflow (GitHub Classroom) shipping. Budget: ~$30 of real LLM burn for agents running regenerations.

### Quarter 1 — Multi-infrastructure capstones

**Q1.1 — `cluster_state_check` (research Proposal 1).** Ephemeral k3d per learner, assertion DSL, Creator emits assertion blocks. Unlocks Kubernetes / Postgres / Kafka / Redis real-state capstones.

**Q1.2 — `chaos_hypothesis_drill` (research Proposal 5).** Builds on Q1.1's cluster infra. Adds chaos-mesh + Prometheus + hypothesis-formation UI. Senior-SRE format nobody else has.

**Q1.3 — `system_design_live` (research Proposal 10).** Excalidraw whiteboard + LLM interviewer. Staff/Principal-grade capstone.

**Q1.4 — `local_cli_verifier` (research Proposal 9).** Publish `sll-lab` CLI. Unlocks dev-env, local-K8s, tooling-config capstones.

**Q1.5 — `pixel_diff_capstone` (research Proposal 8).** Opens UX/design/accessibility course category.

**End-of-quarter state**: 11 cheese-proof, real-work-fidelity capstone formats shipped. Every major course category has a grading-sound terminal deliverable. Budget: ~$200 real LLM burn + ~$50 in k3d/EC2 compute to run the ephemeral-cluster infra. Well within the $150 cap (budget cap bumped to $250 at Q1 for this tranche).

---

## 5. What ships IF we only build ONE thing this month

**Ship the ontology registry (W1.1) + the layered grader (W1.2) + `live_dev_workspace` (M1.1), in that order.**

Those three items together:
- Give Creator a structured decision surface (stops drift);
- Make every code_exercise cheese-proof (stops 60% cap);
- Close the 40% import-fail rate;
- And position the product for Proposal 6 (`github_classroom_capstone`) + Proposal 8 (`pixel_diff_capstone`) to ship Month 2 on the same workspace primitive.

The research agent's #1 was `live_dev_workspace` + the grader overhaul. I'd add the ontology registry as prerequisite-0 — without it, the grader overhaul is still scattered across 10 prompt-edit sites.

---

## 6. Decisions I need from you before I start building

1. **Ontology registry location**: `backend/ontology.py` (single file) vs `backend/ontology/` (package with per-layer module). I'd default to single file until it exceeds ~1500 lines.
2. **Domain-list scope for V1**: ship all 12 tech domains in Layer 4, or start with 5 (the ones we have courses for today — backend_python, data_sql, devops_docker, devops_k8s, ai_dev_tools) and grow? I'd default to 5 + leave the registry schema ready for 12.
3. **Slide-type strictness**: allow LLM-authored free HTML for concept content as a fallback when no slide_type fits? I'd default to "no fallback in V1 — if the LLM tries free HTML, `_is_complete` rejects and asks it to pick a slide_type."
4. **Fixture library hosting**: put the 3 reference repos on the `skills-lab-demos` GitHub org (new) or keep them in `backend/fixtures/`? I'd default to GitHub — the `starter_repo` primitive already assumes that, and learners cloning them is part of the UX.
5. **Weekly scope ambition**: W1 as I've drawn it is 5-6 days of sustained work. If you want it done faster, drop W1.6 (`mentored_iteration`) + W1.7 (`property_test_grader`) to Month 1 — the remainder is 3-4 days.
6. **F24 / F26 resume priority vs ontology-first**: my current half-done state has F26 backend shipped + F24 Creator-prompt + CLAUDE.md docs shipped, but F24 backend validator + F24/F26 frontend pending. Options:
   (a) Finish F24/F26 frontend NOW (1 day), then start ontology → cleanest story.
   (b) Skip F24/F26 frontend, fold it into W1.5 as I've drawn it.
   I'd default to (b) — no reason to context-switch twice.

---

## 7. What I am NOT proposing

- Throwing away the 16 existing exercise types. Every one of them maps into the new ontology via a Layer-2 registry entry. `code_exercise` gets a 5-signal grader upgrade, not a rename.
- Rewriting the Creator wizard from scratch. The 4-step flow stays; step 1 gets 2 more pickers, step 3 gets badges + warnings, that's it.
- Deprecating `must_contain`. It survives as a ≤5%-weight opt-in signal for literal-phrase checks (compliance courses: "did you cite GDPR Article 30?"). Not the default.
- Bespoke runtimes per exercise type. Every new format picks from a closed set of sandbox primitives: `python_sandbox` / `webcontainer` / `ephemeral_k3d` / `github_oauth` / `assertion_runner` / `llm_judge`. No snowflake runtimes.
- Breaking existing courses. Ontology validators gate NEW generations; existing course rows are left alone. Regenerate-on-demand via the Creator if a specific course falls short.

---

## 8. The 10-day concrete cut (what I'd start tomorrow)

Day 1-2: Write `backend/ontology.py` with all 4 layers fleshed out (empty stubs are OK for Layer 4 domains outside the 5 we prioritize). Write the registry → prompt assembler.

Day 3: Refactor `_llm_generate_step_content` to read from registry. Every existing exercise-type prose block becomes a template + registry lookup. Sanity-check: regenerate one existing course end-to-end; verify no regressions.

Day 4: Layered grader for `code_exercise`. `_validate_code_exercise` becomes a pipeline of signal runners. `hidden_tests` support. Legacy `must_contain` preserved but capped.

Day 5: F24/F26 frontend finish + backend GHA poller. Both surface to learner as polished widgets.

Day 6: Parsons fix + `validation_contract` self-description shipped on ALL exercise endpoints.

Day 7: Sandbox mock-module expansion. Regenerate the bcrypt / kafka / otel courses through Creator; verify scaffolds work out-of-box.

Day 8: `mentored_iteration` basic shell (share roleplay engine). Ship 1 code-review course using it.

Day 9: Deploy to 18.236.242.248 ONLY. Smoke-test a Docker-flavored course end-to-end.

Day 10: Run the SWE review agent again as regression test. Expect: 0 cheese-able exercises, 0 capstone URL failures, Parsons working, import-fail rate < 20%.

Budget estimate for the 10 days: ~$25 in real LLM burn (regenerate ~15 courses through the new Creator + 2 agent-reviewer rounds). Well under cap.

---

## 9. Open questions + risks

- **WebContainer Python story**: Pyodide is solid for pure Python + NumPy/Pandas, but breaks on C-extension-heavy libs like `bcrypt` and `psycopg2`. We either accept Python courses use our existing sandbox (with expanded mocks), or we ship a second runtime (ephemeral container) for those. The research agent's proposal 1 covers this — but at Q1 timing. Risk for M1: JS/TS courses get real deps, Python courses still need stubs.

- **GitHub OAuth integration**: `github_classroom_capstone` needs us to act on the learner's behalf. Security review needed before shipping — minimal-scope token (public_repo only?), rotation story, revocation UX. I'd want a ~2-day dedicated implementation window here, not rolled into a crowded week.

- **Ontology-registry drift**: once the registry is the source of truth, keeping it in sync with the 20-odd places the Creator prompt has grown organically requires a one-time audit. Plan for a dedicated 0.5-day "audit + migrate" task before W1.1 kicks off.

- **Budget headroom for Q1**: ephemeral k3d clusters at scale could get expensive. I've costed this as "~$50 / quarter" assuming low concurrent-learner counts (< 10). If the product scales faster, the compute budget needs a real bump request (separate from the LLM budget cap).

- **Creator form persistence interaction**: the ontology adds 2 more pickers to step 1. The draft-persistence localStorage snapshot (shipped this turn) covers them automatically because it reads by ID — no code change needed. One less worry.

---

## 10. If you agree, the immediate next actions I'd take

1. **Greenlight check**: I ship (a) the 5-domain V1 of Layer 4, (b) the ontology registry + prompt assembler (W1.1), (c) the layered code_exercise grader (W1.2). Expected: 2-3 days of work, deployed to 18.236.242.248, regression-tested via the SWE review agent. Budget: ~$10 real LLM burn.

2. **Paused work resumes inline**: F24/F26 frontend lands as W1.5 within the same week.

3. **Deferred for user decision**: whether `mentored_iteration` (W1.6) and `property_test_grader` (W1.7) slip to Month 1. Default: keep in Week 1 if the above 3 finish in 5 days; slip if not.

4. **Reviews artifact doubles as acceptance criteria**: after W1 lands, rerun the SWE review agent. If it still finds a 60%-cap cheese, a broken Parsons, or a placeholder endpoint_check, W1 isn't done. Clear bar.

Your call on the Section 6 decisions (and the greenlight) and I start.
