#!/usr/bin/env python3
"""Enforce the HARNESS-CLOSURE INVARIANT (v8.5 Phase B, 2026-04-23).

The invariant: the harness's test-runner (pytest + plugins) lives in
/opt/harness-venv and MUST be byte-identical across all task runs. LLM-
emitted `requirements.txt` installs to the GLOBAL site-packages; a
correctly-isolated setup means no LLM pip install can touch the harness
venv.

This script asserts the invariant AT GRADE TIME, in two ways:

1. HARNESS-VENV IMMUTABLE — every package in /opt/harness-venv-snapshot.txt
   (captured at image-build time) MUST match its current pip-freeze in the
   harness venv. Any drift = broken isolation, fail fast.

2. NO SHADOW PYTEST — the global site-packages must NOT have pytest or
   pytest-asyncio installed. If it does, the LLM's requirements re-pinned
   pytest INTO THE GLOBAL LAYER, which means tests in /app that
   `import pytest` would get the GLOBAL (LLM-controlled) pytest, while
   /opt/harness-venv/bin/pytest gets the harness version. Double-instance
   hazard — see buddy-Opus landmine Q6.

Exit codes:
  0   — invariant holds → proceed to tests
  127 — invariant violated → surface as DEP_DRIFT: for retry feedback

The retry-feedback rewriter in backend/main.py greps for DEP_DRIFT: to
rewrite the LLM's retry prompt. Any new protected check here should emit
DEP_DRIFT: on failure.
"""
from __future__ import annotations

import os
import subprocess
import sys

HARNESS_VENV_PIP = "/opt/harness-venv/bin/pip"
HARNESS_SNAPSHOT = "/opt/harness-venv-snapshot.txt"

# Shadow-pytest check: these packages MUST NOT appear in GLOBAL site-packages.
# If they do, LLM's requirements.txt installed a competing pytest — we
# refuse to run. Fix: LLM must drop the pytest pin (the image's harness
# venv already has it).
SHADOW_FORBIDDEN_GLOBAL: frozenset[str] = frozenset({
    "pytest",
    "pytest-asyncio",
    "pytest-mock",
    "pytest-json-report",
})


def _pip_freeze(pip_bin: str) -> dict[str, str]:
    """Return lowercase package name → installed version via `<pip_bin> freeze`."""
    out = subprocess.run(
        [pip_bin, "freeze", "--disable-pip-version-check"],
        capture_output=True, text=True, check=False,
    ).stdout
    mp: dict[str, str] = {}
    for ln in out.splitlines():
        ln = ln.strip()
        if "==" not in ln or ln.startswith("#"):
            continue
        name, _, ver = ln.partition("==")
        mp[name.strip().lower()] = ver.strip()
    return mp


def _read_snapshot(path: str) -> dict[str, str]:
    mp: dict[str, str] = {}
    if not os.path.exists(path):
        return mp
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip().lower()
            if "==" not in ln or ln.startswith("#"):
                continue
            name, _, ver = ln.partition("==")
            mp[name.strip()] = ver.strip()
    return mp


def main() -> int:
    drifts: list[str] = []

    # CHECK 1 — harness venv is immutable
    baked = _read_snapshot(HARNESS_SNAPSHOT)
    if baked:
        current = _pip_freeze(HARNESS_VENV_PIP)
        for pkg, baked_v in baked.items():
            got = current.get(pkg)
            if got != baked_v:
                drifts.append(
                    f"DEP_DRIFT: harness-venv {pkg} baked={baked_v} "
                    f"post-install={got or 'MISSING'}"
                )
    # CHECK 2 — no shadow pytest in global site-packages
    global_freeze = _pip_freeze("pip")
    for pkg in SHADOW_FORBIDDEN_GLOBAL:
        got = global_freeze.get(pkg.lower())
        if got is not None:
            drifts.append(
                f"DEP_DRIFT: shadow {pkg}=={got} found in GLOBAL site-packages "
                f"(conflicts with /opt/harness-venv/bin/pytest). "
                f"LLM's validation.requirements must NOT pin {pkg}."
            )

    if not drifts:
        return 0

    for d in drifts:
        print(d, file=sys.stderr)
    print(
        "\nHARNESS-CLOSURE INVARIANT VIOLATED. Either the image's bake "
        "is broken (rebuild sll-python-runner) OR the LLM's "
        "validation.requirements installed a package that conflicts with "
        "the harness's test-runner venv. FIX: drop any pin for pytest / "
        "pytest-asyncio / pytest-mock / pytest-json-report from "
        "validation.requirements — the image ships them in an isolated "
        "venv that your tests invoke via /opt/harness-venv/bin/pytest.",
        file=sys.stderr,
    )
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
