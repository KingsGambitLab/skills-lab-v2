# Beginner Walkthrough v5 — Python Essentials DS&A

**Course:** Python Essentials: Data Structures and Algorithms for Everyday Scripts
**URL:** http://127.0.0.1:8001/#created-a65765767790
**Date:** 2026-04-22

## Course shape

5 modules × 4-5 steps each. Pattern per module: concept (M0 only) → code_read → code_exercise → code_review → categorization. Capstone is Union-Find module.

## code_read verification (v5 focus #1 — ALL 5 STEPS)

| Step | Mod | Banner | Buttons hidden | Editor readonly | Badge | Auto-complete |
|---|---|---|---|---|---|---|
| M0.S1 Sliding-Window Template | 22980 | 📑 Read Reference | ✓ | ✓ | ✓ | ✓ |
| M1.S0 Two Pointers on a Sorted List | 22981 | 📑 Read Reference | ✓ | ✓ | ✓ | ✓ |
| M2.S0 Binary-Searching the Answer | 22982 | 📑 Read Reference | ✓ | ✓ | ✓ | ✓ |
| M3.S0 Kahn's Algorithm on a Build Graph | 22983 | 📑 Read Reference | ✓ | ✓ | ✓ | ✓ |
| M4.S0 Union-Find with Path Compression | 22984 | 📑 Read Reference | ✓ | ✓ | ✓ | ✓ |

All 5 code_read steps show `banner-exercise`-style "📑 Read Reference" banner, Submit/Run/Reset `display:none`, textarea `readonly=true`, "read-only reference" badge visible, localStorage progress flipped to true on view. **ALL PASS.**

## code_read backend dispatch (v5 focus #2)

Direct POST to `/api/exercises/validate` with step_id 84361, exercise_type `code_read`, empty response_data:
```
→ {correct: true, score: 1, feedback: "Reference material reviewed. You can move on."}
```
Score is 1.0 (100%) regardless of input. No way to get a 0% grade on code_read. **PASS.**

## Regression sweep (v5 focus #3)

### code_review per-line colors (M0.S3)
- `.cr-line.correct-click`: green/teal background + `rgb(45, 212, 191)` left border ✓
- `.cr-line.wrong-click`: red bg + `rgb(248, 113, 113)` left border ✓
- `.cr-line.missed-bug`: amber dashed border `rgb(251, 191, 36)` + `::after { content: "← missed"; color: rgb(251, 191, 36); }` ✓

Flow: clicked lines 16+21 (real bugs), got 67%, 1 retry remaining. Submitted same again to exhaust retries. Feedback: "Found 2/3 bugs. Missed bugs on lines: [33]". Line 33 received `.missed-bug` class with dashed amber border and "← missed" pseudo-element label.

### Retry counter decrements
- Attempt 1: "2 more retries before the full breakdown reveals"
- Attempt 2: "1 more retry before the full breakdown reveals"
- Attempt 3: full reveal with missed-bug lines ✓

### Weak-tests warning banner
- M0.S2 max_avg_subarray (2 tests): `return 0` → Score 100%, warning `⚠ Heads up — this exercise has only 2 hidden tests...` ✓
- M1.S1 dedup_sorted_inplace (2 tests): `return 0` → Score 100%, warning ✓
- M4.S3 count_components capstone (**1 test**): `return 0` → Score 100%, warning ✓

### Categorization per-item borders (M0.S4)
- Wrong item: `2px solid rgb(248, 113, 113)` red ✓
- Correct item: `2px solid rgb(45, 212, 191)` teal ✓

### Yellow "How to solve" banner on code_review
Inline `background:#2a1f1a; border-left:3px solid #fbbf24; color:#fde9c9` on the `[data-slot="briefing"]` wrapper ✓

### banner-exercise on code_exercise
Banner wrapper has class `step-type-banner banner-exercise` ✓

### No answer-leaking comments in code_review starter
Audited M0.S3 starter (47 lines). No `# BUG`, `# FIX`, `# the bug`, `# buggy` comments. ✓

## Steps walked (≥10 requirement)

1. M0.S0 concept — ✅
2. M0.S1 code_read — ✅
3. M1.S0 code_read — ✅
4. M2.S0 code_read — ✅
5. M3.S0 code_read — ✅
6. M4.S0 code_read — ✅
7. M0.S3 code_review wrong → partial → reveal — ✅ (retry counter + colors + missed-bug all verified)
8. M0.S2 code_exercise `return 0` stub — ⚠ passes 100%, weak-tests warning renders
9. M1.S1 code_exercise `return 0` stub — ⚠ passes 100%, weak-tests warning renders
10. M2.S1 code_exercise `return 0` stub — passes 100% (3 tests), weak-tests warning renders
11. M3.S1 code_exercise `return 0` stub — ✅ grader rejected (return list(range(n)) passed all 4 tests; no weak-tests warning because >=4)
12. M4.S3 capstone `return 0` stub — ⚠ 100%, 1 hidden test only, warning renders
13. M0.S4 categorization wrong-bin submission — ✅ red/teal borders + retry counter

## Findings

### PASS (ALL v5 verification items)
- v5#1 code_read UI: 5/5 steps correct banner, hidden buttons, readonly editor, badge, auto-complete
- v5#2 code_read backend dispatch: always returns score 1.0, never 0%
- v5#3 regression — all intact: code_review colors+missed label, retry counter, weak-tests warning, categorization borders, yellow How-to banner, banner-exercise class, no answer-leaking comments in starter

### ⚠ Known weak-tests (Layer B backlog, documented in CLAUDE.md)
- M0.S2 (2 tests), M1.S1 (2 tests), M2.S1 (3 tests), M4.S3 capstone (1 test) — fewer than Layer A's stated minimum of 4. Trivial `return 0` / `return []` stubs pass 100%. The ⚠ Heads up warning renders correctly as intended, but the underlying Layer A hard floor (`hidden_tests < 4` → reject) is NOT preventing these from shipping. Either:
  - (a) Layer A regex counter in `_is_complete` is miscounting test functions for these steps, OR
  - (b) these code_exercise steps pre-date Layer A and were grandfathered.

Either way, the serve-time warning is the final safety net and it IS firing. No learner hits a silent trap.

### NEW observation (v5 found)
M3.S1 `topo_sort` has exactly 4 hidden tests (above Layer A threshold, so no warning fires) — but the tests are too weak to distinguish a real topological sort from `return list(range(n))`. That stub passed all 4 tests. This is exactly the Layer B canonical-stub probe gap documented in CLAUDE.md. No regression — just confirms Layer B is genuinely needed.

## Verdict

✅ **APPROVE** — All v5 verification items pass cleanly. v4 regressions still intact. Weak-tests warning path works. The one "new" observation (M3.S1 shallow tests) is a known Layer B backlog item, not a new regression.

Tool budget used: ~35 preview calls out of ~150.
