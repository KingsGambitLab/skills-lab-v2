"""Parse per-language Dockerfiles to extract baked library versions.

This is the source-of-truth for what's installed in each runner image.
Called once at import time; results cached for the process lifetime.

Why this exists:
Before 2026-04-24 v8.6.1, `_runtime_deps_brief(language)` in main.py was
hand-written — if someone bumped a pin in the Dockerfile, the brief didn't
update, and the LLM's prompt told it the old version was available. That
produced silent class-of-bug where the LLM imported a version that
doesn't match what's baked, and the Docker run failed mysteriously.

Solution: parse Dockerfiles at import time. `_runtime_deps_brief` splices
in the parsed versions instead of hard-coding them.

Parsers are deliberately simple regex — we own the Dockerfile format, so
we can shape it to parse cleanly. If the Dockerfile format ever changes
in a way a regex can't handle, we fix the regex (not add a smarter parser).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

_DOCKERFILES_DIR = Path(__file__).resolve().parent / "docker_images"


def _read(name: str) -> str:
    p = _DOCKERFILES_DIR / name
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _parse_python_pins(dockerfile: str) -> dict[str, str]:
    """Extract `pkg==version` pins from all `RUN pip install ...` blocks.
    Handles multiline continuations (backslash-newline).
    """
    out: dict[str, str] = {}
    # Join continuations first so pkg==ver tokens aren't split
    joined = re.sub(r"\\\n\s*", " ", dockerfile)
    for m in re.finditer(
        r"RUN\s+(?:[^&|\n]*&&\s*)?pip\s+install[^\n]*",
        joined,
    ):
        text = m.group(0)
        for pm in re.finditer(r"([A-Za-z0-9_.][A-Za-z0-9_.\-]*)==([0-9][0-9A-Za-z.\-+_]*)", text):
            pkg = pm.group(1).lower()
            # pip normalizes pkg names: - _ . treated as same; lowercase
            out.setdefault(pkg, pm.group(2))
    return out


def _parse_node_pins(dockerfile: str) -> dict[str, str]:
    """Extract `pkg@version` pins from `RUN npm install ...` blocks."""
    out: dict[str, str] = {}
    joined = re.sub(r"\\\n\s*", " ", dockerfile)
    for m in re.finditer(
        r"RUN\s+(?:[^&|\n]*&&\s*)*npm\s+install[^\n]*",
        joined,
    ):
        text = m.group(0)
        for pm in re.finditer(
            r"(@?[A-Za-z0-9_./\-]+)@(\d[0-9A-Za-z.\-+_]*)",
            text,
        ):
            name = pm.group(1)
            # skip scoped pkg prefix matched as `@name`
            if name.startswith("@") and "/" not in name:
                continue
            out.setdefault(name, pm.group(2))
    return out


def _parse_go_base(dockerfile: str) -> Optional[str]:
    """Extract baked Go version from `FROM golang:X.Y-alpine`."""
    m = re.search(r"^FROM\s+golang:(\d+\.\d+(?:\.\d+)?)", dockerfile, re.MULTILINE)
    return m.group(1) if m else None


def _parse_rust_base(dockerfile: str) -> Optional[str]:
    """Extract baked Rust version from `FROM rust:X.Y-alpine`."""
    m = re.search(r"^FROM\s+rust:(\d+\.\d+(?:\.\d+)?)", dockerfile, re.MULTILINE)
    return m.group(1) if m else None


def _parse_python_base(dockerfile: str) -> Optional[str]:
    """Extract baked Python version from `FROM python:X.Y[-tag]`."""
    m = re.search(r"^FROM\s+python:(\d+\.\d+(?:\.\d+)?)", dockerfile, re.MULTILINE)
    return m.group(1) if m else None


def _parse_node_base(dockerfile: str) -> Optional[str]:
    """Extract baked Node version from `FROM node:X[-tag]`."""
    m = re.search(r"^FROM\s+node:(\d+(?:\.\d+)?(?:\.\d+)?)", dockerfile, re.MULTILINE)
    return m.group(1) if m else None


# ─── Parse each Dockerfile at import time ─────────────────────────────

_py_df = _read("sll-python-runner.Dockerfile")
_node_df = _read("sll-node-runner.Dockerfile")
_go_df = _read("sll-go-runner.Dockerfile")
_rust_df = _read("sll-rust-runner.Dockerfile")

PYTHON_LIBS: dict[str, str] = _parse_python_pins(_py_df)
PYTHON_BASE: Optional[str] = _parse_python_base(_py_df)

NODE_LIBS: dict[str, str] = _parse_node_pins(_node_df)
NODE_BASE: Optional[str] = _parse_node_base(_node_df)

GO_BASE: Optional[str] = _parse_go_base(_go_df)
# Go Dockerfile doesn't pre-install application libs (stdlib-only preference)
GO_LIBS: dict[str, str] = {}

RUST_BASE: Optional[str] = _parse_rust_base(_rust_df)
RUST_LIBS: dict[str, str] = {}  # TODO: parse Cargo.toml prewarm file


def get_pinned_libs(language: str) -> dict[str, str]:
    """Return `{pkg: version}` for the baked libs of a given language.
    Language-agnostic interface — callers don't need to know which parser
    runs. Returns an empty dict for unknown languages.
    """
    lo = (language or "").lower()
    if lo in ("python", "py"):
        return dict(PYTHON_LIBS)
    if lo in ("typescript", "ts", "javascript", "js"):
        return dict(NODE_LIBS)
    if lo in ("go", "golang"):
        return dict(GO_LIBS)
    if lo in ("rust", "rs"):
        return dict(RUST_LIBS)
    return {}


def get_base_version(language: str) -> Optional[str]:
    """Return the baked base-language version (e.g. Python 3.11, Go 1.22)."""
    lo = (language or "").lower()
    if lo in ("python", "py"):
        return PYTHON_BASE
    if lo in ("typescript", "ts", "javascript", "js"):
        return NODE_BASE
    if lo in ("go", "golang"):
        return GO_BASE
    if lo in ("rust", "rs"):
        return RUST_BASE
    return None


def format_libs_block(language: str, max_line_width: int = 72) -> str:
    """Format the pinned libs as a human-readable prompt fragment.
    Used by `_runtime_deps_brief` to splice in auto-generated version
    info. Returns an empty string for languages with no baked libs.
    """
    libs = get_pinned_libs(language)
    if not libs:
        return ""
    # Sort by name for stable output
    items = [f"{k}={v}" for k, v in sorted(libs.items())]
    lines: list[str] = []
    current = "  - Baked libs (pre-installed — DO NOT re-pin in requirements): "
    for it in items:
        if len(current) + len(it) + 2 > max_line_width:
            lines.append(current.rstrip(", "))
            current = "    " + it + ", "
        else:
            current += it + ", "
    if current.strip():
        lines.append(current.rstrip(", "))
    return "\n".join(lines)


# Debug helper — convenient for smoke tests / REPL
if __name__ == "__main__":
    for lang in ("python", "typescript", "go", "rust"):
        base = get_base_version(lang)
        libs = get_pinned_libs(lang)
        print(f"{lang}: base={base}, {len(libs)} libs baked")
        for k, v in sorted(libs.items()):
            print(f"  {k:30s}  {v}")
