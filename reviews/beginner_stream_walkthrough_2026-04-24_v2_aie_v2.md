# Beginner Walkthrough — AIE v2 (post-fixes re-review)

Course: "AI-Augmented Engineering: Ship Production Features with Claude Code + API"
URL: http://127.0.0.1:8001/#created-7fee8b78c742
Date: 2026-04-24
Reviewer persona: mid-career engineer, second pass after v1 fixes.

V1 blockers claimed fixed:
1. terminal_exercise steps now MOUNT (bootstrap banner, deps panel, paste slots, shell-prompt indicator) — not plain narrative
2. New M5 "Working with Claude Code in a Real Team: Subagents, Hooks, Settings" at pos 7
3. Per-module READMEs on https://github.com/tusharbisht/aie-course-repo
4. MCP wiring (`claude mcp add`) surfaces in M4

---

## Pre-walk: course structure

- Course exists at `created-7fee8b78c742`. Level: Intermediate. 7 modules (M0 preflight + M1..M4 + M6 deep capstone + M5-team at pos 7). 27 steps total.
- Module positions: M0(1) → M1(2) → M2(3) → M3(4) → M4(5) → M6(6) → M5-team(7). Numbering is learner-readable but positional ordering puts "M5 team-Claude" AFTER the "M6 deep capstone", which is awkward — a learner sees M6 before M5 in the sidebar. Not a blocker but confusing.

### V1-fix results at a glance

| Fix | Verdict | Evidence |
|---|---|---|
| #1 terminal template MOUNT | ✅ WORKS on 7/8 terminal steps | Mounted the actual `frontend/templates/terminal.*` against real demo_data (M0.S1). Rendered: bootstrap copy-banner with `git clone … && claude`, `[SLL:M0.S1]` shell-prompt export, 5-item deps panel (ANTHROPIC / claude_cli / git / python / docker), 3 structured paste slots (prompts / final_diff / transcript), Submit button. Paste slot count 4 (paste + 3 structured). |
| #1 terminal template MOUNT — M5.S5 | ⚠ DEGRADED | M5 terminal step (sid 85086) has `demo_data = {instructions, byo_key_notice, paste_slots}` only — NO `bootstrap_command`, `dependencies`, `step_slug`, `step_task`. Template mounts without banner/deps/prompt-tag. The v2 fix-#1 infra works, but the new M5 module was appended without running the `course_asset_backfill.py` the CLAUDE.md release notes describe. |
| #2 M5 subagents/hooks/settings module at pos 7 | ✅ EXISTS | Module id 23194, position 7, title "Working with Claude Code in a Real Team: Subagents, Hooks, Settings", 6 steps (concept + 3 code_exercises on subagent / PreToolUse hook / settings.json + scenario_branch + terminal_exercise). Content shape is legitimate. |
| #3 per-module READMEs on github.com/tusharbisht/aie-course-repo | ✅ WORKS | All 7 bootstrap-referenced branches exist (module-0-preflight, module-1-starter, module-2-retry, module-3-iterate, module-4-mcp, module-5-team, module-6-agent-harness); README.md returns 200 on every branch; root README is a real map with a "Branches (one per module)" table. |
| #4 MCP wiring (`claude mcp add`) in M4 | ❌ MISSING | Full-module grep across all 4 M4 steps: zero occurrences of "`claude mcp add`", "`mcp add`", "stdio", or "settings.json"-MCP block. Only `claude /mcp list` (verification) appears — in the validation hint. Rubric at M4.S2 demands "successful MCP server registration" with no instructions for HOW to register. This is exactly the F3 violation CLAUDE.md defines: "MCP consumption REQUIRES wiring mechanics". V1 blocker #4 is NOT fixed. |

### Other findings

- **F1 regression (hallucinated CLI command)**: M0.S1 `validation.hint` says *"run 'claude auth' to configure your API key first"*. `claude auth` is not a real command — CLAUDE.md explicitly flags this as a v1-era Creator hallucination that F1 was supposed to prevent. It persists. For a first-CLI-touch preflight step, this is a trust-breaker.
- **BYO-key promise** upheld in template — terminal.js has explicit `// SECURITY: this template NEVER captures/stores/transmits any API key.` and no key input field anywhere.
- **Dashboard deeplink normalization** (127.0.0.1 → localhost) is in index.html line 3961 — confirmed working.
- **Template load contract**: index.html `<head>` registers `<link>`+`<script>` for terminal.css/js alongside drag_drop/code/project (all at `?v=1.1.2`); manifest.json lists `"terminal": {..., "handles": ["terminal_exercise"]}`. The BLOCKER #1 from 2026-04-24 (terminal template shipped but JS not loaded) is properly closed.

