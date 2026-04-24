# Beginner Browser Walkthrough — v4 (2026-04-22)

**Course:** Python Essentials: Data Structures and Algorithms for Everyday Scripts
**URL:** http://127.0.0.1:8001/#created-a65765767790
**Agent:** beginner Python tester, 4th fix-loop pass
**Scope:** verify v4 patches — code_read auto-complete (M1.S0 & M4.S0), code_read banner label, v3 regression smoke

---

## Step M0.S1 — "Read: The Sliding-Window Template" — code_read
- Briefing: 1 (pure reference read; no ask)
- Attempts: none — step auto-completes on view. Cleared `created-a65765767790-22980-1` from localStorage → reloaded → step re-marked complete.
- Banner: `📑 Read Reference` with `step-type-banner banner-concept` class (teal bg) ✅
- Editor: `readonly="true"` on `<textarea class="tmpl-editor">` ✅
- Readonly badge: `<span class="sll-readonly-badge">read-only reference</span>` ✅
- Buttons: Submit / ▶ Run / Reset all `display: none` ✅
- Verdict: ✅ PASS

## Step M1.S0 — "Read: Two Pointers on a Sorted List" — code_read
- Briefing: 1 (reference read)
- Attempts: same as above — cleared from localStorage, reloaded, auto-complete fires on landing. `learnSkillsProgress["created-a65765767790-22981-0"] === true` post-reload.
- Banner / editor / readonly badge / hidden buttons — all as M0.S1. ✅
- Screenshot captured: confirms clean layout.
- **Backend belt-and-suspenders test (direct POST to `/api/exercises/validate` with step_id=84365)**: returned `{correct: false, score: 0, feedback: "0% on this attempt. 2 more retries before the full breakdown reveals..."}`. ❌ **BUG — spec said this should return `{correct: true, score: 1.0}` for code_read. Backend does NOT have the belt-and-suspenders fix.**
- Verdict: ⚠ PARTIAL — UI side fully fixed; backend fallback NOT in place.

## Step M2.S0 — "Read: Binary-Searching the Answer, Not the Array" — code_read
- Same UI shape as above: banner `📑 Read Reference` / `banner-concept`, editor readonly, buttons hidden, badge "read-only reference", auto-completes. ✅
- Verdict: ✅ PASS

## Step M3.S0 — "Read: Kahn's Algorithm on a Build Graph" — code_read
- Same UI shape: all passes. ✅
- Verdict: ✅ PASS

## Step M4.S0 — "Read: Union-Find with Path Compression" — code_read
- Same UI shape as others: banner `📑 Read Reference`, readonly editor, hidden buttons, readonly badge, auto-completes.
- **Backend belt-and-suspenders test (step_id=84377)**: also returned `correct: false, score: 0`. ❌ Same bug as M1.S0.
- Verdict: ⚠ PARTIAL — UI fully fixed; backend fallback still missing.

## Step M1.S2 — "Audit: The Write-Pointer Off-By-One" — code_review
- Briefing: 3
- Attempts (wrong-then-right strategy to probe):
  - Attempt 1: clicked lines 3 + 12 → 0% (0 correct · 2 wrong). Feedback: "2 more retries before the full breakdown reveals. 5 of your responses did not match…". Both flagged lines got `cr-line flagged wrong-click` class with red `3px solid rgb(248, 113, 113)` border-left ✅.
  - Attempt 2: unflagged 3+12, flagged line 6 → 0% (0 correct · 1 wrong). Retry counter decremented to "1 more retry". ✅
  - Attempt 3: flagged line 15 → 33% (1 correct · 2 wrong). "Missed bugs on lines: [17, 19]". Full breakdown revealed as expected.
- Color-coded feedback verified:
  - correct-click: `3px solid rgb(45, 212, 191)` (teal) ✅
  - wrong-click: `3px solid rgb(248, 113, 113)` (red) ✅
  - missed-bug: `3px dashed rgb(251, 191, 36)` (amber) with `::after { content: "← missed" }` ✅
- No answer-leak comments in starter code (regex scan for BUG/FIXME/TODO/HINT/ANSWER → clean) ✅
- "How to solve" banner: dark brown-yellow background `rgb(42, 31, 26)` on the briefing wrapper ✅
- Retry counter decrements correctly: 2 → 1 → reveal ✅
- Verdict: ✅ PASS

## Step M2.S2 — "Audit: The Infinite Loop" — code_review
- Banner `🔎 Code Review` / `banner-exercise` ✅
- Yellow "How to solve" banner present ✅
- No answer-leak in starter ✅
- 41-line code block, all `cr-line` — clean ✅
- Verdict: ✅ PASS (smoke only)

## Step M3.S2 — "Audit: The In-Degree That Forgot to Decrement" — code_review
- Banner `🔎 Code Review` ✅
- Yellow "How to solve" banner bg `rgb(42, 31, 26)` ✅
- No answer-leak in 37-line starter ✅
- Verdict: ✅ PASS (smoke only)

## Step M1.S1 — "Implement: dedup_sorted_inplace(nums)" — code_exercise
- Briefing: 3 (clear scenario + examples in docstring)
- Attempts:
  - Attempt 1 (trivial stub `return 0`): **100% PASS**. Feedback: "All 2 hidden tests passed in Docker (python). ⚠ Heads up — this exercise has only 2 hidden tests. Your code passed what we check, but we can't guarantee it handles all edge cases..." ✅ Weak-tests warning FIRED correctly.
