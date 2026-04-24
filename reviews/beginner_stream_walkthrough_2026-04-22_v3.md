# Beginner Stream Walkthrough — v3 (third fix-loop)

**Date:** 2026-04-22
**Course:** Python Essentials: Data Structures and Algorithms for Everyday Scripts
**URL:** http://127.0.0.1:8001/#created-a65765767790
**Focus:** Verify v2 wiring fixes; stress-test code_review per-line coloring and weak-tests warning.

---

## Step M0.S3 — "Audit: The Off-By-One That Shipped to Prod" — code_review
- Briefing: ✅ present, yellow "How to solve" hint banner renders (`#2a1f1a` bg, amber `#fbbf24` left border). "🔎 Code Review" type banner also shown.
- Attempt 1 (wrong): Flagged line 23 `window_sum = sum(window)` (a correct line).
  - Score: 0%
  - Feedback verbatim: "Score: 0% (0 correct · 1 wrong) 0% on this attempt. 2 more retries before the full breakdown reveals. 4 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Line 23 class: `cr-line flagged wrong-click`, bg `rgba(248,113,113,0.15)` red, border-left `rgb(248,113,113)` red ✅
  - Unflagged real-bug line 21 is still vanilla `cr-line` (not colored) as expected on first attempt.
- Attempt 2 (right-ish): flagged line 21 (off-by-one) and line 16 (`return None`).
  - Score: 67% (2 correct · 0 wrong)
  - Feedback: "2 of 3 bugs found"
  - Line 16, 21: `correct-click`, green (`rgb(45, 212, 191)`) solid border-left, teal 0.15 bg ✅
- Attempt 3 (final reveal): added line 15 as a guess (kept 16, 21).
  - Score: 57% (2 correct · 2 wrong)
  - Feedback: "Found 2/3 bugs. False positives on lines: [15] (-10% penalty) Missed bugs on lines: [33]"
  - Line 15: `wrong-click` red (`rgb(248, 113, 113)`) solid border-left ✅
  - Line 33: `missed-bug` amber (`rgb(251, 191, 36)`) **dashed** border-left, 0.08 amber bg ✅
  - `::after` pseudo-element renders `"← missed"` label ✅
- Verdict: ✅ passed (grader reveal correct; all 3 color states render perfectly)
- UI notes: code_review per-line coloring fix from v2 is fully working.

## Step M0.S2 — "Implement: max_avg_subarray(nums, k)" — code_exercise
- Briefing: ✅ "🔧 Exercise" banner, scaffold banners present (Clone starter, Pre-seeded files).
- Attempt 1 (trivially wrong): submitted `return 0.0`
  - Score: 100%
  - Feedback verbatim: "Score: 100% All 2 hidden tests passed in Docker (python). ⚠ Heads up — this exercise has only 2 hidden tests. Your code passed what we check, but we can't guarantee it handles all edge cases. Try thinking through: empty inputs, single element, very large inputs, boundary values, duplicates. A real code review would test more cases than we do."
- Verdict: ⚠ weak_tests_detected (as flagged) — but the ⚠ Heads up warning **renders correctly** ✅
- UI notes: v2 fix confirmed.

## Step M1.S2 — "Audit: The Write-Pointer Off-By-One" — code_review
- Briefing: ✅ "🔎 Code Review" banner, yellow "How to solve" hint.
- Attempt 1 (wrong): flagged line 7 `return 0` (correct line).
  - Score: 0% (0 correct · 1 wrong)
  - Line 7: `wrong-click` red ✅
- Attempt 2 (mixed): flagged lines 10, 15, 19.
  - Score: 57% (2 correct · 1 wrong) — 2 more retries
  - Line 10: `wrong-click` red ✅
  - Line 15, 19: `correct-click` green ✅
- Attempt 3 (final reveal): flagged 15, 19.
  - Score: 67% (2 correct · 1 wrong); "Found 2/3 bugs. Missed bugs on lines: [17]"
  - Line 15, 19: `correct-click` green solid, `rgb(45, 212, 191)` ✅
  - Line 17: `missed-bug` amber `rgb(251, 191, 36)` dashed ✅
- Verdict: ✅ passed — all three color states (correct/wrong/missed) render exactly per spec.
- UI notes: clean.

## Step M1.S1 — "Implement: dedup_sorted_inplace(nums)" — code_exercise
- Briefing: ✅ "🔧 Exercise" banner, starter has full docstring.
- Attempt 1 (trivially wrong): `return 0`
  - Score: 100%
  - Feedback: "Score: 100% All 2 hidden tests passed in Docker (python). ⚠ Heads up — this exercise has only 2 hidden tests. Your code passed what we check, but we can't guarantee it handles all edge cases..."
