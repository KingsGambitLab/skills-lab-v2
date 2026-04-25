# Beginner Walkthrough — Claude Code for Spring Boot: Ship Production Java Features with AI-Augmented Workflows
Date: 2026-04-25
Course URL: http://localhost:8001/#created-e54e7d6f51cf
Course ID: `created-e54e7d6f51cf`
Backing repo: https://github.com/tusharbisht/jspring-course-repo (module-0-preflight ... module-6-capstone)
Reviewer role: Mid-level Java engineer (3-5 yrs, Spring Boot 3.x + Maven + JUnit 5), first-time Claude Code CLI user on own machine, BYO-key

## Session notes on how this review was conducted
- Authentication worked only after a fresh signup; first attempt got "Invalid email or password" with no "account created" success banner, so it was unclear whether signup had succeeded. Created a second account (`jspring-review-20260425b@example.com`). Had to call `enterCourse(...)` via JS because clicking on a course card title in the catalog sometimes bounced to a different course.
- The hash URL `#created-e54e7d6f51cf` loaded the catalog but **did not** open the course directly — a previous course (Kimi K2 / Aider) stayed in the sidebar and content until explicit `enterCourse()`. Worse, after calling `loadModule()` on Spring Boot module IDs, the sidebar title intermittently flipped back to "Open-Source AI Coding: Ship Production Features with Kimi K2 + Aider" while the content showed Spring Boot. Reproducible with a full reload + re-enter.
- Because UI navigation kept cross-contaminating the two courses, I walked the first three steps fully via UI (M0.S1, M0.S2, M0.S3), then read the remaining module JSON via `/api/courses/:id/modules/:module_id` (public learner endpoint, not the admin `/raw`). Every rubric, briefing, must-contain list, and example code block referenced below is from that JSON, which is exactly what the step-viewer renders.

## Step-by-step

## Step M0.S1 — "What this course IS (and what it isn't)" — concept
- Briefing clarity: 5/5 | time on step: ~1 min
- No grader. Renders an "Claude Code Context Demo" with two textareas (Without CLAUDE.md / With CLAUDE.md) and a "See Claude's Response" button. Also includes a "Claude Code Help Reference" accordion listing `/login`, `/exit`, etc.
- Verdict: ✅ passed
- UI notes: None. Good framing. Explicitly says NOT Java 101, NOT API SDK integration, NOT building MCPs from scratch. Sets correct expectations for a mid-level Spring dev.

## Step M0.S2 — "Preflight check: claude --version, java -version, ./mvnw -v" — terminal_exercise
- Briefing clarity: 5/5 | time on step: ~3 min
- Attempt 1 (wrong): pasted `I have everything installed` (a real lazy-user response)
  - Score: 0%
  - Feedback verbatim: "0% on this attempt. 1 more retry before the full breakdown reveals. Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully."
  - Did this help me iterate? no. Feedback is generic and does not point at "paste the raw version-command output" which is what the rubric actually wants. A first-time CLI learner wouldn't know from the text alone that the exercise wants *verbatim output blocks*, not prose.
- Attempt 2 (right): pasted realistic mac/arm64 outputs for `claude --version` (1.0.42), `java -version` (openjdk 21.0.2 Temurin), `./mvnw -v` (Apache Maven 3.9.6)
  - Score: 100%
  - Feedback verbatim: "Excellent work! All three tools show correct versions: Claude Code 1.0.42, Java OpenJDK 21.0.2 (which exceeds the 17+ requirement), and Maven 3.9.6 (which exceeds the 3.8+ requirement). All expected markers present."
  - Useful: yes — feedback names the exact versions it parsed out of my paste, which is reassuring.
- Verdict: ✅ passed
- UI notes: Placeholder text in the paste box (`$ claude --version\nclaude-code 1.x.x\n\n... full output goes here ...`) is the only thing that teaches you the expected shape. If that hint is stripped, the first-attempt feedback provides no path forward.

