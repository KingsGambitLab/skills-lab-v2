"""One-off script to patch the broken UX Research course (created-145855666162).

Fixes these gaps identified in the LMS audit:
- Step 125: concept intro has no <script> interactive widget
- Step 127: scenario_branch has no validation data
- Step 128: fill_in_blank has no validation.blanks
- Step 132: sjt has placeholder "Approach A/B/C" content
- Step 138: scenario_branch has no validation
- Step 139: system_build capstone is completely empty

Run: python3.14 backend/patch_ux_course.py
"""

import asyncio
from sqlalchemy import select
from backend.database import Step, async_session_factory


# Step 125: Interactive intro "Research Opportunity Detective"
STEP_125_CONTENT = """
<style>
.rop-demo { background: #1e2538; border: 1px solid #2a3352; padding: 24px; border-radius: 12px; color: #e8ecf4; font-family: -apple-system, sans-serif; }
.rop-demo h3 { color: #4a7cff; margin: 0 0 12px 0; }
.rop-hook { border-left: 3px solid #2dd4bf; padding: 12px 14px; background: rgba(45, 212, 191, 0.06); margin: 16px 0; border-radius: 0 8px 8px 0; }
.rop-hook strong { color: #2dd4bf; }
.rop-clue { background: #161b26; border: 1px solid #2a3352; padding: 12px 14px; margin: 8px 0; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 0.9rem; }
.rop-clue:hover { border-color: #4a7cff; transform: translateX(2px); }
.rop-clue.flagged { border-color: #2dd4bf; background: rgba(45, 212, 191, 0.08); }
.rop-clue.flagged::after { content: " ✓ flagged"; color: #2dd4bf; font-weight: 600; }
.rop-clue.misleading { border-color: #f87171; background: rgba(248, 113, 113, 0.08); }
.rop-verdict { margin-top: 20px; padding: 16px; background: #161b26; border-radius: 8px; display: none; }
.rop-verdict.show { display: block; }
.rop-btn { background: #4a7cff; color: white; border: 0; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 12px; }
.rop-btn:hover { background: #6190ff; }
</style>
<div class="rop-demo">
<h3>Research Opportunity Detective</h3>
<div class="rop-hook">
<strong>The $2M Mystery:</strong> StreamlineApp's CEO says "Build dark mode — our competitors have it." Engineering is skeptical. Before you commit 6 engineers for 3 months, what signals actually indicate a real research opportunity?<br><br>
<strong>Your task:</strong> Flag the 3 clues below that genuinely warrant research. Ignore the misleading ones.
</div>

<div class="rop-clue" data-signal="true" data-why="Behavioral evidence — actual user pain">
<strong>📊 Clue 1:</strong> 32% of users open settings, scroll through all options, then close without changing anything. Session recordings show hesitation on "Display" settings.
</div>
<div class="rop-clue" data-signal="false" data-why="Competitor-driven, not user-driven. Correlation ≠ causation.">
<strong>📈 Clue 2:</strong> Two competitors launched dark mode last quarter. Their app store ratings went up by 0.3 stars.
</div>
<div class="rop-clue" data-signal="true" data-why="Direct user voice — qualitative signal from support logs">
<strong>💬 Clue 3:</strong> Support tickets mention "too bright at night" 47 times in the last 90 days, up from 8 times the year before.
</div>
<div class="rop-clue" data-signal="false" data-why="Single stakeholder opinion is not evidence of user need.">
<strong>👔 Clue 4:</strong> The CEO's teenage kids told her they "can't use it on their phones at night."
</div>
<div class="rop-clue" data-signal="true" data-why="Segmented quantitative pattern — night-time engagement drop-off">
<strong>📉 Clue 5:</strong> Retention data shows a 18% drop-off specifically for sessions started between 9pm-6am on mobile devices.
</div>
<div class="rop-clue" data-signal="false" data-why="Technology trends don't equal user needs. Check if YOUR users care.">
<strong>🌐 Clue 6:</strong> 64% of all mobile apps have adopted dark mode by 2024 per TechCrunch report.
</div>

<button class="rop-btn" onclick="submitOpportunityClues()">Submit Your Flags</button>
<div class="rop-verdict" id="ropVerdict"></div>
</div>
<script>
(function(){
  document.querySelectorAll('.rop-clue').forEach(function(clue){
    clue.addEventListener('click', function(){
      this.classList.toggle('flagged');
      document.getElementById('ropVerdict').classList.remove('show');
    });
  });

  window.submitOpportunityClues = function(){
    var clues = document.querySelectorAll('.rop-clue');
    var flagged = 0, correctFlags = 0, wrongFlags = 0, missedSignals = 0;
    clues.forEach(function(c){
      var isSignal = c.dataset.signal === 'true';
      var isFlagged = c.classList.contains('flagged');
      if(isFlagged) flagged++;
      if(isSignal && isFlagged) correctFlags++;
      if(!isSignal && isFlagged){ wrongFlags++; c.classList.add('misleading'); }
      if(isSignal && !isFlagged) missedSignals++;
    });

    var v = document.getElementById('ropVerdict');
    v.classList.add('show');
    if(correctFlags === 3 && wrongFlags === 0){
      v.innerHTML = '<strong style="color:#2dd4bf;">Perfect investigator!</strong> You flagged exactly the 3 evidence-based signals (behavioral data, user voice, engagement patterns) and ignored the competitor-watching, single-stakeholder, and industry-trend noise. <br><br>These are the 3 signal categories real researchers look for: <em>quantitative patterns, qualitative voice, and segmented behavior</em>. The rest is noise that drives WRONG research.';
    } else {
      var reveal = '<strong style="color:#fbbf24;">Close, but let us review:</strong><br><br>';
      clues.forEach(function(c, i){
        var sig = c.dataset.signal === 'true';
        reveal += '<div style="margin:6px 0;"><strong>' + (sig ? '✓ SIGNAL' : '✗ NOISE') + ':</strong> Clue ' + (i+1) + ' — ' + c.dataset.why + '</div>';
      });
      reveal += '<br>The 3 real signals were clues 1, 3, and 5. They share a pattern: <em>behavioral evidence from YOUR users</em>, not opinions or competitor moves.';
      v.innerHTML = reveal;
    }
  };
})();
</script>
"""

