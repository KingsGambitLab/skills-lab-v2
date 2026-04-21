"""Regenerate 'Emergent Full-Stack Support Engineering' via Creator API.
Same title/description as the original — proves the Creator now produces invariant-compliant
courses (no answer leaks, working validation, Creator-chosen level).
"""
import json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

SPEC = {
    "title": "Emergent Full-Stack Support Engineering v2",
    "description": (
        "4-week × 4-hour-per-day intensive full-stack engineering training for support "
        "engineers. Case-based with LLM-judged assessments. Covers Frontend, Backend, DBMS, "
        "Networking, Cloud (AWS+GCP), DevOps. Learners practice real support scenarios via "
        "scenario_branch + ordering + categorization + adaptive_roleplay capstone with a "
        "VP of Engineering who challenges their incident hypothesis. Target level: Intermediate "
        "(2-4 year support engineers ramping to full-stack)."
    ),
    "course_type": "technical",
    "level": "Intermediate",
    "answers": [
        "Support engineers with 2-4 years experience, ramping to full-stack",
        "Claude API for scenario authoring + adaptive_roleplay; scripted incident_console for the capstone drill",
        "Capstone: multi-stack incident with VP pressure (adaptive_roleplay) — persona patience/trust/flexibility start >=5, escalation <=0, rubric: root_cause_specificity, ETA_accuracy, hedging_discipline, precision_under_pressure",
    ],
}


def post(p, b, timeout=300):
    req = urllib.request.Request(BASE+p, data=json.dumps(b).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:500]}


def get(p):
    return json.loads(urllib.request.urlopen(BASE+p, timeout=30).read())


def main():
    t0 = time.time()
    b = get("/api/admin/budget")
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)

    s, start = post("/api/creator/start", SPEC)
    if s != 200: print(f"start: {start}"); return
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": SPEC["answers"][i] if i < len(SPEC["answers"]) else "Use adaptive_roleplay."} for i, q in enumerate(start.get("questions", [])[:4])]
    s, refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
    if s != 200: print(f"refine: {refine}"); return
    s, g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if s != 200: print(f"generate: {g}"); return
    cid = g["course_id"]
    print(f"Generated {cid} in {time.time()-t0:.0f}s", flush=True)

    # Verify: level persisted + no answer leaks
    d = get(f"/api/courses/{cid}")
    print(f"\nTitle: {d['title']}")
    print(f"Level (Creator-chosen): {d.get('level')}")
    print(f"Modules: {len(d['modules'])}")
    leak_summary = {}
    for m in d["modules"]:
        mod = get(f"/api/courses/{cid}/modules/{m['id']}")
        for s2 in mod["steps"]:
            flat = json.dumps(s2.get("demo_data") or {})
            for key in ("correct_position","correct_category","correct_rank","correct_answer","correct_mapping","correct_order","\"correct\": true"):
                if key in flat:
                    leak_summary[key] = leak_summary.get(key, 0) + 1
    if leak_summary:
        print(f"\nLEAKS FOUND: {leak_summary}")
    else:
        print(f"\nCLEAN: no answer-key leaks across any step")

    b = get("/api/admin/budget")
    print(f"\nBudget after: ${b['spent_usd']:.2f}", flush=True)
    print(f"\nCourse URL: http://localhost:8001/#{cid}")


if __name__ == "__main__":
    main()
