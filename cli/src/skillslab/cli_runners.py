"""Terminal-first grading primitives.

Two runners that turn the CLI from a paste-forwarder into a first-class
grading surface — no copy-paste round-trip through the browser.

User directive (2026-04-25, verbatim):
    "Paste output does not make sense in terminal, no?"
    "For GHA flow, cli should be triggered with github push -
     not something unreal."

Both runners CAPTURE the artifact the LMS validator already grades
(plain text for cli_commands; a GHA run URL for gha_workflow_check) and
hand it to the existing bridge_validate path. The backend grading model
doesn't change — only the surface that produces the artifact does.

Architecture:

    validation field present     →  runner                       →  artifact
    ───────────────────────────────────────────────────────────────────────
    .cli_commands: [{cmd,...}]   →  run_cli_commands             →  combined stdout/stderr text
    .gha_workflow_check: {...}   →  run_gha_push_and_watch       →  https://.../actions/runs/<id> URL
    (legacy: must_contain only)  →  paste prompt                 →  free-form learner paste

Both runners produce a string the existing `_bridge_validate` POSTs to
`/api/exercises/validate`. Per-command pass/fail (cli_commands) and
push/watch progress (gha) display inline via the Rich console.

Why two runners and not one:
- cli_commands: deterministic shell capture, no network beyond the LMS
  round-trip at submit time. Fast (<2s/cmd), no auth needed.
- gha_workflow_check: requires `gh auth status` + `git push` permission +
  polling GitHub's API. Slower (typically 30s-5min for a workflow run).
  Different failure modes (auth, push-rejected, workflow-not-found).
  Different progress UX (push spinner → poll for run → watch logs).
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

# Rich is already a dep via cli.py; we accept a Console arg so callers
# (including tests) can pass a mock or capture output.


# ─── cli_commands runner ───────────────────────────────────────────────────

@dataclass
class CliCmdResult:
    """One executed cli_commands entry.

    2026-04-25 v3 — `expected_pattern` / `expected_match` removed. User
    directive: "Regex is a bad way to check here." Tool output format
    varies (e.g. `aider 0.86` vs `Aider v0.86`); LLM-emitted regexes are
    brittle. The LMS rubric + must_contain grade the captured TEXT — the
    CLI's job is to RUN the commands and capture, not predict output
    shape. Exit code is the only deterministic CLI-side signal.
    """
    cmd: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_s: float = 0.0


@dataclass
class CliCmdsRunSummary:
    """Aggregate result of running all cli_commands for a step."""
    results: list[CliCmdResult] = field(default_factory=list)
    all_passed: bool = True            # all `expect` patterns matched (or no expect set)
    captured_text: str = ""            # combined output, formatted for grader submission
    aborted_by_user: bool = False


def run_cli_commands(
    commands: list[dict],
    *,
    cwd: str = ".",
    console: Any = None,
    auto_confirm: bool = False,
    timeout_per_cmd: int = 120,
) -> CliCmdsRunSummary:
    """Run a list of declarative `cli_commands` and capture combined output.

    Each entry in `commands`:
      {
        "cmd": "aider --version",                         # required
        "label": "Aider version smoke",                   # optional, used as section header
        "timeout_s": 30,                                  # optional, default 120
        "ok_exit_codes": [0],                             # optional, default [0]
      }

    2026-04-25 v3 — `expect` regex retired. User directive: "Regex is a
    bad way to check here." The cmd's exit code is the only hard CLI-side
    signal; semantic grading (did the OUTPUT prove the skill?) happens on
    the LMS side via validation.must_contain (substring) + validation.rubric
    (LLM-graded). Tool output format varies — `aider 0.86` vs `Aider v0.86`
    — and predicting it with regex is fragile. The runner now reads only
    cmd / label / timeout_s / ok_exit_codes. If `expect` is present in
    legacy data, it's silently ignored.

    UX (per user directive — preview/confirm, never paste):
      - For each cmd: print `▶ Running: <cmd>` BEFORE running.
      - Show captured output beneath (collapsed if long).
      - Inline ✓/✗ per-cmd result based ONLY on `ok_exit_codes`.
      - At the end, summary + "Submit captured output for grading? [Y/n]"
        unless `auto_confirm=True` (used by --yes flag and tests).

    Returns: CliCmdsRunSummary with the artifact ready for grader submission.
    """
    summary = CliCmdsRunSummary()
    if not commands:
        return summary

    # Defensive: accept str-only entries for back-compat with sloppy Creator
    # output. Wrap in {"cmd": <str>} so the rest of the runner is uniform.
    normalized: list[dict] = []
    for c in commands:
        if isinstance(c, str):
            normalized.append({"cmd": c})
        elif isinstance(c, dict) and c.get("cmd"):
            normalized.append(c)
        # else: silently drop malformed entries (Creator bug, surfaces as 0 cmds)

    # 2026-04-26 — pre-flight env check (per beginner-walk v6 nit #2).
    # Some tools hang for the full timeout when their auth env var is
    # missing (aider waited 120s before erroring; user thought the run
    # was stuck). Detect the common cases up front and fast-fail with
    # a helpful pointer instead of letting a learner stare at silence.
    #
    # Map: regex over `cmd` text → list of env vars that MUST be set.
    # New tools: add the regex + var here; the loop below picks them up.
    import re as _re
    _ENV_REQS: list[tuple[_re.Pattern, tuple[str, ...], str]] = [
        # aider routes through OpenRouter via litellm — needs OPENROUTER_API_KEY
        # (per backend/tech_docs/aider.md line 80). aider hangs ~120s on a
        # missing key before erroring; warn upfront.
        (_re.compile(r"\baider\b"), ("OPENROUTER_API_KEY",),
         "Get a key at https://openrouter.ai/keys, then "
         "`export OPENROUTER_API_KEY=...` and re-run."),
        # claude CLI uses ANTHROPIC_API_KEY OR `claude /login`. Don't fast-fail
        # if key is missing — the user might be using /login auth which lives
        # in ~/.claude/auth.json (bind-mounted). Only warn, don't block.
        # (Intentionally NOT in this list as a hard requirement.)
    ]
    if console:
        for c in normalized:
            cmd = c["cmd"]
            for pat, vars_required, hint in _ENV_REQS:
                if pat.search(cmd):
                    missing = [v for v in vars_required if not os.environ.get(v)]
                    if missing:
                        console.print(
                            f"[bold yellow]⚠ Missing env var{'s' if len(missing)>1 else ''}:[/bold yellow] "
                            f"[yellow]{', '.join(missing)}[/yellow]"
                        )
                        console.print(f"[dim]  Command will likely hang or fail: {cmd[:80]}{'...' if len(cmd) > 80 else ''}[/dim]")
                        console.print(f"[dim]  {hint}[/dim]")
                        console.print()

    if console:
        # 2026-04-27 — replaced the bold-cyan one-liner with a section_rule
        # so the boundary is visible in scrollback (and OSC-marked for iTerm
        # users — cmd-shift-↑ jumps between rules).
        from .rules import section_rule
        section_rule(
            console,
            f"Running {len(normalized)} command{'s' if len(normalized)!=1 else ''} from validation.cli_commands",
            mark=True,
        )
        console.print(f"[dim]Working directory: {cwd}[/dim]")
        console.print()

    chunks: list[str] = []
    for i, c in enumerate(normalized, 1):
        cmd = c["cmd"]
        label = c.get("label") or f"Command {i}"
        ok_codes = set(c.get("ok_exit_codes") or [0])
        timeout = int(c.get("timeout_s") or timeout_per_cmd)
        # `expect` field on legacy data is silently ignored (see docstring).

        if console:
            console.print(f"[bold]{i}/{len(normalized)}[/bold]  [cyan]{label}[/cyan]")
            console.print(f"  [dim]$ {cmd}[/dim]")

        t0 = time.time()
        try:
            r = subprocess.run(
                cmd, cwd=cwd, shell=True, text=True,
                capture_output=True, timeout=timeout,
            )
            stdout = r.stdout or ""
            stderr = r.stderr or ""
            exit_code = r.returncode
        except subprocess.TimeoutExpired:
            stdout, stderr, exit_code = "", f"[skillslab] timed out after {timeout}s", 124
        except Exception as e:
            stdout, stderr, exit_code = "", f"[skillslab] failed to launch: {e}", 127
        elapsed = time.time() - t0

        combined = stdout + ("\n" + stderr if stderr else "")
        cmd_passed = exit_code in ok_codes

        if console:
            tail = combined.strip()
            if tail:
                lines = tail.splitlines()
                shown = "\n  ".join(lines[:8])
                console.print(f"  {shown}")
                if len(lines) > 8:
                    console.print(f"  [dim]... ({len(lines) - 8} more lines captured)[/dim]")
            mark = "[green]✓[/green]" if cmd_passed else "[red]✗[/red]"
            console.print(f"  {mark} [dim](exit={exit_code}, {elapsed:.1f}s)[/dim]")
            console.print()

        if not cmd_passed:
            summary.all_passed = False

        summary.results.append(CliCmdResult(
            cmd=cmd, stdout=stdout, stderr=stderr,
            exit_code=exit_code, duration_s=elapsed,
        ))
        chunks.append(
            f"--- ${cmd} (exit={exit_code}) ---\n"
            f"{combined.rstrip()}\n"
        )

    summary.captured_text = "\n".join(chunks).strip()

    if console:
        passed = sum(1 for r in summary.results if r.exit_code == 0)
        total = len(summary.results)
        # 2026-04-27 — section_rule before the summary so the run/summary
        # boundary is visible in scrollback.
        from .rules import section_rule
        section_rule(console, f"Run summary — {passed}/{total} commands passed")
        line = f"[bold]Summary:[/bold] {passed}/{total} commands ran successfully"
        if summary.all_passed:
            console.print(f"[green]{line} ✓[/green]")
        else:
            console.print(f"[yellow]{line} — some commands had non-zero exit; submission will reflect that[/yellow]")
        console.print(f"[dim]Semantic grading happens on the LMS side via the rubric; the captured output above is what gets submitted.[/dim]")
        console.print()

    if not auto_confirm and console:
        # Prompt for confirmation. Default Yes — most learners just want to ship
        # the captured output. Decline lets them re-run before submitting.
        #
        # 2026-04-26 fix: EOF on piped stdin (`echo y | docker run -i ...
        # skillslab check`, headless CI) was treated as "n" → silently
        # cancelled the submission even when the caller explicitly piped
        # `y`. Per the [Y/n] convention, uppercase = default = yes; EOF
        # without input means "use default" = yes. KeyboardInterrupt is
        # explicit user-cancel and stays as decline.
        try:
            ans = console.input("[bold]Submit captured output for grading?[/bold] [Y/n]: ").strip().lower()
        except EOFError:
            ans = ""  # honor the default (yes)
        except KeyboardInterrupt:
            ans = "n"
        if ans and ans not in ("y", "yes", ""):
            summary.aborted_by_user = True

    return summary


# ─── GHA push-and-watch runner ─────────────────────────────────────────────

@dataclass
class GhaRunSummary:
    """Result of run_gha_push_and_watch."""
    ok: bool = False
    run_url: str | None = None
    conclusion: str | None = None  # success / failure / cancelled / etc.
    error: str | None = None       # populated when ok=False with a beginner-readable msg
    pushed_sha: str | None = None
    pushed_branch: str | None = None


def _git(args: list[str], cwd: str) -> tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, exit_code)."""
    try:
        r = subprocess.run(
            ["git"] + args, cwd=cwd, text=True,
            capture_output=True, timeout=60,
        )
        return r.stdout or "", r.stderr or "", r.returncode
    except subprocess.TimeoutExpired:
        return "", "git timed out", 124
    except FileNotFoundError:
        return "", "git not on PATH", 127


