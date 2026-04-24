# Domain Expert Review — TypeScript v12: Types, Zod, API Clients

- **Reviewer role**: Senior Backend TypeScript Engineer (8+ yrs production TS services)
- **Review date**: 2026-04-24
- **Course id**: `created-bd2b52794db2`
- **Surface**: `http://127.0.0.1:8001/#created-bd2b52794db2` + admin raw endpoint for hidden-test inspection
- **Target learner**: junior about to ship Zod-validated service-layer APIs (TS + Node 20 + jest + zod) within the month
- **Bar**: "If a junior finishes this, can they ship a Zod-validated `POST /orders` endpoint Monday and not page me Tuesday?"

---

## HEADLINE FINDING (read before the step grid)

**7 of the 10 code-producing exercises — including the capstone `fetchJson<T>` and both Zod exercises — ship their starter code, solution code, and hidden tests in PYTHON, not TypeScript.**

This was verified three ways:

1. `demo_data.language == "python"` on steps M1.4, M2.2, M3.2, M4.2, M4.4, M5.2, M5.3 (the capstone).
2. Visual confirmation in the live learner-facing preview — M1.4 renders `def user_to_dto(user: User) -> dict[str, object]:` with `raise NotImplementedError` in the Monaco editor inside a "TypeScript v12" course (screenshot captured during review).
3. Hidden-test inspection via the admin raw endpoint — e.g. M5.3's capstone hidden tests are `pytest` using `unittest.mock.patch`, asserting `result['ok'] is True` against a `_FakeSchema` class. Zero TypeScript.

The course Title, module titles ("Runtime Validation with Zod 3.24", "Typed fetchJson<T>"), and concept HTML all promise TypeScript. The graded artifacts are Python with a TypeScript veneer (Zod-like `.parse`/`.safeParse` mocked via a Python class).

**For a junior who will ship a zod-validated `POST /orders` in TypeScript on Monday, this course grades them on a completely different language.** Everything else in this review is secondary to that fact.

---

## Per-step grading

### M1.1 — "Why Types Fail in Real Codebases" — concept
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☑ as-vs-satisfies (teased) ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: three broken approaches (loose object, interface, type alias) with a click-through comparing them; sets up `satisfies` + Zod combo as the real fix. Content is decent but the "fix" example is hand-waved — the UI just flips a panel.
- What the step GRADES: nothing (concept step, no test).
- Gap: never demonstrates the *actual* `as const` + `satisfies` solution code inline; a junior comes away with "satisfies is good" but no muscle memory.
- Rating: ⭐⭐⭐

### M1.2 — "Model a Feature-Flag Registry with `satisfies`" — code_exercise (TypeScript)
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☑ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial (weakly) ☐ realistic capstone
- What the step TEACHES: `const FLAGS = { ... } satisfies Record<string, FlagConfig>`; the crown-jewel TS feature of this module.
- What the step GRADES: `Object.keys(FLAGS)` contains `newCheckout`/`darkMode`/`betaDashboard`; each flag's `enabled`/`rollout`/`description` has the right primitive type; `is_flag_enabled` / `get_rollout` behave on enabled/disabled/unknown inputs.
- Gap:
  - Hidden tests NEVER check that the inferred literal key type survives — a student who replaces `satisfies` with `as Record<string, FlagConfig>` (losing literal keys) passes every test. The whole point of `satisfies` is to keep autocomplete on `FLAGS.`, and the grader does not verify it.
  - Solution ships `FLAGS[name as keyof typeof FLAGS]` — an `as` cast the rubric explicitly discourages. A type-guard helper `(name): name is keyof typeof FLAGS => name in FLAGS` would be the senior answer; the course models the exact anti-pattern.
  - Function naming is Python (`is_flag_enabled`, `get_rollout`, `list_flag_keys`) in a TS file. Team style drift on day one.
- Rating: ⭐⭐

### M1.3 — "interface vs type: Which for This API?" — categorization
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: 8 scenarios sorted into `interface` / `type alias` / `either works`. Reasonable heuristics (declaration merging, union-only-in-types).
- What the step GRADES: correct category per item. No code.
- Gap: rehashes a weakly-differentiated 2021-era debate. Modern advice is "type aliases by default, interface when you need declaration merging for library augmentation" — not captured here. Generic `ApiResponse<T>` is categorized "either works" but production teams have a strong default.
- Rating: ⭐⭐⭐

