# Domain-Expert Review — Claude Code: From Zero to MCP-Powered Workflows
Persona: Staff AI-Tooling Engineer
Date: 2026-04-22

## Overview

Five-module beginner course (24 total steps) tied together by a "CodeFlow release-notes generator" narrative. Module 1 = install/auth/first edit (5 steps), Module 2 = CLAUDE.md + daily flow (5), Module 3 = subagents (5), Module 4 = hooks + plugins (5), Module 5 = slash command + MCP capstone (4). Step types observed: `concept` (static HTML), `terminal_exercise` (bash-tutorial with a paste-transcript textarea — no embedded terminal), `exercise` (in-browser code editor, Python/shell), `code_review` (click-line-to-flag-bug), `system_build` (capstone checklist). BYO-key privacy line is consistently rendered on exercise steps (security posture passes). Content is narratively polished — voice is consistent, stakes are concrete ("Marcus Chen's team needs release notes automation") — but the technical substrate is frequently fabricated. The course teaches a plausible-sounding but frequently incorrect model of Claude Code's real CLI, hook schema, subagent invocation, plugin CLI, slash-command format, and MCP transport/config. A motivated junior following these instructions verbatim would hit `command not found` or silent-no-op failures at multiple steps.

## Blind-spot coverage

### Blind spot 1 — "Real CLAUDE.md demonstration, not placeholder"
- Covered? **partial**
- Evidence: Module 2 Step 1 (concept) shows a decent pipeline diagram explaining that Claude Code reads `CLAUDE.md` from project root, uses `@file` mentions, carries session context. Module 2 Step 2 ("Author a CLAUDE.md for a fixture repo") is a narrative-only terminal_exercise — it tells the learner "you'll clone our CodeFlow fixture repository, author a comprehensive CLAUDE.md" but provides **no sample CLAUDE.md content, no structure template, no real-repo excerpt showing WHY it is the unlock** (e.g. testing commands, architectural notes, off-limits paths). Module 2 Step 5 titled "When NOT to use Claude Code" is actually (body-copy) another CLAUDE.md creation exercise — title/content mismatch.
- Missing: A real, ~40-line CLAUDE.md from a production-scale repo showing conventions, test commands, off-limits files, review checklist, and architectural one-liners. The course never shows what a high-leverage CLAUDE.md actually looks like.

### Blind spot 2 — "Explore vs Plan vs General-purpose with concrete use-this-one-when rules"
- Covered? **yes** (content quality) / **partial** (accuracy)
- Evidence: Module 3 Step 1 is the single strongest step in the course. Explicit purpose/context/best-for for each of Explore, Plan, General-purpose, plus an explicit "Delegate when / Don't delegate when" list. Quote: "Delegate when: The task is well-defined and isolated ... Don't delegate when: You need iterative back-and-forth or the agent needs to remember previous decisions."
- Missing: The accompanying exercises (Steps 2-4) invoke the agents with fabricated CLI syntax — `claude explore "..."`, `claude plan "..."`, `claude explore --focus=... --name=... &` — none of which are real Claude Code commands. Real subagent invocation is via the Task tool within a session or via `/agents` configs. Step 4 ("Parallel subagents") teaches shell-backgrounding of separate `claude` processes, which is wrong — real parallel subagents run in one turn via multiple Task tool calls.

### Blind spot 3 — "Debugging when Claude goes off the rails (/clear, @mentions, breaking tool-loops, when to stop delegating)"
- Covered? **partial**
- Evidence: Module 2 Step 1 explains `/clear` and lists three legitimate use cases (context drift, performance, topic switching). Module 2 Step 4 ("Picking a model and using /clear between tasks") revisits `/clear`.
- Missing: No coverage of breaking out of a tool-loop (Esc, abort), no coverage of "recognize when Claude is thrashing and drive directly", no coverage of @mentions beyond one throwaway mention in a pipeline diagram, no discussion of when to abandon the session and restart. Module 3 Step 5 ("Delegation judgment call") should live here but instead ships as a Python coding exercise that asks the learner to implement a fake `ClaudeCodeSession` class — teaches no actual judgment.

