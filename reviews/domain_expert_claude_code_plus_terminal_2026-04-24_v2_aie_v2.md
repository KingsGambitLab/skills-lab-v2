# Domain-Expert Review — AI-Augmented Engineering: Ship Production Features with Claude Code + API
Persona: Staff AI-Tooling Engineer
Date: 2026-04-24
Pass: v2

## Overview

Seven modules, 29 steps. Position order is: M0 (Preflight, 2 steps), M1 (First Fix / context gap, 4 steps), M2 (CLAUDE.md, 4 steps), M3 (Drive 70%-right, 4 steps), M4 (MCP + PR review capstone, 4 steps), M6 (Agentic harness, 5 steps), then the NEW v2 addition at position 7 titled "Working with Claude Code in a Real Team: Subagents, Hooks, Settings" (M7, 6 steps including pos=0 concept). Note: the course skips the label "M5" entirely — the old M5 module was removed, M6 kept its name, and the new team-Claude module lives at position 7 without an "M5" or "M7" prefix in its title.

Exercise mix looks good on paper: 9 terminal_exercise, 7 code_exercise, 3 code_review, 2 scenario_branch, 1 categorization, 1 code_read, rest concept. Terminal template mount (terminal.css/terminal.js) confirmed in HTML `<head>` at v=1.1.2 (2026-04-24 comment: "added terminal.css + terminal.js to the head so SllTemplateTerminal registers on boot"). BYO-key security panel is informational-only: no key input widget, explicit comment "No key handling, EVER."

The course has strong narrative bones (Nexboard collaborative-cursor thread, real CLAUDE.md sample, realistic 70%-right scenarios, a clean agentic-loop capstone with tool_use / budget / sha256 stuck-detection). But the two modules added/promoted specifically to address v1's gaps — M4 MCP wiring and M7 team-Claude — both have **factual errors that would cause working-looking configs to silently do nothing in production**. That's the most dangerous failure mode for this persona.

## Blind-spot coverage

### Blind spot 1 — "Does the course SHOW a real CLAUDE.md or a hello-world placeholder?"
- Covered? **yes**
- Evidence: M2.S2 (id 85065) renders an exemplary CLAUDE.md with Project Structure, Core Architecture (exact Redis key shapes `cursor:{canvas_id}` with {x,y,timestamp}), "DO NOT TOUCH" naming actual owners (Marcus Chen owns auth middleware, Sofia Martinez refactoring RedisSessionManager), Common Pitfalls ("cursor positions expire in 30 seconds via EXPIRE"), Testing Conventions ("Use `tests/fixtures/canvas_factory.py`"), and a Current Sprint Context section. This is a genuinely senior CLAUDE.md, not boilerplate.

### Blind spot 2 — "Explore vs Plan vs general-purpose subagents with concrete 'use this when…' rules?"
- Covered? **no**
- Evidence: The course never mentions built-in Explore, Plan, or general-purpose subagents at all. Searched entire M7 + M6 content: zero hits for "Explore", zero for "Plan" (as subagent name), zero for "general-purpose". M7.S1 only teaches how to write ONE custom subagent (a test-fixer) and does not situate it against the built-in agents a learner will encounter every day.
- If partial/no: M7.S0 concept should cover the three built-ins (Read-only tools restriction, Haiku default for Explore, when Claude delegates to them automatically), and then introduce custom subagents as an *extension* rather than the whole story. Otherwise juniors will write a custom test-fixer when the built-in general-purpose agent would do the job.

### Blind spot 3 — "Debugging when Claude Code goes off the rails — /clear, @mentions, breaking tool-loops, stop delegating?"
- Covered? **partial**
- Evidence: M3.S1 mentions `/clear` and rewriting the prompt instead of arguing with output. M7.S4 (scenario_branch, id 85085) has a thoughtful diagnostic pattern: "identical error hash = context poisoning (restart with /clear), different error hash = capability gap (add tools), visible progress = budget issue (raise limits)." That's the kind of heuristic a staff engineer would hand a junior. However `@mentions` (for focusing Claude on a specific file) are never mentioned, and there's no discussion of when to abandon Claude entirely and drive directly.
- If partial: add a short step on `@path/to/file.py` mentions + a rubric for "when to stop delegating" that covers security-sensitive decisions, prod-deploy gates, and org-context work.

