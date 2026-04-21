"""Regenerate the two originally-direct-DB-seeded immersive courses via the Creator API only.

Goal: prove the Creator can produce quality adaptive_roleplay + incident_console
content from prose descriptions alone — no seed scripts, no direct DB writes.
This is the compliance test for the 'all courses via Creator dashboard' invariant.
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {
        # Replaces roleplay-negotiation-vp (originally seeded via direct SQLAlchemy)
        "title": "Defending Scope Under Executive Pressure",
        "description": (
            "For tech leads and senior ICs. You've just been told by a VP that a 6-week "
            "scope must ship in 3 weeks because a customer threatened churn. You must "
            "push back without getting branded 'unhelpful.' Capstone: an adaptive_roleplay "
            "with a VP named Diana who has hidden state (patience, trust, flexibility). "
            "Her tone and position shift based on your actual words — data, vulnerability, "
            "alternatives win; hedging, combativeness, or over-promising lose. "
            "Grade on state trajectory across 15 turns, not a final multiple-choice answer. "
            "No MCQ. Type real words. Live chat with an AI counterparty that remembers."
        ),
        "course_type": "case_study",
        "answers": [
            "Senior engineers, tech leads, staff engineers, engineering managers",
            "Claude API drives the VP persona with hidden state (patience/trust/flexibility). No external tools required.",
            "Capstone: adaptive_roleplay — VP Diana pressures on scope; scoring on state trajectory & BATNA/anchoring/emotional regulation",
        ],
    },
    {
        # Replaces sre-3am-pager (originally seeded via direct SQLAlchemy)
        "title": "Live SRE Drill: 3AM Payments Outage",
        "description": (
            "For SREs and senior backend engineers. Your pager fires at 3:42 AM. "
            "Payments API is in CrashLoopBackOff. 47% error rate. $2K/min bleeding. "
            "Three teams are in the Slack thread. You have ten minutes to find root "
            "cause, stop the bleed, and communicate clearly — before the CEO gets woken. "
            "Capstone: incident_console — you type real kubectl commands, logs stream "
            "live, Slack pings escalate, and destructive commands have cascade effects. "
            "Grade on time-to-resolution, correct root-cause hypothesis, minimum-viable "
            "fix, and Slack response latency. Zero LLM cost per session — scripted engine."
        ),
        "course_type": "technical",
        "answers": [
            "SREs, senior backend engineers, platform engineers, on-call rotations",
            "Pure scripted simulation — no LLM at runtime. kubectl command parser, regex-gated log stream, cascade rules for destructive commands.",
            "Capstone: incident_console — 3AM payments CrashLoopBackOff with Slack escalation & revenue-per-min bleeding",
        ],
    },
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:500]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def gen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}] {spec['title'][:60]}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", {"title": spec["title"], "description": spec["description"], "course_type": spec["course_type"]})
    if status != 200:
        print(f"  [{idx+1}] start failed: {start}", flush=True); return None
    sid = start["session_id"]
    answers = []
    for i, q in enumerate(start.get("questions", [])[:4]):
        ans = spec["answers"][i] if i < len(spec["answers"]) else "Use adaptive_roleplay / incident_console for immersion."
        answers.append({"question_id": q["id"], "answer": ans})
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}] refine failed: {refine}", flush=True); return None
    types = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]: types.add(s.get("exercise_type", s.get("type")))
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}] generate failed: {g}", flush=True); return None
    new_types = sorted(types & {"adaptive_roleplay","incident_console","simulator_loop"})
    print(f"  [{idx+1}] OK {g.get('course_id')} ({time.time()-t0:.0f}s) — new: {new_types}", flush=True)
    return g.get('course_id')


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(2)
    async def bounded(s, i):
        async with sem: return await gen(s, i)
    results = await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    print(f"New course IDs: {results}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
