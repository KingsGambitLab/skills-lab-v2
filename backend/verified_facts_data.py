"""Tech-specific verified-facts data — the actual facts blocks + drift
patterns for every registered tech.

This file is imported once at module load and registers everything via
`register_tech(...)`. To add a new tech:

  1. Append a new `register_tech(...)` call below.
  2. That's it. Creator prompt + drift gate + CI all pick it up.

To grow an existing tech's drift coverage (because production caught a
new drift pattern):

  1. Append a new `(regex, message, ignore_case)` tuple to the relevant
     entry's `drift_patterns` list.
  2. Re-run tools/regression_check.py to confirm no false positives + the
     new pattern catches what it should.

Pattern: REGEX | MESSAGE | IGNORE_CASE_FLAG.
  - ignore_case=False when distinguishing product name vs subcommand
    (e.g. "Claude Code" vs `claude code`).
  - ignore_case=True for slugs/paths where case carries no semantic
    weight (e.g. `kimi-k2-0905`, `.aider/commands/`).
"""
from __future__ import annotations

from .verified_facts import register_tech


# ═══════════════════════════════════════════════════════════════════════
# CLAUDE CODE
# ═══════════════════════════════════════════════════════════════════════

_CLAUDE_CODE_FACTS = """
CLAUDE CODE REFERENCE FACTS (v2026-04 — QUOTE VERBATIM, do not paraphrase):

=== Authentication ===
- Interactive:   `claude /login`            (OAuth flow; opens browser)
- Headless / CI: set env var `ANTHROPIC_API_KEY=<your-key>`
- There is NO `claude auth`, `claude login` (no slash), `claude signin`,
  or `claude configure` subcommand.

=== Built-in tool names (capitalized in subagent YAML + settings.json) ===
Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebFetch, WebSearch, Task,
NotebookEdit, TodoWrite. Do NOT use `read_file`, `edit_file`, `bash`
(lowercase). Do NOT use `str_replace_editor` — that's the Anthropic API
computer-use tool type, not a Claude Code tool.

=== Hook contract ===
- Hooks are SHELL SCRIPTS (or any executable) that read stdin JSON +
  exit with a status code. NOT Python functions returning JSON.
- stdin: `{"tool_name": "Edit", "tool_input": {"file_path": "/x", ...}}`
- stderr: human-readable reason text (shown to model on block)
- exit codes: 0=allow, 2=BLOCK, 1/other=warn-only (does NOT block)
- DO NOT use `exit 1` to block — it warns, doesn't block.

=== settings.json shape (frequently hallucinated) ===
CORRECT:
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit", "hooks": [{"type": "command", "command": "..."}]}
    ]
  },
  "permissions": {"allow": [...], "deny": [...]}
}
WRONG: `pre_tool_use` (snake_case), `subagents` map, `permissions.file_operations.*`,
`permissions.system_commands.*`. Subagents are auto-discovered from
`.claude/agents/*.md`, NOT registered in JSON.

=== MCP wiring ===
- Add: `claude mcp add <name> <command-or-path> [--transport stdio|http]`
- Verify: `claude mcp list` (shell) or `/mcp` (slash inside session)
- DO NOT concatenate: `claude /mcp list` is invalid. Either shell form
  (`claude mcp list`) OR slash form (`/mcp`).
- DO NOT pass URLs as the SOLE arg: `claude mcp add <https-url>` is wrong.
- Per-project: hand-write `.mcp.json` with `mcpServers.<name>`.

=== Custom subagents ===
File: `.claude/agents/<slug>.md` with YAML frontmatter:
  name, description, tools (capitalized list), model, maxTurns
  (NOT max_tokens, NOT system_prompt, NOT allowed_tools)
Auto-discovered. NO `subagents` registration in settings.json.

=== Invocation forms ===
- `claude` (REPL) or `claude -p "<prompt>"` (one-shot)
- `claude '<prompt>'` (no -p) is NOT one-shot — opens REPL, prompt ignored
- There is NO `claude code` subcommand. Product name is "Claude Code"
  (Title Case prose); the CLI is `claude` (no subcommand). Don't write
  `$ claude code` in instructions.
- Claude Code is a CLI installed via npm or curl, NOT a desktop app.
  Don't link to claude.ai/download. Real install:
    npm install -g @anthropic-ai/claude-code
    curl -fsSL https://claude.ai/install.sh | bash

=== Custom slash commands ===
File: `.claude/commands/<name>.md` with `$ARGUMENTS` interpolation.
NO `{{className}}` Mustache templating; NO `Arguments:` body field.
"""

