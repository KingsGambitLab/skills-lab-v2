"""Regenerate the 3 reviewer-flagged courses with improved Creator.

Per CLAUDE.md: we don't patch in place — we regenerate with same inputs to
prove the Creator fix works on fresh generations.

Flagged by reviewers:
- TCS ILP (reviewer 1 = 6.5/10; reviewer 3 = intro 4/10, capstone template placeholder)
- Emergent Full-Stack (reviewer 3 = capstone template placeholder, otherwise strong)
- Statistical Analysis (reviewer 2 = 3/10, empty `# Your answer here` code bodies)
"""
import asyncio
import json
import urllib.request
import mimetypes
import uuid
import time
from pathlib import Path

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "TCS ILP Fresher Onboarding",
        "description": "Complete TCS Initial Learning Program — ASPIRE pre-joining through 60-day ILP capstone. For Indian IT freshers joining their first corporate role.",
        "course_type": "case_study",
        "file": "/tmp/tcs_onboarding.txt",
        "old_course_id": "created-be0707f6989d",
        "answers": [
            {"question_id": "q_0", "answer": "Indian IT freshers (B.Tech/MCA) joining TCS out of college — they face real pressures like bench anxiety, bond letters, stream allocation, and Milestone Test failures"},
            {"question_id": "q_1", "answer": "India — TCS Chennai/Kolkata/Trivandrum DCs, ASPIRE pre-joining, ILP residential"},
            {"question_id": "q_2", "answer": "60 days total; respect that 2-week pre-ILP (ASPIRE) comes first; do NOT claim 'complete ILP' — frame as key highlights and decision points"},
            {"question_id": "q_3", "answer": "Cover fresher-reality: iEvolve, Ultimatix, RMG allocation, bond/service agreement, stream mapping, TCS standup culture, client-facing etiquette — not hypothetical Fortune-500 crises."},
        ],
    },
    {
        "title": "Emergent Full-Stack Support Engineering",
        "description": "4-week × 4-hour-per-day intensive full-stack engineering training for support engineers. Case-based with LLM-judged assessments. Covers Frontend, Backend, DBMS, Networking, Cloud (AWS+GCP), DevOps — all through real Emergent ticket scenarios.",
        "course_type": "technical",
        "file": "/tmp/emergent_training.pdf",
        "old_course_id": "created-6c2bc497245c",
        "answers": [
            {"question_id": "q_0", "answer": "Support engineers at Emergent being upskilled to engineering-transition pathway — calibrate for 85%+ scorers."},
            {"question_id": "q_1", "answer": "All 6 domains in the PDF: Frontend, Backend, DBMS, Networking, Cloud (AWS+GCP), DevOps"},
            {"question_id": "q_2", "answer": "4 weeks, 80 hours, case-based. Capstone must be a LIVE INCIDENT SIMULATION with real logs/stack traces/ticket threads — NOT a portfolio doc or reflection."},
            {"question_id": "q_3", "answer": "Preserve Emergent-specific context: Atlas ticketing, Job ID tracing, assign-before-read protocol, 5-step pipeline (Config→Build→Migration→Secrets→Runtime)."},
        ],
    },
    {
        "title": "Statistical Analysis for Product Decisions",
        "description": "Run A/B tests, compute confidence intervals, avoid common stats mistakes. Python-based exercises using scipy.stats and statsmodels (both mocked in sandbox). NOT spreadsheet-based.",
        "course_type": "technical",
        "old_course_id": "created-a7338158f22a",
        "answers": [
            {"question_id": "q_0", "answer": "Product engineers and data analysts running experiments in production"},
            {"question_id": "q_1", "answer": "Python scipy.stats / statsmodels — avoid Google Sheets references (learners won't have access). Use real numpy/pandas patterns."},
            {"question_id": "q_2", "answer": "Every code_exercise must have REAL starter code (15-40 lines) with specific TODOs — NOT '# Your answer here' stubs. Include imports, data setup, scaffolded function signatures."},
            {"question_id": "q_3", "answer": "Capstone must be a WORKING A/B test analysis module (power calc, CUPED variance reduction, Bayesian posterior) — not a deck or framework doc."},
        ],
    },
]


def _post_json(path, body, timeout=300):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:500]}
    except Exception as e:
        return -1, {"error": str(e)[:500]}


def _post_multipart(path, filepath):
    boundary = f"----Boundary{uuid.uuid4().hex}"
    content = Path(filepath).read_bytes()
    filename = Path(filepath).name
    mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
        f"Content-Type: {mimetype}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return -1, {"error": str(e)[:500]}


async def regen_one(course):
    t0 = time.time()
    print(f"\n[REGEN] {course['title']}", flush=True)

    source = ""
    if course.get("file"):
        status, upload = await asyncio.to_thread(_post_multipart, "/api/creator/upload", course["file"])
        if status == 200:
            source = upload["combined_source_material"]
            print(f"  OK uploaded {upload['total_chars']} chars", flush=True)
        else:
            print(f"  (skip upload: {upload})", flush=True)

    body = {
        "title": course["title"],
        "description": course["description"],
        "course_type": course["course_type"],
    }
    if source:
        body["source_material"] = source

    status, start = await asyncio.to_thread(_post_json, "/api/creator/start", body)
    if status != 200:
        print(f"  FAIL start: {start}", flush=True)
        return None
    session_id = start["session_id"]
    questions = start.get("questions", [])

    answers = []
    for i, q in enumerate(questions):
        if i < len(course["answers"]):
            ans = course["answers"][i]["answer"]
        elif q.get("type") == "choice" and q.get("options"):
            ans = q["options"][0]
        else:
            ans = "Yes, cover this thoroughly with domain-specific realism."
        answers.append({"question_id": q["id"], "answer": ans})

    status, refine = await asyncio.to_thread(_post_json, "/api/creator/refine", {
        "session_id": session_id, "answers": answers,
    })
    if status != 200:
        print(f"  FAIL refine: {refine}", flush=True)
        return None
    modules = refine["outline"]["modules"]
    total_steps = sum(len(m["steps"]) for m in modules)
    print(f"  OK refined: {len(modules)} modules, {total_steps} steps", flush=True)

    status, gen = await asyncio.to_thread(_post_json, "/api/creator/generate", {
        "session_id": session_id, "outline": refine["outline"],
    })
    if status != 200:
        print(f"  FAIL generate: {gen}", flush=True)
        return None
    new_cid = gen.get("course_id")
    elapsed = time.time() - t0
    print(f"  OK new course {new_cid} (was {course['old_course_id']}) in {elapsed:.0f}s", flush=True)
    return {
        "title": course["title"],
        "old_course_id": course["old_course_id"],
        "new_course_id": new_cid,
        "modules": len(modules),
        "steps": total_steps,
        "elapsed": elapsed,
    }


async def main():
    try:
        budget = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${budget['spent_usd']:.2f}/${budget['cap_usd']} (${budget['remaining_usd']:.2f} remaining)", flush=True)
    except Exception:
        pass

    results = await asyncio.gather(*[regen_one(c) for c in COURSES])
    results = [r for r in results if r]

    try:
        budget = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${budget['spent_usd']:.2f}/${budget['cap_usd']} (${budget['remaining_usd']:.2f} remaining)", flush=True)
    except Exception:
        pass

    print("\n=== REGENERATION RESULTS ===", flush=True)
    for r in results:
        print(f"  OK {r['title']}: {r['old_course_id']} → {r['new_course_id']} ({r['modules']}M/{r['steps']}S, {r['elapsed']:.0f}s)", flush=True)

    with open("/tmp/regen_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
