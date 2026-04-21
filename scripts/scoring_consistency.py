"""Validate that the fixed scorer produces a consistent STRONG-vs-WEAK gap across many courses.

Expect strong strategy → score >= 0.7 (usually a win outcome), weak → score <= 0.3 (usually lose).
If any course produces inconsistent gaps, that surfaces new bugs (e.g. win_conditions too hard).
"""
import asyncio, json, urllib.request

BASE = "http://localhost:8001"

TARGETS = [
    ("created-101ba7848a1f", "Negotiation v2"),
    ("created-b5bf83e516b0", "Scope Defense (v1)"),
    ("created-5ab75bbb8414", "Sales Engineer"),
    ("created-e4f8931af85c", "Data Analyst"),
    ("created-f16e2ef7af0f", "Tech Writer"),
    ("created-c382a970e013", "Mobile Eng"),
    ("created-721bcb63fc94", "Eng Manager"),
    ("created-a489de3133a7", "Staff PM"),
]

STRONG = [
    "Thanks for meeting. Before I react: what outcome matters most to you — the revenue number, the board-facing date, or reducing engineering risk? I want to anchor on that first.",
    "Here's my honest data: our last 4 comparable pushes had 80% Sev1 rate at this timeline. I have a phased option — phase 1 (the revenue-critical slice) by week 3, phase 2 decided jointly at week 3 based on what we learn. Weekly exec updates. Would you explore it?",
    "I want to be transparent: I'm 95% confident on phase 1, 70% on phase 2. My 2 senior engineers burn out at 3-week-everything — and if they quit we lose 2 quarters of velocity. Which risk reduces YOUR board-facing exposure more — a phased ship OR a Sev1 at the moment we need revenue?",
    "Concrete commit: Friday of week 3 phase-1 ship, hard gate Wednesday of week 2. If I miss the gate, I escalate immediately to you. Weekly exec updates, joint scope decision at week 3 for phase 2. Is that a yes?",
]

WEAK = [
    "Look, this is just impossible. You don't understand our constraints.",
    "We'll try. We'll see what happens. I can't promise anything.",
    "Why are you pushing so hard? My team will quit.",
    "Fine, we'll commit. Whatever you want.",
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


async def play(step_id, turns):
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200: return None, None
    sid = start["session_id"]
    outcome = "continue"; resp = None
    for t in turns:
        if outcome != "continue": break
        status, resp = await asyncio.to_thread(_post, "/api/roleplay/turn", {"session_id": sid, "message": t})
        if status != 200: break
        outcome = resp.get("outcome", "continue")
    if resp and outcome != "continue":
        db = resp.get("debrief") or {}
        return outcome, db.get("score")
    return outcome, None


async def evaluate(cid, label, idx):
    step_id = find_step(cid)
    if not step_id: return None
    so, sscore = await play(step_id, STRONG)
    wo, wscore = await play(step_id, WEAK)
    gap = (sscore or 0) - (wscore or 0) if (sscore is not None and wscore is not None) else None
    flag = ""
    if sscore is not None and wscore is not None:
        if gap < 0.3: flag = "  [WEAK-GAP]"
        if sscore < 0.5: flag += "  [WIN-TOO-LOW]"
        if wscore > 0.3: flag += "  [LOSE-TOO-HIGH]"
    print(f"  [{idx+1}] {label:22}  STRONG={so}/{sscore}  WEAK={wo}/{wscore}  gap={gap}{flag}", flush=True)
    return {"label": label, "strong_score": sscore, "weak_score": wscore, "gap": gap, "strong_outcome": so, "weak_outcome": wo}


async def main():
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    sem = asyncio.Semaphore(3)
    async def bounded(cid, label, i):
        async with sem: return await evaluate(cid, label, i)
    results = await asyncio.gather(*[bounded(cid, label, i) for i, (cid, label) in enumerate(TARGETS)])
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    # Summary
    gaps = [r["gap"] for r in results if r and r["gap"] is not None]
    if gaps:
        print(f"\nSUMMARY: {len(gaps)} courses scored, avg gap={sum(gaps)/len(gaps):.2f}, min={min(gaps):.2f}, max={max(gaps):.2f}")
        if all(g >= 0.3 for g in gaps):
            print("ALL COURSES PRODUCE A MEANINGFUL PEDAGOGICAL GAP (>= 0.3). Scoring fix is consistent.")
        else:
            weak_courses = [r['label'] for r in results if r and r['gap'] is not None and r['gap'] < 0.3]
            print(f"INCONSISTENT: courses with gap < 0.3: {weak_courses}")


if __name__ == "__main__":
    asyncio.run(main())