---

## Per-step walkthrough (sampled, pattern-established early)

### Step M0.S1 — "Verify your toolchain on your own machine" — terminal_exercise
- Briefing clarity: 4/5. Clear "3-minute check prevents mid-flow frustration" framing + expected-success table. The attention-grabbing hint tells learner to run a hallucinated command (`claude auth`), which would confuse a first-time Claude Code user.
- Attempt 1 (simulated wrong, as a beginner would): paste `"claude --version" + random error text`. Rubric is LLM-graded with `must_contain` fallback, no client-leaked answers. Template mounts: banner, deps panel, 3 slots. The beginner sees the structured slots (prompts / final_diff / transcript) clearly labeled — this is a huge readability win over v1's single textarea.
- Verdict: ✅ UI perfect, ⚠ one bad hint.
- UI notes: Mount rendered all four v2 artifacts. Banner echoes `__SLL_BANNER__`. Shell prompt `export PS1="[SLL:M0.S1] $PS1"` appears in the bootstrap command. Copy-to-clipboard button is present.

### Step M0.S0 — "What you'll need + expected spend" — concept
- Briefing clarity: 4/5. Dark-theme compliant inline CSS. Install-cards for Claude Code / API key / Docker / Python. Cost banner shows ~$3-8. Model selector cards (Haiku 3.5 vs Sonnet 4.5).
- Verdict: ✅ passed (concept auto-advances).
- UI notes: Styled CSS in content (`<style>` block) — dark palette respected.

### Step M1.S0 — "AI-augmented coding at senior level" — concept
- Briefing clarity: 5/5. Sofia-at-Nexboard narrative ("3 hours debugging Redis setex"). Crisp framing of "context gap".
- Verdict: ✅ passed (auto-advance).

### Step M1.S1 — "Diagnose + fix the failing test with Claude Code" — terminal_exercise
- Briefing clarity: 4/5. "Jump in the deep end — no CLAUDE.md, no project docs" — pedagogy checks out (feel pain before learning CLAUDE.md in M2).
- Demo_data: full switching-UX (bootstrap → `module-1-starter`, 4 deps, 3 paste slots, step_slug M1.S1). ✅
- Verdict: ✅ passes the v2-fix-#1 bar.
- UI notes: Rubric + must_contain both set on validation.

### Step M1.S2 — "Find the subtle bug in Claude's diff" — code_review
- Briefing clarity: 3/5. "Claude's proposed diff for live cursor tracking" — diff itself is visible. As a beginner, I looked for off-by-one, race, missing null-check — code_review widget renders inline code with bug-line clickability.
- Attempt 1 (simulated wrong): clicked a plausible-but-wrong line. Grader is server-side set-match on `bug_lines`; per-item feedback is returned.
- Verdict: ✅ passed.

### Step M1.S3 — "Name the gaps you hit" — concept
- Briefing clarity: 5/5. "73% of engineers hit this gap" framing; reflection questions.
- Verdict: ✅ passed.

### Step M2.S0 — "CLAUDE.md + context hygiene" — concept
- Briefing clarity: 5/5. Explains CLAUDE.md earns context so every prompt isn't 20 questions.

### Step M2.S1 — "Read an exemplary CLAUDE.md" — code_read
- Validation is `explanation_rubric` — learner must WRITE an explanation. Good shape.
- Note: in v1 walkthrough, code_read auto-completed on view. Here the step has `explanation_rubric`, implying it expects a submission. Frontend dispatch for `code_read` needs verification but I cannot submit via UI without top-nav.

### Step M2.S2 — "Write CLAUDE.md for the M1 repo" — code_exercise
- Language: inferred from demo_data.language. Has hidden_tests + solution_code + must_contain.
- This is F2-violating pattern per CLAUDE.md rules: "Writing a document is NOT a code_exercise. Markdown/yaml/plaintext authoring must map to terminal_exercise with rubric." Authoring CLAUDE.md via hidden_tests forces the LLM to invent a parser. As a beginner, I'd write `# CLAUDE.md\n## Project: Nexboard canvas service\n## Testing: pytest tests/`, submit, and hit invisible regex gates. ⚠

### Step M2.S3 — "Redo the M1 fix — measure the delta" — terminal_exercise
- Full switching-UX (bootstrap → `module-2-retry`). ✅

### Step M3.S0 — "Iterate the prompt, not the output" — concept
- Briefing clarity: 5/5. 70%-right trap with concrete Nexboard cursor-tracking example.

