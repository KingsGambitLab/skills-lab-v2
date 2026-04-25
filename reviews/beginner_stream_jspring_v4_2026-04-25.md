# Beginner Walkthrough — Claude Code for Spring Boot — Pass v4 (post-AM regen sweep)

Date: 2026-04-25 (after 09:01:12 batch landing)
Course ID: `created-e54e7d6f51cf`
Course URL: http://localhost:8001/#created-e54e7d6f51cf
Reviewer role: Beginner Java engineer (3 years XP at a bank, comfortable with Spring Boot 2.x, has never used Claude Code, BYO-key)
Prior artifacts: `reviews/beginner_stream_jspring_v1_2026-04-25.md` (REJECT), `reviews/beginner_stream_jspring_v3_2026-04-25.md` (SHIP)
Regenerated steps in this sweep (6): `85124` (M3.S2 /controller-review), `85125` (M3.S3 mockito-test-writer subagent), `85127` (M4.S1 hook contract), `85128` (M4.S2 wire 3 hooks), `85118` (M2.S1 anatomy of CLAUDE.md), `85129` (M4.S3 categorization).
Repo: `tusharbisht/jspring-course-repo` reportedly hardened with Spotless+Checkstyle+JaCoCo+5 GHA gates pushed to all 7 module branches.

> Note on labelling: the v1 review used catalog-position labels (M0..M6). The platform stores modules at positions 1..7. So v1's "M2.S1 / M3.S2 / M3.S3 / M4.S1 / M4.S2 / M4.S3" map to actual `modules[3].steps[1] / modules[4].steps[2] / modules[4].steps[3] / modules[5].steps[1] / modules[5].steps[2] / modules[5].steps[3]` respectively. Step IDs are the source of truth; I use v1's catalog labels below for continuity.

## P0 list (verbatim from v1)

Pulled from v1's "Top 3 ship-blockers" + "Beginner-hostile steps" + "Factual errors about Claude Code" sections — every issue worded as a P0:

1. **P0-A (M4.S2 hook wiring schema)** — v1 verbatim: "Module 4 hooks — fix the `.claude/settings.json` schema and hook stdin payload field names. Rewrite S1 and S2 to show real PascalCase event keys (`PreToolUse`, `PostToolUse`, `Stop`), the nested `matcher` + `hooks[].type: \"command\"` + `hooks[].command` shape, and correct stdin JSON field `tool_input` (with `file_path` inside it for Edit/Write). Also update M4.S2 rubric's `must_contain` from `preToolUse` to `PreToolUse`. Also replace `str_replace_editor` with real Claude Code tool names (`Edit`, `Write`)."
2. **P0-B (M3.S3 subagent invocation + frontmatter)** — v1 verbatim: "Module 3 subagent — fix the invocation and frontmatter. Remove `max_tokens: 4000` from the YAML frontmatter. Replace `claude @mockito-test-writer \"prompt\"` with the real invocation pattern (describe the task inside a `claude` session and let the Task tool route to the subagent, or show `/agents` management). Update the rubric `must_contain` accordingly."
3. **P0-C (M3.S2 slash command argument syntax)** — v1 verbatim: "Module 3 slash command — fix the argument syntax. Replace `Arguments: {{className}}` parameter declaration with the documented `$ARGUMENTS` substitution pattern, or if named arguments are truly supported, cite the docs. Keep the audit categories (missing `@Valid`, unhandled exceptions, manual auth, N+1) — those are good."
4. **P0-D (M4.S1 hook contract field names)** — v1 verbatim: "M4.S1: hook stdin JSON uses `tool_input` not `parameters`; Claude Code CLI tool names are `Edit`/`Write`/`MultiEdit`, not `str_replace_editor`."
5. **P0-E (M4.S2 vs M4.S3 casing inconsistency + item count)** — v1 verbatim: "M4.S2 vs M4.S3: M4.S2 uses lowercase `preToolUse`, M4.S3 uses PascalCase `PreToolUse`. Real Claude Code is PascalCase. Internal inconsistency." Plus from M4.S3: "briefing says \"10 hook scenarios\" but the `items` array in the JSON only has 8 (i1–i8). Small but user-visible inconsistency."
6. **P0-F (M5.S2 `claude /mcp list`)** — v1 verbatim: "`claude /mcp list` is not a real shell command. Correct is `claude mcp list` (CLI) or `/mcp` (in session)." (Was ⚠ partial — counted as P0 here because v1 named it as a factual error a beginner would hit verbatim and not self-correct from.)

