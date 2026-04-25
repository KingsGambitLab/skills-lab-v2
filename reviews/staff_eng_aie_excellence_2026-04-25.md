# Staff-Engineer Review — AI-Augmented Engineering (Claude Code + API)

- Course: `created-7fee8b78c742` — "AI-Augmented Engineering: Ship Production Features with Claude Code + API"
- URL: http://localhost:8001/#created-7fee8b78c742
- Repos: https://github.com/tusharbisht/aie-course-repo , https://github.com/tusharbisht/aie-team-tickets-mcp
- Reviewer: me, wearing my staff-engineer / team-adoption hat. I've shipped Claude / tool_use / MCP to prod, so my bar is "does this make a mid-career eng a real Claude-Code citizen in two weeks" — not "is the dashboard polished."
- Date: 2026-04-25

A note on naming: the course card labels modules M0, M1, M2, M3, M4, M6, and the final one "Working with Claude Code in a Real Team." Internally positions are 1-7 so I'll use the user's label convention: M0 preflight, M1 First Fix, M2 CLAUDE.md, M3 70%-Right, M4 MCP+GHA, M5 agentic harness (the "M6 — Agentic Coding" module), M6 team config (the final module).

---

## Top-line verdict: **HOLD**

Not "ship-with-fixes" — **HOLD** until the course-content / starter-repo mismatch and the missing per-module scaffolding are resolved. The pedagogy, the graders, and the platform primitives are unusually strong for an AI-generated course, and the Claude-Code facts are mostly correct. But three ship-blockers (see P0) mean a learner doing M2.S3 and M4.S3 today will hit dead ends that break trust on the very first real assignment. For 80 engineers that's a room-full-of-skeptics disaster, not a small fix-post-launch tail.

The bones are excellent. The content is too pre-release to certify.

---

## What works (grounded in specific steps)

1. **The inversion pedagogy is real, not a slogan.** M1.S2 boots `module-1-starter` which contains a genuinely failing `test_ticket_create_persists` — the `TicketRepository.create()` does `flush()` without `commit()`. That's a real async-SQLAlchemy bug learners DO hit in production. Then M1.S4 names the five context-gap patterns. Then M2 asks them to write a CLAUDE.md for the same repo. Then M2.S4 has them retry. "Feel the pain FIRST, setup SECOND" is structurally intact. Few courses actually land this — most teach CLAUDE.md before anyone has felt why they'd want one.

2. **Graders are real, not theatrical.** I probed three of them with strong and weak submissions:
   - M0.S2 (`terminal_exercise`): weak paste → 0%; fabricated-looking plausible paste → **0.44** with LLM rubric feedback that called out fabrication (`"The format suggests fabricated rather than actual terminal output"`); realistic terminal paste with full docker-pull output → **1.0**. That's ~7× discrimination across a 0–1 scale.
   - M3.S4 (`categorization`, six 70%-right scenarios): all-correct → **1.0** with per-item pedagogical explanations; all-wrong → **0.0** with item-by-item "you chose X, correct is Y." Teaches on wrong answers.
   - M5.S2 (`code_exercise` — tool_use round-trip): weak cheese (`must_contain` strings as comments) → `ImportError: cannot import name 'READ_FILE_TOOL'` in Docker, **0/8 hidden tests pass**. A real hand-written solution → **7/8 tests pass, score 0.88**. The grader actually runs pytest in a container against 8 real hidden tests. No regex-on-prose.

3. **The Claude-Code factual surface is correct.** Spot-checked against the "reference facts" contract the Creator prompt was supposed to enforce (CLAUDE.md §Verified-facts-block): `claude /login` (not `claude auth`), `PreToolUse` hook contract — JSON on stdin + `sys.exit(2)` to block (M6.S2 `must_contain` literally includes `'sys.exit(2)'`, `'json.loads(input_data)'`, `'re.search('`), CAPITALIZED built-in tool names (M6.S1 body: "tools: [Read, Edit, Bash]  with CAPITALIZED tool names"), `.claude/agents/<name>.md` subagent location, `settings.json` permissions deny/allow lists, `claude mcp add` + `claude mcp list` for MCP wiring. These are the ways the LLM usually hallucinates — and they stuck.

4. **The M4 MCP server is a real MCP server, not a stub.** `team-tickets-mcp/server.py` uses the actual `mcp.server` + `stdio_server` SDK, has a working `list_tools()` + `call_tool()` loop, two read-only tools (`list_recent_tickets`, `get_ticket_health`) with proper JSON input schemas, real toy-but-meaningful business logic (days_open + priority + blocked_by → red/yellow/green). ~150 lines, readable end-to-end. That's exactly the level you want engineers to grok.

