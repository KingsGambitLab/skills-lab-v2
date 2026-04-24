# Beginner walkthrough — Python Basics: Core Data Structures and Control Flow

- Course: `created-9f16beee0c09` at http://127.0.0.1:8001/#created-9f16beee0c09
- Subject: beginner Python — variables, types, conditionals, loops, lists/dicts/sets, functions, comprehensions, try/except, file I/O
- Date: 2026-04-22 (pass v71_py)
- Mode: restricted-learner RL (no answer-key access)

## Step 1.1 — "Python Types in 90 Seconds" — concept (auto-complete on view)
- Briefing clarity: 4/5. Clean, a small interactive type-explorer widget, dark-theme safe.
- Verdict: ✅ passed (auto)

## Step 1.2 — "Truthiness & Operators Cheat Sheet" — concept (auto-complete on view)
- Briefing clarity: 4/5. Table of falsy values + short-circuit examples.
- Verdict: ✅ passed (auto)

## Step 1.3 — "Implement `classify_temperature(celsius)`" — code_exercise
- Briefing clarity: 4/5 (didn't specify exact ValueError message — minor gotcha).
- Attempt 1 (casual wrong, no None guard): Score 80%. Feedback: generic "didn't match what the exercise expects. Re-read the briefing" — reveal-gated. Helpful partially, tells me I'm close.
- Attempt 2 (had None guard but wrong error string "celsius cannot be None"): Score 80%. Now feedback IS specific: `E AssertionError: Regex pattern did not match. E Regex: 'Temperature cannot be None' E Input: 'celsius cannot be None'`. Extremely actionable.
- Attempt 3 (error string fixed): Score 100% — all 5 hidden tests passed.
- Verdict: ✅ passed
- UI notes: Submit navigated briefly to '/' mid-attempt once (page reset to hash root). Had to re-navigate; not fatal but a real glitch a beginner would notice.

## Step 1.4 — "Implement `is_valid_username(name)`" — code_exercise
- Briefing clarity: 5/5. Clear requirements + implementation-strategy hint inline.
- Attempt 1 (real): Score 100% — all 10 hidden tests passed first try.
- Verdict: ✅ passed

## Step 2.2 — "Implement `running_average(numbers)`" — code_exercise
- Briefing clarity: 5/5. Worked example in the docstring.
- Attempt 1 (real): Score 100% — 7 hidden tests passed first try.
- Verdict: ✅ passed

## Step 2.3 — "Implement `find_first_anomaly(readings, threshold)`" — code_exercise
- Briefing clarity: 5/5.
- Attempt 1 (real): Score 100% — 8 hidden tests passed first try.
- Verdict: ✅ passed

## Step 3.2 — "Implement `dedupe_preserve_order(items)`" — code_exercise
- Briefing clarity: 5/5. Data-type clarity + worked examples.
- Attempt 1 (real): Score 100% — 7 hidden tests passed first try.
- Verdict: ✅ passed

## Step 3.3 — "Implement `count_word_frequencies(text)`" — code_exercise
- Briefing clarity: 5/5.
- Attempt 1 (real): Score 100% — 7 hidden tests passed first try.
- Verdict: ✅ passed

## Step 4.2 — "Comprehensions" (4 functions) — code_exercise
- Briefing clarity: 5/5. Requested 4 rewrites with clear patterns.
- Attempt 1 (real): Score 100% — 13 hidden tests passed.
- Verdict: ✅ passed
- UI notes: feedback took ~15s to appear after backend Docker run; Submit button text changed to "Grading…" — good affordance but a beginner might think it's stuck.

## Step 5.1 — "Implement `parse_log_line(line)`" — code_exercise — ⚠ PARTIAL
- Briefing clarity: 3/5. Gives a format spec and an example but does NOT specify the exact error-message strings the hidden tests regex-match.
- Attempt 1 (regex-based approach, one generic error message): Score 33% — 2/6 tests passed. Feedback was reveal-gated: "Re-read the briefing". Not actionable — I was re-reading the briefing, which doesn't contain what the test needs.
- Attempt 2 (manual string-parse, still generic error message): Score 33%. Still reveal-gated. Now feedback hints "1 more retry before the full breakdown reveals" — a bit punishing when I'm clearly iterating on a real attempt.
- Attempt 3 (more specific errors): Score 33%. Reveal-gate finally opened: test file expects `ValueError, match="missing service separator"`. That's a VERY specific string the briefing never mentions.
- Verdict: ❌ stuck (beginner-hostile) — a real beginner could not guess "missing service separator" from the spec. The test is treating an implementation-detail error-string as a pedagogical requirement. Could pass now with the revealed hint, but I've hit the 3-attempt cap.
- UI notes: the reveal-gating is 3 attempts, which is long when the blocker is an unspecified test contract. Consider: (a) surface which TESTS passed/failed by NAME from attempt 1 without needing Docker output, or (b) have the Creator specify in briefing when error-message wording is graded.

## Step 5.3 — "Capstone: `analyze_log_file(path)` — Parse, Count, Flag Anomalies" — code_exercise — ⚠ MAJOR BUGS
- Briefing clarity: 4/5 (describes a real task well: dict return with `error_counts`, `anomalies`, `skipped`; median threshold for anomalies).
- **Issue 1: template/starter mismatch**. Briefing asks me to implement `analyze_log_file(path)`. But the starter scaffold is a generic `def solve(inputs: dict[str, Any]) -> dict[str, Any]` stub that does NOT mention `analyze_log_file` at all. This is the kind of "generic fallback scaffold" problem CLAUDE.md warns about. A beginner would read briefing→scaffold→briefing and genuinely not know whether to rename `solve`, wrap it, or add `analyze_log_file` separately.
- **Issue 2: hint is literally truncated mid-word** in the step data: `"Complete the task: Ship a single function that opens a server log file, parses each line (skipping malformed with a war"` — ends mid-word "warning". Hint was server-side truncated during generation or persist.
- **Issue 3: must_contain-only grading**. Validation is `{'must_contain': ['def ', 'return']}` — no hidden_tests. A 2-line trivial stub `def analyze_log_file(path): return {}` scored **100%** ("Your code uses the required constructs and runs successfully"). This is the exact "Python fallback" path CLAUDE.md says should be removed ("Better to say course creation failed"). The capstone of the whole course has the weakest grading surface and gives learners zero pedagogical signal.
- Verdict: ⚠ partial (solvable, but grader is vacuous and briefing/starter disagree)

---

## Summary (samples across all 5 modules)

### Tally
- **concept** (auto-complete): 4 seen (steps 1.1, 1.2, 2.0, 3.0, 4.0 — patterns). All clean.
- **code_exercise** (solid Docker + hidden_tests): 6 passed cleanly (1.3, 1.4, 2.2, 2.3, 3.2, 3.3, 4.2). First-attempt pass rate 6/7 (1.3 needed the error-string iteration). Grader feedback on wrong attempts is USEFUL once the reveal-gate opens (pytest output is shown verbatim).
- **code_exercise with error-string contract**: 1 stuck (5.1 parse_log_line — tests regex-match specific strings the briefing never names).
- **code_exercise with must_contain-only (fallback path)**: 1 trivially-passable (5.3 capstone).

### Exercise-type coverage
This course is overwhelmingly `concept` + `code_exercise`. No drag_drop / categorization / ordering / sjt / code_review / fill_in_blank / parsons seen in the 14 steps I sampled. For a "Python Basics" course that's probably fine (it's all code).

