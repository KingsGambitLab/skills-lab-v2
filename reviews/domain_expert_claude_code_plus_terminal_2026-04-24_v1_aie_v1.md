# Domain-Expert Review — AI-Augmented Engineering: Ship Production Features with Claude Code + API
Persona: Staff AI-Tooling Engineer
Date: 2026-04-24
Pass: v1_aie_v1
Course URL: http://127.0.0.1:8001/#created-7fee8b78c742

## Overview

Six-module, 22-step Intermediate course wrapped in a "ship Nexboard's collaborative cursor tracking" narrative. Module layout: M0 Preflight (2 steps) / M1 First-Fix (4) / M2 CLAUDE.md (4) / M3 Iterate (4) / M4 MCP + Commit Discipline + GHA Capstone (4) / **M6 Agentic Harness** (5 — explicit gap: there is no M5 title; the agentic harness is numbered M6 with step slugs labeled `M5.S3` / `M5.S4` — minor but confusing IA drift). Exercise types used: `concept`, `terminal_exercise` (paste-prompts/diff/transcript), `code_review` (planted bugs), `code_exercise` (Python with hidden pytest tests), `code_read` (exemplar + explanation rubric), `scenario_branch`, `categorization`, `github_classroom_capstone` (validated via the `gha_workflow_check` primitive).

Verdict at a glance: **the agentic harness (M6) is unusually strong — a working Anthropic Messages tool-use loop with `READ_FILE_TOOL` schema, `tool_use_id`, `tool_result`, `stop_reason`, sha256-hash progress detection and a 5-iteration budget. That alone lifts this course above the last "Claude Code" course I reviewed.** The CLAUDE.md exemplar (M2) is also genuinely production-flavored — DO NOT TOUCH list with file:line ranges, Redis TTL gotchas, real sprint context, specific commit-discipline triads. BUT: the team-scale Claude Code surface (hooks, permissions, settings.json, subagent configuration, MCP transport/config) is almost entirely absent — previewed in M1 Step 1 as "what you'll learn" and then never delivered. The MCP module teaches consumption hand-wavily: learners paste a transcript showing `list_recent_tickets` tool_use blocks without ever seeing `claude mcp add`, `mcpServers` in `settings.json`, stdio vs HTTP, or the permission model that lets Claude trust the server.

## Blind-spot coverage

### Blind spot 1 — "Real CLAUDE.md demonstration, not placeholder"
- Covered? **yes**
- Evidence: M2 Step 2 (`85065`, `code_read`) shows a 60+-line production-flavored CLAUDE.md for a Nexboard canvas-collaboration service: project-structure tree, `DO NOT TOUCH` list with line ranges (`src/api/canvas.py lines 45-67 (authentication middleware — Marcus Chen owns this)`), explicit Redis key patterns (`cursor:{canvas_id}`, `presence:{canvas_id}`), testing conventions (`pytest-asyncio`, `fakeredis`, `await cleanup_redis_keys() in teardown or you'll get key collision`), common-pitfall block naming socket event strings verbatim (`cursor_move`, `user_presence`), Redis TTL (`EXPIRE cursor:{canvas_id} 30`), dependency pins, local-dev script. Explanation rubric weights "Technical Specificity" + "Context Gap Analysis" + "Section Purpose Understanding" + "Domain Understanding". This is the single strongest CLAUDE.md artifact I've seen in any of these courses.
- Minor nit: M2 Step 3 "Write CLAUDE.md for the M1 repo" (`85066`) is weirdly framed — it's a Python `code_exercise` asking the learner to write a CLAUDE.md **PARSER** (`read_claude_md`, `extract_sections`, `count_concrete_references`, `is_boilerplate`) rather than actually authoring CLAUDE.md prose. That's a pedagogical detour — writing a markdown-section regex doesn't demonstrate the judgment of deciding what deserves to be in `DO NOT TOUCH` vs. `Common Pitfalls`. Flag for MUST-FIX-before-enrollment: replace this with a paste-based markdown authoring exercise that LLM-rubric-grades against the M2 Step 2 exemplar.

