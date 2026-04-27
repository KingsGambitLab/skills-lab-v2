"""Timestamp + intent rules — boundary cues between sections.

Replaces silent transitions with named rules so scrolling back finds
boundaries instantly. Per buddy-Opus consult: this also covers what a
persistent Live header would have done (cut #6) — every transition
emits its own marker, no need for a redrawing top bar.

Usage:
    from .rules import section_rule
    section_rule(console, "Starting cli_commands (3)")
    # ────── 02:14:08 ▶ Starting cli_commands (3) ──────
"""
from __future__ import annotations

import time

from rich.console import Console

from .theme import Theme, current as current_caps, emit_set_mark


def section_rule(
    console: Console | None,
    intent: str,
    *,
    theme: Theme | None = None,
    mark: bool = False,
) -> None:
    """Emit a horizontal rule with a timestamp + intent label.

    Args:
        console: Rich console (no-op if None or non-interactive)
        intent: short label naming the upcoming section
                (e.g. "Starting cli_commands (3)", "Submitting", "Step complete")
        theme: course theme for accent color (optional)
        mark: if True, also emit OSC SetMark so iTerm users can jump
              between rules with cmd-shift-↑/↓

    Style:
        - HH:MM:SS prefix, dim
        - ▶ glyph (or `>` in plain mode), in accent color
        - intent label in dim white
        - rule line in accent_dim color
    """
    if console is None:
        return
    caps = current_caps(console)

    ts = time.strftime("%H:%M:%S")
    accent = theme.accent if (theme and caps.color) else "cyan"
    accent_dim = theme.accent_dim if (theme and caps.color) else "dim cyan"
    glyph = "▶" if caps.unicode_boxes else ">"

    # Compose the title shown inside the rule. Rich.console.rule accepts
    # a title arg + style. Format:  HH:MM:SS  ▶  intent
    title = f"[dim]{ts}[/]  [{accent}]{glyph}[/]  [white]{intent}[/]"
    console.rule(title, style=accent_dim)

    if mark:
        emit_set_mark(console)


def step_boundary_rule(
    console: Console | None,
    *,
    label: str,
    title: str,
    theme: Theme | None = None,
) -> None:
    """Heavier-weight rule for STEP boundaries. Always emits an OSC
    SetMark (so cmd-shift-↑ jumps between steps in iTerm). Use this
    instead of `section_rule` when the boundary is a learner moving
    from one step to another, not just sub-actions within a step.
    """
    section_rule(
        console,
        f"{label} — {title}",
        theme=theme,
        mark=True,
    )
