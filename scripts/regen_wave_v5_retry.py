"""Retry HR/Sales/Data regen with 800s per-course timeout (last run timed out at 500s
because the tighter _is_complete checks caused LLM retries on some steps)."""
import json, urllib.request, time, concurrent.futures

BASE = "http://localhost:8001"

JOBS = [
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
]


def post(path, body, timeout=800):
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
        }, timeout=120)
        sid = start["session_id"]
        answers = [{"question_id": q["id"], "answer": "Follow the description faithfully. Capstone is ONE coherent scenario with ONE set of entity names threaded through every step."}
                   for q in start.get("questions", [])[:4]]
        refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
        g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=800)
        cid = g["course_id"]
        cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
        print(f"  [{job['slug']:6}] {cid} in {int(time.time()-t0)}s — {len(cd['modules'])} modules", flush=True)
        print(f"           subtitle: {cd.get('subtitle')!r}", flush=True)
        return {"slug": job["slug"], "ok": True, "course_id": cid}
    except Exception as e:
        print(f"  [{job['slug']:6}] FAIL ({int(time.time()-t0)}s): {e}", flush=True)
        return {"slug": job["slug"], "ok": False, "error": str(e)}


if __name__ == "__main__":
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:  # Serial, to avoid saturating LLM API
        futs = [ex.submit(run, j) for j in JOBS]
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())
    print(f"\n--- RETRY SUMMARY ---")
    for r in sorted(results, key=lambda x: x["slug"]):
        if r["ok"]:
            print(f"  {r['slug']:6} SUCCESS {r['course_id']}")
        else:
            print(f"  {r['slug']:6} STILL FAILED: {r['error']}")
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}")
