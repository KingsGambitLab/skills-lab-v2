# Senior Spring Boot Engineer — Domain Re-Review (v3)
**Course:** "Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows"
**Course ID:** `created-e54e7d6f51cf`
**Repo:** `https://github.com/tusharbisht/jspring-course-repo` (7 branches confirmed)
**Reviewer lens:** 8+ yrs Java/Spring Boot in prod (FAANG / fintech / payments). Re-walk #3 after the morning's SHIP-WITH-FIXES (v1) → afternoon's PARTIAL (v2) → tonight's post-regen sweep + repo gate push (v3).
**Date:** 2026-04-25 (evening; v2: `domain_expert_jspring_v2_2026-04-25.md`; v1: `domain_expert_jspring_2026-04-25.md`)

---

## TL;DR

**Verdict: SHIP-WITH-MINOR-FIXES.** The 6 regenerated steps (85124, 85125, 85127, 85128, 85118, 85129) closed every one of the 8 morning P0s on the content side. The pom.xml plugin trio (Spotless + Checkstyle + JaCoCo) is genuinely consistent across all 7 branches (verified via `gh api`). The capstone gate `lab-grade.yml` is real, runs all 5 named gates, and reads exactly as v2 quoted it.

**However, two material claims in the user's brief overstate what shipped:**

1. **The "5 GitHub Actions gates pushed to all 7 module branches" claim is false on its face** — `lab-grade.yml` exists on `module-6-capstone` ONLY. `gh api .../contents/.github/workflows?ref=<branch>` returns HTTP 404 for the other 6 branches. The "5 gates" are 5 STEPS within the single capstone workflow, not 5 separate workflow files; and the workflow lives on one branch, not seven. Defensible (only the capstone branch needs to grade itself), but not what the brief said.

2. **One package-drift relic survived — M2.S2 (step 85119) still ships `com.crateflow.*` as the package convention** that the learner's CLAUDE.md should encode. M2.S1 was regenerated to `com.skillslab.jspring.*`. M2.S2 was not. Same contradiction class as the v2 M3.S1 issue — adjacent step taught a value that the canonical step bans.

Both are fixable with a single 30-sec per-step regen on 85119 + a one-line clarification on the GHA scope. After those land, this clears senior-eng bar.

---

## P0 status table (8 rows)

