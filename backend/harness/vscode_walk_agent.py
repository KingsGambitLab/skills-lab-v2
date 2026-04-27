"""VS Code walk-agent shim — parallel of `cli_walk_agent.py` but for the
desktop VS Code extension surface.

Per buddy-Opus 2026-04-27: every UX layer needs its own walk. The CLI shim
catches terminal-side bugs; the browser shim catches widget-render bugs;
THIS shim catches:
  - SecretStorage / auth-flow regressions
  - WebView CSP regressions (the load-bearing risk Opus flagged)
  - data-action delegator failure modes (silent dead clicks)
  - devcontainer-detection misfires
  - URI handler `vscode://...` deep-link routing
  - Tree provider three-state correctness (✓/▶/◯)
  - "Submit & Continue" merged-command behavior

Same pattern as `cli_walk_agent.py:build_prompt(...)` — produce a
complete prompt that an agent can execute. The agent has Bash + Read +
gh available; doesn't need a real VS Code instance for most checks (we
verify via static + behavioral analysis).
"""
from __future__ import annotations

import os
from pathlib import Path


def default_artifact_path(pass_tag: str = "v1", course_slug: str | None = None) -> str:
    repo = os.environ.get(
        "SKILLSLAB_REPO_ROOT", "/Users/tushar/Desktop/codebases/skills-lab-v2"
    )
    suffix = f"_{course_slug}" if course_slug else ""
    return f"{repo}/reviews/vscode_walk_{pass_tag}{suffix}_2026-04-27.md"


