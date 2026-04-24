# Review Consolidation — 2026-04-24

**Courses reviewed:** TypeScript v14 (`created-14d9215508b7`) + Go v1 (`created-9b979553bf97`)
**Agents:** beginner × 2 + domain-expert × 2 = 4 reviews (TS-beginner partial, 3 steps walked)

**Verdicts:**

| Course | Beginner | Domain-Expert | Combined |
|---|---|---|---|
| TS v14 | PARTIAL (3 steps + meta-observation) | **CONDITIONAL** (0.664 / 1.00) | **CONDITIONAL — blocked by P0 content drift** |
| Go v1 | **REJECT** (P0 platform wiring) | **CONDITIONAL** (0.76 / 1.00) | **REJECT — blocked by P0 leak + cross-course routing** |

---

## P0 — ship-blockers (MUST fix before publishing)

### P0.1 — Answer-key leak on public endpoint (Go course, domain-expert)

**What:** `GET /api/courses/created-9b979553bf97/modules/23187` returns `validation.solution_code` (1678-byte full production solution) and `validation.hidden_tests` verbatim to any unauthenticated request.

**Root cause:** Sanitizer gap in the learner-facing module endpoint. The `_sanitize_step_for_learner()` function at `backend/main.py:~1269` strips `validation.correct_answer` and some other fields, but **not** `validation.solution_code` and **not** `validation.hidden_tests` for code_exercise steps.

**Fix (engine-level, no course regen):**
1. Extend `_sanitize_step_for_learner` to strip `validation.solution_code` + `validation.hidden_tests` + `validation.must_contain` + `validation.requirements` from the public module response.
2. Verify: `curl http://localhost:8001/api/courses/.../modules/<mid>` returns no `solution_code` or `hidden_tests` in any step.
3. Bulk re-test against ALL existing courses (there are 100+) — sanitizer gap affects every code_exercise, not just today's two courses.

**Scope:** language-agnostic. Same issue on every code_exercise step in every course.

---

### P0.2 — Cross-course state leak + Next button teleports across courses (both courses, both beginners)

**What:** Navigating or clicking Next inside one course sometimes loads content / state from a different course. Go-beginner saw Submit on a Go exercise teleport to the TS capstone + `/api/exercises/validate` returned TS/Jest output instead of Go test output. TS-beginner saw URL hash auto-change to the Go course ID during walkthrough. Also saw ghost completion counts on modules never visited.

**Root cause:** Deep-link router bug + possibly `state.currentCourse` / `state.modules` cross-pollution. CLAUDE.md §"Course-switching state bleed (2026-04-18)" partially addressed `onCourseClick`, but **Next button does not tear down prior course state the same way**. Also: hash restoration may load the wrong course when hash parses to `#<courseId>/<moduleId>/<stepIdx>` — if `<moduleId>` exists in two different courses, the router picks the wrong one.

**Fix (frontend-level, no course regen):**
1. In `Next` button handler: validate that the next module/step still belongs to `state.currentCourse.id` before navigating. If not, re-fetch the current course instead of teleporting.
2. In `parseHash` / `restoreFromHash`: require `(courseId, moduleId)` tuple match, not just `moduleId`. Reject hash navigation into a course you're not "enrolled" in (i.e., `state.currentCourse?.id !== hashCourseId` → force full course load).
3. Module-progress sidebar should key on `(courseId, moduleId)`, not `moduleId` alone.

**Scope:** language-agnostic. Platform-wide.

---

### P0.3 — Result<T,E> shape drift across TS capstone steps (TS course, domain-expert)

**What:** Three different shapes in four capstone steps:
- Step 5.0 concept: `{ success: true; data: T }`
- Step 5.1 warm-up: `{ ok: true; value: T }`
- Step 5.2 fetchJson: `{ ok: true; data: T }`

And `ApiError` is incompatible between 5.2 (`class extends Error` union) and 5.3 (tagged `{ kind: 'network' } | ...` union). A learner consuming their 5.2 output in a 5.3 handler gets a type wall.

**Root cause:** Each step is generated independently; the Creator prompt doesn't carry forward canonical type definitions from prior steps in the same course. Same class as the "persona name drifts between modules" bug.

**Fix (Creator-prompt level + regen affected steps):**
1. In `_creator_generate_impl`, thread a `course_canonical_types: dict[str, str]` through per-step generation. First code_exercise / concept in a module that introduces a type seeds the dict; subsequent steps in the SAME module (and later modules) MUST emit those types verbatim.
2. Validation in `_is_complete` for code_exercise: reject if the step declares `Result` / `ApiError` / other course-wide types with a shape different from `course_canonical_types[type_name]`.
3. Per-step regen for the 5 TS capstone steps (5.0-5.4) with the canonical-types thread active.

