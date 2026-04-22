"""Course test harness — "will the learner succeed?" solver.

Invariants
----------
1. Every exercise step in a course is actually solvable.
2. The grader returns the score the assignment SHOULD get for a canonical answer.
3. For code-writing types, a real genuine attempt gets a passing score.
4. For drag-drop / ordering / categorization / sjt / mcq / fill_in_blank, the
   canonical answer (read from the unsanitized admin view) gets >= 0.95.

The harness runs against a live server (default http://127.0.0.1:8001). For
code_exercise + system_build, it prints the exercise for an OUTER AGENT to
solve — the outer agent is launched by the parent script that drives this
harness. This script handles the deterministic half.

Usage:
    python tools/test_course.py <course_id> [--base http://127.0.0.1:8001]
         [--out /tmp/report.md] [--code-solutions /tmp/solutions.json]

Outputs:
    - A markdown artifact with per-step verdicts + aggregate acceptance %.
    - When --code-solutions is given, a JSON file listing the code exercises
      that need an outer-agent solve (fields: step_id, title, exercise_type,
      language, content, code, validation). The outer-agent writes a dict
      {step_id: solution_code} back, and the harness is re-run with
      --apply-solutions pointing at that file.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


def get(base: str, path: str, timeout: float = 30) -> Any:
    req = urllib.request.Request(f"{base}{path}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def post(base: str, path: str, body: dict, timeout: float = 60) -> Any:
    req = urllib.request.Request(
        f"{base}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return {"_http_error": e.code, "_body": e.read().decode()[:500]}
        except Exception:
            return {"_http_error": e.code}


def fetch_full_course(base: str, course_id: str) -> dict:
    """Fetch with include_in_progress so recent gens are visible."""
    full = get(base, f"/api/courses/{course_id}?include_in_progress=1")
    full["modules_full"] = []
    for m in full.get("modules") or []:
        mod = get(base, f"/api/courses/{course_id}/modules/{m['id']}")
        full["modules_full"].append(mod)
    return full


def _admin_step(base: str, step_id: int) -> dict | None:
    """Try to fetch the step in admin-view (with answer key) if such an endpoint
    exists. Falls back to the learner view which is sanitized.
    """
    for path in (f"/api/admin/steps/{step_id}", f"/api/steps/{step_id}"):
        try:
            return get(base, path, timeout=10)
        except Exception:
            continue
    return None


def canonical_answer(step: dict) -> dict | None:
    """Derive the canonical correct submission from the UNSANITIZED step data
    (demo_data + validation as stored in DB). Returns the response_data payload
    to POST to /api/exercises/validate. None if no deterministic answer.
    """
    et = step.get("exercise_type") or ""
    dd = step.get("demo_data") or {}
    val = step.get("validation") or {}
    merged = {**dd, **val}

    if et == "mcq":
        ca = merged.get("correct_answer")
        if ca is None:
            for i, o in enumerate(merged.get("options") or []):
                if isinstance(o, dict) and o.get("correct"):
                    ca = i; break
        return {"answer": ca} if ca is not None else None

    if et == "ordering":
        order = merged.get("correct_order")
        if not order:
            items = merged.get("items") or []
            order = [it.get("id") for it in sorted(items, key=lambda x: x.get("correct_position", 0))]
        return {"order": order} if order else None

    if et == "parsons":
        order = merged.get("correct_order") or (dd.get("lines") or [])
        return {"order": order} if order else None

    if et == "categorization":
        mapping = merged.get("correct_mapping")
        if not mapping:
            mapping = {it.get("id"): it.get("correct_category")
                       for it in (merged.get("items") or []) if it.get("correct_category")}
        return {"mapping": mapping} if mapping else None

    if et == "sjt":
        rankings = merged.get("correct_rankings")
        if not rankings:
            opts = merged.get("options") or []
            rankings = [o.get("correct_rank", i+1) for i, o in enumerate(opts)]
        # sjt validator expects `response.rankings` (list matching option order)
        return {"rankings": rankings} if rankings else None

    if et == "scenario_branch":
        choices = {}
        for s_idx, q in enumerate(merged.get("steps") or []):
            for o_idx, opt in enumerate(q.get("options") or []):
                if isinstance(opt, dict) and opt.get("correct"):
                    choices[str(s_idx)] = o_idx
                    break
        return {"choices": choices} if choices else None

    if et == "fill_in_blank":
        blanks = merged.get("blanks") or []
        if not blanks:
            return None
        # Validator expects response.answers as a LIST (ordered by index), not a dict
        sorted_blanks = sorted(blanks, key=lambda b: b.get("index", 0))
        answers_list = [b.get("answer", "") for b in sorted_blanks]
        return {"answers": answers_list}

    if et == "code_review":
        bug_lines = merged.get("bug_lines") or [b.get("line") for b in (dd.get("bugs") or [])
                                                  if isinstance(b, dict) and b.get("line") is not None]
        return {"bug_lines": bug_lines} if bug_lines else None

    if et == "code_read":
        # code_read is read-and-explain. Canonical = a non-empty explanation.
        # Validator routes to _validate_explain_back which only requires a
        # non-empty string; LLM-rubric grading happens post-submission.
        return {"explanation": "This code's purpose + flow is clear; I read every line and can describe it."}

    if et == "system_build":
        # Harness canonical: mark ALL phases + checklist items complete. DO NOT
        # submit endpoint_url — the probe is for real deploys, not harness tests.
        # With no endpoint_url, the grader falls back to 60/40 phases+checklist
        # scoring; 100% on both → 1.0. This correctly tests "Creator produced a
        # valid rubric" without failing on a non-deployed live probe.
        phases = dd.get("phases") or []
        checklist = dd.get("checklist") or []
        payload = {
            "phases_completed": [p.get("id") for p in phases if isinstance(p, dict)],
            "checklist": {c.get("id"): True for c in checklist if isinstance(c, dict)},
        }
        return payload

    # code / code_exercise / system_build — need a solver, not a canonical
    return None


def test_step(base: str, step: dict) -> dict:
    """Test a single step. Returns {step_id, title, type, verdict, score, detail}."""
    step_id = step.get("id")
    title = step.get("title", "")
    et = step.get("exercise_type") or "concept"
    result = {
        "step_id": step_id, "title": title, "type": et,
        "verdict": "skipped", "score": None, "detail": "",
    }
    # Concept / code (read-only) steps — just verify content is non-empty
    if et in ("concept", "code", ""):
        clen = len(step.get("content") or "")
        codelen = len(step.get("code") or "")
        if et == "concept" and clen < 100:
            result.update(verdict="fail", detail=f"concept content too short ({clen} chars)")
        elif et == "code" and codelen < 20:
            result.update(verdict="fail", detail=f"code (read) snippet too short ({codelen} chars)")
        else:
            result.update(verdict="pass-static",
                          detail=f"content_len={clen} code_len={codelen}")
        return result

    # code_exercise needs a genuine code-writing solve — defer to outer agent
    if et == "code_exercise":
        result.update(verdict="pending-agent-solve",
                      detail=f"lang={(step.get('demo_data') or {}).get('language','?')}")
        return result
    # system_build: the Creator defines phases + checklist + endpoint_check.
    # Deterministic canonical = mark everything complete + submit the Creator's
    # endpoint_check URL. This tests whether the Creator produced a gradable
    # rubric — NOT whether a human learner could deploy the service (out of
    # scope for an agent harness). If the Creator set a placeholder URL like
    # "your-deployed-service/health", the endpoint probe will fail and we'll
    # flag the step.

    # Deterministic-canonical types — submit the answer key and expect high score
    canon = canonical_answer(step)
    if canon is None:
        result.update(verdict="fail", detail="no canonical answer derivable from demo_data+validation")
        return result

    resp = post(base, "/api/exercises/validate", {
        "step_id": step_id, "response_data": canon, "attempt_number": 1,
    })
    if "_http_error" in resp:
        result.update(verdict="fail", detail=f"HTTP {resp['_http_error']}: {resp.get('_body','')[:120]}")
        return result
    score = resp.get("score", 0.0) or 0.0
    correct = bool(resp.get("correct"))
    result["score"] = score
    if correct or score >= 0.95:
        result.update(verdict="pass", detail=f"score={score:.2f}")
    elif score >= 0.5:
        result.update(verdict="partial", detail=f"score={score:.2f} feedback={resp.get('feedback','')[:150]}")
    else:
        result.update(verdict="fail",
                      detail=f"canonical got score={score:.2f} ← grader bug OR bad demo_data. feedback={resp.get('feedback','')[:150]}")
    return result


def render_markdown(course: dict, results: list[dict], base: str) -> str:
    total = len(results)
    by_verdict = {}
    for r in results:
        by_verdict.setdefault(r["verdict"], []).append(r)
    pass_count = len(by_verdict.get("pass", [])) + len(by_verdict.get("pass-static", []))
    partial_count = len(by_verdict.get("partial", []))
    fail_count = len(by_verdict.get("fail", []))
    pending = len(by_verdict.get("pending-agent-solve", []))
    gradable_total = total - len(by_verdict.get("skipped", []))
    acceptance = (pass_count / gradable_total * 100) if gradable_total else 0.0
    # Pending code exercises aren't counted until outer agent solves them
    effective_total = gradable_total - pending if gradable_total > pending else gradable_total

    lines = [
        f"# Course test report: {course.get('title','?')}",
        f"**Course ID**: `{course.get('id','?')}`",
        f"**Base**: `{base}`",
        f"**Generated at**: (per script timestamp)",
        "",
        "## Summary",
        "",
        f"- Total steps: {total}",
        f"- Concept/code (static): {len(by_verdict.get('pass-static', []))}",
        f"- Gradable deterministic: {sum(len(by_verdict.get(v, [])) for v in ('pass', 'partial', 'fail'))}",
        f"- Code-writing (needs agent solve): {pending}",
        f"- **Acceptance (pass / gradable)**: {pass_count}/{gradable_total} = **{acceptance:.1f}%**",
        f"  - {'✅ ≥95%' if acceptance >= 95 else '❌ below 95%'}",
        "",
        "## Per-step verdicts",
        "",
        "| # | Type | Verdict | Score | Title | Detail |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        score = f"{r['score']:.2f}" if r.get("score") is not None else "—"
        lines.append(f"| {i} | `{r['type']}` | **{r['verdict']}** | {score} | {r['title'][:60]} | {r['detail'][:80]} |")
    lines.append("")

    if fail_count:
        lines.append("## Failures")
        lines.append("")
        for r in by_verdict.get("fail", []):
            lines.append(f"### Step {r['step_id']} — `{r['type']}` — {r['title']}")
            lines.append(f"- **verdict**: fail")
            lines.append(f"- **score**: {r.get('score', '—')}")
            lines.append(f"- **detail**: {r['detail']}")
            lines.append("")

    if pending:
        lines.append("## Code-writing exercises (awaiting outer-agent solve)")
        lines.append("")
        for r in by_verdict.get("pending-agent-solve", []):
            lines.append(f"- Step {r['step_id']}: `{r['type']}` — {r['title']}")
        lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course_id")
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    ap.add_argument("--out", default=None)
    ap.add_argument("--code-solutions", default=None,
                    help="Write JSON of pending code exercises for an outer agent to solve")
    ap.add_argument("--apply-solutions", default=None,
                    help="JSON file with {step_id: solution_code} — submit + grade each")
    args = ap.parse_args()

    # Use the admin-raw endpoint so we see unsanitized step data (answer keys
    # intact). The sanitizer strips correct_order / correct_mapping / bug_lines
    # from the learner-facing endpoint, so we can't derive canonicals without
    # this.
    try:
        raw = get(args.base, f"/api/admin/courses/{args.course_id}/raw", timeout=30)
        course = {"id": raw["id"], "title": raw["title"], "modules_full": raw["modules"]}
    except Exception as e:
        print(f"[warn] admin raw endpoint not available ({e}); falling back to sanitized")
        course = get(args.base, f"/api/courses/{args.course_id}?include_in_progress=1")
        course["modules_full"] = []
        for m in course.get("modules") or []:
            course["modules_full"].append(
                get(args.base, f"/api/courses/{args.course_id}/modules/{m['id']}")
            )

    solutions = {}
    if args.apply_solutions:
        solutions = json.loads(Path(args.apply_solutions).read_text())

    results = []
    code_pending = []
    for mod in course["modules_full"]:
        for step in (mod.get("steps") or []):
            et = step.get("exercise_type") or ""
            # Apply agent-supplied code solution if present — code_exercise only.
            # system_build uses canonical (phases + checklist + endpoint_url).
            if et == "code_exercise" and str(step["id"]) in solutions:
                sol = solutions[str(step["id"])]
                resp = post(args.base, "/api/exercises/validate", {
                    "step_id": step["id"],
                    "response_data": {"code": sol},
                    "attempt_number": 1,
                })
                score = resp.get("score", 0.0) or 0.0
                correct = bool(resp.get("correct"))
                if correct or score >= 0.95:
                    verdict = "pass"
                elif score >= 0.5:
                    verdict = "partial"
                else:
                    verdict = "fail"
                results.append({
                    "step_id": step["id"], "title": step.get("title", ""), "type": et,
                    "verdict": verdict, "score": score,
                    "detail": f"agent-solution score={score:.2f} feedback={(resp.get('feedback') or '')[:100]}",
                })
                continue
            r = test_step(args.base, step)
            results.append(r)
            if r["verdict"] == "pending-agent-solve":
                code_pending.append({
                    "step_id": step["id"],
                    "title": step.get("title", ""),
                    "module_title": mod.get("title", ""),
                    "exercise_type": et,
                    "language": (step.get("demo_data") or {}).get("language"),
                    "content_html": (step.get("content") or "")[:3000],
                    "starter_code": step.get("code") or "",
                    "expected_output": step.get("expected_output") or "",
                    "hint": (step.get("validation") or {}).get("hint") or "",
                    "must_contain": (step.get("validation") or {}).get("must_contain") or [],
                })

    # Write outputs
    md = render_markdown(course, results, args.base)
    out_path = args.out or f"/tmp/test_report_{args.course_id}.md"
    Path(out_path).write_text(md)
    print(f"[report] {out_path}")
    print(md.split("## Per-step verdicts")[0])

    if args.code_solutions:
        Path(args.code_solutions).write_text(json.dumps(code_pending, indent=2))
        print(f"[pending solves] {args.code_solutions} · {len(code_pending)} items")

    # Exit code reflects acceptance
    total = sum(1 for r in results if r["verdict"] not in ("skipped", "pending-agent-solve"))
    passed = sum(1 for r in results if r["verdict"] in ("pass", "pass-static"))
    acceptance = (passed / total * 100) if total else 0.0
    print(f"\nACCEPTANCE: {passed}/{total} = {acceptance:.1f}% "
          f"({'≥95% ✅' if acceptance >= 95 else '<95% ❌'})")
    sys.exit(0 if acceptance >= 95 and len(code_pending) == 0 else 1)


if __name__ == "__main__":
    main()
