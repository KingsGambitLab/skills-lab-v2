# Domain-Expert Review — Go for Production: HTTP Services with Robust Error Handling
Persona: Senior Go engineer / SRE (6+ yrs shipping services)
Date: 2026-04-24
Pass: v1

## Overview

5 modules, 21 steps. Level: Intermediate. 2hr estimated. Capstone: ship a URL shortener (LinkScale) to Fly.io with SQLite, rate limiting, slog, graceful shutdown.

| # | Module | Steps | Types |
|---|---|---|---|
| 1 | Go Error Handling: (T, error) Done Right | 5 | concept, code_exercise ×2, code_review, categorization |
| 2 | HTTP Services with net/http (Go 1.22+ ServeMux) | 4 | code_read, code_exercise ×2, parsons |
| 3 | Context, Cancellation, Structured Logging with slog | 4 | concept, code_exercise ×3 |
| 4 | Testing HTTP Services with httptest | 4 | table_compare, code_exercise ×2, system_build (warmup Fly.io /healthz) |
| 5 | Capstone: Ship URL Shortener to Fly.io | 4 | concept, code_exercise ×2, system_build (Fly deploy) |

Diverse exercise mix (9 code_exercise, 2 system_build, plus code_review, parsons, categorization, table_compare, code_read, concept) — not MCQ-heavy. Narrative thread: LinkScale URL shortener (fictional fintech-ish co., named engineers Marcus Chen / Sofia Reyes / David Kim / Alex Rodriguez used as reviewers in the capstone briefing).

## Steps I walked (16 in depth)

M1.S1 concept (Why T,error beats exceptions), M1.S2 code_exercise (FetchUser wrap-with-%w), M1.S3 code_review (errors.Is vs As vs ==), M1.S4 code_exercise (AppError + HTTP mapping), M1.S5 categorization (sentinel/typed/opaque), M2.S2 code_exercise (handler-returns-error), M2.S3 parsons (middleware chain composition), M2.S4 code_exercise (writeJSON/writeError with errors.As), M3.S1 concept (ctx lifeline), M3.S2 code_exercise (FetchAnalytics ctx through DB + HTTP), M3.S3 code_exercise (RequestIDMiddleware unexported key), M3.S4 code_exercise (slog JSONHandler + WithRequestContext), M4.S1 table_compare (NewRecorder vs NewServer), M4.S2 code_exercise + its hidden_tests, M4.S3 code_exercise (integration test panic recovery + log corr), M4.S4 system_build (warmup /healthz), M5.S1 arch concept, M5.S2 token-bucket limiter with x/time/rate, M5.S3 graceful shutdown, M5.S4 capstone deploy.

## Blind-spot coverage

### Blind spot 1 — Teaches the WHY of (T, error): early-return, explicit, no hidden flow
- Covered? **yes**
- Evidence: M1.S1 concept includes a side-by-side Python-exception vs Go-tuple comparison with an interactive SVG stack-unwind animation. Explicit bullets: "No hidden control flow", "Explicit error at each level", "Cleanup guaranteed via defer". Not just using the pattern — the anti-patterns (`finally` skipped, context lost in except clause) are demonstrated in real Python sample code alongside.
- Nit: the section leans on prose after the visual; could sharpen by asking the learner to predict what happens if they forget to return after an error check.

