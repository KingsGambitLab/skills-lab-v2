# VP Product Review — AI-Powered Workday

**Course:** "AI-Powered Workday: Ship 3 Prompt Workflows to Your Team This Week"
**Target audience:** 200-person mid-market SaaS (PMs, Ops, CS, People-Ops, Marketers)
**Reviewer lens:** VP Product / AI Enablement Lead (has shipped adoption programs; has seen shelfware)
**Date:** 2026-04-24
**Coverage:** M0.S1–S2, M1.S1–S5, M2.S1–S4, M3.S1–S4, M4.S1–S2, M4.S4, M5.S1–S3, M5.S5 (full capstone). ≥ 12 steps walked; STRONG + WEAK tested on M1.S3 explanation and M5.S5 capstone; M4 simulator mid-drill screenshotted.

---

## Top-line verdict
**SHIP — with two P0 fixes and one P1 UX bug.**

This is the most real, Monday-deployable non-coder AI course I've evaluated. It teaches the mental model (SPEC + 6-slot template), drills hallucination detection like a skill (not a warning), forces measured before/after baselines, and ends on a markdown artifact that actually pastes into Notion. Three clear drift violations against the "no code" promise are fixable in a week. Until they are, hold a paid 200-seat rollout — but don't kill it.

## What works (grounded in specific steps)

1. **The mental model is named and taught, not listed.** M1.S1 introduces the **SPEC framework** (Specificity + Examples + Constraints + Escalation). M3.S1 introduces the **6-slot template** (Audience / Goal / Format / Examples / Constraints / Escalation). They are the same idea escalated in resolution — the learner gets a repeatable internal grammar, not "here are 10 tips." The SPEC→6-slot progression is pedagogically tight.
2. **Hallucination detection is drilled, not lectured.** M2.S1 frames with "The $2.3M Board Meeting Disaster" and "The Marcus Chen Rule: if this number is wrong, who gets fired?" — concrete consequence framing. M2.S2 then drops 8 facts about fictional "Kelvingrove Corp" (a mix of grounded + fabricated specific-number claims with fake investor names, specific ARR growth, named churn-rate deltas) and asks the learner to separate them. M2.S3 adds the killer trap: a Claude response with 4 confident stats, then a follow-up where Claude says "from industry analysis" with no URLs — the learner who defers to the "industry analysis" phrasing learns the lesson in situ. This is detection-as-skill, not awareness.
3. **Real-world transfer is real.** Exercises use the tasks knowledge workers actually do: weekly status to Marcus Chen, customer-interview synthesis from 5-8 transcripts, performance-review draft from 6 months of 1:1 notes, 847-ticket feedback synthesis, onboarding checklists, Q3 GTM talking points for the board. Recurring stakeholder cast (Marcus Chen / Priya Sharma / Elena Rodriguez / David Kim) builds narrative continuity across 20+ steps — a surprisingly effective retention device. No "imagine a stakeholder" filler.
4. **The grader discriminates. Sharply.**
    - M1.S2 (DELEGATE/PAIR/NEVER): empty submission → `Score: 0% (0 of 8 correct). 2 more retries before the full breakdown reveals.`
    - M1.S3 (explanation rubric): weak answer ("it has more detail") → `Score: 20%` with actionable critique ("didn't identify specific elements like audience definition, format constraints, or structural requirements").
    - M5.S5 capstone: weak → `Score: 5%. Doc rubric: 10%. Your templates lack specificity—'write status updates' and 'write emails' are exactly the vague formulations the rubric warns against.`
    - M5.S5 strong → `Score: 65%. Doc rubric: 90% (threshold 70%). Strong submission that hits most criteria well. Specificity is excellent... Measurement realism is solid with concrete before/after times like '42 minutes' to '11 minutes'. Examples are present and concrete for Templates 1 and 2. Adaptation guide teaches well with the '6-slot structure' principle. Minor gap: Template 3's example output shows '(standard template filled in)'.`
    The 5%→65% range with specific identified gaps is adult-education-quality grading. It will not be gamed by BS answers.
