"""Docker-based real-execution runner (2026-04-22).

Shipped per the "no mocks, Docker-per-run is OK" north-star directive.
Replaces `_build_mock_modules` stubs as the primary execution path for
code_exercise + hidden_tests validation.

Execution model
---------------
1. Pick a base image per language: `python:3.11-slim`, `node:20-slim`,
   `golang:1.22-alpine`, `postgres:16-alpine`.
2. Write learner code + tests into a fresh tempdir.
3. Write a requirements file if Creator provided one (`requirements.txt`,
   `package.json`, `go.mod`).
4. `docker run --rm -v <tempdir>:/app -w /app --network=none --memory=512m
                --cpus=1.0 <image> <cmd>` where `<cmd>` is `sh -c
                'pip install -q -r requirements.txt && pytest -q /app/tests'`
   (or the language-equivalent).
5. Capture stdout/stderr + exit code. Parse pass/fail per test from pytest/jest/go-test output.
6. Clean up tempdir.

Security
--------
- `--network=none`: no outbound traffic from learner code.
- `--memory=512m --cpus=1.0`: resource cap.
- `--rm`: container auto-removed on exit.
- Tempdir mounted read-write but scoped; wiped on finish.
- Wall-clock timeout (default 60s — tunable per exercise).

Availability
------------
`is_docker_available()` returns False when the docker daemon isn't reachable.
Callers fall back to the legacy in-process sandbox in that case.

Languages supported (V1)
------------------------
- python (pytest) — first-class
- javascript / typescript (jest / vitest) — image: node:20-slim
- go (go test) — image: golang:1.22-alpine
- sql (psql) — image: postgres:16-alpine (with ephemeral postgres running)

Extending
---------
Add a new language = one entry in `_IMAGES` + a `_cmd_for_lang` branch.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any

log = logging.getLogger(__name__)


_IMAGES: dict[str, str] = {
    "python":      "python:3.11-slim",
    "py":          "python:3.11-slim",
    "javascript":  "node:20-slim",
    "js":          "node:20-slim",
    "typescript":  "node:20-slim",
    "ts":          "node:20-slim",
    "go":          "golang:1.22-alpine",
    "golang":      "golang:1.22-alpine",
    "sql":         "postgres:16-alpine",
    "postgres":    "postgres:16-alpine",
}

# Gap C (2026-04-22): pre-built images with pytest + top-20 libs pre-installed.
# Build locally via `docker build -t sll-python-runner:latest -f
# backend/docker_images/sll-python-runner.Dockerfile backend/docker_images/`.
# When available + no extra requirements requested, use these to skip the
# ~6-8s pip-install step on every submission.
_PREBUILT_IMAGES: dict[str, str] = {
    "python":      "sll-python-runner:latest",
    "py":          "sll-python-runner:latest",
    "javascript":  "sll-node-runner:latest",
    "js":          "sll-node-runner:latest",
    "typescript":  "sll-node-runner:latest",
    "ts":          "sll-node-runner:latest",
    # 2026-04-22 v7: Go runner with pre-baked go.mod + warm stdlib cache.
    # Saves ~10-15s per invariant check (skips go mod init / go mod tidy /
    # stdlib cold compile). Build: see sll-go-runner.Dockerfile header.
    "go":          "sll-go-runner:latest",
    "golang":      "sll-go-runner:latest",
}


# ═══════════════════════════════════════════════════════════════════════════
# LANGUAGE RUNTIME REGISTRY (2026-04-22 v7)
# ═══════════════════════════════════════════════════════════════════════════
# User directive: "Make sure fixes are extensible to all languages and
# frameworks. Don't hard code anything."
#
# Every per-language decision (Docker image, structured-output sentinel name,
# JSON/XML parser, regex-fallback parser, heuristic incompleteness markers,
# scaffold commands) lives in ONE LanguageConfig entry below. Adding Rust /
# Java / Ruby / C# / Swift / Kotlin / PHP = append one dataclass instance to
# `_LANG_CONFIGS` and register its image/parser. No edits elsewhere.
#
# The three dispatch functions (`_cmd_for_lang`, `_heuristic_starter_is_incomplete`,
# `_parse_test_results`) read from this registry. Hard-coded if/elif branches
# for per-language behavior are gone.

from dataclasses import dataclass, field
from typing import Callable, Optional


def _wrap_with_sentinels(name: str, cmd: str, file_path: str | None = None) -> str:
    """Wrap a test command so its output is bracketed between
    __<NAME>_START__ / __<NAME>_END__ markers for deterministic extraction.

    If `file_path` is provided, the command writes structured output to a
    file and we `cat` the file between sentinels (pattern used by
    pytest --junitxml and jest --outputFile). If None, the cmd's own stdout
    is sentinel-wrapped directly (pattern used by `go test -json`).

    Returns a shell fragment. Caller chains with other steps via `;` or `&&`.
    """
    start = f"echo __{name}_START__"
    end = f"echo __{name}_END__"
    if file_path is not None:
        # Run cmd → cat the file it wrote → terminator + exit code
        return (
            f"{cmd}; "
            f"_EXIT=$?; "
            f"{start}; "
            f"[ -f {file_path} ] && cat {file_path} || echo '<NO_OUTPUT/>'; "
            f"{end}; "
            f"echo EXIT_CODE=$_EXIT"
        )
    # Stream-to-stdout pattern (go test -json)
    return (
        f"{start}; "
        f"{cmd}; "
        f"_EXIT=$?; "
        f"{end}; "
        f"echo EXIT_CODE=$_EXIT"
    )


def _extract_sentinel_block(output: str, name: str) -> Optional[str]:
    """Extract the block between __<NAME>_START__ and __<NAME>_END__ markers.
    Returns None if sentinels aren't present (caller falls back to regex parse
    of the full output).
    """
    import re as _re
    m = _re.search(
        rf"__{name}_START__\n(.*?)\n__{name}_END__",
        output or "",
        _re.DOTALL,
    )
    return m.group(1) if m else None


@dataclass
class LanguageConfig:
    """Per-language runtime config — one entry per language in _LANG_CONFIGS.

    Adding a new language = append one instance; no code changes elsewhere.

    Attributes:
        ids: aliases (lowercased) that match this config.
        image: base Docker image.
        prebuilt_image: optional prebuilt image with test framework pre-installed.
        sentinel: name used by _wrap_with_sentinels / _extract_sentinel_block.
        structured_parser: callable (block_content) -> dict|None.
        fallback_parser: callable (full_output) -> dict.
        incompleteness_markers: list of (regex, reason_label) tuples.
        precise_check: optional (starter, tests) -> (is_incomplete, reason)|None.
        defer_on_ambiguous: when no marker matches, defer to Docker (True) or
            hard-reject (False).
        compile_check_cmd: shell command that does a CHEAP compile / syntax
            check INSIDE the container. Runs BEFORE the full test invariant
            so compile errors (~2-5s) are caught fast instead of waiting
            for the full test run (~15-60s). If this exits nonzero, the
            retry loop gets the compile error IMMEDIATELY without paying
            test execution cost. Language examples:
                python: `python -m py_compile solution.py`
                go:     `go build ./...`
                js:     `node --check solution.js`
                ts:     `npx tsc --noEmit solution.ts`
            Set to None to skip the pre-check (e.g. shell scripts).
    """
    ids: tuple[str, ...]
    image: str
    prebuilt_image: Optional[str] = None
    sentinel: Optional[str] = None
    structured_parser: Optional[Callable[[str], Optional[dict]]] = None
    fallback_parser: Optional[Callable[[str], dict]] = None
    incompleteness_markers: tuple[tuple[str, str], ...] = ()
    precise_check: Optional[Callable[[str, str], Optional[tuple[bool, str]]]] = None
    defer_on_ambiguous: bool = True
    compile_check_cmd: Optional[str] = None
    # ────────────────────────────────────────────────────────────────────
    # v8.5 Phase 1 HARNESS-LEVEL DEP MANAGEMENT (2026-04-23)
    # See CLAUDE.md §LANGUAGE EXTENSION — HARNESS-LEVEL DEP MANAGEMENT.
    # Goal: keep dep-resilience out of per-language prompts. Each config
    # declares its own merge rules + verify command; the runner applies
    # them uniformly.
    # ────────────────────────────────────────────────────────────────────
    # Post-install command run INSIDE the container after the LLM's deps
    # install, BEFORE the test runner. Exit non-zero (ideally 127) on drift;
    # stderr becomes retry-feedback via the `DEP_DRIFT` detection in main.py.
    # Example: "python /opt/verify_baked.py".
    verify_baked_cmd: Optional[str] = None
    # Package names (lowercase) the LLM's emitted requirements MUST NOT
    # pin — typically the test framework + test plugins. The harness-level
    # merge function strips these from the emitted requirements BEFORE
    # install (and logs what it stripped so retry-feedback surfaces it).
    forbidden_llm_pins: frozenset[str] = frozenset()
    # Package specs (package==version) our runner ALWAYS installs regardless
    # of what the LLM emits. Typically the test framework. These appear in
    # the merged requirements file after LLM's entries.
    always_required_packages: tuple[str, ...] = ()
    # Per-language function: (llm_emitted_requirements_text, config) -> final_text.
    # Handles format conversion (pip flat list, npm JSON, go.mod, Cargo.toml),
    # whitelists safe directives, strips forbidden pins, appends always-required.
    # Returns (merged_text, stripped_entries_list). `stripped_entries_list` is
    # surfaced in retry-feedback so the LLM sees what we rejected.
    requirements_merge_fn: Optional[Callable[[str, "LanguageConfig"], tuple[str, list[str]]]] = None
    # ────────────────────────────────────────────────────────────────────
    # v8.6.1 (2026-04-24) VERSION-COMPAT AUTO-PIN
    # Language-agnostic data structure that each LanguageConfig declares:
    # a dict of {pkg_name: (min_version_too_new, safe_downgrade_version)}.
    # At merge time, the merge_fn auto-rewrites any LLM-emitted dep whose
    # version >= min_version_too_new to safe_downgrade_version. Silent to
    # the LLM (logged via stripped_entries). Closes the class of bug where
    # "LLM picks latest, latest requires newer toolchain than baked image".
    # Example for Go 1.22:
    #   {"golang.org/x/time": ("v0.15.0", "v0.7.0"),
    #    "golang.org/x/sync": ("v0.11.0", "v0.8.0")}
    # Interpretation: any x/time >= v0.15.0 gets downgraded to v0.7.0
    # because the baked Go (1.22) can't satisfy v0.15+'s go >= 1.25 req.
    # ────────────────────────────────────────────────────────────────────
    version_compat_map: dict[str, tuple[str, str]] = field(default_factory=dict)
    # ────────────────────────────────────────────────────────────────────
    # v8.5 Phase D COMPILER-GROUNDED RETRY FEEDBACK (2026-04-23)
    # See CLAUDE.md §COMPILER-GROUNDED RETRY FEEDBACK.
    # When a retry fails with a static-check error code in this list, the
    # harness invokes `solution_shape_extractor(solution_code)` to extract
    # the REAL inferred type/signature from the toolchain, then prepends it
    # to the retry-feedback. Turns "TS2339: Property 'error' does not exist"
    # (6-retry thrash) into "here's the real type, write a test that
    # narrows" (typically 1-retry fix).
    # ────────────────────────────────────────────────────────────────────
    # Error codes / regex substrings that indicate a narrowing or inferred-
    # type mismatch the LLM could fix if given the solution's real shape.
    # TS: TS2339 (property doesn't exist), TS2532 (object possibly undefined),
    #     TS18048 (possibly undefined), TS2322 (type not assignable).
    type_grounding_error_codes: tuple[str, ...] = ()
    # Extract the solution's inferred type/shape. Language-specific:
    #   TS:   `tsc --declaration` → .d.ts content
    #   Rust: `cargo check --message-format=json` → suggested fix JSON
    #   Py:   `mypy --reveal-type` → type annotations
    #   Java: `javac -Xlint:all` → typed signature lines
    # Returns None when extraction fails (retry falls back to raw error).
    solution_shape_extractor: Optional[Callable[[str], Optional[str]]] = None


# Registry — populated below each dispatch fn's definition so callables resolve.
_LANG_CONFIGS: list[LanguageConfig] = []


def _get_lang_config(language: str) -> Optional[LanguageConfig]:
    lo = (language or "").lower()
    for cfg in _LANG_CONFIGS:
        if lo in cfg.ids:
            return cfg
    return None


def _image_exists_locally(image: str) -> bool:
    try:
        r = subprocess.run(
            ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


_DOCKER_AVAILABLE: bool | None = None


def is_docker_available() -> bool:
    """Cached check — does `docker info` return cleanly?"""
    global _DOCKER_AVAILABLE
    if _DOCKER_AVAILABLE is not None:
        return _DOCKER_AVAILABLE
    try:
        r = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, timeout=5,
        )
        _DOCKER_AVAILABLE = r.returncode == 0
    except Exception:
        _DOCKER_AVAILABLE = False
    return _DOCKER_AVAILABLE


# ══════════════════════════════════════════════════════════════════════════
# HARNESS-LEVEL DEP MERGE (2026-04-23 v8.5 Phase 1)
# ══════════════════════════════════════════════════════════════════════════
# Per Opus architectural review: language-agnostic dep management is a
# HARNESS responsibility, not a prompt concern. Prompts drift per language
# and silently lose the LLM's attention; a harness-level merge is uniform
# and greppable. Each LanguageConfig declares:
#   - forbidden_llm_pins: packages the LLM may NOT override (test framework)
#   - always_required_packages: packages we ALWAYS install
#   - requirements_merge_fn: per-language format conversion + strip + append
# The runner calls merge_fn BEFORE writing the requirements file into the
# container workdir. What the LLM emitted + what we stripped is logged so
# the retry feedback can tell the LLM what the harness did.
# ══════════════════════════════════════════════════════════════════════════


# Whitelisted line shapes in pip requirements.txt. Anything matching these
# passes through the merge; anything else is stripped + logged.
#   `pkg`                   → bare name
#   `pkg==X`, `pkg>=X`, etc → constrained
#   `pkg[extra]==X`         → extras
#   `# comment`             → comment
# Explicitly stripped (security + failure surfaces):
#   `-e .`, `-r other.txt`, `--index-url`, `--extra-index-url`,
#   `git+https://...`, `--hash=sha256:...`, `file:...`
_SAFE_PIP_LINE_RE = __import__("re").compile(
    r"^\s*(?:#.*)?$"  # blank / comment
    r"|^\s*[A-Za-z0-9_.][A-Za-z0-9_.\-]*"  # package name
    r"(?:\[[A-Za-z0-9_,\-]+\])?"  # optional [extra]
    r"\s*(?:[=<>!~]=?\s*[A-Za-z0-9_.\-*+]+(?:\s*,\s*[=<>!~]=?\s*[A-Za-z0-9_.\-*+]+)*)?"  # optional version spec
    r"\s*(?:;\s*.+)?"  # optional environment marker
    r"\s*$"
)


def _merge_pip_requirements(
    llm_requirements: str,
    cfg: "LanguageConfig",
) -> tuple[str, list[str]]:
    """Merge LLM-emitted requirements.txt with harness-required packages.

    Returns (merged_text, stripped_entries). `stripped_entries` is a list
    of (line, reason) strings — surfaced in retry-feedback so the LLM knows
    what the harness rejected.

    Rules:
      1. Directive lines (`-e`, `-r`, `--index-url`, `git+`, `--hash`, …) →
         STRIPPED + logged. They're either failure modes (no setup.py),
         security holes (LLM-controlled index URL), or incompatible with
         the all-or-none hash-pin requirement.
      2. Forbidden pins (cfg.forbidden_llm_pins) → STRIPPED + logged.
         These are packages we guarantee via the prebuilt image and must
         NOT let the LLM re-pin (resolver would uninstall-then-reinstall
         and break the binary).
      3. Safe lines → passed through verbatim.
      4. cfg.always_required_packages → APPENDED (dedup on package name).
         Fallback defense if the image's prebake ever drifts.
    """
    import re as _re
    stripped: list[str] = []
    safe_lines: list[str] = []
    pinned_names: set[str] = set()  # lowercase package names already in safe_lines

    for raw in (llm_requirements or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue  # blank — skip silently
        if line.lstrip().startswith("#"):
            continue  # comment — skip silently (no value to retain)
        if not _SAFE_PIP_LINE_RE.match(line):
            stripped.append(f"{line} (unsafe directive — only `pkg==ver` lines allowed)")
            continue
        # Extract package name (before [extra] / version spec)
        pkg_match = _re.match(r"^\s*([A-Za-z0-9_.][A-Za-z0-9_.\-]*)", line)
        if not pkg_match:
            stripped.append(f"{line} (unparseable package name)")
            continue
        pkg = pkg_match.group(1).lower()
        if pkg in (cfg.forbidden_llm_pins or frozenset()):
            stripped.append(f"{line} (forbidden: {pkg} is baked in the runner image)")
            continue
        # v8.6.1 (2026-04-24) VERSION-COMPAT AUTO-PIN (pip flavor):
        # if pkg is in cfg.version_compat_map AND LLM pinned a version
        # too new for the baked Python, rewrite to the safe version.
        # Match pattern: `pkg==X.Y.Z` or `pkg~=X.Y` or `pkg>=X`.
        ver_match = _re.search(r"(==|~=|>=)\s*([0-9][0-9A-Za-z.\-+_]*)", line)
        if ver_match and cfg.version_compat_map:
            _op, _ver = ver_match.group(1), ver_match.group(2)
            downgrade = _apply_version_compat_map(pkg, _ver, cfg.version_compat_map)
            if downgrade is not None:
                stripped.append(
                    f"{pkg}{_op}{_ver} → auto-pinned to {pkg}=={downgrade} "
                    f"(incompatible with baked runner environment)"
                )
                line = f"{pkg}=={downgrade}"
        safe_lines.append(line)
        pinned_names.add(pkg)

    # Append always_required_packages that aren't already pinned by LLM's lines.
    for req in (cfg.always_required_packages or ()):
        req_pkg_match = _re.match(r"^\s*([A-Za-z0-9_.][A-Za-z0-9_.\-]*)", req)
        if not req_pkg_match:
            continue
        req_pkg = req_pkg_match.group(1).lower()
        if req_pkg in pinned_names:
            continue  # LLM already pinned it (wasn't on forbidden list) — leave theirs
        safe_lines.append(req.strip())
        pinned_names.add(req_pkg)

    merged = "\n".join(safe_lines).rstrip() + "\n"
    return merged, stripped


def _merge_package_json(
    llm_requirements: str,
    cfg: "LanguageConfig",
) -> tuple[str, list[str]]:
    """Merge LLM-emitted package.json with harness-required structure.

    v8.5 Phase B HARNESS-CLOSURE INVARIANT. Applies the same contract as
    `_merge_pip_requirements`, adapted for npm's package.json:

    1. Strip any key from `dependencies` / `devDependencies` that's in
       `cfg.forbidden_llm_pins` (jest, ts-jest, @types/jest, ...). These
       live in /runner/node_modules; LLM must not re-pin.
    2. Strip `overrides` / `resolutions` / `peerDependencies` / `optional
       Dependencies` entirely. These give npm's resolver permission to
       mutate the transitive graph; we want LLM's install contained.
    3. Strip any `scripts` — LLM should not be running arbitrary shell.
    4. Force `"type": "commonjs"` (or whatever we standardize on) so
       jest's CJS config in /runner/jest.config.js works.
    5. Return canonicalized JSON + human-readable stripped list.
    """
    import json as _json
    stripped: list[str] = []
    forbidden = cfg.forbidden_llm_pins or frozenset()
    try:
        pkg = _json.loads(llm_requirements) if llm_requirements.strip() else {}
    except _json.JSONDecodeError as e:
        # LLM emitted malformed JSON — return empty package.json, log.
        stripped.append(f"(malformed package.json: {e}; emitting empty object)")
        return "{}\n", stripped

    # 1 + 2 — strip forbidden/unsafe top-level keys
    for unsafe in ("overrides", "resolutions", "peerDependencies",
                   "optionalDependencies", "scripts"):
        if unsafe in pkg:
            stripped.append(f"top-level `{unsafe}` (unsafe — resolver/shell attack surface)")
            del pkg[unsafe]

    # 3 — strip forbidden pins from dependencies + devDependencies
    #     AND apply version_compat_map auto-pin for any incompatible pin
    compat_map = cfg.version_compat_map or {}
    for dep_bucket in ("dependencies", "devDependencies"):
        if dep_bucket in pkg and isinstance(pkg[dep_bucket], dict):
            for name in list(pkg[dep_bucket].keys()):
                if name.lower() in forbidden:
                    ver = pkg[dep_bucket][name]
                    stripped.append(
                        f"{dep_bucket}.{name}=={ver} (forbidden: baked in /runner/node_modules)"
                    )
                    del pkg[dep_bucket][name]
                    continue
                # v8.6.1 (2026-04-24) VERSION-COMPAT AUTO-PIN (npm flavor):
                # Normalize npm version specifier (caret `^1.2.3` / tilde
                # `~1.2.3` / range `>=1.2`) to just the base version, check
                # compat_map, rewrite if needed.
                ver_spec = pkg[dep_bucket][name]
                if isinstance(ver_spec, str) and compat_map:
                    import re as _re_npm
                    ver_match = _re_npm.search(r"([0-9][0-9A-Za-z.\-+_]*)", ver_spec)
                    if ver_match:
                        _ver = ver_match.group(1)
                        downgrade = _apply_version_compat_map(name, _ver, compat_map)
                        if downgrade is not None:
                            stripped.append(
                                f"{dep_bucket}.{name}: {ver_spec} → auto-pinned to {downgrade} "
                                f"(incompatible with baked runner environment)"
                            )
                            pkg[dep_bucket][name] = downgrade

    # 4 — force commonjs (jest runs CJS; ESM tests require different config)
    if pkg.get("type") == "module":
        stripped.append('top-level `"type": "module"` (forced to "commonjs" for jest compat)')
        pkg["type"] = "commonjs"

    return _json.dumps(pkg, indent=2) + "\n", stripped


# ══════════════════════════════════════════════════════════════════════════
# v8.6.1 (2026-04-24) VERSION-COMPAT AUTO-PIN
# ══════════════════════════════════════════════════════════════════════════
# Language-agnostic semver compare + per-language `version_compat_map`
# rewriter. Used by every merge_fn that opts in. See LanguageConfig
# .version_compat_map for the data shape.
# ──────────────────────────────────────────────────────────────────────────

def _semver_tuple(v: str) -> tuple[int, ...]:
    """Parse a loose semver (vX.Y.Z, X.Y.Z, X.Y, X) → comparable tuple.
    Strips leading 'v'. Ignores any `-alpha` / `+build` suffix. Missing
    components default to 0. Non-numeric components collapse to 0.
    """
    import re as _re_sv
    s = (v or "").strip().lstrip("vV")
    s = _re_sv.split(r"[-+]", s, 1)[0]  # drop suffix
    parts = s.split(".") if s else []
    out = []
    for p in parts:
        m = _re_sv.match(r"^(\d+)", p)
        out.append(int(m.group(1)) if m else 0)
    while len(out) < 3:
        out.append(0)
    return tuple(out[:3])


def _apply_version_compat_map(
    pkg: str,
    version: str,
    compat_map: dict[str, tuple[str, str]],
) -> Optional[str]:
    """If `pkg` is in compat_map AND `version >= too_new_threshold`, return
    the safe_downgrade_version. Else return None (caller keeps original).
    """
    if not compat_map or pkg not in compat_map:
        return None
    too_new, safe = compat_map[pkg]
    if _semver_tuple(version) >= _semver_tuple(too_new):
        return safe
    return None


def _merge_go_mod(
    llm_requirements: str,
    cfg: "LanguageConfig",
) -> tuple[str, list[str]]:
    """Merge LLM-emitted go.mod with harness rules.

    Rules (same contract as _merge_pip_requirements / _merge_package_json):
      1. `go X.Y` directive — if the LLM specified a newer Go than the
         baked image supports, DOWNGRADE to the baked Go version. We know
         from the runner image's `golang:1.22-alpine` base; this is hard-
         coded below but driven by cfg.version_compat_map["__go__"] if set.
      2. `require` lines — for each package in cfg.version_compat_map,
         if the LLM pinned >= too_new_threshold, REWRITE to safe version.
         Log each rewrite to `stripped_entries` so retry-feedback shows it.
      3. Forbidden pins (cfg.forbidden_llm_pins) — STRIPPED + logged.
      4. Comments and other directives pass through.

    Returns (merged_go_mod_text, stripped_entries).
    """
    import re as _re_go
    lines = (llm_requirements or "").splitlines()
    out_lines: list[str] = []
    stripped: list[str] = []
    in_require_block = False

    # Baked Go version for the downgrade policy. Derived from the image tag
    # (golang:1.22-alpine → "1.22"). Passed via cfg if available, else
    # read from cfg.image string.
    _baked_go: str = ""
    _img = (cfg.image or "") if cfg is not None else ""
    _m = _re_go.match(r"^golang:(\d+\.\d+)", _img)
    if _m:
        _baked_go = _m.group(1)

    def _rewrite_require_line(line: str) -> str:
        """Parse 'require pkg version' or 'pkg version' (inside block).
        Rewrite to compat version if applicable."""
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("//"):
            return line
        # Remove leading 'require' for single-line form
        body = stripped_line
        prefix = ""
        if body.startswith("require "):
            prefix = "require "
            body = body[len("require "):].strip()
        m = _re_go.match(r"^([a-zA-Z0-9_./\-]+)\s+(v?[0-9][^\s]*)(.*)$", body)
        if not m:
            return line
        pkg, ver, tail = m.group(1), m.group(2), m.group(3)
        # Forbidden pin check
        if pkg.lower() in (cfg.forbidden_llm_pins or frozenset()):
            stripped.append(f"{pkg} {ver} (forbidden: provided by runner image)")
            return ""  # drop line
        # version_compat_map check
        downgrade = _apply_version_compat_map(pkg, ver, cfg.version_compat_map or {})
        if downgrade is not None:
            stripped.append(
                f"{pkg} {ver} → auto-pinned to {downgrade} "
                f"(baked Go {_baked_go or '?'} cannot satisfy {ver}'s min-Go requirement)"
            )
            # Preserve original indentation
            indent = line[: len(line) - len(line.lstrip())]
            return f"{indent}{prefix}{pkg} {downgrade}{tail}"
        return line

    for raw in lines:
        line = raw.rstrip()
        stripped_line = line.strip()

        # `go X.Y` directive — downgrade if above baked
        if stripped_line.startswith("go "):
            m = _re_go.match(r"^go\s+(\d+\.\d+)", stripped_line)
            if m and _baked_go:
                llm_go = m.group(1)
                if _semver_tuple(llm_go) > _semver_tuple(_baked_go):
                    stripped.append(
                        f"go {llm_go} directive → auto-downgraded to go {_baked_go} "
                        f"(baked runner image is go {_baked_go})"
                    )
                    indent = line[: len(line) - len(line.lstrip())]
                    out_lines.append(f"{indent}go {_baked_go}")
                    continue
            out_lines.append(line)
            continue

        # require block start
        if stripped_line == "require (":
            in_require_block = True
            out_lines.append(line)
            continue
        if in_require_block and stripped_line == ")":
            in_require_block = False
            out_lines.append(line)
            continue
        # require (single-line) or inside require block
        if stripped_line.startswith("require ") or in_require_block:
            rewritten = _rewrite_require_line(line)
            if rewritten == "":
                continue  # dropped (forbidden pin)
            out_lines.append(rewritten)
            continue

        # everything else pass through
        out_lines.append(line)

    merged = "\n".join(out_lines).rstrip() + "\n"
    return merged, stripped


def _cmd_for_lang(language: str, has_requirements: bool, has_tests: bool,
                  prebuilt: bool = False) -> list[str]:
    """Return the shell command that runs inside the container."""
    L = language.lower()
    if L in ("python", "py"):
        # v8.5 PHASE B HARNESS-CLOSURE INVARIANT (2026-04-23):
        # pytest + plugins live in /opt/harness-venv (isolated). LLM's
        # `pip install -r requirements.txt` installs to GLOBAL site-packages
        # at /usr/local. Harness invokes `/opt/harness-venv/bin/pytest`
        # directly — NEVER global pytest. Two-env isolation eliminates the
        # class of "LLM deps break the test runner."
        #
        # Per Opus Q1 landmine: pytest auto-discovers plugins from sys.path
        # via entry-points. Harness venv has --system-site-packages, so
        # /usr/local is on sys.path; plugins LLM installed there (pytest-cov,
        # pytest-xdist, etc.) would auto-load. We disable autoload +
        # explicitly -p the plugins we want.
        #
        # Per Opus Q3: defensive re-pin DELETED — suggests the invariant
        # can be violated. Merge (upstream) still runs as supply-chain
        # defense. verify_baked runs as 50ms invariant-assertion.
        steps = []
        pip_args = "pip install -q --disable-pip-version-check"
        if has_requirements:
            steps.append(f"{pip_args} -r /app/requirements.txt 2>&1 | tail -20")
            # Phase A verify: assert HARNESS-CLOSURE INVARIANT holds —
            # harness venv immutable + no shadow pytest in global. Fail
            # fast with DEP_DRIFT: (parsed by retry-feedback rewriter).
            steps.append(
                "if [ -f /opt/verify_baked.py ]; then "
                "python /opt/verify_baked.py || exit $?; fi"
            )
        if has_tests:
            # Invoke HARNESS pytest (isolated from LLM install). Auto-plugin
            # discovery disabled; explicitly load pytest-asyncio since it's
            # the one we rely on for FastAPI async tests.
            # v8.5 Phase B (2026-04-23): -p NAMES are the plugin module
            # paths. For pytest-asyncio (pkg name pytest-asyncio), the
            # plugin module is `pytest_asyncio.plugin` not `pytest_asyncio`
            # — importing the package's __init__ doesn't register the
            # plugin hooks. Same for pytest-mock (module `pytest_mock`
            # does auto-register on import; use that).
            # --asyncio-mode=auto so unmarked `async def test_*` are also
            # treated as asyncio tests (makes it more forgiving of LLM
            # that forgets the @pytest.mark.asyncio decorator).
            steps.append(
                "cd /app && "
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
                "/opt/harness-venv/bin/pytest tests/ -q --tb=short "
                "-p pytest_asyncio.plugin -p pytest_mock "
                "--asyncio-mode=auto "
                "--junitxml=/app/_junit.xml 2>&1 | tail -60; "
                "echo __JUNIT_XML_START__; "
                "[ -f /app/_junit.xml ] && cat /app/_junit.xml || echo '<testsuite/>'; "
                "echo __JUNIT_XML_END__; "
                "echo EXIT_CODE=$?"
            )
        else:
            steps.append("cd /app && python solution.py 2>&1; echo EXIT_CODE=$?")
        return ["sh", "-c", " && ".join(steps)]
    if L in ("javascript", "js", "typescript", "ts"):
        # v8.5 PHASE B HARNESS-CLOSURE INVARIANT (2026-04-23):
        # /runner/node_modules has jest + ts-jest + plugins (isolated). LLM's
        # package.json installs to /app/node_modules. NODE_PATH prepends
        # LLM's modules for test-import resolution, then falls through to
        # /runner for jest internals. Config is pinned to /runner/jest.config.js
        # so LLM's /app/jest.config.js (if any) is NEVER auto-discovered
        # (Opus landmine Q5.1).
        steps = []
        if has_requirements:
            # LLM's package.json → install into /app/node_modules. npm will
            # NOT touch /runner/node_modules because it's outside /app and
            # we don't pass --prefix /runner.
            steps.append("cd /app && npm install --no-audit --no-fund --silent 2>&1 | tail -5")
        # v8.6 (2026-04-24) — ts-jest COMPILE-path resolution shim.
        # Bug reproduced: `import { z } from 'zod'` fails with TS2307 even
        # though zod is baked in /runner/node_modules. Root cause: ts-jest's
        # TypeScript compile phase walks node_modules up from the importing
        # file (/app/solution.test.ts), checking /app/node_modules first.
        # Without this shim, zod et al. are only reachable at runtime (via
        # jest's moduleDirectories) not compile-time.
        # Safety: only symlink BAKED RUNTIME LIBS (zod, express, etc.) —
        # NEVER @types/* (LLM manages its own), NEVER jest/ts-jest (those
        # are SHADOW_FORBIDDEN_LLM and would fail verify_baked's CHECK 2).
        # Runs AFTER `npm install` so LLM's real installs take precedence;
        # symlinks only fill gaps for packages LLM didn't declare.
        steps.append(
            "mkdir -p /app/node_modules && "
            "for name in zod express supertest axios bcrypt jsonwebtoken pg redis rxjs node-fetch; do "
            "  [ -d /runner/node_modules/$name ] && [ ! -e /app/node_modules/$name ] && "
            "    ln -sfn /runner/node_modules/$name /app/node_modules/$name; "
            "done; true"
        )
        if has_requirements:
            # Phase A invariant assertion: verify harness modules immutable
            # + no shadow jest in /app/node_modules. Fail fast on DEP_DRIFT.
            if prebuilt:
                steps.append(
                    "if [ -f /opt/verify_baked.mjs ]; then "
                    "node /opt/verify_baked.mjs || exit $?; fi"
                )
        if has_tests:
            if prebuilt:
                # Use HARNESS jest from /runner/node_modules/.bin. Explicit
                # --config and --rootDir so LLM's /app/jest.config.js is
                # ignored. NODE_PATH lets tests resolve LLM-app deps from
                # /app/node_modules while jest internals resolve from /runner.
                steps.append(
                    "cd /app && "
                    "NODE_PATH=/app/node_modules:/runner/node_modules "
                    "/runner/node_modules/.bin/jest "
                    "--config=/runner/jest.config.js --rootDir=/app "
                    "--ci --json --outputFile=/app/_jest.json 2>&1 | tail -10; "
                    "echo __JEST_JSON_START__; "
                    "[ -f /app/_jest.json ] && cat /app/_jest.json || echo '{}'; "
                    "echo __JEST_JSON_END__; "
                    "echo EXIT_CODE=$?"
                )
            else:
                # Fallback path — no prebuilt image. Install on-demand.
                steps.append(
                    "cd /app && npm install --no-audit --no-fund --silent jest ts-jest typescript 2>&1 | tail -3"
                )
                steps.append(
                    "cd /app && npx jest --ci --silent --json --outputFile=/app/_jest.json 2>&1 | tail -10; "
                    "echo __JEST_JSON_START__; "
                    "[ -f /app/_jest.json ] && cat /app/_jest.json || echo '{}'; "
                    "echo __JEST_JSON_END__; "
                    "echo EXIT_CODE=$?"
                )
        else:
            steps.append("cd /app && node solution.js 2>&1; echo EXIT_CODE=$?")
        return ["sh", "-c", " && ".join(steps)]
    if L in ("go", "golang"):
        steps = []
        # 2026-04-22 v7.1: always run `go mod init` regardless of image.
        # Rationale (bug caught on Go regen attempt 4, user diagnosis):
        # the prebuilt sll-go-runner image bakes /app/go.mod INTO the image,
        # but `docker run -v ${workdir}:/app` uses a bind-mount that
        # OVERLAYS /app with the host's empty workdir — hiding the
        # pre-baked go.mod. Every retry failed with
        # `pattern ./...: directory prefix . does not contain main module`
        # and the LLM's actual Go code was never tested. Not an LLM issue,
        # a bind-mount issue. The prebuilt image's value is still the
        # pre-downloaded module cache (GOMODCACHE), which survives since
        # that's in /runner, not /app. Init is fast (~100ms) — just run it.
        steps.append(
            "cd /app && "
            "[ -f go.mod ] || go mod init skillslab >/dev/null 2>&1 || true"
        )
        if has_requirements:
            steps.append("cd /app && go mod download 2>&1 | tail -5")
        else:
            steps.append("cd /app && go mod tidy >/dev/null 2>&1 || true")
        if has_tests:
            # 2026-04-22 v7: `go test -json` emits NDJSON event stream where
            # each per-test event has {"Action": "run"|"pass"|"fail"|"skip",
            # "Test": "TestFoo", ...}. Sentinel-wrap so the parser can find
            # the event stream cleanly even when interleaved with any
            # additional command output.
            steps.append(
                "echo __GO_JSON_START__; "
                "cd /app && go test ./... -count=1 -json 2>&1; "
                "GO_EXIT=$?; "
                "echo __GO_JSON_END__; "
                "echo EXIT_CODE=$GO_EXIT"
            )
        else:
            steps.append("cd /app && go run solution.go 2>&1; echo EXIT_CODE=$?")
        return ["sh", "-c", " && ".join(steps)]
    if L in ("rust", "rs"):
        # 2026-04-23 v8.2: Rust lang. `cargo init --lib` if no Cargo.toml
        # (learner-submitted workdir is blank). Copy warm target cache from
        # /runner/target-cache → /app/target so the compile is incremental.
        # Then `cargo test`. No sentinel — parser reads human summary.
        steps = []
        steps.append(
            "cd /app && "
            "[ -f Cargo.toml ] || cargo init --name skillslab --lib >/dev/null 2>&1 || true; "
            # copy-not-overwrite so learner Cargo.toml wins if they provided one
            "cp -rn /runner/target-cache /app/target 2>/dev/null || true"
        )
        if has_tests:
            steps.append(
                "cd /app && "
                "cargo test --no-fail-fast -- --test-threads=1 2>&1 | tail -200; "
                "echo EXIT_CODE=$?"
            )
        else:
            steps.append("cd /app && cargo run --release 2>&1 | tail -40; echo EXIT_CODE=$?")
        return ["sh", "-c", " && ".join(steps)]
    # default: run as shell script
    return ["sh", "-c", "cat solution.* 2>/dev/null | head -c 2000; echo EXIT_CODE=0"]


def _materialize_files(workdir: str, files: dict[str, str]) -> None:
    for rel, contents in (files or {}).items():
        rel = str(rel).strip().lstrip("/").lstrip("\\")
        if not rel or ".." in rel.split("/"):
            continue
        target = os.path.normpath(os.path.join(workdir, rel))
        if not target.startswith(os.path.normpath(workdir) + os.sep):
            continue
        os.makedirs(os.path.dirname(target) or workdir, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(str(contents))


def _parse_test_results(output: str, language: str) -> dict[str, Any]:
    """Parse runtime test output into {passed, failed, total, exit_code, all_passed}.

    2026-04-22 v7 refactor (user directive: don't hard-code per-language
    behavior): dispatches through _LANG_CONFIGS. Each config declares a
    sentinel name, a structured parser (JSON/XML), and a regex fallback.
    Adding a new language = one registry entry.

    Flow:
      1. Look up LanguageConfig for this language.
      2. If the config declares a sentinel, try to extract the block and
         run the structured parser. If it returns a valid dict, use it.
      3. Otherwise, fall back to the per-language regex parser.
      4. Return a uniform shape regardless of which path succeeded.
    """
    out = output or ""
    import re
    exit_code = 1
    m = re.search(r"EXIT_CODE=(\d+)", out)
    if m:
        exit_code = int(m.group(1))

    cfg = _get_lang_config(language)
    if cfg is None:
        # Unknown language — no structured parse possible.
        return {
            "exit_code": exit_code,
            "passed": 0,
            "failed": 0,
            "total": 0,
            "all_passed": False,
        }

    def _finalize(d: dict) -> dict[str, Any]:
        passed = int(d.get("passed", 0) or 0)
        failed = int(d.get("failed", 0) or 0)
        total = int(d.get("total", 0) or (passed + failed))
        # v8.5 (2026-04-23 Phase 1): propagate `collected` + `collection_error`
        # from the structured parser so Layer A test-count can reason from the
        # runner's REAL discovered count (handles async def, class-based,
        # @pytest.mark.parametrize expansions). Fall back to total when the
        # parser doesn't supply collected (e.g. regex fallback path).
        collected = int(d.get("collected", 0) or 0) or total
        collection_error = bool(d.get("collection_error", False))
        collection_error_msg = str(d.get("collection_error_msg", "") or "")
        return {
            "exit_code": exit_code,
            "passed": max(0, passed),
            "failed": max(0, failed),
            "total": max(0, total),
            "collected": max(0, collected),
            "collection_error": collection_error,
            "collection_error_msg": collection_error_msg,
            "all_passed": exit_code == 0 and failed == 0 and total > 0,
        }

    # Structured parse
    if cfg.sentinel and cfg.structured_parser:
        block = _extract_sentinel_block(out, cfg.sentinel)
        if block is not None:
            try:
                parsed = cfg.structured_parser(block)
                if parsed is not None:
                    return _finalize(parsed)
            except Exception:
                pass  # fall through to fallback

    # Fallback regex parse
    if cfg.fallback_parser:
        try:
            parsed = cfg.fallback_parser(out)
            if parsed is not None:
                return _finalize(parsed)
        except Exception:
            pass

    # Default (language not in registry or parse failed) — empty result.
    return {
        "exit_code": exit_code,
        "passed": 0,
        "failed": 0,
        "total": 0,
        "all_passed": False,
    }


# ═══════════════════════════════════════════════════════════════════════════
# PER-LANGUAGE PARSERS (referenced by _LANG_CONFIGS below)
# ═══════════════════════════════════════════════════════════════════════════

def _parse_pytest_junit_xml(block: str) -> Optional[dict]:
    """Parse pytest JUnit XML. Block is the content between sentinels.

    v8.5 (2026-04-23 Phase 1 — per buddy-Opus L1): also surface the runner's
    discovered test count (`collected`) so Layer A can reason from the actual
    number of tests pytest found — async def, class-based, @pytest.mark.
    parametrize expansions all counted correctly. Plus `collection_error`
    flag when tests=0 + errors>0 (conftest import failure etc.), so retry
    feedback can say "collection failed" instead of silently "0 tests."
    """
    import xml.etree.ElementTree as ET
    root = ET.fromstring(block)
    # pytest emits either <testsuites><testsuite>...</testsuite></testsuites>
    # or just <testsuite> at the root.
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return None
    tests = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = tests - failures - errors - skipped
    failed = failures + errors  # errors count as fail for grading
    collection_error = (tests == 0 and errors > 0)
    # Surface the error message if collection failed (first <error> node).
    err_msg = ""
    if collection_error:
        err_el = suite.find(".//error") or suite.find("error")
        if err_el is not None:
            err_msg = (err_el.get("message") or err_el.text or "")[:400]
    return {
        "passed": passed, "failed": failed, "total": passed + failed,
        "collected": tests, "collection_error": collection_error,
        "collection_error_msg": err_msg,
    }


def _parse_pytest_regex_fallback(out: str) -> Optional[dict]:
    """Fallback for when JUnit XML is unavailable. Extracts each field
    independently so either ordering ('N failed, M passed' or reverse)
    parses correctly. This is the parser used pre-v6 that silently
    collapsed ordering; now always paired with structured primary."""
    import re as _re
    m_passed = _re.search(r"(\d+)\s+passed", out)
    m_failed = _re.search(r"(\d+)\s+failed", out)
    m_errors = _re.search(r"(\d+)\s+error", out)
    passed = int(m_passed.group(1)) if m_passed else 0
    failed = int(m_failed.group(1)) if m_failed else 0
    errored = int(m_errors.group(1)) if m_errors else 0
    failed += errored
    return {"passed": passed, "failed": failed, "total": passed + failed}


def _parse_jest_json(block: str) -> Optional[dict]:
    """Parse jest --json --outputFile report. numPassedTests / numFailedTests
    / numTotalTests are top-level keys. v8.5: also exposes `collected`."""
    import json as _json
    report = _json.loads(block)
    passed = int(report.get("numPassedTests", 0) or 0)
    failed = int(report.get("numFailedTests", 0) or 0)
    total = int(report.get("numTotalTests", 0) or (passed + failed))
    return {
        "passed": passed, "failed": failed, "total": total,
        "collected": total, "collection_error": (total == 0 and passed + failed == 0),
        "collection_error_msg": "",
    }


def _parse_jest_regex_fallback(out: str) -> Optional[dict]:
    import re as _re
    m_passed = _re.search(r"Tests:[\s\S]*?(\d+)\s+passed", out)
    m_failed = _re.search(r"Tests:[\s\S]*?(\d+)\s+failed", out)
    m_total = _re.search(r"Tests:[\s\S]*?(\d+)\s+total", out)
    passed = int(m_passed.group(1)) if m_passed else 0
    failed = int(m_failed.group(1)) if m_failed else 0
    total = int(m_total.group(1)) if m_total else (passed + failed)
    return {"passed": passed, "failed": failed, "total": total}


def _parse_go_test_ndjson(block: str) -> Optional[dict]:
    """Parse `go test -json` NDJSON events. Count only per-test events
    (Action in pass/fail/skip AND Test is set). Package-level events
    without Test are summaries, not individual results. v8.5: also counts
    `run` events as `collected` (actual tests discovered by the runner)."""
    import json as _json
    passed = failed = run_count = 0
    any_event = False
    for ln in block.splitlines():
        ln = ln.strip()
        if not ln or not ln.startswith("{"):
            continue
        try:
            ev = _json.loads(ln)
        except Exception:
            continue
        if not ev.get("Test"):
            continue
        any_event = True
        action = ev.get("Action")
        if action == "run":
            run_count += 1
        elif action == "pass":
            passed += 1
        elif action == "fail":
            failed += 1
    if not any_event:
        return None
    return {
        "passed": passed, "failed": failed, "total": passed + failed,
        "collected": run_count or (passed + failed),
        "collection_error": False, "collection_error_msg": "",
    }


def _parse_go_summary_fallback(out: str) -> Optional[dict]:
    """Fallback: count per-package `ok ` / `FAIL ` prefixes."""
    passed = failed = 0
    for line in out.splitlines():
        if line.startswith("ok"):
            passed += 1
        elif line.startswith("FAIL"):
            failed += 1
    return {"passed": passed, "failed": failed, "total": passed + failed}


def _parse_cargo_test_text_fallback(out: str) -> Optional[dict]:
    """Parse `cargo test` human-readable summary.

    cargo test prints per-binary summary lines like:
        test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; ...
        test result: FAILED. 3 passed; 2 failed; 0 ignored; 0 measured; ...

    Sum across all lines (each crate + integration binary produces its own
    summary). Extract fields independently so passed-before-failed vs
    failed-before-passed ordering doesn't matter.

    Compile errors ("error[EXXXX]: ...") surface as cargo exit != 0 with
    NO `test result:` line — return 0/0/0 which the caller interprets as
    "didn't run" → all_passed=False.
    """
    import re as _re
    passed_total = failed_total = 0
    found_summary = False
    for line in out.splitlines():
        if "test result:" not in line:
            continue
        found_summary = True
        mp = _re.search(r"(\d+)\s+passed", line)
        mf = _re.search(r"(\d+)\s+failed", line)
        if mp:
            passed_total += int(mp.group(1))
        if mf:
            failed_total += int(mf.group(1))
    if not found_summary:
        return {"passed": 0, "failed": 0, "total": 0}
    return {
        "passed": passed_total,
        "failed": failed_total,
        "total": passed_total + failed_total,
    }


# ══════════════════════════════════════════════════════════════════════════
# RAW PASSTHROUGH RETRY FEEDBACK (2026-04-23 v8.5 Phase E final, Opus 4th)
# ══════════════════════════════════════════════════════════════════════════
# Previous attempt (Fragment + regex parser) was another mediator layer —
# Opus's 4th consult: "your parser is a lossy filter pretending to be an
# enrichment layer. When it fails (as it did on TS v5), it fails silently
# with `0 fragments` and a fallback, so you get LESS information than raw
# passthrough would have given."
#
# The final contract: pass RAW stderr + stdout tail directly to the LLM
# with ONE instruction: "Fix these sites." No parsing, no regex, no
# narrative. The LLM reads tool output fine. The regex was me doing the
# LLM's job.
#
# Phase D shape-extractor survives as a simple "if tool_message contains
# any of `type_grounding_error_codes`, append the `.d.ts` block" — no
# parsing, just a string-contains check.
# ══════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════
# COMPILER-GROUNDED RETRY FEEDBACK (2026-04-23 v8.5 Phase D)
# ══════════════════════════════════════════════════════════════════════════
# When a static-check error matches a narrowing/type class the LLM reliably
# mis-handles (e.g. TS discriminated-union narrowing in hidden_tests), the
# normal retry-feedback is weak: "TS2339: Property 'error' does not exist."
# The LLM iterates 6 times on variants of the same bug because it doesn't
# have the SOLUTION's actual return type as structural ground truth.
#
# Fix: detect narrowing-class errors + invoke a language-specific
# `solution_shape_extractor` that runs the TOOLCHAIN to produce the real
# inferred type (e.g. `tsc --declaration` emits .d.ts). Feed the .d.ts
# back into the retry prompt as grounding. The LLM emits narrowing guards
# reliably when handed the discriminated type — it just doesn't emit them
# from scratch.
#
# Extensible per-language (see CLAUDE.md §COMPILER-GROUNDED RETRY FEEDBACK):
#   Rust:   `cargo check --message-format=json`  → expected bounds
#   Java:   `javac -Xlint:all`                    → typed signature
#   Python: `mypy --reveal-type`                  → type hint
#   Go:     `gopls` LSP type info                 → struct shape
# Wire per language via LanguageConfig.solution_shape_extractor.
# ══════════════════════════════════════════════════════════════════════════


def _extract_ts_solution_shape(solution_code: str, timeout_s: int = 30) -> Optional[str]:
    """Extract TypeScript solution's exported declarations via `tsc --declaration`.

    Runs inside the baked sll-node-runner container (has tsc at
    /runner/node_modules/.bin/tsc). Returns the .d.ts content as a string,
    or None if extraction fails.

    Used by main.py's retry-feedback rewriter to surface the real inferred
    return type for narrowing-class TS errors (TS2339/TS2532/TS18048).
    """
    if not solution_code:
        return None
    import tempfile
    workdir = tempfile.mkdtemp(prefix="sll_ts_shape_")
    try:
        with open(os.path.join(workdir, "solution.ts"), "w", encoding="utf-8") as f:
            f.write(solution_code)
        # Symlink /runner/node_modules into /app so tsc can resolve imported
        # types (zod, express, jest, etc.). Without this, imports fall back
        # to `any` — still informative for discriminated-union shape but less
        # precise. typeRoots pinned to harness + app for @types resolution.
        cmd = (
            "ln -sfn /runner/node_modules /app/node_modules; "
            "/runner/node_modules/.bin/tsc --declaration --emitDeclarationOnly "
            "--skipLibCheck --target ES2020 --module commonjs --esModuleInterop "
            "--strict false --moduleResolution node "
            "--typeRoots /runner/node_modules/@types "
            "--outDir /app /app/solution.ts 2>&1 | tail -5; "
            "[ -f /app/solution.d.ts ] && cat /app/solution.d.ts || echo 'NO_DTS'"
        )
        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{workdir}:/app",
                "-w", "/app",
                "--memory=256m",
                "--cpus=1.0",
                "sll-node-runner:latest",
                "sh", "-c", cmd,
            ],
            capture_output=True, text=True, timeout=timeout_s,
        )
        out = (proc.stdout or "").strip()
        if not out or out == "NO_DTS":
            return None
        # If the .d.ts content is non-trivial, return it. Trim to reasonable
        # length — retry prompt budget is finite.
        if len(out) > 2500:
            out = out[:2500] + "\n// ... (truncated)"
        return out
    except Exception as e:
        log.warning("TS solution-shape extraction failed: %s", e)
        return None
    finally:
        try:
            import shutil
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass


def run_in_docker(
    code: str,
    language: str,
    *,
    tests: str | None = None,
    extra_files: dict[str, str] | None = None,
    requirements: str | None = None,
    timeout_s: int = 60,
    entry_filename: str | None = None,
    _override_cmd: str | None = None,
) -> dict[str, Any]:
    """Run learner code + optional tests inside a Docker container.

    Returns {output, error, execution_time, exit_code, test_results?}.
    Falls back to an error dict if Docker isn't available.

    _override_cmd: internal — when set, replaces the language's default
    test command with a raw shell string. Used by compile-check pre-flights
    (P0-2, 2026-04-22 v7) to run `go build` / `python -m py_compile` /
    `tsc --noEmit` without paying for a full test execution.
    """
    t0 = time.time()
    if not is_docker_available():
        return {
            "output": "",
            "error": "docker not available on this host — falling back to legacy sandbox",
            "execution_time": 0,
            "exit_code": -1,
            "docker_available": False,
        }
    image = _IMAGES.get(language.lower())
    if not image:
        return {
            "output": "",
            "error": f"no docker image configured for language {language!r}",
            "execution_time": 0,
            "exit_code": -1,
        }
    # v8.5 Phase B HARNESS-CLOSURE INVARIANT (2026-04-23):
    # Always prefer prebuilt image when available, REGARDLESS of whether
    # the LLM shipped requirements. Before Phase B we fell back to base
    # `python:3.11-slim` when there were requirements, to "give pip a clean
    # slate" — but that path has NO harness-venv and NO verify_baked, so
    # Phase B isolation + invariant checks don't fire. Post-Phase B the
    # prebuilt image is the SOURCE of the harness invariant; never skip it.
    _use_prebuilt = False
    if language.lower() in _PREBUILT_IMAGES:
        prebuilt = _PREBUILT_IMAGES[language.lower()]
        if _image_exists_locally(prebuilt):
            image = prebuilt
            _use_prebuilt = True

    L = language.lower()
    workdir = tempfile.mkdtemp(prefix="sll_docker_")
    try:
        # Write solution file
        entry = entry_filename or {
            "python": "solution.py", "py": "solution.py",
            "js": "solution.js", "javascript": "solution.js",
            "ts": "solution.ts", "typescript": "solution.ts",
            "go": "solution.go", "golang": "solution.go",
            # Rust: src/lib.rs is the conventional entry for `cargo test` on
            # a --lib crate. We write to src/lib.rs so the auto-generated
            # Cargo.toml (via `cargo init --lib`) finds it.
            "rust": "src/lib.rs", "rs": "src/lib.rs",
        }.get(L, "solution.txt")
        with open(os.path.join(workdir, entry), "w", encoding="utf-8") as f:
            f.write(code or "")

        # Write tests
        has_tests = bool(tests and tests.strip())
        if has_tests:
            test_filename = {
                "python": "test_solution.py", "py": "test_solution.py",
                "js": "solution.test.js", "javascript": "solution.test.js",
                "ts": "solution.test.ts", "typescript": "solution.test.ts",
                "go": "solution_test.go", "golang": "solution_test.go",
            }.get(L, "test.txt")
            if L in ("python", "py"):
                # Python: tests in tests/ with conftest.py + __init__.py so
                # `from solution import x` resolves against the workdir.
                tests_dir = os.path.join(workdir, "tests")
                os.makedirs(tests_dir, exist_ok=True)
                with open(os.path.join(tests_dir, "__init__.py"), "w") as f: f.write("")
                with open(os.path.join(workdir, "conftest.py"), "w") as f:
                    f.write("import sys, os\nsys.path.insert(0, os.path.dirname(__file__))\n")
                with open(os.path.join(tests_dir, test_filename), "w", encoding="utf-8") as f:
                    f.write(tests)
            elif L in ("js", "javascript", "ts", "typescript"):
                # Node/TS: write test ALONGSIDE solution so `require('./solution')`
                # in the test resolves. Jest picks up *.test.{js,ts} in the workdir.
                with open(os.path.join(workdir, test_filename), "w", encoding="utf-8") as f:
                    f.write(tests)
            elif L in ("go", "golang"):
                # 2026-04-22 v7: co-locate Go tests WITH solution.go. Go's
                # internal imports require same-package — tests in `tests/`
                # subdir land in `package tests` and can't see solution.go's
                # symbols (every run failed "FAIL skillslab/tests [build
                # failed]"). Placing solution_test.go alongside solution.go
                # means they're in the same package and `go test` picks up
                # *_test.go automatically.
                with open(os.path.join(workdir, test_filename), "w", encoding="utf-8") as f:
                    f.write(tests)
            elif L in ("rust", "rs"):
                # 2026-04-23 v8.2: Rust tests co-locate with lib in src/.
                # Convention: tests go in tests/ for integration OR inline
                # in src/lib.rs #[cfg(test)] mod. We write the LLM-provided
                # test file as tests/integration_test.rs — cargo picks up
                # everything in tests/ automatically with no extra config.
                tests_dir = os.path.join(workdir, "tests")
                os.makedirs(tests_dir, exist_ok=True)
                with open(os.path.join(tests_dir, "integration_test.rs"), "w", encoding="utf-8") as f:
                    f.write(tests)
            else:
                # Other languages — default to tests/ subdir.
                tests_dir = os.path.join(workdir, "tests")
                os.makedirs(tests_dir, exist_ok=True)
                with open(os.path.join(tests_dir, test_filename), "w", encoding="utf-8") as f:
                    f.write(tests)

        # Write requirements
        has_reqs = bool(requirements and requirements.strip())
        harness_stripped_entries: list[str] = []
        if has_reqs:
            req_filename = {
                "python": "requirements.txt", "py": "requirements.txt",
                "js": "package.json", "javascript": "package.json",
                "ts": "package.json", "typescript": "package.json",
                "go": "go.mod", "golang": "go.mod",
            }.get(L, "requirements.txt")
            # v8.5 Phase 1 HARNESS-LEVEL DEP MERGE (2026-04-23):
            # Apply the per-language merge function (if declared) to strip
            # forbidden pins, whitelist directives, and append always-required
            # packages. Captures stripped entries for retry-feedback logging.
            # Languages without a merge_fn get the LLM's requirements verbatim.
            _cfg_merge = _get_lang_config(language)
            if _cfg_merge is not None and _cfg_merge.requirements_merge_fn is not None:
                merged_text, harness_stripped_entries = _cfg_merge.requirements_merge_fn(
                    requirements, _cfg_merge,
                )
                if harness_stripped_entries:
                    log.info(
                        "dep-merge stripped %d LLM pins: %s",
                        len(harness_stripped_entries),
                        "; ".join(harness_stripped_entries)[:300],
                    )
                requirements_to_write = merged_text
            else:
                requirements_to_write = requirements
            with open(os.path.join(workdir, req_filename), "w", encoding="utf-8") as f:
                f.write(requirements_to_write)
        else:
            # v8.5 Phase 1: even without LLM-emitted requirements, install
            # always_required_packages if declared (so pytest is present when
            # the prebake is somehow broken). Empty-requirements case is
            # handled by generating a minimal requirements.txt.
            _cfg_ar = _get_lang_config(language)
            if _cfg_ar is not None and _cfg_ar.always_required_packages:
                req_filename = {
                    "python": "requirements.txt", "py": "requirements.txt",
                    "js": "package.json", "javascript": "package.json",
                    "ts": "package.json", "typescript": "package.json",
                    "go": "go.mod", "golang": "go.mod",
                }.get(L, "requirements.txt")
                if req_filename == "requirements.txt":
                    # Only auto-materialize for pip-style. JSON/mod require
                    # structured authoring.
                    has_reqs = True
                    with open(os.path.join(workdir, req_filename), "w", encoding="utf-8") as f:
                        f.write("\n".join(_cfg_ar.always_required_packages) + "\n")

        # Extra files
        if extra_files:
            _materialize_files(workdir, extra_files)

        # Build docker run command. If _override_cmd is set (compile-check
        # pre-flight), use it directly instead of the full test command.
        if _override_cmd is not None:
            cmd_inner = ["sh", "-c", _override_cmd + "; echo EXIT_CODE=$?"]
        else:
            cmd_inner = _cmd_for_lang(language, has_reqs, has_tests, prebuilt=_use_prebuilt)
        # Note: --network=bridge (default) so pip install / npm install works.
        # We chose network-over-isolation per the no-mocks directive: real
        # package installs, real library APIs. The grading container is
        # ephemeral (--rm) + resource-capped; risk surface is bounded.
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{workdir}:/app",
            "-w", "/app",
            "--memory=512m",
            "--cpus=1.0",
            image,
        ] + cmd_inner
        log.info("docker_run lang=%s image=%s tests=%s reqs=%s", language, image, has_tests, has_reqs)
        proc = subprocess.run(
            docker_cmd,
            capture_output=True, text=True, timeout=timeout_s,
        )
        elapsed = time.time() - t0
        output = (proc.stdout or "")[-8000:]  # last 8KB
        error = (proc.stderr or "")[-2000:]
        test_results = _parse_test_results(output + "\n" + error, language) if has_tests else None
        return {
            "output": output,
            # v8.5 Phase B hotfix (2026-04-23): always return stderr tail.
            # Previously we zeroed `error` when stdout was non-empty —
            # which masked verify_baked's DEP_DRIFT messages (they print
            # to stderr while pip install's banner is on stdout). The
            # invariant's reason-builder reads both; they're concatenated
            # downstream via `stderr + "\n---STDOUT_TAIL---\n" + stdout`.
            "error": error,
            "execution_time": elapsed,
            "exit_code": proc.returncode,
            "test_results": test_results,
            "docker_available": True,
            # v8.5 Phase 1 HARNESS-LEVEL DEP MANAGEMENT (2026-04-23):
            # Surface what the harness stripped from the LLM's requirements
            # so retry-feedback can tell the LLM "we removed X because it's
            # baked" or "we removed Y because it's a security hole." Silent
            # stripping causes "my pin disappeared" debugging nightmares.
            "harness_stripped_entries": harness_stripped_entries,
        }
    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "error": f"docker run timeout ({timeout_s}s exceeded)",
            "execution_time": time.time() - t0,
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"docker_run error: {type(e).__name__}: {e}",
            "execution_time": time.time() - t0,
            "exit_code": -1,
        }
    finally:
        try: shutil.rmtree(workdir, ignore_errors=True)
        except Exception: pass


def _python_ast_precise_check(starter: str, tests: str) -> Optional[tuple[bool, str]]:
    """Python-specific precise check — parses AST to find each function the
    tests import and examines the body. Used as the LanguageConfig.precise_check
    for python. Returns (is_incomplete, reason) or None to defer to markers.
    """
    import ast
    import re as _re
    src = starter or ""
    # What names do the tests import?
    import_lines = _re.findall(r"from\s+solution\s+import\s+([^\n#]+)", tests or "")
    imported = set()
    for line in import_lines:
        clean = line.split("#")[0].strip()
        for name in clean.split(","):
            name = name.strip().split(" as ")[0].strip()
            if name:
                imported.add(name)
    if not imported:
        return True, "tests don't name imports — let Docker authoritative"
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return True, f"starter doesn't parse — let Docker try ({e})"

    fns_by_name = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            fns_by_name[node.name] = node

    verdicts = []
    for name in imported:
        node = fns_by_name.get(name)
        if node is None:
            verdicts.append((name, "not_found"))
            continue
        if isinstance(node, ast.ClassDef):
            method_verdicts = []
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if sub.name.startswith("_"):
                        continue
                    method_verdicts.append((f"{name}.{sub.name}", _classify_fn_body(sub)))
            if not method_verdicts:
                verdicts.append((name, "empty_class"))
            else:
                if any(v == "looks_complete" for _, v in method_verdicts):
                    complete = [mn for mn, v in method_verdicts if v == "looks_complete"]
                    return False, f"class {name} has complete methods {complete}"
                verdicts.append((name, f"class_ok:{method_verdicts}"))
            continue
        verdicts.append((name, _classify_fn_body(node)))

    complete_fns = [n for n, v in verdicts if v == "looks_complete"]
    if complete_fns:
        return False, f"tested function(s) {complete_fns} appear fully implemented in starter"
    if all(v == "not_found" for _, v in verdicts):
        return True, f"tests import {sorted(imported)} but none found in starter — let Docker decide"
    return True, f"AST pass: all tested functions look broken ({verdicts})"


def _heuristic_starter_is_incomplete(starter: str, language: str, tests: str = "") -> tuple[bool, str]:
    """Heuristic pre-filter before the Docker invariant.

    2026-04-22 v7 refactor (user directive: "don't hard code anything —
    make extensible to all languages"): dispatches through _LANG_CONFIGS.
    Per-language behavior lives in each config's `precise_check` (optional)
    and `incompleteness_markers` (regex list) fields. Adding a new language
    = one registry entry.

    Returns (is_incomplete, reason). When is_incomplete=False, the caller
    rejects the step without burning a Docker roundtrip.
    """
    import re as _re
    cfg = _get_lang_config(language)
    if cfg is None:
        return True, f"no LanguageConfig for {language!r} — let Docker decide"

    # Precise check first (e.g. Python AST). May return None to pass through.
    if cfg.precise_check is not None:
        result = cfg.precise_check(starter or "", tests or "")
        if result is not None:
            return result

    # Regex markers
    for pattern, reason in cfg.incompleteness_markers:
        if _re.search(pattern, starter or "", _re.MULTILINE):
            return True, f"{cfg.ids[0]} starter: {reason}"

    # No marker — defer to Docker or hard-reject per config
    if cfg.defer_on_ambiguous:
        return True, f"{cfg.ids[0]} starter: no marker detected, defer to Docker"
    return False, f"{cfg.ids[0]} starter: no incompleteness marker"


def _classify_fn_body(node) -> str:
    """Return one of: 'empty', 'pass', 'raise', 'single_return', 'looks_complete'.
    Ignores leading docstring expression.
    """
    import ast
    body = list(node.body)
    # Skip docstring
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body:
        return "empty"
    first = body[0]
    if isinstance(first, ast.Pass):
        return "pass"
    if isinstance(first, ast.Raise):
        return "raise"
    # Single-return-sentinel body (body length 1, returns a simple literal or None)
    if isinstance(first, ast.Return) and len(body) == 1:
        # Accept any single-return as a valid broken starter (learner expected to replace)
        return "single_return"
    # Everything else looks complete
    return "looks_complete"


# ═══════════════════════════════════════════════════════════════════════════
# LANGUAGE REGISTRY POPULATION
# ═══════════════════════════════════════════════════════════════════════════
# Adding a language = append one LanguageConfig here. No edits elsewhere.
# All three dispatch functions (_cmd_for_lang, _heuristic_starter_is_incomplete,
# _parse_test_results) read from this list.

_LANG_CONFIGS.extend([
    LanguageConfig(
        ids=("python", "py"),
        image="python:3.11-slim",
        prebuilt_image="sll-python-runner:latest",
        sentinel="JUNIT_XML",
        structured_parser=_parse_pytest_junit_xml,
        fallback_parser=_parse_pytest_regex_fallback,
        incompleteness_markers=(
            (r"raise\s+NotImplementedError", "raise NotImplementedError"),
            (r"^\s*pass\s*$", "pass statement"),
            (r"^\s*\.\.\.\s*$", "ellipsis placeholder"),
        ),
        precise_check=_python_ast_precise_check,
        defer_on_ambiguous=True,
        # Byte-compile without executing — catches syntax errors in ~200ms
        # instead of waiting for pytest collection (~3s).
        compile_check_cmd="cd /app && python -m py_compile solution.py tests/*.py 2>&1",
        # v8.5 Phase 1 HARNESS-LEVEL DEP MANAGEMENT (2026-04-23):
        # After LLM's requirements.txt installs, verify the pinned test
        # framework + key libs survived unchanged. Exits 127 with DEP_DRIFT:
        # lines if any protected package was mutated. See verify_baked_python.py.
        verify_baked_cmd="python /opt/verify_baked.py",
        # v8.5 Phase B HARNESS-CLOSURE INVARIANT (2026-04-23):
        # The harness-venv at /opt/harness-venv is the authoritative test
        # framework — NOT global site-packages. So `forbidden_llm_pins`
        # keeps its job (strip LLM attempts to re-pin the test framework
        # into GLOBAL, which verify_baked.py would catch as shadow-pytest)
        # but `always_required_packages` is EMPTY — the harness venv
        # already has everything; no runtime install needed.
        forbidden_llm_pins=frozenset({
            "pytest", "pytest-asyncio", "pytest-mock", "pytest-json-report",
            "pytest-metadata",
        }),
        # Empty — harness-venv provides the test framework. Don't auto-
        # materialize a pytest install into global (would violate invariant).
        always_required_packages=(),
        requirements_merge_fn=_merge_pip_requirements,
    ),
    LanguageConfig(
        ids=("javascript", "js", "typescript", "ts"),
        image="node:20-slim",
        prebuilt_image="sll-node-runner:latest",
        sentinel="JEST_JSON",
        structured_parser=_parse_jest_json,
        fallback_parser=_parse_jest_regex_fallback,
        incompleteness_markers=(
            (r"throw\s+new\s+Error\s*\(\s*['\"][^'\"]*(?i:not\s*implemented|unimplemented|todo|implement\s*me)", "throw new Error(...)"),
            (r"//\s*TODO", "// TODO"),
            (r"/\*\s*TODO", "/* TODO */"),
        ),
        defer_on_ambiguous=True,
        # `node --check` for JS, `tsc --noEmit` for TS. Check both; first
        # match wins (node --check fails loudly on TS so try tsc first).
        compile_check_cmd=(
            "cd /app && "
            "if ls *.ts 2>/dev/null | head -1 > /dev/null; then "
            "  /runner/node_modules/.bin/tsc --noEmit --target ES2020 --module commonjs "
            "    --esModuleInterop --skipLibCheck *.ts 2>&1 || true; "
            "else "
            "  for f in *.js; do node --check \"$f\" 2>&1 || exit 1; done; "
            "fi"
        ),
        # v8.5 Phase B HARNESS-CLOSURE INVARIANT (2026-04-23):
        # jest + ts-jest + @types/jest live in /runner/node_modules.
        # LLM's package.json installs to /app/node_modules (isolated).
        # verify_baked_js.mjs asserts (1) /runner unchanged, (2) /app has
        # no shadow jest/ts-jest.
        verify_baked_cmd="node /opt/verify_baked.mjs",
        forbidden_llm_pins=frozenset({
            "jest", "ts-jest", "@types/jest", "@types/node",
            "jest-environment-node", "jest-jasmine2",
            "@jest/core", "@jest/reporters", "typescript",
        }),
        always_required_packages=(),  # harness-venv equivalent is /runner/node_modules
        requirements_merge_fn=_merge_package_json,
        # v8.5 Phase D: compiler-grounded retry feedback. TS narrowing errors
        # (TS2339 et al.) get the real .d.ts signature injected into retry
        # feedback as structural grounding.
        type_grounding_error_codes=(
            "TS2339",   # property doesn't exist on narrowed type
            "TS2532",   # object possibly undefined
            "TS18048",  # possibly undefined (similar class)
            "TS2322",   # type not assignable
            "TS2345",   # argument not assignable
        ),
        solution_shape_extractor=_extract_ts_solution_shape,
    ),
    LanguageConfig(
        ids=("go", "golang"),
        image="golang:1.22-alpine",
        prebuilt_image="sll-go-runner:latest",
        sentinel="GO_JSON",
        structured_parser=_parse_go_test_ndjson,
        fallback_parser=_parse_go_summary_fallback,
        incompleteness_markers=(
            (r"panic\(\s*\"(?i:not\s*implemented|unimplemented|todo|implement\s*me|stub)", "panic(\"TODO\")"),
            (r"//\s*TODO", "// TODO"),
            (r"/\*\s*TODO", "/* TODO */"),
        ),
        defer_on_ambiguous=True,
        # v8.6.1 (2026-04-24) GO GO.MOD AUTO-PIN
        # Merge fn rewrites LLM-emitted go.mod entries that require newer
        # Go toolchain than baked. Closes the x/time v0.15+ (needs Go 1.25)
        # hot bug that ate ~5 retries of the Token-Bucket step today.
        requirements_merge_fn=_merge_go_mod,
        version_compat_map={
            # Each entry: {pkg_name: (version_that_requires_newer_Go,
            #                         safe_downgrade_compatible_with_1.22)}
            "golang.org/x/time": ("v0.15.0", "v0.7.0"),
            "golang.org/x/sync": ("v0.11.0", "v0.8.0"),
            "golang.org/x/net":  ("v0.30.0", "v0.25.0"),
            "golang.org/x/text": ("v0.20.0", "v0.14.0"),
            "golang.org/x/crypto": ("v0.30.0", "v0.25.0"),
            "golang.org/x/sys":  ("v0.28.0", "v0.22.0"),
        },
        # Go compile-check:
        #   `go build ./...` alone SKIPS _test.go files — misses test-file
        #   compile errors entirely. `go vet ./...` compiles tests too but
        #   only reports vet-class issues, not compile errors.
        #
        #   v8 fix (2026-04-22): use `go test -run '^$' -count=1 ./...`.
        #   This compiles ALL files including tests but runs ZERO test
        #   functions (`^$` matches nothing). Catches both:
        #     - solution.go:   `"fmt" imported and not used`
        #     - solution_test.go:  `undefined: fmt`
        #   in ~1-3s. Without this, every Go capstone retry was wasting the
        #   full 30s invariant roundtrip on errors we could've caught fast.
        compile_check_cmd=(
            "cd /app && "
            "[ -f go.mod ] || go mod init skillslab >/dev/null 2>&1 || true; "
            "go test -run '^$' -count=1 ./... 2>&1"
        ),
    ),
    # 2026-04-23 v8.2: Rust runtime. `cargo test --format json` needs nightly,
    # so we parse the human-readable summary (`test result: ok. N passed; M failed;...`)
    # with a regex fallback. No sentinel — cargo prints the summary at the end
    # of stdout, regex-extractable.
    LanguageConfig(
        ids=("rust", "rs"),
        image="rust:1.75-alpine",
        prebuilt_image="sll-rust-runner:latest",
        sentinel=None,  # no structured output — cargo-test JSON is nightly-only
        structured_parser=None,
        fallback_parser=_parse_cargo_test_text_fallback,
        incompleteness_markers=(
            (r"todo!\s*\(", "todo!() macro"),
            (r"unimplemented!\s*\(", "unimplemented!() macro"),
            (r"panic!\s*\(\s*['\"](?i:not\s*implemented|unimplemented|todo|stub)", "panic!(\"TODO\")"),
            (r"//\s*TODO", "// TODO"),
        ),
        defer_on_ambiguous=True,
        # cargo check catches all compile errors across src + tests in one
        # pass. Much faster than cargo test. ~3-5s with warm target cache.
        compile_check_cmd=(
            "cd /app && "
            "[ -f Cargo.toml ] || cargo init --name skillslab --lib >/dev/null 2>&1 || true; "
            "cargo check --message-format=short 2>&1"
        ),
    ),
])


def validate_solution_starter_invariant(
    starter_code: str,
    solution_code: str,
    tests: str,
    language: str,
    *,
    requirements: str | None = None,
    timeout_s: int = 90,
) -> dict[str, Any]:
    """LangGraph-style pre-publish validation: solution MUST pass, starter MUST fail.

    2026-04-23 v8.5 (Phase 1 architectural refactor — user + buddy-Opus reviewed):
    The old heuristic pre-filter (`_heuristic_starter_is_incomplete` + AST
    `_python_ast_precise_check` + regex `incompleteness_markers`) rejected
    valid starters whose HELPER functions were fully implemented (see e.g. the
    FastAPI v7 `create_test_task` + `simulate_database_error` helpers, which
    ship complete on purpose for the learner to USE). The heuristic classified
    them as "starter looks complete" and skipped Docker. Three consecutive
    FastAPI gens died to this class of false-positive.

    Ground truth is the Docker invariant below (solution passes tests + starter
    fails tests). The only remaining pre-filter is sha256-equality: if the LLM
    byte-for-byte dumps the solution into the starter slot, skip Docker. Zero
    false positives by construction.

    Returns {
      solution_result, starter_result, ok, reason,
      heuristic_rejected: bool (True if sha256 pre-filter fired).
    }
    """
    import hashlib as _hashlib
    _sol_hash = _hashlib.sha256((solution_code or "").encode("utf-8", "replace")).hexdigest()
    _sta_hash = _hashlib.sha256((starter_code or "").encode("utf-8", "replace")).hexdigest()
    if _sol_hash == _sta_hash and solution_code:
        return {
            "solution_result": None, "starter_result": None,
            "ok": False,
            "heuristic_rejected": True,
            "reason": (
                "starter is byte-identical to solution — the LLM dumped the "
                "solution into the starter slot; the learner would have nothing "
                "to do. Regenerate with a TRULY stubbed starter (body replaced "
                "with `pass` / `raise NotImplementedError(...)` / a TODO comment)."
            ),
        }

    # 2026-04-22 v7 P0-2: cheap compile-check BEFORE full test invariant.
    # A full `go test` / `pytest` / `jest` roundtrip is 15-60s. A bare
    # compile-check (`go build`, `python -m py_compile`, `tsc --noEmit`)
    # is 1-3s. When the LLM emits code with trivial compile errors —
    # unused imports, missing imports, undeclared vars — we catch it in
    # one-twentieth the time and hand the error back to the retry loop.
    cfg = _get_lang_config(language)
    if cfg and cfg.compile_check_cmd:
        sol_compile = run_in_docker(
            solution_code, language, tests=tests,
            requirements=requirements, timeout_s=30,
            _override_cmd=cfg.compile_check_cmd,
        )
        if sol_compile.get("exit_code", 1) != 0:
            err_tail = (sol_compile.get("output") or sol_compile.get("error") or "")[-600:]
            return {
                "solution_result": sol_compile, "starter_result": None,
                "ok": False,
                "heuristic_rejected": False,
                "reason": f"solution failed compile-check: {err_tail}",
            }

    sol = run_in_docker(solution_code, language, tests=tests,
                        requirements=requirements, timeout_s=timeout_s)
    sta = run_in_docker(starter_code, language, tests=tests,
                        requirements=requirements, timeout_s=timeout_s)
    sol_tr = sol.get("test_results") or {}
    sta_tr = sta.get("test_results") or {}
    sol_pass = bool(sol_tr.get("all_passed")) or (sol_tr.get("passed", 0) > 0 and sol_tr.get("failed", 0) == 0)
    sta_pass = bool(sta_tr.get("all_passed")) or (sta_tr.get("passed", 0) > 0 and sta_tr.get("failed", 0) == 0)
    if not sol_pass:
        # v8.5 Phase 1 hotfix (2026-04-23 post-Phase 1 v8 observation):
        # pytest collection errors (ImportError, syntax error in tests) print
        # their traceback to STDERR, not stdout. The original reason pulled
        # only stdout[-500:], which in failed runs often contains ONLY the
        # pip-install "Running pip as root" warning — the actual Python
        # traceback is in stderr. Retries saw useless feedback and looped
        # on the same bug. Now pulls from (stderr tail + stdout tail) so the
        # LLM sees the real failure.
        _stderr_tail = (sol.get("error") or "")[-1500:]
        _stdout_tail = (sol.get("output") or "")[-1500:]
        # Prefer stderr when it has content (tracebacks land there); fall back
        # to stdout (pytest assertion-fail output lands here via junit).
        _combined_tail = (_stderr_tail + "\n---STDOUT_TAIL---\n" + _stdout_tail).strip()
        return {
            "solution_result": sol, "starter_result": sta,
            "ok": False,
            "reason": f"solution did not pass tests. tail={_combined_tail[-2500:]!r}",
        }
    if sta_pass:
        return {
            "solution_result": sol, "starter_result": sta,
            "ok": False,
            "reason": (
                "starter already passes tests — the starter has no stub left "
                "for the learner to fill in. Replace the function-under-test's "
                "body with `raise NotImplementedError('TODO: ...')` or `pass` / "
                "`return None` so the tests fail against the starter."
            ),
        }
    return {
        "solution_result": sol, "starter_result": sta,
        "ok": True, "heuristic_rejected": False,
        "reason": "solution passes, starter fails — invariant satisfied",
    }


# Pre-pull commonly-used images at module import time (best-effort; silent on failure).
def prewarm_images() -> list[str]:
    if not is_docker_available():
        return []
    pulled = []
    for image in set(_IMAGES.values()):
        try:
            subprocess.run(["docker", "pull", image], capture_output=True, timeout=60)
            pulled.append(image)
        except Exception:
            pass
    return pulled
