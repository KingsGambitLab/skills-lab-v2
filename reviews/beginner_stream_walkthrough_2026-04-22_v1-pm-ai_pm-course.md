# Beginner Walkthrough — AI Power Skills for Product Managers: Ship Rigorous Strategy

**Date:** 2026-04-22
**Walker profile:** Intermediate PM (2-5 yrs) at B2B SaaS, first-time learner
**Course URL:** http://127.0.0.1:8001/#created-873f5b2fb62f
**Scope:** 9 modules x 4 steps = 36 steps (no code exercises)

---

## Course-wide structure probe (all 36 steps)

| Module | Title | Step 1 | Step 2 | Step 3 | Step 4 |
|---|---|---|---|---|---|
| M1 | AI Strategy Thought-Partner | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M2 | Prompt-Craft for PRDs | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M3 | User Research Synthesis | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M4 | Data Analysis + Bias Detection | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M5 | Experiment Design | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M6 | Competitive Intelligence | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M7 | Defending to VP Marketing | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M8 | Stakeholder Comm + Memos | CONCEPT | SCENARIO | CATEGORIZATION | ORDERING |
| M9 | CAPSTONE CFO Defense | CONCEPT | SCENARIO | CATEGORIZATION | SCENARIO |

**Total**: 9 CONCEPT · 10 SCENARIO · 9 CATEGORIZATION · 8 ORDERING = 36 steps.
**Zero ADAPTIVE_ROLEPLAY steps** in the entire course.

---

## Step 1.1 — "AI as Strategy Thought-Partner — Overview" — concept
- Briefing clarity: 5 | time on step: ~3 min | jargon level: low
- Named anchors: Elena Rodriguez (CEO), Nexus Analytics, churn prediction dashboard — concrete
- Core teaching: divergent vs convergent modes, three-layer verification check ("Is this plausible? Can I verify this independently? What would disprove this?")
- Hallucination example is specific: "ChurnGuard's 23% accuracy boost that doesn't exist"
- 1-sentence takeaway: divergent AI generates options, convergent AI must produce verifiable evidence; PMs who skip the three-layer check ship strategies on quicksand
- Verdict: PASSED — teaches an actual verification method, not a platitude
- UI notes: clean

## Step 1.2 — "AI Strategy Thought-Partner — Part 1" — scenario_branch
- Briefing clarity: 4 | time on step: ~2 min | jargon level: low
- Setup: Sarah Kim (VP CS) has team mixing divergent + convergent thinking in a meeting. You have 4 options.
- Attempt 1 (deliberate plausible-wrong): "David's right — let's just go with support ticket sentiment since we already have that data in Salesforce." This is the common PM trap of data-availability-driven picking.
  - Score: not shown. Step auto-advanced to Step 1.3 CATEGORIZATION with no feedback, no consequence narrative, no score.
  - Feedback verbatim: "" (none)
  - Did this help me? NO — I got marked complete but have no idea whether my pick was wrong, why, or what the better answer looked like.
- Verdict: PARTIAL — the setup is realistic but the grading is broken. Zero formative value for scenarios.
- UI notes: Header says "DECISION 1 OF 3" but the step only contains ONE decision — the "1 OF 3" label is misleading.

## Step 1.4 — "AI Strategy Thought-Partner — Part 3" — ordering
- Briefing clarity: 5 | time on step: ~4 min | jargon level: low
- Items: 5 real-world prompts mixing divergent + convergent workflow for ChurnGuard (Amplitude/Salesforce tech stack mentioned)
- Attempt 1 (deliberate reverse order: s5-s4-s3-s2-s1):
  - Score: 20% (1 correct, 4 wrong)
  - Feedback verbatim: "20% on this attempt. 2 more retries before the full breakdown reveals. 4 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Individual items color-coded (red = wrong, teal = right)
  - Did this help me? PARTIAL — item-level correctness is visible, but the feedback text is generic (no teaching about why "Verify via Amplitude docs" should come AFTER "Rank by feasibility"). Retries are gated on attempts.
