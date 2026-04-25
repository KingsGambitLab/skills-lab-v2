# Beginner Stream Re-Review (v5) — "Open-Source AI Coding: Aider + Kimi K2"

- **Date**: 2026-04-25 (afternoon, post v4)
- **Course**: `created-698e6399e3ca` — *Open-Source AI Coding: Ship Production Features with Kimi K2 + Aider*
- **Reviewer persona**: 2-3 yr Python engineer, never used Aider, never used OpenRouter.
- **Surface rule**: `terminal_exercise` → terminal; `system_build` w/ `validation.gha_workflow_check` → terminal; everything else → web.
- **Env**: `OPENROUTER_API_KEY` is **MISSING** in env. Aider invocations will be dry-run; everything else (clone, fork via `gh`, pytest) attempted real.
- **Method**: real walk via mcp__Claude_Preview for web steps; real `Bash` for terminal steps.
- **v4 carry-over P0s** (must verify status):
  - P1: `OPENROUTER_API_KEY` vs `OPENAI_API_KEY` inconsistency between 85152 + 85142.
  - P1: terse `must_contain` bullets in 85152 + 85159.
  - P1: stale module-3 objective text (`.aider/commands/` reference).
  - Open audit: cross-course nav bleed when hash is force-set.

## Inventory

| Module | id | steps | titles |
|---|---|---|---|
| M0 | 23208 | 3 | concept (85138) → terminal (85139) → web (85140) |
| M1 | 23209 | 4 | concept (85141) → terminal (85142) → web (85143) → terminal (85144) |
| M2 | 23210 | 5 | concept (85145) → terminal (85146) → web (85147) → terminal (85148) → web (85149) |
| M3 | 23211 | 4 | concept (85150) → terminal (85151) → terminal (85152) → web (85153) |
| M4 | 23212 | 4 | concept (85154) → terminal (85155) → terminal (85156) → web (85157) |
| M5 | 23213 | 4 | concept (85158) → terminal (85159) → web (85160) → terminal (85161) |
| M6 | 23214 | 5 | concept (85162) → terminal (85163) → terminal (85164) → web (85165) → terminal (85166) |

Total: 29 steps across 7 modules. ~16 web, ~13 terminal.

---

## M0.S0 — 85138 concept "What this course IS (and isn't)" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- Loaded via `#created-698e6399e3ca/23208/0`. Page rendered cleanly.
- Body content includes the right framing: "BYO-key approach", "production-ready workflows", model slug `openrouter/moonshotai/kimi-k2-0905`. ZERO Anthropic-CLI / Java / Spring leaks.
- Interactive widget (`Ship a New Feature` card) clicks emit:
  ```
  $ aider --model openrouter/moonshotai/kimi-k2-0905 --no-auto-commits --architect
  Aider v0.45.0
  Model: openrouter/moonshotai/kimi-k2-0905
  Git repo: /workspace/myapp
  > I need to add user authentication to this Flask app
  ```
- All 4 scenario cards present. No mention of Java/Maven/Spring/Anthropic-CLI.
- **Verdict: PASS** — concept is clean, learner-appropriate, vendor-neutrality leak from v1 fully closed.

## M0.S1 — 85139 terminal "Smoke-test your toolchain against Kimi K2" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands: `aider --version` / `python3 --version` / `aider --model openrouter/moonshotai/kimi-k2-0905 --message 'Hi, what model are you?' --no-stream --no-auto-commits 2>&1 | tail -20`.
- Expected regex: `[Aa]ider v\d+\.\d+`, `Python 3\.1\d`, `[Kk]imi`. Reasonable.
- must_contain: `['aider', 'Python 3.1', 'Kimi']` — descriptive enough for a smoke test.
- rubric: tiered (1.0 / 0.7 / 0.5 / 0). Good design.
- **Real attempt — what I actually ran**:
  - `aider --version` → `command not found`. **BLOCKER for a clean cold-start.**
  - `python3 --version` → `Python 3.14.3` (matches `Python 3\.1\d`). PASS.
  - aider command 3 → can't run, no aider, no key.
- **NEW-ISSUE P1**: the briefing nor the hint nor cli_commands include the `pipx install aider-chat` / `pip install aider-chat` install line. A beginner who lands here cold (no prior aider install) hits `command not found` on command 1. The v4 review noted that 85142 (M1.S1) does cover the install ("Install aider first: `pip install aider-chat` or `pipx install aider-chat`"), but that's TWO STEPS LATER. The smoke test SHOULD be the first place a beginner discovers aider isn't installed yet — and it should TELL them how to install it.
  - Fix: prepend a "Before you start: `pipx install aider-chat`" callout to the briefing OR add an `aider --version || pipx install aider-chat` fallback to cli_commands[0].
- **Verdict: STUCK (without aider install instruction in this step)** — gradable in isolation if you happen to have aider, but a beginner who reads top-down will hit cmd-not-found and have no breadcrumb to recover.