That's 6 P0s in v1's enumeration. Sequence below = walk each one through the regenned step content + the live UI, then a separate P2 list for v3-cosmetic items I want to re-confirm.

## Walkthrough method

1. Loaded the public learner module endpoint `GET /api/courses/created-e54e7d6f51cf/modules/{module_id}` for each regen'd module — that's the same JSON the step-viewer renders.
2. Drove the live web UI at `http://localhost:8001/#created-e54e7d6f51cf/<module_id>/<step_index>` using the Claude Preview tools, captured DOM `body.innerText` + screenshots for the 6 regen'd steps.
3. Spot-checked step 85131 (M5.S2 — MCP wiring) for P0-F via the same endpoint, even though it wasn't on the regen list, because v3 reported the platform Creator-prompt cascade fixed it.
4. UI nav still cross-contaminates — the same bug v1 reported reproduces today: 1-in-3 hash navigations bounce me from `created-e54e7d6f51cf` to `created-698e6399e3ca` (Kimi K2 course). Falling back to the public learner JSON endpoint for hard text evidence whenever the UI raced.

## Field check — `learner_surface`

The user prompt asked specifically about a `learner_surface=web` step that assumes terminal — could be a P0. I queried the admin raw payload for all 6 regen'd steps:

```
85118 (concept)            -> learner_surface field NOT present
85124 (terminal_exercise)  -> learner_surface field NOT present
85125 (terminal_exercise)  -> learner_surface field NOT present
85127 (concept)            -> learner_surface field NOT present
85128 (terminal_exercise)  -> learner_surface field NOT present
85129 (categorization)     -> learner_surface field NOT present
```

The field is unset across all 6 regen'd jspring steps (and in fact across the whole course payload — none of the 25+ steps set it). The 3 `terminal_exercise` steps render the BYO-key panel + paste-output box appropriate for terminal work, and the 2 `concept` + 1 `categorization` steps are browser-only by exercise-type design. None of the regen'd steps surface the mismatch the user warned about.

Verdict on `learner_surface`: NOT a v4 issue. (If the platform later starts emitting that field for new generations, the existing course will need a backfill, but that is a separate engineering concern.)

---

## Per-P0 verdict

### P0-A — M4.S2 hook wiring schema (step 85128)

**Status: PASS — closed.**

Verbatim evidence from `demo_data.instructions`:

```json
"PreToolUse": [
  {
    "matcher": "Edit",
    "hooks": [
      { "type": "command", "command": "python3 .claude/hooks/block-prod-config.py" }
    ]
  }
],
"PostToolUse": [
  {
    "matcher": "Edit",
    "hooks": [
      { "type": "command", "command": "./mvnw spotless:apply" }
    ]
  }
],
"Stop": [
  {
    "hooks": [
      { "type": "command", "command": "./mvnw test -pl :order-service" }
    ]
  }
]
```

This is the real Claude Code hooks schema — PascalCase event keys, array-of-matchers, nested `hooks` array with `type: "command"` + `command: "<shell string>"`. The flat `{"command": "python3", "args": [...]}` shape from v1 is gone.

Inline Python script also fixed:

```python
input_data = json.load(sys.stdin)
tool_name = input_data.get('tool_name', '')
file_path = input_data.get('tool_input', {}).get('file_path', '')
if tool_name in ['Edit', 'Write'] and 'application-prod.properties' in file_path:
    print('BLOCKED: cannot edit production config', file=sys.stderr)
    sys.exit(2)
```

