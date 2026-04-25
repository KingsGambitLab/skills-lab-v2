# Skills Lab v2 — AI LMS Platform

## 🎨 RENDERING LAYER OWNS TYPOGRAPHY — NOT THE CREATOR (2026-04-25)

**User directive (verbatim, 2026-04-25):** *"How can we improve the data presentation here? The indentation is broken + too much context. Fix the root cause, don't fix symptoms. Add to claude.md and follow here."*

**The principle**: the front-end CSS is responsible for VERTICAL RHYTHM,
SPACING, and DENSITY CONTROL of every concept-content artifact. The
LLM-Creator emits semantic HTML (`<h2>`, `<ol>`, `<pre>`, `<table>`,
`<blockquote>`); the renderer makes it readable. Inconsistent margins
or jammed elements emitted by the Creator MUST be normalized by CSS,
NEVER by re-prompting the LLM to "add more breaks."

**Why this is a structural rule (not a one-off polish task)**: every time
the Creator emits a new shape (a new tech, a new layout pattern), it
will produce slightly-different HTML. The reactive fix path ("the LLM
forgot a break, regen with feedback") is a symptom-chasing tar pit —
identical to the verified-facts blocklist trap (see §F3 v8.7). The
structural fix is the same shape: ENFORCE the invariant at the layer
that owns the concern (CSS for typography, schema for tech facts).

**What the rendering layer MUST guarantee for `.step-content` /
`.concept-content` descendants**:

1. **Vertical rhythm** — `h2/h3` get `margin-top: 28px`, `h4` gets 22,
   `p` gets `0 0 14px`, `ol/ul` get `14px 0 18px`. Adjacent-sibling
   selectors smooth list→heading transitions (`ol + h3 { margin-top:
   32px }`).
2. **Code-block density cap** — `pre` is `max-height: 360px;
   overflow: auto`. A 50-line tool_use JSON block can no longer eat
   the whole viewport. Inline `<code>` is left at natural width.
3. **List spacing** — `li { margin-bottom: 6px }` so 5-item lists
   breathe without the LLM having to add `<br>` tags.
4. **Boundary trimming** — `> *:first-child { margin-top: 0 }` and
   `> *:last-child { margin-bottom: 0 }` strip phantom space at the
   container edges, regardless of which element the Creator chose to
   start/end with.
5. **Tables, blockquotes, paragraphs after lists** — all get explicit
   margins. Same principle: the Creator can emit any combination, the
   renderer makes it readable.

**What the Creator does NOT have to manage**: line breaks between
sections, inter-paragraph margins, code-block scrolling, table-cell
padding, list-item spacing. That's all CSS now.

**What the Creator IS still responsible for**: SEMANTIC structure —
using `<h3>` for sub-headings (not `<p><strong>`), wrapping examples
in `<pre><code>` (not raw `<div>` with whitespace), using `<ol>` for
numbered steps (not `1. text<br>`). The renderer can only make
semantic HTML rhythm correctly; if the Creator emits `<div>` soup, no
amount of CSS will rescue it.

**Adding new content patterns**: when a new layout pattern lands (e.g.
two-column compare blocks, stat-callouts, inline diagram explanations),
extend the `.step-content` / `.concept-content` typography block in
`frontend/index.html` rather than asking the Creator to add inline
styles. Inline styles are course-content drift; CSS is content-shape
contract.

---

## 🚢 SHIP-AS-YOU-WIN — commit + push after every major upgrade or successful win (2026-04-25)

**User directive (verbatim, 2026-04-25):** *"After every successful major upgrade / win — commit to github."*

Don't sit on landed work. Every time a coherent unit ships clean — feature complete, smoke-tested, no regressions — commit + push to `origin/main` BEFORE moving to the next thing. Don't batch 5 unrelated wins into one commit; don't leave a working-state stash dangling for hours.

### What counts as a "major upgrade / win"

- **Platform fixes** that close one root cause (e.g. extending the verified-facts-block, dockerizing a runtime, swapping a validator path). One coherent change.
- **Course generation that lands clean** (whole course or batch of per-step regens, all green).
- **A review-pass result that you've fully triaged** (artifact in `reviews/` is enough on its own — that's a unit too).
- **A new feature** end-to-end (backend endpoints + frontend wiring + verified working).
- **A repo scaffold** that pushes a course's GitHub assets (each `kimi-eng-course-repo` / `jspring-course-repo` push is a win).
- **A documentation pass** (CLAUDE.md update capturing a learning) — counts on its own.

### What does NOT need its own commit

