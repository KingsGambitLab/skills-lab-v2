"""Tests for view renderers (step_card, celebration, toc).

Per buddy-Opus 2026-04-27: smoke-test text content via console.export_text(),
NOT golden-file ANSI snapshots. ANSI churns across Rich versions; text
content is stable.
"""
import pytest
from rich.console import Console

from skillslab import theme
from skillslab.views import render_step_card, render_celebration, render_toc


def _render(panel_or_text) -> str:
    """Render a Panel/Text via a string Console + return the captured text."""
    c = Console(record=True, force_terminal=True, width=100, color_system="truecolor")
    c.print(panel_or_text)
    return c.export_text()


@pytest.fixture(autouse=True)
def _reset_caps():
    theme.reset_for_test()
    yield
    theme.reset_for_test()


# ── step_card ────────────────────────────────────────────────────────

def test_step_card_includes_label_and_title():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(color=True, rich=True, unicode_boxes=True,
                              osc_marks=False, tab_title=False)
    p = render_step_card(
        step={"module_pos": 2, "step_pos": 1,
              "title": "Author CLAUDE.md for the M1 repo",
              "exercise_type": "terminal_exercise",
              "learner_surface": "terminal", "id": 85100},
        theme=th, caps=caps, attempt_count=0,
    )
    text = _render(p)
    assert "M1.S1" in text
    assert "Author CLAUDE.md for the M1 repo" in text
    assert "TERMINAL" in text
    assert "terminal_exercise" in text


def test_step_card_attempt_counter_appears_after_first_submit():
    """attempt_count=0 → no counter shown. attempt_count=2 → 'attempt 3' (n+1)."""
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(True, True, True, False, False)
    step = {"module_pos": 2, "step_pos": 1, "title": "x",
            "exercise_type": "terminal_exercise", "learner_surface": "terminal", "id": 1}

    p0 = render_step_card(step=step, theme=th, caps=caps, attempt_count=0)
    assert "attempt" not in _render(p0).lower()

    p2 = render_step_card(step=step, theme=th, caps=caps, attempt_count=2)
    assert "attempt 3" in _render(p2).lower()


def test_step_card_surface_badge_web_vs_terminal():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(True, True, True, False, False)
    web_step = {"module_pos": 1, "step_pos": 1, "title": "x", "learner_surface": "web", "id": 1}
    term_step = {"module_pos": 1, "step_pos": 1, "title": "x", "learner_surface": "terminal", "id": 1}
    assert "WEB" in _render(render_step_card(step=web_step, theme=th, caps=caps))
    assert "TERMINAL" in _render(render_step_card(step=term_step, theme=th, caps=caps))


def test_step_card_plain_fallback_under_no_color():
    """When caps.rich=False (NO_COLOR / non-tty), render returns Text not
    Panel — plain ASCII, no Unicode boxes. Text content still load-bearing.
    """
    th = theme.theme_for("kimi")
    caps_plain = theme.Capabilities(color=False, rich=False, unicode_boxes=False,
                                    osc_marks=False, tab_title=False)
    p = render_step_card(
        step={"module_pos": 2, "step_pos": 1, "title": "Plain step",
              "exercise_type": "concept", "learner_surface": "web", "id": 1},
        theme=th, caps=caps_plain,
    )
    text = _render(p)
    assert "M1.S1" in text
    assert "Plain step" in text
    assert "skillslab spec" in text  # action hint still visible


# ── celebration ──────────────────────────────────────────────────────

def test_celebration_shows_score_and_progress():
    th = theme.theme_for("claude-code")
    caps = theme.Capabilities(True, True, True, False, False)
    p = render_celebration(
        step={"module_pos": 2, "step_pos": 3, "title": "Author CLAUDE.md"},
        theme=th, caps=caps,
        score=0.85, elapsed_seconds=252,
        course_completed=14, course_total=29,
        next_step_label="M1.S4", next_step_title="Redo the M1 fix",
    )
    text = _render(p)
    assert "M1.S3" in text  # current step (just done)
    assert "DONE" in text
    assert "85%" in text
    # course progress
    assert "14/29" in text
    # next-step pointer
    assert "M1.S4" in text
    assert "Redo the M1 fix" in text


def test_celebration_course_complete_shows_no_next():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(True, True, True, False, False)
    p = render_celebration(
        step={"module_pos": 7, "step_pos": 5, "title": "Final"},
        theme=th, caps=caps, score=1.0,
        course_completed=29, course_total=29,
        next_step_label=None, next_step_title=None,
    )
    text = _render(p)
    assert "Course complete" in text
    assert "100%" in text


def test_celebration_plain_fallback():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(False, False, False, False, False)
    p = render_celebration(
        step={"module_pos": 1, "step_pos": 1, "title": "x"},
        theme=th, caps=caps, score=0.7, elapsed_seconds=60,
        course_completed=1, course_total=10,
        next_step_label="M0.S2", next_step_title="Next thing",
    )
    text = _render(p)
    assert "DONE" in text
    assert "70%" in text
    assert "1/10" in text
    assert "M0.S2" in text


# ── toc ──────────────────────────────────────────────────────────────

def test_toc_shows_module_grouping_and_states():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(True, True, True, False, False)
    meta = {
        "course_title": "Test Course",
        "cursor": 2,
        "steps": [
            {"id": 1, "module_pos": 1, "step_pos": 1, "title": "Preflight check",
             "module_title": "M0 — Preflight"},
            {"id": 2, "module_pos": 1, "step_pos": 2, "title": "Smoke test",
             "module_title": "M0 — Preflight"},
            {"id": 3, "module_pos": 2, "step_pos": 1, "title": "Active step",
             "module_title": "M1 — First fix"},
            {"id": 4, "module_pos": 2, "step_pos": 2, "title": "Pending",
             "module_title": "M1 — First fix"},
        ],
    }
    progress = {
        "1": {"completed": True, "score": 1.0},
        "2": {"completed": True, "score": 0.85},
        "3": {"completed": False, "score": None},
        "4": {"completed": False, "score": None},
    }
    p = render_toc(meta=meta, progress=progress, theme=th, caps=caps)
    text = _render(p)
    assert "Test Course" in text
    assert "Preflight check" in text
    assert "Active step" in text
    assert "Pending" in text
    # cursor marker visible
    assert "you are here" in text


def test_toc_plain_fallback():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(False, False, False, False, False)
    meta = {
        "course_title": "Plain Course",
        "cursor": 0,
        "steps": [
            {"id": 1, "module_pos": 1, "step_pos": 1, "title": "First", "module_title": "M0"},
        ],
    }
    p = render_toc(meta=meta, progress={}, theme=th, caps=caps)
    text = _render(p)
    assert "Plain Course" in text
    assert "First" in text


def test_toc_handles_empty_progress_gracefully():
    th = theme.theme_for("kimi")
    caps = theme.Capabilities(True, True, True, False, False)
    meta = {
        "course_title": "Empty",
        "cursor": 0,
        "steps": [
            {"id": 1, "module_pos": 1, "step_pos": 1, "title": "S1", "module_title": "M0"},
        ],
    }
    # Should not raise
    p = render_toc(meta=meta, progress={}, theme=th, caps=caps)
    text = _render(p)
    assert "S1" in text
