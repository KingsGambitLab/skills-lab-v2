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
import { StepSummary } from "./api";

export interface StepRenderInput {
  courseId: string;
  moduleId: number;
  moduleTitle: string;
  step: StepSummary;
  modulePos: number;        // 1-indexed module position from API
  attemptCount: number;     // 0 if never submitted
  themeAccent: string;      // hex/CSS color from getThemeForCourse
  webBaseUrl: string;       // for "Open in browser" links
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

/** Open or focus the step-card panel for a given step. */
export class StepWebViewManager {
  private panel: vscode.WebviewPanel | null = null;

  constructor(private readonly extensionUri: vscode.Uri) {}

  show(
    input: StepRenderInput,
    onCheck: () => void,
    onNext: () => void,
    onRunInTerminal: () => void,
    onPrev: () => void,
  ): void {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Beside, true);
    } else {
      this.panel = vscode.window.createWebviewPanel(
        "skillslab.step",
        `${labelOf(input)} — Skillslab`,
        { viewColumn: vscode.ViewColumn.Beside, preserveFocus: false },
        { enableScripts: true, retainContextWhenHidden: true },
      );
      this.panel.onDidDispose(() => { this.panel = null; });
      this.panel.webview.onDidReceiveMessage((msg) => {
        if (!msg || typeof msg !== "object") return;
        switch (msg.type) {
          case "submit": onCheck(); break;
          case "next": onNext(); break;
          case "prev": onPrev(); break;
          case "runInTerminal": onRunInTerminal(); break;
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
      howToRun = `
        <div class="action-row">
          <button class="primary" data-vsc-msg="runInTerminal">▸ Open Terminal &amp; Run Steps</button>
          <span class="muted">spawns the integrated terminal with the cli_commands ready</span>
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

  ${howToRun}

  <div class="step-body">${bodyHtml}</div>

  <div class="footer-actions">
    <button class="primary" data-vsc-msg="submit">▸ Submit &amp; Continue</button>
    <button class="secondary" data-vsc-msg="prev" title="Go to previous step">◂ Previous</button>
    <button class="secondary" data-vsc-msg="next" title="Skip without submitting">Skip ▸</button>
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
