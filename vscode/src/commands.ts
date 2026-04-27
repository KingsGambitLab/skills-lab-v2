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
import * as cp from "child_process";
import { LmsClient, StepSummary, ValidateResponse } from "./api";
import { AuthManager } from "./auth";

/**
 * Known course-repo URLs keyed by lower-cased substring of the course title.
 * Used by `startCourse` (Change #4) to suggest "Clone & Reopen in Container"
 * when the learner picks a course whose toolchain expects the devcontainer.
 *
 * NOTE — drift risk: this lookup hardcodes the 3 known v8.6.x course-repos.
 * Replacement plan: backend endpoint `GET /api/courses/{id}/asset` reading
 * from `backend/course_assets.py`. Tracked in the creator-flow worktree.
 * Until then, add a row here when shipping a new BYO-key course.
 */
const KNOWN_COURSE_REPOS: ReadonlyArray<{
  matchTitleLower: string;
  repoUrl: string;
  repoFolderName: string;
}> = [
  {
    matchTitleLower: "open-source ai coding",
    repoUrl: "https://github.com/tusharbisht/kimi-eng-course-repo",
    repoFolderName: "kimi-eng-course-repo",
  },
  {
    matchTitleLower: "ai-augmented engineering",
    repoUrl: "https://github.com/tusharbisht/aie-course-repo",
    repoFolderName: "aie-course-repo",
  },
  {
    matchTitleLower: "claude code for spring boot",
    repoUrl: "https://github.com/tusharbisht/jspring-course-repo",
    repoFolderName: "jspring-course-repo",
  },
];

function findCourseRepo(courseTitle: string): { repoUrl: string; repoFolderName: string } | null {
  const tl = (courseTitle || "").toLowerCase();
  for (const c of KNOWN_COURSE_REPOS) {
    if (tl.includes(c.matchTitleLower)) {
      return { repoUrl: c.repoUrl, repoFolderName: c.repoFolderName };
    }
  }
  return null;
}

/**
 * Install hints surfaced by the pre-flight tool-check picker (Change #1)
 * when a learner is on the host shell + clicks Run This Step + a required
 * tool is missing from PATH. The "right" answer is almost always "Reopen
 * in Container" (we ship a known-good toolchain) but for learners who
 * insist on running locally, this gives them a copy-pasteable starting
 * point per tool. Unknown tools fall through to a generic "see <tool>
 * docs" line — better than silence.
 */
const INSTALL_HINTS: Record<string, string> = {
  aider: "pip install aider-chat   # https://aider.chat/docs/install.html",
  claude:
    "see https://docs.anthropic.com/en/docs/claude-code/setup for the Claude Code CLI installer",
  gh: "macOS: brew install gh   |   Linux: see https://github.com/cli/cli#installation",
  python3: "Python 3.10+ — macOS: pre-installed   |   Linux: apt install python3",
  python: "Python 3.10+ — macOS: pre-installed   |   Linux: apt install python3 + alias",
  pytest: "pip install pytest",
  npm: "install Node.js 20+: https://nodejs.org",
  node: "install Node.js 20+: https://nodejs.org",
  go: "install Go 1.22+: https://go.dev/dl",
  java: "install JDK 21+: https://adoptium.net",
  mvn: "install Maven: https://maven.apache.org/install.html",
  docker: "install Docker Desktop: https://docker.com/products/docker-desktop",
  cargo: "install Rust toolchain: https://rustup.rs",
  rustc: "install Rust toolchain: https://rustup.rs",
};
import { StateManager } from "./state";
import { CourseTree } from "./tree";
import { StepWebViewManager, StepRenderInput } from "./webview";
import { courseThemeAccent } from "./theme";

export class CommandHandlers {
  /**
   * Cached integrated terminal — reused across every Skillslab run so we
   * don't bloat memory + the terminal pane with one terminal per click
   * (user feedback 2026-04-27 v0.1.4: "Don't start a new terminal
   * everytime when clicked on submit in vscode, this will bloat up mem").
   *
   * Lifecycle:
   *   - Lazily created on first runStepInTerminal / runAndAutoSubmit call.
   *   - Reused on every subsequent call (same Skillslab terminal pane,
   *     scrollback intact so the learner can compare runs).
   *   - Invalidated when the user closes the terminal manually
   *     (onDidCloseTerminal listener nulls the cache → next call creates
   *     a fresh one).
   *   - Env is set at creation time and not refreshed on reuse — keys
   *     pulled from SecretStorage on first spawn carry through. To pick
   *     up new keys, learner closes the terminal; the next click creates
   *     a fresh one with current env.
   */
  private cachedTerminal: vscode.Terminal | null = null;

