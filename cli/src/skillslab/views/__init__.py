"""View renderers for skillslab CLI.

Per buddy-Opus consult 2026-04-27: each view is its own file so
revert/replace is per-feature, not per-batch.

  step_card.py   → render_step_card(state, theme, caps) -> Panel
  celebration.py → render_celebration(state, theme, caps) -> Panel
  toc.py         → render_toc(meta, progress, theme, caps) -> Panel | str

Shared dependency on `theme.Theme` is a feature, not a reason to colocate.
"""
from .step_card import render_step_card
from .celebration import render_celebration
from .toc import render_toc

__all__ = ["render_step_card", "render_celebration", "render_toc"]
