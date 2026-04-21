"""Regenerate the 3 headline role courses with the new Creator (primer + tier + capstone-pitch).

This runs AFTER the uvicorn restart that activates _llm_capstone_pitch generation.
Produces fresh IDs that replace the FEATURED_COURSE_IDS in frontend/index.html.
"""
import json, urllib.request, time

BASE = "http://localhost:8001"

JOBS = [
    {
        "slug": "dev",
        "title": "AI Power Skills for Developers: Ship Real Code With Claude / Copilot / Cursor",
        "description": "Master the daily AI workflow of a modern software engineer. Cover Claude Code daily surface (CLAUDE.md, hooks, skills, MCP, slash commands), agentic coding (harnesses, agent loops, sub-agents, worktrees), end-to-end app builds in 2-4 hours with agentic tools, AI-powered code review with Copilot and Cursor, AI-assisted testing automation (unit, integration, e2e, mutation), and security practices for AI-generated code (prompt injection, supply-chain, hallucinated packages). The capstone ships a production feature in 2 hours.",
        "course_type": "technical",
    },
    {
        "slug": "pm",
        "title": "Master AI Skills for Product Managers: From PRDs to Launch With AI",
        "description": "Master the daily AI workflow of a modern Product Manager. Cover AI-assisted discovery (interview synthesis, JTBD extraction from transcripts), PRD writing with AI (user stories, edge cases, failure modes, adversarial review), competitive intelligence automation, launch decisions, metrics and experimentation (natural-language BI, anomaly detection), and stakeholder communication (exec summaries, Slack-reply coaching). The capstone has the PM defending a priority call to skeptical exec stakeholders while the AI copilot hallucinates a customer commit.",
        "course_type": "case_study",
    },
    {
        "slug": "ops",
        "title": "Master AI Skills for Operations Leaders: From Dashboards to Decisions With AI",
        "description": "Master the daily AI workflow of an Ops leader (BizOps, RevOps, Support Ops, Platform Ops). Cover dashboards-to-decisions (natural-language BI in Looker/Amplitude/Hex, anomaly detection, morning exec triage), process automation with AI agents, vendor selection (RFP scoring, TCO modeling), support queue ops (ticket triage, macro generation, sentiment trends), cross-functional communication (status drafting, contradiction detection), and a capstone workday with ONE real metric break, conflicting exec Slack asks, and a vendor-renewal decision in 90 minutes.",
        "course_type": "case_study",
    },
]


def post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def run(job):
    t0 = time.time()
    start = post("/api/creator/start", {
        "title": job["title"],
        "description": job["description"],
        "course_type": job["course_type"],
        "level": "Intermediate",
    })
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Follow the description faithfully. Produce deep, hands-on, tool-specific content for the 2026 skill set."}
               for q in start.get("questions", [])[:4]]
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    cid = g["course_id"]
    # Fetch course to see subtitle
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    print(f"  [{job['slug']}] {cid} ({int(time.time()-t0)}s)")
    print(f"     subtitle: {cd.get('subtitle')!r}")
    print(f"     modules:  {len(cd.get('modules',[]))}")
    return cid, cd.get("subtitle")


if __name__ == "__main__":
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}")

    import concurrent.futures
    ids = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(run, j): j["slug"] for j in JOBS}
        for fut in concurrent.futures.as_completed(futs):
            slug = futs[fut]
            try:
                cid, sub = fut.result()
                ids[slug] = cid
            except Exception as e:
                print(f"  [{slug}] FAIL: {e}")

    print(f"\nNew FEATURED_COURSE_IDS:")
    for slug in ["dev", "pm", "ops"]:
        if slug in ids:
            print(f"  {slug}: '{ids[slug]}'")

    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b['spent_usd']:.2f}")
