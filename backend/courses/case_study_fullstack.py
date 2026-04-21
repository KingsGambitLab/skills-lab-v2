"""
Case Study Course: Full-Stack AI Support System
Build an AI-powered customer support system from requirements to production.
"""

COURSE = {
    "id": "fullstack-ai-support",
    "title": "Full-Stack AI Support System",
    "subtitle": "Design, build, and ship an AI support system for a growing tech company",
    "icon": "🛠️",
    "course_type": "case_study",
    "level": "Intermediate",
    "tags": ["full-stack", "ai-support", "nlp", "production", "case-study", "python"],
    "estimated_time": "~2.5 hours",
    "description": (
        "NovaTech, a B2B SaaS company with 12,000 customers, is drowning in support tickets. "
        "Response times have ballooned to 14 hours and CSAT scores are plummeting. The VP of "
        "Customer Success has given your team 8 weeks to build an AI-powered support system "
        "that can handle Tier-1 tickets automatically and assist human agents on complex issues. "
        "You'll navigate real trade-offs in architecture, model selection, and deployment."
    ),
    "modules": [
        # ── Module 1: The Brief ──────────────────────────────────────
        {
            "position": 1,
            "title": "The Brief",
            "subtitle": "Understand the problem, map stakeholders, and choose your architecture",
            "estimated_time": "30 min",
            "objectives": [
                "Analyze support ticket data to identify automation opportunities",
                "Map stakeholders and their competing priorities",
                "Make defensible architecture decisions under constraints",
            ],
            "steps": [
                # Step 1 -- concept (case setup)
                {
                    "position": 1,
                    "title": "The Support Crisis at NovaTech",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.ticket-demo { background: #1e2538; border: 1px solid #2a3352; border-radius: 12px; padding: 22px; margin: 16px 0; color: #e8ecf4; font-family: 'Inter', system-ui, sans-serif; }
.ticket-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.ticket-demo .hook { background: linear-gradient(135deg, #151b2e, #252e45); border-left: 4px solid #2dd4bf; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 18px; }
.ticket-demo .hook strong { color: #2dd4bf; }
.ticket-demo .instruction { color: #8b95b0; font-size: 0.88em; margin-bottom: 10px; }
.ticket-demo .queue { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 16px; }
.ticket-demo .col h3 { color: #8b95b0; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 10px 0; }
.ticket-demo .col.human h3 { color: #4a7cff; }
.ticket-demo .col.ai h3 { color: #2dd4bf; }
.ticket-demo .ticket { background: #151b2e; border: 1px solid #2a3352; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; cursor: pointer; transition: all 0.15s; position: relative; }
.ticket-demo .ticket:hover { border-color: #4a7cff; }
.ticket-demo .ticket .rank { position: absolute; top: 10px; right: 12px; background: #2a3352; color: #8b95b0; border-radius: 14px; width: 26px; height: 26px; font-weight: 700; font-size: 0.85em; display: flex; align-items: center; justify-content: center; }
.ticket-demo .ticket.ranked .rank { background: #4a7cff; color: #fff; }
.ticket-demo .ticket.ai .rank { background: #2dd4bf; color: #151b2e; }
.ticket-demo .ticket .from { color: #8b95b0; font-size: 0.75em; text-transform: uppercase; letter-spacing: 0.5px; }
.ticket-demo .ticket .subj { color: #e8ecf4; font-weight: 600; font-size: 0.9em; margin: 4px 0; padding-right: 34px; }
.ticket-demo .ticket .body { color: #8b95b0; font-size: 0.82em; line-height: 1.5; }
.ticket-demo .ticket .score { display: none; margin-top: 6px; font-size: 0.78em; color: #8b95b0; font-family: 'Fira Code', monospace; }
.ticket-demo .ticket.ai .score { display: block; }
.ticket-demo .ticket .score b { color: #2dd4bf; }
.ticket-demo .ticket .score .tag { display: inline-block; background: #1e2538; border: 1px solid #2a3352; border-radius: 3px; padding: 1px 6px; margin-right: 4px; color: #8b95b0; }
.ticket-demo .ticket .score .tag.urgent { color: #f87171; border-color: #f87171; }
.ticket-demo .ticket .score .tag.routine { color: #2dd4bf; border-color: #2dd4bf; }
.ticket-demo .controls { margin-top: 14px; text-align: center; }
.ticket-demo .btn-t { background: #4a7cff; color: #fff; border: none; padding: 10px 22px; border-radius: 6px; cursor: pointer; font-weight: 600; margin: 4px; transition: background 0.2s; }
.ticket-demo .btn-t:hover { background: #3a6cef; }
.ticket-demo .btn-t.secondary { background: transparent; border: 1px solid #2a3352; color: #8b95b0; }
.ticket-demo .btn-t.secondary:hover { color: #e8ecf4; border-color: #4a7cff; }
.ticket-demo .verdict { margin-top: 14px; padding: 12px 16px; border-radius: 8px; font-size: 0.9em; display: none; }
.ticket-demo .verdict.show { display: block; }
.ticket-demo .verdict.good { background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.3); color: #2dd4bf; }
.ticket-demo .verdict.meh { background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; }
@media(max-width:700px){ .ticket-demo .queue { grid-template-columns: 1fr; } }
</style>

<div class="ticket-demo">
  <h2>Ticket Triage Challenge</h2>
  <div class="hook">
    <strong>The problem:</strong> Your SaaS gets 200 tickets/day. 60% are routine. Humans waste 4 hours sorting them. What if AI could do it in 2 seconds?
  </div>

  <div class="instruction">Click each ticket in the order you would triage them (most urgent first). Then reveal how AI would triage them.</div>

  <div class="queue">
    <div class="col human">
      <h3>Your Queue</h3>
      <div class="ticket" data-id="t1" onclick="rankTicket(this)">
        <span class="rank" id="r-t1">?</span>
        <div class="from">austin@scale-corp.com -- Enterprise</div>
        <div class="subj">Production is DOWN. 400 users cannot log in.</div>
        <div class="body">Outage started 6 min ago. Entire sales team locked out. This is costing us thousands per minute. Need help NOW.</div>
      </div>
      <div class="ticket" data-id="t2" onclick="rankTicket(this)">
        <span class="rank" id="r-t2">?</span>
        <div class="from">jmiller@gmail.com -- Free tier</div>
        <div class="subj">forgot password</div>
        <div class="body">i cant log in. can you reset it</div>
      </div>
      <div class="ticket" data-id="t3" onclick="rankTicket(this)">
        <span class="rank" id="r-t3">?</span>
        <div class="from">legal@mediahouse.io -- Pro</div>
        <div class="subj">GDPR data deletion request (48hr deadline)</div>
        <div class="body">Under Article 17 we require full deletion of user 88211 data across all systems. Legal deadline expires Thursday.</div>
      </div>
      <div class="ticket" data-id="t4" onclick="rankTicket(this)">
        <span class="rank" id="r-t4">?</span>
        <div class="from">devrel@startup.co -- Growth</div>
        <div class="subj">Feature request: dark mode on mobile</div>
        <div class="body">Would love dark mode on the iOS app. Not urgent, just a nice-to-have for the team.</div>
      </div>
      <div class="ticket" data-id="t5" onclick="rankTicket(this)">
        <span class="rank" id="r-t5">?</span>
        <div class="from">sarah@fintech.inc -- Enterprise</div>
        <div class="subj">Cancelling account, refund demanded</div>
        <div class="body">Third outage this month. We are moving to a competitor. I want a prorated refund AND compensation for lost productivity. Do not send a support article.</div>
      </div>
    </div>

    <div class="col ai" id="aiCol" style="display:none;">
      <h3>AI Triage (2.1s)</h3>
    </div>
  </div>

  <div class="controls">
    <button class="btn-t" onclick="revealAI()">Show AI Triage</button>
    <button class="btn-t secondary" onclick="resetTriage()">Reset</button>
  </div>

  <div class="verdict" id="triageVerdict"></div>
</div>

<script>
(function(){
  var order = [];
  var tickets = {
    t1: {subj: "Production is DOWN. 400 users cannot log in.",   aiRank: 1, tags: "<span class='tag urgent'>P0</span><span class='tag urgent'>OUTAGE</span><span class='tag'>ENTERPRISE</span>", score: "urgency 0.98  revenue_risk 0.95  sla_breach 0.92"},
    t2: {subj: "forgot password",                                 aiRank: 5, tags: "<span class='tag routine'>SELF-SERVE</span><span class='tag'>LOW</span>",                                           score: "urgency 0.08  auto_resolve 0.99  sla_breach 0.05"},
    t3: {subj: "GDPR data deletion request (48hr deadline)",       aiRank: 2, tags: "<span class='tag urgent'>LEGAL</span><span class='tag urgent'>COMPLIANCE</span>",                                  score: "urgency 0.88  legal_risk 0.97  sla_breach 0.71"},
    t4: {subj: "Feature request: dark mode on mobile",             aiRank: 4, tags: "<span class='tag routine'>FEATURE</span><span class='tag'>LOW</span>",                                             score: "urgency 0.12  auto_ack 0.90  sla_breach 0.02"},
    t5: {subj: "Cancelling account, refund demanded",              aiRank: 3, tags: "<span class='tag urgent'>CHURN</span><span class='tag urgent'>RETENTION</span>",                                  score: "urgency 0.82  churn_risk 0.94  needs_human 1.00"}
  };

  function paintQueue() {
    Object.keys(tickets).forEach(function(id){
      var idx = order.indexOf(id);
      var rankEl = document.getElementById('r-' + id);
      var tEl = document.querySelector('.ticket-demo .ticket[data-id=' + id + ']');
      if (idx > -1) {
        rankEl.textContent = (idx + 1);
        tEl.classList.add('ranked');
      } else {
        rankEl.textContent = '?';
        tEl.classList.remove('ranked');
      }
    });
  }

  window.rankTicket = function(el) {
    var id = el.dataset.id;
    var idx = order.indexOf(id);
    if (idx > -1) {
      order.splice(idx, 1);
    } else {
      order.push(id);
    }
    paintQueue();
  };

  window.resetTriage = function() {
    order = [];
    document.getElementById('aiCol').style.display = 'none';
    document.getElementById('triageVerdict').classList.remove('show');
    paintQueue();
  };

  window.revealAI = function() {
    var aiOrder = Object.keys(tickets).sort(function(a,b){ return tickets[a].aiRank - tickets[b].aiRank; });
    var html = '';
    aiOrder.forEach(function(id, i){
      var t = tickets[id];
      html += '<div class="ticket ai"><span class="rank">' + (i+1) + '</span>'
        + '<div class="subj">' + t.subj + '</div>'
        + '<div class="score">' + t.tags + '<br><b>' + t.score + '</b></div>'
        + '</div>';
    });
    var aiCol = document.getElementById('aiCol');
    aiCol.innerHTML = '<h3>AI Triage (2.1s)</h3>' + html;
    aiCol.style.display = 'block';

    var v = document.getElementById('triageVerdict');
    if (order.length === 5) {
      var matches = 0;
      for (var i = 0; i < 5; i++) {
        if (order[i] === aiOrder[i]) matches++;
      }
      if (matches >= 4) {
        v.className = 'verdict show good';
        v.innerHTML = '<strong>' + matches + '/5 match.</strong> You have good triage instincts. At 200 tickets/day, even a 30-second manual read takes 100 minutes. AI collapses that to 7 seconds with the same ranking. The humans you free up go hunt root causes on the P0 outage.';
      } else {
        v.className = 'verdict show meh';
        v.innerHTML = '<strong>' + matches + '/5 match.</strong> Notice what AI caught: GDPR is a legal landmine, not a "compliance ticket." Refund demands signal churn, not a support request. Password resets should never hit a human. The AI scoring is based on SLA, legal risk, churn risk, and revenue exposure -- not just keyword urgency.';
      }
    } else {
      v.className = 'verdict show meh';
      v.innerHTML = 'Rank all 5 tickets to compare against the AI.';
    }
  };
})();
</script>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- scenario_branch (stakeholder mapping)
                {
                    "position": 2,
                    "title": "Stakeholder Minefield",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>Before writing a single line of code, you need to navigate competing
stakeholder interests. Each decision shapes the system you'll build.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "You've been brought in to lead the AI support project. On day one, "
                            "you discover that different stakeholders have very different visions "
                            "for what 'AI support' means. You need to align them before you can "
                            "start building."
                        ),
                        "steps": [
                            {
                                "question": "The CTO wants to fine-tune an open-source LLM on your ticket history. The VP of CS wants to use a hosted API (like Claude) with retrieval-augmented generation. The CFO wants to know why you can't just use keyword matching. Who do you side with?",
                                "options": [
                                    {
                                        "label": "Side with the CTO -- fine-tuning gives us full control and no per-token costs at scale",
                                        "correct": False,
                                        "explanation": (
                                            "Fine-tuning an LLM is a 3-6 month project requiring ML engineering talent "
                                            "you don't have, GPU infrastructure, and ongoing maintenance. With an 8-week "
                                            "deadline and $150K budget, this is scope suicide. Fine-tuning makes sense "
                                            "at 100K+ tickets/day, not 2,400/week."
                                        ),
                                    },
                                    {
                                        "label": "Propose a hosted LLM API with RAG as the core, but acknowledge the CFO's concern by showing the cost projection",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right call. A hosted API with RAG gives you the best "
                                            "quality-to-time ratio. You can ship in 8 weeks, iterate based on real "
                                            "data, and the per-token cost at 2,400 tickets/week is roughly $800-1,200/month "
                                            "-- well within the $8K operating budget. Show the CFO the math."
                                        ),
                                    },
                                    {
                                        "label": "Build a keyword/rule-based system first, then layer AI on top later",
                                        "correct": False,
                                        "explanation": (
                                            "Rule-based systems plateau fast. NovaTech's ticket volume and variety "
                                            "mean you'd need hundreds of rules that break with every product change. "
                                            "You'd spend 8 weeks building something you'd tear down in month 4. "
                                            "Start with the right architecture, even if simpler at first."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "The support team lead, Marcus, pulls you aside: 'My agents are terrified this AI thing is going to replace them. Two people are already looking for other jobs.' How do you handle this?",
                                "options": [
                                    {
                                        "label": "Tell Marcus the AI will handle Tier-1, freeing agents to become 'AI-assisted Tier-2 specialists' with higher job satisfaction and potential for raises",
                                        "correct": True,
                                        "explanation": (
                                            "Reframing the role is critical. Agents who currently spend 52% of their "
                                            "time on password resets and how-to questions will shift to complex problem "
                                            "solving. Position this as a career upgrade, not a threat. Involve agents "
                                            "in training data review -- they become the AI's teachers."
                                        ),
                                    },
                                    {
                                        "label": "Assure Marcus that no one will lose their job -- the AI is just a tool",
                                        "correct": False,
                                        "explanation": (
                                            "Vague reassurances without specifics will ring hollow. Agents can see "
                                            "the ticket numbers -- if AI handles 50% of volume, they'll do the math. "
                                            "You need to paint a concrete picture of their new role, not just say "
                                            "'don't worry.'"
                                        ),
                                    },
                                    {
                                        "label": "Focus on the tech -- the people stuff is HR's problem",
                                        "correct": False,
                                        "explanation": (
                                            "Change management IS your problem. If agents sabotage the system by "
                                            "escalating tickets unnecessarily or giving customers negative framing "
                                            "('sorry, the AI couldn't help you'), the project fails regardless of "
                                            "how good the tech is."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Legal has flagged that NovaTech handles data for healthcare clients (HIPAA) and European clients (GDPR). The VP says 'figure it out.' What's your approach?",
                                "options": [
                                    {
                                        "label": "Use the API provider's data processing agreement, ensure no ticket data is used for model training, and implement PII redaction before any data hits the LLM",
                                        "correct": True,
                                        "explanation": (
                                            "This is the production-grade answer. You need three layers: (1) a DPA with "
                                            "your API provider that covers HIPAA/GDPR, (2) contractual guarantees that "
                                            "data isn't used for training, and (3) a PII redaction pipeline that strips "
                                            "names, emails, and PHI before the LLM sees anything. This adds ~1 week "
                                            "to the build but prevents existential legal risk."
                                        ),
                                    },
                                    {
                                        "label": "Exclude healthcare and EU customers from the AI system entirely",
                                        "correct": False,
                                        "explanation": (
                                            "This solves compliance but creates a two-tier support experience. "
                                            "Healthcare and EU customers would get slower support, which is exactly "
                                            "the problem you're trying to fix. Plus, determining which tickets are "
                                            "from regulated customers requires the same data pipeline work anyway."
                                        ),
                                    },
                                    {
                                        "label": "Move everything on-premises with a self-hosted model",
                                        "correct": False,
                                        "explanation": (
                                            "Self-hosting solves data residency but blows your budget and timeline. "
                                            "You'd need GPU infrastructure ($3-5K/month), ML ops expertise, and 3-4 "
                                            "months just for deployment. Most cloud API providers offer HIPAA-eligible "
                                            "and GDPR-compliant configurations that are far more practical."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Technical architecture decisions are downstream of stakeholder alignment "
                            "and constraints. The best system in the world fails if agents sabotage it, "
                            "legal blocks it, or the CFO pulls funding. Spend your first week on people "
                            "and constraints, not code."
                        ),
                    },
                },
                # Step 3 -- categorization (architecture decisions)
                {
                    "position": 3,
                    "title": "Architecture Decision Map",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>You've decided on a hosted LLM with RAG. Now categorize these architectural
components by which layer of the system they belong to. Getting the layers right
determines how maintainable and scalable the system will be.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Sort these components into the correct architectural layer.",
                        "categories": [
                            "Ingestion & Preprocessing",
                            "Intelligence Layer",
                            "Response & Routing",
                        ],
                        "items": [
                            {
                                "text": "PII redaction pipeline that strips emails, names, and PHI from ticket text",
                                "correct_category": "Ingestion & Preprocessing",
                            },
                            {
                                "text": "Intent classifier that determines ticket category (billing, bug, how-to, etc.)",
                                "correct_category": "Intelligence Layer",
                            },
                            {
                                "text": "Escalation rules engine that routes complex tickets to specialized agents",
                                "correct_category": "Response & Routing",
                            },
                            {
                                "text": "Embedding index of 50,000 resolved tickets for semantic similarity search",
                                "correct_category": "Intelligence Layer",
                            },
                            {
                                "text": "Webhook receiver that normalizes tickets from Zendesk, Intercom, and email",
                                "correct_category": "Ingestion & Preprocessing",
                            },
                            {
                                "text": "Confidence threshold gate -- auto-respond above 0.85, draft for review below",
                                "correct_category": "Response & Routing",
                            },
                            {
                                "text": "Sentiment analysis that detects frustration level before choosing response tone",
                                "correct_category": "Intelligence Layer",
                            },
                            {
                                "text": "Response template engine that formats LLM output into branded, structured replies",
                                "correct_category": "Response & Routing",
                            },
                            {
                                "text": "Language detection and translation layer for non-English tickets",
                                "correct_category": "Ingestion & Preprocessing",
                            },
                        ],
                    },
                },
                # Step 4 -- code (ticket analysis)
                {
                    "position": 4,
                    "title": "Analyze the Ticket Data",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Before building anything, let's analyze NovaTech's actual ticket data to
validate our assumptions about what can be automated. Run this analysis to
see the automation opportunity.</p>
""",
                    "code": """import json
from collections import Counter

# Simulated ticket dataset (representative sample)
TICKETS = [
    {"id": "T-4201", "category": "password_reset", "complexity": "low", "resolution_min": 4, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4202", "category": "how_to", "complexity": "low", "resolution_min": 10, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4203", "category": "billing", "complexity": "medium", "resolution_min": 18, "sentiment": "frustrated", "repeated_contact": True},
    {"id": "T-4204", "category": "bug_report", "complexity": "high", "resolution_min": 52, "sentiment": "frustrated", "repeated_contact": False},
    {"id": "T-4205", "category": "password_reset", "complexity": "low", "resolution_min": 5, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4206", "category": "feature_request", "complexity": "low", "resolution_min": 6, "sentiment": "positive", "repeated_contact": False},
    {"id": "T-4207", "category": "how_to", "complexity": "medium", "resolution_min": 15, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4208", "category": "escalation", "complexity": "very_high", "resolution_min": 95, "sentiment": "angry", "repeated_contact": True},
    {"id": "T-4209", "category": "billing", "complexity": "low", "resolution_min": 8, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4210", "category": "password_reset", "complexity": "low", "resolution_min": 3, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4211", "category": "bug_report", "complexity": "medium", "resolution_min": 30, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4212", "category": "how_to", "complexity": "low", "resolution_min": 8, "sentiment": "neutral", "repeated_contact": False},
    {"id": "T-4213", "category": "escalation", "complexity": "very_high", "resolution_min": 110, "sentiment": "angry", "repeated_contact": True},
    {"id": "T-4214", "category": "billing", "complexity": "medium", "resolution_min": 20, "sentiment": "frustrated", "repeated_contact": False},
    {"id": "T-4215", "category": "feature_request", "complexity": "low", "resolution_min": 7, "sentiment": "positive", "repeated_contact": False},
]

# Analyze automation potential
automation_map = {
    "password_reset": {"automatable": True, "confidence": "high", "ai_role": "full_auto"},
    "how_to": {"automatable": True, "confidence": "medium", "ai_role": "full_auto_with_rag"},
    "billing": {"automatable": "partial", "confidence": "medium", "ai_role": "draft_for_agent"},
    "bug_report": {"automatable": False, "confidence": "high", "ai_role": "classify_and_route"},
    "feature_request": {"automatable": True, "confidence": "high", "ai_role": "acknowledge_and_log"},
    "escalation": {"automatable": False, "confidence": "high", "ai_role": "immediate_human"},
}

print("=== NovaTech Ticket Analysis ===\\n")

# Category distribution
categories = Counter(t["category"] for t in TICKETS)
total = len(TICKETS)
print("Category Distribution:")
for cat, count in categories.most_common():
    pct = count / total * 100
    auto = automation_map[cat]
    print(f"  {cat:20s} {count:3d} ({pct:4.1f}%)  -> {auto['ai_role']}")

# Automation coverage
auto_tickets = sum(1 for t in TICKETS if automation_map[t["category"]]["automatable"] == True)
partial_tickets = sum(1 for t in TICKETS if automation_map[t["category"]]["automatable"] == "partial")
manual_tickets = total - auto_tickets - partial_tickets

print(f"\\nAutomation Potential:")
print(f"  Full automation:    {auto_tickets:3d} ({auto_tickets/total*100:.0f}%)")
print(f"  AI-assisted:        {partial_tickets:3d} ({partial_tickets/total*100:.0f}%)")
print(f"  Human required:     {manual_tickets:3d} ({manual_tickets/total*100:.0f}%)")

# Time savings estimate
avg_times = {}
for cat in categories:
    cat_tickets = [t for t in TICKETS if t["category"] == cat]
    avg_times[cat] = sum(t["resolution_min"] for t in cat_tickets) / len(cat_tickets)

weekly_volume = 2400
print(f"\\nEstimated Weekly Time Savings:")
total_saved = 0
for cat, avg_t in sorted(avg_times.items()):
    cat_pct = categories[cat] / total
    weekly_cat = int(weekly_volume * cat_pct)
    auto = automation_map[cat]
    if auto["automatable"] == True:
        saved = weekly_cat * avg_t * 0.9  # 90% handled by AI
        total_saved += saved
        print(f"  {cat:20s} {saved:6.0f} min/week saved")
    elif auto["automatable"] == "partial":
        saved = weekly_cat * avg_t * 0.4  # 40% time reduction
        total_saved += saved
        print(f"  {cat:20s} {saved:6.0f} min/week saved (partial)")

print(f"\\n  TOTAL: {total_saved:.0f} min/week = {total_saved/60:.0f} agent-hours/week")
print(f"  Equivalent to ~{total_saved/60/40:.1f} full-time agents")
""",
                    "expected_output": """=== NovaTech Ticket Analysis ===

Automation Potential:
  Full automation:      9 (60%)
  AI-assisted:          3 (20%)
  Human required:       3 (20%)""",
                    "validation": None,
                    "demo_data": None,
                },
            ],
        },
        # ── Module 2: Building the Core ──────────────────────────────
        {
            "position": 2,
            "title": "Building the Core",
            "subtitle": "Implement intent classification, response generation, and escalation logic",
            "estimated_time": "45 min",
            "objectives": [
                "Build an intent classification system with confidence scoring",
                "Implement RAG-based response generation with guardrails",
                "Design escalation logic that knows when AI should step aside",
                "Review production code for critical bugs",
            ],
            "steps": [
                # Step 1 -- concept (system design)
                {
                    "position": 1,
                    "title": "The Three-Brain Architecture",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>How the Support System Thinks</h2>
<p>Our system uses three specialized "brains" that work in sequence on every incoming ticket:</p>

<h3>Brain 1: The Classifier</h3>
<p>Determines intent, urgency, and complexity. Fast and cheap -- uses a smaller model
or fine-tuned classifier. Runs on every ticket in < 500ms.</p>
<ul>
  <li><strong>Inputs:</strong> ticket subject, body, customer metadata</li>
  <li><strong>Outputs:</strong> intent label, confidence score, urgency level</li>
  <li><strong>Threshold:</strong> confidence > 0.85 to proceed to auto-response</li>
</ul>

<h3>Brain 2: The Responder</h3>
<p>Generates a contextual response using RAG. Pulls from knowledge base articles,
resolved ticket history, and product documentation. Uses the full LLM.</p>
<ul>
  <li><strong>Inputs:</strong> classified intent, retrieved context, customer tier</li>
  <li><strong>Outputs:</strong> draft response, cited sources, action items</li>
  <li><strong>Guardrails:</strong> no promises, no financial commitments, no PHI in responses</li>
</ul>

<h3>Brain 3: The Router</h3>
<p>Decides the final action: auto-send, queue for agent review, or escalate immediately.
Uses rules + sentiment analysis.</p>
<table>
  <tr><th>Scenario</th><th>Action</th></tr>
  <tr><td>High confidence + low complexity + neutral sentiment</td><td>Auto-send response</td></tr>
  <tr><td>Medium confidence OR medium complexity</td><td>Draft response, queue for agent</td></tr>
  <tr><td>Low confidence OR high complexity OR angry sentiment</td><td>Route to specialist agent</td></tr>
  <tr><td>Repeated contact (3+ tickets in 7 days)</td><td>Escalate to team lead</td></tr>
  <tr><td>Mentions "cancel", "lawyer", "BBB"</td><td>Immediate escalation to manager</td></tr>
</table>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- code_exercise (intent classifier)
                {
                    "position": 2,
                    "title": "Build the Intent Classifier",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build the intent classification function. It takes raw ticket text and returns
a structured classification with confidence scoring. The classifier uses keyword
matching and pattern analysis as a fast first pass -- in production, this would
call an LLM for ambiguous cases.</p>
""",
                    "code": """import re
from typing import Optional

# Intent patterns -- ordered by priority (first match wins for ties)
INTENT_PATTERNS = {
    "password_reset": {
        "keywords": ["password", "reset", "login", "can't log in", "locked out", "forgot", "credentials"],
        "base_confidence": 0.90,
    },
    "billing": {
        "keywords": ["invoice", "charge", "billing", "subscription", "payment", "refund", "upgrade", "downgrade", "plan"],
        "base_confidence": 0.85,
    },
    "how_to": {
        "keywords": ["how do i", "how to", "where is", "can i", "help with", "tutorial", "guide", "set up", "configure"],
        "base_confidence": 0.80,
    },
    "bug_report": {
        "keywords": ["error", "broken", "not working", "crash", "bug", "issue", "glitch", "500", "fails"],
        "base_confidence": 0.82,
    },
    "feature_request": {
        "keywords": ["would be nice", "feature request", "suggestion", "wish", "it would help if", "please add"],
        "base_confidence": 0.88,
    },
    "escalation": {
        "keywords": ["cancel", "lawyer", "legal", "bbb", "unacceptable", "sue", "terrible", "worst"],
        "base_confidence": 0.92,
    },
}

def classify_intent(ticket_text: str, customer_meta: Optional[dict] = None) -> dict:
    \"\"\"Classify a support ticket's intent with confidence scoring.

    Args:
        ticket_text: The full ticket text (subject + body)
        customer_meta: Optional dict with keys like:
            - tier: "free" | "pro" | "enterprise"
            - tickets_last_7_days: int
            - account_age_days: int

    Returns:
        dict with:
            - intent: str (one of the INTENT_PATTERNS keys, or "unknown")
            - confidence: float 0.0-1.0
            - urgency: "low" | "medium" | "high" | "critical"
            - signals: list of matched keywords
            - needs_human: bool
    \"\"\"
    text_lower = ticket_text.lower()

    # TODO: Score each intent by counting keyword matches
    # For each intent, count how many keywords appear in the text
    # The intent with the most matches wins (ties broken by base_confidence)

    # TODO: Calculate confidence based on:
    #   - base_confidence of the winning intent
    #   - number of matching keywords (more matches = higher confidence, cap at 1.0)
    #   - penalty of -0.15 if multiple intents have similar match counts (ambiguous)

    # TODO: Determine urgency based on:
    #   - "critical" if intent is "escalation"
    #   - "high" if customer_meta tier is "enterprise" or tickets_last_7_days >= 3
    #   - "medium" if intent is "bug_report" or "billing"
    #   - "low" otherwise

    # TODO: Set needs_human = True if:
    #   - confidence < 0.85
    #   - urgency is "critical" or "high"
    #   - intent is "unknown"

    return {
        "intent": "unknown",
        "confidence": 0.0,
        "urgency": "low",
        "signals": [],
        "needs_human": True,
    }


# Test cases
test_tickets = [
    "I can't log in to my account. I've tried resetting my password three times but the email never arrives.",
    "We're on the Enterprise plan and our dashboard has been showing a 500 error since this morning. This is affecting our entire team.",
    "How do I set up automated workflows? I saw it mentioned in the webinar but can't find it in the app.",
    "This is the third time I've contacted support this week. Your product is broken and I want to cancel immediately.",
    "Would be nice if you added a dark mode option. Just a suggestion!",
]

for ticket in test_tickets:
    result = classify_intent(ticket, {"tier": "enterprise", "tickets_last_7_days": 1, "account_age_days": 365})
    print(f"Intent: {result['intent']:20s}  Confidence: {result['confidence']:.2f}  Urgency: {result['urgency']:10s}  Human: {result['needs_human']}")
    print(f"  Signals: {result['signals']}")
    print(f"  Text: {ticket[:80]}...")
    print()
""",
                    "expected_output": """Intent: password_reset       Confidence: 0.95  Urgency: high        Human: True
Intent: bug_report            Confidence: 0.90  Urgency: high        Human: True
Intent: how_to                Confidence: 0.88  Urgency: low         Human: False
Intent: escalation            Confidence: 0.95  Urgency: critical    Human: True
Intent: feature_request       Confidence: 0.92  Urgency: low         Human: False""",
                    "validation": {
                        "must_contain": ["intent", "confidence", "urgency", "needs_human", "signals"],
                        "must_return_keys": ["intent", "confidence", "urgency", "signals", "needs_human"],
                        "hint": "Count keyword matches per intent, pick the best, calculate confidence with ambiguity penalty, then derive urgency and needs_human from rules.",
                    },
                    "demo_data": None,
                },
                # Step 3 -- code_review (response generation)
                {
                    "position": 3,
                    "title": "Review the Response Generator",
                    "step_type": "exercise",
                    "exercise_type": "code_review",
                    "content": """
<p>A teammate wrote the response generation module. It has 3 bugs that could
cause incorrect responses, security issues, or poor customer experience.
Find them all.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "code": """def generate_response(intent: str, ticket_text: str, context_docs: list, customer: dict) -> dict:
    \"\"\"Generate an AI response for a support ticket.\"\"\"

    # Build the prompt with retrieved context
    context_str = "\\n".join([doc["content"] for doc in context_docs[:5]])

    system_prompt = f\"\"\"You are a helpful support agent for NovaTech.
    Use the following knowledge base articles to answer the customer's question.
    Context: {context_str}
    Customer name: {customer['name']}
    Customer email: {customer['email']}
    Account type: {customer['tier']}
    \"\"\"

    # Generate response using LLM
    response = call_llm(
        system=system_prompt,
        user=ticket_text,
        max_tokens=500,
    )

    # Post-process: add greeting and sign-off
    final_response = f"Hi {customer['name']},\\n\\n{response}\\n\\nBest regards,\\nNovaTech Support"

    # Log the interaction
    log_ticket_response(
        ticket_text=ticket_text,
        response=final_response,
        customer_email=customer['email'],
        context_used=context_str,
    )

    return {
        "response": final_response,
        "sources": [doc["title"] for doc in context_docs[:5]],
        "confidence": 0.9,  # hardcoded for now
    }""",
                        "bugs": [
                            {
                                "line": 9,
                                "issue": "Customer PII (name, email) injected directly into the LLM system prompt",
                                "severity": "high",
                                "hint": (
                                    "The system prompt sends customer email and name to the LLM. For HIPAA/GDPR "
                                    "compliance, PII must be redacted before reaching the model. The greeting can "
                                    "be added in post-processing (which it already is on line 22) without the LLM "
                                    "ever seeing the customer's real identity."
                                ),
                            },
                            {
                                "line": 25,
                                "issue": "Confidence score is hardcoded instead of derived from the LLM response",
                                "severity": "medium",
                                "hint": (
                                    "A hardcoded confidence of 0.9 means the routing layer will auto-send "
                                    "almost every response, even when the LLM is uncertain or hallucinating. "
                                    "Confidence should be computed from the LLM's log probabilities, or by "
                                    "checking whether the response is grounded in the retrieved context."
                                ),
                            },
                            {
                                "line": 28,
                                "issue": "Full ticket text and customer email are logged together without redaction",
                                "severity": "high",
                                "hint": (
                                    "Logging raw ticket text alongside customer email creates a data retention "
                                    "liability. Ticket text may contain passwords, credit card numbers, or health "
                                    "information. Logs should contain only redacted text and a hashed customer "
                                    "identifier, not raw PII."
                                ),
                            },
                        ],
                    },
                },
                # Step 4 -- code_exercise (escalation logic)
                {
                    "position": 4,
                    "title": "Build the Escalation Engine",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>The escalation engine is the safety net -- it decides when the AI should
step aside and hand off to a human. Get this wrong and you either overwhelm
agents with unnecessary escalations or leave frustrated customers stuck in
an AI loop.</p>
""",
                    "code": """from datetime import datetime, timedelta
from enum import Enum

class Action(Enum):
    AUTO_RESPOND = "auto_respond"
    DRAFT_FOR_REVIEW = "draft_for_review"
    ROUTE_TO_SPECIALIST = "route_to_specialist"
    ESCALATE_TO_LEAD = "escalate_to_lead"
    ESCALATE_TO_MANAGER = "escalate_to_manager"

# Escalation trigger phrases (immediate manager escalation)
ESCALATION_TRIGGERS = ["cancel", "lawyer", "legal action", "bbb", "attorney", "sue you", "report you"]

def decide_action(classification: dict, customer_meta: dict, response_confidence: float) -> dict:
    \"\"\"Determine the appropriate action for a classified ticket.

    Args:
        classification: output of classify_intent() with keys:
            - intent, confidence, urgency, signals, needs_human
        customer_meta: dict with:
            - tier: "free" | "pro" | "enterprise"
            - tickets_last_7_days: int
            - account_age_days: int
            - lifetime_value: float
            - original_text: str (the raw ticket text)
        response_confidence: float, confidence in the generated response (0.0-1.0)

    Returns:
        dict with:
            - action: Action enum value
            - reason: str explaining why this action was chosen
            - priority: int 1-5 (1 = highest)
            - sla_minutes: int (target response time)
            - assigned_to: str (queue or agent group)
    \"\"\"
    # TODO: Check for immediate escalation triggers in the original text
    # If any ESCALATION_TRIGGERS appear -> ESCALATE_TO_MANAGER, priority 1

    # TODO: Check for repeated contacts
    # If tickets_last_7_days >= 3 -> ESCALATE_TO_LEAD, priority 2

    # TODO: Apply confidence-based routing:
    #   - classification confidence >= 0.85 AND response_confidence >= 0.85 -> AUTO_RESPOND
    #   - classification confidence >= 0.70 OR response_confidence >= 0.70 -> DRAFT_FOR_REVIEW
    #   - below both thresholds -> ROUTE_TO_SPECIALIST

    # TODO: Override for enterprise customers:
    #   - If tier is "enterprise", minimum action is DRAFT_FOR_REVIEW (never auto-respond)
    #   - SLA for enterprise: 60 minutes max

    # TODO: Set SLA based on action:
    #   - ESCALATE_TO_MANAGER: 15 min
    #   - ESCALATE_TO_LEAD: 30 min
    #   - ROUTE_TO_SPECIALIST: 120 min
    #   - DRAFT_FOR_REVIEW: 240 min
    #   - AUTO_RESPOND: 0 min (immediate)

    # TODO: Set assigned_to based on action:
    #   - ESCALATE_TO_MANAGER: "management_queue"
    #   - ESCALATE_TO_LEAD: "team_lead_queue"
    #   - ROUTE_TO_SPECIALIST: f"{classification['intent']}_specialists"
    #   - DRAFT_FOR_REVIEW: "general_agents"
    #   - AUTO_RESPOND: "ai_auto"

    return {
        "action": Action.DRAFT_FOR_REVIEW,
        "reason": "default fallback",
        "priority": 3,
        "sla_minutes": 240,
        "assigned_to": "general_agents",
    }


# Test scenarios
scenarios = [
    {
        "name": "Easy password reset",
        "classification": {"intent": "password_reset", "confidence": 0.95, "urgency": "low", "signals": ["password", "reset"], "needs_human": False},
        "customer_meta": {"tier": "pro", "tickets_last_7_days": 0, "account_age_days": 400, "lifetime_value": 2400, "original_text": "I forgot my password"},
        "response_confidence": 0.95,
    },
    {
        "name": "Angry enterprise escalation",
        "classification": {"intent": "escalation", "confidence": 0.92, "urgency": "critical", "signals": ["cancel", "unacceptable"], "needs_human": True},
        "customer_meta": {"tier": "enterprise", "tickets_last_7_days": 4, "account_age_days": 1200, "lifetime_value": 85000, "original_text": "This is unacceptable. I want to cancel our contract and speak to your lawyer."},
        "response_confidence": 0.3,
    },
    {
        "name": "Ambiguous enterprise how-to",
        "classification": {"intent": "how_to", "confidence": 0.72, "urgency": "medium", "signals": ["how to"], "needs_human": False},
        "customer_meta": {"tier": "enterprise", "tickets_last_7_days": 1, "account_age_days": 800, "lifetime_value": 45000, "original_text": "How do I configure SSO with our Azure AD?"},
        "response_confidence": 0.78,
    },
]

for s in scenarios:
    result = decide_action(s["classification"], s["customer_meta"], s["response_confidence"])
    print(f"Scenario: {s['name']}")
    print(f"  Action:   {result['action'].value}")
    print(f"  Reason:   {result['reason']}")
    print(f"  Priority: {result['priority']}")
    print(f"  SLA:      {result['sla_minutes']} min")
    print(f"  Queue:    {result['assigned_to']}")
    print()
""",
                    "expected_output": """Scenario: Easy password reset
  Action:   auto_respond
  Reason:   High confidence classification and response for standard ticket
  Priority: 4
  SLA:      0 min
  Queue:    ai_auto

Scenario: Angry enterprise escalation
  Action:   escalate_to_manager
  Reason:   Escalation trigger detected: cancel, lawyer
  Priority: 1
  SLA:      15 min
  Queue:    management_queue

Scenario: Ambiguous enterprise how-to
  Action:   draft_for_review
  Reason:   Enterprise customer -- AI draft requires agent review
  Priority: 3
  SLA:      60 min
  Queue:    general_agents""",
                    "validation": {
                        "must_contain": ["Action", "ESCALATION_TRIGGERS", "enterprise", "sla_minutes"],
                        "must_return_keys": ["action", "reason", "priority", "sla_minutes", "assigned_to"],
                        "hint": "Check triggers first, then repeated contacts, then confidence thresholds. Apply enterprise override last.",
                    },
                    "demo_data": None,
                },
                # Step 5 -- scenario_branch (edge case decisions)
                {
                    "position": 5,
                    "title": "Edge Case Gauntlet",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>Your system is built but hasn't launched yet. QA found some tricky
edge cases. How you handle these determines whether the system earns
trust or gets pulled in week one.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's the Friday before launch. Your QA engineer, Priya, has found three "
                            "edge cases that don't fit neatly into your current routing logic. Each "
                            "one could embarrass NovaTech if handled wrong in production."
                        ),
                        "steps": [
                            {
                                "question": "A customer writes: 'I love your product! Just wondering if you could help me set up the API integration? Also my credit card on file expired.' This ticket matches both 'how_to' and 'billing' intents with similar confidence. What should the system do?",
                                "options": [
                                    {
                                        "label": "Pick the intent with the higher confidence score and ignore the other",
                                        "correct": False,
                                        "explanation": (
                                            "Ignoring the billing issue means the customer's payment method stays broken. "
                                            "They'll have to write again, which doubles ticket volume and frustrates the customer."
                                        ),
                                    },
                                    {
                                        "label": "Classify as multi-intent, address both topics in the response, and flag billing for follow-up action",
                                        "correct": True,
                                        "explanation": (
                                            "Multi-intent detection is a real-world requirement. The response should answer "
                                            "the API question AND acknowledge the billing issue, creating a follow-up task "
                                            "for the billing team. This prevents repeat contacts."
                                        ),
                                    },
                                    {
                                        "label": "Route to a human agent since the AI can't handle multi-intent tickets",
                                        "correct": False,
                                        "explanation": (
                                            "This is too conservative. Multi-intent tickets are common (roughly 15% of volume). "
                                            "If you route all of them to humans, you undermine the automation gains. Teach the "
                                            "system to handle them."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "A ticket comes in written entirely in Spanish. Your system was only trained on English knowledge base articles. What happens?",
                                "options": [
                                    {
                                        "label": "Add a language detection step in the preprocessing layer -- translate to English for classification, generate the response in English, then translate back to the customer's language",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right pattern: detect -> translate -> process -> translate back. "
                                            "Modern LLMs handle translation well enough for support contexts. Flag for human "
                                            "review if the detected language has low confidence, and always include a note: "
                                            "'This response was auto-translated. Reply in your preferred language.'"
                                        ),
                                    },
                                    {
                                        "label": "Respond in English with a note asking them to resubmit in English",
                                        "correct": False,
                                        "explanation": (
                                            "Terrible customer experience. You're telling a paying customer their language "
                                            "isn't supported. With 12,000 customers globally, language diversity is a given. "
                                            "An LLM-based system should handle multilingual support out of the box."
                                        ),
                                    },
                                    {
                                        "label": "Route all non-English tickets to human agents",
                                        "correct": False,
                                        "explanation": (
                                            "This works short-term but defeats the purpose. If 10% of tickets are non-English, "
                                            "you're routing 240/week to agents unnecessarily. The LLM can translate -- use it."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Edge cases reveal the gap between demo-quality and production-quality AI. "
                            "Multi-intent tickets, language diversity, and ambiguous inputs are not edge "
                            "cases -- they're 15-25% of real traffic. Build for them from day one."
                        ),
                    },
                },
            ],
        },
        # ── Module 3: Production & Iteration ─────────────────────────
        {
            "position": 3,
            "title": "Production & Iteration",
            "subtitle": "Monitor, test, measure, and improve the live system",
            "estimated_time": "35 min",
            "objectives": [
                "Design monitoring dashboards for AI support quality",
                "Set up A/B testing to measure AI vs. human performance",
                "Handle production incidents and learn from failures",
            ],
            "steps": [
                # Step 1 -- code (monitoring dashboard)
                {
                    "position": 1,
                    "title": "Build the Monitoring Dashboard",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Your system has been live for 2 weeks. Run this monitoring code to see
how it's performing. The metrics tell a story -- can you read it?</p>
""",
                    "code": """import json
from datetime import datetime, timedelta

# Simulated 2-week production data
DAILY_METRICS = [
    {"date": "2025-04-01", "total_tickets": 342, "ai_handled": 185, "ai_auto_sent": 142, "ai_drafted": 43, "human_only": 157, "escalations": 18, "csat_ai": 4.1, "csat_human": 4.3, "avg_response_min_ai": 0.5, "avg_response_min_human": 180, "false_positives": 3, "customer_requested_human": 12},
    {"date": "2025-04-02", "total_tickets": 358, "ai_handled": 198, "ai_auto_sent": 155, "ai_drafted": 43, "human_only": 160, "escalations": 15, "csat_ai": 4.0, "csat_human": 4.2, "avg_response_min_ai": 0.4, "avg_response_min_human": 195, "false_positives": 5, "customer_requested_human": 14},
    {"date": "2025-04-03", "total_tickets": 310, "ai_handled": 172, "ai_auto_sent": 130, "ai_drafted": 42, "human_only": 138, "escalations": 12, "csat_ai": 4.2, "csat_human": 4.3, "avg_response_min_ai": 0.5, "avg_response_min_human": 165, "false_positives": 2, "customer_requested_human": 9},
    {"date": "2025-04-04", "total_tickets": 395, "ai_handled": 220, "ai_auto_sent": 175, "ai_drafted": 45, "human_only": 175, "escalations": 22, "csat_ai": 3.8, "csat_human": 4.1, "avg_response_min_ai": 0.6, "avg_response_min_human": 210, "false_positives": 8, "customer_requested_human": 19},
    {"date": "2025-04-05", "total_tickets": 280, "ai_handled": 155, "ai_auto_sent": 118, "ai_drafted": 37, "human_only": 125, "escalations": 10, "csat_ai": 4.3, "csat_human": 4.4, "avg_response_min_ai": 0.4, "avg_response_min_human": 150, "false_positives": 1, "customer_requested_human": 7},
    {"date": "2025-04-06", "total_tickets": 189, "ai_handled": 108, "ai_auto_sent": 85, "ai_drafted": 23, "human_only": 81, "escalations": 6, "csat_ai": 4.4, "csat_human": 4.5, "avg_response_min_ai": 0.3, "avg_response_min_human": 120, "false_positives": 0, "customer_requested_human": 4},
    {"date": "2025-04-07", "total_tickets": 165, "ai_handled": 92, "ai_auto_sent": 72, "ai_drafted": 20, "human_only": 73, "escalations": 5, "csat_ai": 4.5, "csat_human": 4.5, "avg_response_min_ai": 0.3, "avg_response_min_human": 110, "false_positives": 0, "customer_requested_human": 3},
    {"date": "2025-04-08", "total_tickets": 355, "ai_handled": 200, "ai_auto_sent": 160, "ai_drafted": 40, "human_only": 155, "escalations": 16, "csat_ai": 4.1, "csat_human": 4.2, "avg_response_min_ai": 0.5, "avg_response_min_human": 175, "false_positives": 4, "customer_requested_human": 11},
    {"date": "2025-04-09", "total_tickets": 372, "ai_handled": 210, "ai_auto_sent": 170, "ai_drafted": 40, "human_only": 162, "escalations": 14, "csat_ai": 4.2, "csat_human": 4.3, "avg_response_min_ai": 0.4, "avg_response_min_human": 160, "false_positives": 3, "customer_requested_human": 10},
    {"date": "2025-04-10", "total_tickets": 348, "ai_handled": 195, "ai_auto_sent": 158, "ai_drafted": 37, "human_only": 153, "escalations": 13, "csat_ai": 4.2, "csat_human": 4.3, "avg_response_min_ai": 0.4, "avg_response_min_human": 155, "false_positives": 2, "customer_requested_human": 9},
]

# Compute aggregate metrics
total_tickets = sum(d["total_tickets"] for d in DAILY_METRICS)
total_ai = sum(d["ai_handled"] for d in DAILY_METRICS)
total_auto = sum(d["ai_auto_sent"] for d in DAILY_METRICS)
total_fp = sum(d["false_positives"] for d in DAILY_METRICS)
total_human_req = sum(d["customer_requested_human"] for d in DAILY_METRICS)

avg_csat_ai = sum(d["csat_ai"] for d in DAILY_METRICS) / len(DAILY_METRICS)
avg_csat_human = sum(d["csat_human"] for d in DAILY_METRICS) / len(DAILY_METRICS)
avg_response_ai = sum(d["avg_response_min_ai"] for d in DAILY_METRICS) / len(DAILY_METRICS)
avg_response_human = sum(d["avg_response_min_human"] for d in DAILY_METRICS) / len(DAILY_METRICS)

print("=" * 60)
print("  NOVATECH AI SUPPORT -- 10-DAY PRODUCTION REPORT")
print("=" * 60)
print(f"\\n  Total Tickets Processed:     {total_tickets:,}")
print(f"  AI-Handled:                  {total_ai:,} ({total_ai/total_tickets*100:.1f}%)")
print(f"    - Auto-sent:               {total_auto:,} ({total_auto/total_tickets*100:.1f}%)")
print(f"    - Drafted for review:      {total_ai - total_auto:,} ({(total_ai-total_auto)/total_tickets*100:.1f}%)")
print(f"  Human-Only:                  {total_tickets - total_ai:,} ({(total_tickets-total_ai)/total_tickets*100:.1f}%)")

print(f"\\n  Avg Response Time (AI):      {avg_response_ai:.1f} min")
print(f"  Avg Response Time (Human):   {avg_response_human:.0f} min")
print(f"  Speed Improvement:           {avg_response_human/avg_response_ai:.0f}x faster")

print(f"\\n  CSAT Score (AI responses):   {avg_csat_ai:.1f}/5.0")
print(f"  CSAT Score (Human):          {avg_csat_human:.1f}/5.0")
print(f"  CSAT Gap:                    {avg_csat_human - avg_csat_ai:.1f} points")

print(f"\\n  False Positives (wrong AI response): {total_fp} ({total_fp/total_auto*100:.1f}% of auto-sent)")
print(f"  Customer Requested Human:    {total_human_req} ({total_human_req/total_ai*100:.1f}% of AI-handled)")

# Identify the bad day
worst_day = max(DAILY_METRICS, key=lambda d: d["false_positives"])
print(f"\\n  ⚠️  Worst Day: {worst_day['date']} -- {worst_day['false_positives']} false positives, CSAT dropped to {worst_day['csat_ai']}")
print(f"      Root cause: High ticket volume ({worst_day['total_tickets']}) with elevated escalations ({worst_day['escalations']})")

print(f"\\n  Overall Verdict: {'HEALTHY ✅' if avg_csat_ai >= 4.0 and total_fp/total_auto < 0.03 else 'NEEDS ATTENTION ⚠️'}")
""",
                    "expected_output": """NOVATECH AI SUPPORT -- 10-DAY PRODUCTION REPORT

  AI-Handled:                  54.5%
  Avg Response Time (AI):      0.4 min
  CSAT Score (AI responses):   4.2/5.0
  Overall Verdict: HEALTHY""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- categorization (metric types)
                {
                    "position": 2,
                    "title": "Metrics That Matter",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>Not all metrics are created equal. Sort these into the right category
to understand which ones drive decisions, which ones are vanity, and which
ones are safety guardrails.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Classify each metric by its role in the monitoring strategy.",
                        "categories": [
                            "North Star (business outcome)",
                            "Operational Health",
                            "Safety Guardrail",
                        ],
                        "items": [
                            {
                                "text": "Customer Satisfaction (CSAT) score for AI-handled tickets",
                                "correct_category": "North Star (business outcome)",
                            },
                            {
                                "text": "Percentage of customers who request a human after AI response",
                                "correct_category": "Safety Guardrail",
                            },
                            {
                                "text": "Average AI response latency in milliseconds",
                                "correct_category": "Operational Health",
                            },
                            {
                                "text": "False positive rate -- wrong auto-responses sent to customers",
                                "correct_category": "Safety Guardrail",
                            },
                            {
                                "text": "Agent hours saved per week due to AI automation",
                                "correct_category": "North Star (business outcome)",
                            },
                            {
                                "text": "LLM API cost per ticket processed",
                                "correct_category": "Operational Health",
                            },
                            {
                                "text": "Ticket resolution rate (first contact) for AI-handled tickets",
                                "correct_category": "North Star (business outcome)",
                            },
                            {
                                "text": "Number of times AI generates responses containing PII",
                                "correct_category": "Safety Guardrail",
                            },
                            {
                                "text": "RAG retrieval hit rate -- percentage of queries with relevant context",
                                "correct_category": "Operational Health",
                            },
                        ],
                    },
                },
                # Step 3 -- scenario_branch (production incident)
                {
                    "position": 3,
                    "title": "Production Incident: The Thursday Meltdown",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>It's Thursday of week 3. Something has gone wrong. Navigate this
production incident and make the right calls under pressure.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "Your monitoring dashboard lights up at 2:15 PM. In the last hour, the "
                            "'customer requested human' rate spiked from 5% to 28%. CSAT for AI "
                            "responses dropped from 4.2 to 2.8. You have 3 Slack messages from "
                            "support agents saying customers are complaining about 'wrong answers.'"
                        ),
                        "steps": [
                            {
                                "question": "What's your first action?",
                                "options": [
                                    {
                                        "label": "Immediately disable auto-send and switch all AI responses to draft-for-review mode while you investigate",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right call. When your safety metrics spike, you stop the bleeding "
                                            "first. Switching to draft mode means the AI still generates responses (so you "
                                            "can debug), but agents review everything before it reaches customers. You can "
                                            "investigate without causing more damage."
                                        ),
                                    },
                                    {
                                        "label": "Check the logs to understand what changed before taking any action",
                                        "correct": False,
                                        "explanation": (
                                            "Investigating is important, but every minute you spend debugging while "
                                            "auto-send is active, more wrong answers reach customers. In incident response, "
                                            "mitigation comes before root cause analysis. Stop the bleeding, then diagnose."
                                        ),
                                    },
                                    {
                                        "label": "Roll back to the previous version of the system",
                                        "correct": False,
                                        "explanation": (
                                            "A rollback is a valid option, but you didn't deploy anything today. "
                                            "The issue might be upstream -- a knowledge base update, an API change, "
                                            "or a new product release that invalidated your training data. Rolling back "
                                            "won't help if the root cause is external to your code."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "You've switched to draft mode. Investigation reveals that the product team pushed a major UI redesign at 1:30 PM. All the AI's 'how-to' responses now reference buttons and menus that no longer exist. What's the systemic fix?",
                                "options": [
                                    {
                                        "label": "Update the knowledge base articles to match the new UI and re-enable auto-send",
                                        "correct": False,
                                        "explanation": (
                                            "Updating the KB is necessary but not sufficient. The same thing will happen "
                                            "with the next product update. You need a systemic fix, not a one-time patch."
                                        ),
                                    },
                                    {
                                        "label": "Build a product change webhook that automatically flags affected KB articles and disables auto-send for related intents until articles are reviewed",
                                        "correct": True,
                                        "explanation": (
                                            "This is the systemic fix. When the product changes, the AI system should "
                                            "automatically know its knowledge might be stale. The webhook creates a "
                                            "circuit breaker: product change -> flag affected articles -> disable auto-send "
                                            "for those topics -> alert KB team -> re-enable after review. This prevents "
                                            "the same class of incident from ever happening again."
                                        ),
                                    },
                                    {
                                        "label": "Add a disclaimer to all AI responses: 'This information may be outdated. Please verify in the app.'",
                                        "correct": False,
                                        "explanation": (
                                            "A blanket disclaimer undermines trust in every AI response, not just the "
                                            "stale ones. If customers learn to distrust AI responses, they'll request "
                                            "humans every time, defeating the purpose of the system."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Production AI systems fail at the boundaries -- when the world changes and "
                            "the system doesn't know it. The most important architecture decision isn't "
                            "which model to use, it's building circuit breakers that detect when the AI's "
                            "knowledge is stale and gracefully degrade to human handling."
                        ),
                    },
                },
                # Step 4 -- concept (retrospective)
                {
                    "position": 4,
                    "title": "Case Closed: The NovaTech Outcome",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>12-Week Results</h2>

<h3>The Numbers</h3>
<table>
  <tr><th>Metric</th><th>Before</th><th>After</th><th>Change</th></tr>
  <tr><td>Avg Response Time</td><td>14.2 hours</td><td>2.1 hours</td><td>-85%</td></tr>
  <tr><td>CSAT Score</td><td>3.1/5.0</td><td>4.2/5.0</td><td>+35%</td></tr>
  <tr><td>Tickets Handled by AI</td><td>0%</td><td>54%</td><td>--</td></tr>
  <tr><td>Agent Headcount</td><td>18</td><td>18 (0 layoffs)</td><td>0</td></tr>
  <tr><td>Tickets per Agent (complex)</td><td>133/week</td><td>61/week</td><td>-54%</td></tr>
  <tr><td>Agent Satisfaction</td><td>2.8/5.0</td><td>4.0/5.0</td><td>+43%</td></tr>
  <tr><td>Monthly Operating Cost</td><td>$0 (all manual)</td><td>$4,200 (LLM API + infra)</td><td>--</td></tr>
</table>

<h3>What You Built</h3>
<ol>
  <li><strong>Intent Classifier</strong> -- fast, cheap, accurate ticket categorization</li>
  <li><strong>RAG Response Generator</strong> -- contextual answers grounded in knowledge base</li>
  <li><strong>Escalation Engine</strong> -- smart routing with enterprise overrides and safety nets</li>
  <li><strong>Monitoring Dashboard</strong> -- real-time quality tracking with circuit breakers</li>
  <li><strong>Product Change Webhook</strong> -- automatic staleness detection</li>
</ol>

<h3>Key Lessons</h3>
<ul>
  <li><strong>People before code</strong> -- stakeholder alignment and agent buy-in were the hardest parts</li>
  <li><strong>Confidence thresholds matter more than model quality</strong> -- knowing when NOT to respond is the real skill</li>
  <li><strong>Circuit breakers are non-negotiable</strong> -- the system must degrade gracefully when the world changes</li>
  <li><strong>Enterprise customers get humans</strong> -- the cost of a wrong answer at $85K ARR is not worth the automation savings</li>
  <li><strong>Measure what matters</strong> -- CSAT and false positive rate, not total tickets processed</li>
</ul>

<h3>What's Next</h3>
<p>The team is now planning Phase 2:</p>
<ul>
  <li>Proactive support -- detect issues before customers report them</li>
  <li>Multi-language support with quality scoring per language</li>
  <li>Agent copilot mode for Tier-2 tickets (real-time suggestions)</li>
  <li>Feedback loop -- using CSAT data to continuously improve responses</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 5 -- system_build (capstone: Support AI System to Railway)
                {
                    "position": 5,
                    "title": "Deploy: Support AI System to Railway",
                    "step_type": "exercise",
                    "exercise_type": "system_build",
                    "content": """
<style>
.sb-brief { background: #151b2e; border: 1px solid #2a3352; border-radius: 12px; padding: 22px; margin: 12px 0; }
.sb-brief h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.sb-brief h3 { color: #2dd4bf; font-size: 1em; margin-top: 18px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
.sb-brief .objective { background: linear-gradient(135deg, #1e2538, #252e45); border-left: 4px solid #2dd4bf; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 12px 0; color: #e8ecf4; line-height: 1.6; }
.sb-brief .constraints { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin: 10px 0; }
.sb-brief .pill { background: #1e2538; border: 1px solid #2a3352; border-radius: 8px; padding: 10px 12px; font-size: 0.82em; }
.sb-brief .pill strong { color: #4a7cff; display: block; font-size: 0.75em; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.sb-brief .pill span { color: #e8ecf4; font-family: 'Fira Code', monospace; }
.sb-brief ul.accept { list-style: none; padding-left: 0; }
.sb-brief ul.accept li { padding: 6px 0 6px 26px; position: relative; color: #e8ecf4; line-height: 1.5; }
.sb-brief ul.accept li::before { content: "✓"; position: absolute; left: 0; color: #2dd4bf; font-weight: 700; }
</style>

<div class="sb-brief">
  <h2>Mission: Ship the NovaTech Support AI System</h2>
  <div class="objective">
    <strong>Business context:</strong> The support AI you built now has to run 24/7. You are deploying the FastAPI backend with ticket triage, auto-response, and escalation logic to Railway, wired to the mock CRM for customer context and the mock email service for replies. Once live, it must report response latency, auto-response quality, and escalation rate so the product team can watch for drift.
  </div>

  <h3>Production Constraints</h3>
  <div class="constraints">
    <div class="pill"><strong>Latency SLA</strong><span>p95 &lt; 1.8s</span></div>
    <div class="pill"><strong>Scale Target</strong><span>30 tickets/s burst</span></div>
    <div class="pill"><strong>Cost Budget</strong><span>&lt; $0.009 / ticket</span></div>
    <div class="pill"><strong>Platform</strong><span>Railway (Fly.io fallback)</span></div>
    <div class="pill"><strong>Integrations</strong><span>Mock CRM, Mock Email</span></div>
    <div class="pill"><strong>LLM</strong><span>Claude 3.5 Haiku + Sonnet</span></div>
  </div>

  <h3>Acceptance Criteria</h3>
  <ul class="accept">
    <li><strong>POST /tickets</strong> accepts the ticket payload and returns <code>{priority, auto_response, escalate_to}</code></li>
    <li>Triage tiers: <code>low</code>, <code>medium</code>, <code>high</code>, <code>p0</code> -- <code>p0</code> always escalates, never auto-responds</li>
    <li>CRM lookup merges customer context (plan tier, MRR, last CSAT) before the LLM call</li>
    <li>Auto-responses are sent via the mock email service (idempotent by <code>ticket_id</code>)</li>
    <li>Prometheus-style <code>/metrics</code> endpoint exposes <code>ticket_latency_ms</code>, <code>auto_response_quality</code>, <code>escalation_rate</code></li>
    <li>Validation errors return 422, CRM/email outages return 503, email dedupe hits return 200 with <code>deduped: true</code></li>
    <li>Railway deploy uses <code>railway.json</code> + Dockerfile; health probe at <code>/health</code> returns 200 within 5s of cold start</li>
    <li>Grafana (or Railway metrics) dashboard shows p95 latency, escalation %, and auto-response quality over 24h</li>
  </ul>
</div>
""",
                    "code": """\"\"\"NovaTech Support AI -- Starter Code

FastAPI backend: ticket triage + auto-response + escalation + monitoring.
Deploys to Railway (or Fly.io). Extend the TODOs until all acceptance
criteria pass.
\"\"\"

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections import defaultdict
from typing import Any

import httpx
from anthropic import Anthropic, APIError
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field


# ── Configuration ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CRM_API_URL = os.environ.get("CRM_API_URL", "https://mock-crm.invalid")
CRM_API_KEY = os.environ.get("CRM_API_KEY", "")
EMAIL_API_URL = os.environ.get("EMAIL_API_URL", "https://mock-email.invalid")
EMAIL_API_KEY = os.environ.get("EMAIL_API_KEY", "")

TRIAGE_MODEL = os.environ.get("TRIAGE_MODEL", "claude-3-5-haiku-20241022")
RESPONSE_MODEL = os.environ.get("RESPONSE_MODEL", "claude-3-5-sonnet-20241022")
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "2.5"))

# Token pricing (USD per 1K).
PRICE_HAIKU_IN = 0.0008
PRICE_HAIKU_OUT = 0.004
PRICE_SONNET_IN = 0.003
PRICE_SONNET_OUT = 0.015


# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
)
logger = logging.getLogger("support-ai")


def jlog(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, default=str))


# ── Clients ────────────────────────────────────────────────────
claude = Anthropic(api_key=ANTHROPIC_API_KEY)


# ── Schemas ────────────────────────────────────────────────────
class TicketRequest(BaseModel):
    ticket_id: str = Field(min_length=3, max_length=60)
    customer_id: str = Field(min_length=1, max_length=60)
    customer_email: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=6000)
    channel: str = Field(default="email", pattern="^(email|web|chat|api)$")


class TicketResponse(BaseModel):
    ticket_id: str
    priority: str  # "low" | "medium" | "high" | "p0"
    auto_response: str | None
    escalate_to: str | None
    confidence: float
    cost: float
    latency_ms: int
    deduped: bool = False


# ── In-memory metrics + dedupe (swap for Redis in prod) ───────
_sent_tickets: set[str] = set()
_metrics = {
    "latency_ms_hist": [],
    "quality_scores": [],
    "escalations": 0,
    "total": 0,
}


def _record_metric(latency_ms: int, quality: float, escalated: bool) -> None:
    _metrics["latency_ms_hist"].append(latency_ms)
    _metrics["quality_scores"].append(quality)
    _metrics["total"] += 1
    if escalated:
        _metrics["escalations"] += 1
    # Keep window bounded (last 10k).
    for key in ("latency_ms_hist", "quality_scores"):
        if len(_metrics[key]) > 10_000:
            _metrics[key] = _metrics[key][-10_000:]


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(p * len(ordered)))
    return ordered[idx]


# ── Integrations ──────────────────────────────────────────────
async def crm_lookup(customer_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                f"{CRM_API_URL}/customers/{customer_id}",
                headers={"Authorization": f"Bearer {CRM_API_KEY}"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        jlog("crm_error", customer_id=customer_id, error=str(exc))
        raise HTTPException(status_code=503, detail="CRM lookup failed")


async def send_email(ticket_id: str, to: str, body: str) -> bool:
    if ticket_id in _sent_tickets:
        jlog("email_dedup", ticket_id=ticket_id)
        return False
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{EMAIL_API_URL}/send",
                headers={"Authorization": f"Bearer {EMAIL_API_KEY}"},
                json={"to": to, "body": body, "idempotency_key": ticket_id},
            )
            resp.raise_for_status()
    except Exception as exc:
        jlog("email_error", ticket_id=ticket_id, error=str(exc))
        raise HTTPException(status_code=503, detail="Email service unavailable")
    _sent_tickets.add(ticket_id)
    return True


# ── LLM calls ─────────────────────────────────────────────────
TRIAGE_PROMPT = (
    "You are a support triage classifier. Given a ticket and customer context, "
    'return ONLY JSON: {"priority": "low|medium|high|p0", "confidence": 0..1, '
    '"rationale": "<1 line>"}. Score p0 for outages, data loss, security, or '
    "enterprise ($2k+ MRR) urgent issues. Be conservative with p0."
)

AUTO_REPLY_PROMPT = (
    "You are a courteous support engineer writing a reply. Given the triaged "
    "ticket and customer context, write a concise reply (<=120 words) that "
    "acknowledges the issue, provides next steps, and never fabricates. "
    "If you are unsure, state that a specialist will follow up."
)


def _cost_haiku(tokens_in: int, tokens_out: int) -> float:
    return round(
        (tokens_in / 1000) * PRICE_HAIKU_IN + (tokens_out / 1000) * PRICE_HAIKU_OUT, 6
    )


def _cost_sonnet(tokens_in: int, tokens_out: int) -> float:
    return round(
        (tokens_in / 1000) * PRICE_SONNET_IN + (tokens_out / 1000) * PRICE_SONNET_OUT, 6
    )


def triage(req: TicketRequest, crm: dict) -> tuple[dict, float]:
    payload = {"ticket": req.model_dump(), "customer": crm}
    try:
        resp = claude.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=180,
            system=TRIAGE_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload)}],
        )
    except APIError as exc:
        raise HTTPException(status_code=503, detail=f"Triage model error: {exc}")

    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Triage returned invalid JSON")

    cost = _cost_haiku(resp.usage.input_tokens, resp.usage.output_tokens)
    return parsed, cost


def draft_reply(req: TicketRequest, crm: dict, triage_out: dict) -> tuple[str, float, float]:
    payload = {"ticket": req.model_dump(), "customer": crm, "triage": triage_out}
    try:
        resp = claude.messages.create(
            model=RESPONSE_MODEL,
            max_tokens=400,
            system=AUTO_REPLY_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload)}],
        )
    except APIError as exc:
        raise HTTPException(status_code=503, detail=f"Response model error: {exc}")

    body = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    cost = _cost_sonnet(resp.usage.input_tokens, resp.usage.output_tokens)
    # Simple quality heuristic until you add an LLM-as-judge: length + required phrases.
    quality = min(1.0, len(body) / 400) * (0.5 + 0.5 * ("follow up" in body.lower() or "resolve" in body.lower()))
    return body, cost, round(quality, 3)


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="NovaTech Support AI", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "triage_model": TRIAGE_MODEL, "response_model": RESPONSE_MODEL}


@app.get("/metrics")
async def metrics() -> Response:
    p50 = _percentile(_metrics["latency_ms_hist"], 0.50)
    p95 = _percentile(_metrics["latency_ms_hist"], 0.95)
    escalation_rate = (_metrics["escalations"] / _metrics["total"]) if _metrics["total"] else 0.0
    avg_quality = (
        sum(_metrics["quality_scores"]) / len(_metrics["quality_scores"])
        if _metrics["quality_scores"] else 0.0
    )
    body = (
        f"# HELP ticket_latency_ms Ticket handling latency in ms\\n"
        f"# TYPE ticket_latency_ms summary\\n"
        f"ticket_latency_ms{{quantile=\\"0.5\\"}} {p50:.0f}\\n"
        f"ticket_latency_ms{{quantile=\\"0.95\\"}} {p95:.0f}\\n"
        f"# TYPE escalation_rate gauge\\n"
        f"escalation_rate {escalation_rate:.3f}\\n"
        f"# TYPE auto_response_quality gauge\\n"
        f"auto_response_quality {avg_quality:.3f}\\n"
        f"# TYPE tickets_total counter\\n"
        f"tickets_total {_metrics['total']}\\n"
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")


@app.post("/tickets", response_model=TicketResponse)
async def handle_ticket(req: TicketRequest) -> TicketResponse:
    started = time.perf_counter()
    req_id = str(uuid.uuid4())

    crm = await crm_lookup(req.customer_id)
    triage_out, triage_cost = triage(req, crm)
    priority = triage_out.get("priority", "medium")
    confidence = float(triage_out.get("confidence", 0.0))

    auto_response: str | None = None
    escalate_to: str | None = None
    deduped = False
    quality = 0.0
    reply_cost = 0.0

    if priority == "p0" or confidence < 0.6:
        escalate_to = "tier2-oncall@novatech.example" if priority == "p0" else "tier1-queue"
    else:
        auto_response, reply_cost, quality = draft_reply(req, crm, triage_out)
        sent = await send_email(req.ticket_id, req.customer_email, auto_response)
        deduped = not sent

    latency_ms = int((time.perf_counter() - started) * 1000)
    total_cost = round(triage_cost + reply_cost, 6)
    _record_metric(latency_ms, quality, escalate_to is not None)

    jlog(
        "ticket_handled",
        request_id=req_id,
        ticket_id=req.ticket_id,
        priority=priority,
        confidence=confidence,
        escalate_to=escalate_to,
        auto_response_sent=bool(auto_response and not deduped),
        deduped=deduped,
        latency_ms=latency_ms,
        cost=total_cost,
        quality=quality,
    )

    return TicketResponse(
        ticket_id=req.ticket_id,
        priority=priority,
        auto_response=auto_response,
        escalate_to=escalate_to,
        confidence=confidence,
        cost=total_cost,
        latency_ms=latency_ms,
        deduped=deduped,
    )
""",
                    "expected_output": None,
                    "deployment_config": {
                        "platform": "railway",
                        "service": "container",
                        "dockerfile": """FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
""",
                        "requirements": (
                            "fastapi>=0.115.0\n"
                            "uvicorn[standard]>=0.30.0\n"
                            "pydantic[email]>=2.6.0\n"
                            "httpx>=0.27.0\n"
                            "anthropic>=0.39.0\n"
                        ),
                        "infra_hint": (
                            "Create a Railway project with a `railway.json` that sets "
                            '{"build": {"builder": "DOCKERFILE"}, "deploy": '
                            '{"healthcheckPath": "/health", "startCommand": '
                            '"uvicorn app:app --host 0.0.0.0 --port $PORT"}}. '
                            "Set ANTHROPIC_API_KEY, CRM_API_URL/KEY, EMAIL_API_URL/KEY as service variables. "
                            "Point a Grafana Cloud Prometheus scrape job at /metrics, or wire the built-in "
                            "Railway metrics to a Slack webhook when p95 > 1800ms."
                        ),
                    },
                    "demo_data": {
                        "phases": [
                            {"id": "local", "title": "Local Build"},
                            {"id": "docker", "title": "Containerize"},
                            {"id": "deploy", "title": "Deploy to Railway"},
                            {"id": "test", "title": "Monitor"},
                        ],
                        "checklist": [
                            {"id": "check_endpoint", "label": "POST /tickets returns {priority, auto_response, escalate_to} with correct shape"},
                            {"id": "check_p0", "label": "p0 tickets always escalate and never auto-respond"},
                            {"id": "check_crm", "label": "CRM lookup enriches customer context before the LLM call"},
                            {"id": "check_email", "label": "Auto-responses are sent via the email service and deduped by ticket_id"},
                            {"id": "check_metrics", "label": "/metrics exposes ticket_latency_ms, auto_response_quality, escalation_rate"},
                            {"id": "check_errors", "label": "Invalid input returns 422; CRM/email outages return 503"},
                            {"id": "check_docker", "label": "Dockerfile builds and runs on localhost:8080"},
                            {"id": "check_deploy", "label": "Deployed to Railway; /health returns 200 and public URL is live"},
                            {"id": "check_monitor", "label": "Dashboard shows p95 latency, escalation rate, and auto-response quality over 24h"},
                            {"id": "check_cost", "label": "Average per-ticket cost stays below $0.009"},
                        ],
                    },
                    "validation": {
                        "endpoint_check": {
                            "method": "POST",
                            "path": "/tickets",
                            "body": {
                                "ticket_id": "TKT-20260418-0007",
                                "customer_id": "cus_A8472",
                                "customer_email": "dana@acme.example",
                                "subject": "Dashboard widgets not loading after upgrade",
                                "body": "Since the upgrade this morning, our analytics widgets on the main dashboard return a 500 intermittently. We use this for exec reporting and the weekly board meeting is tomorrow.",
                                "channel": "email",
                            },
                            "expected_status": 200,
                            "expected_fields": ["ticket_id", "priority", "auto_response", "escalate_to", "confidence", "cost", "latency_ms"],
                        },
                    },
                },
            ],
        },
    ],
}
