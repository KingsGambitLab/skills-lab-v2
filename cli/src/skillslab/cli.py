"""skillslab — entry-point CLI dispatch.

Top-level commands:
    skillslab login [--email ... --password ...]
    skillslab logout
    skillslab whoami
    skillslab courses                        # list available + your enrollments
    skillslab enroll <course-slug-or-id>
    skillslab start <course-slug-or-id>      # download all step content as markdown files
    skillslab status                         # show current step + progress
    skillslab spec                           # cat the current step's markdown
    skillslab next                           # advance pointer (does NOT auto-check)
    skillslab prev
    skillslab goto M<n>.S<m>
    skillslab check                          # evaluate; on pass, mark complete + advance
    skillslab progress                       # sync from LMS (in case you completed elsewhere)
    skillslab dashboard                      # print URL to open in browser

Per-course wrappers (see pyproject.toml [project.scripts]):
    kimi-course <cmd>     == skillslab --course=kimi <cmd>
    aie-course <cmd>      == skillslab --course=aie <cmd>
    jspring-course <cmd>  == skillslab --course=jspring <cmd>
"""
from __future__ import annotations

import json
import os
import sys
import getpass
from pathlib import Path
from typing import Any

import click
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from . import api, state, __version__
from .check import run_check
from .render import step_to_markdown

console = Console()

# ── Utility helpers ────────────────────────────────────────────────────────

def _resolve_course(slug_or_id: str | None) -> tuple[str, str]:
    """Normalize a slug ('kimi', 'claude-code', 'jspring') OR a course_id
    ('created-…') into (slug, course_id). The mapping is recorded under
    `~/.skillslab/<slug>/meta.json` after the first `start`. For the
    bootstrap path we also accept course_id directly.

    2026-04-25 v3 — slug aliases: deprecated 'aie' is canonicalized to
    'claude-code' so cached state under `~/.skillslab/aie/` keeps working
    after the rename.
    """
    if not slug_or_id:
        # Pick the most recently active course from cached metadata
        latest = None
        h = state.home()
        for child in h.iterdir():
            if not child.is_dir():
                continue
            mp = child / "meta.json"
            if mp.exists():
                try:
                    m = json.loads(mp.read_text())
                    if not latest or (m.get("last_active_at", "") > latest[1].get("last_active_at", "")):
                        latest = (child.name, m)
                except Exception:
                    pass
        if not latest:
            console.print("[red]No active course. Run `skillslab start <course-slug>` first.[/red]")
            sys.exit(2)
        return latest[0], latest[1].get("course_id") or ""
    # Canonicalize aliased slugs FIRST, so the rest of the resolution path
    # operates on the post-alias name. (`_canonicalize_slug` is defined
    # below, near _SLUG_HINTS — module-level lookup, no cycle.)
    canonical = _canonicalize_slug(slug_or_id)
    if canonical != slug_or_id:
        # If a state dir exists under EITHER the new or old slug, prefer
        # whichever has a meta.json. New takes priority.
        for candidate in (canonical, slug_or_id):
            mp = state.home() / candidate / "meta.json"
            if mp.exists():
                try:
                    m = json.loads(mp.read_text())
                    return candidate, m.get("course_id") or canonical
                except Exception:
                    pass
        return canonical, canonical
    # If it looks like an existing slug under HOME, use its meta.json
    cdir = state.home() / slug_or_id
    meta_path = cdir / "meta.json"
    if meta_path.exists():
        try:
            m = json.loads(meta_path.read_text())
            return slug_or_id, m.get("course_id") or slug_or_id
        except Exception:
            pass
    # Else assume it's a course_id directly OR a slug to be resolved server-side
    return slug_or_id, slug_or_id


# Forward-declarations — `_canonicalize_slug` and `_SLUG_ALIASES` are
# defined later in this file (near `_SLUG_HINTS`). Python module-level
# resolution handles this fine because `_resolve_course` is only CALLED
# from command handlers that fire at runtime.


def _get_course_id_or_die(slug: str) -> str:
    cdir = state.home() / slug
    mp = cdir / "meta.json"
    if not mp.exists():
        console.print(f"[red]Course '{slug}' not started locally. Run:[/red]")
        console.print(f"  skillslab start {slug}")
        sys.exit(2)
    return json.loads(mp.read_text()).get("course_id") or slug


# ── Commands ───────────────────────────────────────────────────────────────

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="skillslab")
@click.option("--course", default=None, help="Course slug (kimi / claude-code / jspring) — also via per-course wrapper. `aie` is a deprecated alias for `claude-code`.")
@click.pass_context
def cli(ctx: click.Context, course: str | None):
    """Skills Lab — AI-augmented engineering courses, in your terminal."""
    ctx.ensure_object(dict)
    ctx.obj["course"] = course


@cli.command()
def login():
    """Sign in. Prompts for email + password if not signed in via cookie."""
    cur = state.get_token()
    if cur:
        who = api.whoami()
        if who:
            console.print(f"[green]Already signed in[/green] as [bold]{who['email']}[/bold]")
            console.print("Run `skillslab logout` to switch users.")
            return
    console.print(Panel.fit(
        f"Sign in to [bold]{state.api_url()}[/bold]\n"
        "Set [cyan]SKILLSLAB_API_URL[/cyan] env to point at a different server.",
        title="skillslab login", border_style="cyan",
    ))
    email = click.prompt("Email")
    password = getpass.getpass("Password: ")
    try:
        out = api.login_with_password(email, password, label=f"cli@{os.uname().nodename}")
    except api.ApiError as e:
        console.print(f"[red]Login failed:[/red] {e}")
        sys.exit(1)
    state.set_token(out["token"])
    console.print(f"[green]✓ Signed in[/green] as [bold]{out['email']}[/bold]")
    console.print(f"  token saved to {state.token_path()}")
    console.print(f"  expires:        {out['expires_at']}")


@cli.command()
def logout():
    """Forget the local token (server session is also revoked next time it expires)."""
    if state.get_token():
        state.clear_token()
        console.print("[green]✓ Signed out[/green] (local token cleared)")
    else:
        console.print("[yellow]Already signed out.[/yellow]")


@cli.command()
def whoami():
    """Show who you are."""
    who = api.whoami()
    if not who:
        console.print("[yellow]Not signed in.[/yellow] Run [cyan]skillslab login[/cyan].")
        sys.exit(1)
    console.print(f"[bold]{who['email']}[/bold]   role: [cyan]{who['role']}[/cyan]   user_id: {who['id']}")


