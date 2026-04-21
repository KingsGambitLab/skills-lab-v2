"""Run FULL adaptive_roleplay sessions (up to 15 turns each) on several new function courses.
Each session: 10-15 turns = $0.15-0.30. 6 courses = ~$1.50.
Plus a bigger Clicky burn on function-specific questions.
"""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"

TARGETS = [
    ("created-288a62e7c76f", "Finance Close"),
    ("created-b7e20905a0f9", "Finance Forecasting"),
    ("created-470bc8ea6764", "Recruitment AI"),
    ("created-1082a1d682a4", "Product PM Discovery"),
    ("created-c8d1159a7f0f", "Design AI Research"),
    ("created-73c2e08e7262", "HRBP"),
    ("created-89f1694bef4c", "Legal Counsel"),
    ("created-a960b2c335c1", "Marketing Leader"),
    ("created-afc141eb0fe8", "CS Leader"),
    ("created-c4c529c6bbc4", "Exec decision making"),
]

# 15 well-crafted turns that mix empathy and data
TURNS = [
    "Thanks for taking the time. I want to understand your situation before reacting. What's the most important outcome for you here?",
    "That's helpful context. Let me reflect back: it sounds like [the goal] but with [constraint]. Am I hearing that right?",
    "Okay. Here's the data I've looked at: [specific insight]. Does that change anything?",
    "I appreciate your push-back. Let me be honest about my own concerns: [genuine vulnerability].",
    "What if we tried [concrete proposal with measurable first step]? What would need to be true for you to try that?",
    "That's a great point about [their objection]. I hadn't weighted it enough. How would you address it?",
    "Let me propose a scoped experiment: [specific action by specific date]. Success criteria: [measurable outcome].",
    "I want to be accountable. What milestone would tell you we're on track — or off track?",
    "I hear [their concern]. Here's my honest reaction: [genuine response, not defensive].",
    "Can we align on what we both agree on first? I think we share [common ground]. Is that fair?",
    "What data would change your mind? I want to know what evidence would actually settle this.",
    "Let me commit specifically: I'll [concrete deliverable] by [date]. You'll [review/decide] by [checkpoint]. Workable?",
    "I'm noticing we keep circling. What's really at stake for you here that I might be missing?",
    "I want to propose we end this meeting with a clear next step. What do you need from me to make that possible?",
    "Final thought: I'd rather have honest disagreement than false alignment. Where do you genuinely still disagree?",
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


async def play_full(cid, label, idx):
    step_id = find_step(cid)
    if not step_id:
        print(f"  [{idx+1}] {label}: no roleplay", flush=True); return None
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200:
        print(f"  [{idx+1}] {label}: start failed", flush=True); return None
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
    sem = asyncio.Semaphore(3)
    async def bounded(cid, label, i):
        async with sem: return await play_full(cid, label, i)
    results = await asyncio.gather(*[bounded(cid, label, i) for i, (cid, label) in enumerate(TARGETS)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    outcomes = {}
    total_turns = 0
    for r in results:
        if r:
            outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
            total_turns += r["turns"]
    print(f"Outcomes: {outcomes}", flush=True)
    print(f"Total turns: {total_turns}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