5. **The capstone is a team artifact, not a certificate.** M5.S5 is explicitly "Zero-Code Zone: only claude.ai in your browser + a doc editor (Notion/Google Docs/plain markdown). No terminal, no GitHub, no deployments." Deliverable is a markdown doc with 3 templates (goal/audience/format/example I/O/measured time savings) + a meta-adaptation guide (3+ paragraphs) + HUMAN-VERIFY notes for numbers/compliance content. Acceptance checklist has 6 concrete items (stopwatch measurement, HUMAN-VERIFY flag, 3+-paragraph adaptation guide, etc.). This is exactly the artifact a PM can paste into a Confluence page on Monday.
6. **The simulator is real, not a quiz.** M4.S2 is a live 60-tick simulation: 11 actions (template reply, batch triage, structured-prompt reply, CEO draft, fact-check, slack ping response, 3-min focus break, forward to specialist, etc.), each with tick cost, plus focus-token economy and scheduled interruption events (slack pings at t=300000ms, t=900000ms). Dashboard metrics: time remaining, messages completed, quality score, hallucination catches, focus tokens, CEO email handled. After 5 of my actions I was at 20/60 ticks with quality 41, focus dropped 10→4, 1 hallucination caught. This genuinely tests speed-vs-quality tradeoffs under interruption pressure — not a gamified multiple choice.

## Ship-blockers (P0)

1. **"Zero-code" promise violated in 3 fill-in-the-blank steps** (M1.S4, M2.S4, M5.S2 capstone brief). Each uses Python syntax — `task_name = ""`, `minutes_taken = `, `personal_checklist = { "": "", ... }`, `weekly_time_cost = minutes_taken * {'daily': 5, 'weekly': 1}[frequency]`, `print(f"Task: {task_name}")`. For a course that opens with "✗ API integrations or Claude Code / ✗ Terminal commands or programming," this is false advertising at three stages. A PM / people-ops lead seeing Python dict literals and f-strings will either (a) bail ("this isn't for me"), (b) complete it mechanically without understanding, or (c) complain to their manager that the enablement team misrepresented the course. **Fix:** convert these three steps to plain form fields with labels. Same data captured, zero cognitive cost. Also brings the course into compliance with its own M0.S1 promise.
2. **M4 simulator Event Stream exposes raw JSON to non-coders.** Event stream entries render as `tick 13 {"id":"ping_1","t_offset_ms":300000,"effect":{"focus_tokens":"- 1"}}`. A marketer seeing `t_offset_ms` and nested JSON is being thrown engineering affordances in what should be an inbox simulator. The simulator mechanics are excellent; just render the event as `9:05 AM — Slack ping from Marcus (−1 focus)`. This is a 30-minute string-template fix.

## Nice-to-haves for v2 (P1)

1. **M1.S3 rubric grader caches on re-submit.** Submitted weak answer → scored 20%. Edited to strong answer, hit Submit; button showed "Grading…" and returned, but the displayed feedback panel stayed pinned to the 20% critique. Had to repeat. Behavior was fine on M5.S5 (capstone re-grade returned a fresh score), so this is isolated to the explanation step. Likely a stale state key in the feedback render. Fix before rollout or learners will think the grader is broken.
2. **Drag-and-drop categorization titles lie.** M1.S2 says "sort **15** PM-ops-CS tasks" — only 8 render. M2.S2 says "15 'facts'" about Kelvingrove — only 8 render. Either trim the titles or extend the item lists. The current state looks like a bug, and it caps the drill's difficulty. Same pattern in M4.S4 (6 items, title consistent, OK).
3. **Navigation between modules is unreliable.** Next → sometimes reversed me one step; clicking a module in the sidebar sometimes jumped to M0.S1 instead of the clicked module's step 1. Had to use `window.location.hash = '#created-.../23200/4'` to reliably reach M5.S5. A learner using only the UI will hit this. Smoke-test the step/module router before rollout.
4. **M1.S4 baseline measurement** is conceptually right but isolated. The learner times one task, but there's no place later in the course where the course refers back to "your baseline" as a measurement anchor. Consider a tiny "Carry forward" UI: M1.S4 baseline value flows into the M5 capstone brief. Turns the exercise from a checkbox into a compounding artifact.
5. **Minor vocab bleed:** M3.S4 describes iteration "like editing a document or debugging code" — the "debugging code" half is unnecessary for the persona. M1.S2 mentions "Senior DevOps role" and "frontend developer screening" as job titles in the PM/ops/CS task list — acceptable (they are job titles, not instructional content) but a People-Ops persona might stumble. Substitute with "Senior Account Manager role" and "Customer Success screening" for clean persona fit.
6. **Capstone grader rewards the checklist and doc rubric, but phase checkboxes don't update from the doc content.** I hit 6/6 checklist and 90% doc rubric, but "Phases completed: 0/4" dragged me to 65%. The phases (Structure / Draft / Validate / Publish) are time-based and the learner has no obvious way to mark them from the paste step. Either auto-infer from the doc (e.g., if a stopwatch measurement is present, count Validate as done) or put explicit phase checkboxes next to the acceptance checklist.

