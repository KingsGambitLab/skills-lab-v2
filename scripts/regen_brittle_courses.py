"""Regenerate the 4 courses that showed brittle personas in the scoring-consistency test.
The Creator-prompt + _is_complete guardrails added 2026-04-19 should produce non-brittle
personas in every new generation. This is the universal-fix validation: a single Creator
fix should repair every affected course, not just the one reviewed.
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "AI for Sales Engineers: From Discovery to Technical Close v2",
        "description": (
            "For Sales Engineers and Solutions Consultants. Use LLMs to synthesize discovery "
            "calls into technical requirements, auto-generate RFP responses from playbook, and "
            "simulate live technical deep-dives with CTOs who ask hostile questions. Capstone: "
            "adaptive_roleplay — you're in a final technical eval with a skeptical CTO who's "
            "already tried 2 competitors. Persona STARTS with patience/trust/flexibility >= 5, "
            "escalation at <= 0 only, gives 5+ turns of grace before walking. Rubric tags: "
            "discovery_questions, value_framing, objection_reframe, close_specificity."
        ),
        "course_type": "case_study",
        "answers": [
            "Sales Engineers, Solutions Consultants, Technical Account Managers",
            "Claude API for call synthesis; Python for RFP auto-response; POC plan generation",
            "Capstone: adaptive_roleplay with skeptical CTO; persona starts positive dims >= 5, escalation only at <= 0",
        ],
    },
    {
        "title": "AI for Technical Writers: Docs that Actually Get Read v2",
        "description": (
            "For Technical Writers and Developer Advocates. Use LLMs to audit existing docs "
            "for clarity gaps, generate code samples that compile, and personalize docs for "
            "different personas. Capstone: adaptive_roleplay — a principal engineer reviewer "
            "says your doc is 'too hand-holdy' and wants it cut in half. Persona has hidden "
            "state (trust, patience, flexibility) starting >= 5 each. Escalation only at <= 0. "
            "Rubric tags: specificity_of_feedback, emotional_regulation, separating_behavior_from_person, accountability_ask."
        ),
        "course_type": "case_study",
        "answers": [
            "Technical Writers, Developer Advocates, Documentation Leads",
            "Claude API for doc review; pytest-driven code sample validation",
            "Capstone: adaptive_roleplay with principal engineer reviewer; persona starts >= 5 on positive dims, escalates only at <= 0",
        ],
    },
    {
        "title": "AI for Mobile Engineers: Crash-Free Releases at Scale v2",
        "description": (
            "For iOS and Android engineers. Use LLMs to diagnose Crashlytics reports, "
            "auto-generate release notes, and review PRs for platform-specific pitfalls. "
            "Capstone: incident_console — your app is crashing on iOS 18 after a library "
            "update, 5-star reviews tanking in real-time, a VP demands a rollback and App "
            "Review won't approve the new build for 48 hours. ALSO has adaptive_roleplay "
            "with VP — persona starts patience/trust/flexibility >= 5, escalation at <= 0, "
            "gives 5+ grace turns. Rubric tags: precision_under_pressure, hedging_discipline, "
            "ETA_accuracy, data_specificity."
        ),
        "course_type": "technical",
        "answers": [
            "iOS engineers, Android engineers, Mobile Tech Leads",
            "Claude API for crash-log clustering; scripted incident console for the drill",
            "Capstone: incident_console + adaptive_roleplay (persona starts >= 5, escalates only at <= 0)",
        ],
    },
    {
        "title": "AI for Staff PMs: Strategy Docs to Org-Wide Alignment v2",
        "description": (
            "For Staff and Principal PMs. Use LLMs to stress-test strategy memos, surface "
            "hidden assumptions, and red-team your own org-wide proposals. Capstone: "
            "adaptive_roleplay — you're presenting to a skeptical CEO who has already read 2 "
            "competing strategy memos from peer PMs. 15 turns, high-stakes. CEO persona "
            "STARTS with patience/trust/openness >= 5. Escalation only at <= 0. Gives 5+ "
            "grace turns before walking. Rubric tags: anchoring, BATNA, data_specificity, "
            "emotional_regulation, genuine_vulnerability."
        ),
        "course_type": "case_study",
        "answers": [
            "Staff PMs, Principal PMs, Group PMs",
            "Claude API for memo stress-testing, red-teaming, assumption surfacing",
            "Capstone: adaptive_roleplay with CEO; persona starts >= 5 on positive dims, escalates only at <= 0, 15-turn limit",
        ],
    },
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:400]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def gen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}] {spec['title'][:60]}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", {"title": spec["title"], "description": spec["description"], "course_type": spec["course_type"]})
    if status != 200: print(f"  [{idx+1}] start failed: {start}"); return None
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": spec["answers"][i] if i < len(spec["answers"]) else "Use adaptive_roleplay."} for i, q in enumerate(start.get("questions", [])[:4])]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200: print(f"  [{idx+1}] refine failed: {refine}"); return None
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200: print(f"  [{idx+1}] generate failed: {g}"); return None
    cid = g.get('course_id')

    # Inspect persona guardrails
    d = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}").read())
    persona_info = []
    for m in d["modules"]:
        mod = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}").read())
        for s in mod["steps"]:
            if s.get("exercise_type") == "adaptive_roleplay":
                dd = s.get("demo_data", {})
                cp = dd.get("counterparty", {})
                hs = cp.get("hidden_state", {})
                esc = cp.get("escalation_triggers", [])
                persona_info.append(f"hidden={hs} esc={[t.get('condition') for t in esc]}")
    print(f"  [{idx+1}] OK {cid} ({time.time()-t0:.0f}s) — {'; '.join(persona_info) if persona_info else 'no-roleplay'}", flush=True)
    return cid


async def main():
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    sem = asyncio.Semaphore(3)
    async def bounded(s, i):
        async with sem: return await gen(s, i)
    results = await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    print(f"New IDs: {results}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
