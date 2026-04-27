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
  /**
   * v0.1.5 Change #3 — toolchain status pill for terminal_exercise steps.
   * 🟢 in-container / 🟢 host-ok / 🔴 host-missing (with the missing tools
   * listed + a "Reopen in Container" button inline) / suppressed for
   * non-terminal steps. Populated by commands.ts:openStep via
   * computeToolchainStatus(step).
   */
  toolchainStatus?: {
    status: "n/a" | "in-container" | "host-ok" | "host-missing";
    missingTools: string[];
  };
}

/**
 * v0.1.13 reframe (per user 2026-04-27): "Something or the other keeps
 * breaking in non coding module slides in vscode. Let's only keep
 * coding exercises on vscode, rest let's redesign the vscode page to
 * take users to web."
 *
 * Architecture:
 *   - VS Code's strength is the editor + integrated terminal — i.e.
 *     CODING work. We keep those exercise types fully rendered.
 *   - Non-coding types (concept slides, drag-drops, simulators,
 *     roleplay) are first-class in the BROWSER dashboard where their
 *     widgets render natively. VS Code redirects to the browser
 *     instead of attempting to render them inline.
 *
 * The set of types we render fully in VS Code's WebView. Everything
 * NOT in this set + non-terminal-surface → renders as a "open in
 * browser" redirect pane (no briefing, no submit — just nav + CTA).
 */
const VSCODE_CODING_TYPES = new Set([
  "code",              // read & run demos
  "code_exercise",     // hands-on coding with hidden_tests
  "code_read",         // read code + explain (only for actual code, not text)
  "fill_in_blank",     // syntax recall (only for actual code, not text)
  "terminal_exercise", // BYO-key CLI flow (M0.S2 etc.)
  "system_build",      // capstone build/deploy with code or terminal
]);

/**
 * Decide whether to redirect to browser. Returns true if the step's
 * widget IS the work surface (and rendering it inline in a WebView
 * is brittle — CSP issues, hoisting, etc.).
 */
function shouldRedirectToBrowser(step: StepSummary): boolean {
  const exType = (step.exercise_type || "concept").toLowerCase();
  const surface = (step.learner_surface || "web").toLowerCase();

  // Terminal-surface = always a CLI step → keep in VS Code (auto-run path).
  if (surface === "terminal") return false;

  // Zero-code variants of code_read / fill_in_blank / system_build — the
  // language is text/markdown/plaintext, the widget is a styled reference
  // block + textarea. Browser renders this better.
  const lang = (((step as any).demo_data || {}).language || "").toLowerCase();
  if (lang === "text" || lang === "markdown" || lang === "plaintext") return true;

  // Coding types stay in VS Code; everything else → redirect.
  return !VSCODE_CODING_TYPES.has(exType);
}

