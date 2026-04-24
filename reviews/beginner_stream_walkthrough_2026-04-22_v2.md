# Beginner Stream Walkthrough — 2026-04-22 v2

Course: "Python Essentials: Data Structures and Algorithms for Everyday Scripts"
URL: http://127.0.0.1:8001/#created-a65765767790
Level: Intermediate (per API)
Start time: 2026-04-22

## Structure
- M0: Sliding Window: Running Sums in One Pass (5 steps)
  - S0 concept: Why the Nested Loop Is Killing Your Log Parser
  - S1 code_read: Read: The Sliding-Window Template
  - S2 code_exercise: Implement: max_avg_subarray(nums, k)
  - S3 code_review: Audit: The Off-By-One That Shipped to Prod
  - S4 categorization: Does Sliding Window Apply Here?
- M1: Two Pointers: In-Place Deduplication (4 steps)
  - S0 code_read, S1 code_exercise, S2 code_review, S3 categorization
- M2: Binary Search on a Monotonic Predicate (4 steps)
  - S0 code_read, S1 code_exercise, S2 code_review, S3 code_exercise
- M3: Topological Sort with Kahn's Algorithm (4 steps)
  - S0 code_read, S1 code_exercise, S2 code_review, S3 categorization
- M4: Union-Find for Connected Components — Capstone (4 steps)
  - S0 code_read, S1 code_exercise, S2 code_review, S3 code_exercise

## First-page banner observed
"Course QC reached iteration limit — After 3 iterations, 22 major issues remain. Review the course; you may want to regenerate manually. 3 iterations run" — shown on top of step 1. Warning sign, but not blocking.

---

## Step M0.S0 — "Why the Nested Loop Is Killing Your Log Parser" — concept
- Briefing clarity: 4/5  | time on step: ~2 min
- Non-gradable: concept only. No Submit. Interactive O(n·k) vs O(n) widget present (Run Comparison button + slider). Dark-theme compliant.
- Verdict: ✅ passed (auto)
- UI notes: QC warning banner overlays bottom; dismissible via × button. Progress decremented 1/5 → 2/5 on navigating to next step, so the concept auto-completes on navigation.

