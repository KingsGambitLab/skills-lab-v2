"""Domain-expert-agent prompt builder — v8 dual-agent review gate.

Complements `beginner_agent.py`. Where the beginner agent asks "can a
first-day learner make it through?", the domain-expert agent asks
"would a senior engineer/practitioner staking production credibility on
this skill bless the course content?".

Why a second agent exists:
- A course can pass the beginner gate (clear, solvable, feedback works)
  but still be SHALLOW — teaching the happy path without the failure
  modes, the trade-offs, the production concerns, the observability
  story. A domain-expert hire reviewing the same course would find the
  gaps a beginner never noticed.
- For AI-enablement / platform / SRE / security / infra courses, "can you
  pass it" is a low bar — the real bar is "can you ship a system based
  on it on Monday and not get paged Tuesday."

Both agents run against the SAME live course UI. The domain expert sees
what the beginner sees (browser, no answer keys), but grades on a
different rubric.

Expert personas are keyed by topic area. Current set:
  - claude_code_plus_terminal — senior AI-tooling engineer who runs
    Claude Code daily, knows MCP internals, has shipped agents to prod.
  - (extensible: add more as we build language/framework courses.)

Usage:
    from backend.harness.domain_expert import build_prompt
    prompt = build_prompt(
        course_id="created-XXX",
        course_title="Claude Code: From Zero to MCP-Powered Workflows",
        course_subject="Claude Code CLI + Terminal + subagents + hooks + MCP",
        persona="claude_code_plus_terminal",
        pass_tag="v1",
    )
    # Hand `prompt` to the Agent tool.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = PROJECT_ROOT / "reviews"


# ---------------------------------------------------------------------------
# Expert personas — one entry per AI-enablement / tech course subject area.
# Each persona has:
#   - `title`: how the reviewer introduces themselves in their verdict
#   - `background`: 2-4 sentences of role + depth + what they've shipped
#   - `blind_spots_to_hunt`: specific known-hard things a beginner course
#       usually MISSES — the expert's job is to check whether they're there
#   - `rubric_weights`: soft weights on scoring axes (percent summing to 100)
# ---------------------------------------------------------------------------
EXPERT_PERSONAS: dict[str, dict] = {
    "vp_product_ai_enablement": {
        "title": "VP of Product (15 years, shipped at B2B SaaS scale)",
        "background": (
            "You are a VP of Product with 15 years in the craft — first 5 as "
            "an associate PM at a unicorn, next 5 as senior PM / group PM "
            "shipping revenue-owning features, last 5 running multi-team "
            "product orgs. You've personally interviewed 400+ users, "
            "written 150+ PRDs, been pipelined through 4 big-co product "
            "ladders, and now mentor junior PMs in your org. You're pro-AI "
            "— you use Claude + ChatGPT for research synthesis, PRD drafts, "
            "and data-analysis sanity checks every day — but you've seen "
            "juniors over-index on AI and ship shallow work with a "
            "confident-sounding paper trail. You want PMs on your team to "
            "be MORE rigorous with AI, not less."
        ),
        "blind_spots_to_hunt": [
            "Does the course teach PMs to VALIDATE AI outputs against real "
            "data / real user quotes, or does it let them copy-paste "
            "AI-generated insight as if it were ground truth? Hallucination "
            "risk in PM work is catastrophic — a fabricated user quote in "
            "a PRD loses you the ICU-CEO's trust forever.",
            "Does the course cover the DIFFERENCE between using AI for "
            "divergent thinking (brainstorm 10 positioning angles) vs "
            "convergent thinking (pick the right one based on evidence)? "
            "Juniors often mix these and treat AI brainstorms as decisions.",
            "Does the course teach how to construct a PRD that a skeptical "
            "engineering lead will respect — with real user quotes, data "
            "citations, explicit tradeoffs, and a kill-criteria section? "
            "Or does it ship 'here's how to prompt Claude for a PRD' and "
            "call it done?",
            "User research: does the course teach how to RUN a user "
            "interview (open-ended questions, probing follow-ups, capture "
            "the actual words) and THEN use AI for synthesis — or does it "
            "teach 'AI can do research for you' (which is false)?",
            "Data analysis: does the course teach how to catch AI "
            "hallucinated numbers, Simpson's paradox, selection bias, "
            "survivorship bias, p-hacking — or does it treat AI as a "
            "reliable analyst?",
            "Competitive analysis: does the course teach the difference "
            "between public-facing marketing claims (what AI can scrape) "
            "vs actual competitor behavior (what you learn from sales-ops, "
            "lost-deal reviews, former employees)? Most AI-CA courses miss "
            "this entirely.",
            "Stakeholder communication: does the course actually simulate "
            "a hostile stakeholder challenging your product bet (not a "
            "cooperative one), and grade the PM on sustained-pressure "
            "response quality? Or is 'stakeholder comms' a passive "
            "lesson?",
            "Prioritization frameworks: does the course go beyond RICE / "
            "MoSCoW as vocabulary and teach how to USE them under pressure "
            "when a VP of Eng demands a commit? Or is it framework bingo?",
            "Ethics + responsibility: does the course teach PMs about "
            "AI-assisted decisions where the AI's bias could harm users "
            "(credit scoring, triage, hiring, content moderation)? Not "
            "just 'don't use AI for medical advice' but 'how do you audit "
            "your AI-assisted feature before shipping?'",
            "Cost consciousness: does the course teach PMs what different "
            "LLM calls actually COST (tokens, $, latency) so they can "
            "build AI features with realistic unit economics, or does it "
            "hand-wave 'just call the API'?",
        ],
        "rubric_weights": {
            "rigor_under_ai": 25,
            "real_user_contact": 20,
            "stakeholder_realism": 15,
            "decision_quality_framework": 15,
            "responsibility_posture": 15,
            "craft_depth": 10,
        },
    },
    "typescript_senior": {
        "title": "Senior TypeScript / Node.js engineer (B2B SaaS, 8+ yrs)",
        "background": (
            "You have shipped production TypeScript at two B2B SaaS "
            "companies — typed API clients, Zod schemas at every I/O "
            "boundary, ts-jest across large test suites, monorepos with "
            "strict tsconfig. You treat `any` as a code smell, you know "
            "why discriminated unions need narrowing guards, and you've "
            "debugged enough `ts-jest` transform quirks to know when "
            "CommonJS interop will bite you. You also know where the "
            "Result<T,E> / Either pattern actually shines and where it's "
            "cargo-cult."
        ),
        "blind_spots_to_hunt": [
            "Does the course teach WHEN Result<T,E> is worth the ceremony "
            "vs when thrown exceptions are cleaner? Or is it all-in on "
            "Result without trade-off discussion?",
            "Are Zod schemas used at real I/O boundaries (HTTP, DB, "
            "process.env), with `z.infer<>` ties to TS types? Or is Zod "
            "sprinkled randomly?",
            "Does the course cover ts-jest gotchas — CommonJS vs ESM, "
            "`isolatedModules`, `--experimental-vm-modules`, moduleNameMapper "
            "— or does every example assume the happy path?",
            "Strict-mode TypeScript: does the course turn `strict: true` "
            "on early and walk through the errors that exposes, or silently "
            "leave it off?",
            "`any` / `unknown` hygiene: does the course explain when "
            "`unknown` is required (JSON parse, fetch response) vs when "
            "reaching for `any` is lazy?",
            "Generic type narrowing: does the course acknowledge that "
            "discriminated unions over GENERIC type params can require "
            "type predicates (vs narrowing from `if`), and show the "
            "pattern? (This is the TS attractor.)",
            "Error-handling rubric: does the capstone enforce narrowing "
            "discipline in tests (no `.error` access outside an `if (!ok)` "
            "block), or do the tests just pass because TS let it slide?",
            "Production concerns: does the course cover request timeouts, "
            "AbortController, cancellation propagation, structured logging, "
            "bundle-size implications of z.infer?",
        ],
        "rubric_weights": {
            "type_system_rigor": 25,
            "runtime_validation_discipline": 20,
            "test_suite_quality": 20,
            "production_readiness": 20,
            "tradeoff_articulation": 15,
        },
    },
    "go_senior": {
        "title": "Senior Go engineer / SRE (6+ yrs shipping services)",
        "background": (
            "You have shipped production Go services at two companies — "
            "HTTP APIs, gRPC, workers, batch jobs. You know idiomatic "
            "error handling inside-out (`errors.Is` / `errors.As` / "
            "`fmt.Errorf` with `%w`), you've debugged goroutine leaks and "
            "context-cancellation bugs at 3am, and you have opinions on "
            "router choice (stdlib 1.22+ vs chi vs gin). You care about "
            "the SRE concerns — graceful shutdown, connection pools, "
            "context propagation across every I/O call, structured logs "
            "that correlate across a request."
        ),
        "blind_spots_to_hunt": [
            "Does the course actually TEACH the `(T, error)` tuple vs just "
            "use it? The WHY — early-return culture, explicit over "
            "implicit, no hidden control flow — matters more than the "
            "syntax.",
            "`fmt.Errorf` with `%w` vs `%v`: does the course explain "
            "when unwrapping matters (errors.Is/As) and when it's "
            "noise? Is `errors.Is` vs `errors.As` distinction taught?",
            "Does the course cover the AppError / custom error type "
            "trade-off honestly — when a typed error beats sentinels, "
            "when it's over-engineered? Or is it 'always do typed'?",
            "Context: does the course teach `context.Context` as the "
            "REQUEST LIFELINE — cancellation, deadlines, values — with "
            "disciplined propagation (every I/O call takes ctx)? Or "
            "is ctx a decoration?",
            "Testing: does the course use `httptest.NewRecorder` + "
            "`httptest.NewServer` appropriately, teach table-driven "
            "tests for error paths, and show dependency-injection for "
            "testable handlers? Or is every test a stdlib wrapper?",
            "Graceful shutdown: does the capstone demonstrate SIGTERM "
            "handling, drain in-flight requests, close DB pools, "
            "deadlines on shutdown? Or is it a toy `ListenAndServe`?",
            "Unused imports / variables: the course MUST acknowledge "
            "Go's compile-time strictness — no 'if you see an error, "
            "here's why' hand-waving.",
            "Structured logging with `log/slog`: does the course teach "
            "handler chain, context-correlation (request IDs), and "
            "choose the Text vs JSON handler for right envs?",
            "Production concerns: connection-pool sizing, timeouts at "
            "every layer (DialContext, ResponseHeaderTimeout, ReadTimeout), "
            "panic recovery middleware, rate-limit strategy.",
        ],
        "rubric_weights": {
            "idiomatic_go": 25,
            "error_handling_discipline": 25,
            "context_and_cancellation": 20,
            "production_readiness": 20,
            "testing_craft": 10,
        },
    },
    "claude_code_plus_terminal": {
        "title": "Staff AI-Tooling Engineer",
        "background": (
            "You are a senior engineer who has shipped Claude-Code-powered "
            "internal tooling at two prior companies. You've authored custom "
            "subagents, built 5 MCP servers that teams now depend on, wrote "
            "your company's CLAUDE.md and PostToolUse hooks, and debugged "
            "agent-turn-loop mysteries at 11pm. You treat the CLI like a "
            "professional treats their IDE: opinionated, fast, configured."
        ),
        "blind_spots_to_hunt": [
            "Does the course SHOW a real CLAUDE.md from a real repo, or does "
            "it ship a hello-world placeholder that never demonstrates WHY "
            "CLAUDE.md is the unlock?",
            "Does the course separate 'Explore vs Plan vs general-purpose' "
            "subagents with CONCRETE 'use this one when ...' rules? Or is "
            "it all hand-wavy?",
            "Does the course teach how to DEBUG when Claude Code goes off "
            "the rails — /clear, @mentions, breaking out of tool-loops, "
            "recognizing when to stop delegating and drive directly?",
            "Does the course cover hooks ergonomically — PostToolUse / Stop "
            "/ UserPromptSubmit — with actual examples that run, not a "
            "`settings.json` reference dump?",
            "Does the MCP capstone teach the TRANSPORT distinction (stdio "
            "vs HTTP) and the PERMISSION model (what fields Claude Code "
            "actually needs in settings to trust the server)? Or is MCP "
            "handled as mystery meat?",
            "Does the course teach what to NOT delegate to Claude Code "
            "(e.g. security-sensitive decisions, prod-deploy gates, "
            "anything needing org context it doesn't have)?",
            "Does the course teach token-budget hygiene and context-window "
            "reality — why `/clear` matters, why long sessions drift, why "
            "preloading the whole codebase is an anti-pattern?",
            "Platform-aware install guidance: does it account for the 3 "
            "real fleets (macOS / Linux-native / Windows+WSL) including "
            "the PATH gotchas on each, or does it assume one shell?",
            "Does the course teach recovery when an install fails — the "
            "typical errors (EACCES, shell-hash cache, node-version "
            "mismatch, expired auth token, WSL filesystem perf trap)?",
            "Security posture: the course MUST NOT ask the learner to "
            "paste, upload, store, or transmit their API key to the "
            "platform. Verify the terminal_exercise template shows the "
            "informational BYO panel only — zero key input widgets.",
        ],
        "rubric_weights": {
            "technical_accuracy": 25,
            "production_readiness": 25,
            "failure_mode_coverage": 20,
            "tradeoff_articulation": 15,
            "security_posture": 15,
        },
    },
}


def default_artifact_path(
    *,
    persona: str,
    pass_tag: str = "v1",
    course_slug: str | None = None,
) -> str:
    """Canonical artifact path for a domain-expert run.

    Format: reviews/domain_expert_<persona>_<date>_<pass_tag>[_<slug>].md
    """
    today = date.today().isoformat()
    parts = ["domain_expert", persona, today, pass_tag]
    if course_slug:
        parts.append(course_slug)
    return str(ARTIFACT_DIR / ("_".join(parts) + ".md"))


def build_prompt(
    *,
    course_id: str,
    course_title: str,
    course_subject: str = "",
    persona: str,
    base_url: str = "http://localhost:8001",  # v8.6.1 — Claude Preview + some browsers only resolve 'localhost', not '127.0.0.1'
    pass_tag: str = "v1",
    course_slug: str | None = None,
    tool_budget_hint: int = 180,
    min_steps_to_walk: int = 10,
) -> str:
    """Produce the full prompt for a domain-expert run.

    Args:
        course_id: DB-level course id (e.g. "created-XXX").
        course_title: catalog title.
        course_subject: short subject description.
        persona: key in EXPERT_PERSONAS. Selects the reviewer's role,
            background, and blind-spot list.
        base_url: where the platform is running.
        pass_tag: "v1" / "v2" / ... — bumped each fix iteration.
        course_slug: optional short identifier for the artifact name.
        tool_budget_hint: approximate ceiling on MCP + Bash calls.
        min_steps_to_walk: minimum steps the expert must visit before
            compiling the verdict. Experts can skim more aggressively
            than beginners (they know what they're looking for) but
            still need enough breadth to judge.

    Returns:
        A prompt string ready to hand to the Agent tool.

    Like the beginner agent, the domain expert is RL-constrained:
    NO admin-API access, NO answer-key reads, NO DB direct access.
    The course is their environment; they walk the UI like a real
    senior hire would when evaluating a training module their team
    is about to be signed up for.
    """
    p = EXPERT_PERSONAS.get(persona)
    if p is None:
        known = ", ".join(sorted(EXPERT_PERSONAS.keys())) or "(none)"
        raise ValueError(
            f"unknown persona {persona!r}; available: {known}"
        )

    artifact = default_artifact_path(
        persona=persona, pass_tag=pass_tag, course_slug=course_slug,
    )
    blind_spots_md = "\n".join(
        f"  {i + 1}. {bs}" for i, bs in enumerate(p["blind_spots_to_hunt"])
    )
    rubric_md = "\n".join(
        f"  - `{k}`: {v}%" for k, v in p["rubric_weights"].items()
    )

    return f"""You are a DOMAIN-EXPERT REVIEWER walking a course end-to-end to decide whether your team should enroll in it.

## Who you are

**{p['title']}** — {p['background']}

You are NOT the learner. You are the person who has to decide "will this course make my juniors ship production-grade work, or does it wave hands at the hard parts?" You have a finite reputation with your team — if you bless a shallow course, they lose trust in your judgment. So you read every word skeptically.

## The course you're reviewing

- Title: "{course_title}"
- Subject: {course_subject or "(as described in the catalog)"}
- URL: {base_url}/#{course_id}

## Strict RL rules (no cheating — same as the beginner agent)

You drive the course via `mcp__Claude_Preview__preview_*` tools only. You MUST NOT:
- Access `/api/admin/courses/*/raw` (leaks answer keys)
- Read `skills_lab.db`, `backend/*.py`, `backend/courses/*.py`, or any file that exposes grader internals
- `curl` / `POST` directly to grader endpoints — everything flows through the browser
- Read prior `reviews/*` artifacts before forming your opinion

You MAY:
- Open external references (official Anthropic docs, vendor docs) to cross-check technical claims in the course
- Inspect the browser DOM (`preview_inspect`, `preview_eval`) to verify UI widgets render correctly
- Take screenshots (`preview_screenshot`) for evidence

## What to hunt for — persona-specific blind spots

A beginner course CAN pass the Step-1 gate (clear, solvable, feedback works) and STILL FAIL you here because it skips the production reality. Check for:

{blind_spots_md}

## Rubric weights

Your final score is a weighted average of these axes (0-1 each):

{rubric_md}

Your per-axis score is a judgment call based on the course content + your experience. Justify every axis score with 1-2 specific pieces of evidence from the course.

## Streaming artifact

Write + rewrite this file after every notable step so reviewers can `tail -F` it during the run:

    {artifact}

Artifact structure:

```
# Domain-Expert Review — {course_title}
Persona: {p['title']}
Date: YYYY-MM-DD
Pass: {pass_tag}

## Overview
(1-paragraph summary of course shape: module count, exercise types, scope)

## Blind-spot coverage
For EACH of the {len(p['blind_spots_to_hunt'])} hunt items:
  ### Blind spot N — "<paraphrase>"
  - Covered? yes | partial | no
  - Evidence: exact step M.S, quote from briefing or instructions
  - If partial/no: what the course should have covered

## Axis scores
  - technical_accuracy: 0.X
    - evidence: ...
  - production_readiness: 0.X
    - evidence: ...
  - failure_mode_coverage: 0.X
    - evidence: ...
  - tradeoff_articulation: 0.X
    - evidence: ...
  - security_posture: 0.X
    - evidence: ...

## Weighted score
{"  ".join([f"{k} × {v}%" for k, v in p['rubric_weights'].items()])}
TOTAL: 0.XX / 1.00

## Verdict
- ✅ APPROVE (≥ 0.75) — course meets the production bar; I'd enroll my juniors.
- ⚠ CONDITIONAL (0.60-0.74) — solid foundation but must-fix gaps before enrolling.
  List the gaps as labeled "MUST FIX before approval" + "SHOULD FIX but non-blocking".
- ❌ REJECT (< 0.60) — the course teaches shallow patterns that will cause prod incidents or produce engineers who don't know what they don't know.

## One-line executive summary for the Creator team
(What should the next revision of this course add / change? Be specific.)
```

## Tool-budget discipline

Approximate ceiling: **{tool_budget_hint} tool calls**. You can skim faster than the beginner agent — you know what you're looking for. Dedicate more budget to the cross-referencing (opening official docs to verify claims) than to re-solving exercises.

## Minimum breadth

Walk at least {min_steps_to_walk} steps across the course (especially capstone + the blind-spot-relevant ones). You may skim concept-only modules if the blind-spot items are already addressed.

Reply DONE + the artifact path when complete.
"""
