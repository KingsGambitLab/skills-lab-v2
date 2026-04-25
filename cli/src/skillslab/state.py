"""State + filesystem layout for the skillslab CLI.

EVERYTHING is files. Paths are stable + readable from any text editor:

    ~/.skillslab/
    ├── token                     # one bearer token per host
    ├── api_url                   # which LMS server to talk to (defaults http://localhost:8001)
    └── <course-slug>/
        ├── meta.json             # course id, modules, current step pointer, last sync
        ├── progress.json         # mirror of /api/auth/my-courses for this slug
        └── steps/
            ├── M0.S1-what-this-course-is.md       # ← full step content as markdown
            ├── M0.S2-smoke-test-your-toolchain.md
            └── ...

Course-repo (the curriculum itself) is checked out to the learner's
chosen working dir — NOT under ~/.skillslab. The CLI just remembers
its path in <course-slug>/meta.json under repo_dir.

Design choices:
  - Files first; JSON only where structure helps (meta + progress)
  - Step markdown is human-grep-able + editor-openable + offline-readable
  - The CLI never invents data; everything mirrors the LMS API
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_HOME = Path.home() / ".skillslab"
DEFAULT_API_URL = os.environ.get("SKILLSLAB_API_URL", "http://localhost:8001")


def home() -> Path:
    p = Path(os.environ.get("SKILLSLAB_HOME") or DEFAULT_HOME)
    p.mkdir(parents=True, exist_ok=True)
    return p


def token_path() -> Path:
    return home() / "token"


def api_url() -> str:
    """API URL is configurable via env, with a fallback file at ~/.skillslab/api_url.
    First-run sets it from DEFAULT_API_URL.
    """
    p = home() / "api_url"
    if "SKILLSLAB_API_URL" in os.environ:
        return os.environ["SKILLSLAB_API_URL"]
    if p.exists():
        return p.read_text().strip() or DEFAULT_API_URL
    return DEFAULT_API_URL


def set_api_url(url: str) -> None:
    (home() / "api_url").write_text(url.rstrip("/"))


def get_token() -> str | None:
    p = token_path()
    if not p.exists():
        return None
    return p.read_text().strip() or None


def set_token(token: str) -> None:
    p = token_path()
    p.write_text(token)
    p.chmod(0o600)


def clear_token() -> None:
    p = token_path()
    if p.exists():
        p.unlink()


def course_dir(slug: str) -> Path:
    p = home() / slug
    p.mkdir(parents=True, exist_ok=True)
    (p / "steps").mkdir(parents=True, exist_ok=True)
    return p


def read_meta(slug: str) -> dict[str, Any]:
    f = course_dir(slug) / "meta.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text())
    except Exception:
        return {}


def write_meta(slug: str, meta: dict[str, Any]) -> None:
    (course_dir(slug) / "meta.json").write_text(json.dumps(meta, indent=2))


def write_progress(slug: str, progress: dict[str, Any]) -> None:
    (course_dir(slug) / "progress.json").write_text(json.dumps(progress, indent=2))


def step_filename(module_pos: int, step_pos: int, title: str) -> str:
    """Build a stable, sortable, readable filename for a step's markdown.
    `M{module}.S{step}-{slug}.md` so `ls steps/` already shows the course
    in the right order.
    """
    safe = "".join(
        ch.lower() if ch.isalnum() else "-" for ch in (title or "step")
    ).strip("-")
    safe = "-".join(filter(None, safe.split("-")))[:60] or "step"
    # Human numbering: M0/S0 if module is at backend position 1, else position-1
    return f"M{module_pos - 1}.S{step_pos}-{safe}.md"


def step_path(slug: str, module_pos: int, step_pos: int, title: str) -> Path:
    return course_dir(slug) / "steps" / step_filename(module_pos, step_pos, title)


@dataclass
class StepCursor:
    module_pos: int   # 1-indexed at backend (M0 = position 1)
    step_pos: int     # 0-indexed within module
    step_id: int
    title: str
    exercise_type: str

    def label(self) -> str:
        return f"M{self.module_pos - 1}.S{self.step_pos}"