### M1.4 — "Refactor: Collapse Parallel Definitions" — code_exercise (PYTHON)
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: "collapse `UserRow`/`UserDto`/`UserInput` into one canonical `User` with projection functions." Good lesson.
- What the step GRADES: `pytest` against a Python `class User` with `__init__` role-validation, `user_to_row`, `user_to_dto`, `user_from_input`. Verifies `'UserRow' not in dir(solution)` etc.
- Gap:
  - **Wrong language.** Solution is `from typing import Literal`, not TS. Junior never sees the TS idioms they actually need: `type User = Readonly<{ ... }>`, `const USER_ROLES = ['admin','editor','viewer'] as const`, `type Role = typeof USER_ROLES[number]`, `type UserDto = Omit<User,'created_at'>`.
  - A student who writes correct TS (`satisfies`, `as const`, `Readonly`) would FAIL the Python-running grader. A student who writes Python would "pass" the TypeScript course. Both outcomes are broken.
- Rating: ⭐ (unrecoverable; wrong language at a graded step)

### M2.1 — "Tagged Unions Beat Optional Fields" — concept
- Tier-1 coverage: ☑ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: before/after — optional-everywhere response type vs `{ kind: 'success'; data } | { kind: 'error'; error }`. Correct, clear.
- What the step GRADES: nothing.
- Gap: doesn't mention that `in` operator narrowing and `typeof` narrowing exist beyond discriminant-tag narrowing; doesn't discuss when a `boolean` discriminant (`ok: true | false`) is OK vs when string literals are better. Light on trade-offs.
- Rating: ⭐⭐⭐

### M2.2 — "Build a WebhookEvent Discriminated Union" — code_exercise (PYTHON)
- Tier-1 coverage: ☑ narrowing (in Python, via dict key `type`) ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: discriminated union with three webhook variants + `handleEvent` dispatcher.
- What the step GRADES: `pytest` checks `handleEvent({'type':'payment.succeeded',...})` returns a string containing the payment id. Unknown type raises `ValueError` or `KeyError`.
- Gap:
  - **Wrong language.** Solution uses `TypedDict` + `Union[...]` + `if event['type'] == ...` — Python pattern, not TS narrowing.
  - **No exhaustiveness check graded.** The course *talks* about exhaustive matching in M2.3 but this step accepts a handler with no `assertNever` fallthrough. A junior who forgets a case ships to prod; the grader is blind to it.
  - Python dicts have no `never` — the whole exhaustive-match teaching device from the rubric can't exist here.
- Rating: ⭐ (wrong language, plus misses the primary Tier-1 concept the rubric demands)

### M2.3 — "Exhaustive `assertNever` Pattern" — fill_in_blank
- Tier-1 coverage: ☑ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: `function assertNever(x: never): never { throw ... }` + filling switch cases. This is the one step that actually teaches the Tier-1 exhaustive-match pattern.
- What the step GRADES: six blanks (`x`, `never`, `never`, `validation_error`, `server_error`, `response`).
- Gap:
  - Answer alternatives for blank 0 include `"value"`, `"unreachable"`, `"impossible"` — but the body literally references `x` (`JSON.stringify(x)`), so those alternatives would be WRONG at the TypeScript level. Accepting them means the grader disagrees with the compiler. Minor but telling — the grader doesn't run tsc.
  - No actual compile step enforces the narrowing. A student could fill in a literal string and the UI scores them correct.
  - Doesn't teach the production corollary: `assertNever` is a *compile-time* check that throws at *runtime*, so junior should still log a Sentry breadcrumb before throwing (observability gap).
- Rating: ⭐⭐⭐ (the best step in the course for Tier-1, but still grader is lexical, not semantic)

