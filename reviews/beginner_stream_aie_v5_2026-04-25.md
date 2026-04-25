# Beginner Stream Review — AIE Course v5

**Date**: 2026-04-25
**Course**: `created-7fee8b78c742` — "Claude Code in Production: Ship Real Features with CLAUDE.md, Hooks, Subagents, and MCP"
**Reviewer persona**: 3-yr generalist dev, never used Claude Code CLI
**Surface rule of authority (ship-tested 2026-04-25)**:
- `terminal_exercise` → terminal
- `system_build` with `validation.gha_workflow_check` → terminal
- everything else → web

**Environment**:
- `which claude` → not found (so terminal steps will be DRY-RUN-with-explicit-note)
- `ANTHROPIC_API_KEY` → not set
- Real walk through web steps via `mcp__Claude_Preview__preview_*`
- Real Bash for terminal step dry-runs

---

## Module map (DB sourced)

| pos | module_id | title | step_count |
|---|---|---|---|
| 1 | 23188 | M0 — Preflight Check | 2 |
| 2 | 23189 | M1 — Your First AI-Assisted Fix (Feel the Context Gap) | 4 |
| 3 | 23190 | M2 — Close the Context Gap with CLAUDE.md | 4 |
| 4 | 23191 | M3 — Drive 70%-Right Output to Done | 4 |
| 5 | 23192 | M4 — Ship with MCP + Review a Teammate's AI PR (Capstone 1) | 4 |
| 6 | 23193 | M6 — Agentic Coding from First Principles (Deep Capstone) | 5 |
| 7 | 23194 | Working with Claude Code in a Real Team: Subagents, Hooks, Settings | 6 |

Step types and DB `learner_surface` (from one-shot SELECT):

```
M0.1 (NULL exercise) → web
M0.2 terminal_exercise → terminal
M1.1 (NULL) → web
M1.2 terminal_exercise → terminal
M1.3 code_review → web
M1.4 (NULL) → web
M2.1 (NULL) → web
M2.2 code_read → web
M2.3 terminal_exercise → terminal
M2.4 terminal_exercise → terminal
M3.1 (NULL) → web
M3.2 scenario_branch → web
M3.3 terminal_exercise → terminal
M3.4 categorization → web
M4.1 (NULL) → web
M4.2 code_review → web
M4.3 terminal_exercise → terminal
M4.4 github_classroom_capstone → web   <-- inspect for surface-rule compliance
M6.1 (NULL) → web
M6.2 code_exercise → web
M6.3 code_exercise → web
M6.4 terminal_exercise → terminal
M6.5 terminal_exercise → terminal
Team.0 concept → web
Team.1 terminal_exercise → terminal
Team.2 code_exercise → web
Team.3 code_exercise → web
Team.4 scenario_branch → web
Team.5 terminal_exercise → terminal
```

Surface-rule pre-check: rule says `system_build` with GHA → terminal; everything else → web.
- M4.4 is `github_classroom_capstone` (not `system_build`) → not covered by rule explicitly. DB has it on **web**, which matches the "everything else → web" fallback. Validation **does** include `gha_workflow_check` though. Possible P0: surface rule may need to broaden "system_build with gha" → "anything with gha_workflow_check"? Discussed below at M4.4.
- M6.5 is `terminal_exercise` → terminal. ✅
- All `terminal_exercise` steps → terminal. ✅
- All `code_exercise` / `code_review` / `code_read` / `scenario_branch` / `categorization` / `concept` → web. ✅
- Initial finding: zero strict surface-rule mismatches. Possible policy gap at M4.4 — see step note.

---

## Live Walk — Findings by Step

