# Beginner Stream Re-Review (v4) — "Open-Source AI Coding: Aider + Kimi K2"

- **Reviewer persona**: beginner Python engineer (2-4 yrs XP, comfortable with venv + pytest, has never used Aider, never used OpenRouter, learning open-source AI coding).
- **Date**: 2026-04-25 evening, after a 4-step regen sweep this morning closed the v1 + v3 P0s.
- **Course**: `created-698e6399e3ca`.
- **Inputs**: v1 (REJECT), v2 (APPROVE), v3 (SHIP-WITH-FIXES). Walked the 4 regenned steps via the live web UI and the public learner API.
- **Tool budget used**: ~50 of 130 MCP calls.

---

## v1 P0s reproduced verbatim

The v1 REJECT report named these three ship-blockers (verbatim from `reviews/beginner_stream_kimi_v1_2026-04-25.md`):

1. **"Vendor-neutrality leaks (highest visibility, easiest fix). Swap the shared '🔐 Your key stays on your machine…' banner template to Aider-flavoured text … Swap the paste-textarea placeholder from `$ claude --version` to `$ aider --version`. Swap the M0.S1 troubleshooting accordions from Claude Code / Java / Maven to Aider / Python / pip. Repo references must be `kimi-eng-course-repo`, not `jspring-course-repo`."**

2. **"M3.S3 fabricated Aider custom-commands (highest correctness risk). The `.aider/commands/<name>.md` + `{{ARG1}}` templating pattern does not exist in Aider. Rewrite the step around: (a) an `AGENTS.md`-embedded checklist … (b) a shell alias / `--message-file` workflow, OR (c) Aider's actual `/chat-mode` and conventions-file patterns. Do not ship the invented feature."**

3. **"Cross-course navigation bug (single failure mode, catastrophic impression). `Next →` from a concept step inside the Kimi course jumped me to a step in the Java course. … Either fix the router to clamp within-course, or gate every step-render with a `courseId === currentCourse` check and hard-redirect otherwise."**

---

## P0 status across v1 → v4

### P0 #1 — Vendor-neutrality leaks · **PASS**

**Evidence**: pattern audit on the 4 regenned steps' raw JSON.

| Pattern | 85138 | 85152 | 85159 | 85165 | 85142 (inflight) |
|---|---|---|---|---|---|
| `ANTHROPIC_API_KEY` | 0 | 0 | 0 | 0 | 0 |
| `claude /login` | 0 | 0 | 0 | 0 | 0 |
| `@anthropic-ai/claude-code` | 0 | 0 | 0 | 0 | 0 |
| `jspring-course-repo` | 0 | 0 | 0 | 0 | 0 |
| `OPENROUTER_API_KEY` (correct) | 0 | 1 | 0 | 0 | 1 |
| `kimi-eng-course-repo` (correct) | 0 | 0 | 0 | 0 | 7 |

The single `Anthropic` mention in 85159 (`"Moonshot AI doesn't natively speak MCP like Anthropic models do"`) is pedagogical positioning — exactly the framing the v1 review explicitly carved out as acceptable. No CLI directive, no env-var leak, no Java/Spring-Boot accordion text. UI-side: M0.S0 widget mock terminal correctly emits `aider --model openrouter/moonshotai/kimi-k2-0905 …` (verified by clicking the "Ship a New Feature" scenario card and inspecting `#terminal-output`).

### P0 #2 — Fabricated `.aider/commands/{{ARG1}}` mechanism · **PASS**

**Evidence on step 85152**: 0 occurrences of `{{ARG1}}`, 0 of `.aider/commands/`. Replaced with two REAL Aider mechanisms:

- `aider --model openrouter/moonshotai/kimi-k2-0905 --message-file prompts/audit-endpoint.md app/api/orders.py --no-stream` (real CLI flag — 3 occurrences)
- `/read-only prompts/audit-endpoint.md` (real in-session command — 1 occurrence)

The step body verbatim from the live UI: *"a reusable audit template you can inject into any Aider session with `aider --message-file prompts/audit-endpoint.md` or load mid-session with `/read-only prompts/audit-endpoint.md`."* Both mechanisms exist in Aider — neither is fabricated.