### Blind spot 4 — "Hooks ergonomics — PostToolUse / Stop / UserPromptSubmit with examples that run?"
- Covered? **no** (it appears to be covered but the example is factually broken — see below)
- Evidence: M7.S2 teaches a PreToolUse hook as a single bash script, but the taught mechanism is wrong in three ways that all show up in the hidden-test solution_code:
  1. Input is read from `$CLAUDE_TOOL_INPUT` env var. **Real Claude Code passes hook input via stdin JSON**; `CLAUDE_TOOL_INPUT` does not exist. Verified against code.claude.com/docs/en/hooks which shows the canonical pattern: `COMMAND=$(jq -r '.tool_input.command')`.
  2. To block, the hook exits with code 1. **Real Claude Code blocks on exit code 2**; exit 1 is a non-blocking error. So a student's "safety" hook would log warnings but never actually prevent `rm -rf` or `git push --force`. This is a silent-failure security hole.
  3. The course text says "Claude Code reads hooks from `.claude/hooks/` in your project root." This is incorrect. Hooks must be **declared in settings.json under the `hooks` key** with a matcher + `{type: "command", command: "..."}` entry. Scripts in `.claude/hooks/` do nothing unless wired in via settings. The course never shows this wiring.
- PostToolUse, Stop, UserPromptSubmit are not mentioned anywhere — only PreToolUse.
- If partial/no: rewrite M7.S2 to (a) parse stdin with jq, (b) `exit 2` to block, (c) declare the hook in settings.json with the real schema, and ideally add one more step covering PostToolUse or Stop.

### Blind spot 5 — "MCP transport distinction (stdio vs HTTP) + permission model Claude Code actually needs?"
- Covered? **no**
- Evidence: Entire M4 searched for `claude mcp add`, `--transport`, `mcpServers` schema, `.mcp.json`, stdio-vs-http — **zero hits on all of them**. Only `mcp list` appears, in a single rubric hint. M4.S3 briefing says "Claude Code will register the team-tickets MCP server" without showing the `claude mcp add --transport <stdio|http> team-tickets ...` command, without a `.mcp.json` or `~/.claude.json` JSON example, and without distinguishing stdio from HTTP transports. This is exactly the "mystery meat" failure v2 was supposed to address per the task brief's F3 rule. MCP literally cannot be added without that CLI command or the JSON file — the learner will be stuck.
- M7 introduces a `mcpServers` block but places it in `settings.json`, which is the wrong file. The real location is `~/.claude.json` (user/local scope) or `.mcp.json` (project scope). A learner who follows the course will write a config that Claude Code never reads.
- If partial/no: add an M4.S2.5 (or replace S3 content) that walks through `claude mcp add --transport stdio team-tickets -- npx -y @org/team-tickets-mcp`, then shows the resulting `.mcp.json` or `~/.claude.json` fragment, then shows `/mcp` inside Claude Code to verify and approve. Cover the `--scope project` flag so the MCP is shareable with teammates.

