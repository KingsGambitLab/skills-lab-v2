# VS Code walk-agent v3 — Skillslab extension v0.1.2 / Kimi course (created-698e6399e3ca)

**Pass tag**: v3
**Date**: 2026-04-27
**Repo**: `/Users/tushar/Desktop/codebases/skills-lab-v2/vscode/`
**Build artifact**: `vscode/skillslab-0.1.2.vsix` (rebuilt + smoke-installed) — package.json reports `name=skillslab, version=0.1.2, publisher=tusharbisht1391`
**Course**: created-698e6399e3ca / Open-Source AI Coding (Aider + Kimi K2)

---

## ARCHITECTURAL INVARIANTS (I-X)

### I. TypeScript compiles cleanly — PASS
`cd vscode && npx tsc -p .` exit 0; zero `error TS` lines; produces `dist/{api,auth,commands,extension,state,theme,tree,webview,widgets}.js`.

### II. SecretStorage is the ONLY persistence for keys — PASS
`grep -nE 'localStorage|sessionStorage|writeFile.*token|fs\.appendFileSync.*key' src/*.ts` → ZERO matches.

### III. CLI token inheritance is ONE-WAY — PASS
`auth.ts:tryAdoptCliToken` reads `~/.skillslab/token` only. `grep -nE 'fs\.writeFile|fs\.appendFile' auth.ts` → ZERO matches. Default policy `ask`; consent prompt at line 108.

### IV. WebView CSP is strict — PASS
`grep -nE "unsafe-inline.*script|script-src 'unsafe" src/*.ts` → ZERO matches.

### V. Outer-IIFE unwrap exists — PASS
`widgets.ts:149 function stripOuterIife(code: string)`; called at line 174. Behavioral check confirms IIFE body is hoisted to outer scope (B1 below).

### VI. Devcontainer files present on every working branch — PASS
21/21 ok across 3 repos. Note: harness branch list contains some branches that don't exist per repo (e.g. `module-2-claudemd` only on kimi/jspring; `module-2-retry` only on aie). Per the harness contract ("branches that don't exist on a particular course-repo are fine") this is expected; every branch that exists has the file.

| Repo | Branches with devcontainer.json |
|---|---|
| `tusharbisht/kimi-eng-course-repo` | module-0-preflight, module-1-starter, module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone (7/7) |
| `tusharbisht/aie-course-repo` | module-0-preflight, module-1-starter, module-2-retry, module-3-iterate, module-4-mcp, module-5-team, module-6-agent-harness (7/7) |
| `tusharbisht/jspring-course-repo` | module-0-preflight, module-1-starter, module-2-claudemd, module-3-agents, module-4-hooks, module-5-mcp, module-6-capstone (7/7) |

### VII. URI handler routes correctly — PASS
`extension.ts:128 vscode.window.registerUriHandler(...)`; pattern matched at L144 calls `cmds.openStep(courseId, mod.id, target)`.

### VIII. MVP cuts honored (Opus consult) — PASS
- `ls src/*.ts | wc -l` = 9 (api, auth, commands, extension, state, theme, tree, webview, widgets)
- `createStatusBarItem` → ZERO matches (cut)
- `submitAndContinue` → 8 matches across commands.ts (definition + wire-up), extension.ts (command id), webview.ts (comments)

### IX. LMS frontend has 'Open in VS Code' button — PASS
`frontend/index.html:4671` — `vscode://tusharbisht1391.skillslab/course/...?step=...` (correct publisher.id).

### X. 'How to run' / 'Open Terminal' affordance — PASS
`webview.ts` lines 134, 181, 189: `data-vsc-msg="runInTerminal"` button with `▸ Open Terminal & Run Steps` text and prose at L7 `"How to run this step" section`.

**ARCHITECTURAL: 10/10 PASS**

---

## POST-LAUNCH UX INVARIANTS (XI-XX)

### XI. Previous-button wiring — PASS
- `webview.ts:133 case "prev"`; `webview.ts:431 data-vsc-msg="prev" ◂ Previous`
- `commands.ts:348 async previous(...)`; wire-up at L175
- `extension.ts:92 skillslab.previousStep`; `package.json:23,63` registers command

### XII. Course accent toned to ≤ 3 sites — PASS
`grep -cE '\$\{accent\}' webview.ts` = exactly 3. Forbidden patterns (`accent}22`, `accent}33`, `border:.*accent`, etc.) → ZERO matches.

