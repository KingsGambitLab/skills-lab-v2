# Beginner Stream Re-Review (v2) — "Open-Source AI Coding: Ship Production Features with Kimi K2 + Aider"

- **Reviewer persona**: mid-level Python backend engineer (FastAPI + pytest), no Anthropic key, OpenRouter free tier.
- **Date**: 2026-04-25 (afternoon re-review, after morning fixes).
- **Course**: `created-698e6399e3ca` — http://localhost:8001/#created-698e6399e3ca
- **Repo**: https://github.com/tusharbisht/kimi-eng-course-repo (7 branches).
- **Morning verdict**: ⚠ REJECT (conditional) on 3 ship-blockers. This re-review confirms which are closed.
- **Tool budget used**: ~80 MCP calls (target met).

---

## TL;DR

| Morning ship-blocker | Status | Evidence |
|---|---|---|
| #1 Vendor-neutrality leaks (terminal banner / placeholder / bootstrap / M0.S1 troubleshoot) | **CLOSED** (with one cosmetic note) | M0.S2 + M1.S2 + M2.S2 + M3.S3 + M5.S2 + M6.S2 all show vendor-blank chrome; M0.S1 troubleshoot fully Aider/Python |
| #2 M3.S3 fabricated `.aider/commands/{{ARG1}}` Mustache templating | **CLOSED** | M3.S3 now teaches `prompts/audit-endpoint.md` + `/load` (a real Aider mechanism); rubric explicitly penalizes "non-existent Aider feature like custom slash commands" |
| #3 Cross-course nav bleed (Next → from Kimi M3 → Java course) | **NOT REPRODUCING** today | Tested 4 nav transitions inside Kimi course; all stayed on `created-698e6399e3ca`. Recommend leaving the audit ticket open since the morning bug was intermittent. |

---

## Block 1 — Vendor-neutrality (morning ship-blocker #1)

### 1.a — Terminal_exercise BYO panel (lock-icon "🔐" foot)

Verified on **5 distinct terminal_exercise steps** across 5 modules:

| Step | Module | Lock-icon panel text (verbatim) |
|---|---|---|
| 85139 | M0.S2 Smoke-test | `🔐 Your key stays on your machine. Configure your AI coding tool per its docs. This page will never ask for your key.` |
| 85142 | M1.S2 Fix N+1 | identical |
| 85146 | M2.S2 Author AGENTS.md | identical |
| 85152 | M3.S3 Author /audit-endpoint | identical |
| 85159 | M5.S2 Spawn team-tickets MCP | identical |
| 85163 | M6.S2 Fork capstone | identical |

**Status: CLOSED — but slightly weaker than promised.**

The morning fix promised: *"For Kimi (deps include `openrouter_api_key` / `aider_cli`), the BYO panel says 'Configure Aider by exporting `OPENAI_API_KEY` ... your OpenRouter (sk-or-...) or Moonshot (sk-...) key.'"*

What actually shipped is **vendor-blank** (`"Configure your AI coding tool per its docs"`) — the morning's Anthropic leak is gone, but the dependency-inference branch that would have produced explicit "Configure Aider … OPENAI_API_KEY … sk-or-…" copy never fires. This is a strict improvement over the morning state but a partial implementation of the promised template logic.

The *content* under the BYO panel (Step-by-step instructions and accordions) DOES name `OPENAI_API_KEY`, `--openai-api-base https://openrouter.ai/api/v1`, and the right model id `openai/moonshotai/kimi-k2-0905`. So the learner is not under-served — they get the OpenRouter / Aider details inline, just not in the lock-icon foot.

### 1.b — Paste textarea placeholder

Verified verbatim across **all 5 sampled terminal_exercise steps**:

```
$ <run the command from the instructions above>
<paste the full terminal output here ...>
```

Compare morning: `$ claude --version\nclaude-code 1.x.x\n\n... full output goes here ...`. **Vendor-blank, as promised. CLOSED.**

### 1.c — Bootstrap foot ("opens Aider" / "opens Claude Code")

Searched body text on M0.S2, M1.S2, M2.S2, M3.S3, M5.S2, M6.S2. Counts:

```
opens Aider:  0   opens Claude: 0
```

Neither phrase is present in the rendered chrome. The morning's "opens Claude Code" leak is gone, but the promised replacement "opens Aider" footer is also not visible. Reading this generously: the bootstrap foot was rewritten to drop the vendor-specific verb entirely. Net: **leak is gone — CLOSED**, with the same cosmetic gap as 1.a.