# Step 127: scenario_branch "Stakeholder Resistance Navigator" — add validation
STEP_127_DEMO_DATA = {
    "scenario": "You're presenting findings that show users struggle with the payment confirmation flow, but the VP of Product interrupts: 'We've already invested 6 months in development. Our competitors are launching similar features next quarter. Can't we just fix these issues post-launch?' The Engineering Lead adds, 'Every research cycle adds 2 weeks to our timeline.'",
    "steps": [
        {
            "question": "How do you respond to the VP's 'fix it post-launch' framing?",
            "options": [
                {"label": "Show the cost of fixing usability bugs post-launch vs. pre-launch (industry data: 10-100× more expensive) with one relevant case study from a similar fintech product.", "correct": True, "explanation": "Best: reframes the trade-off in the language the VP cares about (ROI/time) using evidence."},
                {"label": "Agree to ship and document the usability risks in a follow-up doc for later.", "correct": False, "explanation": "You've become a check-the-box researcher. Findings ignored = no impact."},
                {"label": "Escalate to the VP's manager to override the decision.", "correct": False, "explanation": "Nuclear option. Burns the relationship before you've actually engaged on their constraints."},
                {"label": "Redo the research with more users to make the finding 'stronger'.", "correct": False, "explanation": "Research isn't being questioned — priorities are. More data won't change that."},
            ],
        },
        {
            "question": "The Engineering Lead argues research delays ship dates. Your best counter?",
            "options": [
                {"label": "Offer a RITE-style (Rapid Iterative Testing) week-long study that runs PARALLEL to dev, with fixes shipped weekly. Show how this prevents the bigger rework cost.", "correct": True, "explanation": "You solve their constraint (timeline) with a lighter method. Collaborative, not adversarial."},
                {"label": "Argue the research is non-negotiable and required for launch approval.", "correct": False, "explanation": "Appeals to authority turn research into a compliance checkbox. Lose trust."},
                {"label": "Suggest dropping research entirely for this cycle and resuming after launch.", "correct": False, "explanation": "Gives up your role. You'll be excluded from future sprints too."},
                {"label": "Propose moving the launch date by 2 weeks.", "correct": False, "explanation": "Proposing to move dates first shows you don't understand the pressure they're under."},
            ],
        },
        {
            "question": "Three weeks later, launch is go. Post-launch metrics show 22% drop-off in payment confirmation. How do you follow up?",
            "options": [
                {"label": "Schedule a calm retrospective with the team: 'Here's what we predicted, here's what happened, here's what we'd do differently' — without 'I told you so'.", "correct": True, "explanation": "Builds credit. Next research request gets funded pre-emptively."},
                {"label": "Send a Slack message with 'Told you so — we predicted exactly this in our pre-launch report.'", "correct": False, "explanation": "Satisfying but destroys the relationship. You'll be cut out of the next project."},
                {"label": "Quietly update your LinkedIn and start looking for a new job.", "correct": False, "explanation": "Give up before using the situation to build credibility."},
                {"label": "Wait for leadership to notice the metrics and come to you.", "correct": False, "explanation": "Passive. Take the initiative to frame the narrative."},
            ],
        },
    ],
    "insight": "Research influence comes from speaking business language, offering flexible methods that fit team constraints, and building credibility with calm follow-through — not from being 'right'.",
}

