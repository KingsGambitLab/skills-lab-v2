"""Create PM course from Sachin Rekhi's post + Data Analyst course.

Flow:
1. Crawl https://www.sachinrekhi.com/p/claude-code-for-product-managers via /api/creator/fetch_url
2. POST /api/creator/start for PM with that source_material
3. POST /api/creator/start for Data Analyst (no URL, description only)
4. Refine + generate both in parallel
5. Print new course IDs
"""
import json, urllib.request, time, concurrent.futures

BASE = "http://localhost:8001"

PM_URL = "https://www.sachinrekhi.com/p/claude-code-for-product-managers"

ANALYST_DESC = (
    "Master the daily AI workflow of a modern Data Analyst. Cover natural-language SQL "
    "(Looker, Hex, Tableau Ask Data, Snowflake Cortex), dbt-assisted model authoring and "
    "lineage inspection, anomaly detection with AI-driven alerting, experiment analysis "
    "(A/B tests, Simpson's paradox detection), and trust-boundary validation (hallucinated "
    "tables/columns, PII masking, prompt injection, cohort-definition drift). Capstone "
    "reconciles TWO diverging churn queries — learner writes the unified CTE, catches the "
    "definitional diff, and produces a reviewable SQL artifact plus a Slack explanation to "
    "the CFO."
)


def post(path, body, timeout=900):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def make_course(slug, title, description, course_type, source_material=""):
    t0 = time.time()
    try:
        body = {
            "title": title,
            "description": description,
            "course_type": course_type,
            "level": "Intermediate",
        }
        if source_material:
            body["source_material"] = source_material
        start = post("/api/creator/start", body, timeout=400)
        sid = start["session_id"]
        answers = [
            {"question_id": q["id"], "answer":
             "One coherent scenario threaded through every module. Name real tools + real prompts. "
             "Capstone is a concrete deliverable the learner produces by the end, not a meta-doc."}
            for q in start.get("questions", [])[:4]
        ]
        print(f"  [{slug}] refining outline...", flush=True)
        refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
        n_mods = len(refine["outline"]["modules"])
        print(f"  [{slug}] generating {n_mods} modules...", flush=True)
        g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=1200)
        cid = g["course_id"]
        cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
        print(f"  [{slug}] DONE {cid} ({int(time.time()-t0)}s) — {len(cd['modules'])} modules", flush=True)
        print(f"           subtitle: {cd.get('subtitle')!r}", flush=True)
        return {"slug": slug, "ok": True, "course_id": cid}
    except Exception as e:
        print(f"  [{slug}] FAIL ({int(time.time()-t0)}s): {e}", flush=True)
        return {"slug": slug, "ok": False, "error": str(e)}


if __name__ == "__main__":
    b0 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b0['spent_usd']:.2f}", flush=True)

    # 1. Crawl Sachin Rekhi for PM source
    print(f"Crawling {PM_URL} ...", flush=True)
    crawl = post("/api/creator/fetch_url", {"url": PM_URL}, timeout=45)
    pm_source = crawl.get("combined_source_material", "") or ""
    first_page = (crawl.get("pages") or [{}])[0]
    print(f"  status: {first_page.get('status')}  chars: {first_page.get('chars')}  title: {(first_page.get('title') or '')[:80]}")
    if not pm_source:
        print("  WARNING: no PM source crawled — proceeding with description only")

    PM_TITLE = "AI Skills for Product Managers: Claude Code for PMs"
    PM_DESC = (
        "Master the daily AI workflow of a modern PM by learning Claude Code — the agentic "
        "coding tool PMs can use even without being engineers. Based on Sachin Rekhi's "
        "'Claude Code for Product Managers' framework. Cover research synthesis from transcripts, "
        "PRD writing with Claude + Notion, competitive intel pipelines, launch readiness memos, "
        "customer escalation analysis, and rapid prototyping. Capstone: PM ships a working demo "
        "feature (not a deck) to defend a launch decision live to skeptical exec stakeholders."
    )

    jobs = [
        ("pm", PM_TITLE, PM_DESC, "case_study", pm_source),
        ("analyst", "AI Skills for Data Analysts: Ship Real Queries", ANALYST_DESC, "technical", ""),
    ]

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(make_course, s, t, d, ct, src): s for (s, t, d, ct, src) in jobs}
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            results[r["slug"]] = r

    print("\n--- SUMMARY ---")
    for slug, r in results.items():
        if r["ok"]:
            print(f"  {slug:8} {r['course_id']}")
        else:
            print(f"  {slug:8} FAIL: {r['error']}")

    b1 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b1['spent_usd']:.2f} (delta: ${b1['spent_usd']-b0['spent_usd']:.2f})")
