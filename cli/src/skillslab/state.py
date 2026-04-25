"""State + filesystem layout for the skillslab CLI.

EVERYTHING is files. Paths are stable + readable from any text editor:

    ~/.skillslab/
    ├── token                     # one bearer token per host
    ├── api_url                   # which LMS server the CLI talks to (defaults http://localhost:8001)
    ├── web_url                   # which URL the LEARNER opens in their browser (auto-derived from api_url
    │                              # — `host.docker.internal` → `localhost` — but overridable for prod/staging)
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

API URL vs Web URL — TWO separate addresses, ONE config knob each
-----------------------------------------------------------------
Inside the Docker container, the CLI talks to the LMS via SKILLSLAB_API_URL
(default `http://host.docker.internal:8001` in dev compose; `https://lms.example.com`
in prod). That URL is correct *from inside the container*.

But when a `web` step asks the learner to "Open in your browser:", the URL
must be the one the LEARNER's host browser can reach. `host.docker.internal`
only resolves inside Docker — outside, the host browser needs `localhost:8001`
in dev, or `https://lms.example.com` in prod.

Resolution order for `web_url()`:
  1. SKILLSLAB_WEB_URL env var (explicit override)
  2. ~/.skillslab/web_url file (set via `skillslab config web-url <url>`)
  3. Auto-derived from api_url(): swap `//host.docker.internal` → `//localhost`
     (covers the dev-Docker case for free; prod where api == web is also fine
     because no host.docker.internal is involved)
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

    2026-04-25 v2 — same empty-env-var hardening as web_url(): truthy check
    rather than membership check. docker-compose.yml may default
    SKILLSLAB_API_URL to '' which used to return '' here.
    """
    explicit = os.environ.get("SKILLSLAB_API_URL", "").strip()
    if explicit:
        return explicit
    p = home() / "api_url"
    if p.exists():
        return p.read_text().strip() or DEFAULT_API_URL
    return DEFAULT_API_URL


def set_api_url(url: str) -> None:
    (home() / "api_url").write_text(url.rstrip("/"))


def web_url() -> str:
    """URL the LEARNER opens in their browser (a `web` step's dashboard link).

    Distinct from api_url() because of the Docker case: `host.docker.internal`
    only resolves *inside* a container; from the host browser it doesn't resolve
    at all. Resolution order:

      1. SKILLSLAB_WEB_URL env var (explicit override — set in prod/staging)
      2. ~/.skillslab/web_url file (set via `skillslab config web-url <url>`)
      3. Auto-derive from api_url(): swap host.docker.internal → localhost

    For prod where API and web share an FQDN (e.g. `https://lms.example.com`),
    just point SKILLSLAB_API_URL there and (3) returns it untouched.

    2026-04-25 v2 — TRUTHY check, not membership check. CLI-walk v1 caught
    that the docker-compose.yml DEFAULTS the env var to empty-string via
    `${SKILLSLAB_WEB_URL:-}`, which makes `"X" in os.environ` True but the
    value useless. An empty string here returned `""` and produced URLs
    like `/#created-...` (no host). Truthy check falls through to the
    auto-derive path, which is the correct behavior.
    """
    explicit = os.environ.get("SKILLSLAB_WEB_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    p = home() / "web_url"
    if p.exists():
        v = p.read_text().strip()
        if v:
            return v.rstrip("/")
    api = api_url().rstrip("/")
    # The only known auto-derivation: dev-Docker → host browser.
    # Don't try to be clever about other hostnames; if api_url is exotic, the
    # user should set SKILLSLAB_WEB_URL explicitly.
    return api.replace("//host.docker.internal", "//localhost")


def set_web_url(url: str) -> None:
    (home() / "web_url").write_text(url.rstrip("/"))


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
