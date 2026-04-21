"""Regenerate all 7 role courses with the NEW Creator (post Wave-1 learner feedback):

- Expanded BIZ_STRATEGY_BAN (catches 'Product Strategy Document', 'exec deck', 'CPO presentation')
- Distinct-eng-signal floor (>=3 signals)
- PM verbs vs code verbs in checklist (code must dominate in eng capstones)
- Categorization explanations required
- Filler text replaced (fallback no longer emits the self-referential template)
- Categorization payload reader accepts all 4 shapes (mapping/categories/placement/categorizations)

Runs 7 courses in parallel, captures new IDs.
"""
import json, urllib.request, time, concurrent.futures

BASE = "http://localhost:8001"

JOBS = [
    {
        "slug": "dev",
        "title": "AI Power Skills for Developers: Ship Real Code With Claude / Copilot / Cursor",
        "description": "Master the daily AI workflow of a modern software engineer. Cover Claude Code daily surface (CLAUDE.md, hooks, skills, MCP, slash commands), agentic coding (harnesses, agent loops, sub-agents, worktrees), end-to-end app builds in 2-4 hours with agentic tools, AI-powered code review with Copilot and Cursor, AI-assisted testing automation, and security practices. The capstone MUST be a coding deliverable — the learner runs `claude`, writes code, runs `pytest`, opens a PR, deploys. No strategy documents, no executive decks, no CPO presentations.",
        "course_type": "technical",
    },
    {
        "slug": "pm",
        "title": "Master AI Skills for Product Managers: From PRDs to Launch With AI",
        "description": "Master the daily AI workflow of a modern PM. Cover AI-assisted discovery (interview synthesis, JTBD extraction), PRD writing with AI, competitive intelligence, launch decisions, metrics and experimentation, and stakeholder communication. The capstone is ONE coherent scenario — one company, one PM, one launch-day decision — threaded through every step. NO bouncing between fictional companies.",
        "course_type": "case_study",
    },
    {
        "slug": "ops",
        "title": "Master AI Skills for Operations Leaders: From Dashboards to Decisions With AI",
        "description": "Master the daily AI workflow of an Ops leader. Cover dashboards-to-decisions (natural-language BI with specific tools like Looker/Amplitude/Hex), process automation with named AI agents (Zapier AI, n8n, Temporal + LLM), vendor selection, support queue ops, and cross-functional communication. Capstone is ONE 90-minute coherent operational crisis — learner produces actual Slack messages, status page text, a CRO briefing.",
        "course_type": "case_study",
    },
    {
        "slug": "hr",
        "title": "AI Power Skills for HR and Recruitment Leaders",
        "description": "Master the daily AI workflow for HR/Recruitment. Cover sourcing/screening (ATS integrations: Greenhouse, Lever, Ashby), structured interviewing with AI rubrics, comp benchmarking, performance review drafting, DEI analytics with specific bias metrics (adverse-impact 4/5ths rule, EEOC guidance), and PIP documentation. Teach legal boundaries: NYC AEDT, EU AI Act, Illinois AIVIA compliance. Capstone is ONE coherent PIP conversation (one employee name, one timeline) — prep, deliver, document.",
        "course_type": "case_study",
    },
    {
        "slug": "sales",
        "title": "AI Power Skills for Sales and Marketing Leaders",
        "description": "Master the daily AI workflow for Sales. Cover lead research with named tools (LinkedIn Sales Nav, Apollo, Gong), conversation intelligence (Gong Smart Trackers, Chorus), pipeline forecasting in Salesforce, outreach sequences in Outreach/Salesloft, objection handling, and attribution. Capstone threads ONE deal (one account, one buyer, one stack) from research to close — learner produces real prospecting emails, objection-handling scripts, CRO forecast defense.",
        "course_type": "case_study",
    },
    {
        "slug": "data",
        "title": "AI Power Skills for Data Analysts",
        "description": "Master the daily AI workflow of a data analyst. Cover natural-language SQL (Looker, Hex, Tableau Ask Data, Snowflake Cortex), dbt-assisted model authoring, anomaly detection, experiment analysis, and trust-boundary validation (hallucinated APIs, column drift, PII leaks, prompt injection). Capstone reconciles TWO diverging queries — learner writes the unified CTE, catches the cohort-definition diff, produces a reviewable SQL artifact.",
        "course_type": "technical",
    },
    {
        "slug": "legal",
        "title": "AI Power Skills for Legal and Compliance Teams",
        "description": "Master the daily AI workflow for in-house Legal. Cover contract review with Harvey/CoCounsel/Ironclad, DSAR handling, vendor due diligence, policy drafting, regulatory monitoring. Teach privilege boundaries by TOOL (Azure OpenAI + zero-retention DPA vs consumer ChatGPT), waiver risks, defensible-vs-reckless workflows. Capstone is ONE in-house-counsel scenario — learner redlines a vendor MSA, produces counter-positions with legal reasoning, stays within privilege boundaries.",
        "course_type": "compliance",
    },
]


def post(path, body, timeout=500):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def run(job):
    t0 = time.time()
    try:
        start = post("/api/creator/start", {
            "title": job["title"],
            "description": job["description"],
            "course_type": job["course_type"],
            "level": "Intermediate",
        })
        sid = start["session_id"]
        answers = [{"question_id": q["id"], "answer": "Follow the description faithfully. Capstone is ONE coherent scenario with ONE set of entity names threaded through every step. No PM/strategy framing in engineering capstones."}
                   for q in start.get("questions", [])[:4]]
        refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
        g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
        cid = g["course_id"]
        cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
        print(f"  [{job['slug']:6}] {cid} in {int(time.time()-t0)}s — {len(cd['modules'])} modules", flush=True)
        print(f"           subtitle: {cd.get('subtitle')!r}", flush=True)
        return {"slug": job["slug"], "ok": True, "course_id": cid, "modules": len(cd["modules"]), "subtitle": cd.get("subtitle")}
    except Exception as e:
        print(f"  [{job['slug']:6}] FAIL: {e}", flush=True)
        return {"slug": job["slug"], "ok": False, "error": str(e)}


if __name__ == "__main__":
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(run, j): j["slug"] for j in JOBS}
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())

    print(f"\n--- SUMMARY ---")
    for r in sorted(results, key=lambda x: x["slug"]):
        if r["ok"]:
            print(f"  {r['slug']:6} {r['course_id']} — {r['modules']} modules")
        else:
            print(f"  {r['slug']:6} FAIL: {r['error']}")

    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}")
    print(f"\nNEW IDS:")
    for r in sorted(results, key=lambda x: x["slug"]):
        if r["ok"]:
            print(f"  {r['slug']}: '{r['course_id']}'")