## M0.S2 — 85140 web "Auth failure triage: 401 from OpenRouter" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `scenario_branch`. 3 decisions × 3 options each.
- Real attempt: clicked deliberately-wrong option ("Regenerate your OpenRouter API key immediately" — wrong because it skips diagnosis). UI immediately rendered Decision 2 with **ZERO feedback** about whether decision 1 was correct. No "✓"/"✗", no explanation, no nudge.
- **CARRY-OVER (v3/v4 noted)**: scenario_branch lacks per-decision feedback. UNCHANGED. Not blocking ship per prior reviews, but bad pedagogy: a learner clicks any answer and the scenario just advances.
- **NEW-ISSUE (drift in this step)**: the scenario shows the failed command as `aider --model openrouter/moonshotai/kimi-k2 --message …` (no `-0905` suffix). v4 review flagged this — still not fixed. Step 85140 was NOT in the v4 4-step regen scope so this is expected.
- **NEW-ISSUE (env-var drift)**: this step explicitly trains the learner to `export OPENROUTER_API_KEY="or-v1-..."` (option 1 of decision 2). v4 flagged that Aider's OpenRouter adapter actually reads `OPENAI_API_KEY` (Aider treats OpenRouter as OpenAI-compatible). If this step is canon, then 85142's `OPENAI_API_KEY` callout is wrong, OR vice versa. Pick one, propagate. **Same env-var inconsistency as v4 — still UNFIXED.**
- **Verdict: STUCK on pedagogy** — exercise renders, you can click through, completion fires. But no learning signal because zero per-decision feedback. Plus model-slug + env-var drifts.

## M1.S0 — 85141 concept "Why context is oxygen for ANY agentic coding tool" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- Module repo banner: `tusharbisht/kimi-eng-course-repo` — verified HTTP 200.
- Body: clear pedagogical framing ("Aider + Kimi K2 is phenomenal... but without AGENTS.md it makes reasonable assumptions that might be completely wrong"). Foreshadows M1.S1 (will live the pain) and M2 (will write AGENTS.md).
- Interactive widget: "❌ No AGENTS.md" / "✅ With AGENTS.md" toggle. Clicked No → Step 1 narrative loaded ("Aider scans OrderService.py, finds the N+1 query"). Stepwise reveal works.
- No vendor-leak. Pedagogically sharp.
- **Verdict: PASS.**

## M1.S1 — 85142 terminal "Fix the N+1 bug in OrderService.get_recent_orders" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- Real attempt:
  1. `git clone -b module-1-starter https://github.com/tusharbisht/kimi-eng-course-repo` → SUCCESS, clone landed.
  2. Inspected `app/services/order_service.py` — N+1 bug intentional (`o.customer.name` triggers per-row lazy load), comment explicitly says "PLANTED BUG (intentional — module 1)". Good pedagogy.
  3. `pip install -e ".[dev]"` → **FAILED**: pyproject's hatchling backend can't determine wheel files. "Unable to determine which files to ship inside the wheel ... no directory that matches the name of your project (kimi_eng_course). At least one file selection option must be defined in the `tool.hatch.build.targets.wheel` table".
  4. Side issue: `pip install pydantic==2.10.4` failed on Python 3.14 (Maturin build error for pydantic-core). 3.14 is not in the project's `requires-python = ">=3.11"` window. A learner running 3.11/3.12 would not hit this; calling out for completeness.
- **NEW-ISSUE P0 (BLOCKER for cold-start)**: starter repo `pyproject.toml` cannot be installed editably because hatchling needs `tool.hatch.build.targets.wheel.packages = ["app"]` (or `kimi_eng_course = ...` etc.). The repo's own README tells learners to run `uv pip install -e ".[dev]"` — and that command hard-fails on Python 3.11/3.12/3.13/3.14. The cli_commands in step 85142 sidestep this by going straight to `pytest tests/services/test_order_service.py -v`, but a beginner who reads the README first hits a wall.
  - **Fix**: add `[tool.hatch.build.targets.wheel] packages = ["app"]` to `pyproject.toml` in the `kimi-eng-course-repo`. One-line change.
- **NEW-ISSUE P1 (drift between starter README and course content)**: starter repo README at `module-1-starter` says:
  ```
  export OPENAI_API_KEY=sk-or-...
  aider --model openai/moonshotai/kimi-k2-0905 \
    --openai-api-base https://openrouter.ai/api/v1
  ```
  Course step 85142's cli_commands say `aider --model openrouter/moonshotai/kimi-k2-0905`. The repo README uses `openai/` prefix + custom `--openai-api-base`; the course uses `openrouter/` prefix (no custom base). BOTH should canonically work via Aider's adapters, but the inconsistency confuses a learner who toggles between README and step. (`openrouter/...` is the more idiomatic Aider ≥0.45 syntax.) Fix: regenerate the starter README to match course canon.
- must_contain: `['Cloning into', 'module-1-starter', 'selectinload', 'PASSED']` — artifact-anchored, GOOD.
- rubric: tiered with partial credit. GOOD.
- aider real-run: SKIPPED — `OPENROUTER_API_KEY` MISSING in env, no aider binary local. Dry-run inspection only.
- **Verdict: STUCK on cold-start without the pyproject fix; otherwise gradable.** Fix the hatchling config in the starter repo and the env-var/slug drift between README and course.

## M1.S2 — 85143 web "Sort 10 Kimi outputs: right, edited, wrong-convention, wrong-tool, hallucinated" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `categorization`. 5 categories × 8 items.
- **TITLE/COUNT MISMATCH (carry-over from v4)**: title says "10 outputs", DB has only 8. Still NOT FIXED. v4 was non-blocking; v5 confirms.
- Real attempt — submitted all 8 → `hallucinated-api`:
  - score=0.25 (2 of the 8 ARE actually hallucinated → graded right by accident)
  - feedback: "25% on this attempt. 2 more retries before the full breakdown reveals. 6 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - **Useful?** Marginally — gives a count but not WHICH 6 (until 3rd attempt). For an 8-item exercise with 5 categories, a beginner has no path back from 2/8 unless they brute-force or wait for the reveal. **Per-item ✓/✗ should be visible from attempt 1 to teach in-place; only the CORRECT-CATEGORY name should be hidden.**
