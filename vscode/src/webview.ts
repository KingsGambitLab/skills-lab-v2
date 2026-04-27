/**
 * Step-card WebView — renders a step's briefing inside VS Code with full
 * CSP-safety. Uses the data-action delegator (port from frontend) so
 * widget buttons work without `unsafe-inline`.
 *
 * Per buddy-Opus 2026-04-27 (footgun fix): every WebView includes a
 * "How to run this step" section that opens the integrated terminal
 * pre-populated with the right commands. Without this, terminal-shy
 * learners read the briefing, click Submit, and bounce on "no output".
 *
 * UX feedback 2026-04-27 (user screenshot):
 *   1. Need a "Previous" button — added to footer-actions next to Skip.
 *   2. Red theme overwhelming — accent now only appears as a 3px stripe
 *      on the step-header + on the primary CTA. Everything else uses
 *      VS Code-native semantic colors so the panel blends with the IDE.
 *   3. "Open in Browser" was too prominent — now only shown as a primary
 *      action for steps whose widget IS the work (scenario_branch,
 *      simulator_loop, incident_console, etc.). For concept / code_read /
 *      terminal_exercise, the browser link is demoted to a small footer
 *      utility link, since the WebView already renders everything.
 */
import * as vscode from "vscode";
import { rewriteForWebview } from "./widgets";
import { StepSummary, ValidateResponse } from "./api";

export interface StepRenderInput {
  courseId: string;
  moduleId: number;
  moduleTitle: string;
  step: StepSummary;
  modulePos: number;        // 1-indexed module position from API
  attemptCount: number;     // 0 if never submitted
  themeAccent: string;      // hex/CSS color from getThemeForCourse
  webBaseUrl: string;       // for "Open in browser" links
  /**
   * Most-recent grader feedback for THIS step. Populated by
   * commands.ts:submitAndContinue immediately after /api/exercises/validate
   * returns. Renders as a panel at the top of the WebView with score,
   * pass/fail badge, full feedback prose, per-item correctness, and
   * explanations — same level of detail the CLI surfaces post-`check`.
   * Null on the initial open / after navigating away.
   */
  feedback?: ValidateResponse | null;
}

/**
 * Exercise types whose interactive widget IS the work surface.
 * For these, we surface "Open in Browser" as a primary top-of-page CTA
 * because the dashboard widget is what the learner needs to use to
 * actually solve the step (drag-drop, scenario tree, sim console, etc.).
 *
 * Anything not in this set + non-terminal surface → no top-of-page
 * primary action (the WebView already shows the briefing inline).
 */
const BROWSER_WIDGET_TYPES = new Set([
  "scenario_branch",
  "simulator_loop",
  "incident_console",
  "categorization",
  "parsons",
  "sjt",
  "mcq",
  "fill_in_blank",
  "ordering",
  "code_review",
  "adaptive_roleplay",
  "voice_mock_interview",
]);

/**
 * Exercise types that have NO submission to grade — purely read-then-advance.
 * For these, hide the "Submit & Continue" button entirely; the "Next ▸"
 * button becomes the primary action and (on the host side) auto-marks the
 * step complete on the way through (mirrors submitAndContinue's concept
 * branch). User feedback 2026-04-27: "Keep submit & continue only for
 * exercises which requires submission."
 */
const NO_SUBMIT_TYPES = new Set(["concept"]);

/** Open or focus the step-card panel for a given step. */
export class StepWebViewManager {
  private panel: vscode.WebviewPanel | null = null;

  /**
   * Callbacks for the CURRENT step. Updated on every show() so a panel
   * that's already open re-binds to the new step's handlers. The
   * onDidReceiveMessage listener (registered ONCE at panel creation)
   * reads from this.callbacks lazily, so it always invokes the latest
   * step's handler, never a stale closure from when the panel was first
   * created. (Pre-v0.1.2 bug: clicking "Open Terminal" on M0.S2 invoked
   * M0.S1's runInTerminal handler — toast read "S1 has no cli_commands"
   * even though the panel showed M0.S2.)
   */
  private callbacks: {
    onCheck?: () => void;
    onNext?: () => void;
    onPrev?: () => void;
    onRunInTerminal?: () => void;
    onRunAuto?: () => void;
  } = {};

  constructor(private readonly extensionUri: vscode.Uri) {}

