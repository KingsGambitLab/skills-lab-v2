# Creator Flow — Feature Proposal (2026-04-27)

**Branch:** `worktree-creator-flow-2026-04-27`
**Scope statement:** Improve the Creator dashboard + gen pipeline. **Zero changes to learner-facing rendering or to already-published course content.** The non-negotiable guarantee — running courses on prod (52.88.255.208) keep working byte-for-byte — is built into every feature below.

---

## Hard constraint: how we keep existing courses untouched

| Risk surface | Constraint we hold |
|---|---|
| Database schema | All new columns added via `_ensure_column(... nullable=True, default=None)` (engine-agnostic, idempotent). Existing rows: NULL on new columns → existing read-paths unaffected. |
| Creator API | All new behaviors live behind NEW endpoints (e.g. `/api/creator/outline`, `/api/creator/publish`). The existing `/api/creator/{upload,start,refine,generate}` chain stays byte-identical for any client still using it. |
| Course content | We never run "v8 → v9" migrations against existing course rows. Reviewer agents READ existing courses for grading; they never write back. |
| Frontend learner code | We don't touch `frontend/index.html`'s learner step renderer, the validators, the data-action delegator, the celebration panel, etc. Creator dashboard changes are scoped to the wizard surface. |
| LLM prompts | Existing courses don't get re-generated. Prompt changes affect ONLY new gen runs (per CLAUDE.md §"Do Not Patch Broken Generated Courses"). |

Every feature below adds an `additive contract` line stating exactly what the change leaves alone.

---

## What's missing today (synthesized from inventory + CLAUDE.md "queued / TODO")

1. No outline preview/edit between `/refine` and `/generate` — `_llm_refined_outline` runs, the creator clicks Generate, modules silently disappear (the "M5 team-Claude" bug). Filed as queued.
2. No publish gate — courses go live the instant generation completes. Creators can't preview before learners can see.
3. Reviewer agents (`beginner_agent`, `cli_walk_agent`, `vscode_walk_agent`, `domain_expert`) are wired as shims that produce prompts but aren't auto-invoked from the dashboard. Today: hand to Agent tool manually.
4. No live generation timeline — the activity feed exists at `/api/creator/progress/{session_id}` but the dashboard surfaces minimal info. Cost per course is invisible to the creator (only `/api/admin/budget` shows total spend).
5. No outline-diff when refine re-runs — silent module drops can't be spotted at a glance.
6. No source-doc fidelity readout — when uploading a PDF, creator can't see (a) what we extracted, (b) which canonical entities propagated, (c) which got dropped post-gen.
7. Asset-registry edits require Python (`backend/course_assets.py`); no UI.

---

## Proposed features (prioritized)

### Tier 1 — high-impact, low-blast-radius (recommended Sprint 1)

#### F1. Outline Preview & Edit (between `/refine` and `/generate`)

**Problem.** Today the refined outline is returned by `_llm_refined_outline` and the creator clicks Generate without seeing it. CLAUDE.md flags this as the cause of the "M5 team-Claude silently dropped" class of bugs.

**Scope.** Add a new wizard step between Step 2 (Answer Questions) and Step 3 (Generate). It renders the refined outline as an editable tree:
  - Modules: rename, reorder (drag), add, delete
  - Steps: rename, reorder within module, change exercise_type (constrained to ontology), edit description
  - Validation: warn if module count diverges from the source-material's enumerated module list (the "post-refine structural diff" CLAUDE.md mentions)
  - "Re-refine with my edits" button calls `/api/creator/refine` again, this time treating the edited outline as the prior turn's input
  - "Generate Course" only enabled after creator clicks "Looks good"

**Backend.** New endpoint `POST /api/creator/outline` returns the refined outline JSON; new endpoint `POST /api/creator/outline/save` persists creator edits as the input to `/generate`.

**Additive contract.** No change to `/refine` / `/generate` shape. Old clients that skip the new step still work — the new endpoints are only hit by the new wizard. Existing courses untouched.

**Why first.** Highest-leverage, fixes a root-cause bug, no side effects.

---

#### F2. Live Generation Timeline + Cost Meter

**Problem.** Generation takes 5–15 minutes for full courses. Today's dashboard shows a spinner. Creators don't know if a step is stuck, retrying, or making progress. Cost per course is invisible.

