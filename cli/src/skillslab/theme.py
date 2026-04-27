"""Theme + capability flags for skillslab CLI rendering.

Per buddy-Opus consult 2026-04-27 ("Theme first, capability declare not detect"):

  - Course themes are a static dict keyed by slug. Adding a new course =
    one entry. The theme dict carries (accent, accent_dim, icon, banner)
    that every Panel/Rule/Header threads through.

  - Capabilities are DECLARED, not detected. Three tiers:
      * NO_COLOR set or non-tty            → plain ASCII, no panels
      * 256-color or truecolor terminal    → full theme
      * iTerm.app specifically             → OSC SetMark + tab title

    Don't try to enumerate every terminal that supports every feature —
    false positives bite worse than missing features. Rule-of-thumb:
    always-safe features (color, box-drawing) ship by default; vendor
    quirks (OSC, alt-screen) gated by env-sniff.

This module is foundation — no other view module should compute its own
accent color or capability flag.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from rich import box as _box
from rich.console import Console


# ─── Course themes ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Theme:
    """Visual identity for a single course's terminal output."""
    slug: str
    accent: str          # primary accent (Rich color name or hex)
    accent_dim: str      # dimmer accent for borders
    icon: str            # 1-2 emoji chars rendered next to the title
    label: str           # human-readable course label for headers
    box: object          # rich.box style for panels

# Per-course theme registry. Adding a course = one entry; theme threads
# into every Panel/Rule/Header automatically. Falls back to NEUTRAL_THEME
# for anything not registered.
_THEMES: dict[str, Theme] = {
    "kimi": Theme(
        slug="kimi",
        accent="#6366f1",       # indigo
        accent_dim="#4f46e5",
        icon="◆",
        label="Open-Source AI Coding",
        box=_box.ROUNDED,
    ),
    "claude-code": Theme(
        slug="claude-code",
        accent="#f97316",       # orange
        accent_dim="#ea580c",
        icon="●",
        label="Claude Code in Production",
        box=_box.ROUNDED,
    ),
    # `aie` is the legacy slug for the same course; alias to claude-code
    "aie": Theme(
        slug="claude-code",
        accent="#f97316",
        accent_dim="#ea580c",
        icon="●",
        label="Claude Code in Production",
        box=_box.ROUNDED,
    ),
    "jspring": Theme(
        slug="jspring",
        accent="#dc2626",       # red
        accent_dim="#b91c1c",
        icon="▲",
        label="Claude Code for Spring Boot",
        box=_box.ROUNDED,
    ),
}

NEUTRAL_THEME = Theme(
    slug="default",
    accent="cyan",
    accent_dim="dim cyan",
    icon="▌",
    label="Course",
    box=_box.ROUNDED,
)


def theme_for(slug: str | None) -> Theme:
    """Return the registered theme for a course slug, or NEUTRAL_THEME if
    unknown. Tolerates None / empty / unregistered slug.
    """
    if not slug:
        return NEUTRAL_THEME
    return _THEMES.get(slug.lower(), NEUTRAL_THEME)


# ─── Capability flags ─────────────────────────────────────────────────

@dataclass(frozen=True)
class Capabilities:
    """Declared (not auto-detected) terminal capabilities. Constructed
    from env at the start of a session; downstream code reads the flags
    instead of re-checking each call.
    """
    color: bool          # any color at all (>= 8 colors)
    rich: bool           # 256+ colors → full Rich panels
    unicode_boxes: bool  # box-drawing chars (▌ ─ │ ╭ ╰ ✓)
    osc_marks: bool      # iTerm.app OSC 1337 SetMark
    tab_title: bool      # OSC 0/2 set-window-title


def detect_capabilities(console: Console | None = None) -> Capabilities:
    """Read env + console at startup to decide what features to emit.

    Per buddy-Opus: declare, don't detect. We check `NO_COLOR`,
    `console.is_terminal`, `console.color_system`, `TERM_PROGRAM`,
    and `LANG`/`LC_ALL` for UTF-8. No vendor enumeration beyond
    iTerm.app — false positives on WezTerm/Kitty bite worse than
    a missing OSC mark.
    """
    if os.environ.get("NO_COLOR"):
        return Capabilities(False, False, False, False, False)

    is_tty = (console is not None and console.is_terminal)
    color_system = (console.color_system if console else None)

    # Color + Rich panels only when color is real
    color = is_tty and color_system is not None and color_system != "windows"
    rich_color = is_tty and color_system in ("256", "truecolor")

    # Unicode box drawing — assume yes if locale looks UTF-8 OR we're on
    # a real tty. Conservative fallback to ASCII via rich.box.ASCII when
    # we miss; not a footgun, just less pretty.
    lang = (os.environ.get("LANG") or os.environ.get("LC_ALL") or "").lower()
    unicode_boxes = is_tty and ("utf" in lang or "C.UTF" in lang or color)

    # iTerm-specific OSC features
    is_iterm = os.environ.get("TERM_PROGRAM") == "iTerm.app"

    return Capabilities(
        color=color,
        rich=rich_color,
        unicode_boxes=unicode_boxes,
        osc_marks=is_iterm,
        tab_title=is_iterm,  # OSC 2 works elsewhere too but keep scoped
    )


# Module-level singleton. Lazily filled on first call to ensure the
# console object is provided. Most callers go through `current()`.
_caps_singleton: Capabilities | None = None


def current(console: Console | None = None) -> Capabilities:
    """Cached singleton accessor for capabilities. Pass `console` on
    first call from a known-correct context (e.g. cli.py top-level).
    Subsequent calls return the cached value.
    """
    global _caps_singleton
    if _caps_singleton is None:
        _caps_singleton = detect_capabilities(console)
    return _caps_singleton


def reset_for_test() -> None:
    """Reset the capability cache. Tests-only — never call in prod paths."""
    global _caps_singleton
    _caps_singleton = None


# ─── iTerm OSC helpers ────────────────────────────────────────────────

def emit_set_mark(console: Console) -> None:
    """Emit OSC 1337 SetMark. iTerm2 users get cmd-shift-↑/↓ navigation
    between marks for free; everyone else sees nothing (or a single
    invisible escape that gets ignored).

    Writes DIRECTLY to console.file — `console.print` would interpret
    the `[1337]` substring as Rich markup and mangle the OSC sequence.
    """
    if not current(console).osc_marks:
        return
    # OSC 1337 ; SetMark BEL  — write raw, bypass Rich markup parser
    try:
        console.file.write("\x1b]1337;SetMark\x07")
        console.file.flush()
    except Exception:
        # Non-fatal — terminal might not accept raw writes
        pass


def emit_tab_title(console: Console, title: str) -> None:
    """Set the terminal tab/window title. OSC 0 = both icon + title.
    Gated by capability so we don't write garbage to scrollback in
    incompatible terminals.

    Writes DIRECTLY to console.file — same reason as emit_set_mark
    (Rich would treat `[0]` as bracketed markup).
    """
    if not current(console).tab_title:
        return
    # OSC 0 ; <title> BEL  — write raw
    try:
        console.file.write(f"\x1b]0;{title}\x07")
        console.file.flush()
    except Exception:
        pass