- Attempt 2 (correct order s1-s2-s3-s4-s5): Score 100%, "Perfect ordering!"
- Verdict: PASSED — ordering is the strongest exercise type: colour-coded item-level feedback is a real learning tool.

## Step 3.2 — "User Research Synthesis — Part 1" — scenario_branch (hallucination detection)
- Briefing clarity: 5 | jargon level: low
- Setup: You have 47 pages of CS interview transcripts. Sarah needs themes by Friday. Goal: extract genuine insights without manufacturing fake quotes.
- Attempt 1 (deliberate plausible-wrong): "Upload all transcripts to Claude and ask it to 'find the key themes'". This is the exact trap the module is meant to teach.
  - Score: not shown. Auto-advanced to Part 2 CATEGORIZATION. No consequence narrative explaining why blind-dumping is risky.
  - Did this help me? NO — the content is the right topic but the lack of feedback means the learner can breeze through without learning.
- Verdict: PARTIAL — great scenario setup (47 pages, real PM time pressure, named stakeholder), zero grading/teaching on wrong answer.

## Step 4.0 — "Data Analysis + Bias Detection — Overview" — concept (hallucination-detection/bias pedagogy)
- Briefing clarity: 5 | jargon level: medium (intro uses "Simpson's Paradox", "survivorship bias", "selection bias", "p-hacking" explicitly)
- Teaching: named "Big 4 bias traps" + "prove it with a query" habit + "red-team your own analysis"
- Has an in-concept micro-demo: 847 customers / 8.2% churn vs 1203 customers / 15.7% churn — "What's the hidden bias?" (the answer is revealed via the ORDERING step later)
- Verdict: PASSED — this is genuine data-literacy pedagogy, not thin AI-wrapper. One of the strongest concepts in the course.

## Step 4.1 — "Data Analysis + Bias Detection — Part 1" — scenario_branch
- Setup: Jordan Martinez (Director of Product Analytics) Slacks "enterprise customers w/o API integrations are 3x more likely to churn (40% vs 13%) — we need to prioritize API features ASAP." Gotcha: analysis only covers last 6 months, API only available 4 months. Classic selection-bias confound.
- Attempt 1 (plausible-wrong): "Immediately escalate to Sarah Kim that we need API adoption campaigns."
  - Score: not shown. Auto-advanced.
- Verdict: PARTIAL — the scenario is genuinely well-crafted (realistic confound, named roles, specific numbers), but once again: no consequence narrative.

## Step 7.0 / 7.1 — "Defending to VP Marketing" — concept + scenario_branch
- **CRITICAL MISMATCH:** Module title says "Defending to a Skeptical **VP of Marketing**" but the SCENARIO body says you're defending to **Marcus Chen (CFO)**. This is a content bug — the wrong persona.
- Scenario Part 1: 3 canned multiple-choice responses. Options include one obvious-right ("Pull customer quotes + 23% false positive rate comparison") and two straw-men ("AI is the future", "Agree and add 20 widgets"). Plausible-wrong isn't plausible.
- Verdict: PARTIAL — title/content mismatch is a P1 bug; the decision-tree-as-conversation feels performative, not immersive.

## Step 9.0 — "CAPSTONE — Overview" — concept
- Briefing clarity: 5 | jargon level: medium
- Setup: $2M budget, 90 days, team of 4, Marcus Chen will grill you. Concrete challenge domains listed: TAM validation, competitive moat, resource allocation, timeline realism, ROI math.
- Explicit promise: "Defend vs Marcus (Live CFO)" — the flow diagram labels Step 5 as "LIVE CFO"
- Reality check: There IS no Step 5. The capstone has 4 steps: CONCEPT + SCENARIO + CATEGORIZATION + SCENARIO. Neither scenario is a live chat — both are 3-decision multiple-choice branches.

## Step 9.1 — "CAPSTONE — Part 1" — scenario_branch
- Setup: Marcus Chen challenges $180K budget for "unproven AI feature", ROI math
- Options include the well-crafted right answer ("Present revenue-at-risk: 12% churn = $2.4M lost ARR/yr; 2pp reduction saves $400K = 2.2x ROI year 1")
- Not live chat. Three canned options. Auto-advance on click.