## Would I buy this for my 200-person team?

**Yes, with the P0 fixes in place.** I'd run a 10-seat pilot on a Tuesday (PMs + CS leads), fix the three Python-drift steps and the JSON event stream before the broader rollout, and pitch it internally as "1 hour per seat for a shareable 3-template library + a hallucination-detection reflex that survives Monday-morning pressure." The economics — even if each learner only ships 1 of their 3 templates and each template saves 20 min/week — pay back in four weeks for 200 seats. More importantly, the SPEC/6-slot framework gives my team a shared vocabulary for reviewing AI outputs in each other's work; that's the team-multiplier I can't buy in a vendor webinar.

What tips it past "hold": the grader rigor (5% → 65% on the same capstone structure) means learners can't fake completion. The hallucination drill (M2.S2 + M2.S3 decision tree) is the best non-technical treatment I've seen of "confidently wrong." And the capstone artifact is an actual team asset — not a certificate.

What keeps it from "enthusiastic yes": the three Python-drift steps will undermine trust on day one for exactly the persona this course targets. Fix those before anyone sees it.

## Comparable vs Anthropic/OpenAI tutorials

Anthropic's prompt engineering course and OpenAI's Cookbook tutorials are strong for engineers who can read code — both default to Python notebooks and API calls. Neither has a non-coder track that teaches prompt workflows at the team-artifact level. Anthropic's *Prompt Engineering Interactive Tutorial* is the closest comparable on mental-model rigor (it names similar patterns), but it's a Jupyter notebook — instantly hostile to a People-Ops lead. This course wins on three dimensions that vendors don't currently serve: (1) **persona-appropriate affordance** (claude.ai + doc editor only, capstone-level), (2) **realistic Monday pressure** (the M4 simulator with focus tokens and scheduled interruptions is novel — neither Anthropic nor OpenAI ship anything like it in free content), and (3) **team-artifact deliverable** with a meta-adaptation guide. Where vendor tutorials still win: breadth of model-behavior examples and integration with real APIs. For a 200-person non-coder rollout, those advantages don't matter.

If I had to place it on a map: this sits roughly where a paid Maven cohort would charge $300-500/seat, with 80% of the value. The rigor of the grader especially lifts it above what I'd expect from a $49 Udemy non-coder course.

---

## Walkthrough log

### M0.S1 — "What this course is (and deliberately isn't)" [CONCEPT]
- "Reality check: 6+ hours/week lost." Team-multiplier framing, not individual productivity.
- Explicit "NOT" list: no code, no CLI, no API, no transformer theory. Sets the contract.
- BEFORE/AFTER interactive demo; learner can toggle Show Prompts / Show Outputs.

### M0.S2 — "Monday 9am: which task wins?" [SCENARIO, 2 decisions]
- Concurrent pressure: 12 inbox + Marcus Chen board-talking-points ask + Priya's onboarding checklist.
- D2 only reveals after D1 answer. "Marcus responds: can you make this repeatable?" → Document the template / Offer to draft weekly / Share Claude link. Frames team-multiplier correctly.

### M1.S1 — "Prompt engineering is a skill, not a vibe" [CONCEPT]
- SPEC framework introduced: Specificity / Examples / Constraints / Escalation. Each dimension with applied example on board-talking-points use case, including escalation ("Flag if any metric needs board approval").