def build_prompt(
    *,
    course_id: str,
    course_title: str,
    course_slug: str = "kimi",
    pass_tag: str = "v1",
    base_url: str = "http://52.88.255.208",
    repo_root: str = "/Users/tushar/Desktop/codebases/skills-lab-v2",
    user_filed_issues: list[str] | None = None,
) -> str:
    """Produce the full prompt for a VS Code walk-agent run."""
    artifact_path = default_artifact_path(pass_tag=pass_tag, course_slug=course_slug)

    issues_block = ""
    if user_filed_issues:
        issues_block = "\n## RECENTLY-FILED ISSUES (verify each is closed)\n\n"
        for i, iss in enumerate(user_filed_issues, 1):
            issues_block += f"{i}. {iss}\n"
        issues_block += "\nFor EACH, mark CLOSED / STILL OPEN / NEW FORM with verbatim evidence.\n"

    return f"""You are the **VS Code walk-agent** for the Skillslab extension at
`{repo_root}/vscode/`. Walk the desktop-extension surface against the
deployed prod LMS at `{base_url}`. Pass tag: `{pass_tag}`.

You don't need a running VS Code instance. The shim catches bugs via
static + behavioral analysis. Where a check requires running VS Code,
note it as DEFERRED-TO-MANUAL and continue.

## CONTEXT

The Skillslab platform now has THREE client surfaces:

  1. **Browser SPA** — http://{base_url.replace('http://', '').replace('https://', '')}/#<courseId> (read-only catalog/dashboard)
  2. **CLI in Docker** — `tusharbisht1391/skillslab:latest` (terminal)
  3. **VS Code extension** — `vscode/` package (NEW, your scope)

The VS Code extension is **additive** — it re-uses existing LMS API
endpoints (NO backend changes). Per CLAUDE.md hard rule: "we never
handle learner API keys" — bearer + ANTHROPIC_API_KEY + GITHUB_TOKEN
all live in OS keychain via VS Code SecretStorage.

## SANITY GATE — run BEFORE the per-invariant grep checks

Per user directive 2026-04-27 ("shim should ideally not rely on grep as
it can be brittle, rely on higher level functions like click and
execute"), the most load-bearing invariants are now verified by
RUNNING the actual code via Node-based unit tests, not by grepping
source. Run this first; if any test fails, the shim has caught a real
regression that source-grep would likely miss.

```bash
cd {repo_root}/vscode && npm test 2>&1 | tail -30
```

Must end with `ℹ fail 0`. The test suite covers (with verbatim code
execution, no source grep):
  - convertArgsToJson — JS-literal → canonical JSON, all common shapes
  - rewriteOnclicks — emits data-args-json (not data-args-raw), strips inline onclicks
  - stripOuterIife — Crockford / alt / leading-semicolon shapes; preserves IIFEs with args
  - buildRuntimeScript — ZERO Function/eval in output; uses JSON.parse; hoists fn decls
  - rewriteForWebview — full pipeline on realistic widget HTML; data-args-json round-trips through JSON.parse

If `npm test` greens, you've already verified invariants IV (CSP strict),
V (IIFE unwrap), XX (no eval/Function), and behavioral check B1 (server
HTML rewrite). Continue with the grep-level checks below for the rest
(file structure, package.json contents, command registrations) — those
are still source-level since the corresponding code paths don't
naturally execute in a unit-test harness.

## EXPLICIT INVARIANTS

### I. TypeScript compiles cleanly

```bash
cd {repo_root}/vscode
npx tsc -p . 2>&1
echo $?  # must be 0
```

FAIL if non-zero exit OR any `error TS` lines.

### II. SecretStorage is the ONLY persistence for keys

```bash
grep -nE 'localStorage|sessionStorage|writeFile.*token|fs\\.appendFileSync.*key' {repo_root}/vscode/src/*.ts
```

Should match ZERO results. SecretStorage (auth.ts) and globalState
(state.ts, NO secrets) are the only persistence layers.

### III. CLI token inheritance is ONE-WAY

`auth.ts:tryAdoptCliToken` must:
  - READ `~/.skillslab/token` only
  - NEVER call `fs.writeFileSync` or `fs.appendFileSync` on that path
  - Default policy is `ask` (consent prompt before adopting)

```bash
grep -nE 'cliTokenPath|\\.skillslab/token' {repo_root}/vscode/src/auth.ts
grep -nE 'fs\\.writeFile|fs\\.appendFile' {repo_root}/vscode/src/auth.ts
```

Second grep must return ZERO matches.

### IV. WebView CSP is strict (the Opus-flagged risk)

`webview.ts:renderHtml` must:
  - Generate a per-render nonce
  - Embed CSP `<meta>` with `script-src 'nonce-NONCE'` (NOT `'unsafe-inline'`)
  - Strip ALL inline `<script>` from server HTML before embedding
  - Rewrite `onclick="..."` to `data-action="..."` + `data-args-raw="..."`
  - Inject ONE nonce'd script that runs the captured script bodies + the
    data-action delegator

```bash
grep -nE "unsafe-inline.*script|script-src 'unsafe" {repo_root}/vscode/src/*.ts
```

Should return ZERO matches. (`unsafe-inline` for STYLES is fine — Rich-
emitted HTML has inline styles. Scripts must use nonce.)

### V. Outer-IIFE unwrap is in widgets.ts

The 2026-04-27 v7 frontend fix unwraps `(function(){...})()` wrappers
before hoisting. The TypeScript port in `widgets.ts:stripOuterIife` must
have the same regex.

```bash
grep -nE 'stripOuterIife|outerIIFE' {repo_root}/vscode/src/widgets.ts
```

Match expected. Test that the regex handles BOTH shapes:
  - Crockford `(function(){{...}})();`
  - Alt `(function(){{...}}());`
  - Leading-semicolon variant
  - Should NOT strip when the IIFE has args (`(function(x){{...}})("y")`)

### VI. Devcontainer files exist on all 3 course-repos

```bash
for REPO in kimi-eng-course-repo aie-course-repo jspring-course-repo; do
  echo "=== $REPO ==="
  for BRANCH in module-1-starter module-2-claudemd module-2-retry module-3-iterate module-3-agents module-4-mcp module-4-hooks module-5-team module-5-mcp module-6-capstone module-6-agent-harness; do
    gh api repos/tusharbisht/$REPO/contents/.devcontainer/devcontainer.json?ref=$BRANCH 2>&1 | grep -qE '"name"|404' && echo "  $BRANCH: ok"
  done
done
```

Each course's working-branch list must show the devcontainer file
present. Branches that don't exist on a particular course-repo are fine
(branch lists differ; e.g. aie has module-2-retry, kimi has module-2-claudemd).

### VII. URI handler routes correctly

`vscode://tusharbisht1391.skillslab/course/<courseId>?step=<stepId>`

`extension.ts` must register a `registerUriHandler` that:
  - Matches `^/course/([^/]+)$`
  - Reads `step` from URI query
  - Calls `cmds.openStep(...)` with the resolved course/module/step

```bash
grep -nE 'registerUriHandler|openStep' {repo_root}/vscode/src/extension.ts
```

### VIII. Buddy-Opus's MVP cuts honored

Per the 2026-04-27 consult:
  - Status bar item: CUT from v1
  - `next` + `check`: MERGED into `submitAndContinue`
  - Module split: 8 separate files (extension/auth/api/state/tree/webview/widgets/commands/theme)

```bash
ls {repo_root}/vscode/src/*.ts | wc -l   # expect ~9 (8 + theme)
grep -nE 'createStatusBarItem' {repo_root}/vscode/src/*.ts   # expect 0
grep -nE 'submitAndContinue' {repo_root}/vscode/src/*.ts     # expect ≥3
```

### IX. LMS frontend has additive 'Open in VS Code' button

```bash
grep -nE 'vscode://tusharbisht1391\\.skillslab' {repo_root}/frontend/index.html
```

Should match. The button must produce a `vscode://` URL with the right
publisher.id (`tusharbisht1391.skillslab`) so VS Code intercepts.

### X. Footgun fix: 'How to run' affordance present

Per the 2026-04-27 buddy-Opus consult: the WebView must surface a
prominent "Open Terminal" button for terminal-surface steps. Without
it, terminal-shy learners read the briefing, click Submit, and bounce.

```bash
grep -nE 'Open Terminal|runInTerminal|How to run' {repo_root}/vscode/src/webview.ts
```

## POST-LAUNCH UX INVARIANTS (rounds 1-3 user feedback, 2026-04-27)

These invariants codify bugs the user filed AFTER first install. Every
time a regression slips past, add a new invariant here so the next
shim run catches it. Goal: never ship the same UX bug twice.

### XI. Previous-button wiring (Round 1 Fix 1)

User feedback: "No button to go back." A `◂ Previous` button must be
present in the WebView footer + a palette command `Skillslab: Previous Step`
+ a `previous(...)` method on `CommandHandlers`.

```bash
grep -nE 'data-vsc-msg="prev"|case "prev":|◂ Previous' {repo_root}/vscode/src/webview.ts
grep -nE 'async previous\\(|this\\.previous\\(' {repo_root}/vscode/src/commands.ts
grep -nE 'skillslab\\.previousStep' {repo_root}/vscode/src/extension.ts {repo_root}/vscode/package.json
```

All three greps must match. FAIL if any returns zero results.

### XII. Course accent toned down to ≤ 3 sites (Round 1 Fix 2)

User feedback: "Red theme is overwhelming, make it easier on the eyes."
The theme accent (`${{accent}}`) must appear ONLY in three CSS
declarations: 3px header stripe, header label color, primary CTA fill.
Everything else MUST use `var(--vscode-*)` semantic colors.

```bash
grep -cE '\\$\\{{accent\\}}' {repo_root}/vscode/src/webview.ts   # expect exactly 3
```

FAIL if count > 3 (regression — accent leaked back into a badge,
secondary button, link, or border). Specifically forbid these patterns:

```bash
grep -nE '\\$\\{{accent\\}}22|\\$\\{{accent\\}}33|border:.*\\$\\{{accent\\}}|color:.*\\$\\{{accent\\}}.*border' {repo_root}/vscode/src/webview.ts
```

Should return ZERO matches. (`{{accent}}22` was the badge tint hex
suffix; `border: 1px solid {{accent}}` was the secondary button.)

### XIII. Conditional 'Open in Browser' (Round 1 Fix 3)

User feedback: "Reduce the visibility of Open In Browser, as it is not
important." Primary "Open in Browser" CTA must render ONLY for browser-
widget exercise types (where the dashboard widget IS the work). For
other steps, demote to a subtle footer link.

```bash
grep -nE 'BROWSER_WIDGET_TYPES|showFooterBrowserLink|footer-link' {repo_root}/vscode/src/webview.ts
```

`BROWSER_WIDGET_TYPES` set must include at least: scenario_branch,
simulator_loop, incident_console, categorization, parsons, sjt, mcq,
fill_in_blank, ordering, code_review, adaptive_roleplay,
voice_mock_interview. Verify by grepping the set definition.

### XIV. Submit-only-when-required gate (Round 2 Fix A)

User feedback: "Keep submit & continue only for exercises which requires
submission." The Submit & Continue button must NOT render for `concept`-
type steps (or any future no-submit type). A `NO_SUBMIT_TYPES` set must
gate the render via a `requiresSubmission` flag.

```bash
grep -nE 'NO_SUBMIT_TYPES|requiresSubmission' {repo_root}/vscode/src/webview.ts
```

Both names must appear. The footer-actions must wrap the Submit button
in a `${{requiresSubmission ? ... : ``}}` ternary (zero-render for
no-submit steps).

### XV. Skip → Next rename (Round 2 Fix B)

User feedback: "Instead of skip - rename to next." The secondary
forward button must read "Next ▸", not "Skip ▸". Verify the literal
string is gone.

```bash
grep -nE 'Skip ▸|Skip\\b.*data-vsc-msg' {repo_root}/vscode/src/webview.ts
```

Must return ZERO matches. Conversely:

```bash
grep -nE 'Next ▸' {repo_root}/vscode/src/webview.ts   # expect ≥1
```

### XVI. nextOrComplete handler (Round 2 Fix C)

When Submit is hidden (concept), Next becomes the completion action —
the host handler must mark the step complete on its way through, NOT
just advance the cursor.

```bash
grep -nE 'async nextOrComplete\\(|this\\.nextOrComplete\\(' {repo_root}/vscode/src/commands.ts
```

Both occurrences must be present (definition + wire-up in `openStep`).

### XVII. Stale-closure fix in WebView message handler (Round 3 Fix D)

User feedback (verbatim, screenshot-evidenced): "Open Terminal & Run
Steps => no cli commands error" — toast read "S1 has no cli_commands"
on M0.S2. Root cause: `onDidReceiveMessage` was registered ONCE at
panel creation with closures over the FIRST step's callbacks; later
`show()` calls re-rendered HTML but never re-bound the listener.

The fix MUST store callbacks on `this` and have the listener use lazy
lookup, never closure capture:

```bash
grep -nE 'private callbacks:|this\\.callbacks =|this\\.callbacks\\.' {repo_root}/vscode/src/webview.ts
```

Must show: a `private callbacks:` field declaration, an assignment
`this.callbacks = {{ ... }}` in `show()` (BEFORE the `if (this.panel)`
branch so it fires on every show), and dispatch via `this.callbacks.X?.()`
in the listener body. FAIL if the listener body still uses
`onCheck()` / `onNext()` / `onRunInTerminal()` directly (those are
the captured closures from the first call).

### XVIII. Detailed feedback panel rendered IN WebView (Round 3 Fix E)

User feedback: "Submit & Continue => should give detailed feedback,
similar to terminal." Replaces the toast-only flow with a rich panel
showing pass/fail + score + grader prose + per-item correctness +
canonical answer (collapsed) — same depth the CLI surfaces.

```bash
grep -nE 'renderFeedbackPanel|feedback-panel|fb-prose|fb-items' {repo_root}/vscode/src/webview.ts
grep -nE 'feedback\\?: ValidateResponse|input\\.feedback' {repo_root}/vscode/src/webview.ts
```

Both blocks must match. Additionally, `commands.ts:submitAndContinue`
must re-call `openStep(...)` with the validated response (not just
toast):

```bash
grep -nE 'this\\.openStep\\(.*validated' {repo_root}/vscode/src/commands.ts
```

Must match. FAIL if `submitAndContinue` only calls `showWarningMessage`
without re-rendering the WebView with feedback.

### XX. No eval / Function() in WebView runtime (Round 3 Fix G — root-cause)

User feedback (verbatim, WebView console 2026-04-27): "VM16:177
[skillslab widget action] failed to parse args for "selectScenario":
EvalError: Evaluating a string as JavaScript violates the following
Content Security Policy directive because 'unsafe-eval' is not an
allowed source of script."

ROOT CAUSE: pre-v0.1.2 the delegator parsed args via
`Function('return ['+argsRaw+'];')()`. CSP blocks. Beyond CSP, evaluating
arbitrary attribute strings as JS is an XSS amplifier — narrow that
surface to JSON.parse only.

**Verification: execute, don't grep.** Per user directive 2026-04-27:
"shim should ideally not rely on grep as it can be brittle, rely on
higher level functions like click and execute."

`vscode/tests/widgets.test.ts` runs the actual code paths via Node's
built-in test runner and asserts on real outputs (the runtime string
that gets embedded in the WebView's nonce'd `<script>`). Zero source
grep — comment-text mentions of historical `Function(` don't
false-positive because we measure behavior, not source.

```bash
cd {repo_root}/vscode && npm test 2>&1 | tail -25
```

Expected output ends with `ℹ pass 20\\nℹ fail 0` (or higher pass count).
FAIL on any failed test. The relevant assertions (each runs the actual
code path, no grep on source):

  - `buildRuntimeScript: zero Function( or eval( in delegator output`
    → calls `buildRuntimeScript([...])` and asserts the returned
    string contains neither `Function(` nor `eval(`. This is the
    runtime's actual delegator body, byte-for-byte what runs in the
    WebView under CSP `script-src 'nonce-X'`.
  - `buildRuntimeScript: delegator parses args via JSON.parse` →
    asserts the runtime explicitly uses `JSON.parse(argsJson)`.
  - `rewriteOnclicks: emits data-args-json (NOT data-args-raw)` →
    feeds `<button onclick="selectScenario('ship_feature')">` to the
    rewriter and asserts the output contains the canonical JSON shape,
    not the v0.1.1 eval-blocked shape.
  - `rewriteForWebview: data-args-json values round-trip through
    JSON.parse` → strong regression test: extracts every
    `data-args-json="..."` value from the rewriter output and verifies
    each is valid JSON. If a future widget arg shape can't coerce,
    this fails loudly instead of failing silently at click time.

If `npm test` reports any failure, the regression is structural; do
not patch around it.

### XIX. Spec panel for terminal_exercise (Round 3 Fix F)

User feedback: "Spec needs to be shown here as in the terminal for the
user to understand the task at hand." For terminal_exercise (and any
step with cli_commands / must_contain / rubric / endpoint_check /
gha_workflow_check in `validation`), the WebView must render a SPEC
PANEL between the briefing and the footer — same shape the CLI surfaces.

```bash
grep -nE 'renderSpecPanel|spec-panel|spec-section' {repo_root}/vscode/src/webview.ts
```

Must match. The function must handle at minimum: cli_commands (📋 What
to do), must_contain (✅ Must contain), rubric (📐 Grading rubric).
Verify by grepping the function body for those strings:

```bash
grep -nE 'What to do|Must contain|Grading rubric' {repo_root}/vscode/src/webview.ts
```

All three section headers must be present as literal strings.

## BEHAVIORAL CHECKS (where possible without launching VS Code)

### B1. Server HTML rewrite test

Pick a step with a `<script>(function() {{ function generateComparison() {{...}} }})();</script>`
shape (jspring M0.S1 = step 85111 has this). Fetch its `content` field via
the LMS API:

```bash
curl -s {base_url}/api/courses/created-e54e7d6f51cf/modules/23201 \\
  | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d['steps'][0]['content'][:500])"
```

Then SIMULATE the rewrite by reading `widgets.ts:rewriteForWebview`'s
behavior — confirm:
  - `<script>` is stripped
  - `onclick="generateComparison()"` becomes `data-action="generateComparison" data-args-json="[]"`
  - `onclick="selectScenario('ship_feature')"` becomes
    `data-action="selectScenario" data-args-json='["ship_feature"]'`
    (NOT `data-args-raw="'ship_feature'"` — that was the v0.1.1 shape
    that fired CSP EvalError when the delegator's `Function(...)` ran
    on the args at click time).
  - The bundled runtime script defines `window.generateComparison` AT
    OUTER SCOPE (after IIFE unwrap) and the delegator parses args via
    `JSON.parse(argsJson)` — never `Function(...)` / `eval(...)`.

This is the load-bearing CSP test. If it fails here, the WebView shows
inert buttons (the chronic browser bug, ported into VS Code).

### B2. Auth flow simulation

Without launching VS Code, verify the flow:
  1. Bearer NOT in SecretStorage (clean install)
  2. `~/.skillslab/token` does not exist OR `adoptCliToken=never` → returns null
  3. Bearer present → returned without prompt
  4. CLI token present + `adoptCliToken=ask` → consent prompt (we can't
     simulate the prompt; verify the code path exists)

```bash
grep -nE 'showInformationMessage.*Adopt|policy.*ask|consent' {repo_root}/vscode/src/auth.ts
```

### B3. Submit & Continue context-awareness

`commands.ts:submitAndContinue` must:
  - Record an attempt (`state.recordAttempt`)
  - Pass `attempt_number` to `api.validate`
  - On `correct: true` → mark complete + advance cursor + open next step
  - On `correct: false` → show feedback, leave cursor

```bash
grep -nE 'recordAttempt|attempt_number|markComplete' {repo_root}/vscode/src/commands.ts
```

## OUTPUT

Stream-write findings to `{artifact_path}` as you go. Per-invariant
PASS / FAIL with verbatim evidence.

End with:
  - Counts: invariants passed N/10, behavioral checks passed N/3
  - Top issues if any
  - Verdict: SHIP / SHIP-WITH-FIXES / REJECT

## REPLY (<300 words)

Tell me: invariants N/10, behavioral checks N/3, verdict, top 3 issues
if any. Image / extension version used.

{issues_block}
"""
