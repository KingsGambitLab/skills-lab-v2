"""`skillslab toc` — bird's-eye outline of a course.

Reads meta.json (the cursor + step list captured by `start`) and
progress.json (per-step completed flags + scores) and renders a
✓/▶/◯ outline showing where the learner is in the whole course.
"""
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.text import Text

from ..theme import Theme, Capabilities


def render_toc(
    *,
    meta: dict,
    progress: dict,
    theme: Theme,
    caps: Capabilities,
) -> Panel | Text:
    """Render a course table-of-contents.

    Args:
        meta: contents of ~/.skillslab/<slug>/meta.json. Must have
              `course_title` + `steps` (list of cursor entries with
              module_pos, step_pos, title, id).
        progress: contents of progress.json (or partial response from
                  /api/progress/<course_id>). Maps step_id → {completed,
                  score} or similar.
        theme: course Theme
        caps: terminal Capabilities

    Returns: Panel for rich; Text for plain.

    Renders:
        ✓ done    ▶ active (cursor)    ◯ pending
    Score appears next to graded steps.
    """
    title = meta.get("course_title") or theme.label
    cursor_idx = int(meta.get("cursor", 0) or 0)
    steps = meta.get("steps") or []

    # Build a per-step-id index from progress data. Tolerate multiple
    # shapes since different callers may pass either /api/progress or
    # local progress.json.
    progress_by_id: dict[str, dict] = {}
    if isinstance(progress, dict):
        # Shape A: {"steps": [{step_id, completed, score}, ...]}
        for s in progress.get("steps", []) or []:
            sid = s.get("step_id") or s.get("id")
            if sid is not None:
                progress_by_id[str(sid)] = s
        # Shape B: flat dict {step_id: {...}}
        for k, v in progress.items():
            if k == "steps":
                continue
            if isinstance(v, dict):
                progress_by_id.setdefault(str(k), v)

    # Group steps by module
    modules: dict[int, list[tuple[int, dict]]] = {}
    for idx, s in enumerate(steps):
        mp = int(s.get("module_pos", 0) or 0)
        modules.setdefault(mp, []).append((idx, s))

    body = Text()
    if not caps.rich:
        body.append(f"{title}\n\n", style="bold")
    else:
        body.append("\n")

    for mod_pos in sorted(modules.keys()):
        mod_steps = modules[mod_pos]
        mod_label = f"M{mod_pos - 1}"  # M0 = preflight convention
        # Module header line (use first step's module_title if set)
        mod_title = ""
        for _, s in mod_steps:
            if s.get("module_title"):
                mod_title = s["module_title"]
                break
        # Compute module completion
        done = 0
        for _, s in mod_steps:
            sid = s.get("id") or s.get("step_id")
            if sid is not None and progress_by_id.get(str(sid), {}).get("completed"):
                done += 1
        total = len(mod_steps)
        mod_state_glyph = "✓" if (done == total and total > 0) else ("▶" if any(idx == cursor_idx for idx, _ in mod_steps) else "◯")
        glyph = mod_state_glyph if caps.unicode_boxes else mod_state_glyph.replace("✓","[x]").replace("▶","[>]").replace("◯","[ ]")
        mod_color = "green" if mod_state_glyph == "✓" else (theme.accent if mod_state_glyph == "▶" else "dim")
        body.append(f"  {glyph}  ", style=mod_color)
        body.append(f"{mod_label}", style=f"bold {mod_color}")
        if mod_title:
            body.append(f"  {mod_title}", style="bold white" if mod_state_glyph != "◯" else "dim")
        body.append("\n")

        for idx, s in mod_steps:
            sid = s.get("id") or s.get("step_id")
            sp = int(s.get("step_pos", 0) or 0)
            stitle = (s.get("title") or "")[:60]
            prog = progress_by_id.get(str(sid), {})
            completed = bool(prog.get("completed"))
            score = prog.get("score")

            is_cursor = (idx == cursor_idx)
            if completed:
                step_glyph = "✓"
                step_style = "green"
            elif is_cursor:
                step_glyph = "▶"
                step_style = theme.accent
            else:
                step_glyph = "◯"
                step_style = "dim"

            ascii_glyph = step_glyph if caps.unicode_boxes else step_glyph.replace("✓","[x]").replace("▶","[>]").replace("◯","[ ]")
            body.append(f"      {ascii_glyph}  ", style=step_style)
            body.append(f"S{sp}  ", style=f"dim {step_style}")
            body.append(stitle, style="white" if (completed or is_cursor) else "dim")
            if isinstance(score, (int, float)) and score > 0:
                pct = int(round(score * 100)) if score <= 1.0 else int(score)
                body.append(f"   score {pct}%", style="dim")
            if is_cursor:
                body.append(" ", style="dim")
                body.append("← you are here", style=theme.accent)
            body.append("\n")
        body.append("\n")

    if not caps.rich:
        return body

    return Panel(
        body,
        title=f"[{theme.accent_dim}]── {title} ──[/]",
        title_align="left",
        border_style=theme.accent_dim,
        box=theme.box if caps.unicode_boxes else box.ASCII,
        padding=(0, 1),
    )
