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

    return f"""You are a beginner-level CLI user (1-2 yrs of terminal experience, never used `skillslab` CLI before) walking through the Docker container CLI to validate UX. Your job: find friction points a real learner would hit. You are NOT a developer reviewing code — you are a learner trying to do an assignment.

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
