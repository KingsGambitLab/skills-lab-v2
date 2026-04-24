# Domain-Expert Review — AI Power Skills for Product Managers
Persona: VP of Product (15 years, B2B SaaS scale, mentors junior PMs, shipped 150+ PRDs)
Date: 2026-04-22
URL reviewed: http://127.0.0.1:8001/#created-873f5b2fb62f

## Overview

Nine-module course (9 × 4 = 36 steps) structured around a single recurring scenario: Nexus Analytics' "ChurnGuard" AI-powered churn prediction dashboard. Every module follows an identical 4-step pattern: `concept → scenario_branch → categorization → ordering`. Exercise type distribution is 9/9/9/9 (one of each per module). The course is narratively coherent — the Elena Rodriguez / Marcus Chen / Sarah Kim / Aisha Patel / Jordan Martinez / David Thompson cast reappears in every module, giving learners continuity of context.

The capstone (Module 9: "Ship a Real Strategy Doc and Defend It to a Hostile CFO") follows the same 4-step pattern — it is NOT a live adaptive_roleplay with a CFO, despite Module 8's copy promising "realistic adaptive roleplays with hostile executives." The capstone is a sequence of scenario_branch decisions + categorization + ordering. That is the structural story of this course: narratively ambitious, content-rigorous, but pedagogically fixed to a single decision-tree modality across all 9 modules.

## Blind-spot coverage

### Blind spot 1 — "AI-rigor vs AI-dependency: does the course teach validating AI outputs?"
- Covered? **yes (strong)**
- Evidence:
  - Step 1.1 ("AI Strategy Paradox") opens with "half the 'facts' are hallucinated" and introduces a **three-layer check**: "(1) Is this plausible? (2) Can I verify this independently? (3) What would disprove this?"
  - Step 2.1 opens with a **career-ending story** of a PM fired because every customer quote in an AI-drafted PRD was fabricated.
  - Step 2.2 decision 3 explicitly chooses "Ask Jordan Martinez (Director of Product Analytics) what Amplitude's current data pipeline latency actually is" OVER "Prompt Claude: 'Is 4-hour data freshness realistic?'" — the course correctly teaches SME validation over asking AI to check its own work.
  - Step 2.4 (ordering) includes the explicit step "Cross-validate AI-generated technical claims against actual Amplitude and Salesforce documentation to catch hallucinations."
  - Step 3.1 names three failure modes: "Phantom Quotes", "Theme Hallucination", "Lost Traceability."
- Verdict: This is the strongest dimension of the course. A junior PM who genuinely absorbs this material would not ship AI-fabricated claims.

### Blind spot 2 — "Divergent vs convergent AI use"
- Covered? **yes (strong)**
- Evidence:
  - All four steps of Module 1 are devoted to this distinction.
  - Step 1.1 defines it explicitly (Divergent = generate options, brainstorm angles; Convergent = validate claims, choose best option, evidence gathering).
  - Step 1.3 (categorization) forces learners to classify 6 real PM scenarios across THREE buckets: Divergent / Convergent / **Mixed (both needed)** — the "Mixed" category prevents the naive binary.
  - Step 1.4 (ordering) requires learners to sequence a full strategy workflow that alternates between modes.
  - Module 2 reinforces with concrete prompt examples for each mode.
- Verdict: Explicit, repeated, and operationally useful. A VP-level distinction taught early.

### Blind spot 3 — "PRD craft depth: does Module 2 teach elements that survive hostile engineering review?"
- Covered? **yes (strong)** with one gap
- Evidence:
  - Step 2.1 names: "Verification-First Prompting", "Red-Team Discipline", "Evidence Trails: every claim can be traced back to a real source", "Stakeholder Stress-Testing."
  - Step 2.2 decision 2: learner must choose to "Red team this PRD. What would a skeptical VP Engineering say are the 3 biggest implementation risks?" over accepting AI output verbatim.
  - Step 2.3 (categorization) uses three genuine engineering-review failure modes: **Feasibility Killers** (e.g., "99.7% accuracy using existing data"), **Scope Creepers** (e.g., vague "drill down into any customer metric"), **Spec Gaps** (e.g., "Salesforce sync" without API endpoints). These are real fault patterns.
