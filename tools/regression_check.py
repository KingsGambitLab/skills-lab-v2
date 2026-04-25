"""regression_check.py — production-ready CI gate for content drift + CLI smoke.

Per user directive 2026-04-25: "whatever you do, don't make it a one-time
fix, but it should compound over time + extensible for other tech."

This tool runs on every Creator-prompt change, every facts-block change,
every per-step regen, AND every CI build. It walks every course in the LMS
and scans for verified-facts drift via the registry in
`backend/verified_facts.py`. Exits 0 on clean, non-zero on any drift OR
smoke-shim failure — so a failing CI badge means a real regression.

Usage (run from repo root):

    python -m tools.regression_check                       # full sweep
    python -m tools.regression_check --courses kimi,aie    # restrict
    python -m tools.regression_check --skip-smoke          # drift only
    python -m tools.regression_check --skip-drift          # smoke only
    python -m tools.regression_check --json                # machine output

GHA wiring (suggested workflow):

    name: regression-check
    on:
      pull_request:
        paths:
          - "backend/verified_facts*.py"
          - "backend/main.py"   # Creator prompt edits
          - "frontend/index.html"
          - "cli/**"
    jobs:
      regression:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: docker compose up -d  # boots LMS at :8001
          - run: python -m tools.regression_check
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Allow running as `python tools/regression_check.py` OR `python -m tools.regression_check`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_LMS_URL = os.environ.get("LMS_URL", "http://localhost:8001")
DEFAULT_DOCKER_IMAGE = os.environ.get("SKILLSLAB_IMAGE", "skillslab:latest")


# ── Course identification ────────────────────────────────────────────────

# Slug → course id mapping for the canonical AI-enablement courses. The
# CLI's --course wrappers also accept these slugs.
KNOWN_COURSES = {
    "aie":      "created-7fee8b78c742",  # AI-Augmented Engineering: Claude Code
    "kimi":     "created-698e6399e3ca",  # Open-Source AI Coding: Kimi+Aider
    "jspring":  "created-e54e7d6f51cf",  # Java + Spring Boot Claude Code
}


# ── Drift scan ───────────────────────────────────────────────────────────

def scan_drift(lms_url: str, course_filter: list[str] | None) -> dict:
    """Walk every relevant course's modules+steps; run the registry-driven
    drift checker on each step's content. Returns a dict with per-course
    violation lists.
    """
    from backend import verified_facts as vf
    from backend import verified_facts_data  # noqa: F401  (registers on import)

    print(f"\n{'=' * 70}")
    print("DRIFT SCAN  —  verified-facts registry coverage:")
    print(vf.list_drift_summary())
    print(f"{'=' * 70}")

    catalog = json.loads(urllib.request.urlopen(f"{lms_url}/api/courses").read())
    course_ids = []
    if course_filter:
        for f in course_filter:
            if f.startswith("created-"):
                course_ids.append(f)
            elif f in KNOWN_COURSES:
                course_ids.append(KNOWN_COURSES[f])
    else:
        course_ids = [c["id"] for c in catalog]

    total = 0
    course_results = {}
    for cid in course_ids:
        # Find course meta from catalog
        meta = next((c for c in catalog if c["id"] == cid), None)
        if not meta:
            print(f"\n  ✗ {cid}: not in catalog")
            continue
        title = meta.get("title", "")
        # Skip courses with no in-scope tech (avoids scanning every course)
        in_scope = vf.in_scope_techs(title, meta.get("description", ""), "")
        if not in_scope:
            continue

        scope_str = ",".join(t.tech_id for t in in_scope)
        violations_for_course = []
        try:
            data = json.loads(urllib.request.urlopen(f"{lms_url}/api/courses/{cid}").read())
        except Exception as e:
            print(f"\n  ✗ {cid}: couldn't fetch ({e})")
            continue
        for m in data.get("modules", []):
            try:
                mod = json.loads(urllib.request.urlopen(
                    f"{lms_url}/api/courses/{cid}/modules/{m['id']}"
                ).read())
            except Exception:
                continue
            for s in mod.get("steps", []):
                v = vf.check_drift(
                    content=s.get("content", "") or "",
                    code=s.get("code", "") or "",
                    validation=s.get("validation", {}) or {},
                    demo_data=s.get("demo_data", {}) or {},
                    title=s.get("title", "") or "",
                    course_title=title,
                    course_description=meta.get("description", ""),
                )
                if v:
                    label = f"M{m['position']-1}.S{s['position']}"
                    violations_for_course.append({
                        "step_id": s["id"], "label": label,
                        "title": s["title"][:60], "violations": v,
                    })

        n = sum(len(x["violations"]) for x in violations_for_course)
        total += n
        course_results[cid] = {
            "title": title, "scope": scope_str, "n_violations": n,
            "steps_with_drift": violations_for_course,
        }
        marker = "✓" if n == 0 else "✗"
        print(f"\n  {marker} [{scope_str:<20}] {title[:55]}  ({n} drift{'s' if n != 1 else ''})")
        for x in violations_for_course[:5]:
            print(f"      {x['label']} \"{x['title']}\":")
            for v in x["violations"][:2]:
                print(f"        - {v[:130]}")

    print(f"\n  TOTAL drifts across all in-scope courses: {total}")
    return {"total_drifts": total, "courses": course_results}


# ── Smoke shim (CLI walkthrough) ─────────────────────────────────────────

def run_smoke_shim(image: str, lms_url: str) -> dict:
    """Drive the CLI smoke shim inside the Docker image. Returns a dict
    with pass/fail per course."""
    print(f"\n{'=' * 70}")
    print("SMOKE SHIM  —  driving the real `skillslab` binary across kimi/aie/jspring")
    print(f"{'=' * 70}\n")

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{Path.cwd()}/cli:/work",
        "-v", f"{os.path.expanduser('~/.skillslab')}:/root/.skillslab",
        "-e", f"SKILLSLAB_API_URL={lms_url}",
        "--add-host=host.docker.internal:host-gateway",
        image,
        "bash", "-c",
        "pip install -q -e /work >/dev/null 2>&1 && python -m tests.smoke_terminal --skip-start",
    ]
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("  ✗ smoke shim timed out after 10min")
        return {"ok": False, "reason": "timeout"}

    print(result.stdout[-2000:])
    elapsed = int(time.time() - t0)
    n_pass_lines = sum(1 for ln in result.stdout.splitlines() if "✓ PASS" in ln)
    n_fail_lines = sum(1 for ln in result.stdout.splitlines() if "✗ FAIL" in ln)
    ok = result.returncode == 0 and n_fail_lines == 0
    return {"ok": ok, "exit": result.returncode, "elapsed_s": elapsed,
            "courses_pass": n_pass_lines, "courses_fail": n_fail_lines}


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lms-url", default=DEFAULT_LMS_URL)
    ap.add_argument("--image", default=DEFAULT_DOCKER_IMAGE,
                    help="Docker image with the skillslab CLI installed")
    ap.add_argument("--courses", default=None,
                    help="Comma-separated slugs/IDs to restrict drift scan")
    ap.add_argument("--skip-drift", action="store_true")
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--json", action="store_true",
                    help="Print machine-readable JSON summary at end")
    ns = ap.parse_args()

    course_filter = ns.courses.split(",") if ns.courses else None

    drift_result = {"total_drifts": 0, "courses": {}, "skipped": True}
    smoke_result = {"ok": True, "skipped": True}

    if not ns.skip_drift:
        try:
            drift_result = scan_drift(ns.lms_url, course_filter)
        except Exception as e:
            print(f"\n  ✗ drift scan crashed: {e}")
            drift_result = {"total_drifts": -1, "error": str(e)}

    if not ns.skip_smoke:
        try:
            smoke_result = run_smoke_shim(ns.image, ns.lms_url)
        except Exception as e:
            print(f"\n  ✗ smoke shim crashed: {e}")
            smoke_result = {"ok": False, "error": str(e)}

    print(f"\n{'=' * 70}")
    print("REGRESSION CHECK  —  SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Drift total: {drift_result.get('total_drifts','skipped')}")
    print(f"  Smoke shim:  {'OK' if smoke_result.get('ok') else 'FAIL'}")

    if ns.json:
        print(json.dumps({"drift": drift_result, "smoke": smoke_result}, indent=2, default=str))

    # Non-zero exit on regression → CI fails the build
    fail = (
        (drift_result.get("total_drifts") or 0) > 0
        or not smoke_result.get("ok", True)
    )
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
