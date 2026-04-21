"""Seed a course showcasing incident_console exercise type.

Creates 'SRE Incident Response: The 3AM Pager' — a live production outage
simulator with kubectl commands, streaming logs, escalating Slack pings,
revenue ticking, cascade rules for wrong commands.
"""
import asyncio
from sqlalchemy import select
from backend.database import Course, Module, Step, async_session_factory


COURSE_ID = "sre-3am-pager"

COURSE = {
    "id": COURSE_ID,
    "title": "SRE 3AM Pager: Live Incident Response",
    "subtitle": "Not a simulation — a drill",
    "description": "Your pager fires at 3:42 AM. Payments API is crashing. $2,000/min is bleeding. Three teams are already in the Slack thread. You have 10 minutes to find the root cause, stop the bleed, and communicate clearly — before the CEO is woken up. This is not MCQ; you type real kubectl commands and the cluster responds.",
    "course_type": "technical",
    "level": "Intermediate",
    "estimated_time": "30 min",
    "module_count": 2,
    "tags": ["sre", "incident-response", "kubernetes", "debugging", "live-simulation"],
    "icon": "🚨",
}

MODULE_1 = {
    "position": 1,
    "title": "Pre-Drill Briefing",
    "estimated_time": "5 min",
    "step_count": 2,
    "objectives": [
        "Understand the incident-command structure",
        "Know the canonical first 3 commands in any outage",
        "Recognize the cost of destructive-first commands",
    ],
    "steps": [
        {
            "position": 1,
            "title": "How Senior SREs Think in the First 60 Seconds",
            "step_type": "concept",
            "exercise_type": None,
            "content": """<h2>The Observer, Not the Fixer</h2>
<p>The junior instinct when paged: <em>fix it fast, make the pain stop</em>. The senior SRE instinct: <em>understand before acting</em>. In the first 60 seconds, a senior on a page does NOT touch the cluster — they read.</p>
<h3>The Canonical First 3 Commands</h3>
<ol>
  <li><code>kubectl get pods --all-namespaces | grep -v Running</code> — who is unhealthy?</li>
  <li><code>kubectl describe pod &lt;failing-pod&gt;</code> — what does the cluster say?</li>
  <li><code>kubectl logs &lt;failing-pod&gt; --previous</code> — what did it say before it died?</li>
</ol>
<p>Only after those three do you form a hypothesis. Only then do you touch anything.</p>
<h3>Cost of Destructive-First</h3>
<p>Common junior mistake: see a crashlooping pod, <code>kubectl delete pod</code>. Now the cluster respawns it; if the root cause was a config issue, the new pod crashes too. You've added latency and destroyed debugging context (logs are gone from the old pod).</p>
<p>The capstone drill will measure: cascade count (destructive actions that made things worse), time to correct diagnosis, communication with stakeholders under pressure.</p>
""",
        },
        {
            "position": 2,
            "title": "Match Symptoms to Canonical Commands",
            "step_type": "exercise",
            "exercise_type": "categorization",
            "content": """<p>Each symptom below should trigger a specific first diagnostic command. Sort them.</p>""",
            "demo_data": {
                "categories": [
                    "kubectl describe pod",
                    "kubectl logs --previous",
                    "kubectl top pods",
                    "kubectl get events",
                ],
                "items": [
                    {"id": "s1", "text": "Pod is in CrashLoopBackOff", "correct_category": "kubectl logs --previous"},
                    {"id": "s2", "text": "OOMKilled shown in status", "correct_category": "kubectl describe pod"},
                    {"id": "s3", "text": "New deploy just happened, everything is slow", "correct_category": "kubectl get events"},
                    {"id": "s4", "text": "Pod is Running but CPU pegged at 100%", "correct_category": "kubectl top pods"},
                    {"id": "s5", "text": "ImagePullBackOff on a new pod", "correct_category": "kubectl describe pod"},
                    {"id": "s6", "text": "App startup fails with no container logs visible", "correct_category": "kubectl describe pod"},
                ],
            },
            "validation": {"correct_mapping": {
                "s1": "kubectl logs --previous",
                "s2": "kubectl describe pod",
                "s3": "kubectl get events",
                "s4": "kubectl top pods",
                "s5": "kubectl describe pod",
                "s6": "kubectl describe pod",
            }},
        },
    ],
}

