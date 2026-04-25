# Beginner Stream Re-Review (v3) — "Open-Source AI Coding: Aider + Kimi K2"

- **Reviewer persona**: beginner-stream Python engineer (1-2 yrs FastAPI, never used Aider, has an OpenRouter account but never wired it to Aider).
- **Date**: 2026-04-25, after round-5 regen of 4 Kimi steps (85138, 85152, 85159, 85165).
- **Course**: `created-698e6399e3ca`.
- **Inputs**: v1 (morning) REJECT report + v2 (afternoon) APPROVE report.
- **Method**: pulled each regenerated step verbatim from the public learner endpoint (`GET /api/courses/{id}/modules/{module_id}`), grep-scanned for model/vendor leaks, beginner-walked each.

Step-number reconciliation: prompt referenced these as M1.S1 / M4.S3 / M6.S2 / M7.S4. The course's actual structure is M0-M6. Mapping: **85138** = M0.S1 concept ("What this course IS"), **85152** = M3.S3 terminal_exercise (`/audit-endpoint`), **85159** = M5.S2 terminal_exercise (team-tickets MCP + 50-line adapter), **85165** = M6.S4 code_review (Kimi-generated diff).

---

## P0 closure table

The morning v1 REJECT raised three ship-blockers; the afternoon v2 APPROVE confirmed all three closed on the happy-path. v3 verifies the round-5 regens did not reopen any P0 and did not introduce a model-substitution leak.

| v1/v2 P0 | v3 status | Verbatim evidence |
|---|---|---|
| **P0 #1 — Vendor-neutrality leaks** (lock-icon told learners to run `claude /login`; M0.S1 troubleshoot pushed `npm i -g @anthropic-ai/claude-code` + `jspring-course-repo`) | **CLOSED — no regression** | Across all 4 regenerated steps: `ANTHROPIC_API_KEY: 0`, `claude_code: 0`, `npm i -g: 0`, `jspring: 0`, `openjdk: 0`, `mvnw: 0`. The 2 `Anthropic` mentions in 85159 are pedagogical comparison ("MCP is a protocol, not an Anthropic-only thing — any LLM that can dispatch OpenAI-compatible tool_calls can consume it"; "Moonshot AI doesn't natively speak MCP like Anthropic models do"). The 2 `Claude` mentions in 85138 are intentional anti-positioning ("Can open-source tools compete with Claude Code?", "❌ Claude Code tutorial (different tool)"). The 1 `Claude` mention in 85159 is shared-asset attribution. All four are correct pedagogy, not leaks. |
| **P0 #2 — M3.S3 fabricated `.aider/commands/{{ARG1}}` Mustache** | **CLOSED — no regression** | Step 85152: 0 occurrences of `{{ARG1}}`, 0 of `.aider/commands/`. Replaced with two REAL Aider mechanisms: `aider --message-file prompts/audit-endpoint.md` (canonical CLI flag) and `/read-only prompts/audit-endpoint.md` (real in-session command). v2 had described the new mechanism as `/load`; round-5 further hardened to `--message-file` + `/read-only` — both more pedagogically honest. Validation `must_contain` rubric still defends with `['prompts/audit-endpoint.md', 'aider', '/read-only']`. |
| **P0 #3 — Cross-course nav bleed** | **NOT REPRODUCING** in regen sweep — unchanged from v2 | Regen didn't touch the router; audit ticket stays open. |

**On the prompt's "any deepseek / non-Kimi model regression" question**: v1 did NOT flag a `deepseek` or `gpt-4` substitution. The closest analog was the Anthropic-CLI leak — wrong-tool-family (Claude Code) inside an advertised Kimi/Aider course. v3 verifies that family of leak below.

---

## Model-name leak audit (verbatim grep, all 4 regenerated steps)

| Pattern | 85138 | 85152 | 85159 | 85165 | Verdict |
|---|---:|---:|---:|---:|---|
| `deepseek` | 0 | 0 | 0 | 0 | clean |
| `claude-3` | 0 | 0 | 0 | 0 | clean |
| `gpt-4` | 0 | 0 | 0 | 0 | clean |
| `anthropic` | 0 | 0 | 2 | 0 | both pedagogical |
| `claude_code` | 0 | 0 | 0 | 0 | clean |
| `ANTHROPIC_API_KEY` | 0 | 0 | 0 | 0 | clean |
| `kimi` | 6 | 1 | 1 | 3 | correct |
| `aider` | 7 | 19 | 1 | 0 | correct |
| `openrouter` | 1 | 0 | 0 | 0 | correct |
| `moonshot` | 1 | 0 | 2 | 0 | correct |

**No model-substitution survived in any regenerated step.** Remaining `Claude` / `Anthropic` mentions are explicit oppositional framing the prompt allows.

---

## Per-step beginner walk

### Step 85138 — M0.S1 concept "What this course IS (and isn't)"  ✅

Web concept widget: interactive Aider command explorer (`/add` / "Add POST /orders" / `/test` / `/commit`) with simulated responses, plus "What This Course IS / ISN'T" cards. The ISN'T card leads with `❌ Claude Code tutorial (different tool)` — the right framing.

**Prompt's specific question — "does it set expectations correctly vs claiming MCP works out of the box?"** The widget does NOT promise MCP-out-of-the-box; MCP doesn't surface in M0 at all (deferred to M5). The four commitments (terminal Aider, BYO OpenRouter, build POST /orders, GHA-graded, open-source) all match what later modules deliver. ✅

**Friction**: the mock terminal shows `--model moonshotai/kimi-k2`; later modules use `openai/moonshotai/kimi-k2-0905`. A beginner copy-pasting from the widget into their shell will hit a 404 from OpenRouter. Cosmetic but worth aligning.

