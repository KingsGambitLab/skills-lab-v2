"""Wave 3: 10 more courses exploring frontier applications of the new pedagogy."""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {"title": "Founder Fundraising: Pitching to Skeptical VCs",
     "description": "Practice live pitches with an AI VC who asks hard questions, pushes on unit economics, and challenges TAM claims. Capstone: 15-minute pitch simulation with 3 VC personas (enthusiastic, skeptical, silent). adaptive_roleplay-heavy.",
     "course_type": "case_study"},
    {"title": "Salary Negotiation for Senior Engineers",
     "description": "Negotiate your offer. Practice conversations with a recruiter, hiring manager, and exec. Each persona has hidden state (budget flexibility, urgency to close, competition).",
     "course_type": "case_study"},
    {"title": "Code Review Conversations That Build Trust",
     "description": "Learn to give (and receive) code review feedback that improves code AND relationships. Roleplay with defensive engineers, junior engineers afraid to push back, and staff engineers with strong opinions.",
     "course_type": "case_study"},
    {"title": "Redis Ops: Cache Apocalypse",
     "description": "Live incident: Redis cluster at 99% memory, eviction storms, downstream services timing out. Live drill to diagnose and remediate (AOF rewrite, cluster rebalance, memory eviction policy tuning). Zero-LLM.",
     "course_type": "technical"},
    {"title": "Migrating a Monolith: The Strangler Pattern in Practice",
     "description": "Multi-phase simulation of migrating a 10-year monolith to microservices. Decide routing strategy, data splitting, rollback plans. Use simulator_loop for the 18-month migration.",
     "course_type": "case_study"},
    {"title": "Customer Support Under Regulatory Scrutiny",
     "description": "Live roleplay: a customer is asking a question that touches regulated territory (healthcare, finance, privacy). You must answer helpfully without creating legal risk. adaptive_roleplay with a legally-sensitive customer.",
     "course_type": "compliance"},
    {"title": "Tech Lead Office Hours: Managing Conflicting Priorities",
     "description": "4-hour window simulation: 6 engineers need you for different things simultaneously (design review, production bug, career 1:1, architecture debate, new-hire onboarding, interview). Simulator_loop triages incoming requests.",
     "course_type": "case_study"},
    {"title": "Data Engineering: Pipeline Reliability at Scale",
     "description": "Combined incident_console for pipeline outages + adaptive_roleplay for stakeholder communication. Practice debugging Airflow DAG failures live while also handling the PM who's asking 'when will the dashboard be back?'",
     "course_type": "technical"},
    {"title": "Enterprise Architect: System Design Review",
     "description": "You're the architect reviewing an engineer's proposal. Practice live conversations where the engineer defends their design, you probe tradeoffs, and you together converge on the right answer — without being condescending.",
     "course_type": "case_study"},
    {"title": "LLM Engineering: Prompt Iteration Under Production Load",
     "description": "Your AI feature is degrading in production. Error rate 15%. Live drill: tune prompts, check context windows, inspect tool-use failures. Capstone: multi-phase simulator with prompt edits + eval run + canary deploy.",
     "course_type": "technical"},
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:400]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def gen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}/10] {spec['title'][:55]}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", spec)
    if status != 200:
        print(f"  [{idx+1}/10] start failed: {start}", flush=True); return None
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Use adaptive_roleplay / incident_console / simulator_loop for the capstone and at least one mid-course step. Make it immersive."} for q in start.get("questions", [])[:4]]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}/10] refine failed: {refine}", flush=True); return None
    types = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]: types.add(s.get("exercise_type", s.get("type")))
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}/10] generate failed: {g}", flush=True); return None
    new_types = sorted(types & {"adaptive_roleplay","incident_console","simulator_loop"})
    flag = "[NEW]" if new_types else "[trad]"
    print(f"  [{idx+1}/10] {flag} OK {g.get('course_id')} ({time.time()-t0:.0f}s) — new: {new_types}", flush=True)
    return True


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(3)
    async def bounded(s, i):
        async with sem: return await gen(s, i)
    await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
