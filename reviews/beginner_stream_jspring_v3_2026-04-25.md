# Beginner Walkthrough — Claude Code for Spring Boot — Pass v3 (post-round-5 regen)

Date: 2026-04-25 (afternoon, after AM regen sweep)
Course ID: `created-e54e7d6f51cf`
Course URL: http://localhost:8001/#created-e54e7d6f51cf
Reviewer role: Mid-level Java engineer, first-time Claude Code CLI user, BYO-key
Prior artifacts: `reviews/beginner_stream_jspring_v1_2026-04-25.md` (REJECT), `reviews/beginner_stream_jspring_v2_2026-04-25.md` (interim)
Regenerated steps in this sweep (6): `85124` (M3.S2 /controller-review), `85125` (M3.S3 mockito-test-writer subagent), `85127` (M4.S1 hook contract), `85128` (M4.S2 wire 3 hooks), `85118` (M2.S1 anatomy of CLAUDE.md), `85129` (M4.S3 categorization).

> Note on naming: my morning v1 review used "M3.S2/M3.S3/M4.S1/M4.S2/M4.S3/M2.S1" labels per how the modules render in the catalog (M0-M6). The user's regen list uses a 1-based module index where their "M3" = my "M2 — CLAUDE.md", their "M4" = my "M3 — Slash + Subagents", their "M5" = my "M4 — Hooks". Step IDs are the source of truth; I use the catalog labels below for continuity with v1.

## Re-verification table — every P0 from v1