5. **BYO-key is architecturally enforced, not just documented.** The `terminal.html` template text reads "This page will never ask for your key"; `terminal.js` has an inline banner `/* SECURITY: this template NEVER captures/stores/transmits any API key. The BYO-key panel is informational only. Do not add key input. */`. Only password input on the whole site is the app login. The dependencies-panel entry for `anthropic_api_key` renders as an informational label pointing at console.anthropic.com. This is the right architectural posture for a course that will be adopted by 80 engineers — zero platform liability for keys.

6. **`paste_slots` is the right UX primitive.** Every terminal-exercise step has structured paste slots (`prompts` / `final_diff` / `transcript`) instead of a single textarea. The backend combines them, labels each in the LLM-rubric prompt, and gives slot-specific per-submission feedback. This prevents the "paste everything into one blob" failure mode and makes the LLM rubric grader's job tractable.

7. **The lab-grade.yml workflow is real (for M1–M3).** `.github/workflows/lab-grade.yml` runs `pytest -v --tb=short` and asserts `/health` exists via route introspection. Not theater for M1→M3 — the M1 planted bug (`flush()` without commit) really does fail in CI. A senior engineer will recognize this as a "real gate."

---

## P0 ship-blockers (would make a senior eng quit on day 1)

**P0-1. Course narrative uses Nexboard / Redis / Socket.io / cursor tracking; starter repo is a plain FastAPI + SQLite + SQLAlchemy ticket service. They don't match.** Every module's concept content introduces "Sofia Martinez," "Marcus Chen," "Nexboard's collaborative cursor feature," `RedisSessionManager`, "Socket.io real-time infrastructure," PostgreSQL canvases, etc. The actual repo at `github.com/tusharbisht/aie-course-repo` (every branch, confirmed — all seven branches have identical `app/` trees modulo `MODULE.md`) has `app/main.py`, `app/db.py`, `app/repositories.py`, `app/models.py`, `app/health.py` — a tickets-over-SQLite service. No Redis. No Socket.io. No canvas. No WebSocket. The learner clones the repo, opens Claude Code, and immediately realizes the course was written about a different codebase.

This ripples into the graders. **M2.S3** has a hidden test that asserts `assert "redis" in content` — a learner writing a correct CLAUDE.md for the **actual repo** cannot include Redis (it's not there). The test also requires file references like `app/auth/session_manager.py` and `app/db/user_repository.py` — neither directory/file exists. A senior engineer who carefully writes a truthful CLAUDE.md for what's actually on disk **will fail the hidden test suite**, then reasonably conclude the course is broken.

Fix: either (a) regenerate the course with Nexboard removed and Marcus/Sofia rewritten as ticket-service engineers; OR (b) rebuild the starter repo as an actual Nexboard-flavored FastAPI + Redis + Socket.io service with a failing WebSocket/Redis test. Option (a) is 10× cheaper and loses nothing.

**P0-2. M4.S3 hardcodes a hallucinated git URL: `git clone https://github.com/anthropic/team-tickets-mcp.git`.** That repo doesn't exist under `anthropic/`. The real one is `tusharbisht/aie-team-tickets-mcp`. The MCP capstone's literal first instruction fails. This is the single most trust-breaking step in the course — the F1 "no invented CLI commands" rule in the Creator prompt was supposed to block exactly this, but it didn't cover URL namespaces. Fix: point to `https://github.com/tusharbisht/aie-team-tickets-mcp.git` (or move the MCP under a new GH org if you're setting up `skills-lab-demos/`).

**P0-3. The M5 "agent harness" and M6 "team config" scaffolds don't exist in the starter repo.** Every module branch (`module-0-preflight` through `module-6-agent-harness`) is **byte-identical** except for `MODULE.md`. Concretely:
   - `module-6-agent-harness` has no `harness/`, no `planted_bug/`, no `tests/agent_harness/`. The M5.S4 content tells learners "checkout `module-6-agent-harness` which contains a deliberately planted bug" and M5.S5 says "GHA runs it on 3 bugs of rising difficulty" — there IS no 3-bug test suite and there IS no planted bug file. The only failing test in the branch is the M1 `test_ticket_create_persists` (which is identical across all branches).
   - `module-5-team` has no `.claude/` scaffold. M6.S1 expects the learner to write `.claude/agents/test-fixer.md`, M6.S3 writes `.claude/settings.json`, M6.S6 ships a `.claude/` that a teammate can `git clone` — but the branch is empty of scaffolding, so the learner is creating everything from scratch without even a starter directory.
   - `module-3-iterate` has no `migrations/` directory. M3.S3 tells learners "Check `migrations/001_initial.sql` for the exact column names and table structure." That file doesn't exist. The "schema gotcha" the course promises is fictional.
   - `module-4-mcp` has no `/health/tickets` stub, no scaffolded MCP wiring. M4.S3 rubric looks for "Claude generating FastAPI endpoint code that uses MCP tools" — the learner has to create this from zero in a repo that has no hint of where it goes.