_CLAUDE_CODE_DRIFTS = [
    # (pattern, message, ignore_case)
    (r"(?:[\$>]\s*|<code[^>]*>|<pre[^>]*>[^<]*?)\bclaude\s+code\b",
     "uses `claude code` as if it were a subcommand (in shell prompt or code block). The CLI is `claude` (no subcommand). Use `claude` for REPL or `claude -p '<prompt>'` for one-shot.",
     False),
    (r"claude\s*/mcp\s+\w",
     "concatenates `claude /mcp <arg>` — that's neither valid form. Use the SHELL form `claude mcp <subcommand>` OR the SLASH form `/mcp` inside an interactive Claude session, never both.",
     True),
    (r"\bclaude\s+auth\b",
     "uses `claude auth` — invented subcommand. Use `claude /login` (interactive) or `ANTHROPIC_API_KEY` env var (headless).",
     True),
    (r"claude\s+code\s*\(?\s*desktop\s*\)?",
     "calls Claude Code 'Claude Code Desktop' or 'Claude Code (Desktop)' — Claude Code is a CLI, not a desktop app.",
     True),
    (r"claude\.ai/download",
     "links to claude.ai/download as the Claude Code install URL — wrong product. Real install: `npm install -g @anthropic-ai/claude-code`.",
     True),
    (r"str_replace_editor",
     "references `str_replace_editor` as a Claude Code tool name. That's an Anthropic API computer-use tool type. Use capitalized real tools: `Edit`, `Write`, `Read`, `Bash`.",
     True),
    (r'"matcher"\s*:\s*"(?:read_file|edit_file|bash|read|write|edit|grep|glob)"',
     "uses lowercase tool names in a hook matcher — Claude Code tool names are CAPITALIZED in settings.json (`Edit`, `Write`, `Bash`, `Read`, `Grep`, `Glob`).",
     False),
    (r'"hooks"\s*:\s*\{\s*"pre_tool_use"',
     "uses snake_case `pre_tool_use` in settings.json — events are PascalCase (`PreToolUse`, `PostToolUse`, `Stop`).",
     True),
    (r'"subagents"\s*:\s*\{',
     "puts a `subagents` map in settings.json — fictional structure. Subagents are auto-discovered from `.claude/agents/*.md` files.",
     True),
    (r'"file_operations"\s*:\s*\{[^}]*"allowed_extensions"',
     "uses `permissions.file_operations.allowed_extensions` — invented schema. Real shape: `permissions.allow: [...]`.",
     True),
    (r'"system_commands"\s*:\s*\{[^}]*"allowed"',
     "uses `permissions.system_commands.allowed` — invented schema. Real: `permissions.allow: [\"Bash(...)\"]`.",
     True),
    # Hook example uses `exit 1` to "block" — context-dependent
    (r"(?:hook|guardrail|block).{0,400}(?:\bexit\s+1\b|\b(?:sys\.)?exit\s*\(\s*1\s*\))",
     "hook example uses `exit 1` to block — that does NOT block, it warns. Use `exit 2` to block (verified facts).",
     True),

    # ── 2026-04-25 v8.7 expert re-review additions (compounding) ──
    # AIE M6.S5 regressed by emitting `.claude/subagents.json` + `.claude/hooks.json`
    # as separate files. Real Claude Code uses INDIVIDUAL `.claude/agents/*.md`
    # files for subagents, and hooks live INSIDE `settings.json` under `hooks.PreToolUse`.
    (r"\.claude/subagents\.json\b",
     "writes a `.claude/subagents.json` file — that file does NOT exist. Subagents are individual Markdown files at `.claude/agents/<slug>.md`, auto-discovered.",
     True),
    (r"\.claude/hooks\.json\b",
     "writes a `.claude/hooks.json` file — fictional. Hooks live INSIDE `settings.json` at `hooks.PreToolUse: [{matcher, hooks: [{type:\"command\", command}]}]`.",
     True),
    # Invented slash commands flagged by AIE expert
    (r"claude\s*/settings\s+(?:reload|show|validate)",
     "uses `claude /settings reload|show|validate` — invented slash commands. There is no `/settings` slash command for these. To reload settings, restart the session; to inspect, read `~/.claude/settings.json` or `<project>/.claude/settings.json` directly.",
     True),
    # Invented CLI flag for subagents
    (r"claude\s+--subagent\s+\S",
     "uses `claude --subagent <name>` — invented flag. To spawn a session under a custom subagent, use `claude --agent <name>` (the real flag).",
     True),
    # Claude Desktop conflation — `mcpServers` JSON shown as Claude CODE config
    # (it's the schema for Claude DESKTOP). Real Claude Code MCP wiring is via
    # `claude mcp add ... --transport stdio` OR a project `.mcp.json`.
    (r'(?i)claude\s+code.{0,300}"mcpServers"\s*:\s*\{',
     "shows a `mcpServers` JSON block in a Claude Code context. That schema lives in Claude DESKTOP's config (claude_desktop_config.json), not Claude Code. Claude Code uses `claude mcp add <name> <command> --transport stdio` OR a project `.mcp.json` file.",
     True),
    # Haiku 3 pricing labeled as Haiku 3.5 (model pricing drift — Anthropic
    # changed price ladder when 3.5 launched). Haiku 3 was $0.25/$1.25 per M;
    # Haiku 3.5 is $0.80/$4. Catch the old prices when course mentions 3.5.
    (r'(?i)haiku.{0,60}3\.5.{0,400}\$\s*0\.25.{0,40}\$\s*1\.25',
     "labels a cost calculator with Haiku 3 pricing ($0.25 in / $1.25 out) while the course names Haiku 3.5. Haiku 3.5 is $0.80 in / $4.00 out per million tokens.",
     True),
    (r'(?i)\$\s*0\.25\s*(?:in)?\s*/\s*\$\s*1\.25\s*(?:out)?.{0,200}haiku',
     "associates Haiku-3 prices ($0.25/$1.25) with a Haiku label — Anthropic Haiku-3.5 prices are $0.80/$4.00 per million tokens.",
     True),
    # Shebang/language mismatch in hook scripts (caught by AIE M6.S2 review)
    # — `#!/bin/bash` immediately followed by Python imports.
    (r"#!/bin/bash.{0,80}\n\s*(?:import\s+\w+|from\s+\w+\s+import|def\s+\w)",
     "starter has `#!/bin/bash` shebang followed by Python code — file is unrunnable. Either change shebang to `#!/usr/bin/env python3`, or rewrite the body in bash.",
     True),
]