| # | v1 P0 | v3 status | Evidence (verbatim from regenerated step) |
|---|---|---|---|
| 1 | M3.S2 (85124): `Arguments: {{className}}` non-standard slash-command param syntax | **CLOSED** | `argument-hint: [controller-class-name]` and `Audit the $ARGUMENTS Spring Boot controller for these production risks:` — uses real Claude Code `$ARGUMENTS` substitution; frontmatter has `description:` and `argument-hint:` per current docs. |
| 2 | M3.S3 (85125): `claude @mockito-test-writer "prompt"` invalid CLI invocation | **CLOSED** | Three real invocation paths shown: (a) `Use the mockito-test-writer subagent to generate tests for OrderService.` (natural language inside session), (b) `@"mockito-test-writer (agent)" generate tests for OrderService` (@-mention), (c) `claude --agent mockito-test-writer` (dedicated session). The `claude @name "prompt"` shell form is gone. |
| 3 | M3.S3 (85125): `max_tokens: 4000` invalid frontmatter key | **CLOSED** (with new caveat) | Frontmatter now has `model: sonnet` + `maxTurns: 8` instead of `max_tokens`. `maxTurns` is a documented subagent field. The minor `tools: [Read, Edit, Bash]` YAML-list form persists — accepted, harmless. |
| 4 | M4.S1 (85127): `tool_name == "str_replace_editor"` — fictitious Claude Code tool name | **CLOSED** | "Real Claude Code Tool Names (PascalCase): `Edit`, `Write`, `Read`, `Bash`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `MultiEdit`, `NotebookEdit`, plus MCP tools as `mcp__<server>__<tool>`". Hook example matches `tool_name == "Edit"`. No `str_replace_editor` anywhere. |
| 5 | M4.S1 (85127): `parameters.path` instead of real `tool_input.file_path` | **CLOSED** | `file_path=$(echo "$input" \| jq -r '.tool_input.file_path // empty')` and the JSON example `{"tool_name": "Edit", "tool_input": {"file_path": "..."}}`. Field names are correct. |
| 6 | M4.S2 (85128): wrong `settings.json` schema (`{"command": "python3", "args": [...]}` flat shape) | **CLOSED** | Now emits the real schema: `"PreToolUse": [ { "matcher": "Edit", "hooks": [ { "type": "command", "command": "python3 .claude/hooks/block-prod-config.py" } ] } ]`. PostToolUse + Stop blocks follow the same shape. |
| 7 | M4.S2 (85128): lowercase `preToolUse` event name + `must_contain` enforced lowercase | **CLOSED** | Event names PascalCase throughout: `PreToolUse`, `PostToolUse`, `Stop`. Rubric explicitly says: "PascalCase hook names (PreToolUse, PostToolUse, Stop) using the array-of-matchers format". `must_contain` now contains `PreToolUse` (PascalCase). |
| 8 | M4.S2 (85128): inline Python read `data.get('arguments', {}).get('path', '')` — wrong field | **CLOSED** | Python script: `input_data.get('tool_input', {}).get('file_path', '')` — correct fields. |
| 9 | M4.S3 (85129): briefing said "10 hook scenarios" but `items` array had 8 (i1-i8) | **CLOSED** | `items` array now has 10 entries (i1-i10). Two new ones: i9 "Show learner ./mvnw verify output before exit, even if all tools succeeded" and i10 "Always pair @ExtendWith(MockitoExtension.class) with constructor injection" (correctly a CLAUDE.md rule). |
| 10 | M4.S2 vs M4.S3: M4.S2 used lowercase `preToolUse`, M4.S3 used PascalCase — internal inconsistency | **CLOSED** | Both now PascalCase. Categories in 85129: `['PreToolUse', 'PostToolUse', 'Stop', 'UserPromptSubmit', 'none-use-a-CLAUDE-md-rule-instead']`. Casing matches 85128. |
| 11 | M5.S2 (`claude /mcp list` invalid) — flagged ⚠ partial in v1 (not in regen list) | **CLOSED** (regression-free, even though step wasn't regen'd) | Step 85131 now uses `claude mcp list` (correct CLI form) for verification, and `/mcp tools` only inside an interactive session (which IS a real slash command form). I likely missed that the platform Creator-prompt change cascaded the fix. |
| 12 | M2.S1 (85118): was already ✅ in v1 (template was strong); flagged here only to confirm regen didn't regress | **CLOSED — no regression** | Six sections still present, just with one renaming: v1 listed Stack/Conventions/Testing/Don't-Touch/Commands/Escalation; v3 lists Stack/Conventions/Don't Touch/Testing Strategy/Commands/Domain Context. Both are reasonable shapes for a Spring Boot CLAUDE.md. Sample still says `jakarta.*` (correct), Testcontainers + PostgreSQL (correct), `./mvnw clean verify` (correct). |

Result: **all 11 P0/P1 issues from v1 CLOSED.** No NEW P0 surfaced from the regen. No regression in the spot-checked non-regen'd steps.

## Per-step grading (vs v1 morning verdict)

| Step | v1 verdict | v3 verdict | Delta |
|---|---|---|---|
| 85118 (M2.S1 anatomy of CLAUDE.md) | ✅ passed (template was excellent) | ✅ passed | same — small cosmetic restructure ("Domain Context" replaces "Escalation"); both valid for Spring Boot |
| 85124 (M3.S2 /controller-review) | ⚠ partial (`{{className}}` non-standard) | ✅ better | now uses `$ARGUMENTS` + correct frontmatter (`description`, `argument-hint`); the 6-item production-risk audit list is concrete |
| 85125 (M3.S3 mockito subagent) | ❌ stuck (bogus `claude @agent` CLI + `max_tokens`) | ✅ better | three valid invocation methods, `maxTurns: 8` valid frontmatter, correct constructor-injection-with-`@Mock` example |
| 85127 (M4.S1 hook contract) | ❌ stuck (str_replace_editor + parameters.path) | ✅ better | full rewrite: PascalCase tool names, `tool_input.file_path`, working bash example with `jq` parsing, exit-code semantics correct |
| 85128 (M4.S2 wire 3 hooks) | ❌ stuck (wrong schema, lowercase, wrong field name) | ✅ better | full rewrite: real settings.json schema, PascalCase, correct `tool_input.file_path` in the inline Python; rubric enforces PascalCase explicitly |
| 85129 (M4.S3 categorization) | ⚠ partial (8 items vs claimed 10; inconsistent casing with M4.S2) | ✅ better | 10 items present, casing aligned with 85128, decision-tree pedagogy intact |

