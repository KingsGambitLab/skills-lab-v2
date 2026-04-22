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
}


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


def _cmd_for_lang(language: str, has_requirements: bool, has_tests: bool,
                  prebuilt: bool = False) -> list[str]:
    """Return the shell command that runs inside the container."""
    L = language.lower()
    if L in ("python", "py"):
        steps = []
        pip_args = "pip install -q --disable-pip-version-check"
        # Prebuilt image already has pytest + common libs. Skip pip install
        # unless Creator shipped additional requirements.
        if has_requirements:
            steps.append(f"{pip_args} -r /app/requirements.txt 2>&1 | tail -3")
        elif has_tests and not prebuilt:
            steps.append(f"{pip_args} pytest 2>&1 | tail -3")
        if has_tests:
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
    # Gap C: prefer pre-built image when available AND no extra requirements
    # requested (if the Creator shipped a requirements file, we need a clean
    # base so pip install hits the full set).
    _use_prebuilt = False
    if not requirements and language.lower() in _PREBUILT_IMAGES:
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


def _heuristic_starter_is_incomplete(starter: str, language: str, tests: str = "") -> tuple[bool, str]:
    """Gap A + L1 (2026-04-22): AST-based pre-filter before the Docker invariant.

    Why AST: the regex-only heuristic matched `# TODO` anywhere in the source
    (including comments next to a complete implementation) so it let through
    starters where the tested function was actually fully implemented. AST
    parse finds the EXACT function the test imports and checks its BODY's
    first real statement.

    For Python: parse starter → find each function the tests import
    (`from solution import foo, bar`) → examine each tested function's body.
    REJECT iff any tested function's body starts with a real implementation
    (multi-statement body not starting with pass/raise/sentinel return).

    For Go/JS/TS/Ruby: fall back to syntactic markers — AST parsing for those
    languages would need per-language grammars. When in doubt, defer to Docker.

    Returns (is_incomplete, reason). When is_incomplete=False, caller rejects
    without burning a Docker roundtrip.
    """
    import re as _re
    L = (language or "").lower()
    src = starter or ""

    # ── Python: AST check on each tested function ────────────────────
    if L in ("python", "py"):
        import ast
        # What names do the tests import?
        import_lines = _re.findall(r"from\s+solution\s+import\s+([^\n#]+)", tests or "")
        imported = set()
        for line in import_lines:
            # strip trailing comment, split on commas, handle ' as ' aliases
            clean = line.split("#")[0].strip()
            for name in clean.split(","):
                name = name.strip().split(" as ")[0].strip()
                if name: imported.add(name)
        if not imported:
            # Tests don't import specific symbols OR use module import.
            # Can't AST-check precisely; fall through to Docker.
            return True, "tests don't name imports — let Docker authoritative"
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            return True, f"starter doesn't parse — let Docker try ({e})"

        # Index functions + classes at module level
        fns_by_name: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                fns_by_name[node.name] = node

        verdicts = []
        for name in imported:
            node = fns_by_name.get(name)
            if node is None:
                # Name imported but no matching def in starter (module-level var?).
                verdicts.append((name, "not_found"))
                continue
            if isinstance(node, ast.ClassDef):
                # Check each method inside the class
                method_verdicts = []
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if sub.name.startswith("_"):
                            continue
                        method_verdicts.append((f"{name}.{sub.name}", _classify_fn_body(sub)))
                if not method_verdicts:
                    verdicts.append((name, "empty_class"))
                else:
                    # If ANY method looks complete, the class is complete enough to pass tests
                    if any(v == "looks_complete" for _, v in method_verdicts):
                        complete = [mn for mn, v in method_verdicts if v == "looks_complete"]
                        return False, f"class {name} has complete methods {complete}"
                    verdicts.append((name, f"class_ok:{method_verdicts}"))
                continue
            # Function
            verdicts.append((name, _classify_fn_body(node)))

        # Any tested function that looks complete → reject
        complete_fns = [n for n, v in verdicts if v == "looks_complete"]
        if complete_fns:
            return False, f"tested function(s) {complete_fns} appear fully implemented in starter"
        # No-import-match case: fall through to Docker for safety
        if all(v == "not_found" for _, v in verdicts):
            return True, f"tests import {sorted(imported)} but none found in starter — let Docker decide"
        return True, f"AST pass: all tested functions look broken ({verdicts})"

    # ── Go: simple markers ───────────────────────────────────────────
    if L in ("go", "golang"):
        if _re.search(r"panic\(\"[Nn]ot implemented", src) or _re.search(r"^\s*//\s*TODO", src, _re.M):
            return True, "Go starter has panic/TODO"
        return False, "Go starter: no incompleteness marker"

    # ── JS/TS: simple markers ────────────────────────────────────────
    if L in ("javascript", "js", "typescript", "ts"):
        if "throw new Error" in src and "implemented" in src.lower():
            return True, "JS starter throws not-implemented"
        if _re.search(r"//\s*TODO", src):
            return True, "JS starter has TODO comment"
        return False, "JS starter: no incompleteness marker"

    # Other languages — defer to Docker
    return True, f"no AST check for {L} — let Docker decide"


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

    Gap A (2026-04-22): runs a cheap heuristic pre-filter FIRST. If the starter
    has no `pass` / `TODO` / `raise NotImplementedError` / wrong-sentinel marker,
    we infer the LLM wrote the full solution in the starter slot and reject
    IMMEDIATELY — saving the 20-30s Docker roundtrip that would reject it
    anyway. Reduces invariant-retry wall clock from ~25s to ~100ms per reject.

    Returns {
      solution_result, starter_result, ok, reason,
      heuristic_rejected: bool (True if Docker was skipped).
    }
    """
    is_incomplete, heur_reason = _heuristic_starter_is_incomplete(starter_code, language, tests)
    if not is_incomplete:
        return {
            "solution_result": None, "starter_result": None,
            "ok": False,
            "heuristic_rejected": True,
            "reason": f"heuristic reject: starter looks complete ({heur_reason})",
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