### XIII. Conditional 'Open in Browser' — PASS
- `BROWSER_WIDGET_TYPES` set (line 55) contains all 12 required types: scenario_branch, simulator_loop, incident_console, categorization, parsons, sjt, mcq, fill_in_blank, ordering, code_review, adaptive_roleplay, voice_mock_interview
- Primary CTA gated at L192 (`else if BROWSER_WIDGET_TYPES.has(exType)`)
- Footer-link demote-path at L207-210 (`showFooterBrowserLink` + `footer-link` CSS at L317)

### XIV. Submit-only-when-required gate — PASS
- `webview.ts:78 NO_SUBMIT_TYPES = new Set(["concept"])`
- L217 `requiresSubmission = !NO_SUBMIT_TYPES.has(exType)`
- L430: `${requiresSubmission ? `<button class="primary" data-vsc-msg="submit">▸ Submit & Continue</button>` : ``}` (ternary zero-renders for concept)

### XV. Skip → Next rename — PASS
- `Skip ▸` / `Skip\b.*data-vsc-msg` → ZERO matches
- `Next ▸` matches L72 (comment) + L432 (the actual button label)

### XVI. nextOrComplete handler — PASS
`commands.ts:301 async nextOrComplete(...)`; wire-up at L173. Both definition + invocation present.

### XVII. Stale-closure fix in WebView listener — PASS
- `webview.ts:94 private callbacks: { ... }` field declared
- L113 `this.callbacks = { onCheck, onNext, onPrev, onRunInTerminal };` fired BEFORE the `if (this.panel)` early-return branch
- L131-134 dispatch via `this.callbacks.X?.()` (not closure-captured `onCheck()`)
- L126 `this.callbacks = {};` cleared on dispose
- This precisely closes the M0.S2 "Open Terminal" stale-closure bug.

### XVIII. Detailed feedback panel rendered IN WebView — PASS
- `webview.ts:233 const feedbackPanel = renderFeedbackPanel(input.feedback, accent);`
- `feedback-panel`, `fb-prose`, `fb-items` CSS at L361-399 (pass/fail variants, score, items list, collapsible canonical answer)
- L43 `feedback?: ValidateResponse | null;` on input; L573 `function renderFeedbackPanel(...)`
- `commands.ts:286 await this.openStep(courseId, moduleId, step, validated as ValidateResponse);` re-renders WebView with feedback (replaces toast-only flow)

### XIX. Spec panel for terminal_exercise — PASS
- `webview.ts:226 const specPanel = renderSpecPanel(input.step);`
- L477 `function renderSpecPanel(step)` body emits sections at L497 `📋 What to do` (cli_commands), L516 `✅ Must contain`, L524 `📐 Grading rubric`. Bonus: also handles `🌐 Endpoint check` (L535) and `⚡ GitHub Actions check` (L551).
- All three required section headers present as literal strings.

### XX. No eval / Function() in WebView delegator runtime — PASS
- `awk '/const delegator = `/,/^  `;$/' widgets.ts | grep -vE '^\s*(//|\*)' | grep -nE 'Function\(|eval\('` → ZERO matches
- All three required names present:
  - `data-args-json` (line 99 doc, 127 emit, 216 read)
  - `JSON.parse(argsJson)` (line 218)
  - `convertArgsToJson` (line 75 def, 118 call)

**POST-LAUNCH UX: 10/10 PASS**

---

## BEHAVIORAL CHECKS (B1-B3)

### B1. Server HTML rewrite test — PASS
Confirmed via `node` end-to-end against `dist/widgets.js`:

```
Input : <button onclick="selectScenario('ship_feature')">Ship</button> <button onclick="generateComparison()">Cmp</button>
Output: <button data-action="selectScenario" data-args-json="[&quot;ship_feature&quot;]">Ship</button>
        <button data-action="generateComparison" data-args-json="[]">Cmp</button>
```

`convertArgsToJson` correctness:
- `''` → `[]`
- `"'ship_feature'"` → `["ship_feature"]`  (single→double quote coercion)
- `"42, 'a', {x:1}"` → `[42, "a", {"x":1}]`  (object key quoting)
- `'foo()'` → `null`  (refuses to encode function calls — leaves original onclick untouched, CSP blocks)

