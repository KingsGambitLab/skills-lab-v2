"""Render LMS step content to terminal-friendly markdown + ANSI.

Course content comes from the LMS as HTML (Creator emits styled <div>s,
<h3>s, <pre>s, <code>s, <ul>s). Convert to clean markdown for the terminal
+ for offline storage. Strip dark-theme inline styles; keep semantic
structure.

Strategy: regex-driven HTML→markdown converter. Tight scope: handles the
shapes the Creator actually emits. NO general HTML parser dependency
(keeps the CLI lightweight).
"""
from __future__ import annotations

import html as html_mod
import json
import re

import yaml

# Per-element converters. Order matters — apply in sequence.
_CODE_BLOCK_RE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.DOTALL | re.IGNORECASE)
_INLINE_CODE_RE = re.compile(r"<code[^>]*>(.*?)</code>", re.DOTALL | re.IGNORECASE)
_HEADING_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.DOTALL | re.IGNORECASE)
_LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.DOTALL | re.IGNORECASE)
_OL_RE = re.compile(r"<ol[^>]*>(.*?)</ol>", re.DOTALL | re.IGNORECASE)
_UL_RE = re.compile(r"<ul[^>]*>(.*?)</ul>", re.DOTALL | re.IGNORECASE)
_STRONG_RE = re.compile(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", re.DOTALL | re.IGNORECASE)
_EM_RE = re.compile(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", re.DOTALL | re.IGNORECASE)
_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)
_DIV_RE = re.compile(r"<div[^>]*>(.*?)</div>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def html_to_markdown(html: str) -> str:
    if not html:
        return ""
    s = html

    # Code blocks: keep the inside verbatim, wrap as ``` fence
    def _pre_to_fence(m: re.Match) -> str:
        body = m.group(1)
        body = _INLINE_CODE_RE.sub(lambda mm: mm.group(1), body)
        body = _TAG_RE.sub("", body)
        body = html_mod.unescape(body).strip("\n")
        # Detect language from common tokens; default empty.
        # Order matters — more-specific dialects (Java/JS/etc.) BEFORE Python,
        # because Python's `@`/`class` heuristic is lax + would otherwise win.
        lang = ""
        if any(t in body for t in ("@RestController", "public class", "package ", "import java", "@SpringBoot", "@Service", "@Repository")):
            lang = "java"
        elif body.lstrip().startswith(("$ ", "#!/", "git ", "mvn", "pip", "npm", "aider ", "claude ", "docker ", "pytest")):
            lang = "bash"
        elif body.lstrip().startswith(("{", "[")):
            lang = "json"
        elif "<?xml" in body or body.lstrip().startswith("<"):
            lang = "xml"
        elif any(t in body for t in ("def ", "import ", "class ", "from ")) and "function" not in body:
            lang = "python"
        return f"\n\n```{lang}\n{body}\n```\n\n"

    s = _CODE_BLOCK_RE.sub(_pre_to_fence, s)

    # Inline code: wrap with backticks
    s = _INLINE_CODE_RE.sub(lambda m: f"`{html_mod.unescape(_TAG_RE.sub('', m.group(1)))}`", s)

    # Headings
    def _heading(m: re.Match) -> str:
        n = int(m.group(1))
        body = _TAG_RE.sub("", m.group(2)).strip()
        return f"\n\n{'#' * min(n, 6)} {body}\n\n"
    s = _HEADING_RE.sub(_heading, s)

    # Lists — flatten to "- " markers (we don't track ordered numbers; markdown
    # renderers handle the visual)
    def _li(m: re.Match) -> str:
        return "- " + _TAG_RE.sub("", m.group(1)).strip() + "\n"
    s = _LI_RE.sub(_li, s)
    # OL/UL wrappers — strip; the LI lines are already bullet-shaped
    s = _OL_RE.sub(lambda m: "\n" + m.group(1) + "\n", s)
    s = _UL_RE.sub(lambda m: "\n" + m.group(1) + "\n", s)

    # Strong / em
    s = _STRONG_RE.sub(lambda m: f"**{_TAG_RE.sub('', m.group(1)).strip()}**", s)
    s = _EM_RE.sub(lambda m: f"*{_TAG_RE.sub('', m.group(1)).strip()}*", s)

    # Paragraphs / divs / br
    s = _P_RE.sub(lambda m: "\n\n" + m.group(1).strip() + "\n\n", s)
    s = _DIV_RE.sub(lambda m: "\n\n" + m.group(1).strip() + "\n\n", s)
    s = _BR_RE.sub("\n", s)

    # Strip remaining tags
    s = _TAG_RE.sub("", s)

    # Decode entities + collapse whitespace
    s = html_mod.unescape(s)
    s = _BLANK_LINES_RE.sub("\n\n", s)
    return s.strip() + "\n"


def step_to_markdown(step: dict, course_title: str = "", module_title: str = "") -> str:
    """Build a self-contained markdown file for a step. Stamps minimal
    front-matter with step metadata so the CLI can re-parse later if
    needed. Body is the converted HTML content + a SUBMIT section so the
    learner knows the shape of the acceptance check.
    """
    sid = step.get("id")
    title = step.get("title", "(untitled)")
    etype = step.get("exercise_type") or "concept"
    content_html = step.get("content") or ""
    code = step.get("code") or ""
    validation = step.get("validation") or {}

    body = html_to_markdown(content_html)

    parts = [
        "---",
        f"step_id: {sid}",
        f"exercise_type: {etype}",
        f"title: {json.dumps(title)}",
        f"course: {json.dumps(course_title)}",
        f"module: {json.dumps(module_title)}",
        "---",
        "",
        f"# {title}",
        "",
        f"_module:_ {module_title}    _type:_ `{etype}`    _step id:_ `{sid}`",
        "",
        "---",
        "",
        body or "_(no briefing provided)_",
    ]

    # If the step has a `code` field (starter snippet), surface it too
    if code and code.strip():
        parts += ["", "## Starter / Reference", "", "```", code.rstrip(), "```", ""]

    # Acceptance hint — what the CLI's `check` will look at
    rubric = validation.get("rubric") or validation.get("explanation_rubric") or ""
    must_contain = validation.get("must_contain") or []
    cli_check = validation.get("cli_check")
    if cli_check or rubric or must_contain:
        parts += ["", "## Acceptance (`skillslab check`)", ""]
        if cli_check:
            parts += [
                "This step has a native CLI check. Run `skillslab check` to evaluate.",
                "Spec:",
                "```yaml",
                _yaml_dump(cli_check),
                "```",
            ]
        else:
            parts += [
                "This step's acceptance is graded by the LMS rubric.",
                "Run `skillslab check` to submit your work for grading.",
                "",
            ]
            if rubric:
                parts += ["**Rubric criteria:**", "", rubric.strip(), ""]
            if must_contain:
                parts += ["**Must contain (tokens):**", ""] + [f"- `{t}`" for t in must_contain] + [""]

    parts += [
        "",
        "---",
        "",
        "_When ready_:    `skillslab check`    →    `skillslab next`",
        "",
    ]
    return "\n".join(parts)


def _yaml_dump(obj) -> str:
    try:
        return yaml.safe_dump(obj, default_flow_style=False, sort_keys=False).rstrip()
    except Exception:
        return json.dumps(obj, indent=2)
