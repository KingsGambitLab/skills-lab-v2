# Senior Spring Boot Engineer — Domain Review
**Course:** "Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows"
**Course ID:** `created-e54e7d6f51cf`
**Repo:** https://github.com/tusharbisht/jspring-course-repo (branches: module-0-preflight … module-6-capstone)
**Reviewer lens:** 10+ yrs Java/Spring Boot in prod at FAANG / fintech / payments. Evaluating for rollout to ~50 engineers next quarter.
**Date:** 2026-04-25

---

## Top-line verdict: **SHIP-WITH-FIXES (P0s blocking)**

The spine is genuinely strong — CLAUDE.md anatomy, the "feel the pain then learn the fix" M1→M2 arc, the capstone skeleton (idempotency + Bean Validation + Testcontainers + jakarta.*), and the rubric grader discriminate 5× between strong and weak submissions. On that axis the course teaches the right things.

But there are four **factual hallucinations** in the Claude Code tooling (slash command arg syntax, subagent invocation, hooks JSON shape, hook input field path) that a learner following the course literally will hit walls on. And the **course narrative ↔ repo are out of sync on packages + Maven plugins**, which means a diligent engineer who authors CLAUDE.md from M2's template and cross-checks against the real repo will find contradictions. Finally the **capstone GHA workflow is too weak** to discriminate real production quality from a hollow pass.

All of this is fixable in the Creator prompt + repo + lab-grade.yml. None of it requires re-architecting the course. But it's all P0 before this goes to 50 engineers — the hallucinations will burn 20–40 min per learner per module, and the capstone-grader weakness means the course grades "does it compile" not "is it production-ready."

---

## What works (7 bullets, each grounded)

1. **M1.S1 "Context is Oxygen" side-by-side demo is the best hook I've seen for CLAUDE.md.** The without-context example shows `@RunWith(MockitoJUnitRunner.class)` + `javax.transaction.Transactional` (correct JUnit-4 smell); the with-context example shows `@ExtendWith(MockitoExtension.class)` + constructor injection + `@Valid @RequestBody CreateOrderRequest`. That mirrors the exact tooling a real Spring Boot 3.3 team has to retrain ChatGPT on. Sonnet-fresh learners will feel it.