# Step 128: fill_in_blank "Research Proposal Builder" — add validation.blanks
STEP_128_CODE = """# UX Research Proposal: Mobile Checkout Flow Optimization

# ── Research Question ─────────────────
# The ONE question this study will answer (specific, answerable, impactful)
primary_question = \"____\"

# ── Method ────────────────────────────
# Pick the method that matches the question and timeline
method = \"____\"  # e.g. usability-testing, interviews, survey, diary-study

# ── Sample ────────────────────────────
# How many participants and who?
sample_size = ____
participant_criteria = \"____\"

# ── Timeline ──────────────────────────
# Weeks from kickoff to final readout
duration_weeks = ____

# ── Success Metric ────────────────────
# How you'll know the research was worth doing
impact_metric = \"____\"
"""

STEP_128_VALIDATION = {
    "blanks": [
        {"index": 0, "answer": "Why do 73% of users abandon carts at the payment confirmation step?",
         "alternatives": ["What causes checkout abandonment at payment confirmation?",
                         "What friction causes users to drop off at payment confirmation?",
                         "Why are users abandoning the payment confirmation flow?"],
         "hint": "One specific, answerable question tied to the 73% abandonment metric."},
        {"index": 1, "answer": "usability-testing",
         "alternatives": ["usability testing", "moderated-usability-testing", "unmoderated-testing"],
         "hint": "The method that directly observes users interacting with the flow."},
        {"index": 2, "answer": "8",
         "alternatives": ["6", "7", "8", "9", "10", "5"],
         "hint": "Nielsen's research shows 5-8 users reveal ~80% of usability issues."},
        {"index": 3, "answer": "Users who abandoned checkout in the last 30 days",
         "alternatives": ["Recent cart abandoners",
                         "Users who dropped off at payment in the last 30 days",
                         "Users with recent abandoned payments"],
         "hint": "Criteria that gets you people who've actually experienced the problem."},
        {"index": 4, "answer": "2",
         "alternatives": ["1", "2", "3"],
         "hint": "Rapid turnaround — matches sprint cadence."},
        {"index": 5, "answer": "Reduce checkout abandonment by 20%",
         "alternatives": ["Reduce cart abandonment rate by 20%",
                         "20% reduction in checkout abandonment",
                         "Recover $480K in abandoned revenue"],
         "hint": "A business-relevant metric the team will care about."},
    ]
}

# Step 132: sjt "Data Collection Troubleshooting" — replace placeholder with real options
STEP_132_DEMO_DATA = {
    "scenario": "You're 20 minutes into a scheduled 60-minute remote usability test when the participant's video cuts out, audio becomes garbled, and they apologize: 'My internet has been flaky all day, I'm trying to fix it.' Your study timeline is tight — you have 7 more participants to interview this week.",
    "options": [
        {
            "label": "Switch to audio-only immediately, tell the participant 'no worries, we can continue by voice — please share your screen if it comes back,' and keep going without video.",
            "correct_rank": 1,
            "explanation": "BEST: adapts to what's working, respects the participant's time, preserves the data. Most usability insights come from verbal protocol anyway.",
        },
        {
            "label": "Pause the session, help them troubleshoot their connection for 5-10 minutes, then resume if it works.",
            "correct_rank": 2,
            "explanation": "Good intent (preserve the session) but burns time and puts you in IT-support mode. Do this only if the session hinges on visual observation.",
        },
        {
            "label": "Apologize, end the session now, and reschedule for later in the week with a different time.",
            "correct_rank": 3,
            "explanation": "Conservative — you lose 20 minutes of data you already captured. Only the right call if the remaining tasks are heavily visual.",
        },
        {
            "label": "Continue as if nothing happened, guessing at the participant's reactions from the fragments of audio you catch.",
            "correct_rank": 4,
            "explanation": "WORST: produces unreliable data dressed as research. Violates the 'quality over quantity' research ethic.",
        },
    ],
}

STEP_132_VALIDATION = {"correct_rankings": [1, 2, 3, 4]}

