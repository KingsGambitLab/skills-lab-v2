"""Regenerate the other 4 DEAL_BREAKER courses with the grounded pipeline.
Compare anchor-fact hit rate vs original (which were all 0-50% hits before fix).
"""
import json, os, time, urllib.request, uuid, re
from pathlib import Path

BASE = "http://localhost:8001"
SRC_DIR = "/tmp/grounding_test"

JOBS = [
    {
        "file": "kelvingrove_onboarding.docx",
        "title": "Kelvingrove Jr DE Onboarding v2 (grounded)",
        "description": "Onboard Junior Data Engineers at Kelvingrove Analytics using the canonical handbook. Stay faithful to the specified stack, week-by-week milestones, named mentors, and 30/60/90 expectations.",
        "course_type": "technical",
        "anchors": [
            "Evelyn Harsha", "Arjun Kapoor", "Amelia Song", "Ramesh K", "Priyanka",
            "revenue_recognition_daily", "04:00 UTC", "06:30 UTC",
            "stg_hubspot__contacts", "4.2%", "fct_revenue", "amount_cents",
            "WH_XSMALL_ANALYST", "WH_DEV_XSMALL",
            "Snowflake", "dbt Cloud", "Airflow", "Astronomer", "Looker", "Segment",
            "kelv-lint", "kelvingrove_dev", "47% false-positive", "18%",
            "logins_per_week_last_4", "support_tickets_open", "MRR_class",
            "Day 30", "Day 60", "Day 90",
        ],
    },
    {
        "file": "zephyr_dsar_compliance.docx",
        "title": "Zephyr GDPR DSAR v2 (grounded)",
        "description": "Train Zephyr Health's privacy team on the DSAR handling bulletin 2026-03. Preserve specific systems to query, response packaging standards, escalation rules, and named owners.",
        "course_type": "compliance",
        "anchors": [
            "Rivka Mendelsohn", "David Park", "dsar@zephyr.health",
            "Article 15", "30 calendar days", "90 days",
            "Persona", "Jira", "DSAR", "Tresorit",
            "Iron Mountain", "IM-PX-0482",
            "Epic", "NetSuite", "Zendesk", "HubSpot", "Amplitude",
            "Freeman incident", "$340,000",
            "zephyr.health/privacy/subprocessors",
            "Schrems II", "SCC Module 2",
            "Article 20", "600-word",
        ],
    },
    {
        "file": "orbital_enterprise_upsell.pptx",
        "title": "Orbital-Nova Upsell v2 (grounded)",
        "description": "Train Orbital-Nova sales team on the Q2 2026 enterprise-upsell playbook v2.1. Stay faithful to ICP, 7-step motion, objections, metrics.",
        "course_type": "case_study",
        "anchors": [
            "Kenji Yamamoto", "Priya Naresh", "Delia Jordan-Smith", "Daniela Falke", "Amaya",
            "Orbital Platform", "observability", "incident management",
            "$36K", "$120K", "$240K",
            "Series B", "200-2000", "$50M", "$500M",
            "Okta", "Azure AD", "Vanta", "vanta.trust.orbital-nova.com",
            "$420K", "CloudSpire-2025",
            "BDR-EXPAND-v4", "go/orbital-discovery-qs",
            "99.99% SLA", "OTEL", "Datadog",
            "3.2x", "42%", "$138K", "65 days", "12%",
        ],
    },
    {
        "file": "lumen_trial_047_protocol.pptx",
        "title": "Lumen Trial-047 Protocol v2 (grounded)",
        "description": "Train Lumen-Bio investigators on the Phase 2 protocol for LB-4721 in moderate plaque psoriasis. Preserve exact criteria, dosing, AE reporting, names.",
        "course_type": "compliance",
        "anchors": [
            "LB-4721", "JAK2", "psoriasis", "PASI", "PASI-75", "Week 16",
            "Meena Bhattacharya", "Graziano Pellini", "Vinod Kumaran", "Kimberly Oduya",
            "15mg", "twice daily", "80 patients", "2:1",
            "+1-415-555-0194",
            "ICF-047-v3", "2026-02-18",
            "CTCAE v5.0", "MedDRA", "MedWatch",
            "Medidata Rave", "eGFR", "ALT",
            "$4,200", "$8,500",
            "2026-04-02", "2026-04-03",
        ],
    },
]


def upload_file(path):
    boundary = "----LMSBoundary" + uuid.uuid4().hex
    filename = os.path.basename(path)
    import mimetypes
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE+"/api/creator/upload", data=body,
                                  headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_course_text(cid):
    cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
    blob = ""
    for m in cd["modules"]:
        md = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}/modules/{m['id']}", timeout=30).read())
        for s in md["steps"]:
            blob += " " + (s.get("content") or "")
            if s.get("demo_data"): blob += " " + json.dumps(s["demo_data"])
            if s.get("validation"): blob += " " + json.dumps(s["validation"])
    return blob


def run_one(job):
    t0 = time.time()
    path = os.path.join(SRC_DIR, job["file"])
    up = upload_file(path)
    combined = up.get("combined_source_material", "")
    print(f"\n=== {job['file']} (src {len(combined)} chars) ===", flush=True)
    start = post("/api/creator/start", {
        "title": job["title"],
        "description": job["description"],
        "course_type": job["course_type"],
        "source_material": combined,
        "level": "Intermediate",
    })
    sid = start["session_id"]
    answers = [{"question_id": q["id"], "answer": "Follow source faithfully. Never invent names/numbers/frameworks."}
               for q in start.get("questions", [])[:4]]
    refine = post("/api/creator/refine", {"session_id": sid, "answers": answers})
    g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    cid = g["course_id"]
    print(f"  Generated {cid} in {time.time()-t0:.0f}s", flush=True)

    # Audit anchor preservation
    blob = fetch_course_text(cid)
    hits = 0
    misses = []
    for anchor in job["anchors"]:
        if anchor in blob:
            hits += 1
        else:
            misses.append(anchor)
    rate = hits * 100 // len(job["anchors"])
    print(f"  Anchor hit rate: {hits}/{len(job['anchors'])} = {rate}%")
    if misses:
        print(f"  Missing: {misses[:10]}")
    return {"course_id": cid, "hit_rate": rate, "hits": hits, "total": len(job["anchors"]), "misses": misses}


if __name__ == "__main__":
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    results = []
    for j in JOBS:
        r = run_one(j)
        r["file"] = j["file"]
        results.append(r)
    b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\n--- SUMMARY ---")
    for r in results:
        print(f"  {r['file']:50} {r['hits']}/{r['total']} = {r['hit_rate']}%  {'FAITHFUL' if r['hit_rate'] >= 80 else 'MIXED' if r['hit_rate'] >= 50 else 'DEAL_BREAKER'}")
    print(f"Budget after: ${b['spent_usd']:.2f}")
