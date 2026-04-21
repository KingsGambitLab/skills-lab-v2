"""15-turn empathetic roleplay against the regen'd + new tech-function courses — burn to $30+."""
import asyncio, json, urllib.request

BASE = "http://localhost:8001"

TARGETS = [
    # Regen'd seeds (via Creator)
    ("created-b5bf83e516b0", "Regen: Scope Defense"),
    ("created-3604bb66d5df", "Regen: SRE Pager"),
    # Tech-function wave
    ("created-5ab75bbb8414", "Sales Engineer"),
    ("created-e4f8931af85c", "Data Analyst"),
    ("created-f16e2ef7af0f", "Tech Writer"),
    ("created-58acb17bf345", "DevOps"),
    ("created-f1b3a90c7cfe", "Security Eng"),
]

TURNS = [
    "Thanks for taking this time. Before I push back — help me understand what matters most to you here.",
    "That's helpful context. Let me reflect: it sounds like [their concern]. Am I hearing that right?",
    "Here's my honest data: [specific evidence]. How does that change your read?",
    "I want to be transparent about my constraints too: [genuine vulnerability]. What's your reaction?",
    "Let me propose a scoped alternative: [specific action, specific metric, specific date]. Would you explore it?",
    "What data or evidence would actually shift your position? I want to know what would settle this for you.",
    "I hear your urgency. Can I commit to [deliverable] by [date] with a checkpoint at [milestone]? You decide next.",
    "Where do we genuinely still disagree? I'd rather name it than pretend alignment.",
    "If we tried my proposal and it failed at the 2-week mark, what's our joint rollback plan?",
    "Let me land this: what's the one thing I can do in the next 48 hours that would move us forward?",
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
                    return s["id"]
    except Exception: pass
    return None


async def play(cid, label, idx):
    step_id = find_step(cid)
    if not step_id:
        print(f"  [{idx+1}] {label}: no roleplay", flush=True); return None
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200:
        print(f"  [{idx+1}] {label}: start failed", flush=True); return None
    sid = start["session_id"]
    resp = None
    outcome = "continue"
    turns = 0
    for t in TURNS:
        if outcome != "continue": break
        turns += 1
        status, resp = await asyncio.to_thread(_post, "/api/roleplay/turn", {"session_id": sid, "message": t})
        if status != 200: break
        outcome = resp.get("outcome", "continue")
    score = (resp.get("debrief") or {}).get("score") if resp and outcome != "continue" else None
    print(f"  [{idx+1}] {label}: outcome={outcome} score={score} turns={turns}", flush=True)
    return {"label": label, "outcome": outcome, "turns": turns}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(4)
    async def bounded(cid, label, i):
        async with sem: return await play(cid, label, i)
    results = await asyncio.gather(*[bounded(cid, label, i) for i, (cid, label) in enumerate(TARGETS)])
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