# Step 138: scenario_branch "Stakeholder Presentation Simulator" — add validation
STEP_138_DEMO_DATA_UPDATE = {
    "scenario": "Your first meeting is with the C-suite (CEO, CFO, CTO) who have 15 minutes and want to understand business impact. Your research shows that simplifying the guest checkout flow could recover 40% of abandoned carts, worth ~$960K annually.",
    "steps": [
        {
            "question": "How do you open the 15-minute presentation?",
            "options": [
                {"label": "Start with the business impact: '$960K recoverable by fixing one specific checkout friction point. Let me show you exactly which one.'", "correct": True, "explanation": "BEST: leads with the outcome the C-suite cares about, then earns the right to explain how you got there."},
                {"label": "Walk through your methodology: 'We ran a 3-week mixed-methods study with 42 participants using eye-tracking and task analysis...'", "correct": False, "explanation": "Methodology first loses a C-suite audience in the first 60 seconds."},
                {"label": "Show the full research deck with 40 slides of findings, charts, and quotes.", "correct": False, "explanation": "Volume signals thoroughness but kills the 15-min slot."},
                {"label": "Apologize for the complexity of the findings and ask if they want you to skip sections.", "correct": False, "explanation": "Undermines your authority before the first insight lands."},
            ],
        },
        {
            "question": "The CFO asks: 'How confident are you in the $960K number?' What's your best response?",
            "options": [
                {"label": "Show your math transparently: 'Baseline abandonment rate × annual checkout attempts × fix-efficacy from comparable studies. Confidence interval is ±20%. Here's the working.'", "correct": True, "explanation": "BEST: earns trust by being explicit about the method AND the uncertainty."},
                {"label": "Say '$960K is a conservative estimate — the real number could be higher.'", "correct": False, "explanation": "Hype without evidence — CFOs smell this immediately."},
                {"label": "'That was my research partner's number, I'd have to get back to you on the math.'", "correct": False, "explanation": "Never present numbers you can't defend. Credibility-killer."},
                {"label": "'Our sample size is small so it's directional — but directionally there IS an opportunity.'", "correct": False, "explanation": "Hedging weakens the ask. Better: state confidence and show the math."},
            ],
        },
        {
            "question": "CEO says: 'Interesting. What do you need from us to ship this fix?' You want to ensure research is in the next cycle too. Best ask?",
            "options": [
                {"label": "'Prioritize the checkout fix in Q1 (2 eng-weeks), and embed me in the next feature spec review so I can run rapid research in parallel — no schedule delay.'", "correct": True, "explanation": "BEST: concrete ask tied to impact, AND positions research as accelerating not slowing the team."},
                {"label": "'A dedicated research budget for next year so we can do more studies like this.'", "correct": False, "explanation": "Generic budget ask without a specific use case. Easy to deprioritize."},
                {"label": "'Make research mandatory for all new features.'", "correct": False, "explanation": "Mandate creates resentment. Embedding creates influence."},
                {"label": "'Just ship the fix. I can work on the next research project independently.'", "correct": False, "explanation": "Missed the moment to build a lasting partnership."},
            ],
        },
    ],
    "insight": "Executive audiences buy business outcomes delivered with transparent math, then let you earn the next research cycle by tying your ask to shipping speed — not to process gates.",
}

STEP_138_VALIDATION = {}

