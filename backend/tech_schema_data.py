"""Tech schema registrations — canonical-doc-derived.

Each schema is hand-populated from the cached canonical doc at
`backend/tech_docs/<tech>.md`. When canonical docs change:
  1. Update the cached `.md` file
  2. Update the corresponding TechSchema below
  3. CI regression check picks it up automatically

Adding a new tech (Kubernetes, Terraform, AWS CLI, …) = paste a new
register_schema(...) block here.
"""
from __future__ import annotations

from .tech_schema import TechSchema, register_schema


# ═══════════════════════════════════════════════════════════════════════
# AIDER
# Source: backend/tech_docs/aider.md
# ═══════════════════════════════════════════════════════════════════════

register_schema(TechSchema(
    tech_id="aider",
    display_name="Aider",
    scope_markers=(
        "aider", ".aider.conf", "aider-chat", "aider.chat",
        "kimi k2", "kimi-k2", "moonshotai/kimi",
    ),
    canonical_docs=(
        "https://aider.chat/docs/usage/commands.html",
        "https://aider.chat/docs/config/options.html",
        "https://aider.chat/docs/config/aider_conf.html",
        "https://aider.chat/docs/llms/openrouter.html",
    ),
    canonical_doc_path="backend/tech_docs/aider.md",
    dotdir_name=".aider",

    allowed_in_chat_commands=frozenset({
        "/help", "/add", "/drop", "/clear", "/reset",
        "/run", "/test", "/commit", "/diff", "/undo",
        "/architect", "/code", "/ask", "/chat-mode", "/editor",
        "/lint", "/load", "/save", "/tokens",
        "/voice", "/web", "/ls", "/git", "/report",
        "/settings", "/model", "/multiline-mode",
        "/think-tokens", "/reasoning-effort",
        "/copy", "/paste", "/context",
        "/map", "/map-refresh", "/copy-context",
        "/exit", "/quit",
        "/read-only",  # NOT /read
    }),

    allowed_cli_flags=frozenset({
        "--model", "--weak-model", "--editor-model",
        "--api-base", "--openai-api-base", "--openai-api-key", "--api-version",
        "--list-models", "--verify-ssl", "--no-verify-ssl",
        "--read", "--message", "--message-file", "--load",
        "--config", "--git", "--no-git",
        "--auto-commits", "--no-auto-commits", "--dirty-commits", "--no-dirty-commits",
        "--attribute-author", "--no-attribute-author",
        "--attribute-committer", "--no-attribute-committer",
        "--gitignore", "--no-gitignore", "--encoding",
        "--show-diffs", "--no-show-diffs",
        "--architect", "--ask", "--no-stream", "--pretty", "--no-pretty",
        "--dark-mode", "--light-mode",
        "--apply", "--undo",
        "--lint", "--no-lint", "--lint-cmd",
        "--auto-lint", "--no-auto-lint",
        "--test", "--no-test", "--test-cmd",
        "--auto-test", "--no-auto-test",
        "--map-tokens", "--map-refresh",
        "--cache-prompts", "--no-cache-prompts", "--restore-chat-history",
        "--voice-input", "--voice-language", "--voice-format",
        "--multiline-mode", "--fancy-input", "--no-fancy-input",
        "--help", "--version",
    }),

    allowed_config_keys=frozenset({
        # Auth
        "openai-api-base", "openai-api-key", "openrouter-api-key", "anthropic-api-key",
        # Model
        "model", "weak-model", "editor-model", "edit-format",
        # Files
        "read", "load", "gitignore", "encoding",
        # Auto-actions
        "auto-commits", "dirty-commits", "attribute-author", "attribute-committer",
        "auto-lint", "auto-test", "restore-chat-history", "cache-prompts",
        "lint-cmd", "test-cmd",
        # UI
        "dark-mode", "pretty", "stream", "voice-input", "suggest-shell-commands",
        "fancy-input", "multiline-mode", "show-diffs",
        # Map
        "map-tokens", "map-refresh",
        # SSL
        "verify-ssl",
    }),

    allowed_paths_in_dotdir=(
        # Aider doesn't have a project-scoped .aider/ directory of CONFIG;
        # it uses .aider.conf.yml at the project root + a few cache files.
        # The schema rejects any other .aider/ subpath.
        # (Empty allowlist + dotdir_name=".aider" means ANY .aider/X drift triggers.)
    ),

    allowed_model_id_patterns=(
        r"^openrouter/[a-z]+/[a-z][a-z0-9\-]*$",  # canonical OpenRouter
        r"^moonshotai/kimi-k2$",                   # canonical bare
        r"^moonshot/kimi-k2[\-0-9a-z]*$",          # Moonshot direct
        r"^anthropic/[a-z][a-z0-9\-]*$",           # Anthropic via OpenRouter
        r"^claude-(sonnet|opus|haiku)[\-0-9]*$",   # Anthropic direct
        r"^(sonnet|opus|haiku)$",                  # Aliases
    ),

    forbidden_examples=(
        # (bad, good, why)
        ("/load prompts/", "/read-only prompts/<file>",
         "/load REPLAYS slash-command HISTORY, not arbitrary prompt files"),
        (".aider/commands/", "any path you want like prompts/<name>.md",
         "no `.aider/commands/` directory exists in Aider"),
        (".aider/agents/", "Aider has no agents directory",
         "subagents are not a feature in Aider"),
        ("--openrouter-api-key", "OPENROUTER_API_KEY env var",
         "no such CLI flag — use the env var"),
        ("--subagent ", "no equivalent in Aider",
         "subagents are a Claude Code concept, not Aider"),
        ("kimi-k2-0905", "moonshotai/kimi-k2",
         "date-stamped slug; canonical OpenRouter slug is moonshotai/kimi-k2"),
        ("kimi-k2-latest", "moonshotai/kimi-k2",
         "date-stamped alias may rotate; use the unversioned slug"),
        ("kimi-k2-0711", "moonshotai/kimi-k2",
         "date-stamped slug; use the unversioned form"),
        ("/read prompts/", "/read-only prompts/<file>",
         "Aider has /read-only (with hyphen), not /read"),
        ("aider --apply ", "interactive 'y' to accept the diff",
         "--apply is a debug-mode flag that takes a saved diff file and exits; not the normal accept-edit path"),
        ("CLAUDE.md", "AGENTS.md (or CONVENTIONS.md)",
         "CLAUDE.md is Claude Code's convention; Aider uses AGENTS.md (cross-tool standard) declared via `read:` in .aider.conf.yml"),
    ),

    additional_drifts=(
        # (regex, msg, ignore_case, caught_at_step, source_review)
        (r"context-files\s*:", "uses `context-files:` in .aider.conf.yml — real key is `read:`",
         False, "kimi-M2.S2", "Kimi expert pass 2"),
        (r"^\s*test\s*:\s*[\"'].{1,80}[\"']\s*$", "bare `test:` in .aider.conf.yml — real keys are `test-cmd:` + `auto-test:`",
         False, "kimi-M2.S2", "Kimi expert pass 2"),
        (r"^\s*lint\s*:\s*(?:true|false)\s*$", "bare `lint: true|false` in .aider.conf.yml — real keys are `auto-lint:` and/or `lint-cmd:`",
         False, "kimi-M2.S2", "Kimi expert pass 2"),
        (r"--model\s+openrouter/\S+.{0,200}--openai-api-base", "mixes canonical openrouter/ prefix with --openai-api-base — pick one path",
         True, "kimi-M0.S3", "Kimi expert pass 1+2"),
        (r"aider\s+0\.4[0-9]\b|aider\s+0\.5[0-9]\b", "pins stale Aider version (0.4x/0.5x); current is 0.86+",
         True, "kimi-M0.S0", "Kimi expert pass 1"),
    ),

    exercise_invariants=(
        # F2 — writing a markdown / config file is NOT a code_exercise
        {"rule": "code_exercise deliverable must be code-language; markdown/config authoring → terminal_exercise + rubric",
         "if_exercise_type": "code_exercise",
         "if_deliverable_contains": ["markdown file", ".md file", ".aider.conf.yml", "AGENTS.md document",
                                      "config file authoring", "yaml file"],
         "violation": "F2 violation: code_exercise for a markdown/config deliverable. Use terminal_exercise + rubric."},
    ),
))


