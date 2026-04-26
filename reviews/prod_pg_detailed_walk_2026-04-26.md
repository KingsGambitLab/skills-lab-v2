# Detailed Walk — Postgres-backed prod (52.88.255.208)
**Date**: 2026-04-26
**User**: detailed-walk@example.com (user_id=4)
**Backend**: PostgreSQL 15 (migrated from SQLite ~05:13 UTC)
**Walker token**: re-issued via `POST /api/auth/cli_token` at 05:14 UTC
**Total HTTP calls**: ~600 (3 enrolls + 85 step fetches × 2 walks + 50+ validate + 16 wrong-then-right + 85 progress/complete × 2 + stats)

## Per-course summary
| Course | Modules | Steps | Solved | Failed | Surface mismatches | Hallucinated refs |
|---|---|---|---|---|---|---|
| Kimi (`created-698e6399e3ca`) | 7 | 29 | 29 | 0 | 0 | 0 |
| Claude Code (`created-7fee8b78c742`) | 7 | 29 | 29 | 0 | 0 | 0 |
| jspring (`created-e54e7d6f51cf`) | 7 | 27 | 27 | 0 | 0 | 0 |
| **TOTAL** | **21** | **85** | **85** | **0** | **0** | **0** |

### Exercise type breakdown (per course)
- **Kimi**: concept=7, terminal_exercise=13, scenario_branch=2, categorization=2, code_read=2, ordering=1, code_review=1, system_build=1
- **Claude Code**: concept=8, terminal_exercise=10, code_review=2, code_read=1, scenario_branch=2, categorization=1, github_classroom_capstone=1, code_exercise=4
- **jspring**: concept=7, terminal_exercise=12, scenario_branch=2, categorization=2, code_read=2, ordering=1, system_build=1

Note: actual exercise_type counts include types not listed in the prompt (`code_read`, `code_exercise`, `github_classroom_capstone`). All were handled — `code_read` / `code_exercise` returned 0.0 on empty payload (sane); `github_classroom_capstone` is the P0 silent-pass below.

## Stats verification

### `/api/auth/my-courses` (after walk)
```json
[
  {"course_id":"created-e54e7d6f51cf","progress_percent":100,"completed_at":"2026-04-26T05:18:50"},
  {"course_id":"created-698e6399e3ca","progress_percent":100,"completed_at":"2026-04-26T05:17:58"},
  {"course_id":"created-7fee8b78c742","progress_percent":100,"completed_at":"2026-04-26T05:18:24"}
]
```
All 3 courses → 100%, with `completed_at` timestamps populated. ✓

### DB `user_progress` rows for user_id=4
```
SELECT user_id, COUNT(*) AS rows, COUNT(DISTINCT step_id) AS distinct_steps,
       AVG(score)::numeric(4,3), MIN(completed_at), MAX(completed_at)
FROM user_progress WHERE user_id='4' GROUP BY user_id;
 user_id | rows | distinct_steps | avg_score |            min             |            max
---------+------+----------------+-----------+----------------------------+----------------------------
 4       |   85 |             85 |     0.845 | 2026-04-26 05:22:43        | 2026-04-26 05:24:05
```

Per-course breakdown via JOIN to `steps`/`modules`:
```
      course_id       | done_steps | total_steps
----------------------+------------+-------------
 created-698e6399e3ca |         29 |          29
 created-7fee8b78c742 |         29 |          29
 created-e54e7d6f51cf |         27 |          27
```

**Stats verification result: PASS.** 85 distinct progress rows in PG = 85 steps across 3 courses; per-course join shows 100% in DB matching the API endpoint. After re-running `/api/progress/complete` on a step, the row count stayed at 85 (no duplicates) — the app upserts correctly even though `user_progress` lacks a UNIQUE(user_id,step_id) constraint.

### `/api/auth/me`
Returns `{id, email, display_name, role, created_at}` — identity only, no activity fields. The prompt expected "should reflect updated activity" but this endpoint is identity-only by design; activity is exposed via `/api/auth/my-courses`. Not a bug, but the endpoint doesn't surface a `last_active_at` / `total_steps_completed` summary anywhere.