- Banner: `🔧 Exercise` / `banner-exercise` — NOTE: banner color is **amber** `rgb(251, 191, 36)`, not "blue" as spec describes. This is consistent across all code_exercise steps.
- Verdict: ⚠ PARTIAL — warning UI works; trivial `return 0` passing is Layer-B-backlog territory (not a v4 regression).

## Step M1.S3 — "Two Pointers or Something Else?" — categorization
- Briefing: 3 (clear ask)
- Attempt 1 (wrong — dumped all 8 items into "Two Pointers Optimal"):
  - Score: 50% (4 correct / 4 wrong).
  - Per-item borders: `tmpl-item-correct` → `2px solid rgb(45, 212, 191)` (teal) ✅, `tmpl-item-wrong` → `2px solid rgb(248, 113, 113)` (red) ✅
  - Feedback: "2 more retries before the full breakdown reveals. 4 of your responses did not match..."
- Verdict: ✅ PASS (borders correct; retry counter present)

## Step M4.S3 — "Capstone: count_components(n, edges) on a Real Graph" — code_exercise
- Banner `🔧 Exercise` / `banner-exercise` ✅
- Editor writable (readOnly=false) ✅
- Submit / ▶ Run / Reset all visible ✅ — good contrast vs code_read which hides them
- Verdict: ✅ PASS (smoke only)

---

## Tally

| Outcome | Count |
|---|---|
| ✅ PASS | 7 (M0.S1, M2.S0, M3.S0, M1.S2, M2.S2, M3.S2, M1.S3, M4.S3) |
| ⚠ PARTIAL | 3 (M1.S0, M4.S0, M1.S1) |
| ❌ STUCK | 0 |

## Status of prior bugs (per spec)

| Bug | v4 status |
|---|---|
| **code_read auto-complete** (v3 REGRESSED: 0%, counter decremented) | ✅ **FIXED** on UI side — Submit/Run/Reset all `display: none`, editor readonly, step auto-marks complete on view. Verified fresh by clearing localStorage and reloading. |
| **code_read banner label** (v3: raw "code_read" text, banner-default fallback) | ✅ **FIXED** — now renders "📑 Read Reference" with `banner-concept` class on all 5 code_read steps. |
| **Backend belt-and-suspenders for code_read submissions** | ❌ **STILL BROKEN** — POST `/api/exercises/validate` with step_id of a code_read step still returns `{correct: false, score: 0}` (verified on M1.S0 step 84365 AND M4.S0 step 84377). Spec required `{correct: true, score: 1.0}`. |
| **Depth picker removed** | ⚠ NOT VERIFIED (skipped per spec — peripheral, didn't pass through Creator flow) |
| **code_review per-line colors** | ✅ FIXED (green/red/amber-dashed all correctly applied; ← missed pseudo-element present) |
| **categorization per-item borders** | ✅ FIXED (correct=teal, wrong=red, 2px solid) |
| **weak-tests ⚠ Heads-up warning on 100%** | ✅ FIXED — triggers on passing score with <4 tests ("only 2 hidden tests", "we can't guarantee it handles all edge cases") |
| **retry counter decrements** | ✅ FIXED (2 → 1 → reveal) |
| **no answer-leak comments in code_review starter** | ✅ FIXED (3 code_review steps scanned — no BUG/FIXME/TODO/HINT/ANSWER tokens) |
| **yellow "How to solve" banner on code_review** | ✅ FIXED (bg `rgb(42, 31, 26)` dark brown-yellow on briefing wrapper) |
| **blue "🔧 Exercise" banner on code_exercise** | ⚠ PRESENT but NOT BLUE — rendered with `banner-exercise` class using amber `rgb(251, 191, 36)`. Spec said "blue" — likely spec-wording slip since the banner is consistently amber across the whole platform. |

## New bugs introduced by v4

1. ❌ **Backend fallback for code_read submissions missing.** Spec claimed "even if you somehow POST a submission for code_read, it now returns `{correct: true, score: 1.0}`." Actual behavior: POST returns `correct: false, score: 0` with standard code-exercise feedback ("Your submission didn't match what the exercise expects. Re-read the briefing..."). Endpoint tested on two distinct code_read step IDs (84365, 84377) — both return 0%. The UI hides the submit button so real learners can't trigger this via the app, but the backend fallback isn't in place. **Low user-impact** (UI prevents submission) but **spec-stated fix unverified**.

## Verdict

⚠ **CONDITIONAL**

UI-side fixes for code_read are clean across all 5 modules. Banner label, readonly editor, hidden buttons, readonly badge, auto-complete — all working. Code_review color-coding, retry counter, categorization borders, weak-tests warning, no-answer-leak — all verified.

The single outstanding issue is the **backend belt-and-suspenders for code_read submissions**, which the spec explicitly called out as "now returns `{correct: true, score: 1.0}` (not 0%)". It still returns 0%. Since the UI prevents learners from submitting (buttons hidden), user impact is zero, but the server-side safety net is not in place. If a future frontend bug re-exposes the Submit button (as happened in v3), learners will again see 0% scores.

Minor naming discrepancy: the "blue 🔧 Exercise" banner is actually amber (`banner-exercise` → `rgb(251, 191, 36)`); functionally fine.

Recommendation: ship the UI fixes as-is (high user value), log the backend-fallback gap as a follow-up. If strict compliance is required, complete the backend handler for code_read step validation.
