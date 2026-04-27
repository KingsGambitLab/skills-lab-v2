"""CLI-walk-agent prompt builder — the Step-1.5 mandatory gate per CLAUDE.md
for any change touching the `skillslab` CLI surface.

Mirror of `beginner_agent.py`, but for the TERMINAL surface instead of the
browser. We had a structural blind spot: every UX bug in `skillslab spec`
(frontmatter dumps, missing problem statement, terse must_contain bullets,
host.docker.internal hardcoded, etc.) reached the user because no automated
walk exercises the CLI. The browser-walk gate caught browser bugs; the CLI
had no parallel.

This shim emits a canonical prompt for a CLI-walk reviewer agent.

## Clean-slate invariant (same as beginner_agent.py)

The agent is a simulated LEARNER. It does NOT see:
- Source code unless it needs to debug a runtime error
- Internal review notes / known bugs
- Admin endpoints

It DOES see (and uses) the public CLI as a black box:
- `skillslab --help`, every subcommand's --help
- Run output verbatim — the agent grades text rendering, panel highlighting,
  error messages, error recovery
- The Docker compose entrypoint (or `bin/skillslab` launcher) — same path
  the user follows

## What the agent grades

For each command + each rendered step, the agent emits a (verb, output, grade,
rationale) tuple. The grades are:
- ✅ clear  — a beginner would understand this on first read
- ⚠ works   — functional but has a friction point worth fixing
- ❌ broken — confusing OR incorrect output OR an error a learner can't recover from

The agent's report goes to `reviews/cli_walk_<date>_<pass_tag>[_<slug>].md`.

Usage:
    from backend.harness import cli_walk_agent
    prompt = cli_walk_agent.build_prompt(
        course_id="created-698e6399e3ca",
        course_title="Open-Source AI Coding: Aider + Kimi K2",
        course_slug="kimi",
        pass_tag="v1",
    )
    # Then hand `prompt` to the Agent tool with subagent_type="general-purpose".
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = PROJECT_ROOT / "reviews"


def default_artifact_path(pass_tag: str = "v1", course_slug: str | None = None) -> str:
    """Canonical artifact path for a CLI-walk run.

    Format: reviews/cli_walk_<ISO-date>_<pass_tag>[_<slug>].md
    """
    today = date.today().isoformat()
    parts = ["cli_walk", today, pass_tag]
    if course_slug:
        parts.append(course_slug)
    return str(ARTIFACT_DIR / ("_".join(parts) + ".md"))


def build_prompt(
    *,
    course_id: str,
    course_title: str,
    course_slug: str = "kimi",
    pass_tag: str = "v1",
    base_url: str = "http://localhost:8001",
    repo_root: str = "/Users/tushar/Desktop/codebases/skills-lab-v2",
    sample_step_id: int | None = None,
    user_filed_issues: list[str] | None = None,
) -> str:
    """Produce the full prompt for a CLI-walk-agent run.

    Args:
        course_id: DB-level course id (e.g. "created-698e6399e3ca").
        course_title: title a learner sees in the catalog.
        course_slug: slug used by `skillslab start <slug>` (e.g. "kimi", "jspring").
        pass_tag: artifact-version tag (v1/v2/v3 across iterations).
        base_url: LMS API URL (CLI talks to this; the agent's render-only
            path also fetches steps from here).
        repo_root: absolute path to the repo so the agent can locate the
            launcher + cli/docker-compose.yml.
        sample_step_id: if set, render-only checks pin to this step (lets you
            target a specific known-failure step). If None, agent picks one.
        user_filed_issues: list of recent UX issues to verify closed. Optional —
            if non-empty, the agent walks each as part of Section B.
    """
    artifact_path = default_artifact_path(pass_tag=pass_tag, course_slug=course_slug)
    issues_block = ""
    if user_filed_issues:
        issues_block = "\n## RECENTLY-FILED ISSUES (verify each is closed)\n\n"
        for i, iss in enumerate(user_filed_issues, 1):
            issues_block += f"{i}. {iss}\n"
        issues_block += "\nFor EACH, mark CLOSED / STILL OPEN / NEW FORM with verbatim evidence.\n"

    sample_pin = (
        f"Pin Section B to step **{sample_step_id}** specifically (the one"
        f" known to surface the rendering issues)."
    ) if sample_step_id else "Pick any meaty terminal_exercise step to render."

    return f"""You are a beginner-level CLI user (1-2 yrs of terminal experience, never used `skillslab` CLI before) walking through the Docker container CLI to validate UX. Your job: find friction points a real learner would hit. You are NOT a developer reviewing code (except in the STATIC-INVARIANT sections explicitly below) — you are a learner trying to do an assignment.

## CONTEXT

