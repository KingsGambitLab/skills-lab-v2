# Skills Lab v2 — AI LMS Platform

## 🛡️ CRITICAL FIX (2026-04-19 late): Source-Grounded Generation

**The bug**: `_llm_generate_step_content` had NO access to `source_material`. Each step was generated from just the title + description, with the source doc never passed to the per-step LLM call. Result: catastrophic drift on 5/6 doc-grounded courses (MERIDIAN acronym rewritten as medical framework; LB-4721 15mg BID → LUM-301 150mg → LB-047 400mg across modules; Priya Rao → Sarah Chen; David Park → Sarah Chen; 7 real systems in Zephyr DPA replaced with 7 fictional; $420K MTTR paper → "Zenith Corp 340% ROI" fabrication; Oakridge Q3 2025 → "AquaFix Solutions March 2023"). Patient-safety implications for the trial protocol.

**The fix** (backend/main.py):
1. **Thread `source_material` into `_llm_generate_step_content` via `course_context`** — every per-step LLM call now has the full source doc (truncated at 6000 chars).
2. **`_extract_canonical_entities()` regex helper** extracts proper-noun names, dollar amounts, percentages, alphanumeric IDs (CLM-YYYY, LB-4721, ICF-047-v3), phone numbers, emails, URLs, version strings from source. Passed into step prompts as "CANONICAL VOCABULARY — use these exact strings."
3. **Grounding preamble injected when source >= 300 chars**, with 7 explicit rules:
   - Don't invent names (use source names verbatim or omit)
   - Don't invent numbers / thresholds / dollar amounts / dates / phone numbers
   - Don't rename frameworks or acronyms
   - Don't invent parallel scenarios (source is auto-claims → capstone must be auto-claims)
   - Don't replace source's systems/tools
   - When in doubt, quote the source
   - Capstone scenarios must name source's actual personas

**Verification (same Meridian source doc, regenerated post-fix)**:
- **17/17 anchor facts preserved** (100%). All named people (Priya Rao, Karen Liu, Marcus Delgado, Rahul Srinivasan, Amelia Song), all thresholds (0.74, 0.91, 8.5d, 11.2%), all IDs (CLM-YYYY, LTR-4471, LACP-2026), framework (MERIDIAN intact), pitfall (Oakridge + $2.3M) — preserved verbatim.
- Synthetic drill policyholders (John Martinez in CLM-2026-458912, Robert Chen in fraud-detection SJT) correctly appear as scenario-level inventions, which is the right separation.

**Next**: smoke-test the fix on the other 4 DEAL_BREAKER sources (Kelvingrove, Zephyr, Orbital, Lumen) to confirm the fix generalizes. Then upgrade `_is_complete()` to flag generated courses whose content doesn't reference enough canonical_entities (refuse-to-generate rather than accept-drift).

## 🎯 NORTH STAR (2026-04-19 late): Workday Simulator + Case Library

The user's vision (via https://for-emergent.vercel.app/ reference + explicit direction): learners should not march through linear 4-module courses with MCQs. They should drop into a **simulated workday** — multi-pane workspace replicating the exact tools a real professional uses — and work through **numbered cases** (like Emergent's Case 3.1, 4.1, 8.1) that are specific failure-mode / incident / situation drills with short target times (3-20 min) and difficulty tiers (Foundational / Intermediate / Advanced), culminating in ONE "Full Cascade" capstone that synthesizes patterns across layers.

The user's phrasing: **"The more real it is, the more valuable it becomes."**

### Cross-domain patterns (from 5 day-in-life agents: SRE / Data Analyst / SOC / Legal / Staff PM)

**Universal 4-pane workspace shape** every domain has:
1. **Left pane — primary tool**: Grafana (SRE), Looker/Amplitude (Data), Splunk (SOC), MSA-in-Word (Legal), Linear sprint board (PM)
2. **Right pane — inspector/drawer/playbook**: Datadog traces + terminal (SRE), dbt lineage (Data), raw-log JSON (SOC), Notion playbook + prior redlines (Legal), Figma (PM)
3. **Floating Slack** — persistent interruption source with escalating tone ("any update?" → "CFO is asking me now" → "CEO just pinged")
4. **Top bar — timer/queue**: PagerDuty incidents (SRE), meeting countdown (Data), Jira SOC queue (SOC), Ironclad contract queue (Legal), Go/No-Go clock (PM)

**Universal mechanics that kill "quiz feel" and create "job feel"**:
- **Exec Slack interrupts** during deep work. Not scripted prompts at timed offsets — async pings that escalate in tone if ignored.
- **Ambient time pressure**: meeting in 20 min / F deadline / EOQ / launch-week 10am Go/No-Go.
- **99% noise, 1% signal** — filtering IS the skill. SOC: 500 alerts, 12 real. SRE: firehose logs, not gated drips. Legal: 32 pending Ironclad items, 3 deal-breakers.
- **Political framing** — "how you tell the CFO Finance was wrong" matters as much as whether Finance was wrong. Grade the Slack reply, not just the SQL/redline/command.
- **Cross-tool correlation required** — no single pane reveals root cause. SRE: Grafana spike → Datadog trace → kubectl pod. Data: Looker number → Snowflake scratch → dbt PR history.
- **Interruption tax** — deep work crashes every 30-90 min from social pings. Simulator must mirror this.

**Universal grading signals**:
1. Decision quality (did they solve the right problem?)
2. Technical correctness (did the SQL / kubectl / redline actually work?)
3. Communication quality (tone + evidence in the Slack reply, the exec one-pager, the negotiation position)
4. Prioritization (WHAT they chose to ignore is part of the grade, equal weight to what they did)
5. Relationship/trust deltas across stakeholders (did CFO trust increase, did Eng-VP patience hold, did CISO sign off?)

### Case-library course mode (Emergent reference pattern)

Courses using this mode replace the linear "4 modules × 4 steps" skeleton with:
- **A grid of N numbered CASES** (e.g., Case 3.1 "Missing Health Route" / Case 7.1 "Docker Layer Cache Bust" / Case 8.1 "The Full Cascade" CAPSTONE), each with: `number`, `title`, `one-line-symptom`, `discipline_tags[]`, `target_minutes`, `difficulty ∈ {Foundational, Intermediate, Advanced}`, `stack_layers[]`
- **Filter pills** at the top: by discipline, by difficulty, by target time, by failure-mode archetype
- **Difficulty progression markers**: 3-dot pills showing how many difficulty rungs a case climbs
- **One designated CAPSTONE case** at the end — always Advanced, always multi-layer ("The Full Cascade" pattern from Emergent: 4 concurrent symptoms across 4 stack layers, ONE root cause)
- Cases are SHORT (3-20 min each) and TARGETED — not 2-hour modules

### workday_simulator exercise type (to build)

New exercise type that drops learner into the 4-pane workspace described above. The Creator authors per-case:
- `shell_archetype`: one of {ops_infra, data_analytics, security_soc, legal_contract, pm_strategy, design_ux, sales_revops, finance_ledger, people_hr, executive} — picks the pre-baked shell
- `scenario`: initial panes' state (Grafana metric array, Splunk alerts CSV, Looker URL+snapshot, MSA paragraphs, Linear tickets list) + the specific incident/question that started the drill
- `slack_thread`: array of incoming messages with `t_offset_ms` OR `fires_after_action` trigger — mix of useful info, interruptions, exec escalation
- `actions_available`: for each pane, what the learner can DO (click metric panel → drill → related traces; type SPL search; edit Word redline; assign Linear ticket owner; reply in Slack)
- `correlation_path`: the sequence of cross-pane moves that lead to root cause (graded on whether learner found it, not forced order)
- `root_cause` + `correct_actions[]` + `communication_rubric` (tone, evidence-citation, stakeholder-awareness)
- `grading_weights`: decision / technical / comms / prioritization / relationship-deltas

### The scale plan (user asked: "if this works, do top 100 categories")

**10 workspace archetypes × 10 roles each = 100 categories.** Build 10 shells once; Creator authors 10+ case packs per archetype on top. Total: 10 shell builds + ~100 case-library courses (5-8 cases each + 1 capstone = ~800 cases authored).

| Archetype | Shell panes | Example roles (10) |
|---|---|---|
| ops_infra | Grafana, Terminal, Slack, PagerDuty | SRE, DevOps, Platform Eng, DBA, NetOps, Cloud Eng, MLOps, Support Eng, Incident Commander, Hardware Eng |
| data_analytics | Looker/Amplitude, SQL editor, Notebook, Slack | Data Analyst, BI Eng, Data Scientist, ML Eng, Analytics Eng, DS Manager, Experiment PM, Growth Analyst, Financial Analyst, Research Scientist |
| security_soc | SIEM (Splunk), Log drawer, Timeline, Slack | SOC Analyst, Threat Hunter, AppSec, Cloud Sec, IR Lead, Detection Eng, SecEng, GRC, Red Team, Pentest |
| legal_contract | Redline doc, Playbook wiki, Prior-deals, Slack | Commercial Counsel, Privacy Counsel, Employment Counsel, IP Counsel, Litigation, Compliance, Contracts Mgr, Paralegal, Regulatory, Ethics |
| pm_strategy | Linear sprint, Figma, Analytics, Slack | Product Mgr, Staff PM, Group PM, CPO, Growth PM, Ops PM, TPM, PMM, BizOps, Chief of Staff |
| design_ux | Figma canvas, Wireframe gallery, Research transcripts, Slack | UX Designer, UX Researcher, Design Systems, Brand, Content Design, DesignOps, Service Design, IA, Design Lead, UX Writer |
| sales_revops | CRM (Salesforce), Gong calls, Pipeline board, Slack | AE, SE, SDR, CSM, Sales Ops, RevOps, Enterprise Sales, Channel, Sales Eng, Sales Leader |
| finance_ledger | General ledger, FP&A model, Bank feed, Slack | Controller, FP&A, Accountant, Tax, Audit, Treasury, Procurement, IR, CFO Staff, Risk |
| people_hr | ATS, Survey dashboard, Calendar, Slack | HRBP, Recruiter, Talent, Comp, L&D, People Analytics, DEI, EX, HR Ops, CPO |
| executive | KPI dashboard, Board deck, Exec 1:1 calendar, Slack | CEO, COO, GM, CRO, CTO, CMO, VP Eng, Founder, Consultant, Board Member |