# ═══════════════════════════════════════════════════════════════════════
# CLAUDE CODE
# Source: backend/tech_docs/claude_code.md
# ═══════════════════════════════════════════════════════════════════════

register_schema(TechSchema(
    tech_id="claude_code",
    display_name="Claude Code",
    scope_markers=(
        "claude code", "claude-code",
        "@anthropic-ai/claude-code", "claude /login", "claude.ai/code",
        "ai-augmented engineering", "byo-key claude", "byo claude key",
    ),
    canonical_docs=(
        "https://docs.claude.com/en/docs/claude-code",
        "https://code.claude.com/docs/en/setup",
        "https://code.claude.com/docs/en/hooks",
        "https://code.claude.com/docs/en/mcp",
        "https://code.claude.com/docs/en/subagents",
    ),
    canonical_doc_path="backend/tech_docs/claude_code.md",
    dotdir_name=".claude",

    allowed_in_chat_commands=frozenset({
        "/login", "/logout", "/clear", "/help",
        "/mcp", "/agents", "/model", "/init",
        "/pr_comments", "/cost", "/exit",
    }),

    allowed_cli_flags=frozenset({
        "-p", "--print", "--resume", "--continue",
        "--model", "--agent",
        "--output-format", "--max-turns",
        "--help", "--version",
    }),

    allowed_subcommands=frozenset({
        "mcp",       # claude mcp <subcommand>
        "config",    # claude config <subcommand>
        "help",
        "version",
        "doctor",
        # Sub-subcommands of mcp:
        "mcp add", "mcp list", "mcp remove", "mcp serve",
        # Sub-subcommands of config:
        "config get", "config set", "config list",
    }),

    allowed_config_keys=frozenset({
        # settings.json top-level
        "permissions", "hooks", "env", "model",
        # permissions sub-keys
        "allow", "deny", "additionalDirectories",
        # hooks event names (also in allowed_settings_event_names below)
        "PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit",
        "SessionStart", "Notification",
        # hook entry shape
        "matcher", "type", "command",
    }),

    allowed_paths_in_dotdir=(
        ".claude/agents/*.md",
        ".claude/commands/*.md",
        ".claude/hooks/*.py",
        ".claude/hooks/*.sh",
        ".claude/hooks/*.js",
        ".claude/hooks/*",
        ".claude/skills/*/SKILL.md",
        ".claude/skills/*",
        ".claude/settings.json",
        ".claude/settings.local.json",
    ),

    allowed_tool_names=frozenset({
        "Read", "Write", "Edit", "MultiEdit",
        "Bash", "Grep", "Glob",
        "WebFetch", "WebSearch",
        "Task", "NotebookEdit", "TodoWrite",
        "AskUserQuestion", "ExitPlanMode",
    }),

    allowed_settings_event_names=frozenset({
        "PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit",
        "SessionStart", "Notification",
    }),

    allowed_frontmatter_fields=frozenset({
        "name", "description", "tools", "disallowedTools",
        "model", "maxTurns", "permissionMode",
        "mcpServers", "hooks", "skills",
        "memory", "effort", "background", "isolation", "color",
        "initialPrompt",
    }),

    allowed_model_id_patterns=(
        r"^claude-(sonnet|opus|haiku)-\d+(-\d+)?-\d{8}$",  # full id
        r"^(sonnet|opus|haiku)$",                          # alias
    ),

    forbidden_examples=(
        ("claude code ", "claude (no subcommand)",
         "the binary is `claude`; `claude code` is not a subcommand"),
        ("claude auth", "claude /login (interactive) or ANTHROPIC_API_KEY env",
         "invented subcommand"),
        ("claude /mcp list", "`claude mcp list` (shell) OR `/mcp` (slash)",
         "concatenates shell + slash forms — pick one"),
        ("claude --subagent ", "claude --agent <name>",
         "invented flag — the real flag is --agent (no `sub` prefix)"),
        ("claude.ai/download", "npm install -g @anthropic-ai/claude-code OR curl https://claude.ai/install.sh",
         "claude.ai/download is the Claude Desktop product, not Claude Code"),
        ("Claude Code Desktop", "Claude Code (CLI)",
         "Claude Code is a CLI, not a desktop app — don't conflate with the separate Claude Desktop product"),
        ("str_replace_editor", "Edit / Write (capitalized)",
         "str_replace_editor is an Anthropic API computer-use tool type, not a Claude Code tool"),
        (".claude/subagents.json", ".claude/agents/<name>.md (one file per subagent)",
         "subagents are individual Markdown files; no central JSON registry"),
        (".claude/hooks.json", ".claude/settings.json's hooks.PreToolUse[]",
         "hooks live INSIDE settings.json, not in a separate file"),
        ("claude /settings reload", "restart the session",
         "no /settings slash command exists"),
        ("claude /settings show", "read .claude/settings.json directly",
         "no /settings slash command"),
        ("claude /settings validate", "no equivalent — restart and check for errors",
         "no /settings slash command"),
        ("permissions.allow_file_operations", "permissions.allow: [\"Edit(*.py)\", ...]",
         "invented schema; real shape is allow/deny LISTS with patterns"),
        ("permissions.system_commands", "permissions.allow: [\"Bash(...)\"]",
         "invented schema"),
        ("\"pre_tool_use\":", "\"PreToolUse\":",
         "settings.json hook event names are PascalCase, not snake_case"),
        ("claude mcp install ", "claude mcp add <name> <command> --transport stdio",
         "no `install` subcommand"),
    ),

    additional_drifts=(
        # P1 candidate patterns staged for canonical upstream
        (r"(?:hook|guardrail|block).{0,400}(?:\bexit\s+1\b|\b(?:sys\.)?exit\s*\(\s*1\s*\))",
         "hook example uses `exit 1` to block — that does NOT block, it warns. Use `exit 2` to block.",
         True, "AIE-M6.S5", "AIE expert pass 1+2"),
        (r"#!/bin/bash[^\n]*\n\s*(?:import\s+\w+|from\s+\w+\s+import|def\s+\w)",
         "starter has `#!/bin/bash` shebang followed by Python — file is unrunnable. Pick one language.",
         True, "AIE-M6.S2", "AIE expert pass 3"),
        (r"(?:hook|guardrail).{0,200}\bread\s+-p\b",
         "hook command uses interactive `read -p` — hooks are non-interactive (stdin is JSON). Use stdin parsing instead.",
         True, "AIE-M6.S5", "AIE expert pass 3"),
        (r'(?i)haiku.{0,60}3\.5.{0,400}\$\s*0\.25.{0,40}\$\s*1\.25',
         "Haiku 3.5 priced as Haiku 3 ($0.25/$1.25). Real Haiku 3.5: $0.80 in / $4.00 out.",
         True, "AIE-M0.S1", "AIE expert pass 2"),
        (r'(?i)claude\s+code.{0,300}"mcpServers"\s*:\s*\{',
         "shows mcpServers JSON in a Claude Code context — that schema lives in Claude Desktop's config, not Claude Code.",
         True, "AIE-M4.S1", "AIE expert pass 2"),
        (r"\bversion\s*:\s*[\"']\d+\.\d+[\"']",
         "subagent frontmatter has `version: \"...\"` — invented field, silently dropped. Real fields don't include version.",
         True, "AIE-M6.S5", "AIE expert pass 3"),
        (r"\bmax_iterations\s*:",
         "subagent frontmatter has `max_iterations` — invented field. Use `maxTurns:` for turn cap.",
         True, "AIE-M6.S1", "AIE expert pass 3"),
    ),

    exercise_invariants=(
        # F2 — writing a markdown / config file is NOT a code_exercise
        {"rule": "code_exercise deliverable must be code-language; CLAUDE.md / config authoring → terminal_exercise + rubric",
         "if_exercise_type": "code_exercise",
         "if_deliverable_contains": ["CLAUDE.md", "markdown file", "settings.json file authoring",
                                      ".claude/agents/", "subagent file", "yaml frontmatter authoring"],
         "violation": "F2 violation: code_exercise for a CLAUDE.md / config / markdown deliverable. Use terminal_exercise + rubric."},
    ),
))
