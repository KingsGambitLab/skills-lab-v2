"""Generate 10 diverse courses via the Creator API to stress-test LMS.

Runs all 10 in parallel (bounded concurrency) and prints a summary.
"""
import asyncio
import json
import time
import urllib.request
import urllib.error

BASE = "http://localhost:8001"

# 10 wide-topic courses spanning engineering, research, design, business,
# compliance, data, case study, writing, negotiation, finance.
COURSES = [
    {
        "title": "Kubernetes for ML Workloads",
        "description": "Deploy and auto-scale ML models on Kubernetes with GPU scheduling and monitoring",
        "course_type": "technical",
        "expected_bucket": "engineering",
    },
    {
        "title": "Design Thinking for Product Managers",
        "description": "Apply double-diamond methodology to validate ideas before building",
        "course_type": "technical",
        "expected_bucket": "design",
    },
    {
        "title": "Leading Remote Engineering Teams",
        "description": "Build high-trust distributed teams that ship reliably across time zones",
        "course_type": "case_study",
        "expected_bucket": "leadership",
    },
    {
        "title": "GDPR Compliance for SaaS Engineers",
        "description": "Handle personal data correctly: consent, data minimization, breach reporting, DSARs",
        "course_type": "compliance",
        "expected_bucket": "compliance",
    },
    {
        "title": "Statistical Analysis for Product Decisions",
        "description": "Run A/B tests, compute confidence intervals, avoid common stats mistakes",
        "course_type": "technical",
        "expected_bucket": "data-analysis",
    },
    {
        "title": "Scaling a Fintech from 10K to 1M Users",
        "description": "Hit growth milestones while managing compliance, infra cost, and incident rates",
        "course_type": "case_study",
        "expected_bucket": "case-study",
    },
    {
        "title": "Technical Writing for Engineers",
        "description": "Write docs, RFCs, and post-mortems that actually get read and drive decisions",
        "course_type": "technical",
        "expected_bucket": "writing",
    },
    {
        "title": "Negotiation Skills for Tech Leads",
        "description": "Negotiate scope, headcount, deadlines with stakeholders who have more power",
        "course_type": "case_study",
        "expected_bucket": "negotiation",
    },
    {
        "title": "Growth Hacking with AI for B2B SaaS",
        "description": "Use AI to identify growth levers, automate personalization, and measure lift",
        "course_type": "technical",
        "expected_bucket": "marketing",
    },
    {
        "title": "Financial Modeling for Startup Founders",
        "description": "Build defensible unit economics models, forecast cash runway, prepare for VC diligence",
        "course_type": "case_study",
        "expected_bucket": "finance",
    },
]


def _post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}
    except Exception as e:
        return -1, {"error": str(e)[:300]}


def _get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return -1, {"error": str(e)[:300]}


async def generate_one(course_spec, idx):
    """Run start -> refine -> generate for one course."""
    t0 = time.time()
    # 1. Start
    status, start_resp = await asyncio.to_thread(_post, "/api/creator/start", {
        "title": course_spec["title"],
        "description": course_spec["description"],
        "course_type": course_spec["course_type"],
    })
    if status != 200:
        return {**course_spec, "status": f"start_failed({status})", "elapsed": time.time() - t0,
                "error": start_resp.get("error", ""), "course_id": None}

    session_id = start_resp["session_id"]
    questions = start_resp.get("questions", [])
    # Auto-answer with plausible text
    answers = []
    for q in questions[:4]:
        ans = "Yes, include this with comprehensive real-world examples."
        if q.get("type") == "choice" and q.get("options"):
            ans = q["options"][0]
        answers.append({"question_id": q["id"], "answer": ans})

    # 2. Refine
    status, refine_resp = await asyncio.to_thread(_post, "/api/creator/refine", {
        "session_id": session_id,
        "answers": answers,
    })
    if status != 200:
        return {**course_spec, "status": f"refine_failed({status})", "elapsed": time.time() - t0,
                "error": refine_resp.get("error", ""), "course_id": None}

    outline = refine_resp["outline"]
    num_modules = len(outline["modules"])
    total_steps = sum(len(m["steps"]) for m in outline["modules"])

    # 3. Generate
    status, gen_resp = await asyncio.to_thread(_post, "/api/creator/generate", {
        "session_id": session_id,
        "outline": outline,
    })
    elapsed = time.time() - t0
    if status != 200:
        return {**course_spec, "status": f"generate_failed({status})",
                "elapsed": elapsed, "error": gen_resp.get("error", ""),
                "modules": num_modules, "total_steps": total_steps, "course_id": None}

    return {
        **course_spec,
        "status": "OK",
        "elapsed": elapsed,
        "course_id": gen_resp.get("course_id"),
        "modules": num_modules,
        "total_steps": total_steps,
    }


async def main():
    print(f"Generating {len(COURSES)} courses (bounded concurrency=3)...")
    semaphore = asyncio.Semaphore(3)

    async def bounded(spec, idx):
        async with semaphore:
            print(f"  [{idx+1}/{len(COURSES)}] Starting: {spec['title'][:50]}")
            result = await generate_one(spec, idx)
            print(f"  [{idx+1}/{len(COURSES)}] Done ({result['status']}, {result.get('elapsed', 0):.0f}s): {spec['title'][:50]}")
            return result

    results = await asyncio.gather(*[bounded(spec, i) for i, spec in enumerate(COURSES)])

    print("\n\n============ SUMMARY ============")
    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"Succeeded: {ok}/{len(COURSES)}")
    for r in results:
        marker = "✓" if r["status"] == "OK" else "✗"
        cid = r.get("course_id", "-")
        steps_info = ""
        if "total_steps" in r:
            steps_info = f" [{r.get('modules','?')}M/{r.get('total_steps','?')}S]"
        err = f" err={r.get('error','')[:100]}" if r.get("error") else ""
        print(f"  {marker} [{r['expected_bucket']:15}] {r['title'][:50]:<50} → {cid} ({r.get('elapsed', 0):.0f}s){steps_info}{err}")

    # Save results to a file for reviewer agents to pick up
    with open("/tmp/bulk_course_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to /tmp/bulk_course_results.json")


if __name__ == "__main__":
    asyncio.run(main())
