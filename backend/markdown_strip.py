"""Canonical browser-only-block stripper.

Single source of truth for "what content blocks are browser-only" — i.e.
which blocks the terminal-markdown renderer must REMOVE entirely (tag +
body) because their bodies would bleed into the terminal as raw JS / CSS
/ SVG markup if only the tags were stripped.

Why this lives in `backend/` even though the cli/ uses it: the surface
classifier (`backend/learner_surface.py`) needs to ask "would running
the stripper change this content?" — that's the empirical signal for
"this step has browser-only content and therefore renders only in the
browser." Per CLAUDE.md §EXECUTION IS GROUND TRUTH (2026-04-23 v8.5)
and the buddy-Opus consult (2026-04-25): the renderer IS the source of
truth for surface classification. Don't put a regex in the acceptance
gate when the runtime already answers the same question.

The CLI's `cli/src/skillslab/render.py` keeps a parallel copy of these
regex constants because the cli ships as a standalone Python package
(no `backend/` dependency). The cli_walk_agent shim has an invariant
that asserts the two definitions stay in sync.

Adding a new browser-only block type:
  1. Add the regex here.
  2. Add it to `_strip_browser_only_blocks` in this file.
  3. Mirror in `cli/src/skillslab/render.py` (parallel _SCRIPT_RE etc).
  4. The classifier auto-picks up the new pattern — no change needed in
     learner_surface.py.
"""
from __future__ import annotations

import re

# Block-level browser-only content that must be REMOVED ENTIRELY
# (tag + body), not just tag-stripped.

_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.DOTALL | re.IGNORECASE)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style\s*>", re.DOTALL | re.IGNORECASE)
_NOSCRIPT_RE = re.compile(r"<noscript\b[^>]*>.*?</noscript\s*>", re.DOTALL | re.IGNORECASE)
_HEAD_RE = re.compile(r"<head\b[^>]*>.*?</head\s*>", re.DOTALL | re.IGNORECASE)
_SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg\s*>", re.DOTALL | re.IGNORECASE)
_IFRAME_RE = re.compile(r"<iframe\b[^>]*>.*?</iframe\s*>", re.DOTALL | re.IGNORECASE)
_TEMPLATE_RE = re.compile(r"<template\b[^>]*>.*?</template\s*>", re.DOTALL | re.IGNORECASE)
_CANVAS_RE = re.compile(r"<canvas\b[^>]*>.*?</canvas\s*>", re.DOTALL | re.IGNORECASE)
_VIDEO_RE = re.compile(r"<video\b[^>]*>.*?</video\s*>", re.DOTALL | re.IGNORECASE)
_AUDIO_RE = re.compile(r"<audio\b[^>]*>.*?</audio\s*>", re.DOTALL | re.IGNORECASE)


def strip_browser_only_blocks(s: str) -> str:
    """Remove every browser-only block (tag + body) from `s`.

    Replacement strategy:
      - <script> / <style> / <noscript> / <head> / <template>: remove entirely.
      - <svg>: replace with placeholder text (some terminal contexts can
        usefully say "[diagram in browser]"; preserves a footprint).
      - <iframe>: same — placeholder text.
      - <canvas> / <video> / <audio>: remove entirely (no useful fallback text).
    """
    if not s:
        return s
    s = _SCRIPT_RE.sub("", s)
    s = _STYLE_RE.sub("", s)
    s = _NOSCRIPT_RE.sub("", s)
    s = _HEAD_RE.sub("", s)
    s = _SVG_RE.sub("[interactive diagram — see browser]", s)
    s = _IFRAME_RE.sub("[embedded frame — see browser]", s)
    s = _TEMPLATE_RE.sub("", s)
    s = _CANVAS_RE.sub("", s)
    s = _VIDEO_RE.sub("", s)
    s = _AUDIO_RE.sub("", s)
    return s


def has_browser_only_blocks(content: str) -> bool:
    """True iff running the stripper changes the content. Used by the
    surface classifier: if running the stripper changed anything, the
    content has bits that only render in the browser → surface=web.

    This is structural, not regex-on-prose: the property is decided by
    EXECUTION (running the stripper) rather than by pattern-matching
    the input text. New browser-only block types are picked up
    automatically once they're added to the stripper above.
    """
    if not content:
        return False
    return strip_browser_only_blocks(content) != content