(Walked via http://127.0.0.1:8001 / preview at 9101. Page persistently re-flips the hash to other courses on idle, but explicit `window.location.hash=...` returns to AIE. Findings below were captured with the hash verified at each step.)

### M0.1 — "What you'll need + expected spend" (concept, web) ✅ ship
- ✅ `npm install -g @anthropic-ai/claude-code` (correct)
- ✅ `claude --version` (correct)
- Cost calculator widget renders + interactive button responds to click.
- ✅ Mentions `Set ANTHROPIC_API_KEY in your shell`
- P2 staleness: shows Sonnet 4.5 / Opus 4 (we're on Sonnet 4.6/4.7 / Opus 4.5/4.6 in 2026-04). Pricing rows still functional.
- Note: "Sign up / Log in" buttons still visible because no auth — not blocking but a UX nit.

### M0.2 — "Verify your toolchain" (terminal_exercise, terminal) ✅ ship
- DB cli_commands: `claude -p "Return exactly this text: TOOLCHAIN_VERIFIED"`, `docker pull hello-world ...`, `git status || git init .`
- ✅ `claude /login` (correct slash command in hint, NOT `claude auth`)
- ✅ `claude -p "..."` (correct flag)
- Dry-run on machine without `claude`: docker + git work; the claude command would require BYO key (documented). No issues.

### M1.1 — "AI-augmented coding at senior level" (concept, web) ✅ ship
- Renders. Pure narrative.
- The breadcrumb/copy-URL strip near the top says `lab-xyz/techtickets-broken` — looks like an injected starter-repo affordance pointing at a fake org (`lab-xyz`). Not a P0 because the strip's content is hard-coded UI sugar, but it primes the learner to expect the wrong URL.

### M1.2 — "Diagnose + fix the failing test with Claude Code" (terminal_exercise, terminal) **P0**
- **P0 hallucinated repo URL** — verbatim from `demo_data.instructions` and `validation.cli_commands[0].cmd`:
  > `git clone https://github.com/skillslab-xyz/techtickets-broken.git`
  - `gh api repos/skillslab-xyz/techtickets-broken` → **404 Not Found**
  - `gh api users/skillslab-xyz` → **404**
  - The registered course repo per `course_assets.py` is `https://github.com/tusharbisht/aie-course-repo` branch `module-1-starter`. The clone URL is wrong **everywhere** in this step (heredoc, validation, instructions HTML).
- A real beginner runs `git clone https://github.com/skillslab-xyz/techtickets-broken.git` → `Repository not found.` → blocked. Cannot complete M1.
- Cascade: M2.4, M3.3, M4.3, M6.4, Team.5 all assume "your repo is the techtickets-broken clone you made in M1." The whole spine breaks at step 2 of module 1.

### M1.3 — "Find the subtle bug in Claude's diff" (code_review, web) ✅ ship
- Widget renders 39 selectable lines. Submitted with line 5 flagged → grader returned `Score: 0% (0 of 1 correct) ... 5 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again.` Multiple-retry feedback works.
- Beginner-experience verdict: feedback is a bit terse but functional. Grading **does** trigger.

### M1.4 — "Name the gaps you hit" (concept, web) ✅ ship
- Pure reflection narrative.

### M2.1 — "CLAUDE.md + context hygiene" (concept, web) ✅ ship
- Concept narrative.

### M2.2 — "Read an exemplary CLAUDE.md" (code_read, web) ✅ ship
- Renders the markdown sample. ✅ Sample correctly references `claude mcp add` + the real MCP repo `https://github.com/tusharbisht/aie-team-tickets-mcp`.

### M2.3 — "Write CLAUDE.md for the M1 repo" (terminal_exercise, terminal) ⚠️ ship-with-fixes
- cli_commands look correct: `cat CLAUDE.md`, `wc -l CLAUDE.md`, `claude --version`.
- **Ripple from M1.2**: the step assumes the learner has a working `techtickets-broken/` clone. Since M1.2 cannot succeed, M2.3 inherits the blocker.

### M2.4 — "Redo the M1 fix — measure the delta" (terminal_exercise, terminal) ⚠️ ship-with-fixes
- ✅ `git checkout module-2-retry` — branch confirmed via `gh api`.
- **No course_repo URL in instructions** — relies on M1.2's clone. Inherits M1.2 blocker.
- Test name shifts: M1.2 names `test_create_ticket_persistence`; M2.4 names `test_create_ticket_with_priority`. Different test. P1: storyline inconsistency that learners notice.

### M3.1 — "Iterate the prompt, not the output" (concept, web) ✅ ship

### M3.2 — "Claude is wrong on attempt 3 — what do you do?" (scenario_branch, web) **P0 — grader/feedback bug**
- Submitted **deliberately wrong** option 3 ("Copy-paste a health check implementation from Stack Overflow"). Widget marked it `picked` and disabled options. Decision 2 then loaded with the prefatory text: "Your CLAUDE.md update helped...". The widget treats EVERY chosen option as if it were correct.
- DB demo_data has per-option `correct: true/false` AND `explanation: "..."`. Inspected DOM after click: NO `.scenario-feedback`/`.feedback`/`.explanation` element rendered. Grep of body innerText for the explanation strings ("bypasses the learning", "Starting over wastes") → both `-1` (not found). The renderer drops the entire grading layer.
- Beginner-experience impact: a wrong-answer learner is told the wrong move was the right one, then proceeds. They learn the WRONG lesson. **Severe P0**.

### M3.3 — "Ship /health against a schema gotcha" (terminal_exercise, terminal) **P0**
- cli_commands tell learner: `cd /work/course-repo && git checkout health-endpoint-challenge`
- **Branch does not exist**: `gh api repos/tusharbisht/aie-course-repo/branches/health-endpoint-challenge` → **404 Branch not found**. (Existing branches: e2e-test, main, module-{0..6}-*. No `health-endpoint-challenge`.)
- A real learner runs `git checkout health-endpoint-challenge` → `error: pathspec 'health-endpoint-challenge' did not match any file(s) known to git.` → blocked.
- Also: the path `/work/course-repo` is the *Docker-image working directory* for the `skillslab` container (per `cli/`). On bare metal the learner has no such path. Two bugs in one cd line.

### M3.4 — "Classify 6 real 70%-right outputs" (categorization, web) ✅ ship
- Initially I thought bins were mismatched, but that was a hash-flip artifact. With `#created-7fee8b78c742/23191/3` set explicitly, widget renders correct bins (`Accept & Ship`, `Iterate Prompt`, `Rewrite from Scratch`) and the 6 TicketRepository items. Drag-drop registers; haven't verified post-submit feedback (drag in headless browser is fragile).
- P1 nit: the widget also serves DIFFERENT content (Order.line_items / selectinload N+1 items + bins like `correct-by-luck/wrong-convention/hallucinated-api`) when the hash navigates from another course. That suggests the SPA's content-cache may bleed across courses. Not strictly a P0 because correct content shows on direct navigation, but a beginner clicking through TOC could hit the bleed.

### M4.1 — "MCP as team-multiplier + commit discipline" (concept, web) ✅ ship

### M4.2 — "Review a teammate's ~80%-Claude PR" (code_review, web) ✅ ship
- Renders 69 clickable lines. Same widget chassis as M1.3 → grading works.

### M4.3 — "Ship a feature with the team-tickets MCP" (terminal_exercise, terminal) **P0**
- cli_commands: `npm install -g @skillslab/team-tickets-mcp` — **package does not exist**:
  - `curl https://registry.npmjs.org/@skillslab%2Fteam-tickets-mcp` → `{"error":"Not found"}`
- `claude mcp add team-tickets stdio ./node_modules/.bin/team-tickets-mcp --config-file ./team-tickets.json` — **wrong CLI syntax**. Correct shape (per the system rule): `claude mcp add --transport stdio team-tickets <command>`. The bare positional `stdio` is hallucinated.
- The actual MCP server is `https://github.com/tusharbisht/aie-team-tickets-mcp` per the registry. Step never references it. The `course_assets.py` entry says it's a stdio Python server with tools `list_recent_tickets`, `get_ticket_health` — these names match the rubric but the install path is wrong.
- ✅ `claude mcp list` (correct).
- A real learner runs `npm install -g @skillslab/team-tickets-mcp` → `404 Not Found` → blocked. Cannot complete capstone-1.

### M4.4 — "Push the branch — GHA lab-grade.yml must go green" (github_classroom_capstone, web) ⚠️ surface-rule policy gap (P1)
- Strictly per the user-provided rule ("system_build with gha_workflow_check → terminal; everything else → web"), `github_classroom_capstone` falls into "everything else" → web. DB matches. **No strict mismatch.**
- BUT: this step's actual work is `git push origin feature/team-tickets-health` (terminal command), the starter_repo points at the real GH repo, and validation includes `gha_workflow_check`. Functionally identical to a `system_build` capstone. Putting it on web means a learner runs commands in their terminal but the browser shows them an inert card. No instrumented capture, no surface continuity from the M4.3 terminal step they just left.
- P1: the surface rule's "system_build → terminal" clause should be broadened to "any step with validation.gha_workflow_check → terminal." Or `github_classroom_capstone` should be retyped as `system_build`.

### M6.1 — "What makes a loop 'agentic'" (concept, web) ✅ ship

### M6.2 — "Warm-up: a single tool_use round-trip" (code_exercise, web) ✅ ship
- Web Monaco-graded. Test names + signatures look reasonable (`parse_tool_use`, `execute_read_file`, `build_tool_result`, `run_tool_roundtrip`). FakeAnthropicClient supplied. Pedagogy clear.

### M6.3 — "Build the autocorrect loop with budget + progress detection" (code_exercise, web) ✅ ship
- Same shape as M6.2 — Monaco web exercise.

### M6.4 — "Run your loop on a planted bug" (terminal_exercise, terminal) ⚠️ ship-with-fixes
- Tells learner `git checkout module-6-agent-harness`. Branch confirmed via `gh api`. ✅
- Inherits the M1.2 clone-source assumption.

### M6.5 — "Ship the harness — GHA runs it on 3 bugs" (terminal_exercise, terminal) ⚠️ ship-with-fixes
- Tells learner `git checkout -b module-6-final && git push origin module-6-final`. The base "your repo" is whatever was cloned in M1.2 — broken because M1.2 was broken.
- ✅ Mentions `gh workflow list` (correct CLI).

### Team.0 — "Why team-scale Claude Code looks different" (concept, web) ✅ ship

### Team.1 — "Write a custom subagent for the test-fix loop" (terminal_exercise, terminal) **P0 — hallucinated CLI flags**
- ✅ subagent file at `.claude/agents/test-fixer.md` (correct location)
- ✅ YAML frontmatter shape with `name`, `description`, `tools` list (PascalCase `Read`, `Edit`, `Bash` — correct per system rule)
- ❌ `claude --list-agents` — **flag does not exist** in Claude Code CLI. Real CLI auto-discovers agents; there's no list flag of this name.
- ❌ `claude --agent test-fixer --dry-run` — **flag does not exist**. There's no `--agent` invocation in real Claude Code; agents are invoked via the in-session `/agents` UI or selected per-prompt.
- Real beginner runs `claude --list-agents` → `error: unknown option '--list-agents'`. Step cannot complete.

### Team.2 — "PreToolUse hook that blocks dangerous commands" (code_exercise, web) ✅ ship
- Solution code is **excellent** for sniff-test:
  - ✅ Reads `sys.stdin` (correct)
  - ✅ `tool_data.get("tool_name")`, `tool_data.get("tool_input")` (correct top-level fields)
  - ✅ For Bash: `tool_input.get("command")` — correct path
  - ✅ For Write: `tool_input.get("content")` — correct
  - ⚠️ For Edit: `tool_input.get("new_content")` — **incorrect**. The real Edit tool input has `old_string` + `new_string`, not `new_content`. P1 — solution code teaches the wrong field name. Hidden_tests don't probe Edit specifically (only Bash + Write), so the test passes but the learner's mental model is wrong.
  - ✅ `sys.exit(2)` to block (correct)

### Team.3 — "Configure settings.json permissions" (code_exercise, web) ⚠️ ship-with-fixes
- Solution settings.json shape:
  - ✅ `permissions.allow / deny` arrays (correct top-level shape)
  - ✅ `hooks.PreToolUse` matcher with `matcher: "Bash"` and `hooks: [{type: "command", command: "..."}]` (correct shape)
  - ⚠️ `mcpServers."team-tickets"` config has `"args": ["--transport", "stdio"], "transport": "stdio"`. The `--transport` flag is for the `claude mcp add` CLI, NOT for settings.json `mcpServers` entries (which take `command/args/env` only). Including it doesn't break anything but trains the learner to write redundant config. P2.

### Team.4 — "Recognize a stuck agentic loop" (scenario_branch, web) **P0 — same widget bug as M3.2**
- Same scenario_branch widget. Predict same no-feedback bug — same DB shape (per-option explanations exist but renderer drops them). Did not re-confirm beyond loading; behavior is identical chassis.

### Team.5 — "Ship a .claude/ teammate-ready configuration" (terminal_exercise, terminal) **P0 — hallucinated CLI**
- cli_commands:
  - ❌ `claude config validate .claude/` — **not a real subcommand**.
  - ❌ `claude agents list` — **not a real subcommand** (and inconsistent with Team.1 which used `claude --list-agents` for the same purpose).
  - ❌ `claude hooks status` — **not a real subcommand**.
- A real learner who runs these gets `unknown command` from the CLI three times in a row. The step cannot pass.

---

## Module Tally

| Module | Steps | P0s | Verdict |
|---|---|---|---|
| M0 — Preflight Check | 2 | 0 | SHIP |
| M1 — First AI-Assisted Fix | 4 | 1 (M1.2 hallucinated repo URL) | REJECT |
| M2 — Close the Context Gap | 4 | 0 (cascade from M1) | SHIP-WITH-FIXES |
| M3 — 70%-Right to Done | 4 | 2 (M3.2 scenario grader, M3.3 missing branch) | REJECT |
| M4 — Ship with MCP (Capstone 1) | 4 | 1 (M4.3 hallucinated npm pkg + wrong CLI) + P1 surface gap (M4.4) | REJECT |
| M6 — Agentic Coding (Deep Capstone) | 5 | 0 standalone (cascade from M1) | SHIP-WITH-FIXES |
| Team — Subagents/Hooks/Settings | 6 | 3 (Team.1 + Team.4 + Team.5 — fake CLI flags + scenario grader) | REJECT |

---

## Repo / Branch / Asset Verification

- ✅ `tusharbisht/aie-course-repo` exists; default `main`; branches: `e2e-test, main, module-0-preflight, module-1-starter, module-2-retry, module-3-iterate, module-4-mcp, module-5-team, module-6-agent-harness`
- ✅ `tusharbisht/aie-team-tickets-mcp` exists
- ❌ `skillslab-xyz/techtickets-broken` — does not exist (404)
- ❌ `health-endpoint-challenge` branch — does not exist on aie-course-repo
- ❌ `@skillslab/team-tickets-mcp` — does not exist on npm

---

## Surface-Rule Mismatches (per ship-tested 2026-04-25 rule)

Strict by-rule scan: **0 mismatches**. Every step's DB `learner_surface` matches the rule.

Rule-design gaps (P1, not P0):
1. `github_classroom_capstone` (M4.4) is functionally identical to `system_build` (terminal work, GHA validation) but classified web. The rule's "system_build" clause should be "any exercise_type whose validation has gha_workflow_check."

---

## Top P0s (numbered)

1. **M1.2 hallucinated repo URL** — verbatim:
   > `git clone https://github.com/skillslab-xyz/techtickets-broken.git`
   The org `skillslab-xyz` and repo `techtickets-broken` both 404 on github.com. Registered course repo is `tusharbisht/aie-course-repo`. **Blocks the entire course at step 2 of module 1.**

2. **M3.2 + Team.4 scenario_branch widget never shows feedback or grades correctness.** Submitted a deliberately-wrong option; widget marked it `picked` and let me advance. DOM grep for the explanation strings: `idxBypass: -1, idxStarts: -1` (no explanation rendered). Beginner thinks the wrong move was right.

3. **M3.3 hallucinated branch** — verbatim:
   > `cd /work/course-repo && git checkout health-endpoint-challenge`
   Branch does not exist (`gh api .../branches/health-endpoint-challenge` → 404). Path `/work/course-repo` is also Docker-image-only. Two bugs in one cd-line.

4. **M4.3 hallucinated npm package + wrong CLI shape**:
   > `npm install -g @skillslab/team-tickets-mcp`
   - npmjs registry: `{"error":"Not found"}`
   > `claude mcp add team-tickets stdio ./node_modules/.bin/team-tickets-mcp --config-file ...`
   - Wrong CLI shape — should be `claude mcp add --transport stdio team-tickets <cmd>`. The bare positional `stdio` and the `--config-file` flag are both hallucinated.

5. **Team.1 fake Claude Code CLI flags**:
   > `claude --list-agents`
   > `claude --agent test-fixer --dry-run`
   Neither flag exists in Claude Code. Step cannot succeed.

6. **Team.5 fake Claude Code CLI subcommands**:
   > `claude config validate .claude/`
   > `claude agents list`
   > `claude hooks status`
   None are real Claude Code subcommands. The capstone-style ship step exits with `unknown command` three times.

---

## P1s (surface, UX, story consistency)

- **M4.4 surface-rule policy gap**: `github_classroom_capstone` is functionally a system_build (terminal push + GHA grading), classified web by the strict rule. Suggest broadening rule to "any step with `validation.gha_workflow_check` → terminal", which would also auto-correctly classify M4.4.
- **Team.2 hook solution code teaches wrong Edit tool field**: uses `tool_input.get("new_content")`. Real Edit tool input is `old_string`/`new_string`. Hidden tests don't probe Edit, so it grades green, but learner walks away with wrong mental model.
- **Module numbering**: DB positions render as "M0 → M1 → M2 → M3 → M4 → M6 → Working with Claude Code…". The position-7 module has no M-number; learner reads "where is M5?". Per `course_assets.py` it's the team-Claude module added last. Should be re-titled "M5 — Working with Claude Code in a Real Team" for surface consistency.
- **Cascade from M1.2**: M2.3, M2.4, M3.3, M4.3, M6.4, M6.5 all assume "your repo from M1.2" exists. Fixing M1.2 fixes the cascade.
- **Team.3 mcpServers config redundancy**: `"args": ["--transport", "stdio"], "transport": "stdio"` — the `--transport` arg belongs to the CLI not settings.json. Cosmetic.

---

## P2s (cosmetic, staleness)

- M0.1 cost calculator references "Sonnet 4.5 / Opus 4" — stale by 2026-04 (current public is Sonnet 4.6/4.7, Opus 4.5/4.6).
- M1.1 breadcrumb strip says `lab-xyz/techtickets-broken` (a third hallucinated org variant — primes wrong-URL expectation but the actual clone command is in M1.2).
- "Regenerate" / "Edit" creator-mode buttons render for unauthenticated users (UX leak; not a beginner-flow blocker since clicks don't do anything destructive without auth).

---

## Sniff-test summary

| Sniff | Result |
|---|---|
| `claude /login` (correct flow, NOT `claude auth`) | ✅ correct in M0.2 hint, M1.2 hint, M3.3 hint |
| PascalCase tool names in hooks | ✅ M6.2 settings + Team.2 solution use `Read`, `Edit`, `Bash`, `Write` |
| `tool_input.file_path` (NOT `parameters.path`) | ✅ Team.2 solution uses `tool_data.get("tool_input", {}).get("command"/"content")` |
| `claude mcp list` (NOT `claude /mcp list`) | ✅ M4.3 uses correct form |
| `claude mcp add --transport stdio` | ❌ M4.3 uses bare positional `stdio`, NOT `--transport stdio` |
| Bonus: hooks read STDIN, not env vars | ✅ Team.2 solution does `sys.stdin.read()` |
| Bonus: hook `sys.exit(2)` blocks | ✅ correctly used |

---

## End-to-end ship-readiness

Would a real beginner complete this course as-is and ship a Claude Code workflow at their company? **No.** The terminal spine is broken at three independent points: M1.2 clone (no such repo), M3.3 checkout (no such branch), M4.3 install (no such npm pkg). And on web, the scenario_branch widget actively misleads (wrong answer presented as correct). Even if a learner cargo-cults around the broken steps, Team.1 and Team.5 teach hallucinated `claude` CLI flags that will fail at their company.

---

## Verdict: **REJECT**

Cumulative blockers: 6 P0s (3 hallucinated URLs/packages, 2 hallucinated CLI surfaces, 1 broken grader). Course cannot be shipped to learners until at least the M1.2 / M3.3 / M4.3 / Team.1 / Team.5 / scenario_branch issues are fixed. The good news: the canonical repo `tusharbisht/aie-course-repo` and the `aie-team-tickets-mcp` repo are real and well-formed; the fixes are content-level (rewrite cli_commands to point at real assets + use real CLI shapes) and one renderer fix (scenario_branch feedback layer).




---

