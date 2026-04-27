/**
 * Course-themed accent colors — mirrors `cli/src/skillslab/theme.py`.
 * Same hex values per course; same single-source-of-truth principle.
 */

const _THEME_TOKENS: { tokens: string[]; accent: string }[] = [
  // Order matters — most-specific first.
  { tokens: ["spring boot", "java + spring", "jspring"], accent: "#dc2626" },     // red
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