  /**
   * Per-session memory of which workspace folders we've ALREADY prompted
   * "Reopen in Container?" for. Reset on VS Code reload. Without this,
   * Change #2 (re-prompt on workspace folder change) would re-pester the
   * learner for every Add Folder operation when they declined once.
   */
  private _devcontainerAskedFolders = new Set<string>();

  /**
   * Per-session toolchain check cache: tool name (e.g. "aider") → whether
   * `command -v <tool>` returned 0. Used by the pre-flight check (Change
   * #1) and the WebView status pill (Change #3). Cleared automatically
   * when the learner moves into a devcontainer (PATH changes wholesale).
   */
  private _toolPathCache = new Map<string, boolean>();

  /**
   * Title of the most-recently-opened course. Used by reopenInContainer
   * (v0.1.6) to look up the course-repo URL when the current workspace
   * has no devcontainer and we need to fall through to clone-and-reopen.
   */
  private _activeCourseTitle: string | null = null;

  constructor(
    private readonly api: LmsClient,
    private readonly auth: AuthManager,
    private readonly state: StateManager,
    private readonly tree: CourseTree,
    private readonly webview: StepWebViewManager,
    private readonly cfg: () => { apiUrl: string; webUrl: string },
  ) {
    // Invalidate the cached terminal when the user closes it manually
    // — next run creates a fresh one. Without this, getOrCreateTerminal
    // would hand back a disposed reference.
    vscode.window.onDidCloseTerminal((t) => {
      if (t === this.cachedTerminal) {
        this.cachedTerminal = null;
      }
    });
  }

  /**
   * Get the cached Skillslab terminal, or create one if none exists / it
   * was disposed. ALWAYS .show()s before returning so the learner sees
   * the terminal pane focused on every run.
   *
   * Returning a cached terminal preserves scrollback (learners compare
   * runs side-by-side) and avoids the memory-bloat / terminal-clutter
   * problem of one-terminal-per-click.
   */
  private async getOrCreateTerminal(name: string): Promise<vscode.Terminal> {
    // `exitStatus` is undefined for a still-running terminal; populated
    // when the shell exits. Treat the cache as alive only when exitStatus
    // is undefined — otherwise it's a zombie reference.
    if (this.cachedTerminal && this.cachedTerminal.exitStatus === undefined) {
      this.cachedTerminal.show();
      return this.cachedTerminal;
    }
    this.cachedTerminal = vscode.window.createTerminal({
      name,
      env: await this.buildTerminalEnv(),
    });
    this.cachedTerminal.show();
    return this.cachedTerminal;
  }

  // ── Toolchain detection helpers (v0.1.5) ────────────────────────

  /**
   * Are we running inside a devcontainer / Codespace / GitHub-prebuild?
   * VS Code sets one of these env vars in those contexts; on a host
   * shell they're all undefined. Used by the pre-flight check (#1),
   * the suggestion gate (#2), and the status pill (#3) to decide
   * whether the learner is on the toolchain-rich container path.
   */
  private isInsideDevContainer(): boolean {
    return !!(
      process.env.REMOTE_CONTAINERS ||
      process.env.DEVCONTAINER ||
      process.env.CODESPACES
    );
  }

  /**
   * Synchronous PATH check via `command -v <tool>` (POSIX) — falls back
   * to `where <tool>` on Windows. Cached per-tool for the session so we
   * don't re-spawn for every step open. ~30ms first call, ~0ms cached.
   */
  private isToolOnPath(tool: string): boolean {
    if (!tool) return true;
    if (this._toolPathCache.has(tool)) return this._toolPathCache.get(tool)!;
    const probe = process.platform === "win32" ? `where ${tool}` : `command -v ${tool}`;
    let ok = false;
    try {
      cp.execSync(probe, {
        stdio: "ignore",
        timeout: 2000,
        shell: process.platform === "win32" ? "cmd.exe" : "/bin/sh",
      } as cp.ExecSyncOptions);
      ok = true;
    } catch {
      ok = false;
    }
    this._toolPathCache.set(tool, ok);
    return ok;
  }

