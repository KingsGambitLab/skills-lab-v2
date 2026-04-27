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
import { LmsClient, StepSummary, ValidateResponse } from "./api";
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

  async openStep(
    courseId: string,
    moduleId: number,
    step: StepSummary,
    /**
     * Optional grader feedback to display IN the WebView panel above the
     * briefing. Set by submitAndContinue() after /api/exercises/validate
     * returns; null/undefined for fresh opens (sidebar click, URI deep
     * link, palette navigate). User feedback 2026-04-27: detailed
     * feedback should render here, not as a transient toast.
     */
    feedback?: ValidateResponse | null,
  ): Promise<void> {
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
      feedback: feedback ?? null,
    };
    this.webview.show(
      input,
      () => void this.submitAndContinue(courseId, moduleId, detailedStep),
      () => void this.nextOrComplete(courseId, moduleId, detailedStep),
      () => void this.runStepInTerminal(detailedStep),
      () => void this.previous(courseId, moduleId, detailedStep),
      () => void this.runAndAutoSubmit(courseId, moduleId, detailedStep),
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

    // Mark complete on PASS — fire-and-forget; tree refresh handles the
    // ✓ icon. Don't auto-advance; the user explicitly asked for detailed
    // feedback to be visible (matches CLI's `check`-then-`next` flow).
    if (validated.correct) {
      const score = validated.score ?? 1.0;
      try {
        await this.api.markComplete(step.id, Math.round(score * 100));
      } catch (e: any) {
        if (e.status !== 409) {
          vscode.window.showWarningMessage(`Pass detected, sync warning: ${e.message || e}`);
        }
      }
      this.tree.refresh();
      // Brief celebratory toast — full feedback lives in the panel below.
      vscode.window.showInformationMessage(
        `✓ ${labelOf(step)} complete — score ${Math.round(score * 100)}%. Click Next ▸ when ready.`,
      );
    }

    // Re-render the WebView with the validate() response embedded as a
    // feedback panel above the briefing. PASS or FAIL — the panel shows
    // the full grader prose, per-item correctness, and (on FAIL) a
    // collapsed canonical-answer details element. User then clicks
    // Next ▸ (advance) or Submit & Continue (retry) themselves.
    await this.openStep(courseId, moduleId, step, validated as ValidateResponse);
  }

  /**
   * "Next" button handler — context-aware. For pure-read step types
   * (concept), Next IS the completion action: mark the step complete
   * on the way through, then advance. For all other step types, this
   * is a pure skip-forward (no markComplete) — same semantics as the
   * previous "Skip" button (renamed Next per user feedback 2026-04-27).
   *
   * Note: submitAndContinue() already calls next() directly after a
   * passing submission, so this wrapper is ONLY hooked to the WebView's
   * Next button — never to the post-submit advance path. That keeps
   * markComplete idempotent.
   */
  async nextOrComplete(courseId: string, moduleId: number, step: StepSummary): Promise<void> {
    const exType = (step.exercise_type || "concept").toLowerCase();
    if (exType === "concept") {
      try {
        await this.api.markComplete(step.id, 100);
      } catch (e: any) {
        // 409 already-complete: fine. Other errors: still advance —
        // the user's read-and-continue intent shouldn't block on a
        // mark-complete failure (e.g. browsing un-enrolled).
      }
    }
    await this.next(courseId, moduleId, step);
  }

  /** Advance cursor + open next step (no markComplete; called by both
   * the post-submit success path and nextOrComplete's tail). */
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
   * Go back to the previous step (no submit, no completion change).
   * Mirror of `next()` — cursor decrements, step opens. If we're at
   * the first step (cursor.stepIdx === 0), surface a friendly message
   * instead of going negative.
   */
  async previous(courseId: string, moduleId: number, _step: StepSummary): Promise<void> {
    const slug = courseId;
    const cursor = this.state.getCursor(slug);
    if (!cursor) {
      vscode.window.showInformationMessage("No active course.");
      return;
    }
    if (cursor.stepIdx <= 0) {
      vscode.window.showInformationMessage("Already at the first step.");
      return;
    }
    // Walk the flat step list to find the predecessor.
    const course = await this.api.getCourse(courseId);
    const flat: { mid: number; step: StepSummary }[] = [];
    for (const m of course.modules) {
      const mod = await this.api.getModule(courseId, m.id);
      for (const s of mod.steps) flat.push({ mid: m.id, step: s });
    }
    const prevIdx = cursor.stepIdx - 1;
    if (prevIdx < 0 || prevIdx >= flat.length) {
      vscode.window.showInformationMessage("No previous step.");
      return;
    }
    const prev = flat[prevIdx];
    this.state.setCursor(slug, courseId, prevIdx);
    await this.openStep(courseId, prev.mid, prev.step);
    this.tree.refresh();
  }

  /**
   * Build the env dict for a Skillslab terminal — only sets keys that
   * actually exist in SecretStorage so we DON'T clobber the learner's
   * shell env (pre-v0.1.3 bug: `OPENROUTER_API_KEY: ""` literally
   * reset the user's exported key to empty).
   *
   * Per CLAUDE.md hard rule: "we never handle learner API keys". Keys
   * read from SecretStorage are passed through to the spawned terminal's
   * env in-flight only — never logged, never sent to our backend.
   */
  private async buildTerminalEnv(): Promise<Record<string, string>> {
    const env: Record<string, string> = {
      SKILLSLAB_API_URL: this.cfg().apiUrl,
      SKILLSLAB_WEB_URL: this.cfg().webUrl,
    };
    const anthropic = await this.auth.getApiKey("anthropic");
    if (anthropic) env.ANTHROPIC_API_KEY = anthropic;
    const openrouter = await this.auth.getApiKey("openrouter");
    if (openrouter) env.OPENROUTER_API_KEY = openrouter;
    const github = await this.auth.getApiKey("github");
    if (github) env.GITHUB_TOKEN = github;
    return env;
  }

  /**
   * Open the integrated terminal pre-populated with the step's cli_commands.
   * MANUAL mode: we type the commands but the learner runs them themselves
   * + pastes the output back. Used as the fallback when shell-integration
   * isn't available, or when a step's cli_commands include interactive
   * prompts (claude /login, gh auth login).
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
      env: await this.buildTerminalEnv(),
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

  /**
   * AUTO-RUN mode for terminal_exercise (v0.1.3, per user feedback
   * 2026-04-27): "Vscode assignment execution should work like Terminal
   * instead of Web. ... command passes and output should not be paste,
   * it should be similar to terminal (automated)."
   *
   * Spawns a visible terminal, waits for VS Code's shell integration to
   * activate (stable since 1.93), then for each cli_command invokes
   * `Terminal.shellIntegration.executeCommand(...)` and reads streamed
   * output via the returned `TerminalShellExecution.read()` async
   * iterator. Combined output is auto-submitted to /api/exercises/validate
   * — the feedback panel (v0.1.2) renders pass/fail + grader prose
   * + per-token must-contain results inline in the WebView.
   *
   * Fallbacks:
   *   1. Shell integration not available within 4s → fall back to
   *      `runStepInTerminal` (manual mode) + a toast explaining why.
   *   2. Per-command timeout (default 60s) → kill + report error.
   *   3. Combined output > 64KB → truncate (grader's must_contain
   *      checker only needs presence of small tokens).
   */
  async runAndAutoSubmit(
    courseId: string,
    moduleId: number,
    step: StepSummary,
  ): Promise<void> {
    const cmds: { cmd: string; label?: string }[] =
      (step.validation && step.validation.cli_commands) || [];
    if (cmds.length === 0) {
      vscode.window.showInformationMessage(
        `${labelOf(step)} has no cli_commands. Falling back to manual submit.`,
      );
      // No commands to run → fall through to existing submit path
      await this.submitAndContinue(courseId, moduleId, step);
      return;
    }

    const slug = courseId;
    const attempt = this.state.recordAttempt(slug, step.id);

    const term = vscode.window.createTerminal({
      name: `Skillslab · ${labelOf(step)} (auto)`,
      env: await this.buildTerminalEnv(),
    });
    term.show();

    // Wait up to 4s for shell integration to come online. If it doesn't,
    // fall back to manual mode — better to surface that path than to
    // hang forever on a shell that won't integrate.
    const integration = await waitForShellIntegration(term, 4000);
    if (!integration) {
      vscode.window.showWarningMessage(
        `Shell integration not detected for ${labelOf(step)}. ` +
          `Falling back to manual mode — run the commands yourself, then click Submit & Continue.`,
      );
      // Type the commands so the learner can run them manually.
      term.sendText(`# ${labelOf(step)} — manual mode (shell integration unavailable)`, true);
      for (let i = 0; i < cmds.length; i++) {
        const c = cmds[i];
        const isLast = i === cmds.length - 1;
        term.sendText(`# ${i + 1}/${cmds.length}: ${c.label || ""}`, true);
        term.sendText(c.cmd, !isLast);
      }
      return;
    }

    // Stream-execute each cmd; capture stdout+stderr via the read iterator.
    let combinedOutput = "";
    const TIMEOUT_MS = 60_000;
    const MAX_OUTPUT_BYTES = 64 * 1024;

    for (let i = 0; i < cmds.length; i++) {
      const c = cmds[i];
      const banner = `# ${i + 1}/${cmds.length}: ${c.label || ""}`;
      combinedOutput += `${banner}\n$ ${c.cmd}\n`;

      try {
        const exec = integration.executeCommand(c.cmd);
        const reader = exec.read();
        const cmdOutput = await readStreamWithTimeout(reader, TIMEOUT_MS);
        combinedOutput += cmdOutput;
        if (!combinedOutput.endsWith("\n")) combinedOutput += "\n";
      } catch (e: any) {
        combinedOutput += `[skillslab] command failed or timed out: ${e?.message || e}\n`;
      }

      if (combinedOutput.length > MAX_OUTPUT_BYTES) {
        combinedOutput =
          combinedOutput.slice(0, MAX_OUTPUT_BYTES) +
          `\n[skillslab] output truncated at ${MAX_OUTPUT_BYTES} bytes\n`;
        break;
      }
    }

    // Submit captured output as the paste field — the grader's
    // terminal_exercise validator reads `response.paste` (single-slot
    // back-compat per CLAUDE.md §v8.6.1).
    let validated: ValidateResponse | null = null;
    try {
      validated = await this.api.validate(
        step.id,
        step.exercise_type || "terminal_exercise",
        { paste: combinedOutput, captured_output: combinedOutput },
        attempt,
      );
    } catch (e: any) {
      vscode.window.showErrorMessage(
        `Auto-submit failed: ${e?.message || e}. Try ${labelOf(step)}'s "Submit & Continue" button.`,
      );
      return;
    }

    if (validated.correct) {
      const score = validated.score ?? 1.0;
      try {
        await this.api.markComplete(step.id, Math.round(score * 100));
      } catch (e: any) {
        if (e.status !== 409) {
          vscode.window.showWarningMessage(`Pass detected, sync warning: ${e.message || e}`);
        }
      }
      this.tree.refresh();
      vscode.window.showInformationMessage(
        `✓ ${labelOf(step)} passed — score ${Math.round(score * 100)}%. Click Next ▸ when ready.`,
      );
    } else {
      vscode.window.showWarningMessage(
        `${Math.round((validated.score ?? 0) * 100)}% — see feedback in the step panel.`,
      );
    }

    // Re-render the WebView with the validated response so the feedback
    // panel (v0.1.2) shows pass/fail + grader prose + per-token results
    // inline. Same shape Submit & Continue uses.
    await this.openStep(courseId, moduleId, step, validated);
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

/**
 * Wait for the terminal's shell integration to activate, up to `timeoutMs`.
 * Returns the `TerminalShellIntegration` object on success, null on timeout.
 *
 * Shell integration goes through a brief handshake when the terminal's shell
 * sources VS Code's integration scripts (zsh / bash / pwsh / fish). On a
 * cold-start terminal this can take ~200-1500ms. On shells without
 * integration support (sh, dash, custom shells) it never fires — hence the
 * timeout.
 */
function waitForShellIntegration(
  term: vscode.Terminal,
  timeoutMs: number,
): Promise<vscode.TerminalShellIntegration | null> {
  return new Promise((resolve) => {
    if (term.shellIntegration) {
      resolve(term.shellIntegration);
      return;
    }
    const disposables: vscode.Disposable[] = [];
    const timer = setTimeout(() => {
      for (const d of disposables) d.dispose();
      resolve(null);
    }, timeoutMs);
    disposables.push(
      vscode.window.onDidChangeTerminalShellIntegration((e) => {
        if (e.terminal === term) {
          clearTimeout(timer);
          for (const d of disposables) d.dispose();
          resolve(e.shellIntegration);
        }
      }),
    );
  });
}

/**
 * Drain a `TerminalShellExecution.read()` async iterator into a single
 * string, with a hard timeout. The iterator yields stdout+stderr chunks
 * in order; the loop ends when the command completes (iterator returns)
 * OR the timeout fires. We strip ANSI escapes since the grader matches
 * regex against decorated output otherwise.
 */
async function readStreamWithTimeout(
  reader: AsyncIterable<string>,
  timeoutMs: number,
): Promise<string> {
  const chunks: string[] = [];
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error(`read timed out after ${timeoutMs}ms`)), timeoutMs),
  );
  const drainPromise = (async () => {
    for await (const chunk of reader) {
      chunks.push(chunk);
    }
  })();
  await Promise.race([drainPromise, timeoutPromise]);
  // Strip ANSI escape sequences (CSI / OSC) — graders regex-match plain text.
  // eslint-disable-next-line no-control-regex
  const ansiRe = /\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g;
  return chunks.join("").replace(ansiRe, "");
}
