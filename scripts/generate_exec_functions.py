"""More function-focused AI upskilling — HR, Legal, Marketing, Ops, Customer Success leaders, Executive."""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "AI for HR Business Partners: From Headcount Planning to Exit Interviews",
        "description": (
            "For HRBPs. Use LLMs to draft JD/role scorecards, synthesize exit interview themes, "
            "detect attrition signals in engagement survey data, and prep for difficult performance "
            "conversations. Practice adaptive_roleplay with a manager who wants to PIP an employee "
            "without documentation. Capstone: live defense of a skip-level request escalation."
        ),
        "course_type": "case_study",
        "answers": [
            "HR Business Partners, People Managers",
            "Claude API for text synthesis + pandas for engagement signal detection",
            "Capstone: adaptive_roleplay with a manager defending a weakly-documented PIP",
        ],
    },
    {
        "title": "AI for Legal Counsel: Contract Review and Risk Triage",
        "description": (
            "For in-house counsel and paralegals. Practical LLM workflows: red-line a 40-page "
            "contract against your playbook, extract key terms into a structured table, spot "
            "liability clauses that deviate from standard. Hands-on with real-looking SaaS MSA. "
            "Adaptive_roleplay with a sales counterparty pushing to accept non-standard terms."
        ),
        "course_type": "compliance",
        "answers": [
            "In-house legal counsel, paralegals, contract managers",
            "Claude API for contract review. Emphasize bias-awareness in LLM-extracted claims.",
            "Capstone: adaptive_roleplay with sales VP pushing on liability cap",
        ],
    },
    {
        "title": "AI for Marketing Leaders: Campaign Strategy to Attribution",
        "description": (
            "For marketing directors and growth leads. Use LLMs to synthesize campaign post-mortems, "
            "generate A/B test variant copy at scale, and debug attribution reports. Hands-on: "
            "feed 3 months of campaign data to Claude, identify which channels actually drove "
            "pipeline. Capstone: roleplay defending your attribution model to a CFO who "
            "questions every dollar."
        ),
        "course_type": "case_study",
        "answers": [
            "Marketing Directors, Growth Leads, Demand Gen managers",
            "Python + pandas for campaign data, Claude API for synthesis",
            "Capstone: adaptive_roleplay with CFO grilling attribution model",
        ],
    },
    {
        "title": "AI for Operations: Supply Chain + Service Delivery",
        "description": (
            "For Ops and Service Delivery leaders. Use LLMs to auto-classify support tickets, "
            "predict SLA-breach risk, and generate customer status emails. Hands-on with "
            "a simulated 10K-ticket queue. Capstone: live incident_console drill — your "
            "ops system is drowning in 2AM SEV-2 tickets, auto-triage is flaky, customers "
            "are escalating."
        ),
        "course_type": "technical",
        "answers": [
            "Ops leaders, service delivery managers, support leads",
            "Python + pandas + LLM for classification. Use a realistic 10K-ticket simulation.",
            "Capstone: incident_console drill for ticket-queue meltdown",
        ],
    },
    {
        "title": "AI for Customer Success Leaders: Portfolio Health Management",
        "description": (
            "For CS managers and Directors. Use LLMs to synthesize 50 customer calls into "
            "churn-risk signals, draft QBR decks, and coach CSMs through tough renewals. "
            "Hands-on: feed 10 Gong/Chorus-style transcripts to Claude, extract churn-risk "
            "indicators. Capstone: adaptive_roleplay coaching a CSM who has a renewal call "
            "tomorrow and is unprepared."
        ),
        "course_type": "case_study",
        "answers": [
            "CS Managers, CS Directors, Revenue Ops",
            "Claude API for call-transcript synthesis; pandas for portfolio risk scoring",
            "Capstone: adaptive_roleplay coaching session with panicked CSM",
        ],
    },
    {
        "title": "AI for Executives: Making Decisions with Noisy Data",
        "description": (
            "For VPs, SVPs, C-suite. Use LLMs to stress-test strategy memos, synthesize "
            "board-prep data, and red-team your own thinking. Practice high-stakes "
            "decisions with ambiguous info. Capstone: adaptive_roleplay — you're making "
            "a $5M bet, and 3 trusted advisors give conflicting recommendations. "
            "You must choose."
        ),
        "course_type": "case_study",
        "answers": [
            "VPs, SVPs, C-suite execs",
            "Claude API for strategy stress-testing, red-teaming, memo review",
            "Capstone: adaptive_roleplay where you get 3 conflicting advisor opinions and must decide",
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
    if status != 200:
        print(f"  [{idx+1}] start failed: {start}", flush=True); return
    sid = start["session_id"]
    answers = []
    for i, q in enumerate(start.get("questions", [])[:4]):
        ans = spec["answers"][i] if i < len(spec["answers"]) else "Use adaptive_roleplay / incident_console for immersion."
        answers.append({"question_id": q["id"], "answer": ans})
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}] refine failed: {refine}", flush=True); return
    types = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]: types.add(s.get("exercise_type", s.get("type")))
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}] generate failed: {g}", flush=True); return
    new_types = sorted(types & {"adaptive_roleplay","incident_console","simulator_loop"})
    print(f"  [{idx+1}] OK {g.get('course_id')} ({time.time()-t0:.0f}s) — new: {new_types}", flush=True)


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(3)
    async def bounded(s, i):
        async with sem: return await gen(s, i)
    await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
