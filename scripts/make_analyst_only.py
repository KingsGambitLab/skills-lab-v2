"""Retry AI Skills for Data Analysts with a more directive capstone clause."""
import json, urllib.request, time

BASE = "http://localhost:8001"


def post(path, body, timeout=1200):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


if __name__ == "__main__":
    b0 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b0['spent_usd']:.2f}", flush=True)
    t0 = time.time()

    TITLE = "AI Skills for Data Analysts: Ship Real Queries"
    # Code-first description so the generator picks a code_exercise capstone.
    # Yuki v1 review 2026-04-20 found the first attempt shipped an adaptive_roleplay
    # capstone (CFO simulation) that didn't verify SQL skill — a learner could bluff
    # with invented numbers and "win" without writing a single query. This rev adds
    # an explicit CAPSTONE IS A CODE_EXERCISE clause + trust-boundary concreteness.
    DESC = (
        "Master the daily AI workflow of a modern Data Analyst — SQL-first, hands-on. "
        "Cover natural-language SQL with Snowflake Cortex / Looker / Hex, dbt-assisted "
        "model authoring with schema.yml tests, anomaly detection with rolling z-score, "
        "experiment analysis with REAL p-value / confidence-interval computation in Python, "
        "and three dedicated trust-boundary modules: spotting hallucinated columns, PII "
        "masking with regex, and prompt-injection sanitization. Every exercise is hands-on: "
        "the learner writes SQL, Python, dbt YAML, or test assertions — never memos or "
        "strategy docs. CAPSTONE IS A code_exercise: the learner writes the unified CTE "
        "that reconciles two diverging churn queries (cohort-based vs activity-based), "
        "produces test output showing 8 customers with variance between 25%-40%, and a "
        "Slack-message artifact explaining the reconciliation. Shipped deliverable is a "
        "SQL script + Python reconciliation + unit tests — never a deck, never a playbook, "
        "never 'present to stakeholders' as the primary deliverable."
    )

    start = post("/api/creator/start", {
        "title": TITLE, "description": DESC, "course_type": "technical", "level": "Intermediate",
    }, timeout=400)
    sid = start["session_id"]
    answers = [
        {"question_id": q["id"],
         "answer": "Capstone is a code_exercise or system_build — learner writes real SQL/Python, runs tests, "
                   "produces a reviewable artifact. No strategy decks, no research reports, no playbooks."}
        for q in start.get("questions", [])[:4]
    ]
    print("  refining...", flush=True)
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
    n_mods = len(refine["outline"]["modules"])
    print(f"  generating {n_mods} modules...", flush=True)
    # Inspect the capstone shape before submitting
    last_step = refine["outline"]["modules"][-1]["steps"][-1]
    print(f"  capstone step: type={last_step['exercise_type']!r} title={last_step['title']!r}", flush=True)
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=1200)
    cid = g["course_id"]
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    print(f"  DONE {cid} ({int(time.time()-t0)}s) — {len(cd['modules'])} modules", flush=True)
    print(f"  subtitle: {cd.get('subtitle')!r}", flush=True)

    b1 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b1['spent_usd']:.2f} (delta: ${b1['spent_usd']-b0['spent_usd']:.2f})")
    print(f"\nNEW ANALYST ID: {cid}")