### M2.4 — "Spot the Narrowing Bug" — code_review (TypeScript!)
- Tier-1 coverage: ☑ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☑ as-vs-satisfies (anti-`as any`) ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: 5 narrowing bugs in a `HealthEvent` union reducer — premature destructure before narrowing, truthy-check not narrowing, `as any` cast, wrong-scope destructure, using a possibly-undefined variable.
- What the step GRADES: student clicks which line numbers contain bugs. Correct set is `[18, 20, 24, 31, 36, 39]`.
- Gap:
  - Strong on spotting bugs — BAD on teaching the fix. The feedback mentions *what's wrong* but not the canonical repair (narrow first, destructure inside each case).
  - Bug on line 36 is `(event as any)` — good catch — but line 24 (not in the bug list explicitly, see validation file: `[18, 20, 31, 36, 39]` — note: line 24 IS called out in `bugs` but NOT in `bug_lines` validation array). There's drift between `bug_lines` and `bugs[].line` — a student who clicks 24 may be marked wrong despite the feedback explaining why it's buggy.
- Rating: ⭐⭐⭐ (solid content, grader inconsistency)

### M3.1 — "One Source, Many Shapes" — concept
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☑ zod composition (teased)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: derivation graph — `Invoice` → `Omit` → `CreateInvoiceInput`, `Partial` → `UpdateInvoicePatch`, intersection → `InvoiceRow`, `Pick` → `PublicInvoiceDto`.
- What the step GRADES: nothing.
- Gap: doesn't mention `Required<T>`, `NonNullable<T>`, `Awaited<T>`, or the distributive vs non-distributive conditional gotchas; doesn't mention `ReturnType<typeof ...>` or `Parameters<typeof ...>` which are constantly reached for in real service code.
- Rating: ⭐⭐⭐

### M3.2 — "Derive the Update Payload" — code_exercise (PYTHON)
- Tier-1 coverage: ☐ narrowing ☐ error-handling (partial) ☐ retries/timeouts ☑ zod composition (in pythonese)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: build `UpdateInvoiceInput` = `Partial<Omit<Invoice, 'id'|'createdAt'>>` + `validate_update_input` that rejects empty/forbidden payloads.
- What the step GRADES: `pytest` checking `get_type_hints(UpdateInvoiceInput)` contains only `customer`/`amount`/`lineItems`, all `NotRequired`; `validate_update_input({})` raises `EmptyUpdateError`.
- Gap:
  - **Wrong language.** Junior never sees `type UpdateInvoiceInput = Partial<Omit<Invoice, 'id' | 'createdAt'>>`. That one TS line is the primary thing this step ostensibly exists to teach.
  - No Zod. The rubric wants `z.infer<typeof Schema>` + `.pick()` / `.partial()` / `.omit()` — those are a completely different mental model from Python `TypedDict` + `NotRequired`.
- Rating: ⭐

### M3.3 — "Order the Derivation Pipeline" — ordering
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☑ zod composition (mentioned)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: order a pipeline `omit → pick → readonly → brand → export → validate`. Introduces branded types (`id: UserId`).
- What the step GRADES: sequence matches expected array.
- Gap: branded-types is the first time they appear in the course, with zero scaffolding. A junior will see `ReadonlyProfile & { id: UserId }` and not know how to *construct* a `UserId` safely (`declare const brand: unique symbol; type UserId = string & { [brand]: 'User' }`). Rote-memory exercise; no code written.
- Rating: ⭐⭐

### M3.4 — "When NOT to Derive" — mcq
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☑ zod composition (meta)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: don't derive when the composition spans three unrelated types — name it instead.
- What the step GRADES: pick option 1 (the three-type intersection).
- Gap: good intuition pump, but it's 1-of-4 and the answer is obvious from length alone. No depth.
- Rating: ⭐⭐⭐

### M4.1 — "Zod at the Boundary, TS Inside" — concept
- Tier-1 coverage: ☐ narrowing ☑ error-handling (teased) ☐ retries/timeouts ☑ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: validate at the three boundaries — request bodies, external APIs, env vars. Accurate and exactly the right framing for service-layer dev.
- What the step GRADES: nothing.
- Gap: doesn't show an `envSchema = z.object({ DATABASE_URL: z.string().url(), PORT: z.coerce.number().int().positive() })` snippet. Doesn't mention the `.openapi()` / `zod-to-openapi` angle which 90% of production teams adopt. The concept is strong; the scaffolding to execute it is absent.
- Rating: ⭐⭐⭐⭐

