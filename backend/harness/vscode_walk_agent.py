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
  - Crockford `(function(){...}})();`
  - Alt `(function(){...}}());`
  - Leading-semicolon variant
  - Should NOT strip when the IIFE has args (`(function(x){...})("y")`)

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
  - `onclick="generateComparison()"` becomes `data-action="generateComparison" data-args-raw=""`
  - The bundled runtime script defines `window.generateComparison` AT
    OUTER SCOPE (after IIFE unwrap)

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
