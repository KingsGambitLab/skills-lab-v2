# Domain-Expert Review — AI-Augmented Engineering: Ship Production Features with Claude Code + API
Persona: Staff AI-Tooling Engineer
Date: 2026-04-24
Pass: v3

## Overview
7 modules (M0 preflight + M1-M4 + M6 deep capstone + "Real Team" module exposed as M5 position 7). ~29 steps. Mix of concept, code_exercise, code_review, terminal_exercise, scenario_branch, categorization, github_classroom_capstone. v3 claims to add a "Claude Code reference facts" block + 6 targeted regens. Scope is the real one (CLAUDE.md, context hygiene, MCP, custom subagent/hook/settings, GHA capstone, agentic SDK loop). Spot-check below verifies the 5 specific claims in the v3 review prompt.

## v3 claim verification
- (a) **M5.S2 hook uses stdin JSON + `exit 2`** — YES. Content: "Hooks read JSON input from STDIN (not environment variables). Your script receives the tool call data via `input=$(cat)`, parses with `jq`, and exits with code 2 to block". Validation `hidden_tests` asserts `exc_info.value.code == 2`. Verbatim correct.
- (b) **settings.json in M5.S3 has no top-level `agents` key + no `mcpServers`** — YES. Content says "MCP servers go in `~/.claude.json`, while subagents are auto-discovered from `.claude/agents/*.md`." The solution settings.json contains only `permissions` + `hooks`. `create_mcp_config()` returns `mcpServers` in a SEPARATE file. Correct split.
- (c) **M5.S1 subagent YAML uses capitalized tool names** — YES. M5.S2 (the authoring step) explicitly says "tools allowlist using the CAPITALIZED built-in tool names: `Read`, `Edit`, `Bash` — never the lowercase API names."
- (d) **M4 includes `claude mcp add --transport stdio`** — NO. M4.S1 concept shows `claude mcp add server-name` with no `--transport` flag. Neither M4.S1 nor M4.S3 (terminal exercise) mentions `stdio`, `--transport`, or the HTTP/stdio distinction. This claim is UNMET.
- (e) **M0.S1 no longer invents `claude auth`** — YES. Zero occurrences of `claude auth`. Auth references use `claude --version` and "API key configured" (vague but not fictional). Landing page correctly says `claude /login`. Fixed.

## Blind-spot coverage (abbreviated)
1. Real CLAUDE.md — PARTIAL. M2.S2 reads an "exemplary" CLAUDE.md; M2.S3 writes one. Substantive, not hello-world.
2. Subagent taxonomy (Explore/Plan/general) — NO. Course teaches one custom subagent (test-fixer) but never separates the built-in Explore/Plan/general flavors with "use this one when" rules.
3. Debug when CC goes off rails — PARTIAL. M3 scenario + M5.S5 stuck-loop step cover this. `/clear` mentioned (M2.O3 objective), `@mentions` not covered.
4. Hooks ergonomically (PostToolUse, Stop, UserPromptSubmit) — NO. Only PreToolUse taught. Stop/PostToolUse/UserPromptSubmit absent.
5. MCP transport + permission model — PARTIAL→WEAK. Concept mentions `.mcp.json`/`~/.claude/mcp.json` locations. Solution uses `"transport": "stdio"` key, which in current Claude Code is set by the `--transport stdio|sse|http` CLI flag. The `stdio` vs `http` distinction is not explicitly taught.
6. What NOT to delegate — NO. Not covered.
7. Token-budget / context-window — PARTIAL. `/clear` mentioned; no explicit context-window number, drift explanation, or cost-of-preload.
8. Platform-aware install (mac/Linux/WSL) — NO. M0 provides generic download links only.
9. Install-failure recovery (EACCES, shell-hash, node version, WSL filesystem) — NO. Generic checklist.
10. Security: no key upload widget — YES. Terminal exercise uses paste slots only; page banner says "Your key stays on your machine." Clean.