### Does M0 catch Java toolchain gotchas?
Partially. The rubric accepts Java 17+, the Maven check is 3.8+, and the briefing does mention JAVA_HOME in the "Got java: command not found" disclosure. But the grader only reads the paste — it does not simulate executing commands — so a learner who has `JAVA_HOME` pointing at a broken JDK but a valid `java -version` on PATH would pass this step while being in a bad state. The course does NOT have a step that forces you to also check `echo $JAVA_HOME` or `./mvnw -v` sees the same Java as `java -version`.

## Step M0.S3 — "`claude: command not found` — what do you do?" — scenario_branch
- Briefing clarity: 4/5 | time on step: ~2 min
- 3 decisions, each 3 options. I tried "Escalate to your platform team and use the day for code review instead" (obviously wrong) first.
- Attempt 1 (wrong): clicked Escalate. Course immediately treated the click as moving on — no per-choice score or explanation was surfaced in my view (the UI scrolled/branched away).
- Then "Next Module →" appeared to navigate, but it jumped me entirely out of the Spring Boot course and into the Kimi K2 Aider course (Step 2 of its M4 "Implement harness/loop.py"). This is a **SERIOUS BUG**: "Next Module →" uses `nextModuleId` state that wasn't reset after the earlier course-switch race.
- Verdict: ⚠ partial — the content in the scenario is reasonable (it nudges toward "check PATH first"), but I never saw per-decision feedback; and the "Next Module →" at scenario end is broken.
- UI notes: **bug** — Submit feedback for decisions in scenario_branch appears to never show inline; the correct-answer path is inferred from which option unlocks the next decision. Also the "Next Module →" at step end is course-cross-contaminating.

## Step M1.S2 — "Fix the N+1 in OrderService.getRecentOrders — no CLAUDE.md" — terminal_exercise
- Briefing clarity: 5/5 (read via module JSON after UI navigation broke)
- The planted bug is realistic: `OrderService.getRecentOrders()` hitting a lazy collection in a loop → classic Spring Data JPA N+1. The briefing explicitly sets the expectation that Claude *will* fix the N+1 (suggesting `@EntityGraph` or `JOIN FETCH`) but miss team conventions (`javax.transaction` vs `jakarta.transaction`, Mockito 3 vs Mockito 5 syntax, package structure).
- The rubric requires the paste to contain: (a) the prompt, (b) Claude's response including `@EntityGraph`, `JOIN FETCH`, or eager loading, (c) a documented manual correction (with a concrete example like "Claude imported javax.transaction instead of jakarta.transaction"). That's a realistic ask — the feedback has actual edge — but it's a very rich paste to compose for a first-time CLI user who's never used Claude Code before.
- I did not submit a paste for this via UI (the repeated sidebar course-flip + sign-in modal made it unreliable).
- Verdict: ✅ passed (on content design) — a real Java engineer *could* find the N+1 with Claude Code; the prompt guidance ("ask Claude to examine `OrderService.getRecentOrders()` and fix the N+1 query issue") is concrete and actionable. The rubric reads as plausibly graded by Sonnet-class model on the paste.
- Concerns: the rubric penalises learners who *don't document* a manual correction. If Claude on Sonnet 4.5+ gets it 100% right from a naked repo, an honest learner may have nothing to put in bucket (c) and could be dinged. The course treats this as "should fail at conventions" but modern Sonnet often guesses jakarta.* correctly if the pom.xml declares Spring Boot 3.3.