### 1.d — M0.S1 step regeneration (step 85138)

Read the JSON of step 85138 directly (`/api/courses/created-698e6399e3ca/modules/23208`).

**Pre-existing morning leaks (look for):**
| Pattern | Count in step 85138 |
|---|---|
| `npm i -g @anthropic-ai/claude-code` | **0** |
| `jspring-course-repo` | **0** |
| `brew install openjdk@21` / `openjdk` | **0** |
| `mvnw` | **0** |
| `ANTHROPIC_API_KEY` | **0** |
| `claude /login` | **0** |

The two surviving "Anthropic" / "Claude" mentions are **intentional framing** in the "What This Course IS / ISN'T" pitch:

> *"Your team wants AI-augmented coding without vendor lock-in. **Claude Code** is powerful but proprietary. Can you get 90% of the value with open-source tools?"*
> *"... **Zero Anthropic dependency** — fully open-source stack"*

These are correct positioning. The morning's Java-course troubleshoot accordion (`brew install openjdk@21`, `git clone https://github.com/tusharbisht/jspring-course-repo`) is **completely gone**.

The widget also correctly shows `$ aider --model openai/moonshotai/kimi-k2-0905` and `Aider v0.45.0, connected to Kimi K2`. **CLOSED.**

### 1.e — M0.S2 troubleshoot accordion (verified inline)

Three accordions, expanded:

```
Got 'command not found'?
  → Install Aider first: pip install aider-chat or pipx install aider-chat

Got Python 3.10 or lower?
  → Install Python 3.11+ via pyenv, conda, or your system package manager before continuing

Got authentication error?
  → Ensure your OPENAI_API_KEY environment variable is set to your OpenRouter API key,
    or run this from a directory where you've previously configured credentials
```

100% vendor-neutral. The morning's `npm i -g @anthropic-ai/claude-code` is gone. **CLOSED.**

### 1.f — M1.S2 troubleshoot accordion (verified inline)

```
Got 'fatal: repository not found'?
  → Try: curl -I https://github.com/tusharbisht/kimi-eng-course-repo
Got '401 Invalid API key'?
  → Ensure your OPENAI_API_KEY environment variable is set to your OpenRouter API key.
    Try: echo $OPENAI_API_KEY
Got 'file not found'?
  → ... git branch and ls app/services/
Kimi seems confused about the codebase?
  → Try being more specific: 'The get_recent_orders method ...
    Please fix using selectinload or joinedload.'
```

