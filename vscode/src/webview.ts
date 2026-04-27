/**
 * Step-card WebView — renders a step's briefing inside VS Code with full
 * CSP-safety. Uses the data-action delegator (port from frontend) so
 * widget buttons work without `unsafe-inline`.
 *
 * Per buddy-Opus 2026-04-27 (footgun fix): every WebView includes a
 * "How to run this step" section that opens the integrated terminal
 * pre-populated with the right commands. Without this, terminal-shy
 * learners read the briefing, click Submit, and bounce on "no output".
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

/** Open or focus the step-card panel for a given step. */
export class StepWebViewManager {
  private panel: vscode.WebviewPanel | null = null;

  constructor(private readonly extensionUri: vscode.Uri) {}

  show(input: StepRenderInput, onCheck: () => void, onNext: () => void, onRunInTerminal: () => void): void {
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
    const exType = input.step.exercise_type || "concept";
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

    // Browser deep-link for the same step (in case the learner wants to
    // open the dashboard widget — useful for adaptive_roleplay /
    // simulator_loop where the browser widget IS the work surface).
    const browserUrl = `${input.webBaseUrl.replace(/\/$/, "")}/#${input.courseId}/${input.moduleId}/${Math.max(0, input.step.position - 1)}`;

    // The "How to run" affordance — the footgun fix. For terminal-surface
    // steps, prominent button to open the integrated terminal pre-populated
    // with the right commands. For web-surface steps, prominent "Open in
    // browser" button (the work happens in the dashboard widget).
    const howToRun = surface === "terminal"
      ? `<div class="action-row">
           <button class="primary" data-vsc-msg="runInTerminal">▸ Open Terminal &amp; Run Steps</button>
           <span class="muted">spawns the integrated terminal with the cli_commands ready</span>
         </div>`
      : `<div class="action-row">
           <a class="primary" href="${escapeAttr(browserUrl)}" target="_blank" rel="noopener">▸ Open in Browser</a>
           <span class="muted">interactive widget renders in the dashboard</span>
         </div>`;

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
    .step-header {
      border-left: 4px solid ${accent};
      padding: 12px 18px;
      margin-bottom: 24px;
      background: var(--vscode-sideBar-background);
      border-radius: 0 6px 6px 0;
    }
    .step-header h1 { margin: 0 0 4px 0; font-size: 1.1rem; }
    .step-header .label { color: ${accent}; font-weight: 700; margin-right: 8px; }
    .step-meta { font-size: 0.85rem; opacity: 0.85; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
             font-size: 0.75rem; margin-right: 6px; }
    .badge-surface { background: ${accent}22; color: ${accent}; }
    .badge-type { background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); }
    .badge-attempt { background: var(--vscode-statusBarItem-warningBackground);
                     color: var(--vscode-statusBarItem-warningForeground); }
    .action-row { display: flex; gap: 12px; align-items: center;
                  margin: 18px 0; padding: 14px; border: 1px solid var(--vscode-panel-border);
                  border-radius: 6px; background: var(--vscode-textBlockQuote-background); }
    button.primary, a.primary {
      background: ${accent}; color: white; border: none; padding: 8px 16px;
      border-radius: 4px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
      text-decoration: none;
    }
    button.primary:hover, a.primary:hover { opacity: 0.9; }
    .muted { color: var(--vscode-descriptionForeground); font-size: 0.85rem; }
    .footer-actions { display: flex; gap: 12px; margin-top: 32px; padding-top: 20px;
                       border-top: 1px solid var(--vscode-panel-border); }
    .secondary { background: transparent; color: ${accent}; border: 1px solid ${accent};
                  padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 600; }
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
    <button class="secondary" data-vsc-msg="next">Skip — Next Step</button>
    <a class="secondary" href="${escapeAttr(browserUrl)}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;">Open in Browser ↗</a>
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
