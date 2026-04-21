"""Regenerate AI-power-skills reference courses with the upgraded Creator (primer + tier)
and audit each for depth coverage.

Triggers:
- Developer (primer-covered — the one user complained about)
- Product Manager (primer-covered)
- Operations (primer-covered)
- HR / People (no primer yet — baseline test)
- Sales (no primer yet — baseline test)
- Finance (no primer yet — baseline test)
- Data Analyst (no primer yet — baseline test)
- DevOps / SRE (no primer yet — baseline test)
- Legal / Compliance (no primer yet — baseline test)
- Designer (no primer yet — baseline test)

Each course: audit for
- module count (deep_dive should produce >= 6)
- step count (total)
- exercise mix (% hands-on)
- coverage of required subtopics (per-job "anchor signals" defined below)
"""
import json, urllib.request, sys, time, concurrent.futures

BASE = "http://localhost:8001"

JOBS = [
    {
        "slug": "dev",
        "title": "AI Power Skills for Developers: Ship Real Code With Claude / Copilot / Cursor",
        "description": "Master the daily AI workflow of a modern software engineer. Cover everything a dev needs: Claude Code day-to-day (CLAUDE.md, hooks, skills), agentic coding (harnesses, agent loops, sub-agents), end-to-end app builds in 2-4 hours using agentic tools, AI-powered code review with GitHub Copilot and Cursor, testing automation with AI, and security practices for AI-generated code. This is the 2026 developer toolbox.",
        "course_type": "technical",
        "primer": True,
        "anchors": [
            "CLAUDE.md", "hook", "skill", "MCP", "slash command",
            "agentic", "sub-agent", "agent loop", "worktree",
            "build", "deploy", "ship",
            "Copilot", "Cursor", "code review", "PR",
            "test", "coverage", "e2e",
            "security", "injection", "vulnerab",
        ],
    },
    {
        "slug": "pm",
        "title": "Master AI Skills for Product Managers: From PRDs to Launch With AI",
        "description": "Master the daily AI workflow of a modern Product Manager. Cover AI-assisted discovery (interview synthesis, JTBD extraction), PRD writing with AI, competitive intelligence automation, launch decision making, AI-assisted metrics and experimentation, and stakeholder communication. Include a realistic capstone where the PM drafts a PRD under stakeholder pressure.",
        "course_type": "case_study",
        "primer": True,
        "anchors": [
            "PRD", "discovery", "interview", "JTBD", "jobs to be done",
            "roadmap", "launch", "metric", "experiment",
            "stakeholder", "Looker", "Amplitude",
            "synthesis", "competitor", "positioning",
        ],
    },
    {
        "slug": "ops",
        "title": "Master AI Skills for Operations Leaders: From Dashboards to Decisions With AI",
        "description": "Master the daily AI workflow of an Ops leader (BizOps, RevOps, Support Ops, Platform Ops). Cover dashboards-to-decisions (natural-language BI), process automation with AI agents, vendor selection, support queue ops, cross-functional communication, and a capstone workday drill with dashboard drift + CFO Slack + vendor renewal in 90 minutes.",
        "course_type": "case_study",
        "primer": True,
        "anchors": [
            "dashboard", "Looker", "Amplitude", "Hex",
            "automation", "agent", "workflow", "Zapier",
            "vendor", "RFP", "TCO",
            "queue", "ticket", "triage",
            "stakeholder", "CFO", "exec", "digest",
        ],
    },
    {
        "slug": "hr",
        "title": "AI Power Skills for HR and Recruitment Leaders",
        "description": "Master the daily AI workflow for HR and recruitment leaders. Cover AI-assisted sourcing and screening, interview prep and structure, compensation benchmarking, performance review drafting, DEI analysis, PIP documentation, and a capstone where the learner handles a difficult PIP conversation using adaptive roleplay.",
        "course_type": "case_study",
        "primer": False,
        "anchors": [
            "sourcing", "screening", "ATS", "Greenhouse", "Lever",
            "interview", "rubric", "structured",
            "performance", "review", "PIP",
            "comp", "benchmark",
            "DEI", "bias",
        ],
    },
    {
        "slug": "sales",
        "title": "AI Power Skills for Sales and Marketing Leaders",
        "description": "Master the daily AI workflow for Sales and Marketing leaders. Cover AI-assisted lead research, personalized outreach, objection handling, pipeline analysis, content generation, campaign performance analysis, and a capstone where the learner defends a pipeline forecast to the CRO.",
        "course_type": "case_study",
        "primer": False,
        "anchors": [
            "CRM", "Salesforce", "HubSpot",
            "outreach", "email", "sequence",
            "objection", "discovery",
            "pipeline", "forecast", "quota",
            "Gong", "conversation intelligence",
            "campaign", "attribution",
        ],
    },
    {
        "slug": "data",
        "title": "AI Power Skills for Data Analysts",
        "description": "Master the daily AI workflow of a modern data analyst. Cover AI-assisted SQL generation, dashboard building with natural language BI, anomaly detection, experiment analysis, stakeholder communication of findings, and a capstone where the analyst presents a conflicting metrics story to exec stakeholders.",
        "course_type": "technical",
        "primer": False,
        "anchors": [
            "SQL", "query", "dbt",
            "dashboard", "Looker", "Tableau", "Hex",
            "anomaly", "drift",
            "experiment", "A/B",
            "exec", "stakeholder", "CFO", "present",
        ],
    },
    {
        "slug": "legal",
        "title": "AI Power Skills for Legal and Compliance Teams",
        "description": "Master the daily AI workflow for in-house legal and compliance teams. Cover AI-assisted contract review, DSAR handling, vendor due diligence, privacy impact assessments, policy drafting, regulatory change monitoring, and a capstone where the learner negotiates a high-stakes MSA liability cap with a vendor GC.",
        "course_type": "compliance",
        "primer": False,
        "anchors": [
            "contract", "MSA", "NDA", "redline",
            "DSAR", "GDPR", "privacy",
            "vendor", "due diligence",
            "policy", "regulation",
            "Ironclad", "playbook",
        ],
    },
]


