"""Run adaptive_roleplay sessions against MULTIPLE new courses to validate at scale.

Each session: 3-5 turns. Cost per session: ~$0.02.
6 courses × 4 turns avg = 24 turns = ~$0.50-1.00
"""
import asyncio, json, time, urllib.request

BASE = "http://localhost:8001"

# Pick adaptive_roleplay steps from different courses
COURSES_TO_TEST = [
    "created-fb0ba2b5ce45",  # Sales B2B
    "created-3f22cc6eabc5",  # EM First 90 Days
    "created-dda09269e113",  # Customer Success
    "created-f7af957302f6",  # Hiring Senior
    "created-816745fc5bba",  # PM Scope Neg
    "created-aaff632f747d",  # Postgres Ops
    "created-c5aebbdd9cf2",  # ML Ops
    "created-beec755dc001",  # Eng Leadership Under Outage
]

# 3 strong-strategy turns per session
GOOD_TURNS = [
    "Before I answer — help me understand the constraints you're under. Timeline, resources, stakeholders I should know about?",
    "Here's what I'm seeing: [specific observation]. What would change in your outcome if [specific alternative]?",
    "Let me propose something concrete: [phased plan with measurable first step]. What's missing that would make you comfortable committing?",
]


def _post(path, body, timeout=120):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except Exception as e: return -1, {"error": str(e)[:200]}


def find_roleplay_step(cid):
    try:
        d = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}").read())
        for m in d["modules"]:
            mod = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}").read())
            for s in mod["steps"]:
                if s.get("exercise_type") == "adaptive_roleplay":
                    return s["id"], s["title"]
    except Exception: pass
    return None, None


async def test_course(cid, idx):
    step_id, step_title = find_roleplay_step(cid)
    if not step_id:
        print(f"  [{idx+1}] {cid}: no roleplay step found", flush=True)
        return None
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200:
        print(f"  [{idx+1}] {cid}: start failed {start}", flush=True)
        return None
    sid = start["session_id"]
    print(f"  [{idx+1}] {cid}: '{step_title[:45]}' — scenario: {start.get('scenario','')[:80]}", flush=True)
    outcome = "continue"
    for turn_msg in GOOD_TURNS:
        if outcome != "continue": break
        status, resp = await asyncio.to_thread(_post, "/api/roleplay/turn", {"session_id": sid, "message": turn_msg})
        if status != 200:
            print(f"  [{idx+1}] turn failed: {resp}", flush=True); break
        outcome = resp.get("outcome", "continue")
    score = (resp.get("debrief") or {}).get("score") if outcome != "continue" else None
    print(f"  [{idx+1}] {cid}: outcome={outcome} score={score}", flush=True)
    return {"cid": cid, "outcome": outcome, "score": score}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(3)
    async def bounded(cid, i):
        async with sem: return await test_course(cid, i)
    results = await asyncio.gather(*[bounded(cid, i) for i, cid in enumerate(COURSES_TO_TEST)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    outcomes = {}
    for r in results:
        if r: outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    print(f"\nOutcome distribution: {outcomes}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