### M4.2 — "Compose a Nested CheckoutSchema" — code_exercise (PYTHON)
- Tier-1 coverage: ☑ narrowing (via tag) ☐ error-handling ☐ retries/timeouts ☑ zod composition (nominally)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: nested `Checkout { customer, items[], shipping, payment: Card | Bank | Wallet }` with `CheckoutSchema.parse()` / `.safeParse()`.
- What the step GRADES: `pytest`. `parse_checkout({...card payment...}).payment.paymentMethod == 'card'`. `parse_checkout({missing customer})` raises `ValidationError`.
- Gap:
  - **Wrong language.** This is the most egregious case — the lesson explicitly promises "Zod 3.24" and the solution has a hand-rolled Python `class CheckoutSchema: @staticmethod def parse(data): ...`. Zero Zod.
  - No `z.discriminatedUnion('paymentMethod', [CardSchema, BankSchema, WalletSchema])` — which is *the* thing a junior needs to know to ship production Zod.
  - No `z.infer<typeof CheckoutSchema>` demonstration.
  - Hidden tests grade implementation behavior, not the schema shape, so a student could conceivably write an if-tree with no real structural validation and pass.
- Rating: ⭐ (language failure + misses the exact Zod composition lesson it promises)

### M4.3 — ".parse vs .safeParse" — scenario_branch
- Tier-1 coverage: ☑ narrowing ☑ error-handling ☐ retries/timeouts ☑ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☑ error surface (implied) ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: three scenarios — Express handler (`.safeParse` → HTTP 400), queue consumer (`.safeParse` → log & continue), startup env (`.parse` → fail fast). Correct and well-framed.
- What the step GRADES: MCQ per scenario.
- Gap:
  - No code. A junior remembers "parse for startup" but doesn't build the muscle of `const result = Schema.safeParse(req.body); if (!result.success) return res.status(400).json({ errors: result.error.issues });`.
  - Doesn't teach the `result.error.format()` vs `result.error.flatten()` vs `.issues` distinction — the #1 ZodError-to-HTTP-response footgun.
- Rating: ⭐⭐⭐⭐ (excellent intuition pump, held back by no code and no ZodError surface teaching)

### M4.4 — "Refinements & Transforms" — code_exercise (PYTHON)
- Tier-1 coverage: ☐ narrowing ☐ error-handling ☐ retries/timeouts ☑ zod composition (pythonese)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☑ error surface ☐ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: `.refine()` (items non-empty), `.transform()` (lowercase email), cross-field (country ↔ currency).
- What the step GRADES: Python `validate_checkout({...})` returns parsed dict with lowercased email; raises `CheckoutValidationError` with an `errors: list[str]` attribute.
- Gap:
  - **Wrong language.** No actual `z.object({...}).refine(data => data.items.length > 0, { message: ... })` or `.transform(v => v.toLowerCase())`.
  - Never shows `superRefine` — the right tool for cross-field error attribution (attaches issues to specific paths so the client can highlight the offending field).
  - `errors: list[str]` loses path information; real Zod issues are `{ code, path, message }`. Junior learns a weaker model than what production needs.
- Rating: ⭐

### M5.1 — "Designing Result<T,E> for HTTP" — concept
- Tier-1 coverage: ☑ narrowing ☑ error-handling ☑ retries/timeouts (mentions timeout as an error kind) ☑ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☑ generics
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: `Result<T,E>` + the four-variant `ApiError` (`network`, `timeout`, `http`, `validation`) with diagnostic payloads. This is the single best piece of content in the course.
- What the step GRADES: nothing.
- Gap: doesn't mention idempotency, no `Idempotency-Key` header pattern, no mention of `AbortController` plumbing at the teaching level (though M5.4 cameo's it as a bug). The concept is 80% there; the execution in M5.3 destroys it.
- Rating: ⭐⭐⭐⭐ (content-wise — but sets up a promise M5.3 breaks)

### M5.2 — "Warm-up: Result Helpers" — code_exercise (PYTHON)
- Tier-1 coverage: ☑ narrowing ☐ error-handling ☐ retries/timeouts ☐ zod composition
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☐ error surface ☑ generics (Python `Generic[T]`)
- Tier-3 coverage: ☐ observability ☐ pinning ☐ test adversarial ☐ realistic capstone
- What the step TEACHES: `ok(v)` / `err(e)` / `is_ok` / `is_err` type guards.
- What the step GRADES: Python `pytest`. `ok(42).value == 42`, `is_ok(err('x')) is False`, falsy preservation.
- Gap:
  - **Wrong language.** Junior never writes `function isOk<T,E>(r: Result<T,E>): r is { ok: true; data: T } { return r.ok === true; }` — the TS user-defined type guard is a distinct skill not transferable from `TypeGuard[Ok[T]]`.
