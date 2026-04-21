"""Retry the 4 courses that failed on the old quality-floor.

They had incident_console / simulator_loop as capstone which the old
quality-floor rejected. New floor accepts them.
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

FAILED = [
    {
        "title": "Database Ops: Postgres Under Fire",
        "description": "Live incident: a production Postgres primary is at 98% CPU, replication lag climbing, connection pool saturated. Type real psql + pg_stat queries, read live log tail. Wrong commands (VACUUM FULL on hot table) cascade. Correct path: identify the slow query, kill it, reindex in off-hours. Zero-LLM scripted simulator.",
        "course_type": "technical",
    },
    {
        "title": "ML Ops: Model Serving Outage",
        "description": "Live incident: your ML inference endpoint is returning 500s. GPUs are saturated. Model canary at 10% but p99 > 5s. Type kubectl + ML-platform commands, inspect GPU utilization, check model version drift. Cascade rules penalize destructive actions. Remediation path includes autoscaler fix, model rollback, or batch-size reduction.",
        "course_type": "technical",
    },
    {
        "title": "Product Manager: Scope Negotiation with Engineering",
        "description": "Learn to negotiate scope reductions and trade-offs with engineers. Capstone is a live roleplay with a senior engineer who is pushing back on your feature prioritization — they have hidden trust/buy_in/overwhelm state. Uses adaptive_roleplay for the capstone.",
        "course_type": "case_study",
    },
    {
        "title": "Platform Engineering: Kafka Outage Drill",
        "description": "Live incident: Kafka brokers are lagging, consumer groups are falling behind, topics are partition-imbalanced. Type kafkacat + kubectl + AWS CLI commands, read live broker metrics. Capstone is a live incident_console drill. Correct remediation: rebalance partitions, scale consumers, or roll back a recent version bump.",
        "course_type": "technical",
    },
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:500]}
    except Exception as e:
        return -1, {"error": str(e)[:300]}


async def gen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}/4] {spec['title']}...", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", spec)
    if status != 200:
        print(f"  [{idx+1}/4] start failed: {start}", flush=True); return None
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Use immersive pedagogies (adaptive_roleplay, incident_console, simulator_loop) for the capstone."} for q in start.get("questions", [])[:4]]
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}/4] refine failed: {refine}", flush=True); return None
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}/4] generate failed: {g}", flush=True); return None
    print(f"  [{idx+1}/4] OK {g.get('course_id')} in {time.time()-t0:.0f}s", flush=True)
    return {"title": spec["title"], "course_id": g.get("course_id"), "elapsed": time.time()-t0}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception:
        pass
    sem = asyncio.Semaphore(2)
    async def bounded(s, i):
        async with sem:
            return await gen(s, i)
    results = await asyncio.gather(*[bounded(s, i) for i, s in enumerate(FAILED)])
    print("\n=== Retries ===", flush=True)
    for r in results:
        if r: print(f"  OK {r['title']}: {r['course_id']} ({r['elapsed']:.0f}s)", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
