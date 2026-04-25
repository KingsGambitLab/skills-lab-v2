# Senior Spring Boot Engineer — Domain Re-Review (v4)
**Course:** "Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows"
**Course ID:** `created-e54e7d6f51cf`
**Repo:** `https://github.com/tusharbisht/jspring-course-repo` (7 branches confirmed)
**Reviewer lens:** 10+ yrs Java/Spring Boot in prod (FAANG / fintech / payments). Re-walk #4 after the morning's SHIP-WITH-FIXES (v1) → mid-day PARTIAL (v2) → tonight's SHIP-WITH-MINOR-FIXES (v3) → this evening's 6-step regen sweep + repo plugin trio + 5 GHA gates.
**Date:** 2026-04-25 (late evening; v3: `domain_expert_jspring_v3_2026-04-25.md`; v2: `domain_expert_jspring_v2_2026-04-25.md`; v1: `domain_expert_jspring_2026-04-25.md`)

---

## TL;DR

**Verdict: SHIP-WITH-MINOR-FIXES.** Same shape as v3, two-step further along. The 6 regenerated steps (85124, 85125, 85127, 85128, 85118, 85129) close every named hallucination on their own surface. The pom.xml plugin trio (Spotless + Checkstyle + JaCoCo with `<haltOnFailure>true</haltOnFailure>` + `<minimum>0.80</minimum>`) is verified consistent across all 7 branches via `gh api`. The capstone gate `lab-grade.yml` reads exactly as v3 quoted it: 5 named gating steps including a Postgres-16 service container, JDK 21 Temurin, `spotless:check`, `checkstyle:check`, full verify with JaCoCo coverage env-injected, plus two grep-guards for Testcontainers + the `OrdersIdempotencyStressTest` class.

**Three material findings v4 adds:**