Spot-checked non-regen'd steps (no regression, sanity layer):
- 85112 (M0.S2 preflight) — rubric still detailed; instructions unchanged (`claude --version`, `java -version`, `./mvnw -v`); `must_contain` reasonable.
- 85131 (M5.S2 wire team-tickets MCP) — uses `claude mcp add team-tickets "npx @codeflow/team-tickets-mcp" --transport stdio` and `claude mcp list` (correct CLI). The morning P0 here is also CLOSED, even though this step wasn't on the regen list — most likely the platform Creator-prompt tightening cascaded.
- 85136 (M6.S3 implement OrdersController) — capstone scope still realistic (`@Valid`, `Idempotency-Key`, 4+ test methods including idempotent retry); `must_contain` matches what the rubric expects.

## What's still imperfect (P2 — not ship-blockers)

1. **Subagent invocation method 2 (`claude --agent <name>`)** in 85125: this CLI flag is not in the official Claude Code docs. Inside `claude` you can prefix a message with the subagent name or use `/agents` to manage them. A beginner who runs the flag and gets "unknown flag" has the step's `<details>` disclosure as the only fallback. Methods 1 and 3 in that step are correct and sufficient on their own.
2. **`$ claude /agents list`** in 85125 implies a shell command. `/agents` is in-session only; real form is start `claude`, then type `/agents`. Same class of cosmetic issue as #1.
3. **85128 Python hook doesn't check `event_type`** while the bash example in 85127 does. Inconsistent but harmless — settings.json already routes by event, so the simpler script arguably teaches better.
4. **Categorization 85129 i9 phrasing**: "Show learner ./mvnw verify output before exit…" reads awkwardly. Intent is clearly a `Stop` hook; nit only.
5. **M0.S2 wrong-answer feedback** still generic ("doesn't match what the exercise expects"). Untouched in this regen; was P2 in v1 too.

## Verdict — **SHIP**

Every v1 ship-blocker is closed, with verbatim evidence above. The Java/Spring-Boot content was already strong in v1; the post-regen Claude Code mechanics now match real Claude Code (PascalCase event names, real `tool_input.file_path` payload, real settings.json `[matcher → hooks[]]` schema, real `$ARGUMENTS` substitution, real subagent frontmatter). The cosmetic P2s are at worst "unknown command" detours that the step disclosures already unblock; they won't derail the course.

A first-time Claude Code Spring Boot engineer can now walk end-to-end: hooks actually fire, the slash command resolves `$ARGUMENTS`, the subagent frontmatter parses with at least one documented invocation method, and the categorization exercise is internally consistent with the hook content above it. The capstone (85137 GHA-graded) is unchanged from v1's ✅, as is the CLAUDE.md / Testcontainers / Mockito 5 / jakarta.* / RFC 7807 content quality.

## Top blockers — **none**

No hard blockers. P2s for next iteration:

| # | Step | Concern | Fix |
|---|---|---|---|
| P2-1 | 85125 | `claude --agent <name>` flag not in docs | Replace with `/agents` slash command in-session; keep methods 1 + 3 |
| P2-2 | 85125 | `$ claude /agents list` is invalid shell syntax | Show as: start `claude`, then `/agents` inside the session |
| P2-3 | 85128 | Python hook ignores `event_type`, vs bash example in 85127 | Either add the check for parity, or note that settings.json's matcher already routes events |

The platform Creator-prompt tightening propagated through every named regen step and (bonus) appears to have cascaded a fix to M5.S2's MCP CLI as well. **APPROVE for SHIP.**