**Scope.** Replace the progress spinner with a live timeline:
  - Per module: title + status pill (queued / in-progress / done / retrying / failed)
  - Per step (expanded): exercise_type, model used, attempt count, retry feedback (last 200 chars), $cost so far, elapsed time, validation status (compile / Docker invariant / ontology gate), inline preview of the generated content as it streams
  - Course-level: total $ spent, $ remaining vs `ANTHROPIC_BUDGET_USD` cap, ETA based on per-step median
  - "Cancel & save partial" button: stop further generation, persist what's done as a draft

**Backend.** Extend the existing `/api/creator/progress/{session_id}` SSE/poll endpoint with the new fields. New `POST /api/creator/cancel/{session_id}` to halt generation.

**Additive contract.** New fields on the progress endpoint are added but the existing fields stay. Cancel is additive.

**Why early.** Trust + cost-discipline (CLAUDE.md §"$250 budget cap") are creator-side concerns the dashboard should surface.

---

#### F3. Publish Gate (Draft → Preview → Published)

**Problem.** A course goes live to learners the instant `/generate` completes. There's no chance for the creator to preview, no review-loop integration, no "this looks bad, let me regen and try again before anyone sees it."

**Scope.**
  - New `Course.status` column: `draft | reviewing | published | archived` (default `draft` for new courses)
  - **EXISTING courses**: backfilled to `published` on first read so the catalog is unchanged
  - New API: `POST /api/courses/{id}/publish` — flips draft → published; auth-gated to course creator
  - Catalog `GET /api/courses` filters out non-published courses for non-creators (creators see their own drafts)
  - Dashboard shows a "Publish" button after generation + reviewer pass

**Additive contract.** This is the most-touchy feature. Mitigations:
  - `Course.status` defaults to NULL for existing rows; the catalog filter treats `NULL OR 'published'` as visible
  - The flip from public-by-default to draft-by-default applies ONLY to courses created from the new wizard step that explicitly sets `status='draft'`
  - We can ship behind a feature flag (`SKILLSLAB_PUBLISH_GATE=on`) so prod doesn't change behavior until we explicitly enable it

**Why this tier.** Creator-side QC requires this. Without it, every gen mistake hits learners.

---

#### F4. Reviewer-Agent Integration (Creator-Triggered)

**Problem.** Four reviewer shims exist (`beginner_agent`, `cli_walk_agent`, `vscode_walk_agent`, `domain_expert`). Today: invoked manually, output goes to `reviews/*.md`. Creators don't see verdicts in the dashboard.

**Scope.**
  - Dashboard panel lists the reviewer agents relevant to the course shape, each with:
    - Agent name + one-line description of what it grades
    - Estimated cost ("~$0.30 per run" / "~$0.80 per run")
    - "Run" button — posts to `POST /api/courses/{id}/review/{agent}` and kicks off the agent in the background
    - Status pill: `idle | running | done | failed`
  - Recommended reviewers per course shape (suggested, not forced):
    - All courses: `beginner_agent`
    - Courses with `terminal_exercise` steps: `cli_walk_agent`
    - AI-enablement / Claude Code domain: `domain_expert`
  - New `Course.review_artifacts` JSONB column: array of `{agent, verdict, artifact_path, artifact_excerpt, run_at, cost_usd}`
  - Streaming review artifact + verdict pill (SHIP / SHIP-WITH-FIXES / REJECT) renders inline as the agent writes
  - On REJECT, "Triage & Regen" CTA opens the per-step regen UI pre-populated with the reviewer's flagged steps + reasons
  - `SKILLSLAB_REVIEW_AUTO=off` (default) — no automatic invocation; creators decide when to spend the budget

**Additive contract.** Reviewer agents are READ-ONLY against course content. The artifact columns are new — existing courses get NULL → no behavior change. Manual-trigger only, so no surprise spend.

**Why this tier.** Surfaces the existing reviewer shims to creators without committing to per-course auto-spend. Auto-run can land later (Tier 3) once we have data on which agents are worth defaulting on.

---

### Tier 2 — medium-impact (Sprint 2)

#### F5. Outline Diff Viewer (between refine iterations)

When `/refine` re-runs, show diff against the prior outline: added modules in green, removed in red, reordered with arrows. Implementation: client-side using deep-diff against a saved prior outline. Catches silent drops at the source.

