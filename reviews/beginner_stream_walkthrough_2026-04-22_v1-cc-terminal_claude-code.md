# Beginner Walkthrough — Claude Code: From Zero to MCP-Powered Workflows
- Date: 2026-04-22
- Course ID: `created-8412204e6e89`
- Course URL: http://127.0.0.1:8001/#created-8412204e6e89
- Subject: Claude Code CLI + terminal exercises + subagents + hooks + custom slash commands + MCP servers
- Walker role: first-time beginner learner, RL-constrained (no answer-key access)

## Course shape — 5 modules × ~5 steps = 24 steps total
Exercise-type mix per step:
| Module | Step 0 | Step 1 | Step 2 | Step 3 | Step 4 |
|--------|--------|--------|--------|--------|--------|
| M1 Zero-to-First-Success | concept | terminal_exercise | terminal_exercise | terminal_exercise | **code_exercise** |
| M2 CLAUDE.md + Daily Flow | concept | terminal_exercise | terminal_exercise | terminal_exercise | **code_exercise** |
| M3 Subagents | concept | terminal_exercise | terminal_exercise | terminal_exercise | **code_exercise** |
| M4 Hooks | concept | **code_exercise** | terminal_exercise | **code_review** | terminal_exercise |
| M5 Capstone | concept | terminal_exercise | **code_exercise** | **system_build** | — |

Totals: 5× concept · 14× terminal_exercise · 4× code_exercise · 1× code_review · 1× system_build

## Step 1.1 — "Why Claude Code (and what you're about to install)" — concept
- Briefing clarity: 4/5 | time: ~1 min
- Auto-completes on view (step counter jumped to 1/5 instantly).
- Content: dual-column "chat-window way vs Claude Code way" comparison, 4-card feature grid, install preview bullets. Mentions macOS/Linux/Windows+WSL up front.
- Verdict: ✅ passed (auto)
- UI: clean, dark theme, no layout issues.

## Step 1.2 — "Install Claude Code on your OS" — terminal_exercise
- Briefing clarity: 5/5 | time: ~10 min (inflated by bug-hunting)
- **🚨 WIRING BUG (P0) — ROOT CAUSE**: `frontend/index.html` lines 21-23 load `<script src="/templates/{drag_drop,code,project}.js">` but **NOT** `terminal.js`. The dispatch table at line 3841 maps `'terminal_exercise' → 'terminal' → 'SllTemplateTerminal'`, but `SllTemplateTerminal` is never loaded. Result: the widget never mounts, the learner sees only briefing prose, no paste box, no Submit button, no BYO-key panel. **All 14 terminal_exercise steps are invisibly broken by this.** Trivial one-line fix (add `<script src="/templates/terminal.js?v=1.1.1" defer></script>`). After force-loading the script via eval, the full widget renders correctly, confirming the fix.
- Attempt 1 (wrong): pasted `asdf nonsense`
  - Score: 0% · "0% on this attempt. 2 more retries before the full breakdown reveals. Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully."
  - Did this help? **No** — generic. Doesn't tell me WHICH rubric markers were missing.
- Attempt 2 (right): pasted `brew install anthropic/tap/claude-code` + `claude --version → claude-code 0.8.1`
  - Score: 100% · "Perfect! The output clearly shows successful installation and the version command returns 'claude-code 0.8.1', which meets all requirements for the rubric. All expected markers present."
  - Did this help? **Yes** — LLM-rubric cites exactly what it detected.
- **BYO-KEY VERIFIED ✅**: panel reads "🔐 Your key stays on your machine. Configure Claude Code with `claude /login` (or set ANTHROPIC_API_KEY in your shell). This page will never ask for your key." Zero key input fields, zero localStorage slots. (Also verified at code level — terminal.js has an explicit comment banning key capture.)
- **PLATFORM-AWARE VERIFIED ✅**: macOS / Linux / Windows+WSL each get their own `<h4>` heading, distinct install command, troubleshooting `<details>` expandable.
- Verdict: ⚠ BLOCKED-BY-WIRING-BUG in production; once force-loaded, passes cleanly.
- UI notes:
  - After Submit sometimes the hash navigates unexpectedly to unrelated modules (observed 1.2→3.1, 1.3→4.3, 2.3→1.2). Root cause not fully pinned — possibly an errant keydown listener or a bug in `nextStep()` for completed steps when `state.modules` has a numeric-index map and `findIndex` mismatches. Does not block grading, but is disorienting.