### Blind spot 6 — "What NOT to delegate to Claude Code?"
- Covered? **partial**
- Evidence: M3.S1 hints at it ("Do It Yourself — Claude got you 70% there. You write the last 30%"), and M7.S4 has the stuck-loop intervention option "Take manual control and fix the test yourself" (though that's marked suboptimal in context). There is no explicit list of classes of work to NOT delegate — security-sensitive decisions, prod deploys, data-destructive migrations, anything requiring current org context.
- If partial: add a short concept block in M7.S0 or the capstone summary listing red-flag delegation categories.

### Blind spot 7 — "Token-budget hygiene, context-window reality, `/clear`, session drift, preloading anti-pattern?"
- Covered? **partial**
- Evidence: M2.S1 covers `/clear` and notes "when Claude starts repeating itself, makes basic errors it avoided earlier… your context window is polluted." M6.S3 teaches budget (5-iter cap) + sha256 progress detection for an agentic loop. The "why preloading the whole codebase is an anti-pattern" argument is never stated explicitly — a junior could still read this course and think "CLAUDE.md should list every file in the repo."
- If partial: add one sentence to M2.S1 saying "keep CLAUDE.md under ~500 lines; preloading the whole codebase wastes context that should be spent on the current task."

### Blind spot 8 — "Platform-aware install guidance (macOS / Linux / Windows+WSL) incl. PATH gotchas?"
- Covered? **no**
- Evidence: M0.S1 lists "Claude Code (Desktop) — Download for macOS/Windows/Linux" as one link without any OS-specific notes. The MCP docs I cross-referenced explicitly call out a Windows gotcha: "On native Windows (not WSL), local MCP servers that use `npx` require the `cmd /c` wrapper." The course does not warn about this anywhere. No mention of the WSL filesystem-performance trap when the repo lives on `/mnt/c/...`, no PATH hash-cache gotcha on zsh, no Apple-Silicon Rosetta path, no Linux-native globally-installed-node EACCES mention.
- If partial/no: M0 should have a per-platform dropdown block (macOS / Linux / Windows+WSL) with the 2-3 real pitfalls each fleet hits.

### Blind spot 9 — "Install-failure recovery (EACCES, shell-hash cache, node-version mismatch, expired auth token, WSL)?"
- Covered? **no**
- Evidence: M0.S2 rubric mentions "If Claude responds with authentication errors, run 'claude auth' to configure your API key first" — that's the only failure-recovery breadcrumb in the whole course. No coverage of npm EACCES on global installs, `hash -r` after a reinstall in zsh, node-version mismatches, expired/malformed key handling, or the common `command not found: claude` flow after first install on macOS (PATH not yet sourced).
- If partial/no: Add a short "When setup breaks" concept card in M0 with the 5 most common first-run failures and their one-line fixes.

### Blind spot 10 — "Security posture: no key input/upload/transmission?"
- Covered? **yes** (this is the strongest area of the course)
- Evidence: `frontend/templates/terminal.html` contains the comment "BYO-key info panel — NO key handling, EVER. We deliberately do not offer any key input on the page (not even localStorage). The key lives on the learner's machine only." The panel renders informational text "Your key stays on your machine. Configure Claude Code with `claude /login` (or set `ANTHROPIC_API_KEY` in your shell). This page will never ask for your key." No input widget, no localStorage write, no POST of a key field to any endpoint. `demo_data.byo_key_notice: true` is set explicitly on M7.S5 and inherited by default on every terminal_exercise.

## Axis scores

- **technical_accuracy: 0.50**
  - evidence: M7.S2 PreToolUse hook uses `CLAUDE_TOOL_INPUT` env var + `exit 1` to block — both wrong per code.claude.com/docs/en/hooks (real mechanism is stdin JSON + exit 2). M7.S3 settings.json puts `mcpServers` in settings.json and adds a fictional top-level `agents` key; real location is `~/.claude.json` or `.mcp.json`, and subagents are auto-discovered from `.claude/agents/*.md`. M7.S1 subagent frontmatter uses `tools: ["read_file", "edit_file", "bash"]`; real tool names are `Read`, `Edit`, `Bash`. Offsetting positives: M6 agentic harness is technically clean (correct tool_use / tool_result schema, correct stop_reason handling, realistic sha256-based stuck detection), M2 CLAUDE.md example is accurate.
- **production_readiness: 0.55**
  - evidence: M4 MCP step contains zero `claude mcp add`, zero `--transport`, zero `mcpServers` JSON. The capstone MCP step's CI validation is real (GHA lab-grade.yml with workflow conclusion check), but the learner gets there without ever seeing the actual wiring command — they cannot reproduce the feature on a new machine. M7.S5 "Ship a .claude/" step is the right idea (four paste slots for subagent / hook / settings / README) but validates the same incorrect mechanisms as earlier steps, so the "teammate-ready config" ships a config that doesn't work in real Claude Code. M6 capstone shipping-to-GHA is real production-ready work.
- **failure_mode_coverage: 0.60**
  - evidence: M7.S4 stuck-loop scenario_branch (different error hash → capability gap, identical hash → context poisoning, visible progress → budget) is well-designed and matches how a senior engineer actually triages this. M3.S1 iteration-vs-rewrite-vs-do-it-yourself decision tree is solid. Missing: no coverage of PostToolUse / Stop / UserPromptSubmit failure patterns, no install-failure recovery playbook, no `@file` focus mechanic, no treatment of "Claude Code disconnect mid-session" (which the MCP docs specifically call out for HTTP servers).
- **tradeoff_articulation: 0.65**
  - evidence: M0.S1 Budget/Balanced/Premium model-strategy cards (haiku-3.5 vs sonnet-4-5 vs opus-4) with concrete $ costs per tier is exactly the right tradeoff framing. M4.S1 "most senior engineers will use an MCP server, not build one" is a correct and underrated tradeoff call. M2.S1 "CLAUDE.md isn't documentation for humans — it's context for AI" is a sharp framing. What's missing: no discussion of subagent vs main-thread tradeoffs (when does spinning up a subagent pay off vs just running in main), no stdio-vs-HTTP MCP transport tradeoff, no "custom subagent vs built-in general-purpose" tradeoff.
- **security_posture: 0.80**
  - evidence: terminal.html is unambiguous about never handling keys — see Blind Spot 10. M7.S2 PreToolUse hook correctly identifies the RIGHT dangers to block (rm -rf, git push --force, DROP TABLE, `> /dev/sda`). Deductions: (a) the hook implementation does not actually block anything in real Claude Code due to the exit-code/env-var errors, so a student who ships it has a false sense of security — this is itself a security anti-pattern; (b) no mention of the prompt-injection risk from MCP servers that fetch untrusted content, which the official MCP docs specifically warn about.

## Weighted score

technical_accuracy 0.50 × 25%  =  0.1250
production_readiness 0.55 × 25%  =  0.1375
failure_mode_coverage 0.60 × 20%  =  0.1200
tradeoff_articulation 0.65 × 15%  =  0.0975
security_posture 0.80 × 15%  =  0.1200

**TOTAL: 0.60 / 1.00**

## Verdict

**CONDITIONAL** (0.60 — at the lower edge of conditional; one more factual-accuracy regression and this flips to REJECT).

The course skeleton is real. The narrative works. The terminal mount is fixed. The agentic-harness capstone (M6) is actually good and survived the reshuffle cleanly (no stale references except a minor `step_slug: "M5.S3"/"M5.S4"` label drift in the demo_data of two steps). BUT the two modules that v2 specifically shipped to close v1's gaps — M4 MCP wiring and M7 team-Claude — both contain **factually incorrect mechanics that produce configs/hooks that silently no-op in production**. That's worse than not teaching the mechanic at all: a junior will deploy a "safety hook" and ship unsafe code, convinced they're protected.

### MUST FIX before approval

1. **M7.S2 PreToolUse hook rewrite** — use stdin JSON (`jq -r '.tool_input.command'`), block with `exit 2` not `exit 1`. Add a settings.json block that actually wires the hook via the `hooks` key with PreToolUse matcher. Update all hidden tests accordingly. Currently shipping: a hook that never blocks.
2. **M7.S3 settings.json rewrite** — remove the fictional top-level `agents` key (subagents auto-discover from `.claude/agents/*.md`). Move `mcpServers` out of settings.json into `.mcp.json` (project scope) or document that it belongs in `~/.claude.json` (user scope). Fix the permission rule syntax to match `Tool(specifier)` format per the docs.
3. **M4 teach real MCP wiring** — add a concrete `claude mcp add --transport stdio team-tickets -- npx -y <pkg>` command in M4.S3, show the resulting `.mcp.json` / `~/.claude.json` fragment, show `/mcp` verification inside Claude Code, cover the `--scope project` vs `local` vs `user` flag. Without this, the MCP capstone is ungraded-in-practice.
4. **M7.S1 subagent tool names** — change `tools: ["read_file", "edit_file", "bash"]` to `tools: ["Read", "Edit", "Bash"]`. Update hidden tests. This is a one-line fix that saves students from copy-pasting broken subagents.

### SHOULD FIX but non-blocking

5. Add an M7.S0 concept block covering built-in Explore / Plan / general-purpose subagents and when Claude delegates automatically — so custom subagents land as extension, not replacement.
6. Add a platform-aware install matrix to M0 (macOS / Linux-native / Windows+WSL) with each fleet's top 2-3 gotchas. Include the `cmd /c` npx wrapper for native Windows MCPs.
7. Add an "install-failure recovery" concept to M0.S1 with the 5 common errors (EACCES, PATH not sourced, hash -r, expired key, WSL path perf).
8. Cover at least one more hook type (PostToolUse or Stop) so learners don't think PreToolUse is the whole story.
9. Add explicit "what NOT to delegate to Claude Code" list (security-sensitive, prod-deploy, data-destructive, org-context-required) — one concept card in M7.
10. Rename the module labeled "M6 — Agentic Coding from First Principles" to M5 (or rename position 7 to M6) so the numbering is continuous. Fix `step_slug` drift in M6.S4 + M6.S5 demo_data from "M5.S3"/"M5.S4" to "M6.S4"/"M6.S5".
11. Add a short "stdio vs HTTP MCP transport" tradeoff paragraph in M4.S1 — when would a team pick one over the other.

## One-line executive summary for the Creator team

v2 added the right module (M7 Team-Claude) and fixed the terminal mount, but the hook + settings + MCP wiring teach mechanics that silently no-op in real Claude Code (stdin JSON not env var, exit 2 not exit 1, `.mcp.json` not settings.json, auto-discovered subagents not a top-level `agents` key) — fix those four factual errors and this flips from CONDITIONAL 0.60 to APPROVE ~0.80.
