"""Domain-specific Clicky queries to validate that Clicky handles function-specific questions well.
25 queries × ~$0.005-0.01 = $0.15-0.25 — modest burn.
"""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"

QUERIES = [
    # Finance
    ("How do I prompt Claude to classify 500 expense line items?", "created-288a62e7c76f", "concept"),
    ("My AI reconciliation bot keeps flagging false positives. How do I tune?", "created-288a62e7c76f", "code_exercise"),
    ("How should I present an AI-generated forecast to my CFO?", "created-b7e20905a0f9", "concept"),
    ("What bias should I worry about in LLM-generated variance commentary?", "created-288a62e7c76f", "concept"),
    # Recruitment
    ("How do I prompt Claude to score resumes without creating bias?", "created-470bc8ea6764", "concept"),
    ("A candidate pushed back on my comp offer. What's my best move?", "created-470bc8ea6764", "adaptive_roleplay"),
    ("A hiring manager wants to override a no-hire recommendation. How do I respond?", "created-470bc8ea6764", "adaptive_roleplay"),
    # Product
    ("How do I synthesize 50 user interviews with LLMs without losing nuance?", "created-1082a1d682a4", "concept"),
    ("What's a good prompt for generating JTBD statements?", "created-1082a1d682a4", "code_exercise"),
    ("My A/B test shows +3% lift with p=0.04. Should I ship?", "created-8908775a2475", "concept"),
    ("How do I detect sample ratio mismatch in an A/B test?", "created-8908775a2475", "code_exercise"),
    # Design
    ("How do I critique my own mockups with an LLM?", "created-c8d1159a7f0f", "concept"),
    ("An engineering lead wants evidence for my design decisions. How do I respond?", "created-c8d1159a7f0f", "adaptive_roleplay"),
    # HR
    ("A manager wants to PIP an employee without documentation. What's my playbook?", "created-73c2e08e7262", "concept"),
    ("How do I detect attrition signals in engagement survey data?", "created-73c2e08e7262", "code_exercise"),
    # Legal
    ("How do I red-line a 40-page SaaS MSA with Claude efficiently?", "created-89f1694bef4c", "concept"),
    ("Sales is pushing to accept uncapped liability. How do I push back?", "created-89f1694bef4c", "adaptive_roleplay"),
    # Marketing
    ("How do I prove which channels actually drove pipeline?", "created-a960b2c335c1", "concept"),
    ("CFO is questioning my attribution model. How do I defend?", "created-a960b2c335c1", "adaptive_roleplay"),
    # Ops
    ("How do I auto-classify 10K support tickets?", "created-663872e56398", "concept"),
    ("SLA-breach model has 30% false-positive rate. How do I debug?", "created-663872e56398", "code_exercise"),
    # CS
    ("How do I extract churn-risk signals from Gong call transcripts?", "created-afc141eb0fe8", "concept"),
    ("A CSM has a renewal call tomorrow and is unprepared. How do I coach?", "created-afc141eb0fe8", "adaptive_roleplay"),
    # Exec
    ("I'm making a $5M bet with conflicting advisor recs. How do I decide?", "created-c4c529c6bbc4", "concept"),
    ("How do I red-team my own strategy memo with an LLM?", "created-c4c529c6bbc4", "concept"),
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
    print(f"  [{idx+1}/{total}] [{pb}] len={reply_len} | {msg[:65]}", flush=True)
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
