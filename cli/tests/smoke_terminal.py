"""End-to-end terminal smoke — drive the real `skillslab` binary as a learner would.

Catches the class of bug that unit tests miss: render.py blowing up on a
shape-drift step, status/spec/next/check tripping on real LMS data, exit
codes silently masking tracebacks. Walks every step of every course and
reports per-step pass/fail with the offending file path so we can fix the
whole class of teething issues in one pass.

Usage (from the host or inside the docker container):

    # Test all 3 courses (assumes already logged in, token at ~/.skillslab/token)
    python -m cli.tests.smoke_terminal

    # Test one course
    python -m cli.tests.smoke_terminal --course kimi

    # Test against a remote LMS
    SKILLSLAB_API_URL=https://skills.sclr.ac python -m cli.tests.smoke_terminal

    # Skip the `start` step (re-use already-downloaded course content)
    python -m cli.tests.smoke_terminal --skip-start

The shim runs each command as a subprocess, captures stdout + stderr +
exit code, and looks for `Traceback` / `Error` / `AttributeError` in
output even when exit is 0 — the kind of failure that returns 0 because
Click swallowed the exception in a Rich panel.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_COURSES = ["kimi", "aie", "jspring"]


@dataclass
class StepResult:
    course: str
    label: str
    title: str
    command: str
    rc: int
    stdout: str
    stderr: str
    duration_ms: int

    @property
    def looks_failed(self) -> bool:
        if self.rc != 0:
            return True
        # Match real Python tracebacks only — don't false-positive on demo
        # widgets that say "Error hash: null" or "TypeError" inside JS strings.
        # The unambiguous Python-crash signature is the Traceback header.
        if "Traceback (most recent call last):" in self.stdout:
            return True
        if "Traceback (most recent call last):" in self.stderr:
            return True
        return False

    def first_error_line(self) -> str:
        for stream in (self.stderr, self.stdout):
            tb_idx = stream.find("Traceback (most recent call last):")
            if tb_idx == -1:
                continue
            # Return the LAST line of the traceback (the actual exception)
            tail = stream[tb_idx:].splitlines()
            for line in reversed(tail):
                if line.strip() and not line.startswith(" ") and "Error" in line or "Exception" in line:
                    return line.strip()[:200]
            return tail[-1].strip()[:200] if tail else ""
        return ""


@dataclass
class CourseReport:
    slug: str
    started: bool
    n_steps: int
    failures: list[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.started and not self.failures


def _run(cmd: list[str], cwd: str | None = None, timeout: int = 60) -> tuple[int, str, str, int]:
    """Run a command, capture stdout/stderr/rc/duration_ms."""
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout or "", r.stderr or "", int((time.time() - t0) * 1000)
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", (e.stderr or "") + "\n[skillslab] timed out", int((time.time() - t0) * 1000)


def _skillslab_home() -> Path:
    return Path(os.environ.get("SKILLSLAB_HOME") or (Path.home() / ".skillslab"))


def smoke_course(slug: str, *, skip_start: bool, timeout: int) -> CourseReport:
    report = CourseReport(slug=slug, started=False, n_steps=0)

    # 1. start (or skip if requested)
    if not skip_start:
        print(f"\n=== {slug}: start ===", flush=True)
        rc, out, err, ms = _run(["skillslab", "start", slug], timeout=120)
        if rc != 0:
            print(f"[FAIL] skillslab start {slug} → exit {rc}")
            print(out[-500:])
            print(err[-500:])
            report.failures.append(StepResult(slug, "—", "(start)", f"skillslab start {slug}", rc, out, err, ms))
            return report
        print(f"  ok ({ms}ms)")

    # 2. read meta.json to enumerate steps
    meta_path = _skillslab_home() / slug / "meta.json"
    if not meta_path.exists():
        print(f"[FAIL] {slug}: meta.json missing at {meta_path}")
        return report
    meta = json.loads(meta_path.read_text())
    steps = meta.get("steps", [])
    report.started = True
    report.n_steps = len(steps)
    print(f"  → {len(steps)} steps to walk")

    # 3. for each step: goto + spec + status (the read-only path).
    for s in steps:
        label = f"M{s['module_pos']-1}.S{s['step_pos']}"
        title = s["title"]

        # goto
        rc, out, err, ms = _run(["skillslab", "goto", label, "--course", slug], timeout=timeout)
        sr = StepResult(slug, label, title, f"goto {label}", rc, out, err, ms)
        if sr.looks_failed:
            print(f"  [FAIL] {label} ({title[:50]}) goto: {sr.first_error_line()}")
            report.failures.append(sr)
            continue

        # spec — the most common crash site (HTML→markdown, rubric shapes, etc.)
        rc, out, err, ms = _run(["skillslab", "spec", "--no-pager", "--course", slug], timeout=timeout)
        sr = StepResult(slug, label, title, "spec", rc, out, err, ms)
        if sr.looks_failed:
            print(f"  [FAIL] {label} ({title[:50]}) spec: {sr.first_error_line()}")
            report.failures.append(sr)
            continue

        # status — sanity check the cursor logic
        rc, out, err, ms = _run(["skillslab", "status", "--course", slug], timeout=timeout)
        sr = StepResult(slug, label, title, "status", rc, out, err, ms)
        if sr.looks_failed:
            print(f"  [FAIL] {label} ({title[:50]}) status: {sr.first_error_line()}")
            report.failures.append(sr)
            continue

        print(f"  ok  {label} {title[:60]}")

    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--course", action="append", help="course slug (kimi/aie/jspring); repeat to test multiple")
    ap.add_argument("--skip-start", action="store_true", help="reuse already-downloaded course content")
    ap.add_argument("--timeout", type=int, default=60, help="per-command timeout in seconds")
    ns = ap.parse_args()

    courses = ns.course or DEFAULT_COURSES
    print(f"Smoking courses: {courses}")
    print(f"  SKILLSLAB_API_URL = {os.environ.get('SKILLSLAB_API_URL', 'http://localhost:8001 (default)')}")
    print(f"  SKILLSLAB_HOME    = {_skillslab_home()}")
    if not (_skillslab_home() / "token").exists():
        print("\n[error] not signed in. Run `skillslab login` first.")
        sys.exit(2)

    reports = [smoke_course(c, skip_start=ns.skip_start, timeout=ns.timeout) for c in courses]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in reports:
        n_fail = len(r.failures)
        status = "✓ PASS" if r.passed else f"✗ FAIL ({n_fail}/{r.n_steps})"
        print(f"  {r.slug:<10} {r.n_steps:>4} steps   {status}")
    print()
    any_failed = any(not r.passed for r in reports)
    if any_failed:
        print("FAILURES:")
        for r in reports:
            for sr in r.failures:
                print(f"  [{r.slug}] {sr.label} ({sr.title[:60]})")
                print(f"      cmd: {sr.command}")
                print(f"      err: {sr.first_error_line()}")
        sys.exit(1)
    print("All courses smoke-clean. ✨")


if __name__ == "__main__":
    main()
