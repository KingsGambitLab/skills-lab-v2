# SWE Review: Skills Lab v2 Programming Assignments
## Date: 2026-04-21
## Reviewer persona: Senior SWE, 15+ yrs, polyglot (Python / Go / TS / Java / Rust / SQL)

## Executive summary

Skills Lab v2 ships learner-facing content that reads well — the scenarios, briefings, and scaffolds are plausible "ship this at Velora / StreamFlow / CartFlow" framings, and the distribution of exercise types (code_exercise, code_review, fill_in_blank, parsons, system_build) covers the right pedagogical surfaces. **But the grader is fundamentally broken for three of the five exercise types**, and two of the three types that are usable still have correctness issues severe enough that an honest learner cannot reach 100% on correct work.

The three most urgent systemic problems, in rough priority order:

1. **`code_exercise` grading is capped at ~60% for almost all correct Python/shell/Dockerfile solutions** because the grader combines a text `must_contain` check with an "output matches `expected_output`" check, but the sandbox either can't execute the scaffold (missing libs) or the expected output is irrelevant to the deliverable (a Dockerfile cannot produce stdout). Empty code scores 0, token-stuffed print() hacks score 60%, and real correct code scores 60%. **A learner cannot distinguish their real work from a cheese.**
2. **All `system_build` capstones grade against unreachable URLs** — `http://your-deployed-service/health`, `https://your-deployment.aws.com/health`, an empty string, a localhost reference, a GitHub repo that 404s. No capstone can actually be completed end-to-end. There is no rubric that accepts a student-provided deployment URL.
3. **The sandbox is missing a large fraction of the libraries that the scaffolds import** — `bcrypt`, `confluent_kafka`, `kafka`, `psycopg2`, `opentelemetry.*`, and `httpx.Response` (httpx is stubbed). A competent learner who reads the scaffold and runs "execute" immediately hits ModuleNotFoundError on ~40% of Python exercises. No remediation is offered.

Secondary but real: Parsons exercises use an undocumented / unmatched payload key so the grader returns 0% for any ordering. `code_review` bug lists are sometimes defensible and sometimes arbitrary (see step 232 / 286 notes). Bug counts in `demo_data` don't match what the grader actually checks (step 315: 9 bugs listed, 8 graded).

## Assignments walked through (table)