@cli.command()
def courses():
    """List courses you can take + ones you've enrolled in."""
    enrolled = api.my_courses()
    catalog = api.all_courses()

    e_by_id = {e["course_id"]: e for e in enrolled}

    t = Table(title="Skills Lab — Courses", box=box.SIMPLE_HEAVY, show_header=True)
    t.add_column("Slug", style="cyan", no_wrap=True)
    t.add_column("Title", style="white")
    t.add_column("Level", style="yellow")
    t.add_column("Enrolled", style="green")
    t.add_column("Progress", justify="right")
    for c in catalog:
        cid = c.get("id")
        enr = e_by_id.get(cid)
        slug = _slug_for_course_title(c.get("title", ""))
        title = c.get("title", "")[:60]
        level = c.get("level", "") or "—"
        if enr:
            pct = int(enr.get("progress_percent") or 0)
            t.add_row(slug, title, level, "✓", f"{pct}%")
        else:
            t.add_row(slug, title, level, "—", "")
    console.print(t)
    console.print()
    console.print("[dim]Run `skillslab enroll <slug>` to enroll, then `skillslab start <slug>` to begin.[/dim]")


_SLUG_HINTS = [
    ("kimi", ["kimi", "moonshot", "open-source ai coding", "aider"]),
    # 2026-04-25 v3 — renamed AIE → claude-code per user directive. The course
    # is structurally about Claude Code (CLAUDE.md / hooks / subagents / MCP);
    # "AI-Augmented Engineering" was a confusing umbrella label. The hints
    # below match BOTH the old and new titles so cached state on disk and
    # any pre-rename DB entries still resolve.
    ("claude-code", [
        "claude code in production",      # new canonical title
        "claude code mastery",            # alt
        "ai-augmented engineering",       # legacy title (still accepted)
        "claude code + api",              # legacy subtitle
        "claude code + mcp",              # legacy
    ]),
    ("jspring", ["spring boot", "java"]),
]

# Slug aliases — old → new mappings. Used by `_resolve_course` so an
# existing `~/.skillslab/aie/` state directory keeps working after the
# rename. The canonical slug ALWAYS wins for new state.
_SLUG_ALIASES = {
    "aie": "claude-code",
}


def _slug_for_course_title(title: str) -> str:
    t = (title or "").lower()
    for slug, hints in _SLUG_HINTS:
        if any(h in t for h in hints):
            return slug
    return "—"


def _canonicalize_slug(slug: str) -> str:
    """Map deprecated slugs to their canonical form."""
    return _SLUG_ALIASES.get((slug or "").lower(), slug)


@cli.command()
@click.argument("slug")
def enroll(slug: str):
    """Enroll in a course by slug (or course_id)."""
    # If slug is a known short name, find the course in catalog
    cid = slug
    if not slug.startswith("created-"):
        for c in api.all_courses():
            if _slug_for_course_title(c.get("title", "")) == slug:
                cid = c["id"]
                break
        else:
            console.print(f"[red]Unknown slug '{slug}'. Run `skillslab courses` to list.[/red]")
            sys.exit(2)
    out = api.enroll(cid)
    if out.get("already_enrolled"):
        console.print(f"[yellow]Already enrolled[/yellow] (enrollment_id={out['enrollment_id']})")
    else:
        console.print(f"[green]✓ Enrolled[/green] (enrollment_id={out['enrollment_id']})")


@cli.command()
@click.argument("slug")
def start(slug: str):
    """Download every step's content as markdown files under
    ~/.skillslab/<slug>/steps/ AND set the cursor to the first incomplete step.
    Idempotent — re-running refreshes content.
    """
    # Resolve slug → course_id
    cid = slug
    if not slug.startswith("created-"):
        for c in api.all_courses():
            if _slug_for_course_title(c.get("title", "")) == slug:
                cid = c["id"]
                title = c.get("title", "")
                break
        else:
            console.print(f"[red]Unknown slug '{slug}'.[/red]")
            sys.exit(2)
    else:
        # Look up the title from catalog if possible
        title = next((c.get("title", "") for c in api.all_courses() if c.get("id") == cid), "")

    # Auto-enroll if needed
    enrolled = {e["course_id"]: e for e in api.my_courses()}
    if cid not in enrolled:
        try:
            api.enroll(cid)
            console.print(f"[green]✓ Enrolled[/green] in {title}")
        except api.ApiError as e:
            console.print(f"[yellow]Enroll skipped:[/yellow] {e}")

    console.print(f"[cyan]Fetching course content for {title}…[/cyan]")
    modules = api.get_modules_with_steps(cid)

    # Write per-step markdown files
    cdir = state.course_dir(slug)
    for f in (cdir / "steps").glob("*.md"):
        f.unlink()  # fresh start

    # 2026-04-25 — discover each module's starter repo ONCE (mirror of the
    # browser's _findModuleRepoMeta) so every step's md gets the URL in its
    # front-matter, AND meta.json carries it per-step. Same data the
    # learner sees in the browser banner; now also surfaced in `skillslab
    # status` and inside each step's spec.
    from .render import find_module_repo
    cursor_steps = []
    written = 0
    module_repos: dict[int, dict] = {}  # module_pos → repo dict (or None)
    for m in modules:
        m_pos = m.get("position", 0)
        m_title = m.get("title", "")
        repo = find_module_repo(m.get("steps", []) or [])
        if repo:
            module_repos[m_pos] = repo
        for s in m.get("steps", []):
            s_pos = s.get("position", 0)
            md = step_to_markdown(s, course_title=title, module_title=m_title,
                                   module_repo=repo)
            p = state.step_path(slug, m_pos, s_pos, s.get("title", "step"))
            p.write_text(md)
            written += 1
            cursor_steps.append({
                "module_pos": m_pos,
                "step_pos": s_pos,
                "step_id": s.get("id"),
                # 2026-04-25 v2 — also store as `id` so downstream Rich
                # panels can do `step.get('id')` without re-mapping. CLI-walk
                # v1 caught the spec panel rendering "step id: None" because
                # only `step_id` was present.
                "id": s.get("id"),
                "title": s.get("title", ""),
                "exercise_type": s.get("exercise_type") or "concept",
                # 2026-04-25 v2 — capture module_title here so the spec/now
                # panels can show it without re-fetching the course tree.
                # CLI-walk v1 caught the panel rendering "module:    type: ..."
                # with empty module name.
                "module_title": m_title,
                # 2026-04-25 v3 — capture module_id so _browser_url can build
                # a STEP-PRECISE deeplink (#courseId/moduleId/stepIdx). User
                # caught a live bug: clicking the URL on M1.S1 (Why context
                # is oxygen…) sent them to M0.S1 ("What this course IS…")
                # because the URL only had #courseId, and the frontend's
                # cursor was elsewhere. Frontend's parseHash supports the
                # 3-part form; we just weren't building it.
                "module_id": m.get("id"),
                # Phase 3 (2026-04-25) — surface-aware split. Captured at
                # `start` time so status/spec/check can dispatch by surface
                # without refetching the step. NULL → 'web' default (legacy
                # course pre-backfill).
                "learner_surface": s.get("learner_surface") or "web",
                "module_repo_url": (repo or {}).get("url"),
                "module_repo_ref": (repo or {}).get("ref"),
                "filename": p.name,
            })

    # Set cursor to first incomplete step (heuristic: pick step 0 if no progress data;
    # otherwise pick first whose progress is incomplete via /api/progress/{cid})
    cursor_idx = 0
    state.write_meta(slug, {
        "course_id": cid,
        "course_title": title,
        "steps": cursor_steps,
        "cursor": cursor_idx,
        "last_active_at": _now_iso(),
    })

    console.print(f"[green]✓ Wrote {written} step files to[/green] {cdir / 'steps'}")
    console.print(f"[dim]ls {cdir / 'steps'}[/dim]")
    # Don't dump every module's discovered repo here — earlier iteration did,
    # but the legacy HTML-grep fallback picked up prose-referenced URLs (and
    # in some courses, LLM-hallucinated org names) → noisy list of 5
    # different "repos" most of which aren't actual fork targets. Per
    # CLAUDE.md "rendering layer owns presentation, surface data WHEN it's
    # actionable": the per-step `status` command shows the CURRENT module's
    # repo when the learner reaches a step that needs it. start just
    # confirms what landed.
    console.print()
    console.print("[bold]Next:[/bold]")
    console.print(f"  skillslab status      # current step + its module repo (if any)")
    console.print(f"  skillslab spec        # read the current step's briefing")


