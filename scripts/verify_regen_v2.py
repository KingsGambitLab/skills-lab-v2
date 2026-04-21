"""Verify the 4 newly-regenerated v2 courses show a meaningful STRONG-vs-WEAK gap."""
import asyncio, json, urllib.request

BASE = "http://localhost:8001"

V2_COURSES = [
    ("created-c19709409dc8", "Sales Engineer v2"),
    ("created-5d3ebd615077", "Tech Writer v2"),
    ("created-846fc28df28d", "Mobile Eng v2"),
    ("created-21ecc4af0903", "Staff PM v2"),
    ("created-ee56d7f41c3d", "Data Analyst v2"),
]

STRONG = [
    "Thanks for the time. Before I push: what's the one outcome that would make this a clear win for you — the date, the scope, or the ability to communicate confidence to YOUR stakeholder?",
    "Here's my honest data: the hard version of this ships in 10 weeks at 90% confidence. I have a phased alt — phase 1 (the revenue/headline-risk slice) in 4 weeks with a week-2 checkpoint, phase 2 decided jointly at week 4. Weekly exec updates. Would you explore that shape?",
    "I want to be transparent about my constraint: I'm 92% confident on phase 1, 70% on phase 2. My team has 2 senior people; 10-week crunch burns them out and we lose 2 quarters of velocity. Which risk reduces YOUR stakeholder-facing exposure more — phased or an incident at the critical moment?",
    "Concrete commit: Friday week 4 phase-1 ship with Wednesday week 2 hard gate. If I miss the gate, I escalate immediately to you. Weekly exec updates. Joint scope decision at week 4 for phase 2. Does that give you enough to take back?",
    "One more thing: my BATNA if we can't align is a 1-week estimate spike before any commitment. Not ideal, but it prevents premature promise. I'd rather do that than commit to something I don't believe in. What would make phased the yes?",
    "To close: 4-week phase 1 with checkpoints, joint phase-2 decision, weekly updates. You get revenue unlocked faster, team intact, and a defensible story. Is that a yes?",
]

WEAK = [
    "Look, this is impossible. You don't get it.",
    "We'll see. Things might change.",
    "Why pressure my team like this? They'll quit.",
    "Fine, whatever. We'll try.",
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
    score = (resp.get("debrief") or {}).get("score") if resp and outcome != "continue" else None
    return outcome, score


async def evaluate(cid, label, idx):
    step_id = find_step(cid)
    if not step_id:
        print(f"  [{idx+1}] {label}: no roleplay", flush=True); return None
    so, sscore = await play(step_id, STRONG)
    wo, wscore = await play(step_id, WEAK)
    gap = None
    if sscore is not None and wscore is not None:
        gap = sscore - wscore
    status = ""
    if sscore is None: status += " STRONG-cont "
    if wscore is None: status += " WEAK-cont "
    if gap is not None and gap >= 0.3: status += "  ✓GOOD-GAP"
    elif gap is not None: status += "  ⚠SMALL-GAP"
    print(f"  [{idx+1}] {label:22}  STRONG={so}/{sscore}  WEAK={wo}/{wscore}  gap={gap}{status}", flush=True)
    return {"label": label, "sscore": sscore, "wscore": wscore, "gap": gap, "so": so, "wo": wo}


async def main():
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    sem = asyncio.Semaphore(3)
    async def bounded(cid, label, i):
        async with sem: return await evaluate(cid, label, i)
    results = await asyncio.gather(*[bounded(cid, label, i) for i, (cid, label) in enumerate(V2_COURSES)])
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    completed_gaps = [r["gap"] for r in results if r and r["gap"] is not None]
    weak_scores = [r["wscore"] for r in results if r and r["wscore"] is not None]
    print(f"\nSummary:")
    print(f"  WEAK outcomes correctly escalate: {sum(1 for r in results if r and r.get('wscore') and r['wscore'] < 0.2)}/{len(results)}")
    if completed_gaps:
        print(f"  Courses with completed STRONG+WEAK: {len(completed_gaps)}, avg gap={sum(completed_gaps)/len(completed_gaps):.2f}")


if __name__ == "__main__":
    asyncio.run(main())
