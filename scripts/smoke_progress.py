"""Smoke test: kick off /api/creator/generate in a thread and poll /progress
concurrently to verify progress updates stream correctly."""
import json, urllib.request, threading, time

BASE = "http://localhost:8001"


def post(path, body, timeout=600):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get(path, timeout=20):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=timeout).read())


def main():
    print("Starting creator session...")
    start = post("/api/creator/start", {
        "title": "Progress Smoke Test Course for AI Developers",
        "description": "A minimal test course to verify the progress endpoint streams updates during generation. Keep modules short.",
        "course_type": "technical",
        "level": "Intermediate",
    }, timeout=400)
    sid = start["session_id"]
    print(f"  session_id: {sid}")

    answers = [{"question_id": q["id"], "answer": "Keep it short and concrete."}
               for q in start.get("questions", [])[:4]]
    print("Refining outline...")
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=600)
    print(f"  {len(refine['outline']['modules'])} modules in outline")

    # Poll progress BEFORE generate starts to test the 'waiting' state
    p0 = get(f"/api/creator/progress/{sid}")
    print(f"Pre-generate progress: {p0}")

    print("\nKicking off /generate + polling /progress concurrently...\n")
    gen_result = {}
    def _gen():
        gen_result["data"] = post("/api/creator/generate",
                                   {"session_id": sid, "outline": refine["outline"]},
                                   timeout=900)

    t = threading.Thread(target=_gen); t.start()

    # Poll every 1.5s and print deltas
    last_done = -1
    last_phase = None
    samples = 0
    while t.is_alive() and samples < 120:  # max ~3min
        try:
            p = get(f"/api/creator/progress/{sid}")
        except Exception as e:
            print(f"  poll error: {e}")
            time.sleep(1.5); samples += 1; continue
        done = p.get("completed_steps", 0)
        phase = p.get("phase")
        if done != last_done or phase != last_phase:
            total = p.get("total_steps", 0)
            pct = p.get("percent", 0)
            latest = p.get("last_step_title") or ""
            print(f"  [{phase:10}] {done:3}/{total:3} ({pct:3}%) latest={latest[:45]}")
            last_done = done
            last_phase = phase
        if phase in ("done", "error"):
            break
        time.sleep(1.5); samples += 1

    t.join(timeout=60)
    data = gen_result.get("data", {})
    print(f"\n/generate returned course_id={data.get('course_id')}")

    # Final progress state
    final = get(f"/api/creator/progress/{sid}")
    print(f"Final progress: phase={final.get('phase')} done={final.get('completed_steps')}/{final.get('total_steps')} ({final.get('percent')}%)")


if __name__ == "__main__":
    main()