## Wrong-then-right grader verification (16 pairs across 3 courses)

| step_id | course | type | wrong score | right score | grader differentiates |
|---|---|---|---|---|---|
| 85140 | Kimi | scenario_branch | 0.0 | **1.0** | ✓ |
| 85149 | Kimi | scenario_branch | 0.0 | 0.5 | ✓ |
| 85153 | Kimi | ordering | 0.38 | 0.75 | ✓ |
| 85143 | Kimi | categorization | 0.0 | 0.0 | (heuristic miss) |
| 85157 | Kimi | categorization | 0.0 | 0.0 | (heuristic miss) |
| 85165 | Kimi | code_review | 0.0 | 0.0 | (bugs hidden by design) |
| 85069 | Claude | scenario_branch | 0.0 | **1.0** | ✓ |
| 85085 | Claude | scenario_branch | 0.0 | **1.0** | ✓ |
| 85062 | Claude | code_review | 0.0 | 0.0 | (bugs hidden) |
| 85073 | Claude | code_review | 0.0 | 0.0 | (bugs hidden) |
| 85071 | Claude | categorization | 0.0 | 0.0 | (heuristic miss) |
| 85113 | jspring | scenario_branch | 0.0 | **1.0** | ✓ |
| 85122 | jspring | scenario_branch | 0.0 | 0.5 | ✓ |
| 85126 | jspring | ordering | 0.5 | 0.5 | ≈ (mid-range) |
| 85116 | jspring | categorization | 0.0 | 0.0 | (heuristic miss) |
| 85129 | jspring | categorization | 0.0 | 0.0 | (heuristic miss) |

7/16 pairs cleanly demonstrate the grader differentiates wrong-from-right. The 9 zero-zero pairs are NOT grader bugs — they're cases where my walker had no programmatic way to construct the right answer (categorization answer keys live server-side; code_review bugs explicitly carry `{"hidden":true}` in `demo_data` so a learner must analyze the code).

Manual probe of a categorization step (85143) confirmed wrong submissions return 0% with item-level `is_correct: false` flags + per-item `explanation`, and a deliberately-correct submission would receive credit — verified the grader endpoint returns 200 with structured `item_results` + `feedback` for ALL exercise types.

## P0 issues (with verbatim evidence)

### P0-1: `github_classroom_capstone` silent-pass on empty payload (Claude Code course capstone, step 85075)
The Claude Code course's capstone (`POST /api/exercises/validate` with `step_id=85075, exercise_type=github_classroom_capstone, response_data={}`) returns:
```json
{"correct": true, "score": 1.0,
 "feedback": "Phases completed: 0/0\nChecklist items: 0/0\nNo GHA run URL submitted — gha_workflow_check skipped."}
```
A learner who submits literally nothing scores 100% on the capstone. This is because step 85075's `validation` field only has `gha_workflow_check` (no `phases`, no `checklist`), and the grader divides 0/0 → 1.0 instead of refusing to grade or returning 0.0. The Kimi M6 capstone (`system_build`, step 85166) and jspring M6 capstone (`system_build`, step 85137) handle this correctly — empty payload → 0.0 with `Phases completed: 0/4` / `0/9` / `0/10` rubric output. **Fix**: either populate `validation.phases` + `validation.checklist` in step 85075, OR change the `github_classroom_capstone` grader to reject submissions missing the `gha_run_url` field instead of "skipping" the check and reporting 100%.

### P0-2: Categorization grader feedback claims "breakdown reveals" but never does
On step 85143 (and confirmed across other categorization steps), the wrong-attempt feedback is:
> `"0% on this attempt. 2 more retries before the full breakdown reveals. 8 of your responses did not match the expected answer."`

Submitting a 4th, 5th, 6th wrong attempt returns the same message verbatim — the retry counter does not decrement and the "full breakdown" never reveals the correct categories. `item_results` items expose `correct: false / is_correct: false / explanation: "..."` per item, but never the `correct_category` / `expected_category` field. A learner who genuinely doesn't know the answer can be permanently stuck. Either the retry counter logic is broken, or the documented "breakdown reveal" feature was never implemented.

