"""Tests for HTML→markdown conversion in render.py.

Smoke coverage of every conversion the LMS Creator emits in real courses.
"""
from skillslab.render import html_to_markdown, step_to_markdown


def test_empty_html_returns_empty_string():
    assert html_to_markdown("") == ""
    assert html_to_markdown(None) == ""  # type: ignore[arg-type]


def test_pre_block_becomes_fenced_code():
    html = "<pre>def foo():\n    return 42</pre>"
    md = html_to_markdown(html)
    assert "```python" in md
    assert "def foo():" in md
    assert "```" in md.split("def foo():")[1]


def test_pre_block_detects_bash():
    html = "<pre>$ git status\n$ pip install foo</pre>"
    md = html_to_markdown(html)
    assert "```bash" in md


def test_pre_block_detects_java():
    html = "<pre>@RestController\npublic class UserController { }</pre>"
    md = html_to_markdown(html)
    assert "```java" in md


def test_inline_code_uses_backticks():
    html = "<p>Run <code>pytest -q</code> in your repo.</p>"
    md = html_to_markdown(html)
    assert "`pytest -q`" in md


def test_headings_render_as_markdown_levels():
    html = "<h1>Top</h1><h2>Mid</h2><h3>Lower</h3>"
    md = html_to_markdown(html)
    assert "# Top" in md
    assert "## Mid" in md
    assert "### Lower" in md


def test_unordered_list_becomes_dash_bullets():
    html = "<ul><li>first</li><li>second</li></ul>"
    md = html_to_markdown(html)
    assert "- first" in md
    assert "- second" in md


def test_strong_and_em_become_markdown():
    html = "<p>This is <strong>important</strong> and <em>nuanced</em>.</p>"
    md = html_to_markdown(html)
    assert "**important**" in md
    assert "*nuanced*" in md


def test_html_entities_are_decoded():
    html = "<p>5 &gt; 3 &amp; 2 &lt; 4</p>"
    md = html_to_markdown(html)
    assert "5 > 3 & 2 < 4" in md


def test_script_blocks_are_stripped_body_and_all():
    """Browser-only widgets ship as <script>(function(){...})()</script>. The
    body must vanish — not just the <script> tags. Without this, JS source
    code bleeds into the terminal as 60+ lines of gibberish."""
    html = """<p>Concept text.</p>
<script>
(function(){
  let count = 0;
  document.getElementById('x').textContent = 'hi';
  window.runDemo = () => { count++; };
})();
</script>
<p>More text.</p>"""
    md = html_to_markdown(html)
    assert "Concept text." in md
    assert "More text." in md
    assert "(function()" not in md
    assert "document.getElementById" not in md
    assert "window.runDemo" not in md
    assert "let count" not in md


def test_style_blocks_are_stripped():
    html = """<style>.foo { background: red; color: white; }</style><p>real content</p>"""
    md = html_to_markdown(html)
    assert "real content" in md
    assert "background:" not in md
    assert ".foo" not in md


def test_svg_replaced_with_placeholder():
    html = '<p>before</p><svg width="100"><circle r="10"/></svg><p>after</p>'
    md = html_to_markdown(html)
    assert "before" in md
    assert "after" in md
    assert "[interactive diagram" in md
    assert "<circle" not in md


def test_iframe_replaced_with_placeholder():
    html = '<p>see widget below</p><iframe src="/demo">fallback</iframe>'
    md = html_to_markdown(html)
    assert "see widget" in md
    assert "[embedded frame" in md
    assert "fallback" not in md


def test_noscript_is_stripped():
    html = '<noscript>JS required</noscript><p>actual content</p>'
    md = html_to_markdown(html)
    assert "actual content" in md
    assert "JS required" not in md


def test_script_with_attrs_is_stripped():
    html = '<script type="module" src="/x.js">alert(1)</script><p>ok</p>'
    md = html_to_markdown(html)
    assert "ok" in md
    assert "alert" not in md


def test_step_to_markdown_includes_frontmatter_and_title():
    step = {
        "id": 12345,
        "title": "First step",
        "exercise_type": "concept",
        "content": "<p>Welcome.</p>",
        "code": "",
        "validation": {},
    }
    md = step_to_markdown(step, course_title="Demo Course", module_title="Intro")
    assert "step_id: 12345" in md
    assert "exercise_type: concept" in md
    assert '"First step"' in md
    assert "# First step" in md
    assert "Welcome." in md


def test_step_to_markdown_surfaces_starter_code():
    step = {
        "id": 1,
        "title": "Code step",
        "exercise_type": "code_exercise",
        "content": "<p>Write a function.</p>",
        "code": "def add(a, b):\n    pass\n",
        "validation": {},
    }
    md = step_to_markdown(step)
    assert "Starter / Reference" in md
    assert "def add(a, b):" in md


def test_step_to_markdown_renders_rubric_when_present():
    step = {
        "id": 2,
        "title": "Rubric-graded",
        "exercise_type": "system_build",
        "content": "<p>Ship it.</p>",
        "validation": {"rubric": "Score on clarity, depth, and concrete examples."},
    }
    md = step_to_markdown(step)
    assert "Acceptance" in md
    assert "Rubric" in md
    assert "clarity" in md


def test_step_to_markdown_handles_rubric_as_dict():
    """Some LMS courses emit validation.rubric as a dict (criteria + threshold).
    Don't crash; render it as YAML."""
    step = {
        "id": 3,
        "title": "Dict rubric",
        "exercise_type": "code_exercise",
        "content": "<p>Do the thing.</p>",
        "validation": {
            "rubric": {
                "criteria": ["clarity", "correctness", "test coverage"],
                "passing_threshold": 0.7,
            },
        },
    }
    md = step_to_markdown(step)
    assert "Rubric" in md
    assert "clarity" in md
    assert "0.7" in md


def test_step_to_markdown_handles_rubric_as_list():
    step = {
        "id": 4,
        "title": "List rubric",
        "exercise_type": "concept",
        "content": "<p>Reflect.</p>",
        "validation": {"rubric": ["names a real example", "explains the why", "cites sources"]},
    }
    md = step_to_markdown(step)
    assert "real example" in md
    assert "the why" in md
    assert "cites" in md


def test_step_to_markdown_handles_rubric_none():
    step = {
        "id": 5,
        "title": "Concept only",
        "exercise_type": "concept",
        "content": "<p>Read.</p>",
        "validation": {},
    }
    # Should not raise
    md = step_to_markdown(step)
    assert "# Concept only" in md
