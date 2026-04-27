"""End-of-step celebration panel.

Renders when a step grades correct. Shows score + time-to-complete +
course progress + next-step pointer. The earned-it moment.
"""
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.text import Text

from ..theme import Theme, Capabilities


def _progress_bar(completed: int, total: int, width: int = 24) -> str:
    """Unicode progress bar — filled / empty cells."""
    if total <= 0:
        return ""
    pct = max(0.0, min(1.0, completed / total))
    filled = int(round(pct * width))
    return "█" * filled + "░" * (width - filled)


def _format_duration(seconds: int | float | None) -> str:
    """Human-friendly duration. None → '—'."""
    if seconds is None:
        return "—"
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return "—"
    if s < 60:
        return f"{s}s"
    m, sec = divmod(s, 60)
    if m < 60:
        return f"{m}m {sec}s" if sec else f"{m}m"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


def render_celebration(
    *,
    step: dict,
    theme: Theme,
    caps: Capabilities,
    score: float,
    elapsed_seconds: int | float | None = None,
    course_completed: int = 0,
    course_total: int = 0,
    next_step_label: str | None = None,
    next_step_title: str | None = None,
) -> Panel | Text:
    """Render the post-grade celebration card.

    Args:
        step: cursor-style dict (module_pos, step_pos, title)
        theme: course Theme
        caps: terminal Capabilities
        score: grade 0..1 (will be rendered as percent)
        elapsed_seconds: time-to-complete since step opened, if known
        course_completed: how many steps in this course are done
        course_total: total steps in course
        next_step_label: "M2.S4" — if there is a next step
        next_step_title: title of the next step

    Returns: Panel for rich; Text for plain.
    """
    mod_pos = int(step.get("module_pos", 1) or 1)
    step_pos = int(step.get("step_pos", 1) or 1)
    label = f"M{mod_pos - 1}.S{step_pos}"
    pct = int(round(score * 100))

    body = Text()
    if caps.unicode_boxes:
        body.append("\n  ✨  ", style="yellow")
    else:
        body.append("\n  *  ", style="yellow")
    body.append(f"{label} — DONE", style=f"bold {theme.accent}")
    body.append(f"\n\n")

    # Score line
    body.append("  ")
    body.append(f"score {pct}%", style="bold green")
    body.append("    ")
    body.append(f"⏱  {_format_duration(elapsed_seconds)}" if caps.unicode_boxes else f"time {_format_duration(elapsed_seconds)}", style="dim")
    body.append("\n\n")

    # Course progress bar
    if course_total > 0:
        bar = _progress_bar(course_completed, course_total) if caps.unicode_boxes else f"[{course_completed}/{course_total}]"
        cpct = int(round(100 * course_completed / max(1, course_total)))
        body.append("  Course progress: ")
        body.append(bar, style=theme.accent)
        body.append(f"  {course_completed}/{course_total}  ({cpct}%)", style="dim")
        body.append("\n\n")

    # Next-step pointer
    if next_step_label:
        body.append("  ▶  Next: ", style="dim")
        body.append(next_step_label, style=f"bold {theme.accent}")
        if next_step_title:
            body.append(f" — {next_step_title[:60]}", style="white")
        body.append("\n     ")
        body.append("skillslab next", style=theme.accent)
        body.append("\n")
    else:
        body.append("  🎉  ", style="yellow")
        body.append("Course complete!", style="bold green")
        body.append("\n")

    if not caps.rich:
        plain = Text()
        plain.append(f"\n  {label} — DONE\n")
        plain.append(f"  score {pct}%   time {_format_duration(elapsed_seconds)}\n", style="bold")
        if course_total > 0:
            plain.append(f"  Course progress: {course_completed}/{course_total}\n")
        if next_step_label:
            plain.append(f"  Next: {next_step_label} {next_step_title or ''}\n")
            plain.append("  Run: skillslab next\n")
        return plain

    return Panel(
        body,
        border_style=theme.accent,
        box=theme.box if caps.unicode_boxes else box.ASCII,
        padding=(0, 1),
    )
