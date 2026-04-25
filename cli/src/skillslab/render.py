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

# Block-level browser-only content that must be REMOVED ENTIRELY (tag + body),
# not just have its tags stripped — otherwise the body bleeds into the terminal
# as raw JS / CSS / SVG markup. The web frontend executes / renders these; the
# terminal can't, so they're noise either way.
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.DOTALL | re.IGNORECASE)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style\s*>", re.DOTALL | re.IGNORECASE)
_NOSCRIPT_RE = re.compile(r"<noscript\b[^>]*>.*?</noscript\s*>", re.DOTALL | re.IGNORECASE)
_HEAD_RE = re.compile(r"<head\b[^>]*>.*?</head\s*>", re.DOTALL | re.IGNORECASE)
_SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg\s*>", re.DOTALL | re.IGNORECASE)
_IFRAME_RE = re.compile(r"<iframe\b[^>]*>.*?</iframe\s*>", re.DOTALL | re.IGNORECASE)
_TEMPLATE_RE = re.compile(r"<template\b[^>]*>.*?</template\s*>", re.DOTALL | re.IGNORECASE)


# Steps that are interactive widgets in the browser still ship via the LMS
# as "concept" content with embedded <script>. The CLI doesn't have a JS
# runtime — without this strip, the script body bleeds in as raw JS source.
def _strip_browser_only_blocks(s: str) -> str:
    s = _SCRIPT_RE.sub("", s)
    s = _STYLE_RE.sub("", s)
    s = _NOSCRIPT_RE.sub("", s)
    s = _HEAD_RE.sub("", s)
    s = _SVG_RE.sub("[interactive diagram — see browser]", s)
    s = _IFRAME_RE.sub("[embedded frame — see browser]", s)
    s = _TEMPLATE_RE.sub("", s)
    return s


def html_to_markdown(html: str) -> str:
    if not html:
        return ""
    # Step 0: strip browser-only blocks BEFORE any other processing — their
    # bodies must vanish, not just their tags. (Bug surfaced 2026-04-25 on
    # AIE M5.S1 widget that dumped 60+ lines of (function(){})() into the
    # learner's terminal.)
    s = _strip_browser_only_blocks(html)

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


_GITHUB_URL_RE = re.compile(r"https?://github\.com/[\w\-]+/[\w\-]+(?:\.git)?")
_GIT_CLONE_RE = re.compile(r"git\s+clone\s+(\S+\.git)")
# Loose `git clone https://github.com/owner/repo` (no .git suffix required) —
# matches what the LLM emits inside `<pre>` blocks in concept/instruction HTML.
_GIT_CLONE_LOOSE_RE = re.compile(r"git\s+clone\s+(https?://github\.com/[\w\-]+/[\w\-\.]+?)(?=[\s)\"'<]|$)")
_GIT_CHECKOUT_RE = re.compile(r"git\s+checkout\s+([\w\-/]+)")
# Tight discovery — only treat a github URL as the module repo when it
# appears within ~80 chars of a fork/clone/checkout keyword (signal
# that it's the action target, not an example/library reference).
_FORK_CONTEXT_RE = re.compile(
    r"(?:\bfork\b|\bclone\b|\bcheckout\b|git\s+clone|git\s+checkout)"
    r".{0,80}?"
    r"(https?://github\.com/[\w\-]+/[\w\-\.]+?)(?=[\s)\"'<]|$)",
    re.IGNORECASE | re.DOTALL,
)