### Beginner-hostile friction
- Step 5.1: error-message strings are graded but never shown in the briefing. Beginner cannot guess `"missing service separator"`.
- Step 5.3: the capstone — the whole course's pedagogical climax — is gated by `must_contain: ['def ', 'return']`. Any 2-line stub passes. Content and grader contract disagree.
- Hint is truncated mid-word in step 5.3.

### UI glitches (real)
- Submit sometimes navigated page to '/' (hash reset to root) — happened at least twice. Forced re-navigation.
- "Grading…" state with no progress bar can feel stuck on longer Docker runs (10-15s).
- Reveal-gate wording on first failed attempt ("Re-read the briefing") was unhelpful for step 5.1 where the blocker isn't in the briefing.
- Stale step content: navigating by hash change (`location.hash = '#.../23038/0'`) sometimes didn't redraw — the sidebar click path worked, but reflow was inconsistent.
- Backend briefly became unresponsive (connection refused) mid-walkthrough — likely a hung Docker request; had to restart server.

### Wrong-answer teaching quality
- Best (1.3 attempt 2): pytest's own regex error was shown directly. A+ feedback.
- Worst (5.1 attempts 1-3): reveal-gate hides the specific failure until 3 tries burned; when the briefing contains no mention of the contract being tested, beginners can't productively iterate.

### Grader calibration
- Too harsh: 5.1 (reveal-gating specific error-string contract not disclosed upfront).
- Too lenient: 5.3 (must_contain ['def ', 'return'] — trivial stubs pass).
- Calibrated: 1.3, 1.4, 2.2, 2.3, 3.2, 3.3, 4.2 (hidden_tests with reasonable coverage; feedback actionable post-reveal).

### Would I quit as a beginner?
Through modules 1-4 the experience is consistently good — clear briefings, starter scaffolds match the function being requested, hidden tests are strict enough to teach but feedback tells me why I failed. A beginner would feel competent and encouraged.

Module 5 would frustrate me: 5.1 feels arbitrary (test-contract punching I can't see), and 5.3 (the capstone) feels empty because trivial code wins. If this were my first Python course I'd leave module 5 feeling less confident than I did finishing module 4 — not from difficulty, but from incoherence between what the briefing asks and what the grader actually checks.

### Verdict
⚠ **CONDITIONAL** — Ship modules 1-4 as-is; they're solid beginner content with calibrated graders. Fix module 5:
1. Regen step 5.1 with either (a) tests that don't regex-match on error strings, or (b) briefing that lists the exact error-message strings the tests check.
2. Regen step 5.3 with real `hidden_tests` instead of the must_contain-only fallback — this is the capstone, the single most important exercise in the course, and it currently accepts 2-line stubs. (Aligned with the backlog directive in CLAUDE.md v7.1: remove the Python fallback entirely and fail loud when a code_exercise can't be fully generated.)
3. Fix the truncated hint in 5.3 (literal mid-word cutoff "...with a war" — looks like a generation-time string-length limit hit).
4. Align step 5.3 starter with its briefing — scaffold should mention `analyze_log_file(path)` explicitly, not a generic `solve(inputs: dict)`.