## Remaining technical accuracy warts (post-v3)
1. **M5.S1 concept step still ships fictional config examples.** Sarah/Marcus sample configs show `allowed_tools`, `file_access.whitelist/blacklist`, `auto_confirm`, Python hook functions returning `{'block': True}`, and tool names `str_replace_editor`/`bash`. None of these are valid Claude Code syntax. Directly contradicts M5.S2/S3 that were regenerated. **This undermines (b) and (c) in the very concept step that frames the module.**
2. **M5.S3 hook registration uses string form.** `"hooks": {"PreToolUse": "~/.claude/security_hook.sh"}` — real schema is an array of `{matcher, hooks: [{type: "command", command: "..."}]}`. Still wrong.
3. **M5.S3 `permissions.deny` lists `"curl"` and `"wget"`** as bare strings — these aren't tool names in the Claude Code permission system (would be `Bash(curl:*)`/`Bash(wget:*)`). Remaining factual error.
4. **M5.S6 capstone paste slots contradict M5.S2.** Labels `.claude/subagents/test-fix-loop.py` (wrong dir + wrong extension) and `.claude/hooks/pre-tool-use.py` (hooks are shell), and rubric `must_contain` requires `def main()` — i.e., grader forces the wrong artifact shape.
5. **M4 missing `claude mcp add --transport stdio`.** Concept step only shows `claude mcp add server-name`; no HTTP vs stdio transport teaching.

## Axis scores
- technical_accuracy: 0.62
  - evidence: Hook (stdin+exit 2), subagent YAML (capitalized tools), and settings.json structure (no fictional `agents`/`mcpServers`) are now correct in the targeted regen steps — BUT the concept step (S1) still ships invalid syntax, capstone paste slots contradict S2, and `claude mcp add --transport stdio` is missing from M4. Net-positive vs v2 but not production-grade reference material yet.
- production_readiness: 0.58
  - evidence: Covers CLAUDE.md, custom subagent, PreToolUse hook, MCP integration, GHA capstone, agentic SDK loop. Missing: PostToolUse/Stop hooks, Explore/Plan subagent taxonomy, what-not-to-delegate, platform install recovery, transport distinction. Good shape; gaps would bite juniors in prod.
- failure_mode_coverage: 0.55
  - evidence: M3 (70%-right), M5.S5 (stuck loop) are solid. Install-failure recovery absent. Token-drift reasoning thin. Key debugging moves (`@mentions`, breaking tool-loops) not taught.
- tradeoff_articulation: 0.50
  - evidence: M0 model cost tiers (haiku/sonnet/opus) articulated well. MCP stdio vs HTTP tradeoff: not articulated. Delegate vs drive-directly: not articulated. CLAUDE.md size vs token cost: not articulated.
- security_posture: 0.85
  - evidence: No key-upload widgets — BYO banner only, as required. Hook exercise actually teaches blocking rm -rf / DROP TABLE / force-push patterns. Permissions deny-list shape is wrong but intent is right. Solid axis.

## Weighted score
technical_accuracy 0.62 × 0.25 = 0.155
production_readiness 0.58 × 0.25 = 0.145
failure_mode_coverage 0.55 × 0.20 = 0.110
tradeoff_articulation 0.50 × 0.15 = 0.075
security_posture 0.85 × 0.15 = 0.1275
**TOTAL: 0.61 / 1.00**

## Verdict
⚠ **CONDITIONAL** (0.61)

**MUST FIX before approval**
- Regenerate M5.S1 concept step so the demo configs use real Claude Code syntax (capitalized tools, `permissions.allow/deny/ask`, shell hooks, no `allowed_tools`/`file_access`/`auto_confirm`). The concept step currently contradicts the fixed exercise steps.
- Fix M5.S6 capstone: rename paste slots to `.claude/agents/test-fixer.md` + `.claude/hooks/pre-tool-use.sh`, relax rubric so it doesn't force `def main()`, and make `must_contain` match correct file layout.
- Add `claude mcp add --transport stdio` + a stdio-vs-http explanation somewhere in M4 (the v3 prompt called this out explicitly and it's missing).
- Fix M5.S3 hooks schema to `{matcher, hooks:[{type:"command", command:"..."}]}` and drop bare `curl`/`wget` from `permissions.deny`.

**SHOULD FIX but non-blocking**
- Add a PostToolUse or Stop hook example (PreToolUse alone isn't the full story).
- Add a "what to NOT delegate" concept box (security/prod decisions, org-context).
- Add platform-aware install recovery (EACCES, WSL filesystem perf, node mismatch).
- Teach the Explore/Plan/general subagent flavors alongside the custom test-fixer.

## One-line executive summary for the Creator team
v3 successfully fixed the exercise steps the prompt targeted (hook stdin+exit 2, capitalized tools, no fictional `agents`/`mcpServers` keys, no `claude auth`) — but the M5 concept step and M5 capstone rubric still teach the old wrong syntax, and `claude mcp add --transport stdio` is still missing from M4; regenerate those three surfaces and this hits APPROVE.