`tool_input.file_path` is correct (not v1's `arguments.path`). Match list is `['Edit', 'Write']` (real tool names). Exit code 2 with stderr message is the documented blocking pattern.

`validation.must_contain` is now `[".claude/settings.json", "PreToolUse", "BLOCKED: cannot edit production config"]` — `PreToolUse` is PascalCase, matching reality. v1's `preToolUse` lowercase is gone.

Rubric explicitly enforces the fix: *"valid .claude/settings.json with PascalCase hook names (PreToolUse, PostToolUse, Stop) using the array-of-matchers format"* — *"Partial credit (0.5) if hooks are configured but not tested, or if camelCase hook names are used instead of PascalCase."*

### P0-B — M3.S3 subagent invocation + frontmatter (step 85125)

**Status: PASS — closed (with 1 P2 carryover from v3).**

Frontmatter now (verbatim):

```yaml
---
name: mockito-test-writer
description: Generate Mockito 5 + JUnit 5 unit tests for Spring Boot service classes. Uses constructor injection patterns; avoids field injection mocks.
tools: [Read, Edit, Bash]
model: sonnet
maxTurns: 8
---
```

`max_tokens` from v1 is GONE. `maxTurns: 8` is the real documented field for limiting agent conversation depth. `model: sonnet` is valid. `tools: [Read, Edit, Bash]` (YAML list) — both list and comma-separated forms parse, harmless.

Three invocation methods shown:
1. Natural language inside session: `Use the mockito-test-writer subagent to generate tests for OrderService.` — REAL pattern.
2. `@`-mention: `@"mockito-test-writer (agent)" generate tests for OrderService` — REAL pattern.
3. CLI: `claude --agent mockito-test-writer` — **NOT in official Claude Code docs** (P2, carried over from v3).

The v1 P0 was `claude @mockito-test-writer "prompt"` — that exact form is gone. P0-B is structurally closed because methods 1 and 2 are documented patterns, and a beginner who hits "unknown flag" on method 3 has methods 1+2 to fall back on. Step disclosures already prompt the reader to switch invocation forms if one fails.

`validation.must_contain` is `["mockito-test-writer", "ExtendWith", "MockitoExtension"]` — verifies the structural fix without baking in the bogus old CLI form.

### P0-C — M3.S2 slash command argument syntax (step 85124)

**Status: PASS — closed.**

Verbatim from `demo_data.instructions`:

```yaml
---
description: Audit a Spring Boot controller for production risks
argument-hint: [controller-class-name]
---
Audit the $ARGUMENTS Spring Boot controller for these production risks:
1. Missing @Valid annotations on request DTOs
2. Manual exception handling that should use @ControllerAdvice / ResponseEntityExceptionHandler
3. N+1 query risks via lazy JPA relationships
4. Missing transaction boundaries on multi-write paths
5. Hardcoded values that belong in application.yml
6. Missing security annotations (@PreAuthorize, @Secured)
```

`$ARGUMENTS` is the documented Claude Code substitution token. `argument-hint` is the documented frontmatter field for IDE/CLI autocomplete. `description` is real. v1's bogus `Arguments: {{className}}` parameter declaration is gone.

The 6 production-risk audit categories are all real Spring Boot concerns — missing `@Valid` on `@RequestBody` DTOs, manual exception handling that should be `@ControllerAdvice`/`ResponseEntityExceptionHandler`, lazy JPA N+1, missing `@Transactional` boundaries, hardcoded vs `application.yml`, missing `@PreAuthorize`/`@Secured`. The v1 reviewer's "audit categories are good" stance is preserved with stronger copy.

`validation.must_contain` is now `["controller", "risk", "line"]` — generic, no longer enforces the wrong `Arguments:` / `{{className}}` shape from v1.

### P0-D — M4.S1 hook contract field names (step 85127)

**Status: PASS — closed.**

Verbatim from the rendered concept content (web body):

> **Real Claude Code Tool Names (PascalCase):** `Edit`, `Write`, `Read`, `Bash`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `MultiEdit`, `NotebookEdit`, plus MCP tools as `mcp__<server>__<tool>`

Input JSON example shown:

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "src/main/resources/application-prod.properties",
    "new_content": "server.port=8080\n..."
  },
  "event_type": "PreToolUse"
}
```

Bash hook example reads `tool_input.file_path` and matches `tool_name == "Edit"`:

```bash
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
event_type=$(echo "$input" | jq -r '.event_type')