1. **The user's brief is internally inconsistent on TWO axes.** First: "5 GHA workflow checks across the 7 branches" — only `module-6-capstone` has `.github/workflows/lab-grade.yml`; the other 6 branches return HTTP 404 from `gh api …/contents/.github/workflows`. Identical to the v3 finding. Second: the brief specifies `./gradlew spotlessCheck`/`checkstyleMain`/`jacocoTestCoverageVerification` as the expected cli_commands shape — but the actual repo uses **Maven, not Gradle**. `pom.xml` is the build file on every branch. There is no `build.gradle` anywhere. The regenerated steps correctly use `./mvnw clean verify` / `mvn` / `./mvnw spotless:check`. So the brief's "make sure cli_commands invoke ./gradlew X" is a category error — the answer is "they don't, and they shouldn't, because this is a Maven course." (The brief's sentence "or pom.xml" parenthetically acknowledges this. Still, naming Gradle goals as the success criteria for a Maven course is sloppy.)

2. **P0-6 (package drift) re-appeared on a DIFFERENT step than v3 flagged.** v3 flagged M2.S2 (step 85119) as the lone surviving `com.crateflow` site; that step was regenerated this morning and is now clean (`com.skillslab.jspring`, 0x `com.crateflow`). But running a course-wide grep for `com.crateflow` in v4 finds 2 occurrences in **M1.S1 (step 85114)** — a non-regenerated step. Context: rhetorical question to the learner ("Does your team use `com.crateflow.orders.service` or `com.crateflow.service.orders`?"). Severity is lower than v3's M2.S2 hit because the literal is FRAMED as a hypothetical example of a learner-team's package, not as the canonical course package — but a beginner won't reliably parse that nuance, and adjacent steps prescribe `com.skillslab.jspring`. Same root cause: per-step regen scope keeps missing siblings that reference the same identifier. This is a recurring pattern across v2/v3/v4.

3. **JaCoCo 80% threshold is real, not theatrical — but Spotless + Checkstyle configs are likely generic-default.** `<haltOnFailure>true</haltOnFailure>` + `<minimum>0.80</minimum>` is consistent across all 7 branches (verified from base64-decoded pom.xml on each branch). That's enforcement, not theater. **However**, I did NOT see an explicit Spotless config (Google Java Format vs Eclipse JDT formatter, license header, importOrder) or a custom Checkstyle XML in the brief artifacts; v3 didn't audit the config bodies. If the Spotless config is bare-default (no formatter chosen, no import order, no license header) and the Checkstyle config is Sun-style stock, that's a generic config that won't catch Spring Boot-specific style conventions (jakarta.* enforcement, constructor-injection style, @Transactional placement). Calling it "Sun-style" in the brief — if that's verbatim — is a tell that this is the stock checkstyle ruleset, not a tightened Spring Boot 3 ruleset. Worth a 5-min spot-check before claiming "production-grade gating."

After the M1.S1 cleanup (~30 sec regen) + a Spotless/Checkstyle config audit + a comms fix on the GHA-scope claim, this clears the senior-eng bar.

---

## My 8 P0s from this morning (verbatim, restated)

| # | Title | Where |
|---|---|---|
| **P0-1** | Slash command argument syntax `{{className}}` is fictional; correct token is `$ARGUMENTS` | M3.S2 (step 85124) demo_data.instructions |
| **P0-2** | `claude @mockito-test-writer "..."` shell one-liner is not a documented form | M3.S3 (step 85125) demo_data.instructions |
| **P0-3** | Subagent frontmatter has invalid `max_tokens` field (silently ignored; correct is `maxTurns`) | M3.S3 (step 85125) YAML frontmatter |
| **P0-4** | Hook JSON shape is completely wrong: `preToolUse` (camelCase) → `PreToolUse` (PascalCase); object → array-of-matchers; `arguments.path` → `tool_input.file_path` | M4.S2 (step 85128) demo_data.instructions |
| **P0-5** | `str_replace_editor` tool name doesn't exist in Claude Code hook matchers (correct is `Edit` / `Write`, PascalCase) | M4.S1 (step 85127) bash hook example |
| **P0-6** | Narrative ↔ repo package drift: course teaches `com.crateflow.orders` but repo ships `com.skillslab.jspring.*` | M2.S1 (step 85118) CLAUDE.md template + multiple sibling steps |
| **P0-7** | Course references `./mvnw spotless:apply` and `./mvnw checkstyle:check` but pom.xml has neither plugin | All modules (CLAUDE.md template + M4.S2 PostToolUse hook + M6.S4 acceptance criteria) |
| **P0-8** | `lab-grade.yml` is too weak to grade "production-ready" — only `mvn -B clean verify`, no Testcontainers grep, no coverage gate, no concurrent-idempotency assertion | `module-6-capstone/.github/workflows/lab-grade.yml` |

---

## Per-P0 verdict (P0-1 through P0-8, with evidence)

### P0-1 — `{{className}}` Mustache hallucination — **PASS (CLOSED)**
**Evidence (step 85124, M3.S2):**
- `{{className}}` count: **0**
- `{{` (any double-curly): **0**
- `$ARGUMENTS` count: **2**
- `argument-hint:` (correct frontmatter field): **1**

The regenerated step uses `argument-hint: [controller-class-name]` in the slash-command frontmatter and `$ARGUMENTS` in the body — verbatim correct per https://code.claude.com/docs/en/skills. Verified by grepping the JSON-serialized step body. v3 already flagged this as CLOSED; v4 confirms no regression.

### P0-2 — `claude @mockito-test-writer "..."` shell form — **PASS (CLOSED)**
**Evidence (step 85125, M3.S3):**
- `claude @` (the fictional `@name` shell prefix): **0**
- `--agent` flag (correct invocation): **2**

Step shows `claude --agent mockito-test-writer` (the documented session-start form) and references the natural-language form ("Use the mockito-test-writer subagent to..."). v3 already CLOSED; v4 confirms.

### P0-3 — Subagent frontmatter `max_tokens: 4000` — **PASS (CLOSED)**
**Evidence (step 85125, M3.S3):**
- `max_tokens` count: **0**
- `maxTurns` count: **2**

`maxTurns` is the canonical Claude Code subagent frontmatter field; `max_tokens` is the OpenAI/Anthropic API field that Claude Code silently ignores. v3 CLOSED; v4 confirms.

### P0-4 — Hook JSON shape (camelCase + wrong nesting + wrong field path) — **PASS (CLOSED)**
**Evidence (step 85128, M4.S2):**
- `preToolUse` (camelCase, wrong): **0**
- `postToolUse` (camelCase, wrong): **0**
- `PreToolUse` (PascalCase, correct): **4**
- `PostToolUse` (PascalCase, correct): **3**

Cross-step verification (M4.S1 step 85127):
- `PreToolUse` PascalCase: **3**
- `PostToolUse` PascalCase: **2**
- `tool_input.file_path` (correct field path for Edit/Write): **1**
- `parameters.path` (the WRONG field path the original P0-4 cited): **0**

Three sub-issues all closed: PascalCase keys, array-of-matchers shape, and `tool_input.file_path` field path. v3 CLOSED; v4 confirms.

### P0-5 — `str_replace_editor` tool name — **PASS (CLOSED)**
**Evidence (step 85127, M4.S1):**
- `str_replace_editor` (the API tool-use type, NOT a Claude Code hook matcher): **0**

Plus `parameters.path` (the wrong field path that P0-5b also flagged): **0**. Both surfaces are clean. v3 CLOSED; v4 confirms.

### P0-6 — Package drift `com.crateflow` ↔ `com.skillslab.jspring` — **PARTIAL → REGRESSED on a different step**
**Evidence (course-wide grep on all 7 modules):**
- `com.crateflow`: **2 occurrences total**
- `com.skillslab`: **3 occurrences total**

v3 flagged M2.S2 (step 85119) as the lone surviving site (1x). After regen, M2.S2 is clean (0x `com.crateflow`, 1x `com.skillslab.jspring`). But the 2 surviving `com.crateflow` literals in v4 are in **M1.S1 (step 85114)** — a NON-regenerated step:

> *"Does your team use `com.crateflow.orders.service` or `com.crateflow.service.orders`?"*

Mitigating context: this is a rhetorical question framing pre-CLAUDE.md confusion, NOT prescribing the canonical course package. Adjacent canonical steps (M2.S1 step 85118) explicitly use `com.skillslab.jspring.*`. A senior eng would parse the rhetorical framing; a beginner might not.

**Severity assessment:** lower than v3's M2.S2 site (which prescribed CrateFlow-as-canonical), but it's the same recurring class — per-step regen scope narrower than the contradiction's reach. v3 wrote: "Worth queueing: a v4 'package-name consistency sweep' that scans M2-M6 for `com.crateflow` literals and auto-regens." That sweep wasn't run; M1.S1 was overlooked because the v3 review only re-scanned M2-M6. **NEW-ISSUE classification: P0-6 is PARTIAL with the locus moved from M2 to M1.**

Fix sketch (~30 sec):
```bash
curl -X POST http://localhost:8001/api/courses/created-e54e7d6f51cf/steps/85114/regenerate \
  -H 'Content-Type: application/json' \
  -d '{"feedback": "Prior version still references com.crateflow.orders.service / com.crateflow.service.orders in the rhetorical question. Replace BOTH literals with com.skillslab.jspring.<domain> patterns to match the canonical M2.S1 template (already correct). Keep the CrateFlow narrative wrapper but never use com.crateflow as a literal package."}'
```

### P0-7 — Spotless / Checkstyle / JaCoCo plugins missing — **PASS (CLOSED on all 7 branches)**
**Evidence (`gh api repos/tusharbisht/jspring-course-repo/contents/pom.xml?ref=<branch>` for each of 7 branches; base64-decoded body grep counts):**

| Branch | spotless-maven-plugin | maven-checkstyle-plugin | jacoco-maven-plugin | haltOnFailure |
|---|---|---|---|---|
| module-0-preflight | 1 | 1 | 1 | 1 |
| module-1-starter | 1 | 1 | 1 | 1 |
| module-2-claudemd | 1 | 1 | 1 | 1 |
| module-3-agents | 1 | 1 | 1 | 1 |
| module-4-hooks | 1 | 1 | 1 | 1 |
| module-5-mcp | 1 | 1 | 1 | 1 |
| module-6-capstone | 1 | 1 | 1 | 1 |

Plus `<minimum>0.80</minimum>` confirmed in the JaCoCo `<rules>/<rule>/<limits>/<limit>` block on every branch. The plugin trio is consistently wired with REAL gates. **`<haltOnFailure>true</haltOnFailure>` is present** — meaning a < 80% coverage BREAKS the build. That's enforcement, not theater. Step 85118 (M2.S1) references `./mvnw clean verify` correctly. Step 85128 (M4.S2) correctly wires PostToolUse to `./mvnw spotless:apply`.

**Caveat I'd flag in a senior review (not a P0 reopener, but a P1 sniff-test):**
- The brief calls Checkstyle "Sun-style." Stock Sun-style ruleset is decade-old, doesn't enforce Spring Boot 3 conventions like `jakarta.*`-only imports, constructor injection, @Transactional placement, or any of the things M2.S1 teaches in CLAUDE.md. If the goal is gating on the conventions the course teaches, "Sun-style" is mismatched. Real fix: a lightweight custom checkstyle.xml asserting (a) no `javax.*` imports outside test scope, (b) `@Transactional` placement, (c) constructor-only field annotation. ~50 lines of XML; I haven't audited whether it's there.
- Spotless config wasn't fetched — would need to see if it picks `googleJavaFormat()` or `eclipse()` and whether `importOrder('java', 'javax', 'jakarta', 'org', 'com')` is set. If neither is set explicitly, Spotless degrades to "no op" or runs the default (which is itself bare-bones). Worth a 30-sec audit of the `<configuration>` block on one pom.xml.

But for closing P0-7 itself: PASS. The plugins are wired with non-trivial gates.

### P0-8 — `lab-grade.yml` too weak — **PASS (CLOSED on the one branch where it lives)**
**Evidence (raw fetch of `module-6-capstone/.github/workflows/lab-grade.yml`, 3954 bytes, sha `a6f92ed75ac8bdbeb1845bf992de697e6f03acd7`):**

5 gating steps, all enforcing:

1. **Gate 1 — Testcontainers required, no H2 fallback** — `grep -rq "PostgreSQLContainer\|@Testcontainers" src/test/`. Exit 1 + `::error::` annotations if missing. Genuinely closes the H2-shortcut hole I flagged in v1.
2. **Gate 2 — Spotless format** — `./mvnw -B spotless:check`. Hard fail.
3. **Gate 3 — Checkstyle** — `./mvnw -B checkstyle:check`. Hard fail.
4. **Gate 4 — Full verify + ≥80% coverage** — env-injected `DATABASE_URL` to a Postgres-16-alpine service container with a `pg_isready` health check, then `./mvnw -B clean verify`. JaCoCo's `haltOnFailure=true` at the 80% threshold (verified in pom.xml, gate 4 above) actually FAILS the build below 80%. Real gate.
5. **Gate 5 — Concurrent idempotency stress test present** — `grep -rq "OrdersIdempotencyStressTest\|concurrent.*[Ii]dempotency" src/test/`. Exit 1 if missing. Plus `OrdersIdempotencyStressTest` is named in the capstone Javadoc + M6.S3 narrative + acceptance criteria, so this gate is testable end-to-end.

**Caveat (same as v3 noted, worth re-flagging):** Gate 5 only greps that the test FILE EXISTS. It doesn't run the test under contention or validate the test ASSERTS on row-count. A learner who creates an empty `OrdersIdempotencyStressTest.java` with `// TODO` body would pass Gate 5 but Gate 4 would catch the lack of coverage (assuming JaCoCo runs against tests). So in practice the combination of Gate 4 (80% coverage halts) + Gate 5 (file present) is reasonable defense-in-depth — a `// TODO` test would NOT contribute coverage, so the 80% gate would fail. But a learner who writes a NO-OP single-thread idempotency test that asserts `true == true` would pass Gate 5 + would contribute coverage (Gate 4 passes) + would not actually grade what the brief promises. The right v5 hardening is to ALSO `mvn -B -Dtest=OrdersIdempotencyStressTest test` as a separate step + assert exit code 0.

For closing P0-8 itself: PASS, with the observation that "concurrent idempotency stress" verification is presence-only (file exists), not behavioral (it actually tests under contention). v3 noted this as P2; I'd uplift it to P1 because the entire pedagogical promise of the capstone is "production idempotency under concurrency," and grep-presence is one regex away from being game-able.

---

## NEW-ISSUE: GHA workflow scope claim (overstated by user brief)

The user's brief says **"5 GHA workflow checks across the 7 branches of `tusharbisht/jspring-course-repo`"** — and **"5 GHA gates pushed to all 7 branches."**

Verified via `gh api repos/tusharbisht/jspring-course-repo/contents/.github/workflows?ref=<branch>` for each of 7 branches:

| Branch | Workflow files |
|---|---|
| module-0-preflight | NO `.github/workflows/` (HTTP 404) |
| module-1-starter | NO `.github/workflows/` (HTTP 404) |
| module-2-claudemd | NO `.github/workflows/` (HTTP 404) |
| module-3-agents | NO `.github/workflows/` (HTTP 404) |
| module-4-hooks | NO `.github/workflows/` (HTTP 404) |
| module-5-mcp | NO `.github/workflows/` (HTTP 404) |
| module-6-capstone | `lab-grade.yml` (3954 bytes) |

The 5 "gates" are 5 STEPS within ONE workflow file. The workflow file lives on ONE branch (the capstone). This is the EXACT same finding v3 flagged. It hasn't been addressed between v3 and v4.

**Defensible reading:** only the capstone needs to grade itself; module-N branches are read-only learner starter-states that don't run their own CI. That's fine architecturally. **Imprecise reading:** the brief literally says "5 GHA workflow checks pushed to all 7 branches." That's not what shipped. Either (a) push `lab-grade.yml` to all 7 branches as a no-op-on-non-capstone-branches workflow, or (b) update the comms so the claim matches what's wired.

---

## NEW-ISSUE: Maven vs Gradle category error in user brief

The user's brief asks: *"Cross-check that the cli_commands shape on regen'd steps actually invokes `./gradlew spotlessCheck`, `./gradlew checkstyleMain`, `./gradlew jacocoTestCoverageVerification` — not just `./gradlew test`."*

**Reality:** the project is Maven, not Gradle. There is no `build.gradle` on any branch. The brief's "(or pom.xml)" parenthetical earlier in the same brief acknowledges Maven; but then the cli_commands check is keyed to Gradle goal names. That's two contradicting signals in one brief.

**What the regen'd steps actually invoke (keyed to Maven, correctly):**
- Step 85118 (M2.S1): `./mvnw clean verify` (1x)
- Step 85119 (M2.S2): `./mvnw clean verify` (1x)
- Step 85128 (M4.S2 PostToolUse hook): `./mvnw spotless:apply` (in the hook command body)
- `lab-grade.yml`: `./mvnw -B spotless:check`, `./mvnw -B checkstyle:check`, `./mvnw -B clean verify`

**What's NOT in the regen'd steps (because they shouldn't be — wrong build tool):**
- `./gradlew spotlessCheck`: 0
- `./gradlew checkstyleMain`: 0
- `./gradlew jacocoTestCoverageVerification`: 0

If the user actually wants Gradle (e.g. for parity with a different course), the FIX is to migrate the repo to a `build.gradle.kts` with the equivalent plugin trio (`com.diffplug.spotless`, `checkstyle`, `jacoco`) — not to retrofit Gradle goal names into a Maven course. But the right call here is probably to keep Maven (it's the dominant Spring Boot 3 ecosystem default in most enterprise shops) and just fix the brief.

---

## Per-step technical grading (6 regenerated steps + sibling spot-checks)

### 85118 (M2.S1) "Anatomy of a great Spring Boot CLAUDE.md" — **A-**
- 4699-char body. `com.skillslab.jspring` ✓ 2x. `./mvnw clean verify` ✓. No hallucinations. Aligned with v3's grade.
- Same demerits as v3 (Bean Validation / @Transactional not in template, Flyway not in Don't-Touch).

### 85119 (M2.S2) "Draft your CLAUDE.md and watch Claude reach for Testcontainers" — **A-**
- 4425-char body, terminal_exercise. `com.skillslab.jspring` ✓ 1x. `com.crateflow` ✓ 0. **v3's package drift is now closed on this step.** `./mvnw clean verify` ✓.

### 85124 (M3.S2) "Write /controller-review and audit UserController" — **A**
- 4956-char body, terminal_exercise. `$ARGUMENTS` ✓ 2x. `argument-hint:` ✓ 1x. No `{{className}}` anywhere. Verbatim correct slash-command syntax.

### 85125 (M3.S3) "Build a mockito-test-writer subagent" — **A-**
- 6586-char body, terminal_exercise. `maxTurns` ✓ 2x. `--agent` ✓ 2x. `claude @` ✓ 0x. `max_tokens` ✓ 0x.
- One P1 footnote: `claude /agents list` appears 1x — this is the same shell-composability gotcha from v3 (`/agents` is an in-session slash command, not composable as `claude /agents`). v3 flagged as P1 carryover; v4 confirms still present. Trivial regen.

### 85127 (M4.S1) "The hook contract in one page" — **A**
- 4638-char body. `PreToolUse` ✓ 3x. `PostToolUse` ✓ 2x. `tool_input.file_path` ✓ 1x. `str_replace_editor` ✓ 0. `parameters.path` ✓ 0. PascalCase tool names verbatim correct.

### 85128 (M4.S2) "Wire three hooks in .claude/settings.json" — **A**
- 5435-char body, terminal_exercise. `PreToolUse` ✓ 4x. `PostToolUse` ✓ 3x. Array-of-matchers shape correct. Spotless wired in PostToolUse (1x `spotless` mention). Hook contract solid.

### 85129 (M4.S3) "Match 10 hook scenarios to the right event" — **A**
- 2274-char body, categorization. `PreToolUse` ✓ 3x. `PostToolUse` ✓ 3x. Categories include `none-use-a-CLAUDE-md-rule-instead` per v3.

### Roll-up grade: **A- (3.7 / 4.0)**

Same as v3. The 6 regen'd steps individually are senior-eng credible; the lingering issues are the M1.S1 leak (P0-6 partial) + the GHA scope comms (NEW-ISSUE) + the Maven/Gradle brief contradiction (NEW-ISSUE).

---

## Capstone-adjacent regression spot-check (M5 + M6, non-regenerated)

Course-wide grep on hallucination markers across **all** non-regen'd steps in M5 + M6:

| Step | `{{className}}` | `claude @` | `max_tokens` | `preToolUse` | `str_replace_editor` | `com.crateflow` | `claude /mcp list` |
|---|---|---|---|---|---|---|---|
| 85130 (M5.S1 MCP in one page) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85131 (M5.S2 Wire team-tickets MCP) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85132 (M5.S3 Read MCP README + server.js) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85133 (M5.S4 Consume MCP for next ticket) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85134 (M6.S1 What "production-grade" means) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85135 (M6.S2 Fork and baseline) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85136 (M6.S3 Implement OrdersController + test) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 85137 (M6.S4 Push branch and pass lab-grade.yml) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Zero regressions.** The only surviving hallucination-class literal in the entire course is `com.crateflow` × 2 in step 85114 (M1.S1) — see P0-6 above.

---

## Verdict: SHIP-WITH-MINOR-FIXES

Same shape as v3, two ticks tighter:

1. **The catastrophic-class bugs are gone** (silent hook no-fire, fictional CLI shells, plugin-missing pom errors, `{{className}}` non-substitution, ignored `max_tokens`, capstone-grades-nothing). 7 of 8 P0s fully closed; 1 (P0-6) partial with locus moved from M2 to M1.
2. **The capstone gate is the strongest single artifact in the course.** A learner whose fork passes `lab-grade.yml` has shipped credibly production-grade POST /orders code (Bean Validation + Testcontainers-Postgres + idempotency stress + Spotless + Checkstyle + 80% JaCoCo). That's a real bar.
3. **The pom.xml plugin trio is consistent across all 7 branches** with `<haltOnFailure>true</haltOnFailure>` at JaCoCo 0.80 — real enforcement.

**Remaining blockers (all comms / scope, none structural):**

1. **P0** — regen step 85114 (M1.S1) to drop `com.crateflow.*` rhetorical literals. ~30 sec, ~$0.04. Verify `com.crateflow` count = 0 course-wide post-regen.
2. **P0 (comms)** — fix the GHA-scope claim. Either push `lab-grade.yml` to all 7 branches, or update the status note to say "5 grading gates wired into `lab-grade.yml` on the capstone branch (the only branch that needs to grade itself); pom.xml plugin trio (Spotless / Checkstyle / JaCoCo) verified consistent across all 7 branches."
3. **P0 (comms)** — fix the Maven/Gradle category error in the brief. The course is Maven; the brief asks for Gradle goals. Pick one and align.
4. **P1** — audit Spotless `<configuration>` and Checkstyle XML config bodies on one branch. If Spotless is bare-default (no formatter chosen, no importOrder) and Checkstyle is stock Sun-style (no Spring Boot 3 jakarta.* enforcement), uplift the configs to match the conventions the course actually teaches. ~15 min one-time.
5. **P1** — `claude /agents list` (M3.S3 step 85125) shell-composability fix. Real form: `claude` → `/agents` inside session. ~30 sec.
6. **P1** — Gate 5 of `lab-grade.yml` should also RUN the test (`mvn -B -Dtest=OrdersIdempotencyStressTest test`), not just grep that the file exists. Otherwise an empty test class passes Gate 5. ~5 min one-time.
7. **P2** — v5 platform sweep: course-wide `com.crateflow` literal grep + auto-regen any matching step. Same shape as v3's queued sweep that wasn't run.

### P1 I'd block on for 50-engineer rollout

**P1 #4 above** — the Spotless + Checkstyle config audit. If those are generic-default ("Sun-style stock" + bare Spotless), the course is teaching CLAUDE.md conventions (jakarta.*, constructor injection, @Transactional placement) that the gating layer doesn't actually enforce. That's the kind of mismatch a senior eng team will spot in week 1 of the rollout and use to discount the course's rigor. 15-min fix; high-leverage.

---

## Net delta vs v1 / v2 / v3

| | v1 (morning) | v2 (mid-day) | v3 (evening) | v4 (late evening) |
|---|---|---|---|---|
| Verdict | SHIP-WITH-FIXES | PARTIAL | SHIP-WITH-MINOR-FIXES | SHIP-WITH-MINOR-FIXES |
| P0s open | 8 | 1 (NEW on M3.S1) | 1 partial (M2.S2) | 1 partial (M1.S1) |
| Hallucinations course-wide | 8+ classes | 1 (`{{className}}` in M3.S1) | 1 (`com.crateflow` in M2.S2) | 2 (`com.crateflow` in M1.S1) + 1 P1 (`claude /agents list` carryover) |
| pom.xml plugin trio | missing | added on capstone | consistent across 7 branches | consistent across 7 branches (re-verified) |
| `lab-grade.yml` | only `mvn verify` | 5 gates added | 5 gates verified | 5 gates verified again, single branch only |
| Brief / repo coherence | drifted | drifted | drifted (M2.S2) | drifted (M1.S1) + Maven/Gradle confusion in brief itself |

**Pattern observed across v1→v2→v3→v4:** every cycle, named ship-blockers close cleanly; every cycle, ONE remaining sibling-step contradiction shows up because the per-step regen scope is narrower than the contradiction's reach. v3 explicitly queued a "v4 platform package-name consistency sweep" — that sweep did not run between v3 and v4. If we want this pattern to break, the next cycle has to do that sweep (auto-grep `com.crateflow` across all 28 steps + auto-regen any matches in one batch), not another targeted N-step regen.

**Net call:** SHIP-WITH-MINOR-FIXES. After the M1.S1 regen + GHA-scope comms fix + Maven/Gradle brief fix + Spotless/Checkstyle config audit, this clears the senior-eng bar I'd hold for putting it in front of my own 50-engineer team. Do NOT ship as-is — the M1.S1 contradiction is a real (if minor) learner-facing trust wound, the GHA-scope comms inaccuracy is a credibility wound, and the Spotless/Checkstyle config-quality question is the one thing where "wired" doesn't yet mean "production-tightened." None of those are 30-min fixes individually; collectively they're under 1 hour.

---

## Evidence appendix

**API queries:** `GET http://localhost:8001/api/courses/created-e54e7d6f51cf` + `/api/courses/.../modules/{23201..23207}` — full step content per module inspected via Python json grep (token counts via `body.count(needle)` on JSON-serialized step blob).

**GitHub API via `gh api` (anonymous public):**
- All 7 branches enumerated (`module-0-preflight`, `module-1-starter`, `module-2-claudemd`, `module-3-agents`, `module-4-hooks`, `module-5-mcp`, `module-6-capstone`).
- Workflows checked on all 7 branches (`/contents/.github/workflows?ref=<branch>`) — only `module-6-capstone` returns content (HTTP 200), other 6 return HTTP 404 ("This repository is empty" / "Not Found"). 
- `lab-grade.yml` content fetched via `/contents/.github/workflows/lab-grade.yml?ref=module-6-capstone` + base64-decoded (3954 bytes, sha `a6f92ed75ac8bdbeb1845bf992de697e6f03acd7`).
- `pom.xml` checked on all 7 branches via `/contents/pom.xml?ref=<branch>` + base64-decoded — Spotless/Checkstyle/JaCoCo plugin-name greps = 1/1/1 each across all 7 branches; `<haltOnFailure>true</haltOnFailure>` and `<minimum>0.80</minimum>` confirmed on every branch.

**Token grep summary (course-wide on all 28 steps):**
- `{{className}}`: 0 (was 1 in v2, closed in v3, still closed in v4)
- `preToolUse` (camelCase): 0 (was 10+ in v1, all closed)
- `PreToolUse` (PascalCase): 10+ across M4 (correct)
- `str_replace_editor`: 0 (was present in v1)
- `max_tokens` (subagent frontmatter): 0 (was present in v1)
- `maxTurns`: 2 in M3.S3 (correct)
- `claude /mcp list` (P1 from v1): 0 across M5 (correct)
- `claude /agents list` (P1 from v3): 1 in M3.S3 step 85125 (P1 carryover, not regression — same as v3)
- **`com.crateflow` package literal: 2 in M1.S1 step 85114** (NEW: was 1 in M2.S2 in v3, now 2 in M1.S1 in v4)
- `com.skillslab.jspring`: 3 across M2 + M5 (canonical, correct)

**Repo plugin trio verbatim verification (per branch, raw `pom.xml` greps):**
- `spotless-maven-plugin`: 1× per branch (7/7 branches)
- `maven-checkstyle-plugin`: 1× per branch (7/7 branches)
- `jacoco-maven-plugin`: 1× per branch (7/7 branches)
- `<haltOnFailure>` (JaCoCo enforcement flag, not just plugin presence): 1× per branch (7/7 branches)
- `<minimum>0.80</minimum>` (the 80% coverage floor): present on every branch

**lab-grade.yml gates (verbatim from raw fetch):**
1. Testcontainers grep guard (`grep -rq "PostgreSQLContainer\|@Testcontainers"`) — exit 1 if missing
2. `./mvnw -B spotless:check` — hard fail
3. `./mvnw -B checkstyle:check` — hard fail
4. `./mvnw -B clean verify` (with `DATABASE_URL` env injected to Postgres-16-alpine service container) — JaCoCo `haltOnFailure=true` at 80%
5. `OrdersIdempotencyStressTest` grep guard — exit 1 if missing

**Sibling-step regression check (course-wide):** zero regressions across M5 + M6 non-regenerated steps.

**Browser smoke (Claude Preview):** the harness requires sign-in to render gated step content; routing through `#created-e54e7d6f51cf/23205/85128` lands on a sign-in page instead of the step content (auth wall is intentional product behavior, not a bug). API-layer evidence is sufficient to verify the regen content; browser smoke would only verify rendering, which v3 already covered.
