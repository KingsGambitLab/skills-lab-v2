"""Technical-function AI upskilling wave — Sales Engineer, Data Analyst, Tech Writer, DevOps, Security.
5 courses × ~$0.50 = ~$2.50 burn. Complements earlier business-function waves.
"""
import asyncio, json, time, urllib.request, urllib.error

BASE = "http://localhost:8001"

COURSES = [
    {
        "title": "AI for Sales Engineers: From Discovery to Technical Close",
        "description": (
            "For Sales Engineers and Solutions Consultants. Use LLMs to synthesize discovery calls "
            "into technical requirements, auto-generate RFP responses from playbook, and simulate "
            "live technical deep-dives with CTOs who ask hostile questions. Hands-on: feed 3 "
            "discovery call transcripts + customer architecture diagrams to Claude, generate "
            "tailored POC plan. Capstone: adaptive_roleplay — you're in a final technical eval "
            "with a skeptical CTO who's already tried 2 competitors."
        ),
        "course_type": "case_study",
        "answers": [
            "Sales Engineers, Solutions Consultants, Technical Account Managers",
            "Claude API for call synthesis; Python for RFP auto-response; POC plan generation",
            "Capstone: adaptive_roleplay with skeptical CTO in final technical eval",
        ],
    },
    {
        "title": "AI for Data Analysts: Ad-Hoc Analysis to Executive Insight",
        "description": (
            "For Data Analysts and BI Engineers. Use LLMs to translate business questions into "
            "SQL, spot data-quality issues in raw tables, and synthesize dashboards into "
            "executive narratives. Hands-on: messy e-commerce dataset with planted biases "
            "(Simpson's paradox, selection bias). Capstone: simulator_loop — an exec Slack "
            "channel is asking rapid-fire questions about last-quarter churn. You have 30 min "
            "and a dirty dataset. Grade on correctness, speed, and executive communication."
        ),
        "course_type": "technical",
        "answers": [
            "Data Analysts, BI Engineers, Analytics Managers",
            "Python + pandas + DuckDB + Claude API for SQL generation and insight synthesis",
            "Capstone: simulator_loop in exec-pressure analysis situation with planted biases",
        ],
    },
    {
        "title": "AI for Technical Writers: Docs that Actually Get Read",
        "description": (
            "For Technical Writers and Developer Advocates. Use LLMs to audit existing docs "
            "for clarity gaps, generate code samples that compile, and personalize docs for "
            "different personas (beginner dev vs senior architect). Hands-on: feed an OpenAPI "
            "spec + existing docs, identify where users get stuck. Capstone: adaptive_roleplay "
            "— a principal engineer reviewer says your doc is 'too hand-holdy' and wants it cut "
            "in half. Defend or adapt. They have 3 specific complaints."
        ),
        "course_type": "case_study",
        "answers": [
            "Technical Writers, Developer Advocates, Documentation Leads",
            "Claude API for doc review, audience-adaptation; pytest-driven code sample validation",
            "Capstone: adaptive_roleplay defending doc scope vs principal engineer reviewer",
        ],
    },
    {
        "title": "AI for DevOps & Platform Engineers: Self-Service Infrastructure",
        "description": (
            "For DevOps, SRE, Platform engineers. Use LLMs to generate Terraform modules from "
            "plain English, debug flaky CI pipelines, and auto-triage PagerDuty alerts. "
            "Hands-on: a 40-line Terraform module with subtle IAM mis-scopes — fix with LLM "
            "help while tracking cost. Capstone: incident_console — production K8s cluster "
            "at 2 AM, 3 services degraded, your on-call rotation just lost the senior engineer. "
            "12 commands, cascade rules, Slack escalation from CTO."
        ),
        "course_type": "technical",
        "answers": [
            "DevOps Engineers, SREs, Platform Engineers",
            "Terraform + kubectl + Claude API for IaC generation and incident triage",
            "Capstone: incident_console — 2 AM K8s cluster degradation with CTO Slack pressure",
        ],
    },
    {
        "title": "AI for Security Engineers: Threat Detection to Incident Response",
        "description": (
            "For Security Engineers and SOC analysts. Use LLMs to triage SIEM alerts, draft "
            "phishing-awareness emails, and red-team your own incident response playbook. "
            "Hands-on: 500-alert SIEM export — separate real threats from noise. Capstone: "
            "incident_console — a credential-stuffing attack at 4 AM on your auth service. "
            "You must contain, investigate, communicate with legal + CISO, and write the "
            "postmortem. 15 commands, CASB/WAF interactions, CEO Slack asking if customer "
            "data leaked."
        ),
        "course_type": "technical",
        "answers": [
            "Security Engineers, SOC Analysts, Incident Responders",
            "Claude API for SIEM triage; Python for log parsing; simulated SOAR playbooks",
            "Capstone: incident_console — credential-stuffing attack at 4 AM with CEO escalation",
        ],
    },
]


def _post(path, body, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode()[:400]}
    except Exception as e: return -1, {"error": str(e)[:300]}


async def gen(spec, idx):
    t0 = time.time()
    print(f"  [{idx+1}] {spec['title'][:60]}", flush=True)
    status, start = await asyncio.to_thread(_post, "/api/creator/start", {"title": spec["title"], "description": spec["description"], "course_type": spec["course_type"]})
    if status != 200:
        print(f"  [{idx+1}] start failed: {start}", flush=True); return
    sid = start["session_id"]
    answers = []
    for i, q in enumerate(start.get("questions", [])[:4]):
        ans = spec["answers"][i] if i < len(spec["answers"]) else "Use adaptive_roleplay / incident_console for immersion."
        answers.append({"question_id": q["id"], "answer": ans})
    status, refine = await asyncio.to_thread(_post, "/api/creator/refine", {"session_id": sid, "answers": answers})
    if status != 200:
        print(f"  [{idx+1}] refine failed: {refine}", flush=True); return
    types = set()
    for m in refine["outline"]["modules"]:
        for s in m["steps"]: types.add(s.get("exercise_type", s.get("type")))
    status, g = await asyncio.to_thread(_post, "/api/creator/generate", {"session_id": sid, "outline": refine["outline"]})
    if status != 200:
        print(f"  [{idx+1}] generate failed: {g}", flush=True); return
    new_types = sorted(types & {"adaptive_roleplay","incident_console","simulator_loop"})
    print(f"  [{idx+1}] OK {g.get('course_id')} ({time.time()-t0:.0f}s) — new: {new_types}", flush=True)


async def main():
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget before: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass
    sem = asyncio.Semaphore(3)
    async def bounded(s, i):
        async with sem: return await gen(s, i)
    await asyncio.gather(*[bounded(s, i) for i, s in enumerate(COURSES)])
    try:
        b = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
        print(f"Budget after: ${b['spent_usd']:.2f}", flush=True)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
