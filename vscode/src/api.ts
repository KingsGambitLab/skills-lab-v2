/**
 * Thin client over the existing Skillslab LMS REST API.
 *
 * Mirrors `cli/src/skillslab/api.py`. We re-use the SAME endpoints — the
 * extension is a NEW client surface, NOT a new backend. Per user directive
 * "Don't touch any core LMS, this should all be additional work."
 */
import * as vscode from "vscode";
import { AuthManager } from "./auth";

export class ApiError extends Error {
  constructor(public readonly status: number, body: string) {
    super(`API ${status}: ${body.slice(0, 200)}`);
    this.name = "ApiError";
  }
}

export interface CourseSummary {
  id: string;
  title: string;
  subtitle?: string;
  description?: string;
  level?: string;
  course_type?: string;
  module_count?: number;
}

export interface ModuleSummary {
  id: number;
  position: number;
  title: string;
  step_count?: number;
}

export interface StepSummary {
  id: number;
  position: number;
  title: string;
  step_type?: string;
  exercise_type?: string;
  learner_surface?: string;
  content?: string | null;
  code?: string | null;
  expected_output?: string | null;
  validation?: any;
  demo_data?: any;
}

export interface ValidateResponse {
  correct: boolean;
  score: number;
  feedback?: string;
  item_results?: any[];
  correct_answer?: any;
  explanations?: any;
  // v0.1.21 — client-side computed per-token + per-cli_command breakdown
  // for terminal_exercise grades. Synthesized in runAndAutoSubmit from
  // captured output + step.validation.{cli_commands, must_contain}, NOT
  // from the server response. Renders in the feedback panel so learners
  // see which markers passed/failed instead of just an opaque score.
  terminal_breakdown?: {
    cli_commands: Array<{ label: string; cmd: string; expect_pattern: string; matched: boolean }>;
    must_contain: Array<{ token: string; present: boolean }>;
  };
}

export class LmsClient {
  constructor(
    private readonly auth: AuthManager,
    private readonly apiBase: () => string,
  ) {}

  /** Build standard headers — Bearer auth when available. */
  private async headers(needAuth = true): Promise<Record<string, string>> {
    const h: Record<string, string> = { Accept: "application/json" };
    if (needAuth) {
      const t = await this.auth.getBearer();
      if (t) h["Authorization"] = `Bearer ${t}`;
    }
    return h;
  }

  private async req<T>(
    method: "GET" | "POST",
    path: string,
    opts: { body?: any; needAuth?: boolean } = {},
  ): Promise<T> {
    const url = `${this.apiBase().replace(/\/$/, "")}${path}`;
    const headers = await this.headers(opts.needAuth ?? true);
    if (opts.body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetch(url, {
      method,
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new ApiError(res.status, text);
    }
    if (res.status === 204) return undefined as unknown as T;
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return (await res.json()) as T;
    return (await res.text()) as unknown as T;
  }

  // ── Auth ────────────────────────────────────────────────────────

  async loginWithPassword(email: string, password: string): Promise<{ token: string; user_id: number; email: string; expires_at: string }> {
    return this.req("POST", "/api/auth/cli_token", {
      needAuth: false,
      body: { email, password, label: "vscode" },
    });
  }

  async whoami(): Promise<{ id: number; email: string; role: string } | null> {
    if (!(await this.auth.getBearer())) return null;
    try {
      return await this.req("GET", "/api/auth/me");
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return null;
      throw e;
    }
  }

  // ── Catalog (public, no auth) ───────────────────────────────────

  async allCourses(): Promise<CourseSummary[]> {
    return await this.req("GET", "/api/courses", { needAuth: false });
  }

  async getCliConfig(): Promise<{ image: string; repo_url: string; docs_url: string; install_one_liner: string; pull_command: string }> {
    return await this.req("GET", "/api/config/cli", { needAuth: false });
  }

  async getCourseEtag(courseId: string): Promise<{ course_id: string; etag: string; step_count: number } | null> {
    try {
      return await this.req("GET", `/api/courses/${courseId}/content-etag`, { needAuth: false });
    } catch {
      return null;
    }
  }

  // ── Authed reads ────────────────────────────────────────────────

  async myCourses(): Promise<{ course_id: string; progress_percent?: number }[]> {
    const body = await this.req<{ courses?: any[] }>("GET", "/api/auth/my-courses");
    return (body && body.courses) || [];
  }

  async getCourse(courseId: string): Promise<{ id: string; title: string; modules: ModuleSummary[] }> {
    return await this.req("GET", `/api/courses/${courseId}`);
  }

  async getModule(courseId: string, moduleId: number): Promise<{ id: number; title: string; steps: StepSummary[] }> {
    return await this.req("GET", `/api/courses/${courseId}/modules/${moduleId}`);
  }

  // ── Writes ──────────────────────────────────────────────────────

  async enroll(courseId: string): Promise<any> {
    return await this.req("POST", `/api/auth/enroll/${courseId}`, { body: {} });
  }

  async validate(stepId: number, exerciseType: string, responseData: any, attemptNumber: number): Promise<ValidateResponse> {
    return await this.req("POST", "/api/exercises/validate", {
      body: {
        step_id: stepId,
        exercise_type: exerciseType,
        response_data: responseData,
        attempt_number: attemptNumber,
      },
    });
  }

  async markComplete(stepId: number, score?: number, responseData?: any): Promise<any> {
    const body: any = { step_id: stepId };
    if (score !== undefined) body.score = score;
    if (responseData) body.response_data = responseData;
    return await this.req("POST", "/api/progress/complete", { body });
  }
}
