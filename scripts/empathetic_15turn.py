"""Empathetic 15-turn roleplay across function courses.
Expectation: more concedes, healthier conversations, more budget burn (~$2).
"""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"

TARGETS = [
    ("created-288a62e7c76f", "Finance Close"),
    ("created-b7e20905a0f9", "Finance Forecasting"),
    ("created-470bc8ea6764", "Recruitment"),
    ("created-1082a1d682a4", "Product Discovery"),
    ("created-c8d1159a7f0f", "Design AI"),
    ("created-73c2e08e7262", "HRBP"),
    ("created-89f1694bef4c", "Legal"),
    ("created-a960b2c335c1", "Marketing"),
    ("created-afc141eb0fe8", "CS Leader"),
    ("created-c4c529c6bbc4", "Exec Decision"),
]

# 15 empathetic + curious turns
TURNS = [
    "Thanks for this time. Before I say anything — what outcome would feel like a real win for you?",
    "I hear you. It sounds like [reflect]. Is that right, or did I miss something?",
    "That makes sense. I want to honor that. Help me understand what's driving the urgency.",
    "That's really helpful. Let me share my honest concern too: [vulnerability]. How does that land?",
    "You raise a fair point. What data or evidence would make this easier for you?",
    "I'd rather get this right than move fast. Can we take the hardest version of your question first?",
    "I really appreciate you pushing back. Where are we actually disagreeing — is it the goal, the method, or the timing?",
    "Let me propose small: what if we tried [tiny specific step] this week and reconvened with data?",
    "I hear [their deepest concern]. Here's how I'd mitigate it specifically: [specific mitigation].",
    "You know this domain better than I do on [topic]. What would you do if you were in my seat?",
    "I want to be accountable to you. What milestone would tell us we're on track?",
    "Can I commit to a specific deliverable by a specific date? I'll [X] by [Y]; you decide [Z] after that.",
    "What am I missing? I'd rather hear it now than after we've committed.",
    "Let's land this conversation with a clear next step. What would you like me to do in the next 48 hours?",
    "Last check: if this fails, what's our joint plan for catching it early?",
]


def _post(path, body, timeout=120):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except Exception as e: return -1, {"error": str(e)[:100]}


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
    if not step_id: return None
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200: return None
    sid = start["session_id"]
    resp = None
    outcome = "continue"
    turns_used = 0
    for turn in TURNS:
        if outcome != "continue": break
        turns_used += 1
        status, resp = await asyncio.to_thread(_post, "/api/roleplay/turn", {"session_id": sid, "message": turn})
        if status != 200: break
        outcome = resp.get("outcome", "continue")
    score = (resp.get("debrief") or {}).get("score") if resp and outcome != "continue" else None
    print(f"  [{idx+1}] {label}: outcome={outcome} score={score} turns={turns_used}", flush=True)
    return {"label": label, "outcome": outcome, "score": score, "turns": turns_used}


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
    total = 0
    for r in results:
        if r:
            outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
            total += r["turns"]
    print(f"Outcomes: {outcomes}", flush=True)
    print(f"Total turns: {total}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
