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
 * Install hints surfaced by the pre-flight tool-check picker (v0.1.10)
 * when a learner is on the host shell + clicks Run This Step + a required
 * tool is missing from PATH.
 *
 * v0.1.10 reframe (per user 2026-04-27): the install journey IS the
 * skill. Host-install is the recommended path; devcontainer is the
 * escape hatch. So these hints are first-class teaching content, not
 * a fallback. Per-OS variants + a `troubleshoot` block for PATH issues
 * (the #1 failure mode for `pip install --user` flows).
 */
type InstallHint = {
  /** One-line "what is this tool" intro */
  what: string;
  /** Per-OS install commands (copy-pasteable) */
  macos: string;
  linux: string;
  windows: string;
  /** Common-cause troubleshooting after install */
  troubleshoot?: string;
  /** Canonical docs link */
  docs?: string;
};

const INSTALL_HINTS: Record<string, InstallHint> = {
  aider: {
    what: "Aider — open-source AI pair-programmer CLI. Official upstream installer (uv-based, handles Python + PATH automatically).",
    macos:
      "curl -LsSf https://aider.chat/install.sh | sh\n" +
      "  # The official installer handles Python version + PATH for you.\n" +
      "  # Fallback if curl is blocked: brew install python@3.11 && python3.11 -m pip install aider-chat",
    linux:
      "curl -LsSf https://aider.chat/install.sh | sh\n" +
      "  # Fallback: sudo apt install python3.11 python3-pip && python3.11 -m pip install --user aider-chat",
    windows:
      "PowerShell: powershell -ExecutionPolicy ByPass -c \"irm https://aider.chat/install.ps1 | iex\"\n" +
      "  # Fallback: winget install Python.Python.3.11 && python -m pip install aider-chat",
    troubleshoot:
      "If `aider --version` says command not found AFTER the curl-installer ran:\n" +
      "  - Open a NEW terminal — installer adds aider to PATH but the running shell may not have re-sourced .zshrc/.bashrc yet.\n" +
      "  - Verify install dir: `ls ~/.local/bin/aider` (Linux) or `ls ~/Library/Python/*/bin/aider` (macOS pip fallback path).\n" +
      "  - Check Python: `python3 --version` should be 3.10+ — the installer needs this.\n" +
      "  - If curl was blocked (corporate proxy): use the per-OS pip fallback above + ensure `~/.local/bin` is on PATH (`echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc`).",
    docs: "https://aider.chat/docs/install.html",
  },
  claude: {
    what: "Claude Code — Anthropic's official CLI. Official upstream installer.",
    macos:
      "curl -fsSL https://claude.ai/install.sh | sh\n" +
      "  # Official Anthropic installer. Run `claude /login` on first launch.",
    linux: "curl -fsSL https://claude.ai/install.sh | sh",
    windows:
      "PowerShell: irm https://claude.ai/install.ps1 | iex\n" +
      "  # Or download the Windows installer from docs.anthropic.com/en/docs/claude-code/setup",
    troubleshoot:
      "After install:\n" +
      "  - Open a NEW terminal so PATH refreshes.\n" +
      "  - Run `claude /login` to authenticate (browser opens for OAuth).\n" +
      "  - Or skip the browser flow: export ANTHROPIC_API_KEY with your key from console.anthropic.com.\n" +
      "  - Verify: `claude --version` should print '2.x.y (Claude Code)'.\n" +
      "  - If `claude /login` browser doesn't open: copy the auth URL it prints + paste in your browser manually.",
    docs: "https://docs.anthropic.com/en/docs/claude-code/setup",
  },
  gh: {
    what: "GitHub CLI — for fork/clone/PR/Actions interaction.",
    macos: "brew install gh",
    linux:
      "Debian/Ubuntu:\n" +
      "  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg\n" +
      "  echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list\n" +
      "  sudo apt update && sudo apt install gh",
    windows: "winget install --id GitHub.cli",
    troubleshoot:
      "After install:\n" +
      "  - Run `gh auth login` to authenticate (browser opens)\n" +
      "  - Or export GITHUB_TOKEN with a PAT (scopes: repo, workflow)\n" +
      "  - Verify scopes: `gh auth status`",
    docs: "https://github.com/cli/cli#installation",
  },
  python3: {
    what: "Python 3.10+ — required by aider and most Python-based courses. Recommended: install uv (Astral's Python version manager) which handles Python install + virtualenvs cross-platform.",
    macos:
      "curl -LsSf https://astral.sh/uv/install.sh | sh\n" +
      "uv python install 3.11\n" +
      "  # Then: uv run python --version  → Python 3.11.x\n" +
      "  # Fallback: brew install python@3.11  (macOS often ships 3.9, you want 3.10+)",
    linux:
      "curl -LsSf https://astral.sh/uv/install.sh | sh\n" +
      "uv python install 3.11\n" +
      "  # Fallback: sudo apt install python3.11 python3-pip",
    windows:
      "PowerShell: powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n" +
      "uv python install 3.11\n" +
      "  # Fallback: winget install Python.Python.3.11",
    troubleshoot:
      "If `python3 --version` shows < 3.10 AFTER install:\n" +
      "  - With uv: `uv run python --version` (uv-managed Python)\n" +
      "  - macOS: alias python3 to brew's: `echo 'alias python3=python3.11' >> ~/.zshrc`\n" +
      "  - Linux: use `update-alternatives` to point python3 to 3.11\n" +
      "  - Open a NEW terminal so PATH refreshes after the curl installer.",
    docs: "https://docs.astral.sh/uv/",
  },
  python: { what: "", macos: "", linux: "", windows: "", docs: "" }, // alias of python3
  pytest: {
    what: "pytest — Python test runner. Used by Skillslab's Python course graders.",
    macos: "python3 -m pip install pytest",
    linux: "python3 -m pip install --user pytest",
    windows: "python -m pip install pytest",
    troubleshoot: "If `pytest --version` not found, ensure Python's bin dir is on PATH (see python3 hints).",
  },
  npm: {
    what: "Node.js + npm — recommended via fnm (faster than nvm, cross-platform).",
    macos:
      "curl -fsSL https://fnm.vercel.app/install | bash\n" +
      "fnm install 20 && fnm use 20\n" +
      "  # Fallback: brew install node@20",
    linux:
      "curl -fsSL https://fnm.vercel.app/install | bash\n" +
      "fnm install 20 && fnm use 20\n" +
      "  # Fallback: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt install -y nodejs",
    windows:
      "PowerShell: winget install Schniz.fnm\n" +
      "fnm install 20\n" +
      "  # Fallback: winget install OpenJS.NodeJS.LTS",
    troubleshoot:
      "After fnm install, open a NEW terminal so the shell sources fnm's setup (added to ~/.zshrc / ~/.bashrc / PowerShell profile).",
    docs: "https://github.com/Schniz/fnm",
  },
  node: { what: "", macos: "", linux: "", windows: "", docs: "" }, // alias of npm
  go: {
    what: "Go toolchain — for Go-based courses.",
    macos: "brew install go",
    linux: "sudo apt install golang-go   # or download from go.dev/dl for newer versions",
    windows: "winget install GoLang.Go",
    docs: "https://go.dev/dl",
  },
  java: {
    what: "JDK 21+ — for Spring Boot / jspring courses. Recommended via sdkman (manages JDK + Maven + Gradle versions).",
    macos:
      "curl -s 'https://get.sdkman.io' | bash\n" +
      "source ~/.sdkman/bin/sdkman-init.sh\n" +
      "sdk install java 21-tem\n" +
      "  # Fallback: brew install openjdk@21",
    linux:
      "curl -s 'https://get.sdkman.io' | bash\n" +
      "source ~/.sdkman/bin/sdkman-init.sh\n" +
      "sdk install java 21-tem\n" +
      "  # Fallback: sudo apt install openjdk-21-jdk",
    windows:
      "PowerShell: winget install EclipseAdoptium.Temurin.21.JDK\n" +
      "  # sdkman supports Windows via WSL — see sdkman.io/install for details",
    troubleshoot:
      "After sdkman install, open a NEW terminal so .sdkman/bin/sdkman-init.sh is sourced.\n" +
      "Verify: `java --version` should print openjdk 21.x or temurin-21.x.",
    docs: "https://sdkman.io/install",
  },
  mvn: {
    what: "Maven — Spring Boot / jspring build tool. Recommended via sdkman (paired with Java install above).",
    macos: "sdk install maven   # if sdkman is already installed (see java entry)\n  # Fallback: brew install maven",
    linux: "sdk install maven   # if sdkman is already installed\n  # Fallback: sudo apt install maven",
    windows: "PowerShell: winget install Apache.Maven",
    docs: "https://sdkman.io/sdks#maven",
  },
  docker: {
    what: "Docker Desktop — for the optional 'Reopen in Container' escape hatch.",
    macos: "Download from docker.com (free for personal use)",
    linux: "https://docs.docker.com/engine/install/ — pick your distro",
    windows: "Download Docker Desktop from docker.com",
    docs: "https://docker.com/products/docker-desktop",
  },
  cargo: {
    what: "Rust toolchain (cargo + rustc).",
    macos: "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
    linux: "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
    windows: "Download rustup-init.exe from rustup.rs",
    docs: "https://rustup.rs",
  },
  rustc: { what: "", macos: "", linux: "", windows: "", docs: "" }, // alias of cargo
};

/** Detect the OS for install-hints rendering. */
function detectOs(): "macos" | "linux" | "windows" {
  if (process.platform === "darwin") return "macos";
  if (process.platform === "win32") return "windows";
  return "linux";
}

/** Render an install-hints OutputChannel for the missing tools. */
function renderInstallHintsToChannel(
  channel: vscode.OutputChannel,
  missingTools: string[],
  stepLabel: string,
): void {
  const os = detectOs();
  const osLabel = os === "macos" ? "macOS" : os === "linux" ? "Linux" : "Windows";
  channel.appendLine(`# ${stepLabel} — toolchain install hints (detected OS: ${osLabel})`);
  channel.appendLine(``);
  channel.appendLine(
    `Per CLAUDE.md: the install journey IS the skill. Setting up these tools on YOUR machine is part of becoming production-ready — same path you'd take at work. The Reopen-in-Container option is an escape hatch, not the primary path.`,
  );
  channel.appendLine(``);
  channel.appendLine(
    `Recommended path per tool: lead with the upstream curl-installer when one exists ` +
      `(handles cross-platform install + PATH binding). Fall back to platform package ` +
      `managers (brew/apt/winget) only when no upstream installer is available.`,
  );
  channel.appendLine(``);
  for (const tool of missingTools) {
    let hint = INSTALL_HINTS[tool];
    // Resolve aliases (python → python3, node → npm, rustc → cargo)
    if (hint && !hint.what) {
      const aliasMap: Record<string, string> = {
        python: "python3",
        node: "npm",
        rustc: "cargo",
      };
      const target = aliasMap[tool];
      if (target) hint = INSTALL_HINTS[target];
    }
    channel.appendLine(`────────────────────────────────────────────────────`);
    channel.appendLine(`## ${tool}`);
    if (!hint) {
      channel.appendLine(
        `(No install hint registered for "${tool}". Try \`brew/apt/winget search ${tool}\` for your platform.)`,
      );
      continue;
    }
    channel.appendLine(`${hint.what}`);
    channel.appendLine(``);
    channel.appendLine(`### Install (${osLabel}):`);
    channel.appendLine(hint[os] || "(no per-OS recipe — see docs link below)");
    channel.appendLine(``);
    if (hint.troubleshoot) {
      channel.appendLine(`### Troubleshoot:`);
      channel.appendLine(hint.troubleshoot);
      channel.appendLine(``);
    }
    if (hint.docs) {
      channel.appendLine(`### Docs: ${hint.docs}`);
      channel.appendLine(``);
    }
  }
  channel.appendLine(`────────────────────────────────────────────────────`);
  channel.appendLine(
    `After installing, click ▸ Run This Step again. The toolchain pill will turn 🟢 when all tools are on PATH.`,
  );
}
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
   * Synchronous PATH check, login-shell-aware (v0.1.12 fix).
   *
   * Why login shell: the extension host inherits VS Code app's PATH, NOT
   * the user's interactive-shell PATH. On macOS, `pip install --user`
   * puts binaries at `~/Library/Python/3.x/bin/aider` which the user's
   * `.zshrc` adds to PATH — but VS Code app doesn't pick that up
   * automatically. Without `bash -lc`, the check would say "aider not
   * found" even when the user's terminal sees aider just fine. The
   * symptom: 🔴 toolchain pill rendered persistently even after a
   * successful auto-run that captured aider's output.
   *
   * `bash -lc 'command -v X'` forces a login shell that sources
   * /etc/profile + ~/.profile + (Debian: ~/.bashrc via .profile chain).
   * On macOS this picks up Homebrew + pip-user-site additions to PATH.
   * On Linux, similar story for ~/.local/bin from `pip install --user`.
   *
   * Falls back to plain `command -v` if `bash` itself isn't found
   * (rare — Linux/macOS always have bash; Windows uses `where`).
   *
   * Cached per-tool for the session. ~50ms first call (login-shell
   * startup is slower than dash), ~0ms cached.
   */
  private isToolOnPath(tool: string): boolean {
    if (!tool) return true;
    if (this._toolPathCache.has(tool)) return this._toolPathCache.get(tool)!;
    let ok = false;
    try {
      if (process.platform === "win32") {
        cp.execSync(`where ${tool}`, {
          stdio: "ignore",
          timeout: 2000,
          shell: "cmd.exe",
        } as cp.ExecSyncOptions);
      } else {
        // Login-shell PATH lookup — sees what the user's terminal sees.
        cp.execSync(`bash -lc 'command -v ${tool}' >/dev/null 2>&1`, {
          stdio: "ignore",
          timeout: 3000,
          shell: "/bin/sh",
        } as cp.ExecSyncOptions);
      }
      ok = true;
    } catch {
      ok = false;
    }
    this._toolPathCache.set(tool, ok);
    return ok;
  }

  /**
   * Invalidate the per-tool PATH cache. Call after any operation that
   * might add/remove tools from the user's shell (install, container
   * reopen). Triggers a fresh login-shell lookup on next isToolOnPath.
   */
  clearToolchainCache(): void {
    this._toolPathCache.clear();
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
   * Pre-flight gate before runAndAutoSubmit (v0.1.10 reframe). Host
   * install is now the recommended path — installing the toolchain on
   * the learner's own machine IS the skill being taught (per user
   * directive 2026-04-27). The devcontainer escape hatch stays
   * available for corporate-machine / time-pressured learners but is
   * NOT promoted as the default.
   *
   * Returns:
   *   - "proceed" → caller continues into auto-run
   *   - "abort" → caller returns early (we showed install hints,
   *     reopened in container, or learner cancelled)
   */
  private async preflightToolchainGate(step: StepSummary): Promise<"proceed" | "abort"> {
    const status = this.computeToolchainStatus(step);
    if (status.status !== "host-missing") return "proceed";
    const missingList = status.missingTools.join(", ");
    const choice = await vscode.window.showWarningMessage(
      `${labelOf(step)} needs ${missingList} on PATH. ` +
        `Setting up these tools is part of the course — same skill you'd apply at work. ` +
        `Or fall back to the devcontainer if you're time-pressured.`,
      { modal: false },
      "Show install steps",
      "Run anyway",
      "Use devcontainer instead",
    );
    if (choice === "Show install steps") {
      const ch = vscode.window.createOutputChannel("Skillslab Install Hints");
      renderInstallHintsToChannel(ch, status.missingTools, labelOf(step));
      ch.show();
      return "abort";
    }
    if (choice === "Use devcontainer instead") {
      try {
        await vscode.commands.executeCommand("remote-containers.reopenInContainer");
      } catch (e: any) {
        vscode.window.showErrorMessage(
          `Dev Containers extension required. Install via: code --install-extension ms-vscode-remote.remote-containers`,
        );
      }
      return "abort";
    }
    // "Run anyway" or null (dismissed) → proceed; the auto-run will fail
    // gracefully when `aider --version` returns command-not-found, and the
    // grader's regex miss surfaces a clear signal in the feedback panel.
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

    // v0.1.10 reframe of v0.1.5 Change #4 — host install is now the
    // recommended path. The devcontainer is offered as an escape hatch,
    // not the primary suggestion. Per user directive 2026-04-27: the
    // install journey IS the skill; learners should set up the
    // toolchain on their own machine to transfer the skill to work.
    //
    // We probe a small canonical toolset to see if the learner is
    // ready to run on host. If yes → offer to clone the repo into
    // ~/code via VS Code's git.clone (host checkout). If no → show
    // the install-hints panel + offer the devcontainer as escape hatch.
    const repo = findCourseRepo(pick.course.title);
    if (repo && !this.isInsideDevContainer()) {
      const folderNames = (vscode.workspace.workspaceFolders || []).map((f) =>
        path.basename(f.uri.fsPath),
      );
      const alreadyInRepo = folderNames.some((n) => n === repo.repoFolderName);
      if (!alreadyInRepo) {
        // Heuristic toolset shared across the BYO-key courses. We don't
        // have the step's cli_commands here yet (course not loaded);
        // probe what's universal across kimi/aie/jspring.
        const probe = ["aider", "claude", "python3", "git", "gh"];
        const missing = probe.filter((t) => !this.isToolOnPath(t));
        const allReady = missing.length === 0;
        const choice = await vscode.window.showInformationMessage(
          allReady
            ? `${pick.course.title}: toolchain ready on host. Clone ${repo.repoFolderName} and continue, or use the devcontainer escape hatch?`
            : `${pick.course.title}: missing on host PATH: ${missing.join(", ")}. ` +
                `Setting these up is part of the course (skill transfer to work). ` +
                `Or use the devcontainer escape hatch if you're time-pressured.`,
          allReady ? "Clone the repo for me" : "Show install steps",
          allReady ? "I'll clone manually" : "Continue anyway",
          "Use devcontainer (escape hatch)",
        );

        if (choice === "Clone the repo for me") {
          // Host-side clone via VS Code's built-in git.clone (NOT
          // clone-into-volume — that's the devcontainer path).
          try {
            await vscode.commands.executeCommand("git.clone", repo.repoUrl);
            return;
          } catch (e: any) {
            vscode.window.showWarningMessage(
              `Auto-clone failed. Manually: git clone ${repo.repoUrl} && code <folder>`,
            );
          }
        }
        if (choice === "Show install steps") {
          const ch = vscode.window.createOutputChannel("Skillslab Install Hints");
          renderInstallHintsToChannel(
            ch,
            missing,
            `${pick.course.title} (host setup)`,
          );
          ch.appendLine(``);
          ch.appendLine(`# After install, clone the course repo:`);
          ch.appendLine(`git clone ${repo.repoUrl}`);
          ch.appendLine(`cd ${repo.repoFolderName}`);
          ch.appendLine(`code .`);
          ch.show();
        }
        if (choice === "Use devcontainer (escape hatch)") {
          this._toolPathCache.clear();
          await this.invokeCloneInVolume(repo.repoUrl);
          return; // VS Code reloads post-clone
        }
        // "Continue anyway" / "I'll clone manually" / dismissed → fall through
      }
      // (If alreadyInRepo: don't proactively prompt — the toolchain
      // pill (#3) handles the missing-tools case in the WebView.)
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
      () => void this.showInstallHintsForStep(detailedStep),
      (template: string, path: string) => void this.copyTemplateToClipboard(template, path),
      (template: string, path: string, language: string) =>
        void this.openTemplateInBuffer(template, path, language),
    );
  }

  /**
   * v0.1.14 — copy a Files-to-author template to clipboard. Surfaces a
   * brief toast confirming the path so the learner knows what was copied
   * (since the panel has multiple cards).
   */
  async copyTemplateToClipboard(template: string, path: string): Promise<void> {
    try {
      await vscode.env.clipboard.writeText(template);
      vscode.window.showInformationMessage(
        `Copied ${path || "template"} to clipboard. Paste into your editor + save.`,
      );
    } catch (e: any) {
      vscode.window.showErrorMessage(`Could not copy to clipboard: ${e?.message || e}`);
    }
  }

  /**
   * v0.1.14 — open a Files-to-author template in a NEW UNTITLED VS Code
   * editor. Per buddy-Opus review (2026-04-27): we do NOT auto-write to
   * the workspace filesystem (footgun: dirty git tree, wrong cwd, file
   * already exists). The learner pastes-and-saves themselves, retaining
   * agency over where + when the file lands.
   */
  async openTemplateInBuffer(
    template: string,
    path: string,
    language: string,
  ): Promise<void> {
    try {
      // Normalize language to a VS Code language id (the WebView already
      // does this via inferLang; pass it through).
      const lang = language || "plaintext";
      const doc = await vscode.workspace.openTextDocument({
        content: template,
        language: lang,
      });
      await vscode.window.showTextDocument(doc, {
        viewColumn: vscode.ViewColumn.Active,
        preview: false,
      });
      vscode.window.showInformationMessage(
        `Opened ${path || "template"} in a new editor. ` +
          `Edit + save it as ${path || "<your-path>"} in your workspace.`,
      );
    } catch (e: any) {
      vscode.window.showErrorMessage(
        `Could not open template in editor: ${e?.message || e}`,
      );
    }
  }

  /**
   * v0.1.10 — handler for the WebView pill's "Show install steps"
   * button. Opens an OutputChannel with per-OS install commands +
   * troubleshooting for each tool the step needs but the host doesn't
   * have on PATH.
   */
  async showInstallHintsForStep(step: StepSummary): Promise<void> {
    const status = this.computeToolchainStatus(step);
    const missing = status.status === "host-missing" ? status.missingTools : [];
    if (missing.length === 0) {
      vscode.window.showInformationMessage(
        `Toolchain looks ready for ${labelOf(step)}. No install steps needed.`,
      );
      return;
    }
    const ch = vscode.window.createOutputChannel("Skillslab Install Hints");
    renderInstallHintsToChannel(ch, missing, labelOf(step));
    ch.show();
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

    // v0.1.12 — restore auto-advance on PASS (the button is named
    // "Submit & Continue" — auto-advance is the natural semantic).
    // On FAIL, stay on the step + render the feedback panel so the
    // learner can iterate.
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
        `✓ ${labelOf(step)} complete — score ${Math.round(score * 100)}%. Advancing.`,
      );
      // Advance the cursor + open the next step. The learner can hit
      // ◂ Previous from the next step's WebView if they want to revisit
      // the feedback they just got.
      const cursor = this.state.getCursor(slug);
      if (cursor) {
        this.state.setCursor(slug, courseId, cursor.stepIdx + 1);
      }
      await this.next(courseId, moduleId, step);
      return;
    }

    // FAIL — re-render the current step with the feedback panel embedded
    // above the briefing. Pass-or-retry is the learner's call; they
    // click Submit & Continue again to retry, or ◂ Previous / Next ▸
    // to navigate elsewhere.
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
    //
    // v0.1.12: use `echo` instead of `# ...` for the banner. zsh
    // (default macOS shell) does NOT enable INTERACTIVE_COMMENTS by
    // default → `#` at the prompt fails with "command not found: #".
    // `echo "..."` prints the same banner text and works in every shell.
    const term = await this.getOrCreateTerminal(`Skillslab`);
    term.sendText("", false); // ensure we start on a fresh line
    term.sendText(
      `echo "───── ${labelOf(step)} — ${(step.title || "").replace(/"/g, "\\\"")} ─────"`,
      true,
    );
    for (let i = 0; i < cmds.length; i++) {
      const c = cmds[i];
      const isLast = i === cmds.length - 1;
      const label = (c.label || "").replace(/"/g, "\\\"");
      // v0.1.12: echo (not #) so zsh without INTERACTIVE_COMMENTS doesn't error.
      term.sendText(`echo "  ${i + 1}/${cmds.length}: ${label}"`, true);
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
    // v0.1.12: echo banners (not # comments) — zsh without
    // INTERACTIVE_COMMENTS fails on `# foo` at the prompt.
    const term = await this.getOrCreateTerminal(`Skillslab`);
    term.sendText("", false);
    term.sendText(`echo "───── ${labelOf(step)} (auto-run) ─────"`, true);

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
      term.sendText(
        `echo "${labelOf(step)} — manual mode (shell integration unavailable)"`,
        true,
      );
      for (let i = 0; i < cmds.length; i++) {
        const c = cmds[i];
        const isLast = i === cmds.length - 1;
        const label = (c.label || "").replace(/"/g, "\\\"");
        term.sendText(`echo "  ${i + 1}/${cmds.length}: ${label}"`, true);
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

    // v0.1.12 — auto-advance on PASS, same as submitAndContinue.
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
        `✓ ${labelOf(step)} passed — score ${Math.round(score * 100)}%. Advancing.`,
      );
      const cursor = this.state.getCursor(slug);
      if (cursor) {
        this.state.setCursor(slug, courseId, cursor.stepIdx + 1);
      }
      await this.next(courseId, moduleId, step);
      return;
    }

    // FAIL — stay on step, surface feedback in the WebView.
    vscode.window.showWarningMessage(
      `${Math.round((validated.score ?? 0) * 100)}% — see feedback in the step panel.`,
    );

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