**Rollout sequencing** (POC → scale):
1. Ship ONE archetype shell (pick ops_infra — specs are sharpest from SRE agent) + case_library UI + regenerate SRE Emergent course in new format. Budget cost: Creator regen ~$0.50.
2. Have user validate the POC. If good → greenlight scale.
3. Ship remaining 9 shells (engineering: 2-3 weeks of frontend per shell; can overlap).
4. Batch-generate 100 case-library courses via Creator (10 per archetype × 10 archetypes). Cost: 100 × ~$0.35 = ~$35.



## 🔒 HARD INVARIANT #2: Bulk Live-Preview QC — 103/103 Passing (2026-04-19)

After a REJECT verdict from the Emergent-course live QC agent (3 P0s), I shipped the following root fixes (none touch course data — all at Creator/engine/frontend level):

1. **Full answer-key sanitizer** (`_sanitize_step_for_learner` in `backend/main.py`) strips: `validation.*` answer keys, `demo_data.*` top-level answer keys, `items[].correct_position/category/rank`, `options[].correct/explanation`, scenario_branch `steps[].options[].correct/explanation`, `bugs[]` replaced with opaque count markers. Verified: 103/103 courses have ZERO leaked answer fields in JS state.
2. **`/api/exercises/validate` enriched response**: now returns `item_results[]` (per-item correctness with user_category/user_position/user_rank vs correct_*), `correct_answer` (canonical), `explanations[]`. Frontend renders post-submission feedback from this response — no pre-loaded answer fields needed at render time.
3. **Deep-link router**: `parseHash` now accepts bare `#<courseId>` (was requiring `#<courseId>/<moduleId>`). `restoreFromHash` fetches unknown courses directly when not in the cached catalog.
4. **Categorization frontend**: preserves real item IDs (was overwriting with array index, breaking server-side grading); renders per-item teaching feedback with "You put in X, correct is Y" + optional explanation.
5. **Ordering frontend**: uses new `item_results` from server to show per-item position feedback + full "CORRECT ORDER" block when learner gets any wrong.
6. **Learner-side expertise picker REMOVED**: complexity is Creator-chosen via `course.level` (accepted on `/api/creator/start` as optional `level` field, or LLM-inferred + normalized to Beginner/Intermediate/Advanced). Badge is read-only, shown in sidebar header. Stale "Builder mode" label gone.

**Bulk live-preview QC results (2026-04-19):** drove an actual browser (Claude Preview) across all 103 courses, loading each, checking JS-state for answer-key leaks, verifying content renders, catching exceptions. Pass rate: **103/103**. Zero faults. Exercise-type coverage: categorization, ordering, sjt, mcq, code_review, scenario_branch, adaptive_roleplay, voice_mock_interview, incident_console, system_build, fill_in_blank, concept. Validated interactively: ordering (3/5 wrong → correct teaching feedback with ✓/✗ per item + full CORRECT ORDER block), categorization (0/8 wrong → per-item teaching "You put in X, correct is Y"). Regenerated Emergent v2 via Creator flow (invariant-compliant): level="Intermediate" persisted, 0 leaks across all 4 modules, $0.31 cost.

Rule going forward: **any fix required by QC goes at the Creator / engine / frontend level, never by editing course data directly.** Courses that fail re-QC after a root-level fix must be regenerated through `/api/creator/*` — same title/description — to prove the fix propagates.

## 🔒 HARD INVARIANT: All Course Creation & Edits Go Through the Creator Dashboard

**This is the most important operational rule. It overrides any convenience.**

All new courses, all course edits, all content regeneration MUST flow through the public Creator API:
- `POST /api/creator/upload` (optional — file seed)
- `POST /api/creator/start` (title + description + course_type)
- `POST /api/creator/refine` (answers to clarifying questions)
- `POST /api/creator/generate` (persists the course)

**Forbidden:**
- Writing Python seed scripts that `import Course/Module/Step from backend.database` and insert rows directly (e.g. `seed_roleplay_course.py`, `seed_incident_course.py` — these are historical exceptions that predate this rule and must be regenerated via Creator when revisited).
- Hand-patching `backend/courses/*.py` files to "fix" a live course. If a course is broken, the fix goes into the Creator workflow (prompt, post-processing, fallback, quality floor) and the course is REGENERATED from its original title/description.
- SQL `UPDATE` statements or direct DB manipulation to adjust course content. Even typo fixes go through Creator regeneration.
- Any script that constructs `Course()` / `Module()` / `Step()` SQLAlchemy objects and commits them.

**The only exception**: pure data-shape migrations (schema changes in `database.py` that add/rename columns) — but these must NEVER change course CONTENT, only the container around it.

**Why this rule matters:** The Creator is the product. Every direct-write workaround hides a Creator bug. When the Creator is forced to produce every course end-to-end, its limitations surface immediately and become fixable. Every seed-script workaround was a missed opportunity to improve the Creator. This is how the LMS evolves itself.

**Enforcement checklist for every new course idea:**
1. Can I express this as a title + description + answers to 3-4 clarifying questions? (Yes → use Creator.)
2. Does the Creator produce the right exercise types for this course? If not → fix the Creator's taxonomy/prompt, not this one course.
3. Does the generated content meet the quality floor? If not → strengthen `_is_complete()` checks, not this one course.
4. Does the result adopt new pedagogies (adaptive_roleplay/incident_console/simulator_loop) where appropriate? If not → improve the Creator system prompt to teach those types.

Any time a reviewer is tempted to write `UPDATE courses SET ...`, that's a signal: **the Creator has a bug, fix the Creator, regenerate the course.**

## Final Goal

Build an **AI-first Learning Management System** for both learners and course creators.

**The outcome bar**: Once a learner completes a course, they should be competent enough to take a real-life scenario at their workplace, build a system that integrates with others, and use the skill to deliver results for their company. The outcome must be real, not toy. Example: after a Vector DB course, the learner should be able to identify opportunities in their org where vector search creates advantage, pitch the solution to leadership, and build + deploy the system end-to-end in production. Some things can be learned on the way, but this production-readiness must be the intent driving all content and assignments.

### For Creators
- Creators provide curriculum files, assignment guides, or even a single paragraph of context.
- The LMS processes the input, asks follow-up questions and clarifications iteratively until it deeply understands the course requirements.
- The process keeps creators involved — they see how the LMS is building the course, can share inputs/comments at each stage.
- **Optimize for**: reducing revision cycles to publish, creator confidence in output quality.

### For Learners
- Implement Clicky-style AI assistant behavior (see `../ai-skills-lab` for reference):
  - For **concept questions**: thorough, uses analogies, explains the WHY deeply.
  - For **exercise questions**: NEVER gives complete solutions. Instead: explain approach, give one-line hints, ask guiding questions, point to relevant prior concepts.
  - Errors are teaching moments — diagnose root cause first, then suggest fix.
- Learners pick their expertise level and the course tailors accordingly:
  - **Beginner**: hand-holding, step-by-step, visual explanations
  - **Intermediate**: less scaffolding, more code, real patterns
  - **Advanced**: building on terminal/VSCode, deploying to cloud/Vercel, production-scale projects

## Course Design Principles

### Introduction (>90% engagement target)
- Must be **highly interactive and engaging hands-on content** that makes the learner understand WHY the skill matters.
- No verbose walls of text. Be creative — try multiple approaches.
- Use real scenarios, live demos, interactive visualizations, "try it now" moments.
- Hook with a compelling problem before explaining the solution.

### Content Structure
- **No rote learning.** Objective questions (MCQ) are lowest priority.
- Think of smart, creative ways to teach each topic:
  - Scenario branching with real-world consequences
  - Code exercises with progressive difficulty (not toy examples)
  - Drag-and-drop assembly (Parsons problems — max 8 lines)
  - Categorization with domain-realistic items
  - Situational Judgment Tests for soft-skill topics
  - Code review with planted bugs at realistic locations
- 3-layer module structure: **Concept** (contextual narrative) → **Exercise** (application) → **Reflection** (insight/takeaway)

### Difficulty & Depth
- Use `../ai-skills-lab` as a quality baseline — those courses are a starting point but **lack depth, creativeness, and difficulty progression**.
- Production-grade exercises: e.g., Vector DB with 100,000 documents and high retrieval accuracy, not 5-item toy demos.
- Progressive complexity: solo task → automated tooling → full production pipeline → deploy to cloud → integrate with real services.
- Final modules should have learners deploying real systems on AWS/GCP/Azure/Vercel — not just writing code in a browser sandbox.
- Teach the surrounding skills too: how to identify where this technology fits in your org, how to pitch it, how to handle production concerns (scale, monitoring, cost, security).

## Exercise Type Taxonomy (12 types — voice_mock_interview added 2026-04-19)

