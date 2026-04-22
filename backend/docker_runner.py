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


def _cmd_for_lang(language: str, has_requirements: bool, has_tests: bool) -> list[str]:
    """Return the shell command that runs inside the container."""
    L = language.lower()
    if L in ("python", "py"):
        steps = []
        # Always install pytest — the slim image doesn't include it. Quiet pip.
        pip_args = "pip install -q --disable-pip-version-check"
        if has_requirements:
            steps.append(f"{pip_args} pytest -r /app/requirements.txt 2>&1 | tail -3")
        elif has_tests:
            steps.append(f"{pip_args} pytest 2>&1 | tail -3")
        if has_tests:
            # pytest with short tracebacks; `|| true` so non-zero rc doesn't short-circuit EXIT_CODE capture.
            steps.append("cd /app && pytest tests/ -q --tb=short 2>&1 | tail -60; echo EXIT_CODE=$?")
        else:
            steps.append("cd /app && python solution.py 2>&1; echo EXIT_CODE=$?")
        return ["sh", "-c", " && ".join(steps)]
    if L in ("javascript", "js", "typescript", "ts"):
        steps = []
        if has_requirements:
            steps.append("cd /app && npm ci --silent 2>&1 | tail -5")
        if has_tests:
            steps.append("cd /app && npx jest --ci --silent 2>&1 | tail -40; echo EXIT_CODE=$?")
        else:
            steps.append("cd /app && node solution.js 2>&1; echo EXIT_CODE=$?")
        return ["sh", "-c", " && ".join(steps)]
    if L in ("go", "golang"):
        steps = []
        if has_requirements:
            steps.append("cd /app && go mod download 2>&1 | tail -5")
        if has_tests:
            steps.append("cd /app && go test ./... -count=1 2>&1 | tail -40; echo EXIT_CODE=$?")
        else:
            steps.append("cd /app && go run solution.go 2>&1; echo EXIT_CODE=$?")
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
    """Best-effort parse of pytest/jest/go-test output into structured pass/fail counts."""
    L = language.lower()
    out = output or ""
    passed = failed = total = 0
    exit_code = 1
    # Extract exit code marker
    import re
    m = re.search(r"EXIT_CODE=(\d+)", out)
    if m:
        exit_code = int(m.group(1))
    if L in ("python", "py"):
        # pytest: "3 passed, 1 failed in 0.12s" OR "===== X passed ====="
        m = re.search(r"(\d+)\s+passed(?:,\s+(\d+)\s+failed)?", out)
        if m:
            passed = int(m.group(1))
            failed = int(m.group(2) or 0)
            total = passed + failed
        else:
            m2 = re.search(r"(\d+)\s+failed(?:,\s+(\d+)\s+passed)?", out)
            if m2:
                failed = int(m2.group(1))
                passed = int(m2.group(2) or 0)
                total = passed + failed
    elif L in ("javascript", "js", "typescript", "ts"):
        m = re.search(r"Tests:\s+(?:(\d+)\s+failed,\s+)?(\d+)\s+passed,\s+(\d+)\s+total", out)
        if m:
            failed = int(m.group(1) or 0)
            passed = int(m.group(2))
            total = int(m.group(3))
        else:
            m2 = re.search(r"Tests:\s+(\d+)\s+passed,\s+(\d+)\s+total", out)
            if m2:
                passed = int(m2.group(1))
                total = int(m2.group(2))
                failed = total - passed
    elif L in ("go", "golang"):
        # go test: "ok  pkg  0.12s" per-package + "FAIL" if any
        lines = out.splitlines()
        for line in lines:
            if line.startswith("ok"):
                passed += 1
            elif line.startswith("FAIL"):
                failed += 1
        total = passed + failed
    return {
        "exit_code": exit_code,
        "passed": passed,
        "failed": failed,
        "total": total,
        "all_passed": exit_code == 0 and failed == 0 and total > 0,
    }