Per-module branches should be a pedagogical contract ("your environment for module N is exactly what I gave you"). Here they're almost entirely theater — only M1's bug is real. Fix: per module that needs scaffolding, commit the actual starter files to the corresponding branch before enabling the course.

**P0-4. M4 capstone's "green CI" is not a capstone gate — it's an M1 gate in disguise.** `lab-grade.yml` runs one test (`test_ticket_create_persists`) and asserts `/health` exists. The M4 branch doesn't add an `/health/tickets` test or any MCP-specific check. A learner who pushed the un-fixed M4 branch would fail on M1's commit bug, not on anything M4 taught them. Fix: add a test for the feature the learner builds in M4 (e.g., `GET /health/tickets` returns ticket-count JSON), and fail the workflow if it isn't present.

---

## P1 polish (fix before rollout, not ship-blocking individually)

- **Homebrew tap in `terminal.js` dep labels**: `brew install anthropic-ai/claude/claude`. I can't verify this tap exists. The canonical installs are `curl -fsSL https://claude.ai/install.sh | bash` or `npm install -g @anthropic-ai/claude-code`. If the tap doesn't exist, every learner hits "Error: No available formula" at the very first deps-panel render. 10-minute fix.
- **Dashboard-wording drift**: M5 is labeled "M6 — Agentic Coding from First Principles" in the module title but is position 6/7 on the course card. The team-config module is called "Working with Claude Code in a Real Team: Subagents, Hooks, Settings" with steps starting at S0 (inconsistent with the rest starting at S1). Not blocking, but confuses the nav.
- **M4.S3 copy names the wrong flag ordering**: `claude mcp add team-tickets /abs/path/... --transport stdio`. The `--transport` flag is valid, but Claude Code's actual signature is `claude mcp add <name> <command> [args...]`; the transport flag defaults to stdio so it's redundant but works. This is correct-enough; I'd add a parenthetical "(`--transport stdio` is the default; included for clarity)" so a careful reader doesn't assume it's mandatory.
- **M0.S2 rubric requires `"Hello from Docker"` verbatim.** On some Docker output variants the message wraps differently — learners with `docker run --rm hello-world > file; cat file` may paste a variant. The grader tolerates `"Hello from Docker"` as a substring, which matches the canonical text, so this is fine — but I'd widen the rubric to accept `"This message shows that your installation"` OR `"Hello from Docker"` as the Docker-works signal.
- **M2.S2 exemplary CLAUDE.md references the Nexboard stack.** Even if P0-1 is fixed by rewriting the narrative around tickets, the exemplar itself has to be rewritten — otherwise learners model their M2.S3 CLAUDE.md on a template for a codebase they're not working in.
- **M3.S4 categorization items reference Nexboard.** Same issue — each of the 6 items ("hardcoded Socket.io room names", "missed the edge case where users disconnect", "used polling instead of WebSocket events") assumes a Socket.io/cursor world that the starter repo doesn't have. Re-theme to the tickets service (or commit to rebuilding the repo as the Nexboard canvas service).
- **The M6 team module's `settings.json` exercise hardcodes paths like `/opt/team-tickets-mcp/server.py` and `/opt/safety-hooks/dangerous-command-filter.sh`.** Those paths don't exist on a learner's machine (they live in `/opt/...` as if on a shared enterprise image). The intent is clearly "these are placeholders," but the M6.S3 hidden test checks for patterns like `/etc/` and `/home/` in deny-lists — which is fine — but the narrative around `/opt/...` should be "use the path where you cloned the MCP" with an example, not literal `/opt/`.
- **No per-session cost meter on the dashboard.** For a BYO-key course with a promised `$3–8` total spend, I'd expect at least an in-course estimated-cost widget ("this step: ~$0.15 in sonnet-4-5, ~$0.02 in haiku-3.5"). Not blocking, but it's the one thing that makes BYO-key engineers stop sweating. Would also set up Haiku/Sonnet cost comparisons that reinforce M0.S1's model-selector.
- **M1.S3 code_review: the planted bugs are reasonable but a few bug categories overlap**. "Resource leaks" and "Data consistency" both fire on the same stale-cache-key issue depending on where the learner clicks. Not a grader bug — the grader scores by line — but the in-content rubric lists six bug categories and the planted bugs hit four; a senior reviewer will intuit there are 6 bugs when there are ~4.

