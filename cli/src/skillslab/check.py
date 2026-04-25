"""Acceptance checks for the skillslab CLI.

User directive (2026-04-25): *"Evaluations should also run within terminal —
i.e., learner submits the assignment AND sees the result in the terminal;
they don't have to come back to the dashboard."*

The CLI is the single learner-facing surface. Submission + verdict + advance
all happen here. The grading ENGINE behind it can be:

1. **Native cli_check** — `step.validation.cli_check` declares a deterministic
   check the CLI runs locally. Fast, free, no LMS round-trip:

       kind: paste_contains    # all `tokens` must appear in the submission
       kind: command_exit_zero # run `command` in cwd; exit 0 = pass
       kind: file_exists       # check `path` exists in cwd
       kind: pytest            # run `command` (default `pytest -q`); exit 0 = pass
       kind: git_diff_contains # `git diff` (+ optional --staged) must contain `tokens`
       kind: gha_workflow_check  # learner pastes a GH Actions run URL → CLI
                                 # hits the public GitHub API directly
       kind: claude_rubric     # local `claude -p` call (AIE BYO-key path)
       kind: aider_rubric      # local `aider --message` (Kimi BYO-key path)
       kind: local_rubric      # auto-detect claude or aider, whichever is on PATH

2. **LMS bridge (default fallback)** — when there's no `cli_check` but the step
   has a `validation.rubric` or `must_contain`, the CLI captures paste +
   git diff + acceptance-command output, POSTs to `/api/exercises/validate`,
   and renders the verdict back in the terminal. Same grader the browser
   uses; learner never opens the browser.

The course-repo's own `.skillslab.yml` (sitting at cwd) optionally pre-runs
an `acceptance_command` (e.g. `pytest -q && mvn -q test`), captures its
output, and feeds it into the submission. That file is the dev's contract:
"what should `skillslab check` execute on my behalf before grading?"
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from . import api


# ── Local repo contract: .skillslab.yml ────────────────────────────────────

def _read_skillslab_yml(cwd: str) -> dict:
    """Read cwd/.skillslab.yml if present. Returns {} if missing/unreadable.

    Recognized fields (all optional):
      acceptance_command:  shell string; ran in cwd, output captured into paste
      paste_includes:      list of relative paths whose content is appended
      git_diff:            "yes" | "no" | "staged" — capture mode (default yes)
      rubric_model:        override for `claude --model` / `aider --model`
    """
    p = Path(cwd) / ".skillslab.yml"
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {}


def _capture_acceptance(cwd: str, command: str | None) -> tuple[str, int]:
    """Run a shell command in cwd, capture stdout+stderr, return (output, rc).
    Empty/None command → no-op, returns ("", 0).
    """
    if not command or not command.strip():
        return "", 0
    try:
        r = subprocess.run(
            command, cwd=cwd, shell=True, text=True,
            capture_output=True, timeout=300,
        )
        out = (r.stdout or "") + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
        return out, r.returncode
    except subprocess.TimeoutExpired:
        return "[skillslab] acceptance command timed out after 300s\n", 124
    except Exception as e:
        return f"[skillslab] acceptance command failed to launch: {e}\n", 127


def _capture_git_diff(cwd: str, mode: str = "yes") -> str:
    """Capture `git diff` so the rubric grader sees what the learner did.
    mode: "yes" (working tree), "staged" (--staged), "no" (skip).
    """
    if mode == "no":
        return ""
    args = ["git", "diff"]
    if mode == "staged":
        args.append("--staged")
    try:
        r = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=15)
        return r.stdout or ""
    except Exception:
        return ""


def _build_submission(step: dict, cwd: str, paste: str | None) -> tuple[str, int]:
    """Assemble the universal submission text the grader sees.

    Pulls together (in order): the learner's paste/stdin, the
    acceptance-command output, the git diff, plus any include-files
    declared in .skillslab.yml. Returns (submission_text, accept_rc).
    """
    cfg = _read_skillslab_yml(cwd)
    accept_cmd = cfg.get("acceptance_command")
    diff_mode = cfg.get("git_diff", "yes")

    accept_out, accept_rc = _capture_acceptance(cwd, accept_cmd)
    diff = _capture_git_diff(cwd, diff_mode)

    extras = []
    for rel in (cfg.get("paste_includes") or []):
        fp = Path(cwd) / rel
        if fp.exists() and fp.is_file():
            try:
                extras.append(f"--- {rel} ---\n" + fp.read_text())
            except Exception:
                pass

    parts = []
    if paste and paste.strip():
        parts.append(paste.strip())
    if accept_cmd:
        parts.append(f"--- acceptance command: `{accept_cmd}` (exit={accept_rc}) ---\n{accept_out}")
    if diff and diff.strip():
        parts.append(f"--- git diff ---\n{diff}")
    if extras:
        parts.extend(extras)
    return "\n\n".join(parts).strip(), accept_rc


# ── Native cli_check kinds ─────────────────────────────────────────────────

def _check_paste_contains(spec: dict, submission: str) -> dict:
    tokens = spec.get("tokens") or spec.get("must_contain") or []
    missing = [t for t in tokens if t not in submission]
    if missing:
        return {
            "correct": False,
            "score": max(0.0, 1.0 - len(missing) / max(1, len(tokens))),
            "feedback": "Missing tokens in submission: " + ", ".join(f"`{t}`" for t in missing),
        }
    return {"correct": True, "score": 1.0, "feedback": "All required tokens present."}


def _check_command_exit_zero(spec: dict, cwd: str) -> dict:
    cmd = spec.get("command") or ""
    if not cmd:
        return {"correct": False, "score": 0, "feedback": "cli_check.command_exit_zero missing `command`."}
    out, rc = _capture_acceptance(cwd, cmd)
    if rc == 0:
        return {"correct": True, "score": 1.0, "feedback": f"`{cmd}` exited 0.\n{out[-2000:]}"}
    return {"correct": False, "score": 0, "feedback": f"`{cmd}` exited {rc}.\n{out[-2000:]}"}


def _check_file_exists(spec: dict, cwd: str) -> dict:
    rel = spec.get("path") or ""
    p = Path(cwd) / rel
    if p.exists():
        return {"correct": True, "score": 1.0, "feedback": f"`{rel}` exists."}
    return {"correct": False, "score": 0, "feedback": f"`{rel}` does not exist (cwd={cwd})."}


def _check_pytest(spec: dict, cwd: str) -> dict:
    cmd = spec.get("command") or "pytest -q"
    out, rc = _capture_acceptance(cwd, cmd)
    if rc == 0:
        return {"correct": True, "score": 1.0, "feedback": f"Tests passed.\n{out[-2000:]}"}
    return {"correct": False, "score": 0, "feedback": f"Tests failed (rc={rc}).\n{out[-2000:]}"}


def _check_git_diff_contains(spec: dict, cwd: str) -> dict:
    tokens = spec.get("tokens") or []
    mode = spec.get("mode", "yes")
    diff = _capture_git_diff(cwd, mode)
    missing = [t for t in tokens if t not in diff]
    if missing:
        return {
            "correct": False, "score": max(0.0, 1.0 - len(missing) / max(1, len(tokens))),
            "feedback": "Missing in git diff: " + ", ".join(f"`{t}`" for t in missing),
        }
    return {"correct": True, "score": 1.0, "feedback": "All required tokens present in git diff."}


def _check_gha(spec: dict, submission: str) -> dict:
    """Native GitHub-Actions check. The learner pastes a run URL; the CLI
    hits the public GitHub API directly (no LMS round-trip). `GITHUB_TOKEN`
    env var is used for higher rate limits when set.
    """
    url = (submission or "").strip().splitlines()[0] if submission else ""
    m = re.search(r"https://github\.com/([^/]+)/([^/]+)/actions/runs/(\d+)", url)
    if not m:
        return {
            "correct": False, "score": 0,
            "feedback": "Paste a GitHub Actions run URL (https://github.com/<owner>/<repo>/actions/runs/<id>).",
        }
    owner, repo, run_id = m.group(1), m.group(2), m.group(3)
    try:
        import httpx
        headers = {"Accept": "application/vnd.github+json"}
        tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        r = httpx.get(
            f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}",
            headers=headers, timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        conclusion = data.get("conclusion")
        expected = spec.get("expected_conclusion", "success")
        ok = conclusion == expected
        return {
            "correct": ok,
            "score": 1.0 if ok else 0,
            "feedback": (f"GHA run conclusion: {conclusion}. "
                         f"({data.get('html_url','')})"),
        }
    except Exception as e:
        return {"correct": False, "score": 0, "feedback": f"GHA check failed: {e}"}


# ── Local-LLM rubric kinds (claude / aider, BYO-key) ───────────────────────

_RUBRIC_INSTRUCTIONS = """\
You are grading a learner's submission against a rubric.
Output ONLY a single JSON object on a single line, no surrounding prose:
  {"score": <float 0.0-1.0>, "correct": <true|false>, "feedback": "<one paragraph>"}