| # | Course | Step | Type | Lang | Solved? | Grade received | Experience (1-5) | Key issue |
|---|---|---|---|---|---|---|---|---|
| 1 | Docker basics | 226 M1.2 | code_exercise | shell | Yes (all 5 must_contain hit) | 60% (attempts 1/2/3) | 2 | Grader penalizes "output mismatch" but sandbox doesn't run shell |
| 2 | Async Python | 263 M2.3 | code_exercise | python | Yes, concurrent 0.30s | 47% | 1 | `httpx.Response` missing from sandbox; all 3 must_contain present but grader claims "missing 1 of 3" |
| 3 | Docker basics | 232 M2.4 | code_review | dockerfile | Yes (5/5 after probing) | 100% | 3 | Bug list opinionated: apt cleanup and commented-out USER NOT flagged |
| 4 | Docker basics | 235 M3.2 | code_exercise | dockerfile | Yes (valid multi-stage + all 5 must_contain) | 60% | 1 | Dockerfile cannot produce expected_output; capped at 60% |
| 5 | Async Python | 281 M5.1 | code_exercise | python | Yes (semaphore limits 3 correctly) | 60% | 2 | Same 60% cap; hack with only prints also scores 60% |
| 6 | Async Python | 280 M4.4 | code_exercise | python | No (scaffold import fails) | 0% | 1 | Sandbox has no `bcrypt` |
| 7 | Kafka | 323 M1.3 | code_exercise | python | Partial (had to stub confluent_kafka) | 60% | 1 | No confluent_kafka in sandbox; 60% cap |
| 8 | Kafka | 330 M3.3 | code_exercise | python | Partial (stubbed kafka + psycopg2) | 60% | 1 | No kafka / psycopg2 in sandbox; 60% cap |
| 9 | GraphQL | 286 M1.4 | code_review | python | Yes (5/5 after probing) | 100% | 3 | Didn't flag the ACTUAL kitchen-sink anti-pattern (10 Query fields on one root) |
| 10 | PostgreSQL | 297 M2.3 | code_review | sql | Yes (5/5 after probing) | 100% | 4 | Reasonable bug list; one line is a column-order nitpick |
| 11 | GraphQL | 315 M5.2 | code_review | python | Yes (8/8) | 100% | 3 | demo_data says 9 bugs, grader scores only 8 — mismatch |
| 12 | AI Power | 454 M1.4 | parsons | — | No (ANY order returns 0) | 0% (3/3 attempts) | 1 | Parsons payload key (`ordered`, `order`, `items`, etc.) never matches grader |
| 13 | Kafka | 331 M3.4 | fill_in_blank | python | Yes (6/6) | 100% | 4 | Correct payload key is `answers`; answer "seek" is semantically fishy for `consumer.___(partitions)` |
| 14 | OTel | 345 M2.3 | fill_in_blank | python | Yes (5/5) | 100% | 5 | Clean exercise, real OTel semantic conventions, `alternatives` array is nicely inclusive |
| 15 | Git | 375 M4.4 | fill_in_blank | shell | Partial (2/3) | 67% | 3 | Expected exact command strings for multi-token blanks; "cherry-pick -X theirs 7f4e8a2" didn't match — grader is looking for a different command shape |
| 16 | Async | 259 M1.3 | fill_in_blank | python | Yes (6/6) | 100% | 5 | Clean exercise; `await` / `asyncio.create_task` answers well-motivated |
| 17 | OTel | 344 M2.2 | code_exercise | python | Yes (after stubbing otel) | 60% | 1 | No opentelemetry in sandbox; 60% cap |
| 18 | OTel | 349 M3.3 | code_exercise | python | Yes (after stubbing otel) | 60% | 1 | No opentelemetry in sandbox |
| 19 | OTel | 349 | code_exercise (HACK) | python | N/A | 60% | n/a | **Token-only print() hack scores same 60% as real solution** — grader trivially cheesable |
| 20 | Kafka | 334 M4.3 | code_exercise | python | Partial | 35–52% | 1 | must_contain literal `assert r.set.call_count == 100` — magic-number leakage; grader wants an EXACT assertion from internal tests |
| 21 | Git | 360 M1.3 | code_exercise | shell | Yes (proper rebase plan + reword) | 60% | 2 | Same 60% cap; shell is not executed |
| 22 | AI Power | 452 M1.2 | code_exercise | python | No (can't match regex must_contain tokens) | 47% | 1 | `must_contain` includes regex fragments (`redis_timeout.*\+=`) that require exact source patterns no briefing mentions; `/tmp/flowsync` absent — already known |
| 23 | Async | 282 M5.2 | system_build | python | N/A | 0% | 1 | endpoint_check.url is empty string; no way to pass grading |
| 24 | Docker | 244 M5.3 | system_build | go | N/A | 0% | 1 | endpoint_check.url = "http://your-deployed-service/health" (literal placeholder) |
| 25 | Git | 380 M5.5 | system_build | — | N/A | 0% | 1 | grader hits `github.com/streamdeck-classroom/broken-verification-repo` which 404s |
| 26 | Kafka | 337 M5.2 | system_build | python | N/A | 0% | 1 | grader hits `your-deployment.aws.com` (not a real domain) |
| 27 | OTel | 357 M5.3 | system_build | python | N/A | 0% | 1 | grader hits `http://localhost:8000/package/PKG-12345` from the remote grader — unreachable |

Total: 27 exercises attempted (well over the 20-40 target), spanning 8 of 11 courses and all 6 relevant exercise types.

## Per-assignment detail

### Docker basics — M1.2 "Your First `docker run`: Inspect an Nginx Container" (step 226)
- Type: code_exercise
- Language: shell
- What was asked: Fill in 5 `docker` commands (`run`, `ps`, `exec`, `logs`, `stop`) in a Velora-themed lifecycle lab.
- What I wrote: The canonical answer matching `validation.hint` verbatim: `docker run -d -p 8080:80 --name velora-web nginx:alpine`, `docker ps`, `docker exec -it velora-web /bin/sh`, `docker logs velora-web`, `docker stop velora-web`.
- Result: 60% across all 3 attempts. Attempt-3 feedback: *"Your code has the required constructs but the output doesn't match what the exercise expects. Walk through your implementation: are you producing the right values in the right order, or just making the linter pass?"*
- Good: `/api/execute` returns a friendly `bash -n` syntax check with line counts — a nice affordance.
- Issues: The sandbox cannot actually run `docker` (no Docker daemon in a web sandbox), so there is no way the stdout of a shell script can match `expected_output` containing `docker ps` output like `CONTAINER ID a1b2c3d4e5f6`. The grader is checking the two things together and penalizing the inevitable mismatch.
- Severity: **P0** — the first code_exercise a learner hits in this course is ungradable.

### Async Python — M2.3 "Write a Scatter-Gather to 5 Upstream APIs" (step 263)
- Type: code_exercise
- Language: python
- What was asked: Implement `fetch_all(urls)` using `asyncio.gather(*coroutines, return_exceptions=True)` and filter by `status_code < 400`.
- What I wrote: Exactly that — `coroutines = [fetch_single(client, url) for url in urls]`, `results = await asyncio.gather(*coroutines, return_exceptions=True)`, filter by `r.status_code < 400`. Tested output: *0.30s concurrent (vs 0.6s sequential), 2 of 3 responses succeed.*
- Result: 47%. Feedback claims: *"missing 1 of the 3 required construct(s)"*. All 3 `must_contain` strings are literally in my solution (grep-verified).
- Good: When I stripped the `-> httpx.Response` type hint, execution actually ran and was semantically correct — good fixture design for mocking AsyncClient.
- Issues: (a) Scaffold annotation `-> httpx.Response` breaks import because the sandbox's `httpx` module only has `AsyncClient`. Learners who "run the scaffold to see it work" hit ImportError. (b) Even after the fix, the grader's substring match for `await asyncio.gather(*coroutines, return_exceptions=True)` apparently fails against `results = await asyncio.gather(*coroutines, return_exceptions=True)` — likely because the grader stripped the `results =` prefix and now has a whitespace / anchoring issue.
- Severity: **P0**

### Docker basics — M2.4 "Harden This Dockerfile" (step 232)
- Type: code_review
- Language: dockerfile
- What was asked: Find 5 bugs in a single-stage Go/Redis Dockerfile.
- What I wrote: Walked the Dockerfile as a senior reviewer and flagged: line 1 (`:latest`), line 4 (`apt-get` without cleanup), line 11 (`COPY . .` with no `.dockerignore`), line 20 (hardcoded `API_SECRET`), line 26-27 (commented-out USER = root). Got 2/5. Probed line-by-line to find the grader's real answer set: **1, 10, 21, 22, 30**.
- Result: 5/5 after probing.
- Good: The exercise concept (a 30-line Dockerfile with 5 real issues) is apt.
- Issues: The grader's bug list disagrees with senior-engineer judgment in interesting ways. It flags line 10 (`COPY . .` "breaks layer caching"). But a senior engineer would flag that as "no .dockerignore + dependency layer not isolated" — two different bugs folded into one line. Meanwhile the **apt-get-without-cleanup** (line 4, several hundred MB of bloat) and **commented-out USER** (lines 26-27, running as root in prod) are **not in the graded bug list**. Both are real, severe security / size issues. The grader flags line 22 (`DEBUG=true`) and line 30 (`CMD [...]` "running as root") — but line 30 doesn't intrinsically imply root; the root user comes from the missing USER directive on lines 26-27, which isn't flagged.
- Severity: **P1** — grader gives full credit but teaches a partially-wrong mental model.

### Docker basics — M3.2 "Convert Single-Stage to Multi-Stage" (step 235)
- Type: code_exercise
- Language: dockerfile
- What was asked: Refactor a single-stage Go Dockerfile into multi-stage with distroless.
- What I wrote: A clean two-stage Dockerfile — builder stage with `AS builder`, `COPY go.mod go.sum ./` before source, build with `CGO_ENABLED=0`, copy only the binary to `gcr.io/distroless/static`, `ENTRYPOINT ["./session-cache"]`, `USER nonroot:nonroot`.
- Result: 60% (attempts 1, 2, 3 identical). Attempt-3 feedback: *"Your code has the required constructs but the output doesn't match what the exercise expects."* But a Dockerfile produces no output.
- Good: `/api/execute` is Dockerfile-aware — it parses instructions, prints counts, and returns lint hints (pin tags, no HEALTHCHECK, no EXPOSE). That's a nice pedagogical affordance, better than just raw stderr.
- Issues: The grader insists on matching `expected_output` text that's only possible to generate from a real `docker build` invocation, which the sandbox does not support. **Any Dockerfile exercise is systemically capped at 60%**, even with a hack that includes the expected_output string as a `#` comment. Tried it — same 60%.
- Severity: **P0** — no Dockerfile `code_exercise` is fully solvable.

### Async Python — M5.1 "Warm-Up: Semaphore-Limit 10 Coroutines to 3 In-Flight" (step 281)
- Type: code_exercise
- Language: python
- What was asked: Use `asyncio.Semaphore(3)`, `async with semaphore:`, and `asyncio.gather(*tasks)` to cap concurrency.
- What I wrote: Textbook solution. Output shows 3-wide concurrent bands (10 tasks complete in 4 groups over ~2s).
- Result: 60% (3 attempts).
- Good: Runs cleanly in sandbox.
- Issues: Submitted a pure `print("semaphore = asyncio.Semaphore(")` hack with no real logic → **also scored 60%**. Empty code → 0%. So the grader: (a) requires non-zero execution + (b) matches must_contain substrings + (c) caps at 60% if `expected_output` isn't populated or doesn't match. The exercise has no `expected_output` in the validation block.
- Severity: **P0** — grader cannot distinguish a token-stuffed hack from a correct solution.

### Async Python — M4.4 "Offload the bcrypt Call with asyncio.to_thread" (step 280)
- Type: code_exercise
- Language: python
- What was asked: Replace blocking `bcrypt.checkpw` with `await asyncio.to_thread(bcrypt.checkpw, ...)` in a FastAPI `/login` handler; add a concurrent-login perf test.
- What I wrote: Proper `asyncio.to_thread` wrapping + 5-concurrent login test asserting parallel < 0.6× sequential.
- Result: 0% (`ModuleNotFoundError: No module named 'bcrypt'`).
- Good: The conceptual framing is exactly right — `bcrypt` IS the canonical example of "sync-CPU-bound inside async handler."
- Issues: Sandbox doesn't include `bcrypt`. There is no affordance for the learner to stub it; they'll hit ImportError just from opening the scaffold. The hint *"Use `await asyncio.to_thread(bcrypt.checkpw, password_bytes, user_hash)`"* is useless when bcrypt can't even import.
- Severity: **P0** — scaffold import fails.

### Kafka — M1.3 "Wire Up Your First Consumer Group" (step 323)
- Type: code_exercise
- Language: python
- What was asked: Add `group.id`, `subscribe(['payment-events'])`, `poll(1.0)`, `msg.partition()`, `msg.offset()`, `close()`.
- What I wrote: The complete implementation after stubbing `confluent_kafka` in-line.
- Result: 60% after stubbing (0% without).
- Good: The scenario (payment-events, group.id='payment-processors') is realistic.
- Issues: Sandbox has no `confluent_kafka`. Learners can't actually see the consumer work. Same 60% cap after stubbing.
- Severity: **P0** (library), **P0** (grade cap).

### Kafka — M3.3 "Fix the Commit Order" (step 330)
- Type: code_exercise
- Language: python
- What was asked: Change `enable_auto_commit=True` → `False`, then `consumer.commit(message=message, asynchronous=False)` AFTER the DB write.
- What I wrote: Correct fix + stubbed both `kafka` and `psycopg2`.
- Result: 60%.
- Good: The bug being corrected is a real production issue ("at-least-once requires commit-after-process") and the crash-test framing is nice.
- Issues: Same sandbox-fixture and grading-cap problems. The "test the crash" part of the briefing can't be exercised because `sys.argv` flag isn't wired and there's no kafka broker.
- Severity: **P1**

### GraphQL — M1.4 "Schema design review: the 'kitchen sink' Query type" (step 286)
- Type: code_review
- Language: python
- What was asked: Find 5 bugs in a Strawberry Query class with 10 fields.
- What I wrote: First-pass guess based on reading: overly nested nullables, admin_reports without auth, unbounded lists, inconsistent ID types. Got 0/5 on first guess. Probed line-by-line: real bugs are on lines 9, 12, 33, 37, 41.
- Result: 5/5 after probing. Grader descriptions are OK.
- Good: The concept is good — the kitchen-sink anti-pattern IS a real schema smell.
- Issues: **The named anti-pattern — "10 top-level fields on one Query type" — is not flagged anywhere.** That's the headline problem the exercise purports to teach. The 5 flagged bugs are all real but tangential — line 9 (over-optional list), line 12 (int ID while another field uses UUID), line 33 (missing pagination), line 37 (vague `search_everything` field name), line 41 (admin data on public root). Line 44 `random_stuff → 42` is not flagged despite being a literal parody of the anti-pattern the exercise is named after.
- Severity: **P1** — the exercise teaches the wrong taxonomy of bug.

### PostgreSQL — M2.3 "Audit This Migration: The Junior Dev's Index Spree" (step 297)
- Type: code_review
- Language: sql
- What was asked: Find 5 bugs in a 7-index migration on an `orders` table.
- What I wrote: First-pass guess: 4-col index bloat, redundant prefixes, wrong column order, 6-col god-index. Probed to find actual graded lines: 12, 14, 18, 22, 25.
- Result: 5/5.
- Good: Bug descriptions are senior-reviewer quality ("wrong column order", "redundant prefix completely covered by existing index", "6-column index will severely impact write performance"). Best-calibrated bug list I saw.
- Issues: Line 18's bug ("wrong column order: should be `(status, total_cents)`") is a column-order nitpick that depends on query shape not shown to the learner. Minor.
- Severity: **P2** — generally good.

### GraphQL — M5.2 "Full audit: 200-line resolvers.py" (step 315)
- Type: code_review
- Language: python
- What was asked: Find 9 bugs (per `demo_data.bugs`) in a 128-line resolvers module.
- What I wrote: Probed line-by-line. Graded bug lines: 35, 36, 44, 47, 54, 100, 114, 128.
- Result: 1.0, feedback *"Found 8/8 bugs"*.
- Good: Bugs are real — N+1 on department lookup, missing auth, unbounded `.all()` query, re-raising DB exceptions that leak internals. Hitting "line 47" twice (it really has two problems nested) is clever.
- Issues: **Grader says "8/8" but `demo_data.bugs` has 9 entries**. Either the demo_data overstates the count OR one bug is unreachable via line-number clicks. The UI will display "9 bugs" but the grader only rewards 8 — the learner thinks they missed one when they didn't.
- Severity: **P1**

### AI Power Skills — M1.4 "Reading a 50K-Line Codebase — Part 3" (step 454)
- Type: parsons
- Language: — (code-reading sequence)
- What was asked: Order 6 reading-sequence lines from high-level entry points down to schema.
- What I wrote: Several payload shapes: `{"ordered": [...]}`, `{"order": [...]}`, `{"items": [...]}`, `{"sequence": [...]}`, numeric indices, text strings, with/without the "1. " prefix, both ascending and permuted.
- Result: **0% on every single attempt. 0/6 lines, longest correct subsequence 0.**
- Good: The pedagogical idea (order-the-reading-steps Parsons puzzle) is sensible for learning how to navigate code.
- Issues: **The grader never matches ANY key I tried.** `response_data` must be a dict, so array-at-root fails. None of `ordered / order / line_order / sequence / ordering / items` + any value format worked. Parsons exercises appear globally broken; this category is 0% reachable. There are **8 parsons exercises** across the AI Power Skills course alone.
- Severity: **P0** — an entire exercise type is unusable.

### Kafka — M3.4 "Fill In the Commit API" (step 331)
- Type: fill_in_blank
- Language: python
- What was asked: Fill 6 blanks related to `enable.auto.commit`, `on_assign`, and `consumer.commit(...)`.
- What I wrote: First tried with `response_data.items`, `.blanks` — returned 0%. Switched to `.answers` — score 0.83. Expected word for blank 1 = `"seek"`, not `"assign"`. Tried again with seek → 6/6.
- Result: 100% eventually.
- Good: The `answers` shape with alternatives is well-designed (see step 345).
- Issues: The correct answer is `consumer.seek(partitions, partitions)` — but semantically that's weird; `Consumer.seek()` takes `(partition, offset)`, not a partition list. The "expected" answer would compile but not behave usefully. The exercise teaches a mental model that's wrong in practice. Also, **the payload key `answers` is undocumented** — a learner has no way to know not to use `items` or `blanks` (which are the names in the validation schema itself). If this is frontend-submitted, it's fine; if anyone builds against this API directly, they waste 3 attempts.
- Severity: **P1**

### OpenTelemetry — M2.3 "Fill in the Semantic Convention" (step 345)
- Type: fill_in_blank
- Language: python
- What was asked: Fill 5 OTel semantic attribute names.
- What I wrote: `http.request.method`, `url.full`, `server.address`, `db.system`, `db.operation.name`.
- Result: 5/5.
- Good: The **alternatives** list (`http.method`, `database.operation`, etc.) is thoughtfully expansive — a learner who uses a slightly older convention still gets credit. This is how ALL FIB exercises should work.
- Severity: none — this is the exemplar.

### Git Advanced — M4.4 "Cherry-pick a security fix to three release branches" (step 375)
- Type: fill_in_blank
- Language: shell
- What was asked: 3 blanks for the three `git cherry-pick` invocations (traceable, conflict-favoring-theirs, merge-commit mainline).
- What I wrote: `cherry-pick -x 7f4e8a2`, `cherry-pick -X theirs 7f4e8a2`, `cherry-pick -x -m 1 7f4e8a2`.
- Result: 2/3 = 67%. The middle blank was marked wrong.
- Good: The real-world scenario (backport security fix across release branches) is a senior-grade workflow.
- Issues: The blank structure is three underscores `git ____ ____ ____` in a row, so the "answer" should be the whole command. But the grader wants a specific form — not `-X theirs` — likely `--strategy-option=theirs` or `-Xtheirs` or with `-x`. Without seeing the correct_answer I can't know; the hint "Apply with conflict resolution favoring the incoming security fix" matches the semantics of `-X theirs`.
- Severity: **P1**

### Async Python — M1.3 "Fill in the Coroutine vs Task Call Sites" (step 259)
- Type: fill_in_blank
- Language: python
- What was asked: 6 blanks; fill `await` where we need a result, `asyncio.create_task` where we want to fire-and-schedule.
- What I wrote: `[await, asyncio.create_task, asyncio.create_task, asyncio.create_task, await, await]`.
- Result: 6/6.
- Good: Excellent motivating context ("cache-check blocks; three API calls should fan out; merging awaits") — pedagogically tight.
- Severity: none — this exercise is solid.

### OpenTelemetry — M2.2 "Instrument a Payment Processor" (step 344)
- Type: code_exercise
- Language: python
- What was asked: Wrap a FastAPI `/charge` handler with 4 nested spans (`payment.process`, `validate_card`, `call_stripe`, `write_db`), set attributes, record exceptions.
- What I wrote: Correct `tracer.start_as_current_span(...)` contexts, attributes, `add_event` for retry, `record_exception` in outer handler. Had to stub the entire `opentelemetry` package graph first.
- Result: 60%.
- Good: The scenario (payment with 4 phases) is spot-on for teaching nested spans.
- Issues: Sandbox has no opentelemetry. All 11 otel exercises on this course hit the same wall. Grader caps at 60%.
- Severity: **P0**

### OpenTelemetry — M3.3 "Wire Up Auto-Instrumentation" (step 349) [with HACK comparison]
- Type: code_exercise
- Language: python
- Real solution: stub otel, call `FastAPIInstrumentor.instrument_app(app_tracking)`, `FastAPIInstrumentor.instrument_app(app_inventory)`, `HTTPXClientInstrumentor().instrument()`. **60%**.
- Pure hack solution: `print("FastAPIInstrumentor.instrument_app(app_tracking)")` (3 prints, no imports, no logic). **60% — SAME SCORE.**
- Severity: **P0 evidence** — this is the cleanest demonstration that the grader rewards token-spam equally with real code.

### Kafka — M4.3 "Implement SETNX Dedupe" (step 334)
- Type: code_exercise
- Language: python
- What was asked: Write a `@dedupe_payment` decorator using `r.set(dedupe_key, "1", nx=True, ex=86400)`.
- What I wrote: Correct decorator; `assert r.set.call_count == 100` is a specific test harness expectation.
- Result: 35–52% depending on exactly how I write the assertion.
- Good: Idempotent keys via SETNX is a real canonical pattern.
- Issues: The `must_contain` includes `assert r.set.call_count == 100` — a magic number from a test harness the learner hasn't seen. If they write `assert r.set.call_count >= 100` or call it 99 times, they lose points on a completely reasonable implementation. This is grader-over-reaching.
- Severity: **P1**

### Git Advanced — M1.3 "Rebase a feature branch onto main" (step 360)
- Type: code_exercise
- Language: shell
- What I wrote: Full interactive-rebase workflow using `GIT_SEQUENCE_EDITOR`/`GIT_EDITOR` sed scripts to squash 3 fixups and reword the final commit — a legit headless rebase, the kind I'd actually ship.
- Result: 60%. Same 60% cap on shell.
- Severity: **P0** (grade cap again)

### AI Power Skills — M1.2 "Reading a 50K-Line Codebase — Part 1" (step 452)
- Type: code_exercise
- Language: python
- What was asked: Flesh out a `CodebaseAnalyzer` that scans `/tmp/flowsync` for Redis/DB/auth patterns.
- What I wrote: Filled the TODOs with proper `re.findall` calls and counter bumps.
- Result: 47%.
- Good: The pedagogical framing ("read an unfamiliar codebase with AI help") is real and valuable.
- Issues: (a) `/tmp/flowsync` does not exist in the sandbox — no `starter_files` fixture. Scaffold runs but scans nothing, returns empty report. (b) The `must_contain` includes **literal regex fragments** like `redis\.get\(`, `redis_timeout.*\+=`, `token_expiry.*\+=` — these have to appear verbatim in the source. If a learner writes the correct code using `re.search()` instead of `re.findall()`, or bumps `redis_timeout` without the `+=` literal (e.g., `redis_timeout = redis_timeout + 1`), they fail. The grader treats the learner's Python source as a string to regex-search, but matches substring literals, not regex meaning. This is internal-implementation-leakage.
- Severity: **P0** — known bug; documenting the broader class of regex-leakage.

### System_build capstones (steps 282, 244, 380, 337, 357) — pooled review
All five capstones share the same class of bug:
- **step 282 (Async)**: `endpoint_check.url = ""` — empty string; no way for the grader to hit a real URL.
- **step 244 (Docker)**: `endpoint_check.url = "http://your-deployed-service/health"` — literal placeholder, not a real host.
- **step 337 (Kafka)**: `endpoint_check.url = "https://your-deployment.aws.com/health"` — `your-deployment.aws.com` is not a real domain.
- **step 380 (Git)**: `endpoint_check.url = "https://api.github.com/repos/streamdeck-classroom/broken-verification-repo/pulls"` — 404.
- **step 357 (OTel)**: `endpoint_check.url = "http://localhost:8000/package/PKG-12345"` — the remote grader cannot reach the learner's localhost.

None of these accept a student-provided URL. The validation payload shapes I tried (`endpoint_url`, `checklist_confirmed`, plain checkbox state) all return 0%. **No learner can complete a capstone.** Since the capstone is the marketing-grade "ship it" deliverable at the end of every technical course, this is course-completion-blocking for 7-10 courses.

The `phases` / `checklist` / `deployment_config` data in `demo_data` is well-written — clear, 4-phase / 10-item rubric that mirrors real engineering workflow ("scaffold / implement / test / ship"). The framing is good. But the grader never exercises any of it.

Severity: **P0**

## Systemic themes (cross-course patterns)

1. **`must_contain` is a dumb substring match over the learner's source code, not an AST or behavior check.** Consequences:
   - A `print()` of every required token scores the same 60% as a real solution (step 349 definitive evidence).
   - Correct idiomatic code that uses a different assignment target (`results = await asyncio.gather(...)` vs `await asyncio.gather(...)` on a statement line) fails the substring match (step 263).
   - Learner can ace grading by writing garbage that includes the right strings; a learner who re-names variables or factors cleanly *fails*. The incentive is backwards.

2. **`code_exercise` grader appears to multiply must_contain × output-match, with a default 60% cap when either is missing / impossible.** Evidence: `expected_output` is empty on many exercises; in those cases real solutions + hacks both score 60%, while empty code scores 0%. On exercises where `expected_output` IS populated (step 226 Docker shell), the sandbox can't execute the scaffold (no `docker` binary), so the output can't match — still 60%.

3. **The sandbox fixture gap is pervasive.** Missing: `bcrypt`, `confluent_kafka`, `kafka`, `psycopg2`, all `opentelemetry.*`, full `httpx` (stubbed to AsyncClient only). Present: `aiohttp`, `fastapi`, `pydantic`, `redis` (likely), standard lib. Any course whose scaffolds import a missing lib is effectively broken-by-default. At least 4 of 11 courses I sampled have this issue (Async bcrypt step, Kafka, OTel, and partially Async httpx).

4. **`system_build` capstones have no path to completion.** The validation `endpoint_check.url` field contains either empty strings, literal placeholders, `localhost` references that only work from the learner's machine, or live GitHub repos that 404. The grading rubric data (`phases`, `checklist`) is nicely structured and never consulted.

5. **`code_review` bug lists are opinionated and sometimes omit the obvious.** Step 232 (Dockerfile) skips apt-cache-cleanup and the commented-out USER. Step 286 (GraphQL kitchen sink) skips the root complaint named in the title. The grader is deciding what "the bugs" are based on creator choices that don't always match senior-engineer intuition.

6. **`parsons` has a payload-shape mismatch.** No combination of `{"ordered":…}`, `{"order":…}`, `{"items":…}`, `{"sequence":…}` with raw strings, indices, or numbered prefixes passes. The class returns 0/N lines for any ordering. 8 exercises in AI Power Skills course alone are unusable.

7. **`fill_in_blank` is the only systemically-working exercise type** (when you find the `answers` key — which requires one throw-away attempt). Alternatives lists are nicely inclusive on some (step 345), too strict on others (step 375). Correct answers occasionally incorporate fiction ("seek" for a `consumer.___(partitions)` on step 331 where the real API is `assign`).

8. **Bug-count mismatches between `demo_data.bugs` and the grader.** Step 315 displays 9 bug slots but the grader only credits 8 distinct lines. Learner will appear to be missing a bug they aren't.

9. **`must_contain` tokens occasionally reference internal test harness state** (step 334: `assert r.set.call_count == 100`) — a specific magic number from a hidden test. Learners can implement the feature correctly and still fail because they don't know about the ambient assertion.

10. **Briefings are consistently high quality** — the "Velora session cache" / "StreamFlow enrichment pipeline" / "CartFlow 2.8M SKU catalog" framings are vivid, the stakeholder names feel real, the time budgets are reasonable. The content quality is *not* the problem; the *grading infrastructure* is.

## Capstone quality (system_build and equivalents)

Verdict: **Every capstone I reviewed is a doc-write disguised as a ship-deliverable.** The briefings promise "ship this to production," the checklists correctly enumerate the real work (build image → Dockerize → write compose → deploy → smoke-test), and the deployment_config even specifies platforms (Railway, GitHub Actions). But the actual grading probe is an unreachable URL. So either:

- The learner takes the 2-hour "ship it" task seriously, goes deep, ends up with real artifacts — and is unrewarded by the grader (0%).
- Or the learner writes `/done` in the checklist without doing any work and gets the same 0%.

This is the most corrosive grading pattern in the product because the capstone is where it matters most. The good news: the `phases` + `checklist` + `deployment_config` structure is already in the data; if the grader consulted it (e.g., "did you submit a PR URL or a deployed service URL — fetch it and check it returns 2xx?"), this would be salvageable.

System_build exercises I reviewed: step 282 (Async scatter_gather), 244 (Docker Go+Redis), 380 (Git clean history), 337 (Kafka orders consumer), 357 (OTel FastAPI→OTLP→Jaeger). All five share the pattern.

The single exception: step 486 (AI Power Capstone) has `endpoint_check: none`, i.e., no URL-based grading at all — which means it's trivially 0% since there's no pass condition configured.

## Top-10 improvement recommendations (ranked by leverage)

1. **Strip the 60% cap on code_exercise grading.** Replace `must_contain` substring matching with either (a) an AST-based check ("does the solution call `asyncio.gather(...)` with `return_exceptions=True`?") or (b) drop `must_contain` entirely and rely on behavior tests (e.g., a hidden `pytest` harness that imports the learner's module and checks outputs). Today, the grader can't tell real code from token-spam — which is a correctness bug that matters more than any pedagogy bug. **Expected impact: every code_exercise becomes meaningfully graded; hacks stop scoring.** High effort (needs a behavior-test harness per exercise) but it's the #1 blocker.

2. **Fix system_build capstone grading.** Add a `response_data.deployment_url` field that the learner submits; the grader calls `GET {deployment_url}` and runs the `contains` / `json_contains` checks. Today the URL is baked into the validation config and is a placeholder. **Expected impact: capstones become completable.** Low effort (schema change + grader plumbing).

3. **Expand the sandbox Python environment OR provide inline mock fixtures.** At minimum: `bcrypt`, `confluent_kafka`, `kafka-python`, `psycopg2-binary`, `opentelemetry-api`, `opentelemetry-sdk`, and fix `httpx` (install full package or at least make `httpx.Response` exist). Alternatively, include ready-to-use monkey-patches in `demo_data.starter_files` so the scaffold runs out-of-box. Today, ~4 of 11 courses have ImportError-on-open scaffolds. **Expected impact: 40% of code_exercise-bearing courses become runnable.** Medium effort.

4. **Fix the parsons payload key or document it in the validation schema.** The grader accepts `{"ordered": [...]}` but returns 0 for any order. Either the matching logic is checking indices when the submitter sent strings, or vice versa. Add one integration test that submits the canonical correct order and asserts `score == 1.0`. **Expected impact: 8+ parsons exercises become usable.** Low effort — this is likely one bug in the grader.

5. **Allow `must_contain` to be regex when wrapped in `/…/` or use a `must_match_regex` alternative.** The current behavior is "substring match, but the strings sometimes contain regex metacharacters" (step 452's `redis_timeout.*\+=` is the obvious case). Make the intent explicit and document it in the Creator prompt. **Expected impact: eliminates the whitespace / anchoring brittleness in ~20% of exercises.** Low effort.

6. **Enforce `demo_data.bugs.length == graded_bug_count` and show bug numbers to learners.** Today the UI likely shows "N bug slots" while the grader looks at a different N. Step 315: UI 9, grader 8. Fix by generating the list authoritatively in one place. **Expected impact: learners stop second-guessing correct answers.** Low effort.

7. **Audit `must_contain` for magic-number / test-harness leakage.** Step 334's `assert r.set.call_count == 100` forces the learner to know a hidden integer; step 280 likewise expects `test_concurrent_login_performance` by exact name. Creators should be prompted to NOT include assertion literals that reference internal tests. **Expected impact: ~10% of code_exercises stop punishing correct-but-differently-shaped implementations.** Low effort (Creator prompt change).

8. **Calibrate `code_review` bug lists against senior-engineer review.** For every new code_review exercise, require the Creator to justify why the N chosen bugs are the top N. Step 232 missed the commented-out USER directive; step 286 missed the exact anti-pattern the exercise is titled after. A simple check: "of all reasonable bugs in this code, are the N you flagged the N a senior engineer would lead with?" **Expected impact: pedagogical accuracy improves; learners internalize correct taxonomy.** Medium effort (Creator quality gate).

9. **In the UI, return the grader's discovered-bug line on code_review attempts 2 and 3.** Right now the UI says "try again — focus on red items" but never shows which lines are right. Allowing progressive disclosure ("you got lines 1 and 21 right; 3 remaining") would let learners actually learn from feedback instead of guessing. **Expected impact: code_review becomes a learning surface, not a puzzle.** Low effort (UI surface of existing grader data).

10. **Add a `sandbox_affordances` field to each code_exercise's `demo_data`** that inlines library stubs for the libs the sandbox is missing. Today, a learner who wants to verify their code has to either rewrite it to not use the missing imports or abandon execution. A creator-provided stubs block, injected before the learner's code in the sandbox, would close the scaffold-works-out-of-box gap while the sandbox provisioning problem (rec #3) is solved. **Expected impact: every exercise becomes runnable today without waiting on sandbox image upgrades.** Low-medium effort.

---

### Evidence artifacts referenced

- `/tmp/sll_eval/all_steps.json` — cached full text of 172 steps across 8 courses.
- `/tmp/sll_eval/sol_*.py|sh|dockerfile` — my actual submitted solutions per step.
- `/tmp/sll_eval/results_log.md` — running log with quick-fire observations per exercise.
- Course-vs-step mapping:
  - `created-34dd8b787e8e` Async: steps 259, 260, 263, 264, 280, 281, 282
  - `created-1ffaa4c5a762` Docker: steps 226, 230, 232, 235, 244
  - `created-ea0e705ed2cd` Git Advanced: steps 360, 375, 380
  - `created-608d64314daf` GraphQL: steps 286, 315
  - `created-13071a72a576` Kafka: steps 323, 330, 331, 334, 336, 337
  - `created-093173416fee` OTel: steps 344, 345, 349, 352, 355, 357
  - `created-6669632522d9` PostgreSQL: step 297
  - `created-6592bfe6e5db` AI Power: steps 452, 454
