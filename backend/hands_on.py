"""hands_on exercise resolver — fetches course-repo manifest + exercise README,
composes editor-launch URLs for the frontend.

Per CLAUDE.md §"BEHAVIORAL TEST HARNESS" + 2026-04-28 architectural pivot:
- The course-repo is the source of truth for problem statement (README) +
  grader (.grading/<exercise>/Hidden*Test.java or verify.sh).
- The LMS shows the slide content, then renders this resolved bundle so
  the learner can launch their editor (Codespace primary, GitHub.dev or
  local clone as escape hatches) and see the README inline.
- Grading flows from skillslab CLI auto-submit (last-passing-run wins) +
  GHA workflow attestation (source of truth — see Phase 3c/3d).

Wire into main.py via:
    from backend.hands_on import resolve_hands_on, fetch_exercise_readme
    @app.get("/api/courses/{course_slug}/exercises/{nn}/launch")
    async def launch(...): ...
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from backend.course_assets import get_course_assets

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# In-memory TTL cache for manifest + README. GitHub raw.* has rate
# limits (60 req/hour unauthenticated). 5 min TTL is enough that a
# typical learner session re-fetches at most ~1×/exercise.
# ─────────────────────────────────────────────────────────────────────
_CACHE_TTL_S = 300
_cache: dict[str, tuple[float, str]] = {}  # url → (expires_at, body)


def _fetch_text(url: str, *, timeout_s: float = 8.0) -> str:
    """Fetch a URL with TTL cache. Raises urllib.error.URLError on failure."""
    now = time.time()
    cached = _cache.get(url)
    if cached and cached[0] > now:
        return cached[1]
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Skillslab-LMS/2026-04-28 hands_on resolver"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        body = r.read().decode("utf-8", errors="replace")
    _cache[url] = (now + _CACHE_TTL_S, body)
    return body


def _invalidate_cache(prefix: str | None = None) -> int:
    """Drop cached entries (admin endpoint use). Returns count dropped."""
    if prefix is None:
        n = len(_cache)
        _cache.clear()
        return n
    drops = [u for u in _cache if u.startswith(prefix)]
    for u in drops:
        del _cache[u]
    return len(drops)


# ─────────────────────────────────────────────────────────────────────
# URL composition (course-repo → editor-launch URLs)
# ─────────────────────────────────────────────────────────────────────
def _owner_repo(course_repo: str) -> str:
    """Normalize 'https://github.com/owner/repo' → 'owner/repo'."""
    s = course_repo.rstrip("/")
    if s.startswith("https://github.com/"):
        return s[len("https://github.com/"):]
    if s.startswith("git@github.com:"):
        s = s[len("git@github.com:"):]
        if s.endswith(".git"):
            s = s[:-4]
        return s
    return s


def _branch_for(nn: str, slug: str, kind: str = "exercise") -> str:
    """Per-exercise branch convention. Default `exercise/NN-<slug>`
    (Opus 2026-04-28). Other kinds for AI-tool meta-skills:

      - kind="exercise" → exercise/NN-<slug>   (code-fix / feature / refactor)
      - kind="meta"     → meta/NN-<slug>       (AI-tool authoring: CLAUDE.md,
                                                hooks, subagents, MCP, etc.)
      - kind="tour"     → tour/<slug>          (guided walkthrough — no NN)
      - kind="extra"    → extra/<slug>         (bonus content)

    Add kinds via the launch endpoint's `kind` query param OR
    demo_data.exercise_kind on hands_on steps. Defaults to "exercise"
    for backwards-compat.
    """
    if kind == "tour":
        return f"tour/{slug}"
    if kind == "extra":
        return f"extra/{slug}"
    return f"{kind}/{nn}-{slug}"


def _exercise_dir(nn: str, slug: str, kind: str = "exercise") -> str:
    """Per-exercise dir convention. Default exercise-NN-<slug>; for
    kind=meta returns meta-NN-<slug>; for tour returns just <slug>.
    Mirrors _branch_for so the launch endpoint composes branch + dir
    consistently per kind.
    """
    if kind == "tour":
        return slug
    if kind == "extra":
        return slug
    return f"{kind}-{nn}-{slug}"


def _codespace_url(owner_repo: str, branch: str) -> str:
    """Open a NEW Codespace from the given branch (zero-setup, devcontainer-pinned)."""
    return f"https://codespaces.new/{owner_repo}?ref={branch}"


def _github_dev_url(owner_repo: str, branch: str) -> str:
    """Web-based VS Code (github.dev). Opens INSTANTLY in browser, no clone."""
    return f"https://github.dev/{owner_repo}/tree/{branch}"


def _clone_command(course_repo: str, branch: str) -> str:
    """Local clone command — escape hatch for power users."""
    repo_name = course_repo.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    return f"git clone {course_repo} && cd {repo_name} && git checkout {branch}"


# ─────────────────────────────────────────────────────────────────────
# Manifest + README fetchers
# ─────────────────────────────────────────────────────────────────────
def _manifest_url(owner_repo: str, branch: str) -> str:
    return f"https://raw.githubusercontent.com/{owner_repo}/{branch}/.grading/manifest.json"


def _readme_url(owner_repo: str, branch: str, exercise_dir: str) -> str:
    return f"https://raw.githubusercontent.com/{owner_repo}/{branch}/.grading/{exercise_dir}/README.md"


def _fetch_manifest(owner_repo: str, branch: str) -> dict:
    raw = _fetch_text(_manifest_url(owner_repo, branch))
    return json.loads(raw)


def _find_exercise(manifest: dict, nn: str) -> Optional[dict]:
    """Find an exercise in the manifest by zero-padded nn ('00', '01', ...)."""
    for ex in (manifest.get("exercises") or []):
        if str(ex.get("nn", "")).zfill(2) == str(nn).zfill(2):
            return ex
    return None


# ─────────────────────────────────────────────────────────────────────
# Public resolver
# ─────────────────────────────────────────────────────────────────────
@dataclass
class HandsOnLaunch:
    """Resolved launch bundle for a hands_on step. Frontend renders this directly."""
    course_slug: str
    exercise_nn: str
    exercise_slug: str
    course_repo: str
    owner_repo: str
    branch: str
    exercise_dir: str
    # From manifest (best-effort; None if manifest unreachable).
    title: Optional[str]
    kind: Optional[str]              # "behavior" | "verify-script" | "anti-exercise"
    estimated_minutes: Optional[int]
    pedagogy: Optional[str]
    primitive: Optional[str]
    assertion: Optional[str]
    # Editor launchers.
    codespace_url: str
    github_dev_url: str
    clone_command: str
    # The grading-runner contract (from manifest top-level).
    grading_runner: str   # default: "bash .grading/run-grading.sh <exercise_dir>"
    # The README content (markdown; frontend renders).
    readme_md: Optional[str]
    # Soft-fail flags: which fetches succeeded.
    manifest_fetched: bool
    readme_fetched: bool

    def to_dict(self) -> dict:
        return {
            "course_slug": self.course_slug,
            "exercise_nn": self.exercise_nn,
            "exercise_slug": self.exercise_slug,
            "course_repo": self.course_repo,
            "owner_repo": self.owner_repo,
            "branch": self.branch,
            "exercise_dir": self.exercise_dir,
            "title": self.title,
            "kind": self.kind,
            "estimated_minutes": self.estimated_minutes,
            "pedagogy": self.pedagogy,
            "primitive": self.primitive,
            "assertion": self.assertion,
            "codespace_url": self.codespace_url,
            "github_dev_url": self.github_dev_url,
            "clone_command": self.clone_command,
            "grading_runner": self.grading_runner,
            "readme_md": self.readme_md,
            "manifest_fetched": self.manifest_fetched,
            "readme_fetched": self.readme_fetched,
        }


def resolve_hands_on(
    course_slug: str,
    nn: str,
    slug: str,
    kind: str = "exercise",
) -> HandsOnLaunch:
    """Resolve a hands_on step's launch bundle.

    Args:
        course_slug: Course identifier (e.g. "jspring", "cc-spring") — must
            be registered in backend.course_assets.
        nn: Two-character zero-padded exercise number ("00", "01", ...).
            Ignored for kind="tour" / kind="extra".
        slug: Kebab-case exercise slug ("fix-n-plus-one", "build-claude-md").
        kind: 2026-04-28 — branch family. "exercise" (default), "meta",
            "tour", "extra". See `_branch_for`/`_exercise_dir` for shapes.
            Required for cc-spring's meta/* branches (build-claude-md,
            hooks-and-commands, custom-subagent, etc.) since they live
            outside the exercise/* family.

    Returns: HandsOnLaunch with composed URLs + (best-effort) manifest data
        and README content. Manifest/README fetches are SOFT FAILS — the
        bundle still resolves with composed URLs even if GitHub is
        unreachable; the frontend can render bootstrap CTAs and show a
        "README unavailable, see github.com/..." fallback.

    Raises: ValueError on unknown course_slug. (HTTPException-mapped at the
        endpoint layer.)
    """
    asset = get_course_assets(course_slug)
    if not asset:
        raise ValueError(f"Unknown course_slug: {course_slug!r}")

    nn_padded = str(nn).zfill(2)
    owner_repo = _owner_repo(asset.course_repo)
    branch = _branch_for(nn_padded, slug, kind=kind)
    exercise_dir = _exercise_dir(nn_padded, slug, kind=kind)

    title = None
    kind = None
    estimated_minutes = None
    pedagogy = None
    primitive = None
    assertion = None
    grading_runner = "bash .grading/run-grading.sh"  # default contract
    manifest_fetched = False
    readme_fetched = False
    readme_md: Optional[str] = None

    # Try fetch manifest first (small, cached)
    try:
        manifest = _fetch_manifest(owner_repo, branch)
        manifest_fetched = True
        if manifest.get("grading_runner_path"):
            grading_runner = f"bash {manifest['grading_runner_path']}"
        ex = _find_exercise(manifest, nn_padded)
        if ex:
            title = ex.get("title")
            kind = ex.get("kind")
            estimated_minutes = ex.get("estimated_minutes")
            pedagogy = ex.get("pedagogy")
            primitive = ex.get("primitive")
            assertion = ex.get("assertion")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
        log.warning(
            "hands_on: manifest fetch failed for %s exercise %s: %s",
            course_slug, nn_padded, e,
        )

    # Fetch README — try the canonical path first, then fall back through
    # other known layouts. 2026-04-28: external course-repos (e.g. the
    # inspiration repo claude-code-springboot-exercises) keep the problem
    # statement at the BRANCH ROOT (EXERCISE.md / CLAUDE_INSTRUCTIONS.md)
    # instead of inside .grading/. The launch endpoint MUST handle both so
    # the LMS can plug in to externally-authored course-repos without
    # forcing them to mirror our internal layout.
    base = f"https://raw.githubusercontent.com/{owner_repo}/{branch}"
    readme_candidates = [
        # Skillslab convention (jspring / kimi / aie / future)
        f"{base}/.grading/{exercise_dir}/README.md",
        # Inspiration-repo convention (per-exercise dir, no dot-prefix)
        f"{base}/grading/{exercise_dir}/README.md",
        # Inspiration-repo convention (problem statement at branch root)
        f"{base}/EXERCISE.md",
        # Spring/Java convention some courses ship
        f"{base}/README.md",
    ]
    fetched_parts: list[str] = []
    for url in readme_candidates:
        try:
            text = _fetch_text(url)
            if text and text.strip():
                # First successful fetch wins for the primary content. If
                # subsequent paths also exist (e.g. EXERCISE.md AND
                # CLAUDE_INSTRUCTIONS.md), the frontend can show them as
                # collapsible sections via a future enhancement.
                fetched_parts.append(text)
                readme_fetched = True
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            continue
    if not readme_fetched:
        log.warning(
            "hands_on: README/EXERCISE.md not found for %s/%s in any of %d candidate paths",
            course_slug, exercise_dir, len(readme_candidates),
        )
    # Optionally append CLAUDE_INSTRUCTIONS.md when it lives at branch root
    # (inspiration-repo pattern) — gives learners the recommended Claude
    # workflow alongside the problem statement.
    if readme_fetched:
        try:
            ci = _fetch_text(f"{base}/CLAUDE_INSTRUCTIONS.md")
            if ci and ci.strip():
                fetched_parts.append(
                    "\n\n---\n\n## Recommended workflow with Claude Code\n\n" + ci
                )
        except (urllib.error.URLError, urllib.error.HTTPError):
            pass
    if fetched_parts:
        readme_md = "\n\n".join(fetched_parts)

    return HandsOnLaunch(
        course_slug=course_slug,
        exercise_nn=nn_padded,
        exercise_slug=slug,
        course_repo=asset.course_repo,
        owner_repo=owner_repo,
        branch=branch,
        exercise_dir=exercise_dir,
        title=title,
        kind=kind,
        estimated_minutes=estimated_minutes,
        pedagogy=pedagogy,
        primitive=primitive,
        assertion=assertion,
        codespace_url=_codespace_url(owner_repo, branch),
        github_dev_url=_github_dev_url(owner_repo, branch),
        clone_command=_clone_command(asset.course_repo, branch),
        grading_runner=grading_runner + " " + exercise_dir,
        readme_md=readme_md,
        manifest_fetched=manifest_fetched,
        readme_fetched=readme_fetched,
    )