  /**
   * Pull the first whitespace-delimited token off each cli_command.
   * `aider --version` → `aider`. `python3 -m pytest` → `python3`.
   * Skips comment-only entries (`# foo`).
   */
  private firstTokensOf(cliCommands: any[]): string[] {
    const tokens = new Set<string>();
    for (const c of cliCommands || []) {
      const cmd = typeof c === "string" ? c : (c?.cmd || c?.command || "");
      const m = String(cmd).trim().match(/^(\S+)/);
      if (!m) continue;
      const tok = m[1];
      if (tok.startsWith("#")) continue;
      tokens.add(tok);
    }
    return [...tokens];
  }

  /**
   * Compute the toolchain status for a step. Used by openStep (Change #3
   * — pass into the WebView status pill) and by runAndAutoSubmit
   * (Change #1 — gate on missing tools). Synchronous; relies on the
   * per-tool PATH cache so it's cheap on second call.
   *
   * Returns:
   *   - `n/a` for non-terminal steps (pill suppressed)
   *   - `in-container` when REMOTE_CONTAINERS is set (toolchain assumed ready)
   *   - `host-ok` when on host shell + every cli_command's first token is on PATH
   *   - `host-missing` when one or more first tokens are absent → with the list
   */
  computeToolchainStatus(step: StepSummary): {
    status: "n/a" | "in-container" | "host-ok" | "host-missing";
    missingTools: string[];
  } {
    const surface = (step.learner_surface || "").toLowerCase();
    if (surface !== "terminal") return { status: "n/a", missingTools: [] };
    if (this.isInsideDevContainer()) return { status: "in-container", missingTools: [] };
    const cliCommands: any[] = (step.validation && step.validation.cli_commands) || [];
    if (cliCommands.length === 0) return { status: "host-ok", missingTools: [] };
    const tokens = this.firstTokensOf(cliCommands);
    const missing = tokens.filter((t) => !this.isToolOnPath(t));
    return missing.length === 0
      ? { status: "host-ok", missingTools: [] }
      : { status: "host-missing", missingTools: missing };
  }

  /**
   * Pre-flight gate before runAndAutoSubmit (Change #1). When the
   * learner is on the host shell + tools are missing, surface a 3-button
   * picker: Reopen in Container (recommended) / Install hints / Run anyway.
   *
   * Returns:
   *   - "proceed" → caller continues into auto-run
   *   - "abort" → caller returns early (we either reopened in container,
   *     showed install hints, or learner cancelled)
   */
  private async preflightToolchainGate(step: StepSummary): Promise<"proceed" | "abort"> {
    const status = this.computeToolchainStatus(step);
    if (status.status !== "host-missing") return "proceed";
    const missingList = status.missingTools.join(", ");
    const choice = await vscode.window.showWarningMessage(
      `${labelOf(step)} needs ${missingList} on PATH. The course's devcontainer has these pre-installed — recommended over a local install.`,
      { modal: false },
      "Reopen in Container (recommended)",
      "Install hints",
      "Run anyway",
    );
    if (choice === "Reopen in Container (recommended)") {
      try {
        await vscode.commands.executeCommand("remote-containers.reopenInContainer");
      } catch (e: any) {
        vscode.window.showErrorMessage(
          `Dev Containers extension required. Install via: code --install-extension ms-vscode-remote.remote-containers`,
        );
      }
      return "abort";
    }
    if (choice === "Install hints") {
      const ch = vscode.window.createOutputChannel("Skillslab Install Hints");
      ch.appendLine(`# ${labelOf(step)} — missing on PATH: ${missingList}`);
      ch.appendLine(``);
      for (const t of status.missingTools) {
        ch.appendLine(`${t}: ${INSTALL_HINTS[t] || "see " + t + " docs"}`);
      }
      ch.appendLine(``);
      ch.appendLine(
        `Tip: the cleaner path is "Reopen in Container" — the skillslab devcontainer has every tool above pre-installed. See: https://github.com/tusharbisht/kimi-eng-course-repo`,
      );
      ch.show();
      return "abort";
    }
    // "Run anyway" or null (dismissed) → proceed; the auto-run will fail
    // gracefully when `aider --version` returns command-not-found.
    return choice ? "proceed" : "abort";
  }

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