---

## Production-grade specifics — what does this teach that a senior eng doesn't already know?

This is the question I cared about most. A lot of Claude Code courses are surface-level (here's `/clear`, here's `Read`, here's a slash command). This course has at least 3 moves that I haven't seen taught well elsewhere:

1. **The PreToolUse hook contract, verbatim.** M6.S2 forces the learner to write a hook that reads JSON from stdin, pattern-matches with `re.search`, and `sys.exit(2)` to block. The hidden_tests I extracted actually import `extract_command_text`, `check_dangerous_file_operations`, `check_dangerous_git_operations`, `check_dangerous_database_operations`, `check_dangerous_system_operations`, `main` — the learner produces a real pluggable script, not a toy. Most teams I talk to think hooks are "settings.json stuff"; this teaches the actual runtime shape. **This is the single most leveraged skill the course teaches.**

2. **The agentic-loop sha256-progress-detection pattern.** M5.S3 (autocorrect loop) requires `hashlib.sha256(error)` to detect repeat-error-hash stuck conditions, with three distinct stop_reasons (`'success' | 'budget_exhausted' | 'stuck: no progress'`). This is exactly how a production agent stops thrashing — and it's not written up well anywhere. The hidden tests enforce that the loop calls `client.messages.create` at most `budget` times and stops on error-hash repeat. Real engineering content.

3. **`tool_use` / `tool_result` round-trip from first principles.** M5.S2 walks the full SDK primitives: `parse_tool_use` extracts `id + name + input` from a content block, `build_tool_result` constructs the `{type: 'tool_result', tool_use_id, content, is_error?}` message shape, `run_tool_roundtrip` orchestrates the cycle with `stop_reason` handling. The 8 hidden tests cover schema shape, tool_use extraction, tool_result construction (including `is_error`), end-to-end roundtrip with mocked client. This teaches engineers that "build an agent" = "own the loop," not "import a framework." Most Anthropic-SDK tutorials skip directly to frameworks; this doesn't.

4. **Commit discipline under AI acceleration.** M4.S1 frames the "when Claude generates 80% of a feature in 20 minutes, the temptation is to commit everything as one massive change" problem and names three concrete rules (semantic commits, progressive complexity, context preservation). This is the ONLY place in any Claude Code material I've seen treat the "AI-generated PR hygiene" problem head-on.

5. **The M3 prompt-rewrite reflex vs output-argue reflex.** M3.S1 / S2 explicitly teach that when Claude's 3rd attempt is still wrong, the move is **rewrite the original prompt with missing context, not argue with the output**. This is the biggest behavioral gap I see in engineers adopting Claude Code — they stay in "chat mode," argue with the output, burn 40 minutes, and then complain Claude "can't" do it. Naming the anti-pattern is half the cure. Worth the course tuition alone for engineers who haven't developed this reflex yet.

So: NOT surface-level. The pedagogy genuinely targets the skills mid-career engineers are missing. That's why P0 hurts so much — the content is much better than the delivery today.

---

## Comparison anchor — would a senior eng take this over...

- **(a) Reading Anthropic's official docs themselves?** Today (2026-04), no. A competent senior eng can read the Claude Code docs + the tool_use guide + the MCP spec in one afternoon and walk away with the same factual surface. What the docs don't give them is the **inversion pedagogy** (M1 pain → M2 CLAUDE.md → M2 retry measurement), the **categorization drill** (M3.S4), the **stuck-loop intervention rubric** (M6.S4 scenario_branch), and the **commit-discipline-under-AI** framing. Those are worth the 2 hours. But they're not worth it if the hands-on steps don't run — which today they partly don't. **Post-fix: YES over docs, clear win.** Today: no.

- **(b) A 2-hr internal lunch-and-learn?** A good lunch-and-learn would cover the CLI surface + MCP wiring + maybe show a hook. It would NOT build the agentic loop from scratch (too long for one session) and would NOT give learners repeatable measurement (M2 turn-count-before-vs-after). The course's big pedagogical innovation is the "measure the delta" move — M1 cost X turns, M2 retry with CLAUDE.md cost Y turns. Lunch-and-learns can't do that. **Post-fix: YES over lunch-and-learn; it forces each engineer through the delta themselves.**

- **(c) A vendor course like LangChain Academy?** Those courses are framework-bound (agent graphs, LCEL, abstractions). This one deliberately teaches **without** a framework — the M5 agentic harness is ~100 lines of raw SDK. For a team that will deploy Claude / Anthropic SDK in production (not a LangChain abstraction), this is the right posture. LangChain Academy content would actively mislead engineers about where the primitives live. **Post-fix: YES over vendor framework courses, no contest.**

---

## Will this make my team measurably more productive in 2 weeks?

**Today: no.** The starter-repo mismatch alone means engineers will bounce at M2 (first real graded assignment) and spend 30 minutes figuring out whether the course is broken or they are. That's the worst learning moment — bad enough that 10 out of 80 will stop and never return, and the rest will Slack a channel with "is AIE course broken?" within hour 1 of cohort day 1.

**Post-P0 fix: yes, measurably.** The bones are so good that once the three ship-blockers are resolved:
- Every engineer writes a real CLAUDE.md for their own team repo (measurable: before/after turn count on a common task).
- Every engineer ships a PreToolUse hook that blocks a dangerous command their team cares about (measurable: # teams that end up committing one to their repo).
- Every engineer understands the `tool_use` / `tool_result` loop and can debug their own agent when it hangs (measurable: fewer "my agent is stuck" Slack threads in week 3+).
- Every engineer has the behavioral reflex to rewrite prompts instead of argue with output (measurable, but harder — ask week-3 self-rating).

My estimate: if P0-1, P0-2, P0-3 land, this is the single highest-ROI enablement we could run next quarter. Two weeks is realistic. Just not with today's content.

---

## Concrete recommendations

1. **Regenerate the course with the Nexboard narrative excised** — rewrite M1–M6 concept steps to use the tickets service as the native domain, replace "Sofia/Marcus at Nexboard" with generic "your teammate" or ticket-service engineers, drop Redis/Socket.io references, and re-test M2.S3 + M3.S4 hidden tests for the new domain. (Lowest-cost P0 fix — one Creator regen.)
2. **Fix M4.S3's hallucinated clone URL** and point to `tusharbisht/aie-team-tickets-mcp` (or your final `skills-lab-demos/` home).
3. **Commit the per-module scaffolding** that the course content references:
   - `module-3-iterate`: add `migrations/001_initial.sql` with the column definitions the step expects (or delete the migrations reference from the step content).
   - `module-4-mcp`: add a stubbed `app/health/tickets.py` or at least a TODO-in-router that the learner extends.
   - `module-5-team`: add an empty `.claude/` dir with a README explaining it's the scaffold to populate.
   - `module-6-agent-harness`: add the `harness/`, `planted_bugs/`, and `tests/agent_harness/` directories with at least one planted bug that your 3-bug CI workflow actually exercises.
4. **Write a `lab-grade-capstone.yml` (or extend `lab-grade.yml`)** that adds capstone-specific tests per-module — M4 checks for `/health/tickets` returning ticket-count JSON; M5 runs the agent harness against 3 planted bugs; M6 validates the `.claude/` directory structure. Today's single workflow is real for M1–M3 but theater for M4–M6.
5. **Run one end-to-end learner walkthrough post-fix** (with a senior eng, not a beginner-agent) from M0.S1 → M6.S6 actually typing commands. Budget 2.5 hrs. Expect to find 3–5 more P1s.
6. **Ship to a small pilot first** (6–8 engineers, volunteer-opt-in) before mandating to 80. Two-week pilot, collect friction points, then wave-2 expand.

If all six land, this ships as our canonical enablement. If P0-1 and P0-3 don't, greenlight a different content plan for this quarter.

---

## Evidence log (for anyone verifying)

- GitHub tree `tusharbisht/aie-course-repo` every module branch: `b418ef8d` for `tests/test_tickets.py` (identical across all seven branches).
- `git clone https://github.com/anthropic/team-tickets-mcp.git` returns 404; `tusharbisht/aie-team-tickets-mcp` is the real repo.
- `sqlite3 skills_lab.db "SELECT validation FROM steps WHERE id = (SELECT id FROM steps WHERE module_id=23190 AND position=3);"` returns hidden tests asserting `"redis" in content` and file references to `app/auth/session_manager.py`.
- M0.S2 `/api/exercises/validate` probe results: weak=0.0, fabricated=0.44, realistic=1.0.
- M5.S2 (step 85077) `/api/exercises/validate` Docker run returns `7/8 hidden tests passed` on a hand-written solution, `0/1 tests passed` on a comment-cheese submission.
- `terminal.js` contains inline comment: "SECURITY: this template NEVER captures/stores/transmits any API key."
- `.github/workflows/lab-grade.yml` (main branch): runs pytest + asserts `/health` route; no capstone-specific tests for M4 or M6.

— reviewed, 2026-04-25
