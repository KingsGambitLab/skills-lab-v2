/**
 * Auth + secret handling for the Skillslab VS Code extension.
 *
 * Per buddy-Opus consult 2026-04-27:
 *   - VS Code SecretStorage backs OS keychain. Bearer + ANTHROPIC_API_KEY +
 *     GITHUB_TOKEN live there.
 *   - CLI token inheritance is OPT-IN, ONE-WAY. We read ~/.skillslab/token
 *     only with consent (or `skillslab.adoptCliToken: always`), copy into
 *     SecretStorage, then never touch the file again. Never write back —
 *     keeps blast radius contained if either client's token format drifts.
 *   - We never proxy keys through our backend. LLM calls (when a step
 *     prompts for one) happen FROM the extension to Anthropic directly.
 *
 * CLAUDE.md hard rule (verbatim, 2026-04-22):
 *   "we never handle learner API keys"
 *
 * That rule is honored here: keys live ONLY in OS keychain via
 * SecretStorage. They are read at call-time, used in-flight, never logged,
 * never persisted to settings.json, never sent to our backend.
 */
import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

const SECRET_BEARER = "skillslab.bearer";
const SECRET_USER = "skillslab.user";

export interface SignedInUser {
  id: number;
  email: string;
  role: string;
}

export class AuthManager {
  constructor(private readonly ctx: vscode.ExtensionContext) {}

  /**
   * Resolve a bearer token. Order:
   *   1. SecretStorage (already signed in)
   *   2. CLI's ~/.skillslab/token, gated by `skillslab.adoptCliToken`
   *      (default `ask` → consent prompt)
   *   3. null → caller surfaces "Run Skillslab: Sign In" prompt
   */
  async getBearer(): Promise<string | null> {
    const stored = await this.ctx.secrets.get(SECRET_BEARER);
    if (stored) return stored;
    return await this.tryAdoptCliToken();
  }

  /** Persist a fresh bearer (after a successful sign-in). */
  async setBearer(token: string, user?: SignedInUser): Promise<void> {
    await this.ctx.secrets.store(SECRET_BEARER, token);
    if (user) {
      await this.ctx.secrets.store(SECRET_USER, JSON.stringify(user));
    }
    await vscode.commands.executeCommand("setContext", "skillslab.signedIn", true);
  }

  /** Forget the bearer + user — used by Sign Out. */
  async clear(): Promise<void> {
    await this.ctx.secrets.delete(SECRET_BEARER);
    await this.ctx.secrets.delete(SECRET_USER);
    await vscode.commands.executeCommand("setContext", "skillslab.signedIn", false);
  }

  async getUser(): Promise<SignedInUser | null> {
    const raw = await this.ctx.secrets.get(SECRET_USER);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as SignedInUser;
    } catch {
      return null;
    }
  }

  /**
   * Adopt the CLI's token at ~/.skillslab/token if present + permitted.
   * One-way: read only; we never modify or write back the file.
   * Per buddy-Opus: silent inheritance violates least-privilege; transparent
   * inheritance is fine. Default config is `ask` so the user explicitly opts
   * in.
   */
  private async tryAdoptCliToken(): Promise<string | null> {
    const cfg = vscode.workspace.getConfiguration("skillslab");
    const policy = (cfg.get<string>("adoptCliToken") || "ask").toLowerCase();
    if (policy === "never") return null;

    const tokenPath = this.cliTokenPath();
    if (!tokenPath || !fs.existsSync(tokenPath)) return null;

    let token: string;
    try {
      token = fs.readFileSync(tokenPath, "utf8").trim();
    } catch {
      return null;
    }
    if (!token) return null;

    if (policy === "always") {
      await this.ctx.secrets.store(SECRET_BEARER, token);
      await vscode.commands.executeCommand("setContext", "skillslab.signedIn", true);
      return token;
    }

    // policy === "ask"
    const choice = await vscode.window.showInformationMessage(
      "Skillslab found a sign-in token from the CLI at ~/.skillslab/token. " +
        "Adopt it for VS Code? (Read-only — the file is not modified.)",
      "Adopt",
      "Don't ask again",
      "No"
    );
    if (choice === "Adopt") {
      await this.ctx.secrets.store(SECRET_BEARER, token);
      await vscode.commands.executeCommand("setContext", "skillslab.signedIn", true);
      return token;
    }
    if (choice === "Don't ask again") {
      await cfg.update(
        "adoptCliToken",
        "never",
        vscode.ConfigurationTarget.Global
      );
    }
    return null;
  }

  /** Return the platform-appropriate path to the CLI's token file. */
  private cliTokenPath(): string | null {
    const home = os.homedir();
    if (!home) return null;
    return path.join(home, ".skillslab", "token");
  }

  /**
   * Read a learner-supplied secret (Anthropic / GitHub PAT). These are NEVER
   * sent to our backend — they're only used for direct LLM calls or to
   * spawn a terminal task with the env exported. Caller is expected to
   * scope usage tightly.
   */
  async getApiKey(name: "anthropic" | "github" | "openrouter"): Promise<string | null> {
    const k =
      name === "anthropic"
        ? "skillslab.anthropic_key"
        : name === "openrouter"
        ? "skillslab.openrouter_key"
        : "skillslab.github_token";
    return (await this.ctx.secrets.get(k)) || null;
  }

  async setApiKey(name: "anthropic" | "github" | "openrouter", value: string): Promise<void> {
    const k =
      name === "anthropic"
        ? "skillslab.anthropic_key"
        : name === "openrouter"
        ? "skillslab.openrouter_key"
        : "skillslab.github_token";
    await this.ctx.secrets.store(k, value);
  }
}