    // v0.1.5 Change #4 — auto-suggest cloning the course-repo + reopening
    // in its devcontainer. Fires when:
    //   - The picked course is one of the known BYO-key courses (kimi /
    //     aie / jspring) per KNOWN_COURSE_REPOS lookup
    //   - The learner is NOT already inside a devcontainer
    //   - No open workspace folder is the course's repo
    // We never block — "Continue without" lets the learner stay where
    // they are. The clone-into-volume command short-circuits the
    // host-side checkout entirely (Path B from the runbook).
    const repo = findCourseRepo(pick.course.title);
    if (repo && !this.isInsideDevContainer()) {
      const folderNames = (vscode.workspace.workspaceFolders || []).map((f) =>
        path.basename(f.uri.fsPath),
      );
      const alreadyInRepo = folderNames.some((n) => n === repo.repoFolderName);
      if (!alreadyInRepo) {
        const choice = await vscode.window.showInformationMessage(
          `${pick.course.title} runs inside its devcontainer (aider/claude/python pre-installed). Clone ${repo.repoFolderName} and reopen there?`,
          "Clone & Reopen in Container",
          "Continue in current workspace",
        );
        if (choice === "Clone & Reopen in Container") {
          this._toolPathCache.clear();
          await this.invokeCloneInVolume(repo.repoUrl);
          return; // VS Code reloads the window post-clone; rest of flow runs there
        }
      } else {
        // Already in the right folder — just nudge "Reopen in Container"
        void this.maybeSuggestDevContainer();
      }
    }

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
    // Remember which course is active so reopenInContainer (v0.1.6) can
    // look up its course-repo URL if the current workspace has no
    // devcontainer.
    this._activeCourseTitle = courseTitle;
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
      // v0.1.5 Change #3: compute toolchain status for terminal_exercise
      // steps so the WebView pill can render 🟢/🔴 + a "Reopen in
      // Container" button if tools are missing on the host shell.
      toolchainStatus: this.computeToolchainStatus(detailedStep),
    };
    this.webview.show(
      input,
      () => void this.submitAndContinue(courseId, moduleId, detailedStep),
      () => void this.nextOrComplete(courseId, moduleId, detailedStep),
      () => void this.runStepInTerminal(detailedStep),
      () => void this.previous(courseId, moduleId, detailedStep),
      () => void this.runAndAutoSubmit(courseId, moduleId, detailedStep),
      () => void this.reopenInContainer(),
    );
  }

  /**
   * v0.1.6 — context-aware "Reopen in Container" handler.
   *
   * Three cases the button needs to handle:
   *
   *   A. Current workspace HAS a `.devcontainer/devcontainer.json`
   *      → fire `remote-containers.reopenInContainer` (works directly).
   *
   *   B. Current workspace has NO devcontainer + we know the active
   *      course's GitHub repo URL → fire `remote-containers.cloneInVolume`
   *      to clone the course-repo into a Docker volume + reopen there.
   *      User never has to do a host-side checkout.
   *
   *   C. No devcontainer + course-repo unknown → guide the learner to
   *      `Cmd-Shift-P → Dev Containers: Clone Repository in Container
   *      Volume` with a copy-pasteable URL prompt.
   *
   * Pre-v0.1.6 the handler always took path A — when the workspace
   * was unrelated to any course-repo, the Dev Containers extension
   * popped a folder picker (its "where should I look for a devcontainer?"
   * fallback). Confusing and not what the learner asked for.
   */
  async reopenInContainer(): Promise<void> {
    this._toolPathCache.clear();

    // Case A — current workspace already has a devcontainer
    const folders = vscode.workspace.workspaceFolders || [];
    const folderWithDc = folders.find((f) =>
      fs.existsSync(path.join(f.uri.fsPath, ".devcontainer", "devcontainer.json")),
    );
    if (folderWithDc) {
      try {
        await vscode.commands.executeCommand("remote-containers.reopenInContainer");
      } catch (e: any) {
        vscode.window.showErrorMessage(
          `Dev Containers extension required. Install: code --install-extension ms-vscode-remote.remote-containers`,
        );
      }
      return;
    }

    // Case B — no devcontainer in workspace, but the active course has
    // a known repo. Clone-into-volume short-circuits the host checkout.
    const repo = this._activeCourseTitle
      ? findCourseRepo(this._activeCourseTitle)
      : null;
    if (repo) {
      const choice = await vscode.window.showInformationMessage(
        `This workspace has no devcontainer config. Clone the course-repo (${repo.repoFolderName}) into a Docker volume and reopen there?`,
        "Clone & Reopen in Container",
        "Cancel",
      );
      if (choice !== "Clone & Reopen in Container") return;
      await this.invokeCloneInVolume(repo.repoUrl);
      return;
    }

    // Case C — no devcontainer + course unknown. Surface the manual path.
    const choice = await vscode.window.showInformationMessage(
      `This workspace has no devcontainer config and no course-repo URL is registered for the active course. Use the manual clone-into-volume flow?`,
      "Open Clone Command",
      "Cancel",
    );
    if (choice === "Open Clone Command") {
      // Surface the canonical command-palette entry; user pastes their repo URL.
      await this.invokeCloneInVolume(undefined);
    }
  }

  /**
   * v0.1.8 — invoke the Dev Containers extension's clone-into-volume
   * flow with proper activation + multi-id fallback + palette fallback.
   *
   * The pipeline (each step is a fallback for the previous):
   *
   *   1. **Extension presence check.** If the extension isn't installed,
   *      offer to install it via the workbench install command.
   *
   *   2. **Activate the extension.** Dev Containers uses LAZY activation
   *      — its commands aren't registered in VS Code's command registry
   *      until something triggers `ext.activate()`. v0.1.7 hit
   *      "command not found" because it never activated the extension
   *      first. Calling `ext.activate()` is idempotent + cheap if
   *      already active.
   *
   *   3. **Try multiple command ids with a string URL arg.** Different
   *      Dev Containers versions / contexts expose the clone-into-volume
   *      command under slightly different ids
   *      (`cloneInVolume` / `cloneInVolumeFromViewlet`). Try each.
   *
   *   4. **Try the same ids without args.** Some versions only accept
   *      no-arg invocation + show their own URL prompt UI. We surface
   *      a separate "Paste this URL when prompted" toast with the URL
   *      copied to clipboard so the learner can paste in one keystroke.
   *
   *   5. **Last resort: palette pre-populated.** Open the command palette
   *      filtered to the command's title (`workbench.action.quickOpen`
   *      with `>` prefix). The learner hits Enter to invoke. URL is
   *      already on the clipboard from step 4.
   */
  private async invokeCloneInVolume(repoUrl: string | undefined): Promise<void> {
    // Step 1 — extension presence
    const ext = vscode.extensions.getExtension("ms-vscode-remote.remote-containers");
    if (!ext) {
      const choice = await vscode.window.showWarningMessage(
        `The "Dev Containers" extension (ms-vscode-remote.remote-containers) is required for clone-and-reopen. Install it?`,
        "Install Dev Containers",
        "Cancel",
      );
      if (choice === "Install Dev Containers") {
        await vscode.commands.executeCommand(
          "workbench.extensions.installExtension",
          "ms-vscode-remote.remote-containers",
        );
        vscode.window.showInformationMessage(
          `Dev Containers installed. Click "Clone & Reopen in Container" again to retry.`,
        );
      }
      return;
    }

    // Step 2 — wake up the extension. Without this, executeCommand throws
    // "command not found" on lazy-registered command ids.
    if (!ext.isActive) {
      try {
        await ext.activate();
      } catch (e: any) {
        console.warn("[skillslab] failed to activate Dev Containers ext:", e);
      }
    }

    // Step 3 — try multiple command ids with the URL string.
    const candidateCmds = [
      "remote-containers.cloneInVolume",
      "remote-containers.cloneInVolumeFromViewlet",
      "remote-containers.openInContainerVolume",
    ];
    if (repoUrl) {
      for (const cmd of candidateCmds) {
        try {
          await vscode.commands.executeCommand(cmd, repoUrl);
          return; // Success
        } catch (e: any) {
          // Try the next candidate. Most likely cause: command not
          // registered (id mismatch) — keep trying.
          continue;
        }
      }
    }

    // Step 4 — try the same ids without args (extension shows URL prompt).
    // Pre-stage the URL on the clipboard so the learner can paste in one keystroke.
    if (repoUrl) {
      try {
        await vscode.env.clipboard.writeText(repoUrl);
      } catch {}
    }
    for (const cmd of candidateCmds) {
      try {
        await vscode.commands.executeCommand(cmd);
        if (repoUrl) {
          vscode.window.showInformationMessage(
            `URL copied to clipboard. Paste when prompted: ${repoUrl}`,
          );
        }
        return;
      } catch {
        continue;
      }
    }

    // Step 5 — last resort: open the palette pre-filtered to the command title.
    // This always works (the command exists in palette even if direct
    // executeCommand can't find it). URL is already on the clipboard.
    try {
      await vscode.commands.executeCommand(
        "workbench.action.quickOpen",
        ">Dev Containers: Clone Repository in Container Volume",
      );
      vscode.window.showInformationMessage(
        repoUrl
          ? `URL copied to clipboard. Press Enter on the highlighted command, then Cmd-V to paste: ${repoUrl}`
          : `Press Enter on the highlighted command in the palette to start.`,
      );
    } catch (e: any) {
      vscode.window.showErrorMessage(
        `Could not open the Dev Containers clone palette. ` +
          `Run manually: Cmd-Shift-P → "Dev Containers: Clone Repository in Container Volume"` +
          (repoUrl ? ` → paste ${repoUrl} (already on clipboard)` : ""),
      );
    }
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
    // v0.1.4: reuse the single cached Skillslab terminal across runs
    // instead of spawning fresh per click. Banner separates this run
    // from prior runs in the scrollback.
    const term = await this.getOrCreateTerminal(`Skillslab`);
    term.sendText("", false); // ensure we start on a fresh line
    term.sendText(`# ───── ${labelOf(step)} — ${step.title || ""} ─────`, true);
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

    // v0.1.5 Change #1 — pre-flight toolchain gate. If we're on the host
    // shell + tools are missing, surface a 3-button picker (Reopen in
    // Container / Install hints / Run anyway) BEFORE spawning the
    // terminal. Without this, missing aider would surface as a regex
    // miss in the grader → "0% pass" with no actionable signal.
    if ((await this.preflightToolchainGate(step)) === "abort") return;

    const slug = courseId;
    const attempt = this.state.recordAttempt(slug, step.id);

    // v0.1.4: reuse the cached terminal — same Skillslab pane across
    // every run, scrollback preserved so the learner can compare runs.
    const term = await this.getOrCreateTerminal(`Skillslab`);
    term.sendText("", false);
    term.sendText(`# ───── ${labelOf(step)} (auto-run) ─────`, true);

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
    if (this.isInsideDevContainer()) return;
    const folders = vscode.workspace.workspaceFolders || [];
    for (const f of folders) {
      const fsPath = f.uri.fsPath;
      // Per-folder dedupe (Change #2): if we already prompted for THIS
      // folder this session and the learner declined, don't re-pester
      // them on every workspace-change event. They can re-trigger via
      // "Skillslab: Reopen in Container" from the palette.
      if (this._devcontainerAskedFolders.has(fsPath)) continue;
      const dcPath = path.join(fsPath, ".devcontainer", "devcontainer.json");
      if (fs.existsSync(dcPath)) {
        // Mark BEFORE the prompt — even if the user dismisses without
        // answering, we don't want a thrash loop.
        this._devcontainerAskedFolders.add(fsPath);
        const choice = await vscode.window.showInformationMessage(
          `Skillslab: ${path.basename(fsPath)} has a devcontainer config. Reopen in Container? (Brings claude/aider/git/python pre-installed — matches the CLI's batteries-included experience.)`,
          "Reopen in Container",
          "Not Now",
        );
        if (choice === "Reopen in Container") {
          // Switching contexts wholesale invalidates the tool-PATH cache
          this._toolPathCache.clear();
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
