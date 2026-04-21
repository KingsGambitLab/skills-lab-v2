"""More function courses via Creator — Mobile Eng, Frontend Eng, Product Marketing, Growth PM,
Engineering Manager, Staff PM. All via Creator dashboard flow only (no seed scripts).
6 courses × ~$0.50 = ~$3 burn.
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "AI for Mobile Engineers: Crash-Free Releases at Scale",
        "description": (
            "For iOS and Android engineers. Use LLMs to diagnose Crashlytics reports, "
            "auto-generate release notes, and review PRs for platform-specific pitfalls "
            "(memory, battery, lifecycle). Hands-on: feed 50 crash logs to Claude, cluster "
            "into root-cause families. Capstone: incident_console — your app is crashing "
            "on iOS 18 after a library update, 5-star reviews tanking in real-time, "
            "a VP demands a rollback and App Review won't approve the new build for 48 hours."
        ),
        "course_type": "technical",
        "answers": [
            "iOS engineers, Android engineers, Mobile Tech Leads",
            "Claude API for crash-log clustering; scripted simulator for the incident drill",
            "Capstone: incident_console — iOS 18 crash surge with App Review delay + exec pressure",
        ],
    },
    {
        "title": "AI for Frontend Engineers: Accessibility to Performance",
        "description": (
            "For Frontend engineers and Design System owners. Use LLMs to audit WCAG "
            "compliance, optimize bundle sizes, and refactor legacy components to modern "
            "React/Vue. Hands-on: feed a 200-component design system + 10 Lighthouse reports "
            "to Claude, surface the top 5 levers. Capstone: adaptive_roleplay — a skeptical "
            "staff engineer says your migration plan is 'over-engineered' and wants the team "
            "to just patch-in-place. Defend or adapt with data."
        ),
        "course_type": "technical",
        "answers": [
            "Frontend engineers, Design System engineers, Web Performance specialists",
            "Claude API for bundle analysis, a11y audit, refactor suggestions; Lighthouse data",
            "Capstone: adaptive_roleplay defending migration plan to skeptical staff engineer",
        ],
    },
    {
        "title": "AI for Product Marketing Managers: Positioning That Moves Pipeline",
        "description": (
            "For PMMs and Messaging leads. Use LLMs to run competitive teardowns, draft "
            "category-defining narratives, and test messaging against 10 ICP personas. "
            "Hands-on: feed 5 competitor sites + 10 customer call transcripts, generate a "
            "positioning doc draft. Capstone: adaptive_roleplay — your SVP of Marketing "
            "says your positioning is 'too niche' and wants you to expand to 3 more "
            "segments. Defend with data or adapt."
        ),
        "course_type": "case_study",
        "answers": [
            "PMMs, Messaging Leads, Competitive Intelligence managers",
            "Claude API for competitive teardown, persona-testing, narrative drafting",
            "Capstone: adaptive_roleplay defending niche positioning to expansion-hungry SVP",
        ],
    },
    {
        "title": "AI for Growth PMs: Experiments to Pipeline",
        "description": (
            "For Growth PMs and Retention leads. Use LLMs to design rigorous A/B tests, "
            "detect p-hacking in existing experiment reports, and synthesize 20 user-interview "
            "transcripts into retention-driver hypotheses. Hands-on: audit 3 historical "
            "experiment reports for SRM / novelty / seasonality. Capstone: simulator_loop "
            "— you have 12 weeks and a $200k budget to ship 4 experiments. Each choice "
            "trades off reach vs statistical power. Budget runs out if you pick poorly."
        ),
        "course_type": "case_study",
        "answers": [
            "Growth PMs, Retention PMs, Experimentation leads",
            "Python + pandas + Claude API; simulator_loop engine for the experiment-portfolio drill",
            "Capstone: simulator_loop 12-week experiment-portfolio with budget constraint + SRM traps",
        ],
    },
    {
        "title": "AI for Engineering Managers: Performance Calibration to 1:1s",
        "description": (
            "For Engineering Managers. Use LLMs to synthesize 1:1 notes across 8 reports "
            "into a calibration doc, draft difficult feedback, and prep for calibration "
            "committee debates. Hands-on: feed 20 weeks of 1:1 notes per report, generate "
            "a balanced perf review. Capstone: adaptive_roleplay — a peer EM on the "
            "calibration committee argues your senior engineer should be down-leveled. "
            "You disagree. Defend with specific evidence without getting defensive."
        ),
        "course_type": "case_study",
        "answers": [
            "Engineering Managers, Senior EMs, Directors of Engineering",
            "Claude API for 1:1 synthesis, calibration doc drafting",
            "Capstone: adaptive_roleplay with peer EM disputing level of your senior report",
        ],
    },
    {
        "title": "AI for Staff PMs: Strategy Docs to Org-Wide Alignment",
        "description": (
            "For Staff and Principal PMs. Use LLMs to stress-test strategy memos, surface "
            "hidden assumptions, and red-team your own org-wide proposals. Hands-on: "
            "feed a draft 6-page strategy memo + 5 stakeholder transcripts to Claude, "
            "identify the 3 weakest assumptions. Capstone: adaptive_roleplay — you're "
            "presenting to a skeptical CEO who has already read 2 competing strategy memos "
            "from peer PMs. 15 turns, high-stakes. Score on clarity, evidence, humility."
        ),
        "course_type": "case_study",
        "answers": [
            "Staff PMs, Principal PMs, Group PMs",
            "Claude API for memo stress-testing, red-teaming, assumption surfacing",
            "Capstone: adaptive_roleplay with CEO who's read 2 competing strategy memos from peers",
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
        ans = spec["answers"][i] if i < len(spec["answers"]) else "Use adaptive_roleplay / incident_console / simulator_loop for immersion."
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