`rewriteForWebview` end-to-end on `<script>(function(){ function selectScenario(x){...}; window.generateComparison = function(){...}; })();</script>`:
- IIFE unwrapped; `selectScenario` hoisted to outer scope and `window["selectScenario"]=selectScenario` shim emitted
- Generated script bundle contains `JSON.parse(argsJson)` (line in delegator); contains NO `Function(` and NO `eval(`
- Confirms the load-bearing CSP-safe-by-construction behavior

### B2. Auth flow simulation — PASS
`auth.ts:tryAdoptCliToken` (lines 84-127):
1. Reads `cfg.get<string>("adoptCliToken") || "ask"` — default `ask`
2. `policy === "never"` → returns null
3. CLI token file missing → returns null
4. `policy === "always"` → stores in SecretStorage, returns token (no prompt)
5. `policy === "ask"` → `vscode.window.showInformationMessage(...Adopt..., "Adopt", "Don't ask again", "No")` — explicit consent prompt
6. "Don't ask again" updates global config to `never`

Bearer-only flow: `getBearer` returns SecretStorage value if present without prompting (consistent with B2 step 3).

### B3. Submit & Continue context-awareness — PASS
`commands.ts:submitAndContinue` (line 209):
- L211 `const attempt = this.state.recordAttempt(slug, step.id);` — records attempt
- L205 doc + invocation pass `attempt_number` to `api.validate`
- L229/L268 `await this.api.markComplete(step.id, ...)` — on correct=true
- L286 re-calls `openStep(...)` with validated response (NOT just toast)
- L301 `nextOrComplete` mirrors `markComplete` for concept advance

**BEHAVIORAL: 3/3 PASS**

---

## RECENTLY-FILED ISSUES (verify each is closed)

| # | Issue | Status | Evidence |
|---|---|---|---|
| 1 | M0.S1 widget click → CSP EvalError ('unsafe-eval' not allowed) | **CLOSED** | Invariant XX + B1: delegator now uses `JSON.parse(argsJson)` only; no `Function(` or `eval(` in `dist/widgets.js` runtime body. Rewrite emits `data-args-json='["ship_feature"]'` instead of pre-v0.1.2 `data-args-raw="'ship_feature'"`. |
| 2 | M0.S2 Open Terminal toast 'S1 has no cli_commands' (stale-closure) | **CLOSED** | Invariant XVII: callbacks live on `this.callbacks` (webview.ts:94, 113, 131-134); `show()` reassigns BEFORE `if (this.panel)` early-return so listener always reads current step's handlers. Precisely the structural fix described in the bug report (L90-91 doc-comment names this exact regression). |
| 3 | Submit & Continue gave only a toast — no detailed feedback like CLI | **CLOSED** | Invariant XVIII: `renderFeedbackPanel` (webview.ts:573) renders pass/fail + score + grader prose + per-item ✓/✗ + collapsible canonical answer. `commands.ts:286 this.openStep(..., validated as ValidateResponse)` re-renders panel post-validate. |
| 4 | Spec (cli_commands + must_contain) not visible in WebView for terminal_exercise — only briefing prose | **CLOSED** | Invariant XIX: `renderSpecPanel` (webview.ts:477) emits `📋 What to do`, `✅ Must contain`, `📐 Grading rubric` sections (also endpoint + GHA checks). Mounted between briefing and footer at L226. |
| 5 | Submit & Continue rendered for concept steps that have no submission | **CLOSED** | Invariant XIV: `NO_SUBMIT_TYPES = {"concept"}`; `requiresSubmission` ternary (webview.ts:430) zero-renders the Submit button when `exType === "concept"`. |
| 6 | Skip ▸ should be renamed to Next ▸ | **CLOSED** | Invariant XV: `Skip ▸` → ZERO matches; `Next ▸` is the literal at webview.ts:432. |

**6/6 CLOSED**

---

## SUMMARY

- Architectural invariants: **10/10 PASS**
- UX invariants (XI-XX): **10/10 PASS**
- Behavioral checks: **3/3 PASS**
- User-filed issues closed: **6/6**

## VERDICT: SHIP

Every invariant green; every user-filed issue from the v0.1.1 walk has a structural close in v0.1.2 (not a per-symptom patch — the CSP fix is via JSON.parse-only delegator, the stale-closure fix is via `this.callbacks`, the toast→panel fix re-routes through `openStep`). No DEFERRED-TO-MANUAL items needed for this pass.
