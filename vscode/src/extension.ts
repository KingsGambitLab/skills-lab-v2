/**
 * Skillslab VS Code extension — activation entry point.
 *
 * Architecture (per buddy-Opus 2026-04-27):
 *   - extension.ts:  activation + command registration only (this file)
 *   - auth.ts:        SecretStorage + CLI-token-inheritance consent flow
 *   - api.ts:         LMS REST client (re-uses existing endpoints)
 *   - state.ts:       per-step attempt counters + cursor (globalState)
 *   - tree.ts:        sidebar TreeDataProvider (courses → modules → steps)
 *   - webview.ts:     step-card panel with CSP-safe rendering
 *   - widgets.ts:     onclick → data-action rewrite + nonce'd delegator
 *   - commands.ts:    palette commands, submit-and-continue, run-in-terminal
 *   - theme.ts:       course-themed accent (mirrors cli/theme.py)
 *
 * Security posture (CLAUDE.md hard rule, verbatim):
 *   "we never handle learner API keys"
 *
 * → All keys (Anthropic, GitHub PAT, LMS bearer) live in OS keychain via
 *   VS Code SecretStorage. We never proxy keys through our backend. Same
 *   BYO model as the CLI.
 */
import * as vscode from "vscode";
import { AuthManager } from "./auth";
import { LmsClient } from "./api";
import { StateManager } from "./state";
import { CourseTree } from "./tree";
import { StepWebViewManager } from "./webview";
import { CommandHandlers } from "./commands";

