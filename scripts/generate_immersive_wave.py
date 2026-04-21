"""Generate 10 new courses designed to exercise adaptive_roleplay + incident_console.

Each description explicitly signals the new pedagogy so the Creator picks it up.
"""
import asyncio
import json
import urllib.request
import urllib.error
import time

BASE = "http://localhost:8001"

COURSES = [
    # ── adaptive_roleplay-heavy (live human interactions) ───────────────
    {
        "title": "Customer Success: Saving At-Risk Accounts",
        "description": "Practice live conversations with frustrated enterprise customers who are threatening to churn. Each conversation adapts to what you say — the counterparty has hidden trust/frustration/budget_flexibility state. Capstone is a live save-the-account negotiation with a customer whose renewal is in 7 days.",
        "course_type": "case_study",
    },
    {
        "title": "Engineering Manager First 90 Days",
        "description": "Drop-into real manager scenarios: a skip-level with a senior engineer who is burnt out, a difficult 1:1 with someone missing deadlines, a retro with three people who think the project is doomed. Capstone is a live roleplay with a senior engineer considering quitting.",
        "course_type": "case_study",
    },
    {
        "title": "Hiring: Interviewing Senior Candidates",
        "description": "Practice live interview conversations. The candidate has hidden defensiveness/confidence/skill_signal state. Capstone is a live technical screen where the candidate pushes back on your questions — you must evaluate without letting them steer.",
        "course_type": "case_study",
    },
    {
        "title": "Sales: B2B Enterprise Discovery Calls",
        "description": "Practice live discovery calls with B2B buyers. The AI buyer has hidden skepticism/urgency/budget state. Capstone is a live call where you must earn the right to a demo without revealing your full hand.",
        "course_type": "case_study",
    },
    # ── incident_console-heavy (live system debugging) ────────────────
    {
        "title": "Security Incident Response: Phishing + Lateral Movement",
        "description": "Live simulation: a phishing email compromises a dev laptop, attacker pivots laterally, exfiltrating data. You see SIEM logs streaming, EDR alerts firing, Slack threads escalating. Type real commands (shell, splunk queries) to contain and investigate. Graded on time-to-contain, correct attribution, and blast radius.",
        "course_type": "technical",
    },
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
    # ── Hybrid (needs both or has clear new-pedagogy fit) ───────────────
    {
        "title": "Engineering Leadership Under Outage",
        "description": "Module 1-2: concepts on incident command. Module 3: live outage where YOU'RE the IC, with streaming logs and a Slack thread full of engineers. Module 4: live roleplay post-mortem with a VP who's asking hard questions. Combines incident_console (drill) + adaptive_roleplay (post-mortem) for full incident-leadership experience.",
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


def _post_json(path, body, timeout=300):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:500]}
    except Exception as e:
        return -1, {"error": str(e)[:500]}


async def gen_one(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}/10] Starting: {spec['title'][:60]}", flush=True)
    status, start = await asyncio.to_thread(_post_json, "/api/creator/start", {
        "title": spec["title"], "description": spec["description"], "course_type": spec["course_type"],
    })
    if status != 200:
        print(f"  [{idx+1}/10] start failed: {start}", flush=True)
        return None
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Favor immersive/live pedagogies (adaptive_roleplay, incident_console) where they fit. Capstone must be interactive, not a deck."} for q in start.get("questions", [])[:4]]

    status, refine = await asyncio.to_thread(_post_json, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}/10] refine failed: {refine}", flush=True)
        return None

    # Log what exercise types the Creator picked
    types_used = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]:
            types_used.add(s.get("exercise_type", s.get("type")))
    has_new = any(t in types_used for t in ("adaptive_roleplay", "incident_console"))
    print(f"  [{idx+1}/10] refined. Types: {sorted(types_used)}. Uses new types: {has_new}", flush=True)

    status, gen = await asyncio.to_thread(_post_json, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    elapsed = time.time() - t0
    if status != 200:
        print(f"  [{idx+1}/10] generate failed: {gen}", flush=True)
        return None
    cid = gen.get("course_id")
    print(f"  [{idx+1}/10] OK generated {cid} in {elapsed:.0f}s", flush=True)
    return {"title": spec["title"], "course_id": cid, "types": sorted(types_used), "uses_new": has_new, "elapsed": elapsed}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}/${b['cap_usd']} (${b['remaining_usd']:.2f} remaining)", flush=True)
    except Exception:
        pass

    sem = asyncio.Semaphore(3)
    async def bounded(spec, idx):
        async with sem:
            return await gen_one(spec, idx)
    results = await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    results = [r for r in results if r]

    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${b['spent_usd']:.2f}/${b['cap_usd']} (${b['remaining_usd']:.2f} remaining)", flush=True)
    except Exception:
        pass

    print("\n=== RESULTS ===", flush=True)
    uses_new_count = sum(1 for r in results if r["uses_new"])
    print(f"{uses_new_count}/{len(results)} courses used the new exercise types", flush=True)
    for r in results:
        flag = "[NEW-PED]" if r["uses_new"] else "[trad]"
        print(f"  {flag} {r['title']}: {r['course_id']} ({r['elapsed']:.0f}s) — {r['types']}", flush=True)

    with open("/tmp/immersive_wave_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
