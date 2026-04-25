# skillslab — AI-augmented engineering, in your terminal

A CLI that turns a Skills Lab course into a terminal workflow. Learners
sign in, pull the course locally, edit code in their own editor, run
`skillslab check` to grade + advance — never opens the browser. Designed
for the BYO-key courses (Claude Code AIE, Kimi+Aider, Java/Spring Boot
jspring) where the learner already lives in the terminal.

## Why a CLI

Browser tabs are a state graveyard. AI-augmented engineering courses
specifically expect the learner to be IN their terminal — running
`claude`, `aider`, `mvn test`, `git diff` — not toggling between a
tutorial pane and a terminal. The CLI collapses the loop:

```
edit code  →  skillslab check  →  pass + auto-advance  →  skillslab spec
```

Submission and verdict both render in the terminal. The dashboard
becomes optional (mainly for catalog browsing + creator analytics).

## What it ships with

The Docker image (see `Dockerfile`) carries the full toolchain so a
learner can run any of the 3 AI-enablement courses without installing
JDK / Node / aider / claude-code on their host:

| Tool | Version | Why |
|---|---|---|
| Python | 3.11 | CLI runtime + pytest |
| Java + Maven | 21 + 3.9 | jspring course (mvn test, mvn package) |
| Node | 20 | claude CLI (`@anthropic-ai/claude-code` npm) |
| claude | latest | AIE course's BYO-key primary tool |
| aider | 0.85+ | Kimi course's BYO-key primary tool |
| pytest | 8.3+ | Python-side unit tests |
| git | latest | every course |

## Install

### Native (Python ≥ 3.11)

```bash
pip install -e cli/                  # editable from this repo
skillslab --version
```

### Docker (recommended — no host deps)

```bash
cd cli/
docker compose build                 # ~5 minutes first time, cached after
docker compose run --rm skillslab    # drops you into bash inside /work
```

Mounts `~/.skillslab/` so token + cursor + step files survive container
restarts; passes through `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` /
`GITHUB_TOKEN` from the host shell.

## Quickstart

```bash
# 1. Sign in (one-time per machine — bearer token cached at ~/.skillslab/token)
skillslab login

# 2. List + start a course (downloads every step's content as markdown)
skillslab courses
skillslab start aie                  # Claude Code AIE
skillslab start kimi                 # Aider + Kimi (open-source path)
skillslab start jspring              # Java + Spring Boot

# 3. Where am I?
skillslab status
#   ▸ M0.S0 — Setup + first claude /login
#     type: terminal_exercise
#     file: ~/.skillslab/aie/steps/M0.S0-setup-and-first-claude-login.md

# 4. Read the briefing (full markdown of the step)
skillslab spec

# 5. Do the work in your editor, then grade
cd /path/to/your/course-repo        # or whichever cwd the step expects
skillslab check                      # captures git diff + acceptance command
                                     # output, posts to grader, renders verdict
```

## How `skillslab check` works

The check runner has two paths, dispatched per step:

1. **Native cli_check** (deterministic, local, free) — when the step's
   `validation.cli_check` declares one of:
   - `pytest` — runs the tests, exit 0 = pass
   - `command_exit_zero` — runs an arbitrary shell command
   - `file_exists` — checks a file is present
   - `paste_contains` — required tokens in the submission
   - `git_diff_contains` — required tokens in `git diff`
   - `gha_workflow_check` — learner pastes a GitHub Actions run URL,
     CLI hits the public GitHub API directly
   - `claude_rubric` / `aider_rubric` / `local_rubric` — runs the LLM
     rubric grader using the learner's own `claude` / `aider` (BYO key)

2. **LMS bridge (default for rubric-only steps)** — captures
   `git diff` + `.skillslab.yml` `acceptance_command` output + any
   `paste_includes` files + the learner's stdin/`--paste` text, POSTs
   to `/api/exercises/validate`, renders the verdict (score + feedback)
   in the terminal as a Rich Panel. Same grader the browser uses;
   learner never sees the browser.