def _load_cursor(slug: str) -> tuple[dict, int, dict]:
    meta = state.read_meta(slug)
    if not meta:
        console.print(f"[red]No state for course '{slug}'. Run `skillslab start {slug}`.[/red]")
        sys.exit(2)
    steps = meta.get("steps", [])
    cur = int(meta.get("cursor", 0))
    cur = max(0, min(cur, len(steps) - 1))
    return meta, cur, steps[cur] if steps else {}


def _step_surface(step: dict) -> str:
    """Return the step's learner_surface — defaults to 'web' if missing
    (legacy course pre-backfill OR a cached meta.json from before Phase 3
    shipped). 'web' is the safe default — sends the learner to the dashboard
    rather than to a CLI flow that won't grade their work."""
    return (step.get("learner_surface") or "web").lower()


def _strip_frontmatter(md: str) -> str:
    """Strip the leading YAML frontmatter (between two `---` lines) from
    a step's markdown so terminal renders don't show the raw YAML wall.

    The frontmatter exists in the file for tooling (other commands re-parse
    it for step_id / module_repo_url etc.), but it's not human-readable —
    user-filed (2026-04-25): it appeared as a one-line wrap with raw
    `\\u2014` em-dash escapes, looking like a parser error.

    We replace the visible frontmatter with a Rich-rendered header in the
    spec command itself (so the structured info is still surfaced, just
    nicely formatted)."""
    lines = md.splitlines()
    if not lines or lines[0].strip() != "---":
        return md
    end = None
    for i in range(1, min(len(lines), 50)):  # cap scan; frontmatter is small
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return md
    return "\n".join(lines[end + 1:]).lstrip("\n")


def _cwd_is_clone_of(repo_url: str) -> bool:
    """Heuristic: is the current working directory a git clone of `repo_url`?
    Used by _next_action() to decide whether to suggest `clone` vs jump
    straight to `spec`/edit-code/`check`. Tolerates fork URLs (your fork's
    origin might be different from the upstream). Matches by repo NAME +
    owner — if either matches the upstream owner OR the upstream repo
    name, we treat cwd as the right place to work.
    """
    import subprocess
    try:
        r = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=os.getcwd(), capture_output=True, text=True, timeout=3,
        )
        if r.returncode != 0:
            return False
        origin = (r.stdout or "").strip().rstrip(".git").rstrip("/")
        upstream = (repo_url or "").strip().rstrip(".git").rstrip("/")
        if not origin or not upstream:
            return False
        # Match by full repo (owner/repo) OR just repo name (handles forks)
        origin_name = origin.rsplit("/", 1)[-1].lower()
        upstream_name = upstream.rsplit("/", 1)[-1].lower()
        return origin == upstream or origin_name == upstream_name
    except Exception:
        return False


