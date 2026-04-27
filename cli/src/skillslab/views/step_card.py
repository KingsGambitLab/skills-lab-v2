"""Step card renderer — the bold visual title card that opens every step.

Replaces the previous 4-line `_print_meta_header` output with a Rich
Panel showing M.S, title, surface badge, exercise type, est-time,
attempt counter, and the canonical next-action hints.

Buddy-Opus naming nit (2026-04-27): renamed from "trailer card" → "step
card." Trailer would imply end-of-step; step card is the opening.
"""
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.text import Text

from ..theme import Theme, Capabilities


def render_step_card(
    *,
    step: dict,
    theme: Theme,
    caps: Capabilities,
    attempt_count: int = 0,
    course_label: str | None = None,
) -> Panel | Text:
    """Render the step opening card.

    Args:
        step: cursor-style dict with keys: module_pos, step_pos, title,
              exercise_type, learner_surface, id (or step_id).
        theme: course Theme (gives accent color + icon)
        caps: terminal Capabilities (gates plain-ASCII fallback)
        attempt_count: 0 if not yet submitted; else N from state.get_attempt
        course_label: short course name for the lower-right tag

    Returns: Panel for rich-capable terminals; Text for plain.

    Notes:
        - Surface is rendered as a colored badge: ⌨ for terminal, 🌐 for web.
          Plain mode falls back to "TERMINAL" / "WEB" text.
        - Attempt counter renders as "attempt 2" once the learner has
          submitted at least once. Hidden on attempt 0 (first time).
        - Exercise type is shown but in dim style — title is the load-
          bearing label.
    """
    mod_pos = int(step.get("module_pos", 1) or 1)
    step_pos = int(step.get("step_pos", 1) or 1)
    label = f"M{mod_pos - 1}.S{step_pos}"
    title = step.get("title") or "(untitled step)"

    surface = (step.get("learner_surface") or "web").lower()
    surface_icon = "⌨" if surface == "terminal" else "🌐"
    surface_word = "TERMINAL" if surface == "terminal" else "WEB"
    surface_color = theme.accent if surface == "terminal" else "magenta"

    ex_type = step.get("exercise_type") or "concept"

    # Build the meta strip — second line. Format:
    #   ⌨  TERMINAL · 📝  terminal_exercise · attempt 2
    meta = Text()
    if caps.unicode_boxes:
        meta.append(f"{surface_icon}  ", style=surface_color)
    meta.append(surface_word, style=f"bold {surface_color}")
    meta.append("  ·  ", style="dim")
    meta.append(ex_type, style="dim")
    if attempt_count >= 1:
        meta.append("  ·  ", style="dim")
        meta.append(f"attempt {attempt_count + 1}", style="yellow")

    # Build the body — title + meta + canonical actions
    body = Text()
    if caps.unicode_boxes:
        body.append(f"  {theme.icon}  ", style=theme.accent)
    body.append(label, style=f"bold {theme.accent}")
    body.append("\n      ")
    body.append(title, style="bold white")
    body.append("\n\n  ")
    body.append(meta)

    # Hints — the next 3 actions
    body.append("\n\n")
    hints = [
        ("▶  Read briefing:   ", "skillslab spec"),
        ("▶  Submit:          ", "skillslab check"),
        ("▶  Next step:       ", "skillslab next"),
    ]
    for prefix, cmd in hints:
        body.append("  ")
        body.append(prefix, style="dim")
        body.append(cmd, style=theme.accent)
        body.append("\n")

    # Plain fallback: just emit Text
    if not caps.rich:
        # Add the course label header as a leading line for plain mode
        plain = Text()
        plain.append(f"{label} — {title}\n", style="bold")
        plain.append(f"surface: {surface_word.lower()}  ·  type: {ex_type}", style="dim")
        if attempt_count >= 1:
            plain.append(f"  ·  attempt {attempt_count + 1}", style="yellow")
        plain.append(f"\n\n")
        for prefix, cmd in hints:
            plain.append(f"  {prefix.strip()}  {cmd}\n")
        return plain

    subtitle = course_label or theme.label
    return Panel(
        body,
        title=f"[{theme.accent_dim}]── {label} ──[/]",
        title_align="left",
        subtitle=f"[dim]{subtitle}[/]",
        subtitle_align="right",
        border_style=theme.accent_dim,
        box=theme.box if caps.unicode_boxes else box.ASCII,
        padding=(0, 1),
    )