`correct` should be true when score >= 0.7. Be precise + cite specific lines
from the submission when explaining what's missing or right."""


def _run_claude_rubric(rubric: str, submission: str, model: str | None = None) -> dict:
    if not shutil.which("claude"):
        return {"correct": False, "score": 0,
                "feedback": "`claude` CLI not on PATH. Install it from https://docs.anthropic.com/claude/docs/claude-code."}
    prompt = f"{_RUBRIC_INSTRUCTIONS}\n\nRUBRIC:\n{rubric}\n\nSUBMISSION:\n{submission}\n"
    args = ["claude", "-p", prompt]
    if model:
        args.extend(["--model", model])
    try:
        r = subprocess.run(args, text=True, capture_output=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"correct": False, "score": 0, "feedback": "claude rubric call timed out (180s)."}
    if r.returncode != 0:
        return {"correct": False, "score": 0, "feedback": f"claude exited {r.returncode}.\n{(r.stderr or r.stdout)[-2000:]}"}
    return _parse_rubric_json(r.stdout)


def _run_aider_rubric(rubric: str, submission: str, model: str | None = None) -> dict:
    if not shutil.which("aider"):
        return {"correct": False, "score": 0,
                "feedback": "`aider` CLI not on PATH. Install via `pip install aider-chat`."}
    prompt = f"{_RUBRIC_INSTRUCTIONS}\n\nRUBRIC:\n{rubric}\n\nSUBMISSION:\n{submission}\n"
    args = ["aider", "--no-auto-commits", "--no-pretty", "--no-stream", "--message", prompt]
    if model:
        args.extend(["--model", model])
    try:
        r = subprocess.run(args, text=True, capture_output=True, timeout=180,
                           env={**os.environ, "AIDER_AUTO_LINT": "0"})
    except subprocess.TimeoutExpired:
        return {"correct": False, "score": 0, "feedback": "aider rubric call timed out (180s)."}
    if r.returncode != 0:
        return {"correct": False, "score": 0, "feedback": f"aider exited {r.returncode}.\n{(r.stderr or r.stdout)[-2000:]}"}
    return _parse_rubric_json(r.stdout)


