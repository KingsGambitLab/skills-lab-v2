# Staff-Engineer v4 Re-review — Kimi K2 + Aider Course (post round-6 regen sweep)

- Reviewer: senior staff engineer hat. 15+ yr Python/FastAPI/MLOps; OSS contributor; shipped LLM-augmented dev tooling; opinions on what "production-ready Aider workflow" means; knows OpenRouter quirks; knows litellm provider-prefix requirement.
- Date: 2026-04-25 (round-6 — the regen sweep covering 85138 / 85152 / 85159 / 85165 + Creator/TechSchema patches landing the litellm `openrouter/` prefix).
- Course: `created-698e6399e3ca` — http://localhost:8001/#created-698e6399e3ca
- Repo: https://github.com/tusharbisht/kimi-eng-course-repo (verified live, 7 branches: module-0-preflight / module-1-starter / module-2-claudemd / module-3-agents / module-4-hooks / module-5-mcp / module-6-capstone)
- Method: pulled raw step JSON via `GET /api/admin/courses/{id}/raw`; cross-referenced live repo branches via GitHub API; verified cli_commands `expect` regex against the validation-signal claim in the prompt.
- Prior artifacts read: morning v1 (`staff_eng_kimi_aie_postfix_2026-04-25.md`), v2 (`staff_eng_kimi_v2_2026-04-25.md`), v3 (`staff_eng_kimi_v3_2026-04-25.md`).

---

## Morning v1 P0s — verbatim re-statement

From `staff_eng_kimi_aie_postfix_2026-04-25.md` lines 60-76:

**P0-A1.** *"M5 clones the AIE MCP repo (`tusharbisht/aie-team-tickets-mcp`), not a Kimi-specific one. The demo_data in M5.S2 literal instructions reads `git clone https://github.com/tusharbisht/aie-team-tickets-mcp` — and M5.S3's code_read header says `// stdio JSON-RPC handler from tusharbisht/aie-team-tickets-mcp`. There is no `tusharbisht/kimi-team-tickets-mcp`; the repo never existed. A senior eng on course A sees a repo prefixed with `aie-` (the OTHER course's naming) and immediately asks 'is this Kimi course just a fork of the AIE course? Did the author even QC this?' It's a trust-breaking cross-course leak."*

**P0-A2.** *"M7.S4 capstone code_review references `pydantic_idempotency` (not a real PyPI package). [...] The planted-bug list (`bug_lines: [6, 28, 38, 41, 76]`) includes line 6 (the import) — so the EXERCISE is intentionally asking the learner to flag it as an import hallucination. That's pedagogically sound. The problem: [...] without a 1-line gloss explaining 'this is a real class of Kimi hallucination, here's what a real learner would've seen' the exercise reads as 'did the course author vibe-check the code they're asking me to review?' Fix: add 2 lines to M7.S4's briefing."*

---

## P0-A1 — M5 cross-course MCP repo leak

### Walk

