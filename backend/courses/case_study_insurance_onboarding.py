"""
Case Study Course: AI-Powered Insurance Onboarding
Redesign the insurance onboarding flow with AI-assisted document processing and underwriting.
"""

COURSE = {
    "id": "ai-insurance-onboarding",
    "title": "AI-Powered Insurance Onboarding",
    "subtitle": "Redesign insurance onboarding with smart document processing and AI underwriting assist",
    "icon": "📋",
    "course_type": "case_study",
    "level": "Intermediate",
    "tags": ["insurance", "onboarding", "document-processing", "ocr", "underwriting", "case-study", "python"],
    "estimated_time": "~2.5 hours",
    "description": (
        "Meridian Insurance is losing 34% of applicants during onboarding because the process "
        "takes 12-18 days and requires customers to mail physical documents. The Chief Digital "
        "Officer has tasked your team with building an AI-powered onboarding system that reduces "
        "the process to under 48 hours while maintaining underwriting accuracy. You'll tackle "
        "document extraction, validation, risk assessment, and a phased rollout strategy."
    ),
    "modules": [
        # ── Module 1: Discovery & Design ─────────────────────────────
        {
            "position": 1,
            "title": "Discovery & Design",
            "subtitle": "Uncover pain points, map AI opportunities, and design the new flow",
            "estimated_time": "30 min",
            "objectives": [
                "Analyze user research data to identify the biggest onboarding friction points",
                "Map which steps are candidates for AI automation vs. human review",
                "Make design decisions that balance speed with regulatory compliance",
            ],
            "steps": [
                # Step 1 -- concept (case setup)
                {
                    "position": 1,
                    "title": "The Onboarding Problem",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.form-demo { background: #1e2538; border: 1px solid #2a3352; border-radius: 12px; padding: 22px; margin: 16px 0; color: #e8ecf4; font-family: 'Inter', system-ui, sans-serif; }
.form-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.form-demo .hook { background: linear-gradient(135deg, #151b2e, #252e45); border-left: 4px solid #2dd4bf; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 18px; }
.form-demo .hook strong { color: #2dd4bf; }
.form-demo .split { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 10px; }
.form-demo .card { background: #151b2e; border: 1px solid #2a3352; border-radius: 8px; padding: 16px; }
.form-demo .card.old h3 { color: #f87171; margin: 0 0 10px 0; font-size: 0.95em; }
.form-demo .card.new h3 { color: #2dd4bf; margin: 0 0 10px 0; font-size: 0.95em; }
.form-demo .old-list { max-height: 260px; overflow-y: auto; padding-right: 6px; border-top: 1px solid #2a3352; }
.form-demo .old-list::-webkit-scrollbar { width: 6px; }
.form-demo .old-list::-webkit-scrollbar-thumb { background: #2a3352; border-radius: 3px; }
.form-demo .field-row { font-size: 0.82em; padding: 6px 0; border-bottom: 1px dashed #1e2538; color: #8b95b0; display: flex; align-items: center; gap: 6px; }
.form-demo .field-row .num { color: #f87171; font-family: 'Fira Code', monospace; font-size: 0.75em; min-width: 20px; }
.form-demo .ai-prompt { color: #8b95b0; font-size: 0.85em; margin-bottom: 6px; }
.form-demo textarea { width: 100%; background: #0d1117; color: #e8ecf4; border: 1px solid #2a3352; border-radius: 6px; padding: 10px 12px; font-family: inherit; font-size: 0.9em; resize: vertical; min-height: 90px; box-sizing: border-box; }
.form-demo textarea:focus { outline: none; border-color: #2dd4bf; }
.form-demo .btn-f { background: #2dd4bf; color: #151b2e; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 700; margin-top: 10px; width: 100%; transition: background 0.2s; }
.form-demo .btn-f:hover { background: #1dc4af; }
.form-demo .btn-f:disabled { background: #2a3352; color: #8b95b0; cursor: not-allowed; }
.form-demo .extracted { display: none; margin-top: 14px; }
.form-demo .extracted.show { display: block; }
.form-demo .extract-bar { height: 6px; background: #2a3352; border-radius: 3px; overflow: hidden; margin: 6px 0 10px 0; }
.form-demo .extract-bar .fill { height: 100%; background: linear-gradient(90deg, #4a7cff, #2dd4bf); width: 0%; transition: width 1.2s ease-out; }
.form-demo .extract-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px; font-size: 0.78em; }
.form-demo .extract-row { padding: 4px 0; border-bottom: 1px solid #1e2538; display: flex; justify-content: space-between; }
.form-demo .extract-row .k { color: #8b95b0; }
.form-demo .extract-row .v { color: #2dd4bf; font-family: 'Fira Code', monospace; font-weight: 600; }
.form-demo .extract-row .v.missing { color: #8b95b0; font-style: italic; }
.form-demo .stats { margin-top: 12px; text-align: center; font-size: 0.88em; color: #8b95b0; }
.form-demo .stats b { color: #2dd4bf; }
@media(max-width:700px){ .form-demo .split { grid-template-columns: 1fr; } .form-demo .extract-grid { grid-template-columns: 1fr; } }
</style>

<div class="form-demo">
  <h2>Form Builder Challenge</h2>
  <div class="hook">
    <strong>The problem:</strong> 90% of users abandon onboarding. Why? Your form has 47 fields. What if AI filled them in from a 2-sentence story?
  </div>

  <div class="split">
    <div class="card old">
      <h3>Traditional Form (47 fields)</h3>
      <div class="old-list" id="oldFields"></div>
    </div>

    <div class="card new">
      <h3>AI-First Form (1 question)</h3>
      <div class="ai-prompt">Tell us about your car:</div>
      <textarea id="aiInput" placeholder="e.g. I have a 2021 Honda Civic EX, silver, bought new from Honda of Dallas, I drive about 12000 miles a year, mostly city commuting, no accidents, I live in Austin TX, own my home, clean record, want full coverage with 500 deductible">I bought a 2021 Honda Civic EX in silver last year, financed through Honda Financial. I drive about 12,000 miles a year commuting in Austin TX, no accidents, clean record. I want full coverage, 500 dollar deductible.</textarea>
      <button class="btn-f" id="extractBtn" onclick="extractFields()">Let AI Fill the Form</button>

      <div class="extracted" id="extractedBox">
        <div class="extract-bar"><div class="fill" id="extractFill"></div></div>
        <div class="extract-grid" id="extractGrid"></div>
      </div>
    </div>
  </div>

  <div class="stats" id="formStats"></div>
</div>

<script>
(function(){
  var oldFieldList = [
    "Full Legal Name","Date of Birth","SSN (last 4)","Primary Phone","Secondary Phone","Email","Mailing Address Line 1","Mailing Address Line 2","City","State","ZIP Code","Garaging Address","Housing Status","Years at Address","Occupation","Employer","Annual Income","Marital Status","Drivers License Number","License State","License Expiry","Years Licensed","Vehicle Year","Vehicle Make","Vehicle Model","Vehicle Trim","VIN","Body Style","Color","Ownership (own/lease/finance)","Lienholder","Odometer Reading","Primary Use","Annual Mileage","Daily Commute Miles","Parking Location","Prior Carrier","Prior Policy Number","Policy Start","Policy End","Prior Liability Limit","Prior Deductible","At-Fault Accidents 5yr","Moving Violations 3yr","Desired Liability Limit","Desired Deductible","Add-ons (roadside, rental)"
  ];

  var oldHTML = '';
  for (var i = 0; i < oldFieldList.length; i++) {
    oldHTML += '<div class="field-row"><span class="num">' + String(i+1).padStart(2,"0") + '</span>' + oldFieldList[i] + '</div>';
  }
  document.getElementById('oldFields').innerHTML = oldHTML;

  var extractionMap = [
    {k: "vehicle_year", label: "Vehicle Year", re: /(20\\d{2}|19\\d{2})/i},
    {k: "vehicle_make", label: "Make", re: /\\b(Honda|Toyota|Ford|BMW|Audi|Tesla|Nissan|Chevy|Chevrolet|Kia|Hyundai|Mazda|Subaru)\\b/i},
    {k: "vehicle_model", label: "Model", re: /\\b(Civic|Accord|Camry|Corolla|F-150|Model 3|Model Y|Mustang|Pilot|CR-V|Rogue|Altima|Sonata)\\b/i},
    {k: "vehicle_trim", label: "Trim", re: /\\b(EX|LX|SE|SR5|XLE|XSE|Sport|Touring|Limited|Platinum|Premium|Performance)\\b/i},
    {k: "color", label: "Color", re: /\\b(silver|black|white|red|blue|gray|grey|green|gold)\\b/i},
    {k: "ownership", label: "Ownership", re: /\\b(financed|financing|leased|lease|own|owned|bought)\\b/i, map: {"financed": "Finance", "financing": "Finance", "leased": "Lease", "lease": "Lease", "own": "Own", "owned": "Own", "bought": "Finance"}},
    {k: "annual_mileage", label: "Annual Miles", re: /(\\d{1,3}[,.]?\\d{3})\\s*miles/i},
    {k: "primary_use", label: "Primary Use", re: /\\b(commuting|commute|pleasure|business|rideshare|uber|lyft)\\b/i, map: {"commuting": "Commute", "commute": "Commute", "pleasure": "Pleasure", "business": "Business", "rideshare": "Rideshare", "uber": "Rideshare", "lyft": "Rideshare"}},
    {k: "city", label: "City", re: /\\b(Austin|Dallas|Houston|San Antonio|New York|Los Angeles|Chicago|Miami|Seattle|Boston)\\b/i},
    {k: "state", label: "State", re: /\\b(TX|CA|NY|FL|WA|MA|IL|AZ|CO|NC|Texas|California)\\b/i, map: {"Texas": "TX", "California": "CA"}},
    {k: "accidents_5yr", label: "At-Fault Accidents", re: /\\bno accidents|clean record|zero accidents\\b/i, staticVal: "0"},
    {k: "violations_3yr", label: "Violations (3yr)", re: /\\bclean record|no tickets|no violations\\b/i, staticVal: "0"},
    {k: "deductible", label: "Deductible", re: /(\\d{3,4})\\s*(?:dollar|\\$)?\\s*deductible/i, prefix: "$"},
    {k: "coverage_type", label: "Coverage Type", re: /\\b(full coverage|comprehensive|liability only|minimum)\\b/i},
    {k: "lienholder", label: "Lienholder", re: /\\b(Honda Financial|Toyota Financial|Ford Credit|GM Financial|Chase Auto|Bank of America|Wells Fargo)\\b/i},
    {k: "purchase_source", label: "Purchase Source", re: /\\b(Honda of \\w+|dealership|private sale|used from|bought new)\\b/i}
  ];

  function parseStory(text) {
    var out = [];
    for (var i = 0; i < extractionMap.length; i++) {
      var f = extractionMap[i];
      var m = text.match(f.re);
      var val = null;
      if (m) {
        if (f.staticVal) val = f.staticVal;
        else if (f.map) val = f.map[m[1] ? m[1].toLowerCase() : m[0].toLowerCase()] || m[1] || m[0];
        else val = m[1] || m[0];
        if (f.prefix) val = f.prefix + val;
      }
      out.push({k: f.k, label: f.label, value: val});
    }
    return out;
  }

  window.extractFields = function() {
    var text = document.getElementById('aiInput').value.trim();
    if (!text) return;

    document.getElementById('extractBtn').disabled = true;
    document.getElementById('extractBtn').textContent = "Extracting...";
    var box = document.getElementById('extractedBox');
    box.classList.add('show');
    var fill = document.getElementById('extractFill');
    fill.style.width = '0%';

    setTimeout(function(){ fill.style.width = '100%'; }, 40);

    var results = parseStory(text);
    var grid = document.getElementById('extractGrid');
    grid.innerHTML = '';

    var extracted = 0;
    results.forEach(function(r, idx){
      setTimeout(function(){
        var row = document.createElement('div');
        row.className = 'extract-row';
        if (r.value) extracted++;
        row.innerHTML = '<span class="k">' + r.label + '</span>'
          + '<span class="v' + (r.value ? '' : ' missing') + '">'
          + (r.value ? r.value : "ask user") + '</span>';
        grid.appendChild(row);

        if (idx === results.length - 1) {
          var total = 47;
          var autoFilled = extracted + 20;
          if (autoFilled > total) autoFilled = total;
          var pct = Math.round((autoFilled / total) * 100);
          document.getElementById('formStats').innerHTML =
            'AI extracted <b>' + extracted + '/16 core fields</b> in 1.4 seconds. '
            + 'With validators and known-defaults, <b>' + autoFilled + '/' + total + '</b> fields (' + pct + '%) fill automatically. '
            + 'User sees 3 questions, not 47. Drop-off falls from 90% to 18%.';
          document.getElementById('extractBtn').disabled = false;
          document.getElementById('extractBtn').textContent = "Try Another Story";
        }
      }, 120 * idx);
    });
  };
})();
</script>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- scenario_branch (design decisions)
                {
                    "position": 2,
                    "title": "Design Decisions Under Pressure",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>The CDO has assembled a cross-functional team: you (AI lead), an
underwriting manager, a compliance officer, and a UX designer. The first
design review surfaces hard trade-offs.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's the kickoff meeting. The CDO wants the team aligned on the approach "
                            "before anyone writes code. The underwriting manager, Janet, is skeptical. "
                            "The compliance officer, Ray, is nervous. The UX designer, Sofia, is excited "
                            "but worried about scope."
                        ),
                        "steps": [
                            {
                                "question": "Janet, the underwriting manager, says: 'Our underwriters catch errors that cost us $2-3M a year in bad risk. If your AI misreads a document and we bind a policy with wrong data, that's an E&O claim waiting to happen.' How do you address her concern?",
                                "options": [
                                    {
                                        "label": "Propose a confidence-based workflow: AI extracts data with confidence scores, auto-accepts above 95%, flags for human review between 80-95%, and rejects below 80% for manual processing",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right architecture. It gives underwriters a safety net while "
                                            "still automating the clear cases. Historically, 60-70% of documents are "
                                            "clean enough for high-confidence extraction, which still saves massive time. "
                                            "The key insight: the AI doesn't replace the underwriter's judgment -- it "
                                            "eliminates the data entry step that causes most errors today."
                                        ),
                                    },
                                    {
                                        "label": "Show Janet that AI extraction is more accurate than manual data entry, so errors will actually decrease",
                                        "correct": False,
                                        "explanation": (
                                            "This is true on average, but it misses Janet's real concern. She's not worried "
                                            "about average accuracy -- she's worried about the failure mode. A human who "
                                            "makes a typo creates a correctable error. An AI that confidently misreads a "
                                            "VIN creates a silently wrong policy. You need to address the failure mode, "
                                            "not just the average case."
                                        ),
                                    },
                                    {
                                        "label": "Suggest keeping human review on 100% of applications initially and gradually reducing it as the AI proves itself",
                                        "correct": False,
                                        "explanation": (
                                            "This sounds safe but defeats the purpose. If humans review everything, "
                                            "you've just added an AI step without removing the manual step. The onboarding "
                                            "time stays the same or gets worse. You need to trust the AI on clear cases "
                                            "from day one, with well-defined escalation criteria."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Ray, the compliance officer, raises a critical point: 'In 8 of our 15 states, we're required to retain original documents for 7 years. If someone uploads a photo of their ID, does that count as the original?' What's your approach?",
                                "options": [
                                    {
                                        "label": "Store the original uploaded image at full resolution with metadata (timestamp, device info, IP), process a copy for extraction, and implement a document integrity chain with SHA-256 hashes",
                                        "correct": True,
                                        "explanation": (
                                            "This is the compliance-safe architecture. The original image is the 'document "
                                            "of record' -- you never modify it. The extraction happens on a copy. The hash "
                                            "chain proves the document wasn't altered after upload. Most state regulators "
                                            "accept digital originals with proper chain-of-custody documentation. Check with "
                                            "each state's DOI, but this architecture satisfies the strictest interpretations."
                                        ),
                                    },
                                    {
                                        "label": "Just store everything digitally -- it's 2025, regulators will catch up",
                                        "correct": False,
                                        "explanation": (
                                            "Insurance regulation moves slowly and penalties are severe. Assuming regulators "
                                            "will 'catch up' is how companies get consent orders and market conduct fines. "
                                            "Build for the rules as they are today, not as you wish they were."
                                        ),
                                    },
                                    {
                                        "label": "Require customers to also mail originals as a backup, maintaining the digital flow as the fast track",
                                        "correct": False,
                                        "explanation": (
                                            "This re-introduces the exact friction you're trying to eliminate. If customers "
                                            "still have to mail documents, you haven't solved the '12-18 day' problem. "
                                            "Digital originals with proper integrity controls are legally sufficient in "
                                            "most jurisdictions."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Sofia, the UX designer, proposes: 'Let's build a mobile-first upload flow where customers take photos of their documents with their phone camera. We can use real-time quality detection to guide them.' The team loves it, but you see a problem. What is it?",
                                "options": [
                                    {
                                        "label": "Photo quality varies wildly -- glare, blur, shadows, partial captures. We need a quality assessment step that rejects bad images before the AI tries to extract from them",
                                        "correct": True,
                                        "explanation": (
                                            "Garbage in, garbage out. The #1 cause of extraction failures is poor image "
                                            "quality, not model limitations. Build a quality gate: check resolution, detect "
                                            "blur/glare, verify all four corners are visible, and give real-time feedback "
                                            "('Move to better lighting', 'Hold steadier'). This costs ~1 week of development "
                                            "but prevents 40% of extraction errors downstream."
                                        ),
                                    },
                                    {
                                        "label": "Mobile uploads won't work for older customers who aren't tech-savvy",
                                        "correct": False,
                                        "explanation": (
                                            "This is a real concern but not a blocker. You can maintain the existing "
                                            "agent-assisted path as a fallback while making mobile the primary channel. "
                                            "Don't design for the exception at the cost of the majority. 78% of "
                                            "Meridian's applicants are under 55 and have smartphones."
                                        ),
                                    },
                                    {
                                        "label": "We should use a dedicated scanner SDK instead of the native camera",
                                        "correct": False,
                                        "explanation": (
                                            "Scanner SDKs add complexity and app store dependencies. Modern phone cameras "
                                            "are more than capable -- the issue isn't the camera hardware, it's user "
                                            "behavior (bad angles, poor lighting). A quality assessment overlay on the "
                                            "native camera is simpler and more maintainable than a third-party SDK."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Insurance AI projects live or die on stakeholder trust. The underwriting manager "
                            "needs confidence thresholds. The compliance officer needs audit trails. The UX "
                            "designer needs quality gates. Address each concern with a specific architectural "
                            "decision, not hand-waving about how 'AI will handle it.'"
                        ),
                    },
                },
                # Step 3 -- categorization (AI opportunity mapping)
                {
                    "position": 3,
                    "title": "AI Opportunity Map",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>Not every step in the onboarding process should be automated. Categorize
each task by the appropriate level of AI involvement. Getting this wrong
either leaves money on the table or creates compliance risk.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Sort each onboarding task into the appropriate AI automation level.",
                        "categories": [
                            "Full AI Automation",
                            "AI-Assisted (Human Reviews)",
                            "Human Only (AI Cannot Help)",
                        ],
                        "items": [
                            {
                                "text": "Extract name, address, and DOB from a driver's license photo",
                                "correct_category": "Full AI Automation",
                            },
                            {
                                "text": "Determine whether a roof condition photo shows hail damage requiring inspection",
                                "correct_category": "AI-Assisted (Human Reviews)",
                            },
                            {
                                "text": "Verify that the applicant's stated income matches their occupation for underwriting",
                                "correct_category": "AI-Assisted (Human Reviews)",
                            },
                            {
                                "text": "Pre-fill application fields from uploaded documents, highlighting low-confidence values",
                                "correct_category": "Full AI Automation",
                            },
                            {
                                "text": "Decide to decline coverage based on applicant's claims history and risk profile",
                                "correct_category": "Human Only (AI Cannot Help)",
                            },
                            {
                                "text": "Validate that a VIN from a registration document matches NHTSA records",
                                "correct_category": "Full AI Automation",
                            },
                            {
                                "text": "Handle a complaint about a denied application and explain the decision",
                                "correct_category": "Human Only (AI Cannot Help)",
                            },
                            {
                                "text": "Flag an application for fraud review when uploaded documents show signs of tampering",
                                "correct_category": "AI-Assisted (Human Reviews)",
                            },
                            {
                                "text": "Send automated status updates to the applicant at each stage of the process",
                                "correct_category": "Full AI Automation",
                            },
                        ],
                    },
                },
                # Step 4 -- code (process analysis)
                {
                    "position": 4,
                    "title": "Quantify the Opportunity",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Let's analyze Meridian's actual process data to quantify the time savings
and identify which document types cause the most bottlenecks.</p>
""",
                    "code": """import json

# Process data from Meridian's last quarter
PROCESS_DATA = {
    "total_applications": 12600,
    "completed": 8316,  # 66%
    "abandoned": 4284,  # 34%
    "avg_completion_days": 14.5,
    "steps": [
        {
            "name": "Initial Application Form",
            "avg_time_hours": 0.5,
            "drop_off_rate": 0.05,
            "error_rate": 0.12,
            "automation_potential": "high",
            "bottleneck": "manual data entry by agent",
        },
        {
            "name": "Document Collection",
            "avg_time_hours": 96,  # 4 days waiting for mail
            "drop_off_rate": 0.15,
            "error_rate": 0.08,
            "automation_potential": "high",
            "bottleneck": "physical mail required",
        },
        {
            "name": "Document Data Entry",
            "avg_time_hours": 48,  # 2 days in queue + processing
            "drop_off_rate": 0.03,
            "error_rate": 0.18,
            "automation_potential": "high",
            "bottleneck": "manual keying from scanned images",
        },
        {
            "name": "Underwriting Review",
            "avg_time_hours": 72,  # 3 days
            "drop_off_rate": 0.04,
            "error_rate": 0.05,
            "automation_potential": "medium",
            "bottleneck": "underwriter queue backlog",
        },
        {
            "name": "Additional Doc Requests",
            "avg_time_hours": 120,  # 5 days (only 40% of apps need this)
            "drop_off_rate": 0.12,
            "error_rate": 0.03,
            "automation_potential": "high",
            "bottleneck": "requirements not known upfront",
        },
        {
            "name": "Quote & Bind",
            "avg_time_hours": 24,  # 1 day
            "drop_off_rate": 0.08,
            "error_rate": 0.02,
            "automation_potential": "medium",
            "bottleneck": "customer decision time",
        },
    ],
}

# Document type analysis
DOCUMENT_TYPES = [
    {"type": "Driver's License", "volume_pct": 0.95, "extraction_accuracy": 0.94, "avg_extract_time_sec": 2.1, "manual_time_min": 4.5},
    {"type": "Vehicle Registration", "volume_pct": 0.88, "extraction_accuracy": 0.91, "avg_extract_time_sec": 3.2, "manual_time_min": 6.0},
    {"type": "Prior Insurance Dec Page", "volume_pct": 0.72, "extraction_accuracy": 0.82, "avg_extract_time_sec": 5.8, "manual_time_min": 12.0},
    {"type": "Property Photos", "volume_pct": 0.35, "extraction_accuracy": 0.76, "avg_extract_time_sec": 8.5, "manual_time_min": 15.0},
    {"type": "Business License", "volume_pct": 0.15, "extraction_accuracy": 0.85, "avg_extract_time_sec": 4.1, "manual_time_min": 8.0},
    {"type": "Roof Inspection Report", "volume_pct": 0.12, "extraction_accuracy": 0.71, "avg_extract_time_sec": 12.0, "manual_time_min": 20.0},
]

print("=" * 65)
print("  MERIDIAN INSURANCE -- ONBOARDING PROCESS ANALYSIS")
print("=" * 65)

# Step-by-step analysis
print("\\n  PROCESS BOTTLENECK ANALYSIS")
print("  " + "-" * 55)
total_hours = sum(s["avg_time_hours"] for s in PROCESS_DATA["steps"])
for step in PROCESS_DATA["steps"]:
    pct_of_time = step["avg_time_hours"] / total_hours * 100
    bar = "█" * int(pct_of_time / 2)
    print(f"  {step['name']:30s} {step['avg_time_hours']:6.0f}h ({pct_of_time:4.1f}%) {bar}")
    print(f"    Drop-off: {step['drop_off_rate']*100:.0f}% | Errors: {step['error_rate']*100:.0f}% | AI potential: {step['automation_potential']}")

# Time savings projection
print(f"\\n  PROJECTED TIME SAVINGS WITH AI")
print("  " + "-" * 55)
ai_times = {
    "Initial Application Form": 0.1,   # Pre-filled from uploaded docs
    "Document Collection": 0.5,        # Instant upload vs. mail
    "Document Data Entry": 0.5,        # AI extraction vs. manual keying
    "Underwriting Review": 24,         # AI pre-screening reduces to simple review
    "Additional Doc Requests": 2,      # Known upfront from AI analysis
    "Quote & Bind": 4,                 # Real-time quote with e-signature
}

total_ai_hours = 0
for step in PROCESS_DATA["steps"]:
    ai_h = ai_times[step["name"]]
    total_ai_hours += ai_h
    savings_pct = (1 - ai_h / step["avg_time_hours"]) * 100
    print(f"  {step['name']:30s} {step['avg_time_hours']:6.0f}h -> {ai_h:5.1f}h  ({savings_pct:+.0f}%)")

print(f"\\n  Total: {total_hours:.0f}h -> {total_ai_hours:.1f}h = {total_ai_hours/24:.1f} days")
print(f"  Target: 48h (2 days) -- {'MET ✅' if total_ai_hours <= 48 else 'NOT MET ❌'}")

# Document extraction ROI
print(f"\\n  DOCUMENT EXTRACTION ROI")
print("  " + "-" * 55)
monthly_apps = PROCESS_DATA["total_applications"] / 3  # quarterly to monthly
for doc in DOCUMENT_TYPES:
    monthly_volume = monthly_apps * doc["volume_pct"]
    manual_hours = monthly_volume * doc["manual_time_min"] / 60
    ai_hours = monthly_volume * doc["avg_extract_time_sec"] / 3600
    saved = manual_hours - ai_hours
    print(f"  {doc['type']:30s} Accuracy: {doc['extraction_accuracy']*100:.0f}%  | {saved:.0f} hrs/month saved")

# Revenue recovery
completion_rate_improvement = 0.18  # Conservative: 66% -> 84%
recovered_apps = PROCESS_DATA["total_applications"] / 3 * completion_rate_improvement
avg_premium = 1950
recovered_revenue = recovered_apps * avg_premium
print(f"\\n  REVENUE RECOVERY ESTIMATE")
print(f"  Completion rate: 66% -> ~84% (+18 pts)")
print(f"  Recovered applications/month: ~{recovered_apps:.0f}")
print(f"  Average annual premium: ${avg_premium:,}")
print(f"  Annual recovered revenue: ${recovered_revenue * 12:,.0f}")
""",
                    "expected_output": """MERIDIAN INSURANCE -- ONBOARDING PROCESS ANALYSIS

  Total: 361h -> 31.1h = 1.3 days
  Target: 48h (2 days) -- MET

  REVENUE RECOVERY ESTIMATE
  Completion rate: 66% -> ~84% (+18 pts)""",
                    "validation": None,
                    "demo_data": None,
                },
            ],
        },
        # ── Module 2: Smart Document Processing ─────────────────────
        {
            "position": 2,
            "title": "Smart Document Processing",
            "subtitle": "Build OCR + AI extraction, validation pipelines, and underwriting assist",
            "estimated_time": "45 min",
            "objectives": [
                "Build a document extraction pipeline with confidence scoring",
                "Implement cross-field validation to catch extraction errors",
                "Design the underwriting assist system that pre-screens risk",
                "Review extraction code for production-critical bugs",
            ],
            "steps": [
                # Step 1 -- concept (extraction architecture)
                {
                    "position": 1,
                    "title": "The Extraction Pipeline",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>How Document Extraction Works</h2>
<p>The extraction pipeline processes each uploaded document through four stages:</p>

<h3>Stage 1: Image Quality Assessment</h3>
<p>Before extraction, check that the image is usable:</p>
<ul>
  <li><strong>Resolution:</strong> Minimum 300 DPI equivalent (reject blurry photos)</li>
  <li><strong>Completeness:</strong> All four corners visible, no cropping</li>
  <li><strong>Readability:</strong> No heavy glare, shadows, or obstructions</li>
  <li><strong>Document type:</strong> Classify what kind of document this is</li>
</ul>

<h3>Stage 2: OCR + AI Extraction</h3>
<p>Two-pass extraction for maximum accuracy:</p>
<ul>
  <li><strong>Pass 1 (OCR):</strong> Raw text extraction using cloud OCR (Google Vision, AWS Textract)</li>
  <li><strong>Pass 2 (LLM):</strong> Structured field extraction using an LLM with the OCR output + image</li>
  <li><strong>Each field gets a confidence score</strong> based on OCR clarity and LLM certainty</li>
</ul>

<h3>Stage 3: Cross-Validation</h3>
<p>Extracted fields are validated against each other and external sources:</p>
<table>
  <tr><th>Check</th><th>Source</th><th>Catches</th></tr>
  <tr><td>VIN matches make/model/year</td><td>NHTSA API</td><td>OCR misreads, wrong document</td></tr>
  <tr><td>Address matches zip code</td><td>USPS API</td><td>Transposed digits, wrong state</td></tr>
  <tr><td>DOB makes applicant 16-99</td><td>Business rule</td><td>Year misreads (1989 vs 1998)</td></tr>
  <tr><td>Policy dates are not in the future</td><td>Business rule</td><td>Month/day transposition</td></tr>
  <tr><td>Name matches across documents</td><td>Cross-document</td><td>Mismatched applicants</td></tr>
</table>

<h3>Stage 4: Confidence-Based Routing</h3>
<ul>
  <li><strong>>95% confidence on all fields:</strong> Auto-accept, proceed to underwriting</li>
  <li><strong>80-95% on any field:</strong> Highlight uncertain fields, queue for quick human review</li>
  <li><strong><80% on any field:</strong> Reject extraction, request re-upload or manual processing</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- code_exercise (document extraction)
                {
                    "position": 2,
                    "title": "Build the Document Extractor",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build the document extraction function that processes OCR output and
returns structured fields with confidence scores. The function should
handle driver's licenses as the first document type.</p>
""",
                    "code": """import re
from typing import Optional

# Simulated OCR output for a driver's license
SAMPLE_OCR_OUTPUT = {
    "raw_text": (
        "STATE OF CALIFORNIA\\n"
        "DRIVER LICENSE\\n"
        "DL D1234567\\n"
        "CLASS C\\n"
        "EXP 03/15/2027\\n"
        "LN MARTINEZ\\n"
        "FN ELENA SOFIA\\n"
        "DOB 07/22/1991\\n"
        "RSTR NONE\\n"
        "4521 PACIFIC COAST HWY APT 12\\n"
        "LONG BEACH CA 90802\\n"
        "SEX F HAIR BRN EYES BRN\\n"
        "HT 5-06 WT 135 lbs\\n"
        "ISS 03/15/2022"
    ),
    "ocr_confidence": 0.92,
    "document_type_detected": "drivers_license",
    "image_quality_score": 0.88,
}


def extract_drivers_license(ocr_output: dict) -> dict:
    \"\"\"Extract structured fields from a driver's license OCR output.

    Args:
        ocr_output: dict with keys:
            - raw_text: str (OCR text)
            - ocr_confidence: float (overall OCR confidence)
            - document_type_detected: str
            - image_quality_score: float

    Returns:
        dict with:
            - document_type: str
            - fields: dict of {field_name: {value, confidence, source_line}}
            - overall_confidence: float (min of all field confidences)
            - quality_gate: "auto_accept" | "human_review" | "re_upload"
            - warnings: list of str
    \"\"\"
    raw = ocr_output["raw_text"]
    lines = raw.strip().split("\\n")
    base_conf = ocr_output["ocr_confidence"]
    fields = {}
    warnings = []

    # TODO: Extract last name (LN line)
    # Parse the line starting with "LN", extract the name
    # Confidence = base_conf * 1.0 if clear match, * 0.8 if fuzzy

    # TODO: Extract first name (FN line)
    # Parse the line starting with "FN"

    # TODO: Extract date of birth (DOB line)
    # Parse MM/DD/YYYY format, validate it makes the person 16-99 years old
    # Add warning if age seems unusual (< 18 or > 85)

    # TODO: Extract license number (DL line)
    # Parse the line starting with "DL", extract the alphanumeric ID

    # TODO: Extract address (line with street number)
    # Look for a line that starts with a number (street address)
    # Also grab the next line for city/state/zip

    # TODO: Extract expiration date (EXP line)
    # Validate that the license is not expired
    # Add warning if expired

    # TODO: Calculate overall_confidence as the minimum of all field confidences

    # TODO: Determine quality_gate:
    #   - "auto_accept" if overall_confidence >= 0.95
    #   - "human_review" if overall_confidence >= 0.80
    #   - "re_upload" if overall_confidence < 0.80

    return {
        "document_type": "drivers_license",
        "fields": fields,
        "overall_confidence": 0.0,
        "quality_gate": "re_upload",
        "warnings": warnings,
    }


# Test it
import json
result = extract_drivers_license(SAMPLE_OCR_OUTPUT)
print(json.dumps(result, indent=2))
print(f"\\nQuality Gate: {result['quality_gate']}")
print(f"Overall Confidence: {result['overall_confidence']:.2f}")
if result['warnings']:
    print(f"Warnings: {', '.join(result['warnings'])}")
print(f"\\nExtracted Fields:")
for name, data in result['fields'].items():
    status = "✅" if data['confidence'] >= 0.95 else "⚠️" if data['confidence'] >= 0.80 else "❌"
    print(f"  {status} {name:20s} = {data['value']:30s} (conf: {data['confidence']:.2f})")
""",
                    "expected_output": """{
  "document_type": "drivers_license",
  "quality_gate": "human_review",
  "overall_confidence": 0.92
}

Extracted Fields:
  ✅ last_name            = MARTINEZ                       (conf: 0.92)
  ✅ first_name           = ELENA SOFIA                    (conf: 0.92)
  ✅ date_of_birth        = 07/22/1991                     (conf: 0.92)
  ✅ license_number       = D1234567                       (conf: 0.92)
  ⚠️ address              = 4521 PACIFIC COAST HWY APT 12  (conf: 0.88)
  ✅ expiration_date      = 03/15/2027                     (conf: 0.92)""",
                    "validation": {
                        "must_contain": ["fields", "overall_confidence", "quality_gate", "warnings"],
                        "must_return_keys": ["document_type", "fields", "overall_confidence", "quality_gate", "warnings"],
                        "hint": "Parse each line using its prefix (LN, FN, DOB, DL, EXP). For address, look for lines starting with a digit. Multiply base OCR confidence by match quality for each field.",
                    },
                    "demo_data": None,
                },
                # Step 3 -- code_review (validation pipeline)
                {
                    "position": 3,
                    "title": "Review the Validation Pipeline",
                    "step_type": "exercise",
                    "exercise_type": "code_review",
                    "content": """
<p>A contractor wrote the cross-validation pipeline that checks extracted
fields against external sources. It has 3 bugs that could cause incorrect
policy binding or silent data corruption. Find them all.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "code": """def validate_extraction(extracted_fields: dict, external_data: dict) -> dict:
    \"\"\"Cross-validate extracted document fields against external sources.\"\"\"
    validations = []
    all_passed = True

    # Check 1: VIN validation against NHTSA
    if "vin" in extracted_fields:
        vin = extracted_fields["vin"]["value"]
        nhtsa = external_data.get("nhtsa", {})
        if nhtsa.get("make") == extracted_fields.get("vehicle_make", {}).get("value"):
            validations.append({"check": "vin_make_match", "passed": True})
        else:
            validations.append({"check": "vin_make_match", "passed": False})

    # Check 2: Address validation against USPS
    if "address" in extracted_fields:
        addr = extracted_fields["address"]["value"]
        zip_code = addr.split()[-1]
        usps = external_data.get("usps", {})
        if usps.get("valid_zip") == zip_code:
            validations.append({"check": "address_zip", "passed": True})

    # Check 3: DOB makes applicant 16-99
    if "date_of_birth" in extracted_fields:
        from datetime import datetime
        dob = datetime.strptime(extracted_fields["date_of_birth"]["value"], "%m/%d/%Y")
        age = (datetime.now() - dob).days / 365
        if 16 <= age <= 99:
            validations.append({"check": "age_valid", "passed": True})

    # Check 4: Name consistency across documents
    if "dl_name" in extracted_fields and "reg_name" in extracted_fields:
        if extracted_fields["dl_name"]["value"] == extracted_fields["reg_name"]["value"]:
            validations.append({"check": "name_match", "passed": True})
        else:
            validations.append({"check": "name_match", "passed": False})
            all_passed = False

    return {
        "all_passed": all_passed,
        "validations": validations,
        "recommendation": "proceed" if all_passed else "manual_review",
    }""",
                        "bugs": [
                            {
                                "line": 11,
                                "issue": "VIN check failure doesn't set all_passed to False",
                                "severity": "high",
                                "hint": (
                                    "When the VIN make doesn't match the NHTSA data, the validation records "
                                    "'passed: False' but never sets all_passed = False. This means a vehicle "
                                    "with a mismatched VIN will still get a 'proceed' recommendation, potentially "
                                    "binding a policy with the wrong vehicle information."
                                ),
                            },
                            {
                                "line": 17,
                                "issue": "Address validation only appends result when zip is valid -- invalid zips are silently ignored",
                                "severity": "high",
                                "hint": (
                                    "The 'else' branch is missing. If the zip code doesn't match USPS data, no "
                                    "validation record is created and all_passed stays True. An invalid address "
                                    "will sail through validation undetected. Every check must record both pass "
                                    "AND fail results."
                                ),
                            },
                            {
                                "line": 27,
                                "issue": "Name matching uses exact string equality instead of fuzzy matching",
                                "severity": "medium",
                                "hint": (
                                    "Exact string matching will flag 'ELENA S MARTINEZ' vs 'ELENA SOFIA MARTINEZ' "
                                    "as a mismatch, even though they're clearly the same person. Driver's licenses "
                                    "often abbreviate middle names. Use normalized comparison (lowercase, strip "
                                    "middle names/initials) or a fuzzy matching algorithm like Levenshtein distance "
                                    "with a threshold."
                                ),
                            },
                        ],
                    },
                },
                # Step 4 -- code_exercise (underwriting assist)
                {
                    "position": 4,
                    "title": "Build the Underwriting Assist",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>The underwriting assist pre-screens applications and generates a risk
summary that helps underwriters make faster decisions. It doesn't make
the decision -- it surfaces the signals that matter.</p>
""",
                    "code": """from datetime import datetime

# Risk factor weights for auto insurance
AUTO_RISK_WEIGHTS = {
    "driving_record": 0.30,
    "vehicle_risk": 0.20,
    "coverage_gap": 0.15,
    "credit_indicator": 0.15,
    "location_risk": 0.10,
    "age_experience": 0.10,
}

def underwriting_pre_screen(application: dict) -> dict:
    \"\"\"Pre-screen an auto insurance application for underwriting.

    Args:
        application: dict with keys:
            - applicant: {name, dob, license_years, violations, accidents, prior_claims}
            - vehicle: {year, make, model, value, safety_rating, theft_risk}
            - coverage: {prior_carrier, prior_expiry, gap_days, requested_limits}
            - location: {state, zip, urban_rural, theft_index, weather_risk}
            - credit: {credit_tier} -- "excellent" | "good" | "fair" | "poor"

    Returns:
        dict with:
            - risk_score: float 0.0-1.0 (higher = riskier)
            - risk_tier: "preferred" | "standard" | "non_standard" | "decline_review"
            - factors: list of {name, score, weight, weighted_score, detail}
            - flags: list of str (things underwriter should specifically look at)
            - estimated_premium_range: {low, high} in dollars
            - underwriter_summary: str (1-2 sentence narrative for the underwriter)
    \"\"\"
    factors = []
    flags = []

    # TODO: Score driving record (weight: 0.30)
    # 0 violations + 0 accidents = 0.1 (excellent)
    # 1-2 violations, 0 accidents = 0.4
    # Any accidents in last 3 years = 0.7
    # DUI or 3+ violations = 1.0
    # Flag if any prior claims > $10,000

    # TODO: Score vehicle risk (weight: 0.20)
    # safety_rating "5-star" = 0.1, "4-star" = 0.3, "3-star" = 0.5, below = 0.8
    # theft_risk "low" = 0.1, "medium" = 0.4, "high" = 0.8
    # Average the two sub-scores
    # Flag if vehicle value > $60,000 (high-value vehicle)

    # TODO: Score coverage gap (weight: 0.15)
    # gap_days == 0 = 0.0 (continuous coverage)
    # gap_days 1-30 = 0.3
    # gap_days 31-90 = 0.6
    # gap_days > 90 = 0.9
    # Flag if gap > 60 days

    # TODO: Score credit indicator (weight: 0.15)
    # "excellent" = 0.1, "good" = 0.3, "fair" = 0.6, "poor" = 0.9

    # TODO: Score location risk (weight: 0.10)
    # Combine theft_index and weather_risk (both 0.0-1.0), average them

    # TODO: Score age/experience (weight: 0.10)
    # Calculate age from DOB
    # license_years < 3 = 0.8, 3-5 = 0.5, 5-10 = 0.3, 10+ = 0.1
    # If age < 25 and license_years < 5, add 0.2 (cap at 1.0)

    # TODO: Calculate total risk_score as weighted sum

    # TODO: Determine risk_tier:
    #   0.0-0.25: "preferred"
    #   0.25-0.50: "standard"
    #   0.50-0.75: "non_standard"
    #   0.75-1.00: "decline_review"

    # TODO: Estimate premium range based on risk_score
    # Base premium = $1,200/year
    # preferred: $800-$1,400
    # standard: $1,400-$2,400
    # non_standard: $2,400-$4,200
    # decline_review: $4,200-$6,000

    # TODO: Generate underwriter_summary (1-2 sentences)

    return {
        "risk_score": 0.0,
        "risk_tier": "standard",
        "factors": factors,
        "flags": flags,
        "estimated_premium_range": {"low": 0, "high": 0},
        "underwriter_summary": "",
    }


# Test with a real application
test_application = {
    "applicant": {
        "name": "Elena Martinez",
        "dob": "07/22/1991",
        "license_years": 12,
        "violations": 1,
        "accidents": 0,
        "prior_claims": [{"amount": 3200, "year": 2022}],
    },
    "vehicle": {
        "year": 2023,
        "make": "Honda",
        "model": "CR-V",
        "value": 34000,
        "safety_rating": "5-star",
        "theft_risk": "low",
    },
    "coverage": {
        "prior_carrier": "State Farm",
        "prior_expiry": "2025-03-01",
        "gap_days": 15,
        "requested_limits": "100/300/100",
    },
    "location": {
        "state": "CA",
        "zip": "90802",
        "urban_rural": "urban",
        "theft_index": 0.45,
        "weather_risk": 0.2,
    },
    "credit": {"credit_tier": "good"},
}

import json
result = underwriting_pre_screen(test_application)
print(json.dumps(result, indent=2))
print(f"\\nRisk Tier: {result['risk_tier'].upper()}")
print(f"Risk Score: {result['risk_score']:.2f}")
print(f"Premium Range: ${result['estimated_premium_range']['low']:,} - ${result['estimated_premium_range']['high']:,}")
if result['flags']:
    print(f"\\nFlags for Underwriter:")
    for flag in result['flags']:
        print(f"  ⚠️  {flag}")
print(f"\\nSummary: {result['underwriter_summary']}")
""",
                    "expected_output": """{
  "risk_score": 0.33,
  "risk_tier": "standard",
  "factors": [
    {"name": "driving_record", "score": 0.4, "weight": 0.30, "weighted_score": 0.12},
    {"name": "vehicle_risk", "score": 0.1, "weight": 0.20, "weighted_score": 0.02},
    {"name": "coverage_gap", "score": 0.3, "weight": 0.15, "weighted_score": 0.045},
    {"name": "credit_indicator", "score": 0.3, "weight": 0.15, "weighted_score": 0.045},
    {"name": "location_risk", "score": 0.325, "weight": 0.10, "weighted_score": 0.0325},
    {"name": "age_experience", "score": 0.1, "weight": 0.10, "weighted_score": 0.01}
  ],
  "risk_tier": "standard",
  "estimated_premium_range": {"low": 1400, "high": 2400}
}

Risk Tier: STANDARD
Risk Score: 0.33""",
                    "validation": {
                        "must_contain": ["risk_score", "risk_tier", "factors", "flags", "estimated_premium_range"],
                        "must_return_keys": ["risk_score", "risk_tier", "factors", "flags", "estimated_premium_range", "underwriter_summary"],
                        "hint": "Score each factor independently using the rules, then compute the weighted sum. Determine tier from score thresholds. Generate a concise summary mentioning the key risk factors.",
                    },
                    "demo_data": None,
                },
                # Step 5 -- scenario_branch (extraction edge cases)
                {
                    "position": 5,
                    "title": "When Documents Fight Back",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>Your extraction pipeline is built, but real-world documents are messy.
These scenarios test your judgment on edge cases that will determine
whether the system earns underwriter trust.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "The system has been processing test applications for a week. The QA team "
                            "has surfaced three document scenarios that the current pipeline handles "
                            "poorly. Each one represents a class of issues you'll see in production."
                        ),
                        "steps": [
                            {
                                "question": "An applicant uploads a declaration page from their prior insurer, but the document is a multi-page PDF and the relevant coverage information is on page 3. Your OCR extracted all pages but the LLM pulled the agent's name from page 1 as the applicant's name. How do you fix this class of error?",
                                "options": [
                                    {
                                        "label": "Add page-aware extraction: classify each page by content type first, then extract fields only from the relevant page for each field type",
                                        "correct": True,
                                        "explanation": (
                                            "Page-aware extraction is essential for multi-page documents. Page 1 of a dec page "
                                            "typically has agent info, page 2-3 has coverage details, and the last page has "
                                            "endorsements. The LLM should know which page to look at for each field type. "
                                            "This pattern generalizes to all multi-page documents -- inspections, policies, "
                                            "business licenses with attachments."
                                        ),
                                    },
                                    {
                                        "label": "Limit extraction to the first page only -- that's where the important info usually is",
                                        "correct": False,
                                        "explanation": (
                                            "This would miss critical information. Dec pages, inspection reports, and "
                                            "multi-page licenses all have important fields scattered across pages. "
                                            "The answer is smarter extraction, not less extraction."
                                        ),
                                    },
                                    {
                                        "label": "Concatenate all pages into a single text blob and let the LLM figure it out",
                                        "correct": False,
                                        "explanation": (
                                            "This is what caused the bug in the first place. Without page context, the LLM "
                                            "can't distinguish between the agent's name on page 1 and the insured's name "
                                            "on page 3. You lose spatial information that's critical for correct extraction."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "A homeowner uploads a photo of their house for the property assessment. The AI extracts 'condition: good' but the photo clearly shows peeling paint and a sagging gutter. The underwriter flags this as a dangerous false positive. What's the root cause and fix?",
                                "options": [
                                    {
                                        "label": "Property condition assessment from photos should always be 'AI-assisted, human reviews' -- never auto-accept. Add explicit low-confidence scoring for subjective visual assessments",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right lesson. There's a fundamental difference between extracting "
                                            "text (objective, high accuracy) and assessing condition (subjective, requires "
                                            "domain expertise). The AI can flag potential issues ('possible roof damage', "
                                            "'visible wear on exterior') but should never auto-determine condition ratings. "
                                            "Set confidence caps at 0.70 for visual assessments to force human review."
                                        ),
                                    },
                                    {
                                        "label": "Fine-tune a computer vision model specifically for property condition assessment",
                                        "correct": False,
                                        "explanation": (
                                            "A specialized CV model would be more accurate, but this is a 6-month project "
                                            "requiring labeled training data from underwriters. Even then, liability for "
                                            "visual assessments means a human must review. The fix is routing, not model "
                                            "quality. A better model still needs human sign-off for subjective judgments."
                                        ),
                                    },
                                    {
                                        "label": "Remove photo-based assessment entirely and require in-person inspections",
                                        "correct": False,
                                        "explanation": (
                                            "In-person inspections add 5-7 days and cost $150-300 each. For most properties, "
                                            "photos are sufficient when reviewed by a human. The answer is human + AI review, "
                                            "not removing AI from the process entirely."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Document extraction accuracy depends on the type of information being extracted. "
                            "Structured text fields (names, dates, VINs) can reach 90-95% accuracy and be "
                            "auto-accepted with validation. Subjective assessments (property condition, damage "
                            "severity) should always route through a human, no matter how good the model is. "
                            "Know the difference and route accordingly."
                        ),
                    },
                },
            ],
        },
        # ── Module 3: Launch & Learn ─────────────────────────────────
        {
            "position": 3,
            "title": "Launch & Learn",
            "subtitle": "Plan the rollout, define success metrics, and handle failures gracefully",
            "estimated_time": "35 min",
            "objectives": [
                "Design a phased rollout strategy that manages risk",
                "Define metrics that prove business value to stakeholders",
                "Build graceful failure handling for every extraction scenario",
            ],
            "steps": [
                # Step 1 -- code (rollout simulation)
                {
                    "position": 1,
                    "title": "Simulate the Phased Rollout",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>You can't launch AI document processing to 4,200 applications/month
on day one. Run this rollout simulation to see the risk-managed approach.</p>
""",
                    "code": """import json

# Phased rollout plan
ROLLOUT_PHASES = [
    {
        "phase": 1,
        "name": "Shadow Mode",
        "duration_weeks": 2,
        "traffic_pct": 1.0,  # All traffic, but AI runs in shadow
        "ai_auto_accept": False,
        "description": "AI processes every application in parallel with the manual flow. No customer impact. Compare AI extraction vs. manual entry for accuracy baseline.",
        "success_criteria": {
            "extraction_accuracy": 0.90,
            "false_positive_rate": 0.05,
            "processing_time_sec": 30,
        },
        "risk_level": "none",
    },
    {
        "phase": 2,
        "name": "Pilot: Auto Only",
        "duration_weeks": 3,
        "traffic_pct": 0.10,  # 10% of auto insurance apps
        "ai_auto_accept": True,
        "description": "10% of new auto insurance applications use AI extraction with auto-accept above 95% confidence. Human reviews everything below. Homeowners and business stay manual.",
        "success_criteria": {
            "extraction_accuracy": 0.93,
            "false_positive_rate": 0.03,
            "completion_rate_improvement": 0.05,
            "underwriter_satisfaction": 3.5,
        },
        "risk_level": "low",
    },
    {
        "phase": 3,
        "name": "Expanded Pilot",
        "duration_weeks": 4,
        "traffic_pct": 0.50,
        "ai_auto_accept": True,
        "description": "50% of auto applications, 10% of homeowners. Add VIN validation and address verification integrations. Underwriters review AI-flagged applications only.",
        "success_criteria": {
            "extraction_accuracy": 0.95,
            "false_positive_rate": 0.02,
            "completion_rate_improvement": 0.10,
            "avg_onboarding_days": 5,
        },
        "risk_level": "medium",
    },
    {
        "phase": 4,
        "name": "Full Rollout",
        "duration_weeks": 0,  # ongoing
        "traffic_pct": 1.0,
        "ai_auto_accept": True,
        "description": "All product lines. AI handles extraction and pre-screening. Underwriters focus on flagged applications and complex risks only.",
        "success_criteria": {
            "extraction_accuracy": 0.95,
            "false_positive_rate": 0.015,
            "completion_rate": 0.84,
            "avg_onboarding_days": 2,
        },
        "risk_level": "managed",
    },
]

# Simulate each phase
monthly_apps = 4200
avg_premium = 1950
manual_cost_per_app = 45  # dollars (data entry + underwriter time)

print("=" * 70)
print("  MERIDIAN INSURANCE -- ROLLOUT SIMULATION")
print("=" * 70)

cumulative_weeks = 0
for phase in ROLLOUT_PHASES:
    cumulative_weeks += phase["duration_weeks"]
    apps_in_scope = int(monthly_apps * phase["traffic_pct"])

    print(f"\\n  Phase {phase['phase']}: {phase['name']}")
    print(f"  " + "-" * 50)
    print(f"  Duration:     {phase['duration_weeks']} weeks {'(ongoing)' if phase['duration_weeks'] == 0 else ''}")
    print(f"  Traffic:      {phase['traffic_pct']*100:.0f}% ({apps_in_scope:,} apps/month)")
    print(f"  Auto-accept:  {'Yes' if phase['ai_auto_accept'] else 'No (shadow only)'}")
    print(f"  Risk level:   {phase['risk_level']}")
    print(f"  Description:  {phase['description'][:100]}...")

    # Cost analysis
    if phase["ai_auto_accept"]:
        ai_cost_per_app = 2.50  # API + compute
        manual_remaining = apps_in_scope * 0.15  # 15% need human review
        auto_processed = apps_in_scope - manual_remaining
        phase_cost = auto_processed * ai_cost_per_app + manual_remaining * manual_cost_per_app
        manual_baseline = apps_in_scope * manual_cost_per_app
        savings = manual_baseline - phase_cost
        print(f"  Monthly savings: ${savings:,.0f} ({savings/manual_baseline*100:.0f}% reduction)")

    print(f"  Go/No-Go Criteria:")
    for metric, threshold in phase["success_criteria"].items():
        if isinstance(threshold, float) and threshold < 1:
            print(f"    {metric:35s} >= {threshold*100:.1f}%")
        else:
            print(f"    {metric:35s} >= {threshold}")

# Summary timeline
print(f"\\n  TIMELINE SUMMARY")
print(f"  " + "-" * 50)
total_weeks = sum(p["duration_weeks"] for p in ROLLOUT_PHASES)
print(f"  Total rollout duration: {total_weeks} weeks ({total_weeks/4:.0f} months)")
print(f"  Full steady-state savings: ~${monthly_apps * (manual_cost_per_app - 2.50) * 0.85:,.0f}/month")
print(f"  Projected completion rate: 66% -> 84% (+18 pts)")
print(f"  Annual revenue recovery: ~${monthly_apps * 12 * 0.18 * avg_premium:,.0f}")
""",
                    "expected_output": """MERIDIAN INSURANCE -- ROLLOUT SIMULATION

  Phase 1: Shadow Mode
  Phase 2: Pilot: Auto Only
  Phase 3: Expanded Pilot
  Phase 4: Full Rollout

  TIMELINE SUMMARY
  Total rollout duration: 9 weeks
  Projected completion rate: 66% -> 84% (+18 pts)""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- categorization (metrics)
                {
                    "position": 2,
                    "title": "Define Success Metrics",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>The CDO wants a dashboard ready for the board meeting. Sort these metrics
into the right category so stakeholders see what matters most at a glance.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Classify each metric by its role in the success measurement framework.",
                        "categories": [
                            "Business Outcome (board-level)",
                            "Operational Efficiency",
                            "Quality & Safety",
                        ],
                        "items": [
                            {
                                "text": "Application completion rate (currently 66%, target 84%)",
                                "correct_category": "Business Outcome (board-level)",
                            },
                            {
                                "text": "Average onboarding time in days (currently 14.5, target 2)",
                                "correct_category": "Business Outcome (board-level)",
                            },
                            {
                                "text": "Document extraction accuracy rate by document type",
                                "correct_category": "Quality & Safety",
                            },
                            {
                                "text": "Percentage of applications auto-accepted without human review",
                                "correct_category": "Operational Efficiency",
                            },
                            {
                                "text": "False positive rate -- incorrect data accepted by the system",
                                "correct_category": "Quality & Safety",
                            },
                            {
                                "text": "Cost per processed application (currently $45, target $8)",
                                "correct_category": "Operational Efficiency",
                            },
                            {
                                "text": "Annual premium revenue recovered from reduced abandonment",
                                "correct_category": "Business Outcome (board-level)",
                            },
                            {
                                "text": "Underwriter review queue size and average wait time",
                                "correct_category": "Operational Efficiency",
                            },
                            {
                                "text": "Number of policies bound with incorrect data (E&O exposure)",
                                "correct_category": "Quality & Safety",
                            },
                        ],
                    },
                },
                # Step 3 -- scenario_branch (handling failures)
                {
                    "position": 3,
                    "title": "When Things Go Wrong",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>Your system is live in Phase 3 (50% of auto applications). Three
incidents hit in the same week. Navigate each one correctly to keep
the rollout on track.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's week 7 of the rollout. Phase 3 is running at 50% of auto applications. "
                            "The extraction accuracy is at 94.2% -- just below the 95% go/no-go criteria "
                            "for Phase 4. Then three incidents hit in rapid succession."
                        ),
                        "steps": [
                            {
                                "question": "Incident 1: A batch of 23 applications from a single agent in Florida all have the same error -- the prior carrier's policy number is being extracted as the applicant's phone number. Investigation shows these are all from the same insurer (FairPoint Mutual) whose dec pages have an unusual layout. What do you do?",
                                "options": [
                                    {
                                        "label": "Add FairPoint Mutual's dec page layout as a specific template in the extraction pipeline, re-process the 23 applications, and build a monitoring alert for carrier-specific extraction failures",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right response. Carrier-specific document layouts are a known "
                                            "challenge. Building a template library for the top 20 carriers by volume "
                                            "prevents this class of error. The monitoring alert ensures you catch new "
                                            "carrier formats before they affect many applications. Re-processing the "
                                            "affected batch shows accountability."
                                        ),
                                    },
                                    {
                                        "label": "Lower the confidence threshold on prior carrier fields to force more human reviews",
                                        "correct": False,
                                        "explanation": (
                                            "This is a band-aid, not a fix. Lowering the threshold catches FairPoint "
                                            "errors but also routes many correct extractions to human review, increasing "
                                            "the workload on underwriters. The issue is the extraction logic, not the "
                                            "threshold."
                                        ),
                                    },
                                    {
                                        "label": "Roll back Phase 3 until the extraction model is retrained",
                                        "correct": False,
                                        "explanation": (
                                            "Overreaction. A single carrier's unusual layout doesn't justify rolling back "
                                            "the entire phase. The other 94%+ of applications are processing correctly. "
                                            "Fix the specific issue and add monitoring -- don't shut down the system for "
                                            "a localized problem."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Incident 2: An applicant is furious because the system auto-rejected their driver's license photo three times with the message 'Image quality too low.' They eventually called an agent, who discovered the license is valid but issued by a tribal nation, which has a different format than state-issued IDs. What's the systemic fix?",
                                "options": [
                                    {
                                        "label": "Add a fallback path: after 2 rejection attempts, offer the applicant the option to proceed with agent-assisted manual entry, and log the document for template expansion",
                                        "correct": True,
                                        "explanation": (
                                            "The key insight is graceful degradation. No extraction system will handle 100% "
                                            "of document formats on day one. After 2 attempts, the system should recognize "
                                            "it's stuck and offer a human path. Logging the document creates a feedback loop "
                                            "to expand format support over time. This also handles military IDs, "
                                            "international licenses, and other non-standard formats."
                                        ),
                                    },
                                    {
                                        "label": "Train the system to recognize all possible ID formats including tribal, military, and international IDs",
                                        "correct": False,
                                        "explanation": (
                                            "You can't anticipate every format. There are 574 federally recognized tribes, "
                                            "each with potentially different ID formats, plus military IDs, consular IDs, "
                                            "and documents from 195 countries. Build for graceful fallback, not exhaustive "
                                            "coverage. Add formats as you encounter them."
                                        ),
                                    },
                                    {
                                        "label": "Remove the image quality gate entirely -- let the LLM try to extract from any image",
                                        "correct": False,
                                        "explanation": (
                                            "The quality gate exists for a reason. Without it, blurry photos and partial "
                                            "captures generate low-confidence extractions that waste underwriter time. "
                                            "The issue isn't the quality gate itself -- it's the lack of a fallback when "
                                            "the gate repeatedly rejects a legitimate document."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Incident 3: The underwriting manager, Janet, sends you data showing that 4 policies were bound in Phase 3 with incorrect vehicle information -- the wrong model year was extracted and auto-accepted (2019 instead of 2009). This affects premium calculation by ~$400/year per policy. The CDO is asking if the rollout should continue. What do you present?",
                                "options": [
                                    {
                                        "label": "Present the data honestly: 4 errors out of ~2,100 applications (0.19% error rate), compared to the manual process error rate of 2.3%. Add a VIN-to-year cross-check and continue the rollout with the additional validation",
                                        "correct": True,
                                        "explanation": (
                                            "Honesty and context are key. The AI error rate is 10x lower than the manual "
                                            "process, but the error type is different -- AI errors are systematic (same "
                                            "misread pattern) while human errors are random. The cross-check fix prevents "
                                            "this specific class of error. Present the comparison, acknowledge the incident, "
                                            "show the fix, and recommend continuing. The CDO needs to see you're managing "
                                            "risk, not hiding from it."
                                        ),
                                    },
                                    {
                                        "label": "Pause the rollout at Phase 3 until you can guarantee zero extraction errors on vehicle data",
                                        "correct": False,
                                        "explanation": (
                                            "Zero errors is an impossible standard. Even manual data entry has a 2-3% error "
                                            "rate. Pausing until perfection means you never launch. The right standard is "
                                            "'better than manual with improving trend,' not 'zero errors.'"
                                        ),
                                    },
                                    {
                                        "label": "Switch all vehicle data extraction to human-only review and keep AI for personal information only",
                                        "correct": False,
                                        "explanation": (
                                            "This overreacts to 4 errors by removing AI from one of the highest-value "
                                            "extraction categories. Vehicle data has more external validation sources "
                                            "(NHTSA, VIN decoders) than any other document type. The fix is adding the "
                                            "cross-check, not removing automation."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Production AI systems will have incidents. The difference between a system that "
                            "earns trust and one that gets killed is how you respond: fix the specific issue, "
                            "add monitoring to prevent the class of error, compare error rates to the baseline "
                            "(manual process), and always provide a graceful fallback path. Never promise zero "
                            "errors -- promise better-than-human with a continuous improvement loop."
                        ),
                    },
                },
                # Step 4 -- concept (retrospective)
                {
                    "position": 4,
                    "title": "Case Closed: The Meridian Transformation",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>6-Month Results</h2>

<h3>The Numbers</h3>
<table>
  <tr><th>Metric</th><th>Before</th><th>After</th><th>Change</th></tr>
  <tr><td>Application Completion Rate</td><td>66%</td><td>83%</td><td>+17 pts</td></tr>
  <tr><td>Avg Onboarding Time</td><td>14.5 days</td><td>2.8 days</td><td>-81%</td></tr>
  <tr><td>Cost per Application</td><td>$45</td><td>$9.20</td><td>-80%</td></tr>
  <tr><td>Data Entry Errors</td><td>2.3%</td><td>0.4%</td><td>-83%</td></tr>
  <tr><td>Underwriter Queue Wait</td><td>3.2 days</td><td>4 hours</td><td>-95%</td></tr>
  <tr><td>Annual Premium Recovery</td><td>--</td><td>$6.8M</td><td>+$6.8M</td></tr>
  <tr><td>Staff Reductions</td><td>8 data entry clerks</td><td>3 retrained as QA analysts</td><td>5 roles eliminated</td></tr>
</table>

<h3>What You Built</h3>
<ol>
  <li><strong>Document Quality Gate</strong> -- real-time image assessment with guided re-capture</li>
  <li><strong>Multi-Document Extraction Pipeline</strong> -- OCR + LLM with page-aware processing</li>
  <li><strong>Cross-Validation Engine</strong> -- NHTSA, USPS, and business rule checks</li>
  <li><strong>Underwriting Pre-Screener</strong> -- weighted risk scoring with narrative summaries</li>
  <li><strong>Phased Rollout Framework</strong> -- shadow mode through full deployment with go/no-go gates</li>
  <li><strong>Graceful Fallback Paths</strong> -- agent-assisted manual entry when AI can't handle a document</li>
</ol>

<h3>Key Lessons</h3>
<ul>
  <li><strong>Confidence thresholds are the product</strong> -- the model is commodity, the thresholds determine business outcomes</li>
  <li><strong>Objective extraction vs. subjective assessment</strong> -- text fields can be auto-accepted; condition assessments cannot</li>
  <li><strong>Graceful degradation > perfect coverage</strong> -- build fallback paths for documents you can't handle yet</li>
  <li><strong>Carrier template libraries</strong> -- the long tail of document formats requires ongoing maintenance</li>
  <li><strong>Compare to the baseline</strong> -- a 0.4% AI error rate is a win when the manual rate was 2.3%</li>
</ul>

<h3>What's Next</h3>
<p>Meridian is now planning Phase 2 initiatives:</p>
<ul>
  <li>Homeowners photo assessment with human-in-the-loop training</li>
  <li>Real-time quote generation during document upload (instant bind for simple auto)</li>
  <li>Agent copilot mode for complex commercial applications</li>
  <li>Cross-state compliance automation (document requirements vary by state)</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 5 -- system_build (capstone: AI Onboarding Pipeline to GCP)
                {
                    "position": 5,
                    "title": "Deploy: AI Onboarding Pipeline to GCP",
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
  <h2>Mission: Deploy the Meridian Onboarding Pipeline</h2>
  <div class="objective">
    <strong>Business context:</strong> Meridian is ready to move the onboarding pipeline from shadow mode to production. You are deploying the document OCR + AI field extraction + risk scoring service on GCP Cloud Run, wired to the DMV, credit bureau, and underwriting mocks. Applicants upload their documents and the API returns extracted fields, a risk score, and the next step the portal should take.
  </div>

  <h3>Production Constraints</h3>
  <div class="constraints">
    <div class="pill"><strong>Latency SLA</strong><span>p95 &lt; 6.0s (multi-doc)</span></div>
    <div class="pill"><strong>Scale Target</strong><span>15 concurrent onboardings</span></div>
    <div class="pill"><strong>Cost Budget</strong><span>&lt; $0.18 / onboarding</span></div>
    <div class="pill"><strong>Platform</strong><span>GCP Cloud Run</span></div>
    <div class="pill"><strong>OCR</strong><span>Google Document AI (mock)</span></div>
    <div class="pill"><strong>LLM</strong><span>Claude 3.5 Sonnet</span></div>
  </div>

  <h3>Acceptance Criteria</h3>
  <ul class="accept">
    <li><strong>POST /onboard</strong> accepts <code>{documents: base64[]}</code> and returns <code>{extracted_fields, risk_score, next_step}</code></li>
    <li>Document size limit 8MB each, max 6 documents per request; oversize returns 413</li>
    <li>OCR runs concurrently across documents; LLM extraction merges into a single field map</li>
    <li>DMV, credit bureau, and underwriting mock integrations contribute to the risk score (weighted)</li>
    <li><code>next_step</code> is one of <code>auto_approve</code>, <code>manual_review</code>, <code>decline</code>, <code>collect_more_docs</code></li>
    <li>Per-field confidence scores are returned; fields below 0.7 confidence go to manual review</li>
    <li>Structured JSON logs for each onboarding: latency, cost, doc_count, risk_score, next_step</li>
    <li>Deployed to Cloud Run with min-instances=1 (avoid cold starts), max-instances=30, concurrency=4</li>
  </ul>
</div>
""",
                    "code": """\"\"\"Meridian AI Onboarding Pipeline -- Starter Code

FastAPI service: document OCR, AI field extraction, risk scoring.
Deploys to GCP Cloud Run. Extend the TODOs to meet the acceptance
criteria before Meridian's phased rollout gate.
\"\"\"

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
import uuid
from typing import Any

import httpx
from anthropic import Anthropic, APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator


# ── Configuration ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OCR_API_URL = os.environ.get("OCR_API_URL", "https://mock-ocr.invalid")
OCR_API_KEY = os.environ.get("OCR_API_KEY", "")
DMV_API_URL = os.environ.get("DMV_API_URL", "https://mock-dmv.invalid")
CREDIT_API_URL = os.environ.get("CREDIT_API_URL", "https://mock-credit.invalid")
UW_API_URL = os.environ.get("UW_API_URL", "https://mock-uw.invalid")

MODEL_ID = os.environ.get("MODEL_ID", "claude-3-5-sonnet-20241022")
MAX_DOCS = int(os.environ.get("MAX_DOCS", "6"))
MAX_DOC_BYTES = int(os.environ.get("MAX_DOC_BYTES", str(8 * 1024 * 1024)))
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "4.0"))

# Claude 3.5 Sonnet pricing (USD per 1K tokens).
PRICE_IN_PER_1K = 0.003
PRICE_OUT_PER_1K = 0.015


# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
)
logger = logging.getLogger("onboarding-api")


def jlog(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, default=str))


# ── Clients ────────────────────────────────────────────────────
claude = Anthropic(api_key=ANTHROPIC_API_KEY)


# ── Schemas ────────────────────────────────────────────────────
class OnboardRequest(BaseModel):
    applicant_id: str | None = Field(default=None, max_length=60)
    documents: list[str] = Field(min_length=1, max_length=MAX_DOCS)

    @field_validator("documents")
    @classmethod
    def _check_sizes(cls, docs: list[str]) -> list[str]:
        for i, d in enumerate(docs):
            try:
                raw = base64.b64decode(d, validate=True)
            except Exception as exc:
                raise ValueError(f"Document {i}: invalid base64 ({exc})") from exc
            if len(raw) > MAX_DOC_BYTES:
                raise ValueError(f"Document {i}: size {len(raw)} exceeds {MAX_DOC_BYTES}")
        return docs


class ExtractedField(BaseModel):
    name: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_doc: int


class OnboardResponse(BaseModel):
    applicant_id: str
    extracted_fields: dict[str, ExtractedField]
    risk_score: float = Field(ge=0.0, le=1.0)
    next_step: str  # "auto_approve" | "manual_review" | "decline" | "collect_more_docs"
    rationale: str
    cost: float
    latency_ms: int


# ── OCR (mock) ────────────────────────────────────────────────
async def ocr_one(client: httpx.AsyncClient, b64_doc: str, idx: int) -> dict:
    try:
        resp = await client.post(
            f"{OCR_API_URL}/process",
            headers={"Authorization": f"Bearer {OCR_API_KEY}"},
            json={"content_b64": b64_doc},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"doc_index": idx, "text": data.get("text", ""), "doc_type": data.get("doc_type", "unknown")}
    except Exception as exc:
        jlog("ocr_error", doc_index=idx, error=str(exc))
        raise HTTPException(status_code=503, detail=f"OCR failed on document {idx}")


async def run_ocr(documents: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(*[ocr_one(client, d, i) for i, d in enumerate(documents)])


# ── LLM field extraction ──────────────────────────────────────
EXTRACT_PROMPT = (
    "You are a structured data extractor for US P&C insurance onboarding. "
    "Given OCR'd text from one or more documents, extract these fields when present: "
    "full_name, date_of_birth, driver_license, state, address, vehicle_vin, vehicle_year, "
    "vehicle_make, vehicle_model, prior_insurer, ssn_last4. "
    'Return ONLY JSON: {"fields": [{"name": "...", "value": "...", "confidence": 0..1, "source_doc": <idx>}]}. '
    "Never fabricate values. If a field is absent, omit it."
)


def compute_cost(tokens_in: int, tokens_out: int) -> float:
    return round(
        (tokens_in / 1000) * PRICE_IN_PER_1K + (tokens_out / 1000) * PRICE_OUT_PER_1K,
        6,
    )


def extract_fields(ocr_results: list[dict]) -> tuple[list[ExtractedField], int, int]:
    blob = "\\n\\n".join(
        f"=== DOC {r['doc_index']} ({r['doc_type']}) ===\\n{r['text']}" for r in ocr_results
    )
    try:
        resp = claude.messages.create(
            model=MODEL_ID,
            max_tokens=900,
            system=EXTRACT_PROMPT,
            messages=[{"role": "user", "content": blob}],
        )
    except APIError as exc:
        jlog("claude_error", error=str(exc))
        raise HTTPException(status_code=503, detail="Extraction model unavailable")

    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        jlog("llm_parse_error", raw=text[:400])
        raise HTTPException(status_code=502, detail="Extraction returned invalid JSON")

    out: list[ExtractedField] = []
    for f in parsed.get("fields", [])[:40]:
        try:
            out.append(ExtractedField(**f))
        except Exception:
            continue
    return out, resp.usage.input_tokens, resp.usage.output_tokens


# ── Mock enrichment integrations ──────────────────────────────
async def score_sources(fields: dict[str, ExtractedField]) -> dict[str, float]:
    async def _get(url: str, params: dict, source: str) -> float:
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return float(resp.json().get("risk", 0.5))
        except Exception as exc:
            jlog("enrichment_error", source=source, error=str(exc))
            return 0.5  # neutral when source unavailable

    def _field(name: str) -> str:
        f = fields.get(name)
        return f.value if f else ""

    dmv_task = _get(
        f"{DMV_API_URL}/verify",
        {"license": _field("driver_license"), "state": _field("state")},
        "dmv",
    )
    credit_task = _get(
        f"{CREDIT_API_URL}/score",
        {"ssn_last4": _field("ssn_last4")},
        "credit",
    )
    uw_task = _get(
        f"{UW_API_URL}/preflight",
        {"vin": _field("vehicle_vin")},
        "underwriting",
    )
    dmv, credit, uw = await asyncio.gather(dmv_task, credit_task, uw_task)
    return {"dmv": dmv, "credit": credit, "underwriting": uw}


def decide(risk_score: float, fields_map: dict[str, ExtractedField]) -> tuple[str, str]:
    required = {"full_name", "date_of_birth", "driver_license", "vehicle_vin"}
    missing = [f for f in required if f not in fields_map]
    if missing:
        return "collect_more_docs", f"Missing required fields: {', '.join(missing)}"
    low_conf = [name for name, f in fields_map.items() if f.confidence < 0.7]
    if low_conf:
        return "manual_review", f"Low-confidence extractions: {', '.join(low_conf)}"
    if risk_score >= 0.75:
        return "decline", f"Risk score {risk_score:.2f} exceeds auto-decline threshold."
    if risk_score >= 0.45:
        return "manual_review", f"Risk score {risk_score:.2f} needs underwriter review."
    return "auto_approve", f"Risk score {risk_score:.2f} within auto-approve band."


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="Meridian Onboarding API", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": MODEL_ID, "max_docs": MAX_DOCS}


@app.post("/onboard", response_model=OnboardResponse)
async def onboard(req: OnboardRequest) -> OnboardResponse:
    started = time.perf_counter()
    req_id = str(uuid.uuid4())
    applicant_id = req.applicant_id or f"app_{req_id[:8]}"

    ocr_results = await run_ocr(req.documents)
    fields_list, tokens_in, tokens_out = extract_fields(ocr_results)
    fields_map: dict[str, ExtractedField] = {f.name: f for f in fields_list}

    sources = await score_sources(fields_map)
    # Weighted risk score from the three enrichment sources.
    risk_score = round(
        0.40 * sources["dmv"] + 0.35 * sources["credit"] + 0.25 * sources["underwriting"],
        3,
    )

    next_step, rationale = decide(risk_score, fields_map)

    cost = compute_cost(tokens_in, tokens_out)
    latency_ms = int((time.perf_counter() - started) * 1000)

    jlog(
        "onboarding_completed",
        request_id=req_id,
        applicant_id=applicant_id,
        doc_count=len(req.documents),
        fields_extracted=len(fields_map),
        risk_score=risk_score,
        next_step=next_step,
        latency_ms=latency_ms,
        cost=cost,
    )

    return OnboardResponse(
        applicant_id=applicant_id,
        extracted_fields=fields_map,
        risk_score=risk_score,
        next_step=next_step,
        rationale=rationale,
        cost=cost,
        latency_ms=latency_ms,
    )
""",
                    "expected_output": None,
                    "deployment_config": {
                        "platform": "gcp",
                        "service": "cloud_run",
                        "dockerfile": """FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
""",
                        "requirements": (
                            "fastapi>=0.115.0\n"
                            "uvicorn[standard]>=0.30.0\n"
                            "pydantic>=2.6.0\n"
                            "httpx>=0.27.0\n"
                            "anthropic>=0.39.0\n"
                        ),
                        "infra_hint": (
                            "Build and push to Artifact Registry: "
                            "`gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT/meridian/onboarding`. "
                            "Deploy: `gcloud run deploy onboarding --image ... "
                            "--region us-central1 --memory 2Gi --cpu 2 "
                            "--min-instances 1 --max-instances 30 --concurrency 4 "
                            "--allow-unauthenticated --set-secrets "
                            "ANTHROPIC_API_KEY=anthropic-key:latest`. "
                            "Enable Cloud Logging + Cloud Monitoring alerting for p95 latency > 6s "
                            "and 5xx rate > 1%."
                        ),
                    },
                    "demo_data": {
                        "phases": [
                            {"id": "local", "title": "Local Build"},
                            {"id": "docker", "title": "Containerize"},
                            {"id": "deploy", "title": "Deploy to Cloud Run"},
                            {"id": "test", "title": "Field Test"},
                        ],
                        "checklist": [
                            {"id": "check_endpoint", "label": "POST /onboard returns {extracted_fields, risk_score, next_step}"},
                            {"id": "check_validation", "label": "Oversized docs (>8MB) return 413; invalid base64 returns 422"},
                            {"id": "check_ocr", "label": "OCR runs concurrently across all submitted documents"},
                            {"id": "check_extraction", "label": "Claude returns per-field confidence; sub-0.7 fields go to manual review"},
                            {"id": "check_enrichment", "label": "DMV + credit + underwriting mocks contribute to weighted risk score"},
                            {"id": "check_decision", "label": "next_step is one of auto_approve, manual_review, decline, collect_more_docs"},
                            {"id": "check_logs", "label": "Structured JSON logs per onboarding (latency, cost, doc_count, risk_score)"},
                            {"id": "check_docker", "label": "Container builds and serves on localhost:8080 locally"},
                            {"id": "check_deploy", "label": "Deployed to Cloud Run with min=1, max=30, concurrency=4"},
                            {"id": "check_field_test", "label": "Field test with 20 realistic applicant packets passes (p95 < 6s, cost < $0.18)"},
                        ],
                    },
                    "validation": {
                        "endpoint_check": {
                            "method": "POST",
                            "path": "/onboard",
                            "body": {
                                "applicant_id": "app_demo_0042",
                                "documents": [
                                    "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2c+PgplbmRvYmoKdHJhaWxlcgo8PC9Sb290IDEgMCBSPj4KJSVFT0YK",
                                    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
                                ],
                            },
                            "expected_status": 200,
                            "expected_fields": ["applicant_id", "extracted_fields", "risk_score", "next_step", "rationale", "cost", "latency_ms"],
                        },
                    },
                },
            ],
        },
    ],
}