if [[ "$event_type" == "PreToolUse" && "$tool_name" == "Edit" ]]; then
  if [[ "$file_path" == *"application-prod.properties" ]]; then
    echo "🚫 BLOCKED: Never edit production config via Claude" >&2
    exit 2
  fi
fi
```

v1 P0 errors:
- `str_replace_editor` (Anthropic Messages API name, not Claude Code): GONE.
- `parameters.path` field: GONE.

Both replaced with the real Claude Code hook contract. Exit code semantics correct (exit 0 = allow, exit 2 = block + stderr → Claude). The "exit 1 = non-blocking warning (deprecated)" line is a small over-claim — `exit 1` was always non-blocking (it's not "deprecated", just "always was"), but a beginner won't write `exit 1` in their first hook anyway.

### P0-E — M4.S2 vs M4.S3 casing inconsistency + item count (step 85129)

**Status: PASS — closed (both legs).**

Step 85129 categories, verbatim:

```json
"categories": [
  "PreToolUse",
  "PostToolUse",
  "Stop",
  "UserPromptSubmit",
  "none-use-a-CLAUDE-md-rule-instead"
]
```

These are PascalCase, matching 85128's settings.json schema. v1's casing inconsistency (M4.S2 lowercase + M4.S3 PascalCase) is closed: 85128, 85127, AND 85129 all use PascalCase consistently.

Item count: 10 items now present (i1..i10). v1 had 8 (i1..i8). New items:
- **i9**: "Show learner ./mvnw verify output before exit, even if all tools succeeded" → `Stop` (correct — exit-time reporting)
- **i10**: "Always pair @ExtendWith(MockitoExtension.class) with constructor injection" → `none-use-a-CLAUDE-md-rule-instead` (correct — that's a stylistic rule, not a tool-event hook)

Briefing now matches reality. (i9 phrasing is slightly awkward but the categorization is correct.)

### P0-F — M5.S2 `claude /mcp list` (step 85131, NOT regen'd)

**Status: PASS — closed via cascade.**

Step 85131 was NOT on the morning regen list, but v3 hypothesized that the platform Creator-prompt tightening had cascaded a fix. Verifying now via the same module endpoint.

Verification command in `demo_data.instructions` is now `claude mcp list` (correct CLI form, not v1's bogus `claude /mcp list`). Inside-session form `/mcp tools` is also shown (which is a real interactive slash command).

Concept content above the instructions confirms: *"Running `claude mcp list` shows the team-tickets server as 'connected'"*.

`validation.must_contain` is `["team-tickets", "connected", "get_team_tickets"]` — anchored on the right output rather than the wrong CLI form.

P0-F closed. v3's cascade hypothesis confirmed.

---

## P0 closure tally

| # | P0 | Verdict |
|---|---|---|
| P0-A | M4.S2 settings.json schema + tool_input.file_path | PASS |
| P0-B | M3.S3 subagent invocation + frontmatter | PASS |
| P0-C | M3.S2 slash command `$ARGUMENTS` | PASS |
| P0-D | M4.S1 hook contract field names | PASS |
| P0-E | M4.S2/M4.S3 casing + item count | PASS |
| P0-F | M5.S2 `claude /mcp list` (cascade) | PASS |

**6/6 P0s closed.**

---

## NEW issues found in v4 walk

These are issues the regen sweep introduced or did not close. None rise to P0:

1. **NEW-P2 (85125, M3.S3)** — `claude --agent mockito-test-writer` shell flag is shown as Method 2 of agent invocation. This flag is not in the public Claude Code CLI docs at the time of writing. A beginner who runs it will get "unknown flag" or similar, then has to fall back to the in-session natural-language method (Method 1) or the `@`-mention syntax. Methods 1 + 3 are correct and sufficient on their own; Method 2 is decorative. Same issue v3 flagged as P2-1; not closed in this sweep.
2. **NEW-P2 (85125, M3.S3)** — `$ claude /agents list` is shown as a shell command. `/agents` is an in-session slash command, not a shell subcommand of `claude`. A beginner running `claude /agents list` directly will likely get an unknown-command error. v3 flagged as P2-2; not closed.
3. **NEW-P3 (85127, M4.S1)** — Line "`Exit 1 = Non-blocking warning (deprecated)`" implies exit 1 was once a real blocking mechanism. It wasn't; non-zero non-2 codes have always been non-blocking warnings. Cosmetic.
4. **NEW-P3 (85128, M4.S2)** — Inline Python hook reads `tool_input.file_path` but doesn't filter by `event_type`. The bash example in 85127 does. Inconsistent but harmless because settings.json's matcher already routes by event. v3 flagged as P2-3; not closed.
5. **NEW-P3 (85129, M4.S3, i9)** — Phrasing "Show learner ./mvnw verify output before exit, even if all tools succeeded" reads awkwardly. Categorization (Stop) is correct; copy could be tightened.

## Pre-existing P0/P1 NOT in v1 P0 list, still unfixed

These were not in the morning P0 list and are not regen'd, but a real beginner walking the course will still hit them:

- **UI nav-state bleed** — same bug v1 reported. Reproducible today: hash navigation between course IDs intermittently bounces from `created-e54e7d6f51cf` to `created-698e6399e3ca` (Kimi K2). I had to fall back to direct learner JSON endpoint to verify content for 5 of 6 regen'd steps. Course content is fine; the platform-level course-router race is unfixed. Outside the scope of "did the regen close P0s" but a real learner will lose ~30 seconds + confusion every time it triggers.
- **M0.S2 (step 85112) wrong-answer feedback still generic** — same as v1; not in P0 list, not regen'd, no improvement.

---

## Verdict — **SHIP**

All 6 P0s from v1 are closed with verbatim evidence from the regen'd step content + module-endpoint JSON. Spring Boot / Java content (the strongest part of v1) is preserved with no regression. The Claude Code mechanics that were factually wrong in v1 — settings.json schema, hook stdin payload field names, slash-command argument syntax, subagent frontmatter, MCP CLI verification — now match real Claude Code documentation.

A first-time Spring Boot engineer with BYO-key can now copy-paste the example settings.json and have hooks that actually fire. The slash-command will resolve `$ARGUMENTS` correctly. The subagent's `maxTurns: 8` will be honored; one of the 3 documented invocation methods (natural language inside `claude`) is guaranteed to work even if the `--agent` flag is not yet released. The hook scenarios drag-and-drop in M4.S3 is internally consistent with the M4.S2 settings.json above it.

Cosmetic carryovers (the `claude --agent` flag, the `$ claude /agents list` shell-vs-slash confusion, the inline-Python lacking event_type guard, the "deprecated" mis-label on exit 1) are not ship-blockers — every one has a workaround a beginner can find from the step disclosures.

## What changed since v1 (3-line summary)

1. v1 REJECT shipped because Module 4 (hooks) was teaching a fictitious settings.json schema + Module 3 was teaching `claude @<agent>` + `max_tokens` that don't exist. Today's regen replaces all three with real Claude Code constructs and the rubrics now grade against PascalCase event names + `$ARGUMENTS` + `tool_input.file_path`.
2. M4.S3 expanded from 8 items to 10 with consistent PascalCase categories, finally matching its own briefing copy and the M4.S2 settings.json above it.
3. M5.S2 (NOT in the regen list) silently inherited the platform Creator-prompt cascade — `claude /mcp list` is now `claude mcp list`. Free win.