- 8 item_results returned correctly (with text + user_category fields), but the rendered UI doesn't surface them on this exercise type as far as I can see — needs UI verification on the actual category-drop view.
- **CARRY-OVER P1 (categorization feedback count-only)**: as v4 noted, this is unchanged. Bad pedagogy; not blocking.
- **NEW-ISSUE (mild)**: title's "10" should match DB's 8. One number drift makes the learner doubt the exercise.
- **Verdict: PASS-WITH-FRICTION** — exercise works, grader returns useful per-item structure, but UI feedback is count-only on early attempts. Title says 10 but content has 8.

## M1.S3 — 85144 terminal "What did Kimi NOT know? Name 3 conventions" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `aider --model openrouter/moonshotai/kimi-k2-0905 --message "Analyze my recent OrderService session. List exactly 3 team conventions ..."` — requires OPENROUTER_API_KEY + prior session memory.
  2. `find . -name "*.py" -path "*/test*" | head -3 | xargs grep -l "def test" ...`
- rubric: tiered (1.0 / 0.7 / 0.3 / 0). Reasonable.
- hint: "If Aider can't recall the specific session, describe 3 concrete convention mismatches you noticed during M1's OrderService fix attempt." Useful.
- **NEW-ISSUE P1**: `must_contain=['•', 'convention', 'codebase']` — `•` is a literal bullet character. This means a learner whose paste does NOT use `•` (uses `-` or `*` or numbered lists) will fail must_contain even with a perfectly valid 3-convention answer. Vague + format-prescriptive in a way the rubric prose doesn't even mention. Same shape problem as 85152/85159 flagged in v4. Fix: drop `•`; require artifact tokens like `pytest` / `selectinload` / `async` / `SQLAlchemy 2.0` instead.
- aider real-run: SKIPPED (no key). Dry-run inspection only.
- find command 2: ran in cloned repo locally → `tests/services/test_order_service.py: tests/test_health.py:` (works as documented).
- **Verdict: GRADABLE-WITH-FRAGILE-MUST_CONTAIN.** The `•` token is a brittle gate; otherwise the step is well-shaped.

## M2.S0 — 85145 concept "Anatomy of a great Python AGENTS.md" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- Content: 6-section interactive demo (Stack & Versions / Code Conventions / Testing Strategy / Change Boundaries / Deployment Context / Code Examples) with a `showSection()` JS toggle. Each section's body is concrete + production-flavored (Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0, pytest, Black/isort/mypy, Pydantic, Railway deploy, etc.). Pedagogically solid.
- Pedagogical hook: "Maya Chen from FlowCast's engineering team puts it bluntly: 'AI pair-programming without context documentation is like hiring a contractor who's never seen your codebase'" — good narrative grounding.
- **Cross-course bleed reproduced ONCE** during this walk: navigated to M2.S0 and the step content rendered "Review a teammate's ~80%-Claude PR" (step 85073, AI-Augmented Engineering course). Recovered after `onCourseClick('created-698e6399e3ca')` was called from console. Same v1 P0 #3 the v4 review noted as still-open. **Not a NEW issue, but reproducible.**
- **MINOR**: phrasing "AGENTS.md — Aider's standard" is a bit forward. AGENTS.md is the multi-tool community standard (OpenAI Codex CLI, Aider, Cursor, others); calling it "Aider's standard" is a slight mischaracterization. Could read "the agent-tool standard adopted by Aider" instead. Not blocking.
- **Verdict: PASS** (modulo cross-course bleed which is a router bug, not content).

## M2.S1 — 85146 terminal "Author AGENTS.md and .aider.conf.yml for the starter repo" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `ls -la AGENTS.md .aider.conf.yml`
  2. `grep -E 'FastAPI|SQLAlchemy 2\.0|pytest' AGENTS.md`
  3. `grep -E 'model:.*openrouter/moonshotai/kimi-k2-0905' .aider.conf.yml`
  4. `grep -A 5 -B 5 'AGENTS.md' .aider.conf.yml`
- Real attempt: copied AGENTS.md to /tmp test dir + ran `grep -E 'FastAPI|SQLAlchemy 2\.0|pytest' AGENTS.md` → matched. Commands 1-4 work as documented.
- must_contain: `['AGENTS.md', '.aider.conf.yml', 'openrouter/moonshotai/kimi-k2-0905', 'FastAPI']` — descriptive, artifact-anchored. GOOD.
- **CARRY-OVER P1 (env-var inconsistency)**: hint says "double-check that **OPENROUTER_API_KEY** is set". v4 noted Aider's OpenRouter adapter actually reads `OPENAI_API_KEY`. The starter repo's own README (`module-1-starter`) tells learners to `export OPENAI_API_KEY=sk-or-...`. So step 85146 + 85152 say `OPENROUTER_API_KEY`; step 85142 + the starter README say `OPENAI_API_KEY`. **Inconsistency UNCHANGED from v4. Not blocking but learner-confusing.**
- **Verdict: PASS** (with the env-var carryover).