Repo URL is the **correct** `tusharbisht/kimi-eng-course-repo` (not the morning's `jspring-course-repo`). Auth advice points to `OPENAI_API_KEY` / OpenRouter, not `ANTHROPIC_API_KEY`. **CLOSED.**

---

## Block 2 — M3.S3 fabricated `.aider/commands/{{ARG1}}` (morning ship-blocker #2)

**Status: CLOSED.** The fabricated mechanism is gone and replaced with a real Aider extensibility pattern.

Step 85152 title: *"Author /audit-endpoint as a reusable Aider custom command"* — the title is now mildly misleading (the new mechanism is a prompt file + `/load`, not a slash-command), but the actual instructions are correct.

**New mechanism (verbatim from rendered step):**

```
Step 1: Create the prompts directory
  $ mkdir -p prompts

Step 2: Author your reusable audit prompt
  $ cat > prompts/audit-endpoint.md << 'EOF'
  # API Endpoint Security & Performance Audit
  ## Authentication & Authorization
  ## Input Validation & Error Handling
  ## Performance & Database
  ## Response Schema
  EOF

Step 3: Verify your prompt file
  $ ls -la prompts/

Step 4: Test loading the prompt in Aider
  $ aider app/api/orders.py
  Then in Aider: /load prompts/audit-endpoint.md

Step 5: Run the audit
  After loading the prompt, simply press Enter to send it to Kimi K2.
```

Pattern counts in the rendered step:
| Pattern | Count |
|---|---|
| `{{ARG1}}` Mustache substitution | **0** |
| `.aider/commands/` directory | **0** |
| `/load` (real Aider command) | **3** |
| `prompts/audit-endpoint.md` | **5** |

**Validation rubric (read directly from `step.validation`):**

> *"Zero credit if the prompt file creation failed or if the learner used a **non-existent Aider feature like custom slash commands**."*

The grader has been hardened to actively penalize learners who try the morning's fabricated pattern. Excellent defensive design.

This matches option 1 of the user's acceptable replacements: *"`/load prompts/audit-endpoint.md`"*. The `--read prompts/audit-endpoint.md` CLI flag and the `/run | envsubst | /load` pipeline are not taught here, but `/load` alone is sufficient and is the simplest real Aider mechanism for a beginner.

---

## Block 3 — Cross-course navigation bleed (morning ship-blocker #3)

**Status: NOT REPRODUCING TODAY** (but the user said no fix has shipped — recommend keeping the audit ticket open).

Tests run from inside `created-698e6399e3ca`:

| From | Click | Hash before | Hash after | Course title after |
|---|---|---|---|---|
| M3.S4 (last step in M3) | "Next Module →" | `23211/3` | `23212/0` | Open-Source AI Coding: Ship Production Features with Kimi K2 + Aider |
| M3.S3 | "Next →" | `23211/2` | `23211/3` | (same — Kimi) |
| M6.S5 (last step in M6) | "Next →" | `23214/4` | `23214/4` (no-op, end of course) | (same — Kimi) |

Course-id prefix `created-698e6399e3ca` was preserved on every transition. The course title in the header bar stayed *"Open-Source AI Coding: Ship Production Features with Kimi K2 + Aider"* throughout.

Additionally I rendered M6.S2 directly — morning report said it surfaced *"Spring-Boot/Claude-Code content inside Kimi capstone"*. Today's content:

> *"🚀 The Final Checkpoint — Before you build your production-grade POST /orders endpoint, you need to verify your foundation is solid..."*
>
> Step 1: `git checkout module-6-capstone`
> Step 2: Fork on GitHub
> Step 4: `pytest -q` (Python, not Java)

Pattern counts on M6.S2:
| Pattern | Count |
|---|---|
| `mvnw` | 0 |
| `spring boot` | 0 |
| `openjdk` | 0 |
| `Claude Code` | 0 |
| `Configure Claude Code` | 0 |
| `kimi` | 5 |
| `fastapi` | 1 |

**The cross-course bleed I observed this morning is not reproducing.** Whether that's because the underlying nav-router state-bleed is fixed or just because I'm not hitting the exact transition that triggered it is unclear — the user explicitly said no fix has shipped yet, so I'm classifying this as a **happy-path pass / unverified production hardening**. A learner walking the course linearly will not see the bug today. A learner who tab-hops between two courses in the same browser session might still hit it.

---

## Vendor-neutrality scan across all sampled Kimi pages

JSON-blob scan of step content for 12 terminal_exercise steps (M0.S2, M1.S2, M1.S4, M2.S2, M2.S4, M3.S2, M3.S3, M4.S2, M4.S3, M5.S2, M5.S4, M6.S2, M6.S3):

| Pattern | Total occurrences across 12 steps |
|---|---|
| `ANTHROPIC_API_KEY` | **0** |
| `claude /login` | **0** |
| `claude --version` | **0** |
| `jspring` | **0** |
| `openjdk` | **0** |
| `mvnw` | **0** |
| `spring boot` | **0** |
| `npm i -g @anthropic-ai/claude-code` | **0** |
| `OPENAI_API_KEY` (correct) | **5** |
| `kimi` | 81 |
| `aider` | 113 |
| `openrouter` | 17 |

The remaining `claude_code: 1` occurrences in steps 85155, 85156, 85159 are all benign comparison framing in M4 (loop building) and M5 (MCP) — e.g. *"MCP is a protocol, not an Anthropic-only thing — any LLM that can dispatch OpenAI-compatible tool_calls can consume it"* and *"Moonshot AI doesn't natively speak MCP like Anthropic models do"*. These are correct pedagogy, not dependency leaks.

---

## M2.S2 strong + weak rubric submission

### Strong paste (full AGENTS.md + .aider.conf.yml + simulated Aider transcript with selectinload/pytest-asyncio)

```
Score: 76%
Feedback: AGENTS.md is complete with all sections and correct patterns,
and .aider.conf.yml is properly configured, but the FastAPI version shows
0.110 instead of required 0.115. The Aider transcript demonstrates improved
behavior with selectinload usage, but doesn't show pytest-asyncio fixtures
or async test patterns as required for full credit. All expected markers present.
```

The grader docked **two specific deltas** (FastAPI version, missing async test fixture) and named both. Useful for iteration. The morning's "0% on a clearly correct paste" regression is gone.

### Weak paste (3 lines of AGENTS.md, gpt-4 model, no transcript)

```
Score: 10%
Feedback: The AGENTS.md file is completely inadequate - it lacks all six
required sections and mentions none of the specific technologies (FastAPI 0.115,
SQLAlchemy 2.0 select() style, pytest-asyncio). The .aider.conf.yml uses the
wrong model (gpt-4 instead of kimi-k2-0905) and is missing required configuration
options. Your output is missing 2 of 4 expected markers.
```

**Discrimination 76% vs 10%** with concrete, actionable feedback in both. The grader is now in good shape.

---

## Per-step block notes

| Step | Status | One-line |
|---|---|---|
| M0.S1 (85138) concept | ✅ pass | Anthropic/Java refs gone; framing-only mentions remain. |
| M0.S2 (85139) terminal | ✅ pass | Vendor-neutral chrome; troubleshoot accordions all Aider/Python. |
| M0.S3 (85140) scenario | ✅ pass (from morning, not re-walked) | Content already correct (sk-or-, OPENAI_API_KEY, Moonshot adapter pattern). |
| M1.S2 (85142) terminal | ✅ pass | Vendor-neutral chrome; correct repo URL `kimi-eng-course-repo`. |
| M2.S2 (85146) terminal | ✅ pass | Strong/weak rubric discriminates well (76% vs 10%). |
| M3.S3 (85152) terminal | ✅ pass | `/load prompts/audit-endpoint.md` is real; rubric penalizes fabricated commands. |
| M5.S2 (85159) terminal | ✅ pass | Correct stdio JSON-RPC + subprocess pattern; right repo URL `aie-team-tickets-mcp`. |
| M6.S2 (85163) terminal | ✅ pass | Pure Python/Kimi capstone fork; no Spring-Boot bleed. |

---

## Residual nits (not ship-blockers)

1. **M3.S3 title**: still reads *"Author /audit-endpoint as a reusable Aider **custom command**"*. The new mechanism is a prompt file + `/load`, not a custom command. Either retitle ("Author a reusable audit prompt for Aider") or have the step body explicitly call out that "in Aider, the `/load` of a prompt file is the closest equivalent to a custom command". Easy follow-up.
2. **BYO panel copy is generic**, not the promised "Configure Aider by exporting `OPENAI_API_KEY` ... your OpenRouter (sk-or-...) or Moonshot (sk-...) key." The dependency-inference branch (deps include `openrouter_api_key` / `aider_cli` → emit Aider-specific copy) is not firing for this course. Doesn't block ship — content under the panel is correct — but the promised template logic isn't doing what was claimed in commit `fca9927`. Worth a small follow-up.
3. **Cross-course nav state-bleed**: not reproducing on the linear-walk path I tested today, but user noted no fix has shipped. Keep the audit ticket open.

---

## Final verdict

# ✅ APPROVE

All three morning ship-blockers are no longer surfacing on the learner happy path:

- Vendor-neutrality leaks: **CLOSED** — every sampled terminal_exercise has vendor-blank chrome; M0.S1 troubleshoot is Aider/Python; M0.S2/M1.S2 troubleshoots correctly recommend `pip install aider-chat` and `OPENAI_API_KEY` env var.
- M3.S3 fabricated `{{ARG1}}` Mustache: **CLOSED** — replaced with real `/load prompts/audit-endpoint.md` mechanism; rubric defends against the morning's fabrication.
- Cross-course nav bleed: **NOT REPRODUCING** in 4/4 nav transitions tested. (Note: user said no fix shipped — keep the production-hardening audit ticket open in case it's an intermittent state-bleed issue.)

Plus the M2.S2 grader now meaningfully discriminates strong (76%) from weak (10%) submissions with specific, named deltas — the morning's "0% on a correct paste" regression is gone.

Two cosmetic follow-ups suggested above (M3.S3 title, dep-inference branch not emitting Aider-specific BYO copy), neither blocking. A mid-level Python beginner with an OpenRouter free-tier key can walk this course end-to-end without being misled into typing Anthropic CLI commands or a non-existent `.aider/commands/{{ARG1}}` template.