- Rating: ⭐⭐ (concept is right, language is wrong)

### M5.3 — "Capstone: Ship fetchJson<T>" — code_exercise (PYTHON) — **THE CAPSTONE**
- Tier-1 coverage: ☑ narrowing ☑ error-handling (all 4 branches graded!) ☐ retries/timeouts ☐ zod composition (uses `.parse` stub)
- Tier-2 coverage: ☐ as-vs-satisfies ☐ async hygiene ☑ error surface ☑ generics (nominal)
- Tier-3 coverage: ☐ observability ☐ pinning ☑ test adversarial ☐ realistic capstone
- What the step TEACHES: one function, five branches — timeout → `timeout` kind, network error → `network` kind, HTTP >= 400 → `http` kind, JSON parse failure → `parse` kind, schema failure → `validation` kind, else `ok`.
- What the step GRADES: Python `pytest` with `unittest.mock.patch.object(solution, '_http_get', ...)` driving every branch. The tests are actually well-designed — they distinguish `parse` vs `validation` (good adversarial coverage: a student who collapses them would fail). `must_contain` lints for `except _TimeoutError:`, `except _NetworkError:`, `status >= 400`, `schema.parse(`, `return ok(`.
- Gap:
  - **The capstone is written in Python.** The signature a junior is promised — `async function fetchJson<T>(url: string, schema: z.ZodType<T>, options: { timeout?: number; retries?: number; signal?: AbortSignal } = {}): Promise<Result<T, ApiError>>` — is not what they build. They build `def fetch_json(url, schema, timeout_ms=5000, init=None) -> dict`.
  - **No retries.** The "production retries" rubric item — timeouts? no actual `setTimeout` abort plumbing, no `AbortController.abort(new TimeoutError())`; just a `timeout_ms` param that does nothing (`_http_get` is patched by tests). Retries are not implemented, not graded, not even in the TODO list.
  - **No idempotency, no backoff, no jitter, no `Retry-After` header handling.**
  - **No generic constraint.** Rubric asked for `<T extends z.ZodType>` — there's nothing generic at all; `schema: Any`.
  - **Result is a dict, not a discriminated type.** `{'ok': True, 'data': ...}` has no type-level safety. The Tier-1 teaching vehicle (discriminated union + exhaustive match) is absent.
  - **Cannot `z.infer<typeof Schema>`.** Because there's no Zod.
- Rating: ⭐ (tests are solid within their Python universe; the capstone does not prepare a junior for the real signature)

