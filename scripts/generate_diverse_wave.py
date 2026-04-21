"""Generate 8 more diverse courses to stress the Creator on unusual subjects."""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {"title": "Effective Async Communication for Distributed Teams",
     "description": "Master writing clear Slack messages, RFC docs, and meeting notes that work across time zones. Capstone: roleplay with a colleague who misread your message and escalated to your manager.",
     "course_type": "case_study"},
    {"title": "Crisis Communication for Tech Leaders",
     "description": "Lead communication during outages and incidents. Practice live public incident updates, internal Slack threads, and post-mortem meetings. Capstone is a live incident where you're the incident commander.",
     "course_type": "case_study"},
    {"title": "Technical Debt Prioritization",
     "description": "Quantify and prioritize technical debt. Make tradeoff cases to product + leadership. Practice selling a 6-month refactor to a skeptical VP. Capstone is adaptive_roleplay with a 'just ship features' CEO.",
     "course_type": "case_study"},
    {"title": "AI Ethics in Practice for Engineers",
     "description": "Real ethical dilemmas in ML/AI systems: bias in hiring models, privacy in recommendations, consent in training data. Scenarios with branching consequences. Capstone roleplay: explain to a non-technical board why you killed a profitable feature.",
     "course_type": "compliance"},
    {"title": "System Design Interview Preparation",
     "description": "Practice whiteboard-style system design under time pressure. Design URL shortener, chat app, payment system. Interactive interview simulator as capstone — AI interviewer probes your design.",
     "course_type": "technical"},
    {"title": "Data Engineering: Production Pipeline Failures",
     "description": "Live data-pipeline incident drills: Airflow DAG failures, schema drift, stale dashboards, data quality alerts. Fix them via incident_console. Capstone: multi-hour pipeline outage in a data lake.",
     "course_type": "technical"},
    {"title": "OKRs and Strategy for Senior Engineers",
     "description": "Translate company OKRs into engineering work. Write your first OKR. Present roadmap to VPs. Capstone: adaptive_roleplay defending your Q3 plan in a panel review.",
     "course_type": "case_study"},
    {"title": "Technical Hiring at Scale",
     "description": "Build a hiring process that scales. Score rubrics. Calibrate across interviewers. Practice debriefs. Capstone: run a full hiring-debrief simulation with 4 AI panelists who disagree.",
     "course_type": "case_study"},
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:400]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def gen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}/8] {spec['title'][:55]}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", spec)
    if status != 200:
        print(f"  [{idx+1}/8] start failed: {start}", flush=True); return None
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Use adaptive_roleplay / incident_console / simulator_loop where they fit. Make it immersive, not a deck."} for q in start.get("questions", [])[:4]]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}/8] refine failed: {refine}", flush=True); return None
    types = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]:
            types.add(s.get("exercise_type", s.get("type")))
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}/8] generate failed: {g}", flush=True); return None
    uses_new = bool(types & {"adaptive_roleplay", "incident_console", "simulator_loop"})
    flag = "[NEW]" if uses_new else "[trad]"
    print(f"  [{idx+1}/8] {flag} OK {g.get('course_id')} ({time.time()-t0:.0f}s) — types: {sorted(types)}", flush=True)
    return {"title": spec["title"], "course_id": g.get("course_id"), "types": sorted(types), "uses_new": uses_new}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception:
        pass
    sem = asyncio.Semaphore(3)
    async def bounded(s, i):
        async with sem: return await gen(s, i)
    results = await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception:
        pass
    print("\n=== Diverse wave results ===", flush=True)
    uses_new = sum(1 for r in results if r and r["uses_new"])
    print(f"{uses_new}/{sum(1 for r in results if r)} courses used new pedagogies", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
