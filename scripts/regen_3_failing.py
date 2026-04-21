"""Regen VectorDB + LangChain + Docker/K8s after Creator tightening.

Creator floor now rejects:
- code_exercise with placeholder-stub code (`# Your answer here`)
- system_build with `validation: {manual_review: true}` only (needs real auto-check)
- scenario_branch without `correct: true` on any option per question
"""
import json, urllib.request, time

BASE = "http://localhost:8001"

JOBS = [
    {
        "slug": "vectordb",
        "title": "Master Vector Databases: Pinecone, Weaviate, pgvector, Qdrant",
        "description": (
            "Master vector databases from first principles to production. Cover embedding models, "
            "similarity metrics (cosine, L2, inner product), index types (HNSW M/ef params, IVF nlist/nprobe, flat), "
            "hybrid search (dense + BM25 sparse + Cohere Rerank), metadata filtering, multi-tenancy. "
            "Compare Pinecone vs Weaviate vs pgvector vs Qdrant with REAL benchmarks on named corpora "
            "(disclose vector count, dims, recall@k). EVERY code_exercise has real starter Python — imports, "
            "one working helper, 2-3 TODOs the learner fills in. NO empty stubs. Capstone is system_build "
            "with an auto-graded endpoint_check and must_contain assertions: build a production RAG over "
            "100K legal docs with p95 < 200ms, recall@10 > 0.85, reranking, and an eval harness that RUNS."
        ),
        "course_type": "technical",
    },
    {
        "slug": "langchain",
        "title": "Master LangChain and Langfuse: From Prototype to Observable Agent",
        "description": (
            "Master LangChain + Langfuse for production LLM apps. LangGraph for stateful agents (real code "
            "with nodes, edges, state dict), Langfuse tracing wired end-to-end, prompt versioning via Langfuse "
            "Prompts SDK, dataset evals with LLM-as-judge rubrics, red-teaming with 20+ adversarial prompts. "
            "EVERY code_exercise emits 20-40 lines of real Python (imports, StateGraph skeleton, TODO for "
            "specific nodes). Capstone is system_build with auto-graded must_contain: build a support agent "
            "with LangGraph, wire Langfuse, run 50 eval cases from a JSONL dataset, identify 3 failure modes "
            "from traces, fix them — before/after eval deltas are the deliverable. NO manual_review-only. NO "
            "3-MCQ 'eval suite'. Real 50-row dataset and a harness that RUNS."
        ),
        "course_type": "technical",
    },
    {
        "slug": "docker_k8s",
        "title": "Master Docker and Kubernetes: From Container to Production Cluster",
        "description": (
            "Master Docker + Kubernetes from container fundamentals to multi-service prod. Dockerfile best "
            "practices (multi-stage, layer cache, distroless), docker-compose with healthchecks, k8s primitives "
            "(real YAML for Deployment, Service, Ingress, ConfigMap, Secret), Helm charts (values.yaml, "
            "templates/*.yaml, _helpers.tpl), StatefulSets, HPA, observability (working ServiceMonitor + "
            "Grafana dashboard JSON + Prometheus scrape config), rollout strategies (canary, blue-green), "
            "security (RBAC, NetworkPolicy, image scanning). EVERY code_exercise ships 20-40 lines of real "
            "working-but-incomplete YAML the learner completes — NEVER blank files. Capstone is system_build "
            "with auto-graded must_contain for key resource names + deploys a 3-service app (FastAPI + "
            "Postgres + Redis) to a Kind cluster via Helm — verified with `kubectl rollout status` + curl to "
            "the Ingress. NO manual_review-only capstone."
        ),
        "course_type": "technical",
    },
]


def post(path, body, timeout=1200):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def make_course(job):
    slug = job["slug"]
    t0 = time.time()
    try:
        start = post("/api/creator/start", {
            "title": job["title"], "description": job["description"],
            "course_type": job["course_type"], "level": "Intermediate",
        }, timeout=400)
        sid = start["session_id"]
        answers = [
            {"question_id": q["id"],
             "answer": "Every code_exercise has 15-30 lines of real scaffold, imports, 2-3 TODOs. Capstone has auto-graded validation (endpoint_check or must_contain). NO empty stubs, NO manual_review-only."}
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
        print(f"             subtitle: {cd.get('subtitle')!r}", flush=True)
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