def _next_action(slug: str, meta: dict, step: dict | None,
                  caller: str | None = None) -> list[tuple[str, str]]:
    """Return a list of `(verb, command)` tuples the learner should run next.
    Always called from status/start/check/clone — keeps "what now?" omnipresent.

    `caller` is the name of the command currently emitting the panel
    ('spec' / 'next' / 'now' / 'status' / 'check'). When set, the helper
    prunes any action whose primary command is the SAME as the caller —
    a CTA that says "Read briefing  skillslab spec" right after the
    learner DID `skillslab spec` is wasted ink. CLI-walk v4 P2.

    State tree:
      - no token → skillslab login
      - no course meta → skillslab courses && skillslab start <slug>
      - cursor past last step → 🎉 course complete
      - current step is web → open browser + sync + next
      - current step is terminal:
         - has module_repo + cwd not the clone → skillslab clone [--fork]
         - has module_repo + cwd IS the clone → spec / edit / check
         - no module_repo (concept-only) → spec / next
    """
    actions: list[tuple[str, str]] = []
    if not state.get_token():
        actions.append(("Sign in",
                        "skillslab login"))
        return actions
    if not meta:
        actions.append(("Pick a course",
                        f"skillslab courses && skillslab start {slug or '<slug>'}"))
        return actions
    if not step:
        actions.append(("Course complete 🎉",
                        f"skillslab courses    # see other courses"))
        return actions

    surface = _step_surface(step)
    repo_url = step.get("module_repo_url")
    label = f"M{step.get('module_pos', 1) - 1}.S{step.get('step_pos', 0)}"

    if surface == "web":
        # 2026-04-25 v3 — was emitting just `# Then run: skillslab sync && skillslab next`
        # with NO URL — the learner had nothing to actually click. User caught
        # this live: "Link missing". Now emit the dashboard URL as the primary
        # action (Rich [link=...] markup → clickable on modern terminals) and
        # the sync/next as a secondary follow-up.
        # 2026-04-25 v4 — CLI-walk v4 caught this branch was building the URL
        # from course_id ALONE, bypassing _browser_url(course_id, step) which
        # is the canonical site for the 3-part deeplink. Result: clicking the
        # CTA after `skillslab next` on a web step lands on a stale cursor
        # instead of the actual current step (regression of the v3 live bug).
        # Single URL-emission helper now wins: route ALL CTA URL builds
        # through _browser_url() so module_id+step_pos precision flows.
        course_id = (meta or {}).get("course_id") or ""
        if course_id:
            url = _browser_url(course_id, step)
            actions.append(("Open in browser (Cmd/Ctrl-click)",
                            f"[link={url}]{url}[/link]"))
        actions.append(("After completing in the browser",
                        f"skillslab sync && skillslab next"))
        return actions

    # Terminal-native step. Three sub-paths depending on (a) whether the
    # module has a repo, (b) whether cwd is inside that repo's clone.
    # User-filed (2026-04-25): the previous catch-all branch told learners
    # to "Edit work files in /work" for EVERY terminal_exercise without a
    # module repo — but smoke-tests / BYO-key setup / preflight steps
    # don't have files to edit. The flow is: read briefing → run shell
    # commands → paste output. Differentiating now.
    if repo_url:
        if _cwd_is_clone_of(repo_url):
            # Already inside the clone — straight to work
            actions.append(("Read briefing",   f"skillslab spec"))
            actions.append(("Edit code",       f"# claude  /  aider --model openrouter/moonshotai/kimi-k2  /  vim ..."))
            actions.append(("Test locally",    f"# pytest -q   /   mvn -q test   /   ./gradlew test"))
            actions.append(("Grade + advance", f"skillslab check"))
        else:
            # Need to clone first
            actions.append(("Clone the module repo",
                            f"skillslab clone --fork    # forks to your account, clones to /work/<repo>"))
            actions.append(("Or just clone (no push)",
                            f"skillslab clone           # read-only practice"))
    else:
        # No module repo. Decide between:
        #   (a) pure concept / browser-companion → just read + advance
        #   (b) terminal_exercise: skillslab check auto-runs cli_commands +
        #       submits captured output. NO PASTE language.
        #   (c) terminal_exercise with a `code` field (editable scratchpad)
        if step.get("exercise_type") in (None, "concept"):
            actions.append(("Read briefing", f"skillslab spec"))
            actions.append(("Advance",       f"skillslab next"))
        elif step.get("code"):
            # Scratchpad-style: starter snippet shipped in the step itself
            actions.append(("Read briefing", f"skillslab spec"))
            actions.append(("Edit the snippet (printed in spec) + run locally", f"# vim / save your version"))
            actions.append(("Grade",         f"skillslab check"))
        else:
            # Terminal-first (2026-04-25 v3): the CLI auto-runs declared
            # cli_commands + submits captured output. No paste language.
            actions.append(("Read briefing", f"skillslab spec"))
            actions.append(("Run + grade (CLI auto-runs the declared commands)",
                            f"skillslab check"))

    # 2026-04-25 v4 P2 fix — caller-aware pruning. Drop any action whose
    # primary command verb is the SAME as the calling command. After
    # `skillslab spec` finishes, advertising "Read briefing  skillslab spec"
    # as the next action is wasted ink. After `skillslab next` advances
    # the cursor, advertising "Advance  skillslab next" is the same.
    # Pruning promotes the next-best action to primary.
    if caller and actions:
        caller_token = f"skillslab {caller}"
        actions = [(v, c) for (v, c) in actions
                   if not c.strip().startswith(caller_token)]
    return actions


