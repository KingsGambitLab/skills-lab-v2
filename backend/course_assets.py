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


def build_bootstrap_command(
    slug: str,
    module_key: str,
    *,
    post_clone_cmd: str = "claude",
) -> str | None:
    """Build the one-line copy-to-terminal bootstrap for a given
    (course, module). Returns None if the course/module isn't registered.

    Result shape:
      git clone <course_repo> && cd <repo_basename> && git checkout <branch> && <post_clone_cmd>

    The terminal-template JS layer wraps this with the SLL step-aware
    banner + shell prompt indicator, so callers don't need to add those.
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
    return (
        f"git clone {a.course_repo} && "
        f"cd {dirname} && "
        f"git checkout {branch} && "
        f"{post_clone_cmd}"
    )


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