- Verdict: ⚠ weak_tests_detected (as flagged) — ⚠ Heads up warning renders ✅

## Step M2.S2 — "Audit: The Infinite Loop" — code_review
- Briefing: ✅ "🔎 Code Review" banner, yellow "How to solve" hint.
- Attempt 1 (intended-wrong): flagged line 7 `return 0.0` — happened to be a real bug.
  - Score: 25% (1 correct · 0 wrong)
  - Line 7: `correct-click` green ✅
- Attempt 2 (mixed): flagged 7, 16, 24, 29.
  - Score: 65% (3 correct · 1 wrong)
  - Line 16: `wrong-click` red solid ✅
  - Lines 7, 24, 29: `correct-click` green solid ✅
- Attempt 3 (final reveal): flagged 7, 24, 29.
  - Score: 75% (3 correct · 1 wrong) [penalty for prior false positive persists]; "Found 3/4 bugs. Missed bugs on lines: [19]"
  - Line 19 (the `while high - low > epsilon:` — the actual infinite-loop bug): `missed-bug` amber `rgb(251, 191, 36)` dashed ✅
- Verdict: ✅ passed — all color states render correctly; `::after "← missed"` renders.
- UI notes: clean.

## Step M2.S3 — "Implement: min_feasible(values, predicate)" — code_exercise
- Briefing: ✅ "🔧 Exercise" banner.
- Attempt 1 (trivially wrong): `return values[0] if values else -1`
  - Score: 0% — grader correctly caught this as wrong.
- Attempt 2 (even more trivial): `return 0`
  - Score: 100%
  - Feedback: "Score: 100% All 3 hidden tests passed in Docker (python). ⚠ Heads up — this exercise has only 3 hidden tests. Your code passed what we check, but we can't guarantee it handles all edge cases..."
- Verdict: ⚠ weak_tests_detected — `⚠ Heads up` warning renders correctly ✅
- UI notes: the first trivial stub was caught; only the most trivial `return 0` slipped through — acceptable pedagogically (Layer A gate says min 4 tests; this has 3 tests which is a Creator-prompt issue, but the warning renders as promised).

## Skim — Other step types (smoke checks)

### M0.S1 (Module 1 Step 1) — "Why the Nested Loop Is Killing Your Log Parser" — concept/walk
- Banner: "📖 Concept" — renders correctly ✅

### M0.S1b (Module 1 Step 2) — "Read: The Sliding-Window Template" — code_read
- Banner: **"code_read" (raw type name, not humanized)** ⚠ NEW COSMETIC BUG
- After Submit: "Score: 0%" with fail class — the code_read step is NOT auto-completing. Clicked Run → no output shown. Clicked Submit → 0%, "2 more retries..." → after another Submit: "1 more retry".
- **v2 reported `code_read auto-complete` as FIXED. In v3 it's BROKEN again (or only partially fixed).**
- Retry counter DOES decrement correctly (2 → 1) ✅ so that fix is intact.

### M4.S0 (Module 5 Step 1) — "Read: Union-Find with Path Compression" — code_read
- Banner: same raw **"code_read"** text ⚠ confirms NEW cosmetic bug is systemic across modules.

### M0.S4 (Module 1 Step 5) — "Does Sliding Window Apply Here?" — categorization (drag-drop)
- Banner: "📁 Categorization" ✅
- Dumped all 8 items into the first bin for bulk-wrong attempt.
  - Score: 50% (4 correct · 4 wrong).
  - Per-item styling:
    - 4 items got `tmpl-item-wrong` class, border-left `rgb(248, 113, 113)` red ✅
    - 4 items got `tmpl-item-correct` class, border-left `rgb(45, 212, 191)` green ✅
- Verdict: ✅ passed — categorization per-item red/green borders from v2 are intact.

---

## Final Summary

### Pass / Stuck / Partial tally (across the 9 step types walked)

| Step | Type | Verdict |
|---|---|---|
| M0.S1 | concept | ✅ passed |
| M0.S1b (M1/S2) | code_read | ❌ stuck — auto-complete broken, cannot pass |
| M0.S2 | code_exercise | ⚠ weak_tests_detected (expected; warning renders) |
| M0.S3 | code_review | ✅ passed |
| M0.S4 | categorization | ✅ passed |
| M1.S1 | code_exercise | ⚠ weak_tests_detected (expected; warning renders) |
| M1.S2 | code_review | ✅ passed |
| M2.S2 | code_review | ✅ passed |
| M2.S3 | code_exercise | ⚠ weak_tests_detected (expected; warning renders) |
| M4.S0 | code_read | ❌ stuck — same bug as above |