def find_module_repo(steps: list[dict]) -> dict | None:
    """Discover the module's starter repo by scanning sibling steps.

    Mirrors the browser's `_findModuleRepoMeta` (frontend/index.html). Same
    discovery layers, in the same order, so terminal + browser show the
    same answer. Per CLAUDE.md "rendering layer owns presentation" — we
    don't ask the LLM to copy-paste the URL into every step.

    Layers (most-canonical first):
      1. step.demo_data.starter_repo  (structured per CLAUDE.md F26)
      2. step.demo_data.bootstrap_command — `git clone <url> ... [git checkout <branch>]`
      3. github URL grep on demo_data.instructions / step.content (legacy)
    Returns: {"url": str, "ref": str|None, "source_step_id": int} or None.
    """
    if not steps:
        return None
    # 1. Structured starter_repo
    for s in steps:
        sr = (s.get("demo_data") or {}).get("starter_repo")
        if isinstance(sr, dict) and sr.get("url"):
            return {
                "url": sr["url"].rstrip("/").rstrip(".git") + (".git" if sr["url"].endswith(".git") else ""),
                "ref": sr.get("ref"),
                "source_step_id": s.get("id"),
            }
    # 2. bootstrap_command — matches both `.git` URL and bare HTTPS URL
    for s in steps:
        cmd = (s.get("demo_data") or {}).get("bootstrap_command") or ""
        m = _GIT_CLONE_RE.search(cmd) or _GIT_CLONE_LOOSE_RE.search(cmd)
        if m:
            bm = _GIT_CHECKOUT_RE.search(cmd)
            return {
                "url": m.group(1).rstrip(".git"),
                "ref": bm.group(1) if bm else None,
                "source_step_id": s.get("id"),
            }
    # 3. Tight prose discovery: github URL within fork/clone keyword context.
    # Critical: prevents picking up example/library URLs that happen to be in
    # the same content (the user-walk caught us listing 5 module repos when
    # only M6 actually had a fork target — the rest were prose mentions).
    candidates: list[tuple[str, int | None]] = []
    for s in steps:
        text = ((s.get("demo_data") or {}).get("instructions") or "") + " " + (s.get("content") or "")
        for m in _FORK_CONTEXT_RE.finditer(text):
            candidates.append((m.group(1).rstrip(".git"), s.get("id")))
    if candidates:
        # Prefer URLs that show up across MULTIPLE steps (canonical = repeated).
        from collections import Counter
        counts = Counter(url for url, _ in candidates)
        # Pick the most-frequent; tiebreak: first appearance order
        best_url = max(counts.keys(), key=lambda u: (counts[u], -candidates.index((u, next(sid for url, sid in candidates if url == u)))))
        first_sid = next(sid for url, sid in candidates if url == best_url)
        return {"url": best_url, "ref": None, "source_step_id": first_sid}
    return None


