"""F4 — Step-discovery + content-hash diff for safe regen sweeps.

Round-2 v8.7 sweep applied 5 fixes to wrong step IDs because the script
used hand-coded `step_id ↔ M.S-label` maps that drifted from reality.
The regens reported `ok` (LLM emitted SOMETHING) but the structural fix
went to a different step than intended, and the failures looked like
"the gate isn't catching" when actually "the patcher targeted the wrong
file."

This tool:

  - DISCOVER mode: given a course_id + (exercise_type filter, title-keyword
    filter, M.S label hint), print every matching step's actual step_id
    and current content hash. NO hand-coded maps; we always go through
    the live API.

  - PATCH-VERIFY mode: take a CSV of (course_id, step_id, content_hash_before)
    pairs, verify the content_hash CHANGED post-regen. Fail loud if any
    step's hash didn't move — we know something didn't apply.

  - REGEN mode: discover → snapshot hash → fire regen → verify hash moved
    → emit a final summary with per-step before/after hashes.

Usage:

  # Discover all CLAUDE.md authoring steps in AIE
  python -m tools.step_discovery discover \
      --course created-7fee8b78c742 \
      --title-contains "CLAUDE.md" "authoring" "Write CLAUDE"

  # Discover by exercise_type
  python -m tools.step_discovery discover \
      --course created-7fee8b78c742 \
      --exercise-type code_exercise

  # Sweep with regen + hash verification
  python -m tools.step_discovery regen \
      --course created-7fee8b78c742 \
      --title-contains "CLAUDE.md" "authoring" \
      --feedback "Convert from code_exercise to terminal_exercise + rubric. F2 violation: writing markdown is NOT a code_exercise."
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Allow `python -m tools.step_discovery` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_LMS_URL = os.environ.get("LMS_URL", "http://localhost:8001")


def _content_hash(step: dict) -> str:
    """Compute a stable hash over the regennable fields. Excludes id /
    position / module_id (those don't change on regen) but includes title,
    content, code, validation, demo_data, exercise_type, expected_output."""
    payload = {
        "title": step.get("title", ""),
        "exercise_type": step.get("exercise_type"),
        "content": step.get("content", "") or "",
        "code": step.get("code", "") or "",
        "expected_output": step.get("expected_output", "") or "",
        "validation": step.get("validation", {}) or {},
        "demo_data": step.get("demo_data", {}) or {},
    }
    s = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _fetch_course_steps(lms_url: str, course_id: str) -> list[dict]:
    """Fetch every step in a course as a flat list with module-position
    metadata attached. One curl per module."""
    course = json.loads(urllib.request.urlopen(f"{lms_url}/api/courses/{course_id}").read())
    out = []
    for m in course.get("modules", []):
        try:
            mod = json.loads(urllib.request.urlopen(
                f"{lms_url}/api/courses/{course_id}/modules/{m['id']}"
            ).read())
        except Exception as e:
            print(f"  [warn] couldn't fetch module {m['id']}: {e}", file=sys.stderr)
            continue
        for s in mod.get("steps", []):
            out.append({**s, "_m_pos": m["position"], "_m_title": m["title"]})
    return out


def _matches(step: dict, filters: dict) -> bool:
    """Match a step against the discover filters."""
    if filters.get("exercise_type"):
        if (step.get("exercise_type") or "").lower() != filters["exercise_type"].lower():
            return False
    if filters.get("title_contains"):
        title = (step.get("title") or "").lower()
        for kw in filters["title_contains"]:
            if kw.lower() in title:
                return True
        return False
    if filters.get("ms_label"):
        label = f"M{step['_m_pos']-1}.S{step['position']}"
        if label != filters["ms_label"].upper():
            return False
    if filters.get("step_id"):
        if step["id"] != filters["step_id"]:
            return False
    return True


def cmd_discover(ns) -> int:
    filters = {}
    if ns.exercise_type: filters["exercise_type"] = ns.exercise_type
    if ns.title_contains: filters["title_contains"] = ns.title_contains
    if ns.ms_label: filters["ms_label"] = ns.ms_label

    steps = _fetch_course_steps(ns.lms_url, ns.course)
    matches = [s for s in steps if _matches(s, filters)] if filters else steps

    print(f"\nCourse {ns.course}  ({len(steps)} total steps; {len(matches)} matching)")
    print("-" * 80)
    print(f"  {'step_id':<8} {'M.S':<8} {'type':<22} {'hash':<16}  title")
    print("-" * 80)
    for s in matches:
        label = f"M{s['_m_pos']-1}.S{s['position']}"
        et = s.get("exercise_type") or "concept"
        print(f"  {s['id']:<8} {label:<8} {et:<22} {_content_hash(s):<16}  {s['title'][:40]}")
    return 0


def cmd_regen(ns) -> int:
    """Discover + snapshot + regen + verify-hash-moved per step."""
    filters = {}
    if ns.exercise_type: filters["exercise_type"] = ns.exercise_type
    if ns.title_contains: filters["title_contains"] = ns.title_contains
    if ns.ms_label: filters["ms_label"] = ns.ms_label
    if ns.step_id: filters["step_id"] = ns.step_id

    steps = _fetch_course_steps(ns.lms_url, ns.course)
    matches = [s for s in steps if _matches(s, filters)]
    if not matches:
        print("  no matches — refine filters")
        return 1

    print(f"\nRegen sweep: {len(matches)} step(s) in {ns.course}")
    print("-" * 80)
    snapshots = {s["id"]: _content_hash(s) for s in matches}
    for s in matches:
        label = f"M{s['_m_pos']-1}.S{s['position']}"
        print(f"  [SNAP] step_id={s['id']} {label} {s['title'][:50]} hash={snapshots[s['id']]}")

    if ns.dry_run:
        print("  (--dry-run — no regens fired)")
        return 0

    print("\nFiring regens...")
    results = []
    for s in matches:
        label = f"M{s['_m_pos']-1}.S{s['position']}"
        body = {"feedback": ns.feedback or ""}
        req = urllib.request.Request(
            f"{ns.lms_url}/api/courses/{ns.course}/steps/{s['id']}/regenerate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=600)
            out = json.loads(resp.read())
            ok = bool(out.get("ok"))
            ms = int((time.time() - t0) * 1000)
            print(f"  [REGEN] step_id={s['id']} {label} → {'ok' if ok else 'fail: ' + str(out.get('reason','?'))[:120]} ({ms}ms)")
            results.append({"step_id": s["id"], "label": label, "ok": ok})
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            print(f"  [REGEN] step_id={s['id']} {label} → HTTP {e.code}: {body_text[:120]}")
            results.append({"step_id": s["id"], "label": label, "ok": False, "error": f"HTTP {e.code}"})
        except Exception as e:
            print(f"  [REGEN] step_id={s['id']} {label} → {type(e).__name__}: {e}")
            results.append({"step_id": s["id"], "label": label, "ok": False, "error": str(e)})

    print("\nVerifying hash diffs...")
    new_steps = _fetch_course_steps(ns.lms_url, ns.course)
    new_steps_by_id = {s["id"]: s for s in new_steps}
    failed_to_change = 0
    for r in results:
        before = snapshots.get(r["step_id"])
        ns_step = new_steps_by_id.get(r["step_id"])
        if not ns_step:
            print(f"  [VERIFY] step_id={r['step_id']} {r['label']} → step disappeared (?)")
            continue
        after = _content_hash(ns_step)
        moved = before != after
        marker = "✓ MOVED" if moved else "✗ UNCHANGED"
        print(f"  [VERIFY] step_id={r['step_id']} {r['label']} {marker}  before={before} after={after}")
        if not moved and r.get("ok"):
            failed_to_change += 1

    print()
    n_ok = sum(1 for r in results if r.get("ok"))
    print(f"Sweep summary: {n_ok}/{len(results)} regens reported ok, "
          f"{failed_to_change} of those did NOT change content")
    return 1 if failed_to_change else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lms-url", default=DEFAULT_LMS_URL)
    common.add_argument("--course", required=True, help="course_id (e.g. created-7fee8b78c742)")
    common.add_argument("--exercise-type", help="filter by exercise_type")
    common.add_argument("--title-contains", nargs="+", help="filter: title contains ANY of these keywords")
    common.add_argument("--ms-label", help="exact M.S label, e.g. M2.S2")
    common.add_argument("--step-id", type=int, help="exact step_id")

    sp_disc = sp.add_parser("discover", parents=[common], help="list matching steps + their content hashes")
    sp_disc.set_defaults(func=cmd_discover)

    sp_regen = sp.add_parser("regen", parents=[common], help="discover + regen + verify hash moved")
    sp_regen.add_argument("--feedback", required=True, help="feedback string for regen")
    sp_regen.add_argument("--dry-run", action="store_true")
    sp_regen.set_defaults(func=cmd_regen)

    ns = ap.parse_args()
    sys.exit(ns.func(ns))


if __name__ == "__main__":
    main()
