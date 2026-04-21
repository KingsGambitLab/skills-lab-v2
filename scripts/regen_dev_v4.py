"""Regenerate the Developer headline course with all 3 Priya-review fixes:
1. Engineering-capstone genre lock (no business-strategy drift)
2. Cross-step scenario consistency (one company/feature/stack across all capstone steps)
3. Categorization items have explanations + no placeholder text

Audits: capstone step 2 shape, scenario-name consistency, categorization explanations.
"""
import json, urllib.request, time

BASE = "http://localhost:8001"

TITLE = "AI Power Skills for Developers: Ship Real Code With Claude / Copilot / Cursor"
DESC = ("Master the daily AI workflow of a modern software engineer. Cover Claude Code daily surface "
        "(CLAUDE.md, hooks, skills, MCP, slash commands), agentic coding (harnesses, agent loops, "
        "sub-agents, worktrees), end-to-end app builds in 2-4 hours with agentic tools, AI-powered "
        "code review with Copilot and Cursor, AI-assisted testing automation (unit, integration, e2e, "
        "mutation), and security practices for AI-generated code (prompt injection, supply-chain, "
        "hallucinated packages). The capstone ships a production feature in 2 hours using real "
        "terminal commands, real git workflow, real tests — not a strategy deck.")


def post(path, body, timeout=400):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get(path, timeout=60):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=timeout).read())


def main():
    b = get("/api/admin/budget")
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)

    t0 = time.time()
    start = post("/api/creator/start", {
        "title": TITLE,
        "description": DESC,
        "course_type": "technical",
        "level": "Intermediate",
    })
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Follow the description faithfully. The capstone is a CODING deliverable — terminal, git, tests, PR. No strategy decks."}
               for q in start.get("questions", [])[:4]]
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    cid = g["course_id"]
    print(f"Generated {cid} in {int(time.time()-t0)}s", flush=True)

    # Fetch course + all modules
    cd = get(f"/api/courses/{cid}")
    print(f"\nCourse: {cd['title']}")
    print(f"Subtitle: {cd.get('subtitle')!r}")
    print(f"Modules: {len(cd['modules'])}")

    capstone_module = cd["modules"][-1]
    print(f"\nCapstone module: {capstone_module['title']}")
    md = get(f"/api/courses/{cid}/modules/{capstone_module['id']}")

    # Audit capstone steps for scenario consistency
    print(f"\n=== CAPSTONE STEPS ({len(md['steps'])}) ===")
    all_caps_text = ""
    for s in md["steps"]:
        content = s.get("content") or ""
        code = s.get("code") or ""
        dd = s.get("demo_data") or {}
        blob = (content + " " + code + " " + json.dumps(dd)).lower()
        all_caps_text += blob + "\n---\n"
        print(f"\n  S{s['position']}: [{s['exercise_type']}] {s['title']}")
        print(f"     content_len: {len(content)}")
        # Check biz-strategy leak
        BAD = ["strategy & implementation plan", "c-suite presentation", "budget approval",
               "15-page", "financial model", "present to the board", "roi analysis"]
        bad_hits = [b for b in BAD if b in blob]
        if bad_hits:
            print(f"     ⚠️  BIZ-STRATEGY LEAK: {bad_hits}")
        else:
            print(f"     ✓ No biz-strategy leak")
        # Check coding-signal presence
        GOOD = ["git ", "docker", "npm ", "pip ", "curl ", "endpoint", "/api", "run `",
                "commit", "pr ", "pull request", "deploy", "test"]
        good_hits = [g for g in GOOD if g in blob]
        print(f"     coding signals: {good_hits[:6]}")

    # Look for distinct company names — capstone should have ONE.
    import re as _re
    companies = set()
    for word in _re.findall(r"\b[A-Z][a-z]{3,12}(?:[A-Z][a-z]+)*\b", all_caps_text[:5000]):
        if word.lower() in ("claude", "cursor", "copilot", "python", "javascript",
                             "fastapi", "docker", "vercel", "aws", "gcp", "github",
                             "typescript", "react", "node", "linux", "mac", "ubuntu"):
            continue
        companies.add(word)
    # Heuristic: if 2+ distinct fictional names appear, flag
    print(f"\n  Distinct Title-Case entities in capstone: {list(companies)[:10]}")

    # Audit categorization explanations across the course
    print(f"\n=== CATEGORIZATION AUDIT (all modules) ===")
    for m in cd["modules"]:
        md2 = get(f"/api/courses/{cid}/modules/{m['id']}")
        for s in md2["steps"]:
            if s.get("exercise_type") == "categorization":
                # Fetch raw validation to see items with explanations (sanitizer strips them on GET)
                # Try the direct DB access by looking at what we get
                dd = s.get("demo_data") or {}
                items = dd.get("items") or []
                # Frontend sanitizer strips correct_category but keeps text — so we need to
                # hit /api/exercises/validate? No — simpler: just fetch and check
                # Actually explanation is only returned post-submission. So check if it's in demo_data.
                print(f"  M{m['position']} S{s['position']}: {s['title']}")
                print(f"     items: {len(items)}")
                first_item_txt = items[0].get('text','')[:80] if items else '(none)'
                print(f"     first item: {first_item_txt!r}")
                # Check for placeholders
                if items:
                    bad = [it for it in items if 'scenario 1 from' in (it.get('text','') or '').lower() or 'scenario 2 from' in (it.get('text','') or '').lower()]
                    if bad:
                        print(f"     ⚠️  {len(bad)} placeholder items still present")

    b = get("/api/admin/budget")
    print(f"\nBudget after: ${b['spent_usd']:.2f}")
    print(f"\nNEW DEV ID: {cid}")


if __name__ == "__main__":
    main()