## Step 1.3 — "Authenticate with `claude /login`" — terminal_exercise
- Briefing clarity: 4/5 | time: ~3 min
- Attempt 1 (wrong): `asdf` → 0% generic feedback (same as 1.2)
- Attempt 2 (partial right): paste included `/login` + `/status` but omitted "available models" line
  - Score: 77% · "Good work showing successful authentication and status confirmation, but the submission is missing the step showing available models listed, which was required in the rubric for full credit. Your output is missing 1 of 3 expected markers."
  - Did this help? **Yes — very** — pinpoints the missing marker precisely. This is the grader's BEST feedback of the walkthrough.
- Verdict: ⚠ BLOCKED-BY-WIRING-BUG; grader excellent once widget renders.

## Step 1.5 — "Sanity check: what went right?" — code_exercise
- **🚨 CLI-STEERING SLIP (P1)**: This step is labeled `code_exercise` and asks the learner to write Python that parses pasted terminal output (`validate_claude_installation()`, `parse_terminal_output()`, `check_edit_quality()`). The course is ABOUT Claude Code CLI usage, but this step forces meta-programming a parser for it. Mis-typed — should have been `terminal_exercise`. Creator's CLI-steering didn't catch this class: when the user scenario is "paste your output", the exercise should be a `terminal_exercise` not a `code_exercise` around parsing that paste.
- Attempt 1 (right, first-try): wrote a 20-line solution using regex for version + string-contains for diff/accept
  - Score: 100% · "All 6 hidden tests passed in Docker (python)."
  - Did this help? **Yes** — unambiguous pass. Docker runner works end-to-end.
