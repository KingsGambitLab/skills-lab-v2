"""
Case Study Course: The Stolen Vehicle Investigation
An immersive investigation scenario teaching claims processing with AI tools.
"""

COURSE = {
    "id": "stolen-vehicle-case",
    "title": "The Stolen Vehicle Investigation",
    "subtitle": "Investigate a suspicious auto theft claim from intake to resolution",
    "icon": "🔍",
    "course_type": "case_study",
    "level": "Intermediate",
    "tags": ["claims", "fraud-detection", "investigation", "case-study", "python"],
    "estimated_time": "~2 hours",
    "description": (
        "A high-value stolen vehicle claim just hit your desk. The policy holder says "
        "their 2024 Range Rover was stolen overnight, but something doesn't add up. "
        "You'll investigate the claim, build automated investigation tools, and decide "
        "whether to approve, deny, or escalate -- all based on evidence you uncover."
    ),
    "modules": [
        # ── Module 1: The Brief ───────────────────────────────────────
        {
            "position": 1,
            "title": "The Brief",
            "subtitle": "Receive the claim and begin your investigation",
            "estimated_time": "25 min",
            "objectives": [
                "Assess initial claim details and identify red flags",
                "Make sound investigation decisions under uncertainty",
                "Categorize fraud indicators by type",
            ],
            "steps": [
                # Step 1 — concept (case setup)
                {
                    "position": 1,
                    "title": "Incoming: CLM-2025-0847",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.inv-demo { background: #1e2538; border: 1px solid #2a3352; border-radius: 12px; padding: 22px; margin: 16px 0; color: #e8ecf4; font-family: 'Inter', system-ui, sans-serif; }
.inv-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.inv-demo .hook { background: linear-gradient(135deg, #151b2e, #252e45); border-left: 4px solid #2dd4bf; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 18px; }
.inv-demo .hook strong { color: #2dd4bf; }
.inv-demo .scene { background: #151b2e; border: 1px solid #2a3352; border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; font-size: 0.92em; line-height: 1.6; }
.inv-demo .scene strong { color: #fbbf24; }
.inv-demo .timer { display: inline-block; background: #2a1820; border: 1px solid #f87171; color: #f87171; padding: 4px 10px; border-radius: 4px; font-family: 'Fira Code', monospace; font-weight: 700; font-size: 0.95em; margin-left: 10px; }
.inv-demo .sources { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-top: 14px; }
.inv-demo .source { background: #151b2e; border: 1px solid #2a3352; border-radius: 8px; padding: 12px; cursor: pointer; transition: all 0.2s; user-select: none; }
.inv-demo .source:hover { border-color: #4a7cff; transform: translateY(-2px); }
.inv-demo .source.picked { border-color: #2dd4bf; background: rgba(45,212,191,0.08); }
.inv-demo .source.locked { opacity: 0.45; pointer-events: none; }
.inv-demo .source .name { font-weight: 600; color: #e8ecf4; font-size: 0.95em; }
.inv-demo .source .desc { color: #8b95b0; font-size: 0.78em; margin-top: 4px; }
.inv-demo .picked-tag { float: right; background: #2dd4bf; color: #151b2e; font-size: 0.7em; padding: 2px 7px; border-radius: 3px; font-weight: 700; }
.inv-demo .counter { margin: 12px 0; color: #8b95b0; font-size: 0.88em; }
.inv-demo .counter b { color: #4a7cff; }
.inv-demo .btn-inv { background: #4a7cff; color: #fff; border: none; padding: 10px 22px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 10px; transition: background 0.2s; }
.inv-demo .btn-inv:hover { background: #3a6cef; }
.inv-demo .btn-inv:disabled { background: #2a3352; cursor: not-allowed; }
.inv-demo .btn-reset { background: transparent; color: #8b95b0; border: 1px solid #2a3352; padding: 10px 16px; border-radius: 6px; cursor: pointer; margin-left: 8px; font-size: 0.88em; }
.inv-demo .btn-reset:hover { color: #e8ecf4; border-color: #4a7cff; }
.inv-demo .report { display: none; margin-top: 16px; background: #0d1117; border: 1px solid #2a3352; border-radius: 8px; padding: 16px; }
.inv-demo .report.show { display: block; }
.inv-demo .verdict { padding: 12px 14px; border-radius: 6px; margin-bottom: 12px; font-weight: 600; }
.inv-demo .verdict.win { background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.3); color: #2dd4bf; }
.inv-demo .verdict.mixed { background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; }
.inv-demo .verdict.fail { background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3); color: #f87171; }
.inv-demo .trace { margin-top: 10px; font-size: 0.88em; line-height: 1.6; }
.inv-demo .trace-row { padding: 8px 0; border-bottom: 1px solid #1e2538; display: flex; align-items: flex-start; gap: 10px; }
.inv-demo .trace-row:last-child { border-bottom: none; }
.inv-demo .trace-icon { flex-shrink: 0; width: 20px; }
.inv-demo .trace .name { font-weight: 600; color: #e8ecf4; }
.inv-demo .trace .outcome.good { color: #2dd4bf; }
.inv-demo .trace .outcome.bad { color: #f87171; }
.inv-demo .trace .outcome.neutral { color: #8b95b0; }
</style>

<div class="inv-demo">
  <h2>Investigation Dashboard <span class="timer" id="invTimer">02:00:00</span></h2>
  <div class="hook">
    <strong>The problem:</strong> An insurance claim worth $45,000 comes in. You have 2 hours before the thief crosses state lines.
  </div>

  <div class="scene">
    <strong>Scene:</strong> 2:14 AM. A silver 2022 Toyota Camry reported stolen from a downtown parking garage in Phoenix. The claimant says she came back from a concert and the car was gone. Her phone was dead. She waited 40 minutes at a nearby diner before filing the report. Dashcam on the garage caught a figure in a hoodie walking past her car 8 minutes before it left. Highway cameras last pinged the plate headed east on I-10 toward New Mexico. You have 7 data sources. Budget: <strong>3 checks</strong>. Choose wisely.
  </div>

  <div class="counter">Picked: <b id="invCount">0</b> / 3 sources</div>

  <div class="sources" id="invSources">
    <div class="source" data-id="cctv" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Parking Garage CCTV</div>
      <div class="desc">Last 6 hours of camera feed</div>
    </div>
    <div class="source" data-id="gps" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Vehicle GPS Ping</div>
      <div class="desc">Built-in telematics, real-time location</div>
    </div>
    <div class="source" data-id="social" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Social Media Scan</div>
      <div class="desc">Claimants public posts, check-ins</div>
    </div>
    <div class="source" data-id="police" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Police Report Log</div>
      <div class="desc">Active bulletins, nearby thefts</div>
    </div>
    <div class="source" data-id="insurance" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Insurance History</div>
      <div class="desc">Prior claims, carrier records</div>
    </div>
    <div class="source" data-id="telemetry" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Vehicle Telemetry</div>
      <div class="desc">Engine, door, ignition events</div>
    </div>
    <div class="source" data-id="witness" onclick="pickSource(this)">
      <span class="picked-tag" style="display:none;">PICKED</span>
      <div class="name">Eyewitness Accounts</div>
      <div class="desc">Diner staff, nearby pedestrians</div>
    </div>
  </div>

  <button class="btn-inv" id="invGoBtn" onclick="runInvestigation()" disabled>Dispatch Investigation</button>
  <button class="btn-reset" onclick="resetInvestigation()">Reset</button>

  <div class="report" id="invReport">
    <div class="verdict" id="invVerdict"></div>
    <div class="trace" id="invTrace"></div>
  </div>
</div>

<script>
(function(){
  var picks = [];
  var sourceData = {
    cctv:      {name: "Parking Garage CCTV",  good: true,  result: "HIT. Hoodie figure at 2:06 AM. Clear face frame, 0.7s.", weight: 3},
    gps:       {name: "Vehicle GPS Ping",     good: true,  result: "HIT. Vehicle currently at mile 164 on I-10, moving 82 mph east.", weight: 4},
    social:    {name: "Social Media Scan",    good: false, result: "NOISE. Three concert selfies, no red flags. Wasted 40 min.", weight: 0},
    police:    {name: "Police Report Log",    good: true,  result: "HIT. 4 other Camry thefts in same garage this month. Organized ring.", weight: 2},
    insurance: {name: "Insurance History",    good: false, result: "CLEAN. No prior claims. Useful later, not now.", weight: 0},
    telemetry: {name: "Vehicle Telemetry",    good: true,  result: "HIT. Ignition started without key fob at 2:08 AM. Relay attack signature.", weight: 3},
    witness:   {name: "Eyewitness Accounts",  good: false, result: "WEAK. Diner staff saw nothing. No pedestrians. Dead end.", weight: 0}
  };

  function updateUI() {
    document.getElementById('invCount').textContent = picks.length;
    document.getElementById('invGoBtn').disabled = picks.length !== 3;
    document.querySelectorAll('.inv-demo .source').forEach(function(el){
      var id = el.dataset.id;
      var isPicked = picks.indexOf(id) > -1;
      el.classList.toggle('picked', isPicked);
      el.querySelector('.picked-tag').style.display = isPicked ? 'inline-block' : 'none';
      el.classList.toggle('locked', !isPicked && picks.length >= 3);
    });
  }

  window.pickSource = function(el) {
    var id = el.dataset.id;
    var idx = picks.indexOf(id);
    if (idx > -1) {
      picks.splice(idx, 1);
    } else if (picks.length < 3) {
      picks.push(id);
    }
    updateUI();
  };

  window.resetInvestigation = function() {
    picks = [];
    document.getElementById('invReport').classList.remove('show');
    updateUI();
  };

  window.runInvestigation = function() {
    var totalScore = 0;
    var traceHTML = '';
    picks.forEach(function(id){
      var s = sourceData[id];
      totalScore += s.weight;
      var cls = s.good ? 'good' : 'bad';
      var icon = s.good ? 'HIT' : 'MISS';
      traceHTML += '<div class="trace-row">'
        + '<span class="trace-icon outcome ' + cls + '">' + icon + '</span>'
        + '<div><div class="name">' + s.name + '</div>'
        + '<div class="outcome ' + cls + '">' + s.result + '</div></div>'
        + '</div>';
    });

    var v = document.getElementById('invVerdict');
    if (totalScore >= 9) {
      v.className = 'verdict win';
      v.innerHTML = 'THIEF INTERCEPTED. Score ' + totalScore + '/10. '
        + 'State patrol stopped the Camry at mile 172. Driver arrested. Claim approved. Time remaining: 1h 12m. '
        + 'You picked the sources that move the case forward, not the ones that feel reassuring.';
    } else if (totalScore >= 5) {
      v.className = 'verdict mixed';
      v.innerHTML = 'PARTIAL WIN. Score ' + totalScore + '/10. '
        + 'You got a lead but missed a faster path. The thief crossed the border before you pulled telemetry. '
        + 'Try again -- which signals cut hours off the timeline?';
    } else {
      v.className = 'verdict fail';
      v.innerHTML = 'TRAIL WENT COLD. Score ' + totalScore + '/10. '
        + 'You spent the 2 hours on sources that tell you WHO the claimant is, not WHERE the car is. '
        + 'Hint: real-time signals (GPS, CCTV, telemetry) win early. Background data (social, history) wins later.';
    }
    document.getElementById('invTrace').innerHTML = traceHTML;
    document.getElementById('invReport').classList.add('show');
  };
})();
</script>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — scenario_branch
                {
                    "position": 2,
                    "title": "First Moves",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>You've just received the claim. Walk through the initial investigation
decisions. Each choice affects what information you uncover.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "Claim CLM-2025-0847 has landed on your desk. It's a high-value "
                            "stolen vehicle claim with a few details that caught the intake "
                            "team's attention. You need to decide your first investigative steps."
                        ),
                        "steps": [
                            {
                                "question": "What's your first investigative action?",
                                "options": [
                                    {
                                        "label": "Call Derek immediately and ask pointed questions about the theft",
                                        "correct": False,
                                        "explanation": (
                                            "Confronting the claimant before gathering evidence is a common "
                                            "mistake. You have no leverage and might tip him off if fraud is "
                                            "involved. Always build your evidence base first."
                                        ),
                                    },
                                    {
                                        "label": "Pull the full policy history and claims record",
                                        "correct": True,
                                        "explanation": (
                                            "Correct. The policy history will reveal purchase timing, coverage "
                                            "changes, prior claims, and payment patterns -- all critical context "
                                            "before you talk to anyone."
                                        ),
                                    },
                                    {
                                        "label": "Send the claim straight to the Special Investigations Unit",
                                        "correct": False,
                                        "explanation": (
                                            "Premature. SIU referrals should be backed by evidence, not hunches. "
                                            "A few intake notes don't meet the threshold. Investigate first."
                                        ),
                                    },
                                    {
                                        "label": "Approve the claim quickly to hit your processing targets",
                                        "correct": False,
                                        "explanation": (
                                            "Never prioritize speed over diligence on a high-value claim. "
                                            "An $87,500 payout with red flags demands investigation."
                                        ),
                                    },
                                ],
                                "tool_used": "lookup_policy_history('POL-55219')",
                                "result": (
                                    "Policy purchased: November 12, 2024 (4 months ago)\n"
                                    "Coverage: Comprehensive, $500 deductible\n"
                                    "Premium: $340/month -- CURRENT\n"
                                    "Prior claims on this policy: 0\n"
                                    "Prior policies with us: None (new customer)\n"
                                    "Coverage increase: +$6,000 added Feb 28, 2025 (aftermarket wheels)\n"
                                    "Notable: Coverage increase was 16 days before reported theft"
                                ),
                            },
                            {
                                "question": "The coverage was increased just 16 days before the theft. What's your next step?",
                                "options": [
                                    {
                                        "label": "Check if there's a pattern of claims across Derek's other insurance providers",
                                        "correct": True,
                                        "explanation": (
                                            "Good instinct. Running a cross-carrier check through the NICB "
                                            "(National Insurance Crime Bureau) database will reveal if Derek "
                                            "has a history of suspicious claims elsewhere."
                                        ),
                                    },
                                    {
                                        "label": "The timing is suspicious enough -- deny the claim now",
                                        "correct": False,
                                        "explanation": (
                                            "Timing alone isn't grounds for denial. People legitimately add "
                                            "coverage for new accessories. You need corroborating evidence "
                                            "to make a defensible decision."
                                        ),
                                    },
                                    {
                                        "label": "Request the police report and wait for it to arrive",
                                        "correct": False,
                                        "explanation": (
                                            "You should get the police report, but passively waiting wastes "
                                            "investigation time. Run parallel checks while the report is "
                                            "being retrieved."
                                        ),
                                    },
                                ],
                                "tool_used": "nicb_check('Derek Whitfield', vin='SALYA2BU5RA123456')",
                                "result": (
                                    "NICB Database Results:\n"
                                    "- Derek Whitfield: 1 prior theft claim (2021, different carrier, Ford F-150, $42,000, PAID)\n"
                                    "- VIN SALYA2BU5RA123456: No prior reports\n"
                                    "- Address match: Current address matches 2021 claim address"
                                ),
                            },
                            {
                                "question": "Derek had a prior theft claim that was paid out. Combined with the recent coverage increase, how do you proceed?",
                                "options": [
                                    {
                                        "label": "Request a recorded statement from Derek and order a vehicle title history",
                                        "correct": True,
                                        "explanation": (
                                            "Exactly right. A recorded statement locks in his account, and "
                                            "the title history will reveal if there are liens or financial "
                                            "pressure. You're building a complete picture before making "
                                            "any determination."
                                        ),
                                    },
                                    {
                                        "label": "Two theft claims is clearly fraud. Refer to SIU and deny",
                                        "correct": False,
                                        "explanation": (
                                            "Two claims over 4 years is unusual but not proof of fraud. "
                                            "Some people are genuinely unlucky, and some neighborhoods have "
                                            "high theft rates. You need more evidence for a defensible denial."
                                        ),
                                    },
                                    {
                                        "label": "Hire a private investigator to follow Derek",
                                        "correct": False,
                                        "explanation": (
                                            "Surveillance is expensive and premature at this stage. You "
                                            "haven't exhausted cheaper investigation methods yet. PI work "
                                            "is a later-stage tool if other evidence supports it."
                                        ),
                                    },
                                ],
                                "tool_used": "schedule_recorded_statement('CLM-2025-0847') + order_title_history('SALYA2BU5RA123456')",
                                "result": (
                                    "Recorded statement scheduled: March 22, 2025, 2:00 PM\n"
                                    "Title history ordered -- ETA: 1-2 business days\n"
                                    "Preliminary title check: Vehicle has an outstanding loan of $62,000 "
                                    "with Capital One Auto Finance"
                                ),
                            },
                        ],
                        "insight": (
                            "A good investigation builds evidence methodically: policy history first, "
                            "then cross-carrier checks, then recorded statements. Each step informs "
                            "the next. Never jump to conclusions without corroborating evidence, "
                            "and never confront a claimant before you have the full picture."
                        ),
                    },
                },
                # Step 3 — categorization
                {
                    "position": 3,
                    "title": "Classify the Red Flags",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>Based on what you've uncovered so far, sort these red flags into the
correct categories. Understanding <em>why</em> something is a red flag
helps you write stronger investigation reports.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Sort these red flags into the correct investigation category.",
                        "categories": [
                            "Documentation Issues",
                            "Behavioral Red Flags",
                            "Financial Anomalies",
                        ],
                        "items": [
                            {
                                "text": "No home security cameras despite owning an $87,500 vehicle",
                                "correct_category": "Behavioral Red Flags",
                            },
                            {
                                "text": "Coverage increased 16 days before reported theft",
                                "correct_category": "Financial Anomalies",
                            },
                            {
                                "text": "Prior theft claim with a different carrier in 2021",
                                "correct_category": "Financial Anomalies",
                            },
                            {
                                "text": "Spare key location described vaguely as 'somewhere in the house'",
                                "correct_category": "Behavioral Red Flags",
                            },
                            {
                                "text": "Outstanding $62,000 auto loan on the vehicle",
                                "correct_category": "Financial Anomalies",
                            },
                            {
                                "text": "Police report filed promptly the morning after discovery",
                                "correct_category": "Documentation Issues",
                            },
                            {
                                "text": "Claimant is a new customer with no prior relationship",
                                "correct_category": "Behavioral Red Flags",
                            },
                            {
                                "text": "$6,000 aftermarket wheels added recently with receipts",
                                "correct_category": "Documentation Issues",
                            },
                            {
                                "text": "Vehicle has a remaining loan balance exceeding its depreciated value",
                                "correct_category": "Financial Anomalies",
                            },
                        ],
                    },
                },
            ],
        },
        # ── Module 2: Build the Investigation Engine ──────────────────
        {
            "position": 2,
            "title": "Build the Investigation Engine",
            "subtitle": "Create automated tools for claims investigation",
            "estimated_time": "40 min",
            "objectives": [
                "Understand the architecture of an automated investigation system",
                "Build a fraud scoring function",
                "Review and debug investigation code",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "Architecture of an Automated Investigator",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>How the Investigation Engine Works</h2>
<p>We'll build a three-stage pipeline that mirrors what you did manually in Module 1,
but automated and scalable.</p>

<h3>Stage 1: Data Gathering</h3>
<p>Pull all relevant data sources in parallel:</p>
<ul>
  <li><strong>Policy lookup</strong> -- coverage, history, payment status</li>
  <li><strong>NICB check</strong> -- cross-carrier claim history</li>
  <li><strong>Vehicle history</strong> -- title, liens, prior damage reports</li>
  <li><strong>Claimant profile</strong> -- address history, related policies</li>
</ul>

<h3>Stage 2: Risk Scoring</h3>
<p>Each data point generates a weighted risk signal. The fraud scoring function
combines these into an overall risk score (0.0 to 1.0):</p>
<table>
  <tr><th>Signal</th><th>Weight</th><th>Example</th></tr>
  <tr><td>Recent coverage increase</td><td>0.15</td><td>+$6K added 16 days before theft</td></tr>
  <tr><td>Prior theft claims</td><td>0.20</td><td>1 prior claim, different carrier</td></tr>
  <tr><td>Financial pressure</td><td>0.25</td><td>Loan exceeds vehicle value</td></tr>
  <tr><td>New customer</td><td>0.10</td><td>Policy opened 4 months ago</td></tr>
  <tr><td>Documentation gaps</td><td>0.15</td><td>No security footage available</td></tr>
  <tr><td>Behavioral indicators</td><td>0.15</td><td>Vague details on spare key</td></tr>
</table>

<h3>Stage 3: Decision & Routing</h3>
<p>Based on the risk score:</p>
<ul>
  <li><strong>0.0 - 0.3:</strong> Auto-approve (with human review for claims > $10K)</li>
  <li><strong>0.3 - 0.6:</strong> Standard investigation track</li>
  <li><strong>0.6 - 0.8:</strong> Enhanced investigation + SIU review</li>
  <li><strong>0.8 - 1.0:</strong> Immediate SIU referral</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — code (run policy lookup)
                {
                    "position": 2,
                    "title": "Run the Policy Lookup Tool",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Here's the policy lookup tool that powers Stage 1. Run it to see the
data structure our fraud scorer will consume.</p>
""",
                    "code": """from datetime import datetime, timedelta

# Simulated policy database
POLICY_DB = {
    "POL-55219": {
        "policy_number": "POL-55219",
        "holder": "Derek Whitfield",
        "holder_age": 34,
        "address": "1847 Maple Drive, Riverside, CA 92501",
        "vehicle": {
            "year": 2024,
            "make": "Land Rover",
            "model": "Range Rover Sport",
            "color": "Black",
            "vin": "SALYA2BU5RA123456",
            "declared_value": 87500,
        },
        "coverage": {
            "type": "comprehensive",
            "deductible": 500,
            "effective_date": "2024-11-12",
            "modifications": [
                {
                    "date": "2025-02-28",
                    "type": "coverage_increase",
                    "amount": 6000,
                    "reason": "aftermarket_wheels",
                }
            ],
        },
        "payment": {
            "monthly_premium": 340,
            "status": "current",
            "autopay": True,
        },
        "prior_claims": [],
        "customer_since": "2024-11-12",
    }
}

def lookup_policy(policy_number: str) -> dict:
    \"\"\"Look up a policy and compute derived risk fields.\"\"\"
    policy = POLICY_DB.get(policy_number)
    if not policy:
        return {"error": f"Policy {policy_number} not found"}

    # Compute derived fields
    effective = datetime.strptime(policy["coverage"]["effective_date"], "%Y-%m-%d")
    policy_age_days = (datetime.now() - effective).days

    recent_modifications = [
        m for m in policy["coverage"]["modifications"]
        if (datetime.now() - datetime.strptime(m["date"], "%Y-%m-%d")).days < 30
    ]

    return {
        **policy,
        "_derived": {
            "policy_age_days": policy_age_days,
            "is_new_customer": policy_age_days < 180,
            "recent_coverage_changes": len(recent_modifications),
            "total_recent_increase": sum(m["amount"] for m in recent_modifications),
        }
    }

# Run it
import json
result = lookup_policy("POL-55219")
print(json.dumps(result, indent=2, default=str))
print()
print("--- Derived Risk Fields ---")
for k, v in result["_derived"].items():
    print(f"  {k}: {v}")
""",
                    "expected_output": """--- Derived Risk Fields ---
  policy_age_days: 127
  is_new_customer: True
  recent_coverage_changes: 1
  total_recent_increase: 6000""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 — code_exercise (fraud scoring)
                {
                    "position": 3,
                    "title": "Build the Fraud Scoring Function",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build the fraud scoring function that takes claim data from multiple sources
and computes a weighted risk score. Each signal contributes a score between 0.0
and 1.0, weighted by its importance.</p>
""",
                    "code": """def score_fraud_risk(claim_data: dict) -> dict:
    \"\"\"Compute a fraud risk score from aggregated claim data.

    Args:
        claim_data: dict with keys:
            - policy: policy lookup result (with _derived fields)
            - nicb: cross-carrier check result
            - vehicle_history: title and lien information
            - incident: details of the reported incident

    Returns:
        dict with:
            - total_score: float 0.0-1.0
            - signals: list of {name, score, weight, weighted_score, detail}
            - recommendation: "auto_approve" | "standard_investigation" |
                              "enhanced_investigation" | "siu_referral"
    \"\"\"
    signals = []

    # TODO: Check for recent coverage increases (weight: 0.15)
    # If coverage was increased within 30 days of incident, signal = 0.8-1.0
    # If within 60 days, signal = 0.5
    # Otherwise, signal = 0.0

    # TODO: Check for prior theft claims via NICB (weight: 0.20)
    # 0 prior claims = 0.0, 1 prior = 0.6, 2+ prior = 1.0

    # TODO: Check for financial pressure (weight: 0.25)
    # If outstanding loan > declared vehicle value, signal = 0.9
    # If outstanding loan > 70% of value, signal = 0.5
    # Otherwise, signal = 0.1

    # TODO: Check new customer status (weight: 0.10)
    # Policy < 6 months = 0.7, < 12 months = 0.3, otherwise 0.0

    # TODO: Check documentation gaps (weight: 0.15)
    # Missing security footage = 0.4, missing police report = 0.8
    # Both missing = 1.0, neither missing = 0.0

    # TODO: Check behavioral indicators (weight: 0.15)
    # Vague details = 0.5, inconsistent story = 0.9, cooperative = 0.1

    # TODO: Calculate total_score as sum of (signal * weight) for each signal

    # TODO: Determine recommendation based on total_score thresholds
    # 0.0-0.3: auto_approve, 0.3-0.6: standard_investigation
    # 0.6-0.8: enhanced_investigation, 0.8-1.0: siu_referral

    return {
        "total_score": 0.0,
        "signals": signals,
        "recommendation": "auto_approve",
    }


# Test with our case data
claim_data = {
    "policy": {
        "declared_value": 87500,
        "_derived": {
            "policy_age_days": 127,
            "is_new_customer": True,
            "recent_coverage_changes": 1,
            "total_recent_increase": 6000,
        },
    },
    "nicb": {
        "prior_theft_claims": 1,
        "prior_total_payouts": 42000,
    },
    "vehicle_history": {
        "outstanding_loan": 62000,
        "loan_to_value_ratio": 0.71,
    },
    "incident": {
        "police_report_filed": True,
        "security_footage_available": False,
        "spare_key_accounted_for": False,
        "claimant_cooperative": True,
        "story_consistent": True,
        "details_vague": True,
    },
}

import json
result = score_fraud_risk(claim_data)
print(json.dumps(result, indent=2))
print(f"\\nVerdict: {result['recommendation'].upper()} (score: {result['total_score']:.2f})")
""",
                    "expected_output": """{
  "total_score": 0.56,
  "signals": [
    {"name": "recent_coverage_increase", "score": 0.8, "weight": 0.15, "weighted_score": 0.12, "detail": "Coverage increased by $6,000 within 30 days of incident"},
    {"name": "prior_theft_claims", "score": 0.6, "weight": 0.20, "weighted_score": 0.12, "detail": "1 prior theft claim totaling $42,000"},
    {"name": "financial_pressure", "score": 0.5, "weight": 0.25, "weighted_score": 0.125, "detail": "Loan-to-value ratio: 71%"},
    {"name": "new_customer", "score": 0.7, "weight": 0.10, "weighted_score": 0.07, "detail": "Policy age: 127 days"},
    {"name": "documentation_gaps", "score": 0.4, "weight": 0.15, "weighted_score": 0.06, "detail": "No security footage available"},
    {"name": "behavioral_indicators", "score": 0.5, "weight": 0.15, "weighted_score": 0.075, "detail": "Some vague details provided"}
  ],
  "recommendation": "standard_investigation"
}

Verdict: STANDARD_INVESTIGATION (score: 0.56)""",
                    "validation": {
                        "must_contain": ["signals", "weight", "total_score", "recommendation"],
                        "must_return_keys": ["total_score", "signals", "recommendation"],
                        "score_range": [0.0, 1.0],
                    },
                    "demo_data": None,
                },
                # Step 4 — code_review
                {
                    "position": 4,
                    "title": "Review the Investigation Pipeline",
                    "step_type": "exercise",
                    "exercise_type": "code_review",
                    "content": """
<p>A junior developer wrote this investigation pipeline. It has 3 bugs that
could cause incorrect fraud determinations or runtime errors. Find them all.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "code": """def run_investigation(claim_id: str, policy_number: str) -> dict:
    \"\"\"Run a full automated investigation on a claim.\"\"\"

    # Stage 1: Gather data
    policy = lookup_policy(policy_number)
    nicb = nicb_check(policy["holder"])
    vehicle = get_vehicle_history(policy["vehicle"]["vin"])

    # Stage 2: Score the risk
    claim_data = {
        "policy": policy,
        "nicb": nicb,
        "vehicle_history": vehicle,
        "incident": get_incident_details(claim_id),
    }

    risk = score_fraud_risk(claim_data)

    # Stage 3: Route the decision
    if risk["total_score"] > 0.8:
        decision = "siu_referral"
    elif risk["total_score"] > 0.6:
        decision = "enhanced_investigation"
    elif risk["total_score"] > 0.3:
        decision = "standard_investigation"
    else:
        decision = "auto_approve"

    # Log the decision
    save_investigation(claim_id, {
        "risk_score": risk["total_score"],
        "decision": decision,
        "signals": risk["signals"],
        "investigated_by": "auto_pipeline_v1",
    })

    # Notify if high risk
    if risk["total_score"] > 0.6:
        send_alert(
            to="siu@company.com",
            subject=f"High-risk claim: {claim_id}",
            body=f"Risk score: {risk['total_score']}. Decision: {decision}",
        )

    return {
        "claim_id": claim_id,
        "decision": decision,
        "risk_score": risk["total_score"],
    }""",
                        "bugs": [
                            {
                                "line": 5,
                                "issue": "No error handling for policy lookup failure",
                                "severity": "high",
                                "hint": (
                                    "What happens if lookup_policy returns an error dict "
                                    "(e.g., policy not found)? Line 6 accesses policy['holder'] "
                                    "which would throw a KeyError."
                                ),
                            },
                            {
                                "line": 20,
                                "issue": "Decision routing duplicates score_fraud_risk logic and can diverge",
                                "severity": "medium",
                                "hint": (
                                    "The score_fraud_risk function already returns a 'recommendation' "
                                    "field, but this code re-implements the thresholds. If someone "
                                    "updates the thresholds in one place but not the other, the system "
                                    "will make inconsistent decisions."
                                ),
                            },
                            {
                                "line": 37,
                                "issue": "Alert threshold doesn't match SIU referral threshold",
                                "severity": "medium",
                                "hint": (
                                    "The alert fires for scores > 0.6 (enhanced_investigation), "
                                    "but the email says 'High-risk claim' and goes to SIU. An enhanced "
                                    "investigation isn't necessarily an SIU case -- this could cause "
                                    "alert fatigue and desensitize the SIU team."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        # ── Module 3: Ship & Defend ───────────────────────────────────
        {
            "position": 3,
            "title": "Ship & Defend",
            "subtitle": "Complete the investigation and present your findings",
            "estimated_time": "35 min",
            "objectives": [
                "Wire up a complete investigation pipeline",
                "Defend AI-assisted investigation decisions to stakeholders",
                "Reflect on investigation methodology and tools built",
            ],
            "steps": [
                # Step 1 — code_exercise (full pipeline)
                {
                    "position": 1,
                    "title": "Wire Up the Full Pipeline",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Bring everything together. Build the <code>investigate_claim</code> function
that runs all three stages: data gathering, fraud scoring, and decision routing.
Handle errors gracefully and produce a complete investigation report.</p>
""",
                    "code": """import json
from datetime import datetime

# Assume these are imported from previous modules
# lookup_policy, nicb_check, get_vehicle_history, score_fraud_risk

# Mock implementations for the exercise
def lookup_policy(policy_number):
    return {
        "holder": "Derek Whitfield",
        "vehicle": {"vin": "SALYA2BU5RA123456", "declared_value": 87500},
        "declared_value": 87500,
        "_derived": {
            "policy_age_days": 127, "is_new_customer": True,
            "recent_coverage_changes": 1, "total_recent_increase": 6000,
        },
    }

def nicb_check(name):
    return {"prior_theft_claims": 1, "prior_total_payouts": 42000}

def get_vehicle_history(vin):
    return {"outstanding_loan": 62000, "loan_to_value_ratio": 0.71}

def get_incident_details(claim_id):
    return {
        "police_report_filed": True, "security_footage_available": False,
        "spare_key_accounted_for": False, "claimant_cooperative": True,
        "story_consistent": True, "details_vague": True,
    }


def investigate_claim(claim_id: str, policy_number: str) -> dict:
    \"\"\"Run a full investigation and return a structured report.

    Returns:
        dict with keys:
            - claim_id
            - investigation_date
            - data_sources: dict of raw data from each source
            - risk_assessment: output of score_fraud_risk
            - decision: the routing decision
            - report_summary: human-readable summary string
            - errors: list of any errors encountered during investigation
    \"\"\"
    # TODO: Initialize the report structure with claim_id and timestamp

    # TODO: Stage 1 -- Gather data from all sources with error handling
    # If a data source fails, log the error but continue with available data

    # TODO: Stage 2 -- Run the fraud scoring function

    # TODO: Stage 3 -- Make the routing decision using the recommendation
    # from score_fraud_risk (don't re-implement thresholds!)

    # TODO: Generate a human-readable report_summary

    return {}


# Run the investigation
report = investigate_claim("CLM-2025-0847", "POL-55219")
print(json.dumps(report, indent=2, default=str))
""",
                    "expected_output": """{
  "claim_id": "CLM-2025-0847",
  "investigation_date": "2025-03-18T14:30:00",
  "data_sources": {
    "policy": {"status": "success"},
    "nicb": {"status": "success"},
    "vehicle_history": {"status": "success"},
    "incident": {"status": "success"}
  },
  "risk_assessment": {
    "total_score": 0.56,
    "recommendation": "standard_investigation"
  },
  "decision": "standard_investigation",
  "report_summary": "Claim CLM-2025-0847 scored 0.56 (STANDARD_INVESTIGATION). Key risk factors: recent coverage increase, 1 prior theft claim, new customer. Recommend proceeding with recorded statement and title verification.",
  "errors": []
}""",
                    "validation": {
                        "must_contain": ["try", "except", "report_summary"],
                        "must_return_keys": [
                            "claim_id",
                            "investigation_date",
                            "risk_assessment",
                            "decision",
                            "report_summary",
                            "errors",
                        ],
                    },
                    "demo_data": None,
                },
                # Step 2 — scenario_branch (stakeholder Q&A)
                {
                    "position": 2,
                    "title": "Stakeholder Q&A",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>You're presenting your investigation system to the VP of Claims. She has
tough questions. Navigate this conversation to defend your approach.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "You've built the automated investigation pipeline and run it on "
                            "the Whitfield case. Now the VP of Claims, Sandra Chen, wants to "
                            "understand the system before greenlighting it for production."
                        ),
                        "steps": [
                            {
                                "question": "Sandra asks: 'Why should we trust an AI scoring system for fraud detection? Our experienced adjusters have 20 years of intuition.'",
                                "options": [
                                    {
                                        "label": "The AI replaces adjusters entirely -- it's faster and removes human bias",
                                        "correct": False,
                                        "explanation": (
                                            "This framing creates adversarial dynamics with the team and overpromises. "
                                            "No executive will approve a system positioned to replace their people."
                                        ),
                                    },
                                    {
                                        "label": "The system augments adjusters by handling routine data gathering and flagging patterns across thousands of claims that no human could track",
                                        "correct": True,
                                        "explanation": (
                                            "Perfect framing. You positioned AI as a force multiplier, not a replacement. "
                                            "Emphasizing pattern detection at scale is a genuine advantage over human review."
                                        ),
                                    },
                                    {
                                        "label": "AI is the future and we need to adopt it or fall behind competitors",
                                        "correct": False,
                                        "explanation": (
                                            "This is a generic appeal to fear that doesn't address the specific concern. "
                                            "Sandra wants to know why THIS system is trustworthy, not why AI in general matters."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Sandra follows up: 'What happens when the system gets it wrong? An $87,000 wrongful denial is a lawsuit waiting to happen.'",
                                "options": [
                                    {
                                        "label": "The system never auto-denies. It scores risk and routes claims to the appropriate investigation track. Every denial still requires human sign-off.",
                                        "correct": True,
                                        "explanation": (
                                            "This is the key point. The system is a decision-support tool, not a "
                                            "decision-making tool. Human-in-the-loop for all adverse decisions "
                                            "is essential for regulatory compliance and risk management."
                                        ),
                                    },
                                    {
                                        "label": "We've tested it on historical data and it's 95% accurate",
                                        "correct": False,
                                        "explanation": (
                                            "Accuracy numbers are important but don't address the core concern about "
                                            "wrongful denials. A 5% error rate on 10,000 claims is 500 potential lawsuits. "
                                            "You need to explain the safeguards, not just the stats."
                                        ),
                                    },
                                    {
                                        "label": "We can add an appeals process for claimants who disagree",
                                        "correct": False,
                                        "explanation": (
                                            "An appeals process is reactive -- it means you've already harmed the claimant. "
                                            "Sandra wants to know how you prevent wrongful denials, not how you handle them after."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "When presenting AI systems to stakeholders, frame them as augmentation "
                            "tools that keep humans in the loop. Address risk concerns with specific "
                            "safeguards, not accuracy statistics. Executives care about liability "
                            "and team dynamics as much as efficiency gains."
                        ),
                    },
                },
                # Step 3 — concept (retrospective)
                {
                    "position": 3,
                    "title": "Case Closed: What You Built",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>Investigation Complete</h2>

<h3>The Whitfield Case Resolution</h3>
<p>Your investigation pipeline scored claim CLM-2025-0847 at <strong>0.56</strong> --
placing it in the <em>standard investigation</em> track. The recorded statement later
revealed inconsistencies in Derek's timeline, and the title history confirmed the
vehicle was underwater on its loan. The claim was ultimately denied after a thorough
human-led investigation that your system accelerated by days.</p>

<h3>What You Built</h3>
<ol>
  <li><strong>Policy Lookup Tool</strong> -- pulls policy data and computes derived risk fields</li>
  <li><strong>Fraud Scoring Engine</strong> -- weighted multi-signal risk assessment</li>
  <li><strong>Investigation Pipeline</strong> -- end-to-end automation with error handling</li>
  <li><strong>Code Review Skills</strong> -- caught bugs that could cause production incidents</li>
</ol>

<h3>Key Investigation Principles</h3>
<ul>
  <li><strong>Evidence before conclusions</strong> -- gather data before making judgments</li>
  <li><strong>Parallel investigation tracks</strong> -- don't wait for one source when you can check multiple</li>
  <li><strong>Human in the loop</strong> -- AI scores, humans decide</li>
  <li><strong>Defensible decisions</strong> -- every determination must be backed by documented evidence</li>
</ul>

<h3>Next Steps</h3>
<p>In a production environment, you'd add:</p>
<ul>
  <li>Real-time fraud pattern detection across the claims portfolio</li>
  <li>Integration with external data sources (DMV, weather, traffic cameras)</li>
  <li>ML model training on historical claim outcomes</li>
  <li>Audit trail and compliance reporting</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 4 -- system_build (capstone: Claims Investigation API to AWS)
                {
                    "position": 4,
                    "title": "Deploy: Claims Investigation API to AWS",
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
  <h2>Mission: Claims Investigation API in Production</h2>
  <div class="objective">
    <strong>Business context:</strong> The SIU reviews 840 suspicious claims per week. Investigators want a single endpoint that takes a raw claim, enriches it with vehicle title + police report data, geolocation checks, and a Claude-driven narrative assessment, then returns a fraud score and ranked recommendations. You are deploying that service on AWS Lambda behind API Gateway so the claims UI can call it at intake.
  </div>

  <h3>Production Constraints</h3>
  <div class="constraints">
    <div class="pill"><strong>Latency SLA</strong><span>p95 &lt; 3.0s</span></div>
    <div class="pill"><strong>Scale Target</strong><span>20 req/s peak</span></div>
    <div class="pill"><strong>Cost Budget</strong><span>&lt; $0.04 / investigation</span></div>
    <div class="pill"><strong>Platform</strong><span>AWS Lambda + API Gateway</span></div>
    <div class="pill"><strong>Data Sources</strong><span>Police DB, Geo, Title DB</span></div>
    <div class="pill"><strong>LLM</strong><span>Claude 3.5 Sonnet</span></div>
  </div>

  <h3>Acceptance Criteria</h3>
  <ul class="accept">
    <li><strong>POST /investigate</strong> takes <code>{claim_id, vehicle_vin, incident_location}</code> and returns <code>{fraud_score, recommendations[]}</code></li>
    <li>Fraud score is a float in <code>[0.0, 1.0]</code> with a human-readable <code>rationale</code></li>
    <li>At least three enrichment calls (police, geolocation, vehicle title) run in parallel via <code>asyncio.gather</code></li>
    <li>Every mock integration failure is caught and surfaced in the <code>signals</code> field -- the request never fails from one flaky dependency</li>
    <li>Input validation: VIN regex (17 chars, alnum no I/O/Q), claim_id non-empty, location object with lat/lng</li>
    <li>Structured logs include claim_id, latency, cost, signals_triggered, recommendation_count</li>
    <li>Cold-start p95 &lt; 4s; warm p95 &lt; 3.0s verified by integration test (10 known claims, expected scores within &plusmn;0.15)</li>
    <li>All secrets (<code>ANTHROPIC_API_KEY</code>, <code>POLICE_API_KEY</code>, <code>GEO_API_KEY</code>) come from Lambda env vars wired via SAM/CDK</li>
  </ul>
</div>
""",
                    "code": """\"\"\"Claims Investigation API -- Starter Code

FastAPI service deployed to AWS Lambda behind API Gateway. Enriches a claim
with vehicle title, police report, and geolocation data, then asks Claude
for a narrative risk assessment. Returns a fraud score + recommendations.
\"\"\"

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
from anthropic import Anthropic, APIError
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel, Field, field_validator


# ── Configuration ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
POLICE_API_URL = os.environ.get("POLICE_API_URL", "https://mock-police.invalid/api")
POLICE_API_KEY = os.environ.get("POLICE_API_KEY", "")
GEO_API_URL = os.environ.get("GEO_API_URL", "https://mock-geo.invalid/api")
GEO_API_KEY = os.environ.get("GEO_API_KEY", "")
TITLE_API_URL = os.environ.get("TITLE_API_URL", "https://mock-title.invalid/api")

MODEL_ID = os.environ.get("MODEL_ID", "claude-3-5-sonnet-20241022")
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "2.5"))

# Claude 3.5 Sonnet pricing (USD per 1K tokens).
PRICE_IN_PER_1K = 0.003
PRICE_OUT_PER_1K = 0.015

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
)
logger = logging.getLogger("claims-api")


def jlog(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, default=str))


# ── Clients ────────────────────────────────────────────────────
claude = Anthropic(api_key=ANTHROPIC_API_KEY)


# ── Schemas ────────────────────────────────────────────────────
class IncidentLocation(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lng: float = Field(ge=-180.0, le=180.0)
    description: str | None = None


class InvestigateRequest(BaseModel):
    claim_id: str = Field(min_length=3, max_length=40)
    vehicle_vin: str
    incident_location: IncidentLocation

    @field_validator("vehicle_vin")
    @classmethod
    def _check_vin(cls, v: str) -> str:
        if not VIN_PATTERN.match(v):
            raise ValueError("VIN must be 17 alphanumeric chars (no I, O, Q)")
        return v


class Signal(BaseModel):
    source: str
    severity: str  # "info" | "warn" | "critical"
    detail: str


class Recommendation(BaseModel):
    action: str
    priority: str  # "low" | "medium" | "high"
    reason: str


class InvestigateResponse(BaseModel):
    claim_id: str
    fraud_score: float = Field(ge=0.0, le=1.0)
    rationale: str
    signals: list[Signal]
    recommendations: list[Recommendation]
    cost: float
    latency_ms: int


# ── Enrichment (mock integrations) ────────────────────────────
@dataclass
class Enrichment:
    police: dict = field(default_factory=dict)
    geo: dict = field(default_factory=dict)
    title: dict = field(default_factory=dict)
    signals: list[Signal] = field(default_factory=list)


async def _fetch_json(client: httpx.AsyncClient, url: str, params: dict, source: str) -> dict:
    try:
        resp = await client.get(url, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        jlog("enrichment_error", source=source, error=str(exc))
        return {"_error": str(exc)}


async def enrich(req: InvestigateRequest) -> Enrichment:
    \"\"\"Call the three mock integrations in parallel; tolerate partial failure.\"\"\"
    async with httpx.AsyncClient(headers={"User-Agent": "claims-siu/1.0"}) as client:
        police_task = _fetch_json(
            client, f"{POLICE_API_URL}/incidents",
            {"lat": req.incident_location.lat, "lng": req.incident_location.lng,
             "key": POLICE_API_KEY},
            "police",
        )
        geo_task = _fetch_json(
            client, f"{GEO_API_URL}/reverse",
            {"lat": req.incident_location.lat, "lng": req.incident_location.lng,
             "key": GEO_API_KEY},
            "geo",
        )
        title_task = _fetch_json(
            client, f"{TITLE_API_URL}/vin/{req.vehicle_vin}", {}, "title"
        )
        police, geo, title = await asyncio.gather(police_task, geo_task, title_task)

    enrich_obj = Enrichment(police=police, geo=geo, title=title)

    # Convert raw integration output into deterministic signals the LLM can use.
    if "_error" in police:
        enrich_obj.signals.append(Signal(source="police", severity="warn",
                                         detail="Police API unavailable; proceeding without incident reports."))
    elif police.get("incident_count", 0) == 0:
        enrich_obj.signals.append(Signal(source="police", severity="critical",
                                         detail="No police report filed for the incident location on the claimed date."))
    if title.get("salvage_title"):
        enrich_obj.signals.append(Signal(source="title", severity="critical",
                                         detail=f"Vehicle {req.vehicle_vin} has a salvage title on record."))
    if geo.get("distance_from_policy_address_km", 0) > 500:
        enrich_obj.signals.append(Signal(source="geo", severity="warn",
                                         detail=f"Incident is {geo['distance_from_policy_address_km']}km from policy address."))
    return enrich_obj


# ── LLM assessment ────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a fraud investigator for auto claims. Given the enrichment payload and "
    "derived signals, return ONLY a JSON object: "
    '{"fraud_score": <0..1>, "rationale": "<2-3 sentences>", '
    '"recommendations": [{"action": "...", "priority": "low|medium|high", "reason": "..."}]}. '
    "Score objectively on evidence in signals. Never exceed 5 recommendations."
)


def compute_cost(tokens_in: int, tokens_out: int) -> float:
    return round(
        (tokens_in / 1000) * PRICE_IN_PER_1K + (tokens_out / 1000) * PRICE_OUT_PER_1K,
        6,
    )


async def assess(req: InvestigateRequest, enrichment: Enrichment) -> tuple[dict, int, int]:
    payload = {
        "claim_id": req.claim_id,
        "vin": req.vehicle_vin,
        "incident_location": req.incident_location.model_dump(),
        "signals": [s.model_dump() for s in enrichment.signals],
        "police": enrichment.police,
        "geo": enrichment.geo,
        "title": enrichment.title,
    }
    try:
        resp = claude.messages.create(
            model=MODEL_ID,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload)}],
        )
    except APIError as exc:
        jlog("claude_error", error=str(exc))
        raise HTTPException(status_code=503, detail="LLM backend unavailable")

    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        jlog("llm_parse_error", raw=text[:400])
        raise HTTPException(status_code=502, detail="Upstream LLM returned invalid JSON")

    parsed["fraud_score"] = max(0.0, min(1.0, float(parsed.get("fraud_score", 0.0))))
    return parsed, resp.usage.input_tokens, resp.usage.output_tokens


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="Claims Investigation API", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": MODEL_ID}


@app.post("/investigate", response_model=InvestigateResponse)
async def investigate(req: InvestigateRequest) -> InvestigateResponse:
    started = time.perf_counter()
    req_id = str(uuid.uuid4())

    enrichment = await enrich(req)
    parsed, tokens_in, tokens_out = await assess(req, enrichment)
    cost = compute_cost(tokens_in, tokens_out)

    recs = [
        Recommendation(**r) for r in parsed.get("recommendations", [])[:5]
    ]
    latency_ms = int((time.perf_counter() - started) * 1000)

    jlog(
        "investigate_completed",
        request_id=req_id,
        claim_id=req.claim_id,
        latency_ms=latency_ms,
        cost=cost,
        signals_triggered=len(enrichment.signals),
        recommendation_count=len(recs),
        fraud_score=parsed["fraud_score"],
    )

    return InvestigateResponse(
        claim_id=req.claim_id,
        fraud_score=parsed["fraud_score"],
        rationale=parsed.get("rationale", ""),
        signals=enrichment.signals,
        recommendations=recs,
        cost=cost,
        latency_ms=latency_ms,
    )


# ── Lambda handler ────────────────────────────────────────────
# Mangum adapts FastAPI to the AWS Lambda + API Gateway event model.
handler = Mangum(app, lifespan="off")
""",
                    "expected_output": None,
                    "deployment_config": {
                        "platform": "aws",
                        "service": "lambda",
                        "dockerfile": """FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["app.handler"]
""",
                        "requirements": (
                            "fastapi>=0.115.0\n"
                            "mangum>=0.19.0\n"
                            "pydantic>=2.6.0\n"
                            "httpx>=0.27.0\n"
                            "anthropic>=0.39.0\n"
                        ),
                        "infra_hint": (
                            "Package as a container image pushed to ECR, then create a Lambda function "
                            "from that image and attach an HTTP API Gateway. Memory 1024MB, timeout 10s, "
                            "reserved concurrency 40. Wire env vars ANTHROPIC_API_KEY, POLICE_API_URL/KEY, "
                            "GEO_API_URL/KEY, TITLE_API_URL via SAM or CDK. Add CloudWatch log subscription "
                            "so the JSON logs are queryable in Athena/Logs Insights."
                        ),
                    },
                    "demo_data": {
                        "phases": [
                            {"id": "local", "title": "Local Build"},
                            {"id": "docker", "title": "Containerize"},
                            {"id": "deploy", "title": "Deploy to AWS Lambda"},
                            {"id": "test", "title": "Integration Test"},
                        ],
                        "checklist": [
                            {"id": "check_endpoint", "label": "POST /investigate returns {fraud_score, recommendations[]} within 3s"},
                            {"id": "check_vin", "label": "VIN validation rejects malformed VINs with 422"},
                            {"id": "check_parallel", "label": "Police, geo, and title calls run concurrently via asyncio.gather"},
                            {"id": "check_resilience", "label": "When any mock integration fails, request still succeeds with a degraded signal"},
                            {"id": "check_logs", "label": "Structured JSON logs for every request (claim_id, latency, cost, signals)"},
                            {"id": "check_docker", "label": "Container image builds on the lambda/python:3.12 base and runs locally"},
                            {"id": "check_lambda", "label": "Deployed to AWS Lambda + API Gateway; public URL answers /health"},
                            {"id": "check_integration", "label": "Integration test passes on 10 known claims (scores within ±0.15)"},
                            {"id": "check_cost", "label": "Average per-investigation cost stays below $0.04"},
                        ],
                    },
                    "validation": {
                        "endpoint_check": {
                            "method": "POST",
                            "path": "/investigate",
                            "body": {
                                "claim_id": "CLM-2025-0847",
                                "vehicle_vin": "1HGCM82633A123456",
                                "incident_location": {
                                    "lat": 40.7589,
                                    "lng": -73.9851,
                                    "description": "Intersection of W 42nd St and 7th Ave",
                                },
                            },
                            "expected_status": 200,
                            "expected_fields": ["claim_id", "fraud_score", "rationale", "signals", "recommendations", "cost", "latency_ms"],
                        },
                    },
                },
            ],
        },
    ],
}
