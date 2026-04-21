"""Playthrough of adaptive_roleplay steps in Wave 3 courses (5 turns each)."""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"

# Wave 3 courses with adaptive_roleplay
TARGETS = [
    "created-8aa86a79cade",  # VC pitching
    "created-adfdf1fc239a",  # Salary negotiation
    "created-27a8122455da",  # Code review conversations
    "created-6cc7d0e7226a",  # Customer support under scrutiny
    "created-1e8c0841820c",  # Tech lead office hours
    "created-f7ff70596bfa",  # Enterprise architect review
]

# Strong-strategy 5 turns — applicable across domains
STRONG = [
    "Let me understand the full picture first. What outcome would make this a clear win for you?",
    "Here's the tradeoff I'm seeing: [specific observation about the tension]. What am I missing?",
    "Let me propose something concrete: [specific next step with measurable criteria]. What would make you comfortable committing?",
    "I hear the concern about [X]. Here's what I'd do to mitigate it: [specific mitigation]. Does that change the calculus?",
    "Let's align on what 'done' looks like. I commit to [specific deliverable by date]; you review by [specific checkpoint]. Deal?",
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
        print(f"  [{idx+1}] {cid}: no roleplay step", flush=True); return None
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200:
        print(f"  [{idx+1}] start failed", flush=True); return None
    sid = start["session_id"]
    outcome = "continue"
    resp = None
    for turn in STRONG:
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