### Blind spot 2 — "Explore vs Plan vs general-purpose subagents with concrete use-this-one-when rules"
- Covered? **no**
- Evidence: The word "subagents" appears exactly once in the course — in the M1 Step 1 concept forward-looking preview ("By Module 6, you'll have: Custom subagents for your team's specific workflows"). M6 is the agentic-harness module (building your OWN tool-use loop); it does not teach Claude Code's built-in subagent mechanism (`/agents`, `.claude/agents/*.md`, `Task` tool, Explore/Plan modes) at all.
- What's missing: the entire Claude-Code subagent surface. `.claude/agents/` directory, agent frontmatter (name/description/tools/model), how to invoke via Task tool, how to parallelize, when to use general-purpose vs a focused subagent, cost/context implications. For a course whose subtitle advertises "custom subagents", this is a central broken promise.

### Blind spot 3 — "Debugging when Claude Code goes off the rails — /clear, @mentions, breaking out of tool-loops, recognizing when to stop delegating"
- Covered? **partial**
- Evidence (+): M3 Step 1 (`85068`, concept "Iterate the prompt, not the output") operationalizes the "fresh session" reflex — explicitly recommends "Rewrite Your Prompt → fresh session → 73% success rate" over "Keep Asking Claude → 85% rebound rate". M3 Step 2 (`85069`, scenario_branch) makes the learner PICK "Stop and rewrite your original prompt with the specific coordinate requirements" vs "Ask Claude to fix one more time" vs "Do it yourself". The scenario's insight text is correct pedagogy: "When Claude gets the architecture correct but implementation details wrong after 2-3 attempts, don't ask for 'fixes' — rewrite your original prompt to include the missing specifics."
- Evidence (−): `/clear` appears nowhere in the course body (only referenced via the exemplary CLAUDE.md in M2's Context-Hygiene callout — and there only as a recommendation INSIDE the fictional CLAUDE.md, not as a taught Claude Code command). `/compact`, `/cost`, `/model`, Esc to break tool-loops, @file mentions for targeted context reload — none appear. M3's "do it yourself" third path does name the "stop delegating" move, which is good — but the mechanics of HOW to recover (abort the tool loop, prune context, restart with richer CLAUDE.md) are never taught.

### Blind spot 4 — "Hooks ergonomically — PostToolUse / Stop / UserPromptSubmit — with actual examples that run, not a settings.json reference dump"
- Covered? **no**
- Evidence: Hooks are mentioned in ONE place — M1 Step 1's forward-looking preview: "By Module 6, you'll have... **PreToolUse hooks that prevent dangerous operations**". M6 delivers an agentic-harness (your own Python loop), not Claude Code hooks. The real Claude-Code hook surface (`PreToolUse` / `PostToolUse` / `Stop` / `UserPromptSubmit` / `SessionStart` / `PreCompact` / `Notification`, the `matcher` field, JSON-over-stdin payload, exit-code semantics for blocking/approving, `${CLAUDE_PROJECT_DIR}`, `hookSpecificOutput.permissionDecision`) is entirely absent.
- What's missing: A hands-on exercise wiring a `PostToolUse` hook that runs `biome check --write` after every Edit, or a `UserPromptSubmit` hook that injects ticket context via `jq`, or a `Stop` hook that runs `pnpm test` at turn-end. Even one runnable example would change the shape of this course's production-readiness. The previewer who said "team-Claude module got merged into M4" overstated it: M4 doesn't contain hooks/settings.json/permissions content — they're simply omitted.

### Blind spot 5 — "MCP capstone teaches the transport distinction (stdio vs HTTP) + the permission model"
- Covered? **no**
- Evidence: M4 Step 1 (`85072`, concept "MCP as team-multiplier") is pedagogically honest about the framing: "most senior engineers will **use** an MCP server, not build one. The value isn't in writing custom MCP servers from scratch — it's in recognizing when your team has repetitive workflows." That framing is actually fair. BUT the subsequent teaching of CONSUMPTION is a black box: M4 Step 3 (`85074`, terminal_exercise) says "Claude Code will register the team-tickets MCP, query it for recent tickets" — register HOW? The bootstrap_command is `git clone … && claude`. No `claude mcp add`, no `claude mcp add-json`, no `.mcp.json`, no `mcpServers` block in `settings.json`, no transport discrimination (`type: "stdio" / "http" / "sse"`), no `command/args/env` for stdio, no `url/headers/oauth` for remote, no per-tool `permissions.allow` list, no `enabledMcpjsonServers`, no `claude mcp list`. The rubric grades "evidence of MCP tool_use blocks in transcript" — meaning as long as the learner pastes `list_recent_tickets` tool_use output (which they get for free from the pre-wired course repo), they pass without understanding any of the wiring that would let them add their own MCP server to a real team.
- What's missing: In a production team, the engineer deciding whether to trust a new MCP server needs to know (a) is it stdio — which runs locally with my privileges — or HTTP — which phones a remote service? (b) which tools does it expose and does my `permissions.allow` pin them? (c) where does Claude persist per-server config: project `.mcp.json`, user `~/.claude.json`, enterprise managed policy? None of these are introduced. A team that enrolls juniors here will get juniors who can USE the pre-wired team-tickets MCP but cannot wire a new one — which was supposed to be the point.
- Blocker rating: this is the most production-critical gap. Even if the course intentionally scopes "consumption not building", the CONSUMPTION pedagogy itself needs the transport + permission surface. Right now it's mystery-meat.

### Blind spot 6 — "What NOT to delegate to Claude Code (security, prod-deploy, org-context-missing decisions)"
- Covered? **partial**
- Evidence: M1 Step 3 (`85063`, concept "Name the gaps you hit") lists "Ignored 'Do Not Touch' Areas" — `"Claude modified the core authentication middleware or suggested changes to the database migration scripts—areas that should be off-limits for this feature."` M3's three-move decision ("keep asking / rewrite / do it yourself") names "do it yourself" explicitly. M2's exemplary CLAUDE.md demonstrates DO NOT TOUCH in context.
- Evidence (−): The course lists CAPABILITY limits (context gaps, hallucinated imports, wrong testing patterns) but rarely TRUST/JUDGMENT limits. No discussion of: (a) don't paste customer PII into transcripts, (b) don't let Claude write the deploy command for prod, (c) don't merge Claude's commit without reading the diff end-to-end (M3 touches this with Sofia Martinez's quote, but no mechanism — like `git diff --stat` before accept — is taught), (d) how to enforce this via `disallowedTools` / `permissions.deny` (which would require teaching settings.json), (e) secret-leak risk from pasted `.env`, (f) force-push / rm -rf / destructive-command guard rails. The course's framing is "AI gives you 70%-right output, iterate the prompt" — it under-teaches "AI gives you 70%-right output on a security-sensitive decision, STOP AND DRIVE DIRECTLY."

### Blind spot 7 — "Token-budget hygiene + context-window reality"
- Covered? **partial**
- Evidence (+): M2 Step 1 concept mentions context hygiene ("Long conversations accumulate confusion. When Claude starts repeating itself, makes basic errors it avoided earlier, or suggests code that contradicts recent corrections, your context window is polluted. Use /clear to start fresh"). That's the right instinct, quoted INSIDE the exemplary CLAUDE.md (so learners see it in context).
- Evidence (−): No concrete numbers (200K context, where degradation starts, cost per turn). `/compact` never mentioned. `/cost` or `/usage` never mentioned. No demonstration of "preloading the whole codebase = anti-pattern". M0's "expected spend $3–8" pricing banner is the only place economics appears — and it's by-module-rollup only, not per-turn awareness.

### Blind spot 8 — "Platform-aware install guidance — macOS / Linux-native / Windows+WSL — and PATH gotchas"
- Covered? **no**
- Evidence: M0 Step 1 is a pre-flight checklist with generic download links ("Download for macOS/Windows/Linux" → claude.ai/download). No platform-branching, no `brew install --cask claude-code`, no `irm https://claude.ai/install.ps1 | iex` for Windows-native, no `npm install -g @anthropic-ai/claude-code` alternative. No mention of PATH refresh (`hash -r`), no Windows Git-for-Windows prerequisite, no `CLAUDE_CODE_GIT_BASH_PATH`. No `claude doctor`.
- What's missing: branching install tabs with the three real fleets (macOS / native Linux / Windows+WSL + native Windows). The v1_cc_terminal course I reviewed on 2026-04-22 at least ATTEMPTED the tab split (even if the commands were wrong); this course skips the exercise entirely and just hands learners a download button.

### Blind spot 9 — "Recovery when install fails (EACCES / shell-hash / node mismatch / expired auth / WSL perf trap)"
- Covered? **no**
- Evidence: M0 Step 2 (`85059`, terminal_exercise "Verify your toolchain") asks the learner to paste the output of `claude --version`, a `claude` query returning "HELLO", `git version`, `python3 --version`, `docker --version`. The validation's `hint` says: "If Claude responds with authentication errors, run 'claude auth' to configure your API key first." That's ONE recovery path and it's wrong — the real command is `claude /login` (or `ANTHROPIC_API_KEY` env var); `claude auth` doesn't exist as a top-level CLI. No discussion of other common failure modes: EACCES on npm global install, Node-version mismatch (Claude Code requires Node 18+), shell-hash cache (`hash -r`), expired session token, WSL2 filesystem-perf trap (don't install into `/mnt/c/...`).
- This is where a junior will get stuck first and the course gives them nothing.

### Blind spot 10 — "Security posture — no API-key input widget, BYO panel only"
- Covered? **yes**
- Evidence: Scanned all 22 steps' `content`, `code`, `demo_data`, `validation` (~139KB of text). Zero password inputs, zero `<input name="api-key">`, zero `localStorage.setItem(...apiKey...)`, zero `sessionStorage.setItem(...apiKey...)`, zero `name="api_key"` fields. M0 Step 1's API-key card points to `https://console.anthropic.com/` only (no input widget on-site). Matches the CLAUDE.md-enforced "never handle learner keys" invariant.

## Additional blind-spot observations (not in the 10-item list, but load-bearing)

### Agentic harness depth (user-flagged check #2) — STRONG
The M6 agentic-harness module exposes the actual Anthropic Messages tool-use primitives. Step `85077` (warm-up, code_exercise) makes the learner implement:
- `READ_FILE_TOOL` JSON schema with `name`, `description`, `input_schema.type="object"`, `required=["path"]`
- `parse_tool_use(response)` that iterates `response.content` blocks checking `block.type == 'tool_use'`, returning `{id, name, input}`
- `build_tool_result(tool_use_id, content, is_error)` with shape `{type: "tool_result", tool_use_id, content, is_error?}`
- `run_tool_roundtrip` orchestrating: first `client.messages.create(messages=[...], tools=[READ_FILE_TOOL])` → parse tool_use → execute locally → re-call with `messages = [user_prompt, assistant_prior_response, user_tool_result]` → return `{final_text, stop_reason}`

Step `85078` (autocorrect loop) adds:
- 5-iteration budget
- sha256 progress detection (`sha256(error_output)` — if consecutive iterations hash-match, stop with `"stuck: no progress"`)
- Three stop conditions: `success` / `budget_exhausted` / `stuck: no progress`

These are the real primitives. A learner who writes this and passes the hidden tests understands the raw Messages API tool-use cycle, not a chat abstraction. This module answers "does M5/M6 expose actual primitives?" with YES.

One critique: the mock `execute_tool('run_tests')` returns a hardcoded `"FAILED: test_example failed - expected 42, got 0"`, which makes the `stuck` detection trivially fire on every iteration. The test `test_loop_early_stops_on_repeated_error` works because the same hardcoded string hashes the same. In the real world, pytest output changes on EVERY run due to timestamps / random-seed / ANSI colors. The course should teach normalization (strip timestamps, sort failures, extract the traceback's last frame) before hashing — otherwise a trivial `tee -a test.log` difference defeats progress detection. Fixable via a one-paragraph "Normalize before you hash" sidebar.

### MCP consumption pedagogy (user-flagged check #1) — TOY
Despite the fair framing ("most senior engineers USE an MCP, not build one"), the consumption teaching is surface: register-call → paste transcript → rubric greps for `list_recent_tickets` in the output. The mechanics (mcpServers block, transport selection, permission allow-list, auth for remote servers) are invisible. A learner who "passes" M4 Step 3 cannot add an MCP server to their own team's `settings.json`. See blind spot 5 above.

### Team-scale Claude Code surface (user-flagged check #3) — DROPPED, not merged
The previous UX reviewer said the team-Claude module was merged into M4. My grep across all 22 steps finds zero hits for `hooks` (beyond the M1 preview), `permissions`, `settings.json`, `.claude/settings`, `mcpServers`, `stdio`, `transport`, `claude mcp add`, `json-rpc`, `tools/list`, `subagent` (beyond the M1 preview), `agents.json`, `.claude/agents`. The team-scale surface wasn't merged — it was removed. The course previews it in M1 Step 1 ("By Module 6 you'll have... hooks that prevent dangerous operations... custom subagents") and then breaks the promise.

### Commit discipline (user-flagged in brief) — LIGHT
M4 Step 1 concept names a three-commit pattern (`feat: add WebSocket cursor position schema (Claude)` / `feat: implement cursor broadcast logic (human + Claude)` / `fix: handle Redis connection failures (human)`) and the M4 Step 3 rubric weights "three atomic commit messages that are specific and atomic (not generic like 'update stuff')". That's a decent shape for the discipline, but nothing enforces it — the GHA capstone (`85075`) validates `required_conclusion: success` on the lab-grade.yml workflow, not commit-message shape. Learners will paste three atomically-named commits, pass the `must_contain: ["commit"]` check, and the graders will move on. In practice commit discipline is grade-in-name-only.

### GHA capstone (user-flagged in brief) — GOOD SHAPE, THIN SUBSTANCE
M4 Step 4 (`85075`, `github_classroom_capstone`) uses the platform's `gha_workflow_check` validation primitive (from the F24 architecture work in CLAUDE.md) — the learner pushes to a fork, pastes the Actions run URL, backend calls `GET /repos/{owner}/{repo}/actions/runs/{run_id}` and asserts `conclusion=success`. That's the right architecture for grading heavy-infra capstones. BUT the repo `skills-lab-demos/aie-course-repo` is external and not inspectable from here — the rubric doesn't show what `lab-grade.yml` actually checks beyond "Socket.io connection stability tests". Without seeing the workflow, I can't validate whether it runs real tests, or whether the learner could simply git-push their own `lab-grade.yml` that `exit 0`'s and pass. Flag: add an `expected_workflow_sha` or `grading_job` pin to the validation (the CLAUDE.md F24 architecture supports `grading_job: "grade"` — use it). M6 Step 5's GHA check has the same gap.

### Cross-domain narrative discipline — STRONG
Consistent cast: Marcus Chen (EM), Sofia Martinez (Senior Frontend), Alex Rodriguez (schema owner), David Kim (PM), Rachel Thompson (Designer), Nexboard canvas-collab context. Real names weave through CLAUDE.md, the M1 story, M3 iteration narrative, M4 PR review. No persona drift between modules. This is a meaningful production-readiness signal because it models the real-world fact that team context IS the context Claude needs.

## Axis scores

- `technical_accuracy`: **0.62**
  - (+) Agentic loop primitives are correct: tool_use_id, tool_result shape, stop_reason, messages=[user, assistant_prior_content, user_tool_result] re-call pattern — this is Anthropic's real Messages API.
  - (+) CLAUDE.md exemplar is technically accurate (real Redis command patterns, real pytest-asyncio usage, real migration/fixture naming).
  - (−) M0 Step 2 validation hint says "run `claude auth`" — that's not a real Claude Code command (real is `claude /login` / `ANTHROPIC_API_KEY` env).
  - (−) MCP section talks about "Claude Code will register the team-tickets MCP" with no mechanism — the actual registration (`claude mcp add --scope project --transport stdio team-tickets -- python -m team_tickets_mcp`, or `.mcp.json`) never appears.
  - (−) Hooks / settings.json / permissions / subagents → promised in M1 Step 1 preview, not delivered anywhere. Broken contract with the learner.

- `production_readiness`: **0.55**
  - (+) The GHA capstone architecture (`gha_workflow_check` validation) is the right pattern for grading real infra work. The course uses it correctly in M4 + M6.
  - (+) M2's CLAUDE.md has sprint-context section, DO-NOT-TOUCH with file:line ranges, real test-cleanup gotchas — these are the production details juniors miss.
  - (−) The big team-scale production surface (hooks / permissions / team-shared `.claude/settings.json` / org-managed `managed-settings.json` / `.mcp.json` checked into the repo) is entirely absent. A junior who finishes this course cannot land a Claude-Code-augmented workflow at a team of 20+.
  - (−) MCP consumption taught as "the transcript shows tool_use blocks" — doesn't prepare a learner to trust a new MCP, or to choose between a stdio server running with their privileges and an HTTP server phoning a remote service.
  - (−) Install/recovery story is pre-flight only. A junior whose `claude` shell-hash isn't refreshed or whose WSL filesystem is slow will bounce off M0.

- `failure_mode_coverage`: **0.58**
  - (+) M3's "70%-right trap" + scenario_branch + categorization trio teaches the real failure mode of "iterate the prompt, not the output" with concrete realistic outputs. M3 Step 3 categorization (`85071`, "Classify 6 real 70%-right outputs") is the single most-pedagogically-honest step in the course — learners categorize into {Re-prompt, Verify-and-keep, Rewrite yourself} against realistic 70%-right AI outputs.
  - (+) M4's code_review `85073` plants realistic AI bugs: hallucinated httpx method `client.get_avatar_url(user_id)` (real httpx uses `client.get(url)`), missing Redis TTL on cursor data, blocking external API call inside a WebSocket event handler, missing cleanup on disconnect. Those are the actual failure modes of 80%-Claude-generated PRs.
  - (+) M1's planted-bug code_review `85062` similarly real: "Cache user presence in Redis indefinitely" (no TTL), disconnect handler where `userId not available`, unparameterized SELECT (though it does use `$1` placeholder, so false alarm).
  - (−) Missing failure modes: (a) tool-loop thrashing mid-session (no Esc / abort coverage), (b) context-window exhaustion (`/compact`, `/clear`), (c) secret-leak via pasted transcripts, (d) CI-grader-gaming (push a trivial `lab-grade.yml` that exits 0), (e) hallucinated MCP tool names that don't exist on the server.
  - (−) M6's sha256 progress detection will false-negative on any test output with timestamps or random-seeded outputs; the course doesn't teach normalization.

- `tradeoff_articulation`: **0.68**
  - (+) M3 Step 1 concept explicitly contrasts three paths with rebound rates (85% for keep-asking, 73% success for rewrite, sometimes-fastest for do-it-yourself). That's tradeoff discourse done right.
  - (+) M0 Step 1's budget strategy selector (Budget Haiku-only / Balanced / Premium) makes learners pick cost/capability tradeoffs consciously — not hidden.
  - (+) M4 Step 1 honestly concedes "most senior engineers will USE an MCP, not build one" — that's a real pedagogy tradeoff the course OWNS rather than hand-waves.
  - (+) M6 Step 4 rubric specifies "Thoughtful analysis of whether human intervention would have helped" — graded on the learner's tradeoff reasoning, not just code output.
  - (−) No discussion of WHICH MCP transport to pick when (stdio vs HTTP, per-project `.mcp.json` vs user-level `settings.json` vs managed-enterprise).
  - (−) No discussion of model choice per module beyond the M0 pricing banner — no "use haiku when rewriting small diffs, sonnet when building a new module" guidance at the exercise level.

- `security_posture`: **0.80**
  - (+) BYO-key enforcement is textbook clean: zero password inputs, zero localStorage slots, zero key-in-request fields, zero `name="api_key"` forms across the entire course. The hard-rule invariant holds.
  - (+) M2's exemplary CLAUDE.md models a `DO NOT TOUCH` list that includes "`app/config/secrets.py` - Contains production API keys" — the ONE place secret handling is modeled correctly.
  - (−) No teaching of Claude Code's `permissions.deny` / `disallowedTools` as a secret-leak defense (would need the settings.json surface the course skipped).
  - (−) M4 Step 4's `github_classroom_capstone` asks learners to paste a GitHub Actions run URL; no guard against learners pasting private-repo URLs where the grader's API call will fail. The rubric should nudge toward public fork to avoid token-sharing temptation.
  - (−) No mention of secret-leak risk from pasted transcripts. Given the course's paste-heavy validation pattern (3 paste_slots per terminal_exercise), a "redact before paste" sidebar would be essential.

## Weighted score
technical_accuracy × 25% + production_readiness × 25% + failure_mode_coverage × 20% + tradeoff_articulation × 15% + security_posture × 15%
= 0.62·0.25 + 0.55·0.25 + 0.58·0.20 + 0.68·0.15 + 0.80·0.15
= 0.155 + 0.1375 + 0.116 + 0.102 + 0.120
= **0.6305 / 1.00**

## Verdict

### ⚠ CONDITIONAL (score 0.63; in the 0.60–0.74 band)

The course's narrative discipline, CLAUDE.md exemplar, and agentic-harness module are at a senior standard. The failure mode is that it previews a broader team-scale surface (hooks / permissions / subagents / settings.json / MCP wiring) that it then doesn't deliver. A junior finishes this course competent at iterating prompts and writing a tool-use loop from scratch — but cannot land a Claude-Code-augmented workflow onto a 20+ person team, cannot wire a new MCP, cannot author a hook that runs `biome check` after every edit, and cannot reason about whether a new `mcpServers` entry is safe to trust.

### MUST FIX before approval (enrollment blockers for my team)

1. **Deliver the promised team-scale Claude Code module OR remove the preview**. M1 Step 1 preview promises "Custom subagents for your team's specific workflows" + "PreToolUse hooks that prevent dangerous operations". Neither lands. Either add a module (at minimum: `.claude/settings.json` schema, one runnable PostToolUse hook, one `.claude/agents/*.md` subagent config, the permission `allow`/`deny` list discipline) or rewrite the preview to promise only what the course delivers.
2. **Teach MCP CONSUMPTION with real wiring**, not the black box. At minimum: a 10-line concept card showing the `mcpServers` block for a stdio server (`{"command": "python", "args": ["-m", "team_tickets_mcp"], "env": {...}}`), one showing an HTTP/SSE server with `type: "http"` + `url` + `headers`, and the `permissions.allow` discipline for pinning which MCP tools are trusted. Currently a learner who passes M4 cannot add an MCP to their own `settings.json`.
3. **Rewrite M2 Step 3 ("Write CLAUDE.md for the M1 repo")** from its current Python-parser-exercise form to a paste-based markdown authoring exercise. Grade via LLM rubric against the M2 Step 2 exemplar. The current form tests regex skills, not CLAUDE.md judgment.
4. **Fix the M0 Step 2 validation hint**: `claude auth` is not a real command. Use `claude /login` or `export ANTHROPIC_API_KEY=...`. A learner whose first interaction with the CLI is running a fictional command has a broken trust signal before they even start.
5. **Add a teach-moment for tool-output normalization before hashing** in M6 Step 2. Real pytest output has timestamps/ANSI/random-seed variance; naive sha256 progress-detection false-negatives on any realistic output. One paragraph + one canonical normalizer (strip timestamps, sort failures, last-traceback-frame only) would make the autocorrect loop production-grade instead of demo-grade.

### SHOULD FIX but non-blocking

6. Fix IA numbering: the course jumps M4 → M6 with no M5. Step slugs in M6 are labeled `M5.S3` / `M5.S4`. Rename module to M5 and update slugs.
7. Add a `/clear`, `/compact`, `/cost`, `@file` mini-lesson in M3 — the "iterate the prompt" module is the natural home for context-hygiene commands.
8. Add platform-tab install guidance in M0 (macOS `brew install --cask claude-code`, native-Linux `npm i -g`, Windows-native `irm install.ps1 | iex`, WSL2 filesystem-perf warning).
9. Add one failure-recovery playbook in M0 (EACCES on npm global, `hash -r` for shell cache, `claude doctor`, Node 18+ requirement, expired auth refresh).
10. Pin the GHA `grading_job` in M4 Step 4's `gha_workflow_check` validation so a learner can't ship a `lab-grade.yml` that `exit 0`'s and passes. The F24 architecture in CLAUDE.md already supports `grading_job: "grade"` — use it.
11. Add a "what NOT to paste" security sidebar to every terminal_exercise (transcripts can leak `.env`, DB URLs, session tokens, customer data).
12. Add `disallowedTools` / `permissions.deny` teaching as a secret-leak defense once the settings.json surface is added per MUST-FIX #1.

## One-line executive summary for the Creator team

The agentic harness (M6) and CLAUDE.md exemplar (M2) are production-grade; the course REJECTS on its unfulfilled preview-promise of team-scale Claude Code — hooks, permissions, settings.json, subagent configuration, and MCP wiring are previewed in M1 and never delivered. Add a real "team-Claude" module (runnable PostToolUse hook + one `.claude/agents/*.md` config + `mcpServers` stdio+HTTP examples + `permissions.allow` discipline) or remove the preview, then re-review.
