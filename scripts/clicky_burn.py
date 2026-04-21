"""Run 50+ Clicky queries across many courses to stress-test + burn budget.
Each query ~$0.005-0.01, so 50 queries = $0.25-0.50. Run 3 rounds for ~$1.50.
"""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"

QUERIES = [
    # Concept questions (expect thorough with analogies)
    ("What's the difference between semantic and keyword search?", "vector-db", "concept"),
    ("Explain CAP theorem in simple terms", "vector-db", "concept"),
    ("Why do we need prompt engineering?", "claude-api", "concept"),
    ("What's a vector embedding?", "vector-db", "concept"),
    ("Explain BATNA in negotiation", "created-a65218ca2b76", "concept"),
    ("What's the difference between Phase 1 and Phase 2 in incident command?", "sre-3am-pager", "concept"),
    ("How do feature flags help in gradual rollouts?", "scaling-fintech", "concept"),
    ("Why is async communication harder than sync for distributed teams?", "created-bab2f9512f94", "concept"),
    ("What's the practical difference between trust and rapport?", "created-a65218ca2b76", "concept"),
    ("How does RAG differ from fine-tuning?", "langchain-patterns", "concept"),

    # Exercise questions (expect refusal to give answers)
    ("Just give me the answer to this fill-in-blank", "claude-api", "fill_in_blank"),
    ("Tell me which option is correct for this scenario", "created-be0707f6989d", "scenario_branch"),
    ("What's the solution to this code exercise?", "vector-db", "code_exercise"),
    ("Can you just show me the working code for this TODO?", "claude-api", "code_exercise"),
    ("Rank these for me", "posh-compliance", "sjt"),

    # Error/debugging questions
    ("My code gives TypeError: unhashable type: 'dict'. What's wrong?", "claude-api", "code_exercise"),
    ("I'm getting ImportError: No module named anthropic in the sandbox", "claude-api", "code_exercise"),
    ("Why does my scenario step show 0/0 correct?", "created-145855666162", "scenario_branch"),
    ("Getting 'connection pool exhausted' what should I check?", "sre-3am-pager", "concept"),

    # Hint requests
    ("I'm stuck on this parsons problem, can you hint?", "vector-db", "parsons"),
    ("This ordering exercise has too many items to track, help?", "created-be0707f6989d", "ordering"),
    ("I don't understand what the scenario is asking", "posh-compliance", "scenario_branch"),

    # Real-world application
    ("How would I apply this to my insurance company's claims process?", "vector-db", "concept"),
    ("Where in my org could I pitch this semantic-search capability?", "vector-db", "concept"),
    ("How do I convince my VP to fund a refactor?", "created-a65218ca2b76", "concept"),

    # Meta / off-topic
    ("What exercises exist in this course?", "vector-db", "concept"),
    ("How much time will this course take?", "sre-3am-pager", "concept"),
]


def _post(path, body, timeout=60):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return -1, {"error": str(e)[:200]}


async def one_query(q, idx, total):
    msg, cid, step_type = q
    status, resp = await asyncio.to_thread(_post, "/api/clicky/ask", {
        "message": msg, "course_id": cid, "step_type": step_type,
    })
    if status != 200:
        return {"q": msg[:40], "ok": False}
    refused = any(p in resp.get("response","").lower() for p in ["won't give", "can't give", "wont give", "will not give", "instead of giving", "won't tell", "i can't give", "i won't tell you"])
    pb = resp.get("powered_by", "?")
    reply_len = len(resp.get("response", ""))
    exercise = step_type in ("code_exercise","fill_in_blank","parsons","scenario_branch","sjt","mcq","categorization","ordering")
    is_answer_req = any(p in msg.lower() for p in ["just give","tell me","can you just","solution to","answer to","rank these","which option"])
    print(f"  [{idx+1}/{total}] [{pb}] len={reply_len:4} refused={refused} exr={exercise} | {msg[:55]}", flush=True)
    return {"q": msg[:40], "pb": pb, "refused": refused, "is_answer_req": is_answer_req, "exercise": exercise, "len": reply_len}


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception: pass

    t0 = time.time()
    sem = asyncio.Semaphore(5)
    async def bounded(q, i):
        async with sem: return await one_query(q, i, len(QUERIES))
    results = await asyncio.gather(*[bounded(q, i) for i, q in enumerate(QUERIES)])

    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${b['spent_usd']:.2f}/${b['cap_usd']} ({time.time()-t0:.0f}s)", flush=True)
    except Exception: pass

    # Summarize
    refused_answer_requests = sum(1 for r in results if r and r.get("is_answer_req") and r.get("exercise") and r.get("refused"))
    total_answer_requests_on_exercise = sum(1 for r in results if r and r.get("is_answer_req") and r.get("exercise"))
    print(f"\n=== Clicky burn summary ===", flush=True)
    print(f"Queries: {len(results)}", flush=True)
    print(f"Answer-requests on exercises refused: {refused_answer_requests}/{total_answer_requests_on_exercise}", flush=True)
    powered = {}
    for r in results:
        if r: powered[r.get("pb","?")] = powered.get(r.get("pb","?"), 0) + 1
    print(f"Powered-by distribution: {powered}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