### M1.S2 — "DELEGATE / PAIR / NEVER-DELEGATE" [CATEGORIZATION drill]
- 8 tasks render (title says 15). Realistic mix: harassment complaint, performance-improvement plan, hire decision, 847-ticket feedback synthesis, interview question generation.
- Category framework tied to risk level (Low/Med/High).
- Empty submission → `Score: 0% (0 of 8 correct). 2 more retries before the full breakdown reveals.` — respectful gradebook.

### M1.S3 — "Two prompts, same task — explain why one works" [READ REFERENCE + rubric]
- Weak-vs-GREAT weekly status prompt example. GREAT prompt is the same 6-slot template from M0, with disambiguated notes ("3 clients" → "TechFlow, DataCorp, CloudInc"), explicit audience (CEO + VPs), and tone slot.
- **Weak submission**: "it has more detail and is more specific" → `Score: 20%` with rubric-backed critique.
- **Strong submission**: identified audience/goal/format explicitly. **P1 UX bug**: feedback display cached on re-submit.

### M1.S4 — "Time your BEFORE baseline" [FILL IN BLANKS] — **P0 DRIFT**
- Premise right. UI wrong: Python dict/f-string syntax (`task_name = ""`, `weekly_time_cost = minutes_taken * {'daily': 5, ...}[frequency]`, `print(f"...")`). Violates "no code" positioning.

### M1.S5 — "The CEO's 20-minute Monday ask" [SCENARIO, 2 decisions]
- 20-minute pressure with 2 hours of scattered notes + CEO attention. Good 3 options spanning vague prompt vs structured vs manual.

### M2.S1 — "Confident and wrong: how LLMs fabricate" [CONCEPT]
- "The $2.3M Board Meeting Disaster" narrative.
- **5 Red Flags Checklist**: specific numbers without sources, recent dates/events (training cutoff), internal company details, competitor intelligence, "according to recent studies."
- **The Marcus Chen Rule**: "If this number is wrong, who gets fired?" — the right mental model.

### M2.S2 — "Kelvingrove Corp: flag the fabrications" [CATEGORIZATION drill]
- 8 facts rendered about fictional SaaS co (title says 15). Mix: grounded product-space statements vs fabricated "raised $23.5M Series B led by Horizon Ventures" / "ARR grew $47.2M → $73.8M" / "NRR peaked at 127%" / "churn dropped to 3.2% monthly" type hallucinations. Detection-as-skill, not awareness.

### M2.S3 — "The benchmark stats your exec wants to quote" [SCENARIO, 2 decisions]
- Claude produces 4 specific stats for Acme Corp. Pick your move. D2 traps the "Claude said industry analysis" fallback — the right answer is "tell Marcus you need 30 minutes to verify." Excellent.

### M2.S4 — "Your personal 'before I ship this' checklist" [FILL IN BLANKS] — **P0 DRIFT**
- Again Python: `personal_checklist = { "": "", ... }` dict. Premise good (5-line personal gate covering stat_verification / stakeholder_fit / format_check / tone_check / escalation_trigger). Form UI would do it.

### M3.S1 — "Anatomy of a production prompt" [CONCEPT]
- 6-slot template introduced: AUDIENCE / GOAL / FORMAT / EXAMPLES / CONSTRAINTS / ESCALATION. Ties to SPEC from M1.
- Case: Priya's weekly update 30-min → 5-min.

### M3.S2 — "Build the weekly-status template: fill the 6 slots" [FILL IN BLANKS]
- Pure markdown template — **no Python drift**. Good format.

### M3.S3 — "Your template missed 2 wins — how do you fix it?" [SCENARIO, 2 decisions]
- Realistic iteration scenario: template missed $15K vendor renegotiation + cross-team onboarding-template adoption. D1 = Manually add / Update CONSTRAINTS (wins taxonomy) / Update FORMAT (require Key Wins section). D2 = ESCALATION trigger for missing-wins categories. Teaches template-iteration discipline.

### M3.S4 — "Iterate a prompt from meh to ship-quality: order the loop" [ORDERING]
- 6 steps to sequence: test → diagnose delta → add context/role → add example → add constraint/negative example → re-test. Minor bleed: "like editing a document or debugging code" — drop the debugging half.

