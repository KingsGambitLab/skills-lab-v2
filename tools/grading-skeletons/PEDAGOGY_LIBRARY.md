# hands_on Pedagogy Library — exercise archetypes for AI-native courses

This is the **reusable archetype catalog** the Creator draws from when
generating hands_on exercises. Each archetype defines:

- **Skill**: what the learner builds the muscle for
- **Hidden-test primitive**: which framework primitive carries the assertion
- **Starter shape**: how the SUT branch is mutated to create the exercise
- **README outline**: what the learner-facing problem statement looks like
- **AI-tool skill exercised**: how using Claude Code / Aider / Cursor on
  this is meaningfully different from manual code

References: `github.com/tusharbisht/claude-code-springboot-exercises` (primary
inspiration) + jspring's existing exercise-01 (this repo) + CLAUDE.md
§"BEHAVIORAL TEST HARNESS".

---

## Archetype 01 · `performance-bug-detect-and-fix`
**Skill**: spot a non-functional bug (N+1, unbounded recursion, missing index, allocation in hot loop) and apply a canonical fix.

| | |
|---|---|
| **Hidden-test primitive (Java)** | `EntityManagerFactory.unwrap(SessionFactory).getStatistics().getPrepareStatementCount() ≤ N` |
| **Hidden-test primitive (Python)** | `sqlalchemy.event.listen("before_cursor_execute", counter)`; `assert counter ≤ N` |
| **Hidden-test primitive (Node)** | `jest.spyOn(pool, "query")`; assert call count |
| **Starter shape** | Visible tests pass — the fix doesn't change return values, only query count / latency |
| **README outline** | Bug exposition · two canonical fixes (e.g. `@EntityGraph` vs `JOIN FETCH`) · pitfalls (annotation alone isn't enough; don't disable lazy globally) |
| **AI-tool skill** | Letting Claude propose the canonical pattern; reviewing the diff; rejecting non-idiomatic loops |
| **Reference** | jspring `exercise-01-fix-n-plus-one`; inspiration `exercise-03-optimize-n-plus-one` |

---

## Archetype 02 · `validation-bug-fix`
**Skill**: tighten an HTTP contract — bad input must return 400 with `errors[]`, not 500.

| | |
|---|---|
| **Hidden-test primitive** | `mockMvc.perform(post(...).content("{}")).andExpect(status().isBadRequest()).andExpect(jsonPath("$.errors").exists())` |
| **Starter shape** | Endpoint accepts no-body / missing-field requests and returns 500 (Jackson error) or silently 200 |
| **README outline** | Contract: what fields are required, what status to return on each failure mode · optional tip on `@Valid` + `@NotBlank` |
| **AI-tool skill** | Specifying the validation contract precisely; reviewing where the validator lives (DTO vs service) |
| **Reference** | inspiration `exercise-01-fix-validation-bug` |

---

## Archetype 03 · `concurrency-race-fix`
**Skill**: investigate a "flaky" symptom that's actually a race; reproduce reliably; apply a sound fix (DB constraint, optimistic lock, distributed lock).

| | |
|---|---|
| **Hidden-test primitive** | Spawn N threads via `ExecutorService` + `CountDownLatch`; assert exactly 1 success + N-1 clean 409s + ZERO 500s |
| **Starter shape** | Endpoint has no uniqueness guard; visible tests pass because they run sequentially. The "flaky" report comes via README pretending to be a Slack ticket |
| **README outline** | Symptom (Slack-style: "users sometimes see weird errors") · how to reproduce · why the race exists · where the fix should land (DB unique constraint vs service-level check vs both) · what 409 looks like |
| **AI-tool skill** | Bisecting a vague symptom; using Claude to script a concurrent repro (the meat of the lesson) |
| **Reference** | inspiration `exercise-05-investigate-vague-symptom` (HiddenConcurrencyGradingTest) |

---

## Archetype 04 · `tests-from-scratch`
**Skill**: write a thorough test suite for an existing untested class, including edge cases, error paths, and mocks.

| | |
|---|---|
| **Hidden-test primitive** | A "harness" test class that introspects the LEARNER's tests via reflection / surefire reports. Asserts: N tests exist for the target class · happy path covered · ≥2 error paths covered · uses MockBean/Mockito |
| **Starter shape** | Class exists with rich logic; no test file exists at the conventional location |
| **README outline** | What the class does · what edge cases matter (null inputs, retry on transient, idempotency) · the testing conventions to follow (constructor injection, MockBean naming) |
| **AI-tool skill** | Asking Claude to enumerate edge cases; reviewing for coverage holes; rejecting trivial assertions |
| **Reference** | inspiration `exercise-06-tests-from-scratch` (HiddenNotificationGradingTest) |

---

## Archetype 05 · `library-migration`
**Skill**: bump a major library version (Spring 3.2→3.3, Pydantic 1→2, Jest 28→29) and resolve breaking changes.