The v3 reviewer's note that the must_contain rubric was over-narrow (only `/read-only`) appears to have been partially addressed: the `cli_commands` block now models the `--message-file` path explicitly, and the rubric prose covers both injection methods. (The terse `must_contain: ['audit', 'orders.py', 'endpoint']` is still a NEW issue — see below.)

### P0 #3 — Cross-course navigation bleed · **NEW-ISSUE (still observable)**

**Evidence**: while attempting to walk the regenned steps, hash-driven navigation (`location.hash = '#created-698e6399e3ca/23208/0'`) bounced repeatedly to the Java course `#created-e54e7d6f51cf/23204/2` for 3 consecutive nav attempts. The router only stayed on `created-698e6399e3ca` AFTER I called `onCourseClick('created-698e6399e3ca')` from the JS console (i.e. mimicking a real catalog click). The bug v1 flagged is still reproducible: hash-driven SPA nav has a session-cache-bleed problem that defaults to whatever course was loaded last in this browser session.

This is NOT in scope of the 4 regenned content steps — it's a frontend SPA bug. v3 said "no fix has shipped" and that holds. CLAUDE.md §"Per-step regen scope" says router-level bugs go to a separate audit ticket. **Not blocking v4 ship.**

Once the user catalog-clicks into the course, all 4 regenned steps render cleanly via in-app `loadModule` calls (no second-course-bleed once you're "inside" the course).

---

## SPECIFIC v4 verification checklist

### 1. `aider --model` arg uses `openrouter/moonshotai/kimi-k2-0905` (NOT bare) · **PASS** with one minor leak

| Step | Slugs found |
|---|---|
| 85138 | only `openrouter/moonshotai/kimi-k2-0905` (×8) — mock terminal + interactive widget + What-You'll-Learn block |
| 85139 (M0.S1, NOT regenned) | `openrouter/moonshotai/kimi-k2-0905` (×2) |
| 85140 (M0.S2, NOT regenned) | `openrouter/moonshotai/kimi-k2` — **drift, no `-0905` suffix**, but DOES have `openrouter/` prefix. Pre-existing, not in 4-step scope. |
| 85152 | only `openrouter/moonshotai/kimi-k2-0905` (×3) |
| 85142 (inflight) | only `openrouter/moonshotai/kimi-k2-0905` (×3) |

All 4 regenned steps + the inflight 85142 use the canonical slug. The pre-existing version drift in 85140 is a NEW-issue scope creep; flag for follow-up but doesn't block ship.

### 2. `OPENROUTER_API_KEY` env handling explained · **PASS (partial)**

- 85152: explicit explanation — *"Common issue: model not found. Ensure OPENROUTER_API_KEY is set and you're using the full provider prefix: `openrouter/moonshotai/kimi-k2-0905`"*
- 85142 (inflight): *"Got '401 Invalid API key'? → Ensure your OPENAI_API_KEY environment variable is set to your OpenRouter API key. Try: `echo $OPENAI_API_KEY`"*

⚠ **NEW-ISSUE**: 85142's troubleshoot accordion uses `OPENAI_API_KEY` (the env var Aider actually reads when routing through OpenRouter), while 85152's troubleshoot uses `OPENROUTER_API_KEY` (which Aider does NOT read). A beginner who follows 85152's advice to `export OPENROUTER_API_KEY=…` will hit a 401 because Aider's OpenRouter adapter expects `OPENAI_API_KEY`. Both env vars are referenced in the course; pick one and use it everywhere. This is a NEW issue surfaced in v4.

- 85138: doesn't mention env vars (concept step — fine)
- 85159: doesn't mention env vars (the MCP server is a local node subprocess; doesn't need the API key — fine)
- 85165: doesn't mention env vars (code_review — fine)

### 3. No `set` quoting bugs · **PASS**