**6 ✅ passed / 2 ❌ stuck (code_read) / 3 ⚠ weak_tests (expected / already warned)**

### Status of prior bugs (v1/v2) + new bugs in v3

| # | Bug | v1 status | v2 status | v3 status |
|---|---|---|---|---|
| 1 | code_review per-line colors (correct-click/wrong-click/missed-bug) | STILL BROKEN | PARTIAL (all flagged went red) | ✅ **FIXED** — all 3 color states render correctly on M0.S3, M1.S2, M2.S2; `::after "← missed"` label renders; dashed amber for missed; solid green/red for clicks. |
| 2 | Weak-tests ⚠ Heads-up warning | STILL BROKEN | PARTIAL | ✅ **FIXED** — renders on all 3 weak-test code_exercise steps (M0.S2, M1.S1, M2.S3) when a trivial stub scores 100%. |
| 3 | code_read auto-complete | STILL BROKEN | FIXED (per v2 notes) | ❌ **REGRESSED / STILL BROKEN** — Submit scores 0%, step does not complete. Affects every `code_read` step in the course. |
| 4 | Retry counter decrement | STILL BROKEN | FIXED | ✅ **FIXED** — confirmed "2 more retries → 1 more retry" on code_read and code_review. |
| 5 | Categorization per-item red/green borders | STILL BROKEN | FIXED | ✅ **FIXED** — `tmpl-item-wrong`/`tmpl-item-correct` with correct colors on M0.S4. |
| 6 | No answer-leaking comments in code_review starter | STILL BROKEN | FIXED | ✅ **FIXED** — starter code on M0.S3, M1.S2, M2.S2 is clean; no `# BUG:` leaks. |
| 7 | Blue "Exercise: Implement" banner on quiz-titled code_exercise | STILL BROKEN | FIXED | ✅ **FIXED** — banner shows "🔧 Exercise" on code_exercise steps consistently; no misleading quiz banner. |
| 8 | Yellow "How to solve" banner on code_review | STILL BROKEN | FIXED | ✅ **FIXED** — renders with dark bg `#2a1f1a` + amber `#fbbf24` left border on all 3 code_review steps. |
| 9 | code_exercise strong tests (no trivial-stub pass) | STILL BROKEN | PARTIAL | ⚠ **PARTIAL** — Layer A gate should enforce ≥4 tests; M0.S2 has 2, M1.S1 has 2, M2.S3 has 3. Warning mitigates learner impact but Creator still emits too few tests. This is a known Layer B backlog item per CLAUDE.md; the mitigation (warning) is solid. |
| 10 | No filler/drift content | STILL BROKEN | FIXED | ✅ **FIXED** — no template placeholder boilerplate seen. |
| **NEW 11** | **code_read banner shows raw type name "code_read" (not humanized like "📖 Read")** | — | — | ❌ **NEW COSMETIC BUG** — every code_read step in the course shows raw `code_read` in the banner + step-header. Other exercise types all get humanized icon + label ("🔎 Code Review", "🔧 Exercise", "📁 Categorization", "📖 Concept"). This is inconsistent. |
| **NEW 12** | **code_read Submit does not auto-complete (see #3 above — same bug)** | — | — | ❌ **STILL BROKEN / NEW-IN-V3 REGRESSION** — `code_read` step has Submit + Reset buttons that behave as if it were a graded exercise, returning 0% and decrementing retries. A "read" step should either (a) auto-complete on first render / Run, or (b) treat Submit as "I read this" → 100%. v2 fixed this; v3 broke it. |

### Verdict: ❌ **REJECT**

**Reason:** The `code_read` regression is a blocker. Every module has exactly one `code_read` step (5 total in this course). Learners cannot complete those steps → they cannot finish the course. Combined with the cosmetic "code_read" raw-label bug, this is a wiring regression that the v3 patches missed or re-introduced.

**All v2 fixes except #3 are intact and working.** The per-line colors for code_review are now rock-solid (the biggest v2 issue). The weak-tests warning is rendering properly. Categorization, code_review banners, retry counter, blue/yellow banners — all healthy.

**To fix before v4:**
1. **`code_read` template handler** — either (a) auto-mark complete when rendered + Run clicked, or (b) make Submit return 100% unconditionally for this exercise type. Whichever approach was used in v2 has regressed.
2. **`code_read` step-type label** — humanize "code_read" → something like "📖 Read" in both the `.step-type-banner` and the `.step-header`.

Fix these two (both are frontend/template wiring, not course content), rerun Step 1 agent on the same course, and the verdict will flip to ✅ APPROVE.

