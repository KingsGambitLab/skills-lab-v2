"""Regenerate Design + Chief of Staff + Finance courses with the v7 Creator
(cast roster + all-module scenario + MUST-EMIT + filler-fallback-fix + flat-validator).

Serial, 1200s timeout, parallel would saturate Anthropic API.
"""
import json, urllib.request, time

BASE = "http://localhost:8001"

JOBS = [
    {
        "slug": "design",
        "title": "AI for Designers: From Research Synthesis to Production Mockups",
        "description": "Master the daily AI workflow of a modern Product Designer. Cover AI-accelerated user research synthesis (Dovetail/Notably transcript clustering, JTBD extraction), AI-assisted wireframing (Figma + Figma Make, UX Pilot, Galileo, Visily, Uizard, Musho), design-system naming + token generation with AI, accessibility + WCAG checks via AI, production-mockup handoff to engineering, and stakeholder design-critique prep. Capstone threads ONE real product (one company, one feature) from research through production mockup — not a meta-doc about AI design processes.",
        "course_type": "case_study",
    },
    {
        "slug": "cos",
        "title": "AI for Chief of Staff: Cross-Org Synthesis to Exec Prep",
        "description": "Master the daily AI workflow of a modern Chief of Staff. Cover AI-assisted cross-functional synthesis (Notion AI, Linear, Gong call review), OKR rollups and exec dashboard prep, board-meeting pre-reads, exec 1:1 agendas, Slack signal triage, and CEO briefing generation. Capstone is ONE coherent board-prep scenario — one CEO, one company, one board meeting, one pre-read — with the learner producing actual exec briefing text, not a generic crisis playbook. Name specific tools the learner uses (Notion AI, Linear, Lattice, Gong, Gmail/GCal) and give copy-pasteable prompts.",
        "course_type": "case_study",
    },
    {
        "slug": "accountant",
        "title": "AI for Accountants: From Ledger to Audit Prep",
        "description": "Master the daily AI workflow of a Senior Accountant (close, recon, audit prep). Cover NetSuite/Xero/Sage GL queries with AI, BlackLine/FloQast-assisted close acceleration, variance analysis with AI, PBC list automation for audit prep, control testing (SOX 404), and GAAP/IFRS judgment calls (with explicit guardrails: when AI CANNOT opine without CPA review). Capstone threads ONE month-end close for ONE fictional company — learner produces real journal-entry reconciliations, variance commentary, and PBC deliverables. No 'strategic AI implementation' docs.",
        "course_type": "case_study",
    },
]


def post(path, body, timeout=1200):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def run(job):
    t0 = time.time()
    try:
        start = post("/api/creator/start", {
            "title": job["title"],
            "description": job["description"],
            "course_type": job["course_type"],
            "level": "Intermediate",
        }, timeout=400)
        sid = start["session_id"]
        answers = [{"question_id": q["id"], "answer": "One scenario threaded through every module. Name real tools. Capstone is a concrete deliverable, not a meta-doc."}
                   for q in start.get("questions", [])[:4]]
        print(f"  [{job['slug']:10}] refining...", flush=True)
        refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
        print(f"  [{job['slug']:10}] generating ({len(refine['outline']['modules'])} modules)...", flush=True)
        g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=1200)
        cid = g["course_id"]
        cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
        print(f"  [{job['slug']:10}] {cid} in {int(time.time()-t0)}s — {len(cd['modules'])} modules", flush=True)
        print(f"              subtitle: {cd.get('subtitle')!r}", flush=True)
        return {"slug": job["slug"], "ok": True, "course_id": cid}
    except Exception as e:
        print(f"  [{job['slug']:10}] FAIL ({int(time.time()-t0)}s): {e}", flush=True)
        return {"slug": job["slug"], "ok": False, "error": str(e)}


if __name__ == "__main__":
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    results = []
    for j in JOBS:  # serial to avoid API saturation
        results.append(run(j))

    print(f"\n--- SUMMARY ---")
    for r in results:
        print(f"  {r['slug']:10} {'SUCCESS ' + r.get('course_id', '?') if r['ok'] else 'FAIL: ' + r.get('error','')}")
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget after: ${b['spent_usd']:.2f}")