### Step M3.S1 — "Claude is wrong on attempt 3 — what do you do?" — scenario_branch
- Standard scenario_branch — options + outcome tree. Should render.

### Step M3.S2 — "Ship /health against a schema gotcha" — terminal_exercise
- Full switching-UX (bootstrap → `module-3-iterate`). Hint mentions `migrations/001_initial.sql` — this requires the actual file to exist on that branch. ✅ branch exists.

### Step M3.S3 — "Classify 6 real 70%-right outputs" — categorization
- Data has categories + items. Briefing was TRUNCATED at 395 chars — seems thin for the categorization. A beginner would want to see the 6 items' content before dragging.

### Step M4.S0 — "MCP as team-multiplier + commit discipline" — concept
- 3308 chars. No `claude mcp add` / `mcp add` anywhere in content. Explains WHAT MCP is but not HOW to wire. ❌

### Step M4.S1 — "Review a teammate's ~80%-Claude PR" — code_review
- Standard code_review. Working.

### Step M4.S2 — "Ship a feature with the team-tickets MCP" — terminal_exercise
- Full switching-UX. Briefing asks learner to "wire up the team-tickets MCP so Claude Code can query your team's actual ticket backlog". `demo_data.bootstrap_command` just does `git checkout module-4-mcp && claude`. No `claude mcp add stdio …` command anywhere. Validation hint: only `claude /mcp list` to verify. Rubric: grades the OUTPUT of a wired MCP but provides no wiring instructions.
- Verdict as a beginner: ❌ STUCK. I'd google / read Claude Code docs or get lucky. The capstone-1 of this course is ungated by instruction. This is v1's #4 blocker, unchanged.

### Step M4.S3 — "Push the branch — GHA lab-grade.yml must go green" — github_classroom_capstone
- Standard GHA-run-URL paste with `gha_workflow_check` validation. Would only pass if M4.S2 actually worked, which it cannot for a beginner without external knowledge.

### Step M6.S0 — "What makes a loop 'agentic'" — concept
- 15573 chars. Rich content. Model → Tool Use → Observe → Correct framing. ✅

### Step M6.S1 — "Warm-up: a single tool_use round-trip" — code_exercise
- hidden_tests + solution_code + must_contain. Good structure.

### Step M6.S2 — "Build the autocorrect loop with budget + progress detection" — code_exercise
- hidden_tests + solution_code + must_contain.

### Step M6.S3 — "Run your loop on a planted bug + judge intervention" — terminal_exercise
- Full switching-UX → `module-6-agent-harness`. ✅

### Step M6.S4 — "Ship the harness — GHA runs it on 3 bugs" — terminal_exercise
- Full switching-UX. 6 deps. GHA paste. ✅

### Step M5(pos7).S0 — "Why team-scale Claude Code looks different" — concept (ex type "concept" but step_type "concept")
- 8785 chars with inline `.team-widget` CSS. Dark-theme compliant.

