"""AI upskilling for Finance, Recruitment, Product, Design.

Hands-on skills learners can apply Monday morning. Mix of:
- adaptive_roleplay (stakeholder conversations, candidate interviews)
- code_exercise (for finance — SQL/Python analysis; product — analytics queries)
- incident_console (data-quality drills, model-eval failures)
- scenario_branch (decision flows in recruitment, design reviews)
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    # ── Finance ──────────────────────────────────────────────────────
    {
        "title": "AI for Finance: Automating Close and Reconciliation",
        "description": (
            "For FP&A, controllers, accounting managers. Learn to use LLMs + Python "
            "to automate month-end close checks, reconcile GL vs sub-ledger mismatches, "
            "flag anomalies in expense reports, and draft variance commentary. "
            "Hands-on with real-looking trial balance data. Includes: prompting an LLM "
            "to classify 500 expense line items, using pandas to detect outliers in AR aging, "
            "and building a reconciliation bot that drafts Slack messages to requesters. "
            "Capstone: live incident_console drill where a month-end close is at risk."
        ),
        "course_type": "technical",
        "answers": [
            "Finance professionals (FP&A analysts, controllers, senior accountants) — comfortable in Excel, limited Python exposure",
            "Python (pandas) + LLM API for text classification. No Excel macros. Use pandas because it's what data/BI teams use.",
            "Build and deploy code that handles real 500-row TBs. Capstone must be a working close-risk simulator, not a deck.",
        ],
    },
    {
        "title": "AI for Finance: Forecasting and Scenario Modeling",
        "description": (
            "For Finance leaders and senior analysts. Learn to use LLMs for scenario planning, "
            "automated variance analysis, and board-ready commentary generation. Practice "
            "negotiating AI tool rollout with CFO. Hands-on: prompting GPT-4-class models to "
            "generate 3-case forecasts from historical P&L, using embeddings to cluster "
            "comparable-company disclosures, and building a Monte Carlo wrapper. "
            "Capstone: live roleplay defending your AI-generated forecast to a skeptical CFO."
        ),
        "course_type": "case_study",
        "answers": [
            "Senior FP&A, finance directors, CFO staff",
            "Python + pandas + Claude/GPT API. Use Monte Carlo for scenario bands.",
            "Capstone must be an adaptive_roleplay with a CFO pressure-testing the forecast",
        ],
    },
    # ── Recruitment ───────────────────────────────────────────────────
    {
        "title": "AI for Recruitment: From Sourcing to Offer",
        "description": (
            "For recruiters and talent partners. Practical AI workflows: prompt Claude/GPT to "
            "turn a JD into a sourcing query, grade resumes against competencies (without "
            "illegal bias), draft personalized outreach, and structure bar-raiser debriefs. "
            "Includes bias-audit exercise: AI screens 40 resumes, learner flags where the "
            "model over-weights gendered/age markers. Capstone: live adaptive_roleplay "
            "with a candidate who pushes back on comp AND with a hiring manager who wants "
            "to override a no-hire."
        ),
        "course_type": "case_study",
        "answers": [
            "Recruiters, talent partners, TA leads",
            "Claude/GPT API for drafting and scoring. Include a bias-audit exercise showing how models misread signals.",
            "Capstone: adaptive_roleplay with TWO personas — an underpaid-offered candidate AND a hiring manager who wants to override a panel",
        ],
    },
    # ── Product ──────────────────────────────────────────────────────
    {
        "title": "AI for Product Managers: Discovery and Prioritization",
        "description": (
            "For PMs and Group PMs. Learn to use LLMs to accelerate product discovery: "
            "synthesize 50 user interviews into themes, prioritize a backlog against OKRs "
            "using structured prompts, and generate PRD drafts. Hands-on: feed 20 real-sounding "
            "user quotes to Claude, extract jobs-to-be-done, build a scoring prompt that "
            "catches hallucinated claims. Capstone: defend your AI-assisted roadmap to "
            "leadership in a live panel (adaptive_roleplay with CTO, Head of Design, VP Sales "
            "all challenging different aspects)."
        ),
        "course_type": "case_study",
        "answers": [
            "Product Managers, Group PMs, Head of Product",
            "Practical LLM prompting (Claude API), synthesis prompts, structured output for JTBD extraction",
            "Capstone: adaptive_roleplay with 3-panel leadership challenging your roadmap, each with different concerns",
        ],
    },
    {
        "title": "AI for Product: Running Experiments and Reading Signals",
        "description": (
            "For data-literate PMs and Product-Ops. Use LLMs to pre-read experiment designs "
            "for statistical flaws, auto-generate pre-registration documents, and turn raw "
            "A/B results into exec-ready narrative. Hands-on: feed a dirty experiment dataset "
            "(with planted SRM + novelty effect) into your AI pipeline, catch the issues. "
            "Capstone: incident_console-style drill diagnosing a suspicious A/B lift."
        ),
        "course_type": "technical",
        "answers": [
            "PMs, Product-Ops, Growth-PMs who run experiments",
            "Python + scipy.stats + Claude API. Real dataset with planted biases (SRM, novelty).",
            "Capstone: incident_console drill where PM must diagnose a suspicious lift before shipping",
        ],
    },
    # ── Design ──────────────────────────────────────────────────────
    {
        "title": "AI for Designers: From Research Synthesis to Production Mockups",
        "description": (
            "For UX designers, product designers, design leads. Use LLMs to synthesize "
            "user research transcripts into themed insights, generate 5 Jobs-To-Be-Done "
            "statements from 10 interview notes, draft component library naming, and "
            "critique your own mockups via structured prompts. Hands-on: feed a sample "
            "interview transcript to Claude, get themed insights, critique quality. "
            "Capstone: adaptive_roleplay defending your AI-assisted design decisions "
            "to a skeptical engineering lead who wants evidence, not vibes."
        ),
        "course_type": "case_study",
        "answers": [
            "UX/Product Designers, Design Leads, Research Ops",
            "Claude API for synthesis. No heavy coding — prompt engineering focus.",
            "Capstone: adaptive_roleplay with an engineering lead who pushes back on design decisions, demanding evidence",
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
    print(f"  [{idx+1}/{len(COURSES)}] {spec['title'][:60]}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", {
        "title": spec["title"], "description": spec["description"], "course_type": spec["course_type"],
    })
    if status != 200:
        print(f"  [{idx+1}] start failed: {start}", flush=True); return None
    sid = start["session_id"]
    answers = []
    for i, q in enumerate(start.get("questions", [])[:4]):
        ans = spec["answers"][i] if i < len(spec["answers"]) else "Use immersive pedagogy — adaptive_roleplay for stakeholder conversations, incident_console for hands-on drills. Learners should feel they did the work, not watched a video."
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
    flag = "[NEW]" if new_types else "[trad]"
    print(f"  [{idx+1}] {flag} OK {g.get('course_id')} ({time.time()-t0:.0f}s) — new types: {new_types}, all types: {sorted(types)}", flush=True)
    return True


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
        print(f"\nBudget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