| # | Original P0 | Status | Verbatim evidence |
|---|---|---|---|
| **P0-1** | Slash command `{{className}}` Mustache hallucination at M3.S2 | **CLOSED** (and v2's PARTIAL on M3.S1 also closed) | M3.S1 (85123) regen: `argument-hint: [controller-class-name]` + `Audit the $ARGUMENTS Spring Boot controller for:`. Token grep across M3: `{{className}}` = 0 (was 1 in v2). M3.S2 (85124) shows `$ARGUMENTS` 2x. |
| **P0-2** | `claude @mockito-test-writer "..."` non-existent shell form | **CLOSED** | M3.S3 (85125) shows `claude --agent` 1x; "Use the mockito-test-writer subagent" natural-lang form 1x; bare `claude @name` form = 0. |
| **P0-3** | Subagent frontmatter `max_tokens: 4000` | **CLOSED** | M3.S3 frontmatter token grep: `max_tokens` = 0; `maxTurns` = 2; `model: sonnet`; `tools: [Read, Edit, Bash]`. |
| **P0-4** | Hook JSON: camelCase `preToolUse` + wrong shape | **CLOSED** | M4 grep: `preToolUse` (camelCase) = 0; `PreToolUse` (PascalCase) = 10 across S1/S2/S3; `PostToolUse` = 8; `tool_input.file_path` = 1. M4.S2 settings.json shows real array-of-matchers shape. |
| **P0-5** | `str_replace_editor` tool name in hook matchers | **CLOSED** | M4 grep: `str_replace_editor` = 0 across all 3 steps. M4.S1 hook example uses `tool_name == "Edit"` (PascalCase). |
| **P0-6** | `com.crateflow` package drift vs repo's `com.skillslab.jspring` | **PARTIAL** | M2.S1 (85118): `com.skillslab` 2x, `com.crateflow` 0 ✓. **But M2.S2 (85119, NOT regenerated) still teaches `Package layout (com.crateflow.*)` as the CLAUDE.md convention.** Same contradiction class as v2's M3.S1 finding. |
| **P0-7** | Spotless / Checkstyle / JaCoCo plugins missing | **CLOSED (all 7 branches)** | `gh api .../pom.xml?ref=<branch>` for all 7 branches: `spotless-maven-plugin = 1`, `maven-checkstyle-plugin = 1`, `jacoco-maven-plugin = 1` per branch. |
| **P0-8** | `lab-grade.yml` had no real gates beyond `mvn verify` | **CLOSED (where it lives)** | `lab-grade.yml` on `module-6-capstone` (3954 bytes, sha `a6f92ed`): 5 named gates verified via raw fetch — Testcontainers grep, Spotless, Checkstyle, full verify+JaCoCo coverage env-injected to Postgres service container, OrdersIdempotencyStressTest grep. Postgres 16-alpine. JDK 21 Temurin. |

**Score:** 7 of 8 fully closed. 1 partial. 0 net regressions vs v2 (in fact v2's NEW-P0 on M3.S1 closed cleanly).

---

## GitHub Actions workflow inventory (anonymous public read)

`.github/workflows/` exists on `module-6-capstone` ONLY (the other 6 branches return HTTP 404 from `gh api .../contents/.github/workflows?ref=<branch>`). The single workflow file is `lab-grade.yml` (3954 bytes, sha `a6f92ed75ac8bdbeb1845bf992de697e6f03acd7`).

**Inside `lab-grade.yml`, the 5 gates verbatim:**
1. **Testcontainers required (no H2 fallback):** `grep -rq "PostgreSQLContainer\|@Testcontainers" src/test/`. Exit 1 if missing.
2. **Spotless format:** `./mvnw -B spotless:check`.
3. **Checkstyle:** `./mvnw -B checkstyle:check`.
4. **Full verify + ≥80% coverage:** env-injected DATABASE_URL → Postgres service container; runs `./mvnw -B clean verify`. JaCoCo `haltOnFailure=true` at 80% bundle-instruction in pom.xml.
5. **Concurrent idempotency stress test present:** `grep -rq "OrdersIdempotencyStressTest\|concurrent.*[Ii]dempotency" src/test/`. Exit 1 if missing.

**On the user's "5 GHA gates pushed to all 7 module branches" claim:** the 5 gates are 5 STEPS within ONE workflow file. The workflow file exists on ONE branch. Comms imprecision, not fabrication — but I'd flag this in a senior eng review.

---

## Per-regenerated-step technical grading (6 steps)

### 85118 (M2.S1) "Anatomy of a great Spring Boot CLAUDE.md" — **A-**
Six-section schema. Real persona (Sofia debugging `javax.transaction.Transactional` instead of Spring's). **Explicit "never `javax.*` imports" callout (2x via grep)** — the #1 Spring Boot 3 jakarta-migration trap, first-class treatment. Package layout `com.skillslab.jspring.*` aligns with the repo's actual layout. Demerits: `Bean Validation`/`@Transactional` not named in the template; `Don't-Touch` skips Flyway migration files.

### 85124 (M3.S2) "Write /controller-review and audit UserController" — **A**
`argument-hint: [controller-class-name]` frontmatter + `$ARGUMENTS` body — verbatim correct. Slash-command teaches **5 real Spring Boot risks**: missing `@Valid` on DTOs, unhandled exceptions → wrong HTTP codes, manual auth vs `@PreAuthorize`, **N+1 query risks** (3x), missing `@Transactional` on multi-write paths. I'd ship this exact command in a real onboarding repo.

### 85125 (M3.S3) "Build a mockito-test-writer subagent" — **A-**
Frontmatter: `name`/`description`/`tools: [Read, Edit, Bash]`/`model: sonnet`/`maxTurns: 8`. All real. Three invocation forms (natural-language, `claude --agent` shell, @-mention); bare `claude @name "prompt"` = 0. **Constructor injection over `@InjectMocks` taught twice**: rubric says "constructor injection pattern (NO @InjectMocks)"; persona says "Mockito 5 with constructor injection (NOT @InjectMocks field injection)". Footnote: `claude /agents list` (P1, not P0).

### 85127 (M4.S1) "The hook contract in one page" — **A**
Real PascalCase tool names verbatim: `Edit, Write, Read, Bash, Glob, Grep, Agent, WebFetch, WebSearch, MultiEdit, NotebookEdit, plus mcp__<server>__<tool>`. Hook contract correct: stdin JSON, exit 2 = block, exit 0 = allow, exit 1 = deprecated. Real bash uses `.tool_input.file_path` + `tool_name == "Edit"`. Zero `str_replace_editor`, zero `parameters.path`.

### 85128 (M4.S2) "Wire three hooks in .claude/settings.json" — **A**
settings.json structurally correct: array-of-matchers, PascalCase keys. Python blocker reads `input_data.get('tool_name', '')` + `input_data.get('tool_input', {}).get('file_path', '')` — exact field paths, exit 2 for blocked-prod-config. **Spring Boot gotchas wired:** PostToolUse fires `./mvnw spotless:apply` after every Edit (Lombok regen + Java format); Stop fires `./mvnw test -pl :order-service` (catches "Claude broke a test it didn't run"). Missing: `UserPromptSubmit` example.

### 85129 (M4.S3) "Match 10 hook scenarios to the right event" — **A**
Five categories including **`none-use-a-CLAUDE-md-rule-instead`** ← the senior-eng pedagogy: not every concern is a hook concern. 10 scenarios cover real territory including **forbid `javax.*` imports**, **block `db/migration/V*.sql` edits** (Flyway discipline), **`@ExtendWith(MockitoExtension.class)` + constructor injection**.

### Roll-up grade: **A- (3.7 / 4.0)**

Every step teaches Spring Boot ENGINEERING (jakarta migration, Flyway, Lombok regen via Spotless, Mockito 5 constructor injection, `@Transactional` boundaries, `@Valid` Bean Validation, idempotency, Testcontainers vs H2, N+1) — not just CLI usage. The hook step (85127 + 85128) **does** wire PreToolUse/PostToolUse with realistic Spring Boot gotchas: production-config edit blocking, Spotless auto-format (catches Lombok regen), `./mvnw test -pl :order-service` on session end. Senior eng bar: cleared.

---

## Capstone-adjacent regression spot-check (2 non-regenerated steps)

**M5.S3 (85132) "Read the MCP's README + server.js":** all hallucination markers = 0. Clean.

**M6.S4 (85137) "Push branch and pass lab-grade.yml":** all hallucination markers = 0. Substantive signals: `@Valid=5, Testcontainers=3, Idempotency-Key=1, PostgreSQLContainer=2, lab-grade=4, checkstyle=2`. Gate names + test class names + Bean Validation references all aligned with the actual workflow file. **No regressions detected.**

---

## Verdict + rationale

**SHIP-WITH-MINOR-FIXES.** Two outstanding items, neither structural:

### Remaining blocker #1 (real): M2.S2 (step 85119) still teaches `com.crateflow.*`

Direct quote from step content body: *"Conventions: Package layout (com.crateflow.*), naming patterns"*

**Fix sketch (30-sec wall-clock):**
```bash
curl -X POST http://localhost:8001/api/courses/created-e54e7d6f51cf/steps/85119/regenerate \
  -H 'Content-Type: application/json' \
  -d '{"feedback": "Prior version taught Package layout (com.crateflow.*); the actual capstone repo (module-6-capstone branch) uses com.skillslab.jspring.<domain>. Align M2.S2 to com.skillslab.jspring.* so it no longer contradicts M2.S1 (canonical template, already fixed). Keep the CrateFlow narrative wrapper; fix only the package literal."}'
```

Same shape of fix as v2's NEW-P0 on M3.S1 — adjacent step missed by the named-step regen list, easy 1-step sweep to land.

### Remaining blocker #2 (comms-only): "5 GHA gates pushed to all 7 module branches" overstates

`lab-grade.yml` is on `module-6-capstone` ONLY. 6 of 7 branches have no `.github/`. The 5 "gates" are 5 steps inside one workflow file.

**Fix sketch (zero code change):** the next status note should say "5 grading gates wired into `lab-grade.yml` on the capstone branch; pom.xml plugin trio (Spotless / Checkstyle / JaCoCo) verified consistent across all 7 branches." That's literally what shipped. If the *intent* was for `lab-grade.yml` to also exist on all 7 branches, push it everywhere — but that's a feature decision, not a bug.

### Why this is ship-grade despite the two items

The catastrophic-class bugs are gone (silent hook no-fire, fictional CLI shells, plugin-missing pom errors, `{{className}}` non-substitution, ignored `max_tokens`, capstone-grades-nothing). A learner now hits ONE remaining moment of "M2.S2 says `com.crateflow` but M2.S1 says `com.skillslab` — which is it?" — a 5-10 min credibility wound, not a cliff. The capstone gate is the strongest single thing in the course; any learner who passes `lab-grade.yml` has shipped credible POST /orders code (Bean Validation + Testcontainers-Postgres + idempotency stress + Spotless + Checkstyle + 80% JaCoCo).

### Operational queue (priority order)

1. **P0** — regen step 85119 with the package-drift feedback. ~30 sec, ~$0.04. Verify `com.crateflow` count = 0 post-regen.
2. **P0 (comms)** — fix the GHA-scope claim. Update status note OR push `lab-grade.yml` to the other 6 branches.
3. **P1** — `claude /agents list` (M3.S3) shell-composability fix. Real form: `claude` → `/agents` inside session.
4. **P1** — add a `UserPromptSubmit` hook example to M4.S2 (today 3 of 4 event types have worked examples).
5. **P2** — Gate 5 in `lab-grade.yml` should also run the test (`mvn -Dtest=OrdersIdempotencyStressTest test`), not just grep that the file exists.
6. **v4 platform refactor** — package-name consistency sweep across M2-M6. Scan for `com.crateflow` in code blocks; auto-regen any step still referencing it.

### Final call

**SHIP-WITH-MINOR-FIXES.** After the M2.S2 regen + a one-line GHA-scope clarification, this clears the senior-eng bar I'd hold for putting it in front of my own team. **Do NOT ship as-is** — the M2 contradiction is a real learner-facing trust wound, and the GHA-scope claim is a real comms inaccuracy. Both are 30-min fixes. After they land, this is canonical enablement material.

---

## Evidence appendix

**API queries:** `GET http://localhost:8001/api/courses/created-e54e7d6f51cf` + `/modules/{23201..23207}` — full step content per module inspected via Python json grep.

**GitHub API via `gh api` (anonymous public):** repo confirmed public, 7 branches, default `module-0-preflight`. Workflows checked on all 7 branches (`/contents/.github/workflows?ref=<branch>`) — only `module-6-capstone` returns content. `lab-grade.yml` content fetched + base64-decoded. `pom.xml` checked on all 7 branches — Spotless/Checkstyle/JaCoCo plugin trio = 1/1/1 each.

**Token grep summary:** `{{className}}` = 0 across M3 (was 1 in v2 — closed). `preToolUse` (camelCase) = 0 across M4. `PreToolUse` (PascalCase) = 10 across M4. `str_replace_editor` = 0. `max_tokens` = 0. `maxTurns` = 2 in M3.S3. `claude /mcp list` = 0 across M5 (also closed in this sweep). `claude /agents list` = 1 in M3.S3 (P1 carryover). **`com.crateflow` package literal = 1 in M2.S2 (THE remaining P0).** `com.skillslab` = 2 in M2.S1 (canonical template — correct).

**Cross-cycle pattern (v1→v2→v3):** each cycle closes named ship-blockers and surfaces ONE remaining sibling-step contradiction caused by per-step regen scope being narrower than the contradiction's reach. v1 flagged 8 P0s; v2 closed 7 + flagged NEW-P0 on M3.S1; v3 closes M3.S1 cleanly but P0-6 flips to PARTIAL because M2.S2 is the live contradiction now. Worth queueing: a v4 "package-name consistency sweep" that scans M2-M6 for `com.crateflow` literals and auto-regens.
