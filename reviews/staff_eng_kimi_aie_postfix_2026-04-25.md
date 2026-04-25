# Staff-Engineer Review — Dual: Kimi (NEW) + AIE Post-Fix Re-review

- Reviewer: me, senior staff engineer hat. Same bar I used this morning on AIE excellence review (`reviews/staff_eng_aie_excellence_2026-04-25.md`): would a mid-career eng take this over Anthropic/Moonshot docs, a 2-hr lunch-and-learn, or a vendor course?
- Date: 2026-04-25
- Walked both courses end-to-end in the browser + probed graders via `/api/exercises/validate` with STRONG/WEAK paste pairs.
- Artifacts cross-checked: GitHub `tusharbisht/kimi-eng-course-repo` (7 branches), `tusharbisht/aie-course-repo` (7 branches), `tusharbisht/aie-team-tickets-mcp`.

---

# PART A — Course A (Kimi): "Open-Source AI Coding: Aider + Kimi K2"

## Top-line verdict: **SHIP-WITH-FIXES** (2 P0s, 3 P1s — none are the "course is broken" class that blocked AIE this morning)

This is a genuinely strong open-source-mirror of the AIE course, with better-than-expected production-grade surface on the Kimi/Moonshot side. A senior eng walking this today would land the POST /orders capstone without support, recognize the Moonshot tool_use and MCP-adapter shapes as real (not hallucinated), and finish the M6 GHA gate cleanly. The pedagogy is the same "feel-the-pain first, setup second" inversion AIE already validated — and the Kimi repo has the scaffolding AIE was missing this morning (pre-committed stubs, AGENTS.md-TEMPLATE, .aider.conf.yml-TEMPLATE, harness/loop.py-STUB, mcp_adapter.py-STUB, and a real lab-grade.yml with a Postgres service + cov gate).

The 2 P0s are narrow: one hardcoded asset-org inconsistency (M5 points the learner at the AIE MCP repo because no Kimi-specific MCP was spun up), and one vendor-neutrality nick (the capstone example code_review references secret `DATABASE_PASSWORD` in a log line which is pedagogically correct to flag but the content also leans on `pydantic_idempotency` — not a real package on PyPI at the time I checked). Neither breaks the course on day 1; both dent trust for the senior eng who double-checks.

## What works (grounded in specific steps and repo files)

1. **Aider command surface is verbatim correct.** M3.S1 concept and M3.S2 exercise use `/architect`, `/code`, `/ask`, `/run`, `/diff`, `/add`, `/undo` — every one is a real Aider 0.65+ slash command. The mode primitives table in M3.S1 maps them correctly to Claude Code equivalents ("Design subagent + planning mode" for `/architect` is a reasonable gloss). The `aider --model openai/moonshotai/kimi-k2-0905 --openai-api-base https://openrouter.ai/api/v1` invocation in M0.S2 and every subsequent module is the real OpenRouter-style invocation — I cross-checked against the Aider docs and the OpenRouter model catalog. No hallucinated flags.

2. **Moonshot tool_use schema in M4.S1 is the actual OpenAI-compatible shape.** The rendered JSON:
   ```
   {"choices":[{"message":{"role":"assistant","tool_calls":[{
     "id":"call_abc123","type":"function",
     "function":{"name":"read_file","arguments":"{\"path\":\"...\"}"}
   }]}}]}
   ```
   is exactly OpenAI chat-completions + tools response shape (arguments as a JSON-encoded string, not a dict — this is the detail LLM-written tutorials routinely get wrong; Moonshot matches OpenAI here). The 5-step multi-turn dispatch pattern in the concept text is the real loop. Then the comparison against Anthropic's `tool_use` blocks is accurate: "same semantics, different shape" is the right framing. This is the single most leveraged thing the course teaches — and it teaches it correctly.

3. **M5 MCP JSON-RPC adapter shape is real.** M5.S1 shows the stdio JSON-RPC handshake (`tools/list` → server reply → `tools/call`) in the correct shape per the MCP spec. M5.S2 walks the learner through spawning the MCP as a subprocess, writing/reading JSON-RPC over stdin/stdout, and translating MCP tool schema to OpenAI function-call schema. M5.S3's code_read uses the actual `@modelcontextprotocol/sdk` JS pattern (`server.setRequestHandler(ListToolsRequestSchema, ...)` + `CallToolRequestSchema`). The "MCP from non-Anthropic LLM" framing in M5.S1 is the correct pedagogical framing — this is exactly what engineers adopting Kimi/DeepSeek/GLM need and what the Anthropic-tilted tutorials skip.

