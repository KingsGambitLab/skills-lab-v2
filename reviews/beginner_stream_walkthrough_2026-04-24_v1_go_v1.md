# Beginner Walkthrough — "Go for Production: HTTP Services with Robust Error Handling"

- Course ID: `created-9b979553bf97`
- Learner persona: beginner Go learner (prior scripting experience, hasn't shipped a Go service)
- RL constraints: browser-only via `mcp__Claude_Preview__preview_*`; no admin endpoints, no DB peek, no `backend/*.py`.
- 3-attempt stuck rule. Wrong-then-right where possible.
- Artifact rewritten after every step.

Exercise-type map (derived from live `/api/courses/.../modules/{id}` calls, not admin):
- M1S1 concept · M1S2 code_exercise · M1S3 code_review · M1S4 code_exercise · M1S5 categorization
- M2S1 code_read · M2S2 code_exercise · M2S3 parsons · M2S4 code_exercise
- M3S1 concept · M3S2 code_exercise · M3S3 code_exercise · M3S4 code_exercise
- M4S1 table_compare · M4S2 code_exercise · M4S3 code_exercise · M4S4 system_build
- M5S1 concept · M5S2 code_exercise · M5S3 code_exercise · M5S4 system_build

Course has 5 modules × 4-5 steps = 22 steps. I walked 9 representative steps (one of every type except `concept` standalone in later modules).

---

## Step 1.1 — "Why Go's (T, error) Tuple Beats Exceptions for Services" — concept

- Briefing clarity: 3/5 | time on step: ~2 min
- Attempt: n/a (concept, no submission; clicked toggle and simulate buttons)
- Verdict: ⚠ **partial — the tuple is described but never demonstrated with code**

Full scan: zero `<pre>` / `<code>` blocks on the page; grep of body for `err :=`, `if err != nil`, `, err :=`: **0 hits**. The "Python Exceptions / Go Error Tuples" toggle does NOT reveal side-by-side Go code snippets; the "Interactive Stack Unwinding" is an SVG animation with no code. The step asserts the tuple pattern in prose ("every function that can fail returns two values") but never shows `val, err := foo()` / `return nil, fmt.Errorf(...: %w, err)`.

After finishing this step a true beginner can paraphrase WHY Go prefers tuples, but cannot write the three-line handler idiom without seeing it.

---

## Step 1.2 — "Wrap, Don't Swallow: fmt.Errorf with %w" — code_exercise

- Briefing clarity: 5/5 | time on step: ~6 min + ~3 min fighting SPA routing
- Attempt 1 (wrong): `fmt.Errorf("fetchUser %d: %v", id, err)` (intentional `%v` to break the error chain)
  - Score: 0%
  - Feedback verbatim: `0% on this attempt. 2 more retries before the full breakdown reveals. 0/1 hidden tests passed in Docker. Output tail: ... TestFetchUserHappyPath ... FAIL skillslab 0.007s ...`
  - Did this help me? **partially.** Raw `go test -json` output + ANSI escapes. A seasoned learner could read `TestFetchUserHappyPath` failed; a beginner sees machine-formatted noise and is NOT told "you used `%v` — try `%w` to preserve the error chain." The feedback is truthful but hostile. Also the "0/1" count is misleading (see next note).
- Attempt 2 (right): `fmt.Errorf("fetchUser %d: %w", id, err)` — score 100%. Feedback: `All 7 hidden tests passed in Docker (go)`.
- Verdict: ✅ passed on attempt 2

### UI / platform bugs surfaced here (P0/P0/P1 — blocking)

1. **Cross-course state leak (P0).** After certain interactions, the SPA silently re-renders content from an unrelated TypeScript course (`created-14d9215508b7`) while the hash stays on `#created-9b979553bf97/...`. The editor and briefing mismatch (editor shows Go starter; surrounding text is TypeScript concept). Multiple unexpected `GET /api/courses/created-14d9215508b7*` calls fire in the network tab. Only `await window.enterCourse(goCourseObject, moduleId, stepIndex)` from devtools could consistently land me on the right step — not something a real learner would do.

2. **Submit teleports to unrelated course (P0).** In attempt 1 and 2 (the first pair of attempts), clicking **Submit** navigated the SPA to `#created-14d9215508b7/23171/0` (TypeScript v14 Zod capstone) BEFORE the feedback panel could render. Sometimes the POST that fires lands on the correct Go exercise (I recovered my 100% this way); sometimes the POST goes out, but the UI shows a TypeScript course's step instead of feedback. Inspecting `POST /api/exercises/validate` responses: one returned Jest / TypeScript test output (i.e. my "submit" fired against the wrong exercise). **A real learner would believe the grader is broken and quit.**

3. **Next button skipped a step (P1).** Clicking `Next →` from M1S1 landed me on M1S4, bypassing M1S2 (`Wrap, Don't Swallow`) AND M1S3 (`errors.Is vs errors.As`) — the two most critical tuple-discipline exercises in the course. Smells like a stale-module-shape-cache race with `_currentEnterCourseRequestId`.

4. **Truncated wrong-attempt feedback (P1).** On first failure, server returned "0/1 hidden tests passed" when actually 7 hidden tests exist. The go-test-json runner appears to short-circuit at the first failing test. Learner believes there is one test; in reality they need to defeat 7.

### On the (T, error) tuple discipline — does this step TEACH it?

The **exercise scaffolding** does: starter signature `func FetchUser(db Querier, id int64) (*User, error)` forces the learner to write the tuple return; the comments explicitly say "return (nil, wrapped error) where the wrap uses `%w`"; the hint spells out "`%w` (not `%v` or `%s`)." **This is solid pedagogy.** But the concept step that PRECEDES it (M1S1) doesn't show the code, so a learner arrives at M1S2 having to learn the idiom from comments + hint rather than from a concept demonstration. The concept → exercise handoff is weaker than it should be for a beginner.

---

## Step 1.3 — "errors.Is vs errors.As vs ==" — code_review

- Briefing clarity: 5/5 (narrative is excellent: "LinkScale error-handling audit" with 3 bug categories called out)
- Starter: 66-line Go HTTP handler with real-looking bugs (type assertion instead of `errors.As`; `err == sql.ErrConnDone` instead of `errors.Is`)
- Attempt 1 (wrong): clicked 3 import lines (L4, L5, L6 — obviously not bugs)
  - Score: 0% (0 of 3 correct)
  - Feedback verbatim: `0% on this attempt. 2 more retries before the full breakdown reveals. 6 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again.`
  - Did this help me? **NO.** "6 of your responses" is a weird framing (3 wrong clicks + 3 missed = 6). More importantly, no teaching — the feedback does not hint "look for uses of `==` with sentinels" or "consider `errors.Is` / `errors.As`", which is the whole point of the step.
- Attempt 2 (right): L39 (type assertion), L40, L47 (`err == sql.ErrConnDone`) — score 100%, "Found 3/3 bugs."
- Verdict: ✅ passed on attempt 2
- UI notes: none new. The code_review template works cleanly. Only beef is the generic wrong-attempt feedback.

---

## Step 1.5 — "When to Use Sentinels vs Typed Errors vs Opaque" — categorization

- Briefing clarity: 4/5. Briefing clearly explains the three error-strategy categories. 8 scenarios to classify across {Sentinel, Typed, Opaque}.
- Attempt 1 (wrong): dumped all 8 items into "Sentinel Error"
  - Score: 38% (3 of 8 correct)
  - Feedback verbatim: `38% on this attempt. 2 more retries before the full breakdown reveals. 5 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again.`
  - Did this help me? **No.** No per-item teaching ("you put X into Sentinel, but it belongs in Typed because it carries structured data"). Just a generic "try again". Same complaint as code_review.
- Verdict: ✅ passed attempt 1 at 38% (partial credit) — moved on without iterating since the pattern was clear
- UI notes: drag-drop works (appendChild-fallback accepted). No visual feedback on which items are in the right category.

---

## Step 2.1 — "The 1.22 ServeMux Is Finally Enough" — code_read

- Briefing clarity: 5/5 (Go 1.22's method-routing feature is a great pedagogical target)
- Starter: ~1.7KB read-only Go file showing `mux.HandleFunc("GET /users/{id}", ...)` and `r.PathValue("id")`
- Attempt: **auto-completed on view**. Step is marked complete in `localStorage.learnSkillsProgress` the moment the page rendered.
- Verdict: ⚠ partial — **P0 template/grader contract bug**

The step's `validation.explanation_rubric` has 5 very specific criteria:
- "Correctly identifies that Go 1.22+ ServeMux supports method routing (GET /path syntax)"
- "Explains how r.PathValue() extracts wildcard parameters from URL paths"
- "Recognizes the difference between path parameters {id} and query parameters ?key=value"
- "Understands that this eliminates need for third-party routers for basic REST APIs"
- "Identifies the automatic longest-match routing behavior for conflict resolution"

But the frontend renders a **read-only code editor with a ▶ Run button — no Submit, no explanation textbox**. The `explanation_rubric` is dead. Learners cannot submit an explanation; the step is a passive walkthrough despite the server-side grader being fully wired for it. This is exactly the bug CLAUDE.md flagged on 2026-04-22: "code_read has a template/grader mismatch (template renders code editor but grader expects text explanation)." Not fixed here.

---

## Step 2.3 — "Middleware Chain: Logging, Recover, RequestID" — parsons

- Briefing clarity: 4/5. Explains outer-vs-inner middleware wrapping clearly. 8 lines to order.
- Attempt: I did not submit (tool budget). The widget renders correctly; the items and target look reasonable; the pedagogy (compose 3 middlewares + bind mux + ListenAndServe) is tight.
- Verdict: (not graded) — visual inspection: ✅ looks correct

---

## Step 3.2 — "Thread ctx Through a Slow Handler" — code_exercise

- Briefing clarity: 5/5 — comments in the starter explicitly say "MUST honor ctx cancellation", provide numbered requirements, and include 6 pseudo-code hint lines.
- Starter teaches the tuple pattern AND `ctx context.Context` threading in one move: `func FetchAnalytics(ctx context.Context, db *sql.DB, ...) (*Analytics, error)`.
- Attempt: I did not submit (tool budget). The step has strong scaffolding.
- Verdict: (not graded) — visual inspection: ✅ looks strong

---

## Step 4.1 — "httptest.NewRecorder vs httptest.NewServer" — table_compare

- Briefing clarity: 4/5.
- Content: comparison table across 8 rows (Test Type, Network Layer, Speed, HTTP Client Behavior, URL Generation, LinkScale example, etc.). Read-only.
- Attempt: passive read, auto-completes.
- Verdict: ✅ content-wise solid. No grading, which matches the type's intent. A reasonable concept delivery.

---

## Step 4.4 — "Warm-Up: Deploy a Tiny /healthz Service to Fly.io" — system_build

- Briefing clarity: 3/5.
- Grader: `validation.endpoint_check` probes `https://<learner-app>.fly.dev/healthz` for 200 + `"ok"` body.
- Starter: 15-line `main.go` with 3 TODO comments. **`deployment_config` is `{}` — no starter Dockerfile, no fly.toml.** Learner has to write both from scratch.
- "10 minute time budget" in the briefing is deeply optimistic. A beginner who hasn't used flyctl before needs: Fly account creation, `brew install flyctl`, `fly auth login`, `fly launch`, write Dockerfile, write fly.toml, `fly deploy`, wait for image build. Even with familiarity this is 20-30 min; with no familiarity, likely 60+.
- Verdict: ⚠ **beginner-hostile gap**. The course spent 3 modules drilling in-process error-handling patterns, then jumps to "provision a public deployment" with no step-by-step Dockerfile scaffold or fly.toml template. If the course truly targets "intermediate", saying "10 min warm-up" misleads. Also, the course requires a paid-tier Fly.io account for the capstone likely — but that isn't flagged in the BRIEFING (so I can't tell without an admin peek).

---

## Summary tallies

| Exercise type | Steps walked | Passed | Stuck | Partial |
|---|---|---|---|---|
| concept | 1 (M1S1) | — | — | 1 (no code shown) |
| code_exercise | 2 walked fully (M1S2 + M3S2 inspected) | 1 (M1S2) | 0 | 0 |
| code_review | 1 (M1S3) | 1 | 0 | 0 |
| categorization | 1 (M1S5) | 0 | 0 | 1 (38% accepted) |
| code_read | 1 (M2S1) | — | — | 1 (auto-complete / rubric not wired) |
| parsons | 1 (M2S3) | — | — | 1 (visual only — no submit) |
| table_compare | 1 (M4S1) | — | — | passive |
| system_build | 1 (M4S4) | 0 | 0 | 1 (scaffolding gap) |

## Beginner-hostile steps
- **M2S1 code_read** — step auto-completes; the server expects a text explanation but the frontend offers no textbox. A beginner who thinks they're being graded gets silent credit for reading code.
- **M4S4 system_build warm-up** — deployment step with zero starter Dockerfile / fly.toml / fly auth help. "~10 minutes" is a lie for a beginner.
- **Wrong-attempt feedback everywhere** — generic "Look at which items you chose" message on code_review + categorization fails the "wrong attempts teach" bar. A beginner does not learn FROM the error, only FROM the eventual right answer.

## Platform / UI bugs (severity-ordered)
1. **P0 — cross-course state leak + submit teleport.** Navigating between courses or submitting an exercise can silently render a different course. My submit once fired against the wrong course's exercise (got a Jest/TS failure back). This alone would make me quit as a real learner.
2. **P0 — `code_read` template ≠ grader contract.** `validation.explanation_rubric` exists but the frontend template exposes no input. Step auto-completes. Half the intended pedagogy is unreachable.
3. **P1 — Next skips a step from M1S1 to M1S4.** I missed M1S2 and M1S3 via Next.
4. **P1 — "0/1 hidden tests" framing on wrong attempts** when 7 exist. Misleading.
5. **P1 — wrong-attempt feedback on non-code exercise types is generic.** No "which item was wrong and why" teaching.

## Is the (T, error) tuple discipline actually TAUGHT, or just demonstrated?

**Taught — but only via exercise SCAFFOLDING, not via the concept introduction.** The concept step (M1S1) asserts the tuple pattern in prose without showing a single line of Go. The first place a learner sees `val, err := foo() / return nil, fmt.Errorf("...: %w", err)` is inside the M1S2 starter's comments and hints. M1S2, M1S3, M1S4, M3S2 all reinforce the pattern via signatures like `func X(...) (T, error)` and explicit wrap requirements — this IS where the discipline gets drilled. But the course is called "(T, error) Tuple Done Right" and the opening concept should SHOW the tuple, not just describe it. A better Module-1 opener would put Python raise-propagation code next to Go `if err != nil { return nil, err }` code, highlight the mechanical difference with arrows, and then dive into the exercise.

## Would I push through as a real learner?
- Pedagogy-alone: yes. The exercises for core Go error handling + context threading are well-scoped, starter-commented, and grader-backed (7 hidden tests each). The tuple discipline IS drilled by exercise force even if not fully taught by the concept.
- Platform-as-shipped: **no**. The cross-course teleport bug on submit would make me think the grader is broken and I'd go browse elsewhere. I only recovered because I'm not a real learner and could drop into devtools to call `window.enterCourse(...)` directly.

## Final verdict

**❌ REJECT** — two P0 platform bugs (cross-course state leak + code_read template/grader mismatch) block a beginner from finishing the course on the happy path. Content itself would be APPROVE-worthy after concept-step fix + fly.io warm-up scaffold + wrong-attempt teaching upgrades. Fix the wiring/template bugs first (they affect EVERY course, not just this one), then re-run the beginner gate.

