"""Replay same Wave 3 courses with a SOFTER, more empathetic strategy.
Expect: different outcomes — concedes in feedback/trust contexts where directness shut things down.
"""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"

TARGETS = [
    "created-8aa86a79cade",  # VC pitching
    "created-adfdf1fc239a",  # Salary negotiation
    "created-27a8122455da",  # Code review
    "created-6cc7d0e7226a",  # Customer support
    "created-1e8c0841820c",  # Tech lead office hours
    "created-f7ff70596bfa",  # Enterprise architect
]

# Softer, empathetic, curious turns — build trust before pushing
EMPATHETIC = [
    "I really appreciate you taking the time. Before I react — help me understand what's most important to you here.",
    "That makes sense. It sounds like [reflection of their concern]. What would ideally happen from your point of view?",
    "Thank you for being direct. I hear [specific thing they said] and I want to honor that. Would you be open to exploring [gentle suggestion] together?",
    "That's fair. Let me share where I'm coming from too, so we're both on the same page: [genuine vulnerability]. What's your reaction to that?",
    "I'd really value your thinking on this. What would make this a clear win for both of us?",
]


def _post(path, body, timeout=120):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except Exception as e: return -1, {"error": str(e)[:150]}


def find_step(cid):
    try:
        d = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}").read())
        for m in d["modules"]:
            mod = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}").read())
            for s in mod["steps"]:
                if s.get("exercise_type") == "adaptive_roleplay":
                    return s["id"], s["title"], d["title"]
    except Exception: pass
    return None, None, None


async def play(cid, idx):
    step_id, step_title, course_title = find_step(cid)
    if not step_id:
        print(f"  [{idx+1}] no roleplay step", flush=True); return None
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200:
        print(f"  [{idx+1}] start failed", flush=True); return None
    sid = start["session_id"]
    outcome = "continue"
    resp = None
    for turn in EMPATHETIC:
        if outcome != "continue": break
        status, resp = await asyncio.to_thread(_post, "/api/roleplay/turn", {"session_id": sid, "message": turn})
        if status != 200: break
        outcome = resp.get("outcome", "continue")
    score = (resp.get("debrief") or {}).get("score") if resp and outcome != "continue" else None
    print(f"  [{idx+1}] {course_title[:45]}: outcome={outcome} score={score} turns={resp.get('turn','?') if resp else '?'}", flush=True)
    return {"cid": cid, "outcome": outcome, "score": score}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(3)
    async def bounded(cid, i):
        async with sem: return await play(cid, i)
    results = await asyncio.gather(*[bounded(cid, i) for i, cid in enumerate(TARGETS)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    outcomes = {}
    for r in results:
        if r: outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    print(f"Outcomes: {outcomes}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
