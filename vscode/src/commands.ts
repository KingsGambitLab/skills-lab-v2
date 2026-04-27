/**
 * Command palette + URI handler logic.
 *
 * Per buddy-Opus 2026-04-27:
 *   - Cut status bar from v1 (low signal, costs activation events).
 *   - Merge `next` + `check` into a single context-aware command:
 *     `skillslab.submitAndContinue` — does check first; if pass, advances
 *     cursor; if fail, leaves cursor where it was.
 *   - Footgun fix: `runStepInTerminal` opens the integrated terminal
 *     pre-populated with cli_commands so terminal-shy learners have a
 *     guided entry point.
 *
 * Devcontainer detection:
 *   On activation, if the workspace has `.devcontainer/devcontainer.json`,
 *   suggest "Reopen in Container" via the existing Microsoft Dev Containers
 *   extension (no Docker management of our own).
 */
import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { LmsClient, StepSummary } from "./api";
import { AuthManager } from "./auth";
import { StateManager } from "./state";
import { CourseTree } from "./tree";
import { StepWebViewManager, StepRenderInput } from "./webview";
import { courseThemeAccent } from "./theme";

export class CommandHandlers {
  constructor(
    private readonly api: LmsClient,
    private readonly auth: AuthManager,
    private readonly state: StateManager,
    private readonly tree: CourseTree,
    private readonly webview: StepWebViewManager,
    private readonly cfg: () => { apiUrl: string; webUrl: string },
  ) {}

  // ── Auth ────────────────────────────────────────────────────────

  async signIn(): Promise<void> {
    const email = await vscode.window.showInputBox({
      title: "Skillslab Sign In",
      prompt: "Email",
      placeHolder: "you@example.com",
      ignoreFocusOut: true,
    });
    if (!email) return;
    const password = await vscode.window.showInputBox({
      title: "Skillslab Sign In",
      prompt: "Password",
      password: true,
      ignoreFocusOut: true,
    });
    if (!password) return;
    try {
      const resp = await this.api.loginWithPassword(email, password);
      await this.auth.setBearer(resp.token, {
        id: resp.user_id,
        email: resp.email,
        role: "learner",
      });
      vscode.window.showInformationMessage(`Signed in as ${resp.email}`);
      this.tree.refresh();
    } catch (e: any) {
      vscode.window.showErrorMessage(`Sign-in failed: ${e.message || e}`);
    }
  }

  async signOut(): Promise<void> {
    await this.auth.clear();
    vscode.window.showInformationMessage("Signed out.");
    this.tree.refresh();
  }

  // ── Course start ───────────────────────────────────────────────

  async startCourse(): Promise<void> {
    let courses;
    try {
      courses = await this.api.allCourses();
    } catch (e: any) {
      vscode.window.showErrorMessage(`Failed to load courses: ${e.message || e}`);
      return;
    }
    if (courses.length === 0) {
      vscode.window.showInformationMessage("No courses available.");
      return;
    }
    const pick = await vscode.window.showQuickPick(
      courses.map((c) => ({
        label: c.title,
        description: c.level || "",
        detail: c.subtitle || c.description || "",
        course: c,
      })),
      { title: "Pick a course to start", matchOnDescription: true, matchOnDetail: true },
    );
    if (!pick) return;
    // Enroll (idempotent)
    try {
      await this.api.enroll(pick.course.id);
    } catch (e: any) {
      // 401 → not signed in. 409 → already enrolled (fine).
      if (e.status === 401) {
        const choice = await vscode.window.showInformationMessage(
          "Sign in to enroll + track progress?",
          "Sign In",
          "Browse Anonymously",
        );
        if (choice === "Sign In") {
          await this.signIn();
          return await this.startCourse();
        }
      }
    }
    // Set cursor to step 0
    this.state.setCursor(pick.course.id, pick.course.id, 0);
    // Open the first step
    const full = await this.api.getCourse(pick.course.id);
    if (full.modules.length > 0) {
      const firstMod = full.modules[0];
      const modSteps = await this.api.getModule(pick.course.id, firstMod.id);
      if (modSteps.steps.length > 0) {
        await this.openStep(pick.course.id, firstMod.id, modSteps.steps[0]);
      }
    }
    this.tree.refresh();
  }

  // ── Step open / submit / next ───────────────────────────────────