## Step 9.3 — "CAPSTONE Exercise" — scenario_branch
- Setup: Launch day. Marcus challenges ROI. Sarah's team reports 73% AI accuracy (not 85% promised). Elena wants proof of no alert fatigue. 30-min meeting.
- Realistic PM scenario — 73% accuracy vs promise is a real live-wire
- But still canned multiple-choice. Not roleplay.

## UI/UX issues observed
1. **Clicky chat auto-opens** on clicking "Previous" button — intrusive and covers exercise content.
2. **"Previous" jumps across modules** unpredictably — tried to go back from M1.3 and landed in M2.
3. **Hamburger sidebar toggle is jammed** at times — clicking it seems to leave the sidebar permanently expanded.
4. **scenario_branch auto-advance** happens on any click, with NO feedback banner shown — no score, no consequence narrative, no explanation of why an answer is right or wrong.
5. **"DECISION 1 OF 3" label** on single-decision scenarios is misleading.
6. **M7 title/body mismatch** — VP Marketing vs CFO.
7. Clicking a scenario option sometimes navigates to an unrelated module — observed jumping from M4 Part 1 scenario_branch click to M6 Part 1, then to M7, then to M9. Routing after click is non-deterministic.

---

## Tally (partial walk — 6+ steps across 5 modules sampled)

| Exercise type | Passed | Partial | Stuck |
|---|---|---|---|
| concept (x3 sampled: M1, M4, M9) | 3 | 0 | 0 |
| scenario_branch (x5 sampled: M1, M3, M4, M7, M9) | 0 | 5 | 0 |
| categorization (x0 graded — drag-drop with no programmatic submit verified) | - | - | - |
| ordering (x1: M1) | 1 | 0 | 0 |

---

## Extra-check verdicts

### 1. PM craft depth vs AI-thin-wrapper
**Verdict: GOOD — in concepts, weak in scenarios.**

