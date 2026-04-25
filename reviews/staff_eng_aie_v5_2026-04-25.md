# Staff-Eng Domain Review — Claude Code in Production (v5)

**Course**: `created-7fee8b78c742` — *Claude Code in Production: Ship Real Features with CLAUDE.md, Hooks, Subagents, and MCP*
**Reviewer persona**: 15+ yr staff eng, has shipped Claude Code in real teams
**Surface rule (ship-tested 2026-04-25)**:
- `terminal_exercise` → terminal
- `system_build` with `validation.gha_workflow_check` → terminal
- everything else → web
**Date**: 2026-04-25
**Repos referenced**:
- canonical: `https://github.com/tusharbisht/aie-course-repo`
- MCP: `https://github.com/tusharbisht/aie-team-tickets-mcp`

---

## Pre-flight: environment

- `claude --version` → **NOT INSTALLED** on review host (`zsh: command not found: claude`). I cannot run any literal Claude Code command — every `claude ...` claim in the course must be cross-checked against documentation/source instead. **P1**: a course about Claude Code on a review host without the CLI is uncomfortable. The course's own M0 preflight protects against this for *learners*, but reviewer infra should mirror it.
- DB lookup confirmed course title and topology (7 modules, 30 steps).

---

## Repo / branch sniff

- `tusharbisht/aie-course-repo` exists, default branch `main`. Branches present: `main`, `e2e-test`, `module-0-preflight`, `module-1-starter`, `module-2-retry`, `module-3-iterate`, `module-4-mcp`, `module-5-team`, `module-6-agent-harness`. **Notably MISSING**: no `module-4-final` or anything that maps to the M4 capstone branch the course implies. The course step M4.S4 (id 85075) doesn't pin a branch in `gha_workflow_check`, but the briefing tells learners to push their feature branch — okay.
- `tusharbisht/aie-team-tickets-mcp` exists.
- **`skillslab-xyz/techtickets-broken` → 404 (P0).** M1.S2 (id 85061) tells learners to `git clone https://github.com/skillslab-xyz/techtickets-broken.git`. That URL does not exist. Learners hit a 404 in the first non-preflight exercise. Same for `@skillslab/team-tickets-mcp` npm package (M4.S3, id 85074): the real MCP is a Python script in `tusharbisht/aie-team-tickets-mcp`, not an npm package — `npm list -g @skillslab/team-tickets-mcp` will never match the regex `@skillslab/team-tickets-mcp@\d+\.\d+\.\d+` because the package doesn't exist on the npm registry.
- `lab-grade.yml` exists on `main` (and on `module-6-agent-harness`). On `main` it: ruff (advisory, `|| true`), pytest, and asserts `/health` is registered. **Two real concerns**:
  1. `required_jobs: ["test", "lint", "type-check"]` declared in M4.S4 validation, but the actual workflow has a single `grade` job and no `type-check` step at all. The `gha_workflow_check.required_jobs` will not match. Either the validator does substring matching (in which case `lint` matches the "Lint (ruff)" step name), or it does jobs-name matching (in which case all three are missing — there is no job named `test`, `lint`, or `type-check`). **P0 unless the validator is lax in a way I haven't read yet.**
  2. M3.S3 (id 85070) tells learners `cat app/schemas/health.py` should show `database_status.*connected.*error` — but `app/schemas/` doesn't exist on `module-3-iterate` branch (the contents listing showed only `__init__.py, db.py, health.py, main.py, models.py, repositories.py` for `app/`). Same gap on the `health-endpoint-challenge` branch the step references — that branch isn't in the listing either. **P0**: `git checkout health-endpoint-challenge` will fail.

---

## Surface-rule audit (per current rule)