| | |
|---|---|
| **Hidden-test primitive** | Asserts the NEW behavior contract specific to the target version (e.g. RFC 7807 ProblemDetail conformance for Spring 3) — distinct from the old one. The starter has the old behavior; the migrated SUT must produce new-shape responses |
| **Starter shape** | `pom.xml` (or equivalent) is on the OLD version; SUT uses the deprecated APIs. Compile may pass but the new-version tests fail |
| **README outline** | Version targets · top 3 breaking changes (linked to release notes) · migration order (deps first → API surface → tests) |
| **AI-tool skill** | Asking Claude to read the release notes + propose the diff; reviewing each annotation/API change individually |
| **Reference** | inspiration `exercise-07-migration` (HiddenProblemDetailGradingTest — RFC 7807) |

---

## Archetype 06 · `refactor-preserving-behavior`
**Skill**: split a fat class / module into thinner units without changing behavior. Visible tests still pass.

| | |
|---|---|
| **Hidden-test primitive** | Existing integration tests still green + new structural assertions: classes ≤ N LOC · responsibilities live in expected packages · controller delegates to service (no business logic in controller) |
| **Starter shape** | A "fat" controller / service with mixed responsibilities — works correctly, just architecturally bad |
| **README outline** | Current shape · target shape (api/domain/persistence) · refactor order to keep tests green · what NOT to refactor (don't change the HTTP contract) |
| **AI-tool skill** | Plan-mode use: outline the refactor → execute incrementally → run tests between steps |
| **Reference** | inspiration `exercise-04-refactor-fat-controller` |

---

## Archetype 07 · `feature-implement-from-spec`
**Skill**: implement a NEW endpoint / feature from a written spec, including tests.

| | |
|---|---|
| **Hidden-test primitive** | MockMvc / supertest hitting the new endpoint with happy-path + edge cases; asserts response shape + status codes |
| **Starter shape** | Endpoint doesn't exist yet; relevant DTOs / repositories may or may not exist depending on scope |
| **README outline** | Feature spec (what the endpoint does, request shape, response shape, error codes) · acceptance tests in plain English |
| **AI-tool skill** | Iterating with Claude on a from-scratch implementation; using Plan to scope before coding |
| **Reference** | inspiration `exercise-02-implement-search` |

---

## Archetype 08 · `anti-exercise-when-not-to-use-claude`
**Skill**: calibration — recognize when AI assistance is overkill (typo fix, one-line config tweak, copy-paste). Don't reach for Claude reflexively.

| | |
|---|---|
| **Hidden-test primitive** | NONE. Visible failing test exists; learner reads the assertion, fixes the SUT manually in 30s. README explicitly says "do this without launching Claude" |
| **Starter shape** | Trivial bug (off-by-one, wrong constant, typo) with a CLEAR failing assertion |
| **README outline** | Why this exercise exists · the visible test signal · the 30-second fix · meta-lesson: cost-of-context-switch vs cost-of-bug |
| **AI-tool skill** | KNOWING when not to use the tool. Counter-curricular but pedagogically essential |
| **Reference** | inspiration `exercise-08-when-not-to-use-claude` |

---

## Archetype 09 · `slash-command-authoring`
**Skill**: package a Claude prompt as a parameterized slash command (`.claude/commands/<name>.md` with `$ARGUMENTS`).

| | |
|---|---|
| **Grader** | `verify.sh` script — asserts file exists at canonical path, contains `$ARGUMENTS` placeholder, has ≥4 H2 audit sections (or domain-specific shape check) |
| **Starter shape** | `.claude/commands/` directory empty or missing the target command |
| **README outline** | What the slash command does · what audit sections it should cover · how to test by running `claude /<name> SomeController` |
| **AI-tool skill** | Designing reusable Claude artifacts; thinking about parameterization |
| **Reference** | jspring `exercise-03-slash-command-controller-review` |

---

## Archetype 10 · `subagent-authoring`
**Skill**: build a custom Claude subagent (`.claude/agents/<name>.md`) with frontmatter + system prompt scoped to a narrow task.

| | |
|---|---|
| **Grader** | `verify.sh` parses YAML frontmatter (name/description/tools/model fields present) + greps body for required convention references (e.g. `MockitoExtension`, `jakarta`) |
| **Starter shape** | `.claude/agents/` empty |
| **README outline** | Subagent purpose · YAML schema · system prompt requirements (must reference current testing conventions, NOT outdated `MockitoJUnitRunner`) |
| **AI-tool skill** | Writing a system prompt that produces idiomatic output for THIS codebase's conventions |
| **Reference** | jspring `exercise-04-subagent-mockito-test-writer` |

---

## Archetype 11 · `hooks-wiring`
**Skill**: configure Claude Code's hooks contract (`.claude/settings.json`) — PreToolUse blockers + auto-formatters + PostToolUse test runners.

| | |
|---|---|
| **Grader** | `verify.sh` runs Python/jq parser on `.claude/settings.json`; asserts each required hook (matcher pattern + command) is present |
| **Starter shape** | `.claude/settings.json` empty or missing the required hooks |
| **README outline** | Hooks contract (PreToolUse vs PostToolUse, matcher syntax, exit semantics) · the 3 hooks to wire · how to test (try editing the protected file) |
| **AI-tool skill** | Constraining Claude's autonomy thoughtfully; layering safety nets without breaking flow |
| **Reference** | jspring `exercise-05-hooks-three-wired` |

---

## Archetype 12 · `mcp-wiring-and-consume`
**Skill**: register a custom MCP server with Claude Code + use its tools in a prompt.

| | |
|---|---|
| **Grader** | `verify.sh` runs `claude mcp list --json | jq` to assert the named server is connected and exposes ≥N tools |
| **Starter shape** | MCP server cloned but not registered; OR registered but without verifying connection |
| **README outline** | MCP architecture (stdio vs http) · `claude mcp add` syntax · verifying the connection · using a tool from the MCP in a prompt |
| **AI-tool skill** | Composing Claude with custom data sources; reading MCP server docs |
| **Reference** | jspring `exercise-06-mcp-team-tickets-wired` |

---

## Archetype 13 · `claude-md-authoring`
**Skill**: write a `CLAUDE.md` that gives Claude enough project context to follow the team's conventions without prompting.

| | |
|---|---|
| **Grader** | `verify.sh` asserts file exists at repo root with ≥6 H2 sections (Overview, Stack, Layout, Conventions, Testing, Workflow) + references the actual package name from the repo. Optional: deterministic Claude probe asserts Claude RECITES one convention from CLAUDE.md when asked |
| **Starter shape** | No `CLAUDE.md` at the repo root |
| **README outline** | Why CLAUDE.md matters · sections to include · how to test (start a fresh Claude session, ask "what's the testing framework?") |
| **AI-tool skill** | Compressing project context into the smallest possible doc Claude will reliably read |
| **Reference** | jspring's M3 step (planned) + inspiration's `tour/workflow/CLAUDE.md` as a reference example |

---

## Archetype 14 · `workflow-tour`
**Skill**: end-to-end use of Claude Code's full workflow palette — `/init`, plan mode, Explore agent, hooks, slash commands — in one connected session that produces a working artifact.

| | |
|---|---|
| **Grader** | `verify.sh` checks the artifact exists (e.g. `.claude/commands/run-mvn-test.md` created during the tour) + the artifact passes its own contract (uses `$ARGUMENTS`, etc.) |
| **Starter shape** | Repo with `WORKFLOW_TOUR.md` documenting the guided session; learner runs through it producing the artifact at the end |
| **README outline** | The tour script — Plan → Explore → edit → hook-trigger → slash-command-create. Each step takes ~5 min |
| **AI-tool skill** | Connecting all the primitives. Most learners use ONE primitive (Claude as Q&A); this exercise teaches the FULL palette |
| **Reference** | inspiration `tour/workflow/WORKFLOW_TOUR.md` |

---

## How the Creator picks an archetype

For each module's pedagogy goal, walk this dispatch:

1. **Performance / non-functional**: `performance-bug-detect-and-fix` (01)
2. **Concurrency / flaky symptom**: `concurrency-race-fix` (03)
3. **HTTP contract / validation**: `validation-bug-fix` (02)
4. **Test coverage gap**: `tests-from-scratch` (04)
5. **Major library bump**: `library-migration` (05)
6. **Architectural smell (fat class)**: `refactor-preserving-behavior` (06)
7. **New feature from spec**: `feature-implement-from-spec` (07)
8. **Calibration / counter-curricular**: `anti-exercise-when-not-to-use-claude` (08)
9. **AI-tool authoring (slash/subagent/hooks/MCP/CLAUDE.md)**: 09–13
10. **End-to-end Claude Code use**: `workflow-tour` (14)

A WELL-DESIGNED hands-on AI-native course has **exposure to ≥5 distinct
archetypes** across its modules, ending with at least one capstone of
type 06 or 07 plus the calibration anti-exercise (08) somewhere in the
middle.

---

## Adding a new archetype

When a course needs a pattern not covered above:

1. Add an entry here with the same 5-row schema.
2. Add a reference example: a `Hidden*GradingTest.<ext>` (or `verify.sh`)
   in `tools/grading-skeletons/<lang>/exercise-template/<archetype>/`.
3. Reference it from the Creator prompt's archetype dispatch in
   `backend/main.py` (search for "PEDAGOGY ARCHETYPES").
4. Open a PR — review the pedagogy + the test primitive together.

The library grows. The Creator picks. Course-repos materialize per-archetype
test classes from the templates. Everyone benefits from the shared shape.
