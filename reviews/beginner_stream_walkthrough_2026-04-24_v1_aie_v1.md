# Beginner Walkthrough — AI-Augmented Engineering: Ship Production Features with Claude Code + API
Date: 2026-04-24
Course URL: http://127.0.0.1:8001/#created-7fee8b78c742
Reviewer role: Mid-career engineer new to structured AI workflows (beginner-learner mode)
Focus: New terminal_exercise switching-UX (bootstrap banner, dependencies panel, structured paste slots)

---

## Course overview (from sidebar)
- M0 — Preflight Check (1/2 done already)
- M1 — Your First AI-Assisted Fix (Feel the Context Gap) (0/4)
- M2 — Close the Context Gap with CLAUDE.md (0/4)
- M3 — Drive 70%-Right Output to Done (0/4)
- M4 — Ship with MCP + Review a Teammate's AI PR (Capstone 1) (0/4)
- M6 — Agentic Coding from First Principles (Deep Capstone) (0/5)

(Note: no M5 in sidebar — suspicious gap in module numbering.)

---

## Step M0.1 — "What you'll need + expected spend" — concept
- Briefing clarity: 4/5  | time on step: ~2 min
- Type: concept (read-only). Auto-completed on view (sidebar showed 1/2 already done).
- Shows spend breakdown ($3–8), checklist of tools, model-strategy cards.
- Verdict: ✅ passed (auto)
- UI notes: Content is dense but readable. "🔄 Regenerate" and "✏️ Edit" buttons visible — creator tools showing in learner view; shouldn't be there for beginner learner mode.

## Step M0.2 — "Verify your toolchain on your own machine" — terminal_exercise
- Briefing clarity: 2/5  | time on step: ~3 min
- Type-banner says **terminal_exercise** — but the content is rendered using `.concept-content` only. No input box, no Submit button, no bootstrap-command banner, no dependencies panel, no paste slots — none of the NEW switching-UX I was told to evaluate.
- Briefing says "You'll see Claude Code respond to a simple query with the exact string HELLO" but gives no command to run, no paste area, no way to submit the output.
- Next button says **"Next Module →"** (this is last step of M0) and is enabled without any submission. A learner can click through without actually verifying anything.
- Verdict: ❌ stuck (beginner-hostile) — broken step. Step type is terminal_exercise but rendered as concept. Either the schema is missing `bootstrap_command` + dependencies + paste slots, OR the frontend isn't switching renderers on step type.
- UI notes: **Major bug**: terminal_exercise UI is entirely absent. No friction-reducer helped because there was literally no input UI.

## Step M1.1 — "AI-augmented coding at senior level" — concept
- Briefing clarity: 4/5  | time on step: ~2 min
- Good framing: Sofia's 3-hour debug pain, senior-engineer judgment categories, preview of end state.
- Verdict: ✅ passed (auto)

## Step M1.2 — "Diagnose + fix the failing test with Claude Code" — terminal_exercise
- Briefing clarity: 3/5  | time on step: ~3 min
- Again rendered as `banner-concept` / `.concept-content` — no bootstrap-command banner, no dependencies panel, no paste slots. Same bug as M0.2.
- Text tells me to use Claude Code on my machine, but there's no structured area to paste command output, no slot for the failing test name, no slot for the fix diff. Just a narrative + Next button.
- Verdict: ❌ stuck (beginner-hostile) — UI is missing entirely for this step type.

## Step M1.3 — "Find the subtle bug in Claude's diff" — code_review
- Briefing clarity: 4/5 | time on step: ~4 min
- Attempt 1 (wrong): clicked line 2 (`const express = require('express')`) as obvious non-bug.
  - Score: 0% (0/1 correct)
  - Feedback verbatim: "Score: 0% (0 of 1 correct) 0% on this attempt. 2 more retries before the full breakdown reveals. **5 of your responses did not match** the expected answer."
  - Did this help me? NO — the "5 of your responses did not match" phrasing is **wrong** (I selected only 1 line). It's a stale/generic message, not per-attempt. Confusing for a beginner.
- Attempt 2 (real try): flagged lines [18, 25, 38, 42, 55] = no-transaction, no-TTL, cursor-move handler (no auth), cursor-set (no TTL), disconnect cleanup.
  - Score: 20% (2/5 correct), again "5 of your responses did not match" — still wrong phrasing.
  - Did this help me? Partially — it told me how many were right but not WHICH were right vs wrong on early attempts. Generic on wrong tries.
