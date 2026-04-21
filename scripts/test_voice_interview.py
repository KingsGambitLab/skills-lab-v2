"""Smoke-test: generate a behavioral-interview-prep course via Creator.
Verify the Creator picks voice_mock_interview as the capstone.
"""
import json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

SPEC = {
    "title": "Behavioral Interview Prep: Senior PM at a B2B SaaS",
    "description": (
        "For software PMs preparing for senior/staff-level interviews at Series-B to "
        "post-IPO B2B SaaS companies. Practice behavioral questions (ownership of tough "
        "trade-offs, conflict with engineering, stakeholder push-back, scope cuts) with a "
        "simulated hiring manager who listens for STAR structure, specificity, ownership, "
        "and metrics. The capstone MUST be a live VOICE mock interview — the learner speaks "
        "answers via mic and the interviewer replies aloud, because pace / filler words / "
        "structure / delivery are part of the skill being evaluated. Not a typed roleplay."
    ),
    "course_type": "case_study",
    "answers": [
        "Senior PMs, Staff PMs, Product leaders preparing for next-level interviews",
        "Browser-native SpeechRecognition + SpeechSynthesis (no paid voice API). Claude API for persona and scoring.",
        "Capstone: voice_mock_interview — live mic-based behavioral interview with Sarah (Senior Director of Product). STAR_structure, specificity_of_example, ownership_of_outcome, metrics_grounding rubric tags. Minimum 3-turn floor before win.",
    ],
}


def post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:500]}
    except Exception as e: return -1, {"error": str(e)[:300]}


def get(path):
    return json.loads(urllib.request.urlopen(BASE+path, timeout=30).read())


def main():
    t0 = time.time()
    b = get("/api/admin/budget")
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)

    status, start = post("/api/creator/start", SPEC)
    if status != 200:
        print(f"start failed: {start}"); return
    sid = start["session_id"]
    answers = [
        {"question_id": q["id"], "answer": SPEC["answers"][i] if i < len(SPEC["answers"]) else "Use voice_mock_interview for the capstone."}
        for i, q in enumerate(start.get("questions", [])[:4])
    ]
    status, refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"refine failed: {refine}"); return
    # Inspect outline for voice_mock_interview
    types = []
    for m in refine["outline"]["modules"]:
        for s in m["steps"]:
            types.append(s.get("exercise_type", s.get("type")))
    print(f"Outline types: {types}", flush=True)
    has_voice = "voice_mock_interview" in types
    print(f"voice_mock_interview in outline: {has_voice}", flush=True)

    status, g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"generate failed: {g}"); return
    cid = g["course_id"]
    print(f"Generated {cid} in {time.time()-t0:.0f}s", flush=True)

    # Inspect the voice_mock_interview step (if present)
    d = get(f"/api/courses/{cid}")
    found_voice = False
    for m in d["modules"]:
        mod = get(f"/api/courses/{cid}/modules/{m['id']}")
        for s in mod["steps"]:
            if s.get("exercise_type") == "voice_mock_interview":
                found_voice = True
                dd = s.get("demo_data", {})
                cp = dd.get("counterparty", {})
                print(f"\nVOICE STEP: M{m['position']} — {s['title']}")
                print(f"  interview_style: {dd.get('interview_style')}")
                print(f"  voice_mode: {dd.get('voice_mode')}")
                print(f"  opening_question: {dd.get('opening_question','')[:200]}")
                print(f"  persona_name: {cp.get('persona_name')}")
                print(f"  hidden_state: {cp.get('hidden_state')}")
                print(f"  rubric_tags: {dd.get('debrief',{}).get('rubric_tags')}")
                break
        if found_voice: break

    if not found_voice:
        print(f"\n⚠ Creator did NOT pick voice_mock_interview. Capstone type: {types[-1] if types else '?'}")

    b = get("/api/admin/budget")
    print(f"\nBudget after: ${b['spent_usd']:.2f}", flush=True)


if __name__ == "__main__":
    main()