def _parse_rubric_json(text: str) -> dict:
    """Pull the first {…} blob out of the LLM stdout. LLMs sometimes wrap JSON
    in prose; we extract it leniently.
    """
    if not text:
        return {"correct": False, "score": 0, "feedback": "Empty rubric response."}
    try:
        data = json.loads(text.strip())
    except Exception:
        m = re.search(r"\{[^{}]*\"score\"[^{}]*\}", text, re.DOTALL)
        if not m:
            m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return {"correct": False, "score": 0, "feedback": f"Could not parse rubric JSON.\nRaw: {text[:1000]}"}
        try:
            data = json.loads(m.group(0))
        except Exception:
            return {"correct": False, "score": 0, "feedback": f"Could not parse rubric JSON.\nRaw: {text[:1000]}"}
    score = float(data.get("score") or 0)
    correct = bool(data.get("correct") if "correct" in data else (score >= 0.7))
    feedback = data.get("feedback") or ""
    return {"correct": correct, "score": score, "feedback": feedback}


def _local_rubric_dispatch(rubric: str, submission: str, model: str | None) -> dict | None:
    """Pick whichever local LLM CLI is available. Returns None if neither
    `claude` nor `aider` is on PATH (caller should bridge to LMS instead).
    """
    if shutil.which("claude"):
        return _run_claude_rubric(rubric, submission, model)
    if shutil.which("aider"):
        return _run_aider_rubric(rubric, submission, model)
    return None


def _check_claude_rubric(spec: dict, submission: str, cfg: dict) -> dict:
    return _run_claude_rubric(spec.get("rubric") or "", submission,
                               model=spec.get("model") or cfg.get("rubric_model"))


def _check_aider_rubric(spec: dict, submission: str, cfg: dict) -> dict:
    return _run_aider_rubric(spec.get("rubric") or "", submission,
                              model=spec.get("model") or cfg.get("rubric_model"))


