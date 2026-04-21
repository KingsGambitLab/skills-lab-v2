"""Deep Clicky burn — 40+ multi-turn conversations to stress-test teaching quality at scale.

Some are multi-turn (5 messages) to test conversational continuity / history.
Others are single queries across unusual domains.
~$2-3 burn.
"""
import asyncio, json, urllib.request, time

BASE = "http://localhost:8001"


MULTITURN_DIALOGUES = [
    # Concept deep-dive
    [
        ("Explain vector search vs keyword search", "vector-db", "concept", None),
        ("OK so what's an embedding model?", "vector-db", "concept", "prev:1"),
        ("How do I choose between Ada-002 and BGE?", "vector-db", "concept", "prev:2"),
    ],
    # Debugging back-and-forth
    [
        ("My FastAPI is returning 503s in production", "langchain-patterns", "code_exercise", None),
        ("The upstream Claude API is fine — verified", "langchain-patterns", "code_exercise", "prev:1"),
        ("Ah, my connection pool — how do I tune that?", "langchain-patterns", "code_exercise", "prev:2"),
    ],
    # Negotiation coaching
    [
        ("I'm about to ask my VP for a larger budget. How do I prep?", "created-a65218ca2b76", "concept", None),
        ("I don't have competitive offers — what else can I anchor on?", "created-a65218ca2b76", "concept", "prev:1"),
        ("OK got it. What's the worst move I could make in the first 60 seconds?", "created-a65218ca2b76", "concept", "prev:2"),
    ],
    # User interview coaching
    [
        ("I keep accidentally asking leading questions. How do I stop?", "created-f900d10407dd", "concept", None),
        ("Give me an example of 'neutral silence' vs 'awkward silence'", "created-f900d10407dd", "concept", "prev:1"),
    ],
]

SINGLE_QUERIES = [
    "What's eventual consistency and when would I choose it over strong consistency?",
    "How do I tell if my data is biased before training on it?",
    "Explain OAuth 2 PKCE flow like I'm new to it",
    "What's the difference between a memory leak and a GC issue?",
    "How do I estimate DB connection pool size for my app?",
    "What's a good way to review a PR with 50+ file changes?",
    "Explain sampling in distributed tracing",
    "What's service mesh and when is it overkill?",
    "How do I structure a team retro that actually leads to change?",
    "What's the difference between 'disagree and commit' and 'capitulate'?",
    "How should I structure a one-on-one with a senior engineer?",
    "Explain RLHF vs DPO in simple terms",
    "How do I calculate the TAM for a B2B SaaS product?",
    "What's the Dunning-Kruger effect in engineering interviews?",
    "How do I handle a colleague who's gaslighting me in code reviews?",
]


def _post(path, body, timeout=60):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except Exception as e: return -1, {"error": str(e)[:200]}


async def run_multiturn(dialog, idx):
    history = []
    results = []
    for turn_idx, (msg, cid, step_type, _) in enumerate(dialog):
        status, resp = await asyncio.to_thread(_post, "/api/clicky/ask", {
            "message": msg, "course_id": cid, "step_type": step_type,
            "history": history,
        })
        if status != 200:
            print(f"  [MT{idx+1}.{turn_idx+1}] failed: {resp}", flush=True); break
        reply = resp.get("response", "")
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})
        results.append({"turn": turn_idx+1, "len": len(reply)})
    total = sum(r["len"] for r in results)
    print(f"  [MT{idx+1}] dialog length {len(dialog)} turns, total reply chars: {total}", flush=True)


async def run_single(msg, idx):
    status, resp = await asyncio.to_thread(_post, "/api/clicky/ask", {"message": msg})
    if status != 200:
        print(f"  [SQ{idx+1}] failed: {resp}", flush=True); return
    reply_len = len(resp.get("response", ""))
    pb = resp.get("powered_by", "?")
    print(f"  [SQ{idx+1}] [{pb}] len={reply_len} | {msg[:55]}", flush=True)


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass

    t0 = time.time()
    sem = asyncio.Semaphore(4)

    async def bounded_mt(dialog, i):
        async with sem: await run_multiturn(dialog, i)
    async def bounded_sq(msg, i):
        async with sem: await run_single(msg, i)

    tasks = [bounded_mt(d, i) for i, d in enumerate(MULTITURN_DIALOGUES)]
    tasks += [bounded_sq(q, i) for i, q in enumerate(SINGLE_QUERIES)]
    await asyncio.gather(*tasks)

    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${b['spent_usd']:.2f} ({time.time()-t0:.0f}s)", flush=True)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
