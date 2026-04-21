"""Create onboarding courses by uploading training documents through the Creator.

Uses /tmp/tcs_onboarding.txt and /tmp/infosys_foundation.txt as seed material.
Exercises the full pipeline: upload → start → refine → generate.
"""
import asyncio
import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "TCS ILP Fresher Onboarding",
        "description": "Complete TCS Initial Learning Program — ASPIRE pre-joining through 60-day ILP capstone. For Indian IT freshers joining their first corporate role.",
        "course_type": "case_study",
        "file": "/tmp/tcs_onboarding.txt",
        "answers": [
            {"question_id": "q_0", "answer": "Indian IT freshers (B.Tech/MCA) joining TCS out of college"},
            {"question_id": "q_1", "answer": "India"},
            {"question_id": "q_2", "answer": "60 days (matching actual ILP duration)"},
            {"question_id": "q_3", "answer": "Yes — cover both technical foundations (Java, SQL, React) AND professional skills (communication, compliance, client-facing behavior)"},
        ],
    },
    {
        "title": "Infosys Mysore Foundation Program",
        "description": "23-week residential training program for fresh engineering graduates at Infosys GEC Mysore. Covers generic technology foundations + stream specialization (Java/.NET/Testing/New Tech) + capstone.",
        "course_type": "case_study",
        "file": "/tmp/infosys_foundation.txt",
        "answers": [
            {"question_id": "q_0", "answer": "Fresh B.Tech graduates joining Infosys, any stream"},
            {"question_id": "q_1", "answer": "Java Full Stack stream (most common allocation)"},
            {"question_id": "q_2", "answer": "23 weeks total; focus on weeks 1-18 for LMS coverage"},
            {"question_id": "q_3", "answer": "Yes — include Design Thinking, soft skills, and the capstone project structure"},
        ],
    },
]


def _post(path: str, body: dict, timeout: int = 300):
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


def _post_multipart(path: str, filepath: str):
    """Minimal multipart upload using stdlib."""
    import mimetypes, uuid
    boundary = f"----SkillsLabBoundary{uuid.uuid4().hex}"
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return -1, {"error": str(e)[:500]}


async def create_one(course):
    t0 = time.time()
    print(f"\n[{course['title']}]")

    # 1. Upload
    print("  Uploading doc...")
    status, upload = await asyncio.to_thread(_post_multipart, "/api/creator/upload", course["file"])
    if status != 200:
        print(f"  ✗ upload failed: {upload}")
        return None
    source = upload["combined_source_material"]
    print(f"  ✓ extracted {upload['total_chars']} chars")

    # 2. Start
    print("  Starting session...")
    status, start = await asyncio.to_thread(_post, "/api/creator/start", {
        "title": course["title"],
        "description": course["description"],
        "course_type": course["course_type"],
        "source_material": source,
    })
    if status != 200:
        print(f"  ✗ start failed: {start}")
        return None
    session_id = start["session_id"]
    questions = start.get("questions", [])
    print(f"  ✓ session {session_id[:8]} with {len(questions)} questions, {len(start.get('initial_outline',{}).get('modules',[]))} initial modules")

    # 3. Refine (answer the course's pre-written answers + any generic ones)
    answers = []
    for i, q in enumerate(questions):
        if i < len(course["answers"]):
            ans = course["answers"][i]["answer"]
        elif q.get("type") == "choice" and q.get("options"):
            ans = q["options"][0]
        else:
            ans = "Yes, cover this topic comprehensively with real examples."
        answers.append({"question_id": q["id"], "answer": ans})

    print("  Refining outline...")
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {
        "session_id": session_id, "answers": answers,
    })
    if status != 200:
        print(f"  ✗ refine failed: {refine}")
        return None
    modules = refine["outline"]["modules"]
    total_steps = sum(len(m["steps"]) for m in modules)
    print(f"  ✓ refined to {len(modules)} modules / {total_steps} steps")
    for m in modules:
        types = [s.get("exercise_type", s.get("type")) for s in m["steps"]]
        print(f"    - {m['title']}: {types}")

    # 4. Generate
    print("  Generating content (LLM-heavy, 1-2 min)...")
    status, gen = await asyncio.to_thread(_post, "/api/creator/generate", {
        "session_id": session_id, "outline": refine["outline"],
    })
    if status != 200:
        print(f"  ✗ generate failed: {gen}")
        return None
    cid = gen.get("course_id")
    print(f"  ✓ generated {cid} in {time.time() - t0:.0f}s total")
    return {
        "title": course["title"],
        "course_id": cid,
        "modules": len(modules),
        "steps": total_steps,
        "elapsed": time.time() - t0,
    }


async def main():
    # Check budget first
    status, budget = await asyncio.to_thread(_post, "/api/admin/budget", {})  # GET via POST workaround
    import urllib.request
    try:
        budget = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${budget['spent_usd']:.2f} / ${budget['cap_usd']} (remaining ${budget['remaining_usd']:.2f})")
    except Exception:
        pass

    results = []
    for course in COURSES:
        r = await create_one(course)
        if r:
            results.append(r)

    # Final budget
    try:
        budget = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"\nBudget after: ${budget['spent_usd']:.2f} / ${budget['cap_usd']} (remaining ${budget['remaining_usd']:.2f})")
    except Exception:
        pass

    print("\n=== Results ===")
    for r in results:
        print(f"  ✓ {r['title']}: {r['course_id']} ({r['modules']}M/{r['steps']}S in {r['elapsed']:.0f}s)")

    with open("/tmp/training_course_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