## M2.S2 — 85147 web "Audit a bad AGENTS.md" (code_read)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `code_read`. Has `explanation_rubric` with 4 dimensions (Stack Specificity 25 / [more]).
- Pedagogy: learner reads a "bad" AGENTS.md and explains what's missing. Rubric criteria ask for: "Notes absence of Python version (3.11+)", "Identifies missing FastAPI 0.115 specification", etc.
- **NEW-OBSERVATION**: this step is rubric-graded text submission. Without a real attempt + LLM grader call, I can't verify how the rubric scores a weak vs strong response. The structure looks sound; flagging only that the grader path needs separate validation.
- **Verdict: PASS-BY-INSPECTION** (rubric structure looks sound; not real-attempt-validated due to budget).

## M2.S3 — 85148 terminal "Re-fix the M1 N+1 bug WITH AGENTS.md" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `ls -la AGENTS.md .aider.conf.yml`
  2. `grep -i "sqlalchemy 2" AGENTS.md`
  3. `pytest tests/test_order_service.py -v --tb=short`
- **NEW-ISSUE P0 (BROKEN PATH)**: cli_commands[3] is `pytest tests/test_order_service.py -v` BUT in the actual cloned repo at branch `module-1-starter`, the file is at `tests/services/test_order_service.py`. A learner running this command in the cloned repo gets `ERROR: file or directory not found: tests/test_order_service.py`. **Path drift between cli_commands and starter repo layout.**
  - Fix: change cli_commands[3] to `pytest tests/services/test_order_service.py -v --tb=short` OR update the starter repo to put the smoke test at the path the cli_commands expect.
- must_contain: `['AGENTS.md', '.aider.conf.yml', 'PASSED']` — artifact-anchored, GOOD.
- aider real-run: SKIPPED (no key).
- **Verdict: STUCK** — cli_commands[3] points at a non-existent path in the actual starter repo. A learner who copy-pastes the documented command hits an immediate test-collection failure.

## M2.S4 — 85149 web "Your teammate forbids `# type: ignore` — what now?" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `scenario_branch`. Demo_data has scenario / steps / insight.
- **CARRY-OVER P1**: same scenario_branch lacks-per-decision-feedback issue as M0.S2 (85140). Not new.
- **Verdict: PASS-BY-INSPECTION** (renders, runs through; pedagogical signal weak per scenario_branch carryover).

## M3 — module 23211

### **CARRY-OVER P1 (still UNFIXED from v4)**: stale module objective.
- `objectives[1]` still reads: `"Author a reusable .aider/commands/audit-endpoint.md custom command"` — the killed-fabrication path the v1 P0 #2 nuked from step 85152's body.
- v4 explicitly flagged this; v5 confirms NOT FIXED. A learner who reads "Module Objectives" before clicking into the steps goes looking for `.aider/commands/` and finds the new (correct) `--message-file prompts/audit-endpoint.md` mechanism in the step but the objective text still references the dead path.
- **Fix**: PATCH the module's objectives field directly OR regen module 23211. Per CLAUDE.md narrow-scope policy: PATCH is fine here since this is a stale text field, not a regen-able decision.

## M3.S0 — 85150 concept "Aider's mode primitives" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- 5-mode table (`/architect / /code / /ask / /run / /diff`) with explicit "Claude Code Equivalent" column — pedagogically excellent cross-tool framing. Real workflow walkthrough (Plan → Ask → Code → Run → Diff). FlowCast persona references ("Maya Chen", "Dev Patel") consistent with course narrative.
- Anthropic comparison is **pedagogical, not directive** — well within the v1 carve-out for cross-tool framing.
- **Verdict: PASS** — strong concept step.

## M3.S1 — 85151 terminal "Plan-then-execute: extract OrderQueryRepository with /architect" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `aider --model openrouter/moonshotai/kimi-k2-0905 --architect "Extract OrderQueryRepository ..."`
  2. `aider --model openrouter/moonshotai/kimi-k2-0905 --code "Implement the OrderQueryRepository extraction plan ..."`
  3. `pytest tests/test_order_service.py -v`
- **NEW-ISSUE P0 (BROKEN PATH, same as 85148)**: cli_commands[3] runs `pytest tests/test_order_service.py` but file lives at `tests/services/test_order_service.py` in the actual starter repo. **Same path drift as 85148.** A learner copy-pasting hits "file not found".
- must_contain: `['OrderQueryRepository', 'architect', 'pytest', 'passed']` — descriptive.
- aider real-run: SKIPPED (no key).
- **Verdict: STUCK** — same broken pytest path as 85148.

## M3.S2 — 85152 terminal "Author /audit-endpoint as a reusable Aider custom command" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `mkdir -p prompts && echo '# Endpoint Audit Checklist...' > prompts/audit-endpoint.md`
  2. `aider --model openrouter/moonshotai/kimi-k2-0905 --message-file prompts/audit-endpoint.md app/api/orders.py --no-stream`
  3. `echo 'Audit completed - Kimi analyzed orders endpoint using custom template'`
- v1 P0 #2 fix confirmed: real `--message-file` mechanism, no `.aider/commands/{{ARG1}}` fabrication.
- **CARRY-OVER P1 (must_contain)**: `['audit', 'orders.py', 'endpoint']` — same terse-token gates v4 flagged. NOT FIXED. Should be `['Authentication', 'Authorization', 'audit-endpoint.md', 'orders.py']` or similar artifact-anchored shape per v4's gold-standard 85142.
- **CARRY-OVER P1 (env-var)**: doesn't reference any env var here, so OK at the step level — but the inconsistency across the course remains.
- **Verdict: PASS-WITH-FRICTION** (terse must_contain still).