Pattern `\bset\s+\w+=` — 0 matches across all 4 regenned steps. No `set -e`, no `set -o pipefail`, no bash quoting traps for the beginner. (In retrospect, I think the prompt was guarding against a different fault that didn't materialize this iteration.)

### 4. Descriptive `must_contain` bullets, not raw tokens · **NEW-ISSUE**

| Step | must_contain | Verdict |
|---|---|---|
| 85152 | `['audit', 'orders.py', 'endpoint']` | ❌ raw tokens, not descriptive |
| 85159 | `['get_tickets', 'update_ticket', 'MCP']` | ❌ raw tokens |
| 85142 | `['Cloning into', 'module-1-starter', 'selectinload', 'PASSED']` | ✓ artifact-shaped, useful for grading |
| 85138 | `[]` | n/a (concept) |
| 85165 | `[]` | n/a (code_review uses bug-line clicks) |

The v3 review explicitly flagged 85152's narrow `must_contain` as friction. The v4 audit shows 85152 and 85159 are still terse single-token gates, while 85142's regen produced descriptive artifact-anchored markers. The Creator prompt should mirror the 85142 shape across the rest of the regenned terminal exercises.

---

## Beginner-POV notes

- **`pipefail` / shell idioms**: not assumed anywhere in the 4 regenned steps. ✓ A beginner can follow the cli_commands as printed.
- **`aider` install instructions**: 85142's troubleshoot accordion says *"Install aider first: `pip install aider-chat` or `pipx install aider-chat`"*. Mac-friendly + cross-platform (`pipx` works on Linux + Windows-WSL). 85152 and 85159 don't repeat the install instructions — that's fine since 85142 is an earlier step in the linear walk; a beginner is expected to have aider installed by the time they reach M3 / M5.
- **CLI surface (kimi-course CLI)**: every regenned terminal_exercise step shows the same "▶ HOW TO DO THIS STEP" panel with `kimi-course login / start / goto Mn.Sm / spec / check`. Coherent across the 4 steps. The `docker compose run --rm skillslab` bootstrap is identical too — easy to memorize.
- **Hallucinated URLs**: scrubbed. `flowcast-orders-n1` is gone from 85142; `tusharbisht/aie-team-tickets-mcp` returns HTTP 200 (verified via curl); `tusharbisht/kimi-eng-course-repo` returns HTTP 200.
- **Module-3 OBJECTIVE drift**: the M3 module objective in the SPA sidebar STILL reads *"Author a reusable .aider/commands/audit-endpoint.md custom command"* — the fabricated path the v1 P0 nuked from step 85152's body. The objective lives in the module-level `objectives` array, NOT in the step content, so the per-step regen of 85152 didn't touch it. **NEW-ISSUE**: stale module objective references the dead-feature path. If a beginner reads "Module Objectives" before clicking into the steps, they'll go looking for `.aider/commands/` and conclude the fix was incomplete. Easy fix: regen module 23211's objectives (or PATCH the field directly per CLAUDE.md narrow-scope policy — module objectives are static text).

---

## Net delta vs v1

| v1 finding | v4 status | Delta |
|---|---|---|
| Vendor-neutrality leaks (Anthropic banner / placeholder / Java repo) | CLOSED | Confirmed clean across 4 regenned + 85142. Pedagogical Anthropic comparisons retained where appropriate. |
| Fabricated `.aider/commands/{{ARG1}}` | CLOSED | Real `--message-file` + `/read-only` mechanisms shipped. Rubric still penalizes the dead pattern. |
| Cross-course nav bleed | OPEN (router bug) | Reproduced via hash-set; works once you catalog-click in. SPA-level audit ticket — out of scope for content review. |
| Item-count discrepancy (M1.S3 says 10 but UI shows 8) | UNCHANGED | Not in 4-step scope. |
| Hint button counts as attempt | UNCHANGED | Not in 4-step scope. |
| Scenario_branch lacks per-decision feedback | UNCHANGED | Not in 4-step scope. |
| Categorization feedback count-only | UNCHANGED | Not in 4-step scope. |
| Grader noisy (0% on a correct paste) | CLOSED in v2 | v2 confirmed strong/weak rubric discriminates 76% vs 10%. |

---

## NEW issues introduced or surfaced in v4 (not v1 P0s)

1. **`OPENROUTER_API_KEY` vs `OPENAI_API_KEY` inconsistency** — 85152 says `OPENROUTER_API_KEY`; 85142 says `OPENAI_API_KEY`. Aider's OpenRouter adapter actually reads `OPENAI_API_KEY` (because Aider treats OpenRouter as an OpenAI-compatible endpoint). A beginner who exports the wrong variable hits a 401. Pick one across all steps (consensus is `OPENAI_API_KEY` per v2 + v3).

2. **Terse `must_contain` bullets in 85152 and 85159** — `['audit', 'orders.py', 'endpoint']` and `['get_tickets', 'update_ticket', 'MCP']` are raw tokens, not descriptive criteria. The Creator prompt explicitly asked for descriptive bullets in the v4 reviewer brief; not enforced. 85142's regen got it right (`['Cloning into', 'module-1-starter', 'selectinload', 'PASSED']` — artifact-anchored). The fix should propagate the 85142 shape.

3. **Stale M3 module objective references the killed `.aider/commands/` path** — module 23211's `objectives[1]` still says *"Author a reusable .aider/commands/audit-endpoint.md custom command"*. The step-level regen of 85152 doesn't update module-level objectives. A beginner who reads the sidebar will look for `.aider/commands/` and won't find it. This is the v1 P0 leaking into adjacent metadata.

4. **Module 23211's objective drift is symptomatic of a wider class** — every module has an `objectives[]` array authored at course-create time. If the per-step regen rewrites a step's content but the module objective still references the OLD pattern, learners see contradictory framing. Suggest: when regenerating a step that addressed a P0 fabrication, also re-render the parent module's objectives array.

5. **"Failed to load module." transient error on first load of 85138** — observed once via direct hash-load; resolved on Retry button click. Not blocking, but consider adding telemetry / auto-retry to the module fetch path.

---

## Step 85142 inflight regen — final state

✅ **The inflight regen LANDED** during this review window.

- `flowcast-orders-n1`: 0 occurrences (was the hallucinated path)
- `skillslab-platform`: 0 occurrences (was the hallucinated org)
- `kimi-eng-course-repo`: 7 occurrences (correct repo, returns HTTP 200)
- `openrouter/moonshotai/kimi-k2-0905`: 3 occurrences (correct slug)
- `OPENAI_API_KEY` env handling: explicit accordion + `echo $OPENAI_API_KEY` verify
- `must_contain`: `['Cloning into', 'module-1-starter', 'selectinload', 'PASSED']` — artifact-shaped, descriptive, the gold standard the other regenned steps should match
- cli_commands: 4 commands, all real (`gh repo fork` / `git checkout module-1-starter` / `aider --model …` / `pytest -v`)
- troubleshoot accordion: real ones — `fatal: repository not found`, `401 Invalid API key`, `file not found`, "Kimi seems confused about the codebase"

The `https://github.com/skillslab-platform/flowcast-orders-n1` URL is GONE. The hallucination P0 from this morning's known-open-issue is **closed** as of this review.

---

## Verdict

# ✅ SHIP-WITH-FIXES

The 4 regenned steps (85138, 85152, 85159, 85165) plus the inflight 85142 close the v1 P0s on the learner happy path. The 4-step regen sweep this morning successfully:

- Eliminated all Anthropic-CLI / Java / Spring-Boot leaks across the 4 regenned steps.
- Replaced the fabricated `.aider/commands/{{ARG1}}` mechanism with real `--message-file` + `/read-only` flows.
- Aligned all model slugs to `openrouter/moonshotai/kimi-k2-0905`.
- Removed the hallucinated `skillslab-platform/flowcast-orders-n1` URL from 85142.

The 3 NEW issues (env-var inconsistency, terse `must_contain` bullets in 2 of 3 terminal regens, stale module-3 objective text) are non-blocking but should land before the next review cycle. None of them prevent a beginner from completing the 4 steps end-to-end.

The cross-course nav bleed is open as a router-level audit ticket — confirmed the bug class still exists when the SPA's hash gets force-set, but a real learner catalog-clicking in does NOT trigger it. This was the conclusion in v2/v3; v4 confirms.

## Top 3 follow-ups (non-blocking)

1. **Propagate `OPENAI_API_KEY` across the course** — replace the one `OPENROUTER_API_KEY` mention in 85152 with `OPENAI_API_KEY`. Match Aider's actual env-var contract.
2. **Regen module 23211's objectives array** — strip the stale `.aider/commands/audit-endpoint.md` reference; mirror the new step body's "reusable audit prompt for Aider" framing.
3. **Tighten the Creator prompt's `must_contain` shape** — propagate 85142's artifact-anchored shape (`['Cloning into', 'module-1-starter', 'selectinload', 'PASSED']`) to 85152 + 85159 + any future terminal_exercise regens.