# Step 139: system_build capstone "Complete Research Study Deployment" — make it a real deliverable capstone
STEP_139_CONTENT = """
<style>
.capstone-brief { background: #1e2538; border: 1px solid #2a3352; padding: 24px; border-radius: 12px; color: #e8ecf4; line-height: 1.6; }
.capstone-brief h3 { color: #4a7cff; margin-bottom: 10px; }
.capstone-brief h4 { color: #2dd4bf; margin-top: 18px; margin-bottom: 8px; font-size: 1rem; }
.capstone-mission { border-left: 3px solid #2dd4bf; padding: 14px 16px; background: rgba(45,212,191,0.06); border-radius: 0 8px 8px 0; margin-bottom: 16px; }
.capstone-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 14px 0; }
.capstone-box { background: #161b26; border: 1px solid #2a3352; border-radius: 8px; padding: 12px 14px; }
.capstone-box strong { color: #4a7cff; display: block; margin-bottom: 4px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; }
.capstone-ac { background: #161b26; padding: 14px 16px; border-radius: 8px; border-left: 3px solid #fbbf24; margin-top: 14px; }
.capstone-ac li { margin: 6px 0; }
</style>
<div class="capstone-brief">
<h3>🎯 Capstone: Run a Real UX Research Study Start-to-Finish</h3>
<div class="capstone-mission">
<strong style="color:#2dd4bf;">Your mission:</strong> Pick a real product context (your current workplace, a side project, or an open-source app). Execute a full UX research study in 3-4 weeks. The artifact you produce must be good enough to present to actual leadership and drive a real decision — not a classroom exercise.
</div>

<h4>📋 The Deliverables (4 phases)</h4>
<div class="capstone-grid">
<div class="capstone-box"><strong>Phase 1: Plan</strong>A written Research Plan: the single research question, method justification, sample + recruitment plan, timeline, and success metric.</div>
<div class="capstone-box"><strong>Phase 2: Execute</strong>Conduct the study. 5+ participants (usability) or 8+ participants (interviews). Record sessions, write up raw notes same-day.</div>
<div class="capstone-box"><strong>Phase 3: Synthesize</strong>Produce an Affinity Map (digital or physical) → 3-5 key insights → specific, actionable recommendations with priority + effort estimates.</div>
<div class="capstone-box"><strong>Phase 4: Present</strong>15-minute stakeholder presentation. Exec-summary first. Your recommendations MUST be adopted or explicitly declined (written back-and-forth).</div>
</div>

<h4>✅ Acceptance Criteria</h4>
<div class="capstone-ac">
<ul>
<li><strong>The question passes the "so what?" test</strong> — a stakeholder can't say "we already knew that" after reading your insights.</li>
<li><strong>Your sample is defensible</strong> — you can explain to a skeptical engineer why you chose this size and these participants.</li>
<li><strong>Insights are grounded in ≥3 participants</strong> — no single-participant generalizations.</li>
<li><strong>Recommendations are prioritized and effort-estimated</strong> — engineering/product can act on them within 1 sprint.</li>
<li><strong>You got a written decision</strong> — stakeholder either committed to action (with timeline) or declined (with rationale). Lurking ambiguity = fail.</li>
<li><strong>Follow-up metric defined</strong> — what will you measure in 4-8 weeks to know if the recommendation worked?</li>
</ul>
</div>

<h4>🎤 Present to the Class / Team</h4>
<p>Share your 15-minute presentation artifact (deck, Loom, or live session). Peer review focuses on: clarity of the research question, defensibility of the method, depth of insights, and whether the recommendation is concrete enough to ship.</p>
</div>
"""

STEP_139_DEMO_DATA = {
    "phases": [
        {"id": "plan", "title": "Phase 1: Research Plan"},
        {"id": "execute", "title": "Phase 2: Execute Study"},
        {"id": "synthesize", "title": "Phase 3: Synthesize Findings"},
        {"id": "present", "title": "Phase 4: Present & Get Decision"},
    ],
    "checklist": [
        {"id": "c1", "label": "Written research question (passes the 'so what' test)"},
        {"id": "c2", "label": "Method justification: why this method over alternatives"},
        {"id": "c3", "label": "Recruitment plan with defensible sample size (5-8 for usability, 8-12 for interviews)"},
        {"id": "c4", "label": "All sessions completed, recorded, and day-of notes written up"},
        {"id": "c5", "label": "Affinity map created (physical or digital — photograph/screenshot as artifact)"},
        {"id": "c6", "label": "3-5 distinct insights, each grounded in ≥3 participants' data"},
        {"id": "c7", "label": "Recommendations document: prioritized, effort-estimated, owner-assigned"},
        {"id": "c8", "label": "15-minute exec presentation delivered (live or async via Loom)"},
        {"id": "c9", "label": "Written decision from stakeholder: committed, declined-with-rationale, or next-step"},
        {"id": "c10", "label": "Follow-up metric defined and tracking kicked off (4-8 week horizon)"},
    ],
}

STEP_139_VALIDATION = {"manual_review": True}


PATCHES = [
    (125, {"content": STEP_125_CONTENT, "step_type": "concept"}),
    (127, {"demo_data": STEP_127_DEMO_DATA, "validation": {}}),
    (128, {"code": STEP_128_CODE, "validation": STEP_128_VALIDATION}),
    (132, {"demo_data": STEP_132_DEMO_DATA, "validation": STEP_132_VALIDATION}),
    (138, {"demo_data": STEP_138_DEMO_DATA_UPDATE, "validation": STEP_138_VALIDATION}),
    (139, {"content": STEP_139_CONTENT, "demo_data": STEP_139_DEMO_DATA, "validation": STEP_139_VALIDATION}),
]


async def patch_course():
    async with async_session_factory() as db:
        for step_id, fields in PATCHES:
            result = await db.execute(select(Step).where(Step.id == step_id))
            step = result.scalars().first()
            if not step:
                print(f"Step {step_id} NOT FOUND — skipping")
                continue
            for k, v in fields.items():
                setattr(step, k, v)
            print(f"Patched step {step_id}: {step.title}")
        await db.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(patch_course())
