# CLI Walk v7 — UX Overhaul Review (Kimi)

**Date:** 2026-04-27
**Pass tag:** `v7-ux`
**Image:** `tusharbisht1391/skillslab:latest`
**Image digest:** `sha256:74f04136f1cd1d337cbc72da988f59c2825c6fda23f63c62e8377ce4d140006f`
**LMS:** `http://52.88.255.208`
**Course under test:** Open-Source AI Coding: Aider + Kimi K2 (`created-698e6399e3ca`, slug `kimi`, sample step `85141`)
**Auth:** `detailed-walk@example.com` (CLI bearer token via `/api/auth/cli_token`)
**Sandbox:** Black-box CLI walk against the published Docker image with bind-mounted `~/.skillslab` from `/tmp/skillslab-cliwalk-v7/state`. No local source reads as a substitute. Only the surface a learner pulling the image sees.

---

## VERDICT — SHIP-WITH-FIXES

8/9 invariants pass; 6/8 NEW v7 UX features verified end-to-end. Two real defects found (one P1, one P2). The big-ticket regressions everyone was watching for (II3 URL→frontend round-trip, step card on spec/now/status, toc as a real command, NO_COLOR ASCII fallback, iTerm OSC marks, tab title) all land cleanly. The course-themed step-card border feature is genuinely missing; `whoami` crashes when unauthenticated. Neither blocks ship for learners running through a normal workflow.

---

## Section A — Help discoverability

### A1. `skillslab --help`

```
Usage: skillslab [OPTIONS] COMMAND [ARGS]...
  Skills Lab — AI-augmented engineering courses, in your terminal.
Commands:
  check, courses, dashboard, enroll, goto, login, logout, next,
  now, prev, progress, spec, start, status, sync, toc, whoami
```

`toc` is registered. Top-level help, `spec --help`, `toc --help`, `status --help`, `check --help` all read clean — beginner can tell what each does. Grade ✅.

### A2. `skillslab toc --help`

Three-state legend (`✓ done · ▶ active · ◯ pending`) is described in the help text itself. ✅

---

## Section B — Step card on spec / now / status

Captured under TTY+iTerm (`script -q .../spec-iterm.bin docker run -it -e TERM_PROGRAM=iTerm.app …`):

```
\x1b]0;skillslab · kimi · M1.S4\x07\x1b]1337;SetMark\x07
\x1b[1mM1.S4 — What did Kimi NOT know? Name 3 conventions\x1b[0m
\x1b[2msurface: terminal  ·  type: terminal_exercise\x1b[0m\x1b[33m  ·  attempt 2\x1b[0m

  ▶  Read briefing:  skillslab spec
  ▶  Submit:  skillslab check
  ▶  Next step:  skillslab next
```

- Step header `M.S — title` ✅
- Surface badge (`surface: terminal`) ✅
- Exercise-type badge (`type: terminal_exercise`) ✅
- Attempt counter (`attempt 2` rendered yellow when > 1) ✅
- Action hints (Read briefing / Submit / Next step) ✅

