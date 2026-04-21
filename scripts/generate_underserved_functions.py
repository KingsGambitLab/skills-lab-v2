"""Generate 5 courses for underserved functions — Accountant, Investor Relations, BizDev,
Customer Success Ops, Chief of Staff. All via Creator API with the hardened prompt.
~$0.30 per course = ~$1.50 total burn.
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "AI for Accountants: From Ledger to Audit Prep",
        "description": (
            "For Staff Accountants, Controllers, Senior Accountants. Use LLMs to reconcile "
            "50 suspense-account entries, spot anomalies in journal entries, draft audit-ready "
            "documentation from meeting notes, and prep Q&A for external auditors. Hands-on: "
            "feed 3 months of GL entries + reconciliation notes to Claude, identify the top-5 "
            "material anomalies. Capstone: adaptive_roleplay — a Big-4 senior auditor asks you "
            "to defend a capitalized-vs-expensed decision under GAAP scrutiny. Persona starts "
            "with credibility 6, patience 7, skepticism 5; rubric: citation_specificity, "
            "GAAP_reasoning, documentation_integrity, professional_skepticism_discipline."
        ),
        "course_type": "compliance",
        "answers": [
            "Staff Accountants, Senior Accountants, Controllers, Audit prep teams",
            "Claude API for anomaly detection on GL entries; pandas for reconciliation; scripted audit-persona roleplay",
            "Capstone: adaptive_roleplay defending capitalize-vs-expense decision to Big-4 auditor; persona starts positive dims >= 5",
        ],
    },
    {
        "title": "AI for Investor Relations: Earnings Prep to Hostile Questions",
        "description": (
            "For IR Directors and VPs. Use LLMs to synthesize 8-K disclosures, stress-test "
            "the guidance narrative, prep earnings-call Q&A with simulated activist-investor "
            "questions, and draft boardroom-ready summaries. Hands-on: feed last 3 quarters of "
            "transcripts + peer-company filings, identify the 5 most likely adversarial "
            "questions for next quarter. Capstone: adaptive_roleplay — an activist investor "
            "grills you on a guidance miss during live Q&A. Persona starts skepticism 6, "
            "aggression 7 (neg dim - low is good). Rubric: clarity_under_pressure, "
            "guidance_defensibility, data_specificity, composure, redirect_discipline."
        ),
        "course_type": "case_study",
        "answers": [
            "IR Directors, IR VPs, CFO staff, earnings-prep teams",
            "Claude API for transcript synthesis + adversarial Q&A simulation",
            "Capstone: adaptive_roleplay with activist investor on live Q&A; persona >= 5 positive / <= 5 negative dims",
        ],
    },
    {
        "title": "AI for Business Development: Alliance ROI to Partner Roadmaps",
        "description": (
            "For BizDev Directors, Alliance Managers, Channel leaders. Use LLMs to model "
            "partner-tier ROI, draft co-sell playbooks, and synthesize 20 partner calls into "
            "signal on which alliances are actually moving pipeline. Hands-on: feed 6 months "
            "of partner-mapped deals + NPS, identify which partners are accretive vs dilutive. "
            "Capstone: adaptive_roleplay — a strategic partner's VP demands better rev-share "
            "citing their 'outsized contribution'. You know the real data says otherwise. Defend "
            "without burning the relationship. Persona: partner_VP with urgency_pressure 6, "
            "trust 6, flexibility 5. Rubric: data_specificity, relationship_preservation, "
            "genuine_vulnerability, alternative_framing, BATNA."
        ),
        "course_type": "case_study",
        "answers": [
            "BizDev Directors, Alliance Managers, Channel leaders, Partnerships teams",
            "Claude API for partner-call synthesis + deal-attribution analysis; pandas for rev-share modeling",
            "Capstone: adaptive_roleplay with strategic-partner VP demanding better rev-share",
        ],
    },
    {
        "title": "AI for Customer Success Operations: Playbooks to Portfolio Health",
        "description": (
            "For CS Ops Managers and Sr. Analysts. Use LLMs to auto-generate risk-tiered "
            "renewal playbooks, synthesize QBR decks from Gong call transcripts, and predict "
            "attrition 90-days-out from engagement-signal patterns. Hands-on: feed 100 customer "
            "health-scorecards + call transcripts, produce a ranked intervention plan. Capstone: "
            "incident_console — a Tier-1 customer is threatening churn at 48-hour notice, "
            "your CSM is out sick, your VP wants a save-plan in 90 minutes. Commands to run: "
            "pull call history, summarize complaints, draft exec escalation email, propose "
            "pricing/scope concessions. Scripted with cascade rules (wrong concession cascades "
            "to other accounts)."
        ),
        "course_type": "technical",
        "answers": [
            "CS Ops Managers, CS Analysts, RevOps-CS crossovers",
            "Claude API for transcript/scorecard synthesis; incident_console engine for the save drill",
            "Capstone: incident_console — T1 churn threat with CSM out + 48hr deadline",
        ],
    },
    {
        "title": "AI for Chief of Staff: Cross-Org Synthesis to Exec Prep",
        "description": (
            "For Chiefs of Staff to VPs, SVPs, and C-suite. Use LLMs to synthesize 40 weekly "
            "1:1 notes into exec-ready themes, draft board pre-read memos, prep your principal "
            "for difficult meetings, and surface the 3 things that actually need their attention "
            "this week. Hands-on: feed 4 weeks of Slack + calendar + email metadata, identify "
            "the 'broken glass' (issues your exec is ignoring). Capstone: adaptive_roleplay — "
            "your CEO is 15 minutes late to a 30-min board session and hasn't read the pre-read. "
            "You have 10 min to brief them verbally without causing panic. Board-member persona: "
            "skepticism 5, patience 6, engagement 5. Rubric: signal_compression, anticipating_questions, "
            "calmness_under_pressure, alignment_checks."
        ),
        "course_type": "case_study",
        "answers": [
            "Chiefs of Staff, Sr. Business Analysts to C-suite, VP-of-Ops-to-SVP pairs",
            "Claude API for multi-source synthesis (calendar, Slack, email, 1:1 notes)",
            "Capstone: adaptive_roleplay briefing a 15-min-late CEO on a board session with no pre-read",
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
    answers = [{"question_id": q["id"], "answer": spec["answers"][i] if i < len(spec["answers"]) else "Use adaptive_roleplay / incident_console."} for i, q in enumerate(start.get("questions", [])[:4])]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200: print(f"  [{idx+1}] refine failed: {refine}"); return None
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200: print(f"  [{idx+1}] generate failed: {g}"); return None
    cid = g.get('course_id')

    # Inspect persona (if adaptive_roleplay) to confirm guardrails hold
    d = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}").read())
    info = []
    for m in d["modules"]:
        mod = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}").read())
        for s in mod["steps"]:
            if s.get("exercise_type") == "adaptive_roleplay":
                dd = s.get("demo_data", {})
                cp = dd.get("counterparty", {})
                hs = cp.get("hidden_state", {})
                info.append(f"persona={hs}")
            if s.get("exercise_type") == "incident_console":
                info.append(f"incident_console present")
    print(f"  [{idx+1}] OK {cid} ({time.time()-t0:.0f}s) — {' | '.join(info) if info else 'no-immersive'}", flush=True)
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
