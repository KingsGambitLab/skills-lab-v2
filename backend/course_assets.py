"""Course-asset registry.

A single, extensible source of truth for the external assets that
AI-augmented courses depend on:

  - **Starter repos** (GitHub URLs where the learner forks/clones)
  - **Pre-built MCP servers** (course-owned tooling learners consume)
  - **GHA workflow templates** (shape of `lab-grade.yml`)

Why this exists:
  User directive (2026-04-24): "If this works, we will build a lot of
  similar courses. Build everything extensible, don't hard code."

  Hard-coding "this course uses THIS repo and THIS MCP" buries a
  fragile coupling in each course's step content. Instead, a course
  declares a short `asset_slug`; the registry resolves the slug to
  concrete URLs. Adding a new course is one registry entry + one
  github-repo-creation, not edits across the codebase.

Conventions (tracked here so every course follows the same shape):

  1. A starter repo lives at:
       `https://github.com/skills-lab-demos/<slug>-course-repo`
     with branches per module:
       `module-0-preflight`, `module-1-starter`, `module-2-retry`,
       `module-3-iterate`, `module-4-mcp`, `module-5-team`,
       `module-6-agent-harness` (etc. — extend per course).
     GHA workflow at `.github/workflows/lab-grade.yml`.

  2. A pre-built MCP server lives at:
       `https://github.com/skills-lab-demos/<slug>-<mcp_name>-mcp`
     with a README that documents its tool surface for the course's
     M4 (or equivalent) code_read rubric-graded explanation step.

  3. Branch naming is `module-<N>-<short_slug>` across all courses so
     the UX (bootstrap command, breadcrumb banner) is identical.

Adding a new course:
  - Create two GitHub repos (course-repo + mcp) under the skills-lab-demos org.
  - `register_course_assets(slug=..., course_repo=..., mcp_servers=[...])` below.
  - Reference the slug from the Creator course's source_material;
    per-step `demo_data` pulls URLs via `resolve_asset(course_slug, ...)`.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class McpServerAsset:
    """A course-owned MCP server the learner consumes (not builds)."""
    name: str  # e.g. "team-tickets"
    repo: str  # https://github.com/skills-lab-demos/<slug>-team-tickets-mcp
    transport: str = "stdio"  # stdio | http | sse
    tools: tuple[str, ...] = ()  # declared tool names for pedagogy
    description: str = ""


@dataclass(frozen=True)
class CourseAsset:
    """Full asset declaration for one course."""
    slug: str  # short unique id, e.g. "aie"
    title_hint: str  # used for asset README generation
    course_repo: str  # https://github.com/...
    # Branch naming per module. Keys are module slugs (free-form but
    # `module-<N>-<slug>` strongly recommended), values are branch names.
    module_branches: dict[str, str] = field(default_factory=dict)
    # Pre-built MCP servers bundled with this course.
    mcp_servers: tuple[McpServerAsset, ...] = ()
    # The GHA workflow file name inside `.github/workflows/`.
    gha_workflow_file: str = "lab-grade.yml"
    # The expected GHA job name (grader asserts this job passed).
    gha_grading_job: str = "grade"

    # ── Behavioral test harness (2026-04-28) ──
    # Per CLAUDE.md §"BEHAVIORAL TEST HARNESS — the test class IS the
    # rubric": when a course has a hidden grading harness in its repo,
    # the LMS grades by running this command + reading exit code.
    # Universal contract:
    #   - Command takes one arg: the exercise-dir (e.g. "exercise-01-fix-n-plus-one")
    #   - Stages hidden tests, runs language-default test runner with 120s timeout,
    #     emits "RESULT: PASS|FAIL" line + grading-result.json, exits 0/1.
    #   - See tools/grading-skeletons/README.md for the full contract.
    # When set, Creator prompt rule #14 collapses the per-step rubric to a
    # single generic line (cli_command runs this; rubric is "exit 0 = pass").
    # When None, falls back to per-step LLM-authored rubric prose (legacy path
    # for non-code-fix courses + courses that haven't migrated yet).
    grading_runner: str | None = None
    # Language hint for test framework selection in the runner; informational.
    # Values: "java", "python", "node", "go", "rust", "ruby" — corresponds
    # to subdirectories under tools/grading-skeletons/.
    grading_test_lang: str | None = None
    # Per-step → exercise-dir mapping. The Creator (or harness-side overlay)
    # emits the cli_command with this exercise-dir baked in:
    #   bash .grading/run-grading.sh <exercise-dir>
    # Keys are "M{module_position}.S{step_position}" — 1-indexed in BOTH dims,
    # matching the DB Module.position + Step.position fields. Values are the
    # exercise dir name under .grading/ on the course-repo.
    # Steps NOT in this map fall back to the legacy LLM-authored rubric path
    # (preflight steps, deprecated reflection steps, system_build with GHA, etc.).
    exercise_dirs: dict[str, str] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════
# Registry
# ═══════════════════════════════════════════════════════════════════

_COURSE_ASSETS: dict[str, CourseAsset] = {}


def register_course_assets(asset: CourseAsset) -> None:
    """Register a course's external assets. Safe to call multiple times
    per slug (last registration wins — supports hot-reload in dev)."""
    _COURSE_ASSETS[asset.slug] = asset


def get_course_assets(slug: str) -> CourseAsset | None:
    return _COURSE_ASSETS.get(slug)


def all_course_slugs() -> list[str]:
    return sorted(_COURSE_ASSETS.keys())


def resolve_asset(slug: str, kind: str, **kwargs) -> str | None:
    """Resolve a specific URL/value. Returns None if slug unknown.

    Supported `kind`s:
      - "course_repo"                  — returns the full HTTPS URL
      - "module_branch" + module=<key> — returns branch name for that module
      - "mcp_repo" + name=<mcp_name>   — returns repo URL for a named MCP
      - "gha_workflow"                 — workflow file name
      - "gha_grading_job"              — expected grading job name
    """
    a = get_course_assets(slug)
    if not a:
        return None
    if kind == "course_repo":
        return a.course_repo
    if kind == "module_branch":
        return a.module_branches.get(kwargs.get("module", ""))
    if kind == "mcp_repo":
        want = kwargs.get("name", "")
        for m in a.mcp_servers:
            if m.name == want:
                return m.repo
        return None
    if kind == "gha_workflow":
        return a.gha_workflow_file
    if kind == "gha_grading_job":
        return a.gha_grading_job
    return None


def detect_slug_for_course(course_title: str) -> str | None:
    """Match a course title to a registered asset slug via title_hint
    fuzzy word-overlap. Returns the best-matching slug at score >= 0.6,
    or None if no asset matches well enough.

    2026-04-27 — added for harness-side starter_repo injection. The gate
    fires REJECT for repo-walking terminal_exercise / system_build steps
    that emit no scaffold; the harness reads this fn to find the
    course's repo + injects starter_repo deterministically post-LLM-call.
    Buddy-Opus 2026-04-27: "URL injection is harness-side, not LLM-prompt-
    side. Don't trust LLM to remember; gate-time enforcement, harness-side
    injection, never via prompt nag."

    Word-overlap (not regex/substring) so "Open-Source AI Coding: Kimi K2"
    + "Open-Source AI Coding: Ship Production Features with Kimi K2 +
    Aider" matches; "Claude Code in Production" doesn't bleed into
    "Claude Code for Spring Boot" because the differentiating words
    ("production" vs "spring", "boot") win.
    """
    if not course_title:
        return None
    title_words = {w.strip(":,.+") for w in course_title.lower().split() if len(w.strip(":,.+")) > 3}
    if not title_words:
        return None
    best_match: str | None = None
    best_key = (0.0, 0)  # (score_ratio, raw_match_count)
    for slug, asset in _COURSE_ASSETS.items():
        hint = (asset.title_hint or "").lower()
        if not hint:
            continue
        hint_words = {w.strip(":,.+") for w in hint.split() if len(w.strip(":,.+")) > 3}
        if not hint_words:
            continue
        matches = sum(1 for w in hint_words if w in title_words)
        score = matches / len(hint_words)
        if score < 0.6:
            continue
        # Tie-break: when two slugs have equal score (e.g. jspring "Claude Code
        # for Spring Boot" 4/4=1.0 + claude-code "Claude Code in Production"
        # 3/3=1.0 both fire on a Spring Boot title that happens to contain
        # "production"), prefer the slug with MORE absolute hint-word matches.
        # That's the more SPECIFIC match — every word of jspring's hint
        # appeared, including the differentiating "spring" + "boot".
        key = (score, matches)
        if key > best_key:
            best_key = key
            best_match = slug
    return best_match


def module_key_for_position(slug: str, position_1based: int) -> str | None:
    """Map a course's module POSITION (1-indexed) to its registered
    branch key. Convention is "first registered key = M0 / position 1,
    second = M1 / position 2, ...". Today this lines up across the 3
    BYO-key courses (kimi, jspring, claude-code) which all register
    keys in the same order: preflight, first-fix, claudemd, agents,
    hooks, mcp, capstone.
    """
    a = get_course_assets(slug)
    if not a:
        return None
    keys = list(a.module_branches.keys())
    if 1 <= position_1based <= len(keys):
        return keys[position_1based - 1]
    return None


def build_course_context_block(slug: str) -> str:
    """Authoritative course-context for the LLM at every per-step gen call.

    2026-04-27 (post-v6-reviewer URL hallucination findings): the LLM
    regenerated 9 kimi steps and emitted prose like
    `git clone tusharbisht/kimi-course-repo` — a SHORT slug that doesn't
    exist on GitHub. The real slug is `kimi-eng-course-repo`. The harness-
    injected `starter_repo.url` is correct; only briefing prose drifts.

    Per CLAUDE.md §"NO MEDIATORS": no regex on prose to fix this. Per
    buddy-Opus 2026-04-27: the structural fix is to inject a
    course_context block into the system prompt at every call, listing
    the FULL repo URL + per-module branches verbatim. Single source of
    truth, present on every call, ~50 tokens.

    Returns empty string when the slug is unknown / unregistered, so the
    block is just absent from the prompt rather than emitting noise.
    """
    a = get_course_assets(slug)
    if not a:
        return ""
    lines: list[str] = []
    lines.append("=== COURSE CONTEXT (authoritative — quote VERBATIM, do not abbreviate) ===")
    lines.append(f"Course slug: {slug}")
    lines.append(f"Course repo: {a.course_repo}")
    lines.append("Per-module branches:")
    for key, branch in a.module_branches.items():
        lines.append(f"  - {key}: {branch}")
    if a.mcp_servers:
        lines.append("MCP servers (use these names + repos verbatim):")
        for m in a.mcp_servers:
            lines.append(f"  - name: {m.name} | repo: {m.repo} | transport: {m.transport}")
    lines.append("RULE: when emitting `git clone`, prose, or any URL reference, USE THE FULL")
    lines.append("repo URL above. Do NOT invent short slugs like `<org>/<short-name>`. Branch")
    lines.append("names are exactly as listed — no abbreviations.")
    lines.append("=== END COURSE CONTEXT ===")
    return "\n".join(lines)


def build_bootstrap_command(
    slug: str,
    module_key: str,
    *,
    post_clone_cmd: str = "",
) -> str | None:
    """Build the one-line copy-to-terminal bootstrap for a given
    (course, module). Returns None if the course/module isn't registered.

    Result shape (default — no post-clone trailing command):
      git clone <course_repo> && cd <repo_basename> && git checkout <branch>

    With post_clone_cmd:
      git clone <course_repo> && cd <repo_basename> && git checkout <branch> && <post_clone_cmd>

    2026-04-27 (v0.1.17 fix) — default post_clone_cmd flipped from
    `"claude"` to `""` (empty). User feedback: the bootstrap was ending
    in `&& claude` for EVERY step including M0 preflight (toolchain
    verification), so clicking the clone command immediately dropped the
    learner into Claude Code's interactive REPL — wrong for a step whose
    only goal is verifying `claude --version`, `java -version`, `./mvnw -v`
    on the host. Cloning is universal; starting Claude is a per-step
    decision that belongs in `cli_commands` or instructions, not in the
    clone command.

    Callers that genuinely want `&& claude` (e.g. M1.S2 "fix the N+1 with
    Claude Code") can pass `post_clone_cmd="claude"` explicitly. But the
    default no longer footguns the diagnostic / preflight steps.
    """
    a = get_course_assets(slug)
    if not a:
        return None
    branch = a.module_branches.get(module_key)
    if not branch:
        return None
    # Derive repo dir name from the URL
    import re as _re
    m = _re.search(r"/([^/]+?)(?:\.git)?/?$", a.course_repo)
    dirname = m.group(1) if m else "course-repo"
    parts = [
        f"git clone {a.course_repo}",
        f"cd {dirname}",
        f"git checkout {branch}",
    ]
    if post_clone_cmd:
        parts.append(post_clone_cmd)
    return " && ".join(parts)


# ═══════════════════════════════════════════════════════════════════
# Initial registrations
# ═══════════════════════════════════════════════════════════════════
# These live in the same file for bootstrap simplicity. Long-term
# split into per-course modules under `backend/course_assets/<slug>.py`
# once we have >10 courses.
#
# The URLs below are placeholders; when we actually create the
# `skills-lab-demos` GitHub org repos they'll resolve. Per CLAUDE.md:
# "don't hard code" — each course is ONE entry here, not code-level wiring.

register_course_assets(CourseAsset(
    slug="kimi",
    title_hint="Open-Source AI Coding: Kimi K2 + Aider",
    # 2026-04-25 — open-source-friendly variant of the AIE shape.
    # Same patterns (BYO-key, terminal-first, per-module branches,
    # GHA capstone) but Aider + Kimi K2 (Moonshot) + Python content.
    # Reuses the language-agnostic aie-team-tickets-mcp via a Python
    # adapter (M5) so the same MCP serves Anthropic + non-Anthropic
    # learners.
    course_repo="https://github.com/tusharbisht/kimi-eng-course-repo",
    module_branches={
        "preflight":      "module-0-preflight",
        "first-fix":      "module-1-starter",
        "claudemd":       "module-2-claudemd",
        "agents":         "module-3-agents",
        "hooks":          "module-4-hooks",
        "mcp":            "module-5-mcp",
        "capstone":       "module-6-capstone",
    },
    mcp_servers=(
        McpServerAsset(
            name="team-tickets",
            repo="https://github.com/tusharbisht/aie-team-tickets-mcp",
            transport="stdio",
            tools=("list_recent_tickets", "get_ticket_health"),
            description=(
                "Linear-flavored team-tickets MCP (reused from AIE). "
                "Spring Boot + Python teams alike consume it; in M5 the "
                "Kimi course wires it via a Python MCP-adapter that "
                "bridges stdio JSON-RPC to OpenAI-compatible tool_call "
                "definitions Moonshot accepts natively."
            ),
        ),
    ),
))


register_course_assets(CourseAsset(
    slug="jspring",
    title_hint="Claude Code for Spring Boot",
    # v8.6.2 (2026-04-24) — Java + Spring Boot variant of the AIE course
    # shape. Same patterns (BYO-key, terminal-first, per-module branches,
    # GHA capstone) but Maven/JUnit/Testcontainers content. Reuses the
    # language-agnostic aie-team-tickets-mcp (stdio, mock tickets) —
    # Java teams consume it identically to the Python/Node teams.
    course_repo="https://github.com/tusharbisht/jspring-course-repo",
    module_branches={
        "preflight":      "module-0-preflight",
        "first-fix":      "module-1-starter",
        "claudemd":       "module-2-claudemd",
        "agents":         "module-3-agents",
        "hooks":          "module-4-hooks",
        "mcp":            "module-5-mcp",
        "capstone":       "module-6-capstone",
    },
    mcp_servers=(
        McpServerAsset(
            name="team-tickets",
            # Reused from AIE — language-agnostic stdio MCP.
            repo="https://github.com/tusharbisht/aie-team-tickets-mcp",
            transport="stdio",
            tools=("list_recent_tickets", "get_ticket_health"),
            description=(
                "Linear-flavored team-tickets MCP (reused from AIE). Exposes "
                "read-only tools over mock internal API. Spring Boot teams "
                "wire this into Claude Code for 'which ticket should I pick "
                "up next?' context during M5."
            ),
        ),
    ),
    # 2026-04-28 — Behavioral test harness wired. .grading/ skeleton lives
    # on every module branch (commit ce7df23). Creator prompt rule #14
    # picks up grading_runner and emits generic shape for code-fix steps.
    grading_runner="bash .grading/run-grading.sh",
    grading_test_lang="java",
    exercise_dirs={
        # Keys: "M{module_position}.S{step_position}" — 1-indexed.
        # Looked up by harness post-LLM via Step.position + Module.position.

        # M2.S2 — Fix N+1 in OrderService.getRecentOrders (no CLAUDE.md)
        "M2.S2": "exercise-01-fix-n-plus-one",
        # M3.S4 — Retry the N+1 fix WITH CLAUDE.md (same hidden test;
        # different SUT branch tells us whether CLAUDE.md context helped)
        "M3.S4": "exercise-01-fix-n-plus-one",
        # M4.S2 — Slash command /controller-review (verify.sh)
        "M4.S2": "exercise-03-slash-command-controller-review",
        # M4.S3 — mockito-test-writer subagent (verify.sh)
        "M4.S3": "exercise-04-subagent-mockito-test-writer",
        # M5.S2 — Three hooks wired in .claude/settings.json (verify.sh)
        "M5.S2": "exercise-05-hooks-three-wired",
        # M6.S2 — team-tickets MCP wired (verify.sh + claude mcp list --json)
        "M6.S2": "exercise-06-mcp-team-tickets-wired",
        # M7.S3 — Capstone: OrdersController + integration test
        "M7.S3": "exercise-02-orders-controller",
        # NOT mapped (fall back to legacy LLM-rubric path):
        #   M1.S2 preflight — toolchain version checks via exit codes only
        #   M2.S4 conventions reflection — Tier E (deprecated, will redesign)
        #   M3.S2 draft CLAUDE.md — Tier E borderline (defer)
        #   M6.S4 consume MCP — Tier E (defer; needs MCP-side change)
        #   M7.S2 fork+baseline — exit-code only via gh-api
        #   M7.S4 push+GHA — already system_build + gha_workflow_check
    },
))


register_course_assets(CourseAsset(
    # 2026-04-28 — cc-spring registration for the inspiration repo:
    # github.com/tusharbisht/claude-code-springboot-exercises.
    #
    # External course-repo we did NOT create via Skillslab content-gen
    # (per user constraint 2026-04-28: "don't change any repo we did not
    # create"). The CourseAsset is plumbing-only — points the LMS at the
    # external repo, configures the grading-runner path, and lets the
    # launch endpoint compose Codespace / github.dev / clone URLs +
    # README fetch (hands_on.py's fallback chain handles this repo's
    # branch-root EXERCISE.md + CLAUDE_INSTRUCTIONS.md layout).
    #
    # The LMS course rows (Course / Module / Step) are NOT registered
    # here — they will be generated by the Creator (/api/creator/start
    # → /refine → /generate) when the user is ready, per the user's
    # "create by content-gen" directive.
    #
    # Inspiration-repo notes:
    # - 9 exercise/* branches mapped here (01-09). Each grading/<dir>/
    #   has a Hidden*GradingTest.java; problem statement at branch root
    #   in EXERCISE.md + CLAUDE_INSTRUCTIONS.md.
    # - 4 meta/* branches (build-claude-md / hooks-and-commands /
    #   custom-subagent / open-ended-feature) use different dir naming
    #   `meta-NN-<slug>` — would require schema extension; deferred.
    # - tour/workflow + extra/multi-module-preview also deferred.
    # - Inspiration repo's grade.yml does NOT post to Skillslab. Only
    #   `skillslab check` CLI auto-submit (VS Code extension v0.1.23
    #   path) wires up to the LMS for cc-spring; no GHA attestation.
    slug="cc-spring",
    title_hint="Claude Code Spring Boot Exercises (TaskManager)",
    course_repo="https://github.com/tusharbisht/claude-code-springboot-exercises",
    module_branches={
        "validation":     "exercise/01-fix-validation-bug",
        "search":         "exercise/02-implement-search",
        "n-plus-one":     "exercise/03-optimize-n-plus-one",
        "refactor":       "exercise/04-refactor-fat-controller",
        "concurrency":    "exercise/05-investigate-vague-symptom",
        "tests-scratch":  "exercise/06-tests-from-scratch",
        "migration":      "exercise/07-migration",
        "anti-exercise":  "exercise/08-when-not-to-use-claude",
        "confident-wrong": "exercise/09-confident-but-wrong",
    },
    mcp_servers=(),  # cc-spring doesn't ship an MCP server today
    # No GHA attestation for cc-spring — its grade.yml is local-only.
    # The CLI auto-submit path (skillslab check via VS Code v0.1.23) is
    # the only wire from learner runs back to LMS.
    gha_workflow_file="grade.yml",
    gha_grading_job="grading",  # the inspiration's job name; informational
    # The inspiration repo uses `grading/` (no dot-prefix). Our launch
    # endpoint's README fallback chain (backend/hands_on.py 2026-04-28)
    # handles both. Computed branch shape `exercise/NN-<slug>` + dir
    # `exercise-NN-<slug>` already match this repo's convention.
    grading_runner="bash grading/run-grading.sh",
    grading_test_lang="java",
    # No exercise_dirs map — when the Creator generates cc-spring's LMS
    # rows, the F6 prompt rule directs the LLM to emit hands_on steps
    # with demo_data.{course_slug='cc-spring', exercise_nn, exercise_slug}
    # directly. The harness overlay (apply_grading_runner_overlay) is
    # not used here because the LLM's emit is already correct shape.
    exercise_dirs={},
))


register_course_assets(CourseAsset(
    # 2026-04-25 v3 — renamed from "aie" → "claude-code" per user directive.
    # The course's actual subject is Claude Code (CLAUDE.md / hooks /
    # subagents / MCP); "AI-Augmented Engineering" was a confusing umbrella
    # label. The course_repo URL stays at `aie-course-repo` for now (the
    # GitHub repo + module branches are unchanged); migrating the GitHub
    # org+repo name is a separate piece of work that requires the existing
    # learners' forks to be re-targeted. Slug rename is enough to fix the
    # learner-facing surface.
    slug="claude-code",
    title_hint="Claude Code in Production",
    course_repo="https://github.com/tusharbisht/aie-course-repo",
    # v8.6.1 (2026-04-24) — ORDER MATCHES THE GENERATED COURSE. Python 3.7+
    # dicts preserve insertion order, and the backfill maps position 0 →
    # first key, position 1 → second key, etc. The Creator's refine phase
    # produced M4 = mcp → M5 = agent-harness (index 5) → M6 = team-claude
    # (index 6 because team-Claude was added LAST via add_module_to_course).
    # If we ever regen from scratch with team-Claude as M5, reorder accordingly.
    module_branches={
        "preflight":      "module-0-preflight",
        "first-fix":      "module-1-starter",
        "context-gap":    "module-2-retry",
        "iterate":        "module-3-iterate",
        "mcp-capstone":   "module-4-mcp",
        "agent-harness":  "module-6-agent-harness",
        "team-claude":    "module-5-team",
    },
    mcp_servers=(
        McpServerAsset(
            name="team-tickets",
            repo="https://github.com/tusharbisht/aie-team-tickets-mcp",
            transport="stdio",
            tools=("list_recent_tickets", "get_ticket_health"),
            description=(
                "Linear-flavored team-tickets MCP. Exposes read-only tools "
                "over a mock internal API. Used in M4 as the consume-an-MCP "
                "teaching asset."
            ),
        ),
    ),
))
