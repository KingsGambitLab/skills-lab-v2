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
from rich.table import Table

from . import api, state, __version__
from .check import run_check
from .render import step_to_markdown

console = Console()

# ── Utility helpers ────────────────────────────────────────────────────────

def _resolve_course(slug_or_id: str | None) -> tuple[str, str]:
    """Normalize a slug ('kimi', 'aie', 'jspring') OR a course_id ('created-…')
    into (slug, course_id). The mapping is recorded under `~/.skillslab/<slug>/meta.json`
    after the first `start`. For the bootstrap path we also accept course_id directly.
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
@click.option("--course", default=None, help="Course slug (kimi / aie / jspring) — also via per-course wrapper")
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
    ("aie", ["ai-augmented engineering", "claude code + api", "claude code + mcp"]),
    ("jspring", ["spring boot", "java"]),
]

def _slug_for_course_title(title: str) -> str:
    t = (title or "").lower()
    for slug, hints in _SLUG_HINTS:
        if any(h in t for h in hints):
            return slug
    return "—"


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
                "title": s.get("title", ""),
                "exercise_type": s.get("exercise_type") or "concept",
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


def _browser_url(course_id: str, step: dict) -> str:
    """Build the dashboard deeplink for a step. The web frontend's hash
    router accepts `#<courseId>` and the active step is restored from the
    last visited cursor — for a more precise link we'd want a step-id-based
    deep route, but that lives in a separate router change."""
    base = state.api_url().rstrip("/")
    return f"{base}/#{course_id}"


def _print_web_pointer(step: dict, course_id: str, action_verb: str = "see") -> None:
    """Render the cross-surface pointer panel for a `web` step. The CLI
    can't render or grade browser widgets — print a clean copy-paste URL +
    instructions. Per Opus's headless-context note, we do NOT call
    webbrowser.open (silently fails in Codespaces / SSH / Docker)."""
    url = _browser_url(course_id, step)
    label = f"M{step.get('module_pos', 1) - 1}.S{step.get('step_pos', 0)}"
    console.print()
    console.print(Panel(
        f"This step is a [bold]browser-native widget[/bold] "
        f"([yellow]{step.get('exercise_type','?')}[/yellow]) — "
        f"the CLI can't {action_verb} it from the terminal.\n\n"
        f"Open in your browser:\n"
        f"  [bold cyan]{url}[/bold cyan]\n\n"
        f"Navigate to [bold]{label} — {step.get('title','')[:60]}[/bold] in the dashboard.\n"
        f"When you finish, run [bold]skillslab progress[/bold] to refresh, "
        f"then [bold]skillslab next[/bold] to advance to the next terminal step.",
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
            console.print()
            console.print("[dim]skillslab spec     # cat the briefing[/dim]")
            console.print("[dim]skillslab check    # grade your work + advance on pass[/dim]")


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

    if surface == "web":
        # Print the YAML front-matter + first heading + first paragraph
        # of the briefing only, then the browser pointer. The full
        # interactive widget content lives on the web surface — there's
        # no value in dumping the whole markdown here.
        head_lines = []
        in_fm = False
        body_started = False
        body_paragraphs = 0
        for line in md.splitlines():
            if line.startswith("---") and not in_fm:
                in_fm = True
                continue
            if line.startswith("---") and in_fm:
                in_fm = False
                continue
            if in_fm:
                continue
            head_lines.append(line)
            if line.strip() and not line.startswith("#") and not line.startswith("_"):
                body_started = True
            if body_started and line.strip() == "":
                body_paragraphs += 1
                if body_paragraphs >= 2:
                    break
        summary = "\n".join(head_lines).strip()
        if no_pager:
            click.echo(summary)
        else:
            console.print(Markdown(summary))
        _print_web_pointer(step, meta.get("course_id", ""), action_verb="render")
        return

    # Terminal step: render full briefing
    if no_pager:
        click.echo(md)
    else:
        console.print(Markdown(md))


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
    console.print(f"[green]→[/green] M{s['module_pos']-1}.S{s['step_pos']} — {s['title']}")
    console.print("[dim]skillslab spec[/dim]")


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
                console.print(f"\n[bold]Next:[/bold] M{nxt['module_pos']-1}.S{nxt['step_pos']} — {nxt['title']}")
                console.print("[dim]skillslab spec[/dim]")
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


@cli.command(name="sync")
@click.option("--course", default=None)
@click.pass_context
def sync_cmd(ctx, course):
    """Sync progress from the LMS (in case you completed steps elsewhere)."""
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
    url = f"{state.api_url()}/#{cid}"
    console.print(f"  {url}")


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
    sys.argv.insert(1, "--course")
    sys.argv.insert(2, "aie")
    main()


def _wrapper_jspring():
    sys.argv.insert(1, "--course")
    sys.argv.insert(2, "jspring")
    main()


if __name__ == "__main__":
    main()