- Repo root: `{repo_root}`
- LMS API: `{base_url}` (already running)
- Course under test:
   - Title: `{course_title}`
   - ID: `{course_id}`
   - Slug: `{course_slug}` (use this with `skillslab start {course_slug}`)
- Docker image `skillslab:latest` is pre-built. `cli/docker-compose.yml` is the
  compose entrypoint. `cli/bin/skillslab` is the host launcher script.
- {sample_pin}

## EXPLICIT INVARIANTS (run BEFORE the behavioral walk)

The user has caught too many issues live that the previous walks missed.
These are mandatory STATIC checks — fast, deterministic, structural.
Most are grep / source-read / DB-scan; a few exec real commands.
Mark each ✅ pass / ❌ fail with the EXACT evidence (file:line, output line, etc.)

### I. Command-name integrity

**I1.** Extract every `skillslab <CMD>` reference from CLI user-facing strings
       (panels, help text, error messages, docstrings). Sources to grep:
         - cli/src/skillslab/cli.py
         - cli/src/skillslab/check.py
         - cli/src/skillslab/cli_runners.py
         - cli/src/skillslab/render.py
       Run: `grep -hoE "skillslab [a-z][a-z\\-]+" {repo_root}/cli/src/skillslab/*.py | sort -u`
       Then list every Click-registered command via:
         `python3 -c "import sys; sys.path.insert(0, '{repo_root}/cli/src'); from skillslab.cli import cli; print('\\n'.join(sorted(cli.commands)))"`
       FAIL if any referenced `skillslab <CMD>` is not in the registered set.
       (v3 missed: `skillslab progress` was an unknown command.)

### II. URL precision — every emission site routes through `_browser_url`

**II1.** Pick a known web step (e.g. {course_slug} M1.S1, exercise_type=concept).
       Render via Path C, extract the dashboard URL emitted by `_print_web_pointer`.
       Verify it has the 3-part form `#<courseId>/<moduleId>/<stepIdx>` (NOT
       just `#<courseId>` which lands on stale cursor).

**II2.** **CALL-SITE AUDIT (v5)** — `_browser_url(course_id, step)` is the
       canonical URL builder. Audit EVERY URL-emission site to ensure it
       routes through this function. Bypass detection: any line that
       constructs a URL with `web_url()` AND a literal `#` on the same
       line is a candidate bypass. Run (a single command line; no
       continuation):

       ```bash
       grep -nE 'web_url\\(\\).*#' cli/src/skillslab/*.py
       ```

       Should return ONLY lines inside `_browser_url`'s own body. Each
       hit OUTSIDE that function is a URL-emission site that needs to
       be migrated to `url = _browser_url(course_id, step_or_empty_dict)`.

       (v4 caught: `_next_action` web branch built URL from course_id ALONE,
       bypassing `_browser_url`. v5 caught a 3rd site at `dashboard` cmd.
       Same precision-bug class repeated. v5+ must audit all sites, not
       just verify the function is correct.)

**II3.** **URL→FRONTEND ROUND-TRIP** (added 2026-04-27 after a live bug
       II1 missed). II1 only checked URL SHAPE (3 parts present); it didn't
       verify the URL actually points at the right step when the FRONTEND
       parses it. v6 missed: `_browser_url` emitted `step_pos` (1-indexed
       from DB position) where the frontend's `parseHash` reads
       `parts[2]` as a 0-indexed array index → user clicked `M1.S1` URL
       and landed on `M1.S2`.

       **Mechanical round-trip check** — DON'T eyeball the parts:
       ```python
       # Pick a step — preferably the FIRST step of a non-first module so
       # the off-by-one is visible (M1.S1 of any course works).
       step = <DB row for first step of M1, e.g. AIE step_id=85060,
               module_id=23189, step_pos=1>

       # Build the URL the way the CLI does
       from skillslab.cli import _browser_url
       url = _browser_url(course_id, {
           "module_id": step.module_id,
           "step_pos": step.step_pos,
       })

       # Parse the URL the way the frontend's parseHash does
       hash_part = url.split("#", 1)[1]
       parts = [p for p in hash_part.split("/") if p]
       parsed_module_id = int(parts[1])
       parsed_step_idx = int(parts[2])  # 0-indexed array position

       # Look up the step the way the frontend does:
       # state.currentModuleData.steps[stepIdx].id
       module_steps = sorted(
           <DB rows of all steps in module=parsed_module_id>,
           key=lambda s: s.position,
       )
       resolved_step = module_steps[parsed_step_idx]

       assert resolved_step.id == step.id, (
           f"URL points at step_id={{resolved_step.id}} "
           f"but the CLI said it was step_id={{step.id}}. "
           f"Off-by-one between DB position and frontend stepIdx."
       )
       ```

       Run this on at LEAST one S1 step from each course (kimi/aie/jspring).
       If any assertion fails, the URL builder is mis-mapping indexing
       conventions — same bug class as the 2026-04-27 fix.