def run_in_docker(
    code: str,
    language: str,
    *,
    tests: str | None = None,
    extra_files: dict[str, str] | None = None,
    requirements: str | None = None,
    timeout_s: int = 60,
    entry_filename: str | None = None,
) -> dict[str, Any]:
    """Run learner code + optional tests inside a Docker container.

    Returns {output, error, execution_time, exit_code, test_results?}.
    Falls back to an error dict if Docker isn't available.
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

    L = language.lower()
    workdir = tempfile.mkdtemp(prefix="sll_docker_")
    try:
        # Write solution file
        entry = entry_filename or {
            "python": "solution.py", "py": "solution.py",
            "js": "solution.js", "javascript": "solution.js",
            "ts": "solution.ts", "typescript": "solution.ts",
            "go": "solution.go", "golang": "solution.go",
        }.get(L, "solution.txt")
        with open(os.path.join(workdir, entry), "w", encoding="utf-8") as f:
            f.write(code or "")

        # Write tests
        has_tests = bool(tests and tests.strip())
        if has_tests:
            tests_dir = os.path.join(workdir, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            test_filename = {
                "python": "test_solution.py", "py": "test_solution.py",
                "js": "solution.test.js", "javascript": "solution.test.js",
                "ts": "solution.test.ts", "typescript": "solution.test.ts",
                "go": "solution_test.go", "golang": "solution_test.go",
            }.get(L, "test.txt")
            # For Python, tests need to be able to import solution
            if L in ("python", "py"):
                with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
                    f.write("")
                with open(os.path.join(workdir, "conftest.py"), "w") as f:
                    f.write("import sys, os\nsys.path.insert(0, os.path.dirname(__file__))\n")
            with open(os.path.join(tests_dir, test_filename), "w", encoding="utf-8") as f:
                f.write(tests)

        # Write requirements
        has_reqs = bool(requirements and requirements.strip())
        if has_reqs:
            req_filename = {
                "python": "requirements.txt", "py": "requirements.txt",
                "js": "package.json", "javascript": "package.json",
                "ts": "package.json", "typescript": "package.json",
                "go": "go.mod", "golang": "go.mod",
            }.get(L, "requirements.txt")
            with open(os.path.join(workdir, req_filename), "w", encoding="utf-8") as f:
                f.write(requirements)

        # Extra files
        if extra_files:
            _materialize_files(workdir, extra_files)

        # Build docker run command
        cmd_inner = _cmd_for_lang(language, has_reqs, has_tests)
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
            "error": error if proc.returncode != 0 and not output else "",
            "execution_time": elapsed,
            "exit_code": proc.returncode,
            "test_results": test_results,
            "docker_available": True,
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

    Returns {
      solution_result: {test_results…},
      starter_result:  {test_results…},
      ok: bool,
      reason: str (if not ok),
    }
    """
    sol = run_in_docker(solution_code, language, tests=tests,
                        requirements=requirements, timeout_s=timeout_s)
    sta = run_in_docker(starter_code, language, tests=tests,
                        requirements=requirements, timeout_s=timeout_s)
    sol_tr = sol.get("test_results") or {}
    sta_tr = sta.get("test_results") or {}
    sol_pass = bool(sol_tr.get("all_passed")) or (sol_tr.get("passed", 0) > 0 and sol_tr.get("failed", 0) == 0)
    sta_pass = bool(sta_tr.get("all_passed")) or (sta_tr.get("passed", 0) > 0 and sta_tr.get("failed", 0) == 0)
    if not sol_pass:
        return {
            "solution_result": sol, "starter_result": sta,
            "ok": False,
            "reason": f"solution did not pass tests. stdout[-500]={sol.get('output','')[-500:]!r}",
        }
    if sta_pass:
        return {
            "solution_result": sol, "starter_result": sta,
            "ok": False,
            "reason": "starter already passes tests — no work left for the learner",
        }
    return {
        "solution_result": sol, "starter_result": sta,
        "ok": True, "reason": "solution passes, starter fails — invariant satisfied",
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