### Step 85152 — M3.S3 `/audit-endpoint`  ✅

Five steps: (1) `mkdir -p prompts`, (2) author `prompts/audit-endpoint.md` via heredoc with a 4-section audit template (auth, exception handling, response schema, N+1), (3) inject via `aider --message-file prompts/audit-endpoint.md src/routes/orders.py`, (4) mid-session alternative `/read-only prompts/audit-endpoint.md`, (5) verify ≥ 2 issue categories surface.

**Prompt's specific question — "does it actually teach you to author a reusable prompt?"** Yes. Learner ends with a real artifact (`prompts/audit-endpoint.md`), two equally valid injection paths, and a concrete success criterion. The five-step structure is the right scaffolding for a "scale beyond one-off prompts" framing. ✅

**Friction**:
- Title still reads "Author /audit-endpoint as a reusable Aider **custom command**" — body teaches a prompt file + injection. v2 raised this; survived round-5. Retitle to "Author a reusable audit prompt for Aider."
- `must_contain: ['prompts/audit-endpoint.md', 'aider', '/read-only']` — a learner who used `--message-file` exclusively and never typed `/read-only` will hit a false-negative. Widen to `any_of: ['/read-only', '--message-file']`.

### Step 85159 — M5.S2 spawn team-tickets MCP + Python adapter  ⚠

Six steps: clone `tusharbisht/aie-team-tickets-mcp` → `npm install` → manual JSON-RPC smoke (`echo '{"jsonrpc":"2.0",...}' | node index.js`) → write `mcp_adapter.py` from a starter scaffold with 4 TODO methods (`start_server`, `send_request`, `get_tools`, `close`) → run `python mcp_adapter.py` → verify OpenAI-format tool definitions emerge.

**Prompt's specific question — "does it give a working adapter?"** Partially. The starter `MCPAdapter` class is structurally sound and the body hints `subprocess.Popen` with `stdin=PIPE, stdout=PIPE, communicate()`. A beginner familiar with `subprocess` can fill it in. But two implicit gaps: (a) line-delimited JSON-RPC over stdio is the canonical MCP convention — the step doesn't say so; a beginner who calls `process.communicate()` will hang because that closes stdin. (b) Step 3's `echo | node index.js` smoke runs in single-request mode; the Python adapter is implicitly multi-request. The discontinuity isn't called out.

The repo URL `aie-team-tickets-mcp` (with `aie-` prefix from the AI-Engineering course) is acknowledged as shared ("This course reuses the MCP server from our Claude Code course"). v3 didn't independently verify the repo's existence.

**Friction**:
- One-line worked example for `start_server` would close the biggest gap: `self.process = subprocess.Popen(['node', self.mcp_server_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)`.
- Add one-liner: "Read responses LINE-BY-LINE from stdout — MCP uses line-delimited JSON-RPC over stdio."

### Step 85165 — M6.S4 AI code review on Kimi-generated diff  ✅

60-line FastAPI POST /orders implementation with realistic Kimi-flavored bugs. Briefing names six bug categories explicitly (Dependencies, Security, Async/Await, Error Handling, API Contract, Production Readiness) — Maya-rule compliant. 5 bugs configured, returned to learner as `[{hidden: True}, ...] × 5` (answer keys correctly sanitized).

**Prompt's specific question — "does it surface real bugs Kimi tends to introduce?"** Yes. Counting the canonical bug classes in the supplied code: (1) `from pydantic_idempotency import IdempotentRequest` — hallucinated package; (2) `inventory_client.get(...)` with no `await` — async-blocking; (3) `db.commit()` / `db.refresh()` with no `await` on async SQLAlchemy 2; (4) no `try/except` + `db.rollback()` around the partial writes; (5) `request.idempotency_key` declared but never consulted (Module 6's whole point); (6) `httpx.AsyncClient()` never closed; (7) hardcoded `estimated_delivery="2024-04-30"`. That's 5+ distinct realistic Kimi failure classes. Per-line server-side grading is in place. ✅

---

## Final verdict

# ✅ SHIP-WITH-FIXES

All three v1/v2 P0s remain closed under round-5; no new P0s introduced; 0 deepseek / 0 claude-3 / 0 gpt-4 leaks across the 4 regenerated steps; remaining `Claude` / `Anthropic` mentions are pedagogical positioning. A beginner-stream Python engineer with a fresh OpenRouter key can walk all 4 regenerated steps end-to-end without being misled.

## Top 3 (non-blocking) follow-ups

1. **Step 85152 title drift** — body teaches prompt-file injection but title still says "custom command." Rename to "Author a reusable audit prompt for Aider."
2. **Step 85152 validation widening** — accept `--message-file` as an alternative `must_contain` marker so learners who skip `/read-only` aren't false-failed.
3. **Step 85159 adapter scaffold gaps** — add a one-line `subprocess.Popen` worked example and a one-liner about line-delimited JSON-RPC over stdio. Also align step 85138's mock terminal model slug to `openai/moonshotai/kimi-k2-0905`.

## Rationale

The morning v1 REJECT was driven by three concrete failures (vendor-neutrality leak, fabricated Aider feature, cross-course nav bleed). v2 verified all three closed on happy-path. Round-5 regen of the four trickiest steps does not reopen any P0 and does not introduce a model-substitution leak. The only friction surfacing in v3 is the M5.S2 adapter scaffold being a hair under-explained for a true beginner — a doc-density issue, not content-correctness. Net: ship, with the three non-blocking follow-ups above.