def post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_course_modules(cid):
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    blob = ""
    all_steps = []
    for m in cd["modules"]:
        md = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}", timeout=30).read())
        for s in md["steps"]:
            all_steps.append({
                "module": m["title"],
                "step": s["title"],
                "type": s.get("exercise_type") or s.get("step_type"),
                "content_len": len(s.get("content") or ""),
            })
            blob += " " + (s.get("content") or "") + " " + s["title"] + " " + m["title"]
            if s.get("demo_data"): blob += " " + json.dumps(s["demo_data"])
            if s.get("validation"): blob += " " + json.dumps(s["validation"])
    return cd, blob, all_steps


def run_one(job):
    t0 = time.time()
    try:
        start = post("/api/creator/start", {
            "title": job["title"],
            "description": job["description"],
            "course_type": job["course_type"],
            "level": "Intermediate",
        })
        sid = start["session_id"]
        answers = [{"question_id": q["id"], "answer": "Follow the description faithfully. Produce deep, hands-on, tool-specific content."}
                   for q in start.get("questions", [])[:4]]
        refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
        outline = refine["outline"]
        module_count = len(outline.get("modules", []))
        step_count = sum(len(m.get("steps", [])) for m in outline.get("modules", []))
        g = post("/api/creator/generate", {"session_id": sid, "outline": outline})
        cid = g["course_id"]
        _, blob, steps = fetch_course_modules(cid)
        blob_low = blob.lower()
        hits = sum(1 for a in job["anchors"] if a.lower() in blob_low)
        rate = hits * 100 // len(job["anchors"])
        # Exercise mix
        concept_steps = sum(1 for s in steps if s["type"] == "concept")
        exercise_steps = len(steps) - concept_steps
        hands_on_pct = (exercise_steps * 100) // max(1, len(steps))
        return {
            "slug": job["slug"],
            "ok": True,
            "course_id": cid,
            "sec": int(time.time()-t0),
            "primer": job["primer"],
            "modules": module_count,
            "steps_in_outline": step_count,
            "steps_actual": len(steps),
            "concept_steps": concept_steps,
            "hands_on_pct": hands_on_pct,
            "coverage_pct": rate,
            "hits": hits,
            "total_anchors": len(job["anchors"]),
            "missing": [a for a in job["anchors"] if a.lower() not in blob_low],
        }
    except Exception as e:
        return {"slug": job["slug"], "ok": False, "error": str(e), "sec": int(time.time()-t0)}


if __name__ == "__main__":
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}")

    # Parallel generation (3 concurrent to avoid API thrash)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(run_one, j): j for j in JOBS}
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            print(f"  [{r['slug']:6}] {'✓' if r['ok'] else '✗'} "
                  + (f"mods={r['modules']} steps={r['steps_actual']} hands_on={r.get('hands_on_pct',0)}% cov={r['coverage_pct']}% ({r['hits']}/{r['total_anchors']}) {r['sec']}s {r['course_id']}"
                     if r['ok'] else f"ERROR: {r.get('error','?')}"), flush=True)
            results.append(r)

    print("\n--- SUMMARY ---")
    for r in sorted(results, key=lambda x: x['slug']):
        if not r['ok']:
            print(f"  {r['slug']:6} FAIL: {r.get('error')}")
            continue
        p = "PRIMER" if r['primer'] else "baseline"
        verdict = "DEEP" if r['modules'] >= 6 else ("STD" if r['modules'] >= 3 else "SHALLOW")
        cov = "strong" if r['coverage_pct'] >= 75 else "ok" if r['coverage_pct'] >= 50 else "WEAK"
        print(f"  {r['slug']:6} {p:8} mods={r['modules']:2} steps={r['steps_actual']:2} "
              f"hands_on={r['hands_on_pct']:3}% cov={r['coverage_pct']:3}% [{verdict}/{cov}] {r['course_id']}")
        if r['missing']:
            print(f"         missing anchors: {r['missing'][:8]}")

    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b['spent_usd']:.2f}")