## Step M0.S1 — "Read: The Sliding-Window Template" — code_read
- Briefing clarity: 5/5  | time on step: <1 min
- Auto-completed on view: editor `readOnly=true`, Submit button has `display: none`, "read-only reference" phrase present in DOM.
- Progress: 1/5 → 2/5 with no clicks needed.
- Verdict: ✅ passed (auto-complete on view — bug #1 FIXED)
- UI notes: Dark-theme compliant. Editor rendered non-editable textarea. No 3-attempt lockout. ✓ Confirms bug #1 fix.

## Step M0.S2 — "Implement: max_avg_subarray(nums, k)" — code_exercise
- Briefing clarity: 5/5 (StreamConnect challenge framing, requirements list, pattern hint) | time on step: ~4 min
- Attempt 1 (deliberately WRONG): `return sum(nums) / len(nums)` (returns overall average, ignores k entirely)
  - Score: 100% — "All 2 hidden tests passed in Docker (python)."
  - Feedback verbatim: "Score: 100% — All 2 hidden tests passed in Docker (python)."
  - Did this help me? NO — the grader is too weak. Only 2 hidden tests, and my wrong answer apparently happens to match for both inputs. Step auto-advanced 2/5 → 3/5.
- No second attempt needed since the wrong answer passed — but this is a **NEW BUG**: hidden test coverage is too thin to catch an obviously-wrong implementation.
- Verdict: ⚠ partial (passes wiring but grader is non-pedagogical)
- UI notes: Submit fires POST. Feedback area updated. Progress decremented. Docker execution works. **BUT** grader signals 100% correct for a clearly-wrong stub that ignores `k`, the whole point of the exercise. Bug-class: weak test coverage from Creator (solution-starter-invariant gate from CLAUDE.md didn't catch: starter raises `NotImplementedError` so it fails correctly, but a trivial wrong answer also passes — means hidden_tests are under-specified).

## Step M0.S3 — "Audit: The Off-By-One That Shipped to Prod" — code_review
- Briefing clarity: 4/5 — Bug Categories list present, "How to solve:" yellow banner visible ("Read the code below line-by-line. Click any line you believe contains a bug. The title hints at bug categories but the actual planted bugs may differ — trust what you read, not what the title suggests.") **Bug #10 FIXED.**
- Starter code: clean — no answer-revealing comments like "# Off-by-one: missing last valid window". **Bug #7 FIXED.**
- Attempt 1 (deliberately WRONG): clicked line 1 only (function signature).
  - Score: 0% (0 correct · 3 wrong)
  - Feedback verbatim: "0% on this attempt. 2 more retries before the full breakdown reveals. 3 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Retry counter shown: "2 more retries". Submit button fired POST. **Bug #6 partial** — couldn't verify disable-during-post directly, but counter decremented later confirming.
- Attempt 2 (partial right): unflagged line 1, flagged lines 16 and 21 (off-by-one).
  - Score: 67% (0 correct · 3 wrong)
  - Feedback: "67% on this attempt. 1 more retry before the full breakdown reveals..."
  - Retry counter: "2 more retries" → "1 more retry". **Bug #3 FIXED** — counter decrements properly.
- Attempt 3: added line 23 (the slicing + sum redundancy).
  - Score: 57% (penalty for adding false-positive 23)
  - Feedback verbatim: "Found 2/3 bugs. False positives on lines: [23] (-10% penalty) Missed bugs on lines: [33]"
  - Full breakdown revealed after the 3rd attempt.
- Verdict: ⚠ partial — feedback reveals bugs/misses but per-item visual marking is **broken**:
  - Lines 16 and 21 (which the grader confirms as real bugs I correctly flagged) are shown with `wrong-click` class + red-ish `rgba(248,113,113,0.15)` background. This is WRONG — they should be green (correct-click).
  - Line 23 (the actual false positive) also has `wrong-click` red — correct styling for THIS line.
  - Line 33 (the missed bug) has NO visual marker at all.
  - **NEW BUG: per-item visual states don't distinguish correct-click from wrong-click; missed-bug highlighting absent.**
- UI notes: Submit fires POST on every attempt (network shows 3 POSTs to `/api/exercises/validate`). Retry counter updates. Feedback banner updates text. Yellow "How to solve" banner present. BUT the per-line color coding is wrong: everything you flagged ends up red regardless of correctness. Bug #4 is PARTIALLY FIXED (wrong-click red exists) but the green/correct and the missed-bug marks are missing.

## Step M0.S4 — "Does Sliding Window Apply Here?" — categorization
- Briefing clarity: 4/5 (context clear, 3 bins labelled, 8 items)  | time on step: ~5 min
- Attempt 1 (deliberately WRONG): all 8 items into "Different Pattern Needed"
  - Score: 38% (3 correct · 5 wrong) — happens because i2, i4, i7 really are Different.
  - Feedback: "38% on this attempt. 2 more retries before the full breakdown reveals..."
  - Per-item visual state WORKS: `tmpl-item-wrong` with red `border-left: rgb(248,113,113)`, `tmpl-item-correct` with green `border-left: rgb(45,212,191)`. **Bug #4 for categorization = FIXED.**
- Attempt 2 (real): i1,i3,i5,i8 → Perfect Sliding Window; i2,i4,i7 → Different Pattern Needed; i6 → Maybe.
  - Score: 100% (8 correct · 0 wrong)
  - Feedback: "8/8 items correctly categorized."
  - Step advanced 3/5 → 4/5. Progress decremented.
- Verdict: ✅ passed
- UI notes: Submit fires POST. Drag-drop works via native DragEvent dispatch. Feedback banner is distinct div with `pass` class. Prior attempt's feedback REPLACED on new submit (not stale). Retry counter went 2 → (cleared on success). Bug #5 (feedback clear / grading pending) couldn't be directly probed but the net result is clean — no stale text visible.

## Step M1.S0 — "Read: Two Pointers on a Sorted List" — code_read
- Briefing clarity: 5/5 | time: <1 min
- Auto-completed on view. Editor readOnly=true, Submit hidden (display:none), "read-only reference" badge present. Progress 0/4 → 1/4.
- Verdict: ✅ passed (auto)

## Step M1.S1 — "Implement: dedup_sorted_inplace(nums)" — code_exercise
- Briefing clarity: 5/5 (strategy spelled out, validation categories listed) | time: ~2 min
- Attempt 1 (deliberately WRONG): `return 0` (no dedup at all)
  - Score: 100% — "All 2 hidden tests passed in Docker (python)."
  - Did this help? NO — second code_exercise in a row where clearly-wrong code passes. **Same NEW BUG pattern: hidden test coverage is too thin.**
- Verdict: ⚠ partial (wiring fine, grader too weak)
- UI notes: Submit fires POST, feedback appears, step advances 1/4 → 2/4. Docker runs.

## Step M1.S2 — "Audit: The Write-Pointer Off-By-One" — code_review
- Briefing clarity: 4/5 (Bug Categories list + Yellow "How to solve" banner) | time: ~6 min
- Attempt 1 (WRONG): line 6 flagged
  - Score: 0%, "2 more retries before the full breakdown reveals"
- Attempt 2: flagged lines 10, 13, 15
  - Score: 13%, "1 more retry before the full breakdown reveals"
  - Retry counter: 2 → 1 (bug #3 FIXED).
- Attempt 3: flagged only line 15
  - Score: 33% — "Found 1/3 bugs. Missed bugs on lines: [17, 19]"
  - Grader claims bugs on lines 15, 17, 19 — my reading says bug is actually on line 15 alone; lines 17/19 are correct logic. This looks like a course-content accuracy issue (false bugs planted), though I can't be 100% sure without the answer key. **Possible content bug: over-flagged non-bug lines.**
- Verdict: ⚠ partial (graded, but course's "expected bugs" list appears wrong)
- UI notes: Submit fires POST, feedback replaces cleanly, retry counter decrements correctly, wrong-click red visible, correct-click green still MISSING on the flagged-but-correct cases (same per-item styling bug as M0.S2).

## Step M1.S3 — "Two Pointers or Something Else?" — categorization
- Briefing clarity: 4/5 | time: ~4 min
- Attempt 1 (WRONG): all 8 → "Different Strategy Needed" → Score 25% (2 correct · 6 wrong). "2 more retries before the full breakdown reveals"
- Attempt 2: full mapping (5 to Two Pointers, 1 Alternative, 2 Different) → Score 88% (7 correct · 1 wrong). i5 (3-sum triplets) flagged wrong.
- Attempt 3: moved i5 to Alternative Pattern → Score 100%.
- Verdict: ✅ passed
- UI notes: Same smooth behaviors as M0.S4. Per-item colors on final correct state all green. Retry decrement works.

## Step M2.S0 — "Read: Binary-Searching the Answer, Not the Array" — code_read
- Verdict: ✅ passed auto (readOnly editor, Submit hidden, read-only reference badge, progress 0/4 → 1/4).

## Step M2.S1 — "Implement: min_feasible(values, predicate)" — code_exercise
- Briefing clarity: 4/5 (docstring says "smallest VALUE" but returns an index — minor inconsistency) | time: ~3 min
- Attempt 1 (WRONG): `return -1` → Score 0%, feedback: "Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully." **6 hidden tests** (stronger than M0.S2 / M1.S1 which had only 2).
- Attempt 2 (RIGHT): canonical lo/hi binary search → Score 100%, "All 6 hidden tests passed in Docker (python)."
- Verdict: ✅ passed
- UI notes: Submit POSTs, feedback updates, retry message shown on fail, step advanced 1/4 → 2/4 on pass. Solid wrong-answer feedback ("didn't match", "re-read the briefing"), though generic.

## Step M2.S2 — "Audit: The Infinite Loop" — code_review
- Briefing clarity: 3/5 (5 bug categories but "infinite loop" title is misleading; Yellow "How to solve" banner present & trustworthy)
- Attempt 1 (WRONG): line 2 (docstring) → 0% (0/4 bugs). "2 more retries before the full breakdown reveals."
- Attempt 2: flagged lines 24, 27, 36, 40 → 0% again "1 more retry" (0/4 found)
- Attempt 3: flagged lines 16, 19, 20, 29 → Score 30%. "Found 2/4 bugs. False positives on lines: [16, 20] (-20% penalty) Missed bugs on lines: [7, 24]"
- Verdict: ❌ stuck (beginner-hostile). The planted bugs (lines 7, 24 among others) don't match my good-faith reading of the code. Even with attempt 2 including line 24 as a "semantics bug" — it was marked wrong-click while the grader's "missed bugs" output later said it WAS a bug. That's inconsistent — it means during attempt 2's 0% scoring, line 24 was indeed in my set, yet the grader showed 0/4 bugs found. Either the scoring treats "4 clicks = 4 wrong" literally even when one matches, or the answer key is wrong for attempt 2.
- UI notes: Submit fires POST. Retry counter decrements 2→1→breakdown. BUT bug flag persistence across attempts is confusing (the same line marked wrong in one attempt and found in another). **Possible NEW BUG: inconsistent per-attempt feedback** — line 24 was in my attempt 2 click-set and graded 0/4 but the final breakdown says line 24 WAS a bug to find.

## Step M2.S3 — "Is This a Binary-Search-the-Answer Problem?" — code_exercise (quiz-sounding title)
- Briefing clarity: 5/5 — **blue "Exercise: This is an Implement step" banner present** with bg `rgb(26,36,64)`, border-left `rgb(74,124,255)` (blue), text `rgb(205,216,255)`. **Bug #9 FIXED.**
- Attempt 1 (WRONG): `return 1` → Score 100% — "All 1 hidden tests passed in Docker (python)." **Another weak grader: only 1 hidden test that `return 1` happens to satisfy.** Same NEW BUG pattern.
- Verdict: ⚠ partial (pedagogy fail from weak test, but UI/banner fix works)
- UI notes: Blue banner rendered correctly. Submit POST works. Step 2/4 → 3/4.


