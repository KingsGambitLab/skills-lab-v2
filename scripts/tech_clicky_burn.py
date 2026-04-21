"""Clicky burn targeting the 5 new tech-function courses.
~25 queries × ~$0.01 = ~$0.25 burn. Validates Clicky handles the new domains.
"""
import asyncio, json, urllib.request

BASE = "http://localhost:8001"

# Tech-function course IDs from latest wave
COURSES = {
    "sales_eng": "created-5ab75bbb8414",
    "data_analyst": "created-e4f8931af85c",
    "tech_writer": "created-f16e2ef7af0f",
    "devops": "created-58acb17bf345",
    "security": "created-f1b3a90c7cfe",
}

QUERIES = [
    # Sales Engineer
    ("How do I respond when a CTO in a technical eval says our competitor's vector DB is 'good enough'?", COURSES["sales_eng"], "adaptive_roleplay"),
    ("What's the best prompt to turn a 60-min discovery call transcript into a scoped POC plan?", COURSES["sales_eng"], "concept"),
    ("Prospect keeps pushing for a custom benchmark. How do I scope it without burning my SA budget?", COURSES["sales_eng"], "adaptive_roleplay"),
    ("How do I detect 'zombie' deals in my pipeline using LLM analysis of Gong calls?", COURSES["sales_eng"], "concept"),
    ("Walk me through using Claude to audit our RFP responses for technical accuracy.", COURSES["sales_eng"], "concept"),

    # Data Analyst
    ("How do I detect Simpson's paradox in my churn analysis?", COURSES["data_analyst"], "concept"),
    ("CEO wants to know 'why is North region down 5%' in 15 min. How do I approach?", COURSES["data_analyst"], "adaptive_roleplay"),
    ("What prompt structure turns a messy CSV into a clean pandas DataFrame with type inference?", COURSES["data_analyst"], "code_exercise"),
    ("My dashboard shows stable metrics, but my LLM-generated narrative says it's declining. Who's right?", COURSES["data_analyst"], "concept"),
    ("How do I explain confidence intervals to a non-technical VP without losing credibility?", COURSES["data_analyst"], "concept"),

    # Tech Writer
    ("Reviewer says my docs are 'too verbose'. How do I cut without losing beginner accessibility?", COURSES["tech_writer"], "adaptive_roleplay"),
    ("What's a good way to auto-generate code samples from an OpenAPI spec using Claude?", COURSES["tech_writer"], "code_exercise"),
    ("How do I know where users get stuck in my docs without explicit feedback?", COURSES["tech_writer"], "concept"),
    ("Product manager wants the docs ready tomorrow. How do I negotiate scope?", COURSES["tech_writer"], "adaptive_roleplay"),

    # DevOps
    ("K8s pod is in CrashLoopBackOff. What are my first 3 kubectl commands?", COURSES["devops"], "incident_console"),
    ("How do I generate a Terraform module for a 3-AZ RDS Postgres from plain English?", COURSES["devops"], "code_exercise"),
    ("CI pipeline is flaky — fails 1-in-5 builds. How do I triage with Claude?", COURSES["devops"], "concept"),
    ("My on-call senior just quit. How do I upskill junior engineers fast?", COURSES["devops"], "concept"),
    ("CTO is pressuring me to skip the staging environment to hit ship date. How do I push back?", COURSES["devops"], "adaptive_roleplay"),

    # Security
    ("How do I triage 500 SIEM alerts per shift without missing real threats?", COURSES["security"], "concept"),
    ("Credential stuffing attack at 4 AM. What's my first 10-minute plan?", COURSES["security"], "incident_console"),
    ("CEO is asking 'did customer data leak' during incident. How do I respond without speculating?", COURSES["security"], "adaptive_roleplay"),
    ("How do I prompt Claude to red-team my own IR playbook?", COURSES["security"], "concept"),
    ("Engineer checked a secret into public GitHub. What's my next 5 moves?", COURSES["security"], "incident_console"),
    ("CISO wants daily phishing-awareness emails. How do I auto-generate without them looking AI-generated?", COURSES["security"], "concept"),
]


def _post(path, body, timeout=60):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except Exception as e: return -1, {"error": str(e)[:200]}


async def run_one(q, idx, total):
    msg, cid, step_type = q
    status, resp = await asyncio.to_thread(_post, "/api/clicky/ask", {"message": msg, "course_id": cid, "step_type": step_type})
    if status != 200:
        print(f"  [{idx+1}/{total}] failed", flush=True); return
    reply_len = len(resp.get("response", ""))
    pb = resp.get("powered_by", "?")
    refused = "refuse" in resp.get("response", "").lower()[:200] or "can't just" in resp.get("response", "").lower()[:300] or "not going to hand" in resp.get("response", "").lower()[:300]
    flag = " [REFUSE]" if (step_type != "concept" and refused) else ""
    print(f"  [{idx+1}/{total}] [{pb}] len={reply_len}{flag} | {msg[:60]}", flush=True)
    return {"len": reply_len}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(5)
    async def bounded(q, i):
        async with sem: return await run_one(q, i, len(QUERIES))
    results = await asyncio.gather(*[bounded(q, i) for i, q in enumerate(QUERIES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
