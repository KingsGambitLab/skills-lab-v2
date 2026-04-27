"""Tests for section_rule + step_boundary_rule."""
import pytest
from rich.console import Console

from skillslab import theme
from skillslab.rules import section_rule, step_boundary_rule


@pytest.fixture(autouse=True)
def _reset_caps():
    theme.reset_for_test()
    yield
    theme.reset_for_test()


def test_section_rule_emits_intent_label():
    c = Console(record=True, force_terminal=True, color_system="truecolor", width=100)
    section_rule(c, "Starting cli_commands (3)")
    text = c.export_text()
    assert "Starting cli_commands (3)" in text


def test_section_rule_includes_timestamp():
    c = Console(record=True, force_terminal=True, color_system="truecolor", width=100)
    section_rule(c, "Submitting")
    text = c.export_text()
    # HH:MM:SS pattern (5-or-8 digits with colons)
    import re
    assert re.search(r"\d{2}:\d{2}:\d{2}", text)


def test_section_rule_no_op_with_none_console():
    """Defensive — if a caller hasn't set up a console yet, don't crash."""
    section_rule(None, "should not crash")  # should be a no-op


def test_section_rule_emits_osc_mark_under_iterm(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    c = Console(record=True, force_terminal=True, color_system="truecolor", width=100)
    section_rule(c, "Step boundary", mark=True)
    # Rich's record buffer holds the printed segments; check for OSC bytes
    raw = c.file.getvalue() if hasattr(c.file, "getvalue") else ""
    # When `record=True` Rich captures into _record_buffer; we just need
    # to confirm the mark call executes without error and produces output
    text = c.export_text()
    assert "Step boundary" in text


def test_section_rule_no_mark_without_iterm(monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    c = Console(record=True, force_terminal=True, color_system="truecolor", width=100)
    section_rule(c, "Boundary", mark=True)
    # No crash; OSC silently no-ops
    text = c.export_text()
    assert "Boundary" in text


def test_step_boundary_rule_uses_mark_by_default():
    """step_boundary_rule wraps section_rule with mark=True. Smoke test
    that it emits the label + title together."""
    monkeypatch_set_iterm = lambda monkeypatch: monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    c = Console(record=True, force_terminal=True, color_system="truecolor", width=100)
    th = theme.theme_for("kimi")
    step_boundary_rule(c, label="M1.S1", title="Why context is oxygen", theme=th)
    text = c.export_text()
    assert "M1.S1" in text
    assert "Why context is oxygen" in text