- Gap: Kill criteria and explicit tradeoffs sections of a Doshi/Cagan-style PRD are not named. "Failure modes" are covered only as engineering objections, not as "if X happens, we kill this." The explicit Shreyas Doshi PRD template (Problem → Why Now → Solution → Risks → Kill criteria → What we won't do) is not drilled.
- Verdict: Strong on rigor-under-AI, adequate on PRD craft, missing the explicit kill-criteria/non-goals element.

### Blind spot 4 — "User-research rigor: how to RUN an interview vs AI synthesis"
- Covered? **partial**
- Evidence:
  - Step 3.1 hits the synthesis side HARD: three-layer verification (Extract → Verify → Defend), timestamp + speaker ID traceability, anti-phantom-quote discipline.
  - Step 3.2 (categorization) correctly teaches signal-strength triage — vague impressions ("seem less likely") vs verbatim multi-source ("three separate CS managers mentioned they spend 2-3 hours weekly") vs single-anecdote ("a few cases from last quarter").
  - Step 3.3 (ordering) sequences: extract verbatim → cluster → AI theme draft → cross-reference with Amplitude/Salesforce behavioral data → present with confidence levels.
- Gap: There is NO content on **running** the interview itself. No mention of open-ended questions, probing follow-ups ("tell me more about that", the 5-whys), verbatim capture during the session, or even the Mom Test. The course assumes transcripts already exist. A junior PM trained on this module would be excellent at SYNTHESIS but still run shallow interviews.
- Verdict: Half the craft. The AI-synthesis half is world-class; the interview-running half is simply absent.

### Blind spot 5 — "Bias-literate data analysis (Simpson's paradox, survivorship, selection, p-hacking)"
- Covered? **yes (very strong)**
- Evidence:
  - Step 4.1 explicitly names the "Big 4": **Simpson's Paradox, survivorship bias, selection bias, p-hacking**.
  - Step 4.2 scenario: PM suspects bias in a churn analysis because API integrations didn't EXIST for part of the observed period (textbook survivorship + timing bias). Decision 2's correct answer literally says "The original analysis suffered from survivorship bias — customers without API access never had the chance to use it."
  - Step 4.3 (categorization) provides 8 scenarios across 4 bias types. The Simpson's Paradox items are LEGITIMATE cohort inversions: "customers using Feature X have higher retention overall, but when segmented by company size, Feature X actually correlates with higher churn in both small and large customer segments." This is textbook Simpson.
  - Step 4.4 (ordering) sequences bias-testing as a named step: "Test for common biases: Simpson's Paradox by examining subgroup breakdowns, survivorship bias by including churned customers."
- Verdict: Rivals what you'd find in an applied econometrics / behavioral economics module. One of the strongest data-literacy modules I've seen in a PM course. Only missing: p-hacking gets named but not deeply drilled with a concrete A/B-test-reversal example.

### Blind spot 6 — "Competitive analysis reality: real intel sources vs scraping marketing pages"
- Covered? **yes (strong)** with one ethics wrinkle
- Evidence:
  - Step 6.1 explicitly distinguishes **Information vs. Intelligence** ("TechFlow's pricing page lists enterprise features A, B, C" is information; "TechFlow's enterprise deals take 8+ months because their integration team is understaffed" is intelligence).
  - Step 6.1 calls out that "marketing pages tell you what companies want you to believe, not what they actually do" and explicitly flags AI hallucination in competitive-analysis mode.
  - Step 6.2 decision 1 correctly prioritizes "Ask David Thompson (Sales Ops) to pull **lost-deal reports** and schedule calls with the Account Executives who handled these specific losses" over "Use Claude to scrape competitor websites."
- Concern: Step 6.2 decision 2 offers as an option "Create fake enterprise buyer personas and request demos from these competitors to see their actual product capabilities." This is misrepresentation — a real ethics issue in competitive intelligence. I could not verify which option the course marks correct without completing the exercise. If the course endorses this, that is a responsibility red flag. I'd want the Creator team to confirm this is flagged as a WRONG answer.
- Gap: Analyst briefings (Gartner/Forrester/G2), ex-employee intel, and earnings-call transcripts as signal sources are not drilled. Lost-deal reviews and AE calls are the only named-correct source.
- Verdict: Good on the fundamental distinction, adequate on sources, one concerning option needs clarification.

### Blind spot 7 — "Stakeholder realism (Module 7): is Defend-to-VP-Marketing an adaptive roleplay or a decision tree?"
- Covered? **partial (this is the weakest pedagogical dimension)**
- Evidence:
  - Module 7 concept (step 7.1) is excellent: names "Three Layers of Positioning Defense" — Evidence Foundation, Assumption Transparency, Real-Time Adaptation. The real-time adaptation framing ("If DataVault launches enterprise pricing in Q2, we pivot to SMB") is sophisticated.
  - Step 7.2 is labeled **"🎯 SCENARIO"** — i.e., scenario_branch. Learner picks from 3 pre-written responses. The "right" option (show specific customer quotes + 23% false positive rate vs our 8%) IS rigorous content, but the learner RECOGNIZES it, never GENERATES it.
  - Steps 7.3 and 7.4 are categorization + ordering. No free-form push-back chat anywhere in the module.
- Gap: Module 8.1 copy explicitly promises "realistic adaptive roleplays with hostile executives." This is not delivered. Module 8.2, 8.3, 8.4 are all scenario/categorization/ordering too.
- Verdict: The CONTENT of what a good defense looks like is taught well. The MODALITY (pick-from-3 vs generate-under-pressure) is a fraction of the real skill. A junior PM can ace this and still freeze in a real Marcus Chen grilling because they've never been forced to produce a defense on their own.

### Blind spot 8 — "Capstone immersion: Module 9 Defend-to-CFO — does it TEST rigor or just reward confidence?"
- Covered? **partial**
- Evidence:
  - Step 9.1 concept is strong. The explicit rubric is "you'll be graded on strategy rigor, not strategy content. Two PMs might recommend different market approaches — the one who survives Marcus's grilling is the one who sources every claim, acknowledges risks upfront, defends with evidence, adapts to pushback."
  - Step 9.2 exercise type: **🎯 SCENARIO** (scenario_branch). Decision 1: learner picks from 3 options defending a $180K budget. The rigorous option (revenue-at-risk math: "12% annual churn = $2.4M lost ARR; even a 2pp reduction = $400K/year = 2.2x ROI year one") IS the right-labeled answer.
  - Step 9.3: **📁 CATEGORIZATION** — triage 8 realistic CFO objections (ROI assumption, POC demand, timeline realism, causal attribution, data quality gaps, team allocation, competitive moat, market premise) by severity. This is genuinely useful content.
  - Step 9.4: **🎯 SCENARIO** again. Launch-day defense with "Our model is 73% accurate, not the promised 85%" — the correct option presents comparative analysis (73% AI vs 45% manual baseline) rather than the weak "AI improves over time" hand-wave. This IS testing rigor.
- Critical gap: The capstone is NOT a live adaptive chat. It's a 4-step decision tree. There is no moment where the learner must GENERATE their own response to an unpredictable CFO follow-up. The CFO doesn't actually adapt to the learner's chosen path. Does the capstone test rigor? Marginally — the right-labeled options do reward rigor. Does the capstone SIMULATE defending under pressure? No.
- Additionally concerning: There is no "fabricated data claim in the PRD → CFO catches it → learner scored low" failure mode in what I reviewed. The scenarios present data honestly; they don't tempt learners into shipping a lie and then punish them for it.
- Verdict: Rigor is taught IN the correct-answer text but not tested as a live defense skill. The capstone reads more like an open-book exam than a ship-and-defend exercise.

### Blind spot 9 — "Ethics + responsibility (bias, fairness, consent, PII in prompts, prompt-hygiene)"
- Covered? **partial — skewed**
- Evidence:
  - Bias (cognitive and analytical): extensively covered in Module 4. Confirmation bias, selection bias, survivorship bias, Simpson's paradox all named and drilled.
  - Hallucination awareness: threaded throughout all 9 modules.
  - Research transparency: Step 3.1 decision 4 teaches "Clearly mark which insights came from AI analysis vs. your manual review" — this is a responsibility-posture win.
- Gap (significant):
  - **PII in prompts**: zero mentions. No teaching about scrubbing customer data before pasting into Claude/ChatGPT. No mention of enterprise tier vs. consumer tier data-retention differences. For a course training PMs to paste real customer interview transcripts and Salesforce data into AI, this is a meaningful omission.
  - **Consent / fairness for AI-assisted features** (what happens when your AI churn model misclassifies an enterprise account and CS stops reaching out?): not discussed as an ethics issue, only as a "trust calibration" UX issue in Module 5.
  - **Prompt injection / secrets hygiene**: zero mentions. A PM deploying a customer-facing AI feature needs to understand this.
- Verdict: Half the responsibility surface is covered brilliantly (cognitive bias, research integrity, hallucination). The other half (data handling, fairness consequences, prompt-injection) is absent.

### Blind spot 10 — "Production cost / ops awareness (token cost, latency, cache, fallback, unit economics)"
- Covered? **no**
- Evidence:
  - Across all 9 module overviews (~36k chars), my grep for "token | cost | latency | cache | fallback | rate limit | unit economics | throughput" surfaced ONE total match — and it was the word "cost" in a financial-ROI context, not in a token-economics context.
  - Module 5 (Experiment Design + Launch Readiness) is the natural home for this content and does not contain it. "Launch readiness" is framed as user trust + engineering debuggability + stakeholder alignment — not as "what does a Claude API call cost per user per day."
  - No mention of model selection tradeoffs (Haiku vs. Sonnet vs. Opus per use case), no mention of caching strategies for reducing re-computation, no mention of graceful degradation when the model provider is down.
- Verdict: A PM who finishes this course will write a convincing PRD for an AI feature and defend it to the CFO — and then discover at launch that the unit economics don't work because they never modeled token cost per request × DAU. This is the single biggest content omission for a course aimed at PMs who will spec AI features in production.

## Axis scores

- **rigor_under_ai: 0.88**
  Evidence: three-layer check (Step 1.1), career-ending hallucination opener (Step 2.1), SME-validation preferred over AI-self-check (Step 2.2 D3), explicit cross-ref to real API docs (Step 2.4), three-layer synthesis verification (Step 3.1), big-4 bias naming + correct Simpson's examples (Module 4). Rigor teaching is excellent. Minor deduction: the scenario_branch modality means learners recognize rigor but never have to generate it under adaptive pressure.

- **real_user_contact: 0.55**
  Evidence: synthesis rigor is world-class (Module 3.1-3.3), but the interviewing CRAFT is completely absent — no teaching of open-ended questions, probing follow-ups, verbatim capture, the Mom Test, or how to avoid leading questions. A PM leaving this course runs shallow interviews and then synthesizes them beautifully. Heavy deduction for the missing half of the pipeline.

- **stakeholder_realism: 0.55**
  Evidence: content of a good defense (Three Layers in 7.1, 8 realistic CFO objections in 9.3) is strong. But every stakeholder module is scenario_branch — pick-from-3 rather than generate-under-pressure. Module 8.1 PROMISES "realistic adaptive roleplays with hostile executives" and does not deliver. This is the biggest structural gap.

- **decision_quality_framework: 0.78**
  Evidence: RICE-style prioritization in Step 1.2 D2 ("rank by data availability, engineering complexity, potential impact"), signal-strength triage in Step 3.2 (high/medium/low confidence buckets), severity triage in Step 9.3 (critical/high/medium objections), trust-calibration framing in Module 5. The course consistently pushes evidence-weighted decisions. Minor deduction: no explicit ICE/RICE/North-Star naming, no Doshi "bets/risks/tradeoffs" template.

- **responsibility_posture: 0.55**
  Evidence: bias + hallucination coverage is best-in-class. Research transparency ("mark AI-assisted insights") is taught. But PII in prompts, consent, fairness-in-AI-decisions, prompt-injection / secrets hygiene are entirely missing. For a 2026 PM course, this is a material gap.

- **craft_depth: 0.70**
  Evidence: PRD engineering-review failure modes (Step 2.3) are real. Bias examples (Step 4.3) are textbook-correct. Competitive intel vs. information distinction (Step 6.1) is mature. Deduction: every module ends in ordering + categorization exercises, which test recognition not generation, so the learner never writes their own PRD / interview guide / strategy doc. The capstone is named "Ship a Real Strategy Doc" but the deliverable is not drafted by the learner in any step I could access.

## Weighted score

| axis | weight | score | weighted |
|---|---|---|---|
| rigor_under_ai | 0.25 | 0.88 | 0.220 |
| real_user_contact | 0.20 | 0.55 | 0.110 |
| stakeholder_realism | 0.15 | 0.55 | 0.0825 |
| decision_quality_framework | 0.15 | 0.78 | 0.117 |
| responsibility_posture | 0.15 | 0.55 | 0.0825 |
| craft_depth | 0.10 | 0.70 | 0.070 |

**TOTAL: 0.682 / 1.00**

## Verdict

**⚠ CONDITIONAL APPROVE (0.682 = upper end of 0.60–0.74 band)**

This course has genuine teeth where it counts most: rigor under AI (0.88) and bias literacy (the strongest Module 4 I've seen in a PM course). I would NOT pull my PMs out of this course — the cognitive-bias + hallucination + PRD-engineering-review content is material my juniors need. But I will not approve enrollment at list price until the following MUST-FIX items are addressed:

### MUST-FIX (non-negotiable before team enrollment)

1. **Convert Module 9 capstone defense step (9.2 or 9.4) to a genuine adaptive_roleplay** where the learner TYPES their defense and Marcus Chen pushes back adaptively on weak claims. As-is, the capstone reads like an open-book exam, not a defense. Module 8 copy already promises this — make the promise true.

2. **Add a "fabricated claim catches the learner" failure mode** somewhere in the capstone. Give the learner a seeded-false AI-drafted stat, let them either catch it during prep or ship it into the CFO meeting, and score them accordingly. This is the only way to test rigor vs. confidence at the level the course advertises.

3. **Add a Module 3 step on RUNNING an interview** (open-ended questions, probing follow-ups, verbatim capture, the Mom Test, leading-question avoidance). As-is, the module teaches world-class synthesis of transcripts the learner never had to generate well.

4. **Add PII + prompt-hygiene + secrets handling** as either a new sub-section of Module 2 (PRD craft) or Module 5 (launch readiness). For a 2026 course training PMs to paste customer data into Claude, the absence is material.

5. **Clarify Module 6.2 Decision 2** — confirm that "create fake buyer personas and request competitor demos" is flagged as the WRONG (unethical misrepresentation) answer. If the course endorses this, it teaches bad professional behavior to juniors.

### SHOULD-FIX (quality improvements)

6. Add production cost/ops awareness to Module 5: token cost per request × DAU modeling, model-tier selection (Haiku vs. Sonnet vs. Opus), cache design, fallback strategy. PMs who spec AI features without this get ambushed in their first post-launch CFO meeting.

7. Add explicit Doshi/Cagan PRD structure (Kill criteria, Non-goals, Bets, Tradeoffs) as named elements, not just implicit in the categorization exercise.

8. Add a p-hacking concrete example (A/B test reversal or one-sided-p-value cherry-pick) to Module 4.3 — it's named in 4.1 but not drilled like Simpson's and survivorship are.

## One-line executive summary

**Rigor and bias-literacy content is best-in-class, but the course ships a decision-tree capstone where it advertises a live CFO defense — make the capstone a real adaptive_roleplay with a seeded-fabrication trap, add interview-running craft and PII/cost-ops coverage, and this becomes a team-wide enrollment; today it's a conditional yes at a discount.**