**Scope:** language-agnostic. Same drift class affects every multi-step course with shared types (Python classes, Go structs, Rust enums, Java records).

---

### P0.4 — code_read template/grader contract mismatch (Go course, beginner)

**What:** M2.S0 "The 1.22 ServeMux Is Finally Enough" has `validation.explanation_rubric` with 5 scoring criteria, but the frontend renders a read-only code editor + `▶ Run` button and NO textbox / input for the learner's explanation. Step auto-marks complete on load. Half of Module 2's pedagogy is UNREACHABLE.

**Root cause:** `code_read` template renders the same widget as `code` (read-only code display), but doesn't provide a grader-matching input. The Creator emits `explanation_rubric` in validation but the frontend has no widget for it. CLAUDE.md flagged this class of bug on 2026-04-22 ("wiring fixes propagate to every future course") — it didn't get fixed.

**Fix (frontend + engine, no course regen):**
1. Update `code_read` frontend template to render: (a) code display pane, (b) `<textarea>` for the learner's explanation, (c) Submit button → POSTs to `/api/exercises/validate`.
2. `/api/exercises/validate` for `code_read` type: grade the explanation against `validation.explanation_rubric` via LLM rubric (mirrors `adaptive_roleplay` scoring pattern).
3. Ontology gate (`backend/ontology.py`): if `exercise_type == "code_read"` and `validation.explanation_rubric` is present, frontend MUST emit the textarea.

**Scope:** platform-wide. All `code_read` steps across all courses are currently broken.

---

## P1 — real friction, should fix before reviewer re-pass

### P1.1 — Timeout pattern in TS fetchJson uses `Promise.race` + `setTimeout`, not AbortController

**What:** Step 5.2 solution's timeout mechanism is `Promise.race([fetch, setTimeout])` — the underlying fetch is NEVER actually cancelled. Zero mention of `AbortController` / `AbortSignal.timeout(ms)` / signal propagation across the course.

**Root cause:** Creator prompt for TS capstone doesn't mandate AbortController. The LLM defaulted to the "simpler" Promise.race pattern which is an 2018-era anti-pattern.

**Fix:** TS runtime-deps brief + `_is_complete` for code_exercise with `fetch` call: require `AbortController` usage OR `AbortSignal.timeout`. No `Promise.race([fetch, setTimeout])`.

---

### P1.2 — `context.WithValue(r.Context(), "request_id", id)` string-literal ctx-key (Go course, M4.S3)

**What:** After M3.S3 teaches the `type requestIDKey struct{}` idiom (private typed key, zero collisions), M4.S3 regresses to a bare string literal — the exact anti-pattern M3.S3 just flagged as a bug.

**Root cause:** Creator prompt doesn't enforce "once a pattern is taught, later steps use it verbatim."

**Fix:** same as P0.3 mechanism — `course_canonical_patterns` thread. Per-step regen for Go M4.S3.

---

### P1.3 — M2.S2 hint teaches `type-assert` when `errors.As` is correct (Go course)

**What:** M2.S2 hint says "use a type assertion to get the `*AppError`" — contradicts M1.S3 which plants bare type-assertion as a PLANTED BUG. Single-step inconsistency.

**Fix:** single-step hint regen for Go M2.S2 with feedback pointing at M1.S3's bug-taxonomy.

---

### P1.4 — Wrong-answer feedback is not pedagogically useful (Go beginner)

**What:** Failing a Go `code_exercise` returns raw `go test -json` tails with ANSI escapes + misleading "0/1 hidden tests passed" (when 7 tests exist). `categorization` / `code_review` wrong-answer feedback is a generic "look at your choices and try again" — no per-item guidance.

**Root cause:** `/api/exercises/validate` returns raw runner output in a learner-unfriendly format. Needs a grader-feedback layer that maps raw test failures to pedagogical hints ("you used `%v` instead of `%w` — that breaks the error chain").

**Fix:** frontend + engine. Parse test output; when known failure patterns appear (e.g. `errors.Is` returned false + `%v` in source), emit a specific hint. Per-item feedback for categorization already exists for TS — extend to Go tests.

---

### P1.5 — `table_compare` banner shows raw ontology ID "TABLE_COMPARE" (TS beginner)

**What:** Step-type banner displays `TABLE_COMPARE` instead of a pretty label.

**Fix:** trivial frontend map from ontology slide-type IDs to display labels.