  async openStep(courseId: string, moduleId: number, step: StepSummary): Promise<void> {
    // Refetch the full step (the tree only carries summary fields)
    const full = await this.api.getModule(courseId, moduleId);
    const detailedStep = full.steps.find((s) => s.id === step.id) || step;
    const courseSummary = (await this.api.allCourses()).find((c) => c.id === courseId);
    const courseTitle = courseSummary?.title || "";
    const modulePos = full.steps[0]
      ? // module's position is encoded server-side; we get the module's
        // position by fetching the course and finding it
        ((await this.api.getCourse(courseId)).modules.find((m) => m.id === moduleId)?.position || 1)
      : 1;
    const accent = courseThemeAccent(courseTitle);
    const attemptCount = this.state.getAttempt(courseId, detailedStep.id);
    // Update cursor to this step's position-index
    this.state.setCursor(courseId, courseId, detailedStep.position - 1);
    const input: StepRenderInput = {
      courseId,
      moduleId,
      moduleTitle: full.title,
      step: detailedStep,
      modulePos,
      attemptCount,
      themeAccent: accent,
      webBaseUrl: this.cfg().webUrl,
    };
    this.webview.show(
      input,
      () => void this.submitAndContinue(courseId, moduleId, detailedStep),
      () => void this.next(courseId, moduleId, detailedStep),
      () => void this.runStepInTerminal(detailedStep),
    );
  }

  async openCurrentStep(): Promise<void> {
    const slug = this.state.getMostRecentSlug();
    if (!slug) {
      vscode.window.showInformationMessage("No active course. Run 'Skillslab: Start a Course…' first.");
      return;
    }
    const cursor = this.state.getCursor(slug);
    if (!cursor) return;
    // Walk modules to find the step at the cursor's flat index
    const course = await this.api.getCourse(cursor.courseId);
    let idx = 0;
    for (const m of course.modules) {
      const mod = await this.api.getModule(cursor.courseId, m.id);
      for (const s of mod.steps) {
        if (idx === cursor.stepIdx) {
          await this.openStep(cursor.courseId, m.id, s);
          return;
        }
        idx++;
      }
    }
  }

  /**
   * Submit & Continue — context-aware (replaces separate `check` + `next`).
   * - Records an attempt
   * - POST /api/exercises/validate with attempt_number
   * - On `correct: true`: marks complete, advances cursor, opens next step
   * - On `correct: false`: shows feedback in WebView (re-renders), cursor stays
   */
  async submitAndContinue(courseId: string, moduleId: number, step: StepSummary): Promise<void> {
    const slug = courseId; // we key per-courseId in extension state
    const attempt = this.state.recordAttempt(slug, step.id);

    // For terminal_exercise steps, the "submission" is the captured cli_commands
    // output. The extension v1 doesn't auto-run those — it relies on the learner
    // having run them in the integrated terminal first. Caller can pass actual
    // captured text via the WebView postMessage in v1.1.
    // For concept / web-surface steps with no submission, we pass empty data;
    // grader will still attempt to mark complete via /api/progress/complete
    // for concept steps below.

    let response: any = {};
    let validated: any = null;
    const exType = (step.exercise_type || "concept").toLowerCase();
    const surface = (step.learner_surface || "web").toLowerCase();

    if (exType === "concept") {
      // Concept steps: no validation; just mark complete.
      try {
        await this.api.markComplete(step.id, 100);
        validated = { correct: true, score: 1.0, feedback: "Concept step marked complete." };
      } catch (e: any) {
        vscode.window.showErrorMessage(`Mark-complete failed: ${e.message || e}`);
        return;
      }
    } else {
      // For real exercises, learner needs to provide submission. If terminal,
      // suggest they run-in-terminal first (the runStepInTerminal command
      // captures output via clipboard or terminal logs in v1.1).
      if (surface === "terminal") {
        const choice = await vscode.window.showInformationMessage(
          `Have you run the cli_commands for ${labelOf(step)}? Submission grades the captured output.`,
          "Run them now",
          "I already ran them — submit empty",
          "Cancel",
        );
        if (choice === "Run them now") {
          await this.runStepInTerminal(step);
          return;
        }
        if (choice === "Cancel" || !choice) return;
        // "submit empty" → validate with empty payload (will likely score 0,
        // which lets the grader's reveal-gate trip naturally on attempt 3)
      }
      try {
        validated = await this.api.validate(step.id, exType, response, attempt);
      } catch (e: any) {
        vscode.window.showErrorMessage(`Submit failed: ${e.message || e}`);
        return;
      }
    }

    if (validated.correct) {
      const score = validated.score || 1.0;
      try {
        await this.api.markComplete(step.id, Math.round(score * 100));
      } catch (e: any) {
        // Already-complete is fine; surface other errors
        if (e.status !== 409) {
          vscode.window.showWarningMessage(`Pass detected, sync warning: ${e.message || e}`);
        }
      }
      vscode.window.showInformationMessage(
        `✓ ${labelOf(step)} complete — score ${Math.round(score * 100)}%.`,
      );
      // Advance cursor + open next step
      const cursor = this.state.getCursor(slug);
      if (cursor) {
        this.state.setCursor(slug, courseId, cursor.stepIdx + 1);
      }
      this.tree.refresh();
      await this.next(courseId, moduleId, step);
    } else {
      const pct = Math.round((validated.score || 0) * 100);
      const fb = validated.feedback || "Try again — re-read the briefing + iterate.";
      vscode.window.showWarningMessage(
        `${pct}% — ${fb.slice(0, 120)}`,
        "Open WebView",
      );
    }
  }

