"""Phase 3: create 5 more courses.
1. AI skills for UX designers
2. AI skills for Ops
3. Master Vector databases
4. Master LangChain + Langfuse
5. Master Docker and Kubernetes

Serial to avoid API saturation. Each ~2-3 min. Total ~15 min.
"""
import json, urllib.request, time

BASE = "http://localhost:8001"


def post(path, body, timeout=1200):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


JOBS = [
    {
        "slug": "ux",
        "title": "AI Skills for UX Designers: From Research Synthesis to Production Mockups",
        "description": (
            "Master the daily AI workflow of a modern Product Designer. Cover AI-accelerated "
            "user research synthesis (Dovetail/Notably transcript clustering, JTBD extraction, "
            "sentiment-tagged quotes), AI-assisted wireframing (Figma + Figma Make, UX Pilot, "
            "Galileo, Visily, Uizard, Musho), design-system token generation, accessibility + "
            "WCAG checks via AI, production-mockup handoff with Storybook snippets, and "
            "stakeholder design-critique prep. Capstone is ONE coherent product feature threaded "
            "from research → mockup → stakeholder defense. The designer produces a real Figma "
            "file artifact + critique notes — not a meta-document about AI design processes."
        ),
        "course_type": "case_study",
    },
    {
        "slug": "ops",
        "title": "AI Skills for Operations Leaders: From Dashboards to Decisions",
        "description": (
            "Master the daily AI workflow of an Ops leader (BizOps, RevOps, Support Ops). "
            "Cover natural-language BI (Looker AI, Amplitude AI, Hex Magic), process automation "
            "with AI agents (Zapier AI, n8n + LLM), vendor selection + TCO with Claude, support "
            "queue triage + macro generation, cross-functional comms + contradiction detection. "
            "Capstone is ONE coherent workday: one metric breaks, exec Slack pings with "
            "contradictory asks, vendor renewal decision due. The Ops leader produces Slack "
            "drafts, status-page text, and a CRO briefing — no engineering code, no decks."
        ),
        "course_type": "case_study",
    },
    {
        "slug": "vectordb",
        "title": "Master Vector Databases: Pinecone, Weaviate, pgvector, Qdrant",
        "description": (
            "Master vector databases from first principles to production. Cover embedding models "
            "(OpenAI text-embedding-3, Voyage, Cohere, open-source MiniLM), similarity metrics "
            "(cosine, L2, inner product), index types (HNSW, IVF, flat), hybrid search (dense + "
            "sparse + rerank with Cohere Rerank), metadata filtering, multi-tenancy, and cost "
            "optimization. Compare Pinecone vs Weaviate vs pgvector vs Qdrant with benchmarks. "
            "Capstone: build a production RAG system over 100K documents with hybrid search, "
            "p95 < 200ms, with reranking and eval harness — learner ships the actual code + "
            "deployment config."
        ),
        "course_type": "technical",
    },
    {
        "slug": "langchain",
        "title": "Master LangChain and Langfuse: From Prototype to Observable Agent",
        "description": (
            "Master LangChain + Langfuse for production LLM applications. Cover LangChain core "
            "primitives (chains, agents, tools, memory, output parsers), LangGraph for stateful "
            "multi-step agents, Langfuse for tracing/observability/evals, prompt versioning, "
            "cost tracking, A/B testing prompts in production, and red-teaming agents. Capstone: "
            "build and SHIP a customer-support agent with LangChain + Langfuse tracing, run it "
            "against 50 eval cases, identify 3 failure modes from traces, and fix them — with "
            "the before/after eval deltas as the deliverable."
        ),
        "course_type": "technical",
    },
    {
        "slug": "docker_k8s",
        "title": "Master Docker and Kubernetes: From Container to Production Cluster",
        "description": (
            "Master Docker + Kubernetes from container fundamentals to multi-service production "
            "deployments. Cover Dockerfile best practices (multi-stage, layer caching, distroless), "
            "docker-compose for local multi-service stacks, Kubernetes primitives (pods, services, "
            "deployments, ingress, ConfigMaps, Secrets), Helm charts, StatefulSets for stateful "
            "workloads, observability (Prometheus, Grafana, kubectl debug), rollout strategies "
            "(blue-green, canary), and security (RBAC, network policies, image scanning). Capstone: "
            "deploy a 3-service app (API + Postgres + Redis) to a real k8s cluster (kind/minikube) "
            "with Helm, test rolling updates, verify observability — ship the actual manifests."
        ),
        "course_type": "technical",
    },
]


def make_course(job):
    slug = job["slug"]
    t0 = time.time()
    try:
        start = post("/api/creator/start", {
            "title": job["title"],
            "description": job["description"],
            "course_type": job["course_type"],
            "level": "Intermediate",
        }, timeout=400)
        sid = start["session_id"]
        answers = [
            {"question_id": q["id"],
             "answer": "One coherent scenario threaded through every module. Name real tools. "
                       "Capstone is a concrete deliverable learner ships by the end — not a meta-doc."}
            for q in start.get("questions", [])[:4]
        ]
        print(f"  [{slug}] refining...", flush=True)
        refine = post("/api/creator/refine", {"session_id": sid, "answers": answers}, timeout=1200)
        n_mods = len(refine["outline"]["modules"])
        last_step = refine["outline"]["modules"][-1]["steps"][-1]
        print(f"  [{slug}] generating {n_mods} modules (capstone: {last_step['exercise_type']})...", flush=True)
        g = post("/api/creator/generate", {"session_id": sid, "outline": refine["outline"]}, timeout=1200)
        cid = g["course_id"]
        cd = json.loads(urllib.request.urlopen(f"{BASE}/api/courses/{cid}", timeout=30).read())
        print(f"  [{slug}] DONE {cid} ({int(time.time()-t0)}s) — {len(cd['modules'])} modules", flush=True)
        print(f"              subtitle: {cd.get('subtitle')!r}", flush=True)
        return {"slug": slug, "ok": True, "course_id": cid}
    except Exception as e:
        print(f"  [{slug}] FAIL ({int(time.time()-t0)}s): {e}", flush=True)
        return {"slug": slug, "ok": False, "error": str(e)}


if __name__ == "__main__":
    b0 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"Budget before: ${b0['spent_usd']:.2f}", flush=True)

    results = []
    for j in JOBS:
        results.append(make_course(j))

    print("\n--- SUMMARY ---")
    for r in results:
        if r["ok"]:
            print(f"  {r['slug']:12} {r['course_id']}")
        else:
            print(f"  {r['slug']:12} FAIL: {r['error']}")

    b1 = json.loads(urllib.request.urlopen(BASE + "/api/admin/budget").read())
    print(f"\nBudget after: ${b1['spent_usd']:.2f} (delta: ${b1['spent_usd']-b0['spent_usd']:.2f})")