export async function activate(ctx: vscode.ExtensionContext): Promise<void> {
  const auth = new AuthManager(ctx);
  const state = new StateManager(ctx);

  const cfg = () => {
    const c = vscode.workspace.getConfiguration("skillslab");
    return {
      apiUrl: c.get<string>("apiUrl") || "http://52.88.255.208",
      webUrl: c.get<string>("webUrl") || "http://52.88.255.208",
    };
  };

  const api = new LmsClient(auth, () => cfg().apiUrl);
  const tree = new CourseTree(api, state);
  const webview = new StepWebViewManager(ctx.extensionUri);
  const cmds = new CommandHandlers(api, auth, state, tree, webview, cfg);

  // Register the tree view
  ctx.subscriptions.push(vscode.window.registerTreeDataProvider("skillslab.courses", tree));

  // Set initial signed-in context (for menu visibility)
  const bearer = await auth.getBearer();
  await vscode.commands.executeCommand("setContext", "skillslab.signedIn", !!bearer);

  // Register commands
  ctx.subscriptions.push(
    vscode.commands.registerCommand("skillslab.signIn", () => cmds.signIn()),
    vscode.commands.registerCommand("skillslab.signOut", () => cmds.signOut()),
    vscode.commands.registerCommand("skillslab.startCourse", () => cmds.startCourse()),
    vscode.commands.registerCommand("skillslab.openCurrentStep", () => cmds.openCurrentStep()),
    vscode.commands.registerCommand("skillslab.toc", () => cmds.toc()),
    vscode.commands.registerCommand(
      "skillslab.submitAndContinue",
      async () => {
        // No-arg variant — inferred from cursor
        const slug = state.getMostRecentSlug();
        if (!slug) {
          vscode.window.showInformationMessage("No active step. Open one from the sidebar first.");
          return;
        }
        // The WebView's footer button passes the args directly via postMessage;
        // command-palette invocation needs to look up the current step.
        await cmds.openCurrentStep();
        vscode.window.showInformationMessage("Use the WebView panel's 'Submit & Continue' button.");
      },
    ),
    vscode.commands.registerCommand(
      "skillslab.runStepInTerminal",
      async () => {
        await cmds.openCurrentStep();
        vscode.window.showInformationMessage("Use the WebView panel's 'Open Terminal' button.");
      },
    ),
    vscode.commands.registerCommand("skillslab.refreshTree", () => tree.refresh()),
    vscode.commands.registerCommand(
      "skillslab.openStep",
      (courseId: string, moduleId: number, step: any) =>
        cmds.openStep(courseId, moduleId, step),
    ),
    // "Previous Step" — palette + WebView footer button. Mirrors next();
    // does not submit, just decrements cursor + opens the predecessor.
    vscode.commands.registerCommand(
      "skillslab.previousStep",
      async () => {
        const slug = state.getMostRecentSlug();
        if (!slug) {
          vscode.window.showInformationMessage("No active step. Open one from the sidebar first.");
          return;
        }
        const cursor = state.getCursor(slug);
        if (!cursor) return;
        // Walk to find the current step, then call previous(). We don't
        // have the current step object handy at the palette level; the
        // WebView's button passes it via postMessage when the user clicks
        // there. For palette invocation, just use openCurrentStep semantics
        // to get a step then advance from cursor. Simpler: walk the flat
        // list and call previous() with the current step.
        const course = await api.getCourse(cursor.courseId);
        let idx = 0;
        for (const m of course.modules) {
          const mod = await api.getModule(cursor.courseId, m.id);
          for (const s of mod.steps) {
            if (idx === cursor.stepIdx) {
              await cmds.previous(cursor.courseId, m.id, s);
              return;
            }
            idx++;
          }
        }
      },
    ),
  );

  // URI handler — `vscode://tusharbisht1391.skillslab/course/<slug>?step=<sid>`
  // Lets the LMS web dashboard's "Open in VS Code" button deep-link into
  // a specific step. Activated by clicking the button; VS Code intercepts
  // because the publisher.id matches.
  ctx.subscriptions.push(
    vscode.window.registerUriHandler({
      handleUri: async (uri) => {
        // Format: /course/<courseId>?step=<stepId>
        const m = uri.path.match(/^\/course\/([^/]+)$/);
        if (!m) return;
        const courseId = m[1];
        const params = new URLSearchParams(uri.query);
        const stepId = params.get("step");
        try {
          const course = await api.getCourse(courseId);
          for (const mod of course.modules) {
            const sub = await api.getModule(courseId, mod.id);
            const target = stepId
              ? sub.steps.find((s) => String(s.id) === stepId)
              : sub.steps[0];
            if (target) {
              await cmds.openStep(courseId, mod.id, target);
              return;
            }
          }
        } catch (e: any) {
          vscode.window.showErrorMessage(`Could not open ${courseId}: ${e.message || e}`);
        }
      },
    }),
  );

  // Suggest reopen-in-container if a course-repo with .devcontainer/ is open.
  // Footgun fix: terminal-shy learners need claude/aider/etc on PATH; the
  // devcontainer guarantees it. We don't manage Docker ourselves; just
  // delegate to Microsoft's Dev Containers extension via the existing
  // `remote-containers.reopenInContainer` command.
  void cmds.maybeSuggestDevContainer();

  // v0.1.5 Change #2 — re-fire the suggestion when the workspace folder
  // set changes. Today maybeSuggestDevContainer fires only at activation;
  // if the learner opens a course-repo AFTER the extension is already
  // running (Add Folder to Workspace), the prompt never came. Per-folder
  // dedupe inside maybeSuggestDevContainer prevents pestering for
  // folders the learner already declined.
  ctx.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders(() => {
      void cmds.maybeSuggestDevContainer();
    }),
  );

  // v0.1.5 — palette command to manually re-trigger the Reopen flow.
  // Useful when the learner declined the auto-prompt earlier and now
  // wants the toolchain after all. Bypasses the dedupe Set by going
  // through `cmds.reopenInContainer()` directly.
  ctx.subscriptions.push(
    vscode.commands.registerCommand("skillslab.reopenInContainer", () =>
      cmds.reopenInContainer(),
    ),
  );
}

export function deactivate(): void {
  // Nothing to clean up — TreeDataProvider + WebView lifecycles managed by
  // the subscriptions array.
}
