"""Regenerate PM v6. Addresses Sarah v5 findings:
- Module 1 Step 1 shipped "automated content generation for this step was incomplete.
  Ask your course builder or ping #lms-content to regenerate" fallback → fixed by
  retry-on-incomplete (1 retry before fallback) and softer fallback text.
- Capstone Module 8→9 drifted CloudSync → FlowSpace → fixed by all-module scenario
  injection (the invented scenario now threads through EVERY module, not just capstone).
- Module 5 still no named tools → primer+prompt now more aggressive about naming.
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
        "title": "Master AI Skills for Product Managers: From PRDs to Launch With AI",
        "description": "Master the daily AI workflow of a modern PM. Cover AI-assisted discovery (interview synthesis with Dovetail/EnjoyHQ, JTBD extraction), PRD writing with AI (user stories, edge cases, adversarial review), competitive intelligence (Crayon, Klue, Kompyte), launch decisions, metrics and experimentation (Amplitude, Looker, Hex), and stakeholder communication. Capstone is ONE coherent scenario — one PM at one company facing one launch-day decision, threaded through every step. No bouncing between fictional companies or swapping persona names.",
        "course_type": "case_study",
        "level": "Intermediate",
    }, timeout=400)
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "ONE coherent scenario threaded through all 9 modules. Same company, same PM, same product. Name specific PM tools (Dovetail, Amplitude, Crayon, Klue, Linear, Notion)."}
               for q in start.get("questions", [])[:4]]
    print(f"  refining outline...", flush=True)
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=600)
    print(f"  generating course ({len(refine['outline']['modules'])} modules)...", flush=True)
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=900)
    cid = g["course_id"]
    elapsed = int(time.time()-t0)
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    print(f"  DONE: {cid} in {elapsed}s — {len(cd['modules'])} modules", flush=True)
    print(f"  subtitle: {cd.get('subtitle')!r}", flush=True)

    # Audit: does the fallback-text leak appear anywhere? Does the scenario stay coherent?
    print(f"\n=== AUDIT ===")
    fallback_leaks = 0
    tool_hits = 0
    TOOLS = ["dovetail", "amplitude", "looker", "crayon", "klue", "kompyte",
             "linear", "notion", "hex", "tableau", "gong"]
    companies_found = set()
    import re as _re
    for m in cd["modules"]:
        md = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}", timeout=30).read())
        for s in md["steps"]:
            c = (s.get("content") or "") + " " + json.dumps(s.get("demo_data") or {})
            c_lo = c.lower()
            if "automated content generation for this step was incomplete" in c_lo:
                fallback_leaks += 1
                print(f"  ⚠️  FALLBACK LEAK: M{m['position']} S{s['position']}: {s['title']}")
            for t in TOOLS:
                if t in c_lo:
                    tool_hits += 1
                    break
            # Capture Title-Case fictional companies (heuristic)
            for w in _re.findall(r"\b([A-Z][a-z]{3,10}[A-Z][a-z]{2,10}|[A-Z][a-z]{4,15})\b", c[:2000]):
                if w.lower() in {"claude", "cursor", "copilot", "python", "linear", "notion",
                                  "amplitude", "dovetail", "looker", "tableau", "crayon", "klue",
                                  "gong", "slack", "github", "jira", "figma", "monday", "stripe"}:
                    continue
                if len(w) >= 6:
                    companies_found.add(w)
    print(f"\n  Fallback-text leaks: {fallback_leaks}")
    print(f"  Modules mentioning named tools: {tool_hits}")
    print(f"  Distinct Title-Case possibly-fictional entities: {list(companies_found)[:12]}")

    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b['spent_usd']:.2f}")
    print(f"\nNEW PM ID: {cid}")


if __name__ == "__main__":
    main()
