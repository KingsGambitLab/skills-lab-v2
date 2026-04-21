"""Run multiple adaptive_roleplay sessions to stress-test the pedagogy.

- Creates 10 concurrent "learner" personas with different strategies
- Each runs a full 5-10 turn conversation against Diana VP
- Tracks which strategies lead to concede / escalate / walk_away / timeout
- Expected cost: ~$2-4 ($0.01-0.02 per turn × 50-100 turns)
"""
import asyncio, json, time, urllib.request

BASE = "http://localhost:8001"

LEARNER_PERSONAS = [
    # Data-driven, specific, collaborative — should concede
    ["I hear you. Our burn-down shows 14 weeks at current velocity; Q2 ends in 10. What business outcome do you need for the board?",
     "Phase 1 by end of Q2: top-3 merchant flows (80% volume) behind feature flag, 2-week ramp. Phase 2 in Q3 after we've learned velocity. Specific, measurable, defensible.",
     "For Phase 2 commit date: end of Phase 1 sprint 2 once we have real data. Giving you a Q3 date today would be guessing."],
    # Hedging, vague — should erode patience
    ["We'll try our best to make it work.",
     "The team is pretty burnt out right now.",
     "Let me see what I can do.",
     "We'll get close to Q2."],
    # Combative — should escalate
    ["That's not realistic. You're asking the impossible.",
     "Engineering can't work miracles. Your timeline is wrong.",
     "Why don't you tell the board it'll slip?"],
    # Over-committer — loses trust
    ["Sure, we can hit Q2. Full platform. No problem.",
     "I'll personally guarantee it.",
     "We'll just work overtime to make it happen."],
    # Curious, asks good questions — should build trust
    ["What business outcome does 'Q2 live' actually serve? Is it the board message, a contract commitment, or a competitive window?",
     "If we shipped just the 3 flows that carry 80% of volume, does that solve the board message?",
     "Here's what I can commit: Phase 1 by Q2, with explicit rollback plan. Phase 2 timing set after Phase 1 data."],
    # Data + alternative + acknowledges her constraints
    ["Diana, I hear the pressure. Let me lay out the numbers honestly: 14 weeks minimum, Q2 is 10. Gap is 4 weeks. Here's what I can do within Q2: top-3 merchant flows, 80% volume, feature-flag gated.",
     "That gives you a compelling board story AND lets us preserve engineering credibility. Phase 2 commit comes after Phase 1 ships with real data.",
     "I'll have the Phase 1 scope documented by Friday. Weekly check-ins on progress — you'll know about blockers within 24h."],
]


def _post(path, body, timeout=60):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return -1, {"error": str(e)[:200]}


async def run_one(persona_idx, turns):
    # Find the roleplay step ID
    step_id = 462  # known from earlier; will verify
    label = f"learner-{persona_idx+1}"
    print(f"  [{label}] starting...", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/roleplay/start", {"step_id": step_id})
    if status != 200:
        print(f"  [{label}] start failed: {start}", flush=True)
        return {"label": label, "outcome": "start_failed"}
    sid = start["session_id"]
    outcome = "continue"
    turn_count = 0
    for msg in turns:
        if outcome != "continue":
            break
        status, resp = await asyncio.to_thread(_post, "/api/roleplay/turn", {"session_id": sid, "message": msg})
        if status != 200:
            print(f"  [{label}] turn failed: {resp}", flush=True)
            outcome = "error"
            break
        outcome = resp.get("outcome", "continue")
        turn_count = resp.get("turn", turn_count)
    debrief = resp.get("debrief", {}) if outcome != "continue" and outcome != "error" else {}
    print(f"  [{label}] outcome={outcome} turns={turn_count} score={debrief.get('score','?')}", flush=True)
    return {
        "label": label, "outcome": outcome, "turns": turn_count,
        "score": debrief.get("score", 0),
        "final_state": debrief.get("final_state", {}),
    }


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception:
        pass

    sem = asyncio.Semaphore(3)
    async def bounded(persona_idx, turns):
        async with sem:
            return await run_one(persona_idx, turns)
    tasks = [bounded(i, turns) for i, turns in enumerate(LEARNER_PERSONAS)]
    results = await asyncio.gather(*tasks)

    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${b['spent_usd']:.2f}/${b['cap_usd']}", flush=True)
    except Exception:
        pass

    print("\n=== Stress test summary ===", flush=True)
    outcomes = {}
    for r in results:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    print(f"Outcomes distribution: {outcomes}", flush=True)
    for r in results:
        print(f"  {r['label']}: outcome={r['outcome']} turns={r['turns']} score={r['score']} final={r.get('final_state',{})}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
