# Skills Lab v2 — AI-first LMS

An AI-first learning management system that produces production-ready engineers
in domains where most courses produce viewers. Courses are LLM-generated end-to-end
through a Creator pipeline; learners experience them on whichever surface fits the
work — browser for interactive widgets, terminal for code-writing.

> **Status (2026-04-25):** v8.7 — surface-aware split (web ↔ terminal), per-step
> verified-facts drift gate (extensible registry), CI regression check landed.
> Three AI-enablement courses ship-ready with zero drift across both surfaces.

---

## Why this exists

Most LMS platforms produce people who watched a tutorial. We're building one that
produces people who can ship the system to production. Two design pillars hold up
that bar:

1. **The Creator pipeline** generates every course. No hand-coded course content
   ever lives in the repo. When the Creator drifts, we tighten its prompt — never
   patch the symptom in DB. ([CLAUDE.md §"All Course Creation & Edits Go Through
   the Creator Dashboard"](CLAUDE.md))

2. **Surface-aware learner experience.** A drag-drop categorization is browser-native;
   `claude` + `pytest` + `git diff` is terminal-native. Forcing both into one surface
   produces a half-baked second-class experience for whichever didn't fit. The system
   declares per-step which surface owns the assignment end-to-end and routes each
   learner to it; the work + grading completes there.

---

## Architecture (high level)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND  (frontend/index.html — single-file SPA, dark theme)              │
│  ├─ Catalog, learner dashboard, progress sync                              │
│  ├─ 16 exercise widget renderers (drag-drop, simulator, mcq, code, …)      │
│  └─ Terminal-native pointer panel (Phase 3) for `learner_surface=terminal` │
└────────────────────────────────────────────────────────────────────────────┘
                       ▲                                  ▲
                  HTTPS│                                  │HTTPS  (bearer token)
                       │                                  │
┌──────────────────────┴──────────────────────────────────┴──────────────────┐
│ BACKEND  (FastAPI + async SQLAlchemy + SQLite)                              │
│                                                                              │
│  /api/auth/*           — sessions + bearer tokens (Phase 1) + my-courses    │
│  /api/courses/*        — public catalog + sanitized step content            │
│  /api/creator/*        — generate / refine / regenerate (LLM-driven)        │
│  /api/exercises/*      — graders for every exercise type                    │
│  /api/progress/*       — completion + last_activity_at (Phase 3)            │
│                                                                              │
│  Creator pipeline (backend/main.py):                                         │
│    Creator-prompt → LLM gen → _is_complete() gates → persist                 │
│                              │                                               │
│                              └─→ Verified-facts DRIFT GATE (registry)        │
│                                  in-scope techs scanned for known-bad        │
│                                  strings; violations force regen with        │
│                                  failure reason captured into next prompt.   │
│                                                                              │
│  Verified-facts registry (backend/verified_facts.py + _data.py):             │
│    Each tech: scope_markers, facts_block, drift_patterns                     │
│    Adding a new tech = one register_tech(...) call. Compounds over time.     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                       ▲                                  ▲
                       │                                  │
            ┌──────────┘                                  └──────────┐
            │                                                         │
┌───────────┴───────────────────┐        ┌────────────────────────────┴───────┐
│ CLI  (cli/, Phase 2-3)        │        │ TOOLS  (tools/)                    │
│  skillslab login / start /    │        │  regression_check.py — CI gate:    │
│  status / spec / check / next │        │    drift scan + smoke shim, exits  │
│  + Docker image bundling:     │        │    non-zero on regression          │
│  python+java+node+claude+aider│        │  (run on every Creator-prompt or   │
│  +mvn+pytest+git              │        │   facts-block change)              │
└────────────────────────────────┘        └────────────────────────────────────┘
```

---

## The two big infrastructure bets

### 1. Surface-aware split (Phases 2 + 3)

Each Step row carries an explicit `learner_surface` enum: `'web' | 'terminal'`.

- **Browser** renders the existing widget for `web` steps; renders a "🖥 TERMINAL-NATIVE STEP"
  pointer panel (with the per-course wrapper command — `kimi-course goto M.S` /
  `aie-course goto M.S` / `jspring-course goto M.S`) for `terminal` steps. Per-course
  panel content drives example tools (claude / aider / mvn) from the course title.

- **CLI** renders the markdown briefing for `terminal` steps; for `web` steps prints
  a copy-pasteable browser deeplink + summary instead of attempting to grade in terminal
  (per Opus review: no `webbrowser.open` — silently fails in Codespaces / SSH / Docker).

- **Cross-surface staleness** signal: `/api/auth/my-courses` returns `last_activity_at`
  (= `MAX(UserProgress.completed_at)` per course); CLI compares to `meta.json` last-active
  timestamp; shows a "browser advanced beyond CLI — run `skillslab sync`" banner when stale.

The principle is "complete + helpful within ONE surface per assignment." Switching
between steps is fine; fragmenting one assignment across surfaces is not.

### 2. Verified-facts registry (extensible drift gate)

[`backend/verified_facts.py`](backend/verified_facts.py) is a **tech registry** —
each tech (Claude Code, Aider, future Kubernetes / Terraform / AWS CLI / …) declares:

- `scope_markers`: substrings that put the tech "in scope" for a course
- `facts_block`: text injected verbatim into the Creator prompt for in-scope courses
- `drift_patterns`: list of `(regex, violation_message, ignore_case)` tuples scanned
  over generated content to catch known-bad strings (with negation-aware matching —
  "don't use X" is pedagogically correct and ignored)

When the LLM Creator drifts past the injected facts (it does, ~20-30% of the time
on subtle cases), the drift gate in `_is_complete()` rejects the generation, captures
the violations into `_last_invariant_reason`, and forces a retry with the EXACT
failures fed back to the LLM.

**Adding a new tech is one `register_tech(...)` call** in
[`backend/verified_facts_data.py`](backend/verified_facts_data.py). The gate
+ Creator prompt + CI all pick it up automatically. Every drift caught in production
becomes a new pattern entry; the registry compounds over time.

[`tools/regression_check.py`](tools/regression_check.py) runs the registry-driven
drift scan over every course in the catalog + drives the CLI smoke shim across all
3 AI-enablement courses; exits non-zero on regression. Wire into CI on every
Creator-prompt or facts-block change.

---

## The CLI runnable (`skillslab`)

A learner walking through an AI-augmented engineering course (Claude Code AIE,
Aider+Kimi, Java Spring Boot) does the entire loop in their terminal:

```bash
docker compose run --rm skillslab          # build the toolchain image once
skillslab login                             # bearer-token auth (no key transit)
skillslab start aie                         # download all 29 steps as markdown
skillslab status                            # cursor + per-course terminal/web breakdown
skillslab spec                              # rich-rendered briefing
# ...edit code, run pytest / mvn / git diff with claude or aider...
skillslab check                             # grade + advance, verdict in terminal
```

State is files: `~/.skillslab/<course-slug>/{meta.json, progress.json, steps/M0.S1-*.md}`.
Grep-able, hand-editable, offline-readable.

The Docker image carries Python 3.11, Java 17, Node 20, Maven 3.9, claude CLI,
aider, pytest, git — one image, every AIE/Kimi/jspring tool inside. See
[`cli/README.md`](cli/README.md) and [`cli/Dockerfile`](cli/Dockerfile).

A `tests/smoke_terminal.py` shim drives the real `skillslab` binary across every
step of every course as a subprocess; flags any traceback or non-zero exit. 85/85
green at v8.7.

---

## Course catalog (current)

| Course | ID | CLI-eligible | Status |
|---|---|---|---|
| AI-Augmented Engineering: Claude Code | `created-7fee8b78c742` | ✅ | 0 drift (v8.7) |
| Open-Source AI Coding: Kimi+Aider | `created-698e6399e3ca` | ✅ | 0 drift (v8.7) |
| Java + Spring Boot Claude Code | `created-e54e7d6f51cf` | ✅ | 0 drift (v8.7) |
| Plus 4,600+ generated courses across many domains | (browser-only) | — | varies |

Per-course CLI eligibility lives in [`backend/course_assets.py`](backend/course_assets.py).

---

## Running locally

```bash
# Backend
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001

# Open http://localhost:8001 → catalog → pick a course
# Or via CLI:
docker compose -f cli/docker-compose.yml run --rm skillslab
```

Environment:
- `ANTHROPIC_API_KEY` — Creator + Clicky LLM calls
- `ANTHROPIC_BUDGET_USD` (default 250, currently 400) — hard cap; falls back to mocks when exhausted
- `SKILLSLAB_API_URL` (default `http://localhost:8001`) — for the CLI

---

## CI regression check

```bash
.venv/bin/python -m tools.regression_check
```

Walks every course's modules+steps, runs the registry-driven drift scan, runs the
CLI smoke shim. Exits 1 on drift OR smoke regression — wire as a required PR check
on changes to `backend/main.py`, `backend/verified_facts*.py`, `frontend/index.html`,
`cli/**`.

`--skip-drift` / `--skip-smoke` / `--courses kimi,aie` / `--json` for restricted runs.

---

## Architecture decision log (recent)

The detailed history (with rationale, buddy-Opus reviews, expert findings, and
rollback considerations) lives in [CLAUDE.md](CLAUDE.md) — that file is the
authoritative engineering log. Highlights:

- **v8.7 (2026-04-25)** — Verified-facts registry + drift gate; surface-aware
  split (web ↔ terminal); 17-step regen sweep cleaned all known drift; CI gate
  ships non-zero on regression.
- **v8.6.x (2026-04-22→24)** — Per-language Docker runtime (Python/JS/TS/Go);
  zero-code course mode (PMs/CSMs/legal); BYO-key terminal exercise type;
  course-asset registry for GHA-graded capstones.
- **v8.5 (2026-04-23)** — Execution-is-ground-truth (delete pattern-matching
  gates when the runtime can answer); harness-closure invariant; structured
  test output via JUnit XML / Jest JSON / Go -json.
- **Pre-v8** — exercise-type taxonomy (16 types), adaptive_roleplay engine,
  incident_console scripted simulator, voice_mock_interview, surface-aware
  validators, dark-theme sanitizer, source-grounded generation.

---

## Repository layout

```
skills-lab-v2/
├── backend/
│   ├── main.py                      # Creator pipeline + endpoints (10K+ lines)
│   ├── verified_facts.py            # Tech registry (Phase v8.7)
│   ├── verified_facts_data.py       # Registered techs (claude_code, aider, …)
│   ├── learner_surface.py           # Surface classifier (Phase 2)
│   ├── ontology.py                  # Exercise-type contracts
│   ├── course_assets.py             # Per-course external assets (repos + MCPs)
│   ├── per_step.py                  # Per-step regen logic
│   ├── auth.py                      # Sessions + bearer tokens
│   ├── database.py                  # SQLAlchemy models
│   └── schemas.py                   # Pydantic response models
├── frontend/
│   ├── index.html                   # SPA — every widget renderer + dispatch
│   └── templates/                   # Per-exercise-type rendering templates
├── cli/                             # `skillslab` Python CLI (Phase 2)
│   ├── src/skillslab/{cli,api,state,render,check,surface}.py
│   ├── tests/                       # 59 unit tests + smoke_terminal.py
│   ├── Dockerfile                   # Toolchain image
│   ├── docker-compose.yml
│   └── README.md
├── tools/
│   └── regression_check.py          # CI gate (drift + smoke)
├── scripts/
│   ├── backfill_learner_surface.py  # One-shot heuristic backfill (Phase 2)
│   └── …                            # Per-course / per-batch utilities
├── reviews/                         # Per-pass review artifacts (beginner + expert)
└── CLAUDE.md                        # Engineering log + decision rationale
```

---

## License

(Internal — terms TBD.)
