/**
 * Per-step attempt counters + cursor — mirrors `cli/src/skillslab/state.py`.
 *
 * Stored in VS Code globalState so it persists across windows / restarts
 * but stays scoped to this VS Code installation. Keys + step IDs only —
 * NO secrets, NO API keys (those go through `auth.ts` → SecretStorage).
 */
import * as vscode from "vscode";

const KEY_ATTEMPTS = "skillslab.attempts";   // { "<slug>:<step_id>": number }
const KEY_CURSOR = "skillslab.cursor";       // { "<slug>": { courseId, stepIdx } }

export class StateManager {
  constructor(private readonly ctx: vscode.ExtensionContext) {}

  // ── Attempt counter (for /api/exercises/validate's reveal-gate) ──

  recordAttempt(slug: string, stepId: number | string): number {
    const all = this.ctx.globalState.get<Record<string, number>>(KEY_ATTEMPTS, {});
    const k = `${slug}:${stepId}`;
    const next = (all[k] || 0) + 1;
    all[k] = next;
    void this.ctx.globalState.update(KEY_ATTEMPTS, all);
    return next;
  }

  getAttempt(slug: string, stepId: number | string): number {
    const all = this.ctx.globalState.get<Record<string, number>>(KEY_ATTEMPTS, {});
    return all[`${slug}:${stepId}`] || 0;
  }

  resetAttempts(slug: string, stepId?: number | string): void {
    const all = this.ctx.globalState.get<Record<string, number>>(KEY_ATTEMPTS, {});
    if (stepId === undefined) {
      const filtered: Record<string, number> = {};
      for (const k of Object.keys(all)) {
        if (!k.startsWith(`${slug}:`)) filtered[k] = all[k];
      }
      void this.ctx.globalState.update(KEY_ATTEMPTS, filtered);
    } else {
      delete all[`${slug}:${stepId}`];
      void this.ctx.globalState.update(KEY_ATTEMPTS, all);
    }
  }

  // ── Cursor (current step per course) ─────────────────────────────

  setCursor(slug: string, courseId: string, stepIdx: number): void {
    const all = this.ctx.globalState.get<Record<string, { courseId: string; stepIdx: number }>>(
      KEY_CURSOR,
      {},
    );
    all[slug] = { courseId, stepIdx };
    void this.ctx.globalState.update(KEY_CURSOR, all);
  }

  getCursor(slug: string): { courseId: string; stepIdx: number } | null {
    const all = this.ctx.globalState.get<Record<string, { courseId: string; stepIdx: number }>>(
      KEY_CURSOR,
      {},
    );
    return all[slug] || null;
  }

  /** Slug of the most-recently-active course — used to disambiguate
   * "submit & continue" when the learner has multiple courses open. */
  getMostRecentSlug(): string | null {
    const all = this.ctx.globalState.get<Record<string, { courseId: string; stepIdx: number }>>(
      KEY_CURSOR,
      {},
    );
    const keys = Object.keys(all);
    return keys.length > 0 ? keys[keys.length - 1] : null;
  }
}
