"""Regenerate 4 weak-rated courses with new Creator (adaptive_roleplay + incident_console + stronger quality floor)."""
import asyncio, json, time, urllib.request, urllib.error, mimetypes, uuid
from pathlib import Path

BASE = "http://localhost:8001"

COURSES = [
    {"title": "Kubernetes for ML Workloads (v2)",
     "description": "Deploy and operate ML workloads on K8s. Drill incidents: GPU starvation, OOMKilled pods, stuck PVCs, spot-instance evictions. Capstone: live K8s incident drill with kubectl shell. Budget-conscious GPU node-pool design exercise.",
     "course_type": "technical"},
    {"title": "Statistical Analysis for Product Decisions (v2)",
     "description": "Real A/B test analysis under pressure. Learners run queries against a dirty dataset with planted biases (SRM, Simpson's paradox, selection bias). Must defend a launch decision against a CFO who asks hard questions. Uses incident_console for the data-spelunking drill and adaptive_roleplay for the CFO defense.",
     "course_type": "technical"},
    {"title": "TCS ILP Fresher Onboarding (v2)",
     "description": "Complete TCS ILP coverage with FRESHER-REALITY. Cover ASPIRE pre-joining, 60-day ILP rhythm, bench/bond/allocation pressures, iEvolve/Ultimatix/RMG, standup culture, client etiquette. NOT Fortune-500 contract crises. Capstone: adaptive_roleplay with a TCS RMG allocator.",
     "course_type": "case_study"},
    {"title": "Infosys Mysore Foundation Program (v2)",
     "description": "23-week GEC Mysore foundation program. Cover Lex, Stream allocation, Milestone Tests, 9am-5pm rhythm, dorm life, Design Thinking 5-day sprint. Capstone: adaptive_roleplay with a Milestone Test panelist.",
     "course_type": "case_study"},
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:400]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def regen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}/4] {spec['title']}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", spec)
    if status != 200:
        print(f"  [{idx+1}/4] start failed: {start}", flush=True); return None
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Use adaptive_roleplay or incident_console for capstone. Real domain specifics (names, tools, numbers) not generic filler."} for q in start.get("questions", [])[:4]]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}/4] refine failed: {refine}", flush=True); return None
    types = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]: types.add(s.get("exercise_type", s.get("type")))
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}/4] generate failed: {g}", flush=True); return None
    uses_new = bool(types & {"adaptive_roleplay","incident_console","simulator_loop"})
    flag = "[NEW]" if uses_new else "[trad]"
    print(f"  [{idx+1}/4] {flag} OK {g.get('course_id')} ({time.time()-t0:.0f}s)", flush=True)
    return {"title": spec["title"], "course_id": g.get("course_id"), "types": sorted(types), "uses_new": uses_new}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(2)
    async def bounded(s, i):
        async with sem: return await regen(s, i)
    results = await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception: pass
    print("\n=== Regen results ===", flush=True)
    uses_new = sum(1 for r in results if r and r["uses_new"])
    print(f"{uses_new}/{sum(1 for r in results if r)} used new pedagogies", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
