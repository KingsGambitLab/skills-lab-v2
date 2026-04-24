"""Beginner-agent prompt builder — the Step-1 mandatory gate per CLAUDE.md.

The beginner agent walks a course as an RL-style learner (no answer keys, no
admin API, browser-only via Claude_Preview MCP) and produces a streaming
markdown artifact that reviewers consume to approve / reject the course.

Before this module existed, every beginner-agent spawn required hand-authoring
a 100+ line prompt. That's toil and it drifts. This module emits a canonical
prompt from a tiny input (course_id + title + subject) so the gate is
reproducible across courses.

## Clean-slate invariant (2026-04-22 v6)

User directive: **"Always keep a clean slate, don't pass information the
agent should not have."**

The agent is a simulated LEARNER. A real learner does NOT know:
- Which tests exist or how many (hidden_tests count, must_contain contents,
  solution_code, correct_mapping, bug_lines, …)
- Which steps the platform team is worried about
- What known bugs exist in the current build
- What specific wrong answer might trip a weak grader

So this shim accepts ONLY learner-level inputs: `course_id`, `course_title`,
`course_subject` (same as catalog), `pass_tag` (for artifact naming). No
`verify_bugs`, no "focus on step X", no stub suggestions, no backend-internal
state. Reviewers who want to verify a specific regression should do it via
the deterministic harness (`tools/test_course.py`, Step 2) which HAS admin
access — not by leaking internals into the learner simulation.

Usage:
    from backend.harness import build_prompt
    prompt = build_prompt(
        course_id="created-a65765767790",
        course_title="Python Essentials: Data Structures and Algorithms",
        course_subject="beginner/intermediate Python, data structures & algorithms",
        pass_tag="v4",
    )
    # Then hand `prompt` to the Agent tool.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

# Project-root relative path where every beginner-agent run streams its artifact.
# The agent itself writes to this path; reviewers tail -F it during a run.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = PROJECT_ROOT / "reviews"


def default_artifact_path(pass_tag: str = "v1", course_slug: str | None = None) -> str:
    """Return the canonical artifact path for a run.

    Format: reviews/beginner_stream_walkthrough_<ISO-date>_<pass_tag>[_<slug>].md
    """
    today = date.today().isoformat()
    parts = ["beginner_stream_walkthrough", today, pass_tag]
    if course_slug:
        parts.append(course_slug)
    return str(ARTIFACT_DIR / ("_".join(parts) + ".md"))


def build_prompt(
    *,
    course_id: str,
    course_title: str,
    course_subject: str = "",
    base_url: str = "http://localhost:8001",  # v8.6.1 — Claude Preview + some browsers only resolve 'localhost', not '127.0.0.1'
    pass_tag: str = "v1",
    course_slug: str | None = None,
    tool_budget_hint: int = 150,
    min_steps_to_walk: int = 10,
) -> str:
    """Produce the full prompt for a beginner-agent run.

    Args:
        course_id: the DB-level course id (e.g. "created-a65765767790").
        course_title: the title a real learner sees in the catalog.
        course_subject: short subject-area description — same as the catalog
            description a learner would see. The agent MUST see nothing more
            than this about the course's content.
        base_url: where the platform is running.
        pass_tag: "v1" / "v2" / … — bumped each iteration of a fix-loop.
            Used only for artifact naming; the agent is not told which pass
            it is (every run is a fresh learner).
        course_slug: optional short identifier appended to the artifact
            filename. Useful when running against multiple courses in parallel.
        tool_budget_hint: approximate tool-call ceiling.
        min_steps_to_walk: minimum number of steps the agent MUST attempt
            before compiling the final summary.

    Returns:
        A ~3500-char prompt string. Contains ONLY learner-level information.
        Does NOT contain any backend-internal state, known-bug hints, stub
        suggestions, test counts, grader-field names, or pass-tag references.

    The clean-slate invariant (2026-04-22 v6) is enforced at the function
    level: this signature has NO parameter that accepts arbitrary text from
    the caller about bugs or internals. The only free-text inputs are
    `course_title` and `course_subject`, which come from the public catalog.
    """
    artifact = default_artifact_path(pass_tag=pass_tag, course_slug=course_slug)

    return f"""You are a beginner Python programmer (or learner in whatever language the course covers). You've just enrolled in a course and are walking through it for the first time.

## Strict RL rules (no cheating, clean slate)

You know ONLY:
- Course title: "{course_title}"
- Subject area: {course_subject or "as described in the course catalog"}
- The course is at {base_url}/#{course_id}

You MUST NOT:
- Access `/api/admin/courses/*/raw` (leaks answer keys)
- Read `skills_lab.db` directly
- Open any file under `backend/*.py` or `backend/*.json` / `backend/courses/*.py`
- `curl` or `POST` directly to `/api/exercises/validate` or any backend API — all grading goes through the browser UI
- Read any prior review artifact under `reviews/` before starting

You MUST:
- Drive the course via `mcp__Claude_Preview__preview_*` tools — real browser, real clicks
- For every `code_exercise`: write the solution from first principles using ONLY the briefing, the starter code, and the on-page hint. A real learner sometimes submits a casual half-answer to see what the grader says — feel free to try a quick guess first, then a real attempt.
- For every `code_read`: observe what the step expects. Does it auto-complete on view, or does it expect a submission? Note what you experience.
- For every drag-drop / categorization / code_review / mcq / fill_in_blank type: try a wrong answer first (as a real learner exploring the grader), then a real attempt.
- Cap each step at **3 attempts**. If stuck after 3, flag the step `❌ stuck (beginner-hostile)` and move on.
- Walk at least {min_steps_to_walk} steps before compiling the final summary. Skim the rest if the pattern is established.

## Streaming artifact

Write + rewrite this file after EVERY step so a reviewer can `tail -F` it live:

    {artifact}

Per-step block format:
```
## Step <M.S> — "<title>" — <type>
- Briefing clarity: 1-5  | time on step: ~X min
- Attempt 1 (wrong|right): what I submitted
  - Score: X
  - Feedback verbatim: "..."
  - Did this help me? yes|no  Why: ...
- [Attempt 2 / 3 if applicable]
- Verdict: ✅ passed | ❌ stuck | ⚠ partial
- UI notes: any bugs — Submit didn't fire, feedback didn't clear, counter stuck, per-item marks missing, banner text wrong, or anything else off
```

## What to report

Report the honest learner experience:
- Was the briefing clear enough to start the exercise?
- Did the grader feedback help you iterate, or was it generic / misleading?
- Did wrong-answer feedback teach you something, or just punish?
- Did any step feel broken (buttons that did nothing, counter stuck, UI glitches)?
- Would you, as a real learner, have quit or pushed through?

## Tool-budget discipline

Approximate ceiling: **{tool_budget_hint} tool calls**. Don't re-verify every step exhaustively once a pattern is established. Prioritize: one step of every exercise type you encounter + any step that felt unusual. Skim the rest.

## Final summary block

At the end of the artifact:
- Pass / stuck / partial tally by exercise type
- Any step that felt beginner-hostile (couldn't make progress, unclear, broken UI)
- Any step where the grader felt too lenient or too harsh
- Verdict: ✅ APPROVE / ⚠ CONDITIONAL / ❌ REJECT (matching CLAUDE.md Step-1 approval table)

Reply DONE + the artifact path when complete.
"""