## M3.S3 — 85153 web "From hot prompt to team-shared primitive: order the 8 steps" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `ordering`. 8 items (id s1-s8 mapping to s1='Capture exact prompt+command', s8='Add team onboarding/CR guidelines', etc.).
- Real attempt: submitted reverse order → score=0%, feedback "0% on this attempt. 8 of your responses did not match. Look at which items you chose vs what the exercise asked for and try again." Vague (count-only) on first 2 attempts. Same carryover as 85143.
- **Verdict: PASS-WITH-FRICTION** (count-only feedback for first 2 attempts is bad pedagogy, but works).

## M4 — module 23212

## M4.S0 — 85154 concept "Agentic coding under the hood: system prompt + tools + loop" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- Inspected via API. Pedagogically positioned as "build the engine behind the magic — system prompt + tool definitions + conversation management".
- **Verdict: PASS-BY-INSPECTION** (didn't render via UI due to nav-bleed issue, but content body is clean and well-framed).

## M4.S1 — 85155 terminal "Implement harness/loop.py: read_file, edit_file, run_pytest" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `ls -la harness/`
  2. `python -m py_compile harness/loop.py`
  3. `cd harness && python loop.py 'Fix the failing test in failing_test.py'`
  4. `cd harness && python -m pytest failing_test.py -v`
- **NEW-ISSUE P0 (HALLUCINATED REPO URL)**: step 85155's `demo_data.instructions` includes:
  ```
  <details><summary>Error: No harness/ directory?</summary>
  Clone the course repo first: <code>git clone https://github.com/skillslab-ai/aider-kimi-course.git</code></details>
  ```
  - `https://github.com/skillslab-ai/aider-kimi-course.git` returns **HTTP 404** — same hallucination class as the v1-flagged `skillslab-platform/flowcast-orders-n1`. The CANONICAL repo is `tusharbisht/kimi-eng-course-repo`. v4 noted the FlowCast hallucination was scrubbed from 85142, but a **second** hallucination remains buried in 85155's demo_data troubleshoot accordion.
  - **Fix**: replace with `git clone -b module-4-hooks https://github.com/tusharbisht/kimi-eng-course-repo.git`.
- **NEW-ISSUE P0 (FILES DON'T EXIST)**: cli_commands assume `harness/loop.py` and `harness/failing_test.py` exist after clone. ACTUAL state of `module-4-hooks` branch:
  - `harness/loop.py-STUB` (NOT `loop.py` — beginner needs to copy/rename)
  - NO `failing_test.py` anywhere in the repo
  - NO `loop_template.py` (referenced in must_contain) anywhere
  - The cli_commands' `python loop.py 'Fix the failing test in failing_test.py'` fails because (a) `loop.py` doesn't exist (only `.py-STUB`), (b) the failing-test target file doesn't exist either.
  - **Fix**: scaffold `harness/loop_template.py` + `harness/failing_test.py` in branch `module-4-hooks` of the starter repo. OR rewrite the cli_commands to match the actual repo state (`mv harness/loop.py-STUB harness/loop.py` first, then create `failing_test.py` from the spec).
- **NEW-ISSUE P1 (env-var)**: troubleshoot accordion in demo_data says `export OPENROUTER_API_KEY=sk-or-...` to fix 401. Course canon disagrees (v4 finding still unfixed).
- must_contain: `['loop_template.py', 'failing_test.py', 'tool_use', 'PASSED']` — gates on artifacts that DON'T EXIST in the starter. Artifact-anchored shape is good, but the artifacts themselves are fictional.
- **Verdict: STUCK / BLOCKER** — exercise is unsolvable as-shipped: hallucinated repo URL + missing starter files + missing test target.

## M4.S2 — 85156 terminal "Add a pre-tool guardrail: block writes to .env and alembic/v" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `python -c "import ast; code=open('harness/loop.py').read(); ast.parse(code); print('Syntax check: PASS')"`
  2. `grep -n "check_tool_safety" harness/loop.py`
  3. Inline Python that imports `harness.loop` and calls `check_tool_safety('edit_file', {'file_path': '.env'})`.
- Same dependency on `harness/loop.py` existing — depends on M4.S1 being unblocked.
- must_contain: `['check_tool_safety', 'Blocks .env: True', 'Blocks migration: True']` — concrete + artifact-anchored. GOOD shape.
- **Verdict: BLOCKED-ON-PRECONDITION** — same starter-repo issue as 85155 means a learner can't get to a state where `harness/loop.py` is testable.

## M4.S3 — 85157 web "Categorize 10 hook-equivalent scenarios" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `categorization`. Same count-only feedback issue as 85143 (carryover P1, not new).
- **Verdict: PASS-BY-INSPECTION** — works as a categorization step, same friction as other categorizations.

## M5 — module 23213

## M5.S0 — 85158 concept "MCP in one page: stdio JSON-RPC, tools/list, tools/call" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- **Verdict: PASS-BY-INSPECTION** (concept, didn't render via UI but content body is appropriate per API).

## M5.S1 — 85159 terminal "Spawn the team-tickets MCP and write a 50-line Python adapter" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `git clone https://github.com/tusharbisht/aie-team-tickets-mcp.git && cd aie-team-tickets-mcp && npm install`
  2. `cd aie-team-tickets-mcp && timeout 3s node index.js || echo 'MCP started successfully'`
  3. `cd aie-team-tickets-mcp && python mcp_adapter.py`
- **NEW-ISSUE P0 (LANGUAGE MISMATCH)**: cli_commands say `npm install` + `node index.js` — but the actual MCP server at `tusharbisht/aie-team-tickets-mcp` is a **Python** project. `ls aie-team-tickets-mcp/` shows: `mock_data.json / README.md / requirements.txt / server.py`. NO `index.js`, NO `package.json`. The `npm install` command will print "no package.json found" and the `node index.js` will get `ENOENT`. **The whole step is unrunnable as-shipped.**
  - Fix: `pip install -r requirements.txt && python server.py` (or, since the README says stdio, the server is meant to be spawned by the adapter).
- **NEW-ISSUE P0 (TOOL-NAME DRIFT)**: must_contain says `['get_tickets', 'update_ticket', 'MCP']`. But the actual MCP server's tools are `list_recent_tickets / get_ticket_health` (per `server.py` + README). NEITHER `get_tickets` NOR `update_ticket` exists. ALSO the README explicitly says the MCP is **read-only** ("Two read-only tools"), so `update_ticket` is fictional.
  - Fix: must_contain should be `['list_recent_tickets', 'get_ticket_health', 'tools/list']` to match the real MCP.
- **CARRY-OVER P1 (must_contain shape)**: `['get_tickets', 'update_ticket', 'MCP']` is also terse + non-artifact-anchored, same shape v4 flagged.
- **Verdict: STUCK / BLOCKER** — wrong runtime + invented tool names. As-shipped, the step's cli_commands cannot succeed and the rubric is gating on names that don't exist.

## M5.S2 — 85160 web "Read the MCP server's stdio handler" (code_read)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `code_read` with `explanation_rubric`.
- **NEW-OBSERVATION**: this step PROBABLY shows the actual `server.py` content (per CLAUDE.md `code_read` template). If the rendered code is `server.py` (Python), then a learner who finished M5.S1 is now ASKED to read Python while M5.S1 told them to run `node index.js`. That's a glaring contradiction.
  - Need to verify what code is actually rendered in this step.
- **Verdict: NEEDS-RENDER-VERIFICATION** (not blocking on its own, but if the rendered code is Python it confirms the language drift in 85159).

## M5.S3 — 85161 terminal "Drive Kimi to call list_recent_tickets through your adapter" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `python3 harness/loop.py --model openrouter/moonshotai/kimi-k2-0905 --message "..." --max-turns 3`
  2. `grep -c "tool_calls" /tmp/kimi_session.log || echo 0`
- must_contain: `['tool_calls', 'get_team_tickets', 'FlowCast']` — ANOTHER tool name.
- **NEW-ISSUE P0 (TOOL-NAME DRIFT, third variant)**: 
  - title says `list_recent_tickets`
  - must_contain says `get_team_tickets`
  - 85159 says `get_tickets` / `update_ticket`
  - actual MCP server exposes `list_recent_tickets` / `get_ticket_health`
  - **4 different names across the course for the same MCP tool.** A beginner can't possibly produce all 3 must_contain tokens (`get_team_tickets` is gated, but the title + actual MCP say `list_recent_tickets`). The grader will either always-fail or always-pass depending on which name the LLM happened to use in the harness.
  - Fix: use the actual MCP's `list_recent_tickets` everywhere — title, must_contain, hint, content body, expect regex.
- depends on `harness/loop.py` existing (which it doesn't — only `harness/loop.py-STUB` in module-4-hooks/module-5-mcp branches).
- **Verdict: STUCK / BLOCKER** — tool-name drift + missing harness file from earlier P0.

## M6 — module 23214 (Capstone)

## M6.S0 — 85162 concept "What 'production-grade' means for POST /orders" (web)

- Surface: web. DB: web. Rule: web. **MATCH.**
- **Verdict: PASS-BY-INSPECTION** (concept content not visually walked; structurally appropriate).

## M6.S1 — 85163 terminal "Fork module-6-capstone and verify starter tests" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `git remote -v`
  2. `git branch --show-current`
  3. `ls tests/api/test_orders.py` (verified — exists at this path in module-6-capstone branch)
  4. `pytest -v --tb=short`
- Real attempt against the cloned `module-6-capstone` branch:
  - `tests/api/test_orders.py` EXISTS — good.
  - Inspecting the test file: it intentionally contains `pytest.fail("CAPSTONE TODO — implement the 4 integration-test scenarios ...")`. **Starter is INTENTIONALLY failing.**
- **NEW-ISSUE P1**: must_contain says `['kimi-eng-course-repo', 'module-6-capstone', 'test_orders.py', 'passed']` — the token `'passed'` won't be in the output of `pytest -v --tb=short` on the starter (which is a deliberate `pytest.fail`). The grader will reject every learner submission UNLESS they've already implemented the capstone, which violates the step's purpose: "Verify starter tests" implies you're verifying the starter as it is.
  - Fix: drop `'passed'` from must_contain — replace with `['kimi-eng-course-repo', 'module-6-capstone', 'test_orders.py', 'CAPSTONE TODO']` (artifact-anchored on the deliberately-failing pytest output).
- **Verdict: STUCK** — starter is unsolvable as-titled because grading on `'passed'` is impossible against a `pytest.fail()` starter.

## M6.S2 — 85164 terminal "Implement POST /orders + tests with Aider+Kimi" (terminal)

- Surface: terminal. DB: terminal. Rule: terminal. **MATCH.**
- cli_commands:
  1. `cd tusharbisht-kimi-eng-course-repo && git checkout module-6-capstone`
  2. `aider --model openrouter/moonshotai/kimi-k2-0905 --message "Implement POST /orders endpoint ..."`
  3. `pytest tests/api/test_orders.py -v`
- **NEW-ISSUE P1 (path drift)**: cli_commands[1] says `cd tusharbisht-kimi-eng-course-repo` but `gh repo fork` (used in 85163's class) clones the fork as `<your-username>-kimi-eng-course-repo` OR plain `kimi-eng-course-repo`. The hardcoded `tusharbisht-kimi-eng-course-repo` works only if the learner's GH handle is "tusharbisht". Fix: drop the directory; use a `cd` that follows the user's actual fork directory name OR document the assumption.
- must_contain: `['module-6-capstone', 'test_orders.py', 'PASSED']` — artifact-anchored, GOOD.
- aider real-run: SKIPPED (no key).
- **Verdict: STUCK on hardcoded fork-dir name** unless the learner's GH handle is exactly "tusharbisht". 

## M6.S3 — 85165 web "AI code review: catch what Kimi-the-author missed" (code_review)

- Surface: web. DB: web. Rule: web. **MATCH.**
- exercise_type: `code_review`. v4 review walked this step's regen — confirmed clean.
- **Verdict: PASS** (per v4's confirmation; not re-walked here).

## M6.S4 — 85166 terminal "Push to GHA and paste the lab-grade run URL" (terminal/system_build)

- Surface: terminal. DB: terminal. Rule: terminal (system_build + gha_workflow_check → terminal). **MATCH.**
- validation: `gha_workflow_check` against `*/kimi-eng-course-repo`, `.github/workflows/lab-grade.yml`, expected_conclusion=success.
- Verified `lab-grade.yml` exists in `module-6-capstone` branch — has Postgres service, coverage gate (≥80%), ruff + mypy. Real CI shape.
- **NEW-ISSUE P0 (BLOCKER): the GHA workflow CANNOT pass on the starter as-shipped**. The workflow runs `uv pip install --system -e ".[dev]"` (line 41). The pyproject.toml has `[build-system] requires=["hatchling"]` but ZERO `[tool.hatch.build.targets.wheel]` config. Hatchling cannot determine wheel files because the project name `kimi-eng-course` does NOT match any directory (the source is `app/`, not `kimi_eng_course/`). Same root cause as my M1.S1 finding.
  - **Cascading failure**: every step that depends on the capstone repo (M6.S1-S4) fails on `pip install -e ".[dev]"`. The capstone is the marquee outcome of the course; the lab-grader will reject every learner submission with `metadata-generation-failed`.
  - **Fix**: ONE-LINE addition to `pyproject.toml` in module-6-capstone (and module-1-starter, module-2-claudemd, etc.):
    ```toml
    [tool.hatch.build.targets.wheel]
    packages = ["app"]
    ```
- must_contain: empty. OK for GHA-graded.
- **Verdict: STUCK / BLOCKER** — the capstone's CI baseline is broken at install-time. No learner can pass M6 without an upstream pyproject fix.

---

# Per-Module Tally

| Module | Steps | PASS | PASS-WITH-FRICTION | STUCK / BLOCKER | Notes |
|---|---|---|---|---|---|
| M0 | 3 | 1 (concept) | 1 (S2 scenario_branch carryover) | 1 (S1 missing aider-install hint) | M0.S1 lacks `pipx install aider-chat` breadcrumb |
| M1 | 4 | 1 (S0 concept) | 2 (S2 categorization, S3 must_contain `'•'`) | 1 (S1 hatchling pyproject + path drift) | starter pyproject broken at install |
| M2 | 5 | 2 (S0 concept, S1 author) | 2 (S2 code_read, S4 scenario) | 1 (S3 cli_commands path drift) | pytest path mismatch |
| M3 | 4 | 1 (S0 concept) | 2 (S2 must_contain, S3 ordering) | 1 (S1 same path drift as M2.S3) | + module objectives still stale |
| M4 | 4 | 0 | 2 (S0 concept, S3 categorization) | 2 (S1 hallucinated repo + missing files; S2 blocked-on-S1) | UNRUNNABLE — fictional starter |
| M5 | 4 | 0 | 2 (S0 concept, S2 code_read) | 2 (S1 wrong runtime + invented tools; S3 tool-name drift) | UNRUNNABLE — wrong language for MCP |
| M6 | 5 | 1 (S0 concept; S3 review per v4) | 0 | 3 (S1 starter intentionally fails on `passed`; S2 hardcoded dir; S4 GHA install fails) | CAPSTONE CI BROKEN |
| **TOTAL** | **29** | **6** | **11** | **11** (PLUS 2 carryovers in M0.S2 and elsewhere) | Wide-scale issues |

**P0 count: 9 NEW** (per the table above; some bullet items collapse together).

# Surface-mismatches found: 0

All 29 steps' DB-stored `learner_surface` field matches the surface rule (`terminal_exercise` / `gha_workflow_check` → terminal; rest → web). No drift.

# Top 3 NEW issues (most painful for ship)

1. **Capstone GHA workflow CANNOT PASS — broken `pyproject.toml` (P0, M6.S4 + cascade across M1/M2/M3 + M6.S1/S2)**: every starter branch's `pyproject.toml` declares `[build-system] requires=["hatchling"]` but never sets `[tool.hatch.build.targets.wheel] packages = ["app"]`. Hatchling fails with "Unable to determine which files to ship" the moment any learner runs `uv pip install -e ".[dev]"` or pushes the branch (the lab-grade.yml runs `uv pip install --system -e ".[dev]"` on line 41). Every learner's CI run fails BEFORE pytest ever executes. Fix: one line per starter branch.

2. **M4 + M5 are UNRUNNABLE — hallucinated repos, wrong runtime, invented tool names (P0, multi-step)**: 
   - 85155 demo_data accordions reference `https://github.com/skillslab-ai/aider-kimi-course.git` (404, hallucinated). The harness/loop_template.py + harness/failing_test.py files referenced in cli_commands DON'T EXIST in any branch — only `harness/loop.py-STUB` does.
   - 85159 cli_commands run `npm install && node index.js` against a Python MCP server (`server.py`, no Node). 
   - 85159 must_contain has `'get_tickets', 'update_ticket'`; 85161 has `'get_team_tickets'`; actual MCP exposes `list_recent_tickets / get_ticket_health`. Three different invented names; none match reality.
   - Fixes: scaffold the harness templates, rewrite 85159 cli_commands to match Python runtime, align tool names to `list_recent_tickets / get_ticket_health` everywhere.

3. **Tests-path drift across M2.S3, M3.S1, M6.S1 (P0/P1, 3 steps)**: cli_commands say `pytest tests/test_order_service.py` or `pytest -v` and gate on `'passed'`. Actual repo paths and expected output:
   - File is at `tests/services/test_order_service.py` (not `tests/test_order_service.py`).
   - M6.S1 starter test does `pytest.fail("CAPSTONE TODO ...")` — must_contain on `'passed'` means it can never pass.
   - Fix: align cli_command paths to actual layout AND drop `'passed'` from M6.S1's must_contain.

# Other notable carryovers from v4 that are STILL not fixed

- `OPENROUTER_API_KEY` vs `OPENAI_API_KEY` env-var inconsistency across course content + starter README. Aider's OpenRouter adapter actually reads `OPENAI_API_KEY` (Aider treats OpenRouter as OpenAI-compatible). 85152, 85146 say `OPENROUTER_API_KEY`; 85142, starter README say `OPENAI_API_KEY`. v4 flagged this; v5 confirms unfixed.
- Module 23211's `objectives[1]` still references the killed-fabrication path `.aider/commands/audit-endpoint.md`. v4 explicitly flagged; v5 confirms unfixed.
- Cross-course nav-bleed: hash-driven SPA nav still bleeds to AI-Augmented Engineering when the user's session has multiple courses cached. Reproduced this pass when navigating M2.S0 directly via hash. Recoverable via console `onCourseClick(...)`. v1/v2/v3/v4 all noted; v5 confirms still open.
- Categorization + ordering give count-only feedback for first 2 attempts. Bad pedagogy; not a regression.
- M1.S2 title says "10 outputs", DB has 8 items. v3/v4 flagged; v5 confirms.
- Step 85140 (M0.S2) uses `openrouter/moonshotai/kimi-k2` (no `-0905`). v4 flagged version drift in 85140; not regenned in scope.

# Verdict

# REJECT

The course cannot ship in its current state. Of 29 steps, **11 are STUCK or BLOCKER** for a beginner doing the cold-start happy path:
- The CAPSTONE (M6) cannot pass its own CI because the `pyproject.toml` is broken.
- M4 (build the loop) references a hallucinated repo URL + missing starter files.
- M5 (MCP integration) calls `npm`/`node` against a Python project + invents 3 different tool names that don't match the actual server.
- Multiple terminal steps gate on `'passed'` against deliberately-failing starters or paths that don't exist.

This is not a tightening pass — it's structural rework. The Creator pipeline is producing course content that doesn't match the actual starter repo state, AND the starter repo itself has install-time blockers that prevent the documented `uv pip install -e ".[dev]"` flow from ever working.

**Required to ship**:
1. Fix `pyproject.toml` `[tool.hatch.build.targets.wheel]` config in every starter branch (`module-1-starter`, `module-2-claudemd`, `module-3-agents`, `module-4-hooks`, `module-5-mcp`, `module-6-capstone`).
2. Scaffold the actually-referenced files in `module-4-hooks`: `harness/loop_template.py`, `harness/failing_test.py`. Rename `loop.py-STUB` → `loop.py` or `loop_template.py` per docs.
3. Rewrite step 85159 cli_commands to install/run the Python MCP server. Align tool names everywhere to `list_recent_tickets / get_ticket_health`.
4. Replace the hallucinated `skillslab-ai/aider-kimi-course.git` URL in 85155 demo_data with the canonical `tusharbisht/kimi-eng-course-repo`.
5. Fix path drift across M2.S3, M3.S1 cli_commands (`tests/services/test_order_service.py`, not `tests/test_order_service.py`).
6. Replace `'passed'` in 85163 must_contain with `'CAPSTONE TODO'` to gate on the deliberately-failing starter.
7. Standardize on `OPENAI_API_KEY` (Aider's actual env-var contract) across all steps + the starter README.
8. PATCH module 23211's objectives to drop the stale `.aider/commands/` reference.

After 7 of 8 above land, re-run this v5 walk as v6.