### III. cli_commands runner integrity

**III1.** For 3 sample terminal_exercise steps (cover M0, mid, capstone),
       extract `validation.cli_commands` via API. For EACH cmd:
         - Run it with `subprocess.run(cmd, shell=True, ...)` against the
           current container's tools (PATH C does this from the host's
           Python — agent confirms each cmd actually executes cleanly).
         - Verify exit_code == 0 OR cmd intentionally tests failure.
         - Verify the cmd uses CORRECT model invocations: bare
           `moonshotai/kimi-k2` is FORBIDDEN; must be
           `openrouter/moonshotai/kimi-k2-0905`. claude-code course uses
           `claude /login`, `claude --version`, `claude -p`, etc.
       FAIL if any cmd produces non-zero exit OR uses forbidden invocation.
       (v3+live missed: `[Aa]ider v\\d+\\.\\d+` regex didn't match real
       `aider 0.86.2` output; `aider --model moonshotai/kimi-k2` failed
       litellm.BadRequestError.)

### IV. Renderer/grader alignment

**IV1.** Read `cli/src/skillslab/render.py:step_to_markdown`. For each grading
       primitive in the validation schema, verify there's a render branch:
         - cli_commands     → must have a section listing each cmd in the rendered MD
         - gha_workflow_check → must mention push/watch flow
         - cli_check        → must show YAML spec
         - rubric           → must show rubric criteria
         - must_contain     → must show evidence-token list
       FAIL if any primitive has no render branch (briefing won't preview
       what `skillslab check` will do).
       (v3 caught the cli_commands gap as P1; v4 should keep this invariant.)

### V. Stale-string sweep

**V1.** Grep CLI source for terms that should be retired post-rename:
         - `\\baie\\b` (the slug, NOT inside `_SLUG_ALIASES` map or backwards-compat
           comments) — anywhere user-facing should say `claude-code` instead.
         - `host\\.docker\\.internal` (in URL emission paths — use web_url() instead)
         - `paste your output` / `copy and paste` / `pastes? two complete` /
           `final paste` / `pasted output` (in user-facing prose for
           terminal_exercise — terminal-first means no paste verbiage).
       FAIL with file:line for each match in user-facing context.
       (v3 missed: `--course aie` in --help text. Live missed: "next terminal step".)

### VI. Surface-bias prose

**VI1.** Scan pointer / CTA texts for surface-presupposing phrases when the
       next step's surface might be either:
         - "next terminal step" (assumes terminal)
         - "back to the dashboard" (assumes web)
         - "in your browser" without an "if web" qualifier
       FAIL with the verbatim phrase + file:line.
       (Live missed: "advance to the next terminal step" — user caught it.)

### VII. Flag wiring (every advertised flag must be implemented)

**VII1.** Grep CLI source for advertised flags in error messages, help text,
       comments, panel content:
         `grep -hE -- "--[a-z][a-z\\-]+" {repo_root}/cli/src/skillslab/*.py | sort -u`
       For each flag, verify it's registered via @click.option somewhere
       AND that the consuming code path actually USES the value.
       FAIL on any advertised flag with no consumer.
       (v3 caught `--paste <run-url>` advertised but not wired to GHA runner.)

### VIII. Surface drift (DB scan against the v5 simple rule)

**VIII1.** Scan ALL steps in {course_id}: for each step, compute the
        derived surface using the v5 rule (verbatim from
        `backend/learner_surface.py:classify_step` 2026-04-25 v5):
          - `terminal_exercise` → terminal (if course CLI-eligible)
          - `system_build` with validation.gha_workflow_check present → terminal
          - everything else → web
        Compare derived value to `step.learner_surface` stored in DB. ANY
        mismatch is a P0 — ship script would have routed the learner to
        the wrong UI for grading.
        (v3 caught M0.S3 scenario_branch=terminal; v4 caught style-widget
        concept=terminal; v5 simple-rule kills the whole class.)

**VIII2.** Cross-check the resolver code path. Confirm
        `backend/main.py:_resolve_learner_surface` does NOT consult any
        declared/LLM value for the final result (it should only LOG when
        declared disagrees). FAIL if you see `return declared_norm` or
        equivalent — the renderer/classifier is the source of truth, not
        the LLM emission.

### IX. Static smoke: cli_runners imports + no syntax errors

**IX1.** `python3 -m py_compile cli/src/skillslab/{{cli,check,cli_runners,render,state}}.py`
       FAIL on any non-zero exit.

After running I-IX, proceed to the BEHAVIORAL WALK below. The static
invariants run in <30s; no LLM cost. Fail-fast on these — don't waste
walk time on a CLI with structural bugs.

## HOW TO RUN THE CLI (pick whichever path is cleanest)

