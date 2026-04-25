# Claude Code — Canonical Reference (cached 2026-04-25)

Source: https://docs.claude.com/en/docs/claude-code, https://code.claude.com/docs/en
Claude Code version: 2.x (current as of cache date)

This file is the GROUND-TRUTH input for the Claude Code TechSchema. Edit only
when canonical docs change. Reactive findings from review go in the schema's
`additional_drifts` field with provenance, not here.

---

## CLI binary

The binary is `claude`. There is NO `claude code` subcommand. "Claude Code"
is the product name; the CLI is `claude` (no subcommand).

Install:
```
npm install -g @anthropic-ai/claude-code
# OR
curl -fsSL https://claude.ai/install.sh | bash
```

Claude Code is a CLI / terminal app. It is NOT a desktop application.
Don't conflate with "Claude Desktop" (claude.ai/download) — that's the
separate Claude.ai chat app.

## Invocation forms

```
claude                          # opens REPL
claude -p "<prompt>"            # one-shot mode (also: --print)
claude --resume                 # resume last session
claude --continue               # alias
claude --model <name>           # set model for session (sonnet|opus|haiku|<full-id>)
claude --agent <name>           # spawn a session under a custom subagent
claude --output-format json     # one-shot with JSON output
claude --max-turns N            # limit turns in agentic mode
```

NOT real:
- `claude code <args>` — the binary is `claude`, no subcommand
- `claude '<prompt>'` (no -p) — without -p, opens REPL and ignores positional
- `claude auth`, `claude login`, `claude signin`, `claude configure` — no such subcommands
- `claude --subagent <name>` — real flag is `--agent` (no `sub` prefix)

## Authentication

Interactive (opens browser for OAuth):
```
claude /login
# (entered AT THE > PROMPT INSIDE Claude Code)
```

Headless / CI:
```
ANTHROPIC_API_KEY=<key>
```

NOT real:
- `claude auth login`, `claude auth setup` — no auth subcommand
- `claude --api-key <key>` — use env var
- `claude.ai/download` as install URL — that's Claude Desktop

## CLI subcommands (the COMPLETE list)

```
claude mcp <subcommand>         # MCP server management
claude config <subcommand>      # config inspection
claude help [topic]             # help
claude version                  # show version
claude doctor                   # diagnostic
```

`claude mcp` subcommands:
```
claude mcp add <name> <command-or-path> [args...] [--transport stdio|http]
claude mcp list
claude mcp remove <name>
claude mcp serve <name>         # for stdio servers
```

`claude mcp add` examples:
```
claude mcp add team-tickets python -m team_tickets_mcp --transport stdio
claude mcp add my-server /abs/path/server.py --transport stdio
claude mcp add api-server https://example.com/mcp --transport http
```

NOT valid:
- `claude mcp install <github-url>` — no `install` subcommand
- `claude mcp add <https-url-only>` — URL must be paired with a NAME first
- `claude /mcp list <args>` (concatenating shell + slash form) — pick one:
  shell `claude mcp list` OR slash `/mcp` inside REPL

`claude config` subcommands:
```
claude config get <key>
claude config set <key> <value>
claude config list
```

NOT valid:
- `claude /settings reload`, `/settings show`, `/settings validate` — no /settings slash
- `claude --reload-settings` — restart the session instead

## Slash commands (entered AT > PROMPT INSIDE Claude Code, NOT at the shell)

Built-in:
```
/login         # OAuth flow
/logout        # clear creds
/clear         # clear context
/help          # show commands
/mcp           # show MCP server status (NOT /mcp list — bare /mcp)
/agents        # show available subagents
/model         # show / switch model
/init          # initialize a CLAUDE.md
/pr_comments   # review PR comments
/cost          # show session cost
/exit          # exit
```

Custom slash commands live at `.claude/commands/<name>.md`:
```markdown
---
description: Audit a Spring Boot controller for prod risks
argument-hint: [controller-class-name]
---
Audit the $ARGUMENTS controller for missing @Valid, unhandled exceptions, ...
```

Argument substitution: `$ARGUMENTS` (full blob), `$0`, `$1`, `$2` (positional).
NO Mustache `{{className}}` templating.

NOT real:
- `/settings reload|show|validate`
- `/save_session`, `/restore`, `/pause` (no such commands)

## Built-in tool names (CAPITALIZED in subagent YAML + settings.json)