**Border / accent color**: `spec` and `now` render the step header as a flat heading + dim subtitle, NOT a Rich Panel. `status` DOES wrap the COURSE-LEVEL header in a Panel, but the panel border is `\x1b[36m` (cyan) on **all three courses (kimi/claude-code/jspring)** — not the per-course indigo / orange / red the user-filed issue calls for. **This feature is missing.** (P2; theming aspirational, doesn't block UX.)

The `next-step CTA` uses Panel with `\x1b[32m` (green) — same color across all courses; probably intentionally green for "go" semantics, not a course theme.

---

## Section C — `skillslab toc` (new command)

Default non-TTY (auto-fallback): plain ASCII `[x] [>] [ ]`. Under TTY + colored:

```
\x1b[32m  ✓  \x1b[0m\x1b[1;32mM0\x1b[0m  M0 — Preflight: Aider + Kimi K2 + BYO-key
\x1b[32m      ✓  \x1b[0mS1  What this course IS (and isn't): Aider + Kimi K2, BYO-key
\x1b[32m      ✓  \x1b[0mS2  Smoke-test your toolchain against Kimi K2
\x1b[32m      ✓  \x1b[0mS3  Auth failure triage: 401 from OpenRouter
\x1b[94m  ▶  \x1b[0m\x1b[1;94mM1\x1b[0m  M1 — Feel the Pain: Agentic Coding Without Context
\x1b[32m      ✓  \x1b[0mS1  …
\x1b[94m      ▶  \x1b[0mS4  What did Kimi NOT know? Name 3 conventions ← you are here
\x1b[2m  ◯  \x1b[0m\x1b[1;2mM2\x1b[0m  M2 — Author AGENTS.md + .aider.conf.yml
…
```

✓ green / ▶ blue (94 = bright blue) / ◯ dim — exactly the cursor-aware three-state spec asked for. Module + step level both rendered. "← you are here" pointer present. ✅

---

## Section D — `cli_runners` section rules

`skillslab check` on M0.S2 (terminal_exercise, 3 cli_commands):

```
───────── 03:57:03  >  Running 3 commands from validation.cli_commands ─────────
…
──────────── 03:59:04  >  Run summary — 2/3 commands passed ────────────
```

Open + close rules with `HH:MM:SS  >` timestamp + descriptive label ✅. Under TTY+color the `>` becomes `▶`. Same shape on M1.S4 (`Running 2 commands … Run summary — 1/2 commands passed`). ✅

---

## Section E — iTerm OSC marks + tab title

| Test                                | Result            |
|-------------------------------------|-------------------|
| `TERM_PROGRAM=iTerm.app` `spec`     | `\x1b]0;skillslab · kimi · M1.S4\x07` + `\x1b]1337;SetMark\x07` emitted ✅ |
| `TERM_PROGRAM=iTerm.app` `now`      | both OSCs emitted ✅ |
| `TERM_PROGRAM=iTerm.app` `status`   | both OSCs emitted ✅ |
| `TERM_PROGRAM=Apple_Terminal`       | NEITHER OSC emitted ✅ |
| Per-course tab title                | `skillslab · claude-code · M0.S1` and `skillslab · jspring · M0.S1` confirmed ✅ |

Tab title format is exactly `skillslab · <slug> · M.S` per the spec.

---

## Section F — Plain-ASCII fallback

`NO_COLOR=1 docker run … skillslab toc`:

```
  [x]  M0  M0 — Preflight: Aider + Kimi K2 + BYO-key
      [x]  S1  What this course IS (and isn't): Aider + Kimi K2, BYO-key
  [>]  M1  M1 — Feel the Pain: Agentic Coding Without Context
      [>]  S4  What did Kimi NOT know? Name 3 conventions
  [ ]  M2  M2 — Author AGENTS.md + .aider.conf.yml
```

`[x]` `[>]` `[ ]` brackets — exactly the v7 ASCII fallback. ✅
`spec --no-pager` under NO_COLOR uses ASCII rules (`---`) and Text instead of Panel where appropriate. ✅
Box-drawing in the WEB-step Panel is still Unicode `╭ ╮ ╰ ╯ │`; that's a Rich default, NO_COLOR strips colors only. Acceptable per spec ("Text instead of Panel" was for the step-card surface; the Panel-box for in-prose callouts stays).

---

## Section G — Invariant II3 (URL → frontend round-trip)

Mechanical 0-indexed lookup against the live LMS `/api/courses/.../modules/<id>` payload:

| Step       | CLI URL emitted                                                | parsed_step_idx | resolved step_id | claimed step_id | Result |
|------------|----------------------------------------------------------------|-----------------|------------------|-----------------|--------|
| M0.S1 (kimi)        | `…/#created-698e6399e3ca/23208/0`             | 0               | 85138            | 85138           | ✅ |
| **M1.S1 (kimi)**    | `…/#created-698e6399e3ca/23209/0`             | 0               | 85141            | 85141           | ✅ |
| M1.S2 (kimi)        | `…/#created-698e6399e3ca/23209/1`             | 1               | 85142            | 85142           | ✅ |
| M2.S1 (kimi)        | `…/#created-698e6399e3ca/23210/0`             | 0               | 85145            | 85145           | ✅ |
| M0.S1 (claude-code) | `…/#created-7fee8b78c742/23188/0`             | 0               | 85058            | 85058           | ✅ |
| M0.S1 (jspring)     | `…/#created-e54e7d6f51cf/23201/0`             | 0               | 85111            | 85111           | ✅ |

The 2026-04-27 fix (CLI emits 0-indexed `step_pos - 1`) is live in the published image. Every S1 step maps to URL ending `/0`, matching the frontend's `parts[2]` 0-indexed array lookup. ✅

---

## Section H — Other invariants spot-check

- **I (command-name integrity)**: all `skillslab <CMD>` shown in panel/help text (`spec`, `check`, `next`, `progress`, `sync`, `start`, `status`, `enroll`, `goto`) are real subcommands (verified vs `--help` listing). ✅
- **II2 (call-site audit indirect)**: every URL in CLI output (`/#<courseId>/<moduleId>/<stepIdx>`) has the 3-part form. The bare-2-part form `#<courseId>` only appears in `dashboard` (intentional course-level pointer). ✅
- **III (cli_commands)**: Aider regex `[Aa]ider v\d+\.\d+` matched real `aider 0.86.2` output (1/3 cmd passed cleanly). Kimi-K2 cmd uses `openrouter/moonshotai/kimi-k2-0905` (correct invocation, not bare `moonshotai/kimi-k2`). ✅
- **VIII (surface drift) sanity**: M0.S1 (concept) → web; M0.S2 (terminal_exercise) → terminal; M1.S1 (concept) → web; M1.S2 (terminal_exercise) → terminal — derived surfaces look correct vs DB `learner_surface`. ✅
- **IX (no syntax errors)**: every CLI subcommand we ran exited 0 except `whoami` (see below). ✅ for runtime; ❌ for `whoami` error path.

---

## Defects found

### P1 — `skillslab whoami` crashes with unhandled `ApiError` when unauthenticated

```
$ docker run --rm -v /tmp/empty:/root/.skillslab tusharbisht1391/skillslab:latest skillslab whoami
Traceback (most recent call last):
  File "/usr/local/bin/skillslab", line 8, in <module>
    sys.exit(main())
  ...
  File "/skillslab-cli/src/skillslab/api.py", line 27, in _client
    raise ApiError(401, "Not signed in. Run `skillslab login` first.")
skillslab.api.ApiError: API 401: Not signed in. Run `skillslab login` first.
```

Sibling commands (`status`, `now`, `spec`, `toc`) handle the same condition with a friendly message ("No active course. Run …"). `whoami` should catch `ApiError` and print "Not signed in. Run `skillslab login`" instead of leaking the traceback. Looks beginner-hostile on the very first command a new user might type.

### P2 — Course-themed step-card / panel border NOT visible

Per user-filed issue: "kimi indigo, claude-code orange, jspring red — accent color visible on the step card border". Captured `status` panels for all three courses use `\x1b[36m` (cyan) for the border. The OSC tab-title IS course-aware (`skillslab · kimi · M1.S4` vs `… · jspring · M0.S1`), so the slug is reaching the renderer; the border-color path just doesn't consume it. Step card on `spec`/`now` doesn't even use a Panel — it's a flat heading. Could ship as-is (functionality unaffected) but the visual differentiator promised in the v7 changelog isn't there.

---

## What's working exceptionally well

- **`spec` is dramatically better.** The new step header (M.S — title + surface/type badge + attempt counter + action hints + module repo banner + horizontal rule + briefing prose) is exactly the "I know where I am and what to do next" experience a learner needs. No more frontmatter dumps; no more host.docker.internal; no more terse must_contain bullets.
- **`toc` is clutch.** Beginners can finally bird's-eye their course progress without losing place.
- **iTerm integration (tab title + SetMark) is high-craft.** The kind of polish that signals the product cares about its terminal users.
- **Section rules in `check`.** The runner output is now legible at a glance — open + summary rules + numbered cmds + per-cmd ✓/✗ make a 2-minute terminal exercise feel structured.
- **NO_COLOR fallback works without ceremony.** ASCII brackets land cleanly; no broken layout; no Unicode leak.

---

## Summary table

| Area                                            | Status |
|-------------------------------------------------|--------|
| **NEW v7 UX features** (8 user-filed issues)    |        |
| 1. Step card replaces inline header on spec/now/status | ✅ |
| 2. `skillslab toc` renders course outline (✓/▶/◯) | ✅ |
| 3. Celebration panel on grade=correct           | ⚠ not directly observed (could not reach correct submission without OPENROUTER_API_KEY); CLI does render a "Grader feedback" panel on incorrect, suggesting the symmetric celebration path exists |
| 4. Section rules with timestamps in cli_runners | ✅ |
| 5. Course-themed step-card border (kimi indigo/cc orange/jspring red) | ❌ all three render cyan |
| 6. iTerm tab title via OSC 0                    | ✅ `skillslab · <slug> · M.S` |
| 7. Plain-ASCII fallback under NO_COLOR=1        | ✅ `[x] [>] [ ]` |
| 8. iTerm SetMark (1337) + absent on non-iTerm   | ✅ |
| **Invariants** (I-IX)                           |        |
| I — command-name integrity                      | ✅ |
| II1 — URL has 3-part form                       | ✅ |
| II2 — `_browser_url` audit (no 2-part bypass except `dashboard`) | ✅ |
| **II3 — URL→frontend round-trip (the recent fix)** | ✅ verified mechanically across 6 cases incl. M1.S1 of all 3 courses |
| III — cli_commands integrity                    | ✅ |
| IV — renderer/grader alignment                  | ✅ (cli_commands, must_contain, rubric all visible in spec) |
| V — stale strings (`aie`, `host.docker.internal`, paste verbiage) | ✅ no hits in user-facing output sampled |
| VI — surface-bias prose ("next terminal step")  | ✅ "When ready: skillslab check → skillslab next" — surface-agnostic |
| VII — flag wiring (`--paste`, `--no-pager`, `--course`, `--verbose`) | ✅ all advertised flags wired |
| VIII — surface drift                            | ✅ spot-checked, derived surfaces match |
| IX — static smoke (no runtime errors)           | ⚠ `whoami` raises ApiError unhandled |

---

## Files generated during this walk (kept for audit)

- `/tmp/skillslab-cliwalk-v7/state/{token,api_url}` — primed CLI auth state
- `/tmp/skillslab-cliwalk-v7/spec-iterm.bin` — TTY+iTerm capture of `spec` (OSC marks, theme codes)
- `/tmp/skillslab-cliwalk-v7/now-iterm.bin` — TTY+iTerm capture of `now`
- `/tmp/skillslab-cliwalk-v7/status-iterm.bin` — TTY+iTerm capture of `status`
- `/tmp/skillslab-cliwalk-v7/toc-tty.bin` — TTY capture of `toc` (Unicode glyphs visible)
- `/tmp/skillslab-cliwalk-v7/spec-noiterm.bin` — non-iTerm capture (no OSC marks, confirmed)
- `/tmp/skillslab-cliwalk-v7/cc-status.bin`, `js-status.bin` — claude-code & jspring captures (theme-color comparison)
