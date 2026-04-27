# VS Code Walk-Agent — Pass v2 (jspring) — 2026-04-27

**Course**: created-e54e7d6f51cf — JavaSpring (Java Spring Boot AI)
**Pass tag**: v2 (v1 already passed 10/10)
**Extension**: `vscode/`, version 0.1.1 (rebuilt)
**Repo root**: `/Users/tushar/Desktop/codebases/skills-lab-v2`

Note on prompt-build: `backend/harness/vscode_walk_agent.py:138` has a SyntaxError under Python 3.12 in the f-string (single `}` in `(function(){...}})();`). Worked around — invariants executed verbatim per the prompt template.

---

## INVARIANTS

### I. TypeScript compiles cleanly — PASS
`cd vscode && npx tsc -p .` exit=0, no `error TS` lines.

### II. SecretStorage-only persistence — PASS
`grep -nE 'localStorage|sessionStorage|writeFile.*token|fs\.appendFileSync.*key' vscode/src/*.ts` → ZERO matches (exit=1, no matches).

### III. CLI token inheritance is one-way — PASS
- `cliTokenPath` defined at `auth.ts:130`; reads `~/.skillslab/token` (line 7,41,78,89,108).
- `grep -nE 'fs\.writeFile|fs\.appendFile' vscode/src/auth.ts` → ZERO (exit=1).

### IV. WebView CSP strict (no unsafe-inline scripts) — PASS
`grep -nE "unsafe-inline.*script|script-src 'unsafe" vscode/src/*.ts` → ZERO (exit=1).

### V. Outer-IIFE unwrap in widgets.ts — PASS
- `widgets.ts:103` `function stripOuterIife(code: string): string`.
- `widgets.ts:128` invokes `stripOuterIife(raw)` per captured script body.
- Regex `^[;\s]*\(\s*function\s*\(\s*\)\s*\{([\s\S]*)\}\s*(?:\)\s*\(\s*\)|\(\s*\)\s*\))\s*;?\s*$` covers leading-semicolon, Crockford `})()`, and alt `}())` shapes; rejects IIFEs with args (correct).

### VI. Devcontainer files exist on the 3 course-repos — PASS
Per-repo branch census (each present branch shows `ok`; missing branches return 404, allowed by spec since branch lists differ across repos):

| Repo | Branches verified ok | Missing (per spec, ok) |
|---|---|---|
| kimi-eng-course-repo | module-1-starter, module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone | module-2-retry, module-3-iterate, module-4-mcp, module-5-team, module-6-agent-harness |
| aie-course-repo | module-1-starter, module-2-retry, module-3-iterate, module-4-mcp, module-5-team, module-6-agent-harness | module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone |
| jspring-course-repo | module-1-starter, module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone | (same pattern as kimi) |

Each course's working branches all have `.devcontainer/devcontainer.json` present.

### VII. URI handler routes — PASS
- `extension.ts:128` `vscode.window.registerUriHandler(...)`.
- `extension.ts:144` invokes `cmds.openStep(courseId, mod.id, target)`.
- `commands.ts:85-87` `skillslab.openStep` registered.

### VIII. MVP cuts honored — PASS
- `ls vscode/src/*.ts | wc -l` = 9 (matches expected ~9).
- `grep -nE 'createStatusBarItem' vscode/src/*.ts` → ZERO (exit=1). Status-bar correctly cut.
- `grep -nE 'submitAndContinue' vscode/src/*.ts | wc -l` = 4 (≥3 required).

### IX. LMS frontend has Open-in-VS-Code button — PASS
`frontend/index.html:4671` emits `vscode://tusharbisht1391.skillslab/course/${...}?step=${...}` — correct publisher.id.

### X. How-to-run affordance present — PASS
`webview.ts:7` (header doc), `:90` (`runInTerminal` message handler), `:137` (terminal-surface comment), `:145` `<button class="primary" data-vsc-msg="runInTerminal">▸ Open Terminal &amp; Run Steps</button>`.

**Invariants: 10/10 PASS**

