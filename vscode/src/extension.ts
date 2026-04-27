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
}

export function deactivate(): void {
  // Nothing to clean up — TreeDataProvider + WebView lifecycles managed by
  // the subscriptions array.
}