2. **M1.S3 10-item categorization is well-calibrated.** `correct-by-luck / correct-with-edits / wrong-convention / wrong-tool / hallucinated-API` are the right buckets, and the items (`@Component` instead of `@Service`, `javax.transaction` instead of Spring's annotation, H2 instead of Testcontainers, MockMvc instead of WebTestClient, fabricated `customer.profile` relation) are realistic failure modes I'd recognize in a PR review.

3. **M2.S1 CLAUDE.md template names the right Spring Boot 3.3 primitives**: Spring Boot 3.3.4, Java 21, Maven 3.9+, JUnit 5.11, Mockito 5.x, Testcontainers, jakarta.validation.*, RFC 7807 ProblemDetail, `@Transactional(readOnly = true)`, `./mvnw clean verify`, Flyway migrations in `db/migration`. These are the right defaults. The six-section schema (Stack / Conventions / Testing / Don't-Touch / Commands / Escalation) is a pattern I'd adopt for my team CLAUDE.md verbatim.

4. **M4.S3 hook-scenario categorization teaches "use CLAUDE.md, not a hook" as a correct answer.** Items 5 and 7 (`@ExtendWith` convention, `javax.* → jakarta.*` namespace) correctly route to "none-use-a-CLAUDE.md-rule-instead." That's exactly the restraint a senior eng wants — hooks are for deterministic blocking, not style preferences.

5. **M6 capstone skeleton is pedagogically sharp.** `OrdersController.java` in `module-6-capstone` ships with a Javadoc that lists the six requirements verbatim (201/200/409, Idempotency-Key header, `idempotency_keys` Postgres table schema, @Transactional atomicity, no N+1, Testcontainers NOT H2). `OrdersControllerIntegrationTest.java` declares the 4 scenarios (happy path / validation 400 / idempotent replay 200 / idempotent conflict 409) with a failing-on-purpose `fail(...)`. A learner who implements exactly what the Javadoc says is shipping production-credible code.

6. **Rubric grader actually discriminates.** Tested M1.S2 live against the `/api/exercises/validate` endpoint: STRONG submission (named `@EntityGraph`, `@ExtendWith(MockitoExtension.class)`, jakarta swap, H2→Testcontainers, cited module-1 vs module-2 correction counts) scored **1.0**. WEAK submission (single sentence "claude said something about getRecentOrders") scored **0.21**. M2.S4: STRONG **1.0**, WEAK **0.0**. That's a 5× gap on M1.S2 and infinite gap on M2.S4 — the LLM rubric grader with `must_contain` floor is doing real work, not rubber-stamping.

7. **Anti-mock, Testcontainers stance is non-negotiable in the narrative.** M2.S1 and the M6 skeleton both explicitly ban H2 ("never H2 or embedded database") and route integration tests through `@Testcontainers` + real Postgres. That's the right call — H2's dialect drift + Postgres-specific features (JSONB, `ON CONFLICT`, idempotent upsert) mean H2 tests lie in prod. The course holds the line.

---

## P0 ship-blockers

### P0-1 — Slash command argument syntax is fictional (M3.S2)
Course teaches (M3.S2 demo_data.instructions):
```md
# Controller Review Command
Arguments: {{className}}
Audit the {{className}} Spring Boot controller...
```
Real Claude Code slash/skill syntax per https://code.claude.com/docs/en/skills: arguments are substituted via **`$ARGUMENTS`**, **`$0` / `$1` / `$N`** (positional), or named via `arguments:` frontmatter list with `$name` substitution. **`{{className}}` is not a valid token** — Claude Code does not do Mustache-style substitution. A learner typing `/controller-review UserController` gets the string `{{className}}` passed through literally.

**Fix:** In the Creator prompt + the teaching step, replace `Arguments: {{className}}` with:
```md
---
description: Audit a Spring Boot controller for prod risks
argument-hint: [controller-class-name]
---
Audit the $ARGUMENTS Spring Boot controller for these production risks:
1. Missing @Valid annotations on request DTOs...
```
Also drop the `Arguments:` body line — that's not part of the slash-command file format.

### P0-2 — Subagent invocation `claude @mockito-test-writer "..."` does not exist (M3.S3)
Course teaches:
```bash
$ claude @mockito-test-writer "Generate a complete test class for OrderService..."
```
Real invocation per https://code.claude.com/docs/en/sub-agents: either
- Natural language inside an interactive Claude session (`Use the mockito-test-writer subagent to generate...`), or
- `@"mockito-test-writer (agent)"` @-mention inside a session, or
- `claude --agent mockito-test-writer` to start a whole session under that agent.

**Bare `claude @name "prompt"` as a shell one-liner is not a documented CLI form.** The learner pastes it and gets "command not found" or @-shell expansion garbage.

### P0-3 — Subagent frontmatter has invalid `max_tokens` field (M3.S3)
Course teaches:
```yaml
---
name: mockito-test-writer
description: ...
tools:
  - Read
  - Edit
  - Bash
model: claude-sonnet-4-5
max_tokens: 4000
---
```
Real frontmatter fields per docs: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `effort`, `background`, `isolation`, `color`, `initialPrompt`. **There is no `max_tokens` field** — it's silently ignored. The `tools` field accepts a comma-separated string or YAML list; list form is fine but the YAML indentation shown works. `model: claude-sonnet-4-5` accepts full model IDs (docs explicitly show `claude-opus-4-7` as an example), so that's valid syntactically — but worth double-checking `claude-sonnet-4-5` is a shipping model when this rolls out (safer fallback: `model: sonnet`).

### P0-4 — Hook JSON shape is completely wrong (M4.S2)
Course teaches (M4.S2 demo_data.instructions):
```json
{
  "hooks": {
    "preToolUse": {
      "command": "python3",
      "args": ["-c", "import json, sys; data=json.load(sys.stdin); sys.exit(2) if data.get('tool_name')=='Edit' and 'application-prod.properties' in data.get('arguments',{}).get('path','') else sys.exit(0)"]
    }
  }
}
```
Real hook contract per https://code.claude.com/docs/en/hooks (and consistent with the course's OWN `.claude/settings.json` in `module-6-capstone`):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/block-prod-config.py" }
        ]
      }
    ]
  }
}
```
Three errors stacked:
- **`preToolUse` → `PreToolUse`** (PascalCase; camelCase is ignored — hooks silently don't fire)
- **Object with `{command, args}` → Array of `{matcher, hooks:[{type:"command", command}]}`** (entirely different shape)
- **`data.get('arguments',{}).get('path','')` → `data.get('tool_input',{}).get('file_path','')`** (real fields are `tool_name`, `tool_input.file_path` for Edit/Write)

This is the single biggest correctness bug in the course. A learner following M4.S2 verbatim gets zero hook protection on `application-prod.properties` — the hooks literally don't run. And the course's own repo ships a `.claude/settings.json` skeleton with the CORRECT PascalCase shape (`PreToolUse` as array with matcher), so the narrative and the repo are already inconsistent with each other.

### P0-5 — `str_replace_editor` tool name doesn't exist in Claude Code hook matchers (M4.S1)
Course M4.S1 shows:
```bash
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
if [[ "$tool_name" == "str_replace_editor" && ...
```
Real Claude Code tool names (per hooks docs): `Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `AskUserQuestion`, `ExitPlanMode`, plus MCP tools as `mcp__<server>__<tool>`. **`str_replace_editor`** is the Anthropic API tool-use type name (used in `anthropic-computer-use` context), NOT what Claude Code emits via hooks. The hook would never match.

### P0-6 — Narrative ↔ repo package drift (all modules)
Course M2.S1 CLAUDE.md template teaches the canonical package as:
```
com.crateflow.orders
├── controller/     # @RestController classes
├── service/        # @Service business logic
├── repository/
├── entity/
├── dto/
└── config/
```
Actual repo `module-1-starter` ships:
```
com.skillslab.jspring.order
├── Order.java
├── Customer.java
├── OrderRepository.java
├── OrderService.java
└── OrderSummary.java
```
And `module-6-capstone` uses `com.skillslab.jspring.orders` for the capstone. A learner who authors CLAUDE.md off M2.S1's example and then runs Claude against the real repo will get package-convention conflicts on every generated class. The course's OWN `CLAUDE.md-TEMPLATE` file in the repo correctly uses `com.skillslab.jspring.<domain>` — so again the narrative disagrees with the checked-in artifact.

**Fix:** Either (a) rewrite the course's CLAUDE.md template to use `com.skillslab.jspring.orders`, or (b) re-key the repo to `com.crateflow.orders`. Pick one brand and make them match.

### P0-7 — Course references `./mvnw spotless:apply` and `./mvnw checkstyle:check`, but pom.xml has neither plugin
Course M2.S1 CLAUDE.md template includes `./mvnw spotless:apply` in the Commands section. M6.S4 says "acceptance criteria: `./mvnw checkstyle:check` (code style aligned with CLAUDE.md)." M4.S2 wires a PostToolUse hook to `./mvnw spotless:apply` to auto-format after Java edits.

Actual `pom.xml` in `module-6-capstone`:
```xml
<build>
  <plugins>
    <plugin>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-maven-plugin</artifactId>
    </plugin>
  </plugins>
</build>
```
**No Spotless plugin. No Checkstyle plugin.** Every Maven goal the course tells the learner to run will emit `No plugin found for prefix 'spotless'` / `'checkstyle'`. The PostToolUse hook the course wires will fail on every file edit.

### P0-8 — `lab-grade.yml` is too weak to grade "production-ready"
Actual workflow at `module-6-capstone/.github/workflows/lab-grade.yml`:
```yaml
- name: Run full verify
  run: mvn -B -DskipITs=false clean verify
- name: Upload surefire reports on failure
  if: failure()
  ...
```
That's it. No Checkstyle gate, no JaCoCo coverage gate, no grep that Testcontainers is actually used (vs H2), no test that idempotent replay returns the cached 201 (vs a fresh 201), no concurrent-request idempotency test. A learner who ships H2-backed tests + ignores the Idempotency-Key header would pass `mvn clean verify` and pass the GHA conclusion check.

The course narrative (M6.S1, M6.S3, M6.S4) claims rigor: `Testcontainers + Postgres (NOT H2)`, `concurrent idempotent writes`, `integration test coverage ≥ 80%`, `idempotent retry returns cached 201`. The grader asserts none of that.

**Fix (minimum):**
- Add a grep step: `grep -r "PostgreSQLContainer\|@Testcontainers" src/test/ || (echo "Testcontainers not used" && exit 1)`
- Add JaCoCo with a coverage floor: `<haltOnFailure>true</haltOnFailure><rules><rule><limit><minimum>0.80</minimum></limit></rule></rules>`
- Add a smoke assertion test that fires 5 concurrent requests with the same Idempotency-Key and verifies only one row in `orders` + the same response body. This is the test that distinguishes production code from a half-baked skeleton.

---

## P1 polish

- **M0.S2 rubric** requires `openjdk version` in the paste, but Temurin prints `OpenJDK` (mixed case) and Oracle JDK prints `Java(TM) SE Runtime Environment`. Lowercase match-only will fail-by-default for Oracle JDK users. Use a case-insensitive match or accept `java version` OR `openjdk version`.
- **M3.S3 subagent example** emits the YAML frontmatter with `model: claude-sonnet-4-5`. Use `model: sonnet` (alias) instead — it's version-stable as models rev; a full model ID goes stale the next Haiku/Sonnet release.
- **M5.S2 smoke step** shows `claude /mcp list` as a shell command. The real shell command is `claude mcp list`; `/mcp` is an in-session slash command. Minor, but confuses the first run.
- **M4.S1 exit-code protocol** says `exit 1 → Hook script error (treated as allow)`. Real behavior per hooks docs: exit 1 is treated as a non-blocking error and proceeds; stderr IS forwarded to Claude. The "treated as allow" phrasing is correct but the course could call out that stderr is NOT silent — it reaches Claude as an error message, so intermittent hook crashes pollute the conversation.
- **M2.S3 bad-CLAUDE.md audit table** lists `@ConfigurationProperties(prefix="...")` as a "Spring Boot 2.x annotation." That's misleading — `prefix` attribute is valid in Spring Boot 3.3 too. The real 2→3 drift is **constructor-binding**: Boot 3 prefers `@ConfigurationProperties` on a `@ConstructorBinding`-annotated POJO + `@EnableConfigurationProperties`, without setters. Tighten the row.
- **M6.S4 checklist item c6** says `./mvnw checkstyle:check — zero violations required`. Drop this until Checkstyle is actually wired in the pom.
- **The 10-item categorization in M1.S3 only ships 8 items** in `demo_data.items`. Title promises 10. Either add 2 more or change "Sort 10 Claude outputs" to "Sort Claude outputs."
- **"Audit a bad CLAUDE.md" (M2.S3)** is a `code_read` — learner reads a weak CLAUDE.md and explains gaps. The rubric asks them to identify "at least 4 of 6 gaps." Good pedagogy, but the step ships no free-text grader binding visible from the step code; worth smoke-testing the paste flow end-to-end (I only tested M1.S2 and M2.S4 directly).
- **M5 "team-tickets" MCP is a mock ticket store.** That's fine pedagogically but weaker than wiring real Jira / Linear MCP. For a Spring Boot team already on Jira, a Jira-MCP example (even stubbed) would feel less toy.

---

## Production-grade specifics — what a senior eng might actually learn

1. **CLAUDE.md as discipline, not a cheat sheet.** The M2 six-section schema (Stack / Conventions / Testing / Don't-Touch / Commands / Escalation) is something most teams don't have even as a written-doc, let alone a CLAUDE.md. Seeing it formalized into sections where `Don't-Touch` is a ruleset, not "common sense," is the biggest pedagogical shift. My team doesn't have this; I'd adopt the template.
2. **"Feel the pain first" pedagogical flip.** Course goes M1 (no CLAUDE.md, watch it fail) → M2 (write CLAUDE.md for the repo you just failed on) → M2.S4 (retry the exact same bug and see the edit-count drop). I haven't seen that ordering elsewhere — the standard is "here's how to set up your tool, now go use it." This order produces motivational residue that carries into the capstone.
3. **Hooks as deterministic guardrails vs CLAUDE.md as prose guidance.** The M4.S3 categorization explicitly teaches "use CLAUDE.md for conventions (`jakarta.*` namespace), use hooks for destructive-action blocks (`application-prod.properties`)." That division-of-labor is something I've seen teams conflate — they write hooks for style and wonder why the hooks fire constantly.
4. **MCP for ticket context = pre-work context loading.** M5 teaches consuming an MCP to pull ticket state INTO Claude's context before the learner asks "what should I do next?" This flips the usual flow (Claude asks questions → you paste context) to (Claude reads context → you specify intent). For a team with ticket-driven development (Jira + sprint rituals), this is a non-obvious productivity lever.
5. **Capstone-as-PR ritual.** M6.S4 (fork + push + watch GHA + paste run URL) mirrors how real Spring Boot features ship at my org — GHA gate, no manual deploys. Most courses end at `./mvnw test`. This one ends at "prove your fork's GHA run is green." If the lab-grade.yml were sharpened (see P0-8), this is the bar a capstone should hit.

---

## Hallucination call-outs (verbatim quote + correct token)

| # | Where | Course says (verbatim) | Correct |
|---|---|---|---|
| 1 | M3.S2 demo_data.instructions | `Arguments: {{className}}` | `$ARGUMENTS` or `$0`/`$1` substitution; no `Arguments:` body field in the format |
| 2 | M3.S3 demo_data.instructions | `$ claude @mockito-test-writer "Generate a complete test class..."` | `@"mockito-test-writer (agent)"` inside a Claude session, OR natural-language delegation, OR `claude --agent mockito-test-writer` to session-ify |
| 3 | M3.S3 YAML frontmatter | `max_tokens: 4000` | Not a valid frontmatter field; use `maxTurns` for turn cap. `max_tokens` is silently ignored |
| 4 | M4.S2 settings.json | `"preToolUse": { "command": "python3", "args": [...] }` | `"PreToolUse": [ { "matcher": "Edit", "hooks": [ { "type": "command", "command": "..." } ] } ]` |
| 5 | M4.S1 bash hook | `file_path=$(echo "$input" \| jq -r '.parameters.path // ""')` | `.tool_input.file_path` (for Edit/Write tools) |
| 6 | M4.S1 bash hook | `tool_name == "str_replace_editor"` | `tool_name == "Edit"` or `"Write"` (Claude Code tool names, PascalCase) |
| 7 | M5.S2 shell | `$ claude /mcp list` | `claude mcp list` (shell) OR `/mcp` (slash command inside session); they're NOT composable as `claude /mcp list` |
| 8 | M2.S1 Commands section | `./mvnw spotless:apply` | Valid command pattern, BUT the course's pom.xml ships without the spotless plugin → command fails |

---

## Narrative ↔ repo coherence

Spot-checked against https://github.com/tusharbisht/jspring-course-repo (cloned locally, all 7 branches).

| Claim in course | Reality in repo | Verdict |
|---|---|---|
| N+1 planted in `OrderService.getRecentOrders()` | Present at `src/main/java/com/skillslab/jspring/order/OrderService.java:31`, with JavaDoc naming the bug + the right fix (`@EntityGraph` or `JOIN FETCH`) | ✅ MATCH |
| Package `com.crateflow.orders` (M2.S1 CLAUDE.md template) | Repo uses `com.skillslab.jspring.order` and `com.skillslab.jspring.orders` | ❌ DRIFT |
| `.claude/settings.json` has three hook stubs (M4.S2) | Present in `module-6-capstone`, uses CORRECT `PreToolUse`/`PostToolUse`/`Stop` shape (array + matcher) — contradicting M4.S2's narrative | ⚠ CONTRADICTS NARRATIVE |
| `CLAUDE.md-TEMPLATE` with 6 unfilled sections | Present, uses `com.skillslab.jspring.<domain>` in Conventions — again contradicts M2.S1 CrateFlow branding | ⚠ CONTRADICTS NARRATIVE |
| `OrdersController.java` skeleton with idempotency Javadoc | Present at `module-6-capstone/src/main/java/com/skillslab/jspring/orders/OrdersController.java`, ships with the 6 requirements + `throw new UnsupportedOperationException` body | ✅ MATCH (and good) |
| `OrdersControllerIntegrationTest.java` with 4 scenarios | Present with failing `@Test capstone_isUnfinished()` stub and the 4 scenarios in Javadoc | ✅ MATCH |
| `lab-grade.yml` runs full verify incl. ITs, asserts Testcontainers + coverage | Only runs `mvn -B -DskipITs=false clean verify` + uploads surefire on failure. No Testcontainers check, no coverage gate, no idempotency concurrent-write test | ❌ DRIFT — grader weaker than narrative promises |
| `./mvnw spotless:apply` + `./mvnw checkstyle:check` | Neither plugin is in pom.xml on any module branch | ❌ MISSING |
| MCP team-tickets server | Module-5 branch referenced but MCP server binary location is described in course as "pre-built" — I did not clone an MCP repo to verify (out of scope for time budget, but worth checking before ship) | ⚠ UNVERIFIED |

**Summary:** the spine (planted N+1, capstone skeleton, hook file stub, CLAUDE.md template file) exists. But the branding (CrateFlow vs skillslab.jspring), the Maven goals (spotless/checkstyle), and the hook JSON shape diverge between the teaching content and the checked-in artifacts. A learner who reads the course and expects the repo to line up with it WILL find contradictions. That kills trust.

---

## Will my 50-engineer team be measurably more productive in 2 weeks?

**NOT AS SHIPPED. Yes after the P0 fixes land.**

- **Where productivity gains come from:** the CLAUDE.md discipline (P1-style retrofit to any existing repo) is worth ~4 hrs / engineer / week based on the M1→M2 edit-count delta the course demonstrates. For 50 engineers × 2 weeks, that's ~400 eng-hours saved just from fewer manual corrections on Claude output. That's the real product. The capstone-ritual (GHA-gated) is worth another ~2 hrs / PR × ~3 PRs / engineer / week = 300 hrs.

- **Where productivity gets burned back:** each of the P0-1/P0-2/P0-4/P0-5 hallucinations will cost an engineer 20–40 min to diagnose ("the hook isn't firing — why?"). Four hallucinations × 50 engineers × 30 min = 100 hrs of preventable debugging. Plus the narrative-vs-repo package drift (P0-6) will cost another 15 min / engineer / module × 7 modules × 50 eng = ~90 hrs. Net, the hallucinations eat ~half the productivity gain.

- **Where it fails to be measurable:** the capstone's lab-grade.yml (P0-8) lets a hollow solution pass. I can't point to "engineer X shipped a prod-ready POST /orders" if the grader doesn't verify idempotency under concurrency + Testcontainers. That's not a 2-week-productivity issue — it's a "did the course actually deliver on its promise" issue.

**Call:** hold 1 cycle. Fix the 8 P0s (Creator-prompt changes for hallucinations + pom.xml updates + lab-grade.yml hardening + repo package rename OR narrative package rename). Ship to a 5-engineer pilot for 1 week. If pilot learners report zero hook-contract / slash-command / subagent-invocation surprises, broaden to 50. Without those fixes, the course will erode engineer trust in AI-augmented workflows — which is strictly worse than not running the course at all.

---

## Evidence appendix

- **Grader live-tested:**
  - M1.S2 (step_id 85115) STRONG paste scored **1.0**; WEAK paste scored **0.21** (5× gap). `must_contain: ["OrderService", "getRecentOrders", "Claude"]` + LLM rubric both trigger; grader feedback is concrete.
  - M2.S4 (step_id 85121) STRONG paste scored **1.0**; WEAK paste scored **0.0**. Rubric correctly demands `prompt`, `diff`, `edits`, `module` markers; grader feedback names the missing 4-of-4.
- **Repo inspected locally:** cloned `tusharbisht/jspring-course-repo`, read `module-1-starter/src/main/java/com/skillslab/jspring/order/OrderService.java` (N+1 bug confirmed planted), `module-6-capstone/src/main/java/com/skillslab/jspring/orders/OrdersController.java` (skeleton confirmed), `module-6-capstone/.github/workflows/lab-grade.yml` (workflow confirmed weak), `module-6-capstone/.claude/settings.json` (hook shape correct but contradicts M4.S2 narrative), `module-6-capstone/pom.xml` (no spotless, no checkstyle, no jacoco).
- **Claude Code docs cross-referenced:** slash/skill arg substitution (code.claude.com/docs/en/skills), subagent frontmatter + invocation (code.claude.com/docs/en/sub-agents), hook contract (code.claude.com/docs/en/hooks), MCP CLI syntax (code.claude.com/docs/en/mcp). All four hallucinations triangulated against current docs.
- **Browser smoke:** loaded M2.S1 in the Claude Preview browser; rendering correct after a reload, dark-theme compliant, no layout breaks on the CLAUDE.md template example card. The "Failed to load module" banner on first load was a router transient (page reload cleared it).