register_tech(
    tech_id="claude_code",
    # Buddy-Opus 2026-04-25: tightened scope markers. Dropped "anthropic api"
    # and "anthropic claude" — too broad, would match any course that
    # mentions the API in passing without teaching Claude Code specifically.
    # The remaining markers each REQUIRE the course to be teaching Claude
    # Code as a tool, not just referencing it.
    scope_markers=(
        "claude code", "claude-code",
        "@anthropic-ai/claude-code", "claude /login", "claude.ai/code",
        "ai-augmented engineering", "byo-key claude", "byo claude key",
    ),
    facts_block=_CLAUDE_CODE_FACTS,
    drift_patterns=_CLAUDE_CODE_DRIFTS,
)


# ═══════════════════════════════════════════════════════════════════════
# AIDER + open-router-routed models (Kimi K2)
# ═══════════════════════════════════════════════════════════════════════

_AIDER_FACTS = """
AIDER REFERENCE FACTS (v2026-04 — QUOTE VERBATIM, do not paraphrase):

=== Real Aider in-session commands (the FULL list) ===
/help, /add, /drop, /clear, /reset, /run, /test, /commit, /diff, /undo,
/architect, /code, /ask, /chat-mode, /editor, /lint, /load, /save, /tokens,
/voice, /web, /ls, /git, /report, /settings, /model, /multiline-mode,
/think-tokens, /reasoning-effort, /copy, /paste, /context, /map, /map-refresh,
/copy-context, /exit, /quit
There is NO /plan, /scaffold, /refactor, /review.

=== /load + /save ===
- `/save <file>` — saves CURRENT SESSION'S slash-command HISTORY to a file
- `/load <file>` — REPLAYS slash-command history from such a file
- /load does NOT load arbitrary text/markdown into context. It does NOT
  inject "prompt templates" into your message.
- For prompt templates: use `/read <file>` (injects as read-only context),
  OR `aider --message-file <file>` at the shell.

=== `.aider/commands/` does NOT exist ===
- No "custom commands" feature stored at `.aider/commands/<name>.md`.
- Store reusable prompts at any path (e.g. `prompts/<name>.md`); inject via
  `--message-file` or `/read`.

=== Project conventions file ===
- Aider docs say `CONVENTIONS.md`; community standard is `AGENTS.md`.
- Declared in `.aider.conf.yml` via `read: AGENTS.md` (or any path).
- DO NOT call this file `CLAUDE.md` in an Aider course.

=== Model routing — OpenRouter (canonical) ===
- `--model openrouter/<provider>/<model>` + `OPENROUTER_API_KEY`
- For Kimi K2: `--model openrouter/moonshotai/kimi-k2`
- DO NOT use `kimi-k2-0905`, `kimi-k2-latest`, `kimi-k2-0711` — date-stamped
  variants. Canonical is `moonshotai/kimi-k2` (no date).

=== Non-canonical OpenAI-compatible passthrough ===
- `--openai-api-base https://openrouter.ai/api/v1 --model openai/<slug>`
  works (LiteLLM passthrough) but uses `OPENAI_API_KEY` (counter-intuitive).
- Prefer canonical `--model openrouter/...` + `OPENROUTER_API_KEY`.

=== Mode primitives ===
- /architect (plan-only), /code (direct edit), /ask (read-only Q&A)
- /chat-mode <code|architect|ask|help|context> to switch mid-session

=== Cost telemetry ===
- /tokens — prints session token use + estimated cost. Teach this in
  cost-conscious courses.
"""