### Blind spot 4 — "Hooks ergonomically with runnable examples, not settings.json reference dump"
- Covered? **no**
- Evidence: Module 4 Steps 1-3 cover hooks but with a **wrong schema**. Module 4 Step 1 teaches `"hooks": [{"event": "PreToolUse", "command": "..."}]` — a flat array. Real Claude Code hooks schema is `"hooks": {"PreToolUse": [{"matcher": "Bash|Edit", "hooks": [{"type": "command", "command": "..."}]}]}` with three-level nesting. Module 4 Step 2 claims PostToolUse hooks "receive environment variables like TOOL_NAME and AFFECTED_FILES" — **false**; real hooks receive JSON on stdin. Module 4 Step 3 uses a similarly wrong `"hooks": {"stop": {"command": "...", "enabled": true}}` shape.
- Missing: The real nested schema, `matcher` filtering, JSON-over-stdin payload (`tool_name`, `tool_input`, `hook_event_name`), the exit-code semantics for blocking/approving, UserPromptSubmit, SessionStart, PreCompact, Notification hooks. Also missing: `${CLAUDE_PROJECT_DIR}` and the hook JSON output contract (`hookSpecificOutput.permissionDecision`).

### Blind spot 5 — "MCP capstone teaches transport (stdio vs HTTP) + permission model"
- Covered? **no**
- Evidence: Module 5 Step 1 (concept) says MCP servers are "Python processes that expose real tools to Claude Code" — overreaching; any language is supported. Module 5 Step 3 (warm-up) mentions stdio in a sentence ("JSON-RPC over stdio") but never in the capstone acceptance criteria. Module 5 Step 4 capstone says "Test MCP server endpoints with `curl -X POST localhost:8000/tools/search_docs`" — conflates REST with MCP JSON-RPC 2.0, which uses `tools/list` and `tools/call` methods. Also says "Add MCP server to Claude Code settings.json under servers configuration" — real key is `mcpServers` with per-transport shapes (`command/args/env` for stdio, `type: "http"` + `url` + `headers`/`oauth` for HTTP).
- Missing: The `mcpServers` schema, stdio vs streamable-HTTP vs SSE transports, `type` discrimination, OAuth config for remote servers, `claude mcp add` / `claude mcp add-json` CLI, permission model (`enabledMcpjsonServers`, per-tool allow list in `permissions.allow`). Missing any discussion of how Claude Code authenticates to an HTTP MCP server (bearer tokens, `headersHelper`). The deploy-to-Railway aside in acceptance criteria hand-waves production auth.