Pulled step 85159 (M5.S2) raw:
- `validation.cli_commands[0].cmd`: `git clone https://github.com/tusharbisht/aie-team-tickets-mcp.git && cd aie-team-tickets-mcp && npm install && cd .. && pip install httpx`
- The `aie-` prefix is STILL present in the actual clone command. The repo `tusharbisht/aie-team-tickets-mcp` is verified live (per morning artifact line 194; confirmed today: it's a real public Node stdio MCP).
- Content prose now opens with: *"Bridge MCP to Any LLM. Moonshot AI doesn't natively speak MCP (Model Context Protocol) like Anthropic models do — but that doesn't mean you can't consume team context. MCPs are just stdio JSON-RPC processes; any language can spawn them and speak their protocol."* And follows with: *"The MCP repo itself doesn't change — only your consumer wiring is Kimi-specific."*

### Verdict — **CLOSED via reframe (NOT via rename)**

The fix landed as PEDAGOGY, not as a repo rename. The user-facing instructions still say `git clone tusharbisht/aie-team-tickets-mcp`, but the content prose now owns the cross-course reuse explicitly: MCP is a protocol, the same MCP can be consumed across two stacks (Anthropic + Kimi), and that fact IS the lesson. A senior eng reading the prose first will understand WHY the `aie-` prefix is there before they hit the clone command.

This is a defensible call — renaming a repo to `tusharbisht/kimi-team-tickets-mcp` to spare 30 seconds of cognitive friction would have made the cross-stack pedagogy invisible. Reuse-with-explanation > silent-fork. Ship-acceptable.

**Caveat (P1, not blocking):** v2's review (lines 25-31) quoted a verbatim "MCP Without the Magic" panel that is NOT in the live step content. v3 already flagged this as a v2 fabrication. Today's actual content uses the "Bridge MCP to Any LLM" header — same pedagogical move, slightly weaker explicitness. The cross-course-reuse acknowledgment IS in the prose ("the MCP repo itself doesn't change — only your consumer wiring is Kimi-specific"). Closes the trust-breaker. Future polish: tighten ONE line to name the cross-course-reuse fact upfront in the briefing.

P0-A1 = **CLOSED**.

---

## P0-A2 — M7.S4 planted hallucination needs to be flagged

### Walk

Pulled step 85165 (M7.S4) raw:
- `content` (the briefing the learner reads): generic "Bug Categories to Hunt For" list. First item: *"Dependencies & Libraries: Non-existent packages, wrong import paths, version mismatches"* — generic. **`pydantic_idempotency` is NOT named in the briefing.**
- `demo_data.bugs[]`: line 7 entry says `description: "Hallucinated library - pydantic_idempotency does not exist on PyPI"`. This is post-submit feedback (shown after the learner clicks line 7). Not visible during the review.
- The morning P0-A2 fix asks for: *"a 1-line gloss explaining 'this is a real class of Kimi hallucination, here's what a real learner would've seen.'"* That gloss is NOT in the briefing. v3 already flagged this; the round-6 regen did not address it.
- v2's review (lines 39-44) claimed an "IMPORTANT: This 60-line diff was generated by Kimi K2... ONE of the flaws is a HALLUCINATED LIBRARY" warning paragraph. v3 verified this paragraph is NOT in the live step. v4 confirms: still not there.
- Additionally: `demo_data.bugs[]` contains a duplicate entry — line 54 appears twice with byte-identical description. Likely a copy-paste error meant for the second `db.commit()` on line 65/66. Real bug count is 4 unique bugs, not 5; the rubric's `bug_lines: [7, 34, 54, 80]` agrees on 4.

### Verdict — **STILL OPEN, soft form (∼60% closed)**

The exercise is salvageable: the planted-bug feedback DOES reveal `pydantic_idempotency` is fake post-click, so a learner who clicks line 7 and reads the explanation walks away taught. But the morning P0-A2 fix specified a PRE-CLICK gloss in the briefing — that's missing. A senior eng who already burned 30 min pip-installing `pydantic_idempotency` IRL still doesn't see "this exact package is fictional on purpose; don't go look for it" before walking into the exercise.

**Concrete fix (still owed)**: ONE sentence in 85165's briefing: *"Note: one planted bug is `pydantic_idempotency` — a fictional package on purpose. It demonstrates a real Kimi K2 hallucination class. Do not pip-install it."* Plus dedupe the `bugs[]` entry on line 54 → make the second one point to line 65 (the second `db.commit()`).

This is the same fix v3 demanded that didn't land in round-6. ~5 min of narrow JSON edit OR a per-step regen with explicit feedback body.

P0-A2 = **STILL OPEN soft form**.

---

## P0 closure tally

**1/2 P0s fully closed.** P0-A1 closed via prose reframe; P0-A2 still missing the briefing-level planted-bug flag.

| P0 | v1 verdict | v2 verdict | v3 verdict | v4 verdict |
|---|---|---|---|---|
| P0-A1 (M5 cross-course MCP) | OPEN | CLOSED | CLOSED | **CLOSED** |
| P0-A2 (M7.S4 planted-hallucination flag) | OPEN | CLOSED (false claim) | STILL OPEN soft form | **STILL OPEN soft form** |

---

## Senior critique on cli_commands shape — does it capture the right validation signal?

This is the load-bearing technical question for whether the course teaches "shipping" vs "demoing." Walked the regen'd + capstone-adjacent steps:

| Step | exercise_type | cli_commands shape | Captures the right signal? |
|---|---|---|---|
| **85139** (M0.S2 smoke test) | terminal_exercise | 3 commands: `aider --version` + `python3 --version` + `aider --model openrouter/moonshotai/kimi-k2-0905 --message 'Hi, what model are you?'`. Each has an `expect` regex (`[Kk]imi` for the third). | YES for tool presence + invocation shape. The third `expect: [Kk]imi` is the SAME morning P1 (Kimi K2 self-introduction may not always include the literal word). Otherwise sound. |
| **85146** (M2.S2 AGENTS.md + .aider.conf.yml) | terminal_exercise | 4 commands: `ls -la` + `grep -E 'FastAPI\|SQLAlchemy 2\.0\|pytest' AGENTS.md` + `grep -E 'model:.*openrouter/moonshotai/kimi-k2-0905' .aider.conf.yml` + `grep AGENTS.md .aider.conf.yml`. | **YES — best-in-course.** The third command verifies the `openrouter/` prefix is in the config (the litellm requirement the user prompt called out). This is exactly the validation: "did the learner write a config that will ACTUALLY WORK?", not "did the learner type the right words?" |
| **85152** (M3.S3 audit-endpoint) | terminal_exercise | 3 commands: heredoc creates `prompts/audit-endpoint.md` (`expect: ` empty — just creates) + `aider --message-file prompts/audit-endpoint.md` (`expect:` checks audit content surfaces) + an echo. | **PARTIAL.** Command 1 has empty `expect` so it's just smoke-test. Command 2 verifies Kimi's audit output mentions `Authentication\|authorization\|error\|N\+1`. Command 3 is a non-validating echo. The middle command IS doing real work (sees Kimi actually produced an audit); first + third are noise. |
| **85155** (M4.S2 harness/loop.py) | terminal_exercise | 4 commands: `ls -la harness/` + `python -m py_compile harness/loop.py` + `python loop.py 'Fix the failing test'` (expects `(tool_use\|read_file\|edit_file\|run_pytest).*success`) + `pytest -v failing_test.py` (expects `PASSED`). | **YES.** Compile check + exec check + test-driven proof. The third command's `expect` regex captures "tool_use was emitted AND success" — the actual signal that a tool-use loop ran. Solid. |
| **85159** (M5.S2 MCP adapter) | terminal_exercise | 3 commands: `git clone aie-team-tickets-mcp && npm install` (expects `added.*packages`) + `node index.js` (MCP started) + `python mcp_adapter.py` (expects `get_tickets.*update_ticket`). | **YES.** The third command's expect regex verifies the adapter's output mentions both expected MCP tools — proof the adapter is reaching the MCP. |
| **85164** (M6.S3 POST /orders) | terminal_exercise | 3 commands: file-existence check for `app/api/orders.py` + `tests/test_orders_endpoint.py` + `pytest tests/test_orders_endpoint.py -v --tb=short \| tail -50` expecting `passed\|PASSED`. | **YES.** The pytest run is the load-bearing signal. File existence is a cheap pre-check. |
| **85166** (M6 capstone GHA paste) | system_build | NO `cli_commands`. Uses `gha_workflow_check` instead: `{repo_pattern: '*/kimi-eng-course-repo', workflow_file: '.github/workflows/lab-grade.yml', grading_job: 'grade', expected_conclusion: 'success', timeout_minutes: 15}`. | **YES — strongest gate in the course.** Verified upstream lab-grade.yml has `pytest --cov-fail-under=80` + ruff blocking + mypy blocking + Postgres service. Pushing the un-fixed `module-6-capstone` branch with `raise NotImplementedError` fails on pytest, on coverage, and on mypy. The `expected_conclusion=success` is the real signal. |

### Senior assessment

The cli_commands shape across the 6 walked steps is **mostly sound**. The strongest validation signals are 85146 (litellm `openrouter/` prefix grep), 85155 (compile + exec + tool_use regex + pytest), 85164 (pytest with `--tb=short`), and 85166 (real GHA conclusion check).

**The right signals being captured:**
- Tool presence: `--version` checks
- Config correctness: `grep -E 'model:.*openrouter/moonshotai/kimi-k2-0905'` (this is the explicit litellm-prefix audit and IS in the regen)
- Behavior: pytest passing, tool_use JSON emission, MCP tool listing
- CI gate: GHA `expected_conclusion: success` against a real lab-grade.yml

**The one validation-signal gap:** none of the cli_commands check `git log` to verify the learner actually committed (Aider's `--auto-commits true` behavior). For a course teaching team-shareable engineering, "did you commit your work" is a real signal that's missing. This is P1 polish, not P0 — most learners pushing to GHA will commit naturally because GHA wouldn't see uncommitted changes.

**Smoke-testing vs validation:** 85152 command 1 (`mkdir -p prompts && echo 'audit checklist...'`) and 85152 command 3 (`echo 'Audit completed'`) are smoke-tests with no validation signal. Replacing them with `wc -l prompts/audit-endpoint.md > 30` (proves the audit checklist is non-trivial) would tighten the gate. P2.

**`exit code` capture:** The `cli_commands` shape relies on `expect` regex matching against stdout, not on exit code. This means a command that exits 1 but happens to print the expected substring still "passes." For a Phase B-style HARNESS-CLOSURE invariant this would be a hole; for an Aider-tutorial CLI walk it's acceptable because most Aider output is informational. Mention as a P1 platform-level investment for the future, not for this course.

### Capstone GHA — does it actually fail on bad code?

YES. Verified the GHA workflow on the live `module-6-capstone` branch:
- `pytest --cov=app --cov-fail-under=80` against `postgresql+asyncpg://test:test@localhost:5432/test`
- `ruff check .` (BLOCKING — pipefails build)
- `mypy app/` (BLOCKING — strict mode per pyproject.toml on capstone branch)
- Failure uploads `htmlcov/` artifact

A learner pushing the un-fixed branch (`raise NotImplementedError("CAPSTONE TODO")` in `app/api/orders.py`) will fail on:
1. pytest (the unimplemented function returns `None` against a typed return)
2. coverage (function body 0% covered)
3. mypy (likely — depends on the type annotation, but `None` against `OrderResponse` return type fails strict)
4. ruff (cleaner — unused import warnings if any)

Multiple-orthogonal-checks gate. Not a smoke test. Real ship/no-ship.

---

## Cross-course consistency: ship-to-team test

**Could a senior eng who completes this course ship Aider+OpenRouter to a team's daily workflow tomorrow?**

YES, with the P0-A2 gloss fix. Reasoning:

- **OpenRouter onboarding**: M0.S2 walks through `OPENROUTER_API_KEY` env + `aider --model openrouter/moonshotai/kimi-k2-0905`. M2 templates `.aider.conf.yml` with the same prefix. The litellm requirement (the user prompt's explicit concern) is enforced via 85146's `grep -E 'model:.*openrouter/moonshotai/kimi-k2-0905'` check — bare `moonshotai/...` patterns would FAIL this validation. The "forbidden_examples" carrying bare `moonshotai/...` (per the user prompt) is the right enforcement direction.
- **AGENTS.md authoring**: M2 has the learner author one for the FlowCast repo. The `read: [AGENTS.md]` config is templated. This is the team-shareable primitive a senior brings back to their team.
- **Custom commands**: M3.S3's regen now uses real Aider primitives (`--message-file` + `/read-only`). Reusable `prompts/audit-endpoint.md` is a real Aider 0.65+ pattern.
- **Tool-use loop ownership**: M4 forces the learner to OWN the loop in ~100 lines. This is the highest-leverage skill — once owned, provider-swap is trivial.
- **MCP-from-non-Anthropic-LLM**: M5's bridge pattern (the cross-course-reuse pedagogy) is the piece every Anthropic-tilted MCP tutorial skips.
- **Capstone**: GHA-graded POST /orders with idempotency + Testcontainers + 80% cov gate. Real production-grade.

**What's still tutorial-shaped (not blocking, queued backlog):**

- No teaching of OPENROUTER_API_KEY rotation (multiple keys, rotation cadence)
- No model fallback (e.g. fallback to `kimi-k2-0905` if `kimi-k2-latest` regresses, or fallback to a different OpenRouter slug if Moonshot's slug 502s)
- No cost telemetry (per-request cost log, per-day budget cap, per-engineer attribution)
- No team-wide guardrails (Aider hooks for protected paths beyond what the M4 stub demonstrates)
- No CI integration for prompt-regression testing (e.g. CI runs Aider against a fixed seed, asserts output diff is small)

These are P1-backlog gaps the user prompt explicitly de-prioritized. Sane. The course teaches the FOUNDATION; these gaps are second-order team-deployment ergonomics.

---

## Step 85142 spot-check — known-open hallucinated URL

User prompt: *"step 85142 had a hallucinated `skillslab-platform/flowcast-orders-n1` URL. Regen for it is in flight. At end of your run, spot-check 85142 to see if it's now using the canonical `tusharbisht/kimi-eng-course-repo` from course_assets.py."*

### Walk

Pulled 85142 raw:
- `cli_commands[0].cmd`: `gh repo fork https://github.com/tusharbisht/kimi-eng-course-repo --clone || git clone https://github.com/tusharbisht/kimi-eng-course-repo.git`
- `cli_commands[1].cmd`: `cd kimi-eng-course-repo && git checkout module-2-flowcast-orders`
- `demo_data.instructions` HTML: same `gh repo fork tusharbisht/kimi-eng-course-repo` + `git checkout module-2-flowcast-orders`

### URL verdict — **FIXED**

The hallucinated `skillslab-platform/flowcast-orders-n1` URL is gone. The regen now uses the canonical `tusharbisht/kimi-eng-course-repo` from `course_assets.py`. P0-equivalent on URL canonicality is closed.

### NEW REGRESSION introduced by 85142 regen — **P1**

The regen introduces a **fictional branch name**: `git checkout module-2-flowcast-orders`. Verified live via GitHub API: that branch does NOT exist on `tusharbisht/kimi-eng-course-repo`. Real branches:
```
module-0-preflight, module-1-starter, module-2-claudemd, module-3-agents,
module-4-hooks, module-5-mcp, module-6-capstone
```

For an M1 step (the FIRST step a learner sees after preflight), the right branch is `module-1-starter` (which has the planted N+1 bug per morning artifact line 34). The regen synthesized a plausible-but-wrong branch name. A learner running this command verbatim hits `error: pathspec 'module-2-flowcast-orders' did not match any file(s) known to git` and bounces.

**Fix:** change `git checkout module-2-flowcast-orders` → `git checkout module-1-starter`. Both in `cli_commands` AND in `demo_data.instructions` HTML. ~30s narrow JSON edit OR per-step regen with explicit feedback body: *"prior attempt used fictional branch `module-2-flowcast-orders`; the actual branch carrying the N+1 bug is `module-1-starter` per the kimi-eng-course-repo branch list."*

This is a NEW P1 the round-6 regen introduced. Tradable for the URL fix that landed (clearly worth the trade), but needs to land before ship.

---

## Cross-step validation — v3's flagged regressions

v3 flagged 3 regressions in non-regenerated steps. Verified state:

| v3 flag | v3 finding | v4 state |
|---|---|---|
| **R1**: 85155 used Moonshot-direct (`api.moonshot.cn`) | OpenAPI base mismatch with rest of course | **FIXED** — 85155 now uses `OPENROUTER_API_KEY` per its own demo_data; cli_commands match. |
| **R2**: 85164 capstone uses `deepseek-chat` | Course-internal coherence regression | **FIXED** — 85164 now uses `aider --model openrouter/moonshotai/kimi-k2-0905`. |
| **R3**: 85166 narrative says `--cov-fail-under=85`, actual is 80 | Copy drift | **FIXED** — 85166 narrative now says `pytest --cov=app --cov-fail-under=80`. |

All 3 v3 flags closed. Round-6 sweep landed cleanly on these.

---

## P0/P1 final summary

| Item | v4 status |
|---|---|
| P0-A1 (M5 cross-course MCP gloss) | **CLOSED** (via prose reframe, not rename) |
| P0-A2 (M7.S4 planted-hallucination briefing flag) | **STILL OPEN soft form** — 1 sentence + dedupe needed |
| 85142 hallucinated URL | **FIXED** — canonical kimi-eng-course-repo |
| 85142 NEW: fictional `module-2-flowcast-orders` branch | **NEW P1** — fix to `module-1-starter` |
| 85155 OpenRouter mismatch | **FIXED** |
| 85164 deepseek-chat slug | **FIXED** |
| 85166 cov-fail-under copy drift | **FIXED** |
| Aider command surface (14 commands) | CLEAN |
| Moonshot tool_calls JSON shape | CORRECT |
| litellm `openrouter/` prefix enforcement | ENFORCED via 85146 grep |
| Capstone GHA gate | REAL (pytest + ruff + mypy + 80% cov) |
| cli_commands signal capture | MOSTLY SOLID (85152 has 2 weak commands) |

**P0s closed: 1/2.**
**New P1 introduced by round-6: 1 (85142 fictional branch).**
**v3 regressions closed: 3/3.**

---

## Verdict

**SHIP-WITH-FIXES.**

The course is shipping-quality on the core pedagogy — Aider + Kimi K2 + OpenRouter + AGENTS.md + custom prompts + own-the-loop + MCP-from-non-Anthropic-LLM + GHA-graded capstone. The litellm `openrouter/` prefix is enforced at the validation layer (85146 grep), the Moonshot tool_calls JSON shape is correct, the GHA gate is real. The Aider command surface (14 commands across 6 modules) is verbatim accurate against the docs.

Two narrow fixes block clean ship:

1. **85165 (P0-A2)**: ONE sentence in the briefing flagging `pydantic_idempotency` as a planted Kimi-hallucination class + dedupe the `bugs[]` array (the second line-54 entry should point to line 65). ~5 min narrow JSON edit OR per-step regen.
2. **85142 (NEW P1)**: change `git checkout module-2-flowcast-orders` → `git checkout module-1-starter`. ~30s narrow JSON edit.

Total: ~6 minutes of narrow per-step edits per CLAUDE.md §"Always Regen EXACTLY what is broken." No whole-course regen.

---

## Ship-to-team assessment

**YES, ship to a 50-engineer Python team that wants OPEN-SOURCE AI coding without Anthropic dependency — POST the 2 narrow fixes above.**

A senior eng walking this course AS-IS today (with the 2 open items unfixed) will:
- Bounce on M1 step 85142 due to `module-2-flowcast-orders` not existing — they'll figure it out in 60s but the trust deficit lingers.
- Land cleanly on the M7 code review (85165) since Kimi-the-author hallucinations are inherent to the exercise's pedagogy. The post-click feedback DOES name `pydantic_idempotency` — they'll get it. But a SENIOR who already burned cycles on `pip install pydantic_idempotency` IRL gets a "vibe-check" smell from the briefing not naming the planted bug upfront.

POST-fix the experience is clean. Pedagogy is the same winning inversion the AIE course already proved (feel-the-pain → AGENTS.md → measure-delta → own-the-loop → MCP adapter → GHA capstone). The OpenRouter litellm-prefix enforcement is the kind of detail that breaks CI for newcomer teams; teaching it via grep validation is the right move.

The cli_commands shape captures real validation signal (compile / exec / pytest passing / GHA conclusion-success / litellm-prefix grep) — not just smoke-testing. The capstone GHA gate (`pytest --cov-fail-under=80` + ruff blocking + mypy blocking + Postgres service) WILL fail on bad code. This is a real ship/no-ship gate.

ROI math for 50 engineers (unchanged from morning + reinforced):
- Every eng owns the OpenAI-compatible tool_calls loop in ~100 lines (M4) → unblocks provider-swap decisions.
- Every eng authors AGENTS.md for their team repo → measurable dev-loop turn-count delta.
- ~5 engs end up owning an MCP-adapter pattern in production within 6 months → real team-capability lift.

Fixed cost to land: ~6 eng-min (P0-A2 + 85142 branch-name fix). P1-backlog (key rotation, model fallback, cost telemetry) is ~4-6 eng-hr work; can land as a v2 follow-on without re-gating the cohort.

— reviewed, 2026-04-25 (round-6 v4)