# ── The Drill: payment-api outage ────────────────────────────────────
MODULE_2 = {
    "position": 2,
    "title": "The Drill — 3:42 AM PST",
    "estimated_time": "25 min",
    "step_count": 1,
    "objectives": [
        "Diagnose and remediate a live-feeling K8s outage",
        "Communicate with stakeholders under time pressure",
        "Avoid destructive commands that cascade the incident",
    ],
    "steps": [
        {
            "position": 1,
            "title": "Payments API — Error rate 47%, revenue bleeding",
            "step_type": "exercise",
            "exercise_type": "incident_console",
            "content": "",
            "demo_data": {
                "alert": {
                    "title": "P1 — payment-api error rate spike",
                    "severity": "P1",
                    "description": "checkout_api error rate 47% (SLO: 1%); p99 latency 12s (SLO: 500ms). Started ~4 min ago.",
                    "initial_metrics": {"error_rate": 47},
                },
                "revenue_per_min": 2000,
                "time_budget_s": 600,
                "slack_channel": "#incidents",
                "root_cause": "connection pool exhaustion caused by recent deploy missing max_connections config",
                "accepted_remediations": [
                    r"kubectl rollout undo",
                    r"kubectl scale.*--replicas=\d+",
                    r"kubectl set env.*MAX_CONNECTIONS",
                ],
                "commands": [
                    {
                        "pattern": r"^kubectl get pods?(?:\s+.*)?$",
                        "output": (
                            "NAMESPACE     NAME                             READY   STATUS             RESTARTS        AGE\n"
                            "payments      payment-api-7c9fd5b6-abc12       0/1     CrashLoopBackOff   12 (30s ago)    4m\n"
                            "payments      payment-api-7c9fd5b6-def34       0/1     Error              8 (1m ago)      4m\n"
                            "payments      payment-api-7c9fd5b6-ghi56       1/1     Running            0               4m\n"
                            "payments      auth-service-5b4d8c9-qrs77       1/1     Running            0               2d\n"
                            "payments      postgres-primary-0               1/1     Running            0               12d\n"
                        ),
                        "time_cost_s": 15,
                        "unlocks": ["log-discover-pods"],
                    },
                    {
                        "pattern": r"^kubectl describe pod (payment-api\S+|\S+-abc12)",
                        "output": (
                            "Name:         payment-api-7c9fd5b6-abc12\n"
                            "Namespace:    payments\n"
                            "Status:       Running\n"
                            "Containers:\n"
                            "  payment-api:\n"
                            "    Image:   registry.internal/payment-api:v3.2.1\n"
                            "    State:   Waiting\n"
                            "      Reason: CrashLoopBackOff\n"
                            "    Last State: Terminated\n"
                            "      Reason:  Error\n"
                            "      Exit Code: 137\n"
                            "      Started:   Mon, 19 Apr 2026 03:38:41 UTC\n"
                            "      Finished:  Mon, 19 Apr 2026 03:41:52 UTC\n"
                            "    Environment:\n"
                            "      DATABASE_URL:  postgres://payments_rw@postgres:5432/payments\n"
                            "      # MAX_CONNECTIONS not set — defaults to pool of 100, but new deploy doubles thread count\n"
                            "Events:\n"
                            "  Warning  BackOff    10s (x12 over 4m)   Back-off restarting failed container\n"
                            "  Normal   Pulled     5m                   Successfully pulled image v3.2.1\n"
                        ),
                        "time_cost_s": 25,
                        "unlocks": ["log-maxconns", "log-image-diff"],
                    },
                    {
                        "pattern": r"^kubectl logs.*payment-api\S*.*--previous",
                        "output": (
                            "2026-04-19T03:41:50.912Z ERROR [DB] connection pool exhausted (100/100 in use, waiting 30s+)\n"
                            "2026-04-19T03:41:51.108Z ERROR [DB] context deadline exceeded acquiring connection\n"
                            "2026-04-19T03:41:51.204Z FATAL [main] cannot serve requests without DB connection, exiting\n"
                            "2026-04-19T03:41:52.011Z panic: runtime error: invalid memory address\n"
                            "goroutine 1 [running]:\n"
                            "main.main() /app/cmd/payment-api/main.go:42 +0x12c\n"
                        ),
                        "time_cost_s": 20,
                        "unlocks": ["log-rootcause", "log-deploy-event"],
                    },
                    {
                        "pattern": r"^kubectl logs.*payment-api\S*(?!.*--previous)",
                        "output": (
                            "2026-04-19T03:43:02.001Z INFO  [startup] payment-api v3.2.1 starting\n"
                            "2026-04-19T03:43:02.412Z INFO  [db] connecting to postgres://payments@postgres:5432\n"
                            "2026-04-19T03:43:02.891Z ERROR [db] connection pool init failed: max connections reached\n"
                            "(pod will crash shortly; run with --previous for the crash trace)\n"
                        ),
                        "time_cost_s": 10,
                        "unlocks": [],
                    },
                    {
                        "pattern": r"^kubectl get events(?:\s+.*)?$",
                        "output": (
                            "LAST SEEN   TYPE      REASON              OBJECT                                MESSAGE\n"
                            "4m          Normal    Scheduled           pod/payment-api-7c9fd5b6-abc12        Assigned payments/payment-api-7c9fd5b6-abc12 to node-gce-us-e1-a-3\n"
                            "4m          Normal    Pulled              pod/payment-api-7c9fd5b6-abc12        Image v3.2.1 pulled\n"
                            "3m50s       Warning   BackOff             pod/payment-api-7c9fd5b6-abc12        Back-off restarting failed container\n"
                            "5m          Normal    ScalingReplicaSet   deployment/payment-api                Scaled up to 3 from 0 (new revision: 17, from revision 16)\n"
                            "5m          Normal    SuccessfulCreate    replicaset/payment-api-7c9fd5b6       Created pod: payment-api-7c9fd5b6-abc12\n"
                        ),
                        "time_cost_s": 15,
                        "unlocks": ["log-deploy-event"],
                    },
                    {
                        "pattern": r"^kubectl rollout history deployment.*payment-api",
                        "output": (
                            "REVISION  CHANGE-CAUSE\n"
                            "16        Deploy v3.1.8 (rollback candidate, last known good)\n"
                            "17        Deploy v3.2.1 (current, crashing)\n"
                            "   -- annotations show v3.2.1 bumped thread_count: 50 → 100 but did not set MAX_CONNECTIONS\n"
                        ),
                        "time_cost_s": 10,
                        "unlocks": ["log-rollback-avail"],
                    },
                    {
                        "pattern": r"^kubectl rollout undo deployment.*payment-api",
                        "output": (
                            "deployment.apps/payment-api rolled back to revision 16\n"
                            "Watching pods... 3/3 Running. Error rate dropping: 47% → 12% → 2% → 0.3%. SLO green.\n"
                            "Incident resolved. 4m 12s total. Write the post-mortem tomorrow.\n"
                        ),
                        "time_cost_s": 30,
                        "unlocks": [],
                        "is_remediation": True,
                    },
                    {
                        "pattern": r"^kubectl set env deployment.*payment-api.*MAX_CONNECTIONS=\d+",
                        "output": (
                            "deployment.apps/payment-api env updated\n"
                            "Pods restarting with new config... 3/3 Running. Error rate dropping: 47% → 15% → 1%. SLO green in 90s.\n"
                            "Incident resolved via config fix (correct, but rollback would have been faster and safer).\n"
                        ),
                        "time_cost_s": 40,
                        "unlocks": [],
                        "is_remediation": True,
                    },
                    {
                        "pattern": r"^kubectl delete pod",
                        "output": (
                            "pod deleted. New pod spawned by replicaset... also CrashLoopBackOff.\n"
                            "You've destroyed debug context and made no progress. Error rate unchanged.\n"
                        ),
                        "time_cost_s": 20,
                        "unlocks": [],
                    },
                    {
                        "pattern": r"^kubectl scale deployment.*payment-api.*--replicas=0",
                        "output": (
                            "deployment.apps/payment-api scaled to 0\n"
                            "Incoming traffic now fails 100%. Revenue loss accelerating. This is not a fix.\n"
                        ),
                        "time_cost_s": 15,
                        "unlocks": [],
                    },
                    {
                        "pattern": r"^curl (https?://|/)?(\S+/)?health",
                        "output": (
                            "HTTP/1.1 503 Service Unavailable\n"
                            "{\"status\":\"degraded\",\"deps\":{\"postgres\":\"timeout after 30s\",\"redis\":\"ok\"}}\n"
                        ),
                        "time_cost_s": 8,
                        "unlocks": ["log-health-fail"],
                    },
                    {
                        "pattern": r"^kubectl top (pods?|nodes?)",
                        "output": (
                            "NAME                             CPU(cores)   MEMORY(bytes)\n"
                            "payment-api-7c9fd5b6-ghi56       870m         412Mi\n"
                            "auth-service-5b4d8c9-qrs77       22m          140Mi\n"
                            "postgres-primary-0               1240m        2.1Gi     # high — under connection pressure\n"
                        ),
                        "time_cost_s": 12,
                        "unlocks": [],
                    },
                ],
                "log_stream": [
                    {"id": "initial-1", "timestamp": "03:42:18", "level": "ERROR", "line": "[alertmanager] payment-api error_rate 47% > SLO 1%"},
                    {"id": "initial-2", "timestamp": "03:42:19", "level": "WARN",  "line": "[lb] upstream connection failed: connection refused"},
                    {"id": "initial-3", "timestamp": "03:42:22", "level": "ERROR", "line": "[checkout] 4500 failed requests in last 60s"},
                    {"id": "log-discover-pods", "timestamp": "03:42:55", "level": "WARN", "line": "[scheduler] 2 pods in CrashLoopBackOff in namespace payments"},
                    {"id": "log-maxconns", "timestamp": "03:43:05", "level": "INFO", "line": "[observability] deploy 17 of payment-api increased thread_count 50 → 100 at 03:38:41"},
                    {"id": "log-image-diff", "timestamp": "03:43:10", "level": "INFO", "line": "[registry] image diff v3.1.8 → v3.2.1: increased default GOMAXPROCS, more concurrent DB queries"},
                    {"id": "log-rootcause", "timestamp": "03:43:20", "level": "ERROR", "line": "[db] postgres pool max=100 but effective concurrent requests now ~180 (2× thread bump without config update)"},
                    {"id": "log-deploy-event", "timestamp": "03:43:25", "level": "INFO", "line": "[deploy-bot] deploy 17 shipped by @alex-morales at 03:38 via CI/CD pipeline #2847"},
                    {"id": "log-rollback-avail", "timestamp": "03:43:32", "level": "INFO", "line": "[cluster] revision 16 (v3.1.8) available as rollback target — ran clean for 14 days prior"},
                    {"id": "log-health-fail", "timestamp": "03:43:38", "level": "ERROR", "line": "[health] 503 responses now at 52% of total"},
                ],
                "slack_prompts": [
                    {"id": "sp1", "t_offset_ms": 60000, "from": "@priya-pm", "text": "what's going on? getting escalations from enterprise customers"},
                    {"id": "sp2", "t_offset_ms": 180000, "from": "@cfo-office", "text": "revenue dashboard shows ~$6K lost in 3 min — ETA to resolve?"},
                    {"id": "sp3", "t_offset_ms": 360000, "from": "@diana-vp-eng", "text": "CEO is asking if I should wake him. what's your confidence we'll fix in next 10?"},
                ],
                "cascade_rules": [
                    {"trigger_command": "kubectl delete pod", "effect": "error_rate += 5"},
                    {"trigger_command": "kubectl scale deployment.*--replicas=0", "effect": "error_rate += 50"},
                    {"trigger_command": "kubectl exec", "effect": "error_rate += 3"},  # poking at crashed pods
                ],
                "validation": {
                    "grading_rubric": {
                        "time_weight": 0.3,
                        "accuracy_weight": 0.4,
                        "comms_weight": 0.2,
                        "blast_radius_weight": 0.1,
                    },
                },
            },
            "validation": {"manual_review": False},
        },
    ],
}


