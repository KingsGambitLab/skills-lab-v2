"""Tests for theme + capability detection.

Per buddy-Opus 2026-04-27: declare, don't detect. These tests pin the
declaration logic so a regression in the env-sniff branches breaks
pytest, not a learner's session.
"""
import pytest
from rich.console import Console

from skillslab import theme


@pytest.fixture(autouse=True)
def _reset_caps():
    """Capability cache is a module-level singleton; reset between tests
    so each test starts fresh."""
    theme.reset_for_test()
    yield
    theme.reset_for_test()


# ── Theme registry ───────────────────────────────────────────────────

def test_theme_for_known_slugs():
    assert theme.theme_for("kimi").accent == "#6366f1"
    assert theme.theme_for("claude-code").accent == "#f97316"
    assert theme.theme_for("jspring").accent == "#dc2626"


def test_theme_for_aie_alias_is_claude_code():
    """Legacy slug `aie` aliases to claude-code."""
    a = theme.theme_for("aie")
    cc = theme.theme_for("claude-code")
    assert a.accent == cc.accent
    assert a.label == cc.label


def test_theme_for_unknown_slug_falls_back_to_neutral():
    th = theme.theme_for("unknown-course-xyz")
    assert th.slug == "default"
    assert th.accent == "cyan"


def test_theme_for_none_or_empty_returns_neutral():
    assert theme.theme_for(None).slug == "default"
    assert theme.theme_for("").slug == "default"


# ── Capability detection ─────────────────────────────────────────────

def test_no_color_env_disables_everything(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    caps = theme.detect_capabilities(Console())
    assert not caps.color
    assert not caps.rich
    assert not caps.unicode_boxes
    assert not caps.osc_marks


def test_non_tty_disables_color_and_panels(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    # Non-tty Console (e.g. piped output)
    c = Console(force_terminal=False)
    caps = theme.detect_capabilities(c)
    assert not caps.color
    assert not caps.rich


def test_iterm_specifically_enables_osc_marks(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    c = Console(force_terminal=True, color_system="truecolor")
    caps = theme.detect_capabilities(c)
    assert caps.osc_marks
    assert caps.tab_title


def test_other_terminals_skip_osc_marks(monkeypatch):
    """Per buddy-Opus: don't enumerate WezTerm/Kitty — false positives
    bite worse. Only iTerm.app gets OSC marks.
    """
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "WezTerm")
    c = Console(force_terminal=True, color_system="truecolor")
    caps = theme.detect_capabilities(c)
    assert not caps.osc_marks


def test_truecolor_terminal_gets_rich(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    c = Console(force_terminal=True, color_system="truecolor")
    caps = theme.detect_capabilities(c)
    assert caps.color
    assert caps.rich


def test_capability_singleton_cached():
    """current() returns the cached value across calls — consistent
    behavior within a session."""
    c = Console(force_terminal=True, color_system="truecolor")
    a = theme.current(c)
    b = theme.current(c)
    assert a is b


# ── OSC emission (no-op when capability disabled) ────────────────────

def test_emit_set_mark_no_op_without_iterm(monkeypatch, capsys):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    c = Console(force_terminal=True, color_system="truecolor")
    theme.emit_set_mark(c)
    out = capsys.readouterr().out
    # No OSC sequence emitted — output should be empty (or at most
    # whitespace from Rich's flush behavior)
    assert "\x1b]1337" not in out


def test_emit_set_mark_emits_under_iterm(monkeypatch, capsys):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    c = Console(force_terminal=True, color_system="truecolor")
    theme.emit_set_mark(c)
    out = capsys.readouterr().out
    assert "\x1b]1337;SetMark\x07" in out


def test_emit_tab_title_emits_under_iterm(monkeypatch, capsys):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    c = Console(force_terminal=True, color_system="truecolor")
    theme.emit_tab_title(c, "skillslab · kimi · M0.S1")
    out = capsys.readouterr().out
    assert "\x1b]0;skillslab · kimi · M0.S1\x07" in out