---

### P1.6 — Learner never writes a Jest test in the TS capstone (domain-expert)

**What:** Step 5.3 CLAIMS hidden tests enforce narrowing discipline, but the capstone ships no visible test file. Step 5.4 pivots to CI YAML. test_suite_quality axis (20% weight) is a real hole.

**Fix:** Creator prompt should require at least one step where the LEARNER writes a jest test for a function they wrote earlier. Or: surface hidden_tests to learner as a "here are the tests you'd need to pass" pane (read-only, teaches by example).

---

### P1.7 — HTML sanitizer eats `<typeof UserSchema>` in TS concept (domain-expert)

**What:** `z.infer<typeof UserSchema>` renders as `z.infer<typeof userschema="">` — HTML sanitizer treats `<typeof ...>` as an HTML tag.

**Fix:** darkify/sanitizer regex must escape `<` in code-block contexts. HTML escape inside `<pre>` / `<code>` before applying any HTML transformation.

---

## P2 — polish, ship-after

### P2.1 — Missing `http.Server` timeouts in Go capstone (ReadTimeout / WriteTimeout / IdleTimeout / ReadHeaderTimeout) — slowloris-vulnerable. No DB pool sizing. Fix at Creator prompt.

### P2.2 — `AppError` shape drift across 5 Go steps (Status field appears/disappears; code flips int ↔ string). Same mechanism as P0.3.

### P2.3 — M1.S1 Go concept step has ZERO lines of Go code; first tuple-assignment the learner sees is in M1.S2 starter. For a course named "(T, error) Tuple Done Right", the concept opener failing to show a single `val, err := foo()` is a content bug.

---

## What we missed (meta-observations)

1. **The test-agent cycle caught 3 platform-wide wiring bugs** (P0.1 sanitizer, P0.2 cross-course leak, P0.4 code_read mismatch) that the generator + invariant gate cannot catch because they're AT THE UI / API LAYER, not content. Invariant validates solution/starter pairs — it doesn't test the learner's actual experience. **The review-agent cycle is load-bearing; it cannot be skipped.**

2. **`course_canonical_types` / `course_canonical_patterns` is a MISSING CREATOR PRIMITIVE.** We thread `course_context["language"]` + source_material but not "types / names / patterns introduced in prior steps of this same course." Fixing P0.3 + P1.2 + P2.2 is ONE fix at the Creator level.

3. **The LLM-rubric grader pattern (`adaptive_roleplay`) is NOT applied to `code_read`.** `code_read` has `explanation_rubric` in validation but no matching endpoint to grade it. Classic "shipped-type without matching grader" bug, which is the same bug class `code_review` had before v6. Ontology enforcement should have caught this — extend `validate_step_against_ontology` to verify `(exercise_type, grade_primitive_used)` ↔ frontend widget exists.

4. **Bulk-sanitization re-test is needed.** P0.1 means EVERY existing code_exercise step on EVERY course is leaking solution_code + hidden_tests today. Not just today's two courses. CLAUDE.md already has a "bulk live-preview QC" pattern (103/103 earlier) — needs re-run post-fix.

---

## Prioritized fix plan (proposed — waiting for user instruction)

| Priority | Item | Scope | Effort |
|---|---|---|---|
| P0.1 | Sanitizer extension for `solution_code` / `hidden_tests` / `must_contain` / `requirements` | engine | 30 min |
| P0.2 | Next-button course-id validation + hash restore (courseId, moduleId) tuple match | frontend | 1 hr |
| P0.3 | `course_canonical_types` thread in Creator + per-step regen of TS 5.0-5.4 | Creator engine + regen | 2 hr |
| P0.4 | `code_read` frontend textarea + LLM-rubric grader for `explanation_rubric` | frontend + engine | 1.5 hr |
| P1.1 | AbortController requirement in TS brief + per-step regen of 5.2 | Creator prompt + regen | 30 min |
| P1.2 | Go ctx-key pattern enforcement + M4.S3 regen | covered by P0.3 | shared |
| P1.3 | M2.S2 hint regen | per-step regen | 10 min |
| P1.4 | Test-failure pedagogical feedback layer | engine + frontend | 3 hr |
| P1.5 | Slide-type banner pretty labels | frontend | 10 min |
| P1.6 | Creator prompt: at least one learner-writes-tests step in code capstones | Creator prompt + regen | 1 hr |
| P1.7 | HTML sanitizer escape `<` in code blocks | engine | 30 min |
| P2.* | Timeouts / pool sizing / Go concept opener | Creator prompt + regen | 2 hr |
