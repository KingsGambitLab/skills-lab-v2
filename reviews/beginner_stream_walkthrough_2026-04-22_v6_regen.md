# Beginner Stream Walkthrough — v6 (regen)

Course: Python Essentials: Data Structures and Algorithms for Everyday Scripts
URL: http://127.0.0.1:8001/#created-0d40ed9a4086
Started: 2026-04-22 (v6 regen fix-loop)

## Plan
- Course has 5 modules, 22 steps total. Concrete step types to probe:
  - M1: concept / code_read / code_exercise / code_review / categorization
  - M2: (4 steps) exercise-heavy
  - M3: (4 steps) binary search
  - M4: (4 steps) topo sort
  - M5: (5 steps) union-find capstone (includes M5.S1 known-hole step)
- Per RL rules: all 7 code_exercise steps get a deliberately-wrong trivial stub FIRST, then real attempt.

## Step 1.1 — "Hook: The Log-Analyzer That Took 8 Hours" — concept
- Briefing clarity: 5 — clear story, code snippets, complexity labels, CTA.
- Type: 📖 CONCEPT. No input required (read-only).
- Banner: "📖 CONCEPT · Intermediate". Humanized banner visible.
- Verdict: ✅ passed (informational step, no grading).
- UI notes: "Run Analysis (1M records, window=7)" button present, Next button active.

## Step 1.2 — "Read: The Canonical Sliding Sum" — code_read
- Briefing clarity: 5 — complete canonical implementation with key-insight callout, well-commented.
- Banner: "📑 READ REFERENCE" ✅ humanized.
- "read-only reference" badge visible ✅.
- textarea.readOnly = true ✅.
- Submit button present in DOM but hidden (offsetParent null, display:none) ✅.
- Sidebar counter advanced to 2/5 steps on view (auto-complete ✅).
- Verdict: ✅ passed (auto-completes on view).
- UI notes: regression of v1-v5 fix CONFIRMED WORKING.

## Step 1.3 — "Implement: max_avg_subarray(nums, k)" — code_exercise
- Briefing clarity: 4 — three sections (Task Overview, Sliding Window Pattern, Success Criteria).
- Banner: "🔧 EXERCISE" ✅ humanized.
- Attempt 1 (wrong): `def max_avg_subarray(nums, k): return 0.0` — **Score: 100%**. Feedback: "All 2 hidden tests passed in Docker (python)." ⚠ Heads-up warning fired: "only 2 hidden tests".
- Verdict: ❌ **GRADER FAILED** — trivial stub accepted. Layer A did NOT enforce ≥4 tests here (step has only 2).
- UI notes: weak-tests ⚠ banner DID fire ✅. Retry counter not shown (since 100% pass). Banner humanization ✅.
- **BUG**: Layer A test-count floor was supposed to force ≥4 tests, but this step has 2. Either the gate didn't fire or didn't apply to this step.

## Step 1.4 — "Spot the Bug: Off-by-One in the Window Slide" — code_review
- Briefing clarity: 4 — clear window-slide context, 45 lines of instrumented code.
- Banner: "🔎 CODE REVIEW" ✅ humanized.
- No answer-leak comments in starter code ✅ (checked for BUG/TODO/FIX/wrong/incorrect etc).
- Attempt 1 (wrong): flagged line 5 only — Score: 0% (0 correct, 1 wrong). Retry text: "2 more retries". `.cr-line.flagged.wrong-click` class applied ✅.
- Attempt 2: flagged line 25 (the actual off-by-one) — Score: 50% (1 correct, 0 wrong). "1 more retry before full breakdown". `.cr-line.flagged.correct-click` class applied ✅.
- Attempt 3: added line 23 (for-loop upper bound) — Score: 40%. Full breakdown revealed: "Found 1/2 bugs. False positives on [23] (-10%). Missed bugs on [9]".
- Verdict: ⚠ partial (1/2 bugs caught, but grader UI fully working).
- UI notes:
  - `correct-click` (green) applied to line 25 ✅
  - `wrong-click` (red) applied to line 23 after attempt 3 ✅
  - `missed-bug` (amber dashed left border, amber bg) on line 9 ✅
  - `← missed` pseudo-element content on missed-bug line ✅
  - Retry counter decrements: 2 → 1 → breakdown ✅

## Step 1.5 — "Pattern Radar: Is This Sliding Window?" — categorization
- Briefing clarity: 4 — 8 scenarios, 2 bins (Sliding Window / Another Pattern).
- Banner: "📁 CATEGORIZATION" ✅ humanized.
- Attempt 1 (wrong): all 8 items into Sliding Window bin → Score: 50% (4 correct · 4 wrong).
- Per-item borders after attempt: `tmpl-item-wrong` red (rgb 248,113,113), `tmpl-item-correct` green (rgb 45,212,191) ✅.
- Attempt 2: moved the 4 red items to "Another Pattern" bin → Score: 100%.
- Retry counter: "2 more retries before full breakdown reveals" shown on first attempt ✅.
- Verdict: ✅ passed.

