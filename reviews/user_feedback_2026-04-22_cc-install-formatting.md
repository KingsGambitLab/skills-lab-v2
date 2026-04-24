# User-Reported Formatting Feedback — Claude Code Course, Install Step

**Date**: 2026-04-22
**Source**: user screenshot on the Claude Code course (`created-8412204e6e89`), Module 1 install step
**Status**: logged, NOT fixed — awaiting decision on plan below

This file lives alongside the beginner-agent + domain-expert artifacts so the full reviewer list sees the same issues when they triage.

---

## What the screenshot shows

The install step renders as a flowing paragraph with inline mono commands. The actual content is correct (platform-aware, BYO-key panel, expected output, collapsible "error?" disclosures, a paste box + submit, a Score: 100% grader response), but the VISUAL formatting has several rough edges on first read.

## Issues

### 1. Commands run into paragraph flow; long ones hit the right edge

- `$ brew install anthropic/tap/claude-code` is rendered inline with the heading + expected output, all mashed together.
- `$ curl -fsSL https://api.claude.ai/cli/install.sh |` visibly truncates at the right edge — the pipe-to-shell tail is lost.
- No visual "code block" treatment (no background tint, no padding, no copy button, no row framing). It's just monospaced text within the narrative.

### 2. No visual separation between platforms

- `macOS`, `Linux`, `Windows + WSL` are bold headers but the sections below them run together without borders, tabs, or cards. A learner scanning for "what do I run on my laptop" has to read all three.
- No "tab" UX — the template could show only the active-OS section by default with a toggle.

### 3. Expected output and command look the same

- Both are rendered as monospace text on the same background. The learner can't at-a-glance tell "this is what I type" vs "this is what should come back".

### 4. Paste textarea is too small

- The paste box visible at the bottom shows maybe 2 lines. Real `claude --version` output is small (one line) so this case is OK, but later steps will have multi-line terminal output (15-30 lines for `claude /login` or `claude 'edit this file'`). The textarea should auto-expand like the code template does.
- The visible paste `$ brew install anthropic/tap/claude-` wraps mid-command mid-word, showing partial text. That's the textarea being too narrow AND not word-wrap-clean.

### 5. "114 chars" counter is unexplained

- `Paste your terminal output below 114 chars` — is 114 the limit, or the current count? No visual context (no progress bar, no "X of Y"). Looks like a leftover debug label.

### 6. Collapsible disclosures (`▶ Don't have Homebrew installed?`) blend in

- The triangle + bold text is OK but there's no background / border to signal "click me." Learners may miss these fallbacks and get stuck on the happy path.

### 7. Minor: the hamburger `≡` button in the top-left overlaps with step content

- On narrower viewports, the sidebar toggle button sits on top of the concept text. Not a new issue (platform-wide), but visible here.

---

## Root-cause possibilities (for triage)

| Issue | Likely layer | Evidence |
|---|---|---|
| 1, 3 — command/output not in code blocks | **Creator prompt** (instructs `<pre><code>$ command</code></pre>` in `demo_data.instructions` but LLM may emit `<code>` inline instead) OR **template CSS** (no `.terminal-cmd` / `.terminal-expected` styles) | Need to dump the actual `demo_data.instructions` HTML and see which path is wrong |
| 2 — no platform tabs | **Template HTML** (`terminal.html` just dumps `instructions` as innerHTML; no OS-tab structure) | `frontend/templates/terminal.html` is the place |
| 4 — paste textarea too small | **Template CSS** (`terminal.css` probably has `rows=2` or fixed height) | `frontend/templates/terminal.{html,css,js}` |
| 5 — `114 chars` counter | **Template JS** (probably an unpolished character counter shipped as debug) | `frontend/templates/terminal.js` |
| 6 — disclosure affordance | **Template CSS** (no styles on `<details><summary>`) | `frontend/templates/terminal.css` |
| 7 — sidebar toggle overlap | **Platform-wide CSS** (existing, not new) | `frontend/index.html` `<style>` block |

Issues 2/4/5/6 are WIRING/TEMPLATE bugs — fixable in one pass without regenerating the course. Issue 1/3 may be BOTH template (styles) and prompt (LLM emission pattern) — template fix first, regen only if content is genuinely wrong.

---

## Plan options (for decision)

### Option A — Template-only polish pass (smallest, fastest)

Scope: `frontend/templates/terminal.{html,js,css}` + version bump.

1. Wrap each `<pre><code>` command block with a dedicated `.terminal-cmd` class — dark-green-tinted bg, left-border accent, copy button on the right.
2. Wrap "Expected:" lines with `.terminal-expected` class — dim italic, no monospace, different color.
3. Replace raw `<details>` with styled cards (`.terminal-disclosure`) — chevron, subtle bg, hover state.
4. Paste textarea: `auto-resize` on input (existing code template has this pattern — port it).
5. Character counter: either remove or make it informational ("0 / 4000 chars") with a progress bar.
6. Add a "platform tabs" component: detect `<h4>macOS</h4>` / `<h4>Linux</h4>` / `<h4>Windows</h4>` patterns in `instructions` and render as tab switcher.

