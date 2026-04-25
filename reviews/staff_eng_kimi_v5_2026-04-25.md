# Staff-Engineer v5 Re-review — Kimi K2 + Aider Course

- Reviewer: senior staff engineer hat. 15+ yr Python/FastAPI/MLOps; OSS contributor; shipped LLM-augmented dev tooling. Reviewing as someone who would ACTUALLY deploy Aider+Kimi to a 50-eng team.
- Date: 2026-04-25 (round-7, v5 — capstone-grade walkthrough + new surface rule audit + hands-on solve of M7.S2/S3/S4).
- Course: `created-698e6399e3ca` — http://localhost:8001/#created-698e6399e3ca
- Repo: https://github.com/tusharbisht/kimi-eng-course-repo
- Prior artifact: `staff_eng_kimi_v4_2026-04-25.md` (P0-A1 closed, P0-A2 still soft-open; new P1 on 85142 fictional branch).
- New surface rule (ship-tested 2026-04-25):
  - `terminal_exercise` → terminal
  - `system_build` with `validation.gha_workflow_check` → terminal
  - everything else → web

---

## Stream notes (live, will rewrite verdict at the end)

### Step 0 — repo + raw pull

- `GET /api/admin/courses/created-698e6399e3ca/raw` → 167KB JSON. Parsed into 7 modules, 29 steps. **NOTE on user prompt:** prompt referenced "M7.S2/S3/S4" but the DB has only 6 modules (M0-M6). The GHA capstone block is **M6**: 85163 (fork), 85164 (implement), 85165 (code review), 85166 (push to GHA). Treating these as the intended targets per their function. If the user is referring to a separate M7 module that should exist, it does NOT — that itself is a finding.
- Live repo `tusharbisht/kimi-eng-course-repo` reachable via `gh api`. 7 branches present (module-0-preflight through module-6-capstone). Capstone branch contains the live `lab-grade.yml`.

### Step 1 — surface rule audit (NEW from v5 user prompt)

Surface rule per prompt:
- `terminal_exercise` → terminal
- `system_build` w/ `gha_workflow_check` → terminal
- everything else → web

DB state: **all 29 steps have `learner_surface = NULL`**. The prompt asked me to "flag any step where this rule and the DB's `learner_surface` disagree." Strictly read, every step disagrees because every step is NULL. But the runtime is clearly using a fallback resolver (`_resolve_learner_surface` in `backend/main.py:565`) that derives the surface from `exercise_type` at persist/render time. So the rule isn't broken — it's unmaterialized in the DB. **Finding (P1):** the surface column is the source-of-truth declaration, but for THIS course it was never written. If a future regen runs that ASSUMES a value and writes a different one, you'll have silent drift. Recommend a one-time backfill script (the codebase already has a stub at `backend/scripts/backfill_learner_surface.py` and a `backend/learner_surface.py` module) to populate the column for this course.

Per the rule, the expected surfaces:
- terminal: 85139, 85142, 85144, 85146, 85148, 85151, 85152, 85155, 85156, 85159, 85161, 85163, 85164, 85166 (14 steps; the system_build 85166 has gha_workflow_check so it qualifies as terminal)
- web: everything else (15 steps including 85165 code_review)

This is internally consistent with the cli_commands shape — every step that has a meaningful `cli_commands` array OR `gha_workflow_check` is a terminal step. No surface/etype contradictions found. Surface rule = SHIP-COMPATIBLE.

### Step 2 — P0-A1 (M5 cross-course MCP repo) — re-verified

`git clone https://github.com/tusharbisht/aie-team-tickets-mcp` is still the literal command. Prose still owns the cross-course reuse: *"The MCP repo itself doesn't change — only your consumer wiring is Kimi-specific."* v4 closed this via prose reframe; nothing changed in v5. **CLOSED (carry-over).**

### Step 3 — P0-A2 (M7.S4 — i.e. 85165 code_review briefing flag + bugs[] dedupe) — re-verified