def step_to_markdown(
    step: dict,
    course_title: str = "",
    module_title: str = "",
    module_repo: dict | None = None,
) -> str:
    """Build a self-contained markdown file for a step. Stamps minimal
    front-matter with step metadata so the CLI can re-parse later if
    needed. Body is the converted HTML content + a SUBMIT section so the
    learner knows the shape of the acceptance check.

    `module_repo` (if provided) is rendered as a "Module repo" callout
    near the top, so every step in the module shows the same fork/clone
    target — same UX as the browser's module-repo banner.
    """
    sid = step.get("id")
    title = step.get("title", "(untitled)")
    etype = step.get("exercise_type") or "concept"
    content_html = step.get("content") or ""
    code = step.get("code") or ""
    validation = step.get("validation") or {}

    body = html_to_markdown(content_html)

    # Front-matter: module_repo flows in as structured fields so other
    # commands (status / spec / check) can read it without re-parsing prose.
    # `ensure_ascii=False` so unicode characters (em dash —, en dash, smart
    # quotes etc.) pass through verbatim instead of becoming `—` raw
    # escapes. User-filed (2026-04-25): the frontmatter rendered as
    # "M6 — Capstone" which looked like garbled output.
    def _q(s: str) -> str:
        return json.dumps(s, ensure_ascii=False)
    fm = [
        "---",
        f"step_id: {sid}",
        f"exercise_type: {etype}",
        f"title: {_q(title)}",
        f"course: {_q(course_title)}",
        f"module: {_q(module_title)}",
    ]
    if module_repo and module_repo.get("url"):
        fm.append(f"module_repo_url: {_q(module_repo['url'])}")
        if module_repo.get("ref"):
            fm.append(f"module_repo_ref: {_q(module_repo['ref'])}")
    fm.append("---")

    # Module-repo callout right after the title so it's visible in
    # `skillslab spec` regardless of where the step's own content lives.
    # Same UX intent as the browser's module-repo banner — every step in
    # the module shows the same fork/clone target.
    repo_block: list[str] = []
    if module_repo and module_repo.get("url"):
        repo_url = module_repo["url"]
        ref = module_repo.get("ref")
        repo_block = [
            "",
            "> **📦 Module repo:** [" + repo_url + "](" + repo_url + ")"
            + (f"  (branch: `{ref}`)" if ref else ""),
            ">",
            f"> Clone:  `git clone {repo_url}.git`"
            + (f" && cd && `git checkout {ref}`" if ref else ""),
            "",
        ]

    parts = fm + [
        "",
        f"# {title}",
        "",
        f"_module:_ {module_title}    _type:_ `{etype}`    _step id:_ `{sid}`",
    ] + repo_block + [
        "---",
        "",
        body or "_(no briefing provided)_",
    ]

    # 2026-04-25 — user-filed: "Problem statement not found anywhere". The
    # Creator's HTML body usually has narrative ("The Final Checkpoint",
    # "Why This Matters") but the explicit ACTION list lives in
    # demo_data.instructions for terminal_exercise. Surface it as a
    # "## What to do" section so learners always know the steps to perform.
    #
    # 2026-04-25 v2 — CLI-walk v1 caught: instructions is usually a STRING
    # of HTML (`<h3>Step 1: Fork</h3><pre>$ gh repo fork ...</pre>...`).
    # Previous v1 code dumped that as one giant line — Rich's Markdown
    # widget silently strips inline HTML, so a beginner saw the section
    # heading then EMPTY BODY. Worse than no section. Fix: run the same
    # html_to_markdown converter we use on the main body so the section
    # actually renders.
    demo = step.get("demo_data") or {}
    instructions = demo.get("instructions") if isinstance(demo, dict) else None
    if instructions:
        rendered_lines: list[str] = []
        if isinstance(instructions, list):
            for i, instr in enumerate(instructions, 1):
                if isinstance(instr, dict):
                    label = instr.get("label") or instr.get("title") or f"Step {i}"
                    body_txt = instr.get("body") or instr.get("description") or instr.get("text") or ""
                    cmd = instr.get("command") or instr.get("cmd") or ""
                    # body_txt may itself be HTML — convert defensively.
                    if body_txt and ("<" in body_txt and ">" in body_txt):
                        body_txt = html_to_markdown(body_txt)
                    rendered_lines.append(f"{i}. **{label}**")
                    if body_txt:
                        for ln in body_txt.splitlines():
                            rendered_lines.append(f"   {ln}" if ln.strip() else "")
                    if cmd:
                        rendered_lines += [f"   ```", f"   {cmd}", f"   ```"]
                else:
                    # Could be a string item, possibly HTML.
                    txt = str(instr)
                    if "<" in txt and ">" in txt:
                        txt = html_to_markdown(txt)
                    rendered_lines.append(f"{i}. {txt}")
        elif isinstance(instructions, str):
            # The common shape per CLI-walk v1: `<h3>...</h3><pre>...</pre>...`.
            # Always pass through html_to_markdown — it's a no-op on plain text.
            rendered_lines.append(html_to_markdown(instructions))

        # Only emit the section header IF we have actual rendered body —
        # never advertise "What to do" with empty content underneath.
        rendered = "\n".join(rendered_lines).strip()
        if rendered:
            parts += ["", "## What to do", "", rendered, ""]

    # If the step has a `code` field (starter snippet), surface it too
    if code and code.strip():
        parts += ["", "## Starter / Reference", "", "```", code.rstrip(), "```", ""]

    # Acceptance hint — what the CLI's `check` will look at
    rubric = validation.get("rubric") or validation.get("explanation_rubric") or ""
    must_contain = validation.get("must_contain") or []
    cli_check = validation.get("cli_check")
    cli_commands = validation.get("cli_commands") or []
    gha_check = validation.get("gha_workflow_check")
    if cli_check or cli_commands or gha_check or rubric or must_contain:
        parts += ["", "## Acceptance (`skillslab check`)", ""]
        if cli_commands:
            # 2026-04-25 v3 — CLI-walk v3 P1: every regenerated terminal_exercise
            # has cli_commands in DB, the runner executes them at check-time,
            # but the briefing never told the learner WHAT would run. This
            # branch closes the discoverability gap. Each cmd renders as a
            # labeled code block so `skillslab spec` is now a TRUE preview of
            # what `skillslab check` will do.
            parts += [
                "When you run `skillslab check`, the CLI runs the following "
                "commands on your machine, captures their output, and submits "
                "the captured text to the LMS rubric grader. No copy-paste — "
                "the CLI handles capture + submission.",
                "",
                f"**{len(cli_commands)} command{'s' if len(cli_commands) != 1 else ''} will run:**",
                "",
            ]
            for i, c in enumerate(cli_commands, 1):
                if isinstance(c, dict):
                    label = c.get("label") or f"Command {i}"
                    cmd = c.get("cmd", "")
                else:
                    label = f"Command {i}"
                    cmd = str(c)
                parts += [
                    f"{i}. **{label}**",
                    "   ```",
                    f"   $ {cmd}",
                    "   ```",
                ]
            parts += [
                "",
                "_Pass criterion: each command exits 0. Semantic grading "
                "(did the output prove the skill?) is done by the LMS rubric "
                "below on the captured text._",
                "",
            ]
        elif gha_check:
            # 2026-04-25 v3 — GHA-push capstone branch. Runner does git push,
            # polls GHA, watches to conclusion, submits run URL. Briefing
            # explains that flow + what the workflow file checks.
            wf = gha_check.get("workflow_file", "lab-grade.yml")
            expected = gha_check.get("expected_conclusion", "success")
            parts += [
                f"When you run `skillslab check` from inside your fork's clone, "
                f"the CLI commits + pushes the current branch, waits for the "
                f"`{wf}` workflow to complete on GitHub Actions, and submits "
                f"the run URL to the LMS. Pass requires the run's conclusion "
                f"to be `{expected}`.",
                "",
                "_No copy-paste of the run URL — the CLI captures it from `gh run view` and submits._",
                "",
            ]
        elif cli_check:
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
                parts += ["**Rubric criteria:**", "", _rubric_to_text(rubric), ""]
            if must_contain:
                # 2026-04-25 — user-filed: terse `must_contain` bullets
                # like `github.com / passed / test_orders_endpoint.py`
                # carry no context. Add a one-line preface explaining
                # what these tokens are + a heuristic description per
                # token so learners know WHY each must appear in their
                # paste.
                parts += [
                    "**Evidence tokens (auto-detected in your `skillslab check` paste):**",
                    "",
                    "_Your submission must include each of these strings as_ "
                    "_proof you ran the work. The rubric above explains why._",
                    "",
                ]
                parts += [f"- `{t}` — {_describe_must_contain_token(t)}" for t in must_contain]
                parts += [""]

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