**Additive contract.** Pure UI on the new outline preview from F1. No backend change.

#### F6. Source-Doc Fidelity Panel

Post-upload (PDF/DOCX/PPTX), show:
  - Extracted text length + first 1000 chars
  - Canonical entities extracted (`_extract_canonical_entities`)
  - Post-gen: which entities propagated to step content (regex match) vs which got dropped
  - Faithfulness score per step (% canonical entities preserved)

**Additive contract.** Read-only over existing extraction logic. New endpoint `GET /api/creator/fidelity/{course_id}`. Existing pipeline untouched.

#### F7. Cost-Per-Course Dashboard

Per-course `$cost` rollup: Sonnet vs Haiku vs Opus tokens, retry waste, reviewer-agent cost. Plot vs the budget cap. Lets creators decide whether to retry vs accept.

**Additive contract.** New summary endpoint reading from existing `.anthropic_budget.json` + per-call telemetry we already log.

---

### Tier 3 — later (Sprint 3+)

#### F8. Asset-Registry UI

UI to add a course's GitHub repo + branches + MCP servers without editing `backend/course_assets.py`. Persists to a `course_assets` DB table; existing Python registry stays as the canonical seed (no breaking change).

#### F9. Custom Exercise-Type Registration UI

The ontology layer supports `register_assignment(...)` from any module. Surface a creator-facing UI for advanced users to declare new exercise types (with grade primitives).

#### F10. Course Versioning + Diff

After per-step regen, store the prior content as a `course_version` row. Diff viewer between versions. Useful for rolling back regressions.

#### F11. Pre-Gen Feasibility Check

Before clicking Generate, run a quick LLM call that estimates: total $ cost, gen time, expected complexity per module, likely-tricky steps. Lets the creator iterate on inputs before burning budget.

---

## Recommended phasing

| Sprint | Features | Estimated effort | Outcome |
|---|---|---|---|
| **1** | F1, F2, F3 | ~2 weeks | Creator can preview outline + edit, watch generation live with cost meter, ship to a draft gate before learners see anything |
| **2** | F4, F5, F6, F7 | ~2 weeks | Reviewer agents auto-run, source-doc fidelity visible, full cost breakdown per course |
| **3** | F8, F9, F10, F11 | ~3 weeks | Asset registry + custom types via UI, version history, pre-gen feasibility |

---

## What this proposal does NOT touch

- `frontend/index.html`'s learner step rendering (the data-action delegator, validators, celebration, code editor, etc.)
- Existing `/api/exercises/validate` / `/api/progress/complete` / catalog endpoints
- Already-published courses on prod or skills.sclr.ac
- The widget runtime + CSP-safe rewriter (vscode/src/widgets.ts) — orthogonal concern, its own ship cycle
- Per-course content rows in the DB (no migrations that mutate `Step.content`, `Step.code`, `Step.validation`, etc.)
- Anthropic API budget cap mechanism (still hard-capped at $250)

---

## Open questions for the user

1. **Publish gate default for existing courses** — ✅ **DECIDED 2026-04-27**: backfill all existing courses to `status='published'`. The catalog filter treats `NULL OR 'published'` as visible so this is a one-line backfill (`UPDATE courses SET status='published' WHERE status IS NULL`) at deploy time. New courses created via the wizard default to `'draft'`.
2. **Reviewer integration cost** — ✅ **DECIDED 2026-04-27**: do NOT auto-run. Surface as creator-triggered actions on the dashboard ("Run beginner walk", "Run domain-expert review", "Run CLI walk") with a cost estimate next to each button. Each run posts to a new endpoint (e.g. `POST /api/courses/{id}/review/{agent}`) that kicks off the agent in the background and streams the artifact back to the dashboard. Default for `SKILLSLAB_REVIEW_AUTO` env var = `off`.
3. **Outline preview as a separate wizard step (recommended) or an inline expander on Step 2?** — ✅ **DECIDED 2026-04-27**: separate wizard step. Wizard becomes 5 steps: Setup → Answer Questions → **Review Outline** (new) → Generate → Done. Harder to skip + clearer mental model than an expander on Step 2.

All three open questions resolved. Ready to start F1 (Outline Preview & Edit) on this worktree.