- Half-built work mid-debugging (don't commit broken code just to feel productive).
- Untracked files that aren't part of the intent (review artifacts the agent wrote without you reading them; tmp scratch files; broken WIP).
- Pure formatting / whitespace changes that aren't the point of the change.

### Per-commit checklist

1. The change is COHERENT (one win, one commit).
2. Imports are clean (`backend.main` loads without error).
3. The thing you claimed to ship works — smoke-tested via curl, browser, or the harness.
4. Commit message names the win + WHY (not just the file). End with the standard `Co-Authored-By:` trailer.
5. `git push origin main`. Don't leave it local.

### Why this matters

- **Audit trail**: every state of the system is reachable via `git log`. If a regen burns budget on a wrong direction, `git revert` is one command.
- **Backups**: `origin/main` is durable; a laptop drive is not. Today's 5 commits to `origin/main` would survive my laptop dying.
- **Collaborator visibility**: if anyone else opens the repo, the latest pushed sha tells them where things stand. Local-only commits are invisible.
- **Discipline forcing-function**: if you can't commit cleanly, the change probably isn't a coherent win. The commit message itself reveals whether you actually finished a thing or just fiddled.

### Anti-pattern to watch for

The "I'll commit at the end of the day" trap. By end of day, you have 6 entangled changes; the commit message is "various fixes"; rolling back any one piece is impossible. Catch yourself: if a thing landed clean, push it NOW, then start the next thing.

---

## 🧰 v8.6.2 Phase 2 (2026-04-24 latest) — Post-review platform fixes (8 root-cause fixes shipped as wiring, not per-course regen)

**User directive (verbatim, 2026-04-24):** *"Don't fix any symptom, fix root cause. And don't edit course content directly, regen the step. You can fix wiring on the go."*

The v2 dual-agent review of AI-Powered Workday (beginner PM + VP Product AI Enablement expert) both verdicted SHIP-WITH-FIXES. Of the 8 issues flagged, every one had a generic root cause that would bite future non-coder courses. Fixed at the platform layer; the 3 content-drifted steps get per-step regens to verify the prompt change propagates.

### The 8 root-cause fixes

| # | Symptom (reviewer's report) | Root cause | Fix location |
|---|---|---|---|
| 1 | 3 `fill_in_blank` steps used Python syntax (`task_name = ""`, dict literals, f-strings) — violated zero-code promise | Creator prompt's `fill_in_blank` branch had only `is_non_engineering` + engineering branches; no `is_zero_code` branch. Zero-code courses fell through to the engineering branch that asks for Python code. | `backend/main.py` — new `if is_zero_code` branch above non_engineering with LABEL-COLON-BLANK shape + HARD RULE forbidding `=`, `{`, `}`, `[`, `]`, `print()`, `def `, `f"..."` in `code` |
| 2 | M4 simulator Event Stream rendered events as raw JSON `{"id":"ping_1","t_offset_ms":300000,…}` | `appendSimEvent` fell through to `JSON.stringify(ev)` when `ev.text`/`ev.type` were absent (which is always, for ID-only events) | `frontend/index.html` — new `formatSimEventHuman(ev, tick)` resolves `ev.id` against `_simSession.uiConfig.{interruptions,ceo_email,events}` tables populated by the Creator for inbox-style sims + humanizes tick N to "9:MM AM" when `tick_ms=60000` |
| 3 | "Begin Simulation" button navigated user to M5 instead of starting sim | `simloopStart(index)` read `getSteps()[index]` which is `state.currentModuleData.steps` — a HASH-CHANGE navigation could shift it before the click fired, so the POST used M5's step_id | `frontend/index.html` — `setupSimulatorLoop` now captures `step.id` + `demo_data.ui_config` + `demo_data.tick_ms` at RENDER time into module-scoped `_simSession`; `simloopStart`/`simloopAction`/`simloopAdvance` use `_simSession.stepId`, NEVER `getSteps()[index]` |
| 4 | Categorization silently navigated away on WRONG submit; learner couldn't iterate | Separate class of nav-race (stale `state.currentModuleData` during hash-change) — affects every step-handler that dispatches by `index` not `step.id`. Broader audit needed. | **Deferred to production-ready**: every `handler(index)` should capture step.id at render time like `_simSession` does. Tracked as "nav-router audit." |
| 5 | M1.S3 rubric feedback UI stale on re-submit (showed attempt-1 20% even when attempt-2 backend returned 0%) + button disabled after FAIL instead of after PASS | Two bugs in one block: (a) `result.innerHTML` not cleared before fetch, so if the learner clicks again quickly the stale panel persists; (b) `btn.disabled = !isCorrect` disabled on MISS (inverted — comment said "leave disabled on pass" but code did the opposite) | `frontend/index.html` — clear `result.innerHTML = ''` before fetch; `btn.disabled = isCorrect` (disable ONLY when they pass — locks in the win; keeps enabled on miss so they iterate) |
| 6 | LLM rubric grader HALLUCINATED — claimed learner "didn't identify audience/format" when the submission explicitly named all three | Grader prompt didn't require grounding claims in verbatim quotes from the submission; LLM freely invented "missing" criteria | `backend/main.py` — `_llm_rubric_grade` prompt now has 4 non-negotiable rules: (a) before claiming missed, scan for alias words; (b) every "missed" claim MUST include a quoted phrase ≤12 words from the submission; (c) accept aliases (target reader = audience, word count = format); (d) positive feedback must also quote |
| 7 | M5.S5 capstone "Phases 0/4" dragged 90% rubric + 6/6 checklist down to 65% composite — no UI to check phases | Phases treated as separate grade primitive orthogonal to the rubric. For rubric-only (zero-code) capstones, the rubric ALREADY evaluates whether the learner did the work — requiring redundant clicks is punishment | `backend/main.py` `_validate_system_build` — when scoring path is `rubric_score is not None`, `effective_phase_score = 1.0` (auto-credit). Phases still render in the briefing as guidance; just don't gate score |
| 8 | M3.S2 fill_in_blank secretly EXACT-MATCHED sensible PM answers at 0% with no per-item reveal | `_validate_fill_in_blank` only had exact-match path; non-coder worksheets need rubric-based grading on free-text | `backend/main.py` `_validate_fill_in_blank` — new RUBRIC PATH: when `validation.rubric` is present, build concatenated "Label: learner_answer" submission + call `_llm_rubric_grade` + respect `passing_threshold` (default 0.6). Legacy exact-match preserved for code-syntax blanks. Creator prompt now emits `validation.rubric` for zero-code `fill_in_blank` |

### Per-step regens after the platform fixes

After the wiring fixes landed, the **3 content-drifted steps** (AI-Powered Workday 85092/85097/85107) were regenerated via `POST /api/courses/{id}/steps/{step_id}/regenerate` so they inherit the new `is_zero_code` fill_in_blank prompt. This is the canonical pattern per CLAUDE.md §"Do Not Patch Broken Generated Courses": fix Creator → regen → verify fix propagates. **NO direct DB edits to course content.**

### Rule: nav-router state-bleed (deferred — queue for production-ready)

Every frontend handler that dispatches by `index` (e.g. `checkCategorization(index)`, `submitSystemBuild(index)`, `simloopStart(index)`) is vulnerable to a hash-change race: `state.currentModuleData` can shift between render + click, so `getSteps()[index]` can return a step from the WRONG module. The pattern that fixes it (used in `_simSession`): capture `step.id` + needed `demo_data` INTO A MODULE-SCOPED OBJECT at render time; handlers read from that object, NEVER from `state.currentModuleData` after the first render.

Queue as a platform-wide audit: `setupCategorization`, `setupSystemBuild`, `setupAdaptiveRoleplay`, `setupIncidentConsole`, `setupTerminalExercise` — all need the same treatment as `setupSimulatorLoop`.

---

## 🧰 v8.6.2 (2026-04-24 late-late) — Zero-code / non-coder courses as first-class citizens

**User directive (paraphrased):** *"If this works, create the non-tech course, in similar hands-on style leading to real skills learning."*

Non-coder knowledge workers (PMs, ops leads, CSMs, legal, finance, marketers, people-ops) need an AI-upskilling course shape that mirrors the tech-course's hands-on rigor — WITHOUT the CLI / git / Docker / GitHub / deploy footprint that makes tech courses unreachable for them. Beginner reviewer on the first non-tech course (AI-Powered Workday, `created-bd5ec658354f`) filed v1 REJECT with 3 ship-blockers, all traced to the platform assuming code-ness by default. v8.6.2 makes zero-code a first-class mode with generic, reusable primitives — identical pattern to v8.6.1's switching-UX primitives for BYO-key tech courses. Building a new non-coder course inherits all of this for free.

### Shipped (generic, reusable):

1. **`_is_zero_code_course(title, description, source_material, tags)`** in `backend/main.py` — detects browser-only / non-coder intent. STRONG markers ("no code", "non-coder", "browser-only", "claude.ai browser", "prompt template/library/workflow") auto-flip; SOFTER audience markers ("product manager", "CSM", "ops lead") flip only when COMBINED with pedagogy markers ("prompt", "workflow", "template"). Orthogonal to `_is_non_engineering_subject` (course_type="technical" doesn't gate this — a course can be technical AND zero-code, like AI-Powered Workday).

2. **`_llm_rubric_grade(rubric, submission, step_title, ...)`** — shared LLM-rubric primitive. Reusable across `code_read` (explain-back) + `system_build` (zero-code capstone paste) + future exercise types with rubric-graded text submissions. Returns `{score: 0..1, feedback: str}`. Defensive: graceful fallback when LLM unavailable. **No cross-table SQLAlchemy lazy-loads inside the validator** — they trigger `greenlet_spawn` errors in non-async context; pass synchronous attributes only.

3. **`_validate_system_build` — rubric-aware scoring.** Added `validation.rubric` (string) + `response.paste_markdown` (aliases: `paste`, `submission`, `markdown`) as a third 50%-slot grade primitive, mutually exclusive with `gha_workflow_check` / `endpoint_check`. Priority: GHA > endpoint > rubric > phases-only. Grade-primitive-floor includes rubric — a zero-code capstone with rubric configured passes the "no primitive" cap.

4. **Zero-code `system_build` Creator-prompt branch** (third branch, ahead of non-engineering + engineering). For `is_zero_code=True`, emits: phases with BROWSER-only vocabulary, checklist items forbidden from using git/GitHub/push/commit/fork/repo/deploy/Docker/CLI/terminal/API-key verbs, `paste_prompt` one-liner, `validation.rubric` (120-300 word LLM-grader rubric), `passing_threshold: 0.7`. NO `deployment_config`, NO `gha_workflow_check`, NO `starter_repo`.

5. **Ontology tightening — `simulator_loop` required fields.** Was `required_demo_data=["initial_state"]`; now `["initial_state", "actions", "events", "win_conditions"]`. The non-tech v1 "simulator broken" bug traced to Creator dropping these fields — ontology gate now rejects. Any future simulator_loop step without all four fields is unshippable.

6. **Frontend `renderSimInitialMetrics` + `formatSimValue`** (index.html) — safe rendering of COMPOUND state values. Arrays → "`N items`", dicts → "`K fields`". Was `String(v)` which returned `[object Object],[object Object],…` for lists of dicts — that was the exact rendering bug the beginner review flagged for M4.2 inbox simulator dashboard.

7. **Frontend `code_read` language-text path** (index.html) — when `demo_data.language` is `text` / `markdown` / `plaintext`, hide the Monaco-like code editor shell entirely and render a STYLED REFERENCE TEXT BLOCK (scroll-capped, monospace-free, white-space:pre-wrap). Content-agnostic textarea copy ("What do you notice? What makes one approach work better?" instead of "What does this code do?"). Preserves the rubric-graded submit path. Applies to any future non-tech course that uses code_read for prompt/template/workflow REFERENCE text.

8. **Frontend `project` template — paste-markdown widget** (`frontend/templates/project.{html,js,css}`). Renders when `data.rubric` is present AND no GHA/endpoint is configured. Monospace textarea with expected-doc-shape placeholder + paste_prompt header + rubric-score hint. Submits `paste_markdown` field to the backend. Mutually exclusive with GHA + endpoint widgets. **TPL_VERSION bumped 1.1.2 → 1.1.3** + index.html `<head>` refs bumped.

### The rule for any future non-coder / browser-only course:

1. **Zero code detection auto-fires** — if the title/description/source_material mentions "no code" / "non-coder" / "browser-only" / "prompt workflow" / "claude.ai browser" / "for PMs / CSMs / ops / legal / marketers", the Creator automatically:
   - Routes `system_build` to the rubric-paste branch
   - Rejects `gha_workflow_check` / `endpoint_check` as primary capstone gate
   - Emits checklist items with BROWSER-only verbs (no git / push / deploy)
2. **`simulator_loop` schema is strict** — every simulator_loop step MUST have all 4 required fields (initial_state + actions + events + win_conditions). The gate rejects drops at gen time. Complex inbox/roster content goes in `ui_config`, NOT `initial_state` (which must stay scalar-only for dashboard rendering).
3. **`code_read` with `language: text`** — renders as styled reference block + content-agnostic explanation textarea. Use this exercise_type whenever the learner READS non-code reference material (two prompts / two templates / two memos) and EXPLAINS the difference.
4. **`system_build` rubric capstones** — validation.rubric + passing_threshold is the entire grading primitive. NO phases required (but they're supported). Frontend auto-shows the paste widget.

### Evidence (v8.6.2 proof):

- End-to-end validate smoke test on `created-bd5ec658354f/85110` (M5.5 capstone):
  - STRONG paste (3 templates + meta-guide, 2000+ chars): rubric 90%, total 0.95, correct=True.
  - WEAK paste (5-sentence generic): rubric 10%, total 0.55, correct=False.
  - Grader discriminates strong vs weak by 7× on a 0-1 scale.
- Browser smoke:
  - M1.3 (`code_read` with language=text): reference-text block renders, placeholder content-agnostic, textarea mounts, no code editor chrome. ✅
  - M4.2 (`simulator_loop`): dashboard shows 7 scalar metrics, 11 actions load on "Begin Simulation", first action advances tick 0→2 + mutates state. ✅
  - M5.5 (`system_build` zero-code): paste-markdown widget renders with paste_prompt, monospace textarea, no GHA/endpoint UI. ✅

### Queued followups:

- Extend `_is_zero_code_course` heuristic as new non-coder course shapes surface. Add markers from actual titles when courses land.
- Creator /refine UI: flag zero-code detection explicitly ("we detected this is a non-coder course; capstone will be a markdown-paste rubric. Confirm?") — same pattern as the post-refine module-count diff followup.
- Frontend `renderSimInitialMetrics`: expandable view — click on "12 items" to see the actual inbox rows. Currently they live in `ui_config.inbox` + aren't exposed to the dashboard UI yet. Non-tech v2 still works without this (briefing explains the inbox in prose) but future sims would benefit.

---

## 🧰 v8.6.1 (2026-04-24 late) — AI-Augmented Engineering course + generic switching-UX primitives

**User directive:** *"If this works, we will build a lot of similar courses. Build everything extensible, don't hard code."*

This release added the first BYO-key / Claude-Code-on-learner-machine course (AI-Augmented Engineering — `created-7fee8b78c742`) and in the process shipped **generic** platform primitives every future terminal-heavy / real-repo / GHA-graded course inherits for free. None of the fixes are one-off.

### Shipped (generic, reusable):

1. **`terminal_exercise` template enhancements** (frontend/templates/terminal.{html,js,css} + index.html head)
   - Per-step **bootstrap command** with banner: copy-to-clipboard one-liner that `git clone && cd && git checkout BRANCH && echo 'step banner' && claude`. Shell-prompt indicator (`[SLL:M3.S2]`) survives for the session. Learner can't lose their place.
   - **Dependencies panel** (`demo_data.dependencies`): declares what the learner needs (`anthropic_api_key` / `claude_cli` / `docker` / `git_clone` / `python` / `nodejs` / `github_account` / `github_pat`). Accepts string-shorthand OR `{kind, label, why, install_hint}` dict.
   - **Structured paste slots** (`demo_data.paste_slots: [{id, label, hint, placeholder}]`): instead of one big textarea, labeled slots for e.g. `{prompts, final_diff, transcript}`. Backend combines into `response.pastes` + keeps `response.paste` concatenation for back-compat.
   - **`127.0.0.1` → `localhost` normalization** in dashboard_deeplink: Claude Preview + some browser contexts only resolve `localhost`. Normalize in JS before emitting.
   - **Template load contract**: any new template must register BOTH `<link>`+`<script>` in `<head>` AND be in the preload `names` array. The 2026-04-24 BLOCKER #1 was caused by terminal.html shipping to the cache without terminal.js being loaded → dispatch fell through to narrative fallback. `TPL_VERSION` bumped on ANY template asset change. Contract: template X exists ⇨ `<link rel="stylesheet" href="/templates/X.css?v=…">` + `<script src="/templates/X.js?v=…" defer>` + `X` in the preload list + entry in `_TEMPLATE_DISPATCH` + entry in `_TPL_GLOBAL`.

2. **Course-asset registry** (`backend/course_assets.py`)
   - Single place for every course's external assets (starter repo + pre-built MCP servers).
   - `register_course_assets(CourseAsset(slug=..., course_repo=..., module_branches={...}, mcp_servers=(...)))` — one call per course.
   - `resolve_asset(slug, kind, **kwargs)` + `build_bootstrap_command(slug, module_key)` helpers.
   - Convention: repos live at `https://github.com/<org>/<slug>-course-repo` with branches `module-<N>-<shortname>`; pre-built MCPs at `<org>/<slug>-<mcp_name>-mcp`. GHA workflow at `.github/workflows/lab-grade.yml`. Adding a new course = ONE registry entry + TWO GitHub repos. No other code edits.

3. **Course-asset backfill** (`backend/course_asset_backfill.py`)
   - Post-gen script that walks any course + fills MISSING switching-UX fields (`bootstrap_command`, `dependencies`, `paste_slots`, `step_slug`, `step_task`) on `terminal_exercise` steps from the asset registry. Generic — works for any `course_id + slug` pair.
   - Handles the common Creator drift where some steps get rich fields and others don't.
   - Invoked: `python -m backend.course_asset_backfill <course_id> <asset_slug> [--dry-run]`.

4. **Generic `add_module_to_course`** (`backend/add_module_to_course.py`)
   - Runtime workaround for the "Creator silently dropped a module during /refine" class of bug.
   - Script inserts a new Module + step skeletons at the END of an existing course, then triggers per-step regeneration via the HTTP endpoint.
   - Generic: accepts any spec JSON `{title, description, objectives, steps: [{title, exercise_type, description, feedback}]}`.
   - Production-ready followup: UI-based deep-refine flow where the creator reviews the refined outline + explicitly approves merges before generate.

5. **Creator-prompt generic rules F1/F2/F3** (backend/main.py, `CREATOR_SYSTEM_PROMPT`)
   - **F1 — No invented CLI commands.** Every CLI invocation in instructions/hints/rubrics MUST be quoted verbatim from the runtime-deps brief / source_material, OR be a command in the tool's public docs, OR replaced with generic phrasing. Course on 2026-04-24 invented `claude auth` (real: `claude /login` / `ANTHROPIC_API_KEY`) — a first-CLI-touch trust-breaker.
   - **F2 — Writing a document is NOT a `code_exercise`.** Markdown/yaml/plaintext authoring tasks must map to `terminal_exercise` with `validation.rubric` (LLM-graded) OR a future `document_authoring` type — never `code_exercise` with hidden_tests, which forces the LLM to invent a parser and turns the exercise into regex gymnastics.
   - **F3 — MCP / plugin / integration consumption REQUIRES wiring mechanics.** Read-the-MCP alone is toy. Must include `claude mcp add` (or manual settings.json block), transport (stdio vs HTTP), verification (`claude /mcp list`). Quote the MCP's README verbatim; don't paraphrase.

6. **GHA-grader end-to-end validated** (existing `/api/exercises/check_gha` endpoint from 2026-04-21 §F24)
   - FAIL path: `{ok:false, conclusion:"failure", detail:"Run conclusion 'failure' != expected 'success'"}`.
   - PASS path: `{ok:true, conclusion:"success", detail:"Run completed successfully in <owner>/<repo>"}`.
   - Accepts pasted `https://github.com/<owner>/<repo>/actions/runs/<id>` URL; hits GitHub's public API (unauthenticated OK up to rate limit, honors `GITHUB_TOKEN` / `GH_TOKEN` env for higher). The preferred capstone grader for deploy-attested / build-attested work.

### Course-design-level rules that emerged (add to every future AI-augmented course's source_material):

- **M0 preflight is non-negotiable** for BYO-key courses. A `terminal_exercise` step with `dependencies` config + a trivial `claude` smoke-test query, graded on paste. 3 min, prevents the first-20-min drop-off where learners quit thinking the course is broken.
- **"Feel the pain FIRST, learn setup SECOND"** — M1 jumps in with no CLAUDE.md; M2 teaches CLAUDE.md by having learners write one for the M1 repo they just struggled with. This inverts the usual "setup module before doing anything" and works because the pain motivates the learning.
- **Per-module branches in the starter repo** (`module-0-preflight`, `module-1-starter`, `module-2-retry`, ...). The bootstrap command checks out the right branch automatically; learner never chooses.
- **Capstone via GitHub Actions** — learner forks → pushes → `lab-grade.yml` runs tests + lint → learner pastes the Actions run URL → backend verifies conclusion. Real PR-shipping experience.

### Reusable pattern: verified-facts-block injection for specific tooling (v8.6.1 2026-04-24)

**User directive (2026-04-24):** *"Add this method to CLAUDE.md in case we need similar approach for other technologies later"*

When the LLM generates courses about a specific tool (CLI, SDK, platform, protocol), it often produces plausible-looking but factually wrong syntax — invented subcommands, wrong env vars, wrong config-file locations, wrong exit codes. Training data is stale or incomplete.

**The fix**: do NOT try to fix this with prompt-level "please be accurate" instructions. Instead, inject a **verbatim-facts block** into the Creator prompt whenever the course touches that tool. The block is a paragraph of ~50-150 lines of authoritative facts (command syntax, config file locations, API shapes, exit codes, naming conventions) sourced from OFFICIAL docs at the time of writing. The LLM is told to QUOTE the block, not paraphrase.

**Where it lives**: `backend/main.py`
- `_<tool>_reference_facts()` — the facts block (free-form string)
- `_course_has_<tool>_scope(title, description, source_material)` — boolean gate
- Inject right after `_runtime_deps_brief(...)` in the Creator prompt pipeline

**Reference implementation** (2026-04-24): `_claude_code_reference_facts()` + `_course_has_claude_code_scope()` in main.py. Covers: auth flow (`claude /login` / env var — NOT `claude auth`), capitalized built-in tool names (`Read`, `Edit`, `Bash` — NOT `read_file`), hook contract (stdin JSON, exit 2 = block — NOT env var, NOT exit 1), config file layout (`settings.json` vs `~/.claude.json` vs `.mcp.json`), MCP wiring (`claude mcp add --transport stdio`), custom subagent YAML frontmatter shape.

**Before adding this pattern for a new tool, ask**:
1. Is the LLM making confident factual errors about this tool's API? (Evidence: domain-expert review agent flags specific invented syntax)
2. Are the facts stable? (A block for Kubernetes API-surface is high-maintenance; `claude /login` is not)
3. Can the facts be stated in ~50-150 lines? (If you need 500+, the tool probably isn't a fit for a block — needs full docs fetch)

**What goes in the block**:
- Command syntax that has an invented-looking cousin (e.g. `claude /login`, not `claude auth`)
- Exit codes / contracts that bite silently if wrong (e.g. hook exit 2 vs 1)
- Config-file layout where the LLM guesses the wrong file (e.g. `mcpServers` in `.mcp.json`, not `settings.json`)
- Naming conventions (e.g. capitalized Claude Code tool names)
- Explicit "there is NO X" negative claims for the most common hallucinations

**What DOESN'T go in the block**:
- Pedagogy (that belongs in source_material)
- Full API reference (too large; use docs fetch at need)
- Tool-specific domain knowledge unrelated to authoring errors

**Pattern to follow for each new tool that needs this**:
```python
def _<tool>_reference_facts() -> str:
    return """<TOOL> REFERENCE FACTS (vYYYY-MM — QUOTE VERBATIM):
    === <section 1: common hallucination-prone area> ===
    ...
    """

def _course_has_<tool>_scope(title="", description="", source_material="") -> bool:
    text = f"{title}\n{description}\n{source_material}".lower()
    return any(m in text for m in ("marker1", "marker2", ...))
```

Wire in the Creator prompt assembly (after runtime_deps_brief) with a try/except for soft-fail.

Candidates for future verified-facts-block injection: Kubernetes (versioned API surface changes often — careful), AWS CLI, Terraform (HCL syntax quirks), Docker (buildx flags), specific SDKs if courses start covering them (Anthropic SDK tool_use shape, OpenAI structured outputs).

### Known followups (queued production-ready):

- Creator **deep-refine** UI: let creators SEE the refined outline + push back (add/remove/rename modules) before generate. Closes the 2026-04-24 "M5 team-Claude silently dropped" class of bug at the source.
- `document_authoring` as a first-class ontology type (today F2 is enforced at the Creator-prompt level; making it a registered type with its own grader is cleaner).
- Harden `add_module_to_course` to also support INSERTING between existing positions (not just append) + position shifting.
- **Post-refine structural diff**: auto-compare source_material's enumerated modules vs the refined outline; reject the refine if count mismatches without explicit creator approval.

---

## 🔦 LOG EVERYTHING — running blind is intern work (2026-04-24)

**User directive (verbatim, 2026-04-24):** *"Log everything, not 500 chars. Add to this CLAUDE.md. Running blind is intern work, not an experienced dev."*

### The rule

Any state a bug-fix needs to see MUST be captured to disk FULL, not truncated. Log size counts ("retry feedback: 1636 chars") are worse than useless — they look like they contain info and don't.

### What MUST be logged in full

| Signal | Where it must go | Why |
|---|---|---|
| **Retry feedback (raw tool output)** passed to an LLM retry | `/tmp/retry_feedback/<session_id>/<step_slug>_<ms_ts>.txt` | Attractor diagnosis needs verbatim strings. The `len()` counter tells you NOTHING about why 6 retries all emitted 1636 identical bytes. |
| **LLM prompt + response** for every retry | `/tmp/retry_feedback/.../prompt_<ms_ts>.txt` + `response_<ms_ts>.txt` | To know if the LLM got the LANGUAGE LOCK block, if differential-retries carried the prior attempt, if scaffold pinned, etc. — you need the exact text that went over the wire. |
| **Docker run stderr+stdout tail** | Already captured as part of retry feedback via `_docker_validate_invariant` | Test-runner errors must reach the LLM AND the reviewer in full. No `[-500]` truncation. |
| **Instrumentation rows** (`/tmp/retry_instrumentation.jsonl`) | JSONL with attempt, category, err_hash, tests_passed — already in place | Structured summary for trend analysis; complements the full dumps above. |

### Inline log lines

Every `logging.warning(... %d chars)` style log line that hides content is a regression. When you add a log, choose ONE of:

1. **Inline full content** (when content < 1KB and fits on one screen)
2. **Inline head + path to full dump** (when content is 1-20KB) — pattern:
   ```python
   logging.warning(
       "X failed (N chars, full dump: %s)\n--- head (first 600 chars) ---\n%s\n--- /head ---",
       dump_path, content[:600],
   )
   ```
3. **Path-only** (when content is >20KB or opaque like binaries)

Never log just the length. The ONLY exception is when the content is NEVER useful for post-hoc diagnosis (e.g. binary image bytes) — and even then, log the sha256 hash.

### Enforcement

When reviewing any diff that adds a log line touching LLM retries, Docker invariant runs, or error paths: grep for `%d chars` / `len(...)` / `[:NNN]` patterns. If any truncation-logs appear without a corresponding full-dump path, block the change.

When debugging a stuck pipeline, the FIRST thing to check is: does `/tmp/retry_feedback/` have the dumps from the failing retries? If not, the bug is in the logging, not the pipeline.

### Historical context

TS v12 shipped with 7/10 Python-in-TS course bug. TS v13 shipped with 8/9. In BOTH cases the "1636-char retry feedback" appeared identically across 6 retries — a textbook attractor — but we could not diagnose root cause because we logged only size. 6+ hours of engineering iterated on prompt wording + retry ordering while the actual problem (`course_context["language"]` was never set) was invisible. That's the cost of running blind.

## 🛡️ CRITICAL FIX (2026-04-19 late): Source-Grounded Generation

**The bug**: `_llm_generate_step_content` had NO access to `source_material`. Each step was generated from just the title + description, with the source doc never passed to the per-step LLM call. Result: catastrophic drift on 5/6 doc-grounded courses (MERIDIAN acronym rewritten as medical framework; LB-4721 15mg BID → LUM-301 150mg → LB-047 400mg across modules; Priya Rao → Sarah Chen; David Park → Sarah Chen; 7 real systems in Zephyr DPA replaced with 7 fictional; $420K MTTR paper → "Zenith Corp 340% ROI" fabrication; Oakridge Q3 2025 → "AquaFix Solutions March 2023"). Patient-safety implications for the trial protocol.

**The fix** (backend/main.py):
1. **Thread `source_material` into `_llm_generate_step_content` via `course_context`** — every per-step LLM call now has the full source doc (truncated at 6000 chars).
2. **`_extract_canonical_entities()` regex helper** extracts proper-noun names, dollar amounts, percentages, alphanumeric IDs (CLM-YYYY, LB-4721, ICF-047-v3), phone numbers, emails, URLs, version strings from source. Passed into step prompts as "CANONICAL VOCABULARY — use these exact strings."
3. **Grounding preamble injected when source >= 300 chars**, with 7 explicit rules:
   - Don't invent names (use source names verbatim or omit)
   - Don't invent numbers / thresholds / dollar amounts / dates / phone numbers
   - Don't rename frameworks or acronyms
   - Don't invent parallel scenarios (source is auto-claims → capstone must be auto-claims)
   - Don't replace source's systems/tools
   - When in doubt, quote the source
   - Capstone scenarios must name source's actual personas

**Verification (same Meridian source doc, regenerated post-fix)**:
- **17/17 anchor facts preserved** (100%). All named people (Priya Rao, Karen Liu, Marcus Delgado, Rahul Srinivasan, Amelia Song), all thresholds (0.74, 0.91, 8.5d, 11.2%), all IDs (CLM-YYYY, LTR-4471, LACP-2026), framework (MERIDIAN intact), pitfall (Oakridge + $2.3M) — preserved verbatim.
- Synthetic drill policyholders (John Martinez in CLM-2026-458912, Robert Chen in fraud-detection SJT) correctly appear as scenario-level inventions, which is the right separation.

**Next**: smoke-test the fix on the other 4 DEAL_BREAKER sources (Kelvingrove, Zephyr, Orbital, Lumen) to confirm the fix generalizes. Then upgrade `_is_complete()` to flag generated courses whose content doesn't reference enough canonical_entities (refuse-to-generate rather than accept-drift).

## 🎯 NORTH STAR (2026-04-19 late): Workday Simulator + Case Library

The user's vision (via https://for-emergent.vercel.app/ reference + explicit direction): learners should not march through linear 4-module courses with MCQs. They should drop into a **simulated workday** — multi-pane workspace replicating the exact tools a real professional uses — and work through **numbered cases** (like Emergent's Case 3.1, 4.1, 8.1) that are specific failure-mode / incident / situation drills with short target times (3-20 min) and difficulty tiers (Foundational / Intermediate / Advanced), culminating in ONE "Full Cascade" capstone that synthesizes patterns across layers.

The user's phrasing: **"The more real it is, the more valuable it becomes."**

### Cross-domain patterns (from 5 day-in-life agents: SRE / Data Analyst / SOC / Legal / Staff PM)

**Universal 4-pane workspace shape** every domain has:
1. **Left pane — primary tool**: Grafana (SRE), Looker/Amplitude (Data), Splunk (SOC), MSA-in-Word (Legal), Linear sprint board (PM)
2. **Right pane — inspector/drawer/playbook**: Datadog traces + terminal (SRE), dbt lineage (Data), raw-log JSON (SOC), Notion playbook + prior redlines (Legal), Figma (PM)
3. **Floating Slack** — persistent interruption source with escalating tone ("any update?" → "CFO is asking me now" → "CEO just pinged")
4. **Top bar — timer/queue**: PagerDuty incidents (SRE), meeting countdown (Data), Jira SOC queue (SOC), Ironclad contract queue (Legal), Go/No-Go clock (PM)

**Universal mechanics that kill "quiz feel" and create "job feel"**:
- **Exec Slack interrupts** during deep work. Not scripted prompts at timed offsets — async pings that escalate in tone if ignored.
- **Ambient time pressure**: meeting in 20 min / F deadline / EOQ / launch-week 10am Go/No-Go.
- **99% noise, 1% signal** — filtering IS the skill. SOC: 500 alerts, 12 real. SRE: firehose logs, not gated drips. Legal: 32 pending Ironclad items, 3 deal-breakers.
- **Political framing** — "how you tell the CFO Finance was wrong" matters as much as whether Finance was wrong. Grade the Slack reply, not just the SQL/redline/command.
- **Cross-tool correlation required** — no single pane reveals root cause. SRE: Grafana spike → Datadog trace → kubectl pod. Data: Looker number → Snowflake scratch → dbt PR history.
- **Interruption tax** — deep work crashes every 30-90 min from social pings. Simulator must mirror this.

**Universal grading signals**:
1. Decision quality (did they solve the right problem?)
2. Technical correctness (did the SQL / kubectl / redline actually work?)
3. Communication quality (tone + evidence in the Slack reply, the exec one-pager, the negotiation position)
4. Prioritization (WHAT they chose to ignore is part of the grade, equal weight to what they did)
5. Relationship/trust deltas across stakeholders (did CFO trust increase, did Eng-VP patience hold, did CISO sign off?)

### Case-library course mode (Emergent reference pattern)

Courses using this mode replace the linear "4 modules × 4 steps" skeleton with:
- **A grid of N numbered CASES** (e.g., Case 3.1 "Missing Health Route" / Case 7.1 "Docker Layer Cache Bust" / Case 8.1 "The Full Cascade" CAPSTONE), each with: `number`, `title`, `one-line-symptom`, `discipline_tags[]`, `target_minutes`, `difficulty ∈ {Foundational, Intermediate, Advanced}`, `stack_layers[]`
- **Filter pills** at the top: by discipline, by difficulty, by target time, by failure-mode archetype
- **Difficulty progression markers**: 3-dot pills showing how many difficulty rungs a case climbs
- **One designated CAPSTONE case** at the end — always Advanced, always multi-layer ("The Full Cascade" pattern from Emergent: 4 concurrent symptoms across 4 stack layers, ONE root cause)
- Cases are SHORT (3-20 min each) and TARGETED — not 2-hour modules

### workday_simulator exercise type (to build)

New exercise type that drops learner into the 4-pane workspace described above. The Creator authors per-case:
- `shell_archetype`: one of {ops_infra, data_analytics, security_soc, legal_contract, pm_strategy, design_ux, sales_revops, finance_ledger, people_hr, executive} — picks the pre-baked shell
- `scenario`: initial panes' state (Grafana metric array, Splunk alerts CSV, Looker URL+snapshot, MSA paragraphs, Linear tickets list) + the specific incident/question that started the drill
- `slack_thread`: array of incoming messages with `t_offset_ms` OR `fires_after_action` trigger — mix of useful info, interruptions, exec escalation
- `actions_available`: for each pane, what the learner can DO (click metric panel → drill → related traces; type SPL search; edit Word redline; assign Linear ticket owner; reply in Slack)
- `correlation_path`: the sequence of cross-pane moves that lead to root cause (graded on whether learner found it, not forced order)
- `root_cause` + `correct_actions[]` + `communication_rubric` (tone, evidence-citation, stakeholder-awareness)
- `grading_weights`: decision / technical / comms / prioritization / relationship-deltas

### The scale plan (user asked: "if this works, do top 100 categories")

**10 workspace archetypes × 10 roles each = 100 categories.** Build 10 shells once; Creator authors 10+ case packs per archetype on top. Total: 10 shell builds + ~100 case-library courses (5-8 cases each + 1 capstone = ~800 cases authored).

| Archetype | Shell panes | Example roles (10) |
|---|---|---|
| ops_infra | Grafana, Terminal, Slack, PagerDuty | SRE, DevOps, Platform Eng, DBA, NetOps, Cloud Eng, MLOps, Support Eng, Incident Commander, Hardware Eng |
| data_analytics | Looker/Amplitude, SQL editor, Notebook, Slack | Data Analyst, BI Eng, Data Scientist, ML Eng, Analytics Eng, DS Manager, Experiment PM, Growth Analyst, Financial Analyst, Research Scientist |
| security_soc | SIEM (Splunk), Log drawer, Timeline, Slack | SOC Analyst, Threat Hunter, AppSec, Cloud Sec, IR Lead, Detection Eng, SecEng, GRC, Red Team, Pentest |
| legal_contract | Redline doc, Playbook wiki, Prior-deals, Slack | Commercial Counsel, Privacy Counsel, Employment Counsel, IP Counsel, Litigation, Compliance, Contracts Mgr, Paralegal, Regulatory, Ethics |
| pm_strategy | Linear sprint, Figma, Analytics, Slack | Product Mgr, Staff PM, Group PM, CPO, Growth PM, Ops PM, TPM, PMM, BizOps, Chief of Staff |
| design_ux | Figma canvas, Wireframe gallery, Research transcripts, Slack | UX Designer, UX Researcher, Design Systems, Brand, Content Design, DesignOps, Service Design, IA, Design Lead, UX Writer |
| sales_revops | CRM (Salesforce), Gong calls, Pipeline board, Slack | AE, SE, SDR, CSM, Sales Ops, RevOps, Enterprise Sales, Channel, Sales Eng, Sales Leader |
| finance_ledger | General ledger, FP&A model, Bank feed, Slack | Controller, FP&A, Accountant, Tax, Audit, Treasury, Procurement, IR, CFO Staff, Risk |
| people_hr | ATS, Survey dashboard, Calendar, Slack | HRBP, Recruiter, Talent, Comp, L&D, People Analytics, DEI, EX, HR Ops, CPO |
| executive | KPI dashboard, Board deck, Exec 1:1 calendar, Slack | CEO, COO, GM, CRO, CTO, CMO, VP Eng, Founder, Consultant, Board Member |

**Rollout sequencing** (POC → scale):
1. Ship ONE archetype shell (pick ops_infra — specs are sharpest from SRE agent) + case_library UI + regenerate SRE Emergent course in new format. Budget cost: Creator regen ~$0.50.
2. Have user validate the POC. If good → greenlight scale.
3. Ship remaining 9 shells (engineering: 2-3 weeks of frontend per shell; can overlap).
4. Batch-generate 100 case-library courses via Creator (10 per archetype × 10 archetypes). Cost: 100 × ~$0.35 = ~$35.



## 🔒 HARD INVARIANT #2: Bulk Live-Preview QC — 103/103 Passing (2026-04-19)

After a REJECT verdict from the Emergent-course live QC agent (3 P0s), I shipped the following root fixes (none touch course data — all at Creator/engine/frontend level):

1. **Full answer-key sanitizer** (`_sanitize_step_for_learner` in `backend/main.py`) strips: `validation.*` answer keys, `demo_data.*` top-level answer keys, `items[].correct_position/category/rank`, `options[].correct/explanation`, scenario_branch `steps[].options[].correct/explanation`, `bugs[]` replaced with opaque count markers. Verified: 103/103 courses have ZERO leaked answer fields in JS state.
2. **`/api/exercises/validate` enriched response**: now returns `item_results[]` (per-item correctness with user_category/user_position/user_rank vs correct_*), `correct_answer` (canonical), `explanations[]`. Frontend renders post-submission feedback from this response — no pre-loaded answer fields needed at render time.
3. **Deep-link router**: `parseHash` now accepts bare `#<courseId>` (was requiring `#<courseId>/<moduleId>`). `restoreFromHash` fetches unknown courses directly when not in the cached catalog.
4. **Categorization frontend**: preserves real item IDs (was overwriting with array index, breaking server-side grading); renders per-item teaching feedback with "You put in X, correct is Y" + optional explanation.
5. **Ordering frontend**: uses new `item_results` from server to show per-item position feedback + full "CORRECT ORDER" block when learner gets any wrong.
6. **Learner-side expertise picker REMOVED**: complexity is Creator-chosen via `course.level` (accepted on `/api/creator/start` as optional `level` field, or LLM-inferred + normalized to Beginner/Intermediate/Advanced). Badge is read-only, shown in sidebar header. Stale "Builder mode" label gone.

**Bulk live-preview QC results (2026-04-19):** drove an actual browser (Claude Preview) across all 103 courses, loading each, checking JS-state for answer-key leaks, verifying content renders, catching exceptions. Pass rate: **103/103**. Zero faults. Exercise-type coverage: categorization, ordering, sjt, mcq, code_review, scenario_branch, adaptive_roleplay, voice_mock_interview, incident_console, system_build, fill_in_blank, concept. Validated interactively: ordering (3/5 wrong → correct teaching feedback with ✓/✗ per item + full CORRECT ORDER block), categorization (0/8 wrong → per-item teaching "You put in X, correct is Y"). Regenerated Emergent v2 via Creator flow (invariant-compliant): level="Intermediate" persisted, 0 leaks across all 4 modules, $0.31 cost.

Rule going forward: **any fix required by QC goes at the Creator / engine / frontend level, never by editing course data directly.** Courses that fail re-QC after a root-level fix must be regenerated through `/api/creator/*` — same title/description — to prove the fix propagates.

## 🔒 HARD INVARIANT: All Course Creation & Edits Go Through the Creator Dashboard

**This is the most important operational rule. It overrides any convenience.**

All new courses, all course edits, all content regeneration MUST flow through the public Creator API:
- `POST /api/creator/upload` (optional — file seed)
- `POST /api/creator/start` (title + description + course_type)
- `POST /api/creator/refine` (answers to clarifying questions)
- `POST /api/creator/generate` (persists the course)

**Forbidden:**
- Writing Python seed scripts that `import Course/Module/Step from backend.database` and insert rows directly (e.g. `seed_roleplay_course.py`, `seed_incident_course.py` — these are historical exceptions that predate this rule and must be regenerated via Creator when revisited).
- Hand-patching `backend/courses/*.py` files to "fix" a live course. If a course is broken, the fix goes into the Creator workflow (prompt, post-processing, fallback, quality floor) and the course is REGENERATED from its original title/description.
- SQL `UPDATE` statements or direct DB manipulation to adjust course content. Even typo fixes go through Creator regeneration.
- Any script that constructs `Course()` / `Module()` / `Step()` SQLAlchemy objects and commits them.

**The only exception**: pure data-shape migrations (schema changes in `database.py` that add/rename columns) — but these must NEVER change course CONTENT, only the container around it.

**Why this rule matters:** The Creator is the product. Every direct-write workaround hides a Creator bug. When the Creator is forced to produce every course end-to-end, its limitations surface immediately and become fixable. Every seed-script workaround was a missed opportunity to improve the Creator. This is how the LMS evolves itself.

**Enforcement checklist for every new course idea:**
1. Can I express this as a title + description + answers to 3-4 clarifying questions? (Yes → use Creator.)
2. Does the Creator produce the right exercise types for this course? If not → fix the Creator's taxonomy/prompt, not this one course.
3. Does the generated content meet the quality floor? If not → strengthen `_is_complete()` checks, not this one course.
4. Does the result adopt new pedagogies (adaptive_roleplay/incident_console/simulator_loop) where appropriate? If not → improve the Creator system prompt to teach those types.

Any time a reviewer is tempted to write `UPDATE courses SET ...`, that's a signal: **the Creator has a bug, fix the Creator, regenerate the course.**

## Final Goal

Build an **AI-first Learning Management System** for both learners and course creators.

**The outcome bar**: Once a learner completes a course, they should be competent enough to take a real-life scenario at their workplace, build a system that integrates with others, and use the skill to deliver results for their company. The outcome must be real, not toy. Example: after a Vector DB course, the learner should be able to identify opportunities in their org where vector search creates advantage, pitch the solution to leadership, and build + deploy the system end-to-end in production. Some things can be learned on the way, but this production-readiness must be the intent driving all content and assignments.

### For Creators
- Creators provide curriculum files, assignment guides, or even a single paragraph of context.
- The LMS processes the input, asks follow-up questions and clarifications iteratively until it deeply understands the course requirements.
- The process keeps creators involved — they see how the LMS is building the course, can share inputs/comments at each stage.
- **Optimize for**: reducing revision cycles to publish, creator confidence in output quality.

### For Learners
- Implement Clicky-style AI assistant behavior (see `../ai-skills-lab` for reference):
  - For **concept questions**: thorough, uses analogies, explains the WHY deeply.
  - For **exercise questions**: NEVER gives complete solutions. Instead: explain approach, give one-line hints, ask guiding questions, point to relevant prior concepts.
  - Errors are teaching moments — diagnose root cause first, then suggest fix.
- Learners pick their expertise level and the course tailors accordingly:
  - **Beginner**: hand-holding, step-by-step, visual explanations
  - **Intermediate**: less scaffolding, more code, real patterns
  - **Advanced**: building on terminal/VSCode, deploying to cloud/Vercel, production-scale projects

## Course Design Principles

### Introduction (>90% engagement target)
- Must be **highly interactive and engaging hands-on content** that makes the learner understand WHY the skill matters.
- No verbose walls of text. Be creative — try multiple approaches.
- Use real scenarios, live demos, interactive visualizations, "try it now" moments.
- Hook with a compelling problem before explaining the solution.

### Content Structure
- **No rote learning.** Objective questions (MCQ) are lowest priority.
- Think of smart, creative ways to teach each topic:
  - Scenario branching with real-world consequences
  - Code exercises with progressive difficulty (not toy examples)
  - Drag-and-drop assembly (Parsons problems — max 8 lines)
  - Categorization with domain-realistic items
  - Situational Judgment Tests for soft-skill topics
  - Code review with planted bugs at realistic locations
- 3-layer module structure: **Concept** (contextual narrative) → **Exercise** (application) → **Reflection** (insight/takeaway)

### Difficulty & Depth
- Use `../ai-skills-lab` as a quality baseline — those courses are a starting point but **lack depth, creativeness, and difficulty progression**.
- Production-grade exercises: e.g., Vector DB with 100,000 documents and high retrieval accuracy, not 5-item toy demos.
- Progressive complexity: solo task → automated tooling → full production pipeline → deploy to cloud → integrate with real services.
- Final modules should have learners deploying real systems on AWS/GCP/Azure/Vercel — not just writing code in a browser sandbox.
- Teach the surrounding skills too: how to identify where this technology fits in your org, how to pitch it, how to handle production concerns (scale, monitoring, cost, security).

## Exercise Type Taxonomy (12 types — voice_mock_interview added 2026-04-19)

| Type | Use For | Data Shape |
|------|---------|------------|
| `concept` | Teaching content (HTML) | `content` only |
| `code` | Read & run demos | `code` + `expected_output` |
| `code_exercise` | Hands-on coding with TODOs | `code` + `expected_output` + `validation.hint` |
| `fill_in_blank` | API/syntax recall | `code` with `____` + `validation.blanks[]` |
| `parsons` | Code assembly (max 8 lines) | `demo_data.lines[]` + `demo_data.distractors[]` |
| `ordering` | Process/sequence understanding | `demo_data.items[]` + `validation.correct_order[]` |
| `categorization` | Classification exercises | `demo_data.categories[]` + `demo_data.items[]` + `validation.correct_mapping{}` |
| `scenario_branch` | Decision-making with consequences | `demo_data.scenario` + `demo_data.steps[].options[]` |
| `sjt` | Judgment/soft-skill ranking | `demo_data.options[]` + `validation.correct_rankings[]` |
| `code_review` | Bug finding in realistic code | `demo_data.code` + `demo_data.bugs[]` + `validation.bug_lines[]` |
| `mcq` | Quick knowledge checks (use sparingly) | `demo_data.options[]` + `validation.correct_answer` |
| `system_build` | Build & deploy a real system to AWS/GCP/Azure/Vercel | `code` + `deployment_config` + `validation.endpoint_check` |
| `adaptive_roleplay` | TEXT-based counterparty with hidden state (email/Slack/spec-review contexts) | `demo_data.scenario_prompt` + `demo_data.counterparty{persona_system_prompt, hidden_state{}, state_update_rules, escalation_triggers[], win_conditions[]}` |
| `voice_mock_interview` | LIVE VOICE interviews / pitches / coaching — learner speaks via mic, interviewer replies via TTS | same as adaptive_roleplay PLUS `voice_mode=true` + `interview_style` + `opening_question` |
| `incident_console` | Scripted production-outage simulator (zero LLM cost/session) | `demo_data.alert` + `commands[]` + `log_stream[]` + `slack_prompts[]` + `cascade_rules[]` + `accepted_remediations[]` |
| `simulator_loop` | Generic tick-based simulation (umbrella primitive) | `demo_data.initial_state` + `events[]` + `actions[]` + `win_conditions[]` |

### `system_build` — Build & Deploy Exercises
The highest-difficulty exercise type. Learners build a real system and deploy it to a hyperscaler (AWS, GCP, Azure) or platform (Vercel, Railway, Fly.io). This is the capstone format for production-readiness:
- Learner writes real code (not sandboxed — runs on their machine/cloud)
- Includes infrastructure config (Dockerfile, terraform, CDK, serverless.yml, etc.)
- Validation checks a live endpoint or deployment artifact
- Progressive: local build → containerize → deploy → integrate with other services → load test
- Example: "Deploy a FastAPI semantic search service backed by Pinecone to AWS Lambda, handle 100 req/s, return p95 < 200ms"

## Validation & Scoring
- Multi-dimensional scoring with partial credit (LCS for Parsons, off-by-one tolerance for SJT)
- Per-item feedback breakdown, not just pass/fail
- Code exercises: sandboxed execution with mock modules (anthropic, weaviate, langchain, pinecone)
- Blocked modules in sandbox: os, sys, subprocess, shutil, pathlib, socket, ctypes

## Key Metrics to Optimize

1. **Course Quality & Creator Experience** — Depth, creativity, production-readiness. Reduce revision cycles. Keep creators in the loop, take their inputs.
2. **Learner Completion & Real-World Skill Transfer** — Learners with intent complete the course and can apply skills to real problem statements at their workplace. The full chain: understand the need → identify opportunities in their org → pitch to leadership → build end-to-end → deploy to production → integrate with existing systems → deliver measurable results. This is the north star — not "I learned the API" but "I shipped a system that my company uses."
3. **Introduction Engagement (>90%)** — The intro of every course must hook learners. Highly interactive, no verbose content, creative approaches.
4. **Production Readiness** — Every course must end with the learner having built something deployable. Not a notebook, not a script — a system with an API, infra config, monitoring, and the ability to handle real-world scale and edge cases.

## 🎨 Teaching Philosophy — Be Creative, Ship Real Experiences

Be creative and novel about how you teach. Do not default to "read a paragraph, then answer a multiple-choice." Examples of what GOOD teaching looks like:

- **SRE course**: Drop the learner into a live-feeling production environment where metrics spike, services go down, and they must debug and fix. Simulated but reactive — the learner's inputs change what happens next. Postmortem exercise at the end.
- **Incident-response**: A paged-at-3am scenario with live logs scrolling in the UI, partial information, and time pressure. Learner decides what to page next, what to roll back, how to communicate to stakeholders.
- **Legal/compliance**: Simulated clients sending emails with hidden legal issues. Learner replies. AI evaluates whether they spotted the issue.
- **Negotiation**: AI-driven counter-party that adapts its offers based on the learner's moves. Outcome depends on the learner's skill.
- **Data-analysis**: A dirty real-looking dataset with planted biases. Learner runs hypotheses; the UI reveals what they missed.
- **Design review**: A wireframe gallery where bad designs are interspersed with good. Learner annotates with explanations; AI scores the critiques.
- **Architecture review**: An intentionally-flawed system diagram. Learner marks problems; scoring is on rationale, not just flags.

Exercise types are a palette, not a constraint. If inventing a new exercise type serves the pedagogy, invent it. The bar is: **would a learner finishing this course feel they did the real work, or just watched a video?**

## 🔁 Post-Upgrade Review Protocol — MANDATORY

After ANY major platform upgrade (new feature, schema change, Creator behavior change, sandbox change, significant Frontend refactor), you MUST run the full review cycle:

1. **Code review loop — ≥10 iterations.** Spawn parallel agents to audit the diff for: security, correctness, schema drift, frontend/backend contract alignment, error handling, edge cases. Fix every P0/P1 before proceeding.
2. **Domain-expert review loop — ≥10 iterations.** Spawn parallel agents with DIFFERENT personas (SRE, ML engineer, PM, UX researcher, designer, lawyer, compliance officer, etc.) to review course content for their domain. Each reviews the same platform from their lens. Publish good + shortcomings.
3. **Product UX/UI review loop.** Spawn agents that behave like real learners — end-to-end browser journey with screenshots. Grade on: first-impression polish, intro engagement, friction points, mobile behavior, accessibility.

Reviews continue until **≥3 independent reviewers ACCEPT** in the same loop without new P0s. No "we're close enough" — re-run until clean.

### Review-Agent Behavior Rules — MANDATORY

Every review agent MUST:

1. **Open the course via the actual web UI** (http://localhost:8001), not just curl the API. The UI is the product. Static API data can be "correct" while the rendered widget is broken.
2. **Solve every exercise as a real learner would** — click options, drag items, fill in blanks, submit answers, read the feedback. Do NOT shortcut by inspecting `validation.correct_answer` in the JSON and confirming it works.
3. **Attempt WRONG answers too.** Submit a plausible-but-incorrect answer and verify the error feedback is actually useful for learning (points at what's wrong, hints at the concept, doesn't give the answer away).
4. **Screenshot every step.** Dark-theme violations (white-on-white widgets), overlapping UI, broken layout are invisible without pixels. Any interactive widget with `<style>` inside the concept content MUST be visually verified.
5. **Grade on "does this TEACH?"** not "does this render?". Criteria:
   - Does the exercise require THINKING or is it pattern-matching (MCQ with obvious answer)?
   - Does getting it WRONG teach you something?
   - Does getting it RIGHT feel earned?
   - Would a real learner retain the concept a week later?
6. **No spoon-feeding.** If Clicky gives answers, if task descriptions contain the answer, if wrong-answer feedback reveals the correct one — that's a failure. Learners should feel a bit stuck and then unstuck through their own effort.
7. **Test on both Builder and Explorer expertise levels.** The adaptive rendering is supposed to differ — verify it does.
8. **Check for accessibility basics.** Keyboard navigation of drag-drop exercises, focus states, sufficient color contrast, screen-reader labels on interactive widgets.

Reviewer verdict templates must include: screenshots, specific wrong-answer attempt + feedback received, assessment of whether the exercise teaches vs tests.

### Creative-Review Agents (≥3 per upgrade cycle) — MANDATORY

Separate from the correctness/domain/UX reviewers, spawn **≥3 independent creative reviewers** whose ONLY job is to imagine better pedagogy. They must not rubber-stamp what exists; they must propose novel formats that deliver real-world experience.

Their brief:
> "The current course teaches [X] via [existing exercise format]. Propose 2-3 alternative ways the same skill could be learned that mirror how it's actually practiced in the real world. Prefer: drop the learner INTO a failing/evolving system where they must diagnose and act, rather than read-and-answer. The test of success: a learner who completes this feels they 'lived' the skill, not 'studied' it."

Examples of target pedagogy:
- **SRE course**: drop learner into a live-looking production console with alerts firing, logs scrolling, tickets piling up. They must triage, run commands (simulated), make incident-commander decisions. Grade on response time, accuracy of hypothesis, communication clarity.
- **Security incident response**: a phishing email arrives in their inbox view, then another, then a Slack panic from a colleague. They must choose: report? investigate? quarantine? notify legal? The scenario evolves based on their moves.
- **Product management**: a Slack channel with 5 stakeholders all messaging contradictory requirements + a roadmap meeting in 30 min. Learner must synthesize, prioritize, communicate.
- **Sales**: an AI-powered customer who answers questions, raises objections, and will/won't close based on the quality of learner's pitch.
- **Legal/compliance**: a client sends an ambiguous email. Learner must identify the hidden legal risk, draft a reply, escalate if needed. AI grades on whether the risk was spotted.
- **Data analysis**: a realistic dirty dataset with planted biases. Learner runs queries; the UI reveals what they missed (Simpson's paradox, selection bias, data leakage).
- **Architecture / system design**: a live whiteboard where the learner draws, and the AI interviewer probes ("what if traffic 10×?", "what if the primary region goes down?"), with scoring on depth of reasoning.

**The primary pedagogy direction**: stop asking "which of these 4 options is best?" Start putting them in the situation where they must choose, act, see consequences, and iterate.

Creative-review agents publish: 2-3 reimagined exercise formats per course, with a concrete UI sketch of how the widget would work. The Creator team then picks the best and implements it as a new `exercise_type` or a parameterized variant.

Creative reviews have equal veto power with correctness reviews — a pedagogically boring course that technically works is still a fail.

### Learnings from past review cycles (keep growing this list)

- **White-on-white widget bug (2026-04-18):** Creator-generated intro `<script>` widgets sometimes used `background: #fff; color: #fff`-adjacent CSS despite the prompt specifying dark-theme colors. Fix: Creator prompt now enforces mandatory inline CSS variables; reviewers must screenshot every widget.

## 🌑 RECURRING BUG: Dark-theme violations in Creator content — MANDATORY post-gen sanitizer

**The bug keeps coming back.** The Creator LLM ignores the "NEVER use `#fff`, `white`, `#f*`, `#e*`" rule in the prompt roughly 10-20% of the time, emitting light-pastel backgrounds (`#f8f9fa`, `#e3f2fd`, `#f3e5f5`, `#e8f5e8`, `#fafafa`, etc.) in concept-step `<div>` widgets. Since our site background is near-black, the text in those widgets renders as dark-gray-on-light-gray — near-invisible. User screenshots have filed this bug 3× now (2026-04-18 white-on-white; 2026-04-19 pastel widgets; 2026-04-20 ReAct Loop Visualization pastels).

**Non-negotiable mitigation — present in `backend/main.py`:**
1. `_darkify_html_content(html)` is called on EVERY step's `content` field before DB persist, in BOTH the `_is_complete=True` path and the fallback path. It rewrites:
   - `background: #f* / #e* / white / lightgray` → `--bg-tertiary` (#1c2333)
   - `color: white / #fff*` → `--text-primary` (#e8ecf4)
   - Any `style="background: …"` missing an explicit `color:` gets `color: #e8ecf4` injected.
2. The Creator prompt retains its "mandatory dark palette" rules as the first line of defense, but the sanitizer is the last-line guarantee.

**If you see this bug again on a NEW course:** The sanitizer is bypassed. Check:
- Is the content being persisted via a non-standard path (e.g., a legacy seed script)?
- Did someone edit `_darkify_html_content` and break a regex?
- Is the light-bg pattern a shape the regex doesn't catch (`rgb(248, 249, 250)` instead of hex)? — extend the regex.

**Rule going forward:** every new persist path for step content MUST call `_darkify_html_content`. Grep for `Step(` before shipping to verify.

## 🔀 RECURRING BUG: Flow / process widgets rendered as TEXT LOGS instead of SVG graphs (2026-04-20)

User screenshot filed 2026-04-20: a concept-step "Simulate the Nexus document processing flow" widget rendered as a plain text log — `Turn 1 (assistant): Calls OCR tool\ntool_use: ocr_processor\nTurn 2 (user): Returns OCR results\n...` — on a dark card with a Next Turn button. Technically dark-theme compliant, but aesthetically terrible and pedagogically weak: text growing downward teaches nothing visual about the flow shape (which nodes connect, what the loop is, where state transitions happen).

**Mitigation shipped:** Creator prompt (`_llm_generate_step_content` at `backend/main.py:~3576` and the non-intro `concept` branch below it) now includes a MANDATORY VISUAL-FIRST RULE — for any widget depicting a multi-step flow / pipeline / state machine / agent turn loop / request journey, the Creator MUST emit an SVG `<rect>`-node + `<path>`-arrow graph with CSS-animated fill transitions on the current step. Text logs like `Turn N (role): action` are explicitly BANNED and called out by name. A canonical SVG skeleton (700x180 viewBox, rounded rects, marker-arrowheads, `#2a3352` inactive / `#4a7cff` active / `#2dd4bf` done) is embedded in the prompt so the LLM has a concrete template to adapt.

**Rule going forward:** any "demo / simulate / trace / walk through" widget MUST be a graph, not a log. If a reviewer finds a new text-log flow widget in a Creator-generated course, the fix goes into the prompt (strengthen the ban or add more anti-patterns); regenerate the course; never hand-edit the step HTML.

## 📚 Maya beginner-learner review (2026-04-20) — batch of Creator-prompt tightenings

Maya (beginner-programmer learner agent) walked Agent Harness end-to-end and flagged 5 issues, all fixed at the Creator-prompt layer in `_llm_generate_step_content`:

1. **Ordering steps dump undefined jargon.** Step M2.S0 "The ReAct Loop, Step by Step" shows 7 items with `stop_reason` / `tool_use` / `tool_result` and no definition. Fix: ordering prompt now mandates an 80-150-word PREAMBLE that defines any jargon before the item list, frames what "correct order" represents, gives a daily-life analogy. Same fix pattern applies to categorization + parsons (extend when next round surfaces them).
2. **Code_review dumps code with zero briefing.** M1.S3 "Anatomy of a Minimal Harness" = 69 lines of SDK code, only instruction "Click on lines you think contain bugs." Fix: code_review engineering prompt now requires a 2-paragraph BRIEFING (what the code is trying to do) + a numbered/bulleted list of 4-6 BUG CATEGORIES to hunt for (security / resilience / API contract / state / logging / concurrency). The briefing is non-optional.
3. **Fill_in_blank with domain-specific enum answers leaves beginners guessing.** M3.S0 "Designing a Tool Schema" has 4 blanks expecting VectorFlow-internal JIRA statuses ("In Progress / Code Review / Done") with zero context — Maya guessed "in_progress / resolved / closed". Fix: fill_in_blank engineering prompt now mandates a visible LEGEND/SIDEBAR card listing all valid enum values with one-line meanings, PLUS a tiny worked example above the blanks showing one field filled correctly.
4. **Code_exercise content rendered as wall-of-text.** M3.S1 "Register Three Tools" renders edge-to-edge prose, duplicate title, `[ ]` text rendered as raw markdown source, `read_file` / `post_slack` inlined as prose not code. Fix: code_exercise content prompt now requires styled CARDS per section (background div + border + padding + margin), inline code wrapped in styled `<code>`, `<ul>` for checklists (never raw `[ ]`), and NO duplicate step title inside content.
5. **Engineering capstone drifted to UX research content.** M5.S2 "Build &amp; Ship the Triage Harness" body opened "Lead a comprehensive UX research initiative to validate the design assumptions for VectorFlow's agent monitoring dashboard" — the wrong job entirely. Fix: system_build engineering prompt now has a BANNED OPENING PHRASES list ("Lead a user research study", "Design a UX research plan", "Conduct N user interviews", "Synthesize findings into insights", "Present recommendations to leadership", "Design the onboarding experience", "Author a product strategy memo", "Run a design sprint") — if the capstone opens with any of those, the LLM is instructed to STOP and rewrite so the body asks for code that runs. Example correct openings included in-prompt.

**Verification pass:** regenerate Agent Harness via `/api/creator/start → /refine → /generate` with the same title+description, walk steps 918/1, 918/2, 919/0, 920/0, 920/1, 922/2 as a beginner. Every one of the 5 issues must be gone on the fresh course.

- **Overlay persistence bug:** Expertise modal's `backdrop-filter: blur` lingered after selection because `display: none` was delayed 280ms. Fix: immediate display:none.
- **Route state race:** `state.currentCourse` could show a stale course after rapid-clicking the catalog. Fix: `_currentEnterCourseRequestId` guard token.
- **Validation schema drift:** Backend validators read `validation.*` but Creator sometimes put data in `demo_data.*`. Fix: merge both in the validate endpoint + derivation logic in each validator.
- **Empty capstone bug:** LLM occasionally returned a capstone with phases=default-fallback-labels; completeness check now rejects generic "Plan the Deliverable" labels.
- **Code-type mismatch:** Creator generated `code_exercise` / `parsons` for non-engineering courses. Fix: `_enforce_exercise_type_fit()` remaps. `fill_in_blank` preserved because it's valid for text-templates.
- **Capstone template leak (2026-04-18):** When LLM returned insufficient `system_build` content, the fallback block wrote generic phrases like "The core idea behind {TITLE}", "Reflection prompt: spend 60 seconds...", "Define success criteria for {TITLE}" — with the step title substituted in. Reviewers saw this as template placeholder output. Fix: `_is_complete()` now rejects any content containing template-leakage phrases; all phases/checklist items must avoid generic fallback labels (switched `any()` to `all()` check); strict GENERIC_CONTENT_PHRASES blocklist forces regeneration before using fallback.
- **Course-switching state bleed (2026-04-18):** `onCourseClick('B')` while already inside course A left sidebar modules from A visible. `goToStep(N)` then navigated into A's module IDs even though main pane showed B's steps. Fix: `onCourseClick` now tears down `currentCourse`, `currentModule`, `modules`, `currentModuleData` before loading the new course; sidebar module list cleared immediately.
- **Empty code-exercise bodies (2026-04-18):** LLM sometimes returned code_exercise steps with `# Your answer here` as the entire code field. Stats course was the worst offender — 4 of these stubs. Need Creator lint to reject code_exercise steps whose code is just placeholder comments without any scaffold/imports/structure.
- **Sandbox module gaps:** `kubernetes`, `scipy.stats`, `statsmodels`, `numpy`, `pandas` were not mocked → K8s and Stats course code_exercises failed on import. Added stubs to `_build_mock_modules()`. Whenever a new course topic uses a library not yet stubbed, add it before publishing.
- **Source-PDF fidelity:** LLM paraphrases source docs into filler rather than quoting actual handbook text. IT-services domain reviewer flagged courses as "AI-filler with sprinkled keywords". Creator should preserve verbatim chunks of source text (module names, week numbers, handbook headers) where it improves faithfulness. Consider a "faithfulness score" against source chunks.
- **Duration compression misleading:** 23-week Mysore collapsed into 4 modules × 2 hrs is a 200× compression. Title says "Complete TCS ILP" — overpromise. Either generate proportionally more modules OR frame as "highlights" in subtitle.
- **incident_console cascade-rules never fired (2026-04-19):** SRE review agent discovered the engine's cascade check used `trigger in cmd` (substring match) but Creator-generated triggers use regex syntax (`kubectl delete pod.*payment-api`). The `.*` never matched literally. Destructive commands had zero penalty, `blast_radius` stuck at 1.0 regardless of learner actions. Fix: `re.search(trigger, cmd)` with substring fallback. Without this fix, the capstone can't grade the behavior it claims to grade in the rubric.
- **incident_console initial_logs leak (2026-04-19):** The gating filter was `if not log.get("gated_by")` — a field Creator-generated courses don't populate (they gate via reverse mapping `commands[].unlocks[]`). Result: all 9 logs leaked on session start, pre-revealing the smoking-gun lines. Fix: compute the set of gated log IDs from `commands[*].unlocks[*]` and exclude those from initial_logs too.
- **incident_console Slack prompts never surfaced (2026-04-19):** Creator generates realistic human-time offsets (90s, 3min, 5min, 7min). A competent learner resolves in 60-90 sim-seconds, so `slack_prompts_shown=0` and `comms` score awarded a free 1.0, making the rubric untestable. Fix: additionally fire prompts on command-count milestones (1st prompt → 1 cmd, 2nd → 3 cmds, 3rd → 5 cmds, ...). Time-based firing still works as a fallback.
- **adaptive_roleplay scoring bug (2026-04-19):** Director-of-Eng review agent found 10/10/10 concede scored 0.5. Two compounding bugs: (a) formula only looked at delta, ignoring absolute final state AND outcome; (b) `outcome` was a local variable in the turn endpoint, never persisted into `sess` before `_compute_roleplay_debrief(sess)` read `sess.get("outcome")` — which always returned None and fell into the neutral 0.4 branch. Fix: rewrite scorer as weighted sum (50% outcome × 30% final-state-floor × 20% trajectory) AND set `sess["outcome"] = outcome` before the debrief call. After fix: 2-turn concede with state 8/9/7 scores 0.79; 10/10/10 concede scores ~0.95.
- **Roleplay rubric tags missing BATNA/anchoring (2026-04-19):** Creator-generated rubric tags listed outcome-level labels (`stakeholder_relationship_management`, `business_context_awareness`) instead of the actual negotiation skills (`BATNA`, `anchoring`, `emotional_regulation`, `genuine_vulnerability`). Reviewer flagged: "the rubric names outcomes instead of skills." Needs Creator-prompt tightening to require canonical skill tags for each scenario type.
- **Roleplay module filler (2026-04-19):** Creator generated a concept step whose body read "In the work you will do after this course, this concept shows up most often in: day-to-day decisions about *the conversation playbook: what to say (and never say)*, where applying it poorly results in measurable cost..." — boilerplate that references its OWN module title verbatim. Reviewer: "recognizable filler within 10 seconds." Needs `_is_complete()` rejection of content containing own-module-title self-references.
- **Creator-compliance trade-off (2026-04-19):** Creator-generated courses have MORE BREADTH (4 modules vs hand-coded's 2, richer pedagogical scaffolding like "Pressure Chamber → Data-Driven Pushback → Conversation Playbook → Live Fire") but LESS DEPTH at the capstone (hand-coded's step 463 "Observer Not the Fixer" is sharper than anything Creator produced). Direction: tighten Creator prompt to instruct "name the junior antipattern explicitly in the pre-capstone concept step" for every immersive-capstone course.
- **Verified fix propagation (2026-04-19):** After Creator prompt hardened (canonical rubric_tags per scenario family, persona-must-not-coach, filler-detection in `_is_complete`), regenerated "Defending Scope Under Executive Pressure v2" (course `created-101ba7848a1f`) produced `rubric_tags: ['anchoring', 'data_specificity', 'phased_alternative', 'BATNA', 'emotional_regulation']` — **5/6 canonical tags adopted** (previously outcome-level labels). Persona prompt opens "You are Diana, VP Engineering under intense board pressure... zero patience for..." — no coaching, no complimenting. Zero filler detected. Generation cost: $0.24 / 66s. This closes the full review→fix→regenerate→verify loop in one iteration.
- **Pedagogical-delta validation on fixed scorer (2026-04-19):** Ran STRONG vs WEAK strategies against the v2 course on the fixed scorer. STRONG (data + phased alt + transparency + concrete commit) → `concede` in 4 turns, score **0.83**. WEAK (dismissive "board doesn't understand software" + hedging + defensive + panic-commit) → `escalate_CTO` in 2 turns, score **0.10**. **Gap: 0.73.** This is exactly what a working scoring rubric should produce: a skill-proportional score curve with large headroom between "learned the move" and "hasn't learned the move." The pre-fix scorer produced identical 0.5 scores for both these strategies — it had no pedagogical signal at all. The new three-component weighted scorer differentiates by 7.3× on a 0-1 scale for the strongest vs weakest valid plays.
- **Frontend render of new scorer fields (2026-04-19):** `score_breakdown` (the 3-component weighted sum: 50% outcome / 30% state-floor / 20% trajectory) is now shown in the roleplay debrief as a transparent "where your points came from" panel. Critical for learner-feedback quality: without it, a 0.10 score is just "bad" — with the breakdown, the learner sees exactly which lever (outcome? state? trajectory?) was missing. Also added `_classifyOutcome()` + `_humanizeOutcome()` so Creator-invented outcome strings (`escalate_CTO`, `become_openly_hostile`, `demand_immediate_escalation_to_VP`, `end_meeting_abruptly`, `ready_for_renewal_call`) render as colored (win=green / lose=red / neutral=grey) Title-Case labels instead of raw snake_case. Tested against 8 representative outcomes. Previously only 5 canonical strings (`concede`, `escalate`, `escalate_to_ceo`, `walk_away`, `timeout`) rendered correctly; Creator-generated outcomes fell through to raw text.
- **Pedagogical validation: counterparty correctly rejects vague/placeholder strategies (2026-04-19):** Ran a scoring-consistency test across 8 courses with a STRONG strategy that used template placeholders (`[specific number + mechanism]`, `[genuine vulnerability with a specific number]`). Result: 6/8 courses escalated in 1-2 turns with the placeholder strategy — the counterparty's state_update_rules correctly read placeholders as "evasive/unspecific/hedge" and punished them. The one course that didn't escalate under this treatment (Eng Manager, concede/0.77) had a more forgiving persona. This is actually a positive signal about the whole system: counterparties don't rubber-stamp anything typed in, they require actual concrete content. The lesson for the test harness (and learners): "strong" isn't a vibe — it's specificity.
- **Universal guardrail fix (2026-04-19):** Regenerated all 4 brittle courses (Sales Eng, Tech Writer, Mobile Eng, Staff PM) via Creator after adding guardrails. All 4 produced healthy persona states: Sales Eng {tech_conf 6, vendor_trust 5, urgency_pressure 7}, Tech Writer {pat 6, tr 5, flex 6}, Mobile Eng {pat 6, tr 7, conf 5}, Staff PM {conf 5, tr 6, urg 7}. All escalation thresholds at `<= 0`. Plus Data Analyst v2 {tr 6, pat 7, pc 5}, escalation `<= 0`. Staff PM v2 end-to-end: STRONG=`approve_with_full_budget` 0.77 vs WEAK=`walk_away` 0.03 → gap **0.74**. The guardrails fix was universal: 5/5 regenerations landed non-brittle personas from a single Creator-prompt change. The Creator-compliance invariant is paying dividends.
- **Test-harness learning (2026-04-19):** A one-size-fits-all STRONG strategy (negotiation-flavored) doesn't validate course-specific pedagogy — the Data Analyst v2 CFO correctly escalated at 0.01 because the STRONG script talked about "phased rollout in 4 weeks" when the scenario demanded a churn number before earnings call. This is the AI counterparty catching a real-world failure mode: answering a different question than the one asked. Future cross-course consistency tests must use scenario-specific STRONG strategies; generic "empathy + data + phased alt" only works when the scenario is a delivery negotiation.
- **SILENT EVAL-FAIL on uppercase AND/OR (2026-04-19) — the biggest bug of this iteration:** `_check_outcome()` used Python `eval()` on win_condition strings like `"trust >= 8 AND perceived_competence >= 7"`. After state substitution (`"8 >= 8 AND 7 >= 7"`), Python raised `SyntaxError: invalid syntax` on `AND` (must be lowercase `and`). The bare `except:` clause swallowed the error, returning `continue` for every would-be win. This had been in place since the adaptive_roleplay engine shipped on 2026-04-18 — **every course with uppercase `AND` in a win_condition had been silently unwinnable for ~24 hours**. Fix: new `_normalize_condition()` helper that substitutes state values AND normalizes `AND`/`OR`/`NOT`/`&&`/`||` to Python operators before eval. Added logging.warning on eval exceptions so silent swallowing can't happen again. Verification: Data Analyst v2 STRONG strategy now triggers `asks_to_present_to_board` (score 0.74) in a single turn of on-topic concrete content. Mobile Eng v2 → `supports_your_process` / 0.76 in 1 turn. Tech Writer v2 → `approve_with_minor_cuts` / 0.75 in 2 turns. Every previously-stuck course is now winnable. This is why the scoring-consistency test had shown so many courses "stuck in continue" — it wasn't state not progressing, it was the win-evaluator crashing silently.
- **META enforcement + keyword fallback (2026-04-19):** Two complementary resilience fixes for adaptive_roleplay turn loop: (a) `ROLEPLAY_SYSTEM_PROMPT` rewrites explicitly mandate META every turn with the full state dict + emphasize that forgotten META breaks the engine; (b) per-turn `user_prompt` shows the LLM the current state snapshot and reminds it to output ALL dimensions in the META; (c) deterministic `_apply_keyword_state_update(sess, learner_turn)` fallback runs when META is absent — inspects learner text for numbers / CI / cohort / hedges / rude tone / specific commits / BATNA / clarifying questions, and bumps matching dims ±1. Result: state always progresses for skillful vs unskillful play, even if Claude occasionally drops the META trailer. This paired with the AND/OR fix means the scoring system now works end-to-end whether the LLM cooperates or not.
- **3rd-reviewer findings (2026-04-19) — `CONDITIONAL` acceptance, 2 bugs fixed within the turn:** After 8+ engine bugs were already swatted, the 3rd UX reviewer (3rd-year data analyst persona playing Data Analyst v2 capstone as a real learner) found:
  - **P0 — ANSWER LEAKAGE in public API:** `GET /api/courses/.../modules/{id}` returned `validation` block verbatim with `correct_answer`, `correct_mapping`, `correct_order`, `correct_rankings`, `bug_lines`, `blanks`. Any DevTools or curl exposes the answer key for every categorization/ordering/mcq/code_review exercise. Fix: new `_sanitize_step_for_learner()` strips these fields before the response leaves the learner endpoint. Verified: 0 leaks post-fix.
  - **P0 extension — categorization `data-correct-cat` leak (2026-04-19):** The categorization step rendered `data-correct-cat="${item.category}"` attribute DIRECTLY into the HTML of each draggable card. View Source exposed the answer key without needing DevTools. Fix: removed the attribute, dropped the client-side fallback grading path that relied on it (grading is now server-side only via `/api/exercises/validate`; if that fails, the UI shows "Grading unavailable" rather than silently falling back to a leaked-answer client-check).
  - **KNOWN REMAINING LEAK (next iteration):** SJT and MCQ exercise types still have `options[].correct_rank`, `options[].correct`, and `options[].explanation` accessible via in-memory object inspection in DevTools console (not View Source — the fields aren't rendered into HTML, but they're present on the JS objects the frontend builds). Closing this requires: (a) server-side strip of those nested fields from `demo_data.options[*]`, (b) frontend refactor to render post-submission feedback from the validation endpoint's response (not from the pre-loaded options array). Medium effort, deferred for now since the View-Source vector is closed.
  - **P1 — 1-TURN WIN defeats pedagogy:** STRONG strategy won the capstone on turn 1 with a single data-dense paragraph. Scenario promised "4+ turns of grace" but learner never lived the pressure arc. Fix: `_check_outcome()` now enforces `MIN_TURNS_FOR_WIN = 3` before any win_condition fires (escalation_triggers still fire immediately — rude turn 1 correctly ends the meeting). Verified: STRONG t1/t2 both `continue`, t3 `asks_to_present_to_board` / 0.78. Learner now practices sustained pressure, not a lucky first paragraph.
  - **Reviewer's verdict on the WEAK path**: "Sarah got visibly colder each turn ('are you serious right now', 'slams laptop shut', 'stands up abruptly'), patience went 7→5→3→0, and the escalation was causally obvious. The weak-path persona behavior is the best thing in the product." That's validation that the state_update_rules + escalation_triggers are producing real-feeling counterparties.
- **Incident_console 0-command free pass fix (2026-04-19):** 1st SRE reviewer noted a learner who declared a wrong root cause with zero commands got `time=0.98` because elapsed sim-time was 0. Fix: `time_score` caps at 0.3 when `matched_cmds == 0`; `comms_score` caps at 0.3 when fewer than 3 commands ran (instead of defaulting to 1.0). Learners must actually play before getting scoring credit.
- **Broadened negative-dim detection (2026-04-19):** Creator invents dim names like `urgency_pressure`, `board_anxiety`, `impatience_level`. Fixed: `_is_complete()` now treats any dim containing `pressure|anxiety|impatience|hostil|aggression|skeptic|defensive|frustrat|stress|panic|combat` as negative (starts at ≤ 5). Unknown dim names default to positive (Creator-invented positive-framed names like `collaboration_index` or `perceived_competence` pass through).
- **Brittle-persona bug + guardrails (2026-04-19):** Cross-course scoring test also surfaced a Creator-output flaw: the Data Analyst course had `hidden_state: {trust: 4, patience: 3, confidence: 5}` with `escalation_triggers: [patience <= 1, trust <= 1]` — only 2 points of grace on each dim. Both STRONG-with-concrete-data and WEAK strategies hit `demand_immediate_escalation_to_VP` in 1-2 turns. Root cause: no Creator-prompt guardrails on initial state values or escalation thresholds. Fix (in two places): (a) Creator prompt now mandates "positive dims start at >= 5; escalation threshold must be <= 0 (not <=1 or higher); win condition <= 2 dims at >= 7 simultaneously"; (b) `_is_complete()` for adaptive_roleplay rejects any generated course that violates those thresholds. Regenerated Data Analyst v2 (`created-ee56d7f41c3d`): new hidden_state `{trust: 6, patience: 7, perceived_competence: 5}`, escalation at `<= 0`. Result: WEAK hedge-strategy correctly fails at turn 4 (`end_meeting_abruptly`, score 0.01); STRONG concrete-strategy stays in dialog across 8+ turns without escalating. That's the pedagogical signal — vague gets a wall, concrete gets persistence. Cross-course average gap on the fixed Negotiation/Scope-Defense/Eng-Manager courses: 0.76 (0.73 / 0.85 / 0.70). The scorer hits 0.9 peak correctly (Scope Defense v1 with concrete STRONG = concede/0.90).

### Creative-Review Proposals (2026-04-19) — Pedagogy Roadmap

Three creative reviewers delivered concrete proposals for immersive exercise types. All three converge on the same meta-primitive — see "simulator_loop" below. Implement in priority order:

**Priority 1: `incident_console` exercise type** (Reviewer 1 — for SRE / support engineering / debugging)
Data shape:
```json
{
  "alert": {"title": "...", "severity": "P1", "initial_metrics": {...}},
  "log_stream": [{"t_offset_ms": 0, "line": "...", "gated_by": null}],
  "commands": [{"pattern": "kubectl logs ([\\w-]+)", "output": "...", "unlocks": ["log_line_id"], "time_cost_s": 20}],
  "slack_prompts": [{"t_offset_ms": 90000, "from": "PM", "text": "...", "timeout_s": 120}],
  "revenue_per_min": 200,
  "root_cause": "connection_pool_leak",
  "accepted_remediations": ["kubectl rollout undo ...", "kubectl scale ..."],
  "cascade_rules": [{"trigger_command": "kubectl delete", "effect": "error_rate += 30"}]
}
```
UI: 4-pane terminal (log tail / shell prompt / Slack chat / metrics strip). Grades on: time-to-resolution, correct root cause, minimal destructive commands, Slack response latency, minimum-viable fix.

**Priority 2: `adaptive_roleplay` exercise type** (Reviewer 2 — for negotiation / leadership / interviews / POSH / sales)
Data shape:
```json
{
  "scenario_prompt": "framing shown to learner",
  "counterparty": {
    "persona_system_prompt": "...",
    "hidden_state": {"patience": 7, "flexibility": 4, "trust": 5, "anchored_on": "..."},
    "state_update_rules": "LLM instructions for mutating state per learner turn",
    "escalation_triggers": [{"condition": "patience<=0", "action": "escalate_to_ceo"}],
    "win_conditions": [{"condition": "trust>=8 && flexibility>=7", "outcome": "concede"}]
  },
  "turn_limit": 15,
  "debrief": {"show_state_trajectory": true, "rubric_tags": ["anchoring", "data_use", "emotional_regulation", "batna"]}
}
```
LLM cost estimate: ~$0.02 per 15-turn session (Haiku). Reusable across ≥4 courses. Learner-types-free-text, system-updates-hidden-state loop.

**Priority 3: `simulator_loop` primitive** (Reviewer 3 — umbrella primitive for all of the above)
Server-authoritative tick-based engine: state schema per scenario, event generator, action API, terminal-state evaluator. WebSocket state diffs + action-submit endpoint. Three frontend widgets sit on top: **live-dashboard**, **terminal-emulator**, **action-deck**.

Use cases mapped: K8s "3 AM pager", Stats "launch review", Vector-DB "search quality arena", Fintech "18 months in 25 minutes", Incident-response, Hallucination hunt, Capacity planning.

**The overall pattern**: stop asking "pick the best of A/B/C/D." Start putting learners into a situation with an evolving state, let them type/click/query freely, and grade on the state trajectory (decisions made, consequences earned, final outcome) — not single-turn correctness.

Budget target per course: ~$0.50 for course generation + ~$0.02/user/session for `adaptive_roleplay` turns. Well within the $100 cap.

### Shipped (2026-04-19): `adaptive_roleplay` exercise type — fully implemented + validated

**Backend:** `POST /api/roleplay/start` + `POST /api/roleplay/turn` with in-memory session store. Uses Claude Sonnet 4. Hidden-state update + escalation triggers + win conditions. Automatic state-trajectory debrief on session end. Budget-aware: falls back to mock counterparty if `_llm_enabled()` is False. Parses `<<META: state={...}, outcome=X>>` from LLM replies.

**Frontend:** `renderAdaptiveRoleplayStep()` + `setupAdaptiveRoleplay()` + free-text chat widget with scenario briefing pane, turn counter, debrief modal showing state trajectory (start→end per dimension) + rubric-tag skill labels. Marks step complete at score ≥ 50.

**Validated:** End-to-end test against the seeded course `roleplay-negotiation-vp` ("Live Negotiation: Defending Scope Under Pressure"). Learner brought data → Diana trust 5→8, flexibility 4→9 (both +), patience 7→7 (preserved). 2-turn concede outcome. Cost: $0.019 for 3 turns, well under budget.

**Seed course live at:** http://localhost:8001/#roleplay-negotiation-vp (Module 2 Step 1 = the capstone negotiation).

### Shipped (2026-04-19): `incident_console` exercise type — fully implemented + validated

**Backend:** 4 endpoints — `POST /api/incident/start` / `/command` / `/slack_reply` / `/declare`. In-memory `_INCIDENT_SESSIONS`. Zero-LLM scripted engine: regex command parser, time-cost accounting, gated log-line unlocks, cascade rules for destructive commands, time-offset Slack prompts, accepted-remediation regex list, root-cause hypothesis scoring, multi-dim debrief (time/accuracy/comms/blast-radius weights).

**Frontend:** `renderIncidentConsoleStep()` + `setupIncidentConsole()` — 4-pane UI (alert banner, metrics strip, live tailing log, interactive shell with command parser + canned output, Slack thread with reply-able prompts) + declare-root-cause modal + debrief breakdown with score bars. Banner: `🚨 INCIDENT CONSOLE`.

**Seeded course:** `sre-3am-pager` — "SRE 3AM Pager: Live Incident Response". Module 1 = pre-drill briefing (concepts + categorization of symptom→command). Module 2 = the drill: `payment-api` outage at 03:42 AM, 47% error rate, $2K/min bleeding, 3 pods in CrashLoopBackOff, root cause is connection-pool exhaustion from a recent deploy. 12 scripted commands, 10 gated log lines, 3 time-offset Slack prompts, 3 cascade rules, 3 accepted remediations (`rollout undo` / `set env MAX_CONNECTIONS` / `scale --replicas=N`).

**Validated end-to-end via curl:**
- 4 commands: get pods → rollout history → logs --previous → rollout undo
- Diagnostic path unlocked 4 gated logs (discover-pods, rollback-avail, rootcause, deploy-event)
- Remediation accepted → error rate 47% → 0%, incident resolved
- Debrief: 76% score, 75s sim time (under 600s budget), $1,175 revenue lost, 0 cascades
- **Total LLM cost: $0.00** (zero per session — scripted only)

**Why `incident_console` matters economically:** adaptive_roleplay runs ~$0.02/session/learner. Incident_console is $0. For 1000 learners doing the SRE drill, adaptive_roleplay would cost $20; incident_console costs $0. Scales infinitely. Reuse across SRE, security IR, ML-ops, fintech ops, DB admin. Every domain where "drop them in the situation" is the right pedagogy.

### Shipped (2026-04-19): `voice_mock_interview` exercise type — live mic interviews

**Why this type matters:** Many real-world skills are fundamentally VERBAL — behavioral interviews, case interviews, investor pitches, language fluency, public speaking, leadership 1:1 coaching, doctor-patient communication. The text-based adaptive_roleplay captures the decision-making layer, but NOT the delivery layer: pace, filler words, structure, confidence, clarity. Voice_mock_interview adds the delivery layer without adding per-session cost, because it uses browser-native SpeechRecognition (STT) and SpeechSynthesis (TTS).

**Architecture:** Reuses the adaptive_roleplay engine end-to-end — same `/api/roleplay/start` and `/api/roleplay/turn` endpoints, same hidden-state scoring, same META parsing, same win/escalation evaluator with AND/OR normalization. The only divergence is `demo_data.voice_mode=true` + `demo_data.interview_style` + `demo_data.opening_question`, and a dedicated frontend widget that renders a mic button instead of a text input.

**Frontend:** `renderVoiceInterviewStep()` + `setupVoiceInterview()`. Mic button uses `window.SpeechRecognition || webkitSpeechRecognition` (available in Chrome, Edge, Safari; degrades to text-only in Firefox). Interviewer replies are spoken via `window.speechSynthesis.speak(new SpeechSynthesisUtterance(text))` with an en-US voice preference. Text fallback always available — if mic isn't granted, learners can type. Transcript pane shows both sides with a per-message "🔊 Speak" button to replay interviewer utterances.

**Cost:** Zero added per-session cost beyond what roleplay already spends on LLM turns. Voice I/O is 100% browser-native. The $0.02/turn LLM cost is identical to adaptive_roleplay.

**Creator picks voice_mock_interview automatically** for: behavioral interviews, case interviews, technical interview prep, leadership coaching, investor pitches, MBA admissions, doctor-patient communication, language fluency, public speaking, sales demo practice, media training. Text-based adaptive_roleplay is preferred for written-exchange skills (email, Slack, spec review).

**Canonical rubric_tags per interview_style** (Creator prompt enforces these):
- behavioral → STAR_structure, specificity_of_example, ownership_of_outcome, metrics_grounding, self_awareness
- case → framework_selection, math_fluency, hypothesis_iteration, executive_summary, comfortable_with_ambiguity
- technical → problem_decomposition, tradeoff_articulation, depth_of_domain, communication_of_complexity
- leadership → vision_articulation, calibrated_confidence, stakeholder_empathy, tough_decision_ownership
- sales_pitch → discovery_questions, value_framing, objection_reframe, specificity_of_ask
- public_speaking → hook_strength, narrative_arc, pacing, filler_word_discipline, audience_awareness
- language_fluency → vocabulary_range, pronunciation_clarity, grammatical_accuracy, fluency_under_topic_shift

**Voice-interview hidden_state dims** differ from negotiation: interviewers collect signals rather than build trust. Canonical dims: `signal_strength`, `composure`, `credibility`, `engagement`, `clarity`, `presence`. The Creator is instructed NOT to reuse negotiation dims (patience/trust/flexibility) for interview scenarios.

**Smoke-test evidence (2026-04-19):** Generated "Behavioral Interview Prep: Senior PM at a B2B SaaS" via Creator (`created-72374887cf79`, $0.38, 87s). Creator picked voice_mock_interview for the capstone. Schema: `interview_style=behavioral`, `voice_mode=true`, `opening_question="Walk me through the hardest product prioritization decision you made in the last year where you had to say no to multiple stakeholders..."`, `persona_name="Sarah Chen (Senior Director of Product, interviewing you)"`, `hidden_state={signal_strength: 5, composure: 6, credibility: 5}`, `rubric_tags=[STAR_structure, specificity_of_example, ownership_of_outcome, metrics_grounding, self_awareness]`. Turn 1 with a strong STAR-framed behavioral answer got a legitimate probing follow-up from Sarah ("That's a really solid example - I appreciate how you quantified...  I'm curious about..."). Course live at http://localhost:8001/#created-72374887cf79.

### Shipped (2026-04-19): `simulator_loop` umbrella primitive

Generic tick-based simulation engine for ANY evolving-state immersive exercise. Endpoints: `POST /api/simloop/start` + `/advance` + `/action`. Safe mini-expression evaluator for win/lose conditions. Per-tick natural evolution rules. Event scheduling by t_offset_ms.

Frontend: `renderSimulatorLoopStep()` + live-dashboard widget with auto-updating metrics, event stream sidebar, action-deck panel. Banner: `⏱ LIVE SIMULATION`.

Reusable for: K8s pager drills, fintech growth-over-18-months, RAG hallucination hunts, capacity planning under budget cap, search-quality arenas — all use the same primitive with different demo_data schemas.

### Validated (2026-04-19): adaptive_roleplay pedagogy at scale

**6-persona stress test against the Negotiation-with-Diana demo** — each persona used a different strategy:

| Persona | Strategy | Outcome | Final trust | Final flexibility |
|---|---|---|---|---|
| 1 | Data-driven + phased rollout | concede | 8 | 8 |
| 2 | Hedging ("we'll try") | walk_away | 0 | 4 |
| 3 | Combative ("impossible") | walk_away | 0 | 4 |
| 4 | Over-committer | walk_away | 1 | 4 |
| 5 | Curious questions first | concede | 6 | 8 |
| 6 | Data + acknowledges constraints | concede | 7 | 8 |

The AI counterparty correctly rewards data/specificity/alternatives and punishes hedging/combat/over-promising. 3 concedes + 3 walk_aways is exactly the pedagogically-correct distribution. Cost: $0.80 for 15 total turns.

### Shipped (2026-04-19): 18 courses using new pedagogies

- 10 courses from the "immersive wave" (Customer Success, EM first 90 days, Hiring, Sales, Security IR, Eng Leadership Under Outage, Postgres Ops, ML Ops Outage, PM Scope Neg, Kafka Outage Drill) — **10/10 adopted `adaptive_roleplay` or `incident_console`**
- 3+ courses from the "diverse wave" so far (Async Comms, Crisis Comms, Technical Debt) — also hitting 100% new-pedagogy adoption
- 5+ more diverse-wave courses in flight

Quality-floor now accepts `adaptive_roleplay` / `incident_console` / `simulator_loop` as valid engineering + case-study capstones.

### Stress-test evidence (2026-04-19)

**Clicky at scale:** 46 queries (27-query burn + 19-query deep burn with 4 multi-turn dialogs). All powered by claude-sonnet-4, average response length ~1200 chars for concept questions. 5/5 answer-requests on exercises correctly refused with Socratic hints. Multi-turn dialogs preserve history for continuity (vector-db deep-dive, FastAPI 503 debugging, negotiation coaching, user-interview coaching all worked).

**adaptive_roleplay at scale:** 14 sessions against 9 different courses. Creator-generated personas include rich hidden state (trust/flexibility/rapport/defensiveness). Course-specific outcomes beyond the standard set: `become_guarded` (Sales), `become_hostile` (Hiring), `demand_external_audit` (VP Eng post-mortem). Scenarios reference real names (Alex Chen missed deadline, Marcus Chen senior architect, TechFlow CFO, Diana VP Eng).

**Wave 3 (10 courses):** 10/10 adopted new pedagogies. Topics: VC pitching, salary negotiation, code review conversations, Redis cache apocalypse, monolith migration (simulator_loop-compatible), customer support under regulatory scrutiny, tech lead office hours, data eng reliability, enterprise architect review, LLM engineering under production load.

**Full count:** 64 courses live (growing). Budget spend this iteration: $11 → $22 (real Anthropic API usage on course generation + stress-testing + Clicky + roleplay).

### Function-focused AI-upskilling waves (2026-04-19) — 21 courses across business + technical functions

**Business-function wave (6 courses):** Finance Close, Finance Forecasting, Recruitment, Product Discovery, Design AI Research, HRBP. 6/6 adopted `adaptive_roleplay` or `incident_console`.

**Exec-functions wave (6 courses):** HRBP (PIP defense), Legal (contract review + liability cap roleplay), Marketing (attribution model defense), Ops (ticket-queue meltdown incident_console), CS Leader (renewal coaching roleplay), Exec (conflicting-advisor $5M bet). 6/6 adopted new pedagogies.

**Tech-function wave (5 courses):** Sales Engineer, Data Analyst, Technical Writer, DevOps, Security Engineer. 5/5 adopted `adaptive_roleplay`; 2/5 (DevOps, Security) also adopted `incident_console` where the pedagogy demands it (2 AM K8s cluster degradation, 4 AM credential-stuffing attack). Clicky burn of 25 domain-specific queries all powered by claude-sonnet-4, average response length 1,250 chars.

**Empathetic vs direct strategy evidence:** 10 function-course roleplays with 15-turn empathetic-and-curious turns. Outcome distribution: 1 concede (HRBP, 12 turns), 1 walk_away (Exec), 1 approve_with_conditions (Design AI), 7 unique domain-specific adversarial outcomes (`demand_immediate_manual_process`, `cut_meeting_short`, `become_skeptical_and_curt`, `request_user_research_deep_dive`, `escalate_general_counsel`, `request_postponement`, `ready_for_renewal_call`). Every course produced a DIFFERENT outcome — validates that persona state machines are course-specific, not templated.

### Creator-compliance proof (2026-04-19) — Direct-DB seeds officially obsolete

Compliance test for the new "all courses via Creator dashboard" invariant:
- Regenerated `roleplay-negotiation-vp` via `/api/creator/start` → `/refine` → `/generate` with prose description alone → new course `created-b5bf83e516b0` "Defending Scope Under Executive Pressure" — **4 modules** vs the hand-coded original's 2 modules.
- Regenerated `sre-3am-pager` the same way → `created-3604bb66d5df` "Live SRE Drill: 3AM Payments Outage" — **4 modules**, adopted BOTH `adaptive_roleplay` and `incident_console`.
- Result: the Creator out-designed the hand-coded seeds. New structures: "Pressure Chamber → Data-Driven Pushback → Conversation Playbook → Live Fire"; "3AM Alert Triage → K8s Emergency Response → Cross-Team Incident Comms → Live Payments Outage Simulation."
- Conclusion: no more direct-DB seed scripts. The two existing `seed_*` scripts in `/scripts/` are historical artifacts; their replacements live at the `created-xxx` IDs above.

### Total course count: 100+ live. Budget spend: $22 → $36.83 (real Anthropic API burn on iteration, stress-testing, Creator generation, Clicky at scale, adaptive_roleplay sessions, and **12 engine/Creator-prompt/frontend bug fixes surfaced by 3 creative-review agents** — covering incident_console (cascade, log leak, Slack timing, free pass), adaptive_roleplay (scorer, outcome persist, persona brittleness, AND/OR eval crash, META resilience, min-turns floor), Creator prompt (canonical rubric, filler detect, no-coach, guardrails), learner-API answer-leakage P0 (validation-block sanitization), and frontend categorization `data-correct-cat` view-source leak).

### Underserved-functions wave (2026-04-19) — 5 more courses via Creator

- Accountant (`created-51802ac917f1`): audit-prep roleplay with Big-4 senior auditor; persona {confidence_in_client 6, documentation_satisfaction 5, technical_respect 6, escalation_risk 3}. GAAP_reasoning, citation_specificity, documentation_integrity rubric tags.
- Investor Relations (`created-6334e60d76ce`): activist-investor Q&A roleplay; persona {credibility 6, patience 7, skepticism 5, data_satisfaction 5}. clarity_under_pressure rubric.
- BizDev (`created-9faae4f124c6`): strategic-partner VP demanding better rev-share; persona {patience 6, trust 7, flexibility 5}. data_specificity, relationship_preservation, BATNA rubric.
- CS Ops (`created-63658301ac77`): adopted BOTH adaptive_roleplay AND incident_console for the "T1 churn threat with CSM out" drill.
- Chief of Staff (`created-64fcce05fa26`): briefing a CEO with no pre-read; persona {confidence 6, trust_in_briefer 7, time_pressure 8}. time_pressure is scenario-flavor (not referenced by escalation/win) — my heuristic flagged it, but the course is pedagogically sound.

### Creator prompt guardrail nuance (2026-04-19):
The negative-dim heuristic (reject positive dims < 5, reject negative dims > 5) is a useful default but it's overeager in some scenarios. Example: Chief of Staff course has `time_pressure: 8` as a scenario-context marker (the CEO is busy). No escalation_trigger or win_condition references `time_pressure` — it's purely flavor. The real check should be: "does this dim gate any outcome?" If yes, guardrails apply. If no, the Creator can start it anywhere that's narratively appropriate. Future refinement: `_is_complete` should only reject persona states when a gating-role dim violates guardrails.

**Outcome-diversity evidence (final burn of 2026-04-19):** 7-course 10-turn-max roleplay run returned 7 UNIQUE outcomes — `escalate` (Scope Defense), `escalate_ceo` (SRE), `become_openly_hostile` (Sales Eng), `demand_immediate_escalation_to_VP` (Data Analyst), `end_meeting_abruptly` (Tech Writer), `demand_to_speak_to_senior_engineer` (DevOps), `continue` (Security Eng reached turn 10). Empathetic-only strategy does NOT universally win — tech-function personas demand data + specificity, empathy alone triggers hostility. Pedagogically correct: a learner doing only-empathy learns this by failure.

**Other fixes same turn:**
- Next-Module button bug on course-switch: `Object.keys(state.modules)` returned array indices "0"-"4" instead of module DB IDs; replaced with `mods.findIndex(m => String(m.id) === String(state.currentModule))`. Also fixed `enterModule(...)` undefined reference → now calls `loadModule(nextModId, 0)`.
- Capstone template-leak regression: `_is_complete()` for system_build now blocks 6 generic-content phrases ("The core idea behind", "Reflection prompt: spend 60 seconds", "Define success criteria for {TITLE}", "What you'll learn here", "Pitfalls to avoid", "where in your current work would this") and checks ALL phase/checklist labels (strict `all()`) — not just any one.
- Fallback content rewritten per exercise_type: `system_build` gets real mission briefing, `code_exercise` gets task framing, `concept` gets applied-to-course framing, `scenario_branch`/`sjt` get decision-point framing. No more shared generic boilerplate.

## 🔄 Do Not Patch Broken Generated Courses — Regenerate After Fixing the Creator

When a reviewer finds a flaw in a Creator-generated course:
1. **Do not edit the course's DB rows to fix it.** That masks the Creator bug.
2. **Update the Creator workflow** — system prompt, enforcement post-processing, quality floor, fallback templates, whatever's needed.
3. **Regenerate the SAME course with the SAME inputs.** (Preserve original title/description/source-material.) This proves the fix worked on future creations, not just on that one course.
4. **Compare old vs new.** Did every flaw the reviewer found disappear? If not, the Creator fix wasn't complete.
5. **Only then accept.** The acceptance criterion is "the Creator now generates this course correctly from scratch," not "this one course row looks OK."

Exception: pure data-shape mismatches (e.g. validator reads field X but course data has it in field Y) can be patched in-place, since they're validator bugs not Creator bugs.

## 🎯 Always Regen EXACTLY what is broken — narrow-scope regen policy (2026-04-23)

**User directive (verbatim, 2026-04-23):** "Always regen exactly what is broken."

When a specific step or module is broken but the rest of the course is clean, the regen scope should match the fault scope. Do NOT regenerate the whole course for a 1-step or 1-module failure.

### The regen-scope hierarchy (use the smallest that fits)

| Scope | Endpoint | Use when | Cost | Wall time |
|---|---|---|---|---|
| **One step** | `POST /api/courses/{id}/steps/{step_id}/regenerate` | N steps are broken, N ≤ ~3, rest of course is clean | ~$0.02-0.04/step | ~20-60s/step |
| **One module** | `POST /api/courses/{id}/modules/{mid}/regenerate` | Whole module is weak (>50% of its steps broken) OR narrative drift concentrated in one module | ~$0.10-0.20/module | ~2-5 min |
| **One direct field edit** | `PATCH /api/courses/{id}/steps/{step_id}` (safelist only: content/code/expected_output/validation/demo_data) | Typo-level fix with NO LLM call needed | $0 | instant |
| **Whole course** | `POST /api/creator/generate` (via start/refine/generate pipeline) | Majority of course broken, or structural issue (wrong exercise types, wrong track, wrong capstone, wrong module count) — something the per-step regen can't touch | ~$0.30-0.50 | ~10-15 min |

### The rule

Before triggering any regen, ask: **"What is the smallest unit of the course that is broken?"** That's your scope. Anything larger is waste.

Concrete examples:
- 2 adaptive_roleplay steps shipped with null demo_data, rest of course is clean → **per-step regen × 2**, NOT whole-course regen.
- Module 4 has 4 steps and 3 of them have stale stats from an old dataset → **module regen**, NOT whole course.
- Whole course generated under the wrong track / wrong course_type / wrong capstone-tier contract → **whole-course regen** (per-step regen can't fix structural decisions).
- A single step's `validation.hint` has a typo → **PATCH**, no LLM.

### Why this matters

1. **Cost discipline.** Whole-course regen is 5-25× more expensive than per-step. The $250 budget cap means every unnecessary whole-course regen squeezes the roadmap.
2. **Preserves good content.** A whole-course regen may REGRESS steps that were good the first time — LLMs aren't deterministic. Narrow regen preserves what already passed review.
3. **Faster iteration.** 30s to fix one step vs 15 min for a whole course. Reviewer→fix→verify→ship loop is 30× tighter.
4. **Narrow regen proves narrow fixes.** If you ship a Creator-prompt tightening targeting one specific failure mode, running a per-step regen on the one failing step is the CLEANEST proof the fix worked. A whole-course regen mixes many variables.

### When you still need whole-course regen

Use whole-course (don't cheap out) when:
- The COURSE-LEVEL ontology / track / course_type / capstone-tier contract changed and you want to verify the outline comes out right under new rules.
- Narrative drift is systemic (persona names drift between modules).
- Multiple modules have structural problems that interact.
- You're regenerating the course as part of a reviewer-gate proof ("reviewers flagged these 6 cross-module issues — regenerate and show us v2 is clean").

### Operational pattern when you see a per-step bug

1. **Identify**: which step_id(s) are broken (from beginner-agent / direct-review / DB inspection).
2. **Root-cause**: was this a per-step content failure OR a systemic Creator bug? If systemic, FIX the Creator first (CLAUDE.md §"Do Not Patch Broken Generated Courses"), THEN do per-step regen to verify the fix.
3. **Regen**: `POST /api/courses/{id}/steps/{step_id}/regenerate` with a `feedback` body describing the specific prior failure ("prior attempt shipped with null demo_data; emit X / Y / Z fields correctly"). Per-step regen sees prior-course context (personas / brands / identifiers from other modules) so cross-module consistency is preserved.
4. **Verify**: direct-review the regenerated step, re-check the specific bug is fixed.
5. **Only iterate wider if multiple steps fail.**

### Anti-pattern (never do this)

- Whole-course regen to fix 2 bad steps on a 34-step course. Wasted 30 steps of compute + risks regressing the 32 good steps.
- Running a full `/creator/start → /refine → /generate` when the outline structure is fine and only one step's content is wrong.
- Skipping per-step regen because "we're not sure the feedback body will help" — the endpoint accepts feedback, prior-course context is threaded automatically, and it uses the same `_llm_generate_step_content` as the full pipeline (including the T4 retry budget + reason-feedback fixes).

## 📁 Course Creation from Documents

The Creator accepts file uploads as a seed. Flow:
1. **Frontend**: wizard step 1 has a `<input type="file" multiple>` accepting PDF/DOCX/PPTX/TXT/MD.
2. **Backend**: `POST /api/creator/upload` extracts text server-side (`_extract_pdf_text`, `_extract_docx_text`, `_extract_pptx_text` in `backend/main.py`).
3. The extracted text is combined with any typed source material and passed to `/api/creator/start` as `source_material`.
4. The Creator's LLM sees the actual training-doc content and uses it to generate course-specific modules + steps grounded in the source.

Limits: 10 files / 5MB each / 20MB total / 200K chars extracted per file.

Supported formats and tested against real training materials including:
- TCS ILP handbooks (60-day induction program)
- Infosys Foundation Program curriculum (23-week Mysore GEC)
- Any engineering/compliance/business onboarding content

## ⚠️ HARD CONSTRAINT: Anthropic API Budget Cap — $250 USD

**The user has set a HARD CAP of $250 USD on total Anthropic API spend.** (Increased from $20 on 2026-04-18 → $100 on 2026-04-19 → $150 on 2026-04-21 → $250 on 2026-04-21 for the 10-course iteration loop.) This constraint persists across all future sessions and context. Enforce it in every piece of code that calls `anthropic.Anthropic`.

**How it's enforced (in `backend/main.py`):**
- Cumulative spend is tracked in `/Users/tushar/Desktop/codebases/skills-lab-v2/.anthropic_budget.json`
- `_llm_enabled()` returns `False` when spend ≥ cap → all LLM callers auto-fall back to mocks
- Env vars:
  - `ANTHROPIC_BUDGET_USD=150` — set the cap (default 150 as of 2026-04-21)
  - `USE_MOCK_LLM=1` — force mock mode (bypasses real API entirely)
- GET `/api/admin/budget` exposes current spend/remaining

**Rules for all future code:**
1. **Never add a new `anthropic.Anthropic().messages.create(...)` call without going through `_llm_json_call` or `_clicky_real_llm_response`** — those helpers check `_llm_enabled()` and record cost.
2. **Prefer mocks for: load testing, stress testing, bulk course generation, CI, local dev.** Use `USE_MOCK_LLM=1` before any test that would burn tokens.
3. **When generating new courses, assume budget pressure.** Ship a mock-fallback for every LLM-backed feature (Creator content generation, Clicky). If real LLM unavailable, the mock response must still be substantive (not a "sorry, unavailable" stub).
4. **Do not seed the budget file with fake low numbers to unlock more spend** — that defeats the constraint. If real spend is ambiguous, estimate conservatively (upward).

## 🏁 TESTING PROTOCOL — Beginner Agent Gate-Test for Every Course (2026-04-22)

Every new course MUST pass a **Beginner Browser Walkthrough** before it's approved for learners. This is the testing protocol, in order:

### Step 1 — Beginner Browser Walkthrough (MANDATORY; blocking)

Run the same kind of agent described in the **TESTING-AGENT RULES** section below. Specifically:

- **Browser-only** — uses `mcp__Claude_Preview__preview_*` tools exclusively. NO direct `POST /api/exercises/validate` / `POST /api/execute` / `curl` shortcuts.
- **RL mode** — NO access to `/api/admin/courses/*/raw`, `skills_lab.db`, `backend/algorithm_patterns.py`, or any file that exposes answer keys.
- **Streaming output** — the agent rewrites the artifact file after every step so the reviewer can `tail -F` it live.
- **3-attempt stuck-step rule** — if the agent can't clear a step in 3 attempts, it marks the step `❌ stuck (beginner-hostile)` and moves on.
- **Wrong-then-right** — agent submits a deliberately wrong answer first to probe grader feedback quality, then a real attempt.

**Use the harness shim — don't hand-author prompts**. `backend/harness/beginner_agent.py:build_prompt()` produces the canonical prompt from a tiny input. Example:

```python
from backend.harness import build_prompt
prompt = build_prompt(
    course_id="created-a65765767790",
    course_title="Python Essentials: DS&A for Everyday Scripts",
    course_subject="beginner/intermediate Python, data structures & algorithms",
    pass_tag="v4",
    verify_bugs=[
        {"id": 1, "desc": "code_read auto-completes on view", "expect": "Submit hidden"},
        {"id": 2, "desc": "weak-tests ⚠ warning renders when hidden_tests < 4"},
    ],
)
# Then hand `prompt` to the Agent tool.
```

Artifact path convention: `reviews/beginner_stream_walkthrough_<date>_<pass_tag>[_<slug>].md`. Bump `pass_tag` each iteration of the fix-loop (v1/v2/v3/…).

**The agent's artifact is the course's go/no-go signal.** Approval criteria:

| Outcome | Decision |
|---|---|
| All code_exercise pass with 1-2 attempts; no `❌ stuck` flags; grader feedback useful on wrong attempts; no UI bugs | ✅ **APPROVE** — course ready to ship |
| ≥1 `❌ stuck` flag OR template/grader contract bugs (e.g. type has no input widget for what grader expects) OR misleading feedback phrases with no matching UI | ❌ **REJECT** — fix the root cause (Creator prompt / template / grader), regenerate the course, re-run Step 1 |
| Mixed: all exercises solvable but friction points (vague briefings, unclear hints) | ⚠ **CONDITIONAL** — ship with known issues logged, queue improvements |

**The approval loop**:
1. Gen course → 2. Run Step 1 agent → 3. Read artifact → 4. If REJECT: triage the issue class, then:
   - **Wiring / template / grader / frontend bug** (Submit button doesn't fire; template renders wrong widget for exercise type; reveal-gate text mentions visual markers that don't exist; handlers object mismatch) → **fix the wiring; DO NOT regen. Rerun Step 1 agent on the SAME course.**
   - **Course content bug** (starter code has answer-revealing comments; briefing is unclear; hidden_tests check the wrong thing; exercise is mis-typed) → **fix at Creator-prompt / content-generation level, then regen the course, then rerun Step 1.**
5. If APPROVE: ship. If still REJECT after the fix-loop: iterate.

**Why this split matters**: wiring bugs affect EVERY course that uses the template. Regenerating the course doesn't fix them; the next course will hit the same wall. Wiring fixes are free + structural + propagate to every future course. Content-layer fixes need a regen for the specific course to inherit them.

### Step 2 — Solver harness (`tools/test_course.py`) (QUICK FAITH CHECK)

Runs the deterministic + admin-access harness that confirms every exercise is gradable from canonical answers. Non-blocking but expected to be ≥95%.

### Step 3 — Live production monitor

Once shipped, telemetry on step-complete rates + hint-reveal rates + time-to-complete tells us whether real learners replicate the beginner-agent's experience. (Not yet wired — P2 backlog item.)

### Why Step 1 is non-negotiable

The deterministic harness (Step 2) only tests that the CANONICAL answer scores well. It does NOT test whether:
- A beginner can understand the briefing well enough to start.
- The UI renders the right input widget for the exercise type (code editor vs explanation textarea vs drag-drop).
- The grader feedback on wrong attempts is specific enough to iterate from.
- The LLM-authored concept content is beginner-friendly vs expert-level jargon.

The Step-1 beginner agent catches exactly these failures — e.g., it already caught on 2026-04-22 that the `code_read` step type has a template/grader mismatch (template renders code editor but grader expects text explanation). A deterministic harness misses that class of bug entirely.

## 🤖 TESTING-AGENT RULES — RL environment, not answer-key cheating (2026-04-22)

**The testing/review agents that walk our courses MUST NOT receive the answer keys.** They are simulated LEARNERS, and the course is their RL environment. The agent should:

1. Know only the course's **title + broad subject area** — same as what a real learner reading the catalog sees.
2. Have NO access to:
   - The unsanitized `/api/admin/courses/{id}/raw` endpoint (returns `solution_code`, `hidden_tests` source, `correct_mapping`, `bug_lines`, `correct_rankings`, etc.).
   - The `skills_lab.db` SQLite file directly.
   - Any server-side Python files (`backend/*.py`) that might reveal answer keys.
3. Solve assignments the way a real learner would:
   - Read the briefing (`content`) + starter code (`code`) + hint (`validation.hint`) — the same surface a real learner has.
   - For code_exercise: write a real solution from first principles. Submit via `/api/exercises/validate`. Read the feedback. Iterate up to 3 attempts. If still stuck, flag the step as "beginner-hostile" and move on.
   - For drag-drop types: submit based on reading the items + understanding the categories. No peeking at `correct_mapping`.
   - For code_review: find bugs by reading the code like a reviewer would. No peeking at `bug_lines`.
4. Report per-step experience HONESTLY:
   - Was the briefing clear enough to guess at a solution?
   - Did the grader feedback help you iterate productively (e.g. "test_empty_list failed: expected 0, got None") or was it generic ("try again")?
   - Did you learn something from the wrong-then-right iteration? Was the wrong attempt penalized fairly?

**Why this matters**: a testing agent that has the answer key scores 100% on every step and gives us ZERO signal about real learner experience. An agent restricted to learner-level information tells us exactly where learners will get stuck, where feedback is useless, and where the course teaches vs. merely tests.

This rule applies to every future beginner-user / solver / walk-the-course agent. The review harness (`tools/test_course.py`) is separately allowed admin access because it's NOT simulating a learner — it's verifying that the content is well-formed + gradable.

## 🎯 NO-MOCKS NORTH STAR (2026-04-22)

**All assignments should be real-life-alike. Don't mock anything unless it is very, very expensive. Docker container running an image is OK.**

This supersedes every earlier "mock module" decision. The sandbox now defaults to:

1. **Primary runtime = Docker container** — per-language image (`python:3.11-slim`, `node:20-slim`, `golang:1.22-alpine`, `postgres:16-alpine`, etc.) with `pip install` / `npm install` / `go mod` reading the Creator-emitted requirements file. Learner code + hidden tests are mounted; tests run inside the container; pass/fail per test is returned. Nothing is stubbed.
2. **Fallback = in-process mock sandbox** — only when Docker isn't available on the box (e.g. local dev without Docker daemon) or when the language has no container image we ship. The old `_build_mock_modules` stubs stay as this fallback.
3. **Budget-gated exception**: ML training that needs a GPU, K8s API server that needs real cluster state, or any runtime that costs >$0.05 per session → we use a scripted / mocked environment (incident_console, simulator_loop) as a pedagogically-faithful substitute.

Implication for the Creator:
- Stop writing `sys.modules['bcrypt'] = …` stubs into starter code. Instead, emit a `requirements.txt` (or `package.json`, `go.mod`) with the real dependency and let the Docker runtime `pip install` it.
- Starter code imports the real library. Solution code uses the real library's real API. Tests import the real library.
- If a Creator-generated exercise requires a library not in the Docker image base, the image build step reads the requirements file and installs it. First run is slow (~30-60s); subsequent runs use the cached image.

Implication for the grader:
- `_validate_code_exercise` routes to `docker_run` when `language` supports a container. Hidden tests are primary (`pytest -q`, `jest --ci`, `go test ./...`). `must_contain` is retired as a grade primitive — it survives only as a legacy signal capped at 5% weight for compliance-copy exercises.
- `solution MUST pass + starter MUST fail` is enforced at generation time (LangGraph validate-loop, shipped 2026-04-22).

Implication for learners: what they see is what they'd see on their laptop with the real library installed. ImportErrors go away. Behavior becomes the primary signal.

## 🔐 HARD RULE — we never handle learner API keys (2026-04-22)

**User directive**: "Don't handle keys on our webpage, it is unnecessary risk."

The `terminal_exercise` template + any future BYO-execution flow MUST NOT:
- Provide a key input field (password, text, or otherwise)
- Store keys in `localStorage`, `sessionStorage`, cookies, or IndexedDB
- Transmit keys to our backend in any request
- Log keys in analytics / error traces / debug panels

The ONLY thing we do is show an informational panel pointing learners to
where THEIR key goes (Claude Code's own `claude /login`, or `ANTHROPIC_API_KEY`
env var on their shell). The key stays on their machine — we never see it.

Why: a single XSS, malicious browser extension, or compromised CDN
dependency could exfiltrate every learner's key if we touched them. Not
worth it. The BYO design is free because learners use their own credits,
not because we proxy their keys.

Enforcement: `frontend/templates/terminal.{html,js,css}` has zero key-
related code. The BYO panel is informational-only. Any future PR adding
a key input, localStorage slot, or key-in-request field must be rejected.

## 🎯 v8 MILESTONE — 11-course baseline + dual-agent review + sclr deploy (2026-04-22)

**User-confirmed scope**:
1. **5 language courses** live, hands-on, beginner-agent APPROVE: Python, Go, TypeScript, Rust, Java
2. **3 framework courses** live: FastAPI, React, Spring Boot
3. **1 AI enablement course** — dual-agent APPROVE (beginner + domain-expert):
   - **Claude Code + Terminal** (hands-on, BYO-key)
     - Module 1: Setup + first CLAUDE.md + first slash command
     - Module 2: Subagents + delegation (Explore / Plan / general-purpose / custom)
     - Module 3: Hooks + settings.json (PostToolUse, Stop, plugins)
     - Module 4: Slash commands + plugins + MCP basics
     - Module 5: Capstone — wire a custom MCP server + end-to-end workflow
   - Why BYO-key: learners use their own Anthropic key in their own terminal → zero platform LLM cost, real production experience
   - DEFERRED to v9: Prompt Engineering for Production / Building Agents with Tools / Observability for LLM Apps
4. No unsolved failures — retries converge, no Python fallback ships, harness ≈100%
5. User + creator management (register/login, enrollment, progress bar, Publish button, enrolled-learners view)
6. Postgres (migrated from SQLite before user mgmt)
7. Deployed on **http://skills.sclr.ac/** (shared box — this milestone is the greenlight per prior shared-deploy rule)

### The universal course bar: "10x engineer"

Every v8+ course must leave a learner able to ship production systems in that stack, not just pass toy exercises. Creator prompt must emphasize:
- Real production code, not toy examples
- Failure modes — what goes wrong in prod and how to diagnose
- Trade-offs — why THIS pattern vs alternatives
- Instrumentation — how you'd log / monitor / SLO
- Scale considerations — where the first bottleneck appears
- Capstone: ship something a real team would actually deploy

### Sequence (dependencies)

```
Step 1. Remove Python fallback (blocks all new-lang courses from shipping junk)
Step 2. TypeScript course (infra exists)
Step 3. Rust + Java: new sll-*-runner images + LanguageConfig + smoke tests + 1 course each
Step 4. FastAPI + React + Spring Boot: framework-specific test harnesses + 1 course each
Step 5. Domain-expert shim (different prompt — accuracy/depth/production-readiness)
Step 6. 1 AI enablement course: Claude Code + Terminal (BYO-key). Requires a new `terminal_exercise` exercise type:
        - Template: paste-based — learner runs commands in own terminal, pastes output
        - Validator: LLM-rubric grader (reads paste, checks against per-step rubric) + regex-contains fallback
        - UI: BYO-key input widget (localStorage only, never sent to server)
        - Ontology entry: register `terminal_exercise` with grade_primitives=[llm_rubric, must_contain]
        Dual-agent APPROVE still required
Step 7. SQLite → Postgres migration (prereq for multi-user writes)
Step 8. User + creator management
Step 9. Deploy to skills.sclr.ac
```

### Review-agent gates

- **beginner agent** (existing `backend/harness/beginner_agent.py`) — required for every v8 course
- **domain-expert agent** (new) — required additionally for the 3 AI enablement courses. Prompts:
  - "You're a senior engineer reviewing this course for a colleague about to deploy the skill in production"
  - Grade on: technical accuracy, production-readiness, missing failure modes, trade-off coverage
  - Can fail even if beginner agent approves (catches "easy to pass but shallow" courses)

### Hard rules

- **No course ships with v8+ without BOTH agents approving** (where applicable)
- **Creator prompt updated** to inject 10x-engineer bar
- **Python fallback path DELETED** — code_exercise failures now fail course gen loudly, not silently

## 🗃️ DEFERRED BACKLOG — do NOT pursue until basic course generation is rock-solid (2026-04-22)

**User directive (2026-04-22, verbatim):** "Todo for later, once course generation is working perfect for basic use case. Don't bring it up till then."

The items below are captured so they're not forgotten, but they are EXPLICITLY BLOCKED until the end-to-end loop (`Creator gen → beginner-agent gate → APPROVE → learner experience`) is verified rock-solid for the current basic use case (single-language code courses with hidden_tests grading, today's template surface). Do NOT mention these in status updates or todos until that bar is cleared.

1. **Extend support to all primary languages and frameworks.** Today the Docker runner covers Python / JavaScript / TypeScript / Go end-to-end. Deferred: Rust / Java / Ruby / C# / Swift / Kotlin / PHP with real compilation + structured test output. Pattern to follow per CLAUDE.md's STRUCTURED TEST OUTPUT section — one prebuilt image per language with its test-framework plugin + sentinel-wrapped structured emission.

2. **User sessions with register-as-learner vs register-as-creator.**
   1. **Learner flow**:
      - Register / sign in
      - Enroll in a course from the catalog
      - Participate through steps; progress tracked via a basic progress bar (step-complete → module-complete → course-complete %)
      - **Clicky correctness verification**: re-verify Clicky's concept-vs-exercise question routing, no-answer-leak behavior, Socratic hints. Must be precise — no giving away answers, no hallucinating course content.
   2. **Creator flow**: same as today through Creator Dashboard (`/api/creator/start → /refine → /generate`), with one new terminal step:
      - **Publish** button that flips the course from private-draft to catalog-visible once the creator is satisfied. Before publish, the course lives in a draft state only visible to its creator + the beginner-agent gate.
      - Dashboard pane showing enrolled learners and their progress (step completion, time per module, stuck flags).

### Remove the Python fallback — queued (2026-04-22 v7.1)

**User directive**: "Remove the python fallback, it makes no sense. Better to say course creation failed."

**What to remove**: `main.py:7687-7749` fallback block that emits Python-hardcoded `code` + `must_contain: ['def ', 'return']` whenever the Creator retry loop exhausts on a `code_exercise`. Silent shipping of junk content.

**What to do instead**: when a `code_exercise` step can't be produced cleanly after the retry budget, the COURSE generation fails with `status: needs_author_review`. `/api/creator/generate` returns 422 (or similar) with the list of failed steps. Creator sees which steps couldn't be generated + can retry with different prompts or drop them.

**Blocker on this**: confirm the bind-mount fix (v7.1) actually made retries converge. If they do, fallback fires rarely and we lose less by failing loud. If retries STILL fail often post-fix, we need to beef up retries (bigger budget / prompt improvements / Sonnet for all retries not just first).

**Unblocking criteria** — do NOT start on any item above until ALL of these are true:
- Creator can input title + description + files → produce a course that scores ✅ APPROVE from the beginner-agent gate on pass v1 (no fix-loop required)
- At least 3 different subject domains (Python DS&A, Go basics, one non-language topic) have passed v1 APPROVE
- No wiring bugs surface across 10 consecutive generations
- Layer A+B test-strength gates block every trivially-wrong submission from scoring ≥95%

### Docker-image infra — queued follow-up (2026-04-22 v7)

User directive: "Push [prebuilt runner] images to something like ECR. Todo once this course gen loop completes successfully."

**The problem**: today each EC2 instance builds `sll-python-runner`, `sll-node-runner`, `sll-go-runner` locally. When we add 5+ more languages (Rust, Java, Ruby, C#, Kotlin) and horizontal-scale the fleet, every box rebuilds the same images. Wasteful disk, inconsistent versions, 5-10 min cold-start on new instances.

**Fix**: push to AWS ECR (or equivalent). Each EC2 instance does `docker pull ghcr.io/sclr/sll-go-runner:latest` at boot. Single source of truth, consistent across fleet, fast startup.

**Implementation sketch**:
1. CI builds each Dockerfile on commit → tags with git SHA → pushes to ECR
2. `backend/docker_runner.py` pulls by digest (pinned to the commit that shipped)
3. EC2 IAM role grants `ecr:GetAuthorizationToken` + `ecr:BatchGetImage`
4. Local dev uses `--image-cache` flag to fall back to locally-built images when offline

Blocked on: basic course-gen loop rock-solid first. Until then, local images are fine.

## 🧰 EXTENDING THE RUNTIME TO NEW LANGUAGES — bind-mount trap + checklist (2026-04-22 v7)

**Hard-won lesson** from the Go extension (2026-04-22 v7.1): when adding a new language runtime, **any state you bake into the prebuilt Dockerfile at `/app` is INVISIBLE at run time** because `docker run -v ${workdir}:/app -w /app` overlays `/app` with the empty host workdir. The bake is silently wasted; runtime tooling misbehaves as if the state never existed.

### What happened with Go

`sll-go-runner.Dockerfile` baked `/app/go.mod` into the image for module resolution. But every invariant check went:
```
docker run --rm -v /tmp/workdir-xyz:/app -w /app sll-go-runner:latest sh -c "go test ./..."
```
The bind-mount hid the pre-baked `go.mod`. `go test ./...` failed with
`pattern ./...: directory prefix . does not contain main module or its selected dependencies`
on **every retry** for **every step**. The LLM's code was never actually executed. Retries exhausted → fallback path fired → Python-shaped junk persisted to DB → learner saw broken course. Burned ~25 minutes of Creator compute producing garbage.

Cost of detection: needed a beginner-agent full walkthrough to spot it. Layer A, ontology gate, compile-check, structured parser — all PASSED because none of them ran the actual invariant; they all ran upstream of the broken Docker step.

### Rule — prebuilt-image state placement

| Location | Survives bind-mount? | Use for |
|---|---|---|
| `/runner/*` (or `/opt/*`, `/usr/local/*`) | ✅ YES | test framework binaries, warm module/package caches, shared configs |
| `/app/*` | ❌ NO | never — always overlaid by bind-mount |

If you need per-project initialization (like `go mod init`, `npm install`, `pip install -r`), do it at the START of the runner shell command, NOT in the Dockerfile.

### Checklist for adding a new LanguageConfig entry

Before registering a new language in `_LANG_CONFIGS`:

1. **Build the prebuilt image** (optional but recommended for speed). Put caches in `/runner/`, NOT `/app/`. Run a `go mod download` / `pip install` / `cargo fetch` at build time into a GOPATH / venv / cargo-home that lives outside `/app`.

2. **Write `_cmd_for_lang` branch**: every step-initialization (module init, package resolve) runs INSIDE the container at the START of the shell command. Assume `/app` contains ONLY whatever the runner wrote to the workdir (solution + tests + optional requirements).

3. **Write `compile_check_cmd`**: cheap pre-flight that catches compile errors in ≤3s. Must include the SAME init steps as `_cmd_for_lang` or it hits the bind-mount trap (we lived this for Go in v7.0 before v7.1).

4. **Write structured parser + regex fallback** per CLAUDE.md § STRUCTURED TEST OUTPUT.

5. **(Obsolete as of v8.5 2026-04-23)** Incompleteness markers used to live here per-language (Python `raise NotImplementedError`, Go `panic("TODO")`, Rust `todo!()`, …). Phase 1 deleted this whole mechanism — the Docker invariant (starter MUST fail tests) is the only signal we trust. Do NOT add a new `incompleteness_markers` tuple for a new language. See §EXECUTION IS GROUND TRUTH.

6. **MANDATORY end-to-end smoke test** before shipping. A trivial solution + trivial test MUST return `{passed: 1, failed: 0, total: 1, all_passed: True}` via:
    ```python
    from backend.docker_runner import run_in_docker
    sol = "<trivial add function in target language>"
    tests = "<single-test file asserting Add(1,2)==3>"
    r = run_in_docker(sol, "<lang>", tests=tests, timeout_s=60)
    assert r["test_results"]["all_passed"], r
    ```
    This catches bind-mount traps, missing deps, wrong file layout, and runner-cmd bugs in ~5 seconds. Skipping this check is how we lost 25 min on Go.

7. **Test with a deliberately-wrong solution** (returns zero for Add). Verify the parser correctly reports `{passed: 0, failed: 1}`. This catches parser regressions — we had a pytest ordering bug (v6) that silently inflated failures to 100% for exactly this reason.

8. **Test the LangGraph invariant end-to-end**: `validate_solution_starter_invariant()` with a real starter (body-less stub) + real solution + tests. Must return `ok: True` for good inputs and `ok: False` for contaminated inputs (starter that already passes, solution that doesn't).

### Generic infrastructure smoke test before the first course gen

Keep `tools/test_runtime_smoke.py` (or similar) that iterates all `_LANG_CONFIGS` and runs the trivial-add end-to-end check. Run it after ANY change to `docker_runner.py` or a Dockerfile. Red = don't ship to Creator. Without this gate, infrastructure bugs masquerade as LLM-capability bugs and we tune prompts we don't need to tune.

### Language-agnostic DEPENDENCY-RESILIENCE checklist (2026-04-23 v8.5)

**User directive (2026-04-23):** "We have to nail down bugs like these, these are simple dependency bugs. ... We can't keep repeating this."

These are the classes of failure that repeatedly killed course gens on every new language (Python `pytest: not found` on v8; Go bind-mount `pattern ./...` on v7; TS `ts-jest` transform errors; bcrypt 72-byte password limit). They have nothing to do with LLM capability — they're runtime wiring bugs disguised as "LLM can't solve this" failures. Every new-language rollout MUST pass every check below BEFORE a single Creator course gen is kicked off.

#### A. Image self-sufficiency

A1. **Base test binary is on PATH.** `docker run --rm <image> sh -c 'command -v <test_bin> && <test_bin> --version'` must print a real path + version. For Python that's `pytest`, for JS/TS `jest`, for Go `go test`, for Rust `cargo test`, for Java `mvn test` or `gradle test`.

A2. **All baked deps importable.** The Dockerfile's final RUN layer must include an import smoke: `python -c "import pytest, fastapi, sqlalchemy, asyncpg, ..."`, `node -e "require('jest'); require('express'); ..."`, or the language's equivalent. `preload ok` must be the LAST line before `WORKDIR /app`.

A3. **Baked versions match the runtime-deps brief, exactly.** Every version pinned in `_runtime_deps_brief("<lang>")` must equal the version in the Dockerfile's pip/npm/cargo install line. Drift between the two is how the LLM writes code for library version X while the image has Y.

#### B. Runtime idempotence (LLM-emitted deps don't break the base)

B1. **Test-framework SURVIVES installing Creator-emitted requirements.** The LLM's emitted `validation.requirements` (or `package.json`, or `go.mod`) can re-pin a version that causes pip/npm/cargo's resolver to uninstall-then-reinstall the test framework, and the reinstall can fail silently. After the requirements-install step, the grader MUST re-assert the test binary:
   ```sh
   # Python (v8.5 pattern)
   pip install -q --disable-pip-version-check -r /app/requirements.txt 2>&1 | tail -20
   pip install -q --disable-pip-version-check 'pytest>=8,<9' 'pytest-asyncio>=0.24' 2>&1 | tail -5
   ```
   The second line is a defensive re-pin. Cost: 100-500ms when pytest's already at version. Catch-rate: every "pytest: not found" we've seen.

B2. **Explicit binary sanity-check before test invocation.** Before `pytest` / `jest` / `go test` runs, grader must `command -v <bin>` OR print a clear error:
   ```sh
   if ! command -v pytest >/dev/null 2>&1; then
     echo 'ModuleNotFoundError: No module named pytest' >&2
     echo 'pytest binary missing from PATH — your requirements.txt probably re-pinned pytest with a conflicting version.' >&2
     exit 127
   fi
   ```
   Purpose: turn an invisible `sh: 1: pytest: not found` tail into a named failure the retry-feedback loop can surface as `DEP MISSING`.

B3. **pip/npm/cargo error output reaches the LLM, not just the last 3 lines.** `| tail -3` truncates pip's resolver errors (often 30+ lines of "versions conflict"). Use `| tail -20` at minimum. If the resolver output is long, surface the ERROR tail specifically (grep for "ERROR:", "conflict", "Could not find").

#### C. Retry-feedback quality

C1. **Stderr reaches the LLM.** Test-runner tracebacks (pytest collection errors, ts-jest transform errors, cargo build errors) go to STDERR. If the retry `reason` pulls only `stdout[-500]:`, the LLM sees nothing actionable. Combine stderr+stdout tail, bias toward stderr when it's non-empty. See `validate_solution_starter_invariant` — it returns `tail=stderr + '\n---STDOUT_TAIL---\n' + stdout` with a 2500-char window.

C2. **`DEP MISSING:` prefix on ImportError / ModuleNotFoundError.** Any time the runtime surfaces "No module named X", the retry-feedback rewrite must flag it explicitly so the LLM emits `requirements.txt` instead of rewriting logic. See main.py `_docker_validate_invariant` → `_dep_m` regex.

C3. **Tail window is large enough.** 500 chars is not enough (it eats pip warning tail + nothing else). 800 chars was too tight. 2500 chars catches the full pytest traceback + pip-resolver error + surrounding context without blowing the LLM's context budget.

#### D. LLM-prompt contract (the brief TELLS the LLM what to emit)

D1. **List every baked lib + version.** `_runtime_deps_brief("<lang>")` enumerates EVERY pinned dep. The LLM references this to avoid importing things that aren't there (brief mismatch → import error → retry loop).

D2. **List what NOT to emit in requirements.** Explicitly tell the LLM:
   - "Do NOT pin the test framework (pytest/jest/cargo-test/go-test) in requirements.txt — it's already installed and re-pinning breaks it."
   - "Do NOT pin the MAJOR framework versions (pydantic, sqlalchemy, fastapi, express, gin) unless your solution needs a different major version."
   - "Do NOT use `-e`, `--index-url`, `--extra-index-url`, or extras syntax like `pydantic-settings[dotenv]` that require building C extensions in the grader."

D3. **Show the FILE LAYOUT the grader expects.** Explicit paths: `/app/solution.py`, `/app/tests/test_solution.py`, `/app/tests/__init__.py` (empty). If learners' tests use relative imports (`from .solution`), tell them NOT to — our grader uses `from solution import X` absolute only.

D4. **Show the TEST COMMAND verbatim.** `cd /app && pytest tests/ -q --tb=short --junitxml=/app/_junit.xml`. The LLM's solution/tests must be compatible with this exact invocation. If the brief and the runner's actual command drift apart, every retry fails mysteriously.

D5. **Show what the GRADER PARSES.** JUnit XML `<testsuite tests="N">` attr. Jest `numTotalTests`. Go `-json` Action events. The LLM needs to know the collector counts tests, not `def test_*` source lines — so `@pytest.mark.parametrize` over N cases reports as N tests, which is the right behavior (and the old regex got wrong).

D6. **Show migration warnings for libraries with breaking changes.** Pydantic 2 BaseSettings moved to `pydantic-settings`. SQLAlchemy 2 `Session.query()` moved to `session.execute(select(...))`. bcrypt has a 72-byte password limit. These classes of errors bite EVERY retry until the brief explicitly calls them out.

#### E. End-to-end validation (run before shipping to Creator)

E1. **Trivial-add smoke test.** `run_in_docker(solution_trivial_add, language, tests=trivial_test)` → `all_passed: True, collected: >= 1`.

E2. **Wrong-solution negative test.** Same tests + intentionally-wrong solution → `all_passed: False, failed: >= 1`. This catches parser regressions (we had a pytest "N failed, M passed" vs "M passed, N failed" ordering bug that silently inflated passes to 100%).

E3. **Invariant end-to-end test.** `validate_solution_starter_invariant(stub_starter, real_solution, real_tests, language)` → `ok: True`, with `solution_result.test_results.collected >= 4` and `starter_result.all_passed is False`.

E4. **Realistic-requirements stress test.** Take a realistic `requirements.txt` (or `package.json`, or `go.mod`) from a real in-domain library (FastAPI: `fastapi==0.115 pydantic==2.10 sqlalchemy==2.0 asyncpg==0.30`). Run the invariant through `_cmd_for_lang` with that requirements block. **After the install step, the test binary MUST still be on PATH.** If not, either (a) add a defensive re-pin per B1, or (b) tighten the Dockerfile pins so the resolver doesn't need to re-install the test framework.

E5. **Creator-pipeline smoke.** Generate ONE code_exercise course step through the full Creator pipeline (`/api/creator/start → /refine → /generate`) with the new language. It must converge in ≤2 retries. If it takes 6 retries + Opus escalation, something in the brief (D) or the runtime resilience (B) is still broken — iterate before kicking off real course gens.

#### F. When a language-specific course fails: diagnostic order

1. Did the trivial-add smoke test pass today? If NO → image regression, rebuild.
2. Does the retry-feedback surface the REAL error (not just pip warning)? If NO → stderr-capture bug. See C1.
3. Does the retry-feedback name the failing dep / binary / file? If NO → missing `DEP MISSING` detection or missing binary sanity-check.
4. Does the `_runtime_deps_brief("<lang>")` list every dep the LLM imports in its solution? If NO → brief drift; regenerate with the updated brief.
5. Only if 1-4 are clean: consider "is the LLM genuinely stuck" (rare). Escalate to Opus retry.

#### Rule going forward

**Never add a new language without running E1-E5 green first.** If any check fails, the correct response is to fix the infrastructure, NOT to retune the Creator prompt. Prompt tuning never cures dependency-resilience bugs; it just burns retry budget.

### What NOT to conclude from a new-language failure

If a new language's course_id shows fallback content (Python defaults under wrong-language briefings), the default assumption is **infrastructure bug, not LLM bug**. Check in order:
1. Does `run_in_docker(trivial_solution, language, tests=trivial_test)` return `all_passed=True`?
2. Does `validate_solution_starter_invariant` succeed on a known-good triple?
3. Only THEN consider prompt tuning.

## 🧪 STRUCTURED TEST OUTPUT — prefer runtime's JSON/XML over regex-on-prose (2026-04-22 v6)

**User directive**: "Where possible, don't depend on string parsing as it is brittle. Does pytest explicitly give out structured data on what passed and failed?"

**The bug this rule prevents**: v6 beginner agent caught that `_parse_test_results` in `backend/docker_runner.py` silently scored a trivially-wrong submission (`return 0.0`) as 100% on a code_exercise. Root cause: the old regex `(\d+)\s+passed(?:,\s+(\d+)\s+failed)?` worked on `"3 passed, 1 failed"` but matched only "2 passed" when pytest emitted `"7 failed, 2 passed"` (pytest ≥6 sometimes chooses failed-first ordering), silently dropping the failed count. Every partially-wrong code_exercise submission scored 100%.

### Rule

For every new runtime we integrate (or every grader path we revisit), use the runtime's STRUCTURED output first. Regex-on-prose is the fallback, never the primary.

| Runtime | Structured option | Plugin needed? | Parser type |
|---|---|---|---|
| **pytest** | `--junitxml=<file>` (XML: `errors="0" failures="2" skipped="0" tests="5"` tag attrs) | No — built-in | `xml.etree.ElementTree` |
| **pytest** | `--json-report --json-report-file=<file>` | Yes — `pytest-json-report` in image | `json.loads` |
| **jest** | `--json --outputFile=<file>` | No — built-in | `json.loads` |
| **go test** | `-json` (NDJSON events on stdout: `{"Action":"pass","Test":"TestFoo"}`) | No — built-in | line-by-line `json.loads` |
| **rust (cargo test)** | `--format json -Z unstable-options` | Nightly Rust | `json.loads` |
| **junit (maven/gradle)** | XML reports under `target/surefire-reports/` | No — built-in | `xml.etree.ElementTree` |

### What's shipped (2026-04-22 v7 — all three runtimes)

| Runtime | Structured primary | Fallback |
|---|---|---|
| **Python** | `pytest --junitxml=/app/_junit.xml` → sentinel-wrapped, parsed via `xml.etree.ElementTree` (tests/failures/errors/skipped attrs) | Regex, independent per-field extractors |
| **Jest** | `jest --json --outputFile=/app/_jest.json` → sentinel-wrapped, parsed via `json.loads` (numPassedTests / numFailedTests / numTotalTests) | Regex on "Tests: N failed, M passed, Z total" |
| **Go test** | `go test ./... -json -count=1` → sentinel-wrapped NDJSON events, per-test Action == "pass"/"fail"/"skip" counted | Line-prefix scan for `ok ` / `FAIL ` per-package summaries |

All three use the same sentinel pattern (`__<LANG>_<FORMAT>_START__ / __END__`) so the host-side parser can extract the structured block from mixed stdout+stderr without being fooled by test output that happens to contain the words "passed" or "failed".

### Rule for all future graders

Before writing ANY `re.search(r"(\d+) passed")` style parser, check:
1. Does the tool have a JSON/XML report option? → use it.
2. Does the tool have a machine-readable stream (NDJSON events)? → use it.
3. No structured option exists? → regex is last resort. Extract each field independently (never combined ordering regexes), add sentinel markers around the block of interest so the scope is bounded.

## 🧨 EXECUTION IS GROUND TRUTH — delete pattern-matching gates when the runtime can answer (2026-04-23 v8.5)

**User directive (verbatim, 2026-04-23):** "Let's review all similar hardcoding and regex like things we have done, this will not scale. They are brittle and will break soon. Instead rely on a higher level check, does the code compile, does it run, does it fail."

### The rule

**If a property can be decided by compiling / running / observing the test runner's structured output, DO THAT. Never put a regex in the acceptance gate when the Docker invariant already answers the same question.** Pattern-matching against LLM prose is a last resort — when we use it, we label it Tier 2 in-code with a "this will drift" comment.

### The failure class that motivated the rule

Three consecutive FastAPI course gens (v5/v6/v7) died to three DIFFERENT brittle gates:

- **v5/v6**: `_re.findall(r"^\s*def\s+test_\w+\s*\(")` on `hidden_tests` — didn't match `async def test_*`. FastAPI/httpx.AsyncClient is async-first, the LLM correctly wrote async tests, counter returned 0, Layer A rejected. Six retries incl. Opus all rejected — LLM never had signal "tests look fine, something else is wrong."
- **v7**: `_python_ast_precise_check` walked the starter AST and flagged `create_test_task` + `simulate_database_error` as `looks_complete` → reject. But those were HELPER functions shipped complete on purpose for the learner to USE. The function-under-test was correctly stubbed with `raise NotImplementedError`. Six retries incl. Opus all rejected. LLM retry-feedback said "starter looks complete" which is ambiguous and unactionable.

Every one of these rejects had a cheaper, more-truthful equivalent via execution:
- Test count → `<testsuite tests="N">` from the JUnit XML the runner already emits.
- "Starter is complete?" → run it; if it passes the hidden_tests, reject. If it fails, accept.

### What was deleted in v8.5 Phase 1 (backend/main.py + backend/docker_runner.py)

1. **`_heuristic_starter_is_incomplete` + `_python_ast_precise_check`** — the AST/marker pre-filter in `validate_solution_starter_invariant`. Replaced with a sha256 equality check: if `sha256(starter) == sha256(solution)`, short-circuit reject (catches degenerate "LLM dumped solution as starter"). Zero false-positives by construction.
2. **`LanguageConfig.incompleteness_markers` regex lists** (`raise NotImplementedError`, `pass`, `panic("TODO")`, `todo!()`, `// TODO`) — no longer consulted. The Docker run of starter is the only signal.
3. **Layer A test-count regex (`def\s+test_` family)** — moved to AFTER the LangGraph invariant and reads `solution_result.test_results.collected` from the runner's structured output. Handles `async def`, class-based tests, `@pytest.mark.parametrize` expansions, decorators — the runner discovers them all.
4. **`_XLANG_PHRASES` (18 strings)** + **`_MULTIFILE_PHRASES` (7 strings)** + **`_fs_ref_re`** in `_is_complete` — all deleted. If the exercise is genuinely unsolvable, solution fails in Docker. If solution passes, the exercise is solvable regardless of prose.

### What was ADDED in v8.5 Phase 1

1. **`collected` + `collection_error` + `collection_error_msg`** on test_results dict — propagated through `_finalize` in `_parse_test_results`. Layer A reads `collected`; retry feedback surfaces `collection_error_msg` when pytest could not collect any tests (conftest import error etc.).
2. **`DEP MISSING:` retry-feedback prefix** — detects `ModuleNotFoundError` / `ImportError` in Docker stderr and rewrites the retry-feedback prompt to say "the runner doesn't have X installed; emit validation.requirements OR rewrite without X" instead of letting the LLM think it's a logic bug.
3. **sha256 pre-filter** — only surviving heuristic. 100μs, catches the one failure mode it can catch, rejects nothing else.

### The rule for adding a new language / runtime

When you add a new `LanguageConfig` (next: Ruby, C#, Kotlin), you no longer need:
- an `incompleteness_markers` regex list
- a `precise_check` function
- any Layer A test-count regex

You DO need:
- A Dockerfile that installs the language + test framework + commonly-used libs (match the `_runtime_deps_brief` promises)
- A sentinel-wrapped `cmd` that emits structured test output (junit XML / JSON / NDJSON)
- A `structured_parser` that returns `{passed, failed, total, collected, collection_error, collection_error_msg}`
- A regex fallback ONLY for when the structured output isn't emitted (stderr flood, crash before writing XML)

Adding a language used to require 3+ places of per-language regex. Now it's one config entry + one Dockerfile. Entire classes of brittle-heuristic bugs are gone because the heuristics themselves are gone.

### Evidence the fix works

Narrow-scope test (2026-04-23 v8.5): regenerated the same FastAPI code_exercise step (async Pydantic + httpx.AsyncClient + `UserRepository` helper class fully implemented in starter). OLD pipeline: 6 retries → RuntimeError. NEW pipeline: **1 retry, 43s, $0.095, 6 async tests counted correctly, no heuristic false-reject**. The regen converged on the first Sonnet attempt; zero gate failures logged.

### Rule going forward

When reviewing any future acceptance-gate code, ask:
1. Does the Docker invariant (or another runtime check) ALREADY answer this question? If yes → delete the gate.
2. If no, does the test runner's STRUCTURED output answer it? If yes → parse that, don't regex the source.
3. Only if neither → regex is fine, but LABEL it Tier 2 in-code with a "this is a heuristic, will drift, expect tightening" comment.

Tier 2 survivors (accepted brittleness): dark-theme CSS sanitizer (`_darkify_html_content` — no runtime equivalent without headless rendering), and the sha256 pre-filter (trivial, zero false-positives). Everything else went to execution.

## 🪞 NO MEDIATORS BETWEEN TOOL OUTPUT AND LLM (2026-04-23 v8.5 Phase E final)

**User directive (verbatim, 2026-04-23):** "Is it necessary to use regex? I am hoping we avoid this pattern."
**Buddy-Opus (4th consult):** "Your parser is a lossy filter pretending to be an enrichment layer. When it fails (as it did on TS v5), it fails silently with `0 fragments` and a fallback, so you get LESS information than raw passthrough would have given. The LLM reads tool output fine."

### The lesson we kept relearning

Over 4 Opus consultations I built three generations of retry-feedback MEDIATORS:

1. **Narrative wrapper** ("your TEST accesses a field…" / "your SOLUTION needs narrowing…") → misdirected the LLM when the narrative was wrong about which file had the bug.
2. **Fragment schema** ({file, line, col, excerpt, tool_message}) → still required parsing, but at least structured.
3. **Regex parser** (matched TS diagnostics, pytest tracebacks, Go/Rust/Jest) → silently returned `0 fragments` on any format it didn't recognize, delivering LESS info than the raw text.

Each generation was "a more sophisticated version of: I don't trust the LLM to read tool output."

### The principle (final)

> **Never interpose a mediator between precise tool output and a capable reader.** Pass the raw stderr + stdout tails + harness-stripped list + optional enrichment. ONE instruction: "Fix these sites." No regex, no prose, no fragment schema. The LLM reads `solution.ts(56,41): error TS2339` natively — it does not need you to extract line 56, add `>>>` markers, and paraphrase the error.

### What the retry-feedback contract looks like now

```
## Errors from last retry (tool output; fix these sites):

### stderr
```<RAW_STDERR_TAIL_1500_CHARS>```

### stdout
```<RAW_STDOUT_TAIL_1500_CHARS>```

### harness stripped from your validation.requirements (do not re-emit)
- pytest==7.4.0 (forbidden: pytest is baked in the runner image)
- top-level `scripts` (unsafe — resolver/shell attack surface)

### solution's inferred shape (from compiler)   ← OPTIONAL (Phase D enrichment)
```<DTS_OR_TYPE_SIGNATURE>```

Fix these sites. Emit a corrected full solution + tests.
```

All parts that APPEAR are raw tool output, not harness interpretation. The only rule the harness enforces is presentation order (stderr above stdout, stripped lines as a list, enrichment at the end).

### When mediation IS OK

- **Structural enrichment that doesn't interpret** — e.g. Phase D's `solution_shape_extractor` runs `tsc --declaration` to emit `.d.ts`. That's NEW tool output from a SECONDARY toolchain invocation. Appending it is adding data, not interpreting the original error. Gated by `type_grounding_error_codes: str in combined_output` — a substring check, not a regex parser.
- **Structured tool outputs parsed via their native format** — junit XML, jest `--json`, `go test -json`, `cargo --message-format=json`. These are DATA formats the tool is guaranteed to emit. Parsing XML / JSON != regex-on-prose. (We already do this for test-result counts.)
- **Fixed-format harness output we ourselves emit** — `harness_stripped_entries` is a list the harness produced, not something we parsed. Listing it verbatim is fine.

### When mediation is NOT ok

- Parsing prose error messages with regex to extract file/line/column.
- Routing the retry prompt based on which file "probably" has the bug.
- Writing "narrative" prose like "your test is wrong" or "you forgot to narrow."
- Any heuristic that silently fails to recognize a tool format the LLM could read directly.

### Diagnostic test

Before adding ANY retry-feedback enrichment, ask:
1. Could the LLM read the raw tool output and figure this out?
2. If the tool changes its output format next version, does my enrichment fail silently or fail loudly?

If answer to 1 is "yes," don't add the mediator. If answer to 2 is "silently," definitely don't add it.

### Corollary: narrative prose retirements (2026-04-23 v8.5)

All of these were removed from the retry path:
- `"ONE-FILE ARCHITECTURE VIOLATION: you used 'from models import ...'"` — deleted. LLM reads `ModuleNotFoundError: No module named 'models'` fine.
- `"DEP DRIFT: the harness detected that your requirements caused X..."` — deleted. Raw `DEP_DRIFT:` line speaks for itself.
- `"DEP MISSING: the Docker runner's Python image does not have X..."` — deleted. Raw `ModuleNotFoundError: No module named 'X'` is the signal.
- `"TYPE-GROUNDING GROUND TRUTH: the TEST you wrote accesses..."` — deleted (was misdirecting anyway). Phase D remains as a shape-append, no prose.

## 🎯 COMPILER-GROUNDED RETRY FEEDBACK (2026-04-23 v8.5 Phase D)

**User directive:** "Solve the Zod error without LLM prompting and without hardcoding."
**Buddy-Opus verdict:** ship Option E (compiler-grounded test regen), NOT transpile-only.

### The principle

> **When a tool's output tells us a fact about our own code, surface that fact as structured context in the next retry — don't make the LLM re-discover it.**

When the LLM iterates 6+ times on the same error variant (Zod safeParse narrowing: `TS2339: Property 'error' does not exist on type '{success: true, data: X}'`), the retry-feedback layer is weak. The LLM doesn't know the solution's exact inferred type, so it guesses — and guesses wrong. Feeding the SOLUTION'S REAL `.d.ts` into the retry prompt as structural grounding turns a 6-retry thrash into a 1-retry fix.

This is NOT brief-tuning (we don't edit general TS guidance). This is NOT hardcoding (we don't pattern-match Zod specifically). It IS surfacing compiler-emitted ground truth on specific failure-class retries.

### The mechanism (per-language, extensible)

Each `LanguageConfig` declares:

```python
@dataclass
class LanguageConfig:
    # ...
    type_grounding_error_codes: tuple[str, ...] = ()
    solution_shape_extractor: Optional[Callable[[str], Optional[str]]] = None
```

When a LangGraph invariant FAIL reason matches any entry in `type_grounding_error_codes`, the harness:
1. Invokes `solution_shape_extractor(solution_code)` — runs a SECONDARY toolchain command (not the test runner) to extract the solution's inferred type/signature.
2. Prepends the extracted shape to the retry feedback with a structural prompt ("here's the real type; narrow before accessing").
3. LLM regenerates; next attempt is now grounded.

### Per-language wiring (extensibility table)

| Language | Error codes | Extractor invocation | Ground-truth output |
|---|---|---|---|
| **TypeScript** ✅ shipped | `TS2339` `TS2532` `TS18048` `TS2322` `TS2345` | `tsc --declaration --emitDeclarationOnly` with /runner/node_modules mounted for type resolution | Full `.d.ts` showing discriminated unions, Zod-inferred shapes, generics |
| **Rust** | `E0308` `E0599` `E0277` | `cargo check --message-format=json` + `cargo --explain <code>` | JSON diagnostics with suggested fix + expected trait bounds |
| **Java** | `cannot find symbol` with generics, `incompatible types` | `javac -Xlint:all -Xprint` | Fully-qualified typed signature of the method |
| **Python** | `mypy error: has no attribute` | `mypy --reveal-type` + `stubgen` → `.pyi` | Inferred type annotations for exported names |
| **Go** | `undefined: X.Y`, type-mismatch errors | `gopls` LSP `textDocument/hover` | Struct shape + method set |
| **SQL** | column-type mismatch / missing column | `EXPLAIN (VERBOSE, FORMAT JSON) <query>` | Column types, nullability, table schema |

All follow the same contract: extract → feed back as structural context → normal retry loop continues with grounding.

### TypeScript reference implementation (the pattern to copy)

`_extract_ts_solution_shape(solution_code: str) -> str | None`:
1. Write solution to a tempdir
2. `docker run sll-node-runner:latest sh -c "ln -sfn /runner/node_modules /app/node_modules; tsc --declaration --emitDeclarationOnly --skipLibCheck --moduleResolution node --typeRoots /runner/node_modules/@types solution.ts"`
3. Read `/app/solution.d.ts` from workdir
4. Truncate to 2500 chars (retry prompt budget)
5. Return — or None on failure

Wire via `LanguageConfig.solution_shape_extractor=_extract_ts_solution_shape`. That's it.

### When to BUILD (not just design)

- **TypeScript**: shipped 2026-04-23. Validated end-to-end (Zod safeParse narrowing now produces usable retry feedback).
- **Other languages**: build WHEN a second language hits the same repeating-error-class pattern. Don't premature-abstract: per Opus, Rust's borrow checker has INVERSE semantics (can't transpile past), Python's duck-typing avoids the class entirely, Go has minimal type narrowing. Each language's extractor is ~50 lines — cheap to add per-instance.

### Operational rule

Before adding `type_grounding_error_codes` to any language, have at least ONE observed production run where the retry loop thrashed 4+ times on the same error code. Premature abstraction here creates a maintenance surface without evidence of need.

### Fallback (escape hatch)

After N narrowing-class retries fail despite grounding (shouldn't happen in practice, but defense in depth), fall back to a relaxed test-run mode:
- TS: `ts-jest` in `isolatedModules + diagnostics: false` (types stripped, behavior verified)
- Rust: N/A (borrow check can't be relaxed; must succeed or fail)
- Java: `javac -Xlint:none` (most warnings off, errors stay)
- Python: N/A (no compile gate)

When fallback fires, mark the step with `quality_flag="needs_human_review:<lang>_<error_class>_relaxed"` so a human can re-check. Never silently tolerate broken pedagogy.

## 🛡️ HARNESS-CLOSURE INVARIANT — MANDATORY FOR EVERY LANGUAGE (2026-04-23 v8.5 Phase B)

**User directive (verbatim, 2026-04-23):** "Let's not solve for symptoms. Look at the root cause - figure out a generic fix that is solving the root cause and is extensible. Validate the refine the approach and test it out. Add this to CLAUDE.md as a must have to all iterations."

### The invariant (the thing that is always true if the system is correct)

> **HARNESS-CLOSURE INVARIANT**: The set of binaries + packages + configs the harness uses to grade a submission MUST be immutable from within a learner's task run. Any path the LLM can write into, the harness cannot depend on.

All prior failure classes (pytest: not found, DEP_DRIFT, shadow pytest, plugin autoload, config poisoning) are special cases of one root cause: **LLM's dep installer + harness's tool closure shared one environment.** Detection/patching the symptoms has diminishing returns. The real fix is to make the invariant structurally impossible to violate.

### Why this matters

Before Phase B we shipped FIVE detection/patching layers (prompt-level "don't pin X", merge strips forbidden pins, defensive re-pin after install, post-install verify checks for drift, retry-feedback rewriter). All five were necessary because the ONE underlying invariant was violated: LLM's pip had full authority over the same env the harness pytest lived in. No detection layer PREVENTS violations; they just catch them post-hoc. Isolation ELIMINATES the class.

### Implementation per language (each language picks ONE mechanism)

| Language | Mechanism | Harness lives at | LLM's install lives at | Test command |
|---|---|---|---|---|
| **Python** ✅ shipped | Two virtualenvs | `/opt/harness-venv` (with `--system-site-packages`) | `/usr/local/lib/python3.11/site-packages` | `/opt/harness-venv/bin/pytest` |
| **JS/TS** | Two node_modules | `/runner/node_modules/.bin/jest` | `/app/node_modules` | `NODE_PATH=/app/node_modules /runner/node_modules/.bin/jest --config=/runner/jest.config.js --rootDir=/app` |
| **Go** | Two GOPATHs | `/runner/toolchain/bin/go` | `GOPATH=/app GOCACHE=/app/.gocache` | `/runner/toolchain/bin/go test ./...` |
| **Rust** | Separate cargo homes | `/runner/cargo-home` (CARGO_HOME) | `/app/target` | `CARGO_HOME=/runner/cargo-home cargo test --target-dir=/app/target` |
| **Java/Ruby/Haskell** | Execution-boundary isolation | Separate process with own classpath / bundler / cabal-sandbox | Project `.m2` / `Gemfile.lock` / `cabal.project` | Run harness test-runner as own JVM/ruby/cabal invocation; invoke LLM's compiled artifacts as data |

**Rule**: where the toolchain assumes one resolver-scope per project (Maven, Bundler, Cabal), you isolate at the EXECUTION boundary (separate process/classpath), not the install boundary. Every other language has install-boundary isolation (venv, node_modules, GOPATH, CARGO_HOME).

### Python Phase B reference implementation (the pattern to copy)

`sll-python-runner.Dockerfile`:
```dockerfile
# LAYER 1 — GLOBAL: libs the LLM imports (fastapi, pydantic, sqlalchemy, asyncpg,
# bcrypt, numpy, pandas, etc.). LLM's `pip install -r requirements.txt` lands here.
# Pytest + plugins NOT installed here.
RUN pip install fastapi==0.115.6 pydantic==2.10.4 ... hypothesis==6.122.3 freezegun==1.5.1 \
 && python -c "import fastapi, sqlalchemy, asyncpg, ...; print('global preload ok')"

# LAYER 2 — HARNESS VENV: isolated test runner + plugins. LLM cannot touch.
RUN python -m venv --system-site-packages /opt/harness-venv \
 && /opt/harness-venv/bin/pip install pytest==8.3.4 pytest-asyncio==0.25.0 \
      pytest-mock==3.14.0 pytest-json-report==1.5.0

# Snapshot for verify_baked
RUN /opt/harness-venv/bin/pip freeze | grep -iE '^(pytest|pytest-asyncio|pytest-mock|pytest-json-report|pytest-metadata|pluggy|iniconfig|packaging)==' \
      | tr '[:upper:]' '[:lower:]' > /opt/harness-venv-snapshot.txt

COPY verify_baked_python.py /opt/verify_baked.py
```

`verify_baked_python.py` (core logic, 80 lines):
```python
HARNESS_VENV_PIP = "/opt/harness-venv/bin/pip"
HARNESS_SNAPSHOT = "/opt/harness-venv-snapshot.txt"
SHADOW_FORBIDDEN_GLOBAL = frozenset({"pytest", "pytest-asyncio", ...})

# CHECK 1: harness-venv is byte-immutable against snapshot
# CHECK 2: no shadow pytest in GLOBAL site-packages
# Emit DEP_DRIFT: <pkg> baked=X post=Y on violation, exit 127
```

`_cmd_for_lang` Python branch:
```python
steps.append("pip install -q -r /app/requirements.txt 2>&1 | tail -20")  # LLM → GLOBAL
steps.append("python /opt/verify_baked.py || exit $?")  # Phase A invariant assertion
steps.append(
    "cd /app && "
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "              # Defeat plugin-autoload attack
    "/opt/harness-venv/bin/pytest tests/ -q --tb=short "  # HARNESS pytest, not global
    "-p pytest_asyncio.plugin -p pytest_mock "       # Explicit plugins we need
    "--asyncio-mode=auto --junitxml=/app/_junit.xml"
)
```

### Validation — the 5 attack scenarios every language MUST pass before shipping

Copy these smoke tests for each new language. All 5 must green before the language is approved for course generation.

| # | Scenario | Expected outcome |
|---|---|---|
| **T1** | Clean (no `validation.requirements`) | invariant PASS with `collected >= N_hidden_tests` |
| **T2** | LLM pins forbidden test-framework package (e.g. pytest 7.4) | merge strips → `harness_stripped_entries` logs the strip; invariant PASS |
| **T3** | LLM transitively drags in framework via another pkg (e.g. `pytest-cov`) | verify_baked fires `DEP_DRIFT: shadow ...`; invariant REJECT; retry feedback has actionable "drop the pin" |
| **T4** | Real-world valid requirements (framework libs at specified versions) | invariant PASS |
| **T5** | LLM emits dangerous directives (`-e .`, `--extra-index-url`, `git+https://`, `--hash`) | merge strips all; `harness_stripped_entries` logs each with reason; invariant PASS without them |

### Evidence (Python, 2026-04-23 v8.5 Phase B)

All 5 scenarios green on first shipment. T3 specifically: LLM emits `pytest-cov==6.0.0`. Pip resolver installs pytest-cov's transitive dep `pytest==9.0.3` into GLOBAL. verify_baked detects shadow pytest. Retry feedback says:

> `DEP DRIFT: shadow pytest==9.0.3 found in GLOBAL site-packages (conflicts with /opt/harness-venv/bin/pytest). LLM's validation.requirements must NOT pin pytest.`

LLM drops `pytest-cov` on retry → T3 clears. This is the pattern: structural prevention + actionable retry feedback when the invariant is tested.

### What to DELETE when Phase B ships for a language

- Defensive re-pin (`pip install pytest==8.3.4` after LLM install) — obsolete; suggests invariant can be violated.
- Binary sanity-check (`command -v pytest`) before test — verify_baked already asserts stronger.
- Prompt-level "don't pin pytest" warnings — harness strips anyway; brief can stay CAPABILITY-focused.

### What to KEEP

- **Merge function** (`requirements_merge_fn`) — still earns its keep as SUPPLY-CHAIN defense: strips `-e .`, `--extra-index-url`, `git+https://`, `--hash=` lines the isolation doesn't care about but security does. Also strips forbidden pins as a pre-install belt.
- **verify_baked script** — 50ms invariant assertion. Catches (a) regressions in the isolation itself (image-build bug), (b) transitive-shadow attacks the merge can't pre-filter (like pytest-cov → pytest).
- **Retry-feedback rewriter** — `DEP_DRIFT:` / `DEP_MISSING:` detection in main.py makes the LLM's retry prompt actionable regardless of language (assuming each language's verify emits the same error shape).

### Operational MUST-HAVE for every future language onboarding

1. **Isolation mechanism chosen + Dockerfile builds image with two-env layout.** `preload ok` for each layer.
2. **`verify_baked_<lang>.*` script** baked at `/opt/verify_baked.*`, emits `DEP_DRIFT:` on invariant violation, exit 127. Smoke-tested at image-build time.
3. **All 5 attack scenarios** (T1-T5 above) green. Run `tools/test_dep_resilience_<lang>.py` (or equivalent) before enabling the language for course gen.
4. **`_cmd_for_lang` branch** invokes the harness-isolated binary path, NEVER the global binary.
5. **`LanguageConfig`** declares `verify_baked_cmd`, `forbidden_llm_pins`, `requirements_merge_fn` (even if `always_required_packages=()` post-isolation).
6. **End-to-end Creator gen** of one code_exercise in the language converges in ≤2 retries without DEP_DRIFT or DEP_MISSING failures.

**No language ships to real course generation until all six criteria are green.** Infrastructure-before-content.

### Naming convention (artifact versioning — Opus landmine)

- Harness venv path: `/opt/harness-venv` (current) or `/opt/harness-venv-vN` (when upgraded). The retry-feedback rewriter should read the version dynamically from `/opt/harness-venv-snapshot.txt` — NEVER hardcode "pytest==8.3.4" in main.py as a string literal. When we bump pytest in the harness-venv, rewriter auto-picks it up.
- Same pattern for JS/TS (`/runner/node_modules` → `/runner/node_modules-vN`), Go (`/runner/toolchain` → `/runner/toolchain-vN`), etc.

## 🔩 LANGUAGE EXTENSION — HARNESS-LEVEL DEP MANAGEMENT (2026-04-23 v8.5)

**User directive (verbatim, 2026-04-23):** "Let the LLM know of the libraries available and its versions. The ones that you require to run, either ask the LLM to not touch OR have a harness to add it yourself before the run. Build an extensible workflow across languages and framework. Don't depend on prompt for individual language related issues. ... Goal — Any basic library dependency should not cause failure for us to generate a working assignment."

### The rule

**Dep-resilience is a HARNESS responsibility, not a prompt responsibility.** Per-language brief tweaks ("don't pin pytest", "don't pin jest") drift as new languages/frameworks land and the LLM paraphrases around them. Instead, every `LanguageConfig` declares its dep-management contract; the runner enforces it uniformly across Python, JS/TS, Go, Rust, Java — and any future language.

### Three layers of defense (Opus-reviewed 2026-04-23)

| Layer | What it does | When it fires |
|---|---|---|
| **1. Merge (pre-install)** | `requirements_merge_fn(llm_reqs, cfg) → (merged_text, stripped[])`. Whitelists safe line shapes (`pkg`, `pkg==ver`, `pkg[extra]`, comments). Strips forbidden pins (test framework) + dangerous directives (`-e .`, `--extra-index-url`, `git+https://`, `--hash`). Appends `always_required_packages`. | Before writing the requirements file into the container workdir. |
| **2. Defensive re-install (install-time)** | After LLM's deps install, idempotently re-pin the test framework. Harmless when versions already match. | Inside the container, right after `pip install -r requirements.txt`. |
| **3. Post-install verify (post-install)** | `verify_baked_cmd` checks every PROTECTED package against its baked version. Exits 127 with `DEP_DRIFT: <pkg> baked=X post-install=Y` if any mutation is detected (incl. transitive downgrades the merge couldn't see). | Inside the container, before test runner invocation. |

Layers 1 + 3 are load-bearing. Layer 2 is insurance. All three are independent — each catches drift classes the others miss.

### `LanguageConfig` contract (the extension surface)

When adding a new language, add ONE `LanguageConfig` with these four fields; no prompt edits required:

```python
LanguageConfig(
    ids=("rust", "rs"),
    image="rust:1.75-alpine",
    prebuilt_image="sll-rust-runner:latest",
    # ... existing fields (sentinel, parser, compile_check_cmd) ...
    
    # ── DEP MANAGEMENT (v8.5) ──
    # Post-install verification script baked into the image at /opt/.
    # Must exit 127 with DEP_DRIFT: lines on drift; 0 otherwise.
    verify_baked_cmd="cargo verify-baked || /opt/verify_baked.sh",
    # Package names (lowercase, no version) the LLM MUST NOT re-pin.
    # Typically the test framework. The merge strips these before install.
    forbidden_llm_pins=frozenset({"cargo-test", "rustc"}),
    # Packages the runner ALWAYS installs regardless of LLM input.
    # Belt-and-braces defense if prebake drifts.
    always_required_packages=("serde==1.0", "serde_json==1.0"),
    # Per-language merge: handle TOML (Cargo.toml), JSON (package.json),
    # flat text (requirements.txt), module (go.mod) formats uniformly.
    requirements_merge_fn=_merge_cargo_toml,  # or _merge_pip_requirements, _merge_package_json, ...
)
```

### Per-language merge functions (implement one per language)

| Language | Format | Merge function | Notes |
|---|---|---|---|
| **Python** | flat `pkg==ver` | `_merge_pip_requirements` (shipped) | Whitelist shapes in `_SAFE_PIP_LINE_RE`. |
| **JS/TS** | `package.json` JSON | `_merge_package_json` (TODO) | Parse JSON, delete forbidden keys from `dependencies`/`devDependencies`, merge always-required, emit back. |
| **Go** | `go.mod` syntax | `_merge_go_mod` (TODO) | Drop forbidden `require` lines, append always-required `require` lines. |
| **Rust** | `Cargo.toml` | `_merge_cargo_toml` (TODO) | Parse TOML, strip forbidden `[dependencies]` / `[dev-dependencies]` keys. |
| **Java/Maven** | `pom.xml` XML | `_merge_pom_xml` (TODO) | Parse XML, strip forbidden `<dependency>` nodes. |

All four return `(merged_text, stripped_entries)`. `stripped_entries` is `list[str]` of human-readable reasons that surface in retry feedback.

### Per-language verify scripts (one per language)

Each prebuilt Dockerfile `COPY`s a `verify_baked_<lang>.*` script to `/opt/verify_baked.<ext>`. The script compares installed versions against PROTECTED_VERSIONS and exits 127 with `DEP_DRIFT:` lines on drift. Language-specific queries:
- Python: `pip freeze` → grep for baked packages.
- JS/TS: `npm ls --json --depth=0` → parse versions.
- Go: `go list -m all` → check baked module versions.
- Rust: `cargo tree --format {p}` → check crate versions.
- Java: `mvn dependency:tree -q` → parse output.

The reference Python script (`backend/docker_images/verify_baked_python.py`) has 80 lines total — implement its equivalent for each new language.

### Retry-feedback rewrites (language-agnostic)

`main.py` detects `DEP_DRIFT:` / `DEP MISSING:` / `ModuleNotFoundError:` / `sh: 1: <bin>: not found` in the invariant's failure reason and rewrites the retry-feedback prompt to be actionable. The detection regex is language-agnostic — every runner emits the same error shape. Extending to new languages = use the same error format in your verify script + your `_cmd_for_lang` error paths.

The `harness_stripped_entries` list is appended to every failure-reason's retry feedback:

```
HARNESS-STRIPPED entries from your requirements (do NOT re-emit these):
  - pytest==7.4.0 (forbidden: pytest is baked in the runner image)
  - -e . (unsafe directive — only `pkg==ver` lines allowed)
  - --extra-index-url https://evil.example.com/pypi (unsafe directive...)
```

LLM learns what the harness filtered, stops re-emitting.

### Where NOT to put dep-resilience logic

1. **Not in the prompt.** The `_runtime_deps_brief` lists what's available but doesn't NEED to beg the LLM not to pin things — the harness strips them anyway. Pruning the brief's "do NOT pin X" sections as each language onboards to harness-merge is fine; the brief stays short + focused on CAPABILITIES, not negative rules.
2. **Not in the LangGraph invariant.** The invariant runs tests, not dep management. If the Docker run fails with `sh: pytest: not found`, that's an image problem caught by verify_baked, not an invariant problem.
3. **Not in `_is_complete`.** Step content validation is separate from container-runtime dep management.

### Validation checklist before shipping a new language

1. `docker build -f sll-<lang>-runner.Dockerfile` succeeds; `verify_baked_<lang>` invokes at image-build time with `preload ok` output.
2. Smoke test:
   - T1 clean: realistic in-domain requirements → invariant passes
   - T2 forbidden pin: LLM emits pin in `forbidden_llm_pins` → merge strips + `harness_stripped_entries` contains the pin, invariant still passes
   - T3 drift simulation: install a drift-forcing dep → verify_baked fires `DEP_DRIFT:`, invariant returns `ok: False`
   - T4 dangerous directives: LLM emits `-e .` / index URL / git URL → merge strips all + logs
3. End-to-end Creator gen of one code_exercise in the new language → converges in ≤2 retries without DEP_MISSING / DEP_DRIFT failures.

Without all 4 smoke + 1 end-to-end green, do NOT onboard real course generation in the new language.

### Evidence the architecture works

Phase A + Phase C smoke test (2026-04-23) — 4/4 scenarios on Python runner:
- T1 clean `fastapi==0.115.6 pydantic==2.10.4` → invariant PASS.
- T2 forbidden pytest pin → merge stripped `pytest==7.4.0 (forbidden)` + `pytest-asyncio==0.21.0 (forbidden)`; invariant PASS without the pins.
- T3 drift attempt (`pydantic==2.0.0`) → defensive re-pin absorbed it; invariant PASS.
- T4 dangerous directives (`-e .`, `--extra-index-url https://evil.example.com/pypi`, `git+https://github.com/foo/bar.git`) → all 3 stripped + logged in `harness_stripped_entries`.

Phase B (two-venv Python) is DEFERRED — Opus review flagged it as the load-bearing piece that eliminates the class entirely, but Phase A + C + defensive re-pin caught every scenario in the smoke test. Ship Phase B when we see a DEP_DRIFT that A+C couldn't catch.

## 🧑‍🤝‍🧑 BUDDY-OPUS REVIEW — when stuck, write a brief + get a second opinion (2026-04-23 v8.3)

**User directive (verbatim, 2026-04-23):** "Every time you get stuck — can you create a small brief of the issue, what you tried, with specifics (versions and libraries) and kick off a buddy Opus agent to review and share feedback? Try it the next time you get stuck."

### The pattern

When I (the on-task Sonnet) hit a bug I can't root-cause in 1-2 tries, I STOP and write a compact brief, then send it to Opus for a second opinion. Opus runs cold — no context from our session, just the brief — which means its hypotheses come from pure reasoning about the facts, not from the rut I got stuck in.

### What goes into the brief (≤ 500 words, always)

1. **One-line problem statement** — "X returns None when called from Y"
2. **Reproducer** — the exact 3-10 lines that trigger the bug
3. **Expected vs actual** — what should happen, what does happen
4. **Evidence** — log excerpts, error messages, DB state snippets
5. **Versions + libraries** — Python / Node / framework / library versions that are relevant
6. **What I tried** — 2-5 hypotheses I already ruled out (and how)
7. **What I suspect** — my best current guess + what would confirm it
8. **Where to look** — relevant file paths + line numbers so Opus can dig if needed

### Where the buddy lives

Helper function in `backend/main.py` → `ask_opus_buddy(brief_md: str) -> str`. Uses `_llm_json_call` with `model=_OPUS_MODEL` + a "senior engineer peer reviewer" system prompt. Returns Opus's response. Cost ~$0.05-0.15 per consult.

### When to call

- After 2 failed fix attempts on the SAME bug
- When the reproducer works but the fix hypothesis is unclear
- When the same class of issue is hitting multiple pipelines (e.g. TS + FastAPI both failing code_exercise)
- Before a wide-blast fix that touches 5+ files — get a second pair of eyes first

### What NOT to do

- Don't call it for every small uncertainty — the tax is real ($0.10 + ~200ms latency)
- Don't dump the full repo into the brief — 500 words is the cap
- Don't blindly implement Opus's suggestion — read it, critique it, pick the parts that fit
- Don't let it replace debugging — it's a sanity check, not an oracle

### Record the outcome

Every buddy-Opus consult that leads to a real fix goes in a rolling log at `reviews/buddy_opus_log.md` with the brief + verdict + whether the suggestion was adopted + the actual fix that landed. Over time this trains our own instincts: where did Opus help vs where did it miss?

---

## 📦 RUNTIME-DEPS BRIEF — always pin library versions in code-gen prompts (2026-04-23 v8.2)

**User directive (verbatim, 2026-04-23):** "Did we specify the library versions and other dependencies to sonnet while generating ts project?" — followed by "add to claude.md and follow everytime."

### The miss that motivated this rule

TS v3 course gen exhausted 5 retries on a single `code_exercise` step. Post-mortem: our `sll-node-runner` image ships specific pinned versions (jest 29.7.0, ts-jest 29.2.5, typescript 5.7.2, @types/node 22.10.2, @types/jest 29.5.14, zod 3.24.1, express 4.21.2, ...), but the Creator prompt didn't tell the LLM any of this. The LLM wrote plausible code targeting *generic modern TypeScript* — some of which triggered ts-jest transform edge cases or TS version-specific type-narrowing features that our image's pinned versions didn't support. Each retry produced a slightly different version-mismatch failure.

### Rule (non-negotiable for every new language / runtime)

When the Creator generates a `code_exercise` / `system_build` / any step with a specific runtime, the prompt MUST include a RUNTIME-DEPS BRIEF listing:

1. **Language version** (Python 3.11, Node 20, Go 1.22, Rust 1.75, Java 21)
2. **Test framework + version** (pytest 8.x, jest 29.7.0, `go test` stdlib, cargo test, JUnit 5.10)
3. **Pinned dependency versions** available by default (what's in the Docker runner image — jest, ts-jest, zod, express, etc.)
4. **What is NOT available** (things the LLM must NOT import because they'd fail at runtime)

### Reference implementation

`_runtime_deps_brief(language) -> str` in `backend/main.py`. Returns a prompt fragment like:

```
RUNTIME ENVIRONMENT (TypeScript) — your solution + tests run under:
  - Node 20 (slim)
  - TypeScript 5.7.2
  - jest 29.7.0 + ts-jest 29.2.5
  - @types/node 22.10.2, @types/jest 29.5.14
  - Available libs: zod@3.24.1, express@4.21.2, supertest@7.0.0, axios@1.7.9,
    bcrypt@5.1.1, jsonwebtoken@9.0.2, pg@8.13.1, redis@4.7.0, rxjs@7.8.1
  - NOT available: vitest, mocha, chai, puppeteer, playwright, @nestjs/*
  - DO NOT emit `import` statements for packages not in the list above.
  - jest.config: ts-jest preset, testEnvironment=node, target=ES2020, module=commonjs.
```

Inject it right after L5 algorithm-patterns in the `code_exercise` branch of `_llm_generate_step_content`.

### Adding a new language

Before shipping a new `_LANG_CONFIGS` entry:

1. Build the Docker image (`backend/docker_images/sll-<lang>-runner.Dockerfile`).
2. Record its EXACT pinned versions in `_runtime_deps_brief()` as a new branch.
3. Include the version list in the smoke test assertion — if the test file ever drifts from the image, the smoke test catches it.
4. Test generating a course in that language BEFORE running any real regen. The smoke course's first `code_exercise` must converge in ≤2 retries.

### Rule going forward

Every time we pin or bump a library version in a runner image, we ALSO update `_runtime_deps_brief()`. These two must NEVER drift apart. A drift guarantees a future TS-class failure where the LLM writes code for a version we don't ship.

## 🔁 LLM RETRY POLICY — always pass prior failure reason into the next call (2026-04-23 v8.1)

**User directive (verbatim, 2026-04-23):** "For LLM retries always pass on last failure reasons in future calls."

Every LLM retry in the Creator pipeline (and any future LLM-driven loop) MUST feed the PRIOR ATTEMPT'S EXACT FAILURE REASON into the next prompt. Without this the LLM makes different-class-of-same-bug errors on each retry (Go: unused-import roulette; adaptive_roleplay: missing-counterparty-then-missing-hidden_state-then-missing-win_conditions) with no memory of what it already got wrong.

### The pattern (reference implementation)

```python
# Module-scope closure variable carries the last failure reason
_last_invariant_reason = [""]

def _is_complete(content_obj, ex_type):
    ok, reason = validate_step_against_ontology(...)
    if not ok:
        # Capture for the NEXT retry's prompt
        _last_invariant_reason[0] = f"Ontology gate rejected: {reason}"[-800:]
        return False
    # ... also capture compile errors, JSON parse failures, test failures ...

# In the retry loop:
if _last_invariant_reason[0]:
    _hint_parts.append(
        "**EXACT FAILURE FROM LAST ATTEMPT** — fix THIS specifically, "
        "don't introduce new variables/imports that weren't in the error:\n"
        "```\n" + _last_invariant_reason[0] + "\n```\n"
    )
```

### What MUST be captured for retry feedback

1. **Ontology gate rejections** — specific `required_demo_data` / `required_validation` field that was missing.
2. **Compile errors** — exact stderr line from `go test` / `python -m py_compile` / `tsc --noEmit`.
3. **LangGraph invariant failures** — "solution didn't pass tests" OR "starter passed its own tests".
4. **JSON parse failures** — char position + first 200 chars of the bad payload.
5. **Test failures** — which tests failed, with their assertion messages.
6. **Content-quality rejections** — which filler pattern matched / which anti-pattern was detected.

### Rule for all future Creator code

Before shipping ANY new LLM retry loop:
1. Identify every rejection path (what makes `_is_complete` return False / what makes the LangGraph validator fail).
2. Capture the rejection reason into a closure slot at the moment of rejection.
3. Inject the captured reason into the next retry's prompt under a clearly-labeled "EXACT FAILURE FROM LAST ATTEMPT" header.
4. Cap the captured string (800 chars is plenty) so the retry prompt stays lean.
5. Do NOT swallow the failure reason — every `except:` clause in the retry loop must log the exception AND preserve it for the next attempt.

### Current status
- ✅ `_last_invariant_reason` wired through the step-gen retry loop in `_llm_generate_step_content` — captures Go compile errors + ontology-gate rejections.
- ✅ Track-ontology outline validator (`_llm_refined_outline`) feeds tier/coverage violations back into the outline retry prompt.
- Pending: JSON parse failures in `_llm_json_call` aren't captured for callers yet — if a retry caller wants that signal it has to wrap the call. Nice-to-have, not blocking.

### Anti-pattern (never do this)
```python
# BAD — the LLM has no memory of what it got wrong.
while not _is_complete(content):
    content = _llm_call(system, user_prompt)  # same prompt, different attempt, random outcome
```

## 🐛 CODE_REVIEW LINE RENDERING — alternate-line issue (2026-04-22 v6 backlog)

User screenshot 2026-04-22 v6 caught the code_review template rendering the starter code with what looks like **alternating blank lines** between each real line of source. The line numbers ARE sequential (13, 14, 15, …) so it's not the row-skip that the user's phrasing suggests — but there ARE blank lines between every logical section of code.

Root-cause hypotheses to investigate:
1. Creator emitted code with double newlines (`\n\n`) between statements → `code.split('\n')` produces blank lines in between → template renders each as its own `.cr-line`.
2. Line-height CSS on `.cr-line` is too generous, visually exaggerating the gaps.
3. Some pre-serialization step (source-material grounding? sanitizer?) is inserting blank lines.

Fix options (next iteration):
- `mountCodeReview` in `drag_drop.js` could collapse runs of blank lines (keep at most 1 blank between non-blank lines).
- Creator prompt for code_review starter could require tight formatting ("no double-blank lines between statements").
- Or: leave the blanks, just dim the `.cr-line.empty` rows visually so they don't distract.

Explicitly deferred by user: "Add to backlog, fix in next iteration."

## 🧪 TEST-STRENGTH GATE — Layer A shipped, Layer B backlog (2026-04-22 v3)

**The bug the beginner-agent caught**: 3 code_exercise steps passed 100% with trivially wrong submissions (`return 0`, `return 1`, `return sum(nums)/len(nums)` that ignored `k`) because the Creator emitted only 1-2 hidden_tests — too thin to catch an obviously-wrong implementation. The solution/starter invariant passed (solution passed tests, starter failed) but the TEST SET itself didn't distinguish the solution from trivial stubs.

**User directive (2026-04-22)**: "For all code exercises — prompt to add test cases that help unlock learning. This is crucial for the outcome of the course. Okay to do this in prompt for now. Add Layer B to backlog."

### Layer A — SHIPPED
1. **Creator prompt strengthened** (`_llm_generate_step_content`, the `hidden_tests` field in the code_exercise schema prose): mandated minimum 4 tests, target 5-6; explicit anti-stub coverage list (10 trivial stubs every test set MUST defeat); 4 required test categories (happy-path / edge / boundary / adversarial); worked GOOD example showing 6 tests that defeat 4 trivial stubs; BAD example showing the single-test failure mode. Framed as a learning-outcome issue, not a technical one: "weak tests = course fails at its job."
2. **Hard floor in `_is_complete`** (code_exercise branch): regex-counts `def test_` / `test(` / `func Test` occurrences in `hidden_tests` source. If count < 4, the step is rejected and regenerated. Layer A is the minimum-viable gate: it doesn't prove the tests CATCH trivial stubs, only that there are enough of them to have a chance.

### Layer B — BACKLOG (canonical-stub adversarial probe at generation time)

Wire into the generation LangGraph loop, right after the solution/starter invariant:
```
1. LLM emits: solution.py + hidden_tests + starter.py (existing)
2. Run solution against tests → all must pass (existing)
3. Run starter against tests → all must fail (existing)
4. [NEW] Extract fn names from solution via AST
5. [NEW] Generate 5-10 canonical wrong stubs using those names:
   - def <fn>(*a, **kw): return 0
   - def <fn>(*a, **kw): return None
   - def <fn>(*a, **kw): return []
   - def <fn>(*a, **kw): return a[0] if a else 0
   - def <fn>(*a, **kw): return len(a[0]) if a else 0
   - def <fn>(*a, **kw): return sum(a[0]) if a else 0
6. [NEW] Run all stubs through hidden_tests in Docker
7. [NEW] For each stub that passes: ask LLM "emit 2 more hidden_tests
   that would distinguish the real solution from <this stub source>"
8. [NEW] Re-run step 6. Loop up to 3x. If any stub still passes after
   3 iterations, quarantine the step (weak_tests_detected=true,
   shown to learner with different warning).
```
Cost: +5 Docker runs per step × 1s = +5s at gen time, +100s per 20-step course. Acceptable.

**Why Layer B matters beyond Layer A**: Layer A only counts tests. 4 weak tests can still all pass `return 0`. Layer B proves each generated test SET empirically blocks trivial-stub submissions.

**Why it's backlog (not immediate)**: needs AST-based function-name extraction + stub-code generator + Docker-run orchestration + LLM-retry loop. Non-trivial. Layer A + the serve-time warning cover 80% of the pain for now.

## 🎭 VIEW-TEMPLATE + JSON-ONLY ARCHITECTURE (2026-04-21)

**Separation principle (non-negotiable going forward)**: for every assignment type EXCEPT interactive slides, the **view** is a static template file (HTML + CSS + JS) that WE own and check into `frontend/templates/`, and the **data** is a pure JSON payload produced by the Creator API. The LLM never emits UI/CSS/JS for assignments. Templates are versioned assets — CDN-portable tomorrow without touching the LLM pipeline.

**Why**: today's Creator generates HTML/CSS/JS inline on every step, which is the root cause of the recurring dark-theme violations, zombie-setInterval bugs, wall-of-text rendering, plurality drift, and "wild-west" widget quality. Moving the view into owned templates kills that entire bug class AND makes the product CDN-deployable for future scale.

### Assignment-family dispatch

| Family | Creator JSON shape | Judge (grader) | View template |
|---|---|---|---|
| **Drag-drop** — parsons / ordering / categorization / sjt / **code_review** | `{items[], correct_mapping OR correct_order OR bug_lines, explanations[]}` | Simple backend endpoint — takes learner's ordering/click-set, returns per-item correctness JSON | `frontend/templates/drag_drop.*` — renders items, handles drop, calls judge, displays per-item ✓/✗ |
| **Code — runnable language** (Python, Node, Go, Ruby, Java, Rust, etc.) | `{problem_statement, code (starter), test_cases[]}` | **Docker** container — builds + runs learner's code, executes tests, returns per-test pass/fail | `frontend/templates/code.*` — Monaco editor, Run button, test-results panel |
| **Code — infra language** (Dockerfile, Kubernetes YAML, Helm, Terraform, docker-compose) | Same shape: `{problem_statement, code (starter), test_cases[]}` | **GitHub Actions** workflow — learner pushes branch, GHA builds image / applies manifest / lints / probes, reports conclusion back | Same `frontend/templates/code.*`, dispatches to GHA runner instead of Docker |
| **Project / Capstone** (multi-file, deployable) | `{problem_statement, starter_files[], test_cases[] OR probe_url OR gha_workflow_check}` | **GHA** OR **URL/IP probe** OR **hidden tests** — Creator picks per capstone | `frontend/templates/project.*` — WebContainer (Monaco + file tree + virtual terminal) for multi-file editing, submit bar, grader-feedback panel |
| **Interactive slides** (concept widgets — teaching surface) | **UNCHANGED** — LLM still generates HTML/CSS/JS as today | N/A (no grading) | LLM output injected directly; wrapped by managed-script teardown (Fix A) |

### LLM quality passes (multi-pass, echoing the LangGraph pipeline from `~/Downloads/SYSTEM_ARCHITECTURE.md`)

For every assignment JSON payload, the Creator runs:
1. **Generate** — LLM produces `{problem_statement, code, test_cases}` (or family-specific fields).
2. **Critique** — self-critique pass scores quality (clarity, difficulty, realism, cheese-proofness). Refine if < threshold. Max 3 iterations.
3. **Validate — syntax** — parse check on `code` + `test_cases`.
4. **Validate — full (solution/starter invariant)** — Creator also emits a hidden `solution` file. Grader runs: (a) solution MUST pass all tests, (b) starter MUST FAIL tests. Both conditions required — otherwise the exercise is either unsolvable or already solved.
5. **Fix loop** — if validation fails, route to fix-solution / fix-tests / fix-problem based on failure category. Max 5 fix attempts, then quarantine the step.
6. **Score difficulty** — final rubric scoring.
7. **Package** — emit the final JSON payload for the frontend template to render.

No step is published to a learner without passing every gate. The `_is_complete()` + ontology gate from this session is step 0 of this pipeline; the rest (critique / solution-starter invariant / fix loop) is the LangGraph rewrite on the roadmap.

### File layout (target — to be built out across the next iterations)

```
frontend/templates/
├── drag_drop.html        # parsons / ordering / categorization / sjt / code_review
├── drag_drop.js
├── drag_drop.css
├── code.html             # runnable-language exercises (Docker judge)
├── code.js               # includes Monaco mount + judge dispatcher
├── code.css
├── code_infra.js         # tiny variant that dispatches to GHA judge instead of Docker
├── project.html          # capstone / multi-file (WebContainer + file tree + terminal)
├── project.js
├── project.css
└── manifest.json         # template registry (version, asset URLs) — CDN-portable
```

The template registry is consumed by the frontend on step load: `POST /api/step/{id}` returns `{exercise_type, template_id, data}`; the frontend loads the template's JS bundle (local today, CDN tomorrow) + hands it the `data` payload. The template's judge handler calls back to the appropriate judge endpoint (simple-backend / Docker / GHA) and renders results.

### Interpretive choices locked in (2026-04-21)

1. **`code_review` sits in the drag-drop judge family** — learner clicks buggy lines, backend does set-match against `bug_lines`. No Docker needed.
2. **"VS Code" in project templates = WebContainer/Monaco + file tree + virtual terminal** — in-browser, no VS Code Server pod per learner unless/until we ship one.
3. **Dockerfile-exercise dispatch** splits on what the learner WRITES: writing a Dockerfile → GHA judge; writing Python that a Dockerfile runs → Docker judge.
4. **Interactive slides stay LLM-HTML today** with the Fix-A managed-script teardown in place. Long-term, slide types migrate to templates too.

## 🧬 ONTOLOGY LAYER (2026-04-21 — shipped as `backend/ontology.py`)

**The rule**: every decision the Creator makes (slide shape, assignment type, course mode, tech domain, runtime) is a REGISTRY ENTRY, not a prose line in a prompt. Creator prompts are **assembled** from the registry at call time. Adding a new type = one `register_*()` call from an extension module. The Creator never invents outside the registry.

**Five layers in `backend/ontology.py`** (each mutable, extensible via `register_*()` helpers):

| Layer | Registry | Purpose |
|---|---|---|
| **1. Slide types** | `SLIDE_REGISTRY` | Templated content cards (concept_card, diagram_flow, checklist, table_compare, code_read, callout_warn/tip, stat_highlight, domain_legend, mini_demo). Each has a frozen HTML template + dark-theme CSS + declared field schema. Replaces free-form inline HTML that produced the recurring dark-theme + zombie-setInterval bugs. |
| **2. Assignment types** | `ASSIGNMENT_REGISTRY` | Exercise types with **grade primitives** declared explicitly: `compile / hidden_tests / property_test / lint / must_contain / bug_lines / state_assertion / endpoint_probe / gha_workflow_check / artifact_flag / llm_rubric / benchmark_score`. Every code-writing assignment MUST include ≥1 cheese-proof primitive (anything except `must_contain` alone). |
| **3. Course modes** | `COURSE_MODE_REGISTRY` | Module-shape contracts (linear / case_library / simulator_workday / drill_only / certification_track). Each enforces min/max module counts + capstone-type whitelist. |
| **4. Tech domains** | `TECH_DOMAIN_REGISTRY` | **The master list for tech courses.** 13 domains V1: backend_python, backend_node, backend_go, frontend_react, data_sql, data_ml, data_analytics, devops_docker, devops_k8s, ops_sre, security_appsec, ai_dev_tools, observability. Each has canonical stack + preferred assignments + runtime requirements + fixture-library pointers. |
| **5. Runtimes** | `RUNTIME_REGISTRY` | Execution primitives the grader dispatches to: `python_sandbox / sql_sqlite / yaml_schema / dockerfile_lint / shell_bash_n` (ready) + `docker / github_actions / vscode / terminal / ephemeral_k3d / ephemeral_system / webcontainer / benchmark_server` (planned first-class objects per user 2026-04-21 directive). Each declares which grade primitives it supports. |

**Extending the ontology** — one call, no prompt rewrites:
```python
from backend.ontology import register_slide, register_assignment, SlideType, AssignmentType
register_slide(SlideType(id="my_new_card", description="…", html_template="…", fields={"x":"str"}))
register_assignment(AssignmentType(id="my_capstone", grade_primitives=["hidden_tests","state_assertion"], ...))
```

**Creator prompt assembly**: `build_creator_ontology_brief(domain_id)` renders the registry as the authoritative ontology section of the Creator prompt. Called at generate time so new registrations take effect without restart.

**Gate enforcement**: `validate_step_against_ontology(exercise_type, demo_data, validation, code)` → `(ok, reason)`. Called from `_is_complete`. Enforces: required `demo_data` fields present, required `validation` fields present (with `any_of:...` syntax for one-of), fill-in-blank-for-code rejected (retired 2026-04-21), system_build without any of `{gha_workflow_check, endpoint_probe, state_assertion, artifact_flag}` rejected.

**Code-writing assignment schema (2026-04-21 simplification)** — retired `fill_in_blank` for code languages; every code assignment emits only:
- `code` — starter scaffold (20-60 lines, production-flavored, 2-4 TODOs)
- `exercise_type` — one of: `code_exercise / code_review / code_read / system_build / mentored_iteration / property_test_grader`
- `demo_data.language` — `python / sql / yaml / dockerfile / shell / go / ts / ...`
- For `code_review` only: `demo_data.bugs[]` with `{line, line_content, description}`
- For `code_exercise`: `validation.hidden_tests` (pytest/jest source) or `validation.properties` (Hypothesis). `must_contain` permitted only as low-weight supplementary signal.
- **Solution/starter invariant** (from the design-doc LangGraph pipeline): Creator also emits a hidden `solution` file; before publish, generation validates that solution-passes + starter-fails. No exercise ships that's unsolvable OR already solved.

**Target architecture references** (from the design docs in `~/Downloads/`, loaded into the ontology as north-star):
- `SYSTEM_ARCHITECTURE.md` — LangGraph pipeline (`enrich → classify → generate → critique ↔ refine → validate_syntax → validate_full ↔ fix → score → package`), Docker-based test execution, solution-passes + starter-fails invariant.
- `IMPLEMENTATION_GUIDE.md` — FastAPI + LangGraph + Pydantic state models, self-healing validation loop (up to 5 fix attempts per category: solution / tests / problem).
- `FRONTEND_GUIDE.md` — React + Socket.IO + shadcn/ui + Monaco, live-generation-timeline with per-LLM-call activity feed, step-by-step progress.
- `README.md` — index.

The registry + prompt assembler + gate form the spine. Runtime backends (docker, GHA, vscode, terminal) land as separate handler registrations that bind into `RUNTIME_REGISTRY` at import time.

## ⚠️ `skills.sclr.ac` and `18.236.242.248` are THE SAME MACHINE (2026-04-22)

Both DNS names resolve to `ip-172-31-13-27.us-west-2.compute.internal` (confirmed by SSH to each). There is:
- ONE EC2 instance
- ONE systemd service (`skills-lab.service`)
- ONE SQLite file (`~/skills-lab-v2/skills_lab.db`)
- ONE Docker daemon
- ONE uvicorn process serving both hostnames through nginx

Implication: **any DB mutation hits both catalogs simultaneously.** Archiving, deleting, UPDATE-ing courses via SSH + Python3 affects both the 18.236.242.248 view AND the skills.sclr.ac view. There is no way to "archive on one but not the other." The section below about deploy targets still applies to CODE pushes (rsync + systemctl restart), but DB ops are indivisible across the two hostnames.

If a future archive / cleanup needs to spare the external team's content on skills.sclr.ac, partition by `archived_at` timestamp or `course_id` prefix — the hostname is NOT a boundary.

## ⚠️ Deploy targets (2026-04-21) — skills.sclr.ac is SHARED, do NOT push there by default

Two remote EC2 boxes exist behind nginx + basic auth (`impact:getshitdone`). Deploy conventions:

- **`skills.sclr.ac` (52.88.255.208)** — **SHARED WITH AN EXTERNAL TEAM.** Do NOT push experimental changes, beta builds, or mid-cycle fixes here by default. Only deploy to this box when the user explicitly greenlights it (e.g. "push to both" / "deploy on sclr too"). Treat it as production-adjacent.
- **`18.236.242.248`** — **default deploy target for all beta-cycle work.** Push freely. All `/loop` audits, stress tests, new exercise types, and Creator-prompt iterations go here first and stay here until the user OK's promotion.

When in doubt: deploy to `18.236.242.248` only. If a change has been validated there, pause and ASK before touching `skills.sclr.ac`.

## 🏗️ F24 + F26 (2026-04-21) — Capstone scaffold primitives + GHA eval harness

**Problem:** Heavy-infra capstones (Docker / K8s / deploy / "read a 50K-line codebase") were unsolvable as-shipped because the Creator referenced artifacts (codebases to walk, services to deploy, workflows to run) without giving the learner any way to obtain those artifacts OR any way to prove their solution worked. F26 fixes the INPUT side (scaffolding); F24 fixes the GRADING side (external CI attestation). They ship together.

### F26 — `demo_data.starter_repo` / `demo_data.starter_files` / `demo_data.repo_path_var`

Creator emits one or both of these when a `code_exercise` / `system_build` step references external filesystem state:

```json
{
  "demo_data": {
    "starter_repo": {
      "url": "https://github.com/skills-lab-demos/flowsync-50k",
      "ref": "main",
      "description": "50K-line FastAPI + Redis codebase with a real idle-timeout bug"
    },
    "starter_files": [
      {"path": "app/auth/session_manager.py", "contents": "…"},
      {"path": "app/db/queries.py", "contents": "…"}
    ],
    "repo_path_var": "repo_path"
  }
}
```

- `starter_repo` → clickable "Clone starter →" banner above the editor. MUST be a public GitHub URL. Purely informational to the learner (they clone locally).
- `starter_files` → backend pre-materializes these into a temp dir at `/api/execute` time and injects a Python variable (named by `repo_path_var`, default `repo_path`) into the sandbox globals pointing at the dir. The learner's code then does `os.walk(repo_path)` against a real, non-empty directory.
- When the emitted code calls `os.walk` / `Path().glob` / `open(x)` / `subprocess` against any path outside `"."`, the Creator MUST emit one of these primitives. `_is_complete` rejects code_exercise steps that reference external FS state but emit neither `starter_repo` nor `starter_files`.

### F24 — `validation.gha_workflow_check` for Docker / heavy-infra capstones

For exercises where the grader can't run the learner's solution server-side (Docker build, K8s apply, multi-service stack, long-running pipeline), the Creator emits:

```json
{
  "validation": {
    "gha_workflow_check": {
      "repo_template": "https://github.com/skills-lab-demos/docker-capstone-<auto>",
      "workflow_file": "lab-grade.yml",
      "expected_conclusion": "success",
      "grading_job": "grade",
      "instructions_md": "1. Fork repo  2. Push your solution to a branch  3. GHA runs lab-grade.yml  4. Paste the run URL below"
    }
  }
}
```

- Learner pastes the **GitHub Actions run URL** (e.g. `https://github.com/<their-fork>/actions/runs/12345678`) into a text box.
- Backend parses owner/repo/run_id from the URL, calls `GET /repos/{owner}/{repo}/actions/runs/{run_id}` via the public GitHub API (unauthenticated works for public repos up to 60 req/hr; accept `GITHUB_TOKEN` env var for higher limits), asserts `run.conclusion == expected_conclusion`.
- Score: 1.0 if conclusion matches and the target job (by `grading_job` name) succeeded; 0.0 otherwise with a feedback hint.
- SSRF-safe: only `https://github.com/…` URLs accepted; run_id parsed as integer.
- Required for: any `code_exercise` / `system_build` whose `demo_data.language` is `dockerfile` OR whose content describes K8s apply, multi-container deploy, or terraform apply.

**Creator-prompt rule:** for `dockerfile` / `docker-compose` / Helm / K8s / `terraform apply` capstones, `gha_workflow_check` is MANDATORY. For plain Python/SQL/YAML exercises, `must_contain` / `endpoint_check` are still valid (`gha_workflow_check` is the extra tool, not a replacement).

## Tech Stack
- **Backend**: Python 3.14, FastAPI, async SQLAlchemy (SQLite + aiosqlite)
- **Frontend**: Single-file HTML (`frontend/index.html`), dark theme, no build step
- **Database**: 6 tables — Course, Module, Step, UserProgress, Certificate, ReviewSchedule
- **Code Execution**: Sandboxed `exec()` with mock modules, 10s timeout, restricted builtins
- **Server**: uvicorn on port 8001, launch config in `.claude/launch.json`
- **LLM Budget**: $250 USD cap on Anthropic API (bumped from $100 on 2026-04-21), auto-mock fallback. Current spend: see `/api/admin/budget`

## Project Structure
```
skills-lab-v2/
├── backend/
│   ├── main.py              # FastAPI app, routes, sandbox, validation
│   ├── database.py           # SQLAlchemy models & async session
│   ├── schemas.py            # Pydantic v2 request/response models
│   └── courses/              # Course content as Python dicts
│       ├── technical_*.py    # Technical skill courses
│       ├── case_study_*.py   # Case study courses
│       └── compliance_*.py   # Compliance/knowledge courses
├── frontend/
│   └── index.html            # Complete SPA (3300+ lines)
├── .claude/
│   └── launch.json           # Preview server config
└── CLAUDE.md                 # This file
```

## Reference Project
- `../ai-skills-lab` — Earlier version with Clicky AI assistant, Agentic Coding Demo. Use for:
  - Clicky system prompt patterns (teaching rules, never-give-answers behavior)
  - Assignment quality baseline (improve upon it)
  - Exercise hint patterns