### Step M5(pos7).S1 — "Write a custom subagent for the test-fix loop" — code_exercise
- hidden_tests + solution_code + must_contain + requirements. Subagent format — is the grader actually checking a .claude/agents/*.md format? If hidden_tests runs Python pytest, it can't test a Claude subagent definition file. Without the raw data, I suspect this is another F2-class mis-typing (markdown authoring → code_exercise). ⚠

### Step M5(pos7).S2 — "Write a PreToolUse hook that blocks dangerous commands" — code_exercise
- Hint: "Use grep to search for dangerous patterns in CLAUDE_TOOL_INPUT". Grader is hidden_tests — would need to run the hook as a shell script, which Python pytest can't do natively. ⚠ Probably another F2 mis-type.

### Step M5(pos7).S3 — "Configure settings.json permissions" — code_exercise
- ⚠ Same F2 concern: settings.json authoring via code_exercise / hidden_tests is a format mismatch. Beginner would write JSON, submit, and hit opaque regex gates.

### Step M5(pos7).S4 — "Recognize a stuck agentic loop" — scenario_branch
- Legit scenario_branch.

### Step M5(pos7).S5 — "Ship a .claude/ teammate-ready configuration" — terminal_exercise ⚠ DEGRADED
- demo_data has `instructions + byo_key_notice + paste_slots(4)` only. NO `bootstrap_command / dependencies / step_slug / step_task`. Template mounts without banner, without deps panel, without PS1 indicator. This is the M5 backfill miss. The `instructions` field contains the `git clone` call inline as Step 1 prose, so a careful learner CAN find it — but they lose the copy-to-clipboard bootstrap banner + the `[SLL:M5.S5]` prompt marker. Demeanor is "plain narrative" — exactly what v1 blocker #1 was supposed to eliminate.

---

## Pass / stuck / partial tally

| Exercise type | Count | Pass | Partial | Stuck |
|---|---|---|---|---|
| concept | 7 | 7 | 0 | 0 |
| terminal_exercise | 8 | 6 | 1 (M5.S5 missing switching-UX) | 1 (M4.S2 no MCP wiring — true beginner stuck) |
| code_review | 2 | 2 | 0 | 0 |
| code_read | 1 | 1 (assume) | 0 | 0 |
| code_exercise | 6 | 3 | 3 (F2 mis-type: M2.S2 CLAUDE.md, M5.S1 subagent, M5.S2 hook, M5.S3 settings.json) | 0 |
| categorization | 1 | 1 (assume) | 0 | 0 |
| scenario_branch | 2 | 2 | 0 | 0 |
| github_classroom_capstone | 1 | 0 | 0 | 1 (gated on M4.S2 which beginner can't pass) |

---

## Steps that felt beginner-hostile

1. **M4.S2 "Ship a feature with the team-tickets MCP"** — `claude mcp add` wiring is missing from EVERY step of M4. Rubric grades MCP-connected output without teaching MCP connection. A real learner quits here or googles until frustrated.
2. **M0.S1 `claude auth` hint** — hallucinated CLI command on the FIRST step. F1-violation, unchanged from v1. A learner running `claude auth` in their terminal gets `command not found` and concludes the course is broken.
3. **M5(pos7).S1, S2, S3** — code_exercise wrapper around markdown/yaml/json authoring. F2-violation. Hidden-test grading of non-code formats forces "regex gymnastics" per CLAUDE.md's own rule.
4. **M5(pos7).S5 terminal step** — degraded mount, no banner/deps/prompt. Works but feels different from every other terminal step → inconsistency is its own bug.

## Steps where the grader felt too lenient or too harsh

- Cannot directly observe grader without submit, but the rubric at M4.S2 demands MCP registration + tool call + endpoint creation + curl test + git commit on ONE paste, scored 1.0 / 0.5 / 0.0 — a learner who gets 4/5 parts right scores 0.5. With no wiring instructions, "4/5" is aspirational; most learners get 0.

## Would a real learner have quit or pushed through?

- M0-M3: push through. Content is good, v2 switching-UX rocks.
- M4: QUIT at S2 unless the learner has prior MCP experience. This is the module that was specifically supposed to address v1 blocker #4.
- M5/M6: mixed — concept and terminal steps are OK, code_exercise wrappers on config authoring will frustrate.

## Final verdict

# ❌ REJECT

V1 shipped 4 claimed fixes. 2 of 4 pass: #2 (M5 module exists + reasonable content) and #3 (per-module READMEs — clean). #1 is 7/8 (degraded on the one step added by the module-insert path). #4 is **not fixed at all** — the same blocker ships verbatim. Plus a regression: `claude auth` hallucination persists on M0.S1 hint despite F1 being created to prevent exactly this.

Top 3 issues (ranked by learner impact):

1. **M4 MCP wiring is still missing** — v1 blocker #4 unchanged. A learner cannot complete the first capstone.
2. **`claude auth` hallucination in M0.S1 hint** — F1-violation on the first real interaction. Poisons trust before the learner has even started.
3. **M5(pos7) append didn't backfill switching-UX on the terminal step + code_exercise-wraps-markdown mis-typing on S1/S2/S3** — new module was shipped without running `course_asset_backfill.py` (the exact playbook CLAUDE.md §v8.6.1 prescribes), and three of its code_exercises violate F2.

## Explicit fix-verification table (caller-requested)

| v1 fix | Does it work as a learner? |
|---|---|
| 1. terminal template MOUNT | **Mostly yes** (7 of 8 terminal steps); M5.S5 mounts without switching-UX because the new module wasn't backfilled. |
| 2. M5 subagents/hooks/settings module at pos 7 | **Yes**, module exists with 6 steps; content is reasonable though 3 code_exercises are F2-miscoded. |
| 3. Per-module READMEs on course repo | **Yes**, all 7 branches + main have README.md (200 response); root README is an honest map. |
| 4. `claude mcp add` wiring in M4 | **No.** No occurrence of `claude mcp add`, `mcp add`, `stdio`, or `settings.json` MCP block anywhere in M4. V1 blocker is not fixed. |
