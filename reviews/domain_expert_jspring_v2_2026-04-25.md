# Senior Spring Boot Engineer — Domain Re-Review (v2)
**Course:** "Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows"
**Course ID:** `created-e54e7d6f51cf`
**Repo:** https://github.com/tusharbisht/jspring-course-repo (7 branches: module-0-preflight, module-1-starter, module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone)
**Reviewer lens:** 10+ yrs Java/Spring Boot in prod (FAANG / fintech / payments). Re-walk after the morning's SHIP-WITH-FIXES verdict. Same eng. Same bar. Different question: "did the fixes land, and is this ready to put in front of 50 engineers?"
**Date:** 2026-04-25 (afternoon re-review; original morning artifact: `domain_expert_jspring_2026-04-25.md`)

---

## Top-line verdict (revised): **SHIP-WITH-FIXES — closer, but one new P0 surfaced + one fix is incomplete**

7 of the 8 morning P0s closed cleanly with verbatim evidence. **P0-1 only PARTIALLY closed** — the fix landed at the named step (M3.S2, step 85124) but the same `{{className}}` hallucination is still live, in the SAME course, one step earlier (M3.S1, step 85123). A learner reading the course in order hits the wrong syntax in the concept step before reaching the corrected exercise step.

The repo work (P0-7 + P0-8) is genuinely solid — Spotless, Checkstyle, JaCoCo all wired, lab-grade.yml hardened to 5 real gates, all 7 branches consistent. The Creator-prompt fixes for hooks (P0-4 + P0-5) and subagents (P0-2 + P0-3) propagated correctly through per-step regen. P0-6 (package drift) closed at the canonical CLAUDE.md template step.

But the per-step regen approach left two adjacent steps with stale relic content. With M3.S1 still teaching `{{className}}` + `@InjectMocks` (the very pattern M3.S3 explicitly bans), a diligent learner WILL encounter the contradiction on the first walk through Module 3. That's the ship-blocker.

**Cost-to-fix is small** — 2-3 more per-step regens, 5-10 min wall-clock. Not a re-architecture; just finishing the propagation. After those land + a quick re-walk, this ships.

---

## Per-P0 status

### P0-1 — Slash command argument syntax — **PARTIAL**

**Morning finding:** M3.S2 demo_data taught `Arguments: {{className}}` — fictional Mustache-style substitution. Real syntax: `$ARGUMENTS` / `$0` / `$1` / `argument-hint:` frontmatter.

**Fix applied:** Per-step regen of step 85124 (M3.S2) + facts-block extension (commit 5544b70).

**Re-walk evidence — M3.S2 (step 85124):**
> ```md
> ---
> description: Audit a Spring Boot controller for production risks
> argument-hint: [controller-class-name]
> ---
> Audit the $ARGUMENTS Spring Boot controller for these production risks:
> ```
Two `$ARGUMENTS` substitutions counted. Zero `{{className}}`. Frontmatter shape correct (`description`, `argument-hint`, no body `Arguments:` line). **At step 85124, the fix is verbatim correct.**

**But — M3.S1 (step 85123, "Slash commands vs subagents vs hooks — when to use which") was NOT regenerated** and still ships the original hallucination as a teaching example:
> ```
> // .claude/commands/controller-review.md
> Audit {{className}} for:
> - Missing @Valid annotations on request DTOs
> - Unhandled exceptions (should return proper HTTP codes)
> - Manual auth checks (should use @PreAuthorize)
> - N+1 query risks in related entity fetches
>
> Usage: /controller-review OrdersController
> ```
Verified live in browser at `#created-e54e7d6f51cf/23204/0`: `hasMustache: true`, `hasArguments: false`. The learner sees `{{className}}` in the concept step, then sees `$ARGUMENTS` in the exercise step, with no narrative bridging them. They will believe both forms work.

