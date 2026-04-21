"""Regenerate Dev v6 with:
- Extended banlist (playbook, agent strategy doc, velocity metrics presentation)
- Retry-on-incomplete (1 retry per step if _is_complete rejects)
- All-module scenario consistency
- MUST-EMIT code-artifact prompt tightening

Serial, 900s timeout.
"""
import json, urllib.request, time

BASE = "http://localhost:8001"


def post(path, body, timeout=900):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    t0 = time.time()
    start = post("/api/creator/start", {
        "title": "AI Power Skills for Developers: Ship Real Code With Claude / Copilot / Cursor",
        "description": "Master the daily AI workflow of a modern software engineer. Cover Claude Code daily surface (CLAUDE.md, hooks, skills, MCP, slash commands), agentic coding (harnesses, agent loops, sub-agents, worktrees), end-to-end app builds in 2-4 hours, AI-powered code review, testing automation, and security practices. The capstone is a HANDS-ON coding deliverable — run `claude`, write code, execute `pytest`, open a PR with `gh pr create`, deploy. Zero strategy documents, zero playbooks, zero executive presentations.",
        "course_type": "technical",
        "level": "Intermediate",
    }, timeout=120)
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Ship CODE. Every step produces terminal commands, code, or test output. No docs, no decks, no matrices, no playbooks."}
               for q in start.get("questions", [])[:4]]
    print(f"  refining outline...", flush=True)
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
    print(f"  generating course ({len(refine['outline']['modules'])} modules)...", flush=True)
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=900)
    cid = g["course_id"]
    elapsed = int(time.time()-t0)
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    print(f"  DONE: {cid} in {elapsed}s — {len(cd['modules'])} modules", flush=True)
    print(f"  subtitle: {cd.get('subtitle')!r}", flush=True)
    # Quick capstone audit
    capstone = cd["modules"][-1]
    md = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{capstone['id']}", timeout=30).read())
    print(f"\nCapstone steps:")
    for s in md["steps"]:
        content = (s.get("content") or "") + " " + json.dumps(s.get("demo_data") or {})
        content_lo = content.lower()
        biz_hits = [p for p in ["playbook", "strategy document", "responsibility matrix",
                                 "engineering leadership presentation", "velocity metrics",
                                 "executive deck", "cpo presentation"]
                    if p in content_lo]
        code_hits = [p for p in ["pytest", "git commit", "`git ", "gh pr", "docker build",
                                 "curl ", "npm ", "claude ", "```bash", "```sh"]
                     if p in content_lo]
        verdict = "🚨 BIZ-DRIFT" if biz_hits else ("✓ code" if code_hits else "? neutral")
        print(f"  S{s['position']}: [{s['exercise_type']}] {s['title'][:60]} {verdict}")
        if biz_hits:
            print(f"     leak: {biz_hits}")
        if code_hits:
            print(f"     code: {code_hits[:3]}")

    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b['spent_usd']:.2f}")
    print(f"\nNEW DEV ID: {cid}")


if __name__ == "__main__":
    main()