def _check_local_rubric(spec: dict, submission: str, cfg: dict) -> dict:
    out = _local_rubric_dispatch(spec.get("rubric") or "", submission,
                                  model=spec.get("model") or cfg.get("rubric_model"))
    if out is None:
        return {"correct": False, "score": 0,
                "feedback": "No local LLM CLI on PATH. Install `claude` or `aider`."}
    return out


_NATIVE_KINDS = {
    "paste_contains":     lambda spec, sub, cwd, cfg: _check_paste_contains(spec, sub),
    "command_exit_zero":  lambda spec, sub, cwd, cfg: _check_command_exit_zero(spec, cwd),
    "file_exists":        lambda spec, sub, cwd, cfg: _check_file_exists(spec, cwd),
    "pytest":             lambda spec, sub, cwd, cfg: _check_pytest(spec, cwd),
    "git_diff_contains":  lambda spec, sub, cwd, cfg: _check_git_diff_contains(spec, cwd),
    "gha_workflow_check": lambda spec, sub, cwd, cfg: _check_gha(spec, sub),
    "claude_rubric":      lambda spec, sub, cwd, cfg: _check_claude_rubric(spec, sub, cfg),
    "aider_rubric":       lambda spec, sub, cwd, cfg: _check_aider_rubric(spec, sub, cfg),
    "local_rubric":       lambda spec, sub, cwd, cfg: _check_local_rubric(spec, sub, cfg),
}


# ── LMS bridge (default fallback) ──────────────────────────────────────────

def _bridge_validate(step: dict, submission: str, accept_rc: int) -> dict:
    """Invisible to the learner — we POST + render the verdict in the
    terminal. The learner runs `skillslab check`, gets a Panel back. They
    don't open the dashboard.
    """
    sid = step.get("id")
    etype = step.get("exercise_type") or "concept"
    payload = {
        "paste_markdown": submission,
        "paste": submission,
        "submission": submission,
        "markdown": submission,
        "acceptance_exit_code": accept_rc,
    }
    try:
        out = api.validate_exercise(sid, etype, payload)
    except api.ApiError as e:
        return {"correct": False, "score": 0, "feedback": f"LMS validate error: {e}",
                "_debug": {"submission": submission, "accept_rc": accept_rc, "error": str(e)}}

    score = out.get("score")
    correct = bool(out.get("correct") or (isinstance(score, (int, float)) and score >= 0.7))
    feedback = out.get("feedback") or out.get("message") or ""
    if not feedback and out.get("explanations"):
        feedback = "\n".join(out["explanations"])
    return {
        "correct": correct,
        "score": score if score is not None else (1.0 if correct else 0.0),
        "feedback": feedback,
        # Stash the full payload + raw grader response so `--verbose` can show
        # learners exactly what was submitted + evaluated. Also includes the
        # _captured_ output of `acceptance_command` so they can see whether
        # (e.g.) `aider` was actually on PATH.
        "_debug": {
            "submission": submission,
            "accept_rc": accept_rc,
            "raw_response": out,
        },
    }


# ── Public entry point ────────────────────────────────────────────────────