**Verdict: PARTIAL. Re-regen step 85123 with the same facts-block-extended Creator prompt.** Verbatim broken token: `Audit {{className}} for:` at M3.S1. What should be there: `Audit $ARGUMENTS for:` (or remove the example block entirely and reference step 85124's real artifact).

---

### P0-2 — Subagent invocation forms — **CLOSED**

**Morning finding:** Course taught `claude @mockito-test-writer "..."` — a non-existent shell form.

**Fix applied:** Per-step regen of M3.S3 (step 85125) — teaches 3 valid forms.

**Re-walk evidence — M3.S3 demo_data step-by-step:**
- **Method 1: Natural language** — *"Then in the session, type: `Use the mockito-test-writer subagent to generate tests for OrderService.`"* ✓
- **Fallback @-mention** — *"Try the @-mention syntax: `@\"mockito-test-writer (agent)\" generate tests for OrderService`"* ✓
- **Method 2: Dedicated session** — *"Exit the previous session and start a new one under the agent: `$ claude --agent mockito-test-writer`"* ✓

All three forms are documented per https://code.claude.com/docs/en/sub-agents. Zero appearances of the bare `claude @name "prompt"` form anywhere in the regenerated step. The rubric also enforces this — `must_contain` includes `mockito-test-writer`, `ExtendWith`, `MockitoExtension`. **Verdict: CLOSED.**

One footnote-level note: step 85125's "Step 3: Verify Agent Registration" shows `$ claude /agents list`. That's the same composability bug as the morning's P1 on `/mcp` — `/agents` is in-session, `claude /agents list` doesn't run. Real form: `claude` (start session) → `/agents` (list inside). Not worth re-blocking ship over, but the same class of issue I flagged on `/mcp` in the morning (and that one's still live too — see "New issues observed" below).

---

### P0-3 — Subagent frontmatter `max_tokens` — **CLOSED**

**Morning finding:** Course emitted `max_tokens: 4000` in subagent frontmatter — silently ignored by Claude Code (real fields don't include it).

**Fix applied:** Per-step regen of M3.S3 — uses `maxTurns: 8` instead.

**Re-walk evidence — M3.S3 frontmatter:**
> ```yaml
> ---
> name: mockito-test-writer
> description: Generate Mockito 5 + JUnit 5 unit tests for Spring Boot service classes. Uses constructor injection patterns; avoids field injection mocks.
> tools: [Read, Edit, Bash]
> model: sonnet
> maxTurns: 8
> ---
> ```
- `maxTurns: 8` ✓ (valid documented field)
- `model: sonnet` ✓ (alias, version-stable — even better than the `claude-sonnet-4-5` literal I called out in P1 morning)
- `tools: [Read, Edit, Bash]` ✓ (PascalCase, list form, exactly correct)
- Zero `max_tokens` anywhere in the regenerated step (grep-counted: 0).

**Verdict: CLOSED.** Bonus: the rubric body explicitly mentions "maxTurns" so even if a learner pastes back a different shape, the grader catches it.

---

### P0-4 — Hook JSON shape — **CLOSED**

**Morning finding:** Course taught `preToolUse` (camelCase) with `{command, args}` object — three errors stacked: wrong case, wrong shape, wrong field path.

**Fix applied:** Per-step regen of M4.S2 (step 85128) — array of matchers, PascalCase, real field paths.

**Re-walk evidence — M4.S2 settings.json:**
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
- PascalCase: `PreToolUse`, `PostToolUse`, `Stop` ✓ (exact match to docs)
- Array-of-matchers shape ✓ (each entry has `matcher` + `hooks: [{type, command}]`)
- Field paths in the Python blocker — `input_data.get('tool_name', '')` and `input_data.get('tool_input', {}).get('file_path', '')` ✓ (matches real hook contract)
- Token grep across M4 module: `preToolUse` (camelCase) = 0; `PreToolUse` (PascalCase) = 4 in S2 + 3 in S1 = 7 occurrences; `tool_input` = 4 in S2 + 2 in S1; `file_path` = 4 in S2 + 5 in S1.
- Matches the course's own checked-in `module-6-capstone/.claude/settings.json` shape that I called out as contradicting the narrative in the morning. Narrative ↔ artifact now agree. ✓

**Verdict: CLOSED.** This was the most consequential bug of the 8 (silent hook non-firing). Fully landed.

---

### P0-5 — `str_replace_editor` tool name — **CLOSED**

**Morning finding:** Course used `str_replace_editor` in hook tool-name matchers. That's the Anthropic API tool-use type, NOT what Claude Code emits via hooks. Hook would never match.

**Fix applied:** Per-step regen of M4.S1 (step 85127) — real PascalCase tool names.

**Re-walk evidence — M4.S1 ("The hook contract in one page"):**
> *"**Real Claude Code Tool Names (PascalCase):** `Edit`, `Write`, `Read`, `Bash`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `MultiEdit`, `NotebookEdit`, plus MCP tools as `mcp__<server>__<tool>`"*

And the worked bash example:
> ```bash
> tool_name=$(echo "$input" | jq -r '.tool_name')
> file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
> event_type=$(echo "$input" | jq -r '.event_type')
>
> if [[ "$event_type" == "PreToolUse" && "$tool_name" == "Edit" ]]; then
>   if [[ "$file_path" == *"application-prod.properties" ]]; then
>     echo "🚫 BLOCKED: Never edit production config via Claude" >&2
>     exit 2
>   fi
> fi
> ```
- Token grep: `str_replace_editor` = 0 across the entire M4 module. ✓
- Tool name matched: `"Edit"` (PascalCase string literal) ✓
- Field path: `.tool_input.file_path` ✓ (real field; the morning artifact's correction)
- Exit codes correct: `exit 2` to block, `exit 0` to allow, `Exit 1` flagged as "non-blocking warning (deprecated)" — that nuance is more correct than I bothered to articulate this morning.

**Verdict: CLOSED.** Plus the M4.S1 concept now serves as a clean canonical-facts page learners can return to.

---

### P0-6 — Package drift CrateFlow vs skillslab — **CLOSED at the canonical step; PARTIAL across the module**

**Morning finding:** Course CLAUDE.md template taught `com.crateflow.orders`; repo uses `com.skillslab.jspring.<domain>`.

**Fix applied:** Per-step regen of M2.S1 (step 85118) — aligns to repo.

**Re-walk evidence — M2.S1 ("Anatomy of a great Spring Boot CLAUDE.md"):**
> *"Notice how the SkillsLab team structures their packages in `com.skillslab.jspring.*`:"*
> ```
> com.skillslab.jspring.tickets/
> ├── controller/     # REST endpoints
> ├── service/        # Business logic
> ├── repository/     # Data access
> ├── entity/         # JPA entities
> └── dto/            # Request/response objects
> ```
- M2.S1 grep: `crateflow` = 0; `skillslab` = 5. ✓
- Package structure matches `module-6-capstone/src/main/java/com/skillslab/jspring/orders/` exactly.

**Caveat — narrative drift across other M2 steps:** the **CrateFlow brand** (the fictional company / the personas Sofia Rodriguez + Marcus Chen) still appears throughout the rest of M2:
- M2.S2 (step 85119, "Draft your CLAUDE.md"): `crateflow=2`
- M2.S3 (step 85120, "Audit a bad CLAUDE.md"): `crateflow=3`
- M2.S4 (step 85121, "Retry M1's N+1 fix"): `crateflow=1`
- M2.S5 (step 85122, "Teammate pushes a CLAUDE.md rule"): `crateflow=2`
- M3 module: 6 CrateFlow references across 4 steps
- M4 module (regenerated): also still references CrateFlow

This is a brand-naming choice, not a package-namespace bug. The actual P0 was the package conflict (`com.crateflow.orders` package literal in code), and that's gone. The CrateFlow brand is fine as a fictional company narrative wrapper — IF the package examples ALL use `com.skillslab.jspring.*`. They do, at the canonical M2.S1 template. I have not exhaustively spot-checked every code snippet across all 28 steps, but the regen of M2.S1 + the alignment to the repo's actual `com.skillslab.jspring.orders` is the load-bearing fix.

**Verdict: CLOSED on the bug as scoped.** The CrateFlow narrative wrapper is a deliberate brand choice + not a package-correctness issue. Re-evaluate only if a future regen drops a `com.crateflow.*` package literal back into a code example.

---

### P0-7 — Spotless + Checkstyle + JaCoCo plugins — **CLOSED**

**Morning finding:** Course referenced `./mvnw spotless:apply` + `./mvnw checkstyle:check`; pom.xml had neither plugin. Every Maven goal the course taught would error with "no plugin found."

**Fix applied:** Spotless + Checkstyle + JaCoCo plugins added to pom.xml on all 7 branches.

**Re-walk evidence — `module-6-capstone/pom.xml`:**

Spotless plugin:
> ```xml
> <plugin>
>   <groupId>com.diffplug.spotless</groupId>
>   <artifactId>spotless-maven-plugin</artifactId>
>   <version>${spotless.version}</version>
>   <configuration>
>     <java>
>       <googleJavaFormat>
>         <version>1.22.0</version>
>         <style>GOOGLE</style>
>       </googleJavaFormat>
>       <removeUnusedImports/>
>       <importOrder/>
>       <trimTrailingWhitespace/>
>       <endWithNewline/>
>     </java>
>   </configuration>
> </plugin>
> ```

Checkstyle plugin (bound to verify phase, fails on error):
> ```xml
> <plugin>
>   <groupId>org.apache.maven.plugins</groupId>
>   <artifactId>maven-checkstyle-plugin</artifactId>
>   <version>${checkstyle.maven.version}</version>
>   <dependencies>
>     <dependency>
>       <groupId>com.puppycrawl.tools</groupId>
>       <artifactId>checkstyle</artifactId>
>       <version>${checkstyle.version}</version>
>     </dependency>
>   </dependencies>
>   <configuration>
>     <configLocation>checkstyle.xml</configLocation>
>     <consoleOutput>true</consoleOutput>
>     <failsOnError>true</failsOnError>
>   </configuration>
>   <executions>
>     <execution>
>       <id>verify-checkstyle</id>
>       <phase>verify</phase>
>       <goals><goal>check</goal></goals>
>     </execution>
>   </executions>
> </plugin>
> ```

JaCoCo plugin (80% bundle-instruction coverage gate, halt on failure):
> ```xml
> <plugin>
>   <groupId>org.jacoco</groupId>
>   <artifactId>jacoco-maven-plugin</artifactId>
>   <version>${jacoco.version}</version>
>   <executions>
>     <execution><id>prepare-agent</id><goals><goal>prepare-agent</goal></goals></execution>
>     <execution><id>report</id><phase>verify</phase><goals><goal>report</goal></goals></execution>
>     <execution>
>       <id>check-coverage</id>
>       <phase>verify</phase>
>       <goals><goal>check</goal></goals>
>       <configuration>
>         <haltOnFailure>true</haltOnFailure>
>         <rules>
>           <rule>
>             <element>BUNDLE</element>
>             <limits>
>               <limit>
>                 <counter>INSTRUCTION</counter>
>                 <value>COVEREDRATIO</value>
>                 <minimum>0.80</minimum>
>               </limit>
>             </limits>
>           </rule>
>         </rules>
>       </configuration>
>     </execution>
>   </executions>
> </plugin>
> ```

**Cross-branch consistency** — checked all 7 branches via `gh api`:
| Branch | spotless-maven-plugin | maven-checkstyle-plugin | jacoco-maven-plugin |
|---|---|---|---|
| module-0-preflight | 1 | 1 | 1 |
| module-1-starter | 1 | 1 | 1 |
| module-2-claudemd | 1 | 1 | 1 |
| module-3-agents | 1 | 1 | 1 |
| module-4-hooks | 1 | 1 | 1 |
| module-5-mcp | 1 | 1 | 1 |
| module-6-capstone | 1 | 1 | 1 |

**`checkstyle.xml`** is also checked in (top-level), with: jakarta.* enforcement (RegexpMultiline blocking `^import javax\.(servlet|persistence|validation|...)`), `UnusedImports`, `AvoidStarImport`, `FileTabCharacter`, trailing-whitespace check. Severity = error. This is exactly the kind of config a real Spring Boot 3 team checks in.

**Verdict: CLOSED.** Plugin versions are pinned (Spotless 2.43.0, Checkstyle 10.20.1 via maven-plugin 3.5.0, JaCoCo 0.8.12), Java target 21, Spring Boot 3.3.5. Modern, current, no cargo-cult.

---

### P0-8 — `lab-grade.yml` rigor — **CLOSED (very well)**

**Morning finding:** Workflow only ran `mvn clean verify`. No Testcontainers grep, no coverage gate, no concurrent-idempotency stress test. Hollow solutions could pass.

**Fix applied:** lab-grade.yml hardened — 5 gates.

**Re-walk evidence — verbatim from `module-6-capstone/.github/workflows/lab-grade.yml`:**

**Setup:** Postgres 16-alpine service container with health check, JDK 21 Temurin with Maven cache. ✓

**Gate 1 — Testcontainers required (no H2 fallback):**
> ```yaml
> if ! grep -rq "PostgreSQLContainer\|@Testcontainers" src/test/; then
>   echo "::error::Testcontainers + Postgres are required for integration tests."
>   echo "::error::H2 / in-memory DB fallback is not allowed — see CLAUDE.md Don't-Touch."
>   exit 1
> fi
> ```
This is the exact grep I asked for in the morning. ✓

**Gate 2 — Spotless format check:**
> `./mvnw -B spotless:check`

**Gate 3 — Checkstyle (jakarta.* enforcement + style):**
> `./mvnw -B checkstyle:check`

**Gate 4 — Full verify + ≥80% coverage** (env-injected DATABASE_URL → service postgres):
> ```yaml
> env:
>   DATABASE_URL: jdbc:postgresql://localhost:5432/jspring_test
>   DATABASE_USER: jspring
>   DATABASE_PASSWORD: jspring
> run: ./mvnw -B clean verify
> ```
Verify phase chains through pre-IT → IT → post-IT, then jacoco:check fails the build < 80% (haltOnFailure=true in pom). ✓

**Gate 5 — Concurrent idempotency stress test PRESENT:**
> ```yaml
> if ! grep -rq "OrdersIdempotencyStressTest\|concurrent.*[Ii]dempotency" src/test/; then
>   echo "::error::Capstone requires a concurrent-idempotency stress test."
>   echo "::error::Add OrdersIdempotencyStressTest under src/test/java/.../orders/"
>   echo "::error::asserting that 5 concurrent POSTs with the same Idempotency-Key"
>   echo "::error::produce exactly 1 row in 'orders' + identical response bodies."
>   exit 1
> fi
> ```
This is exactly the discriminator I asked for in the morning ("the test that distinguishes production code from a half-baked skeleton"). The grep accepts either the explicit class name OR the `concurrent.*[Ii]dempotency` pattern, so a learner who names their test `concurrentIdempotencyTest()` inside another file also passes. Reasonable flexibility. ✓

**Artifact uploads:** surefire-reports on failure, jacoco-coverage on success. Both present. ✓

**Verdict: CLOSED.** This is a meaningfully production-credible CI gate now. A learner who ships H2-backed tests fails Gate 1. A learner who ships zero tests passes Gate 2-3 but fails Gate 4 (coverage 0%). A learner who deletes the idempotency test fails Gate 5. The stack of 5 gates discriminates properly.

One refinement worth queuing for v3 (NOT a ship-blocker): Gate 5 only checks the stress test is *present*, not that it actually *executes correctly*. A learner could write `@Test void OrdersIdempotencyStressTest() { /* TODO */ }` — the file exists, grep matches, but the assertions don't run. The stronger gate is also `mvn -Dtest=OrdersIdempotencyStressTest test` as an explicit step that verifies it runs + the test class isn't `@Disabled`. Probably not worth fixing pre-pilot — Gate 4's coverage floor mostly catches it (a hollow stress-test file contributes 0 covered instructions).

---

## Summary table

| P0 | Morning verdict | Re-walk verdict |
|---|---|---|
| P0-1 (slash arg syntax) | ship-blocker | **PARTIAL** — fixed at M3.S2 (step 85124), still broken at M3.S1 (step 85123) |
| P0-2 (subagent invocation) | ship-blocker | **CLOSED** |
| P0-3 (max_tokens frontmatter) | ship-blocker | **CLOSED** |
| P0-4 (hook JSON shape) | ship-blocker | **CLOSED** |
| P0-5 (str_replace_editor tool name) | ship-blocker | **CLOSED** |
| P0-6 (CrateFlow vs skillslab packages) | ship-blocker | **CLOSED** at canonical step (brand wrapper preserved) |
| P0-7 (Spotless / Checkstyle missing) | ship-blocker | **CLOSED** all 7 branches |
| P0-8 (lab-grade.yml weakness) | ship-blocker | **CLOSED** 5 gates |

7 / 8 fully closed. 1 partial.

---

## New issues observed during the re-walk

### NEW-P0 — M3.S1 (step 85123) was missed by the per-step regen
**Token-count grep across M3 (live API):**
```
M3.S1 (id 85123): {{className}}=1, $ARGUMENTS=0, @InjectMocks=present, CrateFlow=2
M3.S2 (id 85124): {{className}}=0, $ARGUMENTS=2, @InjectMocks=absent     ← regenerated
M3.S3 (id 85125): {{className}}=0, $ARGUMENTS=0, @InjectMocks=banned     ← regenerated
M3.S4 (id 85126): {{className}}=0, $ARGUMENTS=0
```

Step 85123 still teaches:
- `Audit {{className}} for: ...` (the morning's P0-1 hallucination) — but framed as a slash-command example, identical to the broken pattern
- `@InjectMocks` in the subagent example body — directly contradicts step 85125's regenerated rubric ("constructor injection (NOT @InjectMocks field injection)")

**The contradiction:** a learner walks M3.S1 → reads "use `@InjectMocks`" + "Audit `{{className}}`" — then walks M3.S2 → reads `$ARGUMENTS` — then walks M3.S3 → reads "NOT @InjectMocks". Two contradictions in one module. Worse than either hallucination alone, because it actively erodes trust ("which one is right?").

**Fix:** per-step regen of step 85123 with the same Creator prompt extension that fixed 85124 + 85125. Wall-clock ~30s. After that, re-walk M3 end-to-end to confirm.

### P1 — `claude /agents list` is the same composability shape as the morning's `claude /mcp list`
Step 85125's "Step 3" says:
> ```
> $ claude /agents list
> ```
The real shell form is `claude` (start session), then `/agents` inside. There's no `claude /agents list` shell composition. Same class as the morning's `claude /mcp list` finding (P1 in the morning artifact). I'd queue both for a P1 polish pass — neither is fatal, but each costs a learner 2-5 min the first time they hit it.

### P1 — M5.S2 `claude /mcp list` (carried over)
Confirmed not regenerated this cycle. Still says `$ claude /mcp list` (real form: `claude mcp list` shell, OR `/mcp` slash inside session). Carry forward.

### P2 — `model: sonnet` alias adopted, `claude-sonnet-4-5` literal not present
The morning's P1 about model-ID drift (use the alias, not the literal) is **already fixed** — step 85125's frontmatter ships `model: sonnet`. Better than what I expected from a per-step regen.

### Note — M2.S1's six-section schema bumped from morning's six to "1. Stack / 2. Conventions / 3. Don't Touch / 4. Testing / 5. Commands / 6. Domain Context"
Morning's notes had Sections as Stack / Conventions / Testing / Don't-Touch / Commands / Escalation. Today's regenerated step swaps "Escalation" → "Domain Context". I prefer "Escalation" (when to ask a human) but "Domain Context" is also defensible (entity relationships, API contracts). Not a regression, just a delta worth flagging — the morning's reviewer might re-look and miscount.

---

## Hallucination call-outs revisited (morning's table re-checked verbatim)

| # | Where | Morning quote (verbatim) | Now |
|---|---|---|---|
| 1 | M3.S2 demo_data.instructions | `Arguments: {{className}}` | **Replaced at M3.S2** with `$ARGUMENTS` + `argument-hint:` frontmatter ✓ |
| 1b | **NEW** — M3.S1 (concept body) | `Audit {{className}} for:` | **Still present** — regen missed this step |
| 2 | M3.S3 demo_data.instructions | `$ claude @mockito-test-writer "Generate..."` | **Replaced** with 3 valid forms (natural-lang inside session, @-mention, `claude --agent <name>`) ✓ |
| 3 | M3.S3 YAML frontmatter | `max_tokens: 4000` | **Removed.** New frontmatter has `maxTurns: 8`, `model: sonnet` ✓ |
| 4 | M4.S2 settings.json | `"preToolUse": { "command": ..., "args": [...] }` | **Replaced** with `"PreToolUse": [{ "matcher": "Edit", "hooks": [{"type":"command", ...}] }]` ✓ |
| 5 | M4.S1 bash hook | `.parameters.path` | **Replaced** with `.tool_input.file_path` ✓ |
| 6 | M4.S1 bash hook | `tool_name == "str_replace_editor"` | **Replaced** with `tool_name == "Edit"` ✓ |
| 7 | M5.S2 shell | `$ claude /mcp list` | **Still present** (carried as P1 polish — not regenerated this cycle) |
| 8 | M2.S1 Commands section | `./mvnw spotless:apply` | **Now valid** — Spotless plugin in pom.xml, Spotless gate in lab-grade.yml ✓ |

7 of 8 hallucinations closed. NEW-1b is a regression-of-incompleteness (the same hallucination was introduced into a sibling step that wasn't on the morning's per-step fix list).

---

## Will my 50-engineer team be measurably more productive in 2 weeks?

**With the M3.S1 regen done: YES.**
**As-shipped right now: HOLD ONE MORE CYCLE.**

The fixes that landed this cycle covered the catastrophic-class bugs (silent hook non-firing from P0-4; subagent CLI form that doesn't exist from P0-2; pom.xml goals that error out from P0-7; capstone grader that grades nothing from P0-8). Those four were the morning's most expensive hallucinations from a productivity-cost standpoint, and they're closed.

The remaining M3.S1 issue costs a learner ~10-20 min to debug ("why did `{{className}}` not substitute?") + creates a credibility wound when M3.S1 contradicts M3.S3 on `@InjectMocks`. Across 50 engineers that's ~10-15 hrs of preventable confusion plus a meaningful trust erosion on a course whose product-market-fit hinges on AI-augmented productivity gains.

**Recommendation:**
1. **Run one more per-step regen on step 85123** with the same facts-block-extended Creator prompt that fixed 85124. Roughly 30 sec of wall-clock LLM time, ~$0.04.
2. **One more re-walk** of M3 (4 steps) to confirm the contradiction is gone. 2 min of agent time.
3. **Pilot to 5 engineers** for 1 week. If pilot reports zero hook-contract / slash-command / subagent-invocation surprises, broaden to 50.
4. **Queue P1 polish** for v3: `claude /agents list` shell-composability fix at M3.S3 + `claude /mcp list` at M5.S2.

The capstone grader (P0-8 fix) is the strongest single thing in this course. A learner who passes lab-grade.yml has shipped credible POST /orders code, full stop. That's the bar I'd want my own team's PRs to clear. The course's "feel the pain → fix it → ship it" arc + a real GHA gate at the end is how I'd want AI-augmented training to work.

**Final call:** ship-with-fixes (one P0 outstanding). After step 85123 regen + M3 re-walk, this is genuine ship-as-canonical-enablement material.

---

## Evidence appendix

- **API queries:** `GET http://localhost:8001/api/courses/created-e54e7d6f51cf/modules/<mid>` for M2 (23203), M3 (23204), M4 (23205) — full step bodies inspected for tokens and rubric content.
- **Browser smoke (Claude Preview port 9101):** loaded `#created-e54e7d6f51cf/23204/0` (M3.S1) — confirmed `hasMustache: true`, `hasInjectMocks: true`, `hasArguments: false`, `hasCrateFlow: true`. Loaded other regenerated steps to confirm fixes rendered.
- **GitHub repo (`tusharbisht/jspring-course-repo`) via gh CLI:**
  - `gh api repos/.../contents/pom.xml?ref=<branch>` — fetched on all 7 branches; verified Spotless + Checkstyle + JaCoCo plugins present everywhere.
  - `gh api repos/.../contents/.github/workflows/lab-grade.yml?ref=module-6-capstone` — fetched + verified all 5 gates verbatim.
  - `gh api repos/.../contents/checkstyle.xml?ref=module-6-capstone` — fetched + verified jakarta.*-enforcement RegexpMultiline + UnusedImports + AvoidStarImport rules.
  - Branch list: `module-0-preflight`, `module-1-starter`, `module-2-claudemd`, `module-3-agents`, `module-4-hooks`, `module-5-mcp`, `module-6-capstone` — note morning artifact called these `module-2-retry` / `module-3-slash` which were the working names; today's actual branch names are `module-2-claudemd` / `module-3-agents`. Same content; just naming.
- **Token grep summary across all examined steps:**
  - `{{className}}` count: 1 (M3.S1) — the outstanding bug.
  - `$ARGUMENTS` count: 2 (M3.S2 only).
  - `max_tokens` count: 0 across module M3.
  - `maxTurns` count: 2 (M3.S3 only).
  - `preToolUse` (camelCase): 0 across M4.
  - `PreToolUse` (PascalCase): 7 across M4 steps.
  - `str_replace_editor` count: 0 across M4.
  - `tool_input.file_path` shows up as 4 references in M4.S2 + 5 in M4.S1 — correct.
- **Cross-cycle artifact:** morning's `domain_expert_jspring_2026-04-25.md` table cross-checked line-by-line against today's content. 7/8 lines flipped from broken→fixed; line 1 (P0-1) only flipped at the regenerated step, leaving sibling step 85123 unfixed.