- Attempt 3: added lines [13, 20, 54, 57]. Final feedback revealed: "Found 2/4 bugs. False positives on [13, 20, 42, 54, 55, 57] (-60% penalty). Missed bugs on lines: [19, 39]"
  - Score: 0% (clamped)
  - Verdict: ⚠ partial — grader is **off-by-one** on meaningful clickable regions. I clicked line 38 (`socket.on('cursor-move'...)`) but grader expected 39 (the destructuring line). Same for 18 vs 19 (handler header vs INSERT body). Beginner-hostile because "click the line with the bug" is ambiguous: the comment preceding an INSERT vs the INSERT itself.
- UI notes:
  - Wrong-attempt feedback says "5 of your responses did not match" regardless of how many were selected → **bug in feedback copy**
  - -60% FP penalty clamps to 0% on a 2/4 find — feels harshly punishing for a first-time reviewer
  - Reveal of correct answers only appears on attempt 3 — that's fine pedagogy, but the penalty math undermines the reveal
  - The line numbers in the code block have visible double-blank-line gaps; harder to scan than standard diff

## Step M1.4 — "Name the gaps you hit" — concept
- Briefing clarity: 4/5 | time on step: ~1 min
- Named the 5 observable signs of under-contextualized AI. Auto-complete on view.
- Verdict: ✅ passed (auto)

## Step M2.1 — "CLAUDE.md + context hygiene" — concept
- Briefing clarity: 5/5 | time on step: ~2 min
- Strong narrative (Sofia, Marcus Chen metrics), concrete structure of CLAUDE.md.
- Verdict: ✅ passed (auto)

## Step M2.2 — "Read an exemplary CLAUDE.md" — code_read
- Briefing clarity: 4/5 | time on step: ~3 min
- Full CLAUDE.md example for Nexboard Canvas service shown in read-only editor. Genuinely useful reference.
- Explanation textarea present with placeholder "What does this code do?".
- Attempt 1: typed "It's a CLAUDE.md file." as half-answer. Clicked **"Submit explanation"**.
  - Score: **NO FEEDBACK RETURNED**. No POST to /api/exercises/validate fired (confirmed via network panel). No score, no pass/fail banner, no advance signal.
  - Did this help me? NO — I genuinely couldn't tell if I passed, failed, or if the button was broken.
- Verdict: ⚠ partial — step is read-only but the **Submit explanation button is dead weight** — clicking it does nothing. Either it should grade the explanation with Haiku, or it shouldn't be there. Big confusion source for a learner.
- UI notes: the "Submit explanation" button is visible, enabled, clickable, but calls no endpoint. Console is silent. Looks like a wired-up-but-not-implemented UI.

## Step M2.3 — "Write CLAUDE.md for the M1 repo" — code_exercise
- Briefing clarity: 2/5 | time on step: ~8 min
- **Serious content mismatch**: step title and briefing say "Write a CLAUDE.md file for the M1 repo" (a prose/markdown deliverable), but the starter code is a Python file with 7 TODO functions (parser for CLAUDE.md). The hint ("Use regex patterns to find markdown headers like `## Project Structure`") confirms the real task is "implement a markdown parser in Python", not "author a CLAUDE.md".
- A real learner would be whiplashed here: you read the brief expecting to write documentation, then you see Python stubs and have to guess at the actual task.
- Attempt 1 (casual/wrong): wrote stubs that return empty. Score 12% (1/8 hidden tests). Feedback showed junit-xml tail with assertion errors — dense but debuggable.
- Attempt 2 (real): implemented `extract_sections`, `validate_sections`, `count_concrete_references`, `is_boilerplate`, etc. Score **100% (8/8)**.
- Verdict: ✅ passed, but ⚠ briefing mismatch is a blocker for anyone without strong Python regex + pytest intuition.
- UI notes: grader responsive (~3s), feedback banner `.tmpl-feedback pass` shows clearly. Hidden-test output tail helped debug. However Python editor is `<textarea rows="2">` — very cramped for a 50-line implementation; had to rely on autosize. No syntax highlighting, no indentation help. Beginner-hostile editor.

## Step M2.4 — "Redo the M1 fix — measure the delta" — terminal_exercise
- Briefing clarity: 3/5 | time on step: ~1 min (skimmed)
- Same bug: banner says terminal_exercise, body is `.concept-content` only. Briefing text literally says "You'll paste both prompts plus the final working diff" — so the author wrote this expecting structured paste slots. None rendered.
- Verdict: ❌ stuck (beginner-hostile) — UI missing.

## Step M3.1 — "Iterate the prompt, not the output" — concept
- Skimmed. Auto-complete. ✅