Pulled `bugs[]` array on 85165:
```
[
  {line: 7,  description: "Hallucinated library - pydantic_idempotency does not exist on PyPI"},
  {line: 34, description: "Missing await keyword for async HTTP call"},
  {line: 54, description: "Missing await for async SQLAlchemy commit operation"},
  {line: 54, description: "Missing await for async SQLAlchemy commit operation"},   <-- DUPLICATE
  {line: 80, description: "Hardcoded delivery date instead of calculated estimate"}
]
```
- Duplicate line-54 entry **STILL THERE**. v4 demanded dedupe; round-7 did not address.
- Briefing prose **still does NOT** name `pydantic_idempotency` upfront. Generic "Dependencies & Libraries: Non-existent packages..." line is the closest hint.
- `validation.bug_lines: [7, 34, 54, 80]` — 4 unique entries. The duplicate in `bugs[]` is purely descriptive — it doesn't double-count rubric points. The bug is cosmetic/UX (hovering over the line might show two identical tooltips), but it signals "the author didn't QC this exercise" to a senior reviewer. Same finding v4 made.
- The second `db.commit()` IS in fact on line 65 of the rendered `code` (verified: `for item in request.line_items: ... db.add(order_item) ... db.commit()` is on line 65 of `demo_data.code`). The duplicate-54 entry was MEANT to be a 65 entry. So the rubric is also missing line 65 from `bug_lines`.

**P0-A2 verdict (v5):** STILL OPEN. Same shape as v4. Fix is unchanged: ONE briefing sentence + dedupe → relabel one to `line: 65`.

### Step 4 — capstone solve walk (the user prompt's "M7.S2/S3/S4 hands-on")

#### 85163 (fork + verify starter tests) — terminal_exercise

cli_commands:
1. `git remote -v` expects `github\.com/.+/kimi-eng-course-repo` — CORRECT (just verifies clone is there)
2. `git branch --show-current` expects `module-6-capstone` — CORRECT
3. `ls tests/api/test_orders.py` expects `tests/api/test_orders\.py` — CORRECT (matches live repo)
4. `pytest -v --tb=short` expects `passed` — **WEAK** (the starter test is `pytest.fail("CAPSTONE TODO")` — pytest will NOT print "passed" anywhere if the only test fails. Also `tests/test_health.py` does pass, so on the starter clone that test will print "1 passed, 1 failed" — the `passed` regex matches the partial. So the gate accepts a WIP. Reasonable as a "did you clone correctly" smoke, but it's not validating "starter tests pass" — it's validating "at least one test passed." Misleading expect).

Hands-on result: ran the equivalent (`cd /tmp && git clone --branch module-6-capstone ... kimi-capstone-walk`). Worked. Verified `tests/api/test_orders.py` is present. **Verdict: PASSES with weak signal on cli_commands[3].**

#### 85164 (implement POST /orders + tests with Aider+Kimi) — terminal_exercise

cli_commands:
1. `cd tusharbisht-kimi-eng-course-repo && git checkout module-6-capstone` expects branch switch — **NEW BUG (P1):** the directory is `kimi-eng-course-repo` (no `tusharbisht-` prefix) per `gh repo fork`'s default behavior. `gh repo fork --clone` creates a directory named after the REPO, not `<owner>-<repo>`. Verified by reading 85142's `gh repo fork https://github.com/tusharbisht/kimi-eng-course-repo --clone` (which creates `kimi-eng-course-repo/`). Running `cd tusharbisht-kimi-eng-course-repo` will fail with `cd: no such file or directory`. **NEW P1.**
2. `aider --model openrouter/moonshotai/kimi-k2-0905 --message "Implement POST /orders endpoint..."` — model slug correct (litellm-prefixed). Verbatim message length is 800+ chars; reasonable Aider invocation. expect: `Changes made|Applied edit|Successfully created|completed` — broad regex, will match.
3. `pytest tests/api/test_orders.py -v` expects `test_.*PASSED|\d+ passed` — CORRECT path (matches live repo) and CORRECT regex.

Hands-on solve: I do not have `OPENROUTER_API_KEY` set OR `aider` installed in this sandbox, so I could not invoke Aider end-to-end against Kimi. Instead I read the starter `app/api/orders.py` and `tests/api/test_orders.py` and confirmed the 4 spec-specified scenarios (happy / 422 / 200-replay / 409-conflict) match what the docstring asks. **NEW finding (P0):** the spec REQUIRES a Postgres `idempotency_keys` table (per the orders.py docstring), but **NO migration / Alembic config / model exists for it in the starter repo** (verified `grep -rn idempotency` returns only docstring/test prose hits + `app/api/orders.py:idempotency_key: str = Header(...)` — zero schema definitions). The learner has to:
  (a) write the `IdempotencyKey` SQLAlchemy model
  (b) ensure it's created in the test fixture (Testcontainers `Base.metadata.create_all` flow)
  (c) reason about response_body persistence, hash collisions