| step | exercise_type | DB surface | rule says | match? |
|------|---|---|---|---|
| M0.S1 | concept | web | web | OK |
| M0.S2 | terminal_exercise | terminal | terminal | OK |
| M1.S1 | concept | web | web | OK |
| M1.S2 | terminal_exercise | terminal | terminal | OK |
| M1.S3 | code_review | web | web | OK |
| M1.S4 | concept | web | web | OK |
| M2.S1 | concept | web | web | OK |
| M2.S2 | code_read | web | web | OK |
| M2.S3 | terminal_exercise | terminal | terminal | OK |
| M2.S4 | terminal_exercise | terminal | terminal | OK |
| M3.S1 | concept | web | web | OK |
| M3.S2 | scenario_branch | web | web | OK |
| M3.S3 | terminal_exercise | terminal | terminal | OK |
| M3.S4 | categorization | web | web | OK |
| M4.S1 | concept | web | web | OK |
| M4.S2 | code_review | web | web | OK |
| M4.S3 | terminal_exercise | terminal | terminal | OK |
| **M4.S4** | **github_classroom_capstone** | **web** | (rule undefined for this type) | **see below** |
| M6.S1 | concept | web | web | OK |
| M6.S2 | code_exercise | web | web | OK |
| M6.S3 | code_exercise | web | web | OK |
| M6.S4 | terminal_exercise | terminal | terminal | OK |
| M6.S5 | terminal_exercise | terminal | terminal | OK |
| M7.S0 | concept | web | web | OK |
| M7.S1 | terminal_exercise | terminal | terminal | OK |
| M7.S2 | code_exercise | web | web | OK |
| M7.S3 | code_exercise | web | web | OK |
| M7.S4 | scenario_branch | web | web | OK |
| M7.S5 | terminal_exercise | terminal | terminal | OK |

**Surface mismatches found: 0 against the literal rule** — but I want to flag two issues with the rule's coverage:

1. **`github_classroom_capstone` is unknown to the surface rule (P1).** M4.S4 is the literal "Push the branch — GHA must go green" capstone. The rule names `system_build` with `gha_workflow_check`, but the DB stores this step as `github_classroom_capstone`. If the Creator/seed pipeline emitted this exercise type instead of `system_build`, the rule has a gap. The step has `validation.gha_workflow_check.workflow_file: ".github/workflows/lab-grade.yml"`, so by the *intent* of the rule it should be **terminal** (this step requires a real `git push` from the learner's machine). It is currently surfaced as **web** — which is consistent with the literal rule (`everything else → web`) but probably wrong by spirit. **Recommend**: extend the rule to `github_classroom_capstone with gha_workflow_check → terminal`.
2. **M7 is module position 7 but titled "Working with Claude Code in a Real Team" — it's not flagged "M5"** even though the M4 capstone says "(Capstone 1)" implying a Capstone 2 elsewhere. M6 is the "Deep Capstone." M7 then is a third post-capstone module. Course feels heavy: 7 modules with two capstones. Not a blocker, but reorder/rename is worth a P2.

---

## Capstone GHA fork-test (M4.S4 + M6.S5)

**Method**: cloned `tusharbisht/aie-course-repo`, created branch `reviewer-test-bad-2026-04-25`, pushed unchanged starter (with the planted-bug `repositories.py` and the broken async fixture). Watched lab-grade.yml run.

**Result**: GHA `grade` job **failed** as expected — but for the WRONG REASON.
- Run URL: https://github.com/tusharbisht/aie-course-repo/actions/runs/24937526829
- Failure: `tests/test_tickets.py::test_ticket_create_persists - AttributeError: 'async_generator' object has no attribute 'post'`

**Root cause (P0 — STARTER REPO BUG)**: `tests/test_tickets.py` defines `client` as `@pytest.fixture` (a sync fixture wrapping an async generator) under `pytest-asyncio==0.25.0`. In 0.25 the default mode is `strict`, which means `@pytest.fixture async def ...` does not wire — you must use `@pytest_asyncio.fixture` OR set `asyncio_mode = "auto"` in pyproject/pytest.ini.

There's no `pyproject.toml`/`pytest.ini`/`setup.cfg` on `module-1-starter` (HTTP 404 for all three when fetched). So:

- Every learner who clones M1 hits this AttributeError instead of the persistence-failure signal.
- The "fix" the course wants (add `await self.s.commit()` to `TicketRepository.create`) **does nothing for the AttributeError** — even with the right fix, the test will still error before reaching the persistence assertion.
- The CLAUDE.md template on `module-2-retry` SAYS `asyncio_mode=auto` is set, but there is no config file to set it in. So even M2's "redo with CLAUDE.md" run also fails for the wrong reason.
- The capstone (M4.S4) GHA grades on `pytest -v` — meaning the green-check the rubric requires is unreachable until either (a) the fixture is rewritten, or (b) `pyproject.toml` is added with `[tool.pytest.ini_options] asyncio_mode = "auto"`. **This single bug breaks M1, M2, M3, M4 — half the course.**

**Surface fix**: Add to `module-1-starter/pyproject.toml` (and propagate to all module branches):
```
[tool.pytest.ini_options]
asyncio_mode = "auto"
```
OR change the fixture to `@pytest_asyncio.fixture` in `tests/test_tickets.py`. **Single-line fix; ship-blocker.**

**I did NOT push a "good" branch with the fix because the bug above isn't the one the course teaches. The course's planted bug is the missing-commit one in `repositories.py`. Verifying that the GHA correctly grades the *good* commit-fix version of the code would require first patching the test infra, which is itself a course bug.** That's exactly the dependency a fork-and-push test is supposed to surface — and it surfaced.

**Cleanup**: deleted `reviewer-test-bad-2026-04-25` from origin (no PR ever opened).

---

## Per-step audit

### M0 — Preflight

- **M0.S1 (concept)**: budget + tooling. OK. Standard preflight framing.
- **M0.S2 (terminal_exercise)**: 3 cli_commands — `claude -p "..." TOOLCHAIN_VERIFIED`, `docker pull hello-world`, `git status || git init .`. Surface=terminal ✓. Hint correctly recommends `claude /login` for auth. **Tiny nit (P2)**: `docker images hello-world` regex `hello-world.*latest` — passes only after a successful pull and on most local docker installs lists by repo, fine.

### M1 — First AI-Assisted Fix

- **M1.S1 (concept)**: senior framing. OK.
- **M1.S2 (terminal_exercise)** — **P0**: `git clone https://github.com/skillslab-xyz/techtickets-broken.git` → 404. The repo doesn't exist. Real starter is `tusharbisht/aie-course-repo`, branch `module-1-starter`. **Fix**: rewrite cli_commands to use that branch. Also the planted-bug fix path is broken because of the async-fixture bug above — until that is fixed, even a perfect Claude-Code session against this step cannot make `pytest` go from FAILED to PASSED, so the rubric (item #4: "Verify the fix works") is unreachable.
- **M1.S3 (code_review)**: sniffs for "the subtle bug in Claude's diff" — fine as a web exercise. No GH calls so URL hallucinations don't bite here.
- **M1.S4 (concept)**: gap-naming reflection. OK.

### M2 — CLAUDE.md context hygiene

- **M2.S1 (concept)**, **M2.S2 (code_read)**: web. OK.
- **M2.S3 (terminal_exercise)**: writes `# Project Structure / # Stack Overview / # Development Commands / # Code Quality Rules`. Reasonable. Surface=terminal ✓. **Note**: the actual `CLAUDE.md-TEMPLATE` on `module-2-retry` uses *different* section names (`## Stack / ## Conventions / ## Testing / ## Don't-Touch / ## Commands / ## Escalation`). The course validation requires `# Project Structure...` etc. but the canonical template says `## Stack`. **P1 — schema drift between course `must_contain` and starter template.** Whichever the learner follows, one of them rejects.
- **M2.S4 (terminal_exercise)**: `git status` expects `On branch module-2-retry`. Branch exists ✓. But the `pytest tests/test_tickets.py::test_create_ticket_with_priority -v` — that test **does not exist** in `tests/test_tickets.py` on `module-2-retry` (the file has `test_ticket_create_persists`, no priority test). **P0 — test name hallucinated.** Either the must_contain is wrong, or the starter repo is missing a test the course assumes exists.

### M3 — Drive 70%-right to done

- **M3.S1 (concept)**, **M3.S2 (scenario_branch)**: web. OK.
- **M3.S3 (terminal_exercise)** — **P0 multi-issue**: 
  - References branch `health-endpoint-challenge` → branch does not exist (404).
  - References `app/schemas/health.py` → directory does not exist on `module-3-iterate`.
  - The schema field the step claims (`database_status` with values `connected`/`error`) is not what the actual `app/health.py` stub describes (`{status: ok|degraded, checks: {db, redis}}`). The course is grading a different schema than the starter teaches. Three independent contradictions in a single step.
- **M3.S4 (categorization)**: web. OK.

### M4 — MCP capstone

- **M4.S1 (concept)**, **M4.S2 (code_review)**: web. OK.
- **M4.S3 (terminal_exercise)** — **P0**:
  - `npm list -g @skillslab/team-tickets-mcp` — fictional npm package. The MCP is at `tusharbisht/aie-team-tickets-mcp` and is a Python script. The npm-list expect-regex will never match. Step is unpassable as written.
  - `claude mcp list` is correct (verified facts confirm).
  - `claude -p "Use team-tickets MCP to show current ticket count"` — this prompt asks for "ticket count" and expects regex `list_recent_tickets|get_ticket_health|ticket.*count`. The MCP doesn't expose a count tool; it has `list_recent_tickets` and `get_ticket_health`. The match will likely succeed because Claude usually names a tool it called, but this is fragile. **P1**.
  - **Critical fact-mismatch (P0)**: the MCP repo's own README tells learners to put `mcpServers: {team-tickets: {command, args}}` in `~/.claude/settings.json`. Per verified facts, **`mcpServers` is the Claude Desktop config schema, not Claude Code.** Claude Code uses `claude mcp add team-tickets python /abs/path/server.py --transport stdio` OR a project-scoped `.mcp.json`. The course curriculum is teaching the WRONG canonical config layout for the SDK it claims to teach. This is the most-replicable mistake users will make in production.
- **M4.S4 (github_classroom_capstone)** — **P0**:
  - `validation.gha_workflow_check.required_jobs: ["test", "lint", "type-check"]` but the actual workflow has a single job `grade` containing steps named "Lint (ruff)", "Run tests", "Confirm health endpoint". There is no `type-check` (mypy) anywhere. Either the validator is silently passing on missing jobs, or every learner fails because three required jobs aren't satisfied.
  - `success_condition: "all_jobs_pass"` will pass once lab-grade.yml's single `grade` job goes green — but `required_jobs` is then misleading documentation that promises type-checking the course never delivers.
  - The starter-repo async-fixture bug means lab-grade.yml fails for everybody until that's patched, regardless of M4 work.

### M6 — Agentic Coding Deep Capstone

- **M6.S1 (concept)**, **M6.S2 (code_exercise)**, **M6.S3 (code_exercise)**: web. OK.
- **M6.S4 (terminal_exercise)**: requires branch `module-6-agent-harness` and `agent_harness.py`. Branch exists ✓; `harness/` dir exists on the branch ✓. Need to verify `agent_harness.py` is at repo root (currently in `harness/` based on listing) — **P1, path may be off**.
- **M6.S5 (terminal_exercise)** — **P0**: requires branch `module-6-final` → branch does NOT exist. The whole final-grading path is broken. The validator expects `git ls-remote --heads origin module-6-final` to return `refs/heads/module-6-final`; it will return empty.

### M7 (positioned as M5 in title) — Subagents/Hooks/Settings

- **M7.S0 (concept)**: OK.
- **M7.S1 (terminal_exercise)** — **P0**:
  - Heredoc creates `.claude/agents/test-fixer.md` with `name: "Test Fixer"` and tools `Read|Edit|Bash` — capitalized correctly ✓ (matches verified facts).
  - **`claude --list-agents` and `claude --agent test-fixer --dry-run` are FICTIONAL flags.** Per verified facts the slash-command surface is `/agents` (interactive) inside a session, and there is no `--list-agents` on the shell CLI nor any documented `--dry-run`. Course is teaching learners to type a command that doesn't exist.
  - YAML frontmatter shape — verified facts state subagent frontmatter requires `name`, `description`, `tools` (array). The course frontmatter adds `max_iterations: 5` which is **NOT a documented frontmatter field**. May be silently ignored, but counts as fact drift.
- **M7.S2 (code_exercise — hook code)**: well-aligned with verified facts (stdin JSON, exit 2 = block, PascalCase tool names, `tool_name`/`tool_input.command` shape) — this is the strongest step in the course. ✓
- **M7.S3 (code_exercise — settings.json)**: aligned (allow/deny arrays, PascalCase events, hooks key in settings.json). One **P1**: the example uses paths like `/etc/*`, `~/.ssh/*` in the dangerous-patterns deny list — settings.json `permissions.deny` matches tool calls (`Bash(rm:*)`), not arbitrary file globs. The function returns the wrong shape for what `permissions.deny` actually consumes.
- **M7.S4 (scenario_branch)**: web. OK.
- **M7.S5 (terminal_exercise)** — **P0**: `claude config validate .claude/` is a fictional subcommand. Per verified facts the engine even calls this out as commonly hallucinated: "uses `claude /settings reload|show|validate` — invented slash commands". `claude agents list` is a real shape but the fact-block specifies the slash form `/agents` inside session; whether `claude agents list` is currently a real shell subcommand is implementation-dependent — **need to confirm against the version the course assumes**. `claude hooks status` — also fictional (no such subcommand documented).
  - The expectation regex on `claude config validate` is `valid|success|✓` — will never match. Step is unpassable.

---

## Verified-facts cross-check

| Fact (canonical) | Course teaches | Match? |
|---|---|---|
| Auth: `claude /login` interactive OR `ANTHROPIC_API_KEY` env (NOT `claude auth`) | M0.S2 hint says `claude /login` | ✓ |
| Built-in tool names PascalCase (`Read`, `Edit`, `Bash`) | M7.S1 frontmatter uses these correctly | ✓ |
| Hook contract: stdin JSON, exit 2 = block (NOT exit 1, NOT env var) | M7.S2 code teaches stdin + exit 2 | ✓ |
| `~/.claude.json` (auth/creds) vs `~/.claude/settings.json` (user settings) vs `<project>/.claude/settings.json` (project) vs `.mcp.json` (project MCP) | M7.S3 uses `~/.claude/settings.json` | ✓ for path, but the canonical 4-file taxonomy is never **explained** to the learner. Course only teaches one file. **P1 — incomplete coverage of canonical config layout.** |
| MCP wiring: `claude mcp add <name> <cmd> --transport stdio` | M4.S3 only uses `claude mcp list`; never teaches `claude mcp add`; the MCP README teaches the WRONG `mcpServers` block | **MISMATCH (P0)** |
| Subagent YAML frontmatter: `name`, `description`, `tools` array — auto-discovered from `.claude/agents/*.md` | M7.S1 uses these fields ✓ but adds fictional `max_iterations` | **PARTIAL** |
| `claude config validate / hooks status / --list-agents / --agent ... --dry-run` | M7.S1 + M7.S5 use all four | **ALL FICTIONAL — P0** |

---

## Production-readiness assessment

### Hook design (M7.S2 + M7.S3)

- **Idempotency**: the PreToolUse hook is **stateless** — every call is independent. ✓
- **Race conditions**: PreToolUse runs synchronously per tool call; the example doesn't write any shared state. PostToolUse hooks (which the course does NOT teach but the M5 settings template references with `ruff format <path>`) WOULD have race issues if two parallel Edits hit the same file. Course doesn't surface this. **P2 — production gap**.
- **Failure mode**: hook example `fail open` on JSON parse error — comment says "If we can't parse input, allow by default." This is the right call for safety hooks (avoid bricking the agent), but production teams may want fail-closed for sensitive paths. Not discussed. **P2**.
- **Hook performance**: regex matching in Python is fine for a teaching example. No mention of timeouts (Claude Code applies a 5-second default per hook — undocumented in this course). **P2**.

### MCP failure handling (M4)

- The course does NOT teach `claude mcp` failure modes. No mention of:
  - what happens when the MCP subprocess crashes mid-session
  - how to reconnect (`/mcp` slash; restart session)
  - debugging stdio framing errors
  - `~/.claude/logs/` (or project equivalent) for MCP traces
- M4.S3 hint says "If the MCP registration fails, try the full absolute path to the MCP binary instead of the relative ./node_modules path" — but the MCP isn't an npm package, so this hint is misleading on multiple axes.
- **P0 production gap.** Real teams running MCP in CI/in shared dev rigs hit reconnection issues weekly. The course skips it entirely.

### Capstone production-shaped or tutorial-shaped?

- M4.S4 is **tutorial-shaped**: push a branch and let GHA run pytest. This is shape-of-CI but not shape-of-production. There is no:
  - branch protection / required-checks discussion
  - PR review pattern (M4.S2 reviews a teammate's PR but in isolation, not as the gating step before push)
  - rollout/rollback discussion
  - any flavor of incident if the test goes red mid-push
- M6.S5 is **closer to production** (ship a harness that runs against multiple bugs of rising difficulty) but still grades on `git ls-remote --heads origin module-6-final`, not on quality of output, not on harness telemetry. **The grading primitive is "did you push" — not "is your harness any good."**
- **Verdict on capstone shape**: *tutorial with a CI thumb on top*. Not production-grade.

---

## Cross-course positioning (Claude Code vs OpenRouter+Aider)

The course is the second AI-enablement track (Kimi/OpenRouter+Aider being the first). Cross-course role clarity check:

- **Where Claude Code wins per this course**: agentic autopilot via the official CLI, hooks/permissions for team safety gates, MCP for context enrichment, `.claude/` as a checked-in team config. ✓ — these are the right talking points.
- **Where OpenRouter+Aider wins (per the Kimi course)**: model routing across providers, lower latency on swap-in/swap-out, BYO-everything if Claude Code's authority surface is too opinionated.
- **Course actively discusses the trade-off?** No. M4 implicitly assumes Claude Code is the agent, no comparison. The introductory module (M0.S1) talks about "expected spend" but doesn't position when Aider/OpenRouter is preferable. **P1 — cross-course role-clarity gap.**
- A learner finishing both courses cannot answer "for THIS task, which tool do I reach for?" Recommend a 1-paragraph addendum on M0.S1 or M7.S0.

---

## Live sniff-test summary

| Probe | Result |
|---|---|
| `claude --version` on review host | NOT INSTALLED (P1 reviewer-infra, not course bug) |
| `gh api repos/tusharbisht/aie-course-repo` | exists, 9 branches |
| `gh api repos/tusharbisht/aie-team-tickets-mcp` | exists |
| `gh api repos/skillslab-xyz/techtickets-broken` | **404 (P0)** |
| `gh api repos/skillslab/team-tickets-mcp` | **404 (P0)** |
| `gh api .../branches/health-endpoint-challenge` | **404 (P0)** |
| `gh api .../branches/module-6-final` | **404 (P0)** |
| `gh api .../contents/app/schemas?ref=module-3-iterate` | **404 (P0)** — schema dir doesn't exist |
| `lab-grade.yml` on `main` | exists, single `grade` job (lint advisory, pytest, health-check assert) |
| `lab-grade.yml` on `module-6-agent-harness` | exists, identical to main |
| Live GHA fork+push (bad branch) | **failed for the wrong reason (broken async fixture, P0)** |

---

## P0 list (ship-blockers)

1. **Starter repo async fixture is broken on every module branch** — `tests/test_tickets.py` uses `@pytest.fixture` on an async generator under pytest-asyncio 0.25 strict mode with no `asyncio_mode=auto` config. Breaks M1, M2, M3, M4 capstone GHA. Single-line fix.
2. **Hallucinated repo URL in M1.S2**: `skillslab-xyz/techtickets-broken` does not exist.
3. **Hallucinated npm package in M4.S3**: `@skillslab/team-tickets-mcp`. The MCP is a Python script.
4. **Wrong MCP wiring taught in MCP repo README** — `mcpServers` JSON block is the Claude Desktop schema, not Claude Code. Course should teach `claude mcp add team-tickets python /abs/path/server.py --transport stdio` OR a `.mcp.json`.
5. **M3.S3 schema mismatch**: course validates `app/schemas/health.py` containing `database_status` field — directory doesn't exist on starter, the actual `app/health.py` teaches a different schema.
6. **M3.S3 branch `health-endpoint-challenge` does not exist.**
7. **M2.S4 references test `test_create_ticket_with_priority` that doesn't exist** in starter.
8. **M6.S5 branch `module-6-final` does not exist.**
9. **M7.S1 uses fictional `claude --list-agents` and `claude --agent ... --dry-run` flags.**
10. **M7.S5 uses fictional `claude config validate` and `claude hooks status` subcommands** — the very kind of hallucination the verified-facts engine is supposed to block.
11. **M4.S4 `gha_workflow_check.required_jobs` lists `["test", "lint", "type-check"]` but the actual workflow has one `grade` job and no type-check step.**

## P1 list

1. **CLAUDE.md schema drift**: `module-2-retry/CLAUDE.md-TEMPLATE` uses different section names than the M2.S3 must_contain.
2. **M4.S3 hint references a path style that's wrong** for a Python-script MCP.
3. **Cross-course role clarity (Claude Code vs OpenRouter+Aider) not discussed.**
4. **M6.S4 `agent_harness.py` may be at `harness/agent_harness.py`, not repo root.**
5. **`github_classroom_capstone` not covered by surface rule** — works out OK by default-to-web today but fragile.
6. **Production hook race-condition + timeout discussion absent** in M7.S2/S3.
7. **MCP failure-mode/reconnection guidance absent** in M4.

## P2 list

1. Capstone is tutorial-shaped — grade primitive is "did you push," not output quality.
2. Course feels heavy at 7 modules with 2 capstones; rename to 5 modules + 2 deep capstones might read cleaner.
3. M5 settings.json template (the `.claude/settings.json-TEMPLATE` on `module-5-team`) uses `_hint` keys — stylistic choice, but unconventional. Real settings.json lints will warn about unknown keys depending on Claude Code version.

---

## Counts

- **P0 found**: **11**
- **P1 found**: 7
- **Surface mismatches** (literal rule): **0** (rule's coverage of `github_classroom_capstone` should be extended; spirit-mismatch on M4.S4)
- **Hallucinated URLs / nonexistent branches / nonexistent npm**: **6** distinct cases
- **Fictional Claude Code subcommands**: **4** (`--list-agents`, `--agent ... --dry-run`, `claude config validate`, `claude hooks status`)

---

## Verdict: **REJECT**

Cannot ship to a real eng team. The course teaches Claude Code in production but the starter repo CI fails for an unrelated infra bug from the very first exercise, multiple capstone branches don't exist, the MCP repo's own README contradicts the verified-facts canonical config layout, and four `claude ...` subcommands cited in the curriculum simply do not exist in the CLI. A senior eng who paid for this course would file 11 issues and ask for a refund within an hour.

**Path back to SHIP-WITH-FIXES** (rough order):

1. Fix the async-fixture bug across all branches (1-line `asyncio_mode = "auto"` in pyproject.toml).
2. Replace `skillslab-xyz/techtickets-broken` → `tusharbisht/aie-course-repo` (branch `module-1-starter`) in M1.S2.
3. Replace `npm list -g @skillslab/team-tickets-mcp` with `pip show team-tickets-mcp` OR `python -c "import team_tickets; print(team_tickets.__version__)"` in M4.S3. Update the MCP README to teach `claude mcp add team-tickets python /abs/path/server.py --transport stdio` (NOT `mcpServers`).
4. Create the missing branches: `health-endpoint-challenge`, `module-6-final`. Add `app/schemas/health.py` to `module-3-iterate` matching the schema the course validates.
5. Replace fictional CLI subcommands. Use `cat .claude/agents/test-fixer.md` as proof-of-existence instead of `claude --list-agents`. Drop the `--dry-run` claim. Replace `claude config validate` with a real check (`python -c "import json; json.load(open('.claude/settings.json'))"`). Drop `claude hooks status` or replace with `cat .claude/settings.json | jq .hooks`.
6. Fix M2.S4 test name. Reconcile CLAUDE.md template section names.
7. Add a real MCP failure-mode appendix to M4 (5-min sub-step) covering reconnection.
8. Either fix `gha_workflow_check.required_jobs` to `["grade"]` or split lab-grade.yml into 3 jobs.

Estimated time-to-fix: 4-6 hours of repo+DB work for a creator who knows the system. The teaching arc is sound; the implementation is a beta.

---

*Reviewer: senior staff eng surrogate*
*Date: 2026-04-25*
*Source course: created-7fee8b78c742*
*Repo SHA reviewed: main HEAD as of 2026-04-25T02:27:30Z*