## Step M3.2 — "Claude is wrong on attempt 3 — what do you do?" — scenario_branch
- Briefing clarity: 5/5 | time on step: ~3 min
- Attempt 1 (wrong on Decision 1): clicked "Ask Claude to fix the coordinate mapping one more time" (the anti-pattern option). The step gave **no immediate wrong-answer feedback** — it silently advanced to Decision 2. A real learner wouldn't know Decision 1 was wrong until the final combined score.
- Attempt 1 (right on Decision 2): clicked "add specifics to the prompt". Score 50% (1/2 correct). Feedback revealed incorrect/correct per option.
- Retry: the "incorrect" option is now locked — cannot click the correct Decision 1 after the fact. **There is no way to retry a single scenario**; only the whole step or skip. Feedback says "2 more retries" but clicking anything on already-scored step did nothing.
- Verdict: ⚠ partial (50% locked). The "3 of your responses did not match" copy is again wrong (only 2 decisions).
- UI notes: the "pick → advance → silent grade" flow would have felt fine if there were per-decision coaching on wrong picks. Without it, the whole step is a graded final exam, not a teaching tool.

## Step M3.4 — "Classify 6 real 70%-right outputs" — categorization (drag-drop)
- Briefing clarity: 4/5 | time on step: ~4 min
- 6 real AI-generated output descriptions → 3 bins (Re-prompt / Verify-and-keep / Rewrite yourself). Clear pedagogic frame.
- Attempt 1 (wrong): dumped all 6 into bin 0 (re-prompt). Got 2/6 = 33%. "4 of your responses did not match" (correct this time — 4 of 6).
- Attempt 2 (real): careful mapping by content: 6/6 = 100%.
- Verdict: ✅ passed on attempt 2.
- UI notes: drag-drop works via HTML5 events; no keyboard alternative visible for accessibility. Reset clears bins properly.

## Step M3.3 — "Ship /health against a schema gotcha" — terminal_exercise
- Skimmed. Same rendering bug: terminal_exercise → concept-content. Briefing explicitly says "paste your two prompts and the fix diff" but no paste UI.
- Verdict: ❌ stuck (beginner-hostile)

## Step M4.0 — "MCP as team-multiplier + commit discipline" — concept
- Skimmed. Auto-complete. ✅

## Step M4.1 — "Review a teammate's ~80%-Claude PR" — code_review
- Skimmed. Same structure as M1.3. Bug category hints + clickable code. Expected to suffer the same off-by-one feedback issue as M1.3.
- Verdict: ⚠ skipped in depth, pattern already characterized

## Step M4.2 — "Ship a feature with the team-tickets MCP" — terminal_exercise
- Skimmed. Confirmed same concept-rendering bug. Briefing says "Your final paste should include the Claude session showing MCP tool calls, a clean diff with the new feature, and three atomic commit messages" — paste_slots data exists in API, UI doesn't render it.
- Verdict: ❌ stuck (beginner-hostile)

## Step M6.2 — "Build the autocorrect loop with budget + progress detection" — code_exercise
- Briefing clarity: 4/5 | time on step: ~10 min
- Starter had 2 TODOs (sha256_error, autocorrect_loop) + helpers already written.
- Attempt 1 (real solution): implemented full agentic loop with iteration tracking, sha256-based stuck detection, budget exhaustion fallback. Score 100% / 8 hidden tests.
- Verdict: ✅ passed cleanly on first real try.
- UI notes: this is the sweet spot of the course — clear task, useful scaffolding, fast grader, relevant domain. Same cramped editor pain as M2.3.

---

## Exercise-type tally

| Type                 | Steps sampled | Passed | Stuck | Partial |
|----------------------|---------------|--------|-------|---------|
| concept              | 5             | 5      | 0     | 0       |
| code_read            | 1             | 0      | 0     | 1       |
| code_exercise        | 2             | 2      | 0     | 0       |
| code_review          | 1 (deep) + 1 skim | 0 | 0    | 1 (+1 skim) |
| terminal_exercise    | 5 sampled     | 0      | 5     | 0       |
| scenario_branch      | 1             | 0      | 0     | 1       |
| categorization       | 1             | 1      | 0     | 0       |

## Key findings — data-vs-UI gap on terminal_exercise

The API returns `demo_data` for every terminal_exercise step with the NEW-UX payload: `bootstrap_command` (e.g. "git clone …/aie-course-repo && claude"), `dependencies` (list of `{kind: anthropic_api_key}`, `{kind: claude_cli}`, `{kind: python, version: 3.11+}`, etc.), and `paste_slots` (e.g. `{id: prompts, label: Your prompts, hint: …}`, `{id: final_diff, …}`). The data is populated. The frontend is rendering all of them as `.concept-content` only — no bootstrap banner, no dependencies panel, no structured paste slots, no Submit. Learners see a narrative page and a "Next →" button only.