_AIDER_DRIFTS = [
    (r"kimi-k2-0\d{3}\b|kimi-k2-latest\b|kimi-k2-0711\b",
     "uses a date-stamped Kimi K2 slug. The canonical OpenRouter slug is `moonshotai/kimi-k2` — use the unversioned form for stability.",
     True),
    (r"/load\s+\S*\.(?:md|txt|prompt)\b",
     "teaches `/load <prompt-file>.md` — that's NOT how /load works. /load replays slash-command history; use `/read <file>` or `aider --message-file <file>`.",
     True),
    (r"\.aider/commands(?:/|\b)",
     "references `.aider/commands/` directory — fictional. Aider has no 'custom commands' feature at that path.",
     True),
    (r"--openai-api-base.{0,200}OPENAI_API_KEY",
     "teaches `--openai-api-base` + `OPENAI_API_KEY` for OpenRouter — non-canonical LiteLLM passthrough. Use `--model openrouter/...` + `OPENROUTER_API_KEY`.",
     True),
    (r"\bCLAUDE\.md\b",
     "uses CLAUDE.md as the project-conventions file in an Aider course — that's the Claude-Code-specific name. Aider docs say `CONVENTIONS.md`; community standard is `AGENTS.md`.",
     False),
    (r"aider\s+0\.4[0-9]\b|aider\s+0\.5[0-9]\b",
     "pins to a stale Aider version (0.4x / 0.5x). Use 'Aider 0.86+' or 'any recent Aider' instead.",
     True),

    # ── 2026-04-25 v8.7 Kimi expert re-review additions (compounding) ──
    # `.aider.conf.yml` invented keys flagged by Kimi expert (M2.S1):
    #   - `context-files:` — not a real key; should be `read:`
    #   - bare `test:` (not `test-cmd:` or `auto-test: true`)
    #   - bare `lint: true` boolean (not `auto-lint: true` / `lint-cmd: "..."`)
    (r"^\s*context-files\s*:",
     "uses `context-files:` in .aider.conf.yml — not a valid key. Correct key is `read: <path>` (or list of paths).",
     False),
    (r"^\s*test\s*:\s*[\"'].{1,80}[\"']\s*$",
     "uses bare `test:` key in .aider.conf.yml — not a valid key. Correct: `test-cmd: \"pytest -xvs\"` plus `auto-test: true`.",
     False),
    (r"^\s*lint\s*:\s*(?:true|false)\s*$",
     "uses bare `lint: true|false` in .aider.conf.yml — not a valid key. Correct: `auto-lint: true` (bool) OR `lint-cmd: \"ruff check\"` (string).",
     False),
    # Hybrid OpenRouter syntax — uses canonical `openrouter/...` prefix AND
    # `--openai-api-base` flag together. Pick one path: canonical or LiteLLM
    # passthrough. M0.S2 review caught this.
    (r"--model\s+openrouter/\S+.{0,300}--openai-api-base",
     "mixes canonical `openrouter/<model>` prefix WITH `--openai-api-base` flag — pick one path. Canonical form: `--model openrouter/moonshotai/kimi-k2` + `OPENROUTER_API_KEY` (NO --openai-api-base needed).",
     True),
]

register_tech(
    tech_id="aider",
    # Buddy-Opus 2026-04-25: tightened scope markers. Dropped bare
    # "openrouter" — OpenRouter is used by many tools (Claude, Cursor,
    # litellm-routed apps); a course mentioning it isn't necessarily an
    # Aider course. Kept the Kimi K2 markers because they ARE specific to
    # this course family (Kimi+Aider+OpenRouter is the only stack we ship).
    scope_markers=(
        "aider", ".aider.conf", "aider-chat", "aider.chat",
        "kimi k2", "kimi-k2", "moonshotai/kimi",
    ),
    facts_block=_AIDER_FACTS,
    drift_patterns=_AIDER_DRIFTS,
)


# ═══════════════════════════════════════════════════════════════════════
# To add a new tech, paste a register_tech(...) block here.
# Examples we'll likely need next:
#   - kubernetes / kubectl (kubectl deploy doesn't exist; etc.)
#   - terraform (resource block syntax; provider versioning)
#   - aws_cli (subcommand families; --profile vs $AWS_PROFILE)
#   - docker (BuildKit syntax; bind-mount semantics)
#   - postgres (\d psql backslash commands; SQL syntax)
#
# These will be added when courses covering them surface drift in
# production review. The registry pattern means each addition is one
# block here, no main.py edits.
# ═══════════════════════════════════════════════════════════════════════