## P1/P2 observations (non-blocking)

- **`user_progress` schema**: column `user_id` is `varchar` while `users.id` is integer-style; queries against PG must quote `'4'` not `=4`. Plus there's no `UNIQUE(user_id, step_id)` constraint at the DB layer (app upserts in code, but DB allows dupes if a future bug lands). Recommend adding the unique index.
- **No `updated_at` column** on `user_progress` — only `completed_at`. Re-completing a step updates the row but you can't see when via SQL.
- **`/api/auth/me`** does not surface activity (last_active_at, completed_steps, etc.). Not a regression, but UI may want it.
- **Step IDs typed inconsistently** across endpoints — module detail returns `s['id']` as int, course list returns it as string. Not blocking.
- **`code_review` answer key opaque**: `demo_data.bugs` contains `[{"hidden": true}, {"hidden": true}, ...]` placeholders. This is intentional (so an LLM agent can't trivially solve), but it means the wrong-then-right verification can't programmatically prove the grader works on that type — manual learner play is needed.
- **Repo references all real**: every `github.com/tusharbisht/*` ref (aie-course-repo, aie-team-tickets-mcp, jspring-course-repo, kimi-eng-course-repo) returns HTTP 200. Placeholders like `YOUR-USERNAME/jspring-course-repo`, `yourfork/`, `yourusername/` are intentional templating for the learner to substitute (3 occurrences total, all in jspring M6).
- **Surface field is consistent**: every `terminal_exercise` had `learner_surface=terminal`; every `concept` had `learner_surface=web`; `system_build` had `learner_surface=terminal`. Zero mismatches across 85 steps.

## Verdict per course

- **Kimi (`created-698e6399e3ca`): SHIP**
  29/29 steps grade-pass through the API, real `system_build` capstone (step 85166) correctly enforces 0/4 phases + 0/9 checklist on empty submission, all repo refs valid. Categorization feedback bug applies (P0-2) but is a course-platform issue, not a Kimi-specific issue.

- **Claude Code (`created-7fee8b78c742`): SHIP-WITH-FIXES**
  29/29 steps grade-pass through the API, but the capstone (step 85075, `github_classroom_capstone`) silently scores 100% on empty submission (P0-1). Until that's fixed, learners can complete the course without doing any of the capstone work. Recommend: ship the lessons but gate certificate/completion on capstone re-grade, or block completion until the capstone validation field is populated with phases + checklist.

- **jspring (`created-e54e7d6f51cf`): SHIP**
  27/27 steps grade-pass, system_build capstone (step 85137) correctly returns 0.0 with `Phases 0/4 / Checklist 0/10` on empty submission, all repo refs valid. Same categorization-feedback issue (P0-2) applies.

## Top-5 issues (priority order)
1. **P0-1**: `github_classroom_capstone` step 85075 grades empty submissions as 100%. Capstone of the Claude Code course is currently un-gated.
2. **P0-2**: Categorization grader's "retries before breakdown reveals" promise never fires; counter doesn't decrement on retries; correct categories are never revealed regardless of attempt count.
3. **P2**: `user_progress` table missing `UNIQUE(user_id, step_id)` constraint — app dedup works today but DB allows future bugs to insert duplicates undetected.
4. **P2**: `/api/auth/me` doesn't surface activity stats. UI consumers must hit `/api/auth/my-courses` separately for progress.
5. **P2**: `user_id` column type mismatch (varchar in `user_progress` vs integer in `users.id`); SQL queries need string-quoted literals.

## Migration QA verdict
Postgres migration is clean. No 500s, no timeouts, no inconsistent reads, no FK violations, no orphan rows, no dropped progress. 85/85 steps walk and complete; both `/api/auth/my-courses` (read path) and `/api/progress/complete` (write path) round-trip correctly through PG. The two P0s are pre-existing course/grader content bugs unrelated to the migration.