def _gh(args: list[str], cwd: str = ".", timeout: int = 30) -> tuple[str, str, int]:
    """Run a `gh` (GitHub CLI) command. Returns (stdout, stderr, exit_code)."""
    try:
        r = subprocess.run(
            ["gh"] + args, cwd=cwd, text=True,
            capture_output=True, timeout=timeout,
        )
        return r.stdout or "", r.stderr or "", r.returncode
    except subprocess.TimeoutExpired:
        return "", "gh timed out", 124
    except FileNotFoundError:
        return "", "gh not on PATH (install GitHub CLI in the container)", 127


def run_gha_push_and_watch(
    spec: dict,
    *,
    cwd: str = ".",
    console: Any = None,
    poll_interval_s: int = 5,
    poll_max_s: int = 600,
) -> GhaRunSummary:
    """The terminal-native capstone flow: push current branch, find the GHA
    run for the pushed SHA, watch it to completion, return the run URL.

    `spec` is the step's `validation.gha_workflow_check`:
      {
        "repo_template": "https://github.com/<org>/<slug>",   # informational
        "workflow_file": "lab-grade.yml",                     # informational
        "expected_conclusion": "success",                     # informational
        "grading_job": "grade",                               # informational
      }

    None of the spec fields gate this runner — they're informational so the
    learner sees what's expected. The actual grading happens server-side
    (the existing _check_gha or backend gha_workflow_check call) once the
    run URL is captured here and submitted.

    Returns: GhaRunSummary. On `ok=True`, `run_url` is the artifact to
    submit. On `ok=False`, `error` is a beginner-readable next-step
    suggestion (run `gh auth login`, fork first, etc.).

    UX:
      - Each phase prints a clear status line so the learner sees progress
      - Ctrl+C during the watch phase aborts cleanly with a "rerun later" hint
      - All git / gh commands shown verbatim so debugging is transparent
    """
    out = GhaRunSummary()

    if console:
        console.print()
        console.print("[bold cyan]▶ Capstone GHA flow — push & watch[/bold cyan]")
        console.print(f"[dim]cwd: {cwd}[/dim]")

    # ─── Pre-flight: gh authenticated? ───────────────────────────────────
    auth_out, auth_err, auth_rc = _gh(["auth", "status"])
    if auth_rc != 0:
        out.error = (
            "GitHub CLI is not authenticated. Run:\n"
            "    gh auth login\n"
            "and select GitHub.com → HTTPS → paste your token (or use the browser flow).\n"
            f"[gh auth status said: {auth_err.strip()[:200]}]"
        )
        if console:
            console.print(f"[red]✗ {out.error}[/red]")
        return out

    # ─── Pre-flight: cwd is a git clone? ─────────────────────────────────
    so, se, rc = _git(["rev-parse", "--show-toplevel"], cwd)
    if rc != 0:
        out.error = (
            f"Current directory `{cwd}` is not inside a git repository.\n"
            "Fork the capstone repo on GitHub first, then clone YOUR fork:\n"
            "  gh repo fork <upstream-url> --clone\n"
            "  cd <repo-name>\n"
            "Then re-run `skillslab check` from inside the clone."
        )
        if console:
            console.print(f"[red]✗ {out.error}[/red]")
        return out
    repo_root = so.strip()

    # ─── Pre-flight: origin points at user's fork (not upstream)? ────────
    origin_out, _, rc = _git(["config", "--get", "remote.origin.url"], cwd=repo_root)
    if rc != 0:
        out.error = (
            "No `origin` remote configured. Re-clone via `gh repo fork "
            "<upstream-url> --clone` (sets origin to your fork) OR set "
            "origin manually to YOUR fork (not upstream)."
        )
        if console:
            console.print(f"[red]✗ {out.error}[/red]")
        return out
    origin_url = origin_out.strip()

    # Get GH user's login so we can compare with origin URL owner.
    user_out, _, _ = _gh(["api", "user", "-q", ".login"])
    gh_user = user_out.strip()
    m_origin = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", origin_url)
    origin_owner = m_origin.group(1) if m_origin else ""
    origin_repo = m_origin.group(2) if m_origin else ""
    if gh_user and origin_owner and origin_owner.lower() != gh_user.lower():
        # Allow it but warn — some learners legitimately push to a team-owned fork.
        if console:
            console.print(
                f"[yellow]⚠ origin is `{origin_owner}/{origin_repo}` but you're "
                f"signed in as `{gh_user}` — make sure you have push permission.[/yellow]"
            )

    # ─── Branch + commit state ───────────────────────────────────────────
    br_out, _, rc = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    if rc != 0 or not br_out.strip():
        out.error = "Could not determine current branch (detached HEAD?). Check out a branch first."
        if console: console.print(f"[red]✗ {out.error}[/red]")
        return out
    branch = br_out.strip()

    # If working tree is dirty, offer to commit. Per user directive — natural
    # developer flow — but always require explicit consent before mutating
    # the repo.
    dirty_out, _, _ = _git(["status", "--porcelain"], cwd=repo_root)
    if dirty_out.strip():
        if console:
            console.print()
            console.print(f"[yellow]Uncommitted changes detected on `{branch}`:[/yellow]")
            for line in dirty_out.strip().splitlines()[:10]:
                console.print(f"  [dim]{line}[/dim]")
            if len(dirty_out.strip().splitlines()) > 10:
                console.print(f"  [dim]...({len(dirty_out.strip().splitlines()) - 10} more files)[/dim]")
            # Same EOF-vs-Ctrl-C semantics as the cli_commands prompt above:
            # piped stdin / EOF means "use the [Y/n] default = yes"; only
            # explicit Ctrl-C cancels. (2026-04-26)
            try:
                ans = console.input(
                    "[bold]Commit all changes and push?[/bold] [Y/n]: "
                ).strip().lower()
            except EOFError:
                ans = ""  # honor default
            except KeyboardInterrupt:
                ans = "n"
            if ans and ans not in ("y", "yes", ""):
                out.error = "Cancelled — commit your changes manually then re-run `skillslab check`."
                console.print(f"[yellow]{out.error}[/yellow]")
                return out
            try:
                msg = console.input(
                    "[bold]Commit message[/bold] [skillslab capstone submit]: "
                ).strip() or "skillslab capstone submit"
            except (EOFError, KeyboardInterrupt):
                msg = "skillslab capstone submit"
            console.print(f"[dim]$ git add -A && git commit -m {msg!r}[/dim]")
            _, _, rc = _git(["add", "-A"], cwd=repo_root)
            if rc == 0:
                _, ce, rc = _git(["commit", "-m", msg], cwd=repo_root)
                if rc != 0:
                    out.error = f"git commit failed: {ce.strip()[:200]}"
                    console.print(f"[red]✗ {out.error}[/red]")
                    return out

    # ─── Push ────────────────────────────────────────────────────────────
    if console:
        console.print(f"[dim]$ git push origin {branch}[/dim]")
    push_out, push_err, rc = _git(["push", "origin", branch], cwd=repo_root)
    if rc != 0:
        out.error = (
            f"git push failed: {(push_err or push_out).strip()[:300]}\n"
            "If the error mentions `non-fast-forward` or `rejected`, you may need to pull first or push to a new branch."
        )
        if console: console.print(f"[red]✗ {out.error}[/red]")
        return out
    if console:
        console.print(f"[green]✓[/green] pushed [bold]{branch}[/bold] to [cyan]{origin_owner}/{origin_repo}[/cyan]")

    sha_out, _, _ = _git(["rev-parse", "HEAD"], cwd=repo_root)
    pushed_sha = sha_out.strip()
    out.pushed_sha = pushed_sha
    out.pushed_branch = branch

    # ─── Find the run ────────────────────────────────────────────────────
    if console:
        console.print(f"[dim]Waiting for GHA workflow to register run for {pushed_sha[:8]}...[/dim]")

    run_id: str | None = None
    deadline_register = time.time() + 60  # allow 60s for GH to start the workflow
    while time.time() < deadline_register and run_id is None:
        # gh run list returns the most-recent runs on the branch as JSON
        ls_out, ls_err, rc = _gh(
            ["run", "list", "--branch", branch, "--limit", "10",
             "--json", "databaseId,headSha,status,conclusion,url,createdAt"],
            cwd=repo_root, timeout=15,
        )
        if rc != 0:
            time.sleep(poll_interval_s)
            continue
        try:
            import json as _j
            runs = _j.loads(ls_out or "[]")
        except Exception:
            runs = []
        for run in runs:
            if str(run.get("headSha", "")).startswith(pushed_sha[:7]) or run.get("headSha") == pushed_sha:
                run_id = str(run["databaseId"])
                out.run_url = run.get("url")
                break
        if run_id is None:
            time.sleep(poll_interval_s)

    if run_id is None:
        out.error = (
            f"No GHA run found for {pushed_sha[:8]} on branch `{branch}` after 60s.\n"
            "Possible causes: the workflow doesn't exist on this branch, or GHA is delayed.\n"
            "Re-run `skillslab check` in a minute, or open the Actions tab to investigate."
        )
        if console: console.print(f"[red]✗ {out.error}[/red]")
        return out

    if console:
        console.print(f"[green]✓[/green] run found: [cyan]{out.run_url}[/cyan]")
        console.print(f"[dim]Watching to completion (Ctrl+C to background)...[/dim]")

    # ─── Watch ───────────────────────────────────────────────────────────
    deadline_watch = time.time() + poll_max_s
    last_status: str | None = None
    while time.time() < deadline_watch:
        st_out, _, rc = _gh(
            ["run", "view", run_id, "--json", "status,conclusion,url"],
            cwd=repo_root, timeout=15,
        )
        if rc != 0:
            time.sleep(poll_interval_s)
            continue
        try:
            import json as _j
            data = _j.loads(st_out or "{}")
        except Exception:
            data = {}
        status = data.get("status")
        conclusion = data.get("conclusion")
        if status != last_status and console:
            console.print(f"  [dim]· status: {status}[/dim]")
            last_status = status
        if status == "completed":
            out.conclusion = conclusion
            out.run_url = data.get("url") or out.run_url
            out.ok = True
            if console:
                color = "green" if conclusion == "success" else "red"
                console.print(
                    f"[{color}]✓ run completed: conclusion={conclusion}[/{color}]  [dim]{out.run_url}[/dim]"
                )
            return out
        time.sleep(poll_interval_s)

    out.error = (
        f"GHA run is still in progress after {poll_max_s}s. URL: {out.run_url}\n"
        "Re-run `skillslab check` once it's done, or pass --paste <run-url>."
    )
    if console: console.print(f"[yellow]⚠ {out.error}[/yellow]")
    return out
