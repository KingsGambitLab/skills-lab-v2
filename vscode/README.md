# Skillslab — VS Code Extension

Walk Claude Code / Aider / Spring Boot courses in VS Code without leaving the editor. Same BYO-key model as the CLI — your Anthropic key stays in your OS keychain; we never see it.

## Features

- **Sidebar tree**: courses → modules → steps with ✓ / ▶ / ◯ states
- **Step card WebView**: briefing + interactive widgets, theme-accented per course
- **Submit & Continue**: single context-aware command (palette or WebView button) — submits, shows feedback, advances on pass
- **Terminal pre-populate**: click "Open Terminal" in any step to spawn the integrated terminal with the right `gh repo fork` / `claude` / `pytest` already typed
- **Devcontainer support**: detects course-repos with `.devcontainer/devcontainer.json` and offers Reopen in Container — the `tusharbisht1391/skillslab` toolchain image takes over so `claude` / `aider` / `git` / `pytest` are all on PATH

## Security

- Bearer + API keys live in **VS Code SecretStorage** (OS keychain — Keychain on macOS, Credential Manager on Windows, libsecret on Linux)
- We never log, persist, or transmit keys through our backend
- LLM calls (when a step prompts) happen FROM your machine TO Anthropic directly
- Same posture as the desktop CLI

## Install

### From VSIX (sideload — current path while marketplace listing pending)

Download the `.vsix` from the [latest GitHub release](https://github.com/KingsGambitLab/skills-lab-v2/releases) and:

```
code --install-extension skillslab-0.1.1.vsix
```

### From Marketplace

(Coming soon — pre-release channel first.)

## Configuration

| Setting | Default | Notes |
|---|---|---|
| `skillslab.apiUrl` | `http://52.88.255.208` | LMS API URL — override for self-hosted |
| `skillslab.webUrl` | `http://52.88.255.208` | Web dashboard URL (used by Open in Browser) |
| `skillslab.adoptCliToken` | `ask` | One-way inheritance from CLI's `~/.skillslab/token`. Read-only — file is never modified |
| `skillslab.preferredCourse` | `""` | Slug to default to when no cursor is set |

## Commands

All under the `Skillslab:` palette prefix:

- `Sign In` / `Sign Out`
- `Start a Course…`
- `Show Table of Contents`
- `Open Current Step`
- `Submit & Continue`
- `Run This Step in Terminal`
- `Refresh Courses`

## Privacy

This extension talks to:
1. The LMS API (configurable; default `http://52.88.255.208`) — for catalog, step content, validation, progress
2. Anthropic API — only when a step's interactive widget invokes it, and only with your locally-stored key
3. GitHub API — for `gh repo fork` style commands run from the integrated terminal

We do not collect telemetry. We do not phone home. Network calls are limited to the three endpoints above.

## Development

```
cd vscode/
npm install
npm run compile
# Open this folder in VS Code, press F5 to launch a development host
```

Tests:

```
npm run test
```

Package as `.vsix`:

```
npm run package
```

## Architecture (per buddy-Opus consult 2026-04-27)

- `auth.ts` — SecretStorage + CLI token consent
- `api.ts` — LMS REST client
- `state.ts` — globalState for cursor + attempts
- `tree.ts` — sidebar tree (courses → modules → steps)
- `webview.ts` — step-card panel
- `widgets.ts` — onclick → data-action rewrite + nonce'd delegator (CSP-safe)
- `commands.ts` — palette commands + submit-and-continue
- `theme.ts` — course themes
- `extension.ts` — activation + URI handler
