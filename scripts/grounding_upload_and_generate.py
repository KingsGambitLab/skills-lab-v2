"""Upload each source doc to the LMS and generate a course from it via Creator API.

Prints the resulting course_id per source so the fidelity agents can then audit.
"""
import json, os, time, urllib.request, urllib.error
import mimetypes

BASE = "http://localhost:8001"
SRC_DIR = "/tmp/grounding_test"

JOBS = [
    {"file": "meridian_claim_triage_sop.docx",     "title": "MeridianInsure Claim Triage",
     "description": "Train Tier-1 claim adjusters at MeridianInsure on the v4.2 claim triage SOP. Follow the source handbook faithfully — the MERIDIAN checklist (Match/Evidence/Reach-out/Investigate/Determine/Issue/Aftercare), specific thresholds, escalation rules, named owners.",
     "course_type": "compliance"},
    {"file": "kelvingrove_onboarding.docx",         "title": "Kelvingrove Analytics — Jr Data Engineer Onboarding",
     "description": "Onboard Junior Data Engineers at Kelvingrove Analytics using the canonical handbook. Stay faithful to the specified stack, week-by-week milestones, named mentors, and 30/60/90 expectations.",
     "course_type": "technical"},
    {"file": "zephyr_dsar_compliance.docx",         "title": "Zephyr Health GDPR DSAR Handling",
     "description": "Train Zephyr Health's privacy team on the DSAR handling bulletin 2026-03. Preserve specific systems to query, response packaging standards, escalation rules, and named owners.",
     "course_type": "compliance"},
    {"file": "orbital_enterprise_upsell.pptx",      "title": "Orbital-Nova Enterprise Upsell",
     "description": "Train Orbital-Nova sales team on the Q2 2026 enterprise-upsell playbook v2.1. Stay faithful to the ICP scorecard, 7-step motion, objection responses, and named stakeholders.",
     "course_type": "case_study"},
    {"file": "lumen_trial_047_protocol.pptx",       "title": "Lumen-Bio Trial-047 Protocol Training",
     "description": "Train Lumen-Bio investigators on the Phase 2 protocol for LB-4721 in moderate plaque psoriasis. Preserve exact inclusion/exclusion criteria, dosing schedule, AE reporting process, named PI/monitors.",
     "course_type": "compliance"},
    {"file": "halcyon_crisis_comms_playbook.pptx",  "title": "Halcyon Cybersecurity Breach Crisis Comms",
     "description": "Train Halcyon's comms and exec leadership on the breach crisis comms playbook v2.3. Preserve hour-by-hour activation (0-4, 4-24, 24-72), named owners, tone guidelines, regulatory notifications.",
     "course_type": "case_study"},
]


def upload_file(path):
    """Multipart upload via the LMS's /api/creator/upload endpoint."""
    import uuid as _uuid
    boundary = "----LMSBoundary" + _uuid.uuid4().hex
    filename = os.path.basename(path)
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/api/creator/upload", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:400]}
    except Exception as e: return -1, {"error": str(e)[:300]}


def get(path):
    return json.loads(urllib.request.urlopen(BASE+path, timeout=30).read())


def generate_one(job):
    path = os.path.join(SRC_DIR, job["file"])
    t0 = time.time()
    print(f"  uploading {job['file']}...", flush=True)
    up = upload_file(path)
    combined = up.get("combined_source_material") or up.get("files", [{}])[0].get("text") or ""
    print(f"    extracted {len(combined)} chars", flush=True)

    body = {
        "title": job["title"],
        "description": job["description"],
        "course_type": job["course_type"],
        "source_material": combined,
        # explicit: faithful-to-source mode, intermediate level
        "level": "Intermediate",
    }
    status, start = post("/api/creator/start", body)
    if status != 200:
        print(f"    start failed: {start}"); return None
    sid = start["session_id"]
    answers = [
        {"question_id": q["id"],
         "answer": "Follow the source material faithfully. Do not invent details. Every fact, name, threshold, or policy in the generated content must trace to the uploaded document."}
        for q in start.get("questions", [])[:4]
    ]
    status, refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"    refine failed: {refine}"); return None
    status, g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"    generate failed: {g}"); return None
    cid = g["course_id"]
    print(f"    generated {cid} in {time.time()-t0:.0f}s", flush=True)
    return {"source": job["file"], "course_id": cid, "title": job["title"]}


def main():
    b = get("/api/admin/budget")
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    results = []
    for j in JOBS:
        r = generate_one(j)
        if r: results.append(r)
    b = get("/api/admin/budget")
    print(f"Budget after:  ${b['spent_usd']:.2f}", flush=True)
    # Save mapping for the fidelity-checker agents
    with open("/tmp/grounding_test/generated_courses.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nMapping saved to /tmp/grounding_test/generated_courses.json")
    for r in results:
        print(f"  {r['source']} -> {r['course_id']}")


if __name__ == "__main__":
    main()