## The `.skillslab.yml` contract

A course-repo's per-module branch typically ships a `.skillslab.yml`
at the repo root. The CLI reads it on every `skillslab check`:

```yaml
# .skillslab.yml — example for a Java module
acceptance_command: mvn -q test
paste_includes:
  - src/main/java/com/example/UserService.java
  - src/test/java/com/example/UserServiceTest.java
git_diff: yes              # 'yes' | 'no' | 'staged'
rubric_model: sonnet       # optional override for claude --model
```

The `acceptance_command` runs first; its stdout/stderr/exit are folded
into the submission so the rubric grader (or `paste_contains`) can see
test output. `paste_includes` appends specific files verbatim — useful
when the diff is small but the grader needs to see surrounding context.

## Per-course wrappers

Each course gets a thin wrapper script so the namespace stays clean:

```bash
aie-course status         # == skillslab --course=aie status
kimi-course check         # == skillslab --course=kimi check
jspring-course spec       # == skillslab --course=jspring spec
```

These are registered in `pyproject.toml [project.scripts]`.

## State layout

Everything is files. Inspect, grep, hand-edit if you need to:

```
~/.skillslab/
├── token                       # bearer token (chmod 0600)
├── api_url                     # which LMS server
└── aie/                        # one dir per course-slug
    ├── meta.json               # course_id, modules, cursor pointer
    ├── progress.json           # mirror of /api/auth/my-courses
    └── steps/
        ├── M0.S0-setup-and-first-claude-login.md
        ├── M0.S1-smoke-test-claude-cli.md
        ├── M1.S0-explore-the-repo.md
        └── ...
```

Each step is a self-contained markdown file with:
- YAML front-matter (step_id, exercise_type, title, course, module)
- The full briefing (concept content rendered from the LMS HTML)
- A "Starter / Reference" section if the step has a code starter
- An "Acceptance" section showing the rubric / must_contain / cli_check spec
- Footer pointing back to `skillslab check` / `skillslab next`

## Course-author guide — adding `.skillslab.yml` + PRD + SPEC to a module

See `examples/` in this directory:

- `examples/PRD.md` — explains WHAT the learner is building
- `examples/SPEC.md` — defines the technical contract (interfaces, tests, acceptance)
- `examples/.skillslab.yml` — declares the acceptance_command + paste_includes

Each module branch in a course-repo (e.g. `module-1-starter`,
`module-2-refactor`) should ship these three files at the root, plus
the planted gaps the learner fills in. The CLI's `start` command writes
the per-step markdown briefings; the course-repo provides the actual
code surface the learner edits.

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `SKILLSLAB_API_URL` | `http://localhost:8001` | LMS server |
| `SKILLSLAB_HOME` | `~/.skillslab` | State dir |
| `SKILLSLAB_BRIDGE_VALIDATE` | unset | (advanced) force LMS bridge mode |
| `ANTHROPIC_API_KEY` | unset | claude CLI auth |
| `OPENROUTER_API_KEY` | unset | aider auth (OpenRouter route) |
| `GITHUB_TOKEN` / `GH_TOKEN` | unset | GHA-check rate limit |

## Hacking

```bash
pip install -e cli/[dev]             # if a dev extra is added later
python3 -m py_compile cli/src/skillslab/*.py
skillslab --help
```

The codebase is intentionally small (~1500 LoC across 6 files):

| File | Purpose |
|---|---|
| `cli.py` | Click dispatcher; all subcommands |
| `state.py` | Filesystem layout, token, course meta |
| `api.py` | Thin httpx client for `/api/*` |
| `render.py` | LMS HTML → terminal markdown |
| `check.py` | Acceptance check dispatcher (native + bridge) |
| `__init__.py` | Version |

## License

Same license as the parent skills-lab-v2 repo.