```bash
# Path A — direct compose, with WORK_DIR override (no launcher dependency)
mkdir -p /tmp/skillslab-walk
SKILLSLAB_WORK_DIR=/tmp/skillslab-walk \\
  docker compose -f {repo_root}/cli/docker-compose.yml \\
  run --rm skillslab skillslab status

# Path B — use the launcher (simulates user with `skillslab` on PATH)
cd /tmp/skillslab-walk
{repo_root}/cli/bin/skillslab status

# Path C — rendering-only, no Docker (fastest for Section B)
cd {repo_root}/cli
python3 -c "
import sys; sys.path.insert(0, 'src')
from skillslab.render import step_to_markdown
import urllib.request, json
data = json.loads(urllib.request.urlopen('{base_url}/api/courses/{course_id}').read())
for m in data.get('modules', []):
    sub = json.loads(urllib.request.urlopen('{base_url}/api/courses/{course_id}/modules/' + str(m['id'])).read())
    for s in sub.get('steps', []):
        print(step_to_markdown(s, course_title=data['title'], module_title=m['title']))
"
```

`skillslab login` requires an LMS bearer token. If you can't get a token, focus
on the auth-free paths: Path C (rendering), `--help` flows, `skillslab now`
without a course state, the launcher behavior. Document any auth blockers.

{issues_block}

## TEST CHECKLIST

For each step, capture: **command** / **output** (verbatim, ≤30 lines) /
**grade** ✅⚠❌ / **why** (1-2 sentences from a beginner's POV).

### Section A — Help discoverability
A1. `skillslab --help` (top-level)
A2. `skillslab now --help`
A3. `skillslab spec --help`
A4. `skillslab clone --help`
A5. `skillslab status --help`
A6. `skillslab check --help`

Grade: would a beginner know what each does without reading source?

### Section B — Rendering correctness (the key surface)
For one terminal_exercise step from `{course_title}`:
B1. Render via Path C. Capture full markdown output.
B2. ✅/❌ — is YAML frontmatter visible as prose? (should be stripped or styled)
B3. ✅/❌ — any raw `\\u2014` / `\\u2018` / similar unicode escapes? (should be verbatim)
B4. ✅/❌ — is there a clear "what to do" / action-list / problem statement section?
B5. ✅/❌ — do `must_contain` bullets carry descriptions, or are they bare tokens?
B6. ✅/❌ — anything else a beginner would call out?

### Section C — Next-step guidance
C1. Run `skillslab now` (with state if available, without if not). Does it answer
    "where am I + what's next" in one glance?
C2. Run `skillslab next` (advance cursor). Is the next-step CTA highlighted (Rich Panel)?
C3. After `skillslab check` (passing or failing), is the next instruction obvious?

### Section D — Browser URL correctness
D1. For a `web` step, capture the "Open in your browser:" URL line.
    Should it be `localhost`? `host.docker.internal`? Verify it's the host-reachable one.
D2. Set `SKILLSLAB_WEB_URL=https://lms.example.com` in the env and re-run.
    Verify the URL is replaced.

### Section E — Launcher + work-dir cleanliness
E1. `mkdir -p /tmp/skillslab-walk-clean && cd /tmp/skillslab-walk-clean`,
    invoke launcher: `{repo_root}/cli/bin/skillslab status` (or `bash`).
    From inside container: `ls /work` should be empty (or contain only your repo).
E2. Compare with running compose from `{repo_root}/cli/`:
    `cd {repo_root}/cli && docker compose run --rm skillslab ls /work` should
    pollute `/work` with cli source files (the failure path that motivated
    the launcher). The launcher in E1 should NOT have this.

### Section F — Error recovery
F1. Run `skillslab status` with no course started. What's the error?
    Is it actionable? (Should suggest `skillslab login` / `skillslab start <slug>`.)
F2. Run `skillslab spec` for a non-existent step. Same question.
F3. Run `skillslab check` with no clipboard / no paste. Same question.

### Section G — Beginner first-impression (open-ended)
G1. As a first-time user, what's the FIRST thing you'd be confused by?
G2. What's missing? (Onboarding text? Install instructions? Pre-flight check?)
G3. What would help? (One-line per friction point.)

## OUTPUT

Write your full report to: `{artifact_path}` (markdown, 1500-2500 words). Structure:

1. **Verdict** (top line): SHIP / SHIP-WITH-FIXES / REJECT
2. **Sections A–G** with verbatim output and grades
3. **Top 5 friction points** (P0/P1/P2 priority, concrete fix sketch)
4. **Things working well** (don't just complain — call out what's right)
5. **Suggestions for the permanent CLI-walk harness** — what should it always check?

You are simulating a LEARNER. Don't read CLI source unless you need to debug a runtime error. The CLI is a black box; you grade what comes out.
"""