/**
 * Exercise types that have NO submission to grade — purely read-then-advance.
 * For these, hide the "Submit & Continue" button entirely; the "Next ▸"
 * button becomes the primary action and (on the host side) auto-marks the
 * step complete on the way through (mirrors submitAndContinue's concept
 * branch). User feedback 2026-04-27: "Keep submit & continue only for
 * exercises which requires submission."
 *
 * Note: redirect-to-browser steps don't render a submit button in the
 * first place (their entire body is the redirect pane), so this set
 * only matters for the in-VS-Code coding path.
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
    onReopenInContainer?: () => void;
    onShowInstallHints?: () => void;
    onCopyTemplate?: (template: string, path: string) => void;
    onOpenInBuffer?: (template: string, path: string, language: string) => void;
  } = {};

  constructor(private readonly extensionUri: vscode.Uri) {}

  show(
    input: StepRenderInput,
    onCheck: () => void,
    onNext: () => void,
    onRunInTerminal: () => void,
    onPrev: () => void,
    onRunAuto?: () => void,
    onReopenInContainer?: () => void,
    onShowInstallHints?: () => void,
    onCopyTemplate?: (template: string, path: string) => void,
    onOpenInBuffer?: (template: string, path: string, language: string) => void,
  ): void {
    // ALWAYS update callbacks BEFORE reveal/render — the listener below
    // reads via `this.callbacks.X?.()` so this swap is what makes the
    // already-open panel route to the new step.
    this.callbacks = {
      onCheck,
      onNext,
      onPrev,
      onRunInTerminal,
      onRunAuto,
      onReopenInContainer,
      onShowInstallHints,
      onCopyTemplate,
      onOpenInBuffer,
    };

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
          case "reopenInContainer": this.callbacks.onReopenInContainer?.(); break;
          case "showInstallHints": this.callbacks.onShowInstallHints?.(); break;
          case "copyTemplate": {
            const tpl = typeof msg.template === "string" ? msg.template : "";
            const path = typeof msg.path === "string" ? msg.path : "";
            this.callbacks.onCopyTemplate?.(tpl, path);
            break;
          }
          case "openInBuffer": {
            const tpl = typeof msg.template === "string" ? msg.template : "";
            const path = typeof msg.path === "string" ? msg.path : "";
            const lang = typeof msg.language === "string" ? msg.language : "";
            this.callbacks.onOpenInBuffer?.(tpl, path, lang);
            break;
          }
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
    // v0.1.13 — non-coding steps render as a clean "open in browser"
    // redirect pane, not an attempted-render of an interactive widget
    // that breaks under CSP / hoist constraints in a WebView.
    if (shouldRedirectToBrowser(input.step)) {
      return this.renderRedirectHtml(input);
    }
    return this.renderCodingHtml(input);
  }

  /**
   * Full WebView render for CODING steps — terminal_exercise / code_exercise /
   * code_read / fill_in_blank / system_build / code. This is the path with
   * the briefing, spec panel, auto-run terminal button, feedback panel,
   * Submit & Continue / Next, etc. Same shape as pre-v0.1.13.
   */
  private renderCodingHtml(input: StepRenderInput): string {
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
    }
    // v0.1.13: in this code path, the only steps reaching renderCodingHtml
    // are CODING types (terminal_exercise / code_exercise / code_read /
    // fill_in_blank / system_build / code). Non-coding types are routed
    // to renderRedirectHtml upstream. So the prior "BROWSER_WIDGET_TYPES"
    // branch (which served drag-drops + simulators + roleplay) is no
    // longer reachable here — those types redirect. Removed.

    // Footer browser link — kept as a subtle escape hatch for coding
    // steps in case the learner wants the dashboard view too (e.g. to
    // see other learners' submissions, comments, etc.).
    const footerBrowserLink = `<a class="footer-link" href="${escapeAttr(browserUrl)}" target="_blank" rel="noopener">view in browser ↗</a>`;

    // Submit & Continue only renders for steps that actually grade a
    // submission. For pure-read steps (concept), the Next button is
    // promoted to primary + the host auto-marks the step complete on
    // its way through.
    const requiresSubmission = !NO_SUBMIT_TYPES.has(exType);

    // v0.1.5 Change #3 — toolchain status pill. Renders ONLY for
    // terminal-surface steps (status !== "n/a"). For host-missing,
    // includes an inline "Reopen in Container" button that postMsgs
    // back to commands.ts:reopenInContainer.
    const toolchainPill = renderToolchainPill(input.toolchainStatus);

    // Spec panel — for terminal_exercise (and any step with cli_commands
    // / must_contain / rubric in validation), render the SAME spec the
    // CLI surfaces post-2026-04-25 (CLI-walk fix). User feedback
    // 2026-04-27: "Spec needs to be shown here as in the terminal for
    // the user to understand the task at hand." The briefing prose alone
    // doesn't tell the learner WHICH commands to run or WHAT must appear
    // in the output for it to pass.
    // v0.1.14: when this is an authoring step, the spec panel's
    // "What to do" header is relabeled "We'll verify" (those cli_commands
    // are GRADING checks, not authoring instructions — the authoring is
    // in the Files-to-author panel above).
    const specPanel = renderSpecPanel(input.step, { verifyMode: isAuthoringTerminalExercise(input.step) });

    // Feedback panel — most-recent /api/exercises/validate response.
    // Renders at the very top of body so the learner reads it first
    // after submitting. User feedback 2026-04-27: "Submit & Continue
    // should give detailed feedback, similar to terminal." Replaces
    // the toast-only flow that swallowed feedback prose.
    const feedbackPanel = renderFeedbackPanel(input.feedback, accent);

    // v0.1.14 — `📝 Files to author` panel for AUTHORING terminal_exercise
    // steps. Renders BEFORE the spec/verify panel so the learner sees
    // "what to write" before "how we'll grade it". Falls back to empty
    // string for diagnostic steps + courses generated before F5 (no
    // template_files in DB) UNLESS the retrofit heuristic detects
    // authoring (must_contain references files cli_commands probe).
    // User feedback 2026-04-27: "VS code gives no idea about what to do."
    const isAuthoring = isAuthoringTerminalExercise(input.step);
    const filesToAuthorPanel = isAuthoring
      ? renderFilesToAuthorPanel(input.step)
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

    /* ── Files-to-author panel (v0.1.14) ──
       Shown for AUTHORING terminal_exercise steps. Per buddy-Opus review:
       the code blocks must be visually unambiguous as REFERENCE (not editor).
       No cursor on hover, no edit affordance. Copy-to-clipboard is the
       primary action; "open in untitled buffer" is the safer alternative
       to auto-write-to-workspace (avoids dirty-tree / wrong-cwd footguns). */
    .files-to-author {
      margin: 16px 0 22px;
      padding: 14px 18px 18px;
      background: var(--vscode-sideBar-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
    }
    .files-to-author > h3 {
      margin: 0 0 14px;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--vscode-foreground);
    }
    .files-to-author > .panel-intro {
      font-size: 0.85rem;
      color: var(--vscode-descriptionForeground);
      margin: 0 0 14px;
      line-height: 1.55;
    }
    .file-card {
      margin-bottom: 16px;
      padding: 0;
      background: var(--vscode-textBlockQuote-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      overflow: hidden;
    }
    .file-card:last-child { margin-bottom: 0; }
    .file-card .file-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      background: var(--vscode-editorWidget-background, var(--vscode-sideBar-background));
      border-bottom: 1px solid var(--vscode-panel-border);
    }
    .file-card .file-path {
      font-family: var(--vscode-editor-font-family);
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--vscode-foreground);
      flex: 1 1 auto;
    }
    .file-card .file-language-pill {
      font-size: 0.7rem;
      padding: 2px 7px;
      background: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
      border-radius: 3px;
      font-family: var(--vscode-editor-font-family);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .file-card .file-optional {
      font-size: 0.72rem;
      padding: 2px 7px;
      background: transparent;
      color: var(--vscode-descriptionForeground);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 3px;
    }
    .file-card .file-actions {
      display: flex;
      gap: 6px;
      flex: 0 0 auto;
    }
    .file-card .file-actions button {
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      border: 1px solid transparent;
      padding: 4px 10px;
      font-size: 0.78rem;
      font-weight: 500;
      border-radius: 3px;
      cursor: pointer;
    }
    .file-card .file-actions button:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    .file-card pre.file-template {
      margin: 0;
      padding: 12px 14px;
      background: var(--vscode-textCodeBlock-background);
      color: var(--vscode-editor-foreground);
      font-family: var(--vscode-editor-font-family);
      font-size: 0.85rem;
      line-height: 1.55;
      overflow-x: auto;
      max-height: 360px;
      overflow-y: auto;
      /* Make it visually unambiguous as a REFERENCE, not an editor:
         no caret on hover, no text-input affordance. Copy/Open buttons
         in the header are the only ways to interact. */
      cursor: default;
      user-select: text;          /* still selectable for manual copy */
      white-space: pre;
    }
    .file-card .file-hints {
      padding: 10px 14px;
      font-size: 0.8rem;
      color: var(--vscode-descriptionForeground);
      background: var(--vscode-sideBar-background);
      border-top: 1px solid var(--vscode-panel-border);
      line-height: 1.5;
    }
    .file-card .file-hints strong { color: var(--vscode-foreground); }

    /* ── Toolchain status pill (terminal_exercise only, v0.1.5) ── */
    .toolchain-pill {
      display: flex; align-items: center; gap: 10px;
      margin: 0 0 14px;
      padding: 8px 14px;
      border-radius: 4px;
      font-size: 0.85rem;
      border: 1px solid var(--vscode-panel-border);
    }
    .toolchain-pill.in-container,
    .toolchain-pill.host-ok {
      background: var(--vscode-inputValidation-infoBackground,
                        var(--vscode-textBlockQuote-background));
      border-left: 3px solid var(--vscode-charts-green, #2dd4bf);
    }
    .toolchain-pill.host-missing {
      background: var(--vscode-inputValidation-warningBackground,
                        var(--vscode-textBlockQuote-background));
      border-left: 3px solid var(--vscode-charts-red, #f97316);
    }
    .toolchain-pill .pill-icon { font-size: 1rem; }
    .toolchain-pill .pill-text { flex: 1; }
    .toolchain-pill button {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none; padding: 4px 10px; border-radius: 3px;
      font-size: 0.8rem; cursor: pointer; font-weight: 500;
    }
    .toolchain-pill button:hover { background: var(--vscode-button-hoverBackground); }

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

  ${toolchainPill}

  ${howToRun}

  <div class="step-body">${bodyHtml}</div>

  ${filesToAuthorPanel}

  ${specPanel}

  <div class="footer-actions">
    ${requiresSubmission ? `<button class="primary" data-vsc-msg="submit">▸ Submit &amp; Continue</button>` : ``}
    <button class="secondary" data-vsc-msg="prev" title="Go to previous step">◂ Previous</button>
    <button class="${requiresSubmission ? `secondary` : `primary`}" data-vsc-msg="next" title="Go to next step">Next ▸</button>
    <span class="footer-spacer"></span>
    ${footerBrowserLink}
  </div>

  <script nonce="${nonce}">
    // Wire footer + how-to-run buttons through to the host extension.
    // v0.1.14: copyTemplate / openInBuffer carry template + path + language
    // as data-* attributes (URI-encoded so newlines + quotes survive).
    document.addEventListener('click', function(e) {
      const el = e.target.closest && e.target.closest('[data-vsc-msg]');
      if (!el) return;
      e.preventDefault();
      const acquireVsCodeApi = window['acquireVsCodeApi'];
      const vscode = (window.__vscApi = window.__vscApi || (acquireVsCodeApi && acquireVsCodeApi()));
      if (!vscode) return;
      const type = el.getAttribute('data-vsc-msg');
      const msg = { type: type };
      // For Files-to-author actions, decode the template + path + language
      // and ship them inline.
      if (type === 'copyTemplate' || type === 'openInBuffer') {
        try {
          const enc = el.getAttribute('data-template-encoded') || '';
          msg.template = decodeURIComponent(enc);
        } catch (_) { msg.template = ''; }
        msg.path = el.getAttribute('data-file-path') || '';
        msg.language = el.getAttribute('data-file-language') || '';
      }
      vscode.postMessage(msg);
    });
    // Re-injected widget runtime (data-action delegator + hoist).
    ${scriptBundle}
  </script>
</body>
</html>`;
  }

  /**
   * v0.1.13 — render the "open in browser" redirect pane for non-coding
   * exercise types (concept slides, scenario_branch, drag-drops,
   * simulators, roleplay, voice interviews). No briefing render, no
   * spec panel, no submit button — just a clean "this lives in the
   * browser" CTA + nav buttons. Avoids the CSP/hoist breakage that
   * embedding interactive widgets in a WebView produces.
   *
   * Reasoning is summarized for the learner: "VS Code is for the
   * coding work; the browser is where the interactive widgets live."
   * Reduces confusion + sets expectation that some steps are
   * intentionally browser-side.
   */
  private renderRedirectHtml(input: StepRenderInput): string {
    const stepLabel = labelOf(input);
    const exType = (input.step.exercise_type || "concept").toLowerCase();
    const accent = input.themeAccent;
    const attemptBadge =
      input.attemptCount >= 1
        ? `<span class="badge badge-attempt">attempt ${input.attemptCount + 1}</span>`
        : "";

    const cspWebView = this.panel!.webview.cspSource;
    // Tiny inline script handles the prev/next button postMessages — needs
    // a nonce'd script-src like the coding render does. Generate a fresh
    // nonce per render.
    const nonce = generateNonceLocal();
    const csp = [
      `default-src 'none'`,
      `style-src 'unsafe-inline' ${cspWebView}`,
      `img-src ${cspWebView} https: data:`,
      `script-src 'nonce-${nonce}'`,
    ].join("; ");

    const browserUrl = `${input.webBaseUrl.replace(/\/$/, "")}/#${input.courseId}/${input.moduleId}/${Math.max(0, input.step.position - 1)}`;

    // Short reason text — varies by type so the learner knows WHY the
    // browser is the right surface for this particular step.
    const reasonText: Record<string, string> = {
      concept: "Concept slides often have interactive widgets (visualizers, command explorers, decision trees) that render natively in the browser.",
      scenario_branch: "Scenario branches are interactive decision trees with branching consequences — the browser dashboard renders them as a click-through experience.",
      simulator_loop: "Live simulations (tick-based dashboards, evolving state, action panels) render as a multi-pane widget in the browser.",
      incident_console: "The incident console is a 4-pane simulator (alert banner, log tail, shell, Slack) — designed for the browser dashboard.",
      categorization: "Drag-and-drop categorization works best with the browser's native drag-drop API.",
      ordering: "Drag-to-reorder works best with the browser's native drag-drop API.",
      parsons: "Code-line drag-and-drop assembly works best with the browser's native drag-drop API.",
      sjt: "Ranking-style judgment exercises render as interactive option-rankers in the browser.",
      mcq: "Quick knowledge-check questions render best as a clickable option list in the browser.",
      adaptive_roleplay: "Adaptive roleplay is a turn-based chat with hidden state — the browser shows the full debrief panel + state trajectory after the session.",
      voice_mock_interview: "Voice mock interviews use the browser's microphone + speech-synthesis APIs — VS Code WebViews can't access those.",
      code_review: "Code review exercises (clicking suspected bug lines) render as an annotated code viewer in the browser.",
    };
    const reason =
      reasonText[exType] ||
      "This step's interactive content renders natively in the browser dashboard.";

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
      border-left: 3px solid ${accent};
      padding: 10px 16px;
      margin-bottom: 22px;
      background: var(--vscode-sideBar-background);
      border-radius: 0 4px 4px 0;
    }
    .step-header h1 { margin: 0 0 4px 0; font-size: 1.05rem; font-weight: 600; }
    .step-header .label { color: ${accent}; font-weight: 700; margin-right: 8px; }
    .step-meta { font-size: 0.82rem; opacity: 0.85; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
             font-size: 0.72rem; margin-right: 6px; font-weight: 500;
             background: var(--vscode-badge-background);
             color: var(--vscode-badge-foreground); }
    .badge-attempt { background: var(--vscode-statusBarItem-warningBackground);
                     color: var(--vscode-statusBarItem-warningForeground); }

    .redirect-pane {
      display: flex; flex-direction: column; align-items: center;
      text-align: center;
      padding: 48px 24px;
      margin: 16px 0 32px;
      background: var(--vscode-textBlockQuote-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 6px;
    }
    .redirect-icon {
      font-size: 3rem;
      margin-bottom: 16px;
      opacity: 0.85;
    }
    .redirect-pane h2 {
      margin: 0 0 12px 0;
      font-size: 1.15rem;
      font-weight: 600;
      color: var(--vscode-foreground);
    }
    .redirect-pane p {
      max-width: 520px;
      margin: 0 0 20px 0;
      font-size: 0.92rem;
      color: var(--vscode-descriptionForeground);
      line-height: 1.6;
    }
    .redirect-pane a.cta {
      background: ${accent};
      color: white;
      border: none;
      padding: 11px 22px;
      border-radius: 4px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      margin-bottom: 14px;
    }
    .redirect-pane a.cta:hover { opacity: 0.88; }
    .redirect-pane .followup {
      font-size: 0.82rem;
      color: var(--vscode-descriptionForeground);
      margin-top: 8px;
      max-width: 480px;
    }

    .footer-actions { display: flex; gap: 10px; align-items: center;
                       margin-top: 28px; padding-top: 18px;
                       border-top: 1px solid var(--vscode-panel-border); }
    .footer-spacer { flex: 1; }
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
    button.primary {
      background: ${accent};
      color: white;
      border: none;
      padding: 7px 16px;
      border-radius: 3px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
    }
    button.primary:hover { opacity: 0.88; }
  </style>
</head>
<body>
  <div class="step-header">
    <h1><span class="label">${escapeAttr(stepLabel)}</span>${escapeAttr(input.step.title || "")}</h1>
    <div class="step-meta">
      <span class="badge">${escapeAttr(exType)}</span>
      ${attemptBadge}
      <span style="opacity: 0.85;">module: ${escapeAttr(input.moduleTitle)}</span>
    </div>
  </div>

  <div class="redirect-pane">
    <div class="redirect-icon">🌐</div>
    <h2>This step lives in the browser</h2>
    <p>${escapeAttr(reason)} VS Code is where you do the actual coding work — terminal commands, code edits, capstones.</p>
    <a class="cta" href="${escapeAttr(browserUrl)}" target="_blank" rel="noopener">▸ Open in Browser</a>
    <div class="followup">When you finish in the browser, click <strong>Next ▸</strong> below to advance to the next step. Coding modules render fully here.</div>
  </div>

  <div class="footer-actions">
    <button class="secondary" data-vsc-msg="prev" title="Go to previous step">◂ Previous</button>
    <button class="primary" data-vsc-msg="next" title="Go to next step">Next ▸</button>
    <span class="footer-spacer"></span>
  </div>

  <script nonce="${nonce}">
    document.addEventListener('click', function(e) {
      const el = e.target.closest && e.target.closest('[data-vsc-msg]');
      if (!el) return;
      e.preventDefault();
      const acquireVsCodeApi = window['acquireVsCodeApi'];
      const vscode = (window.__vscApi = window.__vscApi || (acquireVsCodeApi && acquireVsCodeApi()));
      if (vscode) vscode.postMessage({ type: el.getAttribute('data-vsc-msg') });
    });
  </script>
</body>
</html>`;
  }
}

/**
 * Local nonce generator for renderRedirectHtml (avoids needing to import
 * widgets.ts:generateNonce — keeps the redirect path self-contained).
 */
function generateNonceLocal(len = 24): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let s = "";
  for (let i = 0; i < len; i++) s += chars.charAt(Math.floor(Math.random() * chars.length));
  return s;
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
 * Render the TOOLCHAIN STATUS PILL for terminal_exercise steps (v0.1.5
 * Change #3). Surfaces 🟢/🔴 + missing-tools list + a "Reopen in
 * Container" button that posts `reopenInContainer` back to the host.
 *
 * Returns "" for non-terminal steps so the WebView doesn't show a
 * misleading pill on concept / browser-widget steps.
 */
function renderToolchainPill(
  status: StepRenderInput["toolchainStatus"] | undefined,
): string {
  if (!status || status.status === "n/a") return "";
  if (status.status === "host-ok") {
    // v0.1.10 — host-ok is the PRIMARY success state. Host install is
    // the recommended path; the learner's own machine = the skill they're
    // taking back to work.
    return `<div class="toolchain-pill host-ok">
      <span class="pill-icon">🟢</span>
      <span class="pill-text">Host toolchain ready — required tools detected on PATH</span>
    </div>`;
  }
  if (status.status === "in-container") {
    // Devcontainer is now the escape hatch — still "ready" but framed
    // as a fallback path, not the recommended one.
    return `<div class="toolchain-pill in-container">
      <span class="pill-icon">🟢</span>
      <span class="pill-text">Devcontainer escape hatch active — toolchain pre-installed (aider · python3 · git · gh)</span>
    </div>`;
  }
  // host-missing — primary CTA is "Show install steps" (the install IS
  // the skill); devcontainer is a secondary escape-hatch link.
  const missing = (status.missingTools || []).map(escapeAttr).join(", ");
  return `<div class="toolchain-pill host-missing">
    <span class="pill-icon">🔴</span>
    <span class="pill-text">Missing on PATH: <strong>${missing}</strong>. Installing these on your machine is part of the course (skill transfer).</span>
    <button data-vsc-msg="showInstallHints">Show install steps</button>
    <a class="footer-link" href="#" data-vsc-msg="reopenInContainer" style="margin-left: 8px; font-size: 0.8rem;">or use devcontainer →</a>
  </div>`;
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
/**
 * v0.1.14 — detect whether a terminal_exercise step is AUTHORING (learner
 * writes config/doc files) vs DIAGNOSTIC (learner runs prepared cmds).
 *
 * Per CLAUDE.md §"EXECUTION IS GROUND TRUTH" + user directive 2026-04-27
 * "Make sure to not rely on regex, it is brittle" — we use ONLY the
 * EXPLICIT signals on the step:
 *
 *   1. `step.task_kind === "authoring"` (set by F5+ Creator)
 *   2. `step.demo_data.template_files` is a non-empty array (the
 *      structural payload that gates the Files-to-author panel)
 *
 * Either is sufficient. NO regex on cli_commands shape, NO heuristic
 * inference from titles. Existing pre-F5 rows that should render as
 * authoring need to be regenerated — the regen pass picks up the new
 * Creator prompt + emits task_kind + template_files explicitly.
 */
function isAuthoringTerminalExercise(step: StepSummary): boolean {
  const stepAny = step as any;
  if ((stepAny.task_kind || "").toString().toLowerCase() === "authoring") {
    return true;
  }
  const dd = stepAny.demo_data || {};
  return Array.isArray(dd.template_files) && dd.template_files.length > 0;
}

/**
 * Render the FILES-TO-AUTHOR panel (v0.1.14, per F5 Creator schema +
 * buddy-Opus tightenings). Reads `step.demo_data.template_files`. For
 * each file: path + language pill + non-editable code block (visually
 * unambiguous as a REFERENCE, not an editor — no caret on hover, no
 * edit affordance) + Copy-to-clipboard + Open-in-buffer buttons +
 * optional hints below.
 *
 * Returns "" if no template_files are present (renderer falls back to
 * the existing spec panel only — preserves behavior for diagnostic
 * steps + pre-F5 courses).
 */
function renderFilesToAuthorPanel(step: StepSummary): string {
  const stepAny = step as any;
  const dd = stepAny.demo_data || {};
  const files: any[] = Array.isArray(dd.template_files) ? dd.template_files : [];
  if (files.length === 0) return "";

  // Infer language from extension when override is absent.
  const inferLang = (path: string): string => {
    const ext = (path.split(".").pop() || "").toLowerCase();
    const map: Record<string, string> = {
      md: "markdown",
      yml: "yaml",
      yaml: "yaml",
      json: "json",
      toml: "toml",
      conf: "ini",
      cfg: "ini",
      py: "python",
      ts: "typescript",
      js: "javascript",
      sh: "bash",
      txt: "plaintext",
    };
    return map[ext] || "plaintext";
  };

  const cards = files
    .map((f, idx) => {
      const path = String(f.path || `file-${idx + 1}`);
      const template = String(f.template ?? f.contents ?? ""); // back-compat
      const language = String(f.language || inferLang(path));
      const optional = !!f.optional;
      const hints = f.hints ? String(f.hints) : "";
      const placeholders: any[] = Array.isArray(f.placeholder_regions)
        ? f.placeholder_regions
        : [];
      // Inline placeholder hint summary (top-of-card guidance).
      const placeholderHint = placeholders
        .map(
          (pr) =>
            `<li>Lines ${escapeAttr(String(pr.start_line || "?"))}–${escapeAttr(String(pr.end_line || "?"))}: ${escapeAttr(String(pr.instruction || ""))}</li>`,
        )
        .join("");

      // The template content is HTML-escaped + wrapped in <pre><code> so
      // it visually reads as code. Non-editable styling enforced via CSS.
      // The data-template attribute carries the raw template for the
      // copy/open postMessage handlers (encoded so newlines + quotes
      // survive HTML attribute escaping).
      const encoded = encodeURIComponent(template);
      return `
        <div class="file-card">
          <div class="file-header">
            <span class="file-path">${escapeAttr(path)}</span>
            <span class="file-language-pill">${escapeAttr(language)}</span>
            ${optional ? `<span class="file-optional">optional</span>` : ""}
            <div class="file-actions">
              <button data-vsc-msg="copyTemplate"
                      data-template-encoded="${encoded}"
                      title="Copy this template to your clipboard">Copy</button>
              <button data-vsc-msg="openInBuffer"
                      data-template-encoded="${encoded}"
                      data-file-path="${escapeAttr(path)}"
                      data-file-language="${escapeAttr(language)}"
                      title="Open in a new untitled VS Code editor (paste-and-save yourself)">Open in editor</button>
            </div>
          </div>
          <pre class="file-template">${escapeAttr(template)}</pre>
          ${
            hints || placeholderHint
              ? `<div class="file-hints">
                   ${hints ? `<div>${escapeAttr(hints)}</div>` : ""}
                   ${placeholderHint ? `<div style="margin-top:6px;"><strong>Fill-in spots:</strong><ul style="margin:4px 0 0; padding-left:18px;">${placeholderHint}</ul></div>` : ""}
                 </div>`
              : ""
          }
        </div>`;
    })
    .join("");

  return `
    <div class="files-to-author">
      <h3>📝 Files to author</h3>
      <p class="panel-intro">
        These are the files this step asks you to write. Each card below shows a
        starter template — <strong>copy or open in a new editor</strong>, then
        edit + save in your workspace. The "We'll verify" panel further down
        shows what we'll check after you save.
      </p>
      ${cards}
    </div>`;
}

function renderSpecPanel(
  step: StepSummary,
  opts?: { verifyMode?: boolean },
): string {
  const v = (step.validation || {}) as any;
  const sections: string[] = [];
  // v0.1.14: when called from an AUTHORING terminal_exercise context
  // (Files-to-author panel above), the cli_commands header relabels to
  // "🔍 We'll verify" — those commands ARE the grading probes, not
  // authoring instructions.
  const verifyMode = !!(opts && opts.verifyMode);
  const cliHeader = verifyMode ? "🔍 We'll verify" : "📋 What to do";

  // ── cli_commands list (terminal_exercise) ──
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
      `<div class="spec-section"><h3>${cliHeader}</h3><ol>${items}</ol></div>`,
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