```
Read           # read a file
Write          # write a new file
Edit           # edit an existing file
MultiEdit      # batch edits
Bash           # execute shell commands
Grep           # ripgrep search
Glob           # file pattern matching
WebFetch       # fetch a URL
WebSearch      # search the web
Task           # spawn a subagent
NotebookEdit   # edit Jupyter notebooks
TodoWrite      # task tracking
AskUserQuestion # multi-choice user prompt
ExitPlanMode   # exit plan mode
```

NOT real (commonly hallucinated):
- `read_file`, `edit_file`, `bash` (lowercase) — real names are CAPITALIZED
- `str_replace_editor` — that's an Anthropic API computer-use tool type, NOT a Claude Code tool
- `run_command`, `execute_bash`, `shell_exec` — use `Bash`

## settings.json — the COMPLETE schema

```json
{
  "permissions": {
    "allow": ["Edit(*.py)", "Bash(git push:*)", "Read(*)"],
    "deny": ["Edit(.env)", "Bash(rm -rf:*)"],
    "additionalDirectories": ["/extra/paths"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "python3 .claude/hooks/check.py"}
        ]
      }
    ],
    "PostToolUse": [...],
    "Stop": [...],
    "UserPromptSubmit": [...]
  },
  "env": {"FOO": "bar"},
  "model": "sonnet"
}
```

Event names are PascalCase: `PreToolUse`, `PostToolUse`, `Stop`,
`UserPromptSubmit`, `SessionStart`, `Notification`.

Matcher values are tool names (PascalCase) joined by `|`, OR the literal `*`,
OR omitted for events that don't take a tool.

NOT real / commonly hallucinated:
- `pre_tool_use` (snake_case) — events are PascalCase
- `subagents:` map at top level — subagents are FILES at `.claude/agents/*.md`, not registered here
- `permissions.file_operations.allowed_extensions` — real shape is `permissions.allow: [...]`
- `permissions.system_commands.allowed` / `.blocked` — same
- `permissions.allow_file_operations: true` (bool) — real is allow/deny LISTS with patterns
- `safety:` block — no such field
- `version: "1.0"` at top level — no version field
- `claude --reload-settings` — restart the session

## Hook contract (FREQUENTLY HALLUCINATED)

Hooks are EXECUTABLES (any language) that read stdin JSON + exit with a code.
NOT Python functions returning JSON. NOT environment-variable-based.

stdin JSON shape:
```json
{
  "tool_name": "Edit",
  "tool_input": {"file_path": "/abs/path", "old_string": "...", "new_string": "..."},
  "session_id": "...",
  "transcript_path": "..."
}
```

Exit codes:
- 0 = ALLOW (tool call proceeds)
- 2 = BLOCK (tool call prevented; stderr shown to model)
- 1 / other = warn-only (stderr forwarded as warning, NOT a block)

DO NOT use `exit 1` to "block" — it warns, doesn't block. Use `exit 2`.

stderr text is shown to the model as the reason on block.

Example PreToolUse hook (bash) blocking edits to prod config:
```bash
#!/usr/bin/env bash
input=$(cat)
tool=$(echo "$input" | jq -r '.tool_name // ""')
path=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ "$tool" == "Edit" || "$tool" == "Write" ]] && [[ "$path" == *application-prod.properties ]]; then
  echo "BLOCKED: cannot edit production config" >&2
  exit 2
fi
exit 0
```

Hooks must be NON-INTERACTIVE — stdin is consumed by the JSON. Don't use
`read -p`, interactive `select`, or anything that asks for terminal input.

NOT real:
- `def validate_db_operations(tool_name, args) -> dict` returning `{"block": True, "reason": ...}` — hooks are executables, not Python functions
- `data.arguments.path`, `data.parameters.path` — real fields are `tool_name` (top-level) and `tool_input.<field>`
- `CLAUDE_TOOL_INPUT` env var — input is on stdin

## File system layout (`.claude/` directory)

ALLOWED paths under `.claude/`:
```
.claude/agents/<slug>.md           # custom subagents (auto-discovered)
.claude/commands/<name>.md         # custom slash commands
.claude/hooks/<name>.{py,sh,...}   # hook scripts (referenced from settings.json)
.claude/settings.json              # project-level settings (permissions + hooks)
.claude/skills/<name>/             # custom skills (newer feature; SKILL.md inside)
```

