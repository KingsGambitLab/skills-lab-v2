"""Create courses from user-provided PDF uploads (Virtusa FDE + Emergent).

Full pipeline: upload → start → refine → generate.
"""
import asyncio
import json
import urllib.request
import urllib.error
import mimetypes
import uuid
import time
from pathlib import Path

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "Virtusa Forward Deployed Engineer Program",
        "description": "14-week intensive hands-on curriculum for Virtusa FDEs operating at enterprise insurance clients. Zero lectures, 100% task-driven, real client deployment scenarios.",
        "course_type": "case_study",
        "file": "/Users/tushar/Downloads/virtusa_fde_curriculum.docx.pdf",
        "answers": [
            {"question_id": "q_0", "answer": "Mid-level software engineers transitioning into Virtusa Forward Deployed Engineer roles at insurance clients"},
            {"question_id": "q_1", "answer": "Insurance industry (P&C and Life) — large enterprise digital transformation clients"},
            {"question_id": "q_2", "answer": "14 weeks, full-time, task-driven (zero lectures)"},
            {"question_id": "q_3", "answer": "All technical areas from the curriculum: client systems, insurance domain, data pipelines, integration, deployment — AND the soft skills of client-facing consulting"},
        ],
    },
    {
        "title": "Emergent Full-Stack Support Engineering",
        "description": "4-week × 4-hour-per-day intensive full-stack engineering training for support engineers. Case-based with LLM-judged assessments. Covers Frontend, Backend, DBMS, Networking, Cloud (AWS+GCP), DevOps — all through real Emergent ticket scenarios.",
        "course_type": "technical",
        "file": "/tmp/emergent_training.pdf",
        "answers": [
            {"question_id": "q_0", "answer": "Support engineers at Emergent being upskilled to handle full-stack issues"},
            {"question_id": "q_1", "answer": "All 6 domains: Frontend, Backend, DBMS, Networking, Cloud (AWS+GCP), DevOps"},
            {"question_id": "q_2", "answer": "4 weeks, 80 total hours, case-based with LLM-judged assessments"},
            {"question_id": "q_3", "answer": "Calibrate for engineering-transition pathway (85%+ scorers). Include real Emergent ticket scenarios throughout."},
        ],
    },
]


def _post_json(path, body, timeout=300):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
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
        BASE + path,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return -1, {"error": str(e)[:500]}


async def create_one(course):
    t0 = time.time()
    print(f"\n[{course['title']}]", flush=True)

    print("  Uploading PDF...", flush=True)
    status, upload = await asyncio.to_thread(_post_multipart, "/api/creator/upload", course["file"])
    if status != 200:
        print(f"  FAIL upload: {upload}", flush=True)
        return None
    source = upload["combined_source_material"]
    print(f"  OK extracted {upload['total_chars']} chars", flush=True)

    print("  Starting session (LLM: initial outline + questions)...", flush=True)
    status, start = await asyncio.to_thread(_post_json, "/api/creator/start", {
        "title": course["title"],
        "description": course["description"],
        "course_type": course["course_type"],
        "source_material": source,
    })
    if status != 200:
        print(f"  FAIL start: {start}", flush=True)
        return None
    session_id = start["session_id"]
    questions = start.get("questions", [])
    initial_mods = start.get("initial_outline", {}).get("modules", [])
    print(f"  OK session {session_id[:8]}... {len(questions)} Qs, {len(initial_mods)} initial modules", flush=True)
    for m in initial_mods:
        print(f"    - {m.get('title')}", flush=True)

    # Answer questions
    answers = []
    for i, q in enumerate(questions):
        if i < len(course["answers"]):
            ans = course["answers"][i]["answer"]
        elif q.get("type") == "choice" and q.get("options"):
            ans = q["options"][0]
        else:
            ans = "Cover this topic thoroughly with real examples from the source material."
        answers.append({"question_id": q["id"], "answer": ans})

    print("  Refining (LLM: detailed outline)...", flush=True)
    status, refine = await asyncio.to_thread(_post_json, "/api/creator/refine", {
        "session_id": session_id, "answers": answers,
    })
    if status != 200:
        print(f"  FAIL refine: {refine}", flush=True)
        return None
    modules = refine["outline"]["modules"]
    total_steps = sum(len(m["steps"]) for m in modules)
    print(f"  OK refined: {len(modules)} modules, {total_steps} steps", flush=True)
    for m in modules:
        types = [s.get("exercise_type", s.get("type")) for s in m["steps"]]
        print(f"    - {m['title']} [{', '.join(types)}]", flush=True)

    print("  Generating (LLM: ~1-3 min, all steps in parallel)...", flush=True)
    status, gen = await asyncio.to_thread(_post_json, "/api/creator/generate", {
        "session_id": session_id, "outline": refine["outline"],
    })
    if status != 200:
        print(f"  FAIL generate: {gen}", flush=True)
        return None
    cid = gen.get("course_id")
    elapsed = time.time() - t0
    print(f"  OK generated {cid} in {elapsed:.0f}s total", flush=True)
    return {
        "title": course["title"],
        "course_id": cid,
        "modules": len(modules),
        "steps": total_steps,
        "elapsed": elapsed,
    }


async def main():
    # Budget before
    try:
        budget = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget: ${budget['spent_usd']:.2f}/${budget['cap_usd']} (${budget['remaining_usd']:.2f} remaining)", flush=True)
    except Exception:
        pass

    # Run both in parallel — Creator endpoints already parallelize step-content internally
    results = await asyncio.gather(*[create_one(c) for c in COURSES])
    results = [r for r in results if r]

    # Budget after
    try:
        budget = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${budget['spent_usd']:.2f}/${budget['cap_usd']} (${budget['remaining_usd']:.2f} remaining)", flush=True)
    except Exception:
        pass

    print("\n=== RESULTS ===", flush=True)
    for r in results:
        print(f"  OK {r['title']}: {r['course_id']} ({r['modules']}M/{r['steps']}S, {r['elapsed']:.0f}s)", flush=True)

    with open("/tmp/pdf_course_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