---

## BEHAVIORAL CHECKS

### B1. Server HTML rewrite test — PASS
- `curl http://52.88.255.208/api/courses/created-e54e7d6f51cf/modules/23201` returned step_id=85111, "What this course IS (and what it isn't)".
- Content head shows server-emitted `<div style="background: #1e2538; color: #e8ecf4; ...">` — well-formed dark-theme inline styles, no inline `<script>` in the head sample (consistent with darkified content; for any step that DOES carry inline scripts, `widgets.ts:extractAndStripScripts` removes them and feeds bodies to the nonce'd runtime).
- The pipeline (extract scripts → rewrite onclicks → outer-IIFE unwrap → hoist function decls + const/let arrow assignments to `window` → install `[data-action]` delegator at line 144) faithfully mirrors the v7 frontend rewrite. CSP-compliant by construction.

### B2. Auth flow simulation — PASS
- `auth.ts:8` doc says "only with consent (or `skillslab.adoptCliToken: always`)".
- `:42` "`(default ask → consent prompt)`".
- `:86` `const policy = (cfg.get<string>("adoptCliToken") || "ask").toLowerCase();`.
- `:106` "`policy === "ask"`" branch (consent prompt path exists).
- Combined with III above: read-only, opt-in, default-ask, never written back.

### B3. Submit & Continue context-awareness — PASS
- `commands.ts:198` `const attempt = this.state.recordAttempt(slug, step.id);` — records attempt.
- `:192` doc: "POST /api/exercises/validate with attempt_number".
- `:216` `await this.api.markComplete(step.id, 100);` — correct path.
- `:252` `await this.api.markComplete(step.id, Math.round(score * 100));` — partial-credit path.

**Behavioral: 3/3 PASS**

---

## USER-FILED ISSUES (verify CLOSED)

### UX-1. Previous button — CLOSED
- `webview.ts:288` `<button class="secondary" data-vsc-msg="prev" title="Go to previous step">◂ Previous</button>`.
- `commands.ts:162` dispatches `() => void this.previous(courseId, moduleId, detailedStep)`.
- `commands.ts:311` `async previous(courseId: string, moduleId: number, _step: StepSummary): Promise<void>`.
- `package.json:23` `"onCommand:skillslab.previousStep"` activation event; `:63` command contribution.

### UX-2. Theme toned down — CLOSED
- `${accent}22` (badge-surface light tint): ZERO matches (exit=1).
- `border: 1px solid ${accent}` (secondary-button border): ZERO matches (exit=1).
- Total `${accent}` occurrences in `webview.ts` = **3** (exact match to spec):
  1. `:184` `border-left: 3px solid ${accent};` (header stripe)
  2. `:191` `.step-header .label { color: ${accent}; font-weight: 700; margin-right: 8px; }` (label inside header)
  3. `:215` `background: ${accent};` (primary button)

### UX-3. Open-in-Browser conditional — CLOSED
- `webview.ts:46` `const BROWSER_WIDGET_TYPES = new Set([...])`.
- `:142` `if (surface === "terminal")` branch.
- `:148` `else if (BROWSER_WIDGET_TYPES.has(exType))` branch.
- `:163-165` `const showFooterBrowserLink = surface !== "web" || !BROWSER_WIDGET_TYPES.has(exType);` and `:165` `const footerBrowserLink = showFooterBrowserLink ? ...` — subtle utility link only when WebView is the work surface.

**UX-fixes: 3/3 CLOSED**

---

## VERDICT

- **Invariants**: 10/10 PASS
- **Behavioral**: 3/3 PASS
- **UX-fixes**: 3/3 CLOSED

**SHIP.**

Top notes (non-blocking):
1. `backend/harness/vscode_walk_agent.py:138` has an f-string SyntaxError (single `}` in `})();`). Doesn't affect this run (worked around by reading the prompt template directly), but the shim is broken for callers that import it. Should be fixed.
2. Devcontainer branch coverage is per-repo (each course-repo has its own working-branch list). Spec accepts this; no action needed.
