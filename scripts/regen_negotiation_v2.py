"""Regenerate the negotiation course ONE more time through Creator to validate:
  1. Canonical rubric_tags (BATNA, anchoring, emotional_regulation, genuine_vulnerability)
  2. Filler-detection in _is_complete rejects own-title self-reference
  3. Persona doesn't coach the learner
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

SPEC = {
    "title": "Defending Scope Under Executive Pressure v2",
    "description": (
        "For tech leads. You've been told a 6-week scope must ship in 3 weeks or a customer "
        "will churn. You must defend the timeline without getting branded 'unhelpful.' Capstone: "
        "adaptive_roleplay with a VP named Diana under board pressure. Her hidden state "
        "(patience, trust, flexibility) shifts based on whether you bring data, hedge, over-promise, "
        "or propose phased alternatives. Grade on state trajectory across 15 turns, not multiple "
        "choice. Rubric MUST name: anchoring, BATNA, data_specificity, phased_alternative, "
        "emotional_regulation, genuine_vulnerability. Diana must NOT coach the learner; she stays "
        "in-role as a VP under real board pressure."
    ),
    "course_type": "case_study",
    "answers": [
        "Senior engineers, tech leads, staff engineers, engineering managers",
        "Claude API drives the VP persona with hidden state (patience/trust/flexibility). No external tools.",
        "Capstone: adaptive_roleplay — VP Diana pressures on scope; rubric uses canonical negotiation skill tags (anchoring, BATNA, data_specificity, phased_alternative, emotional_regulation, genuine_vulnerability). Persona stays in-role, does not coach.",
    ],
}


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:500]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def main():
    t0 = time.time()
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)

    status, start = await asyncio.to_thread(_post, "/api/creator/start", {"title": SPEC["title"], "description": SPEC["description"], "course_type": SPEC["course_type"]})
    if status != 200: print(f"start failed: {start}"); return
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": SPEC["answers"][i] if i < len(SPEC["answers"]) else "Use adaptive_roleplay."} for i, q in enumerate(start.get("questions", [])[:4])]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200: print(f"refine failed: {refine}"); return
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200: print(f"generate failed: {g}"); return
    cid = g["course_id"]
    print(f"Generated {cid} in {time.time()-t0:.0f}s", flush=True)

    # Inspect rubric_tags
    d = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}").read())
    for m in d["modules"]:
        mod = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}").read())
        for s in mod["steps"]:
            if s.get("exercise_type") == "adaptive_roleplay":
                dd = s.get("demo_data", {}) or {}
                print(f"rubric_tags: {dd.get('debrief',{}).get('rubric_tags')}")
                cp = dd.get("counterparty", {})
                sysp = (cp.get("persona_system_prompt") or "")[:300]
                print(f"persona_sys_prompt (first 300 chars): {sysp}")
            if s.get("exercise_type") == "concept":
                # Check for filler
                content = (s.get("content") or "")[:200].lower()
                has_filler = any(p in content for p in [
                    "in the work you will do after",
                    "applying it poorly results in measurable",
                    "this concept shows up most often"
                ])
                print(f"  M{m['position']} S{s['position']} concept filler-detected: {has_filler}")

    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