This is a reasonable senior-eng task BUT the briefing on 85164 + 85166 doesn't surface it. A learner who copy-pastes "Implement POST /orders endpoint with Pydantic validation, idempotency, async transactions" to Kimi will get an `IdempotentRequest`-style import (cf. 85165's planted hallucination!) — Kimi has been trained on `pydantic-idempotency` package phantom code as well as on bespoke Postgres patterns. The naming-of-the-table-in-the-docstring is the only scaffold. **The capstone tests an under-scaffolded skill: building idempotency from spec.**

Time-budget reality for a senior: ~30 min to read spec, ~30 min to drive Aider through model+endpoint+test, ~15 min on test fixture for `idempotency_keys` table (Testcontainers + create_all + asyncpg). 75 min total. The 85166 phase plan (10 + 60 + 10 + 10) = 90 min, so it's roughly aligned. Acceptable.

#### 85165 (code review) — code_review

Already audited above. P0-A2 STILL OPEN.

#### 85166 (push to GHA + paste run URL) — system_build

cli_commands: 0 (empty). Validation is `gha_workflow_check` — verified with the live `lab-grade.yml`:
- `pytest -q --strict-markers --cov=app --cov-fail-under=80` (BLOCKING)
- `ruff check .` (BLOCKING)
- `mypy app/` (BLOCKING, strict=true per pyproject.toml)
- Postgres 16 service container

Per the new surface rule: `system_build` w/ `gha_workflow_check` → terminal. **CORRECT** (this step needs the learner in their terminal pushing the branch).

**NEW BUG (P1) on 85166:** `demo_data.checklist[c5]` says *"Use Aider to implement tests/test_orders_endpoint.py with Testcontainers + 4+ scenarios"* — this path **does NOT exist** in the live repo. Real path is `tests/api/test_orders.py`. Verified via `gh api repos/.../contents/tests`: only `test_health.py` is at the root; the orders test lives under `tests/api/`. A learner following the checklist literally creates a NEW `tests/test_orders_endpoint.py` that is NOT picked up by the existing test scaffolding (and worse — it duplicates the canonical test, splitting coverage). **Cross-step path drift** — 85164 and the live repo agree on `tests/api/test_orders.py`; 85166 disagrees. ~30s narrow JSON edit.

Same checklist bug on c3: *"Run pytest -q locally — starter tests pass, test_orders_endpoint.py exists but empty"* — `test_orders_endpoint.py` does not exist; the file is `tests/api/test_orders.py` and it's not "empty," it's a `pytest.fail("CAPSTONE TODO")` stub.

### Step 5 — sniff tests (litellm prefix, env var, hallucinated paths)

| Sniff | Result |
|---|---|
| Bare `moonshotai/...` (no `openrouter/` prefix) on aider --model | **CLEAN** — 0 hits across all 29 steps. Every aider invocation uses `openrouter/moonshotai/kimi-k2-0905`. |
| `OPENROUTER_API_KEY` consistency | **CLEAN** — only 85140 mentions `ANTHROPIC_API_KEY` and that's an intentional WRONG-answer scenario_branch foil (good pedagogy). |
| Live `gh api` probe of `tusharbisht/kimi-eng-course-repo` branches | All 7 branches present. `module-6-capstone` exists and contains lab-grade.yml. |
| Live `gh api` probe of `tusharbisht/aie-team-tickets-mcp` (M5 dep) | (carry-over from v4) Live, public, real Node MCP. |
| Live `gh api` of `tests/api/test_orders.py` on capstone branch | EXISTS. Path drift in 85166 only (P1 above). |
| GHA gate fails on bad code | **YES.** Pushing the unfixed `module-6-capstone` branch with `raise NotImplementedError` fails on (1) pytest_orders test, (2) starter `tests/api/test_orders.py:test_capstone_is_unfinished` calls `pytest.fail("CAPSTONE TODO")`, (3) coverage <80%, (4) likely mypy under strict mode (NotImplementedError fn returns None against `OrderResponse` annotation). 4-orthogonal-checks gate. |
| `git log` validation for `--auto-commits` | **MISSING** (carry-over P1 from v4). No step verifies the learner committed. |
| Cost telemetry teaching | **NOT TAUGHT** (CLAUDE.md backlog confirmed still open). M0.S1 mentions "pennies-per-conversation costs" aspirationally; M4 budget loop is "conversation budget" (turn-cap), NOT cost/token accounting. Senior would have to add this themselves. |