NOT real / commonly hallucinated:
- `.claude/subagents.json` — subagents are FILES at `.claude/agents/*.md`
- `.claude/hooks.json` — hooks are configured INSIDE settings.json, not separate file
- `.claude/config.json` — real file is `settings.json`
- `.claude/agents.yml` — agents are individual `.md` files

User-global vs project-scoped:
```
~/.claude/settings.json            # user-global settings
~/.claude.json                     # legacy MCP servers config
<project>/.claude/settings.json    # project-scoped (overrides user-global)
<project>/.mcp.json                # project-scoped MCP servers
```

## Subagent YAML frontmatter — the COMPLETE schema

File: `.claude/agents/<slug>.md`

```markdown
---
name: test-fixer
description: Runs pytest, proposes minimal fix, verifies, stops at 5 iterations.
tools: [Read, Edit, Bash]
disallowedTools: [WebFetch]
model: sonnet
maxTurns: 8
permissionMode: acceptEdits
mcpServers: [team-tickets]
hooks: {}
skills: [code-review]
memory: ""
effort: "medium"
background: false
isolation: "session"
color: "blue"
initialPrompt: ""
---
<system prompt body as markdown>
```

`name` MUST match the file basename (`.claude/agents/test-fixer.md` → `name: test-fixer`).
This is what `claude --agent test-fixer` looks up.

NOT real frontmatter fields (silently dropped):
- `max_tokens` (use `maxTurns`)
- `system_prompt` (the body IS the system prompt)
- `allowed_tools` (use `tools:`)
- `version` (no version field)
- `max_iterations` (no such field — use `maxTurns`)
- `agent_id` (no id field)

## MCP wiring

Add a server (writes to `~/.claude.json` user-global):
```bash
claude mcp add <name> <command-or-path> [args...] [--transport stdio|http]
# Examples:
claude mcp add team-tickets python -m team_tickets_mcp --transport stdio
claude mcp add wiki /opt/wiki-mcp/server.py --transport stdio
claude mcp add api-srv https://example.com/mcp --transport http
```

Verify:
```bash
claude mcp list           # shell — lists registered MCPs
# OR inside REPL:
/mcp                      # shows status of registered MCPs
```

NOT valid:
- `claude /mcp list` — concatenates shell + slash, pick one
- `claude mcp install <github-url>` — no `install` subcommand
- `mcpServers` in `settings.json` — that's CLAUDE DESKTOP's config (`claude_desktop_config.json`), NOT Claude Code

Project-scoped via `.mcp.json` (checked into git):
```json
{
  "mcpServers": {
    "team-tickets": {
      "command": "python",
      "args": ["-m", "team_tickets_mcp"],
      "transport": "stdio"
    }
  }
}
```

## Model identifiers (current as of 2026-04)

Aliases:
- `sonnet` (latest Sonnet)
- `opus` (latest Opus)
- `haiku` (latest Haiku)

Specific (use these in code examples that should still work in 6 months):
- `claude-sonnet-4-5-20250929` — Sonnet 4.5
- `claude-opus-4-1-20250805` — Opus 4.1
- `claude-haiku-3-5-20241022` — Haiku 3.5

NOT real:
- `claude-3.5-sonnet` (use `sonnet` or full id)
- `sonnet-3.5` (use full id `claude-sonnet-3-5-20240620` if you mean 3.5)
- `claude-4`, `claude-5` (use specific full id)

## Pricing (2026-04 — verify against current console.anthropic.com/pricing)

Per million tokens (input / output):
- Haiku 3.5: $0.80 / $4.00
- Haiku 3: $0.25 / $1.25 (older)
- Sonnet 4.5 / 3.5: $3.00 / $15.00
- Opus 4.1 / 3: $15.00 / $75.00

Cache hits: 90% discount on input.
Cache writes: 25% premium on input (5min TTL) or 100% premium (1hr TTL).

If a course mentions Haiku 3.5 in copy, the calculator MUST use $0.80 / $4.00,
not the older Haiku 3 rates.

## Cost telemetry inside Claude Code

`/cost` shows session cost + token usage:
```
Total cost: $0.12
Input tokens: 8,234
Output tokens: 156
Cache reads: 4,521
```

Also: `claude -p "..." --output-format=json` includes `usage` + `cost` fields.