def _rubric_to_text(rubric) -> str:
    """The LMS sometimes emits validation.rubric as a string (zero-code
    courses), sometimes as a dict (`{criteria: [...], passing_threshold: 0.7}`),
    sometimes as a list of bullet strings. Normalize to readable markdown so
    the briefing always renders.
    """
    if rubric is None:
        return ""
    if isinstance(rubric, str):
        return rubric.strip()
    if isinstance(rubric, list):
        return "\n".join(f"- {item}" for item in rubric).strip()
    if isinstance(rubric, dict):
        # Common shapes: {criteria: [...], passing_threshold: 0.7}
        # or {scoring: {...}, hints: [...]}. YAML-dump for legibility.
        return _yaml_dump(rubric)
    return str(rubric).strip()


def _describe_must_contain_token(token: str) -> str:
    """Heuristic: produce a 3-8 word description of what a `must_contain`
    token is checking for. Used to expand terse evidence-token bullets
    (`- github.com`) into self-explaining lines (`- github.com — your fork URL`).

    Pattern matches the most common token shapes the Creator emits:
      - URLs / hostnames        → "GitHub fork URL", "API endpoint", etc.
      - File paths              → "the file you ran"
      - Pytest output markers   → "pytest passed indicator"
      - GHA workflow markers    → "GitHub Actions output"
      - mvn / gradle markers    → "Maven build success"
    Falls back to "evidence string" so we always emit SOMETHING.

    User-filed (2026-04-25): bare must_contain bullets carry no context;
    learners don't know whether 'passed' means a Java test or pytest.
    """
    t = (token or "").strip()
    tl = t.lower()
    # URLs first
    if "github.com" in tl:
        if "/actions/runs/" in tl:
            return "GitHub Actions run URL"
        return "GitHub fork URL"
    if tl.startswith(("http://", "https://")):
        return "URL evidence"
    if "://" in tl:
        return "endpoint URL"
    # File paths / file names
    file_exts = (".py", ".java", ".kt", ".ts", ".tsx", ".js", ".go", ".rs",
                 ".sql", ".yml", ".yaml", ".toml", ".md", ".sh")
    if any(tl.endswith(ext) for ext in file_exts):
        return f"the {tl.rsplit('.', 1)[-1]} file you worked on"
    if "/" in t and not t.startswith("/"):
        return "file path"
    # Test / build framework output markers
    if tl in ("passed", "pass", "ok", "success", "succeeded"):
        return "test/run success indicator"
    if tl in ("failed", "fail", "error"):
        return "failure marker (for negative-case proofs)"
    if tl.startswith("build success"):
        return "Maven/Gradle build success"
    if "tests passed" in tl or "tests ran" in tl:
        return "test runner output"
    if tl.startswith("pytest") or "py::" in tl:
        return "pytest output line"
    if tl.startswith("mvn ") or "[info]" in tl or "build success" in tl:
        return "Maven build output"
    if "gradle" in tl:
        return "Gradle build output"
    if "junit" in tl:
        return "JUnit output"
    if tl.startswith("gh run") or tl.startswith("workflow_dispatch"):
        return "GitHub Actions output"
    if "completed successfully" in tl or "conclusion: success" in tl:
        return "GHA conclusion line"
    # Common keywords
    if tl in ("commit", "merge", "branch", "main", "master"):
        return "git output marker"
    if tl in ("docker", "container", "image"):
        return "Docker output marker"
    # Generic fallback — better than nothing
    return "evidence string (must appear in your paste)"