| Type | Use For | Data Shape |
|------|---------|------------|
| `concept` | Teaching content (HTML) | `content` only |
| `code` | Read & run demos | `code` + `expected_output` |
| `code_exercise` | Hands-on coding with TODOs | `code` + `expected_output` + `validation.hint` |
| `fill_in_blank` | API/syntax recall | `code` with `____` + `validation.blanks[]` |
| `parsons` | Code assembly (max 8 lines) | `demo_data.lines[]` + `demo_data.distractors[]` |
| `ordering` | Process/sequence understanding | `demo_data.items[]` + `validation.correct_order[]` |
| `categorization` | Classification exercises | `demo_data.categories[]` + `demo_data.items[]` + `validation.correct_mapping{}` |
| `scenario_branch` | Decision-making with consequences | `demo_data.scenario` + `demo_data.steps[].options[]` |
| `sjt` | Judgment/soft-skill ranking | `demo_data.options[]` + `validation.correct_rankings[]` |
| `code_review` | Bug finding in realistic code | `demo_data.code` + `demo_data.bugs[]` + `validation.bug_lines[]` |
| `mcq` | Quick knowledge checks (use sparingly) | `demo_data.options[]` + `validation.correct_answer` |
| `system_build` | Build & deploy a real system to AWS/GCP/Azure/Vercel | `code` + `deployment_config` + `validation.endpoint_check` |
| `adaptive_roleplay` | TEXT-based counterparty with hidden state (email/Slack/spec-review contexts) | `demo_data.scenario_prompt` + `demo_data.counterparty{persona_system_prompt, hidden_state{}, state_update_rules, escalation_triggers[], win_conditions[]}` |
| `voice_mock_interview` | LIVE VOICE interviews / pitches / coaching — learner speaks via mic, interviewer replies via TTS | same as adaptive_roleplay PLUS `voice_mode=true` + `interview_style` + `opening_question` |
| `incident_console` | Scripted production-outage simulator (zero LLM cost/session) | `demo_data.alert` + `commands[]` + `log_stream[]` + `slack_prompts[]` + `cascade_rules[]` + `accepted_remediations[]` |
| `simulator_loop` | Generic tick-based simulation (umbrella primitive) | `demo_data.initial_state` + `events[]` + `actions[]` + `win_conditions[]` |

### `system_build` — Build & Deploy Exercises
The highest-difficulty exercise type. Learners build a real system and deploy it to a hyperscaler (AWS, GCP, Azure) or platform (Vercel, Railway, Fly.io). This is the capstone format for production-readiness:
- Learner writes real code (not sandboxed — runs on their machine/cloud)
- Includes infrastructure config (Dockerfile, terraform, CDK, serverless.yml, etc.)
- Validation checks a live endpoint or deployment artifact
- Progressive: local build → containerize → deploy → integrate with other services → load test
- Example: "Deploy a FastAPI semantic search service backed by Pinecone to AWS Lambda, handle 100 req/s, return p95 < 200ms"

## Validation & Scoring
- Multi-dimensional scoring with partial credit (LCS for Parsons, off-by-one tolerance for SJT)
- Per-item feedback breakdown, not just pass/fail
- Code exercises: sandboxed execution with mock modules (anthropic, weaviate, langchain, pinecone)
- Blocked modules in sandbox: os, sys, subprocess, shutil, pathlib, socket, ctypes

## Key Metrics to Optimize

1. **Course Quality & Creator Experience** — Depth, creativity, production-readiness. Reduce revision cycles. Keep creators in the loop, take their inputs.
2. **Learner Completion & Real-World Skill Transfer** — Learners with intent complete the course and can apply skills to real problem statements at their workplace. The full chain: understand the need → identify opportunities in their org → pitch to leadership → build end-to-end → deploy to production → integrate with existing systems → deliver measurable results. This is the north star — not "I learned the API" but "I shipped a system that my company uses."
3. **Introduction Engagement (>90%)** — The intro of every course must hook learners. Highly interactive, no verbose content, creative approaches.
4. **Production Readiness** — Every course must end with the learner having built something deployable. Not a notebook, not a script — a system with an API, infra config, monitoring, and the ability to handle real-world scale and edge cases.

## 🎨 Teaching Philosophy — Be Creative, Ship Real Experiences

Be creative and novel about how you teach. Do not default to "read a paragraph, then answer a multiple-choice." Examples of what GOOD teaching looks like:

- **SRE course**: Drop the learner into a live-feeling production environment where metrics spike, services go down, and they must debug and fix. Simulated but reactive — the learner's inputs change what happens next. Postmortem exercise at the end.
- **Incident-response**: A paged-at-3am scenario with live logs scrolling in the UI, partial information, and time pressure. Learner decides what to page next, what to roll back, how to communicate to stakeholders.
- **Legal/compliance**: Simulated clients sending emails with hidden legal issues. Learner replies. AI evaluates whether they spotted the issue.
- **Negotiation**: AI-driven counter-party that adapts its offers based on the learner's moves. Outcome depends on the learner's skill.
- **Data-analysis**: A dirty real-looking dataset with planted biases. Learner runs hypotheses; the UI reveals what they missed.
- **Design review**: A wireframe gallery where bad designs are interspersed with good. Learner annotates with explanations; AI scores the critiques.
- **Architecture review**: An intentionally-flawed system diagram. Learner marks problems; scoring is on rationale, not just flags.

Exercise types are a palette, not a constraint. If inventing a new exercise type serves the pedagogy, invent it. The bar is: **would a learner finishing this course feel they did the real work, or just watched a video?**

## 🔁 Post-Upgrade Review Protocol — MANDATORY

After ANY major platform upgrade (new feature, schema change, Creator behavior change, sandbox change, significant Frontend refactor), you MUST run the full review cycle:

1. **Code review loop — ≥10 iterations.** Spawn parallel agents to audit the diff for: security, correctness, schema drift, frontend/backend contract alignment, error handling, edge cases. Fix every P0/P1 before proceeding.
2. **Domain-expert review loop — ≥10 iterations.** Spawn parallel agents with DIFFERENT personas (SRE, ML engineer, PM, UX researcher, designer, lawyer, compliance officer, etc.) to review course content for their domain. Each reviews the same platform from their lens. Publish good + shortcomings.
3. **Product UX/UI review loop.** Spawn agents that behave like real learners — end-to-end browser journey with screenshots. Grade on: first-impression polish, intro engagement, friction points, mobile behavior, accessibility.

Reviews continue until **≥3 independent reviewers ACCEPT** in the same loop without new P0s. No "we're close enough" — re-run until clean.

### Review-Agent Behavior Rules — MANDATORY

Every review agent MUST:

1. **Open the course via the actual web UI** (http://localhost:8001), not just curl the API. The UI is the product. Static API data can be "correct" while the rendered widget is broken.
2. **Solve every exercise as a real learner would** — click options, drag items, fill in blanks, submit answers, read the feedback. Do NOT shortcut by inspecting `validation.correct_answer` in the JSON and confirming it works.
3. **Attempt WRONG answers too.** Submit a plausible-but-incorrect answer and verify the error feedback is actually useful for learning (points at what's wrong, hints at the concept, doesn't give the answer away).
4. **Screenshot every step.** Dark-theme violations (white-on-white widgets), overlapping UI, broken layout are invisible without pixels. Any interactive widget with `<style>` inside the concept content MUST be visually verified.
5. **Grade on "does this TEACH?"** not "does this render?". Criteria:
   - Does the exercise require THINKING or is it pattern-matching (MCQ with obvious answer)?
   - Does getting it WRONG teach you something?
   - Does getting it RIGHT feel earned?
   - Would a real learner retain the concept a week later?
6. **No spoon-feeding.** If Clicky gives answers, if task descriptions contain the answer, if wrong-answer feedback reveals the correct one — that's a failure. Learners should feel a bit stuck and then unstuck through their own effort.
7. **Test on both Builder and Explorer expertise levels.** The adaptive rendering is supposed to differ — verify it does.
8. **Check for accessibility basics.** Keyboard navigation of drag-drop exercises, focus states, sufficient color contrast, screen-reader labels on interactive widgets.

Reviewer verdict templates must include: screenshots, specific wrong-answer attempt + feedback received, assessment of whether the exercise teaches vs tests.

### Creative-Review Agents (≥3 per upgrade cycle) — MANDATORY

Separate from the correctness/domain/UX reviewers, spawn **≥3 independent creative reviewers** whose ONLY job is to imagine better pedagogy. They must not rubber-stamp what exists; they must propose novel formats that deliver real-world experience.

Their brief:
> "The current course teaches [X] via [existing exercise format]. Propose 2-3 alternative ways the same skill could be learned that mirror how it's actually practiced in the real world. Prefer: drop the learner INTO a failing/evolving system where they must diagnose and act, rather than read-and-answer. The test of success: a learner who completes this feels they 'lived' the skill, not 'studied' it."

Examples of target pedagogy:
- **SRE course**: drop learner into a live-looking production console with alerts firing, logs scrolling, tickets piling up. They must triage, run commands (simulated), make incident-commander decisions. Grade on response time, accuracy of hypothesis, communication clarity.
- **Security incident response**: a phishing email arrives in their inbox view, then another, then a Slack panic from a colleague. They must choose: report? investigate? quarantine? notify legal? The scenario evolves based on their moves.
- **Product management**: a Slack channel with 5 stakeholders all messaging contradictory requirements + a roadmap meeting in 30 min. Learner must synthesize, prioritize, communicate.
- **Sales**: an AI-powered customer who answers questions, raises objections, and will/won't close based on the quality of learner's pitch.
- **Legal/compliance**: a client sends an ambiguous email. Learner must identify the hidden legal risk, draft a reply, escalate if needed. AI grades on whether the risk was spotted.
- **Data analysis**: a realistic dirty dataset with planted biases. Learner runs queries; the UI reveals what they missed (Simpson's paradox, selection bias, data leakage).
- **Architecture / system design**: a live whiteboard where the learner draws, and the AI interviewer probes ("what if traffic 10×?", "what if the primary region goes down?"), with scoring on depth of reasoning.

**The primary pedagogy direction**: stop asking "which of these 4 options is best?" Start putting them in the situation where they must choose, act, see consequences, and iterate.

Creative-review agents publish: 2-3 reimagined exercise formats per course, with a concrete UI sketch of how the widget would work. The Creator team then picks the best and implements it as a new `exercise_type` or a parameterized variant.

Creative reviews have equal veto power with correctness reviews — a pedagogically boring course that technically works is still a fail.

### Learnings from past review cycles (keep growing this list)

- **White-on-white widget bug (2026-04-18):** Creator-generated intro `<script>` widgets sometimes used `background: #fff; color: #fff`-adjacent CSS despite the prompt specifying dark-theme colors. Fix: Creator prompt now enforces mandatory inline CSS variables; reviewers must screenshot every widget.

## 🌑 RECURRING BUG: Dark-theme violations in Creator content — MANDATORY post-gen sanitizer

**The bug keeps coming back.** The Creator LLM ignores the "NEVER use `#fff`, `white`, `#f*`, `#e*`" rule in the prompt roughly 10-20% of the time, emitting light-pastel backgrounds (`#f8f9fa`, `#e3f2fd`, `#f3e5f5`, `#e8f5e8`, `#fafafa`, etc.) in concept-step `<div>` widgets. Since our site background is near-black, the text in those widgets renders as dark-gray-on-light-gray — near-invisible. User screenshots have filed this bug 3× now (2026-04-18 white-on-white; 2026-04-19 pastel widgets; 2026-04-20 ReAct Loop Visualization pastels).

**Non-negotiable mitigation — present in `backend/main.py`:**
1. `_darkify_html_content(html)` is called on EVERY step's `content` field before DB persist, in BOTH the `_is_complete=True` path and the fallback path. It rewrites:
   - `background: #f* / #e* / white / lightgray` → `--bg-tertiary` (#1c2333)
   - `color: white / #fff*` → `--text-primary` (#e8ecf4)
   - Any `style="background: …"` missing an explicit `color:` gets `color: #e8ecf4` injected.
2. The Creator prompt retains its "mandatory dark palette" rules as the first line of defense, but the sanitizer is the last-line guarantee.

**If you see this bug again on a NEW course:** The sanitizer is bypassed. Check:
- Is the content being persisted via a non-standard path (e.g., a legacy seed script)?
- Did someone edit `_darkify_html_content` and break a regex?
- Is the light-bg pattern a shape the regex doesn't catch (`rgb(248, 249, 250)` instead of hex)? — extend the regex.

**Rule going forward:** every new persist path for step content MUST call `_darkify_html_content`. Grep for `Step(` before shipping to verify.

## 🔀 RECURRING BUG: Flow / process widgets rendered as TEXT LOGS instead of SVG graphs (2026-04-20)

User screenshot filed 2026-04-20: a concept-step "Simulate the Nexus document processing flow" widget rendered as a plain text log — `Turn 1 (assistant): Calls OCR tool\ntool_use: ocr_processor\nTurn 2 (user): Returns OCR results\n...` — on a dark card with a Next Turn button. Technically dark-theme compliant, but aesthetically terrible and pedagogically weak: text growing downward teaches nothing visual about the flow shape (which nodes connect, what the loop is, where state transitions happen).

**Mitigation shipped:** Creator prompt (`_llm_generate_step_content` at `backend/main.py:~3576` and the non-intro `concept` branch below it) now includes a MANDATORY VISUAL-FIRST RULE — for any widget depicting a multi-step flow / pipeline / state machine / agent turn loop / request journey, the Creator MUST emit an SVG `<rect>`-node + `<path>`-arrow graph with CSS-animated fill transitions on the current step. Text logs like `Turn N (role): action` are explicitly BANNED and called out by name. A canonical SVG skeleton (700x180 viewBox, rounded rects, marker-arrowheads, `#2a3352` inactive / `#4a7cff` active / `#2dd4bf` done) is embedded in the prompt so the LLM has a concrete template to adapt.

**Rule going forward:** any "demo / simulate / trace / walk through" widget MUST be a graph, not a log. If a reviewer finds a new text-log flow widget in a Creator-generated course, the fix goes into the prompt (strengthen the ban or add more anti-patterns); regenerate the course; never hand-edit the step HTML.

## 📚 Maya beginner-learner review (2026-04-20) — batch of Creator-prompt tightenings

Maya (beginner-programmer learner agent) walked Agent Harness end-to-end and flagged 5 issues, all fixed at the Creator-prompt layer in `_llm_generate_step_content`:

1. **Ordering steps dump undefined jargon.** Step M2.S0 "The ReAct Loop, Step by Step" shows 7 items with `stop_reason` / `tool_use` / `tool_result` and no definition. Fix: ordering prompt now mandates an 80-150-word PREAMBLE that defines any jargon before the item list, frames what "correct order" represents, gives a daily-life analogy. Same fix pattern applies to categorization + parsons (extend when next round surfaces them).
2. **Code_review dumps code with zero briefing.** M1.S3 "Anatomy of a Minimal Harness" = 69 lines of SDK code, only instruction "Click on lines you think contain bugs." Fix: code_review engineering prompt now requires a 2-paragraph BRIEFING (what the code is trying to do) + a numbered/bulleted list of 4-6 BUG CATEGORIES to hunt for (security / resilience / API contract / state / logging / concurrency). The briefing is non-optional.
3. **Fill_in_blank with domain-specific enum answers leaves beginners guessing.** M3.S0 "Designing a Tool Schema" has 4 blanks expecting VectorFlow-internal JIRA statuses ("In Progress / Code Review / Done") with zero context — Maya guessed "in_progress / resolved / closed". Fix: fill_in_blank engineering prompt now mandates a visible LEGEND/SIDEBAR card listing all valid enum values with one-line meanings, PLUS a tiny worked example above the blanks showing one field filled correctly.
4. **Code_exercise content rendered as wall-of-text.** M3.S1 "Register Three Tools" renders edge-to-edge prose, duplicate title, `[ ]` text rendered as raw markdown source, `read_file` / `post_slack` inlined as prose not code. Fix: code_exercise content prompt now requires styled CARDS per section (background div + border + padding + margin), inline code wrapped in styled `<code>`, `<ul>` for checklists (never raw `[ ]`), and NO duplicate step title inside content.
5. **Engineering capstone drifted to UX research content.** M5.S2 "Build &amp; Ship the Triage Harness" body opened "Lead a comprehensive UX research initiative to validate the design assumptions for VectorFlow's agent monitoring dashboard" — the wrong job entirely. Fix: system_build engineering prompt now has a BANNED OPENING PHRASES list ("Lead a user research study", "Design a UX research plan", "Conduct N user interviews", "Synthesize findings into insights", "Present recommendations to leadership", "Design the onboarding experience", "Author a product strategy memo", "Run a design sprint") — if the capstone opens with any of those, the LLM is instructed to STOP and rewrite so the body asks for code that runs. Example correct openings included in-prompt.

**Verification pass:** regenerate Agent Harness via `/api/creator/start → /refine → /generate` with the same title+description, walk steps 918/1, 918/2, 919/0, 920/0, 920/1, 922/2 as a beginner. Every one of the 5 issues must be gone on the fresh course.

- **Overlay persistence bug:** Expertise modal's `backdrop-filter: blur` lingered after selection because `display: none` was delayed 280ms. Fix: immediate display:none.
- **Route state race:** `state.currentCourse` could show a stale course after rapid-clicking the catalog. Fix: `_currentEnterCourseRequestId` guard token.
- **Validation schema drift:** Backend validators read `validation.*` but Creator sometimes put data in `demo_data.*`. Fix: merge both in the validate endpoint + derivation logic in each validator.
- **Empty capstone bug:** LLM occasionally returned a capstone with phases=default-fallback-labels; completeness check now rejects generic "Plan the Deliverable" labels.
- **Code-type mismatch:** Creator generated `code_exercise` / `parsons` for non-engineering courses. Fix: `_enforce_exercise_type_fit()` remaps. `fill_in_blank` preserved because it's valid for text-templates.
- **Capstone template leak (2026-04-18):** When LLM returned insufficient `system_build` content, the fallback block wrote generic phrases like "The core idea behind {TITLE}", "Reflection prompt: spend 60 seconds...", "Define success criteria for {TITLE}" — with the step title substituted in. Reviewers saw this as template placeholder output. Fix: `_is_complete()` now rejects any content containing template-leakage phrases; all phases/checklist items must avoid generic fallback labels (switched `any()` to `all()` check); strict GENERIC_CONTENT_PHRASES blocklist forces regeneration before using fallback.
- **Course-switching state bleed (2026-04-18):** `onCourseClick('B')` while already inside course A left sidebar modules from A visible. `goToStep(N)` then navigated into A's module IDs even though main pane showed B's steps. Fix: `onCourseClick` now tears down `currentCourse`, `currentModule`, `modules`, `currentModuleData` before loading the new course; sidebar module list cleared immediately.
- **Empty code-exercise bodies (2026-04-18):** LLM sometimes returned code_exercise steps with `# Your answer here` as the entire code field. Stats course was the worst offender — 4 of these stubs. Need Creator lint to reject code_exercise steps whose code is just placeholder comments without any scaffold/imports/structure.
- **Sandbox module gaps:** `kubernetes`, `scipy.stats`, `statsmodels`, `numpy`, `pandas` were not mocked → K8s and Stats course code_exercises failed on import. Added stubs to `_build_mock_modules()`. Whenever a new course topic uses a library not yet stubbed, add it before publishing.
- **Source-PDF fidelity:** LLM paraphrases source docs into filler rather than quoting actual handbook text. IT-services domain reviewer flagged courses as "AI-filler with sprinkled keywords". Creator should preserve verbatim chunks of source text (module names, week numbers, handbook headers) where it improves faithfulness. Consider a "faithfulness score" against source chunks.
- **Duration compression misleading:** 23-week Mysore collapsed into 4 modules × 2 hrs is a 200× compression. Title says "Complete TCS ILP" — overpromise. Either generate proportionally more modules OR frame as "highlights" in subtitle.
- **incident_console cascade-rules never fired (2026-04-19):** SRE review agent discovered the engine's cascade check used `trigger in cmd` (substring match) but Creator-generated triggers use regex syntax (`kubectl delete pod.*payment-api`). The `.*` never matched literally. Destructive commands had zero penalty, `blast_radius` stuck at 1.0 regardless of learner actions. Fix: `re.search(trigger, cmd)` with substring fallback. Without this fix, the capstone can't grade the behavior it claims to grade in the rubric.
- **incident_console initial_logs leak (2026-04-19):** The gating filter was `if not log.get("gated_by")` — a field Creator-generated courses don't populate (they gate via reverse mapping `commands[].unlocks[]`). Result: all 9 logs leaked on session start, pre-revealing the smoking-gun lines. Fix: compute the set of gated log IDs from `commands[*].unlocks[*]` and exclude those from initial_logs too.
- **incident_console Slack prompts never surfaced (2026-04-19):** Creator generates realistic human-time offsets (90s, 3min, 5min, 7min). A competent learner resolves in 60-90 sim-seconds, so `slack_prompts_shown=0` and `comms` score awarded a free 1.0, making the rubric untestable. Fix: additionally fire prompts on command-count milestones (1st prompt → 1 cmd, 2nd → 3 cmds, 3rd → 5 cmds, ...). Time-based firing still works as a fallback.
- **adaptive_roleplay scoring bug (2026-04-19):** Director-of-Eng review agent found 10/10/10 concede scored 0.5. Two compounding bugs: (a) formula only looked at delta, ignoring absolute final state AND outcome; (b) `outcome` was a local variable in the turn endpoint, never persisted into `sess` before `_compute_roleplay_debrief(sess)` read `sess.get("outcome")` — which always returned None and fell into the neutral 0.4 branch. Fix: rewrite scorer as weighted sum (50% outcome × 30% final-state-floor × 20% trajectory) AND set `sess["outcome"] = outcome` before the debrief call. After fix: 2-turn concede with state 8/9/7 scores 0.79; 10/10/10 concede scores ~0.95.
- **Roleplay rubric tags missing BATNA/anchoring (2026-04-19):** Creator-generated rubric tags listed outcome-level labels (`stakeholder_relationship_management`, `business_context_awareness`) instead of the actual negotiation skills (`BATNA`, `anchoring`, `emotional_regulation`, `genuine_vulnerability`). Reviewer flagged: "the rubric names outcomes instead of skills." Needs Creator-prompt tightening to require canonical skill tags for each scenario type.
- **Roleplay module filler (2026-04-19):** Creator generated a concept step whose body read "In the work you will do after this course, this concept shows up most often in: day-to-day decisions about *the conversation playbook: what to say (and never say)*, where applying it poorly results in measurable cost..." — boilerplate that references its OWN module title verbatim. Reviewer: "recognizable filler within 10 seconds." Needs `_is_complete()` rejection of content containing own-module-title self-references.
- **Creator-compliance trade-off (2026-04-19):** Creator-generated courses have MORE BREADTH (4 modules vs hand-coded's 2, richer pedagogical scaffolding like "Pressure Chamber → Data-Driven Pushback → Conversation Playbook → Live Fire") but LESS DEPTH at the capstone (hand-coded's step 463 "Observer Not the Fixer" is sharper than anything Creator produced). Direction: tighten Creator prompt to instruct "name the junior antipattern explicitly in the pre-capstone concept step" for every immersive-capstone course.
- **Verified fix propagation (2026-04-19):** After Creator prompt hardened (canonical rubric_tags per scenario family, persona-must-not-coach, filler-detection in `_is_complete`), regenerated "Defending Scope Under Executive Pressure v2" (course `created-101ba7848a1f`) produced `rubric_tags: ['anchoring', 'data_specificity', 'phased_alternative', 'BATNA', 'emotional_regulation']` — **5/6 canonical tags adopted** (previously outcome-level labels). Persona prompt opens "You are Diana, VP Engineering under intense board pressure... zero patience for..." — no coaching, no complimenting. Zero filler detected. Generation cost: $0.24 / 66s. This closes the full review→fix→regenerate→verify loop in one iteration.
- **Pedagogical-delta validation on fixed scorer (2026-04-19):** Ran STRONG vs WEAK strategies against the v2 course on the fixed scorer. STRONG (data + phased alt + transparency + concrete commit) → `concede` in 4 turns, score **0.83**. WEAK (dismissive "board doesn't understand software" + hedging + defensive + panic-commit) → `escalate_CTO` in 2 turns, score **0.10**. **Gap: 0.73.** This is exactly what a working scoring rubric should produce: a skill-proportional score curve with large headroom between "learned the move" and "hasn't learned the move." The pre-fix scorer produced identical 0.5 scores for both these strategies — it had no pedagogical signal at all. The new three-component weighted scorer differentiates by 7.3× on a 0-1 scale for the strongest vs weakest valid plays.
- **Frontend render of new scorer fields (2026-04-19):** `score_breakdown` (the 3-component weighted sum: 50% outcome / 30% state-floor / 20% trajectory) is now shown in the roleplay debrief as a transparent "where your points came from" panel. Critical for learner-feedback quality: without it, a 0.10 score is just "bad" — with the breakdown, the learner sees exactly which lever (outcome? state? trajectory?) was missing. Also added `_classifyOutcome()` + `_humanizeOutcome()` so Creator-invented outcome strings (`escalate_CTO`, `become_openly_hostile`, `demand_immediate_escalation_to_VP`, `end_meeting_abruptly`, `ready_for_renewal_call`) render as colored (win=green / lose=red / neutral=grey) Title-Case labels instead of raw snake_case. Tested against 8 representative outcomes. Previously only 5 canonical strings (`concede`, `escalate`, `escalate_to_ceo`, `walk_away`, `timeout`) rendered correctly; Creator-generated outcomes fell through to raw text.
- **Pedagogical validation: counterparty correctly rejects vague/placeholder strategies (2026-04-19):** Ran a scoring-consistency test across 8 courses with a STRONG strategy that used template placeholders (`[specific number + mechanism]`, `[genuine vulnerability with a specific number]`). Result: 6/8 courses escalated in 1-2 turns with the placeholder strategy — the counterparty's state_update_rules correctly read placeholders as "evasive/unspecific/hedge" and punished them. The one course that didn't escalate under this treatment (Eng Manager, concede/0.77) had a more forgiving persona. This is actually a positive signal about the whole system: counterparties don't rubber-stamp anything typed in, they require actual concrete content. The lesson for the test harness (and learners): "strong" isn't a vibe — it's specificity.
- **Universal guardrail fix (2026-04-19):** Regenerated all 4 brittle courses (Sales Eng, Tech Writer, Mobile Eng, Staff PM) via Creator after adding guardrails. All 4 produced healthy persona states: Sales Eng {tech_conf 6, vendor_trust 5, urgency_pressure 7}, Tech Writer {pat 6, tr 5, flex 6}, Mobile Eng {pat 6, tr 7, conf 5}, Staff PM {conf 5, tr 6, urg 7}. All escalation thresholds at `<= 0`. Plus Data Analyst v2 {tr 6, pat 7, pc 5}, escalation `<= 0`. Staff PM v2 end-to-end: STRONG=`approve_with_full_budget` 0.77 vs WEAK=`walk_away` 0.03 → gap **0.74**. The guardrails fix was universal: 5/5 regenerations landed non-brittle personas from a single Creator-prompt change. The Creator-compliance invariant is paying dividends.
- **Test-harness learning (2026-04-19):** A one-size-fits-all STRONG strategy (negotiation-flavored) doesn't validate course-specific pedagogy — the Data Analyst v2 CFO correctly escalated at 0.01 because the STRONG script talked about "phased rollout in 4 weeks" when the scenario demanded a churn number before earnings call. This is the AI counterparty catching a real-world failure mode: answering a different question than the one asked. Future cross-course consistency tests must use scenario-specific STRONG strategies; generic "empathy + data + phased alt" only works when the scenario is a delivery negotiation.
- **SILENT EVAL-FAIL on uppercase AND/OR (2026-04-19) — the biggest bug of this iteration:** `_check_outcome()` used Python `eval()` on win_condition strings like `"trust >= 8 AND perceived_competence >= 7"`. After state substitution (`"8 >= 8 AND 7 >= 7"`), Python raised `SyntaxError: invalid syntax` on `AND` (must be lowercase `and`). The bare `except:` clause swallowed the error, returning `continue` for every would-be win. This had been in place since the adaptive_roleplay engine shipped on 2026-04-18 — **every course with uppercase `AND` in a win_condition had been silently unwinnable for ~24 hours**. Fix: new `_normalize_condition()` helper that substitutes state values AND normalizes `AND`/`OR`/`NOT`/`&&`/`||` to Python operators before eval. Added logging.warning on eval exceptions so silent swallowing can't happen again. Verification: Data Analyst v2 STRONG strategy now triggers `asks_to_present_to_board` (score 0.74) in a single turn of on-topic concrete content. Mobile Eng v2 → `supports_your_process` / 0.76 in 1 turn. Tech Writer v2 → `approve_with_minor_cuts` / 0.75 in 2 turns. Every previously-stuck course is now winnable. This is why the scoring-consistency test had shown so many courses "stuck in continue" — it wasn't state not progressing, it was the win-evaluator crashing silently.
- **META enforcement + keyword fallback (2026-04-19):** Two complementary resilience fixes for adaptive_roleplay turn loop: (a) `ROLEPLAY_SYSTEM_PROMPT` rewrites explicitly mandate META every turn with the full state dict + emphasize that forgotten META breaks the engine; (b) per-turn `user_prompt` shows the LLM the current state snapshot and reminds it to output ALL dimensions in the META; (c) deterministic `_apply_keyword_state_update(sess, learner_turn)` fallback runs when META is absent — inspects learner text for numbers / CI / cohort / hedges / rude tone / specific commits / BATNA / clarifying questions, and bumps matching dims ±1. Result: state always progresses for skillful vs unskillful play, even if Claude occasionally drops the META trailer. This paired with the AND/OR fix means the scoring system now works end-to-end whether the LLM cooperates or not.
- **3rd-reviewer findings (2026-04-19) — `CONDITIONAL` acceptance, 2 bugs fixed within the turn:** After 8+ engine bugs were already swatted, the 3rd UX reviewer (3rd-year data analyst persona playing Data Analyst v2 capstone as a real learner) found:
  - **P0 — ANSWER LEAKAGE in public API:** `GET /api/courses/.../modules/{id}` returned `validation` block verbatim with `correct_answer`, `correct_mapping`, `correct_order`, `correct_rankings`, `bug_lines`, `blanks`. Any DevTools or curl exposes the answer key for every categorization/ordering/mcq/code_review exercise. Fix: new `_sanitize_step_for_learner()` strips these fields before the response leaves the learner endpoint. Verified: 0 leaks post-fix.
  - **P0 extension — categorization `data-correct-cat` leak (2026-04-19):** The categorization step rendered `data-correct-cat="${item.category}"` attribute DIRECTLY into the HTML of each draggable card. View Source exposed the answer key without needing DevTools. Fix: removed the attribute, dropped the client-side fallback grading path that relied on it (grading is now server-side only via `/api/exercises/validate`; if that fails, the UI shows "Grading unavailable" rather than silently falling back to a leaked-answer client-check).
  - **KNOWN REMAINING LEAK (next iteration):** SJT and MCQ exercise types still have `options[].correct_rank`, `options[].correct`, and `options[].explanation` accessible via in-memory object inspection in DevTools console (not View Source — the fields aren't rendered into HTML, but they're present on the JS objects the frontend builds). Closing this requires: (a) server-side strip of those nested fields from `demo_data.options[*]`, (b) frontend refactor to render post-submission feedback from the validation endpoint's response (not from the pre-loaded options array). Medium effort, deferred for now since the View-Source vector is closed.
  - **P1 — 1-TURN WIN defeats pedagogy:** STRONG strategy won the capstone on turn 1 with a single data-dense paragraph. Scenario promised "4+ turns of grace" but learner never lived the pressure arc. Fix: `_check_outcome()` now enforces `MIN_TURNS_FOR_WIN = 3` before any win_condition fires (escalation_triggers still fire immediately — rude turn 1 correctly ends the meeting). Verified: STRONG t1/t2 both `continue`, t3 `asks_to_present_to_board` / 0.78. Learner now practices sustained pressure, not a lucky first paragraph.
  - **Reviewer's verdict on the WEAK path**: "Sarah got visibly colder each turn ('are you serious right now', 'slams laptop shut', 'stands up abruptly'), patience went 7→5→3→0, and the escalation was causally obvious. The weak-path persona behavior is the best thing in the product." That's validation that the state_update_rules + escalation_triggers are producing real-feeling counterparties.
- **Incident_console 0-command free pass fix (2026-04-19):** 1st SRE reviewer noted a learner who declared a wrong root cause with zero commands got `time=0.98` because elapsed sim-time was 0. Fix: `time_score` caps at 0.3 when `matched_cmds == 0`; `comms_score` caps at 0.3 when fewer than 3 commands ran (instead of defaulting to 1.0). Learners must actually play before getting scoring credit.
- **Broadened negative-dim detection (2026-04-19):** Creator invents dim names like `urgency_pressure`, `board_anxiety`, `impatience_level`. Fixed: `_is_complete()` now treats any dim containing `pressure|anxiety|impatience|hostil|aggression|skeptic|defensive|frustrat|stress|panic|combat` as negative (starts at ≤ 5). Unknown dim names default to positive (Creator-invented positive-framed names like `collaboration_index` or `perceived_competence` pass through).
- **Brittle-persona bug + guardrails (2026-04-19):** Cross-course scoring test also surfaced a Creator-output flaw: the Data Analyst course had `hidden_state: {trust: 4, patience: 3, confidence: 5}` with `escalation_triggers: [patience <= 1, trust <= 1]` — only 2 points of grace on each dim. Both STRONG-with-concrete-data and WEAK strategies hit `demand_immediate_escalation_to_VP` in 1-2 turns. Root cause: no Creator-prompt guardrails on initial state values or escalation thresholds. Fix (in two places): (a) Creator prompt now mandates "positive dims start at >= 5; escalation threshold must be <= 0 (not <=1 or higher); win condition <= 2 dims at >= 7 simultaneously"; (b) `_is_complete()` for adaptive_roleplay rejects any generated course that violates those thresholds. Regenerated Data Analyst v2 (`created-ee56d7f41c3d`): new hidden_state `{trust: 6, patience: 7, perceived_competence: 5}`, escalation at `<= 0`. Result: WEAK hedge-strategy correctly fails at turn 4 (`end_meeting_abruptly`, score 0.01); STRONG concrete-strategy stays in dialog across 8+ turns without escalating. That's the pedagogical signal — vague gets a wall, concrete gets persistence. Cross-course average gap on the fixed Negotiation/Scope-Defense/Eng-Manager courses: 0.76 (0.73 / 0.85 / 0.70). The scorer hits 0.9 peak correctly (Scope Defense v1 with concrete STRONG = concede/0.90).

### Creative-Review Proposals (2026-04-19) — Pedagogy Roadmap

Three creative reviewers delivered concrete proposals for immersive exercise types. All three converge on the same meta-primitive — see "simulator_loop" below. Implement in priority order:

**Priority 1: `incident_console` exercise type** (Reviewer 1 — for SRE / support engineering / debugging)
Data shape:
```json
{
  "alert": {"title": "...", "severity": "P1", "initial_metrics": {...}},
  "log_stream": [{"t_offset_ms": 0, "line": "...", "gated_by": null}],
  "commands": [{"pattern": "kubectl logs ([\\w-]+)", "output": "...", "unlocks": ["log_line_id"], "time_cost_s": 20}],
  "slack_prompts": [{"t_offset_ms": 90000, "from": "PM", "text": "...", "timeout_s": 120}],
  "revenue_per_min": 200,
  "root_cause": "connection_pool_leak",
  "accepted_remediations": ["kubectl rollout undo ...", "kubectl scale ..."],
  "cascade_rules": [{"trigger_command": "kubectl delete", "effect": "error_rate += 30"}]
}
```
UI: 4-pane terminal (log tail / shell prompt / Slack chat / metrics strip). Grades on: time-to-resolution, correct root cause, minimal destructive commands, Slack response latency, minimum-viable fix.

**Priority 2: `adaptive_roleplay` exercise type** (Reviewer 2 — for negotiation / leadership / interviews / POSH / sales)
Data shape:
```json
{
  "scenario_prompt": "framing shown to learner",
  "counterparty": {
    "persona_system_prompt": "...",
    "hidden_state": {"patience": 7, "flexibility": 4, "trust": 5, "anchored_on": "..."},
    "state_update_rules": "LLM instructions for mutating state per learner turn",
    "escalation_triggers": [{"condition": "patience<=0", "action": "escalate_to_ceo"}],
    "win_conditions": [{"condition": "trust>=8 && flexibility>=7", "outcome": "concede"}]
  },
  "turn_limit": 15,
  "debrief": {"show_state_trajectory": true, "rubric_tags": ["anchoring", "data_use", "emotional_regulation", "batna"]}
}
```
LLM cost estimate: ~$0.02 per 15-turn session (Haiku). Reusable across ≥4 courses. Learner-types-free-text, system-updates-hidden-state loop.

**Priority 3: `simulator_loop` primitive** (Reviewer 3 — umbrella primitive for all of the above)
Server-authoritative tick-based engine: state schema per scenario, event generator, action API, terminal-state evaluator. WebSocket state diffs + action-submit endpoint. Three frontend widgets sit on top: **live-dashboard**, **terminal-emulator**, **action-deck**.

Use cases mapped: K8s "3 AM pager", Stats "launch review", Vector-DB "search quality arena", Fintech "18 months in 25 minutes", Incident-response, Hallucination hunt, Capacity planning.

**The overall pattern**: stop asking "pick the best of A/B/C/D." Start putting learners into a situation with an evolving state, let them type/click/query freely, and grade on the state trajectory (decisions made, consequences earned, final outcome) — not single-turn correctness.

Budget target per course: ~$0.50 for course generation + ~$0.02/user/session for `adaptive_roleplay` turns. Well within the $100 cap.

### Shipped (2026-04-19): `adaptive_roleplay` exercise type — fully implemented + validated

**Backend:** `POST /api/roleplay/start` + `POST /api/roleplay/turn` with in-memory session store. Uses Claude Sonnet 4. Hidden-state update + escalation triggers + win conditions. Automatic state-trajectory debrief on session end. Budget-aware: falls back to mock counterparty if `_llm_enabled()` is False. Parses `<<META: state={...}, outcome=X>>` from LLM replies.

**Frontend:** `renderAdaptiveRoleplayStep()` + `setupAdaptiveRoleplay()` + free-text chat widget with scenario briefing pane, turn counter, debrief modal showing state trajectory (start→end per dimension) + rubric-tag skill labels. Marks step complete at score ≥ 50.

**Validated:** End-to-end test against the seeded course `roleplay-negotiation-vp` ("Live Negotiation: Defending Scope Under Pressure"). Learner brought data → Diana trust 5→8, flexibility 4→9 (both +), patience 7→7 (preserved). 2-turn concede outcome. Cost: $0.019 for 3 turns, well under budget.

**Seed course live at:** http://localhost:8001/#roleplay-negotiation-vp (Module 2 Step 1 = the capstone negotiation).

### Shipped (2026-04-19): `incident_console` exercise type — fully implemented + validated

**Backend:** 4 endpoints — `POST /api/incident/start` / `/command` / `/slack_reply` / `/declare`. In-memory `_INCIDENT_SESSIONS`. Zero-LLM scripted engine: regex command parser, time-cost accounting, gated log-line unlocks, cascade rules for destructive commands, time-offset Slack prompts, accepted-remediation regex list, root-cause hypothesis scoring, multi-dim debrief (time/accuracy/comms/blast-radius weights).

**Frontend:** `renderIncidentConsoleStep()` + `setupIncidentConsole()` — 4-pane UI (alert banner, metrics strip, live tailing log, interactive shell with command parser + canned output, Slack thread with reply-able prompts) + declare-root-cause modal + debrief breakdown with score bars. Banner: `🚨 INCIDENT CONSOLE`.

**Seeded course:** `sre-3am-pager` — "SRE 3AM Pager: Live Incident Response". Module 1 = pre-drill briefing (concepts + categorization of symptom→command). Module 2 = the drill: `payment-api` outage at 03:42 AM, 47% error rate, $2K/min bleeding, 3 pods in CrashLoopBackOff, root cause is connection-pool exhaustion from a recent deploy. 12 scripted commands, 10 gated log lines, 3 time-offset Slack prompts, 3 cascade rules, 3 accepted remediations (`rollout undo` / `set env MAX_CONNECTIONS` / `scale --replicas=N`).

**Validated end-to-end via curl:**
- 4 commands: get pods → rollout history → logs --previous → rollout undo
- Diagnostic path unlocked 4 gated logs (discover-pods, rollback-avail, rootcause, deploy-event)
- Remediation accepted → error rate 47% → 0%, incident resolved
- Debrief: 76% score, 75s sim time (under 600s budget), $1,175 revenue lost, 0 cascades
- **Total LLM cost: $0.00** (zero per session — scripted only)

**Why `incident_console` matters economically:** adaptive_roleplay runs ~$0.02/session/learner. Incident_console is $0. For 1000 learners doing the SRE drill, adaptive_roleplay would cost $20; incident_console costs $0. Scales infinitely. Reuse across SRE, security IR, ML-ops, fintech ops, DB admin. Every domain where "drop them in the situation" is the right pedagogy.

### Shipped (2026-04-19): `voice_mock_interview` exercise type — live mic interviews

**Why this type matters:** Many real-world skills are fundamentally VERBAL — behavioral interviews, case interviews, investor pitches, language fluency, public speaking, leadership 1:1 coaching, doctor-patient communication. The text-based adaptive_roleplay captures the decision-making layer, but NOT the delivery layer: pace, filler words, structure, confidence, clarity. Voice_mock_interview adds the delivery layer without adding per-session cost, because it uses browser-native SpeechRecognition (STT) and SpeechSynthesis (TTS).

**Architecture:** Reuses the adaptive_roleplay engine end-to-end — same `/api/roleplay/start` and `/api/roleplay/turn` endpoints, same hidden-state scoring, same META parsing, same win/escalation evaluator with AND/OR normalization. The only divergence is `demo_data.voice_mode=true` + `demo_data.interview_style` + `demo_data.opening_question`, and a dedicated frontend widget that renders a mic button instead of a text input.

**Frontend:** `renderVoiceInterviewStep()` + `setupVoiceInterview()`. Mic button uses `window.SpeechRecognition || webkitSpeechRecognition` (available in Chrome, Edge, Safari; degrades to text-only in Firefox). Interviewer replies are spoken via `window.speechSynthesis.speak(new SpeechSynthesisUtterance(text))` with an en-US voice preference. Text fallback always available — if mic isn't granted, learners can type. Transcript pane shows both sides with a per-message "🔊 Speak" button to replay interviewer utterances.

**Cost:** Zero added per-session cost beyond what roleplay already spends on LLM turns. Voice I/O is 100% browser-native. The $0.02/turn LLM cost is identical to adaptive_roleplay.

**Creator picks voice_mock_interview automatically** for: behavioral interviews, case interviews, technical interview prep, leadership coaching, investor pitches, MBA admissions, doctor-patient communication, language fluency, public speaking, sales demo practice, media training. Text-based adaptive_roleplay is preferred for written-exchange skills (email, Slack, spec review).

**Canonical rubric_tags per interview_style** (Creator prompt enforces these):
- behavioral → STAR_structure, specificity_of_example, ownership_of_outcome, metrics_grounding, self_awareness
- case → framework_selection, math_fluency, hypothesis_iteration, executive_summary, comfortable_with_ambiguity
- technical → problem_decomposition, tradeoff_articulation, depth_of_domain, communication_of_complexity
- leadership → vision_articulation, calibrated_confidence, stakeholder_empathy, tough_decision_ownership
- sales_pitch → discovery_questions, value_framing, objection_reframe, specificity_of_ask
- public_speaking → hook_strength, narrative_arc, pacing, filler_word_discipline, audience_awareness
- language_fluency → vocabulary_range, pronunciation_clarity, grammatical_accuracy, fluency_under_topic_shift

**Voice-interview hidden_state dims** differ from negotiation: interviewers collect signals rather than build trust. Canonical dims: `signal_strength`, `composure`, `credibility`, `engagement`, `clarity`, `presence`. The Creator is instructed NOT to reuse negotiation dims (patience/trust/flexibility) for interview scenarios.

**Smoke-test evidence (2026-04-19):** Generated "Behavioral Interview Prep: Senior PM at a B2B SaaS" via Creator (`created-72374887cf79`, $0.38, 87s). Creator picked voice_mock_interview for the capstone. Schema: `interview_style=behavioral`, `voice_mode=true`, `opening_question="Walk me through the hardest product prioritization decision you made in the last year where you had to say no to multiple stakeholders..."`, `persona_name="Sarah Chen (Senior Director of Product, interviewing you)"`, `hidden_state={signal_strength: 5, composure: 6, credibility: 5}`, `rubric_tags=[STAR_structure, specificity_of_example, ownership_of_outcome, metrics_grounding, self_awareness]`. Turn 1 with a strong STAR-framed behavioral answer got a legitimate probing follow-up from Sarah ("That's a really solid example - I appreciate how you quantified...  I'm curious about..."). Course live at http://localhost:8001/#created-72374887cf79.

### Shipped (2026-04-19): `simulator_loop` umbrella primitive

Generic tick-based simulation engine for ANY evolving-state immersive exercise. Endpoints: `POST /api/simloop/start` + `/advance` + `/action`. Safe mini-expression evaluator for win/lose conditions. Per-tick natural evolution rules. Event scheduling by t_offset_ms.

Frontend: `renderSimulatorLoopStep()` + live-dashboard widget with auto-updating metrics, event stream sidebar, action-deck panel. Banner: `⏱ LIVE SIMULATION`.

Reusable for: K8s pager drills, fintech growth-over-18-months, RAG hallucination hunts, capacity planning under budget cap, search-quality arenas — all use the same primitive with different demo_data schemas.

### Validated (2026-04-19): adaptive_roleplay pedagogy at scale

**6-persona stress test against the Negotiation-with-Diana demo** — each persona used a different strategy:

| Persona | Strategy | Outcome | Final trust | Final flexibility |
|---|---|---|---|---|
| 1 | Data-driven + phased rollout | concede | 8 | 8 |
| 2 | Hedging ("we'll try") | walk_away | 0 | 4 |
| 3 | Combative ("impossible") | walk_away | 0 | 4 |
| 4 | Over-committer | walk_away | 1 | 4 |
| 5 | Curious questions first | concede | 6 | 8 |
| 6 | Data + acknowledges constraints | concede | 7 | 8 |

The AI counterparty correctly rewards data/specificity/alternatives and punishes hedging/combat/over-promising. 3 concedes + 3 walk_aways is exactly the pedagogically-correct distribution. Cost: $0.80 for 15 total turns.

### Shipped (2026-04-19): 18 courses using new pedagogies

- 10 courses from the "immersive wave" (Customer Success, EM first 90 days, Hiring, Sales, Security IR, Eng Leadership Under Outage, Postgres Ops, ML Ops Outage, PM Scope Neg, Kafka Outage Drill) — **10/10 adopted `adaptive_roleplay` or `incident_console`**
- 3+ courses from the "diverse wave" so far (Async Comms, Crisis Comms, Technical Debt) — also hitting 100% new-pedagogy adoption
- 5+ more diverse-wave courses in flight

Quality-floor now accepts `adaptive_roleplay` / `incident_console` / `simulator_loop` as valid engineering + case-study capstones.

### Stress-test evidence (2026-04-19)

**Clicky at scale:** 46 queries (27-query burn + 19-query deep burn with 4 multi-turn dialogs). All powered by claude-sonnet-4, average response length ~1200 chars for concept questions. 5/5 answer-requests on exercises correctly refused with Socratic hints. Multi-turn dialogs preserve history for continuity (vector-db deep-dive, FastAPI 503 debugging, negotiation coaching, user-interview coaching all worked).

**adaptive_roleplay at scale:** 14 sessions against 9 different courses. Creator-generated personas include rich hidden state (trust/flexibility/rapport/defensiveness). Course-specific outcomes beyond the standard set: `become_guarded` (Sales), `become_hostile` (Hiring), `demand_external_audit` (VP Eng post-mortem). Scenarios reference real names (Alex Chen missed deadline, Marcus Chen senior architect, TechFlow CFO, Diana VP Eng).

**Wave 3 (10 courses):** 10/10 adopted new pedagogies. Topics: VC pitching, salary negotiation, code review conversations, Redis cache apocalypse, monolith migration (simulator_loop-compatible), customer support under regulatory scrutiny, tech lead office hours, data eng reliability, enterprise architect review, LLM engineering under production load.

**Full count:** 64 courses live (growing). Budget spend this iteration: $11 → $22 (real Anthropic API usage on course generation + stress-testing + Clicky + roleplay).

### Function-focused AI-upskilling waves (2026-04-19) — 21 courses across business + technical functions

**Business-function wave (6 courses):** Finance Close, Finance Forecasting, Recruitment, Product Discovery, Design AI Research, HRBP. 6/6 adopted `adaptive_roleplay` or `incident_console`.

**Exec-functions wave (6 courses):** HRBP (PIP defense), Legal (contract review + liability cap roleplay), Marketing (attribution model defense), Ops (ticket-queue meltdown incident_console), CS Leader (renewal coaching roleplay), Exec (conflicting-advisor $5M bet). 6/6 adopted new pedagogies.

**Tech-function wave (5 courses):** Sales Engineer, Data Analyst, Technical Writer, DevOps, Security Engineer. 5/5 adopted `adaptive_roleplay`; 2/5 (DevOps, Security) also adopted `incident_console` where the pedagogy demands it (2 AM K8s cluster degradation, 4 AM credential-stuffing attack). Clicky burn of 25 domain-specific queries all powered by claude-sonnet-4, average response length 1,250 chars.

**Empathetic vs direct strategy evidence:** 10 function-course roleplays with 15-turn empathetic-and-curious turns. Outcome distribution: 1 concede (HRBP, 12 turns), 1 walk_away (Exec), 1 approve_with_conditions (Design AI), 7 unique domain-specific adversarial outcomes (`demand_immediate_manual_process`, `cut_meeting_short`, `become_skeptical_and_curt`, `request_user_research_deep_dive`, `escalate_general_counsel`, `request_postponement`, `ready_for_renewal_call`). Every course produced a DIFFERENT outcome — validates that persona state machines are course-specific, not templated.

### Creator-compliance proof (2026-04-19) — Direct-DB seeds officially obsolete

Compliance test for the new "all courses via Creator dashboard" invariant:
- Regenerated `roleplay-negotiation-vp` via `/api/creator/start` → `/refine` → `/generate` with prose description alone → new course `created-b5bf83e516b0` "Defending Scope Under Executive Pressure" — **4 modules** vs the hand-coded original's 2 modules.
- Regenerated `sre-3am-pager` the same way → `created-3604bb66d5df` "Live SRE Drill: 3AM Payments Outage" — **4 modules**, adopted BOTH `adaptive_roleplay` and `incident_console`.
- Result: the Creator out-designed the hand-coded seeds. New structures: "Pressure Chamber → Data-Driven Pushback → Conversation Playbook → Live Fire"; "3AM Alert Triage → K8s Emergency Response → Cross-Team Incident Comms → Live Payments Outage Simulation."
- Conclusion: no more direct-DB seed scripts. The two existing `seed_*` scripts in `/scripts/` are historical artifacts; their replacements live at the `created-xxx` IDs above.

### Total course count: 100+ live. Budget spend: $22 → $36.83 (real Anthropic API burn on iteration, stress-testing, Creator generation, Clicky at scale, adaptive_roleplay sessions, and **12 engine/Creator-prompt/frontend bug fixes surfaced by 3 creative-review agents** — covering incident_console (cascade, log leak, Slack timing, free pass), adaptive_roleplay (scorer, outcome persist, persona brittleness, AND/OR eval crash, META resilience, min-turns floor), Creator prompt (canonical rubric, filler detect, no-coach, guardrails), learner-API answer-leakage P0 (validation-block sanitization), and frontend categorization `data-correct-cat` view-source leak).

### Underserved-functions wave (2026-04-19) — 5 more courses via Creator

- Accountant (`created-51802ac917f1`): audit-prep roleplay with Big-4 senior auditor; persona {confidence_in_client 6, documentation_satisfaction 5, technical_respect 6, escalation_risk 3}. GAAP_reasoning, citation_specificity, documentation_integrity rubric tags.
- Investor Relations (`created-6334e60d76ce`): activist-investor Q&A roleplay; persona {credibility 6, patience 7, skepticism 5, data_satisfaction 5}. clarity_under_pressure rubric.
- BizDev (`created-9faae4f124c6`): strategic-partner VP demanding better rev-share; persona {patience 6, trust 7, flexibility 5}. data_specificity, relationship_preservation, BATNA rubric.
- CS Ops (`created-63658301ac77`): adopted BOTH adaptive_roleplay AND incident_console for the "T1 churn threat with CSM out" drill.
- Chief of Staff (`created-64fcce05fa26`): briefing a CEO with no pre-read; persona {confidence 6, trust_in_briefer 7, time_pressure 8}. time_pressure is scenario-flavor (not referenced by escalation/win) — my heuristic flagged it, but the course is pedagogically sound.

### Creator prompt guardrail nuance (2026-04-19):
The negative-dim heuristic (reject positive dims < 5, reject negative dims > 5) is a useful default but it's overeager in some scenarios. Example: Chief of Staff course has `time_pressure: 8` as a scenario-context marker (the CEO is busy). No escalation_trigger or win_condition references `time_pressure` — it's purely flavor. The real check should be: "does this dim gate any outcome?" If yes, guardrails apply. If no, the Creator can start it anywhere that's narratively appropriate. Future refinement: `_is_complete` should only reject persona states when a gating-role dim violates guardrails.

**Outcome-diversity evidence (final burn of 2026-04-19):** 7-course 10-turn-max roleplay run returned 7 UNIQUE outcomes — `escalate` (Scope Defense), `escalate_ceo` (SRE), `become_openly_hostile` (Sales Eng), `demand_immediate_escalation_to_VP` (Data Analyst), `end_meeting_abruptly` (Tech Writer), `demand_to_speak_to_senior_engineer` (DevOps), `continue` (Security Eng reached turn 10). Empathetic-only strategy does NOT universally win — tech-function personas demand data + specificity, empathy alone triggers hostility. Pedagogically correct: a learner doing only-empathy learns this by failure.

**Other fixes same turn:**
- Next-Module button bug on course-switch: `Object.keys(state.modules)` returned array indices "0"-"4" instead of module DB IDs; replaced with `mods.findIndex(m => String(m.id) === String(state.currentModule))`. Also fixed `enterModule(...)` undefined reference → now calls `loadModule(nextModId, 0)`.
- Capstone template-leak regression: `_is_complete()` for system_build now blocks 6 generic-content phrases ("The core idea behind", "Reflection prompt: spend 60 seconds", "Define success criteria for {TITLE}", "What you'll learn here", "Pitfalls to avoid", "where in your current work would this") and checks ALL phase/checklist labels (strict `all()`) — not just any one.
- Fallback content rewritten per exercise_type: `system_build` gets real mission briefing, `code_exercise` gets task framing, `concept` gets applied-to-course framing, `scenario_branch`/`sjt` get decision-point framing. No more shared generic boilerplate.

## 🔄 Do Not Patch Broken Generated Courses — Regenerate After Fixing the Creator

When a reviewer finds a flaw in a Creator-generated course:
1. **Do not edit the course's DB rows to fix it.** That masks the Creator bug.
2. **Update the Creator workflow** — system prompt, enforcement post-processing, quality floor, fallback templates, whatever's needed.
3. **Regenerate the SAME course with the SAME inputs.** (Preserve original title/description/source-material.) This proves the fix worked on future creations, not just on that one course.
4. **Compare old vs new.** Did every flaw the reviewer found disappear? If not, the Creator fix wasn't complete.
5. **Only then accept.** The acceptance criterion is "the Creator now generates this course correctly from scratch," not "this one course row looks OK."

Exception: pure data-shape mismatches (e.g. validator reads field X but course data has it in field Y) can be patched in-place, since they're validator bugs not Creator bugs.

## 📁 Course Creation from Documents

The Creator accepts file uploads as a seed. Flow:
1. **Frontend**: wizard step 1 has a `<input type="file" multiple>` accepting PDF/DOCX/PPTX/TXT/MD.
2. **Backend**: `POST /api/creator/upload` extracts text server-side (`_extract_pdf_text`, `_extract_docx_text`, `_extract_pptx_text` in `backend/main.py`).
3. The extracted text is combined with any typed source material and passed to `/api/creator/start` as `source_material`.
4. The Creator's LLM sees the actual training-doc content and uses it to generate course-specific modules + steps grounded in the source.

Limits: 10 files / 5MB each / 20MB total / 200K chars extracted per file.

Supported formats and tested against real training materials including:
- TCS ILP handbooks (60-day induction program)
- Infosys Foundation Program curriculum (23-week Mysore GEC)
- Any engineering/compliance/business onboarding content

## ⚠️ HARD CONSTRAINT: Anthropic API Budget Cap — $100 USD

**The user has set a HARD CAP of $100 USD on total Anthropic API spend.** (Increased from $20 on 2026-04-18.) This constraint persists across all future sessions and context. Enforce it in every piece of code that calls `anthropic.Anthropic`.

**How it's enforced (in `backend/main.py`):**
- Cumulative spend is tracked in `/Users/tushar/Desktop/codebases/skills-lab-v2/.anthropic_budget.json`
- `_llm_enabled()` returns `False` when spend ≥ cap → all LLM callers auto-fall back to mocks
- Env vars:
  - `ANTHROPIC_BUDGET_USD=20` — set the cap (default 20)
  - `USE_MOCK_LLM=1` — force mock mode (bypasses real API entirely)
- GET `/api/admin/budget` exposes current spend/remaining

**Rules for all future code:**
1. **Never add a new `anthropic.Anthropic().messages.create(...)` call without going through `_llm_json_call` or `_clicky_real_llm_response`** — those helpers check `_llm_enabled()` and record cost.
2. **Prefer mocks for: load testing, stress testing, bulk course generation, CI, local dev.** Use `USE_MOCK_LLM=1` before any test that would burn tokens.
3. **When generating new courses, assume budget pressure.** Ship a mock-fallback for every LLM-backed feature (Creator content generation, Clicky). If real LLM unavailable, the mock response must still be substantive (not a "sorry, unavailable" stub).
4. **Do not seed the budget file with fake low numbers to unlock more spend** — that defeats the constraint. If real spend is ambiguous, estimate conservatively (upward).

## Tech Stack
- **Backend**: Python 3.14, FastAPI, async SQLAlchemy (SQLite + aiosqlite)
- **Frontend**: Single-file HTML (`frontend/index.html`), dark theme, no build step
- **Database**: 6 tables — Course, Module, Step, UserProgress, Certificate, ReviewSchedule
- **Code Execution**: Sandboxed `exec()` with mock modules, 10s timeout, restricted builtins
- **Server**: uvicorn on port 8001, launch config in `.claude/launch.json`
- **LLM Budget**: $100 USD cap on Anthropic API, auto-mock fallback. Current spend: see `/api/admin/budget`

## Project Structure
```
skills-lab-v2/
├── backend/
│   ├── main.py              # FastAPI app, routes, sandbox, validation
│   ├── database.py           # SQLAlchemy models & async session
│   ├── schemas.py            # Pydantic v2 request/response models
│   └── courses/              # Course content as Python dicts
│       ├── technical_*.py    # Technical skill courses
│       ├── case_study_*.py   # Case study courses
│       └── compliance_*.py   # Compliance/knowledge courses
├── frontend/
│   └── index.html            # Complete SPA (3300+ lines)
├── .claude/
│   └── launch.json           # Preview server config
└── CLAUDE.md                 # This file
```

## Reference Project
- `../ai-skills-lab` — Earlier version with Clicky AI assistant, Agentic Coding Demo. Use for:
  - Clicky system prompt patterns (teaching rules, never-give-answers behavior)
  - Assignment quality baseline (improve upon it)
  - Exercise hint patterns