def _print_next_actions(actions: list[tuple[str, str]]) -> None:
    """Render the (verb, command) list as a HIGHLIGHTED 'Next' panel.

    The first action is the primary CTA — bold + cyan + boxed. Secondary
    actions follow as dimmer hints. Pattern matches `_print_web_pointer`'s
    panel treatment so learners learn one visual vocabulary: a panel ALWAYS
    means "this is what to do now."

    User-filed (2026-04-25): "skillslab spec being the next step should be
    more highlighted". The previous flat indent + dim text version blended
    into the rest of the output and learners ran blind.
    """
    if not actions:
        return
    # Primary action: boxed panel with bold command (cannot be missed).
    # 2026-04-25 v3 — explicit `$ ` prompt prefix in front of the primary
    # command so it visually reads "type this at your shell prompt." Plus
    # secondary actions render command-FIRST so the typeable command is the
    # leftmost token on each row (was verb-first → command buried).
    # User-filed: "make skillslab spec more clear as the next line user
    # should type."
    primary_verb, primary_cmd = actions[0]
    is_typeable = (
        not primary_cmd.startswith("#")
        and not primary_cmd.startswith("[link=")
        and not primary_cmd.startswith("http")
    )
    if is_typeable:
        body_lines = [f"[dim]$[/dim] [bold cyan]{primary_cmd}[/bold cyan]"]
    else:
        body_lines = [f"[bold cyan]{primary_cmd}[/bold cyan]"]
    if len(actions) > 1:
        body_lines.append("")
        body_lines.append("[dim]then:[/dim]")
        for verb, cmd in actions[1:]:
            cmd_typeable = (
                not cmd.startswith("#")
                and not cmd.startswith("[link=")
                and not cmd.startswith("http")
            )
            if cmd_typeable:
                # COMMAND first (left-aligned), description in dim parens to the right
                body_lines.append(f"  [cyan]{cmd}[/cyan]  [dim]— {verb}[/dim]")
            else:
                # Non-typeable hint (URL or shell-comment) — verb first
                body_lines.append(f"  [cyan]{verb}[/cyan]   [dim]{cmd}[/dim]")
    console.print()
    console.print(Panel(
        "\n".join(body_lines),
        title=f"▶ Next: {primary_verb}",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def _browser_url(course_id: str, step: dict) -> str:
    """Build the dashboard deeplink for a step.

    Frontend hash-router (frontend/index.html:parseHash) accepts:
        #<courseId>                                  — open at last cursor
        #<courseId>/<moduleId>                       — open at module first step
        #<courseId>/<moduleId>/<stepIdx>             — open AT this step (0-indexed)

    2026-04-25 v3 — User caught a live bug: clicking the printed URL while
    on Kimi M1.S1 ("Why context is oxygen…") landed them on M0.S1 ("What
    this course IS…") because we only emitted `#<courseId>`, and the
    frontend restored from a stale cursor. Now we build the 3-part form
    when we have module_id + step_pos in the cursor entry. Falls back to
    the 1-part form for legacy state where module_id wasn't captured.

    Uses state.web_url() (NOT api_url()) because `host.docker.internal` only
    resolves inside the container; the learner's host browser needs
    `localhost:8001` (dev) or the prod FQDN.
    """
    base = state.web_url().rstrip("/")
    module_id = step.get("module_id")
    step_pos = step.get("step_pos")
    if module_id is not None and step_pos is not None:
        return f"{base}/#{course_id}/{module_id}/{step_pos}"
    if module_id is not None:
        return f"{base}/#{course_id}/{module_id}"
    return f"{base}/#{course_id}"


def _print_web_pointer(step: dict, course_id: str, action_verb: str = "see") -> None:
    """Render the cross-surface pointer panel for a `web` step. The CLI
    can't render or grade browser widgets — print a clean clickable URL +
    instructions. Per Opus's headless-context note, we do NOT call
    webbrowser.open (silently fails in Codespaces / SSH / Docker).

    2026-04-25 v3 — URL is wrapped in Rich's [link=URL] markup, which emits
    OSC 8 escape sequences. Modern terminals (iTerm2, macOS Terminal,
    VSCode terminal, GNOME Terminal, Windows Terminal) render that as a
    clickable link. Older terminals fall back to plain text — same UX as
    before, never worse.
    """
    url = _browser_url(course_id, step)
    label = f"M{step.get('module_pos', 1) - 1}.S{step.get('step_pos', 0)}"
    console.print()
    console.print(Panel(
        f"This step is a [bold]browser-native widget[/bold] "
        f"([yellow]{step.get('exercise_type','?')}[/yellow]) — "
        f"the CLI can't {action_verb} it from the terminal.\n\n"
        f"Open in your browser ([dim]Cmd/Ctrl-click to open[/dim]):\n"
        f"  [bold cyan][link={url}]{url}[/link][/bold cyan]\n\n"
        f"Navigate to [bold]{label} — {step.get('title','')[:60]}[/bold] in the dashboard.\n"
        f"When you finish, run [bold]skillslab progress[/bold] to refresh, "
        f"then [bold]skillslab next[/bold] to advance to the next step.",
        title=f"WEB step  ·  {label}", border_style="magenta", box=box.ROUNDED,
    ))


@cli.command()
@click.option("--course", default=None, help="Course slug (defaults to most-recent)")
@click.pass_context
def status(ctx, course):
    """Show current step + progress."""
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta, cur, step = _load_cursor(slug)
    total = len(meta.get("steps", []))
    # Surface-aware progress summary: count terminal vs web steps so the
    # learner knows how many CLI-vs-browser hops the course has.
    surfaces = [_step_surface(s) for s in meta.get("steps", [])]
    n_terminal = surfaces.count("terminal")
    n_web = surfaces.count("web")
    surface_breakdown = ""
    if n_terminal and n_web:
        surface_breakdown = f"\nsurfaces: [bold]{n_terminal}[/bold] terminal · [bold]{n_web}[/bold] web"
    # Cross-surface staleness signal — has the browser advanced beyond the
    # CLI's view since the last `skillslab progress` sync? Compare server's
    # last_activity_at (set by `progress` command) against meta's local
    # `last_active_at` (set by `next` / `goto` / passing `check`).
    stale_banner = ""
    server_la = meta.get("server_last_activity_at") or ""
    cli_la = meta.get("last_active_at") or ""
    if server_la and cli_la and server_la > cli_la:
        stale_banner = (
            f"\n[yellow]⚠ Server activity at {server_la} is newer than the CLI's "
            f"({cli_la}) — run [bold]skillslab progress[/bold] to refresh.[/yellow]"
        )
    console.print(Panel(
        f"[bold]{meta.get('course_title','')}[/bold]\n"
        f"slug: [cyan]{slug}[/cyan]    course_id: [dim]{meta.get('course_id','')}[/dim]\n"
        f"cursor: step [bold]{cur + 1}[/bold] of {total}{surface_breakdown}{stale_banner}",
        border_style="cyan", box=box.ROUNDED,
    ))
    if step:
        m_pos = step.get("module_pos", 0)
        s_pos = step.get("step_pos", 0)
        label = f"M{m_pos - 1}.S{s_pos}"
        surface = _step_surface(step)
        console.print(f"\n▸ [bold cyan]{label}[/bold cyan] — {step.get('title','')}")
        console.print(f"  type: [yellow]{step.get('exercise_type')}[/yellow]    "
                      f"surface: [{'magenta' if surface == 'web' else 'green'}]{surface.upper()}[/]")
        # Module-repo context (same data the browser banner shows). Captured
        # at start time + cached in meta.json's per-step entries.
        if step.get("module_repo_url"):
            ref = step.get("module_repo_ref")
            ref_str = f"  (branch: [yellow]{ref}[/yellow])" if ref else ""
            console.print(f"  📦 module repo: [cyan]{step['module_repo_url']}[/cyan]{ref_str}")
        console.print(f"  file: [dim]{state.course_dir(slug) / 'steps' / step.get('filename','')}[/dim]")
        if surface == "web":
            _print_web_pointer(step, meta.get("course_id", ""), action_verb="render")
        else:
            # 2026-04-25 v2 — was two `[dim]` lines; CLI-walk v1 caught
            # this as the most-run command's CTA still being flat text
            # while next/now/spec got Panel highlighting. Same Panel
            # treatment here for visual consistency — every "what's next"
            # surfaces in a green-bordered Panel.
            actions = _next_action(slug, meta, step, caller="status")
            _print_next_actions(actions)


@cli.command()
@click.option("--course", default=None)
@click.option("--no-pager", is_flag=True, help="Print as raw markdown (don't rich-render)")
@click.pass_context
def spec(ctx, course, no_pager):
    """Print the current step's briefing (markdown).

    For browser-native steps (categorization / drag-drop / simulators), the
    full briefing is rendered in the dashboard's widget — the CLI prints a
    short summary + the dashboard URL.
    """
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta, cur, step = _load_cursor(slug)
    surface = _step_surface(step)
    p = state.course_dir(slug) / "steps" / step.get("filename", "")
    if not p.exists():
        console.print(f"[red]Step file missing: {p}[/red]")
        sys.exit(2)
    md = p.read_text()

    # Strip YAML frontmatter from the visible render. User-filed (2026-04-25):
    # the frontmatter was being printed as plain prose ("step_id: 85163
    # exercise_type: terminal_exercise title: ..." all on one wrapped line)
    # which looked like a parser error. The structured metadata is still in
    # the file (so other tools can re-parse it), but for human reading we
    # surface a tidy header from `step` instead.
    md_body = _strip_frontmatter(md)

    # Build the styled header (replaces the YAML wall of escapes).
    m_pos = step.get("module_pos", 0)
    s_pos = step.get("step_pos", 0)
    label = f"M{m_pos - 1}.S{s_pos}"
    repo_url = step.get("module_repo_url")
    repo_ref = step.get("module_repo_ref")
    header_lines = [
        f"[bold cyan]{label}[/bold cyan] — [bold]{step.get('title','')}[/bold]",
        f"[dim]module:[/dim] {step.get('module_title','')}    "
        f"[dim]type:[/dim] [yellow]{step.get('exercise_type','concept')}[/yellow]    "
        f"[dim]step id:[/dim] [cyan]{step.get('id')}[/cyan]",
    ]
    if repo_url:
        ref_str = f"  (branch: [yellow]{repo_ref}[/yellow])" if repo_ref else ""
        header_lines.append(
            f"[dim]📦 Module repo:[/dim] [cyan]{repo_url}[/cyan]{ref_str}\n"
            f"[dim]Clone:[/dim]  [bold]git clone {repo_url}.git[/bold]"
        )
    console.print()
    console.print(Panel(
        "\n".join(header_lines),
        border_style="cyan", box=box.ROUNDED, padding=(0, 1),
    ))

    if surface == "web":
        # For web steps, only show first heading + first paragraph (the
        # full widget renders in the browser). Skip the full markdown dump.
        body_lines = []
        body_paragraphs = 0
        for line in md_body.splitlines():
            body_lines.append(line)
            if line.strip() == "" and any(l.strip() for l in body_lines[:-1]):
                body_paragraphs += 1
                if body_paragraphs >= 2:
                    break
        summary = "\n".join(body_lines).strip()
        if no_pager:
            click.echo(summary)
        else:
            console.print(Markdown(summary))
        _print_web_pointer(step, meta.get("course_id", ""), action_verb="render")
        return

    # Terminal step: render full briefing (frontmatter already stripped).
    if no_pager:
        click.echo(md_body)
    else:
        console.print(Markdown(md_body))

    # Always end with the next-action hint so learners know what's coming.
    # caller="spec" prunes "Read briefing → skillslab spec" since they JUST
    # did spec — promotes the actual next step (`check`) to primary.
    actions = _next_action(slug, meta, step, caller="spec")
    _print_next_actions(actions)


@cli.command(name="now")
@click.option("--course", default=None)
@click.pass_context
def now_cmd(ctx, course):
    """Show what to do RIGHT NOW — current step + the command to run next.

    \b
    Examples:
      skillslab now                # for the default / most-recent course
      skillslab now --course kimi  # for a specific course

    Useful any time you've been away from the CLI, after a context switch,
    or when you've forgotten which step you're on. Surfaces: where in the
    course, the surface (web/terminal), the module repo, and the next
    command to run, all in one panel.
    """
    # Dev note: User-filed (2026-04-25) — "Add a cli helper command to show
    # next step at all times". CLI-walk v1 caught the previous docstring
    # leaking commit-message-style provenance into Click's --help output;
    # rewrote as user-facing prose with `\b` to preserve the example block.
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta, cur, step = _load_cursor(slug)
    total = len(meta.get("steps", []))
    label = f"M{step.get('module_pos', 1) - 1}.S{step.get('step_pos', 0)}" if step else "—"
    surface = _step_surface(step) if step else "?"
    surface_color = "magenta" if surface == "web" else "green"
    title_line = (
        f"[bold]{meta.get('course_title','')}[/bold]\n"
        f"[dim]cursor:[/dim] step [bold]{cur + 1}[/bold] of {total}    "
        f"[dim]current:[/dim] [bold cyan]{label}[/bold cyan] "
        f"([{surface_color}]{surface.upper()}[/])\n"
        f"[bold]{step.get('title','—')}[/bold]"
    )
    if step.get("module_repo_url"):
        title_line += f"\n[dim]📦 module repo:[/dim] [cyan]{step['module_repo_url']}[/cyan]"
    console.print()
    console.print(Panel(title_line, border_style="cyan", box=box.ROUNDED, padding=(0, 1)))
    # caller="now" — `now` is itself an "answer the question" cmd, so we
    # don't prune `now`, but we still pass the kwarg for symmetry/clarity.
    actions = _next_action(slug, meta, step, caller="now")
    _print_next_actions(actions)


@cli.command(name="next")
@click.option("--course", default=None)
@click.pass_context
def next_cmd(ctx, course):
    """Advance the cursor to the next step (does NOT auto-check)."""
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta = state.read_meta(slug)
    if not meta:
        console.print("[red]No active course state.[/red]"); sys.exit(2)
    cur = int(meta.get("cursor", 0))
    steps = meta.get("steps", [])
    if cur + 1 >= len(steps):
        console.print(f"[yellow]Already on the last step.[/yellow] {len(steps)} steps total.")
        return
    meta["cursor"] = cur + 1
    meta["last_active_at"] = _now_iso()
    state.write_meta(slug, meta)
    s = steps[cur + 1]
    label = f"M{s['module_pos']-1}.S{s['step_pos']}"
    surface = _step_surface(s)
    surface_color = "magenta" if surface == "web" else "green"
    # 2026-04-25 v3 — visual separator so learners can SEE where the next
    # assignment starts in their scrollback. User-filed live walk request:
    # "let's add line breaks where needed... after every skillslab next
    # command, let's add linebreaks and formatting to make it easy to
    # understand where next assignment started".
    console.print()
    console.print(Rule(f"[bold cyan]{label}[/bold cyan] — {s['title']}",
                       style="cyan"))
    console.print()
    console.print(
        f"[dim]surface:[/dim] [{surface_color}]{surface.upper()}[/]    "
        f"[dim]type:[/dim] [yellow]{s.get('exercise_type','concept')}[/yellow]    "
        f"[dim]step id:[/dim] [cyan]{s.get('id') or s.get('step_id')}[/cyan]"
    )
    # 2026-04-25 — replaced the dim-grey hint with a highlighted CTA panel.
    # caller="next" prunes "Advance → skillslab next" (they just advanced).
    actions = _next_action(slug, meta, s, caller="next")
    _print_next_actions(actions)
    console.print()


@cli.command(name="prev")
@click.option("--course", default=None)
@click.pass_context
def prev_cmd(ctx, course):
    """Move the cursor back one step."""
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta = state.read_meta(slug)
    if not meta:
        console.print("[red]No active course state.[/red]"); sys.exit(2)
    cur = int(meta.get("cursor", 0))
    if cur <= 0:
        console.print("[yellow]Already on the first step.[/yellow]")
        return
    meta["cursor"] = cur - 1
    state.write_meta(slug, meta)
    s = meta["steps"][cur - 1]
    console.print(f"[green]←[/green] M{s['module_pos']-1}.S{s['step_pos']} — {s['title']}")


@cli.command()
@click.argument("label")
@click.option("--course", default=None)
@click.pass_context
def goto(ctx, label, course):
    """Jump to a step by label (e.g. M1.S2)."""
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta = state.read_meta(slug)
    if not meta:
        console.print("[red]No active course state.[/red]"); sys.exit(2)
    target = label.strip().upper()
    for i, s in enumerate(meta.get("steps", [])):
        l = f"M{s['module_pos']-1}.S{s['step_pos']}"
        if l == target:
            meta["cursor"] = i
            state.write_meta(slug, meta)
            console.print(f"[green]→[/green] {l} — {s['title']}")
            return
    console.print(f"[red]No step labeled {target}.[/red] Run `skillslab status` to see options.")
    sys.exit(2)


@cli.command()
@click.option("--course", default=None)
@click.option("--fork/--no-fork", default=False,
              help="Fork the upstream repo to your account first (requires gh CLI authed).")
@click.option("--dir", "target_dir", default=None,
              help="Where to clone (default: /work/<repo-name>).")
@click.pass_context
def clone(ctx, course, fork, target_dir):
    """Clone the current module's starter repo into your toolchain workspace.

    Designed to run INSIDE the toolchain container — keeps learners
    immersive without ever exiting to the host. Reads the current
    cursor's `module_repo_url` (cached at `start` time), optionally
    forks via `gh` CLI, clones into `/work/<repo-name>`, then prints
    the cd command to enter it.

    With --fork: requires `gh` (GitHub CLI) on PATH and `gh auth status`
    showing logged-in. Forks the upstream to your account, clones THAT,
    and sets the upstream remote so `git pull` against the original
    branch still works.

    Without --fork: clones the upstream directly (read-only practice).
    For capstone steps that ask you to PUSH back, use --fork.
    """
    import shutil, subprocess, os
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta, cur, step = _load_cursor(slug)
    repo_url = step.get("module_repo_url")
    repo_ref = step.get("module_repo_ref")
    if not repo_url:
        console.print("[yellow]Current module has no discoverable starter repo.[/yellow]")
        console.print("[dim]Run `skillslab status` — module_repo line is shown if any.[/dim]")
        sys.exit(1)

    # Derive repo name from URL: tusharbisht/kimi-eng-course-repo → kimi-eng-course-repo
    repo_name = repo_url.rstrip("/").rstrip(".git").rsplit("/", 1)[-1]
    dest = Path(target_dir) if target_dir else Path("/work") / repo_name
    if dest.exists():
        console.print(f"[yellow]{dest}[/yellow] already exists — skipping clone.")
        console.print(f"  cd {dest}")
        return

    if fork:
        if not shutil.which("gh"):
            console.print("[red]`gh` CLI not on PATH.[/red] Install gh inside the container "
                          "(it ships with the latest skillslab image — rebuild via "
                          "`docker compose build`).")
            sys.exit(1)
        # Verify auth
        rc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if rc.returncode != 0:
            console.print("[red]`gh` not authenticated.[/red] Run `gh auth login` "
                          "(or set GITHUB_TOKEN env) before --fork.")
            sys.exit(1)
        console.print(f"[cyan]Forking[/cyan] {repo_url} to your account…")
        # gh repo fork accepts the upstream URL; --clone clones the fork
        gh_args = ["gh", "repo", "fork", repo_url, "--clone", "--remote", "--default-branch-only=false"]
        if str(dest) != str(Path.cwd() / repo_name):
            # gh fork doesn't take an explicit dest; clone to cwd then move
            tmp_parent = dest.parent
            tmp_parent.mkdir(parents=True, exist_ok=True)
            os.chdir(tmp_parent)
        r = subprocess.run(gh_args, text=True)
        if r.returncode != 0:
            console.print("[red]Fork failed.[/red] Try forking via the GitHub web UI then "
                          "re-running `skillslab clone` (no --fork).")
            sys.exit(1)
        # gh clones to cwd/<repo-name> by default — that's our `dest`.
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        clone_url = repo_url if repo_url.endswith(".git") else repo_url + ".git"
        r = subprocess.run(["git", "clone", clone_url, str(dest)], text=True)
        if r.returncode != 0:
            console.print(f"[red]git clone failed (rc={r.returncode}).[/red]")
            sys.exit(1)

    # If module specifies a branch, check it out
    if repo_ref:
        console.print(f"[cyan]Checking out branch[/cyan] {repo_ref}…")
        subprocess.run(["git", "-C", str(dest), "fetch", "origin"], text=True)
        subprocess.run(["git", "-C", str(dest), "checkout", repo_ref], text=True)

    console.print(f"\n[green]✓ Ready[/green] at [bold]{dest}[/bold]")
    console.print()
    console.print("[bold]Next:[/bold]")
    console.print(f"  cd {dest}")
    console.print(f"  skillslab spec        # read the briefing")
    console.print(f"  # ...edit code with claude / aider...")
    console.print(f"  skillslab check       # grade + advance")


@cli.command()
@click.option("--course", default=None)
@click.option("--paste", default=None, help="Provide submission text directly (default: read stdin if piped)")
@click.option("--cwd", default=".", help="Working directory for the acceptance command (default: cwd)")
@click.option("--verbose", "-v", is_flag=True,
              help="On failure, show the full submission + grader response + dispatch path.")
@click.pass_context
def check(ctx, course, paste, cwd, verbose):
    """Grade the current step. Native cli_check spec runs locally; rubric-only
    steps fall back to bridge mode (capture stdout/git diff and POST to LMS).
    On pass: marks step complete + advances cursor.

    Use `--verbose` (or set `SKILLSLAB_DEBUG=1`) on failure to inspect:
        - what submission text was sent
        - the acceptance_command exit code (was `aider` actually on PATH?)
        - the raw grader response (so you can iterate from real signal)
    """
    # Env override matches the standard verbose pattern across CLIs
    if os.environ.get("SKILLSLAB_DEBUG") == "1":
        verbose = True
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta, cur, step = _load_cursor(slug)
    cdir = state.course_dir(slug)
    p = cdir / "steps" / step.get("filename", "")
    if not p.exists():
        console.print(f"[red]Step file missing: {p}[/red]"); sys.exit(2)

    # Surface gate: web-native steps grade in the browser; CLI can't
    # validate drag-drop / simulator submissions. Print the dashboard
    # pointer + bail (don't auto-mark, don't advance — let the learner
    # finish in browser, then `skillslab progress` syncs the result).
    if _step_surface(step) == "web":
        _print_web_pointer(step, meta.get("course_id", ""), action_verb="grade")
        console.print("\n[dim]After completing in the browser, run "
                      "[bold]skillslab progress[/bold] to sync, then "
                      "[bold]skillslab next[/bold] to advance.[/dim]")
        return

    # Pull the latest validation spec for this step
    cid = meta.get("course_id")
    # We need fresh cli_check from the API (sources of truth: server)
    # For now we already have step.id; refetch the step's validation
    try:
        modules = api.get_modules_with_steps(cid)
        full_step = None
        for m in modules:
            for s in m.get("steps", []):
                if s.get("id") == step.get("step_id"):
                    full_step = s
                    break
            if full_step:
                break
    except api.ApiError as e:
        console.print(f"[red]API error:[/red] {e}")
        sys.exit(2)

    if full_step is None:
        console.print("[red]Could not refetch step from server.[/red]"); sys.exit(2)

    # Read paste content if learner is piping or passing it
    if paste is None and not sys.stdin.isatty():
        paste = sys.stdin.read()

    result = run_check(full_step, cwd=cwd, paste=paste, console=console)

    if result.get("correct"):
        score = result.get("score") or 1.0
        try:
            api.mark_step_complete(step.get("step_id"), score=int(round(score * 100)) if isinstance(score, float) else score)
            console.print(f"[green]✓ Step complete[/green] — synced to dashboard")
            # Advance
            if cur + 1 < len(meta.get("steps", [])):
                meta["cursor"] = cur + 1
                meta["last_active_at"] = _now_iso()
                state.write_meta(slug, meta)
                nxt = meta["steps"][cur + 1]
                label = f"M{nxt['module_pos']-1}.S{nxt['step_pos']}"
                console.print(f"\n[green]→[/green] [bold cyan]{label}[/bold cyan] — [bold]{nxt['title']}[/bold]")
                # 2026-04-25 v3 — CLI-walk v2 caught: this branch was the
                # last "flat dim CTA" remnant after v2 upgraded next / now /
                # status / spec to Panel. Same one-line fix as P1-5 — the
                # post-pass message is one of the most-rewarded moments
                # (learner just succeeded), so keeping it visually
                # consistent reinforces the loop.
                # caller="check" prunes "Run + grade → skillslab check" —
                # they just passed it; show the NEW step's actions.
                actions = _next_action(slug, meta, nxt, caller="check")
                _print_next_actions(actions)
            else:
                console.print(f"\n[bold green]🎉 Course complete![/bold green]")
        except api.ApiError as e:
            console.print(f"[yellow]Pass detected, but sync failed:[/yellow] {e}")
    else:
        score = result.get("score")
        if isinstance(score, float):
            score = f"{score * 100:.0f}%" if score <= 1 else f"{score:.0f}%"
        console.print(f"\n[red]✗ Not yet[/red] — score: [bold]{score or 'n/a'}[/bold]")
        if result.get("feedback"):
            console.print(Panel(result["feedback"], title="Grader feedback", border_style="yellow"))

        # Debug surface — only shown with -v / --verbose / SKILLSLAB_DEBUG=1.
        # Without this, learners see "0% — re-read the briefing" and have no
        # signal to iterate from. With it, they see exactly what was sent +
        # what the grader saw + which dispatch path produced the verdict.
        dbg = result.get("_debug") or {}
        if verbose and dbg:
            console.print()
            console.print(Panel(
                f"[bold]dispatch path:[/bold] {dbg.get('dispatch','?')}\n"
                f"[bold]acceptance_command exit_code:[/bold] {dbg.get('accept_rc','?')}",
                title="Debug", border_style="dim",
            ))
            sub = dbg.get("submission") or ""
            console.print(Panel(
                sub if sub else "[dim](submission was empty — did you run `git add` "
                                  "/ pipe content with --paste / set acceptance_command "
                                  "in .skillslab.yml?)[/dim]",
                title="Submission sent to grader", border_style="dim",
            ))
            raw = dbg.get("raw_response")
            if raw is not None:
                try:
                    pretty = json.dumps(raw, indent=2, default=str)
                except Exception:
                    pretty = str(raw)
                console.print(Panel(pretty, title="Raw grader response", border_style="dim"))
        elif not verbose:
            console.print("[dim]   re-run with --verbose to see the submission "
                          "+ grader response[/dim]")


def _do_sync(ctx, course):
    """Body shared by `sync` and `progress` commands. Extracted as a helper
    so the two surface names (both used widely in user-facing prompts) can
    share one implementation. 2026-04-25 v3 — user caught a live bug:
    `skillslab progress` was an unknown command despite our pointer panel
    telling learners to run it. Both names now resolve here."""
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta = state.read_meta(slug)
    if not meta:
        console.print("[red]No active course state.[/red]"); sys.exit(2)
    enrolled = api.my_courses()
    mine = next((e for e in enrolled if e["course_id"] == meta.get("course_id")), None)
    if not mine:
        console.print("[yellow]Not enrolled in this course on the server.[/yellow]")
        return
    state.write_progress(slug, mine)
    # Phase 3 (2026-04-25) — record server's last activity into meta so
    # status/spec can surface a "browser advanced beyond your CLI" banner.
    if mine.get("last_activity_at"):
        meta["server_last_activity_at"] = mine["last_activity_at"]
        state.write_meta(slug, meta)
    pct = mine.get("progress_percent") or 0
    console.print(f"[green]✓ Synced[/green] — {pct}% complete on the server")
    if mine.get("last_activity_at"):
        console.print(f"  last activity (any surface): [dim]{mine['last_activity_at']}[/dim]")


@cli.command(name="sync")
@click.option("--course", default=None)
@click.pass_context
def sync_cmd(ctx, course):
    """Sync progress from the LMS (in case you completed steps elsewhere)."""
    _do_sync(ctx, course)


@cli.command(name="progress")
@click.option("--course", default=None)
@click.pass_context
def progress_cmd(ctx, course):
    """Sync progress from the LMS — alias for `sync`. Both names work; the
    user-facing prompts (web-pointer panel, status messages) refer to
    `skillslab progress` because that's the more learner-natural verb."""
    _do_sync(ctx, course)


@cli.command()
@click.option("--course", default=None)
@click.pass_context
def dashboard(ctx, course):
    """Print the URL of the course's web dashboard (open in browser when desired)."""
    slug = course or ctx.obj.get("course") or _resolve_course(None)[0]
    meta = state.read_meta(slug)
    if not meta:
        console.print("[red]No active course state.[/red]"); sys.exit(2)
    cid = meta.get("course_id")
    # 2026-04-25 v2 — was state.api_url() which prints host.docker.internal
    # in dev; learner's browser can't resolve that. CLI-walk v1 caught this
    # exact regression — same bug class as _print_web_pointer's, just in
    # this command. Both must use web_url().
    # 2026-04-25 v3 — wrap URL in Rich [link=...] markup so modern terminals
    # render it as Cmd/Ctrl-clickable. User-filed live walk request.
    # 2026-04-25 v5 — route through _browser_url() so this site doesn't
    # bypass the canonical URL helper. dashboard is course-level (no
    # specific step in scope) so we pass an empty step dict; _browser_url's
    # fallback path emits the 1-part `#<courseId>` form, which is correct
    # for course-landing. CLI-walk v4 invariant II2 caught this bypass.
    url = _browser_url(cid, {})
    console.print(f"  [link={url}]{url}[/link]   [dim](Cmd/Ctrl-click to open)[/dim]")


# ── Entry points ───────────────────────────────────────────────────────────

def _now_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def main():
    cli(obj={})


def _wrapper_kimi():
    sys.argv.insert(1, "--course")
    sys.argv.insert(2, "kimi")
    main()


def _wrapper_aie():
    """Deprecated wrapper kept for back-compat with anyone who installed
    `aie-course` as their alias. Auto-canonicalizes to claude-code.
    """
    sys.argv.insert(1, "--course")
    sys.argv.insert(2, "claude-code")
    main()


def _wrapper_claude_code():
    sys.argv.insert(1, "--course")
    sys.argv.insert(2, "claude-code")
    main()


def _wrapper_jspring():
    sys.argv.insert(1, "--course")
    sys.argv.insert(2, "jspring")
    main()


if __name__ == "__main__":
    main()
