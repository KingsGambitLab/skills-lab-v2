"""PM v3 — after auto-remap for non-coder case_study courses.

The capstone should now be adaptive_roleplay (PM defending the launch decision)
instead of system_build (multi-service API integration).
"""
import json, urllib.request, time

BASE = "http://localhost:8001"

PM_URL = "https://www.sachinrekhi.com/p/claude-code-for-product-managers"


def post(path, body, timeout=1200):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


if __name__ == "__main__":
    b0 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b0['spent_usd']:.2f}", flush=True)

    print(f"Crawling {PM_URL} ...", flush=True)
    crawl = post("/api/creator/fetch_url", {"url": PM_URL}, timeout=45)
    pm_source = crawl.get("combined_source_material", "") or ""

    TITLE = "AI Skills for Product Managers: Claude Code for PMs"
    # Emphasize that the capstone is a PM-doable defense, not a full-stack build.
    # The Creator primer has been updated to force adaptive_roleplay + one scoped
    # code_exercise for PM capstones, but the description also helps steer.
    DESC = (
        "Master the daily AI workflow of a modern Product Manager by learning Claude "
        "Code — the agentic coding tool PMs can use even without being engineers. Based "
        "on Sachin Rekhi's 'Claude Code for Product Managers' framework. Cover research "
        "synthesis from transcripts, PRD writing with Claude + Notion, competitive intel "
        "pipelines, launch readiness memos, customer escalation analysis, and rapid "
        "prototyping. CAPSTONE IS A PM-DOABLE DEFENSE (adaptive_roleplay): the PM has "
        "prototyped a small feature with Claude Code and now defends their launch "
        "decision live to a skeptical CFO or VP Eng. No multi-service API integration. "
        "No Terraform. No deploy-to-production-MVP monstrosities. The PM's deliverable "
        "is artifacts they genuinely produced (PRD, customer-synthesis doc, a tiny "
        "working demo they can click through) + the ability to defend it under pressure."
    )

    t0 = time.time()
    start = post("/api/creator/start", {
        "title": TITLE, "description": DESC,
        "course_type": "case_study",  # not technical — PM is not coding
        "level": "Intermediate",
        "source_material": pm_source,
    }, timeout=400)
    sid = start["session_id"]
    answers = [
        {"question_id": q["id"],
         "answer": "Capstone is an adaptive_roleplay where the PM defends a launch decision to a skeptical CFO/CTO. "
                   "The PM produces artifacts EARLIER in the course (PRD, synthesis, small demo) — the capstone "
                   "defends those artifacts. No multi-service builds. No Terraform. No deploy URLs."}
        for q in start.get("questions", [])[:4]
    ]
    print("  refining...", flush=True)
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
    n_mods = len(refine["outline"]["modules"])
    last_step = refine["outline"]["modules"][-1]["steps"][-1]
    print(f"  generating {n_mods} modules (capstone type: {last_step['exercise_type']})...", flush=True)
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=1200)
    cid = g["course_id"]
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    print(f"  DONE {cid} ({int(time.time()-t0)}s) — {len(cd['modules'])} modules", flush=True)
    print(f"  subtitle: {cd.get('subtitle')!r}", flush=True)

    # Verify capstone shape
    cap_module_id = cd['modules'][-1]['id']
    md = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{cap_module_id}", timeout=30).read())
    print(f"\n=== Capstone module: {cd['modules'][-1]['title']} ===")
    for s in md['steps']:
        print(f"  S{s['position']}: [{s['exercise_type']}] {s['title']}")

    b1 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b1['spent_usd']:.2f} (delta: ${b1['spent_usd']-b0['spent_usd']:.2f})")
    print(f"\nNEW PM ID: {cid}")