Concepts teach real PM discipline: three-layer verification heuristic, "prove it with a query" habit, Big-4 bias traps (Simpson's/survivorship/selection/p-hacking), verification-first prompting with examples, red-teaming your own strategy. These are not thin-wrapper "copy this prompt into ChatGPT" content — they're defensible rigor frameworks.

But the SCENARIO exercises don't reinforce the concepts: they ask a single multiple-choice question and auto-advance. So the rigor taught in the concept briefing doesn't get practiced.

### 2. Scenario framing quality
**Verdict: VERY GOOD.**

Scenarios are specific and realistic: named stakeholders (Elena Rodriguez/CEO, Marcus Chen/CFO, Sarah Kim/VP CS, Jordan Martinez/Dir Product Analytics, David Thompson/Sales Ops), named company/product (Nexus Analytics, ChurnGuard), concrete numbers ($2.4M ARR lost, $180K budget, 73% accuracy vs 85% promised, 47 pages of transcripts, 40% vs 13% churn confound with 6-month/4-month timing trap). No generic "your PM team needs to decide..." framing.

### 3. Wrong-answer teaching
**Verdict: FAIL — the critical pedagogy gap.**

On scenario_branch steps, choosing any option (right OR plausible-wrong) auto-advances with no feedback banner, no score, no consequence narrative. The learner cannot tell if they picked the right answer, and more critically, cannot learn from picking the wrong one. This is the worst pedagogical failure in the course — because the scenario setups are genuinely good, the missed learning is high-signal.

Ordering exercises DO give per-item color-coded feedback + score + retry count. This is where the course's pedagogy actually works.

### 4. Capstone (Module 9) — defend to hostile CFO
**Verdict: WATERED-DOWN.**

exercise_type = scenario_branch (standard multiple-choice with 3 canned options per decision).

It is NOT an immersive roleplay. The overview page explicitly promises "Defend vs Marcus (Live CFO)" as Step 5, but no Step 5 exists — the capstone has only 4 steps (CONCEPT, SCENARIO, CATEGORIZATION, SCENARIO). Neither of the two SCENARIO steps is a live chat.

The content of each canned option is realistic PM work (good revenue-at-risk math in option 1 of Part 1), but the ceremony of "defending under hostile questioning" is performed by picking a pre-written defense out of three — not by composing a response and getting pushback.

### 5. Missing adaptive_roleplay check (M7 and M9)
**Verdict: CONFIRMED MISSING.**

Probed all 9 modules x 4 steps = 36 steps. Exercise types found: CONCEPT, SCENARIO, CATEGORIZATION, ORDERING. Zero adaptive_roleplay / roleplay exercises anywhere in the course. Both defense modules (M7 VP Marketing defense, M9 CAPSTONE CFO defense) use ordinary scenario_branch. The immersive-feeling "defend to stakeholder" promise is consistently framed but never delivered. Additionally, M7's title mentions **VP of Marketing** but the body defends against **Marcus Chen (CFO)** — a content authoring bug.

### 6. AI-hallucination-detection pedagogy (M1 + M4)
**Verdict: GOOD in concepts, WEAK in exercises.**

M1 concept: Names the "three-layer check" (plausible / independently verifiable / what would disprove?) with a concrete fabricated-citation example ("ChurnGuard's 23% accuracy boost that doesn't exist").

M4 concept: Names the "Big 4 bias traps" (Simpson's Paradox, survivorship, selection, p-hacking) + teaches "prove it with a query" habit + includes an interactive bias-spotting demo with real numbers (847/8.2% vs 1203/15.7% — hidden confound).

So the course DOES teach specific verification methods — not just "watch for hallucinations." But because the scenario_branch exercises don't give feedback on wrong picks, the bias-detection workflow never gets practiced rigorously in the exercises. The M3 User Research Synthesis scenario ("upload all transcripts and ask for themes" is the trap option) is exactly the moment where consequence feedback would teach the hallucination skill — and it's empty.

---

## Beginner-hostile issues

1. **No scenario_branch feedback** — learner cannot tell right from wrong on ~10 of 36 steps (28% of the course).
2. **Clicky chat auto-opens** on Previous clicks and covers the exercise.
3. **Navigation is unpredictable** — clicking scenario options sometimes jumps to a different module than expected.
4. **M7 title/body mismatch** (VP Marketing vs CFO) — content bug that breaks trust.
5. **Single-decision scenarios labeled "DECISION 1 OF 3"** — the UI implies a decision tree that doesn't exist.
6. **Capstone's "Live CFO defense"** promise is broken — the flow diagram advertises a Step 5 that doesn't exist.
7. **Clicky's "won't give exercise answers" guardrail** is interesting but never tested here — if learners can't see why they were wrong, they'll go ask Clicky, which refuses to help.

---

## Final Verdict: CONDITIONAL ⚠

**Reasoning:**
The course has genuinely strong concept pedagogy — named characters, specific numbers, real PM scenarios, rigor frameworks (three-layer check, Big-4 biases, verification-first prompting, red-teaming). Content depth is legitimately higher than "copy-paste-a-prompt" courses.

But three structural problems make it not-yet-shippable:
1. **scenario_branch auto-advance with no feedback** destroys the teaching value of ~10/36 steps (the most common exercise type).
2. **No adaptive_roleplay** anywhere, despite M7 and M9 advertising live stakeholder defense — the capstone flow diagram promises a step that doesn't exist.
3. **M7 title/body mismatch** (VP Marketing vs CFO) is a P1 authoring bug.

**What needs to happen before approve:**
- [ ] Add consequence narrative + score display on scenario_branch steps (per-option teaching blurb after click)
- [ ] Replace M7 and M9 SCENARIO exercises with adaptive_roleplay (live chat) to match course framing
- [ ] Fix M7 title/body mismatch (decide: VP Marketing OR CFO, align both)
- [ ] Fix "DECISION 1 OF 3" label when only one decision exists
- [ ] Fix Previous-button navigation (should go back one step, not jump modules)
- [ ] Prevent Clicky auto-open on navigation

**Once those are in, this is a strong course.** The concept-level content is genuinely 10x over "AI for PMs" content elsewhere. Ship once the feedback loop is wired.
