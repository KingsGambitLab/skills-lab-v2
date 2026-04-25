# Beginner Stream Review — "Open-Source AI Coding: Ship Production Features with Kimi K2 + Aider"

- **Reviewer persona**: mid-level Python backend engineer (3-5 yrs FastAPI + SQLAlchemy + pytest), no Anthropic key, wants free/cheap AI coding → signed up for OpenRouter free tier + Aider + Kimi K2.
- **Date**: 2026-04-25
- **Course**: `created-698e6399e3ca` — http://localhost:8001/#created-698e6399e3ca
- **Steps walked**: 18 of 29 (meeting the ≥12 quota; sampled across all 7 modules).
- **Tool budget used**: ~110 of 130 MCP calls.

---

## Tally

| Status     | Count | Steps |
|------------|------:|-------|
| Passed     | 6     | M0.S1 (concept), M0.S3 (scenario), M1.S2 (term. exerc.), M2.S2 (authoring), M4.S3 (guardrail), M6.S5 (GHA grader) |
| Partial    | 7     | M0.S2 (preflight), M1.S1, M1.S3 (drag-drop), M2.S1 (concept), M3.S1 (concept), M4.S1 (concept), M5.S1 (concept) |
| Stuck / Rejected | 3 | M3.S3 (fabricated custom-commands), M5.S2 (unverified repo), M6.S2 (cross-course leak) |
| Unobserved | 11   | deeper steps; stopped at budget and after ship-blockers surfaced |

Overall usability score: **3.2/5** for a beginner who trusts course content at face value. Without careful triangulation, a beginner would be misled by the fabricated Aider custom-commands step and by the Anthropic-branded troubleshooting accordions.

---

## Per-step blocks (observed)

### Step 0.0 — "What this course IS (and isn't)" — concept
- Briefing clarity: 4/5 | time: 2 min
- No attempt (concept page).
- Interactive Aider Command Explorer shows `--model / /run / /test / /diff / /undo / /architect / /code`. Clicking `/architect` returns accurate text describing plan-before-code.
- Verdict: ✅ passed.
- UI note: good framing of cost delta ($0.04-$0.12/turn Kimi vs $0.30-$1.00/turn Claude Code).

### Step 0.1 — "Smoke-test your toolchain against Kimi K2" — terminal_exercise
- Briefing clarity: 3/5 | time: 6 min
- Attempt 1 (wrong): `$ aider --version\ncommand not found: aider` → **Score: 7%**. Feedback: "Your submission didn't match what the exercise expects. Re-read the briefing." Useful for iteration? **no** — completely generic.
- Attempt 2 (real, detailed): full aider + python + Kimi roundtrip → **Score: 0%**. Grader regressed to zero on a clearly correct paste. Bug.
- Attempt 3 (shorter real): aider + python + "I am Kimi" response → after Submit the app jumped me into a **different course** (`created-e54e7d6f51cf`, the Java/Claude-Code course) and I lost score context.
- Verdict: ⚠ partial. Grader is noisy and navigation bug loses state on submit.
- **Critical flags (ship-blockers):**
  1. Lock-icon info panel says: *"Configure Claude Code with `claude /login` (or set ANTHROPIC_API_KEY in your shell). This page will never ask for your key."* — this is in the Kimi+Aider course promised to be zero-Anthropic. **This exact sentence recurs on every terminal_exercise** in M0, M1, M2, M3, M4, M5, M6 — a global template leak.
  2. Paste textarea placeholder reads: `$ claude --version\nclaude-code 1.x.x\n\n... full output goes here ...` — another Claude-Code template that never got swapped for Aider.
  3. Troubleshooting accordions (after expansion) show **three Java/Spring-Boot items**: *"Got 'claude: command not found'?"* recommends `npm i -g @anthropic-ai/claude-code`; *"Got 'java: command not found'?"* references brew/adoptium; *"Got './mvnw: No such file or directory'?"* tells you to `git clone https://github.com/tusharbisht/jspring-course-repo && git checkout module-0-preflight`. None of this belongs in the Kimi+Aider Python course.
  4. No explicit OpenRouter 401 guidance here (it lives in M0.S3). No `sk-or-*` key-format explanation here (lives in M0.S3). A beginner hitting 401 at M0.S2 has no breadcrumbs on this page.

