/**
 * Sidebar TreeDataProvider — courses → modules → steps with ✓/▶/◯ states.
 *
 * Mirrors what `skillslab toc` shows in the CLI but native to VS Code's
 * tree view conventions. Each node is clickable → opens the step in the
 * step-card WebView (handled in commands.ts).
 *
 * Re-uses LMS API endpoints; no new backend code.
 */
import * as vscode from "vscode";
import { LmsClient, CourseSummary, ModuleSummary, StepSummary } from "./api";
import { StateManager } from "./state";

type NodeKind = "course" | "module" | "step" | "loading" | "empty";

interface NodeBase {
  kind: NodeKind;
  label: string;
  description?: string;
}

export interface CourseNode extends NodeBase {
  kind: "course";
  course: CourseSummary;
}

export interface ModuleNode extends NodeBase {
  kind: "module";
  courseId: string;
  module: ModuleSummary;
}

export interface StepNode extends NodeBase {
  kind: "step";
  courseId: string;
  moduleId: number;
  step: StepSummary;
  active: boolean;     // is this the current cursor for the course?
  completed: boolean;
}

export interface MessageNode extends NodeBase {
  kind: "loading" | "empty";
}

export type SkillsNode = CourseNode | ModuleNode | StepNode | MessageNode;

export class CourseTree implements vscode.TreeDataProvider<SkillsNode> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SkillsNode | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  // Per-course module list cache to avoid refetching on every expand
  private modulesCache: Map<string, ModuleSummary[]> = new Map();
  private stepsCache: Map<string, StepSummary[]> = new Map(); // key: `${courseId}:${moduleId}`

  constructor(
    private readonly api: LmsClient,
    private readonly state: StateManager,
  ) {}

  refresh(): void {
    this.modulesCache.clear();
    this.stepsCache.clear();
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(node: SkillsNode): vscode.TreeItem {
    switch (node.kind) {
      case "loading":
      case "empty": {
        const item = new vscode.TreeItem(node.label, vscode.TreeItemCollapsibleState.None);
        item.description = node.description;
        item.contextValue = `skillslab.${node.kind}`;
        return item;
      }
      case "course": {
        const item = new vscode.TreeItem(
          node.course.title,
          vscode.TreeItemCollapsibleState.Collapsed,
        );
        item.id = `course:${node.course.id}`;
        item.description = node.course.level || "";
        item.tooltip = node.course.subtitle || node.course.description || "";
        item.iconPath = new vscode.ThemeIcon("book");
        item.contextValue = "skillslab.course";
        return item;
      }
      case "module": {
        const item = new vscode.TreeItem(
          node.module.title,
          vscode.TreeItemCollapsibleState.Collapsed,
        );
        item.id = `mod:${node.courseId}:${node.module.id}`;
        item.description = `${node.module.step_count ?? "?"} steps`;
        item.iconPath = new vscode.ThemeIcon("folder");
        item.contextValue = "skillslab.module";
        return item;
      }
      case "step": {
        const item = new vscode.TreeItem(
          `S${node.step.position}  ${node.step.title}`,
          vscode.TreeItemCollapsibleState.None,
        );
        item.id = `step:${node.courseId}:${node.moduleId}:${node.step.id}`;
        const surface = (node.step.learner_surface || "web").toLowerCase();
        item.description = `${node.step.exercise_type || "concept"}  ·  ${surface}`;
        // Three-state icon: ✓ done / ▶ active / ◯ pending
        if (node.completed) {
          item.iconPath = new vscode.ThemeIcon("check", new vscode.ThemeColor("charts.green"));
        } else if (node.active) {
          item.iconPath = new vscode.ThemeIcon("play", new vscode.ThemeColor("charts.orange"));
        } else {
          item.iconPath = new vscode.ThemeIcon("circle-large-outline");
        }
        item.contextValue = "skillslab.step";
        item.command = {
          command: "skillslab.openStep",
          title: "Open Step",
          arguments: [node.courseId, node.moduleId, node.step],
        };
        return item;
      }
    }
  }

  async getChildren(node?: SkillsNode): Promise<SkillsNode[]> {
    if (!node) {
      // Root: list courses
      try {
        const courses = await this.api.allCourses();
        if (courses.length === 0) {
          return [{ kind: "empty", label: "No courses available" }];
        }
        return courses.map((c) => ({
          kind: "course" as const,
          label: c.title,
          course: c,
        }));
      } catch (e: any) {
        return [{ kind: "empty", label: `Failed to load courses: ${e.message || e}` }];
      }
    }
    if (node.kind === "course") {
      const courseId = node.course.id;
      let modules = this.modulesCache.get(courseId);
      if (!modules) {
        try {
          const full = await this.api.getCourse(courseId);
          modules = full.modules || [];
          this.modulesCache.set(courseId, modules);
        } catch (e: any) {
          return [{ kind: "empty", label: `Failed to load modules: ${e.message || e}` }];
        }
      }
      return modules.map((m) => ({
        kind: "module" as const,
        label: m.title,
        courseId,
        module: m,
      }));
    }
    if (node.kind === "module") {
      const cacheKey = `${node.courseId}:${node.module.id}`;
      let steps = this.stepsCache.get(cacheKey);
      if (!steps) {
        try {
          const full = await this.api.getModule(node.courseId, node.module.id);
          steps = full.steps || [];
          this.stepsCache.set(cacheKey, steps);
        } catch (e: any) {
          return [{ kind: "empty", label: `Failed to load steps: ${e.message || e}` }];
        }
      }
      // Per-course slug for cursor lookup
      const slug = this.slugForCourseId(node.courseId);
      const cursor = slug ? this.state.getCursor(slug) : null;
      const cursorStepIdx = cursor?.stepIdx ?? -1;
      return steps.map((s, idx) => ({
        kind: "step" as const,
        label: s.title,
        courseId: node.courseId,
        moduleId: node.module.id,
        step: s,
        active: idx === cursorStepIdx,
        completed: idx < cursorStepIdx, // cursor-based: anything before cursor = done
      }));
    }
    return [];
  }

  /** Best-effort slug from course title — mirrors cli/_slug_for_course_title.
   * Used for cursor lookup; falls back to courseId if no match.
   */
  private slugForCourseId(courseId: string): string | null {
    // We don't have title here, but the cursor is keyed by slug across the
    // extension. Just fall back to the courseId — state.ts accepts any
    // string key, so the cursor still resolves consistently.
    return courseId;
  }
}