  /** Advance cursor + open next step (skip without submit). */
  async next(courseId: string, moduleId: number, _step: StepSummary): Promise<void> {
    const slug = courseId;
    const cursor = this.state.getCursor(slug);
    if (!cursor) {
      vscode.window.showInformationMessage("No active course.");
      return;
    }
    // Find next step across modules
    const course = await this.api.getCourse(courseId);
    const flat: { mid: number; step: StepSummary }[] = [];
    for (const m of course.modules) {
      const mod = await this.api.getModule(courseId, m.id);
      for (const s of mod.steps) flat.push({ mid: m.id, step: s });
    }
    const nextIdx = cursor.stepIdx + 1;
    if (nextIdx >= flat.length) {
      vscode.window.showInformationMessage("🎉 Course complete!");
      return;
    }
    const next = flat[nextIdx];
    this.state.setCursor(slug, courseId, nextIdx);
    await this.openStep(courseId, next.mid, next.step);
    this.tree.refresh();
  }

  /**
   * Open the integrated terminal pre-populated with the step's cli_commands.
   * This is the footgun fix from the buddy-Opus consult: terminal-shy learners
   * need a guided entry point. They click a button; the terminal opens with
   * the right `gh repo fork` / `claude` / `pytest` already typed.
   */
  async runStepInTerminal(step: StepSummary): Promise<void> {
    const cmds: { cmd: string; label?: string }[] =
      (step.validation && step.validation.cli_commands) || [];
    if (cmds.length === 0) {
      vscode.window.showInformationMessage(
        `${labelOf(step)} has no cli_commands. Read the briefing for what to run.`,
      );
      return;
    }
    const term = vscode.window.createTerminal({
      name: `Skillslab · ${labelOf(step)}`,
      env: {
        SKILLSLAB_API_URL: this.cfg().apiUrl,
        SKILLSLAB_WEB_URL: this.cfg().webUrl,
        ANTHROPIC_API_KEY: (await this.auth.getApiKey("anthropic")) || "",
        OPENROUTER_API_KEY: "",
        GITHUB_TOKEN: (await this.auth.getApiKey("github")) || "",
      },
    });
    term.show();
    // Echo the briefing label, then send each cmd. Don't auto-execute the
    // last one — let the learner press Enter so they SEE what's about to
    // happen (no surprise actions).
    term.sendText(`# ${labelOf(step)} — ${step.title || ""}`, true);
    for (let i = 0; i < cmds.length; i++) {
      const c = cmds[i];
      const isLast = i === cmds.length - 1;
      term.sendText(`# ${i + 1}/${cmds.length}: ${c.label || ""}`, true);
      term.sendText(c.cmd, !isLast); // last one: don't auto-press Enter
    }
  }

  // ── ToC ─────────────────────────────────────────────────────────

  async toc(): Promise<void> {
    // Re-uses the tree view — just focus it. The tree IS the table of
    // contents (with ✓/▶/◯ states per step).
    await vscode.commands.executeCommand("workbench.view.extension.skillslab");
  }

  // ── Devcontainer detection ──────────────────────────────────────

  /** If the workspace has `.devcontainer/devcontainer.json`, suggest
   * "Reopen in Container". Skipped if already running inside one
   * (env REMOTE_CONTAINERS / DEVCONTAINER set).
   */
  async maybeSuggestDevContainer(): Promise<void> {
    if (process.env.REMOTE_CONTAINERS || process.env.DEVCONTAINER) return;
    const folders = vscode.workspace.workspaceFolders || [];
    for (const f of folders) {
      const dcPath = path.join(f.uri.fsPath, ".devcontainer", "devcontainer.json");
      if (fs.existsSync(dcPath)) {
        const choice = await vscode.window.showInformationMessage(
          `Skillslab: this folder has a devcontainer config. Reopen in Container? (Brings claude/aider/git/python pre-installed.)`,
          "Reopen in Container",
          "Not Now",
        );
        if (choice === "Reopen in Container") {
          await vscode.commands.executeCommand("remote-containers.reopenInContainer");
        }
        return;
      }
    }
  }
}

function labelOf(step: StepSummary, modulePos?: number): string {
  // We don't always have module_pos; fall back to S<step.position>
  return modulePos !== undefined
    ? `M${modulePos - 1}.S${step.position}`
    : `S${step.position}`;
}