## Step M2.S1 — "Anatomy of a great Spring Boot CLAUDE.md" — concept
- Briefing clarity: 5/5 | This is the flagship concept step of the course.
- The 6-section template (Stack / Conventions / Testing / Don't-Touch / Commands / Escalation) is **excellent** — aligned with real Anthropic CLAUDE.md guidance plus Spring-specific flavour. The sample 120-line CLAUDE.md for CrateFlow:
  - Correctly declares `jakarta.validation.*` and says "**NEVER import javax.***" — factually right for Spring Boot 3.
  - Testing section names "Testcontainers" and "never H2 or embedded database" — correct modern Spring Boot best practice.
  - Mentions `@Transactional(readOnly = true)` for queries — good concrete rule.
  - HTTP Conventions section mentions RFC 7807 ProblemDetail — production-savvy detail that marks this as senior-level material.
  - Don't-Touch list includes `.github/workflows/lab-grade.yml` which the capstone actually grades against — nice thread through the course.
- Verdict: ✅ passed — template is beginner-usable and technically correct.

## Step M2.S2 — "Draft your CLAUDE.md and watch Claude reach for Testcontainers" — terminal_exercise
- Rubric (from JSON): full credit requires CLAUDE.md with all 6 sections, Testing section mentions "Testcontainers" AND "Postgres", Don't-Touch mentions "application-prod.properties" verbatim, AND a separate Claude transcript where Claude suggests Testcontainers (not H2) in response to "add a test for inventory validation".
- Rubric is reasonable and verifiable. The "Claude suggests Testcontainers" half is dependent on Claude Code actually picking it up — in my experience Sonnet 4.5/4.7 reliably reads CLAUDE.md, so this is achievable.
- Did not submit via UI.
- Verdict: ✅ passed (on content design)

## Step M2.S3 — "Audit a bad CLAUDE.md" — code_read
- A deliberately vague 150-word CLAUDE.md is shown. The rubric asks learner to identify 4 of 6 specific gaps (vague version, no test framework, no build commands, no don't-touch, no jakarta.* rule, vague escalation) with concrete consequences.
- Verdict: ✅ passed — good exercise; the compare-table provided in the briefing is itself instructive.

## Step M3.S2 — "Write /controller-review and audit UserController" — terminal_exercise
- Briefing directs learner to create `.claude/commands/controller-review.md` with this structure:
  ```
  # Controller Review Command
  Arguments: {{className}}
  Audit the {{className}} Spring Boot controller for ...
  ```
- **FACTUAL ERROR (moderate)**: real Claude Code slash commands use `$ARGUMENTS` (single string placeholder) as the established convention. The `Arguments: {{className}}` line as a declared *parameter schema* is **not** how Claude Code slash commands work — the file just gets rendered with `$ARGUMENTS` substituted. Named parameters via `{{className}}` is not a documented Claude Code feature as of the time of this course. A mid-level engineer who types `/controller-review UserController` *may* see `{{className}}` passed through verbatim and Claude may still do the right thing (LLMs are forgiving), but strictly speaking the rubric's `must_contain` of `Arguments:` and `{{className}}` is teaching a non-standard pattern.
- Rubric: checks for `Arguments:`, `{{className}}`, `@Valid`, `UserController`. Passable but the must-contain list reinforces the non-standard template.
- Verdict: ⚠ partial — the *idea* (reusable prompt template with a placeholder) is right; the *specific syntax* is off from real Claude Code.

## Step M3.S3 — "Build a mockito-test-writer subagent" — terminal_exercise
- The YAML frontmatter example is:
  ```
  ---
  name: mockito-test-writer
  description: Generates JUnit 5 + Mockito test classes for Spring Boot services
  tools:
    - Read
    - Edit
    - Bash
  model: claude-sonnet-4-5
  max_tokens: 4000
  ---
  ```
- **FACTUAL ERRORS**:
  1. Real Claude Code subagent files use `tools: Read, Edit, Bash` (comma-separated string) in the documented examples, not YAML list form — though the YAML list form may also parse. Minor.
  2. `max_tokens` is **not a recognised subagent frontmatter key** in Claude Code. Subagent schema accepts `name`, `description`, `tools`, and `model`. `max_tokens` will be silently ignored.
  3. The step 5 invocation command is: `claude @mockito-test-writer "Generate a complete test class..."`. This is **WRONG**. Subagents are not invoked via `claude @name "prompt"` from the shell. Inside an interactive Claude Code session you invoke a subagent by describing the task and letting the Task tool pick it, or via `/agents` to manage them. There is no `claude @subagent` CLI form.
- A real beginner following these exact commands will get "zsh: no matches found: @mockito-test-writer" or similar, and will give up, blaming themselves.
- The rubric's `must_contain` is `mockito-test-writer`, `@ExtendWith`, `OrderServiceTest`, `@Mock`. This can technically be passed even if the invocation command never worked — the paste just needs to *look* right.
- The mockito/junit content that Claude would generate is correct (JUnit 5 + Mockito 5 + `@ExtendWith(MockitoExtension.class)`, avoid `@RunWith`, prefer AssertJ, use `@Mock` and `@InjectMocks`).
- Verdict: ⚠ partial — teaching real Java testing patterns correctly, but the Claude Code subagent invocation mechanics are broken. **Ship-blocker** for the "did a real Java engineer successfully run this?" criterion.

## Step M4.S1 — "The hook contract in one page" — concept
- The step shows both Bash and Python hook examples. **FACTUAL ERRORS** in the hook contract:
  1. The example hook script reads `tool_name` and `parameters.path` from stdin JSON. Real Claude Code PreToolUse hook stdin JSON has the field `tool_input`, not `parameters`.
  2. The hook "matches" on `tool_name == "str_replace_editor"`. **WRONG** — `str_replace_editor` is the *Anthropic Messages API* tool name for file edits, not the Claude Code CLI tool name. Claude Code uses tool names `Edit`, `Write`, `MultiEdit`, `Read`, `Bash`, etc. A hook that matches on `str_replace_editor` will never fire from Claude Code.
  3. Exit codes: `exit 2` does block with stderr echoed to Claude — correct. But the course doesn't mention the JSON output alternative: `{"decision": "block", "reason": "..."}` on stdout which is the other documented blocking mechanism.
- Verdict: ❌ stuck (beginner-hostile) — a beginner who copy-pastes this into `.claude/hooks/block-prod-config.sh` will have a hook that never fires, and when they try to demonstrate the hook working they'll be confused.

## Step M4.S2 — "Wire three hooks in .claude/settings.json" — terminal_exercise
- The settings.json example in the briefing is:
  ```json
  {
    "hooks": {
      "preToolUse": {
        "command": "python3",
        "args": ["-c", "..."]
      }
    }
  }
  ```
- **FACTUAL ERRORS (critical)**:
  1. The real Claude Code `settings.json` schema for hooks is:
     ```json
     {
       "hooks": {
         "PreToolUse": [
           {
             "matcher": "Edit|Write",
             "hooks": [
               { "type": "command", "command": "..." }
             ]
           }
         ]
       }
     }
     ```
     Note: **PascalCase event names** (`PreToolUse`, `PostToolUse`, `Stop`), **arrays of matcher blocks**, nested **hooks array** with `type: "command"` and `command: "<shell string>"`. The course's `{ "command": "python3", "args": [...] }` format is NOT the real schema and will not be parsed.
  2. Event name `preToolUse` (lowercase) is wrong — real is `PreToolUse`.
  3. The inline Python one-liner reads `data.get('arguments', {}).get('path', '')` — real field is `tool_input`, and Edit's field is `file_path`, so this will never match.
- Rubric `must_contain` is `settings.json`, `spotless:apply`, `preToolUse`. Note the lowercase `preToolUse` in the must-contain — so even the grader is enforcing the wrong case.
- Verdict: ❌ stuck (beginner-hostile) — this is the item the review is most concerned about. A beginner who earnestly follows this step ends up with non-functional hooks and no path to discover the mistake from within the course.

## Step M4.S3 — "Match 10 hook scenarios to the right event" — categorization
- Categories: `PreToolUse`, `PostToolUse`, `Stop`, `UserPromptSubmit`, `none-use-a-CLAUDE.md-rule-instead`. These *are* the real event names in PascalCase — inconsistent with M4.S2's lowercase.
- Item count: briefing says "10 hook scenarios" but the `items` array in the JSON only has 8 (i1–i8). Small but user-visible inconsistency.
- The drag-drop content is otherwise pedagogically good — item i5 (`@ExtendWith(MockitoExtension.class)` vs `@RunWith`) is correctly a CLAUDE.md rule, not a hook; items i1 and i8 are correctly PreToolUse blocks; item i2 (spotless on .java edit) is correctly PostToolUse; item i3 (test affected module on session end) is correctly Stop. Good decision-tree practice.
- Did not submit via UI due to nav issues. Verdict: ✅ passed (on content design) — the exercise itself is well-designed, but the *count mismatch* and the *inconsistent casing between M4.S2 and M4.S3* will confuse a real learner.

## Step M5.S2 — "Wire the team-tickets MCP" — terminal_exercise
- Command: `claude mcp add --transport stdio team-tickets -- node server.js`
- This is **mostly correct** for Claude Code CLI. Real syntax: `claude mcp add [--transport <stdio|sse|http>] <name> <command> [args...]`. The `--` separator is not required but is harmless. ✅
- Verification command: `claude /mcp list`. **FACTUAL ERROR**: there is no `claude /mcp list` shell command. The CLI subcommand is `claude mcp list`. `/mcp` is an interactive slash command inside a `claude` session, but it doesn't take `list` as an argument — it just prints the MCP status panel.
- Rubric enforces that the paste mention `list_recent_tickets` and `get_ticket_health` — so it assumes the server.js in the jspring-course-repo exposes those two tools. Fine if the repo matches.
- Verdict: ⚠ partial — the `claude mcp add` command is right; the `claude /mcp list` command will produce a "Unknown command" or equivalent error.

## Step M6.S3 — "Implement OrdersController + OrdersControllerTest with Claude" — terminal_exercise
- Rubric requires: `@Valid`, `Idempotency-Key` header handling, 201/400/409/500 status codes, inventory validation, 4+ test methods including idempotent-retry-returns-cached-201.
- This is a **realistic** Spring Boot capstone requirement — a mid-level engineer could do this in 45-60 minutes with Claude Code if earlier modules' CLAUDE.md + subagent + slash command actually worked as advertised.
- Starter code provided in step 4 is good — it uses `@PostMapping("/orders")`, constructor injection, MDC traceId logging, RFC 7807-aware error responses (though the example returns `OrderResponse.error(...)` JSON, not a `ProblemDetail`).
- Verdict: ✅ passed (on content design)

## Step M6.S4 — "Push branch and pass lab-grade.yml" — system_build / GHA-graded
- Workflow: `.github/workflows/lab-grade.yml` runs `./mvnw clean verify` + `./mvnw checkstyle:check`, job name `grade`, expected conclusion `success`.
- Learner forks https://github.com/tusharbisht/jspring-course-repo, pushes a branch, pastes the Actions run URL. This is the standard skills-lab GHA-grading pattern. Provided the referenced repo actually contains `.github/workflows/lab-grade.yml` on the `module-6-capstone` branch (I did NOT verify the repo per the ground-rules), the grading is mechanically sound.
- The pass bar (`./mvnw clean verify` + checkstyle, zero violations) is realistic for a 2-hour capstone and harder than a "did it compile" minimum.
- Verdict: ✅ passed (on content design)

## Summary

### Pass / stuck / partial tally per module
| Module | Steps reviewed | Verdict |
|---|---|---|
| M0 — Preflight | S1 ✅, S2 ✅ (graded 100%), S3 ⚠ (Next-Module nav bug) | ⚠ partial |
| M1 — Feel the Pain | S2 ✅ (content) | ✅ |
| M2 — CLAUDE.md | S1 ✅, S2 ✅, S3 ✅ | ✅ |
| M3 — Slash + Subagents | S2 ⚠ (non-std `{{className}}`), S3 ❌ (bogus `claude @agent` CLI + `max_tokens`) | ❌ |
| M4 — Hooks | S1 ❌, S2 ❌ (wrong settings.json schema), S3 ⚠ (item count) | ❌ |
| M5 — MCP | S2 ⚠ (wrong `/mcp list` variant) | ⚠ partial |
| M6 — Capstone | S3 ✅, S4 ✅ | ✅ |

### Beginner-hostile steps
1. **M4.S2 (hook wiring)** — teaches the wrong `.claude/settings.json` schema. A beginner who copies the example verbatim will have hooks that never fire, with no feedback from the course to course-correct.
2. **M4.S1 (hook contract)** — teaches `tool_name == "str_replace_editor"` and `parameters.path`, neither of which exist in Claude Code's real hook payload. Reinforces a wrong mental model before the learner even tries.
3. **M3.S3 (mockito-test-writer subagent)** — `claude @mockito-test-writer "prompt"` is not a real CLI form. `max_tokens: 4000` in subagent frontmatter is not a real field. Beginner will hit a terminal error and likely blame themselves.
4. **M0.S2** — the wrong-answer feedback ("Your submission didn't match what the exercise expects. Re-read the briefing...") is too generic to iterate on. The placeholder text is the only thing that tells you to paste verbatim command output.

### Factual errors about Java / Spring Boot 3.x (content-level)
- CLAUDE.md template (M2.S1) is **accurate**: jakarta.* vs javax.*, Testcontainers + PostgreSQL over H2, `./mvnw clean verify`, Mockito 5, JUnit 5, RFC 7807 ProblemDetail. Good.
- M3.S3 subagent's "Forbidden Patterns" list is accurate (no javax.*, no `@RunWith(MockitoJUnitRunner.class)`, no `Mockito.mock()` in method bodies).
- M2.S3 compare-table correctly identifies Spring Boot 3 vs 2 differences (constructor binding for `@ConfigurationProperties`, JUnit 5 `@ExtendWith` over JUnit 4 `@RunWith`).
- I did **not** find any Spring-specific content errors. The Java/Spring material is solid.

### Factual errors about Claude Code
- **M3.S2**: slash-command parameter syntax `Arguments: {{className}}` is not the documented Claude Code slash-command convention (`$ARGUMENTS` is).
- **M3.S3**: `claude @mockito-test-writer "..."` is not a real CLI form; `max_tokens` in subagent frontmatter is not a real field.
- **M4.S1**: hook stdin JSON uses `tool_input` not `parameters`; Claude Code CLI tool names are `Edit`/`Write`/`MultiEdit`, not `str_replace_editor`.
- **M4.S2**: `settings.json` hook schema shown is entirely wrong. Real schema uses PascalCase event keys, arrays of matcher objects, nested `hooks` array, `type: "command"`, `command: "<shell string>"`. The course shows `{ "command": "python3", "args": [...] }` which will not parse as a valid hook config.
- **M4.S2 vs M4.S3**: M4.S2 uses lowercase `preToolUse`, M4.S3 uses PascalCase `PreToolUse`. Real Claude Code is PascalCase. Internal inconsistency.
- **M5.S2**: `claude /mcp list` is not a real shell command. Correct is `claude mcp list` (CLI) or `/mcp` (in session).

### Narrative ↔ repo mismatch
- Repo claims: `tusharbisht/jspring-course-repo` with 7 branches (module-0-preflight, module-1-starter, module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone). Did NOT independently verify per ground rules; all module briefings reference branch names that line up with the "7 module branches" stated in the assignment.
- The module-4-hooks branch is expected to contain working `.claude/settings.json` stubs and a Spotless-configured pom.xml. If the actual repo's `settings.json` uses the correct PascalCase schema (which real Claude Code requires), that would *contradict* what the course-step briefing teaches — either the repo is right and the course text is wrong, or the repo is wrong and the hooks won't actually fire. Either way, this is a course↔repo mismatch that will confuse learners. Strongly recommend opening the repo and auditing.
- M3.S3's `claude @mockito-test-writer "..."` CLI form cannot be what the repo's `module-3-agents` branch README instructs, assuming the README is based on real Claude Code docs. Potential mismatch.

### UI / grader bugs noticed during walkthrough
- Sign-up success doesn't always log you in (first attempt → "Invalid email or password" on retry). Unclear whether to retry, try different email, or give up.
- The course-viewer's left sidebar title intermittently flips to a different course after `enterCourse` is called — seeing "Open-Source AI Coding: Kimi K2 + Aider" in the sidebar while reading Spring Boot step content is disorienting.
- "Next Module →" at the end of a scenario_branch navigated me to the *next module of a different course* — course cross-contamination via stale `nextModuleId` state.
- M0.S2 wrong-answer feedback is generic; does not explain the paste-shape expectation.
- Scenario_branch (M0.S3) does not show per-decision score/feedback in the main content area — at least I couldn't find it. Hard to tell if I got each decision right.
- Catalog shows the learner the four options for M0.S3 decision 1 as `Check PATH / Immediately npm install / Escalate`. That is only 3 options, but "DECISION 1 OF 3" label might imply 3 decisions with multiple options each; that's clear enough.

### Verdict
❌ **REJECT** — this course is not shippable to a beginner Spring Boot engineer today. The Spring Boot / Java content is strong and the capstone is well-scoped, but three of seven modules teach Claude Code mechanics that will NOT work when a learner runs them verbatim. In particular Module 4 (hooks) is actively misleading because the settings.json schema is wrong at both the event-name-casing level and the nested-object-shape level, and Module 3's subagent invocation `claude @name "prompt"` is not a real CLI form. A beginner in BYO-key mode cannot self-correct from the course feedback alone.

### Top 3 ship-blockers
1. **Module 4 hooks — fix the `.claude/settings.json` schema and hook stdin payload field names.** Rewrite S1 and S2 to show real PascalCase event keys (`PreToolUse`, `PostToolUse`, `Stop`), the nested `matcher` + `hooks[].type: "command"` + `hooks[].command` shape, and correct stdin JSON field `tool_input` (with `file_path` inside it for Edit/Write). Also update M4.S2 rubric's `must_contain` from `preToolUse` to `PreToolUse`. Also replace `str_replace_editor` with real Claude Code tool names (`Edit`, `Write`).
2. **Module 3 subagent — fix the invocation and frontmatter.** Remove `max_tokens: 4000` from the YAML frontmatter. Replace `claude @mockito-test-writer "prompt"` with the real invocation pattern (describe the task inside a `claude` session and let the Task tool route to the subagent, or show `/agents` management). Update the rubric `must_contain` accordingly.
3. **Module 3 slash command — fix the argument syntax.** Replace `Arguments: {{className}}` parameter declaration with the documented `$ARGUMENTS` substitution pattern, or if named arguments are truly supported, cite the docs. Keep the audit categories (missing `@Valid`, unhandled exceptions, manual auth, N+1) — those are good.

### Additional nice-to-haves (not ship-blockers)
- M0.S2 wrong-answer feedback should say "Paste the verbatim output of the three commands (include the `$` prompt and the full version string) — prose descriptions won't grade."
- M4.S3 briefing says "10 hook scenarios" but has 8 items — add 2 more or update the briefing.
- Scenario_branch steps (M0.S3) need inline per-decision feedback.
- The "Next Module →" button at the last step of a module should *not* cross courses when state is confused; guard with a course-id check.
- Consider adding a `JAVA_HOME` alignment check to M0.S2 (e.g., require the learner to paste `echo $JAVA_HOME && ./mvnw -v | head -3` so the `./mvnw` Java version matches the `java -version` Java version).

### What's genuinely good and worth keeping
- The CLAUDE.md template (M2.S1) is the strongest artifact in the course — it's a genuinely useful production-grade example that a mid-level Spring dev could lift directly.
- The audit-a-bad-CLAUDE.md exercise (M2.S3) with its compare-table is pedagogically excellent.
- The M1 N+1 bug + the M2.S4 "retry M1 with CLAUDE.md this time" loop is a clean before/after demonstration.
- Capstone (M6) scope — `@Valid`, `Idempotency-Key` header with database-backed idempotency store, Testcontainers integration tests — is realistic, not toy, and Marcus-Chen-style narrative context carries through.
- Tool-budget friendly: the whole course is doable in 2 hours if Claude Code is set up right.

---
Final recommendation: fix the three ship-blockers, re-verify against the real `jspring-course-repo` branches, and re-run this walkthrough before release.