### Blind spot 6 — "What NOT to delegate to Claude Code"
- Covered? **partial**
- Evidence: Module 2 Step 5 has a paragraph: "Claude Code excels at focused edits but has clear boundaries. It can't browse the web, run tests automatically, or access external APIs during execution." Module 3 Step 1 has "Don't delegate when: You need iterative back-and-forth..."
- Missing: The course conflates **capability limits** ("can't browse web") with **judgment/trust limits** (security-sensitive decisions, prod-deploy gates, anything needing org context it doesn't have, PII exposure in pasted transcripts, secret-leak risk). No discussion of "don't put Claude Code behind a production deploy without human-in-the-loop", no discussion of dangerous commands (`rm -rf`, force-push to main), no mention of `disallowedTools` / permission allow-list discipline. This is the biggest production-reality miss.

### Blind spot 7 — "Token-budget hygiene + context-window reality"
- Covered? **partial**
- Evidence: Module 2 Step 1 mentions "Large sessions can slow down response times" and calls out context drift. Module 3 Step 1 mentions "token efficiency" for isolated subagent contexts.
- Missing: No concrete numbers (e.g. "~200K context window, degradation starts around 100K"), no mention of `/compact`, no `/cost` or `/usage` discussion, no demonstration of why preloading the entire codebase is an anti-pattern, no discussion of when to break a task into subagent-scoped work vs drive everything in main session. The coverage is a vague "long sessions drift" — which is correct but the course never operationalizes it.

### Blind spot 8 — "Platform-aware install guidance (macOS, Linux-native, Windows+WSL) + PATH gotchas"
- Covered? **partial** (intent) / **no** (execution)
- Evidence: Module 1 Step 2 splits into macOS / Linux / Windows+WSL tabs with different commands. Intent is right.
- Execution is wrong: Commands shown are `brew install anthropic/tap/claude-code` (invented tap — real is `brew install --cask claude-code`), `curl -fsSL https://api.claude.ai/cli/install.sh | bash` (invented URL — real is `https://claude.ai/install.sh`). Windows tab shows the same Linux curl incantation, missing real Windows support: `irm https://claude.ai/install.ps1 | iex`, the CMD `install.cmd` variant, `winget install Anthropic.ClaudeCode`, the Git-for-Windows prerequisite for native Windows, and the PATH / `CLAUDE_CODE_GIT_BASH_PATH` setting. No mention of `claude doctor`.

### Blind spot 9 — "Recovery when install fails (EACCES, shell-hash, node-version, expired auth, WSL perf trap)"
- Covered? **no**
- Evidence: Each install step has a "Don't have Homebrew installed?" / "Got permission denied?" / "Command not found?" collapsible — but these are opened via disclosure/dropdowns that were not rendered in the DOM as I walked through, so they appear to be placeholder titles with no runnable content behind them. None of the text I retrieved included actual remediation steps.
- Missing: `sudo npm` caveat (the docs explicitly warn against it), EACCES prefix remediation, `hash -r` / shell-hash cache, Node 18+ requirement note, WSL2 filesystem-performance advice (don't install into `/mnt/c/...`), how to refresh expired auth tokens, `claude doctor` for self-diagnosis.

### Blind spot 10 — "Security: no API key input widget, BYO panel only"
- Covered? **yes**
- Evidence: DOM-wide sweep confirms 0 password inputs, 0 API-key-named fields. Every terminal_exercise step renders the privacy line: *"🔐 Your key stays on your machine. Configure Claude Code with claude /login (or set ANTHROPIC_API_KEY in your shell). This page will never ask for your key."* The only submission widgets are a free-text textarea for pasting terminal output and an in-browser code editor. Capstone's "Deployed service URL" widget is missing (text promises a URL field, only the transcript paste-area is present — that's a minor UX gap, not a security one).

## Axis scores

- **technical_accuracy: 0.25**
  Evidence: Fabricated install URL `api.claude.ai/cli/install.sh` (real: `claude.ai/install.sh`). Fabricated brew tap `anthropic/tap/claude-code` (real: `--cask claude-code`). Fabricated subcommands `claude explore`, `claude plan`, `claude status --agents`, `claude plugins browse/search/install`, `claude --config-path`. Wrong hook schema (flat array with `event` key vs real nested `{"hooks":{"EventName":[{"matcher":..., "hooks":[{"type":"command",...}]}]}}`). Wrong hook input model (env vars vs stdin JSON). Wrong slash-command format (executable `.py` in `~/.config/claude-code/commands/` vs real markdown in `.claude/commands/*.md`). Wrong MCP client invocation (`curl -X POST localhost:8000/tools/search_docs` vs JSON-RPC `tools/call`). Wrong config key (`servers` vs `mcpServers`). Wrong hook-path (`~/.config/claude-code/` vs `~/.claude/`). Non-existent fixture repo `github.com/anthropic-edu/codeflow-fixture.git`. Model names are stale (`claude-sonnet-4-5` in 2026). The agent-mental-model explainer (M3S1) and the CLAUDE.md/`/clear` explainer (M2S1) are the only technically clean sections.

- **production_readiness: 0.30**
  Evidence: Good intent — narrative framing ties to a realistic workflow (release notes generation). But the concrete artifacts a learner produces (broken hooks, broken slash command, broken MCP config, broken CLI invocations) do not survive contact with real Claude Code. A junior following this course cannot ship a working hook or MCP server. The capstone's acceptance checklist has non-runnable items ("Deploy MCP server to Railway and update settings.json with production URL" with no schema/transport/auth guidance). No coverage of CI patterns, team-distribution (managed settings, plugin marketplaces), or org-wide governance.

- **failure_mode_coverage: 0.25**
  Evidence: Each terminal_exercise step has placeholder "Got X error?" disclosure sections but I could not confirm they render any remediation content. No `/clear`-in-practice walkthrough, no "recognize a tool loop", no "Claude is hallucinating library APIs — how to catch it", no "broken auth token" recovery, no `claude doctor`. One debug-a-hook step (M4S4) is good as a pattern (click lines with bugs) but the code it asks learners to debug uses the fabricated schema so learners end up internalizing a wrong mental model.

- **tradeoff_articulation: 0.45**
  Evidence: Module 3 Step 1 and Module 2 Step 1 articulate real tradeoffs well (delegate vs do, context pollution vs continuity, model choice fast/cheap vs slow/brilliant). Module 5 Step 1 has a decent "UI layer (slash commands) vs backend layer (MCP)" framing. But most other steps default to "this feature is great here's how to use it" without tradeoff nuance. No tradeoffs articulated for stdio vs HTTP MCP, standalone configs vs plugins, shared vs personal hooks, latest vs stable release channel.

- **security_posture: 0.80**
  Evidence: PASS on the key-handling boundary — zero key-input widgets, BYO disclaimer consistently rendered. Docked points because the course (a) never teaches `permissions.allow`/`deny` lists, (b) never discusses dangerous tool calls (`rm -rf`, `Bash(sudo *)`), (c) never mentions sandboxing options, (d) in the capstone hand-waves deploying an MCP server to Railway without teaching bearer-token auth or OAuth setup, and (e) never cautions about pasting transcripts that may contain secrets into the lab submission box.

## Weighted score

  0.25 × 0.25 = 0.0625
  0.30 × 0.25 = 0.0750
  0.25 × 0.20 = 0.0500
  0.45 × 0.15 = 0.0675
  0.80 × 0.15 = 0.1200

TOTAL: **0.37 / 1.00**

## Verdict

❌ **REJECT (< 0.60)**

MUST-FIX list (non-exhaustive; these are the blockers):
1. Replace every fabricated CLI invocation with real Claude Code commands. Concretely: remove `claude explore`, `claude plan`, `claude status --agents`, `claude plugins browse/search/install`, `claude --config-path`; demonstrate real subagent invocation via Task tool / `/agents` interactive UX; demonstrate plugin management via `/plugin` slash commands and `--plugin-dir`.
2. Rewrite the entire hooks module around the real nested schema (`{"hooks":{"EventName":[{"matcher":"Tool","hooks":[{"type":"command","command":"..."}]}]}}`) and the stdin-JSON input contract (`jq -r '.tool_input.file_path'` etc.), not env vars.
3. Rewrite the slash-command step: slash commands are markdown files in `.claude/commands/*.md` or plugin-namespaced, not executable Python in `~/.config/claude-code/commands/`.
4. Rewrite the MCP capstone around the `mcpServers` config key, the `type: "stdio" | "http" | "sse"` discriminator, `claude mcp add` CLI, and the JSON-RPC 2.0 protocol (not REST). Add explicit HTTP-auth coverage (bearer, headersHelper, OAuth).
5. Fix install commands for all three platforms — use `claude.ai/install.sh` (not `api.claude.ai/cli/install.sh`), `brew install --cask claude-code` (not the invented tap), add Windows PowerShell `irm | iex` and winget paths, mention `claude doctor` and Git for Windows prereq.
6. Add a real production CLAUDE.md sample (~40 lines) showing conventions, test commands, off-limits files — the course never demonstrates the artifact it keeps hyping.
7. Replace `github.com/anthropic-edu/codeflow-fixture.git` with a real, reachable fixture or stub it out.
8. Add a dedicated "what NOT to delegate" step covering security-sensitive changes, prod-deploy gates, secret handling, and the `permissions.allow/deny` / `disallowedTools` discipline.
9. Populate (don't just title) the "Got X error?" disclosure sections with real remediation for EACCES, shell-hash, Node-version mismatch, expired auth, WSL perf.
10. Fix model names to current (April 2026) families.

## One-line executive summary for the Creator team

The narrative arc is solid but ~60% of the technical specifics (CLI subcommands, hook schema, slash-command format, MCP protocol, install URLs) are fabricated — ship a re-grounding pass against code.claude.com/docs before this course goes anywhere near a paying learner.