def run_check(step: dict, cwd: str = ".", paste: str | None = None, console: Any = None,
              auto_confirm: bool = False) -> dict:
    """Grade a step. Submission + verdict both happen in the terminal — the
    learner never has to switch to the dashboard.

    Dispatch order (terminal-first as of 2026-04-25):
      0a. step.validation.cli_commands present → run them, capture combined
          output, submit captured text via bridge_validate. NO PASTE PROMPT.
          (The user explicitly asked: "Paste output does not make sense in
          terminal" — this branch is the structural fix.)
      0b. step.validation.gha_workflow_check present (capstone) → push current
          branch, poll GHA, watch run, submit run URL via bridge. NO PASTE.
          (The user asked: "For GHA flow, cli should be triggered with
          github push - not something unreal.")
      1.  step.validation.cli_check.kind in _NATIVE_KINDS  → run locally (legacy)
      2.  step.validation.must_contain only                → token check locally
      3.  step.validation.rubric (LMS bridge — default)    → POST to /validate

    Returns: {correct: bool, score: float|int, feedback: str}
    """
    validation = step.get("validation") or {}
    cli_check = validation.get("cli_check")
    cli_commands = validation.get("cli_commands")
    gha_check = validation.get("gha_workflow_check")
    cfg = _read_skillslab_yml(cwd)

    def _attach_debug_factory(submission_text: str, accept_rc_val: int):
        def _attach(result: dict, *, path: str) -> dict:
            result.setdefault("_debug", {})
            result["_debug"].setdefault("submission", submission_text)
            result["_debug"].setdefault("accept_rc", accept_rc_val)
            result["_debug"]["dispatch"] = path
            return result
        return _attach

    # 0a) cli_commands runner — terminal-first replacement for the paste flow
    if isinstance(cli_commands, list) and cli_commands:
        from .cli_runners import run_cli_commands
        run = run_cli_commands(
            cli_commands, cwd=cwd, console=console,
            auto_confirm=auto_confirm,
        )
        if run.aborted_by_user:
            return {
                "correct": False, "score": 0,
                "feedback": "Submission cancelled. Re-run `skillslab check` when ready.",
                "_debug": {"dispatch": "cli_commands:aborted"},
            }
        # The captured text becomes the "paste" the bridge submits to the LMS.
        # Backend validator (must_contain / rubric / both) grades unchanged.
        attach = _attach_debug_factory(run.captured_text, accept_rc_val=0)
        return attach(_bridge_validate(step, run.captured_text, accept_rc=0),
                       path="cli_commands")

    # 0b) gha_workflow_check runner — push + watch + submit run URL
    if isinstance(gha_check, dict):
        # 2026-04-25 v3 — `--paste <run-url>` short-circuit. CLI-walk v3 P2
        # caught: the GHA-watch timeout error advertised "or pass --paste
        # <run-url>" but --paste fed legacy _build_submission, not the GHA
        # validator. Now: if `paste` looks like a GitHub Actions run URL
        # AND the step has gha_workflow_check, skip push/watch and submit
        # the URL directly to the LMS validator. Same dispatch path label
        # for telemetry.
        import re as _re
        paste_str = (paste or "").strip()
        if paste_str and _re.search(
            r"https://github\.com/[^/]+/[^/]+/actions/runs/\d+",
            paste_str,
        ):
            run_url = paste_str.splitlines()[0].strip()
            if console:
                console.print(f"[dim]Using --paste run URL directly (skipping push/watch): {run_url}[/dim]")
            attach = _attach_debug_factory(run_url, accept_rc_val=0)
            return attach(_bridge_validate(step, run_url, accept_rc=0),
                           path="gha_push_watch:via_paste")
        from .cli_runners import run_gha_push_and_watch
        gha = run_gha_push_and_watch(gha_check, cwd=cwd, console=console)
        if not gha.ok or not gha.run_url:
            return {
                "correct": False, "score": 0,
                "feedback": gha.error or "GHA flow failed — see output above.",
                "_debug": {"dispatch": "gha_push_watch:failed"},
            }
        # Submit the run URL as the "paste" — LMS grader (or _check_gha) will
        # hit the GitHub API to verify conclusion. SAME backend contract.
        attach = _attach_debug_factory(gha.run_url, accept_rc_val=0)
        return attach(_bridge_validate(step, gha.run_url, accept_rc=0),
                       path="gha_push_watch")

    # Build paste-style submission for the legacy paths below.
    submission, accept_rc = _build_submission(step, cwd, paste)
    _attach_debug = _attach_debug_factory(submission, accept_rc)

    # 1) Explicit cli_check on the step → run it locally
    if isinstance(cli_check, dict) and cli_check.get("kind"):
        kind = cli_check["kind"]
        fn = _NATIVE_KINDS.get(kind)
        if fn is not None:
            return _attach_debug(fn(cli_check, submission, cwd, cfg), path=f"cli_check:{kind}")
        if console is not None:
            console.print(f"[yellow]Unknown cli_check kind '{kind}', falling back.[/yellow]")

    # 2) must_contain only → deterministic local check
    must_contain = validation.get("must_contain") or []
    rubric_raw = validation.get("rubric") or validation.get("explanation_rubric")
    if must_contain and not rubric_raw:
        return _attach_debug(
            _check_paste_contains({"tokens": must_contain}, submission),
            path="must_contain",
        )

    # 3) Rubric (or rubric+must_contain) → bridge to LMS by default. Verdict
    #    comes back through the API and we render it in the terminal.
    if rubric_raw or must_contain:
        return _attach_debug(
            _bridge_validate(step, submission, accept_rc),
            path="bridge_validate",
        )

    # 4) No grading hook at all
    return _attach_debug({
        "correct": False, "score": 0,
        "feedback": ("This step has no cli_commands / gha_workflow_check / "
                     "rubric / must_contain — it may be a concept-only step. "
                     "Run `skillslab next` to advance."),
    }, path="no_hook")