### M5.4 — "Post-Mortem: Trade-offs You Made" — code_review (TypeScript)
- Tier-1 coverage: ☑ narrowing ☑ error-handling ☑ retries/timeouts ☑ zod composition
- Tier-2 coverage: ☑ as-vs-satisfies (anti-patterns shown) ☑ async hygiene ☐ error surface ☑ generics
- Tier-3 coverage: ☑ observability (implicit) ☐ pinning ☑ test adversarial ☐ realistic capstone
- What the step TEACHES: review a real TS `fetchJson<T>` implementation; spot 4 bugs — unbounded `schemaCache` (memory leak), unstable `schema.toString()` cache key, returning inside retry loop on 4xx/5xx without breaking it, `AbortController` event-listener leak.
- What the step GRADES: click the correct line numbers `[9, 20, 24, 35]`.
- Gap:
  - **This step is the only place a junior sees production-grade TS `fetchJson<T>` code. It comes AFTER the capstone they "built" in Python.** Pedagogically backwards: expose the target signature BEFORE asking them to build it.
  - The bugs are good (real production bugs), but the student never FIXES them — no code-exercise follow-up. Awareness without muscle memory.
  - Exponential backoff mentioned but not graded for correctness (constant `Math.pow(2, attempt) * 1000` has no jitter — that's another bug not flagged).
- Rating: ⭐⭐⭐ (good content, wrong position in the course, no active practice)

---

## Final verdict

### Per-tier scores (1-5)

| Tier | Score | Reasoning |
|------|-------|-----------|
| **Tier 1 — non-negotiable production concerns** | **1.5 / 5** | Narrowing is covered in two steps (2.3 well, 2.4 OK). Error-handling completeness exists in concept (5.1) and grading (5.3) — but the graded code is Python. Retries/timeouts: *zero* real coverage — capstone doesn't implement, doesn't test. Zod composition: the two Zod exercises (4.2, 4.4) are Python mocks of Zod, not Zod. |
| **Tier 2 — junior footguns** | **2 / 5** | `satisfies` gets one exercise (1.2) but the solution itself uses an `as` cast. Async hygiene: touched only in 5.4 review (not practiced). ZodError surface: never graded, never shown in code — biggest single concrete production gap. Generics teaching: rubric asked "does fetchJson<T> teach generic constraints?" — no, because it's Python. |
| **Tier 3 — production readiness** | **1 / 5** | Observability: never mentioned. Version pinning: never mentioned. Tests adversarial: M5.3 tests are well-designed adversarial (+), but they grade Python. Realistic capstone: the signature a junior ships on Monday is not the one they built. |

### Top 3 production gaps (what a junior learns the hard way on the job)

1. **The entire Zod / TS / Result<T, ApiError> muscle memory.** A junior who finishes this course has never typed `z.object({...})`, `z.discriminatedUnion(...)`, `z.infer<typeof ...>`, `Schema.safeParse(body)`, `result.error.issues`, or `Result<T, E>` in TypeScript. They've typed the Python analogues. On Monday they'll `z.object({ email: z.string() })` and hit the first type error they've never seen.
2. **Retry / timeout / abort plumbing.** No step implements an `AbortController`, no `setTimeout(() => controller.abort(), timeoutMs)`, no 429 `Retry-After`, no exponential backoff with jitter, no idempotency-key pattern. Tuesday's page is a 429 storm because the junior hand-rolled `for (let i=0; i<3; i++) { try { ... } catch {} }` with no jitter and hammered an upstream.
3. **ZodError → HTTP 400 response shape.** M4.3 says "return HTTP 400" but never shows `res.status(400).json({ errors: result.error.issues.map(i => ({ path: i.path.join('.'), message: i.message })) })`. Every B2B SaaS team has a house style for this; the junior will ship `res.status(400).json(result.error)` and leak the full Zod internal structure to the API consumer.

### Top 2 strongest aspects

1. **M5.1 conceptual framing of `Result<T, ApiError>` with a 4-variant union.** Correctly names `network`, `timeout`, `http`, `validation` as distinct kinds with diagnostic payloads. This is exactly the framing a senior would use on a whiteboard.
2. **M5.3 hidden-test adversarial design.** Within its (Python) universe, the capstone tests actually distinguish `parse` vs `validation` failure — a student collapsing them to "something went wrong" fails. `must_contain` checks on specific `except` clauses prevent gaming. This is the one place the grading is better than a typical course — if only it were in TypeScript.

### Verdict: ❌ **REJECT**

Not because the pedagogical *shape* is wrong — M5.1's `Result<T, ApiError>` framing and M5.3's adversarial test design are both above average. But a **"TypeScript v12: Types, Zod, API Clients"** course that hands a junior Python for 7 of 10 exercises, including the capstone and both Zod exercises, is not a TypeScript course. It is a typed-Python course with a TS veneer on the concept HTML and two `code_review` steps. A junior who completes it and ships TypeScript on Monday has the *concepts* but zero reps of the actual syntax, idioms, and footguns (`as const`, `satisfies`, user-defined type guards, `z.infer`, `z.discriminatedUnion`, `ZodError.issues`, `AbortController`, exhaustive `never` checks enforced by tsc).

This is not a "conditional ship with supplements" situation because the broken axis is the language of instruction itself — you'd have to replace the graded artifact of nearly every exercise, at which point you've written a new course. Send it back to the Creator pipeline with the diagnosis: the `language` field in `demo_data` is being set inconsistently (`ts` on M1.2 and M2.4 and M5.4, `python` everywhere else) and the solution generator followed the wrong branch on seven steps.

### One-sentence hot take

It's a well-designed TypeScript syllabus whose graded exercises were filled out by a Python pipeline — ship the Python version to a "Types, Zod-likes, API Clients in Python" course and regenerate this one with the language pin set correctly.
