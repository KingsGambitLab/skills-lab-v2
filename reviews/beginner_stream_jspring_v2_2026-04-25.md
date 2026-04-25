# Beginner Re-Review (v2) — Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows

Date: 2026-04-25 (afternoon, post-fix re-review)
Course URL: http://localhost:8001/#created-e54e7d6f51cf
Course ID: `created-e54e7d6f51cf`
Backing repo: https://github.com/tusharbisht/jspring-course-repo (branches `module-0-preflight` … `module-6-capstone`)
Reviewer role: Mid-level Java engineer (3-5 yrs Spring Boot 3.x + Maven + JUnit 5), first-time Claude Code CLI user, BYO-key
Reviewer style: same as `beginner_stream_jspring_v1_2026-04-25.md` (the morning REJECT). This is the narrow re-review that focuses on whether the 3 ship-blockers are P0-closed.

## Methodology
- The course was reachable but the "Spring Boot ↔ Kimi K2 Aider" sidebar/cross-course nav-race that the morning review flagged is still live (`enterCourse('created-e54e7d6f51cf')` ended up at `#created-698e6399e3ca/23211/2`). That's a platform nav-router bug already on the deferred-followup list and NOT one of today's 3 fixes, so this re-review reads each fixed step via `GET /api/courses/created-e54e7d6f51cf/modules/{mid}` (the public learner endpoint that powers the step viewer) — same approach as the morning walkthrough. Every quote below is from the JSON the renderer consumes.
- Also walked the strong + weak grader path on M3.S3 directly via `POST /api/exercises/validate` to confirm the rubric still discriminates.
- Step-id table (course's "module 5" = M4 hooks because M0 sits at position 1 in the catalog):

| Module | Module ID | Step IDs (verified this pass) |
|---|---|---|
| M0 — Preflight | 23201 | S1 = 85111 (control) |
| M2 — CLAUDE.md | 23203 | S1 = 85118 (FIX target) |
| M3 — Slash + Subagents | 23204 | S2 = 85124 (FIX), S3 = 85125 (FIX) |
| M4 — Hooks | 23205 | S1 = 85127 (FIX), S2 = 85128 (FIX), S3 = 85129 (FIX) |
| M6 — Capstone | 23207 | S3 = 85136 (control), S4 = 85137 (control) |

---

## Morning blocker 1 — M4 hooks taught wrong `.claude/settings.json` schema

**Morning verdict (v1):** ❌ stuck. M4.S1 used `tool_name == "str_replace_editor"` + `parameters.path`. M4.S2 used flat `{ "command": "python3", "args": [...] }` under lowercase `preToolUse`. M4.S3 used PascalCase categories but the briefing said "10 hook scenarios" while the items array only had 8. Course also had cross-step casing inconsistency.

**Today's fix:** facts block extended (commit `5544b70`) + per-step regen of M4.S1/S2/S3.

### Walked: M4.S1 (step 85127) — "The hook contract in one page"

**P0 closed? ✅ YES.**

Verbatim quotes from the new content:

> `Real Claude Code Tool Names (PascalCase):` `Edit`, `Write`, `Read`, `Bash`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `MultiEdit`, `NotebookEdit`, plus MCP tools as `mcp__<server>__<tool>`

> ```json
> {
>   "tool_name": "Edit",
>   "tool_input": {
>     "file_path": "src/main/resources/application-prod.properties",
>     "new_content": "server.port=8080\n..."
>   },
>   "event_type": "PreToolUse"
> }
> ```

> ```bash
> if [[ "$event_type" == "PreToolUse" && "$tool_name" == "Edit" ]]; then
>   if [[ "$file_path" == *"application-prod.properties" ]]; then
>     echo "🚫 BLOCKED: Never edit production config via Claude" >&2
>     exit 2
>   fi
> fi
>
> if [[ "$event_type" == "PostToolUse" && "$tool_name" == "Edit" ]]; then
>   if [[ "$file_path" == *.java ]]; then
>     echo "🧹 Auto-formatting Java with Spotless..." >&2
>     ./mvnw spotless:apply -q
>   fi
> fi
> ```

Verified by grep on the step's raw JSON:
- `PreToolUse` / `PostToolUse` / `UserPromptSubmit` all present in PascalCase. ✅
- Lowercase `preToolUse` count: 0. ✅
- `str_replace_editor` count: 0. ✅
- `tool_input` present, `file_path` present. ✅
- Real Claude Code tool names (Edit/Write/Bash) all enumerated. ✅
- Exit codes correctly described: exit 0 = allow, exit 2 = block (Claude shows stderr message), exit 1 deprecated. ✅

### Walked: M4.S2 (step 85128) — "Wire three hooks in .claude/settings.json"

**P0 closed? ✅ YES.**

The settings.json the briefing tells the learner to write:

> ```json
> {
>   "hooks": {
>     "PreToolUse": [
>       {
>         "matcher": "Edit",
>         "hooks": [
>           { "type": "command", "command": "python3 .claude/hooks/block-prod-config.py" }
>         ]
>       }
>     ],
>     "PostToolUse": [
>       {
>         "matcher": "Edit",
>         "hooks": [
>           { "type": "command", "command": "./mvnw spotless:apply" }
>         ]
>       }
>     ],
>     "Stop": [
>       {
>         "hooks": [
>           { "type": "command", "command": "./mvnw test -pl :order-service" }
>         ]
>       }
>     ]
>   }
> }
> ```

This matches the real Claude Code schema exactly: PascalCase event keys, array-of-matchers shape, nested `hooks` array with `{type: "command", command: "..."}` entries.

The example Python hook reads stdin correctly:

> `tool_name = input_data.get('tool_name', '')`
>
> `file_path = input_data.get('tool_input', {}).get('file_path', '')`

`tool_input.file_path` for Edit — exactly what the morning review demanded.

The validation must_contain is now `['.claude/settings.json', 'PreToolUse', 'BLOCKED: cannot edit production config']` — PascalCase `PreToolUse`, NOT the morning's lowercase `preToolUse`. ✅

The grader rubric itself instructs:

> "if camelCase hook names are used instead of PascalCase" → partial credit reduction

so the grader actively penalises the old wrong shape. ✅

Greps on the JSON:
- `PreToolUse` / `PostToolUse` / `Stop` all present. ✅
- Lowercase `preToolUse` count: 0. ✅
- `matcher` key present. ✅
- Old broken shape `{"command": "python3", "args": [...]}` NOT present. ✅
- `tool_input` and `file_path` present. ✅
- `str_replace_editor` count: 0. ✅

### Walked: M4.S3 (step 85129) — "Match 10 hook scenarios to the right event"

**P0 closed? ✅ YES.**

categories (verbatim from `demo_data.categories`):

> `["PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit", "none-use-a-CLAUDE-md-rule-instead"]`

items count: **10** (was 8 in v1). ids: `i1, i2, i3, i4, i5, i6, i7, i8, i9, i10`.

The two new items (i9, i10) sample:

> i9: "Show learner ./mvnw verify output before exit, even if all tools succeeded"
> i10: "Always pair @ExtendWith(MockitoExtension.class) with constructor injection"

i9 → `Stop` (correct — runs after session ends). i10 → `none-use-a-CLAUDE-md-rule-instead` (correct — that's a code-style convention, not a hook-able tool event). Both pedagogically clean.

Casing is now consistent with M4.S2 (both PascalCase). The morning's casing inconsistency complaint is gone.

---

## Morning blocker 2 — M3 subagent's bogus `claude @agent "prompt"` CLI form + non-existent `max_tokens` frontmatter

**Morning verdict (v1):** ❌ stuck. M3.S3 had `max_tokens: 4000` in YAML frontmatter (not a real field) and the step 5 invocation was `claude @mockito-test-writer "Generate ..."` (not a real CLI form). M3.S2 used `Arguments: {{className}}` Mustache-ish parameter declaration instead of `$ARGUMENTS`.

**Today's fix:** per-step regen of M3.S2 + M3.S3.

### Walked: M3.S2 (step 85124) — "Write /controller-review and audit UserController"

**P0 closed? ✅ YES.**

The slash-command file the briefing tells the learner to write (verbatim from `demo_data.instructions`):

> ```
> ---
> description: Audit a Spring Boot controller for production risks
> argument-hint: [controller-class-name]
> ---
> Audit the $ARGUMENTS Spring Boot controller for these production risks:
> 1. Missing @Valid annotations on request DTOs
> 2. Manual exception handling that should use @ControllerAdvice / ResponseEntityExceptionHandler
> 3. N+1 query risks via lazy JPA relationships
> 4. Missing transaction boundaries on multi-write paths
> 5. Hardcoded values that belong in application.yml
> 6. Missing security annotations (@PreAuthorize, @Secured)
> ```

> "The command uses `$ARGUMENTS` to reference whatever you type after the slash command."

That's the documented Claude Code slash-command convention exactly. Greps:
- `$ARGUMENTS` count: present. ✅
- `{{className}}` Mustache count: 0. ✅

The frontmatter also adopts the documented `argument-hint:` field, which is a nice extra (was not in the morning's version).

### Walked: M3.S3 (step 85125) — "Build a mockito-test-writer subagent"

**P0 closed? ✅ YES.**

Subagent frontmatter (verbatim):

> ```
> ---
> name: mockito-test-writer
> description: Generate Mockito 5 + JUnit 5 unit tests for Spring Boot service classes. Uses constructor injection patterns; avoids field injection mocks.
> tools: [Read, Edit, Bash]
> model: sonnet
> maxTurns: 8
> ---
> ```

`max_tokens` count in step JSON: **0**. ✅
`maxTurns` count: present. ✅
`tools` is `[Read, Edit, Bash]` — real Claude Code tool names, not `str_replace_editor`. ✅

Three valid invocation methods are now taught explicitly:

> **Method 1: Natural Language** —
> "Start a Claude session and use natural language: `$ claude` … Then in the session, type: `Use the mockito-test-writer subagent to generate tests for OrderService.`"

> **@-mention** (in-session) —
> `@"mockito-test-writer (agent)" generate tests for OrderService`

> **Method 2: Dedicated Session** —
> `$ claude --agent mockito-test-writer`

NO `claude @mockito-test-writer "..."` shell form anywhere in the step. Greps:
- `claude\s+@mockito` (the broken shell form) count: 0. ✅
- `--agent mockito-test-writer` count: present. ✅
- `str_replace_editor` count: 0. ✅

A small thing: the @-mention tutorial uses `@"mockito-test-writer (agent)"` which is the in-session disambiguation pattern. That's the documented form for cases where the subagent name collides with an MCP tool — fine to teach.

### Grader discrimination test on M3.S3

To confirm the rubric grader hadn't been weakened by the regen, I posted strong + weak responses to `POST /api/exercises/validate` for step 85125:

| Submission | Score | Feedback |
|---|---|---|
| **STRONG** — full agent .md with PascalCase tool names, `claude --agent` invocation, `OrderServiceTest.java` with `@ExtendWith(MockitoExtension.class)` + constructor injection + 4 `should_*_when_*` test methods | **1.0** ("Excellent work! … properly structured agent file with valid YAML frontmatter, successful agent invocation using the --agent flag, and a well-structured test class …") |
| **WEAK** — one-line "I tried but it didn't work." | **0.0** ("0% on this attempt. 2 more retries before the full breakdown reveals.") |

Δ = 1.0 on a 0-1 scale. Grader still discriminates cleanly. ✅

---

## Morning blocker 3 — M2 CLAUDE.md template used wrong package `com.crateflow.orders`

**Morning verdict (v1):** moderate concern flagged in the broader v1 walkthrough — repo uses `com.skillslab.jspring.<domain>` while the M2.S1 template used `com.crateflow.orders`.

**Today's fix:** per-step regen of M2.S1.

### Walked: M2.S1 (step 85118) — "Anatomy of a great Spring Boot CLAUDE.md"

**P0 closed? ✅ YES.**

Verbatim from the new content:

> "Notice how the SkillsLab team structures their packages in `com.skillslab.jspring.*`:"
>
> ```
> com.skillslab.jspring.tickets/
> ├── controller/     # REST endpoints
> ├── service/        # Business logic
> ├── repository/     # Data access
> ├── entity/         # JPA entities
> └── dto/            # Request/response objects
> ```

> "Without this in CLAUDE.md, Claude might generate `com.example.demo.tickets` or worse, mix different package patterns across files."

Greps across the entire course JSON:
- `com.crateflow` (the broken package): **0 hits**. ✅
- `com.skillslab.jspring`: **2 hits** (M2.S1 narrative + the package-tree code block). ✅
- One residual `CrateFlow` brand reference appears in the **course subtitle** ("Ship CrateFlow's production POST /orders endpoint in 2 hours …"). That's the fictional-company narrative-flavor name — NOT a Java package — and the rest of the course consistently uses `SkillsLab` as the package authority. Not a ship-blocker; arguably a brand-voice nit. Left as a minor issue below.

The other M2.S1 fundamentals are still right: `jakarta.*` import rule, Testcontainers + PostgreSQL (no H2), `@Transactional(readOnly = true)`, RFC 7807 ProblemDetail (the morning's "good things to keep"). No regressions.

---

## Repo-side verifications (jspring senior's flags)

These are the three artifacts the senior reviewer asked me to confirm at the GitHub branch level.

### `module-6-capstone/pom.xml` has Spotless plugin? ✅ YES.

```xml
<plugin>
    <groupId>com.diffplug.spotless</groupId>
    <artifactId>spotless-maven-plugin</artifactId>
    <version>${spotless.version}</version>  <!-- 2.43.0 -->
    <configuration>
        <java>
            <googleJavaFormat>
                <version>1.22.0</version>
                <style>GOOGLE</style>
            </googleJavaFormat>
            <removeUnusedImports/>
            <importOrder/>
            <trimTrailingWhitespace/>
            <endWithNewline/>
        </java>
    </configuration>
</plugin>
```

Comment in the pom.xml even references the rationale: "course's M2.S1 CLAUDE.md template references `./mvnw spotless:apply` and the M5 hooks course wires a PostToolUse hook to run it." So `./mvnw spotless:apply` will resolve cleanly when learners run it. ✅

### `module-6-capstone/pom.xml` has Checkstyle plugin? ✅ YES.

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-checkstyle-plugin</artifactId>
    <version>${checkstyle.maven.version}</version>  <!-- 3.5.0 -->
    <dependencies>
        <dependency>
            <groupId>com.puppycrawl.tools</groupId>
            <artifactId>checkstyle</artifactId>
            <version>${checkstyle.version}</version>  <!-- 10.20.1 -->
        </dependency>
    </dependencies>
    <configuration>
        <configLocation>checkstyle.xml</configLocation>
        <consoleOutput>true</consoleOutput>
        <failsOnError>true</failsOnError>
        <linkXRef>false</linkXRef>
    </configuration>
    <executions>
        <execution>
            <id>verify-checkstyle</id>
            <phase>verify</phase>
            <goals><goal>check</goal></goals>
        </execution>
    </executions>
</plugin>
```

Bound to the `verify` phase, fails on error, references a `checkstyle.xml` config in the repo root. Course's M6.S4 acceptance lists `./mvnw checkstyle:check` — this matches. ✅

### `module-6-capstone/pom.xml` JaCoCo with 80% gate? ✅ YES.

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>${jacoco.version}</version>  <!-- 0.8.12 -->
    ...
    <execution>
        <id>check-coverage</id>
        <phase>verify</phase>
        <goals><goal>check</goal></goals>
        <configuration>
            <haltOnFailure>true</haltOnFailure>
            <rules>
                <rule>
                    <element>BUNDLE</element>
                    <limits>
                        <limit>
                            <counter>INSTRUCTION</counter>
                            <value>COVEREDRATIO</value>
                            <minimum>0.80</minimum>
                        </limit>
                    </limits>
                </rule>
            </rules>
        </configuration>
    </execution>
</plugin>
```

INSTRUCTION coverage ≥ 0.80 enforced at `verify`, `haltOnFailure=true`. ✅

### `module-6-capstone/.github/workflows/lab-grade.yml` has 5 gates?

✅ YES — confirmed:

| # | Gate | Step name in workflow | Verbatim |
|---|---|---|---|
| 1 | Testcontainers required (no H2 fallback) | "Gate — Testcontainers required (no H2 fallback)" | `if ! grep -rq "PostgreSQLContainer\|@Testcontainers" src/test/; then ... exit 1; fi` |
| 2 | Spotless format check | "Gate — Spotless format" | `./mvnw -B spotless:check` |
| 3 | Checkstyle | "Gate — Checkstyle" | `./mvnw -B checkstyle:check` |
| 4 | Full verify + ≥80% JaCoCo coverage | "Gate — Full verify + ≥80% coverage" | `./mvnw -B clean verify` (jacoco:check runs in verify phase, fails build < 0.80) |
| 5 | Concurrent-idempotency stress test present | "Gate — Concurrent idempotency test present" | `if ! grep -rq "OrdersIdempotencyStressTest\|concurrent.*[Ii]dempotency" src/test/; then ... exit 1; fi` |

Comments in the workflow even cite the senior review:
> "2026-04-25 — senior review caught that a learner could swap Testcontainers for H2 and still pass."
> "2026-04-25 — senior review specifically called out: 'fire 5 concurrent POST /orders with the same Idempotency-Key, verify only one row + same response body'."

Real Postgres 16-alpine service mounted with healthcheck. JDK 21 Temurin. Surefire reports uploaded on failure, JaCoCo HTML uploaded on success. ✅

---

## Control-step regression sweep

Re-walked M0.S1 and M6.S3 / M6.S4 to confirm the regen of M2/M3/M4 didn't break anything else.

### M0.S1 (step 85111) — "What this course IS (and what it isn't)"

- Two-textarea "Without CLAUDE.md / With CLAUDE.md" demo present (`noContextPrompt` + `withContextPrompt` ids intact). ✅
- "See Claude's Response" button (`generateComparison`) intact. ✅
- "This Course Teaches You To:" 4-card grid intact. ✅
- No `com.crateflow` package reference; no `str_replace_editor`; no lowercase `preToolUse`. ✅
- Same content as the v1 walkthrough recorded. No regression.

### M6.S3 (step 85136) — "Implement OrdersController + OrdersControllerTest with Claude"

- `must_contain: ['OrdersController.java', 'OrdersControllerTest.java', '@Valid', 'Idempotency-Key']` — same as v1. ✅
- Rubric still requires 4+ test methods incl. idempotent retry path. ✅
- No regression.

### M6.S4 (step 85137) — "Push branch and pass lab-grade.yml"

- `gha_workflow_check.repo_template = "https://github.com/tusharbisht/jspring-course-repo"` ✅
- `workflow_file = "lab-grade.yml"`, `grading_job = "grade"`, `expected_conclusion = "success"`. ✅
- `instructions_md` walks: fork → clone → checkout module-6-capstone → push → paste run URL. ✅
- No regression.

---

## New issues this pass (none P0)

1. **Course subtitle still uses "CrateFlow"** ("Ship CrateFlow's production POST /orders endpoint…") while the package authority everywhere else is `SkillsLab`. This is brand-voice drift between the catalog blurb and the M2.S1 narrative ("Notice how the SkillsLab team structures their packages…"). Strictly a P2 polish nit — not a learner-blocker, since it's only the catalog subtitle and nobody types `com.crateflow` anywhere actionable. Recommend: subtitle regen OR pick one fictional company and stick with it across the course.

2. **Cross-course nav-router race still live** (already on the deferred-followup list as "nav-router state-bleed audit" — see CLAUDE.md §"v8.6.2 Phase 2"). When I called `enterCourse('created-e54e7d6f51cf')` after a fresh page load, the hash bounced to a different course id (`#created-698e6399e3ca/23211/2`). NOT one of today's three target fixes; carrying forward unchanged from the morning verdict.

3. **M0.S2 wrong-answer feedback is still generic** ("Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully."). Not addressed today. Carrying forward as P2.

4. **M5.S2 still teaches `claude /mcp list` as a shell command** (real is `claude mcp list` for shell, `/mcp` only inside session). Not on today's fix list — morning v1 already noted it as ⚠ partial. Carrying forward as P1 candidate for next regen pass.

5. **M3.S2 grader's `must_contain: ['controller', 'risk', 'line']`** is loose — three common English words; even a non-Claude paste could trip them. Not a regression (was the same in v1) and the rubric LLM-grade still discriminates, but worth tightening at next regen ("file `.claude/commands/controller-review.md`", "`$ARGUMENTS`"). P2.

---

## Summary table

| Morning blocker | P0 closed? | Evidence quote |
|---|---|---|
| #1 — M4 hooks (.claude/settings.json schema, stdin paths, real tool names, M4.S3 = 10 items) | ✅ YES | `"PreToolUse": [{"matcher": "Edit", "hooks": [{"type": "command", "command": "..."}]}]` (M4.S2) + `tool_input.file_path` reads (M4.S1, M4.S2) + `[Read, Edit, Bash]` real tool names (M4.S1) + 10 items i1–i10 (M4.S3) |
| #2 — M3 subagent / slash command (`$ARGUMENTS`, no `claude @agent "..."`, no `max_tokens`) | ✅ YES | `Audit the $ARGUMENTS Spring Boot controller…` (M3.S2) + `tools: [Read, Edit, Bash]\nmodel: sonnet\nmaxTurns: 8` (M3.S3) + `$ claude --agent mockito-test-writer` (M3.S3) — and 0 occurrences of `max_tokens`, 0 of `claude @mockito-test-writer "…"` shell form |
| #3 — M2 canonical package `com.skillslab.jspring.*` | ✅ YES | `Notice how the SkillsLab team structures their packages in com.skillslab.jspring.*` + 0 hits of `com.crateflow` package, 0 hits of any `com.crateflow.orders` |
| Repo: pom.xml Spotless plugin | ✅ YES | `<artifactId>spotless-maven-plugin</artifactId><version>2.43.0</version>` |
| Repo: pom.xml Checkstyle plugin | ✅ YES | `<artifactId>maven-checkstyle-plugin</artifactId><version>3.5.0</version>` bound to `verify` phase |
| Repo: pom.xml JaCoCo ≥80% | ✅ YES | `<minimum>0.80</minimum>` BUNDLE INSTRUCTION COVEREDRATIO with `<haltOnFailure>true</haltOnFailure>` |
| Repo: lab-grade.yml 5 gates | ✅ YES | All 5 named gate steps present (Testcontainers / Spotless / Checkstyle / verify+JaCoCo / concurrent-idempotency stress test) |
| Grader still discriminates on M3.S3 | ✅ YES | strong = 1.0, weak = 0.0, Δ = 1.0 on 0-1 scale |
| Control: M0.S1 not regressed | ✅ YES | demo widget intact, 4-card "What you'll learn" grid intact |
| Control: M6.S3 / S4 not regressed | ✅ YES | must_contain unchanged, gha_workflow_check unchanged |

---

## Final verdict

✅ **APPROVE — ship.**

All three morning P0 ship-blockers are closed by today's fixes. The new content matches real Claude Code mechanics that a beginner can actually copy-paste and have work on the first try:

- M4 hooks teaches the real `.claude/settings.json` schema (PascalCase events, array-of-matchers, nested `hooks[]` with `type: "command"` + `command: "<shell string>"`), the real stdin payload (`tool_input.file_path`), and real tool names (`Edit`, `Write`, `Bash`). The grader's must_contain enforces PascalCase. M4.S3 has the promised 10 items.
- M3 slash command uses `$ARGUMENTS` (real). M3 subagent uses `tools: [Read, Edit, Bash]` + `maxTurns: 8` (no `max_tokens`) and teaches three valid invocation methods (natural language, `@"name (agent)"` mention, `claude --agent <name>`). The bogus `claude @agent "prompt"` shell form is gone.
- M2 CLAUDE.md template uses canonical package `com.skillslab.jspring.<domain>` matching the repo. No `com.crateflow.orders` anywhere actionable.
- Backing repo's `module-6-capstone` branch has Spotless + Checkstyle + JaCoCo (with 80% gate), and lab-grade.yml runs all 5 named gates including the concurrent-idempotency stress test the senior review specifically called out.

Residual issues — course-level subtitle still says "CrateFlow", nav-router cross-course race still in flight, M5.S2 still teaches `claude /mcp list`, M0.S2 feedback still generic — are P1/P2 follow-ups, NOT ship-blockers for the beginner-Spring-Boot-engineer use case the morning REJECT was scoped to. Recommend filing them as the next iteration's regen list.

A real beginner Spring Boot engineer who walks today's course end-to-end can actually run every Claude Code mechanic the course teaches, can clone the repo and hit `./mvnw spotless:apply` / `./mvnw checkstyle:check` cleanly, and can pass the GHA capstone via the documented 5 gates. That is the bar this re-review was set at, and it is met.