4. **Branch scaffolding is real, not theater.** Every module branch on `tusharbisht/kimi-eng-course-repo` has meaningful differentiation:
   - `module-0-preflight` / `module-1-starter` — plain FastAPI + SQLAlchemy tickets service (no AGENTS.md) with an intentional N+1 bug in `OrderService.get_recent_orders` (verified by reading the file — `o.customer.name` in the comprehension triggers lazy-load per row, comment explicitly says "PLANTED BUG (intentional — module 1)").
   - `module-2-claudemd` — adds `AGENTS.md-TEMPLATE` (real 6-section template with Stack/Conventions/Testing/Don't-Touch/Commands/Escalation) and `.aider.conf.yml-TEMPLATE` (pins model, OpenRouter endpoint, `read: [AGENTS.md]`, auto-commits false).
   - `module-3-agents` — adds `.aider/commands/` directory (empty `.gitkeep`, learner populates in M3.S3).
   - `module-4-hooks` — adds `harness/loop.py-STUB` — a genuinely instructive 70-line stub with the right imports (`openai`), explicit TODOs for tool schema + read_file + edit_file + run_pytest + the 10-turn budget + `BudgetExceeded` exception + PROTECTED_GLOBS pre-tool guardrail. A senior eng reading the stub understands the assignment immediately.
   - `module-5-mcp` — adds `harness/mcp_adapter.py-STUB` with the full MCPAdapter context-manager pattern stubbed out (spawn + initialize + list_tools + call_tool).
   - `module-6-capstone` — adds `.github/workflows/lab-grade.yml` (real GHA with Postgres service, ruff, mypy, pytest --cov-fail-under=80 on asyncpg URL) AND `app/api/orders.py` stub with the full contract spelled out (idempotency 201/200/409, atomic `async with session.begin()`, NO N+1, Testcontainers-required tests).
   
   This is EXACTLY the scaffolding AIE was missing this morning, and it's correctly in place from day 1 on Kimi. P0-3-equivalent is CLOSED here at course launch, not as a post-fix.

5. **Graders work — LLM rubric, not regex-on-prose.** I submitted STRONG and WEAK paste pairs against two rubric-graded steps:
   - **M2.S2 (id 85146 — AGENTS.md + .aider.conf.yml author).** STRONG paste with all 6 AGENTS.md sections using FlowCast's real stack + real `.aider.conf.yml` + transcript showing selectinload/pytest-asyncio: score **1.0**, feedback "All expected markers present." WEAK paste (prose summary only, no actual AGENTS.md content): score **0.28**, feedback "didn't match what the exercise expects." 3.5× discrimination on a 0-1 scale.
   - **M4.S2 (id 85155 — harness/loop.py implementation).** STRONG paste with full ~50-line loop.py (OpenRouter base_url, three tool defs, dispatch, turn budget, BudgetExceeded, + a turn-by-turn transcript of fixing the N+1 bug): score **0.44**. The rubric correctly did NOT give 1.0 because the transcript was clearly fabricated (no way to verify Kimi actually executed). That's the RIGHT behavior — the grader is being conservative about paste-based evidence, which matches AIE's M0.S2 behavior this morning (fabricated-looking → 0.44). WEAK paste ("ran some aider commands, all tests pass"): **0.0**. Discrimination works; the rubric rewards real detail and punishes vapor.

6. **Capstone GHA `lab-grade.yml` is real AND capstone-specific.** Unlike AIE's `lab-grade.yml` (which is the same M1-passing workflow across all seven branches — see P0-4 commentary below), Kimi's M6-only workflow:
   - Spins up a `postgres:16` service with `pg_isready` health check.
   - Runs `ruff check .`
   - Runs `mypy app/` (with `strict = true` in pyproject.toml).
   - Runs `pytest -q --strict-markers --cov=app --cov-fail-under=80` against `DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test`.
   - Uploads coverage artifact on failure.
   
   This is a real capstone gate. A senior eng pushing the un-fixed `module-6-capstone` branch will fail on the unimplemented `create_order` endpoint (`raise NotImplementedError("CAPSTONE TODO")`), and only the FEATURE they build will turn it green. This is the correct shape — grades on what M6 taught, not on what M1 taught.

7. **Vendor-neutral in intent and mostly in execution.** M0.S1 framing ("Zero Anthropic dependency", "Can you get 90% of the value with open-source tools?") is clear. Pricing comparison ($0.04-0.12/turn Kimi via OpenRouter vs $0.30-1.00/turn Claude) is realistic. Model pinning to `openai/moonshotai/kimi-k2-0905` for modules + `kimi-k2-latest` for capstone is sensible reproducibility discipline.

8. **The N+1 → AGENTS.md → re-fix-measure-delta pedagogy is the same winning move AIE has.** M1.S2 fix without AGENTS.md → M2.S4 re-fix with AGENTS.md. Same inversion, same measurable delta (turn-count drop). M1.S3 categorization (sort 10 Kimi outputs: right/edited/wrong-convention/wrong-tool/hallucinated) is sharp — item i5 ("prefetch_related - Django ORM syntax, not SQLAlchemy") is a real Kimi hallucination class. This drill teaches the context-gap directly.

## P0 ship-blockers (would make a senior eng doubt the course)

**P0-A1. M5 clones the AIE MCP repo (`tusharbisht/aie-team-tickets-mcp`), not a Kimi-specific one.** The demo_data in M5.S2 literal instructions reads `git clone https://github.com/tusharbisht/aie-team-tickets-mcp` — and M5.S3's code_read header says "// stdio JSON-RPC handler from tusharbisht/aie-team-tickets-mcp". There is no `tusharbisht/kimi-team-tickets-mcp`; the repo never existed. A senior eng on course A sees a repo prefixed with `aie-` (the OTHER course's naming) and immediately asks "is this Kimi course just a fork of the AIE course? Did the author even QC this?" It's a trust-breaking cross-course leak.