### M4.S1 — "Why inbox drift destroys most people's AI workflows" [CONCEPT + interactive]
- Focus Collapse demo: click "Start Workday" and watch Specificity / Context depth / Error checking degrade from High → Med → Low under interruptions. Nice kinesthetic setup.

### M4.S2 — "Monday 9am, 60 simulated minutes: work the inbox" [LIVE SIMULATION]
- 11 discrete actions with tick costs. Focus-token economy. Scheduled slack ping events. 60-tick budget.
- **Mid-drill screenshot captured** (20/60 ticks, 5 msgs completed, quality 41, 1 hallucination catch, 1 CEO email handled, focus 4). The mechanics feel like Monday-morning pressure, not a gamified quiz.
- **P0**: Event Stream entries rendered as raw JSON (`{"id":"ping_2","t_offset_ms":900000,"effect":{"focus_tokens":"- 1"}}`). Needs a plain-English renderer.

### M4.S4 — "Classify what went wrong in 6 of your drafts" [CATEGORIZATION]
- 6 AI drafts forwarded by Marcus with distinct defect types. Error taxonomy: HALLUCINATED / OFF-TONE / MISSED-STAKEHOLDER / FORMAT-WRONG / WRONG-ACTION / FINE-TO-SHIP. Good pattern-recognition drill. Items and title line up (no "15 but only 8 shown" issue here).

### M5.S1 — "Why sharing workflows multiplies impact" [CONCEPT + Template Adoption Simulator]
- Nexflow case: 6 people × 45 min → 6 × 15 min weekly after template adoption. 4 hours/week saved.
- Template adoption simulator with Week 0 → Week N propagation animation.

### M5.S2 — "Pick YOUR 3 tasks (the brief)" [FILL IN BLANKS] — **P0 DRIFT**
- Python again: `task_1_name = ""`, `task_1_current_time_minutes = `, incomplete `print(f"...")` f-string, literal `*` before a missing frequency multiplier. Capstone brief doesn't need code.

### M5.S3 — "Template 1: build it against your highest-frequency task" [FILL IN BLANKS]
- Pure markdown template with slot labels. Good format.

### M5.S5 — "Ship the Team Prompt Library doc" [CAPSTONE SYSTEM BUILD]
- **Deliverable**: markdown doc with 3 templates (goal / audience / format / example input / example output / time-saved measurement) + meta-adaptation guide (3+ paragraphs, not bullets) + HUMAN-VERIFY flags for numbers/compliance content.
- **Zero-code promise kept at capstone level**: "This capstone uses only claude.ai in your browser + a doc editor (Notion/Google Docs/plain markdown). No terminal, no GitHub, no deployments."
- **Weak submission** (3 one-liner templates): `Score: 5%. Doc rubric: 10%. 'write status updates' and 'write emails' are exactly the vague formulations the rubric warns against. No examples present. No adaptation guide. No hallucination warnings.`
- **Strong submission** (3 templates with real before/after times, HUMAN-VERIFY notes, 3-paragraph adaptation guide): `Score: 65%. Checklist 6/6. Doc rubric: 90% (threshold 70%). Specificity excellent. Measurement realism solid with concrete before/after like 42 min → 11 min. Examples concrete for Templates 1 & 2. Adaptation guide teaches well with the '6-slot structure' principle. Minor gap: Template 3's example output is abbreviated.` The phase-checkbox tracker (Structure/Draft/Validate/Publish) didn't auto-credit from the doc, dragging 90% doc score down to 65% composite — see P1 #6.

---

## What I did not walk (and why)
- M1.S4 Python syntax prevented me from submitting a clean baseline; I noted it as a ship-blocker rather than work around it.
- M2.S4 same reason.
- M4.S3 (colleague slack-ping Acme churn email scenario) — skipped due to tool-budget ceiling; the adjacent steps (M4.S1, S2, S4) were enough to verify the module's design intent.
- M5.S4 (Template 2: a differently-shaped task) — skipped; M5.S3 already showed the markdown-only UI pattern, and S5 is where the capstone rubric lives.