### Blind spot 2 — `fmt.Errorf %w` vs `%v`; errors.Is vs errors.As distinction
- Covered? **yes**
- Evidence: M1.S2 hint: *"Use fmt.Errorf with %w (not %v or %s) — %w is what makes errors.Is and errors.Unwrap traverse the chain."* Acceptance criteria explicitly include `errors.Is(err, sql.ErrNoRows) still matches on the wrapped error` (#3). M1.S3 code_review plants the anti-patterns (`err.(sqlite3.Error)` and `err == sql.ErrConnDone`) so the learner has to find them. M2.S4 writeError explicitly says "use errors.As to check if err is an AppError type".
- Minor drift: M2.S2 hint says "type-assert the error to AppError and use its Code field for the HTTP status" — this is wrong idiom (should be `errors.As` to survive wrapping) and Code is the app code, not the status (Status is Status). The prior and subsequent steps teach the correct pattern; just this hint regresses.

### Blind spot 3 — AppError/custom-error honesty: when typed beats sentinel, when overengineered
- Covered? **partial**
- Evidence: M1.S5 categorization drill pits Sentinel / Typed / Opaque against 8 scenarios. That's the right shape of exercise. However the CONCEPT content around it doesn't directly lay out the trade-off rubric (cost of defining a typed error, coupling caller to typed shape, when a sentinel + `%w` is cheaper).
- Gap: the course never pushes back against AppError. A learner could walk away thinking "every error must be AppError." Honest production Go is more nuanced — internal helpers often return opaque errors, only the HTTP boundary needs the typed one. A sidebar "when NOT to use AppError" would close this.

### Blind spot 4 — Context as the REQUEST LIFELINE with disciplined propagation
- Covered? **yes (strong)**
- Evidence: M3.S2 FetchAnalytics is a perfect realistic exercise — DB call + outbound HTTP, both must take ctx. The starter's doc comment enumerates 4 requirements including "abort within ~50ms on ctx cancel". The hidden test in M3.S2 registers a **custom `database/sql/driver` fakeDriver** that only honors `QueryContext`'s cancellation path — if the learner calls `db.Query`, the fakeDriver's Query path returns fast and other tests using a short-deadline ctx will fail. That's real test design: the tests catch the exact mistake the concept warns against.
- M3.S3 teaches `type requestIDKey struct{}` — canonical unexported key idiom for ctx values.
- Minor issue: M4.S3's RequestIDMiddleware example regresses to `context.WithValue(r.Context(), "request_id", requestID)` — a STRING LITERAL key, exactly what M3.S3 warned against. This will confuse a careful learner. Also that snippet generates request_id via `fmt.Sprintf("req-%d", time.Now().UnixNano())` which is NOT cryptographically random as M3.S3 taught.

### Blind spot 5 — httptest craft: NewRecorder vs NewServer, table-driven tests, DI
- Covered? **partial-yes**
- Evidence: M4.S1 table_compare explicitly contrasts NewRecorder (unit) vs NewServer (integration) across 6 axes. M4.S2 is table-driven tests for error paths (happy path, bad JSON, missing field, duplicate). M4.S2's starter defines a `MockDB` — showing DI for testable handlers. M4.S3 uses httptest.NewServer to test the full middleware chain end-to-end incl panic recovery + log correlation via `bytes.Buffer` captured slog handler.
- Gap: the hidden test for M4.S2 only asserts the outer TestCreateUser doesn't panic and a few happy/sad paths. It does NOT enforce that the learner's test IS table-driven — a flat if-else implementation would pass. The Layer-A gate (≥4 hidden tests) is met but "table-driven" is claimed, not enforced. A real senior would require the learner to populate at least a `[]struct{...}` slice.

### Blind spot 6 — Graceful shutdown: SIGTERM, drain, deadline, DB close
- Covered? **yes (strong)**
- Evidence: M5.S3 RunServer starter doc comment calls out the 4 gotchas that trip every junior: (1) use `http.Server` struct so `.Shutdown()` is available, (2) don't treat `http.ErrServerClosed` as an error, (3) derive the shutdown deadline from `context.Background()` NOT the already-canceled parent ctx, (4) channel for listen-error propagation. The hint doubles down: "http.ErrServerClosed is the EXPECTED return from ListenAndServe after Shutdown — don't treat it as an error. And derive the shutdown deadline from context.Background(), not the already-canceled parent ctx." Matches 30s Fly.io kill_timeout explicitly. This is REAL production knowledge.
- Small gap: the capstone doesn't make the learner close DB pool explicitly inside Shutdown — for a SQLite URL shortener it's less dramatic, but for a Postgres pool a senior would want `db.Close()` called after `srv.Shutdown` returns. Nice-to-have to mention.

### Blind spot 7 — Go's compile-time strictness (unused imports / vars) acknowledged
- Covered? **partial**
- Evidence: Every code_exercise starter has explicit `_ = fmt.Sprintf` / `_ = io.Discard` / `_ = errors.New` compile-keep lines. That IS how you acknowledge the strictness in scaffolding. No concept step explicitly says "Go refuses to compile if you leave an unused import" — which beginners find shocking coming from Python/JS. This is "assumed" knowledge, okay for an intermediate course but would deserve a mention.

### Blind spot 8 — slog handler chain, context correlation, Text vs JSON
- Covered? **partial-yes**
- Evidence: M3.S4 builds `SetupLogger` → `slog.NewJSONHandler(os.Stdout)`. `WithRequestContext(ctx, logger)` extracts request_id from ctx and returns `logger.With("request_id", id)` — correct correlation pattern. Handler chain (Recover → Logger → RequestID) is exercised in M2.S3 parsons.
- Gap: Text vs JSON handler choice is not explicitly taught. Production Go logs JSON to stdout (for log aggregator ingestion) but dev uses Text. The course defaults to JSON without acknowledging the choice. A "why JSON here" sidebar would help.
- M3.S4 handler uses `contextKey` string-const pattern, M3.S3 uses `struct{}` empty-type pattern — both valid but the course doesn't reconcile them. Reader will wonder which to adopt.

### Blind spot 9 — Connection-pool sizing, timeouts at every layer, panic-recovery middleware, rate limit strategy
- Covered? **partial**
- Evidence: M2.S3 parsons teaches Recover(Logger(RequestID(mux))) composition — panic-recovery in outermost. M4.S3 integration test exercises panic recovery end-to-end. M5.S2 rate limiter uses canonical `golang.org/x/time/rate` token bucket + per-IP `sync.Map` + X-Forwarded-For awareness. M5.S3 mentions Fly.io 30s kill_timeout.
- Major gap: NO discussion of `http.Server` ReadTimeout / WriteTimeout / IdleTimeout / ReadHeaderTimeout. The starter http.Server in M5.S3 is `&http.Server{Addr, Handler}` — no timeouts at all, which is a production footgun (slowloris). Similarly NO mention of DB `MaxOpenConns` / `MaxIdleConns` / `ConnMaxLifetime` even though the capstone uses SQL. A senior would not ship that configuration. These are exactly the "timeouts at every layer" items an SRE hunts for.

## P0 issue I discovered outside the blind-spot list

**`validation.solution_code` + `validation.hidden_tests` leak to the learner endpoint.**
`GET /api/courses/created-9b979553bf97/modules/23187` (public, no auth) returns `steps[1].validation.solution_code` = full 1678-byte production solution for the rate limiter, and `steps[*].validation.hidden_tests` = full test source. A learner with DevTools open sees the solutions to every code_exercise in the capstone before writing a line. Classes this course below the "hands-on" bar — you can't grade what you give away.

The sanitizer `_sanitize_step_for_learner` in backend/main.py was supposed to strip `validation.*` answer keys per CLAUDE.md 2026-04-19. Either it missed these two keys, or this course was persisted bypassing the sanitizer. Needs fixing at the engine level (sanitizer regex) + re-serving this course; per CLAUDE.md §"Do Not Patch Broken Generated Courses" the course shouldn't be DB-edited — the sanitizer fix will propagate.

Verified via:
```
$ curl -s http://127.0.0.1:8001/api/courses/created-9b979553bf97/modules/23187 | jq '.steps[1].validation | keys'
["hint","hidden_tests","solution_code","must_contain","requirements"]
```

## Inter-module code drift

`AppError` is redefined 5 times across steps with DIFFERENT field sets:

| Step | Code field | Status field | Err field | Unwrap |
|---|---|---|---|---|
| M1.S4 | `string` (app code) | `int` (HTTP) | `error` | mentioned |
| M2.S2 | `int` (HTTP) | — | `error` | — |
| M2.S4 | `int` (HTTP) | — | `error` | yes |
| M5.S2 (solution) | `string` (app code) | `int` (HTTP) | — | — |
| M5.S4 | `int` (HTTP) | — | `error` | yes |

Field `Code` flips between "application code (string)" and "HTTP status (int)" between adjacent modules. A learner trying to reuse their M1.S4 AppError across modules hits a type wall. Root cause: per-step content generation without cross-module type coherence. Fix at the Creator-prompt level (carry forward the canonical type definition as "prior context" through the outline's shared-code) is the right layer, not a course edit.

## Axis scores

- **idiomatic_go: 0.80**
  - Strong: `%w` wrapping, `errors.Is/As`, unexported ctx-key type (M3.S3), `QueryContext` + `NewRequestWithContext`, `golang.org/x/time/rate`, `http.Server` with `.Shutdown()`.
  - Weak: the M4.S3 anti-example reverts to string-key context values (contradicts the M3.S3 lesson); `AppError` shape drift between modules forces learners to disentangle inconsistencies; hint on M2.S2 says "type-assert" where `errors.As` is correct.
- **error_handling_discipline: 0.78**
  - Strong: `%w` vs `%v` explicitly taught; `errors.Is` vs `errors.As` vs `==` as a dedicated code_review; categorization drill of sentinel/typed/opaque; AppError starter code with full Unwrap + HTTP mapping.
  - Weak: course never honestly discusses WHEN AppError is overengineering; AppError shape drift across modules undermines the "design it once" message; one hint (M2.S2) regresses to bare type-assertion.
- **context_and_cancellation: 0.82**
  - Strong: M3.S2's FetchAnalytics is a near-perfect exercise with `QueryContext` + `NewRequestWithContext` + `%w` wrap, and the hidden test uses a custom `database/sql/driver` fakeDriver that ACTUALLY catches non-ctx-threaded code. That's real grading for a real skill. M3.S3 teaches unexported key type. M5.S3 graceful shutdown teaches the `context.Background()` fresh-ctx trick.
  - Weak: M4.S3 regresses to string-key ctx value; no explicit coverage of ctx deadlines vs cancellation distinction (`WithTimeout` vs `WithCancel`); no coverage of what happens when you DON'T check ctx (e.g. long CPU loop — `select { case <-ctx.Done(): ... }` pattern never taught).
- **production_readiness: 0.65**
  - Strong: Fly.io warmup (M4.S4) + capstone deploy (M5.S4), panic-recovery middleware, graceful shutdown, rate limiter using `x/time/rate`, structured JSON logs, X-Forwarded-For awareness in ClientIP.
  - Weak: NO http.Server timeouts (ReadTimeout/WriteTimeout/IdleTimeout/ReadHeaderTimeout) anywhere — slowloris-vulnerable by default; NO DB pool sizing (MaxOpenConns/MaxIdleConns/ConnMaxLifetime) despite using SQL; NO observability beyond slog (no /metrics endpoint, no readiness vs liveness split — healthz is just one probe; no request duration histogram). In a course titled "for Production", these are must-haves.
- **testing_craft: 0.70**
  - Strong: M4.S1 NewRecorder vs NewServer comparison matrix; M4.S2 table-driven tests with MockDB DI; M4.S3 integration test with full middleware chain + slog bytes.Buffer capture; M3.S2 hidden test with custom SQL driver that enforces ctx propagation.
  - Weak: "table-driven" not enforced by hidden tests (a flat if-else passes); no property-based tests introduced even for the rate limiter where they'd shine; no parallel-test / race-detector coverage despite concurrency in the rate limiter.

## Weighted score

idiomatic_go 0.80 × 25% = 0.200
error_handling_discipline 0.78 × 25% = 0.195
context_and_cancellation 0.82 × 20% = 0.164
production_readiness 0.65 × 20% = 0.130
testing_craft 0.70 × 10% = 0.070

**TOTAL: 0.759 / 1.00**

## Verdict

**CONDITIONAL APPROVE (0.76 — just above the 0.75 bar, but with one P0 that MUST land first).**

### MUST FIX before approval (P0/P1)

1. **(P0) Answer-key leak**: `validation.solution_code` and `validation.hidden_tests` exposed on public module endpoint. Strip at the `_sanitize_step_for_learner` level — extend the field-strip list. Confirmed via direct curl. Verified on module 23187 step 23186 — solution_code len=1678, fully spells out the production rate-limiter. Ship the sanitizer extension, then re-fetch and re-curl. No course re-gen required — this is a serve-time sanitizer gap.

2. **(P1) M4.S3 contradicts M3.S3 on ctx-value keys**: `RequestIDMiddleware` example in the integration-test starter uses `context.WithValue(r.Context(), "request_id", ...)` with a string literal — the exact anti-pattern M3.S3 flagged. Fix at Creator-prompt level ("every ctx value in ALL examples must use an unexported key type") + regenerate M4.S3 per the narrow-scope regen policy.

3. **(P1) M2.S2 hint says "type-assert" where "errors.As" is correct**: regenerate M2.S2 hint text only (`PATCH /steps/.../regenerate` on the single step's hint, or a direct field edit if safelisted).

### SHOULD FIX but non-blocking

4. **(P2) Missing http.Server timeouts**: add a sidebar / new step teaching ReadTimeout / WriteTimeout / IdleTimeout / ReadHeaderTimeout. For a production course, omitting these is the single biggest gap.

5. **(P2) AppError shape drift across 5 steps**: Creator-prompt change — when a type is defined in step N, carry its canonical definition forward as context to step N+1's starter so subsequent steps don't redeclare with different field names/types.

6. **(P2) "Table-driven tests" not enforced**: extend the hidden test for M4.S2 to statically check that the learner's test file contains a `[]struct` literal with ≥3 elements and a `for _, tc := range tests` loop.

7. **(P3) AppError-honesty sidebar**: a 2-paragraph callout on "when NOT to use AppError" — internal helpers / private APIs don't need typed errors, they just need `%w`-wrapped opacity.

8. **(P3) DB pool sizing**: once the SQLite capstone is working, a follow-up concept step on `db.SetMaxOpenConns` / etc. would be worth adding; even if the capstone doesn't need it, the senior-grade outcome claim demands it.

### REAL vs TOY — the key question the caller asked

- **context.Context**: REAL. M3.S2 actually catches the cancellation failure with a custom driver — that's the cleanest production-grade ctx exercise I've seen in a course format.
- **graceful-shutdown**: REAL. M5.S3 names the 4 exact gotchas that trip juniors (ErrServerClosed handling, fresh ctx for timeout, channel for listen errors, http.Server vs ListenAndServe). Matches what I'd review in a PR.
- **rate-limiter**: REAL. `x/time/rate` + sync.Map + X-Forwarded-For awareness. The toy version would be a counter-per-second map; this isn't that.
- **slog correlation**: REAL at the M3.S4 level (WithRequestContext → logger.With), but UNDERMINED at M4.S3 by the string-key regression. The pattern the learner will copy from the integration-test scaffolding is the weaker one — that's the issue to fix.

## One-line executive summary

Close to production-grade — the context / graceful-shutdown / rate-limiter patterns are REAL, not toy; but MUST fix the `solution_code` leak (P0), the M4.S3 ctx-key anti-pattern regression, and the M2.S2 "type-assert" hint before I enroll juniors; add http.Server timeouts + resolve the AppError cross-module drift to earn a clean APPROVE.