This means:
- The NEW switching-UX provides **zero friction reduction over a plain textarea**, because there is no input field at all — it's strictly worse than the old plain-textarea flow that still had a Submit button.
- Course flow silently skips the 5 terminal_exercise steps (1 in M0, 1 in M1, 1 in M2, 1 in M3, 2 in M4+M6) — that's ~25% of graded steps.

## Other broken/rough UX

1. **Wrong-answer message stale**: "N of your responses did not match the expected answer" where N is a constant (often 3–5) regardless of how many items the learner selected. Seen on code_review, scenario_branch. Misleading and confusing.
2. **Code review off-by-one line matching**: clicking the handler header (line 18 `await pool.query(INSERT …)`) vs the `INSERT` string line 19 gets graded as wrong. Beginner-hostile because "the bug is here" visually points to the comment+body pair.
3. **Penalty math clamps to 0%**: finding 2/4 bugs with 6 false positives gave Score 0% (-60% FP penalty). Feels punitive rather than instructive.
4. **Scenario step locks after first submit**: can't retry a wrong decision; the full breakdown never reveals for retries if the step auto-locks.
5. **code_read "Submit explanation" is a no-op**: clicking it fires no network call, gives no feedback, no advance signal. Either remove it or wire it to a grader.
6. **No M5**: module list jumps M4 → M6. Broken structure or missing module.
7. **Python editor is `<textarea rows=2>` with no syntax highlighting**: OK for single-line tweaks, hostile for 50+ line implementations.
8. **Creator tools visible to learner** ("🔄 Regenerate", "✏️ Edit" buttons on every step). Confusing — a beginner might click Regenerate and wipe the step they were doing.
9. **Intro step (M0.1) auto-complete without checklist confirmation**: the big preflight checklist (install Claude Code, get API key, install Python etc.) is shown but no click is required to advance. Real beginners could skip it and fail later.

## Would I push through?

As a mid-career engineer, I'd push through M2/M3/M6 code_exercises because they felt well-designed and the grader is fast. I would **quit at the first terminal_exercise** (M0.2) because:
- The task asks me to run something on my machine.
- There's nowhere to paste what I did.
- The Next button works without verification.
- That signals the course is broken and will not actually grade my setup.

A true beginner would either (a) silently skip every terminal step thinking "it just wants me to read", or (b) try to submit, find no input, assume the course is broken, and close the tab.

## Verdict: ⚠ CONDITIONAL APPROVE

Rationale: the code_exercise and categorization paths are solid — grader is real, feedback is fast, scaffolding helps. The concept steps read well. BUT the terminal_exercise rendering gap is a category-wide failure (5 of ~23 steps, all the hands-on capstone work), plus several feedback-copy and code_review grading bugs. Fix terminal_exercise rendering (it's a pure frontend/template-mount miss — data is already present) + the wrong-answer stale copy + the code_read dead button, and this becomes a clean APPROVE.

## Top 3 issues to fix (prioritized)

1. **Terminal_exercise template not mounting.** Every terminal_exercise step renders as `.concept-content` with no Submit path, despite `demo_data` containing `bootstrap_command`, `dependencies`, and `paste_slots`. This kills ~25% of the course. (Frontend template switcher never dispatches to the terminal template; fix in the code that picks `tmpl-terminal.html` for `step_type === 'terminal_exercise'`.)
2. **Wrong-answer feedback copy is stale/constant.** Multiple step types (code_review, scenario_branch) show "N of your responses did not match" where N is hardcoded and bears no relation to how many items the learner selected. Confuses beginners badly on first wrong attempts. Fix the grader response builder to use actual miss count.
3. **Code_read Submit-explanation button is dead weight.** No network call, no feedback, no advance signal. Either wire it to Haiku explanation grading (as the infrastructure implies it should) or hide it.

## Explicit answer: did the new terminal-exercise UX reduce friction?

**No — it made friction worse.** Because the bootstrap-command banner, dependencies panel, and structured paste slots never rendered, the UX on terminal_exercise steps regressed to: a narrative page with a Next button. A plain textarea with a Submit button would have been strictly better — at least a learner could paste something and get a response. The new UX is a net negative **as shipped** on this course, but only because the data-to-template wiring is broken; the underlying `demo_data` payload is rich and would be a clear win once rendered. If the wiring were fixed, I'd expect the new UX to be a large friction win, because the paste_slots are named and purpose-specific (prompts / diff / commit messages) which beats an undifferentiated textarea.