- Verdict: ✅ passed / ⚠ mis-typed (would confuse a real beginner who thought they'd paste terminal output)
- Tests observed: `test_validates_version_output`, `test_parses_edit_diff`, `test_detects_acceptance`, `test_validates_meaningful_comment`, `test_rejects_poor_edits`, `test_installation_check_success` — 6 tests, meets Layer A.

## Step 3.3 — "Plan subagent: design a feature before writing it" — terminal_exercise
- Attempt 1 (wrong): `asdf random junk`
  - Score: 0% · same generic feedback as 1.2
- Did not complete a right attempt (pattern now clear).
- Verdict: ⚠ BLOCKED-BY-WIRING-BUG (same as all terminal_exercise); grader responsive.

## Step 4.1 — "Write a PostToolUse hook that runs tests after Edit" — code_exercise
- **🚨 TEST-COUNT GATE MISS (P2)**: Creator emitted hidden_tests as a **bash test suite** (`test_script_exists()`, `test_tool_name_check()` — bash function syntax). The Layer A regex gate in `_is_complete` counts `def test_` / `test(` / `func Test` and misses bash's `test_name() {...}`. So this step shipped with a bash suite that DOES have 4+ test functions, but the gate doesn't know that.
- Attempt: not executed (too many steps to walk exhaustively — noted as findable).
- Briefing clarity: 4/5 — starter code has clear TODOs, `hint` says "Check the TOOL_NAME environment variable and use the check_python_files helper function before running pytest."
- `must_contain` has 3 specific bash tokens: `if [[ "$TOOL_NAME" == 'Edit' ]]`, `check_python_files "$AFFECTED_FILES"`, `pytest -q`
- Verdict: ⚠ partial — exercise well-formed but the Layer A gate's regex needs to include bash pattern `^\s*test_\w+\s*\(\)`.

## Step 4.4 — "Debug a broken hook" — code_review
- Briefing clarity: 4/5 — briefing lists "Bug Categories to Hunt For" (event matching / overly broad matchers / …). 37-line hybrid JSON+bash code sample.
- `demo_data.bugs` is sanitized to `[{hidden:true}, ...]` — answer-leak protection works.
- Attempt 1 (wrong-probing): flagged lines 1, 5, 17, 34 (random)
  - Score: 0% (1 correct · 3 wrong) · "0% on this attempt. 2 more retries before the full breakdown reveals."
- Attempt 2: flagged 3, 6, 8, 29 (my best guesses: `postToolUse` case, `tool_used` event name, `"*"` broad matcher, `$1` positional arg)
  - Score: 30% (2 correct · 2 wrong) · "1 more retry before the full breakdown reveals"
- Attempt 3: flagged 3, 6, 8, 32 (added the `if [[ -f ` line thinking shell injection)
  - Score: 30% (2 correct · 4 wrong) · "Found 2/4 bugs. False positives on lines: [3, 32] (-20% penalty). Missed bugs on lines: [34, 36]"
- Did this help? **Yes on attempt 3** — full breakdown revealed real bugs (lines 34 = `echo "Tests completed"` without checking pytest exit code; 36 = no `exit 1` on file-not-found). But the grader treats my flag of line 3 (`"postToolUse"` — lowercase, which IS the CORRECT key name mistake per Claude Code docs — should be `PostToolUse`) as a false positive. That's arguable — a beginner who knows the Claude Code schema will correctly flag line 3 and be penalized. Grader-contract bug OR the Creator chose a narrower bug set.
- Verdict: ⚠ partial — I never clear 30%. Grader accepted only pytest-error-handling bugs, not the config-key casing bug that a Claude-Code-fluent learner would flag first.

## Step 5.4 — "Capstone: ship `search_docs` MCP server and call it live" — system_build
- Inspection only (requires real Railway deploy to grade).
- Scope: 4 phases (Scaffold 20min → Implement 60min → Test 30min → Ship 50min = 160 min / ~2.5 hrs)
- 10-item checklist covers: install Claude Code / clone starter / implement `search_docs` greps markdown / implement `git_analyze_commits` via GitPython / curl test local MCP / register in settings.json / run `claude "Use search_docs to..."` / deploy to Railway / create `/release-notes` slash command / generate real release notes.
- `endpoint_check` targets a learner-specific Railway URL (`https://<learner-deploy>.railway.app/tools/search_docs`) with POST expecting JSON-shape `{content, metadata.tool: "search_docs"}`.
- Starter `code` (2795 chars) scaffolds FastAPI + CORS middleware + Pydantic + Click CLI.
- Verdict: ✅ looks production-grade — real deployment, real MCP protocol, real slash command wiring.
- UI: "Check my CI" button + "Submit capstone" button suggest GHA-workflow-check hook too (not inspected).
- Depth assessment: this capstone genuinely teaches end-to-end MCP server authoring + slash command extension. Not hand-wavy.

## Extra-check answers

### 1. Zero key capture — ✅ VERIFIED (but gated by wiring bug)
- `terminal.js` has explicit no-key-capture rules baked in as a comment. BYO panel text reads "🔐 Your key stays on your machine. Configure Claude Code with `claude /login` (or set ANTHROPIC_API_KEY in your shell). This page will never ask for your key."
- Searched DOM for `input[type=password]`, `input[name*=key i]`, `localStorage.setItem.*api`: zero matches.
- Screenshot captured once template was force-loaded — confirms panel is informational only.

### 2. Platform-aware install — ✅ VERIFIED
- Step 1.2 `demo_data.instructions` renders 3 distinct blocks: **macOS** (`brew install anthropic/tap/claude-code`), **Linux** (`curl -fsSL https://api.claude.ai/cli/install.sh | bash`), **Windows + WSL** (same curl + WSL-setup troubleshooting). Each has a troubleshooting `<details>` expand.
- Also step 1.1 concept mentions "Platform-specific installation (macOS/Linux/Windows+WSL)" explicitly.

### 3. Grader feedback quality — ⚠ MIXED
- Wrong-first gives GENERIC "Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully." No signal on WHICH rubric markers are missing. Useless for iteration from the first wrong.
- Partially-right gives **EXCELLENT** specific feedback: "missing the step showing available models listed, which was required in the rubric for full credit. Missing 1 of 3 expected markers." Cites the missing marker.
- After 3 attempts on code_review, full breakdown reveals "Found 2/4 bugs. False positives on: [...]. Missed bugs on: [...]" — useful for learning.
- Net: the grader is USEFUL once learner has tried partially-right, and useful after exhausting 3 attempts. But the first-wrong response is too generic — a beginner could be stuck for many minutes.

### 4. Capstone depth — ✅ SUFFICIENT
- M5 teaches: slash command authoring (M5.S1 terminal_exercise `/release-notes`), minimal MCP server with stdio JSON-RPC (M5.S2 warm-up code_exercise with 6 hidden tests including `tools/list` and `tools/call` handlers), full deploy capstone (M5.S3 system_build: scaffold + implement + test + deploy to Railway + register in settings.json + integrate via slash command).
- The concept step at M5.S0 walks through the slash-command / MCP-server two-layer architecture with concrete examples.
- Not hand-wavy — a learner completing all 4 steps would actually author a custom slash command AND ship an MCP server. ✅

### 5. code_exercise steps that slipped through CLI-steering — ⚠ 2 of 4 are concerning
- **M1.S5 "Sanity check"**: mis-typed. Should be terminal_exercise (paste + LLM-rubric). Instead learner writes a Python parser. ← cleanest CLI-steering slip.
- **M4.S1 "Write a PostToolUse hook"**: correctly-scoped (learner writes shell script for the hook), but hidden_tests use bash test functions which the Layer A gate doesn't count. Functional but gate-bypassing.
- **M2.S4 "When NOT to use Claude Code"** and **M3.S4 "Delegation judgment call"**: not inspected in detail. M2.S4 asks learner to write a CLAUDE.md file (legit code_exercise). M3.S4 likely asks a design-judgment question (code_exercise for a judgment call is a mis-type but I didn't verify).
- **M5.S2 warm-up MCP server**: correctly-typed — learner writes an actual Python MCP server; 6 Python hidden tests.
- Net: ~1-2 out of 4 code_exercises slipped the CLI-steering filter. Creator prompt needs to reinforce "this is a CLI course, not a Python parser course."

## Summary — BUG / REGRESSION / FRICTION list (prioritized)

### P0 — Blockers
- **W1 — terminal.js not loaded in `frontend/index.html`** (lines 21-23). Blocks **14 of 24 steps** (all terminal_exercise). Trivial one-line fix: add `<script src="/templates/terminal.js?v=1.1.1" defer></script>` alongside the other three template scripts. After force-load, everything works.

### P1 — Major friction
- **F1 — Generic wrong-first grader feedback.** "Your submission didn't match what the exercise expects. Re-read the briefing..." tells a beginner NOTHING. The LLM-rubric grader CAN emit specific marker-level feedback (proven on partial-right submissions) but suppresses it on the first wrong. Recommendation: always show "you're missing N of M markers" even on 0%, without revealing which specific rubric markers. A beginner learns from directional signal ("you have 0 markers" vs "3 markers but some are wrong").
- **F2 — Unexpected hash navigation on Submit.** Observed multiple times: submitting on Mx.Sy pulls you to Mz.Sw where z/w aren't +1. Did not fully root-cause. Possibly a completed-step-skip logic in `nextStep()` or a stale reference in `state.modules`. User disorientation is real.

### P2 — Content/Creator-level
- **C1 — M1.S5 "Sanity check" mis-typed as code_exercise** — should be terminal_exercise. Course steering needs a rule: if the starter code's docstring says "parse pasted terminal output", the type is wrong.
- **C2 — M4.S1 bash hidden_tests bypass Layer A count.** Regex `def test_` / `test(` / `func Test` doesn't match bash `test_name() { ... }`. Gate should be extended.
- **C3 — M4.S4 code_review** grader's "correct" bug set is narrower than a real Claude-Code-fluent reviewer would flag. Line 3 (`"postToolUse"` lowercase, should be `PostToolUse` per hook schema) is treated as a false positive.

### Pass / Stuck / Partial tally
| Type | Walked | ✅ Passed | ⚠ Partial/Friction | ❌ Stuck | Notes |
|------|--------|-----------|----------------------|----------|-------|
| concept | 1 | 1 | 0 | 0 | Auto-complete |
| terminal_exercise | 3 (+ inspection of all 14) | 2 (after workaround) | 1 | 14 in prod | Blocked by W1 |
| code_exercise | 1 attempted + 3 inspected | 1 | 0 | 0 | 1 mis-typed (C1) |
| code_review | 1 | 0 | 1 | 0 | Stuck at 30% after 3 attempts |
| system_build | 0 attempted (inspection only) | — | — | — | Real deploy required |

## Verdict

**❌ REJECT — blocked on P0 wiring fix**

14 of 24 steps (the entire terminal_exercise chain — the CORE of this BYO-key, Claude-Code-specific pedagogy) are unreachable in production because `terminal.js` is not loaded by `index.html`. This is a trivial one-line fix but also a wiring class that CLAUDE.md Step-1 approval table explicitly classifies as "Wiring/template bug → fix the wiring; DO NOT regen. Rerun Step 1 agent on the SAME course."

Once the wiring bug is fixed:
- Rerun the beginner-agent Step 1 on this same course (no regen needed).
- Separately address the content-level issues (C1 mis-typing, F1 wrong-first grader feedback) via Creator-prompt iteration + regeneration.

The dual-agent bar (beginner + domain-expert) can't be evaluated here with confidence because the terminal path is broken. Domain-expert review should wait until at least one complete beginner walkthrough passes without workarounds.

**Positive signals (when the template renders correctly)**:
- BYO-key panel is informational-only as required — zero key capture — design adheres to the hard rule.
- Platform-aware install (macOS/Linux/Windows+WSL) is rendered side-by-side as mandated.
- LLM-rubric grader works and gives excellent partial-credit + marker-level feedback.
- M5 capstone is production-grade (slash command + MCP server + Railway deploy + GHA CI check).
- Answer keys are sanitized (`bugs: [{hidden:true}, ...]`, no leaks).
- Concept steps use a consistent CodeFlow / Marcus Chen narrative that anchors the whole course.