async def seed():
    async with async_session_factory() as db:
        existing = await db.execute(select(Course).where(Course.id == COURSE_ID))
        prior = existing.scalars().first()
        if prior:
            await db.delete(prior)
            await db.flush()

        course = Course(
            id=COURSE["id"], title=COURSE["title"], subtitle=COURSE["subtitle"],
            description=COURSE["description"], course_type=COURSE["course_type"],
            level=COURSE["level"], tags=COURSE["tags"],
            estimated_time=COURSE["estimated_time"], module_count=COURSE["module_count"],
            icon=COURSE["icon"],
        )
        db.add(course)
        await db.flush()

        for m_data in (MODULE_1, MODULE_2):
            module = Module(
                course_id=COURSE_ID, position=m_data["position"], title=m_data["title"],
                objectives=m_data.get("objectives", []),
                estimated_time=m_data.get("estimated_time"),
                step_count=m_data.get("step_count"),
            )
            db.add(module)
            await db.flush()
            for s_data in m_data["steps"]:
                step = Step(
                    module_id=module.id, position=s_data["position"], title=s_data["title"],
                    step_type=s_data["step_type"], exercise_type=s_data.get("exercise_type"),
                    content=s_data.get("content"), code=s_data.get("code"),
                    expected_output=s_data.get("expected_output"),
                    validation=s_data.get("validation"), demo_data=s_data.get("demo_data"),
                )
                db.add(step)
        await db.commit()
        print(f"Seeded course: {COURSE_ID}")


if __name__ == "__main__":
    asyncio.run(seed())
