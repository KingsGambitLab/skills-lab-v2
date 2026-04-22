# Creative Capstone Research: Toward Real-Work Pedagogy in Skills Lab v2
## Date: 2026-04-21
## Researcher: Technical Pedagogy Researcher — combines developer-experience design, autograding infrastructure, and 2020-2026 hands-on learning-platform practice. Inputs: the SWE review (`/reviews/swe_assignment_review_2026-04-21.md`, 27 exercises across 8 courses) plus the CLAUDE.md spec (16 exercise types, workday-simulator north star, shipped `adaptive_roleplay` / `incident_console` / `simulator_loop` / `voice_mock_interview`). Output: 10 new or refined capstone formats, 4 refinement bundles to the existing types, and a shippable 1-week / 1-month / 1-quarter roadmap.

---

## 1. Key themes from the SWE review (quote + restate)

The review's voice is calm, numerate, and specific. Restated as themes — in the order they surface bugs the Creator+runtime combination cannot hide:

### Theme A — "The grader cannot tell real work from a cheese."
This is the review's headline bug and the single strongest signal for every proposal below. Direct quotes:

> "Empty code scores 0, token-stuffed print() hacks score 60%, and real correct code scores 60%. A learner cannot distinguish their real work from a cheese." (Executive summary #1)

> "Real solution: stub otel, call `FastAPIInstrumentor.instrument_app(app_tracking)` ... 60%. Pure hack solution: `print(\"FastAPIInstrumentor.instrument_app(app_tracking)\")` (3 prints, no imports, no logic). 60% — SAME SCORE." (step 349 HACK comparison)

> "A `print()` of every required token scores the same 60% as a real solution (step 349 definitive evidence). ... The incentive is backwards."

Any new capstone format we introduce must pass a "cheese test": can a learner who does no real work score anywhere near a learner who does the real work? Every proposal below is designed so the answer is "no" — grading reads **state or behavior**, not **source tokens**.

### Theme B — "All five capstones hit an unreachable URL."
The review is blunt:

> "All `system_build` capstones grade against unreachable URLs — `http://your-deployed-service/health`, `https://your-deployment.aws.com/health`, an empty string, a localhost reference, a GitHub repo that 404s. No capstone can actually be completed end-to-end."

> "Every capstone I reviewed is a doc-write disguised as a ship-deliverable... either the learner takes the 2-hour 'ship it' task seriously, goes deep, ends up with real artifacts — and is unrewarded by the grader (0%). Or the learner writes `/done` in the checklist without doing any work and gets the same 0%."

5/5 capstones failed. The marketing-grade deliverable is 0% reachable. The course completion rate that matters most — "did the learner ship a real thing?" — cannot be measured. Note: F24 (the `gha_workflow_check` primitive in CLAUDE.md) is already designed to fix a subset of this; the proposals below extend it to non-GHA surfaces (live HTTP, K8s cluster state, DB state, OTel spans actually emitted).

### Theme C — "The sandbox is missing 40% of the libraries the scaffolds import."
Specifically:

> "The sandbox is missing a large fraction of the libraries that the scaffolds import — `bcrypt`, `confluent_kafka`, `kafka`, `psycopg2`, `opentelemetry.*`, and `httpx.Response` (httpx is stubbed). A competent learner who reads the scaffold and runs 'execute' immediately hits ModuleNotFoundError on ~40% of Python exercises."

> "At least 4 of 11 courses I sampled have this issue (Async bcrypt step, Kafka, OTel, and partially Async httpx)."

The reviewer also notes (step 280): "The hint 'Use `await asyncio.to_thread(bcrypt.checkpw, password_bytes, user_hash)`' is useless when bcrypt can't even import." The scaffold is the first thing a learner touches. An import-failing scaffold is a first-impression failure.

### Theme D — "Grader-internal state leaks into must_contain."
Step 334 (Kafka SETNX): the `must_contain` includes `assert r.set.call_count == 100` — a magic number from a hidden test harness. Step 452: `must_contain` includes literal regex fragments like `redis_timeout.*\+=`. The reviewer's phrase for this: "internal-implementation-leakage." Any `must_contain` that references a variable, test function, or integer constant the learner has never seen is grading-over-reach. Quote:

> "If they write `assert r.set.call_count >= 100` or call it 99 times, they lose points on a completely reasonable implementation. This is grader-over-reaching."

### Theme E — "Code_review bug lists disagree with senior-engineer judgment."
Step 232: the Dockerfile review skips `apt-get`-without-cleanup (several-hundred-MB bloat) AND the commented-out `USER` (runs as root in prod). Step 286: the "kitchen sink Query type" exercise is literally titled after the anti-pattern of having 10 root fields — and that anti-pattern is **not flagged by the grader**. The reviewer:

> "The 5 flagged bugs are all real but tangential... Line 44 `random_stuff → 42` is not flagged despite being a literal parody of the anti-pattern the exercise is named after."

And step 315:

> "Grader says '8/8' but `demo_data.bugs` has 9 entries. Either the demo_data overstates the count OR one bug is unreachable via line-number clicks. The UI will display '9 bugs' but the grader only rewards 8 — the learner thinks they missed one when they didn't."

### Theme F — "Parsons is globally broken — an entire exercise type returns 0%."
> "0% on every single attempt. 0/6 lines, longest correct subsequence 0... The grader never matches ANY key I tried. ... an entire exercise type is unusable."

> "There are 8 parsons exercises across the AI Power Skills course alone."

Even when the pedagogical idea is sensible, a payload-key mismatch makes the surface dead. This implies a broader point: any new exercise type must ship with an **integration test that submits the canonical correct answer and asserts score == 1.0** before going live.

### Theme G — "Fill_in_blank is the exemplar — when it works."
Step 345 (OTel semantic convention): 5/5 with a permissive `alternatives` list (`http.method` and `http.request.method` both accepted). Reviewer: "This is how ALL FIB exercises should work."

The lesson: grading must be **synonym-aware**. A correct idea expressed in a slightly different vocabulary should not be penalized. This is Theme A's dual: not only should cheese score low, but correct-but-differently-shaped work should score high.

### Theme H — "Briefings are consistently high quality. The grading infrastructure is the problem."
> "The briefings promise 'ship this to production,' the checklists correctly enumerate the real work (build image → Dockerize → write compose → deploy → smoke-test), and the deployment_config even specifies platforms (Railway, GitHub Actions). But the actual grading probe is an unreachable URL."

> "The content quality is *not* the problem; the *grading infrastructure* is."

This is the most actionable framing in the whole review. The Creator is already writing plausibly-excellent content. The fix is at the engine/runtime level — not at the prompt level.

### Theme I — the 60% cap is a grading-logic bug, not a content bug.
> "`code_exercise` grader appears to multiply must_contain × output-match, with a default 60% cap when either is missing / impossible."

This is a tractable engine change. Everything below assumes it is fixed (per recommendation #1 in the review) — the proposals add new *signals* the grader can multiply by, rather than cluttering the existing signals.

### Theme J — "The grader never matches any key I tried."
This is the most frightening theme in the review. It is a product-quality failure: the reviewer paid real attention, tried 5 payload shapes, and still could not reach the grader. If a senior SWE can't guess the API, neither can a learner. Every new exercise type we ship must carry a **self-describing schema** (the learner client negotiates the payload shape from metadata returned by `GET /step/{id}`, not from folk knowledge).

---

## 2. Industry scan (table)

Each row lists one platform, the specific mechanic it does better than our shipped stack, and how that mechanic maps onto Skills Lab v2. Only platforms where a concrete lesson-for-us exists are included — general overviews filtered out.

| Platform | What it does right | Applicable lesson for Skills Lab v2 |
|---|---|---|
| **KodeKloud** | "Scoring in KodeKloud labs is done by a grading script, which examines the **end state** of the system. The grading process does not consider how you arrived at the solution." [kodekloud](https://kodekloud.com/) | For K8s / Docker / SQL capstones, run a check script against **real cluster or DB state** (`kubectl get`, `SELECT`), not against the learner's source code. See Proposal 1 (`cluster_state_check`) + refinement to `system_build`. |
| **Killercoda** | Scenario has a `verify.sh` script that runs server-side after learner clicks "Check" — pass/fail based on exit code. [killercoda faq](https://killercoda.com/faq) | Add a `verify_shell` primitive to `code_exercise` that the grader runs with the learner's filesystem mounted. Score = 0/1 from exit code + parsed stdout JSON. See Proposal 1. |
| **Instruqt** | Four lifecycle scripts per challenge: `setup`, `check`, `solve`, `cleanup`. **The `solve` script is run during `instruqt track test` to guarantee any challenge is winnable.** [instruqt docs](https://docs.instruqt.com/tracks/manage/test-a-track) | Borrow the `solve → check → expect 1.0` invariant. Every Creator-generated capstone must ship a reference `solve.sh` that the engine runs in CI; no capstone merges into the catalog unless the canonical solution scores 1.0. Directly fixes Theme F (Parsons globally broken) and Theme B (no capstone reachable). |
| **Kaggle** | "Public / Private test split — the Private set is hidden from learners until the competition ends." "Shake-up": overfitting to a public grader is penalized at closure. [kaggle docs](https://www.kaggle.com/docs/competitions) | Held-out eval sets for anything benchmark-able (retrieval accuracy, classification precision, SQL query latency). A learner tunes against a public subset; their final grade is computed against a hidden private subset they never saw. See Proposal 2 (`benchmark_arena`). |
| **StackBlitz WebContainers** | "Run the native versions of npm, pnpm, and yarn, all in the browser, all in your app, up to 10x faster than local." `npm install` works against the real registry inside the tab. [webcontainers.io](https://webcontainers.io/) | Solves our ImportError-on-scaffold problem. For any Node/Bun exercise we can materialize a real `package.json` and let the learner `npm install httpx bcrypt confluent-kafka-js` — no sandbox stub list to maintain. Python needs a different solution (Pyodide) but the architecture is identical. See Proposal 3 (`live_dev_workspace`). |
| **Hack The Box / TryHackMe** | Flag-format `THM{...}` submission scheme. Grader is a string-compare against a per-learner-salted secret that was only obtainable by actually exploiting the scenario. [thm help](https://help.tryhackme.com/en/articles/8473460-capture-the-flag-ctf) | For security courses, "cheese-proof" final step: learner submits a flag they can only have seen by performing the required action on a live target VM. Applies to any capstone where "I got to the end" can be proved by a piece of state only the successful path generates. See Proposal 4 (`artifact_flag_capstone`). |
| **Gremlin Chaos GameDays** | "Up to 20 scenarios ... teams mark Passed or Failed after running, then add post-run notes." [gremlin docs](https://www.gremlin.com/docs/fault-injection-gamedays) | Run a learner-driven GameDay where the *learner* chooses which chaos experiments to run against a simulated system, then grade on whether their hypothesis (written pre-experiment) matched the actual blast radius. Turns SRE-course passive content into active experimental science. See Proposal 5 (`chaos_hypothesis_drill`). |
| **Advent of Code** | Per-learner randomized puzzle input; submission is a pure string/number answer. "You never submit any code. You just submit the answer." No grading of code style — only: did your answer hash match? [aoc about](https://adventofcode.com/2024/about) | For any course with a hard-computed deterministic output (SQL result, ML metric, parse result), generate a per-learner input seed; grade by hash of learner's numeric/string answer. Impossible to cheese, impossible to share solutions. See Proposal 2 variant and refinement to `code_exercise`. |
| **CodeGrade** | "Code Quality test step makes industry standard linters and static code quality assessment tools available, such as ESLint for JavaScript, with the ability to upload custom style guides and rules." [codegrade](https://www.codegrade.com/blog/automatically-grading-javascript-code-assignments) | Drop `must_contain` substring matching. Replace with: lint pass (ruff/eslint), test pass (pytest/jest), coverage threshold (pytest-cov), style/typing (mypy/tsc). Grading composes per-signal scores; each signal has a public weight. See §4 refinement of `code_exercise`. |
| **Gradescope** | "Instructors provide a **setup script** and an **autograder script**, and Gradescope manages accepting student submissions, running the autograder at scale, and distributing results." [gradescope guides](https://guides.gradescope.com/hc/en-us/articles/22066635961357) | Standardize the autograder interface. Every course's grader is a container that takes `/submission/` → produces `/result/score.json` with per-test pass/fail + per-test weight. Removes tight coupling between the LMS engine and the Creator's freeform `must_contain` spec. See §5 grading cross-cutting recs. |
| **GitHub Classroom** | "After a student accepts an assignment, on every push to the assignment repository, GitHub Actions runs the commands for your autograding test." [github docs](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding) | Exactly what CLAUDE.md's F24 (`gha_workflow_check`) points at. Extend it: every capstone in the catalog ships with an owned starter-repo, a `.github/workflows/lab-grade.yml`, and a reference `solve.sh`. Proposal 6 (`github_classroom_capstone`). |
| **Exercism mentor track** | "Mentors typically provide one to three pieces of feedback on any iteration, and when students submit new iterations with the feedback addressed, mentors give another one to three pieces of feedback." [exercism docs](https://exercism.org/docs/mentoring/how-to-give-great-feedback) | LLM-as-mentor iteration loop: learner submits, AI (Haiku) returns ≤ 3 focused improvements, learner resubmits, AI re-checks only the new delta. Max 3 iterations per exercise. Budget-controlled. See Proposal 7 (`mentored_iteration`). |
| **Frontend Mentor** | "Design comparison slider — see the difference in final solution vs the design." AI-report spots 3× more issues than humans. [frontendmentor](https://www.frontendmentor.io/) | For any UI-building capstone, ship a Figma export or reference screenshot + pixel-diff grader. "Build this UI so it matches the reference within threshold T on dimensions {layout, typography, palette, spacing}." See Proposal 8 (`pixel_diff_capstone`). |
| **Boot.dev + `bootdev` CLI** | "Deploy real infrastructure to your own AWS account, with a bootdev CLI that verifies the state of infrastructure and provides real-time feedback." [boot.dev](https://www.boot.dev/) | The *learner's CLI* runs the check. A local `sll-lab check` tool is published to PyPI/npm; it authenticates against our API, probes the learner's own environment, and reports findings back. Works for on-the-learner-box capstones (K8s cluster, local FastAPI). See Proposal 9 (`local_cli_verifier`). |
| **HackerRank CodePair / Virtual Whiteboard** | "Live collaborative coding — integrated video, audio, text chat, records every keystroke for replay." Virtual whiteboard supports system design. [hackerrank codepair](https://www.hackerrank.com/products/interview) | For system-design capstones, ship a multi-box + arrow canvas where learners draw, an LLM interviewer asks probing follow-ups ("what if traffic 10×?"), and grading is on depth of reasoning, not artifact-match. See Proposal 10 (`system_design_live`). Also complements existing `voice_mock_interview`. |
| **PagerDuty IC training + "Failure Fridays"** | "Purposefully inject failure into their systems to test their resilience, treating this like a major incident with an incident commander." [pagerduty](https://response.pagerduty.com/training/incident_commander/) | Extend `incident_console` with a **multi-role pager rotation** mode: learner rotates through IC / SME / Comms roles across a 30-minute simulated on-call shift. Grades on role-switching quality. See refinement to `incident_console`. |
| **Property-based testing (Hypothesis, QuickCheck)** | "Models are developed to assess both the functional behaviour of programs and their algorithmic complexity, and from the functional correctness model a large number of test cases are derived automatically." (Academic: [ACM-ITiCSE-2016](https://dl.acm.org/doi/10.1145/2899415.2899443)) | Replace `must_contain` + `expected_output` with a **property test**. Creator specifies properties ("for any sorted list input, output should be monotonically non-decreasing"); grader runs 200 randomized inputs through the learner's function. Score = pass-rate. Cheese-proof: a print-spam solution fails any actual property check. See Proposal 11 (`property_test_grader`). |

---

## 3. Novel capstone formats (11 proposals)

Each proposal addresses one or more SWE themes by name. The unifying design constraint: **grade behavior or state, never source tokens.** A second constraint: use **existing public infrastructure** (GitHub Actions, public registries, WebContainers, Docker Hub) wherever possible; avoid bespoke runtime work.

### Proposal 1: `cluster_state_check` — grade against real Kubernetes / Docker / DB state

**Real-world analog**: A platform engineer gets a Jira ticket: "payment-api is running in degraded mode on the prod cluster — fix it." They `kubectl get pod`, `kubectl describe`, `kubectl apply -f patch.yaml`, and the success criterion is the cluster's end-state (healthy pods, correct replicas, service reachable), not what they typed in their terminal history. KodeKloud's entire lab pedagogy is built on this; our `incident_console` already captures the "live console" feel but grades a scripted log unlock, not actual cluster state.

**Pedagogy**: Forces the learner to produce **real manifest / SQL / kubectl state** instead of prose about it. A `print("kubectl apply -f fix.yaml")` hack fails by construction — the check is `kubectl get deployment payment-api -o json` and inspecting `.status.readyReplicas == 3`. Directly addresses Theme A (no cheese possible) and Theme B (capstone grading now runs against a real target).

**UI sketch**:
- Left pane: the classic Skills Lab console output view, streaming `kubectl` / `docker` / `psql` commands the learner types.
- Right pane: "Target state" — a dark card listing the 6 specific assertions (`.status.readyReplicas >= 3`, `deployment.metadata.annotations['maintained-by'] == 'SRE'`, `Service payment-api has Endpoints > 0`, etc.) with a green-check / red-X next to each. Updates live as the learner's state changes.
- Top banner: "You have 20 minutes. When you think it's fixed, click **Submit**; we'll re-run all assertions."
- Learner uses our in-browser terminal (already wired in `incident_console`) to actually mutate the ephemeral cluster.

**Data shape**:
```json
{
  "exercise_type": "cluster_state_check",
  "demo_data": {
    "briefing": "The payment-api deployment is in CrashLoopBackOff...",
    "cluster_template": "k3d://skills-lab/templates/broken-payment-api",
    "time_budget_s": 1200,
    "allowed_tools": ["kubectl", "k9s", "curl"],
    "starter_files": [
      {"path": "manifests/deployment.yaml", "contents": "..."}
    ]
  },
  "validation": {
    "assertions": [
      {"id": "ready", "cmd": "kubectl get deploy payment-api -o json",
       "jsonpath": "$.status.readyReplicas", "op": ">=", "value": 3, "weight": 0.3},
      {"id": "env", "cmd": "kubectl get deploy payment-api -o json",
       "jsonpath": "$.spec.template.spec.containers[0].env[?(@.name=='MAX_CONNECTIONS')].value",
       "op": "==", "value": "100", "weight": 0.2},
      {"id": "health", "cmd": "curl -sf http://payment-api.cluster.local/healthz",
       "expect_exit": 0, "weight": 0.3},
      {"id": "no_destructive", "cmd": "kubectl get events --field-selector reason=Killing",
       "expect_count_below": 5, "weight": 0.2}
    ],
    "solve_script": "kubectl set env deploy/payment-api MAX_CONNECTIONS=100 && kubectl rollout restart deploy/payment-api"
  }
}
```

**Grading rubric**: Score = weighted sum of passing assertions. Every assertion runs server-side against the learner's ephemeral k3d/kind cluster. Zero token matching. Zero learner-source inspection.

**Sandbox requirements**:
- One ephemeral k3d (K3s-in-Docker) cluster per learner, per session. Spin up from a snapshotted template on session start, tear down on submit. Budget: ~200 MB memory + 1 vCPU-minute per session.
- Alternatively: share a multi-tenant k8s cluster and scope each learner to a namespace + NetworkPolicy. Cheaper at scale.
- Same pattern for Docker (Docker-in-Docker), Postgres (per-learner ephemeral DB), Kafka (Redpanda per learner), Redis.
- This is the "missing runtime" that Theme C complains about. Once built, `bcrypt` / `confluent_kafka` / `opentelemetry` stop being our problem — the learner runs real `pip install` inside their own ephemeral container.

**Budget**: $0 LLM per session (grading is scripted). ~$0.01 compute per session (5-min ephemeral cluster on a burst-sized box).

**Why-real-life score**: **10/10** — identical to how a real engineer works: edit YAML, apply, observe cluster, repeat.

**Implementation difficulty**: **8/10** — the biggest piece of infra work in this proposal set. Requires: (a) ephemeral cluster provisioning, (b) per-learner network isolation, (c) an assertion DSL (cmd + jsonpath + op), (d) a Creator prompt that produces assertion blocks, (e) extending `_is_complete()` to reject cluster-state capstones without at least 4 assertions + a `solve_script`. But once built, covers K8s, Docker, Helm, terraform-apply, DB migration — roughly 25% of our capstone surface.

**Recommended ship order**: Quarter-1 (after F24/GHA pathway proves the external-grader pattern; this is the in-house version of the same idea).

---

### Proposal 2: `benchmark_arena` — Kaggle-style held-out eval with public/private split

**Real-world analog**: An ML engineer at Velora is asked to build a retrieval service for 2.8M SKUs. They iterate against a validation set, tune, iterate. On launch day, prod traffic is a different distribution — they find out how well they really tuned. Kaggle's public/private leaderboard reproduces exactly this dynamic: tune against public, graded on hidden private.

**Pedagogy**: Teaches **generalization discipline** — "if I overfit to the eval I can see, I get punished at submit time." Our current courses never test this. Applies to: retrieval (top-k precision), classification (F1), SQL query performance (p95 on unseen data), RAG quality (retrieval recall on held-out questions), semantic search, ranking, any ML/data capstone. Addresses Theme A (can't cheese a held-out metric) + Theme H (Creator writes vivid "CartFlow 2.8M SKU" scenarios → we now grade the claim).

**UI sketch**:
- Left pane: code editor + public eval button ("Run on 500-row public set"). Returns a live score against the visible subset; learner can iterate 50 times.
- Right pane: **public leaderboard** showing peer pseudonyms and scores, plus a "private leaderboard locks in 6h" countdown.
- Submit button: locks their current solution hash, schedules the private-eval job. At unlock: big modal — "public: 0.84 → private: 0.76. You overfit by 0.08. Here's which slices of the hidden set you missed." (This failure mode is pedagogically the *point*.)

**Data shape**:
```json
{
  "exercise_type": "benchmark_arena",
  "demo_data": {
    "briefing": "CartFlow's 2.8M SKU search has p@10 = 0.62. Get it above 0.80.",
    "task": "implement_retrieval",
    "interface_contract": "def search(query: str, k: int = 10) -> list[dict]",
    "starter_repo": {"url": "https://github.com/skills-lab-demos/cartflow-retrieval", "ref": "main"},
    "public_eval_dataset_url": "https://cdn.sll.ac/arena/cartflow/public.jsonl",
    "public_eval_size": 500,
    "iteration_limit": 50
  },
  "validation": {
    "metric": "precision_at_10",
    "private_eval_server": "https://arena.sll.ac/eval/cartflow",
    "private_eval_size": 5000,
    "passing_threshold": 0.72,
    "excellence_threshold": 0.82,
    "grading_formula": "max(0, (private_score - 0.5) / 0.4)"
  }
}
```

**Grading rubric**: Linear scaling between passing threshold (e.g., 0.72) and excellence threshold (e.g., 0.82). `score = clamp01((private - pass) / (excellence - pass))`. Anti-cheese: the private set isn't exposed; the eval server rejects submissions whose `public_score > private_score + 0.10` (obvious overfitting) with a warning.

**Sandbox requirements**:
- Eval server = FastAPI service running on our infra, loaded with the hidden dataset in memory.
- Learner's submission is a container image (or a pip-installable wheel, or a git ref). Eval server spins up the learner's code in isolation, runs 5000 queries, times out at 10 min.
- Per-course: one curated public + private dataset pair. Not every course needs this — only data/ML/retrieval/ranking ones.

**Budget**: $0.02 LLM per session (just for the post-submit coaching summary via Haiku). ~$0.05 compute per submit (5000-query eval).

**Why-real-life score**: **9/10** — the only reason not 10 is that real production work is measured on live traffic, not a static held-out set. But this is still the closest thing a learner can get.

**Implementation difficulty**: **6/10** — moderate. Needs: eval-server container, dataset-curation pipeline, leaderboard UI, submit-rate-limiting. Reuses: starter-repo pattern from F26, external-grader pattern from F24.

**Recommended ship order**: Month-1. Ship ONE benchmark (CartFlow retrieval or Velora classification) as proof; scale to other data/ML courses after pattern validated.

---

### Proposal 3: `live_dev_workspace` — WebContainer-backed real filesystem + real npm install

**Real-world analog**: A developer clones a repo, `npm install`, runs tests, fixes failing tests. The moment-to-moment loop of real work. StackBlitz WebContainers make this run entirely in a browser tab with native Node.js speed.

**Pedagogy**: Closes the 40% import-fail rate (Theme C) **permanently** for Node/JS/TS courses and creates a path to closing it for Python (via Pyodide). Instead of maintaining a mock-module list that must be updated each time a course references a new library, **the learner does a real install against the real registry**. `bcrypt`, `confluent-kafka-js`, `@opentelemetry/*` all just work. A failing install is itself a real learning moment ("your Node version is wrong — fix the engines block").

**UI sketch**:
- Three-pane IDE: file tree left, editor center, terminal bottom-right.
- Pre-materialized project: `package.json`, `src/`, `test/`, `README.md`. Opens pre-warmed with `npm install` already run (via WebContainer prebuild) so first impression is "things work."
- Green "Run Tests" button ↔ terminal tab with jest output.
- "Submit" runs the full test suite against a hidden extra-tests directory that the learner can't read but whose pass-rate becomes the grade.

**Data shape**:
```json
{
  "exercise_type": "live_dev_workspace",
  "demo_data": {
    "runtime": "webcontainer_node",
    "workspace_template_repo": "https://github.com/skills-lab-demos/async-scatter-ts",
    "prebuild_commands": ["npm ci", "npm run typecheck"],
    "learner_entry": "src/scatter.ts",
    "visible_tests": "test/scatter.public.spec.ts",
    "time_budget_s": 1800
  },
  "validation": {
    "hidden_tests_ref": "test/scatter.hidden.spec.ts",
    "grading_formula": "tests_passed / total_tests",
    "rubric_weights": {"correctness": 0.7, "perf_budget": 0.2, "lint_pass": 0.1}
  }
}
```

**Grading rubric**: Hidden test suite pass rate. For perf-sensitive tasks (our scatter-gather in step 263), a `perf_budget` check measures wall-clock against a threshold. Cheese test: a stub that hardcodes a return value fails all hidden tests except the trivial one.

**Sandbox requirements**:
- WebContainer iframe embedded in our frontend for JS/TS/Python-via-Pyodide. Runs in learner's browser — zero server compute.
- A per-exercise Git template repo hosted on a public GitHub org we own (`skills-lab-demos`).
- Hidden tests stored server-side; the grader clones the workspace, runs hidden tests in a sandboxed Node container on our infra, not in the browser (keeps tests secret).

**Budget**: $0 compute in the browser (WebContainer is client-side). ~$0.005 per submit for server-side hidden-test run (a 30-second Node container).

**Why-real-life score**: **9/10** for JS/TS. Python via Pyodide limits some native deps (`bcrypt`'s C extension is iffy) so **7/10** for Python; still beats today's sandbox.

**Implementation difficulty**: **5/10** — WebContainer integration is well-documented; the heavy lift is: (a) generate workspace templates via Creator, (b) write the hidden-tests pattern, (c) a "re-materialize workspace" button for when learners break it.

**Recommended ship order**: Month-1. Replaces ~40% of our current `code_exercise` types for JS/TS + async/http courses. Biggest first-impression win.

---

### Proposal 4: `artifact_flag_capstone` — CTF-style "prove you got there" by submitting a harvested value

**Real-world analog**: A security engineer chases a vulnerability through a system. They don't write a report mid-chase — they extract a specific piece of data (a config value, a token, a hash) that only appears when the exploit chain succeeds. This is the CTF pattern: a `flag{...}` string is in the system, visible only to a successful attacker.

**Pedagogy**: Generalizes beyond security. In *any* capstone where the "did you really complete the work" is provable by a piece of state only the finished work generates:
- **Security**: SQL injection capstone — the learner recovers a hash buried in `admin.config`; the hash is per-learner, generated from the learner's user-id at cluster creation.
- **Data / ML**: after running a RAG pipeline against a specific corpus, the learner emits the answer to "what's the policy number mentioned in claim CLM-2026-458912?" The answer is known only to someone who actually retrieved + ranked + extracted correctly.
- **Observability**: after instrumenting a trace, the learner extracts the span-id of the DB call from the exported OTLP stream — provable that OTel is actually wired, not just text-claimed.
- **Git**: after finishing the rebase drill, the learner copies the final commit SHA. Because the starter is per-learner (tiny random commit in the starter repo), the SHA is unique per-learner. A shared-answer can't work.
- **Kafka**: the learner publishes an event, the grader tails the partition and reads the event's checksum. If the checksum matches expected-per-learner, done.

**UI sketch**: Minimal — a single text input labeled "Paste the recovered flag / token / checksum / commit SHA here." Above it: the briefing + a live tail of the system's logs (so they see progress toward harvesting the artifact). Below: "Submit." Grader is a sha256 equality check against a per-learner-salt secret.

**Data shape**:
```json
{
  "exercise_type": "artifact_flag_capstone",
  "demo_data": {
    "briefing": "You have a running broken RAG pipeline. Fix the retrieval, then tell me the policy number from claim CLM-2026-458912.",
    "starter_system_url": "https://lab.sll.ac/session/{sid}/rag-pipeline",
    "expected_artifact_format": "POL-[0-9]{8}",
    "hint": "The answer is in the top-1 retrieved doc after a correctly-tuned retrieval."
  },
  "validation": {
    "artifact_hash_salt": "per-learner-uuid",
    "expected_artifact_sha256": "{computed per-learner at session start}",
    "regex_shape": "^POL-[0-9]{8}$"
  }
}
```

**Grading rubric**: Binary by default (you found it or you didn't). Optional: partial credit for submitting near-misses within Levenshtein distance 2 (e.g., flipped 2 digits = 0.5 score + a "so close" hint). Cheese-proof by construction: the answer is unique per-learner and only appears in the system state after the real work is done.

**Sandbox requirements**:
- Per-learner ephemeral "treasure hunt" system. Reuses the cluster infra from Proposal 1.
- A seed-generation script per capstone that, given learner-id, produces the system's initial state AND the expected flag.
- Answer-submission endpoint that hashes the submitted string and compares.

**Budget**: $0 LLM. ~$0.02 compute per session (a 20-min ephemeral system).

**Why-real-life score**: **8/10** — matches the "extract a specific value from a working system" dynamic common in ops / security / data-forensics roles. Slightly lower than Proposal 1 because the final submission is a single string, not multiple state changes. But the path to that string is the whole job.

**Implementation difficulty**: **6/10** — needs: per-learner seed generator, a small library of capstone scenarios with seeded secrets, submission endpoint.

**Recommended ship order**: Month-1 (for security courses, which currently lack a capstone format entirely), Quarter-1 (generalized to other domains).

---

### Proposal 5: `chaos_hypothesis_drill` — Gremlin-style GameDay where the learner proposes + tests a failure hypothesis

**Real-world analog**: PagerDuty's "Failure Fridays": engineers pick a service, write a hypothesis ("if we kill the replica primary, the secondary takes over within 20s and we see no 5xx spike"), inject the fault, observe, write a post-mortem. Gremlin GameDays formalize exactly this loop.

**Pedagogy**: Teaches **experimental science under production constraints** — a skill totally absent from our current curriculum. Our `incident_console` is reactive (alert fires → you respond). This is proactive — you prove a system behaves as you think it does, or you discover you were wrong.

Real seniority bar: "can you form a falsifiable hypothesis, design an experiment that would refute it, run the experiment safely, interpret the result?" That's the promotion criterion for many SRE / staff / principal roles. No course in our catalog trains this today.

**UI sketch**:
- Pane 1: **Hypothesis card** the learner types into first. "If we kill 1 of 3 replicas of `payment-api`, we expect {specific metric: error rate stays < 2%} and {other metric: p95 latency rises <= 50ms}." Required fields: one binary prediction + two quantitative predictions.
- Pane 2: **Experiment console** — the learner picks a chaos action (`kill_pod`, `network_latency`, `cpu_saturate`, `dns_fail`) and applies it to a named target.
- Pane 3: **Live telemetry** — a live-updating dashboard showing the metrics they predicted about, plus 4 distractor metrics (realistic production noise).
- Pane 4: **Post-mortem** (after they click "end experiment"): guided form asking them to compare predicted vs actual, identify what surprised them, and propose one follow-up.

**Data shape**:
```json
{
  "exercise_type": "chaos_hypothesis_drill",
  "demo_data": {
    "scenario": "Velora payment-api: 3 replicas, 200 rps synthetic, 99.5% SLO.",
    "system_template": "gremlin_lab://templates/payment-api-3replica",
    "available_chaos": ["kill_pod", "network_latency_ms:50-2000", "cpu_sat_pct:10-95", "dns_fail"],
    "metrics_streamed": ["error_rate", "p95_latency_ms", "replica_count", "cpu_utilization"],
    "distractor_metrics": ["queue_depth", "cache_hit_rate", "gc_pause_ms", "gossip_delay"]
  },
  "validation": {
    "required_hypothesis_fields": ["binary_prediction", "quantitative_1", "quantitative_2"],
    "grading": {
      "hypothesis_quality": 0.2,
      "experiment_design": 0.2,
      "prediction_accuracy": 0.3,
      "postmortem_quality": 0.3
    },
    "rubric_prompts": [
      "Is the hypothesis falsifiable with the available chaos actions?",
      "Did the learner bound their predictions numerically?",
      "Were predictions within 25% of observed?",
      "Does the postmortem identify at least one surprise and one follow-up?"
    ]
  }
}
```

**Grading rubric**: 4-component weighted. Parts (a) + (b) graded by Haiku against rubric prompts. Parts (c) + (d) graded deterministically: did predicted vs actual numbers agree within a band? Did the postmortem text contain "surprise" or "follow-up" semantic content (Haiku-checked)?

**Sandbox requirements**:
- Ephemeral target system (reuse Proposal 1 cluster infra).
- A chaos controller that can apply a bounded set of fault types. Open-source chaos-mesh or a small homebrewed fault-injector against the ephemeral namespace is plenty.
- Metrics collector (Prometheus-shaped) exposing time series to the UI.

**Budget**: ~$0.03 LLM per session (Haiku for hypothesis/postmortem grading). ~$0.03 compute per session.

**Why-real-life score**: **9/10** — this is the senior-SRE promotion interview format. Extremely under-served by existing platforms.

**Implementation difficulty**: **7/10** — chaos controller + metrics pipeline is real work but chaos-mesh + Prometheus are open-source; the LMS-side is a thin UI over those.

**Recommended ship order**: Quarter-1. Ship after Proposal 1 (shares the ephemeral-cluster infra).

---

### Proposal 6: `github_classroom_capstone` — full PR-workflow capstone with real CI attestation

**Real-world analog**: A developer is given a Linear / Jira ticket. They branch off main, write code, open a PR, CI runs, reviewers comment, they iterate, they merge. **This IS the job** for most software roles. Our current "system_build" is a cosplay of this because the grader hits an unreachable URL.

**Pedagogy**: Gives learners **end-to-end practice with the actual tools** — Git, branches, PRs, CI, reviewer comments. Turns a capstone into an artifact the learner can link on their LinkedIn / portfolio.

CLAUDE.md's F24 (`gha_workflow_check`) is already designed for the CI-run-attestation half. This proposal extends it with (a) reviewer comments generated by Haiku on the PR itself, (b) a pre-merge gate requiring the learner to reply to each comment and push a fix commit, (c) mandatory branch cleanup + squash-merge.

**UI sketch**:
- Step 1 — "Fork the starter repo" — big button that calls `gh repo fork` on the learner's behalf (OAuth'd).
- Step 2 — "Read the ticket" — a Linear-styled card with the story, AC, and "definition of done."
- Step 3 — in-browser editor (WebContainer) or instruction to clone locally. Learner commits + pushes to their fork on a branch.
- Step 4 — "Open the PR" — button opens their PR via `gh pr create`.
- Step 5 — live PR view: CI runs (real GitHub Actions), AI-reviewer (Haiku) leaves 2-3 comments on specific lines within 30s of PR open.
- Step 6 — learner responds to each comment, pushes new commits, PR auto-updates, AI re-reviews.
- Step 7 — once CI green + every AI comment resolved + squash-merged to learner's `main` → grader marks complete.

**Data shape**: extends CLAUDE.md's F24 shape:
```json
{
  "exercise_type": "github_classroom_capstone",
  "demo_data": {
    "starter_repo_template": "skills-lab-demos/velora-rate-limit-capstone",
    "ticket": {"title": "Add token-bucket rate-limiter to /api/login", "description": "...", "acceptance_criteria": [...]},
    "time_budget_min": 120
  },
  "validation": {
    "gha_workflow_check": {
      "workflow_file": "lab-grade.yml",
      "expected_conclusion": "success",
      "grading_job": "grade"
    },
    "ai_review_rubric": {
      "num_comments": 3,
      "must_flag": ["race_condition_in_bucket_refill", "missing_p95_test", "no_feature_flag"],
      "comment_resolution_required": true
    },
    "merge_required": true,
    "grading_formula": "0.5 * ci_pass + 0.3 * ai_review_resolved + 0.2 * merge_clean"
  }
}
```

**Grading rubric**: 3-component weighted: CI green (0.5), AI review resolved (0.3), squash-merge clean (0.2). Each component is verifiable via GitHub API — no learner-source-text guessing.

**Sandbox requirements**:
- GitHub OAuth flow to let us `gh repo fork` / `gh pr comment` / `gh api repos/{}/actions/runs/{}` on the learner's behalf.
- A template-repo library under `skills-lab-demos` on GitHub (one repo per capstone, already a CLAUDE.md F26 primitive).
- A small bot identity (`@sll-reviewer`) that leaves PR comments.

**Budget**: ~$0.05 LLM per session (Haiku for 3-5 PR review comments). Public GitHub Actions = free for open-source; $0.008/min for private. Our cost: near zero.

**Why-real-life score**: **10/10** — this IS the job, not a simulation of it. Portfolio-grade output.

**Implementation difficulty**: **6/10** — GitHub integration is the heavy lift; AI-comment generation is reuse of Creator primitives.

**Recommended ship order**: Month-1 for the basic version (reuse F24 + F26, add AI-review bot). Quarter-1 for the full "PR workflow" with comment-resolution gating.

---

### Proposal 7: `mentored_iteration` — Exercism-style 1–3 improvements-per-round with a learner-controlled cadence

**Real-world analog**: A junior engineer on their first code review. A senior reviewer leaves 3 comments ("naming here, missing error path, could extract function"). Junior pushes a fix. Senior looks again, leaves 2 new comments on the new code. Three iterations and the code lands. Exercism's mentor track is literally this loop.

**Pedagogy**: Closes a gap we don't address: **giving learners the skill to iterate on feedback.** Our current 3-attempt model is closer to "try again" than "consider this feedback, respond to it specifically, push a refined version." This format is explicitly pedagogical about improvement velocity.

Also addresses a Theme A failure mode: with iteration, a "print spam" first attempt gets comments like "there's no actual logic here; can you take another pass with `asyncio.gather` in mind?" — the cheese is immediately detected and the learner is redirected instead of just scored.

**UI sketch**:
- Left: code editor with the learner's submission.
- Right: "Mentor conversation" — Slack-like thread. Mentor (LLM, Haiku) posts 1–3 comments inline on specific lines with arrows pointing at them. Each comment has a "I fixed this" checkbox.
- Bottom: "Re-submit" button is only enabled once every comment is checked. On re-submit, mentor re-reads only the diff and posts 1–3 new comments.
- Completion: after 1–3 rounds, mentor either marks "approved" (score computed from code quality + iteration count) or "needs-more-iterations" (partial score).

**Data shape**:
```json
{
  "exercise_type": "mentored_iteration",
  "demo_data": {
    "task": "Refactor this 200-line resolver to eliminate N+1 queries",
    "starter_code": "...",
    "mentor_persona_prompt": "You are a senior Python engineer at Velora. Leave 1–3 comments per iteration. Never give the full solution."
  },
  "validation": {
    "max_rounds": 3,
    "rubric_tags": ["n_plus_1_fix", "type_safety", "readability", "tests"],
    "grading": {
      "final_code_quality": 0.6,
      "iteration_efficiency": 0.2,
      "comment_engagement": 0.2
    }
  }
}
```

**Grading rubric**: Final code quality scored by Haiku against the 4 rubric tags (structured JSON: yes/no per tag). Iteration efficiency: converged in fewer rounds = higher score. Comment engagement: did learner address the specific comment, or just change random things?

**Sandbox requirements**: Just LLM calls + editor + conversation UI. No new runtime. Reuses `adaptive_roleplay` conversation memory pattern but with code-review semantics.

**Budget**: ~$0.04 LLM per session (3 rounds × Haiku × ~1500-token exchange).

**Why-real-life score**: **8/10** — identical to junior-to-senior code-review dynamics. Loses a point because the mentor isn't a real human with context on your team's history — but 80% of the pedagogy comes through.

**Implementation difficulty**: **4/10** — low; reuses adaptive_roleplay conversation engine, new UI component, Creator prompt for mentor persona.

**Recommended ship order**: Week-1 (lowest effort, highest pedagogical yield for code-heavy courses).

---

### Proposal 8: `pixel_diff_capstone` — Frontend Mentor-style build-this-design with automated visual diff

**Real-world analog**: A frontend engineer at a startup gets a Figma handoff. They implement, PR up a preview URL, the designer loads it, scrubs between design and implementation, and flags deltas. Pixel-perfect? Probably not. Within tolerance on layout / typography / palette / spacing? Yes or no. Frontend Mentor is exactly this workflow.

**Pedagogy**: For **any UI-building capstone** (dashboard builds in our Data / Looker-analog course; admin consoles; mobile apps), grading on visual-output-match instead of source-text-match. Completely cheese-proof: a `print()` hack produces no DOM.

**UI sketch**:
- Left: code editor (HTML/CSS/JS or a framework template: Next.js/Vue/Svelte).
- Right: **preview iframe** rendered from their code + a **reference screenshot** with a slider to A/B between them.
- Submit triggers: (a) headless Playwright renders their page at 3 viewports (mobile/tablet/desktop), (b) compare against reference screenshots via SSIM + per-region percent-diff, (c) extract computed styles of key elements (`button.primary` bg should be `#4a7cff`) and match.

**Data shape**:
```json
{
  "exercise_type": "pixel_diff_capstone",
  "demo_data": {
    "reference_screenshots": {"mobile": "...", "tablet": "...", "desktop": "..."},
    "figma_url": "https://www.figma.com/file/...",
    "style_guide": {"primary": "#4a7cff", "font_family": "Inter", ...},
    "starter_repo": "https://github.com/skills-lab-demos/dashboard-capstone"
  },
  "validation": {
    "pixel_diff_threshold": 0.93,
    "computed_style_assertions": [
      {"selector": "button.primary", "property": "background-color", "expected": "#4a7cff"}
    ],
    "grading": {
      "visual_similarity": 0.5,
      "style_conformance": 0.3,
      "responsive_breakpoints": 0.2
    }
  }
}
```

**Grading rubric**: SSIM-based visual-similarity score × computed-style assertion pass rate × responsive breakpoints (mobile render passed ≥ 0.9 SSIM, tablet ≥ 0.9, desktop ≥ 0.9). Cheese test: empty page = 0 visual similarity.

**Sandbox requirements**: WebContainer runtime (from Proposal 3) + server-side Playwright for the submit-time diff. SSIM library (scikit-image) for diff computation.

**Budget**: $0 LLM. ~$0.01 compute per submit.

**Why-real-life score**: **8/10** — real frontend work is design-to-code, period. This captures it cleanly. Loses points because real work involves design negotiation ("this can't be done in CSS, let's discuss") which we don't simulate.

**Implementation difficulty**: **5/10** — Playwright + SSIM is 2-day eng work. Creator-side: generate design brief + target screenshots. Could leverage AI-generated reference designs (DALL-E / Figma plugins).

**Recommended ship order**: Quarter-1. Opens a whole new category of courses: UX/UI, design-systems, accessibility.

---

### Proposal 9: `local_cli_verifier` — Boot.dev-style "run `sll-lab check` on your own machine"

**Real-world analog**: A developer works locally. They want to check their work passes. They run `npm test` or `go test` or `pytest`. Boot.dev's `bootdev` CLI does this for their cloud-deployed AWS labs — a local tool checks real remote infrastructure.

**Pedagogy**: Enables capstones that **must run on the learner's own machine** (local K8s, local Docker, local Python env with specific tooling, dotfile configs, shell setup). Today's sandbox can't do this at all. Addresses a class of capstones Skills Lab v2 has no path to: "set up a proper dev env," "configure your editor with linters + formatters + type-checkers wired together," "install a local K8s cluster and deploy a canary service."

**UI sketch**:
- Step 1: "Install the checker: `pipx install sll-lab` or `npm i -g sll-lab`."
- Step 2: "Authenticate once: `sll-lab login` (browser OAuth pop)."
- Step 3: Instructions for the capstone ("On your machine, install k3d, create a cluster, deploy this manifest, verify it runs.")
- Step 4: "When you think it's done, run `sll-lab check cap-12345`. The CLI probes your local env, collects assertions, POSTs to our API. Score shows up in your browser."

**Data shape**:
```json
{
  "exercise_type": "local_cli_verifier",
  "demo_data": {
    "capstone_id": "cap-velora-local-k8s",
    "briefing": "On your machine: install k3d, create cluster 'velora', deploy payment-api, verify service responds.",
    "install_commands": ["pipx install sll-lab", "sll-lab login"],
    "check_command": "sll-lab check cap-velora-local-k8s"
  },
  "validation": {
    "assertions": [
      {"check": "k3d_cluster_named", "name": "velora", "weight": 0.2},
      {"check": "deployment_healthy", "ns": "default", "name": "payment-api", "weight": 0.3},
      {"check": "service_responds", "url": "http://payment-api.velora.local/healthz", "expect_status": 200, "weight": 0.3},
      {"check": "manifest_matches_pattern", "path": "./manifests/payment-api.yaml", "jq_match": ".spec.replicas >= 3", "weight": 0.2}
    ]
  }
}
```

**Grading rubric**: CLI runs assertions, POSTs per-assertion pass/fail, server computes weighted score. Cheese-proof: the check runs on the learner's real machine state; empty directories fail all assertions.

**Sandbox requirements**: A published `sll-lab` CLI (Python + TypeScript flavors). A documented HTTP contract (`POST /api/capstone/{id}/submit-cli-report` with assertion results). OAuth for learner identity.

**Budget**: $0 LLM, $0 compute per session (work happens on the learner's machine).

**Why-real-life score**: **10/10** — this IS local dev-env work. Nothing simulated about it.

**Implementation difficulty**: **5/10** — CLI authoring + distribution (PyPI / npm). Main work: defining the assertion library (k3d probes, docker probes, pytest runners, mypy integrations).

**Recommended ship order**: Quarter-1. Enables a whole class of senior/DevEx/platform capstones we can't touch today.

---

### Proposal 10: `system_design_live` — live whiteboard with an AI interviewer probing depth of reasoning

**Real-world analog**: Senior-level interviews (L5/L6 at FAANG, Staff/Principal at startups) include a 45–60 min system-design round. Interviewer puts up "design Uber" / "design a distributed counter" / "design Dropbox's sync engine." Candidate draws boxes, the interviewer asks follow-ups that probe the design's edges ("what if the primary region goes down? what's your consistency model for metadata? how does the client handle conflict resolution?"). HackerRank Virtual Whiteboard and Google's "system design" interview track this.

**Pedagogy**: This is the single most-under-served capstone format in the whole industry of technical learning — no platform outside of paid interview-prep does it well. For our senior-track courses (distributed systems, databases, system design, platform eng) this IS the capstone.

Complementary to our shipped `voice_mock_interview`: voice captures soft skills; `system_design_live` captures deep-technical articulation.

**UI sketch**:
- Main canvas: a fabric.js / excalidraw-lite box-and-arrow whiteboard. Boxes have types (Service, DB, Queue, Cache, Client). Arrows have labels (RPC / Kafka / HTTP).
- Right rail: **AI interviewer chat** — structured chat where the interviewer references specific boxes on the canvas ("your Redis cluster — what's your eviction policy under sustained write pressure?").
- Bottom: **Probe queue** — the AI surfaces a growing list of follow-up probes the learner hasn't addressed yet. Learner drags probes to "answered" or types a reply.
- Submit: the AI generates a 5-dimension rubric score + a written critique.

**Data shape**:
```json
{
  "exercise_type": "system_design_live",
  "demo_data": {
    "prompt": "Design a 100K-writes/sec distributed counter that can survive region failure.",
    "starter_canvas": null,
    "interviewer_persona_prompt": "You are a Staff Engineer at a cloud provider...",
    "probe_bank": [
      "What's your consistency model?",
      "How does client handle a partition?",
      "What's your read/write path separation?",
      "What's your backup + restore story?",
      "How does this scale 10× from here?"
    ]
  },
  "validation": {
    "turn_limit": 20,
    "rubric_tags": ["problem_decomposition", "tradeoff_articulation", "failure_mode_coverage", "data_model_clarity", "scale_awareness"],
    "min_probes_addressed": 8,
    "grading": {
      "depth_per_rubric": 0.6,
      "probe_coverage": 0.2,
      "canvas_cleanliness": 0.2
    }
  }
}
```

**Grading rubric**: Haiku (or Sonnet for premium) scores per-rubric-tag depth from the chat transcript + final canvas snapshot. `probe_coverage` is mechanical. `canvas_cleanliness`: was the canvas labeled, was there a data-flow legend, etc. — Haiku-scored.

**Sandbox requirements**: Whiteboard widget (open-source: excalidraw is trivially embeddable). LLM turn loop (reuse adaptive_roleplay engine).

**Budget**: ~$0.08 LLM per session (20 turns × Haiku ≈ $0.005/turn, with possible Sonnet escalation for final scoring = ~$0.03).

**Why-real-life score**: **9/10** — this is the L5+ promotion interview, near-exactly.

**Implementation difficulty**: **6/10** — whiteboard widget + LLM prompting is real work; reuses existing turn-based engine.

**Recommended ship order**: Quarter-1. Paired with Proposal 5 (chaos drill), this gives us the senior-track pair.

---

### Proposal 11: `property_test_grader` — Hypothesis-style property-based grading

**Real-world analog**: A senior engineer writes tests. Not "test that sort([3,1,2]) == [1,2,3]" (that's the example-based approach our `must_contain` + `expected_output` imitates). Instead: "for any list L, `sort(L)` should be a permutation of L, and should be monotonically non-decreasing." Property testing. Shrinking. Randomized input generators. Hypothesis (Python) / QuickCheck (Haskell/Erlang). There's a 2016 ACM paper showing this works *very well* for grading programming exercises.

**Pedagogy**: Completely replaces the broken `must_contain` substring approach. Cheese-proof by construction: a stub can't satisfy random inputs. Also teaches learners an actual industry skill (property-based testing) that our curriculum doesn't cover today.

**UI sketch**:
- Editor pane with learner's code.
- "Run 200 property checks" button — runs the Creator-specified properties against random inputs.
- Results pane: per-property pass rate + a shrunk failing case for any that failed ("property `sort_is_monotonic` failed on input `[3, nan, 1]`; here's the minimum failing input").

**Data shape**:
```json
{
  "exercise_type": "property_test_grader",
  "demo_data": {
    "task": "Implement merge_sort(arr: list[int]) -> list[int]",
    "interface_contract": "def merge_sort(arr: list[int]) -> list[int]",
    "starter_code": "def merge_sort(arr): pass",
    "example_input_output": [{"in": [3,1,2], "out": [1,2,3]}]
  },
  "validation": {
    "properties": [
      {"id": "is_permutation", "hypothesis": "assert sorted(arr) == sorted(merge_sort(arr))", "weight": 0.3},
      {"id": "is_monotonic", "hypothesis": "r = merge_sort(arr); assert all(r[i] <= r[i+1] for i in range(len(r)-1))", "weight": 0.4},
      {"id": "handles_empty", "hypothesis": "assert merge_sort([]) == []", "weight": 0.1},
      {"id": "stable_on_dups", "hypothesis": "...", "weight": 0.2}
    ],
    "generators": [
      {"name": "arr", "hypothesis": "lists(integers(min_value=-1000, max_value=1000), max_size=500)"}
    ],
    "num_examples_per_property": 200
  }
}
```

**Grading rubric**: Score = Σ (weight × pass_rate) across properties. Each property gets 200 randomized examples. A learner's solution that crashes → fails the property. A stub that always returns `[]` → fails `is_permutation` for any non-empty input.

**Sandbox requirements**: Hypothesis installed in the grader (trivially). An assertion DSL that is safe to `eval` on learner code — we already have primitives for this in the shipped engine.

**Budget**: $0 LLM, ~$0.001 compute per submit (200 hypothesis examples run in < 1s).

**Why-real-life score**: **7/10** — realistic for library/algorithm work; less relevant for UI / ops / glue code. But for the algorithmic chunk of our curriculum, this is ideal.

**Implementation difficulty**: **4/10** — Hypothesis + a property DSL is a weekend hack. Creator prompt changes to emit properties per exercise is the main lift.

**Recommended ship order**: Week-1 (for algorithmic exercises) / Month-1 (extended to async / retry / concurrency properties).

---

## 4. Improvements to existing types (refinements to the 16 we have)

Not new — targeted surgery on the 4 exercise types the SWE most criticized. Each refinement references an SWE review line by step number.

### `code_exercise` — three refinements (addresses Themes A, C, D)

**Refinement 1 — replace the `must_contain × expected_output` grader with a layered signal stack.**

Current behavior (per step 281): `"a pure `print('semaphore = asyncio.Semaphore(')` hack with no real logic → also scored 60%. Empty code → 0%."` Token stuffing and real work are indistinguishable.

New signal stack, in ascending order of what they grade:
- **Signal 1 — syntactic pass** (`compile(source, '<learner>', 'exec')` succeeds): 10%. Catches completely broken submissions.
- **Signal 2 — behavioral pass** (run learner code against a hidden pytest harness): 50%. Replaces `expected_output` entirely. Creator specifies `hidden_tests_path` with 3–10 tests; grader runs them and reports per-test pass.
- **Signal 3 — property pass** (Hypothesis; see Proposal 11): 20%. For functions with clear invariants. Optional.
- **Signal 4 — static analysis** (ruff / mypy / eslint at strict level): 10%. Linter clean = +10%.
- **Signal 5 — human-readable diff from reference** (Haiku-graded): 10%. Is the learner's approach idiomatic?

Substring `must_contain` is dead. It stays in the DB for legacy courses but the grader emits a deprecation warning and the 60% cap is removed.

**Refinement 2 — ship `starter_files` for every `code_exercise` whose scaffold touches the filesystem.**

CLAUDE.md's F26 primitive already exists. The refinement is **tightening `_is_complete()`**: reject any `code_exercise` whose scaffold code contains `open(`, `Path(`, `os.walk`, `glob.glob`, `subprocess.` — unless `demo_data.starter_files` or `demo_data.starter_repo` is present. Directly prevents step 452's `/tmp/flowsync` problem from reproducing.

**Refinement 3 — `sandbox_affordances` block for library stubs + a real-deps lane via WebContainer.**

Two-tier approach:
- **Tier 1 — stubs ship with the course**: extend `demo_data` with a `sandbox_affordances.stubs` map that the sandbox injects before the learner's code. Stub for `bcrypt`: `{ "bcrypt": { "checkpw": "lambda p, h: p.decode() == h.decode()" } }`. Creator produces these when emitting exercises that reference missing libs. Addresses step 280 (bcrypt missing) immediately, before runtime infra lands.
- **Tier 2 — WebContainer runtime**: for JS/TS/Python-via-Pyodide courses, skip stubs entirely (Proposal 3).

`_is_complete()` rejection: if scaffold imports a module from our known-missing list (`bcrypt`, `confluent_kafka`, `kafka`, `psycopg2`, `opentelemetry.*`) and neither tier is provided, generation fails.

---

### `code_review` — three refinements (addresses Themes E, F)

**Refinement 1 — Creator must justify why the N chosen bugs are the top N, with a senior-review pass before publish.**

Current behavior (per step 232): the grader picks lines 1, 10, 21, 22, 30 as "the 5 bugs," but skips `apt-get`-without-cleanup (major size bloat) and the commented-out `USER` (running as root in prod). The Creator doesn't explain WHY these 5 and not others.

New `_is_complete()` check for `code_review`:
- Every bug in `demo_data.bugs[]` must include `{line_number, bug_description, severity, cited_rule}`.
- `cited_rule` must reference a named rule (`CWE-521`, `SOLID-single-responsibility`, `dockerfile-best-practices-apt-cleanup`, `PEP-8-style`).
- A **second Haiku pass** on the final bug list: given the code + the chosen bugs, list all bugs a senior reviewer would plausibly flag. If the Haiku pass finds a P0-severity bug (security / correctness) that the Creator's bug list missed, **generation fails** and regenerates.

Addresses step 232 + step 286 both — the "exercise is named after an anti-pattern that isn't in the graded bug list" failure mode.

**Refinement 2 — enforce `len(demo_data.bugs) == len(validation.bug_lines)`.**

Step 315: "UI 9, grader 8." One-line fix in `_is_complete`: `assert len(step.demo_data.bugs) == len(step.validation.bug_lines)`. If not, regenerate. Takes 5 minutes to implement.

**Refinement 3 — progressive disclosure in feedback: "you got 2 of 5; line 12 was correct, line 1 was wrong."**

Current UI (per review §9): "try again — focus on red items" but never tells the learner which lines were right. This is unnecessarily opaque. The grader already knows. Surface the "you got lines 12 and 21 right, 3 remaining" info on attempt 2 and 3. Learners then focus their re-reading on the unknown lines.

---

### `system_build` — three refinements (addresses Themes B, H)

**Refinement 1 — the grader accepts a learner-submitted URL; `endpoint_check.url` becomes the runtime-resolved value.**

Current behavior: validation has `endpoint_check.url = "http://your-deployed-service/health"` (step 244) or empty string (step 282). No learner URL is accepted.

New:
- Frontend adds a mandatory `deployment_url` text input next to the submit button.
- Backend plumbs the learner-submitted URL into the existing `endpoint_check` machinery.
- Server-side SSRF guard: reject `localhost`, `127.*`, `10.*`, `172.*`, `192.168.*`, `.internal`, `metadata.google.internal`, `169.254.169.254` unless the course explicitly opts into that range.

Six-line backend change (documented in CLAUDE.md F24 commentary) ships the baseline fix.

**Refinement 2 — a `Creator-hosted ephemeral-check endpoint` option the Creator emits at generation time.**

For capstones where the learner builds a service that should be callable from our grader: the Creator includes a `demo_data.check_probe` block that defines:
- URL template (`{learner_url}/api/items/{probe_id}`)
- Expected response shape (JSON schema)
- Per-probe assertions ("`response.status == 200`, `response.json['item_count'] == 47`")

At submit, the grader runs all probes against the learner-submitted URL. If any probe fails, specific feedback ("probe 3: expected `item_count == 47`, got `null`") is shown. Addresses the "2-hour ship it and get 0%" problem directly.

**Refinement 3 — require one of `{gha_workflow_check, endpoint_check+learner_url, cluster_state_check, local_cli_verifier, artifact_flag}` at generation time.**

`_is_complete()` for `system_build`: the validation block must contain at least one of the five verifiable grading primitives. If none are present, the capstone is not shippable. This *structurally* prevents another 5-of-5 capstone failure. The Creator prompt is updated to pick the correct one based on course type:
- Docker / K8s → `gha_workflow_check` or `cluster_state_check`.
- FastAPI / Node service → `endpoint_check + learner_url`.
- Data / ML → `benchmark_arena` or `artifact_flag`.
- Dev-env / CLI → `local_cli_verifier`.

---

### `fill_in_blank` — two refinements (addresses Themes G, J)

**Refinement 1 — mandate an `alternatives` array per blank; reject FIBs without them.**

Step 345 (OTel) is praised as the exemplar: "`http.request.method`, `url.full`, ... The alternatives list (`http.method`, `database.operation`, etc.) is thoughtfully expansive — a learner who uses a slightly older convention still gets credit." Step 375 (Git cherry-pick) fails because `"cherry-pick -X theirs 7f4e8a2"` doesn't match the grader's exact string.

New `_is_complete()` check: every `validation.blanks[]` entry must have `alternatives: [...]` of at least 3 synonyms / equivalent-meaning strings. Creator prompt is tightened: "For every blank, emit 3–10 acceptable answers covering {original name, older alias, semantic equivalent, common typo that's still correct, vendor-specific variant}."

**Refinement 2 — self-describing payload schema returned from `GET /step/{id}`.**

Theme J + step 454 parsons bug: "The grader never matches any key I tried." Learners guess payload shapes and consume attempts on payload-shape wrong-turns. Fix: `GET /step/{id}` returns a `validation_payload_schema` block with the exact key the grader expects + a one-line example. Frontend uses it. Third-party clients use it. No more "3 attempts wasted on `items` vs `answers`." Same treatment for parsons, ordering, categorization, SJT — all four get self-describing schemas returned with the step.

---

## 5. Cross-cutting recommendations

### Ontology — a cleaner taxonomy for Creator generation

Today's 16 exercise types mix three distinct axes. Reorganize them along the axes and the Creator's choice becomes structured:

| Axis | Values | Current types mapped |
|---|---|---|
| **Interaction mode** | static, interactive, dialogic, simulation | static = mcq/fib/ordering; interactive = code_exercise/parsons; dialogic = adaptive_roleplay/voice_mock_interview; simulation = incident_console/simulator_loop |
| **Grade primitive** | text_match, state_check, behavior_test, llm_rubric, hybrid | text_match: mcq/fib/parsons; state_check: cluster_state_check/artifact_flag; behavior_test: property_test_grader/live_dev_workspace; llm_rubric: code_review/roleplay debrief; hybrid: system_build (ci + rubric) |
| **Reality score** | simulated, shadow, real | simulated: all today; shadow: voice_mock_interview; real: github_classroom_capstone (actual PR in actual repo) |

Creator prompt mandate: every generated step declares `{interaction_mode, grade_primitive, reality_score}`. `_is_complete()` validates the triple. This replaces the ad-hoc "pick from 16 types" with a structured generator.

The Creator also needs a **courseware archetype** field to differentiate: `{conceptual_primer, drill, case_study, capstone, certification_prep}`. A capstone's grading contract is different from a drill's; today both are freeform.

### Grading — replace `must_contain` as the default text-only grade primitive

Already covered piecewise above. Concretely, the default grader stack for a `code_exercise` becomes:
1. `compile()` — 10%
2. Behavior test (pytest / jest) — 50%
3. Property test (Hypothesis) — 20%
4. Lint/type-check — 10%
5. LLM rubric (idioms, readability) — 10%

`must_contain` remains available as a **signal 6** (optional, weight ≤ 5%) for cases where a literal phrase MUST be present (e.g., GDPR audit course — "did you cite article 30 specifically?"). Cap it; don't let it drive the score.

### Sandbox — what library / runtime additions close the 40% import-fail rate?

**Short-term (Week-1)**: extend the mock-module list in `_build_mock_modules()`. Add: `bcrypt`, `confluent_kafka` (stub of `Consumer`/`Producer`), `kafka` (stub of `KafkaConsumer`/`KafkaProducer`), `psycopg2` (stub of `connect()` → cursor → execute pattern), `opentelemetry.api`, `opentelemetry.sdk`, `opentelemetry.instrumentation.fastapi`, full `httpx` (Response + MockTransport). Per the review: this alone closes 4 of 11 affected courses.

**Medium-term (Month-1)**: WebContainer runtime for JS/TS + Pyodide for Python (Proposal 3). Retires the mock-module maintenance treadmill entirely for those languages.

**Long-term (Quarter-1)**: ephemeral Docker / k3d clusters for ops + data capstones (Proposal 1). Closes Kafka, Redis, Postgres, OTel → Jaeger, FastAPI → DB → Redis flows all at once.

### Realism — what scenarios / fixture datasets would we need a library of?

Currently the Creator invents everything at generation time. Some fixtures are reused well (Velora / StreamFlow / CartFlow) but each course grows its own data, often thin (step 452: `/tmp/flowsync` doesn't exist at all). Propose a **fixture library** hosted at `skills-lab-demos` on GitHub + `fixtures.sll.ac`:

- **Codebases**: 5 "real-feeling" repos at 5K, 50K, 200K lines — `flowsync` (Python/FastAPI/Redis), `velora-web` (Next.js/Node/Postgres), `cartflow-search` (Python/FAISS/Pinecone), `streamflow-etl` (Python/dbt/Airflow), `oakridge-billing` (Go/gRPC/MySQL). Each intentionally has N planted bugs + M intentional design smells.
- **Datasets**: 10 tabular sets (1K to 1M rows) with realistic PII + bias + dirty-data patterns. Shared across Data + AI + Analytics courses.
- **Logs**: 5 curated log dumps from simulated incidents (matching our 5 SRE incident types).
- **APIs**: 3 running reference APIs learners can integrate against (mock payment provider, mock auth service, mock email sender).
- **Trace corpora**: 2 OTel trace exports with realistic span trees for the observability course.

Library is versioned. A course's `source_material` can reference a fixture-library URL; the grader knows how to verify against it.

### Scale — an `instruqt-style track test` CI invariant

Steal Instruqt's pattern: every capstone in the catalog must ship a reference `solve_script` / `solve.sh`. Our CI pipeline regularly runs:
```
for step in catalog:
  spin_up_ephemeral_env(step)
  run_solve_script(step)
  run_grader(step)
  assert grader_score >= 0.95
```
If any capstone's own solve script scores < 0.95 against its own grader, the capstone is flagged broken and quarantined from learner-facing catalog. This single invariant would have caught every bug in the SWE review (Parsons, capstone URLs, 60% cap, Dockerfile output-match) before any learner saw it.

### Learner API self-description

Every step returned from `GET /step/{id}` includes:
```json
{
  "validation_contract": {
    "submit_endpoint": "/api/exercises/validate",
    "payload_shape": { "answers": "dict<blank_id, string>", "time_spent_s": "int" },
    "example_payload": {"answers": {"b1": "await", "b2": "asyncio.create_task"}},
    "grade_signals": [
      {"id": "tests_passed", "weight": 0.5},
      {"id": "lint_clean", "weight": 0.1}
    ]
  }
}
```
Eliminates the parsons payload-key mystery and any future variant. Third-party clients, review agents, and the frontend read the same schema.

---

## 6. Suggested top-5 to ship first — Week 1 / Month 1 / Quarter 1 buckets

### Week 1 — prompt-only + minor engine work

**W1.1 — Refine `code_exercise` grader** (replace `must_contain + expected_output` with the layered signal stack). Drops the 60% cap. Makes Haiku-style behavior tests the 50% component. Creator prompt changes to emit `hidden_tests` instead of `must_contain` (keep `must_contain` as optional low-weight signal). **This is the review's recommendation #1 and is pre-requisite for every other proposal.**

**W1.2 — `mentored_iteration` (Proposal 7)** for any `code_review` or `code_exercise` step. Reuses `adaptive_roleplay` conversation engine; new UI component. Low effort, huge pedagogy lift (closes Theme A cheese + teaches iteration skills).

**W1.3 — `property_test_grader` (Proposal 11)** for algorithmic exercises. Hypothesis + a property DSL; Creator emits properties. Cheese-proof. Low effort.

**W1.4 — Parsons fix + self-describing payload schema** (§5 learner API self-description). Ship the schema; add the one integration test Instruqt-style (`solve → expect 1.0`). Unblocks 8+ Parsons exercises immediately.

**W1.5 — Refinement bundle**: extend sandbox mock modules (bcrypt + kafka + psycopg2 + opentelemetry); add `_is_complete()` rules for code_review (bug-count equality, cited_rule requirement); add `len(endpoint_check.url) > 10 and not placeholder` check rejecting `"your-deployment.aws.com"`; ship learner-submitted deployment URL input.

After week 1: the product stops shipping cheese-able grades, the 5/5 capstone failures are at least partially solvable, Parsons works, and 40% import-fail rate falls to ~15%.

### Month 1 — new runtime primitives

**M1.1 — `live_dev_workspace` via WebContainers (Proposal 3)** for JS/TS and Async/HTTP Python courses. Replaces the 40% import-fail rate entirely for those languages. Biggest first-impression win.

**M1.2 — `benchmark_arena` (Proposal 2)** for one pilot course (CartFlow retrieval). Proves the public/private eval pattern. Other data courses follow.

**M1.3 — `github_classroom_capstone` (Proposal 6)** baseline version using F24 + F26. Real PR, real CI, real AI-review bot. First capstone that produces portfolio-grade artifacts.

**M1.4 — `artifact_flag_capstone` (Proposal 4)** for security courses. Per-learner seeded secret. Zero-cheese.

**M1.5 — Creator refinements bundle**: Haiku second-pass for code_review bug lists (Refinement 1), FIB alternatives array mandate, `_is_complete()` structural rules for system_build, ontology triple enforcement.

After month 1: zero capstones are ungradable, three new cheese-proof capstone formats are live, WebContainer closes 40% → 5% import-fail rate, and the first pilot benchmark arena is running.

### Quarter 1 — multi-infrastructure capstones

**Q1.1 — `cluster_state_check` (Proposal 1)** — ephemeral k3d + assertion DSL. Unlocks Kubernetes / Docker / Postgres / Kafka real-state capstones. Biggest single infra investment, biggest unlock.

**Q1.2 — `chaos_hypothesis_drill` (Proposal 5)** — builds on Q1.1's ephemeral cluster infra. Adds chaos-mesh + Prometheus + hypothesis-formation UI. Senior-SRE promotion-grade capstone.

**Q1.3 — `system_design_live` (Proposal 10)** — excalidraw + LLM interviewer. Gives senior-track courses their top-end capstone.

**Q1.4 — `local_cli_verifier` (Proposal 9)** — publish `sll-lab` CLI. Unlocks dev-env + local-k8s + tooling-config capstones.

**Q1.5 — `pixel_diff_capstone` (Proposal 8)** — Playwright + SSIM. Opens UX/design/accessibility course surface.

After quarter 1: 11 cheese-proof, real-work-fidelity capstone formats shipped. Every major course category has a grading-sound terminal deliverable. The product can credibly say "a learner who completes this course has actually done the job, not rehearsed it."

---

## #1 PRIORITY — if we can only ship ONE thing next month

**Ship `live_dev_workspace` (Proposal 3, WebContainers) + Week-1's `code_exercise` grader overhaul together.**

Rationale:
- Fixes Theme A (cheese-proof grading) via the layered signal stack + hidden-tests pattern.
- Fixes Theme C (40% import-fail rate) via real `npm install` for JS/TS courses and Pyodide for Python.
- Fixes Theme H (good content, bad infra) — the content stays, the infra under it becomes real.
- Reuses F26 starter-files primitive already in CLAUDE.md.
- Positions the product for Proposal 8 (pixel-diff) and Proposal 6 (github_classroom_capstone) which both build on the same workspace primitive.
- Biggest learner-visible first-impression improvement: "I opened the scaffold, hit run, it worked" replaces "I hit run, it ImportError'd, I abandoned the course."

If there's time for a second shippable: Proposal 7 (`mentored_iteration`) for the non-engineering courses. Cheapest + highest-leverage LLM feature we haven't shipped.

---

## Sources

- [KodeKloud — Master DevOps, Cloud & AI](https://kodekloud.com/)
- [Killercoda Interactive Environments FAQ](https://killercoda.com/faq)
- [Instruqt — Test tracks](https://docs.instruqt.com/tracks/manage/test-a-track) · [Challenge scripts](https://docs.instruqt.com/sandboxes/lifecycle-scripts/add-a-script-to-check-challenge-execution)
- [Kaggle — Competition Documentation](https://www.kaggle.com/docs/competitions) · [The Ladder: Reliable ML leaderboards](http://proceedings.mlr.press/v37/blum15.pdf)
- [StackBlitz — WebContainers](https://webcontainers.io/) · [Introducing WebContainers](https://blog.stackblitz.com/posts/introducing-webcontainers/)
- [TryHackMe — Capture the Flag](https://help.tryhackme.com/en/articles/8473460-capture-the-flag-ctf) · [Hack The Box CTFs](https://www.hackthebox.com/hacker/ctf)
- [Gremlin — GameDays](https://www.gremlin.com/docs/fault-injection-gamedays) · [Scenarios](https://www.gremlin.com/docs/fault-injection-scenarios)
- [Advent of Code — About 2024](https://adventofcode.com/2024/about)
- [CodeGrade — Automatically grading JavaScript](https://www.codegrade.com/blog/automatically-grading-javascript-code-assignments)
- [Gradescope — Grading a Programming Assignment](https://guides.gradescope.com/hc/en-us/articles/22066635961357-Grading-a-Programming-Assignment)
- [GitHub Classroom — Use autograding](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding)
- [Exercism — How to give great feedback](https://exercism.org/docs/mentoring/how-to-give-great-feedback)
- [Frontend Mentor — Challenges](https://www.frontendmentor.io/)
- [HackerRank — CodePair + Virtual Whiteboard](https://www.hackerrank.com/products/interview) · [System Design whiteboards](https://www.hackerrank.com/blog/virtual-whiteboarding-for-system-design-interviews/)
- [Boot.dev — Back-end Developer Path](https://www.boot.dev/tracks/backend)
- [Automatic Grading of Programming Exercises using Property-Based Testing (ACM ITiCSE 2016)](https://dl.acm.org/doi/10.1145/2899415.2899443) · [Hypothesis — Property-based testing for Python](https://hypothesis.works/articles/what-is-property-based-testing/)
- [PagerDuty — Incident Commander Training](https://response.pagerduty.com/training/incident_commander/)