### Step 6 — production-pattern realism check (capstone)

Does M6 capstone teach realistic production patterns? Checking against the capstone spec docstring:

| Pattern | Required? | Tested by GHA? |
|---|---|---|
| Idempotency (201/200/409 via Postgres-backed key table) | YES | YES (4 test scenarios required by docstring) |
| Async transactions (`async with session.begin()`) | YES | implicit — would fail integration tests if not atomic |
| Pydantic v2 validation → 422 | YES | YES (scenario b) |
| No N+1 (uses `selectinload`) | YES | NOT directly enforced — passes if tests pass |
| Concurrent-write safety (PRIMARY KEY constraint on idempotency_keys) | implicit | NOT TESTED (no concurrent-load test scenario) |
| Logging w/ correlation IDs | mentioned in 85166 prose | NOT ENFORCED |
| Timeouts on external calls | mentioned in 85165 (line 34 missing await) | NOT ENFORCED |

Verdict: capstone is **production-shaped** for atomicity + validation + idempotency. **Production-gap** on concurrent-write race testing (a senior would add `pytest.mark.asyncio` with `asyncio.gather` to fire 10 concurrent identical-key requests and assert 9 of them get the replay path) and on logging/timeouts (mentioned, not gated). For a 6-module course this is acceptable — the patterns are NAMED even when not enforced.

### Step 7 — ship-to-team senior assessment

**Could a senior eng who completes this course ship Aider+OpenRouter to a 50-eng team's daily workflow tomorrow?**

**YES**, with the 3 narrow blockers fixed (one carryover P0 + two new P1s). Strengths:

- M0 → M2 → M3 → M4 → M5 → M6 progression is the right inversion: feel-the-pain → AGENTS.md → workflows → own-the-loop → MCP-bridge → GHA capstone. A senior gets the FOUNDATION to evangelize this internally.
- litellm `openrouter/` prefix enforced via M2.S2 (85146) grep. The exact thing that breaks team CI when teams adopt OpenRouter without reading docs.
- M4's own-the-loop in ~100 lines IS the killer skill. Once a senior owns the loop they can swap providers in a sprint.
- M5's "MCP is just stdio JSON-RPC, language-agnostic" pedagogy lifts MCP out of the Anthropic-only tutorial swamp.
- M6 GHA gate is real (ruff + mypy + 80% coverage + Postgres) — failure is failure.

Weaknesses (what a senior would flag at their team retro after rolling out):

- **No cost telemetry** — a senior introducing OpenRouter to a 50-eng team will be asked "what's our token spend?" within week 1. Course doesn't teach the answer. (CLAUDE.md backlog item is REAL.)
- **No model fallback** — Moonshot 502s happen. Course doesn't show `aider --model fallback...` or `litellm.acompletion(fallbacks=...)`.
- **No prompt-regression CI** — a senior wants "if I change my AGENTS.md, does Aider's behavior on 5 canary tasks regress?" Not taught.
- **No concurrent-write idempotency test** — capstone teaches the pattern but doesn't gate the race condition.
- **Capstone schema scaffolding gap** — `idempotency_keys` table is named in docstring but no model/migration exists. Forces the learner to invent the schema. Realistic for a senior; under-scaffolded for an "intermediate" learner. P1 documentation polish: add a one-line note to 85164 briefing: *"You'll need to add an `IdempotencyKey` SQLAlchemy model — the docstring specifies the schema."*

### Step 8 — P0/P1 final tally