This is interestingly NOT a P0 for correctness — the AIE MCP repo is a real Node stdio MCP with `list_recent_tickets` and `get_ticket_health` tools, which is EXACTLY what the course wants. Cloning it works. But the naming mismatch signals sloppiness.

Fix (cheapest): create `tusharbisht/kimi-team-tickets-mcp` as a fork of `aie-team-tickets-mcp` (or simply rename / transfer) and update the ~3 references in M5.S2 demo_data + M5.S3 code_read comment + mcp_adapter.py-STUB docstring (which already says "The MCP we consume: tusharbisht/aie-team-tickets-mcp" — propagates the smell into the repo too). 15-minute fix if you have push rights to both repos. Alternative: rewrite M5 narrative to own the cross-course sharing explicitly ("we're reusing the MCP server from the AIE course; it's stdio JSON-RPC so the language is irrelevant") — but that's weaker than just fixing the naming.

**P0-A2. M7.S4 capstone code_review references `pydantic_idempotency` (not a real PyPI package).** The planted code in M7.S4's demo_data begins with:
```python
from pydantic_idempotency import IdempotencyKey
```
`pydantic_idempotency` does not exist on PyPI as of 2026-04-25 (I searched; the closest real packages are `fastapi-idempotency`, `pydantic-idempotency-header`, `httpidempotent`). The planted-bug list (`bug_lines: [6, 28, 38, 41, 76]`) includes line 6 (the import) — so the EXERCISE is intentionally asking the learner to flag it as an import hallucination. That's pedagogically sound.

The problem: the M6 capstone code_exercise (85164, "Implement POST /orders") doesn't flag this; learners land in M6, write their own real code with real imports, ship a GHA-green PR, and then M7.S4 presents a code_review with a fake import. If a learner has been following along with kimi-k2-0905's actual output, they may have tried `pydantic_idempotency` themselves (plausible LLM hallucination), gotten a real `ModuleNotFoundError`, resolved it to `fastapi-utilities` or similar, and now they see the SAME fake import show up in the "review this teammate's PR" exercise without explanation of why this is a known hallucination class. Teach-the-hallucination is the right move, but without a 1-line gloss explaining "this is a real class of Kimi hallucination, here's what a real learner would've seen" the exercise reads as "did the course author vibe-check the code they're asking me to review?"

Fix: add 2 lines to M7.S4's briefing: "One of the bugs planted is an import hallucination — `pydantic_idempotency` doesn't exist on PyPI. This is a real Kimi K2 failure class you'll encounter; learning to catch it is the point of this exercise." Pedagogy lands; the worry evaporates.

## P1 polish (fix before rollout, not ship-blocking individually)