### Step 0.2 — "Auth failure triage: 401 from OpenRouter" — scenario_branch
- Briefing clarity: 4/5 | time: 3 min
- Three decisions, three options each. Content quality is genuinely good: mentions `sk-or-` prefix, `OPENAI_API_KEY` env var, OpenRouter vs direct Moonshot endpoint, and the adapter pattern (separate Moonshot key needed for direct endpoint).
- Clicked D1 option 2 ("Switch to api.moonshot.ai") — a dodgy choice for first diagnostic step. No per-question feedback; step just progressed.
- Clicked D2 option 1, D3 option 0 — final screen shows only a summary paragraph. **No scoring, no per-branch feedback, no "you picked wrong in D1 — here's why"**.
- Verdict: ⚠ partial. Content is right; pedagogy is thin — scenario_branch doesn't distinguish right vs wrong paths.

### Step 1.0 — "Why context is oxygen" — concept
- Briefing clarity: 4/5 | time: 3 min
- Clicked "Show the Fix Attempts" → *"Failed to load course details."* — the interactive demo panel errored. No content surfaced.
- Verdict: ⚠ partial.

### Step 1.1 — "Fix the N+1 bug in OrderService.get_recent_orders (no AGENTS.md)" — terminal_exercise
- Briefing clarity: 5/5 | time: 7 min
- Attempt 1 (wrong): garbage string → **Score: 7%**. Useful for iteration? **no** — generic.
- Attempt 2 (real, detailed Aider transcript with SEARCH/REPLACE block, selectinload, async 2.0 rewrite note, pytest swap) → **Score: 87%**. Feedback: "you've demonstrated all required components... Your output is missing 2 of 3 expected markers." Useful? **partially** — good narrative, but doesn't tell you *which* two markers.
- Verdict: ✅ passed (partial grading info).
- **Accuracy check (per user's ask)**: Kimi's planted N+1 in `OrderService.get_recent_orders()` → the course explicitly contrasts SA 1.x `query()` with 2.0 `select()` and expects learners to escalate to async `select().options(selectinload(...))`. That matches modern SQLAlchemy 2.0 shape. The briefing even calls out that Kimi will likely reach for unittest/1.x `query()` without AGENTS.md — a realistic setup. ✓ Good.

### Step 1.2 — "Sort 10 Kimi outputs" — categorization
- Briefing clarity: 5/5 | time: 8 min
- **Discrepancy**: briefing says "10 realistic outputs"; UI shows 8.
- Attempt 1 (wrong): everything dropped into `wrong-tool` → **Score: 25% (2 of 8 correct)**. Feedback: "6 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again." Useful? **partially** — gives count but not per-item.
- Attempt 2 (reasoned mapping): programmatically moved items by `data-id`, but the Submit button then showed *"Score: 0%. Paste your terminal output first."* — template mis-identification bug after programmatic drag-drop (it thought the step was a terminal_exercise). Real human learners dragging the UI would likely not hit this; it's an artifact of my tooling.
- Verdict: ⚠ partial. Content items are genuinely good (Django `prefetch_related`, Flask `@app.route`, `load_strategy()` hallucination are spot-on realistic Kimi failure modes).

### Step 2.0 — "Anatomy of a great Python AGENTS.md" — concept
- Briefing clarity: 5/5 | time: 4 min
- Content: six-section `AGENTS.md` template (Stack / Conventions / Testing / Don't-Touch / Commands / Escalation) with concrete "NEVER 1.x query()", "pytest-asyncio not unittest", "selectinload on relationships" examples. Very high quality.
- Verdict: ✅ passed.

### Step 2.1 — "Author AGENTS.md and .aider.conf.yml" — terminal_exercise
- Briefing clarity: 5/5 | time: 6 min
- Attempt 1 (full realistic AGENTS.md + `.aider.conf.yml` with `model`, `openai-api-base`, `auto-commits: false`, `dirty-commits: false`, `read: AGENTS.md`, plus simulated Aider transcript showing selectinload + pytest-asyncio) → **Score: 100%**. Feedback narrative correctly called out the Aider shape and Kimi behaviour. Useful? **yes** — best grader feedback in the course.
- Verdict: ✅ passed.
- **Accuracy check (per user's ask)**: `.aider.conf.yml` field names `model`, `openai-api-base`, `read`, `auto-commits`, `dirty-commits` → all correct YAML keys per Aider 0.64-0.69 docs. ✓ Good.
  - Minor: the course's *example* in the briefing omits `openai-api-base`, relying on the learner to add it from the CLI invocations shown elsewhere. Beginners will likely leave it out → Aider will then default to api.openai.com and 401 against a `sk-or-` key. Worth adding explicitly.

### Step 3.0 — "Aider's mode primitives: /architect, /code, /ask, /run, /diff" — concept
- Briefing clarity: 5/5 | time: 3 min
- All five commands accurate. Table mapping Aider mode → Claude Code equivalent is a nice transfer-learning affordance. Example workflow (architect → ask → code → run → diff) is realistic.
- Verdict: ✅ passed.
- **Accuracy check (per user's ask)**: `/architect /code /run /test /diff /undo` are all real Aider commands. `/ask` is also real. ✓ Good.
  - Nit: `/test` is shown in the Interactive Command Explorer in M0.S0 but is not present in most Aider installs by default (it's `/run pytest` or a custom command). Minor.

### Step 3.1 — "Plan-then-execute with /architect + /code" — terminal_exercise
- Briefing clarity: 4/5 | time: 5 min
- Content mostly right. But step 5 says literally run `/code` (no args) after `/architect …`. Aider's real flow: after `/architect <plan>`, Aider either proposes edits directly or you re-enter code mode and re-state. A bare `/code` with no prompt is not meaningful. Minor accuracy gap.
- Same `claude /login` lock-icon leak.
- Did not submit (exercise expects real repo state).
- Verdict: ⚠ partial.

### Step 3.2 — "Author /audit-endpoint as a reusable Aider custom command" — terminal_exercise
- Briefing clarity: 2/5 | time: 4 min (abandoned)
- **SHIP-BLOCKER**: The step claims `.aider/commands/audit-endpoint.md` with `{{ARG1}}` substitution is "Aider 0.65+ convention for custom prompt templates" and that running `/audit-endpoint orders` will invoke the template.
- **This is fabricated.** As of Aider 0.65-0.69, Aider has no built-in custom-slash-command registry with `{{ARG1}}` template substitution. What Aider actually supports: `--message-file`, shell aliases, or `.aider.conf.yml` `read:` for shared preamble text. A beginner who follows these instructions literally will create the file, type `/audit-endpoint orders`, and get "unknown command".
- The user's ask flagged exactly this: *"Are the `.aider/commands/` paths correct (vs older `~/.aider/`)?"* — neither is real.
- Verdict: ❌ stuck.

### Step 4.0 — "Agentic coding under the hood: system prompt + tools + loop" — concept
- Briefing clarity: 5/5 | time: 4 min
- Shows the real OpenAI `choices[].message.tool_calls[].function.name / arguments` shape (stringified JSON). Contrasts with Anthropic `content[].type="tool_use"`. Dispatch table is correct.
- Verdict: ✅ passed.
- **Accuracy check (per user's ask)**: "does the loop teach the OpenAI tool_use schema (function-call format) or the older completions API?" → **Yes, function-calling format. Correct.**

### Step 4.1 — "Implement harness/loop.py in ~100 lines" — terminal_exercise
- Briefing clarity: 4/5 | time: 3 min (not submitted — requires real code)
- Endpoint `https://openrouter.ai/api/v1` correct. Tool names (read_file, edit_file, run_pytest) reasonable. 10-turn budget, tool error handling, JSON-RPC style all mentioned.
- Minor: branch name `module-4-hooks` doesn't match M4 title "Loop building" (you'd expect `module-4-loop`). Low impact.
- Same `claude /login` lock-icon leak.
- Verdict: ⚠ partial.

### Step 4.2 — "Add a pre-tool guardrail: block .env / alembic/versions" — terminal_exercise
- Briefing clarity: 5/5 | time: 5 min (not submitted)
- **This is exactly what the user asked about**: "Does it include the pre-tool guardrail (block .env edits)?" **Yes**. Code uses correct OpenAI shape: `{"tool_call_id": ..., "role": "tool", "content": ...}`. Continue-on-block pattern is right.
- Verdict: ✅ content quality.

### Step 5.0 — "MCP in one page: stdio JSON-RPC, tools/list, tools/call" — concept
- Briefing clarity: 5/5 | time: 4 min
- Real MCP spec: `{"jsonrpc": "2.0", "method": "tools/list", "id": 1}` and `{"method": "tools/call", "params": {"name": ..., "arguments": ...}}` are correct. Notes that Moonshot doesn't natively speak MCP and teaches two strategies (Python adapter vs context dump). ✓
- Verdict: ✅ passed.
- **Accuracy check (per user's ask)**: "does it teach real JSON-RPC or hand-waved?" → **real JSON-RPC.**

### Step 5.1 — "Spawn team-tickets MCP and write a 50-line Python adapter" — terminal_exercise
- Briefing clarity: 4/5 | time: 4 min (not submitted)
- **SHIP-BLOCKER candidate**: clones `https://github.com/tusharbisht/aie-team-tickets-mcp` — the `aie-` prefix belongs to the AI-Engineering course (separate), not the Kimi course. The user's known repo list only calls out `kimi-eng-course-repo`. This may or may not exist under tusharbisht. Verify before ship.
- Verdict: ⚠ partial pending repo verification.

### Step 6.0 — "What 'production-grade' means for POST /orders" — concept
- Briefing clarity: 5/5 | time: 4 min
- Six pillars: Pydantic v2 `@field_validator`, Idempotency-Key + Postgres dedup, `async with session.begin()`, Testcontainers, structured logs + correlation_id, explicit `selectinload`. All correct.
- Verdict: ✅ passed.

### Step 6.1 — "Push to GHA and paste the lab-grade run URL" — system_build
- Briefing clarity: 5/5 | time: 6 min
- Four phases, clear acceptance checklist. GHA workflow `.github/workflows/lab-grade.yml` is real.
- Attempt 1 (wrong URL `http://not-a-real-url.com`) → `✗ Bad GHA run URL. Expect https://github.com/<owner>/<repo>/actions/runs/<id>.` — **exact format validation, helpful**.
- Attempt 2 (plausible but fake URL `https://github.com/learner123/kimi-eng-course-repo/actions/runs/11223344`) → `✗ GitHub API HTTP 404: {"message":"Not Found"...}` — **actually hits the live GitHub API**. Excellent implementation of real grading.
- Verdict: ✅ passed.

### Step 6.1 (alt content) — cross-course leak observed
- When my rapid hash-navigation crossed with session-expire, navigating to `#created-698e6399e3ca/23214/1` rendered a Java/Spring-Boot/Claude-Code step inside the Kimi capstone's module content area. Sidebar switched to the Java course title. Recovered by signing in and re-navigating.
- This is an SPA state-management bug, possibly exacerbated by my programmatic use of `window.location.hash = …` rather than user-clicks. Still worth flagging — beginners who browser-back or middle-click will likely hit it.

---

## Beginner-hostile flags

1. **The lock-icon info panel** appears on every terminal_exercise and **tells the learner to run `claude /login` or set `ANTHROPIC_API_KEY`**. A zero-Anthropic promise is broken in the course's most-visible reassurance banner.
2. **Paste textarea placeholder** hints at `$ claude --version` output — wrong tool for this course.
3. **M0.S2 troubleshooting accordions** recommend `npm i -g @anthropic-ai/claude-code`, reference `brew install openjdk@21`, and push learners toward the Java repo. A beginner with `aider: command not found` gets no usable help.
4. **M3.S3 teaches a feature that does not exist in Aider** (`.aider/commands/name.md` with `{{ARG1}}` templating). This is the single highest-risk content error — beginners will spend hours trying to make it work.
5. **Grader is noisy**: in M0.S1 a clearly correct answer scored 0%; a worse answer scored 7%. In M1.S1 a thorough answer scored 87% with "missing 2 of 3 expected markers" but no indication of what's missing.
6. **Hint button counts as an attempt** (burned a retry slot for clicking "💡 Hint").
7. **Scenario_branch gives no per-decision feedback** — learners can pick the worst option at every branch and still see the same closing summary.
8. **Drag-drop categorization feedback** is count-only ("6 of 8 wrong"), which is frustrating past attempt 1.
9. **Cross-course navigation**: `Next →` on a concept step inside the Kimi course carried me to a step in the Spring-Boot course. Session-expiry also drops you back on a different `created-*` hash.
10. **Item-count mismatch**: M1.S3 says "10 realistic outputs"; UI has 8.
11. **Briefing vs help mismatch**: M0.S1 expects learner to hit 401; no 401 guidance on the page. 401 guidance lives in M0.S3, one step further. Order is backwards for a beginner.

---

## Vendor neutrality check

**FAIL — course advertised as "Zero Anthropic dependency" but leaks Anthropic-CLI references in 6+ places:**

| Location | Leak |
|----------|------|
| Every terminal_exercise lock-icon banner | "Configure Claude Code with `claude /login` (or set ANTHROPIC_API_KEY in your shell)" |
| Every terminal_exercise paste-textarea placeholder | `$ claude --version\nclaude-code 1.x.x\n\n... full output goes here ...` |
| M0.S1 "command not found" accordion | Recommends `npm i -g @anthropic-ai/claude-code` |
| M0.S1 second accordion | Talks about `java`, `brew install openjdk@21` |
| M0.S1 third accordion | Tells learner to clone `jspring-course-repo` and `git checkout module-0-preflight` (wrong repo!) |
| M6.S2 (after state drift) | Full Spring-Boot / `CLAUDE.md` / `claude --help` content rendered inside a Kimi course step |

Marketing promise: "Zero Anthropic dependency." Reality: learner gets told six different ways to install/configure Anthropic's CLI. **This is the single biggest positioning risk.** If the course ships like this and a learner posts the banner screenshot to Hacker News, it becomes a meme. **Must fix before release.**

---

## Aider command accuracy spot-checks

| Command/Feature | Claim | Reality | Verdict |
|-----------------|-------|---------|---------|
| `/architect` | plan without editing | correct | ✅ |
| `/code` | edit files directly | correct | ✅ |
| `/ask` | chat without file changes | correct | ✅ |
| `/run` | shell + interpret | correct | ✅ |
| `/diff` | show pending edits | correct | ✅ |
| `/undo` | revert last edit | correct | ✅ |
| `/add <path>` | add file to chat | correct | ✅ |
| `/read <path>` | add read-only file | correct | ✅ |
| `/test` | (implied as real) | not a default; needs `--test-cmd` | ⚠ minor |
| `.aider.conf.yml` `model:` | model name | correct | ✅ |
| `.aider.conf.yml` `openai-api-base:` | base URL | correct | ✅ |
| `.aider.conf.yml` `read:` (list or string) | auto-load context | correct | ✅ |
| `.aider.conf.yml` `auto-commits: false` | disable auto-commit | correct | ✅ |
| `.aider.conf.yml` `dirty-commits: false` | disable dirty-commit | correct | ✅ |
| `.aider/commands/<name>.md` with `{{ARG1}}` | custom slash commands | **FABRICATED** — not a real Aider feature | ❌ ship-blocker |
| `/audit-endpoint orders` | invoke custom command | **FABRICATED** — consequence of above | ❌ ship-blocker |
| `--model openai/moonshotai/kimi-k2-0905` | OpenRouter model slug | correct as of 2026-04 | ✅ |
| `--openai-api-base https://openrouter.ai/api/v1` | OpenRouter endpoint | correct | ✅ |

The course's Aider surface is 90% accurate. The custom-commands step (M3.S3) is the one clean miss.

---

## Moonshot tool_use schema correctness

M4.S1 concept page shows:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "read_file",
          "arguments": "{\"path\": \"app/services/order_service.py\"}"
        }
      }]
    }
  }]
}
```

This is the **correct OpenAI-compatible tool-calls shape** as returned by Moonshot's API via OpenRouter. `arguments` is correctly shown as a stringified JSON (not an object — a common beginner trap). The response/dispatch step uses `role: "tool"` with `tool_call_id` — also correct. The Anthropic comparison table (`content[].type="tool_use"`, `content[].name`, `content[].input`, `role: "user"` with `tool_result` blocks) is accurate for Messages API.

M4.S3 guardrail code uses the same shape: `{"tool_call_id": tool_call.id, "role": "tool", "content": block_reason}` — correct.

**Verdict: Moonshot/OpenAI tool_use schema is taught correctly.** No hand-waving.

---

## Specifically-tested items (user's checklist)

1. **M0 preflight — catches OpenRouter 401 / wrong-region?** M0.S3 does cover `sk-or-` shape and OpenRouter 401. But M0.S1 doesn't — learner might hit 401 at smoke-test and get no targeted help on that page. Partial credit.
2. **M1.S1 N+1 fix — planted bug modern SA 2.0 shape?** Briefing explicitly cites "SQLAlchemy 2.0 select() style, pytest-asyncio, async" and contrasts with 1.x `query()`. M1.S3 categorization reinforces it with realistic failure modes. ✓ Good.
3. **M2 AGENTS.md — Aider convention fields correct?** `model`, `openai-api-base`, `read`, `auto-commits`, `dirty-commits` all correct. Minor: `openai-api-base` omitted from the example (should be shown explicitly). ✓ Good.
4. **M3 Aider workflows — real commands?** `/architect /code /run /diff /undo /ask /add /read` all real. `.aider/commands/<name>.md` with `{{ARG1}}` is **fabricated**. ❌ ship-blocker.
5. **M4 Loop — OpenAI tool_use vs completions?** Correct function-calling format, with pre-tool guardrail example for `.env` / `alembic/versions/`. ✓ Good.
6. **M5 MCP — real JSON-RPC?** Correct shape (`jsonrpc: "2.0"`, `tools/list`, `tools/call`, `id`, `params`). ✓ Good.
7. **M6 Capstone — Pydantic v2 + idempotency + Testcontainers + real GHA?** All pillars present. `lab-grade.yml` GHA exists. GHA URL validator actually hits GitHub API (HTTP 404 surfaced correctly). Coverage threshold: **85% not 80%** (the user's prompt said 80% — the course says 85%; 85% is stricter, reasonable). mypy is invoked as `mypy app/` without `--strict`. ✓ Good.
8. **Vendor neutrality check — any Anthropic CLI references?** **Yes, pervasive.** See Vendor neutrality section above. ❌ ship-blocker.

---

## Verdict

**❌ REJECT — CONDITIONAL on fixing the three ship-blockers below. If the blockers are fixed, this is a ⚠ CONDITIONAL pass; a beginner who makes it past the cross-course leaks and the fabricated Aider custom-commands step will learn the real substance of Aider+Kimi K2 engineering and ship a real GHA-graded capstone.**

### Top 3 ship-blockers

1. **Vendor-neutrality leaks** (highest visibility, easiest fix). Swap the shared "🔐 Your key stays on your machine…" banner template to Aider-flavoured text (`aider --openai-api-key` or `OPENAI_API_KEY` env, with `sk-or-…` example). Swap the paste-textarea placeholder from `$ claude --version` to `$ aider --version`. Swap the M0.S1 troubleshooting accordions from Claude Code / Java / Maven to Aider / Python / pip. Repo references must be `kimi-eng-course-repo`, not `jspring-course-repo`.

2. **M3.S3 fabricated Aider custom-commands** (highest correctness risk). The `.aider/commands/<name>.md` + `{{ARG1}}` templating pattern does not exist in Aider. Rewrite the step around: (a) an `AGENTS.md`-embedded checklist the learner pastes as context when running `/ask "audit the orders endpoint using the checklist in AGENTS.md"`, OR (b) a shell alias / `--message-file` workflow, OR (c) Aider's actual `/chat-mode` and conventions-file patterns. Do not ship the invented feature.

3. **Cross-course navigation bug** (single failure mode, catastrophic impression). `Next →` from a concept step inside the Kimi course jumped me to a step in the Java course. Session-expiry drops the learner on a different `created-*` hash. M6.S2 rendered a Spring-Boot/Claude-Code step inside the Kimi capstone. Either fix the router to clamp within-course, or gate every step-render with a `courseId === currentCourse` check and hard-redirect otherwise.

### Nice-to-have follow-ups (non-blocking)

- Grader quality: tell learners *which* markers they missed, not just how many.
- Scenario_branch: per-decision feedback (right/wrong + why) instead of terminal summary only.
- Categorization: per-item correctness after attempt 1 exhausted.
- Drop `/test` from the Interactive Command Explorer unless linked to `--test-cmd` config.
- Show `openai-api-base:` in the M2.S1 example AGENTS.md / `.aider.conf.yml` block — beginners will otherwise forget and 401 against api.openai.com.
- Fix M1.S3 "10 outputs" vs 8 in UI.
- Fix Hint button counting as an attempt.
- Verify `github.com/tusharbisht/aie-team-tickets-mcp` exists (M5.S2) — the `aie-` prefix suggests cross-course borrow.
- Branch name `module-4-hooks` vs module title "Loop building" — align.