  show(
    input: StepRenderInput,
    onCheck: () => void,
    onNext: () => void,
    onRunInTerminal: () => void,
    onPrev: () => void,
    onRunAuto?: () => void,
  ): void {
    // ALWAYS update callbacks BEFORE reveal/render — the listener below
    // reads via `this.callbacks.X?.()` so this swap is what makes the
    // already-open panel route to the new step.
    this.callbacks = { onCheck, onNext, onPrev, onRunInTerminal, onRunAuto };

    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Beside, true);
    } else {
      this.panel = vscode.window.createWebviewPanel(
        "skillslab.step",
        `${labelOf(input)} — Skillslab`,
        { viewColumn: vscode.ViewColumn.Beside, preserveFocus: false },
        { enableScripts: true, retainContextWhenHidden: true },
      );
      this.panel.onDidDispose(() => {
        this.panel = null;
        this.callbacks = {};
      });
      this.panel.webview.onDidReceiveMessage((msg) => {
        if (!msg || typeof msg !== "object") return;
        switch (msg.type) {
          case "submit": this.callbacks.onCheck?.(); break;
          case "next": this.callbacks.onNext?.(); break;
          case "prev": this.callbacks.onPrev?.(); break;
          case "runInTerminal": this.callbacks.onRunInTerminal?.(); break;
          case "runAuto": this.callbacks.onRunAuto?.(); break;
        }
      });
    }
    this.panel.title = `${labelOf(input)} — Skillslab`;
    this.panel.webview.html = this.renderHtml(input);
  }

  dispose(): void {
    this.panel?.dispose();
    this.panel = null;
  }

  private renderHtml(input: StepRenderInput): string {
    const stepLabel = labelOf(input);
    const surface = (input.step.learner_surface || "web").toLowerCase();
    const surfaceWord = surface === "terminal" ? "TERMINAL" : "WEB";
    const exType = (input.step.exercise_type || "concept").toLowerCase();
    const stepContent = input.step.content || "";
    const accent = input.themeAccent;
    const attemptBadge =
      input.attemptCount >= 1
        ? `<span class="badge badge-attempt">attempt ${input.attemptCount + 1}</span>`
        : "";

    // Step content rewrite — strip inline scripts/onclicks, return CSP-safe
    // body + a runtime script bundle to inject under our nonce.
    const { html: bodyHtml, scriptBundle, nonce } = rewriteForWebview(stepContent);

    // CSP — strict. Only nonce'd scripts allowed; styles inline OK (Rich-
    // style emits inline styles). No external script-src; no eval.
    const cspWebView = this.panel!.webview.cspSource;
    const csp = [
      `default-src 'none'`,
      `style-src 'unsafe-inline' ${cspWebView}`,
      `img-src ${cspWebView} https: data:`,
      `script-src 'nonce-${nonce}'`,
      `font-src ${cspWebView}`,
    ].join("; ");

    // Browser deep-link for the same step (opens the dashboard widget —
    // useful for scenario_branch / simulator_loop / etc. where the widget
    // IS the work surface).
    const browserUrl = `${input.webBaseUrl.replace(/\/$/, "")}/#${input.courseId}/${input.moduleId}/${Math.max(0, input.step.position - 1)}`;

    // Decide what (if anything) to surface as the top-of-page primary
    // action. Three buckets:
    //   - terminal surface → "Open Terminal" (footgun fix from buddy-Opus)
    //   - browser-widget exercise type → "Open in Browser" (widget = work)
    //   - everything else (concept / code_read / etc.) → no banner;
    //     the briefing in the WebView is the whole experience.
    let howToRun = "";
    if (surface === "terminal") {
      // v0.1.3: primary CTA is "Run This Step" (auto-execute via shell
      // integration + auto-capture output + auto-submit). Pre-v0.1.3
      // the only path was "Open Terminal" → learner runs commands by
      // hand → pastes output OR submits empty (both feel broken).
      // Manual fallback stays available as a subtle link below.
      howToRun = `
        <div class="action-row">
          <button class="primary" data-vsc-msg="runAuto">▸ Run This Step</button>
          <span class="muted">runs cli_commands in a terminal, captures output, auto-submits</span>
          <span class="footer-spacer"></span>
          <a class="footer-link" href="#" data-vsc-msg="runInTerminal">↳ open terminal manually</a>
        </div>`;
    } else if (BROWSER_WIDGET_TYPES.has(exType)) {
      howToRun = `
        <div class="action-row">
          <a class="primary" href="${escapeAttr(browserUrl)}" target="_blank" rel="noopener">▸ Open in Browser</a>
          <span class="muted">the interactive ${escapeAttr(exType.replace(/_/g, " "))} widget renders in the dashboard</span>
        </div>`;
    }
    // else: no top-of-page action — concept / code_read / system_build
    // briefings are self-contained in the WebView.

    // Decide whether to include the small "Open in Browser ↗" footer
    // link. We show it ONLY when we did NOT already promote it to a
    // top-of-page primary (i.e. for terminal-surface + concept-style
    // steps, in case the learner WANTS the dashboard view as a
    // secondary path). Stays subtle — link styling, not button.
    const showFooterBrowserLink =
      surface !== "web" || !BROWSER_WIDGET_TYPES.has(exType);
    const footerBrowserLink = showFooterBrowserLink
      ? `<a class="footer-link" href="${escapeAttr(browserUrl)}" target="_blank" rel="noopener">view in browser ↗</a>`
      : "";

    // Submit & Continue only renders for steps that actually grade a
    // submission. For pure-read steps (concept), the Next button is
    // promoted to primary + the host auto-marks the step complete on
    // its way through.
    const requiresSubmission = !NO_SUBMIT_TYPES.has(exType);

    // Spec panel — for terminal_exercise (and any step with cli_commands
    // / must_contain / rubric in validation), render the SAME spec the
    // CLI surfaces post-2026-04-25 (CLI-walk fix). User feedback
    // 2026-04-27: "Spec needs to be shown here as in the terminal for
    // the user to understand the task at hand." The briefing prose alone
    // doesn't tell the learner WHICH commands to run or WHAT must appear
    // in the output for it to pass.
    const specPanel = renderSpecPanel(input.step);

    // Feedback panel — most-recent /api/exercises/validate response.
    // Renders at the very top of body so the learner reads it first
    // after submitting. User feedback 2026-04-27: "Submit & Continue
    // should give detailed feedback, similar to terminal." Replaces
    // the toast-only flow that swallowed feedback prose.
    const feedbackPanel = renderFeedbackPanel(input.feedback, accent);

    return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <title>${escapeAttr(stepLabel)} — Skillslab</title>
  <style>
    body { font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
           background: var(--vscode-editor-background);
           color: var(--vscode-editor-foreground);
           margin: 0; padding: 24px; line-height: 1.55; }

    /* ── Header — only place the course accent shows up beyond the CTA.
       3px stripe (was 4px) + label color. Everything else native. ── */
    .step-header {
      border-left: 3px solid ${accent};
      padding: 10px 16px;
      margin-bottom: 22px;
      background: var(--vscode-sideBar-background);
      border-radius: 0 4px 4px 0;
    }
    .step-header h1 { margin: 0 0 4px 0; font-size: 1.05rem; font-weight: 600; }
    .step-header .label { color: ${accent}; font-weight: 700; margin-right: 8px; }
    .step-meta { font-size: 0.82rem; opacity: 0.85; }

    /* Badges — all VS Code-native (no accent). Surface badge becomes a
       neutral pill instead of a colored one. */
    .badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
             font-size: 0.72rem; margin-right: 6px; font-weight: 500; }
    .badge-surface { background: var(--vscode-badge-background);
                     color: var(--vscode-badge-foreground); }
    .badge-type { background: var(--vscode-badge-background);
                  color: var(--vscode-badge-foreground); opacity: 0.75; }
    .badge-attempt { background: var(--vscode-statusBarItem-warningBackground);
                     color: var(--vscode-statusBarItem-warningForeground); }

    /* ── Top-of-page action row (terminal/browser primary CTA) ── */
    .action-row { display: flex; gap: 12px; align-items: center;
                  margin: 16px 0; padding: 12px 14px;
                  border: 1px solid var(--vscode-panel-border);
                  border-radius: 4px;
                  background: var(--vscode-textBlockQuote-background); }

    /* ── Primary CTA — the ONLY widget that uses the course accent
       beyond the header stripe + label. Solid fill, white text. ── */
    button.primary, a.primary {
      background: ${accent};
      color: white;
      border: none;
      padding: 7px 16px;
      border-radius: 3px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
    }
    button.primary:hover, a.primary:hover { opacity: 0.88; }

    /* ── Secondary buttons — VS Code's secondary palette, NOT accent ── */
    .secondary {
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      border: 1px solid transparent;
      padding: 7px 14px;
      border-radius: 3px;
      cursor: pointer;
      font-size: 0.92rem;
      font-weight: 500;
      text-decoration: none;
      display: inline-block;
    }
    .secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
    .secondary[disabled] { opacity: 0.5; cursor: not-allowed; }

    .muted { color: var(--vscode-descriptionForeground); font-size: 0.83rem; }

    /* ── Footer actions — Submit primary, Prev/Skip secondary, browser link ── */
    .footer-actions { display: flex; gap: 10px; align-items: center;
                       margin-top: 28px; padding-top: 18px;
                       border-top: 1px solid var(--vscode-panel-border); }
    .footer-spacer { flex: 1; }
    .footer-link {
      color: var(--vscode-textLink-foreground);
      font-size: 0.82rem;
      text-decoration: none;
      opacity: 0.85;
    }
    .footer-link:hover { opacity: 1; text-decoration: underline; }

    pre { background: var(--vscode-textCodeBlock-background); padding: 12px;
          border-radius: 4px; overflow-x: auto; }
    code { font-family: var(--vscode-editor-font-family); }

    /* ── Spec panel — cli_commands / must_contain / rubric ── */
    .spec-panel {
      margin: 16px 0 22px;
      padding: 14px 18px;
      background: var(--vscode-sideBar-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
    }
    .spec-section { margin-bottom: 14px; }
    .spec-section:last-child { margin-bottom: 0; }
    .spec-section h3 { margin: 0 0 8px 0; font-size: 0.92rem;
                       font-weight: 600;
                       color: var(--vscode-foreground); }
    .spec-section ol, .spec-section ul {
      margin: 0; padding-left: 22px;
    }
    .spec-section li {
      margin-bottom: 5px; font-size: 0.88rem;
      line-height: 1.5;
    }
    .spec-section code {
      background: var(--vscode-textCodeBlock-background);
      padding: 1px 6px; border-radius: 3px;
      font-size: 0.85rem;
    }
    .spec-section pre.rubric {
      max-height: 180px; overflow: auto;
      font-size: 0.82rem; padding: 10px 12px;
      white-space: pre-wrap;
    }

    /* ── Feedback panel (post-Submit) ── */
    .feedback-panel {
      margin: 0 0 22px;
      padding: 14px 18px;
      border-radius: 4px;
      border-left: 4px solid var(--vscode-panel-border);
    }
    .feedback-panel.pass {
      background: var(--vscode-inputValidation-infoBackground);
      border-left-color: var(--vscode-testing-iconPassed,
                                var(--vscode-charts-green));
    }
    .feedback-panel.fail {
      background: var(--vscode-inputValidation-warningBackground);
      border-left-color: var(--vscode-testing-iconFailed,
                                var(--vscode-charts-red));
    }
    .feedback-panel .fb-header {
      display: flex; align-items: center; gap: 10px;
      font-size: 1rem; font-weight: 600;
      margin-bottom: 8px;
    }
    .feedback-panel .fb-score {
      font-variant-numeric: tabular-nums;
      font-size: 0.92rem;
      opacity: 0.85;
    }
    .feedback-panel .fb-prose {
      font-size: 0.9rem; line-height: 1.55;
      white-space: pre-wrap;
    }
    .feedback-panel .fb-items {
      margin: 10px 0 0; padding-left: 22px;
      font-size: 0.85rem;
    }
    .feedback-panel .fb-items li { margin-bottom: 4px; }
    .feedback-panel .fb-items li.fb-correct::marker { content: "✓ "; color: var(--vscode-charts-green); }
    .feedback-panel .fb-items li.fb-wrong::marker { content: "✗ "; color: var(--vscode-charts-red); }
    .feedback-panel details { margin-top: 8px; font-size: 0.85rem; }
    .feedback-panel details summary { cursor: pointer; opacity: 0.8; }

    .step-body { font-size: 0.95rem; }
    .step-body h2, .step-body h3, .step-body h4 { margin-top: 28px; }
    .step-body p { margin: 0 0 14px; }
    .step-body ul, .step-body ol { margin: 14px 0 18px; padding-left: 24px; }
    .step-body li { margin-bottom: 6px; }
    .step-body table { border-collapse: collapse; margin: 14px 0; }
    .step-body th, .step-body td { padding: 6px 12px; border: 1px solid var(--vscode-panel-border); }
  </style>
</head>
<body>
  <div class="step-header">
    <h1><span class="label">${escapeAttr(stepLabel)}</span>${escapeAttr(input.step.title || "")}</h1>
    <div class="step-meta">
      <span class="badge badge-surface">${surfaceWord}</span>
      <span class="badge badge-type">${escapeAttr(exType)}</span>
      ${attemptBadge}
      <span class="muted">module: ${escapeAttr(input.moduleTitle)}</span>
    </div>
  </div>

  ${feedbackPanel}

  ${howToRun}

  ${specPanel}

  <div class="step-body">${bodyHtml}</div>

  <div class="footer-actions">
    ${requiresSubmission ? `<button class="primary" data-vsc-msg="submit">▸ Submit &amp; Continue</button>` : ``}
    <button class="secondary" data-vsc-msg="prev" title="Go to previous step">◂ Previous</button>
    <button class="${requiresSubmission ? `secondary` : `primary`}" data-vsc-msg="next" title="Go to next step">Next ▸</button>
    <span class="footer-spacer"></span>
    ${footerBrowserLink}
  </div>

  <script nonce="${nonce}">
    // Wire footer + how-to-run buttons through to the host extension.
    document.addEventListener('click', function(e) {
      const el = e.target.closest && e.target.closest('[data-vsc-msg]');
      if (!el) return;
      e.preventDefault();
      const acquireVsCodeApi = window['acquireVsCodeApi'];
      const vscode = (window.__vscApi = window.__vscApi || (acquireVsCodeApi && acquireVsCodeApi()));
      if (vscode) vscode.postMessage({ type: el.getAttribute('data-vsc-msg') });
    });
    // Re-injected widget runtime (data-action delegator + hoist).
    ${scriptBundle}
  </script>
</body>
</html>`;
  }
}

function labelOf(input: StepRenderInput): string {
  return `M${input.modulePos - 1}.S${input.step.position}`;
}

function escapeAttr(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Render the SPEC PANEL — same shape the CLI surfaces post-2026-04-25
 * for `terminal_exercise` (and any step whose `validation` carries
 * cli_commands / must_contain / rubric). Without this panel the
 * learner reads the briefing prose but doesn't know which commands to
 * run or what tokens must appear in the output for the step to pass.
 *
 * Returns "" (empty string) when the step has no spec content; the
 * caller injects that into the HTML where the panel would go.
 */
function renderSpecPanel(step: StepSummary): string {
  const v = (step.validation || {}) as any;
  const sections: string[] = [];

  // ── What to do — cli_commands list (terminal_exercise) ──
  const cliCmds: any[] = Array.isArray(v.cli_commands) ? v.cli_commands : [];
  if (cliCmds.length > 0) {
    const items = cliCmds
      .map((c: any) => {
        const cmd = typeof c === "string" ? c : (c.cmd || c.command || "");
        const label =
          typeof c === "object"
            ? c.label || c.description || c.why || ""
            : "";
        return `<li><code>${escapeAttr(String(cmd))}</code>${
          label ? ` <span class="muted">— ${escapeAttr(String(label))}</span>` : ""
        }</li>`;
      })
      .join("");
    sections.push(
      `<div class="spec-section"><h3>📋 What to do</h3><ol>${items}</ol></div>`,
    );
  }

  // ── Must contain — token-based pass criteria ──
  const mustContain: any[] = Array.isArray(v.must_contain) ? v.must_contain : [];
  if (mustContain.length > 0) {
    const items = mustContain
      .map((m: any) => {
        const tok =
          typeof m === "string" ? m : (m.token || m.text || m.value || "");
        const desc =
          typeof m === "object" ? m.description || m.why || m.reason || "" : "";
        return `<li><code>${escapeAttr(String(tok))}</code>${
          desc ? ` <span class="muted">— ${escapeAttr(String(desc))}</span>` : ""
        }</li>`;
      })
      .join("");
    sections.push(
      `<div class="spec-section"><h3>✅ Must contain</h3><ul>${items}</ul></div>`,
    );
  }

  // ── Rubric — LLM-grader rubric prose (truncated, scroll-capped) ──
  if (typeof v.rubric === "string" && v.rubric.trim().length > 0) {
    const r = v.rubric.length > 1200 ? v.rubric.slice(0, 1200) + "…" : v.rubric;
    sections.push(
      `<div class="spec-section"><h3>📐 Grading rubric</h3><pre class="rubric">${escapeAttr(r)}</pre></div>`,
    );
  }

  // ── Endpoint check — for system_build steps ──
  if (v.endpoint_check && typeof v.endpoint_check === "object") {
    const ep = v.endpoint_check;
    const url = ep.url || ep.endpoint || "";
    const expected = ep.expected_status || ep.expected || "";
    if (url) {
      sections.push(
        `<div class="spec-section"><h3>🌐 Endpoint check</h3><ul><li><code>${escapeAttr(
          String(url),
        )}</code>${
          expected ? ` <span class="muted">— expects ${escapeAttr(String(expected))}</span>` : ""
        }</li></ul></div>`,
      );
    }
  }

  // ── GHA workflow check — for capstone deploy steps ──
  if (v.gha_workflow_check && typeof v.gha_workflow_check === "object") {
    const gh = v.gha_workflow_check;
    const repo = gh.repo_template || gh.repo || "";
    const wf = gh.workflow_file || "lab-grade.yml";
    if (repo) {
      sections.push(
        `<div class="spec-section"><h3>⚡ GitHub Actions check</h3><ul><li>Fork <code>${escapeAttr(
          String(repo),
        )}</code>, push your solution, paste the run URL — workflow <code>${escapeAttr(
          String(wf),
        )}</code> must report <code>success</code>.</li></ul></div>`,
      );
    }
  }

  if (sections.length === 0) return "";
  return `<div class="spec-panel">${sections.join("")}</div>`;
}

/**
 * Render the FEEDBACK PANEL — most-recent /api/exercises/validate response.
 * Replaces the toast-only flow with a rich in-WebView card showing pass/fail,
 * score percentage, full feedback prose, per-item correctness (when
 * item_results[] is present), explanations, and the canonical correct
 * answer if the grader returned one.
 *
 * Returns "" when no feedback is set (initial step open / post-navigation).
 */
function renderFeedbackPanel(
  feedback: ValidateResponse | null | undefined,
  _accent: string,
): string {
  if (!feedback) return "";
  const pass = !!feedback.correct;
  const pct = Math.round((feedback.score ?? 0) * 100);
  const headerIcon = pass ? "✓" : "✗";
  const headerText = pass ? "Submission accepted" : "Not quite — keep iterating";
  const cls = pass ? "pass" : "fail";

  const proseHtml = feedback.feedback
    ? `<div class="fb-prose">${escapeAttr(String(feedback.feedback))}</div>`
    : "";

  // Per-item results — common shape across categorization / ordering /
  // sjt / mcq / code_review. Each item has correct: bool + optional
  // user_/expected_ fields + explanation.
  let itemsHtml = "";
  const items = (feedback.item_results || []) as any[];
  if (Array.isArray(items) && items.length > 0) {
    itemsHtml =
      `<ul class="fb-items">` +
      items
        .map((it: any, idx: number) => {
          const ok = !!it.correct;
          const lbl =
            it.label || it.text || it.id || it.token || `Item ${idx + 1}`;
          const yours =
            it.user_answer ?? it.user_category ?? it.user_position ?? it.user_rank ?? null;
          const expected =
            it.correct_answer ?? it.correct_category ?? it.correct_position ?? it.correct_rank ?? null;
          const ex = it.explanation || "";
          let detail = "";
          if (!ok && (yours !== null || expected !== null)) {
            detail = ` <span class="muted">(your: ${escapeAttr(
              String(yours),
            )} → correct: ${escapeAttr(String(expected))})</span>`;
          }
          const exHtml = ex
            ? `<div class="muted" style="margin-top:2px;font-size:0.82rem;">${escapeAttr(
                String(ex),
              )}</div>`
            : "";
          return `<li class="${ok ? "fb-correct" : "fb-wrong"}">${escapeAttr(
            String(lbl),
          )}${detail}${exHtml}</li>`;
        })
        .join("") +
      `</ul>`;
  }

  // Canonical correct answer — collapsed by default to avoid spoiling
  // before the learner has tried; only useful on a FAIL submission.
  let canonicalHtml = "";
  if (!pass && feedback.correct_answer !== undefined && feedback.correct_answer !== null) {
    const ca =
      typeof feedback.correct_answer === "object"
        ? JSON.stringify(feedback.correct_answer, null, 2)
        : String(feedback.correct_answer);
    canonicalHtml = `<details><summary>Canonical answer</summary><pre>${escapeAttr(
      ca,
    )}</pre></details>`;
  }

  return `<div class="feedback-panel ${cls}">
    <div class="fb-header">
      <span>${headerIcon} ${headerText}</span>
      <span class="fb-score">${pct}%</span>
    </div>
    ${proseHtml}
    ${itemsHtml}
    ${canonicalHtml}
  </div>`;
}