**Cost**: ~200 lines of JS/CSS. Zero regen needed. Works against EVERY existing Claude Code course + any future CLI-tool course. Cache-bust to v1.2.0.

**Tradeoff**: The platform-tabs heuristic assumes the Creator emits `<h4>OS</h4>` structure. If it emits something else (`<h3>` or prose headers), the tab detection silently no-ops and we fall back to today's flat rendering.

### Option B — Template polish + Creator-prompt tightening (deeper, needs approval)

All of Option A, PLUS: strengthen the Creator prompt for `terminal_exercise` to force the `<h4>macOS</h4>` + `<pre><code>$ cmd</code></pre>` + `<p class="terminal-expected">Expected: ...</p>` structure, so the template tabs + styling reliably hit.

**Cost**: Option A + prompt edit (which I WILL NOT do without your approval per your earlier directive). Requires regen of at least the Claude Code course to verify — $0.30-$0.50, 10-15 min.

**Tradeoff**: Higher polish ceiling, but locks us into a specific HTML structure the LLM has to follow.

### Option C — Hold for dual-agent findings, batch the fix

Let the beginner + domain-expert agents finish their walkthroughs. Merge their findings with this list. Decide Option A vs B once the full findings are in, fix in one pass + one cache bump.

**Tradeoff**: Slower feedback loop for you, but one regen rather than two.

---

## Recommendation

**Option C** — the agents' in-flight findings will likely surface more template issues (e.g. paste-box-too-small may show up on Module 5 capstone with long MCP-server output; `114 chars` counter probably gets flagged too). Batching avoids a second cache bump within the same 30-min window.

Awaiting your call.

---

## UPDATE 2026-04-22 21:50 — Beginner agent + Domain-expert both complete

**Beginner agent verdict**: ❌ REJECT. P0 wiring bug found.

- **terminal.js is not loaded in index.html** — only drag_drop.js / code.js / project.js are in the `<script>` tags at lines 21-23. Every `terminal_exercise` step silently fails to mount. 14 out of 24 course steps non-functional.
- Trivial 1-line fix: add `<script src="/templates/terminal.js?v=1.1.1" defer></script>`.
- Once fixed, no regen needed — the same course comes alive. Beginner reports: "once fixed, course grades well (BYO-key compliant, platform-aware, production-grade capstone)."
- Artifact: `reviews/beginner_stream_walkthrough_2026-04-22_v1-cc-terminal_claude-code.md`

**Domain-expert verdict**: ❌ REJECT (0.37/1.00). Content hallucination.

- See full breakdown above; 60% of CLI/hook/slash-command/MCP specifics fabricated.
- Needs source_material grounding (Claude Code docs) + course regen.
- Artifact: `reviews/domain_expert_claude_code_plus_terminal_2026-04-22_v1-cc-terminal_claude-code.md`

**Research agent verdict**: Observations only, no edits. Top 3 recommendations:
1. Per-wrong-answer teaching feedback (prompt edit, high impact)
2. "In-tool lessons" format — directly addresses the hallucination class for Claude Code course specifically
3. Socratic AI-tutor panel (reuse adaptive_roleplay infra)

Artifact: `reviews/research_competitor_platforms_2026-04-22.md`

---

## Consolidated fix list for the Claude Code course (all sources)

### P0 — blocking any relaunch of this course
1. **Add terminal.js to index.html** (beginner agent, 1-line fix)
2. **Re-ground content against Claude Code docs** (expert, requires regen) — covers hook schema, CLI commands, install URLs, MCP protocol, slash-command format, config paths

### P1 — strong improvements
3. **Populate `▶ "Got X error?"` disclosures with real remediation content** (expert + user screenshot)
4. **Per-wrong-answer teaching feedback** (research agent)
5. **Per-step "what NOT to delegate" coverage** (expert, production realism miss)
6. **Explicit `permissions.allow/deny` + `disallowedTools` discipline** (expert)
7. **Platform tabs in install step + code-block framing** (user screenshot)
8. **Paste textarea auto-resize + remove `114 chars` debug counter** (user screenshot)

### P2 — deeper reframing (separate approval needed)
9. **In-tool lessons format** for Claude Code course (research agent Gap #4) — would replace entire course format with `.claude/commands/*.md` model that lives inside Claude Code itself; solves the hallucination class at format level
10. Socratic AI-tutor panel across all lessons (research agent Gap #5)

---

## Status: PINNED per user directive

User said "pin for 1 hour" (2026-04-22 ~21:50). PM AI-enablement course build starts now. Circle back ~22:50.