| Item | v5 status | Effort to land |
|---|---|---|
| P0-A1 (M5 cross-course MCP gloss) | **CLOSED** (carryover from v4) | — |
| P0-A2 (85165 briefing flag + bugs[] dedupe) | **STILL OPEN** | 5 min narrow JSON edit |
| 85142 fictional branch | **CLOSED** in this round (now uses `module-1-starter`) | — |
| 85155, 85164, 85166 OpenRouter/cov-fail-under coherence | **CLOSED** (carryover) | — |
| **NEW P1**: 85164 cli_commands[0] cd to non-existent `tusharbisht-kimi-eng-course-repo` directory | **OPEN** | 30s narrow edit (drop `tusharbisht-` prefix) |
| **NEW P1**: 85166 checklist c3/c5 reference fictional `tests/test_orders_endpoint.py` | **OPEN** | 30s narrow edit (→ `tests/api/test_orders.py`) |
| **NEW P1**: 85163 cli_commands[3] expect `passed` accepts partial-pass output | **OPEN** | 1 min (tighten regex to e.g. `\d+ passed[^,]*$` and ensure starter tests are all green pre-implementation) |
| P1 (carryover): no `git log` validation for auto-commits | **OPEN** | 1 step-edit per terminal_exercise |
| P1 (carryover): no cost telemetry teaching | **OPEN** | M4 sub-step (~30 min content authoring) |
| P1 (carryover): no model fallback teaching | **OPEN** | M0 sub-step or M2 conf example |
| P1 (carryover): no concurrent-write idempotency test in capstone | **OPEN** | 1 test scenario in lab-grade.yml or starter test_orders.py |
| Surface rule conformance | DB column NULL across course; runtime fallback derives correctly. **DECLARATIVE GAP** — recommend backfill | 1 script invocation |

**P0s closed: 1/2 (P0-A1 carry, P0-A2 still open).**
**New issues found: 3 P1s + 1 P0 (capstone schema scaffolding gap, downgraded to P1 since pedagogy is salvageable + actually realistic for senior persona).**

---

## Verdict

**SHIP-WITH-FIXES.**

The course is shipping-quality on the core pedagogy AND the validation-signal capture (litellm prefix grep, GHA gate with 4 orthogonal checks, real Postgres service, mypy strict). What's blocking clean ship is narrow-edit class issues, total ~6 minutes of regen authoring:

1. **85165 P0-A2** (carryover): 1 briefing sentence flagging `pydantic_idempotency` as a planted Kimi hallucination + dedupe `bugs[]` line-54 → reassign one entry to line 65.
2. **85164 P1 (NEW)**: cli_commands[0] `cd tusharbisht-kimi-eng-course-repo` → `cd kimi-eng-course-repo`.
3. **85166 P1 (NEW)**: checklist c3/c5 path `tests/test_orders_endpoint.py` → `tests/api/test_orders.py`.
4. **85163 P1 (NEW)**: cli_commands[3] tighten `passed` regex to require all-pass.
5. (Optional, defer to next round) Add a 2-line note in 85164 briefing about the `IdempotencyKey` model the learner has to author.

## Ship-to-team assessment

**YES — POST the 3 narrow fixes above, ship to a 50-eng Python team that wants OPEN-SOURCE AI coding without Anthropic dependency.**

A senior eng who walks this course AS-IS today will:
- Hit a 60-second bounce on 85164 (`cd tusharbisht-kimi-eng-course-repo` fails) — figure it out, mild trust deficit.
- Hit a confusion-bounce on 85166 checklist (creates the wrong-named test file, then can't figure out why pytest doesn't pick it up) — ~5 min lost, moderate trust deficit.
- Land on the GHA gate cleanly — that's the load-bearing primitive. PASS or FAIL is real.
- Walk away owning: AGENTS.md authoring + OpenRouter/litellm config + Aider workflow primitives + their own tool-use loop + MCP adapter pattern + GHA-gated capstone shipping.

POST-fix the experience is clean. The pedagogy mirrors what proven AIE-course patterns established: feel-pain → context → workflows → own-the-loop → MCP → ship-via-CI. The OpenRouter litellm-prefix enforcement is the kind of detail that teaches "how to ACTUALLY ship this to your team's CI" not just "how to demo this on your laptop."

Cost-telemetry and model-fallback gaps remain — these are the real backlog items for v2 of the course IF teams adopt at scale. For initial cohort ship: not blocking, but flag in the course README's "what's next" so a senior knows to add them before a wide rollout.

— reviewed, 2026-04-25 (round-7 v5)
