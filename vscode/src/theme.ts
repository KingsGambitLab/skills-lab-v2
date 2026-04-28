/**
 * Course-themed accent colors — mirrors `cli/src/skillslab/theme.py`.
 * Same hex values per course; same single-source-of-truth principle.
 */

const _THEME_TOKENS: { tokens: string[]; accent: string }[] = [
  // Order matters — most-specific first.
  // 2026-04-27 v0.1.16 — jspring flipped from red (#dc2626) → Spring brand
  // green (#6db33f). User feedback: "Red indicates something is broken,
  // unnecessarily puts users alert mode." Red as the dominant accent on
  // every action button + panel-stripe was reading as constant-error UX.
  // Spring's official brand color is the natural non-alarmist fit.
  { tokens: ["spring boot", "java + spring", "jspring"], accent: "#6db33f" },     // Spring brand green
  { tokens: ["kimi k2", "kimi+aider", "kimi", "aider"], accent: "#6366f1" },       // indigo
  { tokens: ["claude code", "claude-code", "ai-augmented engineering"], accent: "#f97316" }, // orange
];

const _NEUTRAL_ACCENT = "#3b82f6";

export function courseThemeAccent(courseTitle: string): string {
  const t = (courseTitle || "").toLowerCase();
  for (const entry of _THEME_TOKENS) {
    if (entry.tokens.some((tok) => t.includes(tok))) return entry.accent;
  }
  return _NEUTRAL_ACCENT;
}
