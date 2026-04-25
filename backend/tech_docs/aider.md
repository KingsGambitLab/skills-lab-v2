# Aider — Canonical Reference (cached 2026-04-25)

Source: https://aider.chat/docs (commands.html, options.html, llms/openrouter.html, conf.html)
Aider version: 0.86+ (current as of cache date)

This file is the GROUND-TRUTH input for the Aider TechSchema. Edit only
when canonical docs change (don't add ad-hoc entries from review findings —
those go in the schema's `additional_drifts` field instead, with provenance).

---

## In-chat slash commands (the COMPLETE list)

```
/help              # show commands
/add <files>       # add files to chat context (writeable)
/read-only <file>  # add files as read-only context
/drop [files]      # remove files from chat
/clear             # clear chat history (keep files)
/reset             # clear chat AND drop files
/run <cmd>         # run shell command, add output to chat
/test <cmd>        # run test command, output as context for next edit
/commit            # commit current changes with LLM-generated message
/diff              # show diff of current edits
/undo              # undo last commit
/architect         # plan-only mode (LLM proposes, you approve)
/code              # direct edit mode (default)
/ask               # read-only Q&A about codebase (no edits)
/chat-mode <mode>  # switch mode: code|architect|ask|help|context
/editor [text]     # open $EDITOR for a multiline message
/lint              # run lint on chat files
/load <file>       # REPLAY slash-command HISTORY from a file (NOT load text into context)
/save <file>       # save slash-command history to a file
/tokens            # show token usage + cost for current session
/voice             # voice input
/web <url>         # add URL contents as context
/ls                # list files in chat
/git <cmd>         # run git command
/report            # generate session report
/settings          # show current settings
/model <name>      # switch model mid-session
/multiline-mode    # toggle multiline input
/think-tokens      # show thinking-token usage
/reasoning-effort  # set reasoning effort level
/copy              # copy last response
/paste             # paste from clipboard
/context           # show full context tree
/map               # show repo map
/map-refresh       # refresh repo map cache
/copy-context      # copy entire context to clipboard
/exit              # exit aider
/quit              # alias for /exit
```

Commonly hallucinated / NOT real:
- `/read` (real is `/read-only`)
- `/plan`, `/scaffold`, `/refactor`, `/review` modes (use `/architect`)
- `/save_prompts`, `/custom`, `/template` (no such commands)
- `.aider/commands/<name>.md` directory (fictional)

## CLI flags (the COMPLETE list — from `aider --help`)

Auth + model:
```
--model <name>                # e.g. openrouter/moonshotai/kimi-k2
--weak-model <name>           # smaller model for cheap tasks
--editor-model <name>         # different model for /editor
--api-base <url>              # custom OpenAI-compatible base URL
--openai-api-base <url>       # alias for --api-base (LiteLLM compat)
--openai-api-key <key>        # use $OPENAI_API_KEY env var instead
--api-version <ver>           # for Azure OpenAI
--list-models                 # list available models
--verify-ssl / --no-verify-ssl
```

Auth env vars (preferred over flags):
```
ANTHROPIC_API_KEY              # for Claude models
OPENAI_API_KEY                 # for OpenAI direct
OPENROUTER_API_KEY             # for OpenRouter routing
GROQ_API_KEY, COHERE_API_KEY   # other providers
DEEPSEEK_API_KEY, GEMINI_API_KEY
```

There is NO `--openrouter-api-key` flag. Use `OPENROUTER_API_KEY` env var.

Project + files:
```
--read <file>                 # add files as read-only at startup
--message "<text>"            # one-shot message, exit after
--message-file <path>         # one-shot message from file, exit after
--load <file>                 # replay command history at startup
--config <file>               # use custom .aider.conf.yml path
--git / --no-git              # enable/disable git ops
--auto-commits / --no-auto-commits   # toggle auto-commits
--dirty-commits / --no-dirty-commits # toggle commit-on-startup-if-dirty
--attribute-author / --no-attribute-author
--attribute-committer / --no-attribute-committer
--gitignore / --no-gitignore
--encoding <enc>
--show-diffs / --no-show-diffs
```

Modes:
```
--architect                   # start in architect mode
--ask                         # start in ask-only mode
--no-stream                   # disable streaming
--pretty / --no-pretty
--dark-mode / --light-mode
```

Apply / undo / debug:
```
--apply <file>                # DEBUG: apply a saved diff file, exit. NOT for normal use.
--undo                        # undo last commit, exit
--lint / --no-lint
--lint-cmd "<cmd>"
--auto-lint / --no-auto-lint
--test / --no-test
--test-cmd "<cmd>"
--auto-test / --no-auto-test
```

Map + context:
```
--map-tokens <N>              # token budget for repo map (default 1024)
--map-refresh <strategy>      # auto/manual/files/always
--cache-prompts / --no-cache-prompts
--restore-chat-history
```

Voice + UI:
```
--voice-input
--voice-language <lang>
--voice-format <fmt>
--multiline-mode
--fancy-input / --no-fancy-input
```

Commonly hallucinated / NOT real:
- `--openrouter-api-key` (use env var)
- `--subagent <name>` (no such concept in Aider)
- `--plan` (use `--architect`)
- `--enable-mcp` (no MCP support yet — see https://github.com/Aider-AI/aider/issues/4506)

## .aider.conf.yml — the COMPLETE allowed key list

```yaml
# Auth
openai-api-base: https://...
openai-api-key: sk-...
openrouter-api-key: sk-or-...     # if you really need a config-file key
anthropic-api-key: sk-ant-...

# Model
model: openrouter/moonshotai/kimi-k2
weak-model: openrouter/anthropic/claude-3-haiku
editor-model: openrouter/anthropic/claude-3-5-sonnet
edit-format: diff                 # diff | whole | udiff | architect

# Files / project
read: AGENTS.md                   # also: read: [file1, file2]
load: prompts/preflight.md        # replay slash-history at startup
gitignore: true
encoding: utf-8

# Auto-actions (booleans)
auto-commits: false
dirty-commits: false
attribute-author: true
attribute-committer: true
auto-lint: true
auto-test: false
restore-chat-history: true
cache-prompts: false

# Test + lint
lint-cmd: "ruff check ."
test-cmd: "pytest -xvs"

# UI
dark-mode: true
pretty: true
stream: true
voice-input: false
suggest-shell-commands: true
fancy-input: true
multiline-mode: false

# Map + context
map-tokens: 1024
map-refresh: auto

# SSL + network
verify-ssl: true
```

Commonly hallucinated / NOT real keys:
- `context-files:` (real is `read:`)
- bare `test:` (real is `test-cmd:` + `auto-test:`)
- bare `lint: true` (real is `auto-lint:` and/or `lint-cmd:`)
- `subagents:`, `commands:`, `hooks:`, `agents:` (none exist in Aider config)
- `mcp:`, `mcp_servers:` (Aider has no MCP support yet)
- `system_prompt:`, `prompt_template:` (use `read: <file>` for system context)

## Model routing — canonical forms

OpenRouter (preferred for Kimi K2):
```
--model openrouter/<provider>/<model>
# OPENROUTER_API_KEY=<key>
# Examples:
#   --model openrouter/moonshotai/kimi-k2-0905    (specific date-stamped, stable)
#   --model openrouter/moonshotai/kimi-k2         (rolling alias — may rotate)
#   --model openrouter/anthropic/claude-3-5-sonnet
```

The `openrouter/` prefix is REQUIRED. Aider runs through litellm, and
litellm refuses any model arg without a provider prefix
(`litellm.BadRequestError: LLM Provider NOT provided`). Don't pass the
bare OpenRouter slug as the model — it's the slug ON OpenRouter, not the
arg ON aider.

Anthropic direct:
```
--model claude-sonnet-4-5-20250929  # specific
--model sonnet                       # alias
# ANTHROPIC_API_KEY=<key>
```

Moonshot direct (NOT through OpenRouter):
```
--model moonshot/kimi-k2-0905
# MOONSHOT_API_KEY=<key>
# api_base: https://api.moonshot.ai/v1
```

LiteLLM passthrough (non-canonical, works but not documented):
```
--model openai/<openrouter-slug> --openai-api-base https://openrouter.ai/api/v1
# OPENAI_API_KEY=<openrouter-key>
```

## Kimi K2 model arg — canonical forms (--model)

For BYO-OpenRouter (the immersive course's standard path):
- `openrouter/moonshotai/kimi-k2-0905` — date-stamped, pinned to a specific
  release. PREFERRED for course content because the model behavior won't
  shift under a learner mid-walk.
- `openrouter/moonshotai/kimi-k2` — rolling alias to the latest k2. Fine
  for casual use; risky for course step rubrics that depend on specific
  output shape.

NEVER use bare `moonshotai/kimi-k2` (without the `openrouter/` prefix)
as the --model arg. It looks right (it IS the OpenRouter slug), but
litellm has no way to know which provider you mean and rejects it at
runtime. Course content authored against the bare form ships broken.

For Moonshot direct (no OpenRouter intermediary):
- `moonshot/kimi-k2-0905` — single-slash provider prefix (different from
  the openrouter variant which is double-slash). Requires
  `MOONSHOT_API_KEY` instead of `OPENROUTER_API_KEY`.

## Anthropic models on aider

For BYO-OpenRouter:
- `openrouter/anthropic/claude-3-5-sonnet`
- `openrouter/anthropic/claude-3-5-haiku`
- `openrouter/anthropic/claude-3-opus-20240229`

For Anthropic direct:
- `claude-sonnet-4-5-20250929` — specific
- `sonnet` / `opus` / `haiku` — aliases (latest of each tier)

## File system conventions

- `.aider.conf.yml` — project-local config
- `~/.aider.conf.yml` — user-global config
- `.aider.tags.cache.v3` — repo-map cache (gitignored by default)
- `.aider.chat.history.md` — session history (gitignored by default)
- `.aider.input.history` — input history (gitignored by default)
- `AGENTS.md` (cross-tool standard) OR `CONVENTIONS.md` (Aider-specific) — project conventions, declared via `read: <file>` in conf

NO `.aider/commands/` directory exists. NO `.aider/agents/` directory exists.

## MCP support

Aider does NOT natively support MCP yet (as of 0.86+). See open issue:
https://github.com/Aider-AI/aider/issues/4506

If a course wants MCP-style tools with Aider, build a custom tool-loop
in Python that wraps Aider's command interface — there's no first-class
`/mcp` command or `mcp` config key.

## Cost telemetry

`/tokens` is the in-session command. It prints:
```
Total cost (usd): $0.04
Sent tokens: 12,345
Received tokens: 678
```

For OpenRouter, costs are computed against the published per-million-token
prices for the routed model. Aider does NOT expose Moonshot's separate
internal billing for direct API.

## Auto-commits behavior

Default: `auto-commits: true`. Aider commits each accepted edit immediately
with an LLM-generated message. PR-review workflows usually want this OFF.

`dirty-commits: true` (default): Aider commits any uncommitted working-tree
changes as "before aider" so its own diffs stay clean.