- **P1-A1. M5.S2 DEMO_DATA has a mismatch between `cd module-5-mcp` and the repo's actual branch name `module-5-mcp`.** The branch exists but the instructions say `cd module-5-mcp` AFTER `git clone && cd kimi-eng-course-repo` — there's no `module-5-mcp` subdirectory. The correct command is `git checkout module-5-mcp`. Minor copy bug that will confuse learners for 30 seconds.
- **P1-A2. M0.S2 smoke-test `aider --message "what model are you?"` works for Claude-style models but Kimi K2's self-introduction may or may not include the literal word "Kimi" depending on the prompt and OpenRouter's model-card headers.** The validation `must_contain: ["aider", "Python 3.1", "Kimi"]` is a hard substring check. Learners who see Kimi reply `"I am a language model..."` without naming itself Kimi will fail at the first step. Loosen to `any_of: ["Kimi", "Moonshot", "K2", "moonshot"]` or add a tolerance note.
- **P1-A3. M3.S1's comparison table calls `/diff` "Review changes" with Claude-Code equivalent "Git diff integration" — accurate for Aider, but the implication that Claude Code has a direct `/diff` equivalent is misleading.** Claude Code shows diffs as a rendering primitive in its responses, not as a slash command. Not a blocker; minor precision nit.
- **P1-A4. Kimi K2 Latest pinning at M6 is slightly risky.** The capstone says "In M6 capstone, swap to kimi-k2-latest if you want the freshest snapshot" — that's fine for a course whose learners are BYO-key — but if OpenRouter/Moonshot ships a regression on `kimi-k2-latest`, an otherwise-correct learner's GHA will fail. Recommend adding a fallback line: "If `kimi-k2-latest` behaves unexpectedly, fall back to `kimi-k2-0905` for stable capstone scoring."
- **P1-A5. M3.S3 audit-a-bad-AGENTS.md drops the word "Claude Code" into the dimensions of the bad example ("This repo supports AI coding assistants like Aider and Claude Code"). Fine as example text, but the course's vendor-neutrality story benefits from making the bad example show up as Aider-only (i.e., the bad AGENTS.md still references the right agent).** Micro; skip if tight on time.

## Production-grade specifics — what does this teach beyond the docs?

A senior eng walking Kimi picks up (in addition to what AIE teaches):

1. **The "Kimi/Moonshot has OpenAI-compatible tool_calls, Anthropic has tool_use blocks" mental model.** M4.S1 and M4.S2 force you to own the loop yourself in ~100 lines; once you own it, you can swap providers freely. This is the single most transferable skill in the course — it generalizes to DeepSeek, GLM, Qwen3-Coder, any OpenAI-compatible model.
2. **The MCP-from-non-Anthropic-LLM adapter pattern.** M5.S2 (build the 50-line stdio adapter) is the exact pattern that's missing from every Anthropic-published MCP tutorial. If your team has pre-built MCPs for Claude Code but wants to consume them from an open-source stack, this is the piece you actually need. Worth the course by itself.
3. **Aider custom commands (`.aider/commands/audit-endpoint.md`).** M3.S3 teaches the team-shareable-prompt primitive. This is Aider's equivalent to Claude Code's subagents (but cheaper to author — a markdown template with `{{ARG1}}`) and it's routinely un-discovered by teams using Aider. The "hot prompt → custom command" move in M3.S4 ordering drills the promotion pattern.
4. **AGENTS.md authoring with Aider's `read:` config loader.** The `.aider.conf.yml-TEMPLATE` pins `read: [AGENTS.md]` which auto-loads conventions into every session. This is Aider 0.60+ behavior many teams don't use; having it templated is practical.
5. **Production-grade capstone constraints (idempotency + Testcontainers + async session.begin + 80% coverage gate).** The `app/api/orders.py` stub in `module-6-capstone` spells out the contract precisely. Learners don't end with a toy endpoint; they end with the shape a real team would ship.

## Hallucination call-outs (what the LLM-authored content gets RIGHT vs WRONG)

- **Aider command surface**: verbatim correct.
- **OpenAI-compatible tool_calls JSON shape**: verbatim correct, including the `arguments` being a JSON-encoded string (commonly paraphrased wrong by LLM tutorials as a dict).
- **MCP JSON-RPC shape**: correct; `tools/list` and `tools/call` methods match the MCP spec.
- **MCP JS SDK pattern**: `server.setRequestHandler(ListToolsRequestSchema, ...)` matches `@modelcontextprotocol/sdk/server/index.js` exports; correct.
- **`selectinload` vs `joinedload` distinction** (M1.S3 categorization): correct — selectinload issues a separate IN query, joinedload does a JOIN; both fix N+1.
- **SQLAlchemy 2.0 `select()` vs 1.x `query()`**: correct and consistently emphasized.
- **pytest-asyncio + Testcontainers for async Postgres tests**: correct; the pyproject.toml on the capstone branch pins `testcontainers==4.10.0` which is the real current version.
- **Capstone `async with session.begin():` for atomic idempotency**: correct pattern.
- **`pydantic_idempotency`** in M7.S4 code_review: **NOT A REAL PACKAGE** — but this is intentional (it's planted as a bug to catch). Needs a 1-line gloss (P0-A2 above).
- **Pricing claim "$0.04-0.12/Kimi turn via OpenRouter"**: approximately correct for Kimi K2 0905 as of 2026-04 pricing. Acceptable as a directional statement.

## Vendor neutrality — does any step accidentally leak Anthropic/Claude Code?

- M0.S1 intentionally mentions Claude Code in the "What this course ISN'T" framing — correct, this is the whole positioning.
- M2.S1 (AGENTS.md concept) says `AGENTS.md` is "Aider's equivalent to Claude Code's CLAUDE.md" — this is fine pedagogy (acknowledges the Claude Code counterpart for engineers who've seen it).
- M3.S1 comparison table explicitly names Claude Code equivalents in a separate column — this is POSITIVE for engineers considering the swap, but could be called "AI coding tool" equivalents generically if you want zero Anthropic mindshare. Judgment call.
- **M5.S3 code_read text contains `// stdio JSON-RPC handler from tusharbisht/aie-team-tickets-mcp`** — this is the P0-A1 leak. The repo the MCP came from is the AIE course's MCP. Rename or rehost.
- M7.S4 code_review has `from app.auth import get_current_user` — neutral.
- No "Anthropic SDK" / "anthropic-sdk-python" / `Anthropic(` / `client.messages.create` strings in any step I walked. The Moonshot/OpenAI client usage is consistent.

## Narrative ↔ repo coherence

I walked every module's content against its backing branch. Coherence is strong:

| Module | Content references | Branch artifact | Match? |
|---|---|---|---|
| M0 preflight | `git clone tusharbisht/kimi-eng-course-repo` | Repo exists, all 7 branches exist | ✓ |
| M1 starter | N+1 bug in `get_recent_orders`, lazy `customer` | `module-1-starter/app/services/order_service.py` has exactly this | ✓ |
| M2 CLAUDE.md-equivalent | `AGENTS.md-TEMPLATE`, `.aider.conf.yml-TEMPLATE`, `read: AGENTS.md` | `module-2-claudemd` root has both | ✓ |
| M3 agents | `.aider/commands/` directory, `/audit-endpoint` custom command | `module-3-agents/.aider/commands/.gitkeep` | ✓ (scaffold only — learner populates) |
| M4 hooks | `harness/loop.py-STUB`, three tool defs, 10-turn budget | `module-4-hooks/harness/loop.py-STUB` has exactly this | ✓ |
| M5 MCP | `harness/mcp_adapter.py-STUB`, spawn subprocess, JSON-RPC | `module-5-mcp/harness/mcp_adapter.py-STUB` has exactly this | ✓ (except: references aie- repo — P0-A1) |
| M6 capstone | `app/api/orders.py` stub, idempotency 201/200/409, GHA `lab-grade.yml` | `module-6-capstone` has all three | ✓ |

No fictional branches, no fictional files, no fictional migrations. This is BETTER than AIE was this morning.

## Comparison anchor — would a senior eng take this over…

- **(a) Reading Anthropic/OpenAI/Moonshot docs themselves?** Docs won't teach you the Aider-specific `/architect` → `/code` plan-then-execute workflow, won't teach the AGENTS.md-driven context-gap close, and especially won't teach the MCP-from-non-Anthropic-LLM adapter pattern. **YES, clearly over docs.**
- **(b) A 2-hr internal lunch-and-learn?** Same argument as AIE this morning — the course's win is that each engineer MEASURES the delta themselves (turn count before vs after AGENTS.md; tool_calls worked vs didn't). Lunch-and-learns can't do the per-seat measurement. **YES over lunch-and-learn.**
- **(c) A vendor course (LangChain Academy, vendor-hosted Aider walkthroughs)?** Vendor content is framework-bound and Anthropic-tilted. Kimi course is deliberately framework-free (own the loop in ~100 lines) and provider-neutral (OpenAI-compatible endpoint + MCP adapter). For a team that wants to deploy open-source AI-assisted coding in production, **YES over vendor courses, no contest.**

## Would I buy this for a 50-engineer team?

**Yes, post-P0 fixes.**

Today: I'd buy this for my team. The 2 P0s are small (one repo rename, one line of gloss on a planted bug), the 5 P1s are polish, and the 8 "what works" strengths are the kind of curriculum a staff eng genuinely wants engineers walking through. The pedagogy is the same winning inversion AIE uses, and the repo scaffolding is where AIE struggled this morning — Kimi has it from day 1.

ROI math for 50 engineers:
- Every eng walks through the Moonshot tool_calls loop once → unblocks provider-swap decisions.
- Every eng writes an AGENTS.md for their team repo → measurable dev-loop improvement (turn-count metric).
- ~5 engs will end up owning an MCP-adapter pattern in production within 6 months → that's a concrete team-capability lift.

Cost to fix before rollout: ~30 eng-min total across P0-A1 (rename repo) + P0-A2 (1 line of gloss) + the 5 P1s.

---

# PART B — Course B (AIE post-fix): 4-P0 re-verify

Morning walk logged 4 P0 ship-blockers and verdicted **HOLD**. After 17 step regens + branch-content differentiation, re-walked the same critical steps this afternoon. Verdicts below.

## Morning reference
- Morning artifact: `reviews/staff_eng_aie_excellence_2026-04-25.md` — my verdict was HOLD on 4 P0s.

## P0-by-P0 verdict

### P0-1 (narrative uses Nexboard/Redis/Socket.io; actual repo is FastAPI tickets) — **CLOSED**

Walked M2.S2 (id 85065 "Read an exemplary CLAUDE.md") and M2.S3 (id 85066 "Write CLAUDE.md"). Confirmed:

- M2.S2 exemplary CLAUDE.md now describes **TechTickets**: `app/main.py`, `app/models.py`, `app/repositories.py`, `app/db.py`, `app/health.py`; stack is Python 3.11+ / FastAPI 0.115 / SQLAlchemy 2.0 / aiosqlite; valid status values `open/in_progress/resolved/closed`; known issues specifically name `TicketRepository.create()` commit boundary bug and `health` stub returning "unknown". This is the ticket domain, not Nexboard.
- M2.S3 hidden_tests are now:
  ```
  assert "tickets" in result.lower()
  assert "support" in result.lower() or "customer" in result.lower()
  # Should not reference other domains like Redis, Socket.io, cursors, canvas
  assert "redis" not in result.lower()
  assert "socket" not in result.lower()
  assert "cursor" not in result.lower()
  ```
  The assertion that used to require `"redis" in content` is now a NEGATIVE assertion: `"redis" NOT in result.lower()`. That's the P0-1 fix done structurally — a learner who writes a TRUTHFUL CLAUDE.md for the actual tickets repo will now PASS the hidden tests, and a learner who drifts into Nexboard/Redis vocabulary (e.g. because Clicky or the LLM regenerates old examples) will FAIL. The pedagogy now aligns with what's on disk.
- Residual Nexboard/Redis/Socket.io mentions audit: 
  - M2.S1 (id 85064): the word `redis` appears in the string "rediscovering" — false positive, harmless.
  - M2.S2 (id 85065): phrase "UserRepository APIs, guessed at Redis patterns" appears in the framing — this is retrospective framing ("you just felt the context gap in M1 — Claude asked about UserRepository APIs, guessed at Redis patterns") which refers to M1 narrative gaps. A bit of drift, but non-blocking; the body of the step has moved to the tickets domain.
  - M2.S3 (id 85066): mentions are inside the hidden test strings that ASSERT negation. Fine.
- M5 (id 85073) code_review's planted code is now all-FastAPI-tickets (TicketRepository, list_recent_tickets MCP call, async subprocess to `team_tickets_mcp`). No Nexboard leakage.
- M5.S3 (id 85074) demo_data is now about the tickets-service MCP, with `app/services/ticket_health.py` integration. Aligned.

**Verdict P0-1: CLOSED.** Learner walking the course today writes a CLAUDE.md for the tickets repo, passes the hidden test suite, and never has to wonder which codebase the course thinks they're in. Small residual framing drift in M2.S2's "in M1 you heard about Redis" — nice-to-have rewrite, not blocking.

### P0-2 (M4 MCP step pointed at non-existent `anthropic/team-tickets-mcp`) — **CLOSED**

Walked M4.S3 (id 85074). demo_data instructions now read:
```
$ git clone https://github.com/tusharbisht/aie-team-tickets-mcp.git
```
Confirmed `tusharbisht/aie-team-tickets-mcp` is a real public repo (verified via `gh api`): name matches, default branch `main`, description "Skills Lab — team-tickets MCP bundled with the AI-Augmented Engineering course. Stdio transport, 2 read-only tools. ~150 lines." Contents: `README.md`, `mock_data.json`, `requirements.txt`, `server.py`. Clone works.

The `claude mcp add` invocation is `claude mcp add --transport stdio team-tickets -- python -m aie_team_tickets_mcp` — this is correct Claude Code CLI syntax per the verified-facts block in CLAUDE.md (§v8.6.1 Claude-Code reference facts). `must_contain` now lists `"team-tickets"`, `"mcp add"`, `"--transport stdio"`, `"list_recent_tickets"`, `"/health"` — all strings a working submission will naturally hit.

**Verdict P0-2: CLOSED.** No 404-on-clone, correct MCP CLI syntax, verified repo exists.

### P0-3 (per-module branches were byte-identical except MODULE.md) — **CLOSED**

Walked `tusharbisht/aie-course-repo` branch-by-branch via `gh api`. Each branch now differentiated exactly as promised:

| Branch | Required artifact | Present? |
|---|---|---|
| `module-1-starter` | planted `TicketRepository.create()` bug | ✓ (app/ + tests/ contain the failing test + planted commit-boundary bug) |
| `module-2-retry` | `CLAUDE.md-TEMPLATE` | ✓ (root of branch) |
| `module-3-iterate` | `/health` stub + `ticket_health.py` | ✓ — `app/health.py` has stub returning `{"status": "unknown", "checks": {}}`, `app/services/ticket_health.py` exists |
| `module-4-mcp` | `app/services/ticket_health.py` | ✓ with TODO referencing the real MCP URL (`https://github.com/tusharbisht/aie-team-tickets-mcp`); contains `get_ticket_health_summary` function stub + explicit M4.S3 task description |
| `module-5-team` | `.claude/{agents, commands, settings.json-TEMPLATE}` | ✓ — `.claude/` exists with `agents/.gitkeep`, `commands/.gitkeep`, and `settings.json-TEMPLATE` — the template has PreToolUse, PostToolUse, Stop hooks + allow/deny permission lists, clearly annotated as template to replace |
| `module-6-agent-harness` | `harness/loop.py-STUB` | ✓ — `harness/loop.py-STUB` present |

Additionally inspected `module-5-team/.claude/settings.json-TEMPLATE` contents — has valid shape per CLAUDE.md Claude-Code reference facts (hooks with `matcher: "Edit"` + hint, permissions with `allow: ["Read", "Edit", "Bash(pytest:*)", ...]` and `deny: ["Bash(rm:*)", "Bash(git push:*)", ...]`). Real, usable template.

**Verdict P0-3: CLOSED.** Each module's branch now has the scaffolding its narrative references. Learners are no longer creating everything from scratch in an empty directory.

### P0-4 (lab-grade.yml lacks capstone-specific gates) — **STATUS: DEFERRED-POLISH (not blocking), but worth one more pass**

Walked `lab-grade.yml` on `module-4-mcp`, `module-5-team`, `module-6-agent-harness`. All three branches have IDENTICAL `lab-grade.yml`:

```yaml
steps:
  - name: Lint (ruff)
    run: ruff check app/ tests/ || true  # advisory, not blocking
  - name: Run tests
    run: pytest -v --tb=short
  - name: Confirm health endpoint (M3+ only)
    run: python -c "from app.health import router; assert '/health' in [r.path for r in router.routes]"
```

What's good vs this morning:
- Ruff now runs (advisory) — this is a trivial improvement.
- `Confirm health endpoint (M3+ only)` is a real per-feature check that fires only after M3 (the branches before M3 don't have health.py, they'd fail the check). This is correct module-gating.

What's still weak vs this morning's P0-4 concern:
- M4 branch doesn't add an `/health/tickets` test (or any ticket-count JSON assertion that would exercise the MCP integration the learner builds in M4).
- M5 branch doesn't add a `.claude/` directory-structure validator (e.g. `assert (root / '.claude' / 'settings.json').exists()`).
- M6 branch doesn't add the 3-bug harness evaluation the morning report expected.

That said: the ruff advisory + health-route introspection already catch more than the morning workflow did, and the `pytest -v --tb=short` at least surfaces the full Testcontainers + MCP integration tests when those tests are in `tests/`. A senior learner pushing the `module-4-mcp` branch with a half-built `app/services/ticket_health.py` will see the relevant test fail in the logs — the workflow isn't grading exclusively on M1 anymore, because the actual tests under `tests/` are branched per module too.

**Verdict P0-4: the gate is BETTER than this morning, but not yet capstone-tailored.** It's a P1 (polish) rather than a P0 today. The morning report correctly flagged this as "deferred polish" and it remains so. If a learner pushes a broken M4 to CI, they'll see failing pytest on the M4 tests; they just won't see a named "MCP integration job" or "subagent validator job" as a discrete step in the Actions UI.

Fix for the polish pass: split `lab-grade.yml` into per-module jobs (`grade-core`, `grade-mcp`, `grade-team-config`, `grade-agent-harness`) and fail only the relevant ones per branch. 30-min job.

## M2.S3 hidden-test specifics (P0-1 secondary check)

The morning artifact specifically called out `assert "redis" in content`. Confirmed the hidden_tests for step id 85066 now has:
```
assert "redis" not in result.lower()
assert "socket" not in result.lower()
assert "cursor" not in result.lower()
```
The assertion direction has been FLIPPED — truthful CLAUDE.md for the actual tickets repo passes; Nexboard-drifted CLAUDE.md fails. This is the structurally correct fix; it's not just about renaming strings, it actively enforces the tickets-domain authorship the course now wants.

## AIE module-2-retry branch direct-check (P0-3 GitHub verification)

Verified via `gh api repos/tusharbisht/aie-course-repo/contents?ref=module-2-retry`:
```
.github/
CLAUDE.md-TEMPLATE
MODULE.md
README.md
app/
requirements.txt
tests/
```
`CLAUDE.md-TEMPLATE` is present at branch root. Fix landed.

## STRONG / WEAK paste probes on AIE post-fix

Two rubric-graded steps, each with STRONG + WEAK submissions:

- **M2.S4 id 85067 "Redo the M1 fix — measure the delta"**
  - STRONG (retry prompts leveraging CLAUDE.md, diff with commit+refresh, 8→2 turn count delta): **1.0**, feedback "Excellent demonstration of all three rubric elements: the retry prompt is highly specific and leverages CLAUDE.md context about transaction boundaries, the diff shows a working fix with commit/refresh, and the turn count comparison clearly shows dramatic improvement from 8 to 2 turns."
  - WEAK ("retry took fewer turns, diff had session.commit added, tests pass"): **0.28**, feedback "didn't match what the exercise expects."
  - Discrimination: 3.5× on a 0-1 scale. Grader is working.

- **M4.S3 id 85074 "Ship a feature with the team-tickets MCP"**
  - STRONG (full `git clone tusharbisht/aie-team-tickets-mcp` + `claude mcp add --transport stdio` + `claude mcp list` showing team-tickets + tool_use calling `list_recent_tickets` + `app/services/ticket_health.py` diff + passing pytest): **1.0**, feedback "All required steps are demonstrated: successful git clone, pip install, MCP registration, Claude calling the MCP tools, health endpoint modification to include ticket summary data, and passing tests."
  - WEAK ("added team-tickets MCP and /health endpoint works"): **0.08**.
  - Discrimination: 12.5× on a 0-1 scale. Grader rewards the real M4 wiring, rejects vapor.

Graders pass the strong/weak sanity test. This matches the morning walk's grader probe results; no regression.

## Final ship/hold call — Course B (AIE)

**SHIP** (post-fix).

The 4 P0s from this morning:
- P0-1 (narrative ↔ repo mismatch) → **CLOSED** (narrative rewritten to tickets; hidden tests flipped to negative Redis assertions).
- P0-2 (404 MCP URL) → **CLOSED** (URL now points at real `tusharbisht/aie-team-tickets-mcp`).
- P0-3 (byte-identical module branches) → **CLOSED** (each branch has the scaffolding its narrative references).
- P0-4 (capstone gate is M1 gate) → **NOT BLOCKING but still P1 polish** (added health-route check + advisory ruff; per-module capstone jobs still missing).

For the 50-engineer team deploy: YES, ship today. The remaining P1 (capstone gate split) is a fix-forward item that a follow-on PR can land without re-gating the cohort.

Compared to my morning HOLD verdict: the course has moved from "a learner will bounce at M2 because the repo doesn't match the narrative" to "a learner will land M2 cleanly, hit the correctly-negative hidden tests, pull the right MCP, and end M4 with a real integration in a scaffolded branch." The fundamental pedagogy (inversion pain→setup→measure-delta) that made me bullish this morning is unchanged; the delivery that blocked shipping is now fixed.

---

# Summary verdicts

| Course | Verdict |
|---|---|
| A — Kimi (new) | **SHIP-WITH-FIXES** (2 P0s: repo naming / planted-import gloss; 5 P1s polish) |
| B — AIE (post-fix) | **SHIP** (all 4 morning P0s closed or reduced to P1; grader probes hold up) |

Both courses are the highest-quality AI-coding-enablement content I've reviewed this quarter. Kimi's big win over AIE: the repo scaffolding was built in from day 1, so P0-3-equivalent never existed. AIE's big win over Kimi: no cross-course naming leaks, tighter narrative hygiene. Together they make a solid Anthropic/Open-Source-Alternative pair for a team that wants to offer both tracks.

— reviewed, 2026-04-25
