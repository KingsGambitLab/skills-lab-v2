"""
Compliance Course: Prevention of Sexual Harassment (POSH)
Scenario-driven training covering recognition, response, and responsibilities.
"""

COURSE = {
    "id": "posh-compliance",
    "title": "Prevention of Sexual Harassment (POSH)",
    "subtitle": "Recognize, respond to, and prevent workplace harassment",
    "icon": "🛡️",
    "course_type": "compliance",
    "level": "All Levels",
    "tags": ["compliance", "posh", "harassment-prevention", "workplace-safety", "hr"],
    "estimated_time": "~1 hour",
    "description": (
        "This isn't a checkbox exercise. Through realistic scenarios and gray-area "
        "situations, you'll develop the judgment to recognize harassment, the confidence "
        "to respond appropriately, and the knowledge to fulfill your legal obligations "
        "under the POSH Act."
    ),
    "modules": [
        # ── Module 1: Understanding Workplace Harassment ──────────────
        {
            "position": 1,
            "title": "Understanding Workplace Harassment",
            "subtitle": "Beyond the obvious -- recognizing what harassment really looks like",
            "estimated_time": "20 min",
            "objectives": [
                "Recognize harassment in ambiguous, real-world situations",
                "Understand key definitions under the POSH Act, 2013",
                "Know the composition and role of the Internal Complaints Committee",
            ],
            "steps": [
                # Step 1 — concept (scenario hook)
                {
                    "position": 1,
                    "title": "This Happened at a Real Company",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.posh-demo { background: #1e2538; border: 1px solid #2a3352; border-radius: 12px; padding: 22px; margin: 16px 0; color: #e8ecf4; font-family: 'Inter', system-ui, sans-serif; }
.posh-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.posh-demo .hook { background: linear-gradient(135deg, #151b2e, #252e45); border-left: 4px solid #2dd4bf; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 18px; }
.posh-demo .hook strong { color: #2dd4bf; }
.posh-demo .subhead { color: #8b95b0; font-size: 0.88em; margin-bottom: 14px; }
.posh-demo .scenes { display: flex; flex-direction: column; gap: 10px; }
.posh-demo .scene { background: #151b2e; border: 1px solid #2a3352; border-radius: 8px; padding: 14px 16px; transition: all 0.2s; }
.posh-demo .scene.answered { border-color: #4a7cff; }
.posh-demo .scene .label { color: #8b95b0; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.posh-demo .scene .body { font-size: 0.92em; line-height: 1.55; color: #e8ecf4; margin-bottom: 10px; }
.posh-demo .buttons { display: flex; gap: 6px; flex-wrap: wrap; }
.posh-demo .btn-class { background: #151b2e; color: #e8ecf4; border: 1px solid #2a3352; padding: 7px 12px; border-radius: 5px; cursor: pointer; font-size: 0.82em; transition: all 0.15s; }
.posh-demo .btn-class:hover { border-color: #4a7cff; }
.posh-demo .btn-class.picked.accept { background: rgba(45,212,191,0.15); border-color: #2dd4bf; color: #2dd4bf; }
.posh-demo .btn-class.picked.question { background: rgba(251,191,36,0.15); border-color: #fbbf24; color: #fbbf24; }
.posh-demo .btn-class.picked.violation { background: rgba(248,113,113,0.15); border-color: #f87171; color: #f87171; }
.posh-demo .feedback { display: none; margin-top: 10px; padding: 10px 12px; border-radius: 6px; font-size: 0.84em; line-height: 1.5; }
.posh-demo .feedback.show { display: block; }
.posh-demo .feedback .verdict { font-weight: 700; margin-bottom: 4px; }
.posh-demo .feedback.correct { background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.3); color: #e8ecf4; }
.posh-demo .feedback.correct .verdict { color: #2dd4bf; }
.posh-demo .feedback.wrong { background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.3); color: #e8ecf4; }
.posh-demo .feedback.wrong .verdict { color: #f87171; }
.posh-demo .feedback .cite { display: block; margin-top: 6px; color: #8b95b0; font-style: italic; font-size: 0.8em; }
.posh-demo .final { display: none; margin-top: 14px; padding: 14px 16px; border-radius: 8px; background: rgba(74,124,255,0.08); border: 1px solid rgba(74,124,255,0.3); color: #e8ecf4; }
.posh-demo .final.show { display: block; }
.posh-demo .final b { color: #4a7cff; }
</style>

<div class="posh-demo">
  <h2>Spot the Line</h2>
  <div class="hook">
    <strong>The problem:</strong> 73% of employees have witnessed workplace harassment. Only 14% reported it. What stops people from reporting, and what are the actual legal lines?
  </div>

  <div class="subhead">Read each interaction. Classify it as <b style="color:#2dd4bf">Acceptable</b>, <b style="color:#fbbf24">Questionable</b>, or <b style="color:#f87171">Violation</b>. Many are gray areas -- that is the point.</div>

  <div class="scenes" id="poshScenes"></div>

  <div class="final" id="poshFinal"></div>
</div>

<script>
(function(){
  var scenes = [
    {
      id: "s1",
      label: "Scene 1: The Compliment",
      body: "A team lead tells a direct report in the hallway: That color really suits you. You always dress so well.",
      correct: "question",
      explanation: {
        accept: "Not quite. Repeated commentary on a reports appearance, even if well-meant, crosses into territory the POSH Act recognizes as creating an uncomfortable work environment when power-asymmetric.",
        question: "Correct. A one-off compliment is not illegal, but Vishaka Guidelines warn against superiors repeatedly commenting on subordinates appearance. Frequency and power imbalance matter more than intent.",
        violation: "Close but context matters. A single comment, without pattern or pressure, would rarely meet the legal threshold alone. It becomes a violation when repeated or tied to job outcomes."
      },
      cite: "Reference: Vishaka v. State of Rajasthan (1997); POSH Act 2013, Section 3(2)."
    },
    {
      id: "s2",
      label: "Scene 2: The Invitation",
      body: "A senior manager invites a junior analyst to dinner -- alone -- to discuss her promotion. She declines. He invites again the next week, adding: I think you are being difficult.",
      correct: "violation",
      explanation: {
        accept: "No. This involves a quid pro quo signal -- tying career outcomes to acceptance of after-hours personal contact. That alone meets the statutory test.",
        question: "Closer, but still too lenient. Once a subordinate declines and the superior pressures them a second time with veiled career consequences, the law treats this as sexual harassment.",
        violation: "Correct. Section 3(2)(iv) of the POSH Act: implicitly promising preferential treatment, or threatening detrimental treatment, tied to sexual or personal behavior is harassment. Pressure after refusal is the clincher."
      },
      cite: "Reference: POSH Act 2013, Section 3(2)(iv); Apparel Export Promotion Council v. Chopra (1999)."
    },
    {
      id: "s3",
      label: "Scene 3: The Messages",
      body: "A colleague sends another colleague six Instagram DMs in two days after work hours, despite the second person only replying once, politely. The messages include compliments and a photo of a sunset with the caption: wish you were here.",
      correct: "violation",
      explanation: {
        accept: "No. Persistent unsolicited personal contact, after signals that it is unwelcome, meets the unwelcome conduct threshold under the POSH Act.",
        question: "Understandable read, but the facts go past gray. One-sided reply ratio plus persistence plus romantic framing = unwelcome conduct as defined in the statute.",
        violation: "Correct. The key word in Section 3 is unwelcome. The pattern (one reply, six messages, romantic framing) establishes the conduct was unwelcome regardless of sender intent."
      },
      cite: "Reference: POSH Act 2013, Section 3(1); Shanta Kumar v. CSIR (Delhi HC, 2017)."
    },
    {
      id: "s4",
      label: "Scene 4: The Contact",
      body: "During a team photo, a manager briefly puts his arm around a junior employees shoulder for the shot. She stiffens but says nothing. He removes his arm after the photo.",
      correct: "question",
      explanation: {
        accept: "Too permissive. Even brief physical contact without consent in a power-asymmetric relationship should not be waved through. Her body language signaled discomfort.",
        question: "Correct. A single fleeting contact in a group setting is a gray area -- not automatically illegal but requires care. If she reports feeling uncomfortable, the ICC should inquire whether a pattern exists.",
        violation: "Too strict on a single event. Courts distinguish casual contact from pattern-based harassment. However, if the manager has done this repeatedly with women and not men, the analysis shifts."
      },
      cite: "Reference: POSH Act 2013, Section 3(2)(v); Medha Kotwal Lele v. Union of India (2013)."
    },
    {
      id: "s5",
      label: "Scene 5: The Aftermath",
      body: "An employee files an ICC complaint. Two weeks later, her quarterly review is downgraded from Exceeds to Meets by the manager she reported, who also reassigns her off the flagship project.",
      correct: "violation",
      explanation: {
        accept: "No. This is textbook retaliation.",
        question: "Not gray. Adverse action following a protected complaint, by the named respondent, with no documented performance issue, is retaliation as a matter of law.",
        violation: "Correct. Section 19(h) of the POSH Act specifically protects complainants from retaliation. Downgrading a review and removing a high-visibility project after a complaint triggers independent liability -- even if the underlying harassment complaint does not prevail."
      },
      cite: "Reference: POSH Act 2013, Section 19(h); Vishaka Guidelines, Clause 7."
    }
  ];

  var answers = {};

  function buildButton(sceneId, choice, label, picked) {
    var cls = "btn-class " + choice + (picked ? " picked" : "");
    return '<button class="' + cls + '" data-sid="' + sceneId + '" data-choice="' + choice + '">' + label + '</button>';
  }

  function render() {
    var html = '';
    scenes.forEach(function(s){
      var ans = answers[s.id];
      html += '<div class="scene' + (ans ? ' answered' : '') + '" id="sc-' + s.id + '">'
        + '<div class="label">' + s.label + '</div>'
        + '<div class="body">' + s.body + '</div>'
        + '<div class="buttons">'
        + buildButton(s.id, "accept", "Acceptable", ans === "accept")
        + buildButton(s.id, "question", "Questionable", ans === "question")
        + buildButton(s.id, "violation", "Violation", ans === "violation")
        + '</div>';
      if (ans) {
        var isCorrect = ans === s.correct;
        html += '<div class="feedback show ' + (isCorrect ? "correct" : "wrong") + '">'
          + '<div class="verdict">' + (isCorrect ? "Correct legal read" : "The law sees this differently") + '</div>'
          + s.explanation[ans]
          + '<span class="cite">' + s.cite + '</span>'
          + '</div>';
      }
      html += '</div>';
    });
    document.getElementById('poshScenes').innerHTML = html;

    document.querySelectorAll('.posh-demo .btn-class').forEach(function(btn){
      btn.addEventListener('click', function(){
        var sid = this.getAttribute('data-sid');
        var choice = this.getAttribute('data-choice');
        answers[sid] = choice;
        render();
      });
    });

    var answered = Object.keys(answers).length;
    if (answered === scenes.length) {
      var correct = 0;
      scenes.forEach(function(s){ if (answers[s.id] === s.correct) correct++; });
      var f = document.getElementById('poshFinal');
      f.classList.add('show');
      f.innerHTML = '<b>' + correct + '/5 legally correct.</b> '
        + (correct >= 4
            ? "You read the statute well. Notice how often you said Questionable -- thats the realistic answer for most workplace gray areas. The legal test is pattern, power, and unwelcomeness, not intent."
            : "Most people miss Scene 1 or Scene 4 because intent feels important. Under the POSH Act it is not: the test is whether the conduct is unwelcome, not whether the actor meant harm. Review the citations.");
    }
  }

  render();
})();
</script>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — sjt (gray area: repeated coffee invitations)
                {
                    "position": 2,
                    "title": "The Persistent Invitation",
                    "step_type": "exercise",
                    "exercise_type": "sjt",
                    "content": """
<p>Read this scenario carefully and rank the response options from
<strong>BEST (1)</strong> to <strong>WORST (4)</strong>.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "Vikram is a senior manager. He has asked Aisha, a junior analyst on "
                            "another team, to grab coffee four times in the past two weeks. Aisha "
                            "declined politely the first two times, citing being busy. The third "
                            "time, Vikram said, 'Come on, it's just coffee -- I could really help "
                            "your career here.' Aisha went but felt uncomfortable. Now Vikram has "
                            "asked again, this time via a personal text message on Saturday morning. "
                            "Aisha mentions this to you in passing and says, 'It's probably nothing, "
                            "but it's starting to feel weird.'"
                        ),
                        "instruction": "Rank these responses from BEST (1) to WORST (4):",
                        "options": [
                            {
                                "id": "a",
                                "text": "Tell Aisha she should just firmly say no next time -- it's probably just awkward networking and not worth escalating.",
                                "correct_rank": 3,
                                "explanation": (
                                    "This minimizes Aisha's discomfort and puts the burden on her to manage "
                                    "a senior person's behavior. While not the worst response, it dismisses "
                                    "a pattern that includes a power imbalance (senior manager vs. junior "
                                    "analyst) and after-hours personal contact."
                                ),
                            },
                            {
                                "id": "b",
                                "text": "Listen without judgment, acknowledge that the pattern sounds concerning, and let Aisha know she can file a complaint with the ICC if she wants to -- offer to help her understand the process.",
                                "correct_rank": 1,
                                "explanation": (
                                    "This is the best response. You validate her experience without "
                                    "overreacting, inform her of her options without pressuring her, "
                                    "and offer practical support. You're respecting her agency while "
                                    "ensuring she has the information she needs."
                                ),
                            },
                            {
                                "id": "c",
                                "text": "Go directly to Vikram and tell him to stop contacting Aisha outside work hours.",
                                "correct_rank": 4,
                                "explanation": (
                                    "This is the worst option. Confronting the alleged harasser without "
                                    "the complainant's consent can escalate the situation, lead to "
                                    "retaliation against Aisha, and compromise any future formal "
                                    "investigation. Never act without the affected person's knowledge."
                                ),
                            },
                            {
                                "id": "d",
                                "text": "Tell Aisha you'll report it to the ICC on her behalf since it's your duty to report harassment.",
                                "correct_rank": 2,
                                "explanation": (
                                    "The instinct to act is good, but filing on someone else's behalf "
                                    "without their explicit consent removes their agency. In most cases, "
                                    "the affected person should decide whether to file. The exception is "
                                    "if you're a manager with a legal duty to report -- but even then, "
                                    "you should discuss it with the person first."
                                ),
                            },
                        ],
                        "scoring": "full_match=10, off_by_one=7, off_by_two=4, off_by_three=0",
                    },
                },
                # Step 3 — concept (definitions)
                {
                    "position": 3,
                    "title": "Key Definitions Under the POSH Act",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>The POSH Act, 2013 -- What You Need to Know</h2>

<p>The <strong>Sexual Harassment of Women at Workplace (Prevention, Prohibition and
Redressal) Act, 2013</strong> defines the legal framework for addressing workplace
harassment in India. While the Act specifically protects women, many organizations
extend similar protections to all employees.</p>

<h3>What Constitutes Sexual Harassment?</h3>
<p>The Act defines sexual harassment as any unwelcome act or behavior, whether
directly or by implication, including:</p>
<ol>
  <li><strong>Physical contact and advances</strong> -- unwanted touching, blocking movement</li>
  <li><strong>Demand or request for sexual favours</strong> -- explicit or implied quid pro quo</li>
  <li><strong>Sexually coloured remarks</strong> -- comments about appearance, jokes with sexual content</li>
  <li><strong>Showing pornography</strong> -- sharing explicit content physically or digitally</li>
  <li><strong>Any other unwelcome physical, verbal, or non-verbal conduct of a sexual nature</strong></li>
</ol>

<h3>The "Unwelcome" Standard</h3>
<p>The key word is <strong>unwelcome</strong>. It doesn't matter if the behavior was
intended as friendly, humorous, or complimentary. What matters is whether it was
<em>wanted</em> by the recipient. Context, power dynamics, and frequency all factor
into this assessment.</p>

<h3>The "Reasonable Woman" Test</h3>
<p>Courts apply the standard of whether a <em>reasonable person in the same
circumstances</em> would find the conduct hostile, intimidating, or offensive. This
accounts for the fact that harassment is experienced differently based on power
dynamics, gender, and cultural context.</p>

<h3>Extended Workplace</h3>
<p>Under the Act, "workplace" includes:</p>
<ul>
  <li>Office premises, offsite locations, and client sites</li>
  <li>Work-related travel and events (including team dinners and offsites)</li>
  <li>Digital communications (email, messaging apps, video calls)</li>
  <li>Any place visited by the employee arising out of or during employment</li>
</ul>

<h3>Internal Complaints Committee (ICC)</h3>
<p>Every organization with 10+ employees must constitute an ICC. It must include:</p>
<ul>
  <li>A <strong>Presiding Officer</strong> -- a senior woman employee</li>
  <li>At least <strong>2 members</strong> from employees committed to women's causes or with legal/social work experience</li>
  <li>At least <strong>1 external member</strong> from an NGO or a person familiar with issues of sexual harassment</li>
  <li>At least <strong>50% women members</strong></li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 4 — mcq (ICC composition)
                {
                    "position": 4,
                    "title": "Knowledge Check: ICC Composition",
                    "step_type": "exercise",
                    "exercise_type": "mcq",
                    "content": """
<p>Test your understanding of the Internal Complaints Committee requirements.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "question": "Which of the following is a mandatory requirement for the Internal Complaints Committee under the POSH Act?",
                        "options": [
                            {
                                "text": "The Presiding Officer must be the CEO or a board member",
                                "correct": False,
                                "explanation": (
                                    "The Presiding Officer must be a senior woman employee, "
                                    "not necessarily the CEO or a board member. The role requires "
                                    "seniority within the organization, not a specific title."
                                ),
                            },
                            {
                                "text": "At least one member must be from an external organization (NGO or person familiar with sexual harassment issues)",
                                "correct": True,
                                "explanation": (
                                    "Correct. The Act mandates at least one external member to ensure "
                                    "independence and prevent internal bias. This person typically comes "
                                    "from an NGO or has relevant legal/social work background."
                                ),
                            },
                            {
                                "text": "All members must be women",
                                "correct": False,
                                "explanation": (
                                    "At least 50% of ICC members must be women, but the committee "
                                    "is not required to be exclusively women. Male members can serve, "
                                    "provided the majority-women requirement is met."
                                ),
                            },
                            {
                                "text": "The committee must include at least one HR representative",
                                "correct": False,
                                "explanation": (
                                    "While HR often supports the ICC process, the Act does not mandate "
                                    "an HR representative on the committee. The specified requirements "
                                    "are: a senior woman Presiding Officer, 2+ employee members, and "
                                    "1+ external member."
                                ),
                            },
                        ],
                    },
                    "demo_data": None,
                },
            ],
        },
        # ── Module 2: Recognizing & Responding ────────────────────────
        {
            "position": 2,
            "title": "Recognizing & Responding",
            "subtitle": "What to do when you witness or receive a complaint",
            "estimated_time": "20 min",
            "objectives": [
                "Navigate complex bystander scenarios with appropriate judgment",
                "Rank responses in power-imbalance situations",
                "Know the correct sequence for filing a complaint",
            ],
            "steps": [
                # Step 1 — scenario_branch (witnessing inappropriate comments)
                {
                    "position": 1,
                    "title": "The Team Dinner",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>You're at a team dinner after a successful project launch. Things are about
to get uncomfortable. Walk through this scenario and make your choices.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's 9 PM at a restaurant after your team's quarterly offsite. "
                            "Drinks have been flowing. Nikhil, a popular team lead, starts making "
                            "comments about Meera's outfit: 'You should dress like that more often -- "
                            "it's much better than your usual boring work clothes.' A few people "
                            "laugh nervously. Meera smiles but looks uncomfortable. Nikhil then puts "
                            "his arm around Meera's shoulder for a selfie she clearly didn't agree to."
                        ),
                        "steps": [
                            {
                                "question": "You notice Meera looks uncomfortable after Nikhil's comments and the unsolicited physical contact. What do you do in the moment?",
                                "options": [
                                    {
                                        "label": "Create a natural interruption -- ask Meera to help you order something at the bar, giving her an exit from the situation",
                                        "correct": True,
                                        "explanation": (
                                            "This is effective bystander intervention. You de-escalate without "
                                            "creating a public confrontation, give Meera a choice to exit, and "
                                            "don't put her on the spot. This technique is called 'the distraction.'"
                                        ),
                                    },
                                    {
                                        "label": "Stand up and loudly call out Nikhil's behavior in front of the whole table",
                                        "correct": False,
                                        "explanation": (
                                            "While confronting the behavior is important, doing it publicly and "
                                            "aggressively can embarrass Meera, escalate the situation, and make "
                                            "you look like the aggressor. A private word with Nikhil later is "
                                            "more effective."
                                        ),
                                    },
                                    {
                                        "label": "It's a casual dinner with drinks -- people get touchy. Don't overreact",
                                        "correct": False,
                                        "explanation": (
                                            "Alcohol and informal settings don't change the definition of "
                                            "unwelcome conduct. A team dinner is an extension of the workplace "
                                            "under the POSH Act. Dismissing it normalizes the behavior."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "The next day at work, Meera pulls you aside and says, 'About last night -- Nikhil does this every time we go out. I've told him to stop but he says I'm being too sensitive. I don't want to make it a big deal, but I'm dreading the next team event.' What do you say?",
                                "options": [
                                    {
                                        "label": "Ask Meera if she'd like to talk to the ICC or if she'd prefer you to have a quiet word with Nikhil first -- let her decide the approach",
                                        "correct": True,
                                        "explanation": (
                                            "You're centering Meera's agency while presenting actionable options. "
                                            "The fact that she's told Nikhil to stop and he continued means this "
                                            "is a repeated pattern, which strengthens any future complaint. "
                                            "Supporting her choice of approach is critical."
                                        ),
                                    },
                                    {
                                        "label": "Tell Meera that this is definitely harassment and she needs to file a formal complaint immediately",
                                        "correct": False,
                                        "explanation": (
                                            "While it likely is harassment (repeated unwelcome conduct despite "
                                            "being asked to stop), pressuring someone to file before they're ready "
                                            "can backfire. Many people drop complaints when they feel pushed. "
                                            "Support and inform, don't direct."
                                        ),
                                    },
                                    {
                                        "label": "Suggest Meera simply avoid team events where Nikhil will be present",
                                        "correct": False,
                                        "explanation": (
                                            "This punishes the wrong person. Meera shouldn't have to exclude "
                                            "herself from team activities because of someone else's behavior. "
                                            "This approach also doesn't solve the problem -- it just hides it."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Effective bystander intervention uses subtle techniques -- distraction, "
                            "delegation, and delayed follow-up -- rather than public confrontation. "
                            "When someone confides in you, prioritize their agency: inform them of "
                            "options, support their choice, and never pressure them to act before "
                            "they're ready."
                        ),
                    },
                },
                # Step 2 — sjt (power imbalance)
                {
                    "position": 2,
                    "title": "The Performance Review",
                    "step_type": "exercise",
                    "exercise_type": "sjt",
                    "content": """
<p>This scenario involves a power imbalance between a manager and a direct
report. Rank the responses carefully -- the nuances matter.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "During a private performance review, your manager Anand says: "
                            "'Your work has been excellent, and I'm recommending you for a promotion. "
                            "By the way, I noticed you've been going through a tough time personally. "
                            "If you ever need to talk -- really talk -- my door is always open. Even "
                            "outside office hours.' He then adds: 'You know, the last person in your "
                            "role didn't get promoted because they weren't a good cultural fit. I'd "
                            "hate for that to happen to you.' His tone shifts from professional to "
                            "something more personal. You're not sure if he's being supportive or "
                            "if there's an implied expectation."
                        ),
                        "instruction": "Rank these responses from BEST (1) to WORST (4):",
                        "options": [
                            {
                                "id": "a",
                                "text": "Thank him for the promotion recommendation and say you prefer to keep personal discussions within work hours and through HR if needed. Document the conversation in writing afterward.",
                                "correct_rank": 1,
                                "explanation": (
                                    "This is the strongest response. You maintain professionalism, "
                                    "set a clear boundary without accusation, and create a written "
                                    "record. The documentation is crucial if the behavior escalates."
                                ),
                            },
                            {
                                "id": "b",
                                "text": "Ignore the personal comments and steer the conversation back to your performance metrics and promotion criteria.",
                                "correct_rank": 2,
                                "explanation": (
                                    "Redirecting is a reasonable immediate response, but it doesn't "
                                    "set a boundary or create documentation. It may work in the moment "
                                    "but leaves the door open for similar behavior in the future."
                                ),
                            },
                            {
                                "id": "c",
                                "text": "Take him up on the offer -- having a good relationship with your manager is important for career growth, and he's probably just being friendly.",
                                "correct_rank": 4,
                                "explanation": (
                                    "This is the riskiest response. The combination of a promotion "
                                    "discussion with personal overtures and a veiled reference to "
                                    "someone who 'wasn't a cultural fit' creates a concerning power "
                                    "dynamic. Accepting the offer could blur professional boundaries "
                                    "and create expectations."
                                ),
                            },
                            {
                                "id": "d",
                                "text": "After the meeting, mention the conversation to a trusted colleague to get a second opinion on whether you're overreacting.",
                                "correct_rank": 3,
                                "explanation": (
                                    "Seeking perspective is understandable, but informal discussions "
                                    "with colleagues can lead to gossip and may not give you accurate "
                                    "guidance. If you need a second opinion, speak with the ICC or HR "
                                    "confidentially. They can advise without creating workplace dynamics."
                                ),
                            },
                        ],
                        "scoring": "full_match=10, off_by_one=7, off_by_two=4, off_by_three=0",
                    },
                },
                # Step 3 — ordering (complaint filing steps)
                {
                    "position": 3,
                    "title": "Filing a Complaint: The Correct Sequence",
                    "step_type": "exercise",
                    "exercise_type": "ordering",
                    "content": """
<p>Arrange these steps in the correct order for filing a sexual harassment
complaint under the POSH Act. The sequence matters -- skipping or reordering
steps can compromise the process.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Arrange these steps in the correct order for filing a POSH complaint:",
                        "items": [
                            {
                                "id": "a",
                                "text": "Document the incident(s) in writing with dates, times, locations, witnesses, and any evidence (screenshots, emails)",
                                "correct_position": 1,
                            },
                            {
                                "id": "b",
                                "text": "Submit a written complaint to the Internal Complaints Committee within 3 months of the last incident (extendable to 6 months with cause)",
                                "correct_position": 2,
                            },
                            {
                                "id": "c",
                                "text": "ICC acknowledges the complaint and provides a copy to the respondent within 7 working days",
                                "correct_position": 3,
                            },
                            {
                                "id": "d",
                                "text": "The respondent submits a written reply to the ICC within 10 working days",
                                "correct_position": 4,
                            },
                            {
                                "id": "e",
                                "text": "ICC conducts an inquiry following principles of natural justice -- both parties may present witnesses and evidence",
                                "correct_position": 5,
                            },
                            {
                                "id": "f",
                                "text": "ICC completes the inquiry within 90 days and submits findings and recommendations to the employer",
                                "correct_position": 6,
                            },
                            {
                                "id": "g",
                                "text": "Employer acts on ICC recommendations within 60 days -- this may include disciplinary action, transfer, or other remedies",
                                "correct_position": 7,
                            },
                        ],
                    },
                },
            ],
        },
        # ── Module 3: Your Responsibilities ───────────────────────────
        {
            "position": 3,
            "title": "Your Responsibilities",
            "subtitle": "What's expected of you based on your role",
            "estimated_time": "20 min",
            "objectives": [
                "Know role-specific responsibilities (IC, manager, ICC member)",
                "Navigate the proper response to receiving a complaint",
                "Apply multiple POSH concepts in a complex scenario",
            ],
            "steps": [
                # Step 1 — concept (responsibilities by role)
                {
                    "position": 1,
                    "title": "Everyone Has a Role to Play",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>Responsibilities by Role</h2>

<h3>As an Individual Contributor</h3>
<ul>
  <li><strong>Know the policy.</strong> Ignorance is not a defense. Understand what constitutes harassment and how to report it.</li>
  <li><strong>Respect boundaries.</strong> If someone says your behavior makes them uncomfortable, stop immediately. Don't debate whether it "should" bother them.</li>
  <li><strong>Be an active bystander.</strong> If you witness harassment, intervene safely or report it. Silence enables.</li>
  <li><strong>Support colleagues.</strong> If someone confides in you, listen without judgment, inform them of their options, and respect their decisions.</li>
  <li><strong>Cooperate with inquiries.</strong> If called as a witness, provide honest testimony. Refusing to cooperate or providing false information can result in disciplinary action.</li>
</ul>

<h3>As a Manager</h3>
<p>You have all the IC responsibilities, <strong>plus</strong>:</p>
<ul>
  <li><strong>Legal duty to act.</strong> If you become aware of harassment in your team -- even informally -- you may have a legal obligation to address it. Consult with HR or the ICC.</li>
  <li><strong>Create a safe environment.</strong> Set team norms, address inappropriate jokes or comments in the moment, and model respectful behavior.</li>
  <li><strong>Never retaliate.</strong> If a team member files a complaint (against you or anyone else), any adverse action (poor reviews, reassignment, exclusion) will be treated as retaliation.</li>
  <li><strong>Monitor team dynamics.</strong> Watch for signs of exclusion, discomfort, or sudden behavior changes that might indicate unreported harassment.</li>
  <li><strong>Protect confidentiality.</strong> Never discuss a complaint with anyone who doesn't need to know. Breaching confidentiality is a violation under the Act.</li>
</ul>

<h3>As an ICC Member</h3>
<ul>
  <li><strong>Impartiality.</strong> You cannot serve on a case where you have a personal or professional conflict of interest.</li>
  <li><strong>Confidentiality.</strong> All proceedings, testimony, and outcomes are strictly confidential. Violations carry penalties under the Act.</li>
  <li><strong>Due process.</strong> Both parties must be heard. Follow the principles of natural justice -- no predetermined outcomes.</li>
  <li><strong>Timely completion.</strong> Complete inquiries within the 90-day statutory window.</li>
  <li><strong>Trauma-informed approach.</strong> Understand that complainants may not recall events perfectly or may appear calm -- this doesn't indicate fabrication.</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — scenario_branch (receiving a complaint as manager)
                {
                    "position": 2,
                    "title": "A Complaint Lands on Your Desk",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>You're a manager. One of your team members comes to you with a complaint
about a colleague. Walk through the proper response -- every step matters.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's Tuesday morning. Kavitha, a developer on your team, asks to speak "
                            "with you privately. She's visibly upset. She tells you that Ravi, another "
                            "developer on your team, has been sending her sexually explicit memes on "
                            "WhatsApp. She shows you her phone -- there are about a dozen messages "
                            "over the past month. She says she told Ravi to stop twice, but he "
                            "responded with a laughing emoji and kept going. Kavitha says she doesn't "
                            "want to 'make a scene' but she can't take it anymore."
                        ),
                        "steps": [
                            {
                                "question": "Kavitha has just shown you the messages. What is your immediate response?",
                                "options": [
                                    {
                                        "label": "Thank Kavitha for trusting you, acknowledge the seriousness of what she's shown you, and let her know you're required to ensure this is addressed but that she has options for how to proceed",
                                        "correct": True,
                                        "explanation": (
                                            "This balances your legal duty as a manager (you can't ignore what "
                                            "you've been told) with Kavitha's need for agency. You're being "
                                            "transparent that this can't be swept under the rug, while giving "
                                            "her a voice in how it's handled."
                                        ),
                                    },
                                    {
                                        "label": "Tell Kavitha you'll handle it and immediately go talk to Ravi to tell him to stop",
                                        "correct": False,
                                        "explanation": (
                                            "Never confront the respondent yourself. This bypasses the ICC, "
                                            "could be seen as you conducting an unauthorized investigation, "
                                            "might escalate the situation or lead to retaliation, and could "
                                            "compromise a formal inquiry later."
                                        ),
                                    },
                                    {
                                        "label": "Ask Kavitha if she's sure the messages were meant to be sexual -- maybe Ravi just has an edgy sense of humor",
                                        "correct": False,
                                        "explanation": (
                                            "Questioning the complainant's interpretation is dismissive and "
                                            "potentially re-traumatizing. Intent doesn't matter under the Act -- "
                                            "the test is whether the conduct was unwelcome, which Kavitha has "
                                            "clearly indicated by asking Ravi to stop twice."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Kavitha says she'd like to file a formal complaint with the ICC. She asks you what she should do with the WhatsApp messages. What do you advise?",
                                "options": [
                                    {
                                        "label": "Tell Kavitha to take screenshots of all messages with timestamps visible, save them in a secure location, and bring them to the ICC -- but not to delete the originals or confront Ravi about them",
                                        "correct": True,
                                        "explanation": (
                                            "Preserving evidence is critical. Screenshots with timestamps create "
                                            "a verifiable record. Advising against deletion protects the evidence "
                                            "chain, and advising against confronting Ravi prevents evidence "
                                            "tampering or retaliation."
                                        ),
                                    },
                                    {
                                        "label": "Ask Kavitha to forward the messages to your work email so you can include them in your report to the ICC",
                                        "correct": False,
                                        "explanation": (
                                            "Do not collect or store evidence yourself. You are not part of the "
                                            "ICC inquiry, and having explicit content on your work email creates "
                                            "chain-of-custody issues. Your role is to connect Kavitha with the "
                                            "ICC, not to build the case."
                                        ),
                                    },
                                    {
                                        "label": "Tell Kavitha to delete the messages for her own well-being and just describe them in her complaint",
                                        "correct": False,
                                        "explanation": (
                                            "Never advise deleting evidence. Without the actual messages, the "
                                            "complaint becomes a he-said-she-said situation. The messages are "
                                            "the strongest evidence Kavitha has."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Two days later, you notice that Ravi and Kavitha have been assigned to the same project sprint. What do you do?",
                                "options": [
                                    {
                                        "label": "Quietly reassign either Ravi or Kavitha to a different sprint, citing workload balancing, without revealing the complaint to anyone",
                                        "correct": True,
                                        "explanation": (
                                            "As a manager, you should take reasonable steps to minimize contact "
                                            "between the parties during a pending inquiry, without disclosing "
                                            "the complaint. Framing it as a workload decision maintains "
                                            "confidentiality while protecting Kavitha."
                                        ),
                                    },
                                    {
                                        "label": "Do nothing -- the ICC will sort it out and you shouldn't interfere",
                                        "correct": False,
                                        "explanation": (
                                            "You have a duty of care as a manager. Forcing a complainant to "
                                            "work closely with the respondent during an active inquiry creates "
                                            "an hostile environment and could be seen as failing to protect "
                                            "your team member."
                                        ),
                                    },
                                    {
                                        "label": "Email the project lead explaining that Kavitha filed a harassment complaint against Ravi and they shouldn't be on the same sprint",
                                        "correct": False,
                                        "explanation": (
                                            "This breaches confidentiality, which is a violation under the "
                                            "POSH Act. You can rearrange work without explaining why. Never "
                                            "disclose that a complaint has been filed to anyone who doesn't "
                                            "need to know."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "When an employee comes to you with a complaint: (1) Listen and acknowledge, "
                            "(2) Be transparent about your obligations as a manager, (3) Advise on "
                            "evidence preservation, (4) Connect them with the ICC, (5) Take reasonable "
                            "steps to protect them during the inquiry -- all while maintaining strict "
                            "confidentiality."
                        ),
                    },
                },
                # Step 3 — sjt (complex final assessment)
                {
                    "position": 3,
                    "title": "Final Assessment: The Gray Zone",
                    "step_type": "exercise",
                    "exercise_type": "sjt",
                    "content": """
<p>This final scenario combines multiple concepts: power dynamics, bystander
responsibility, organizational culture, and the limits of informal resolution.
Rank the responses carefully.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "You're on the Internal Complaints Committee. A complaint has been filed "
                            "by Sneha, a contract employee, against Arjun, the head of the business "
                            "unit she's assigned to. Sneha alleges that Arjun has been making her "
                            "stay late for 'mentoring sessions' where he discusses her personal life, "
                            "comments on her appearance, and has twice suggested they continue the "
                            "conversation over dinner. Sneha is up for contract renewal in 6 weeks.\n\n"
                            "During the inquiry, Arjun's defense is: 'I mentor all my team members. "
                            "I've taken male employees to dinner too. Sneha is misreading professional "
                            "interest as something else. She's a contract worker trying to leverage "
                            "this for a permanent position.'\n\n"
                            "Two witnesses confirm the late 'mentoring sessions' happened, but say "
                            "they didn't hear anything inappropriate. Sneha has no written evidence "
                            "-- the comments were all verbal."
                        ),
                        "instruction": "Rank these approaches from BEST (1) to WORST (4):",
                        "options": [
                            {
                                "id": "a",
                                "text": "Continue the inquiry based on Sneha's testimony and the witness confirmation of the pattern. Verbal harassment is still harassment under the Act, and lack of written evidence doesn't invalidate a complaint. Ensure Sneha's contract renewal is insulated from this process.",
                                "correct_rank": 1,
                                "explanation": (
                                    "This is the correct approach. The POSH Act does not require written "
                                    "evidence -- testimony is valid. The witnesses corroborate the pattern "
                                    "even if they didn't hear specific comments. Protecting the contract "
                                    "renewal from interference is essential to prevent retaliation. The "
                                    "complainant's employment status (contract vs. permanent) does not "
                                    "diminish their rights under the Act."
                                ),
                            },
                            {
                                "id": "b",
                                "text": "Suggest an informal resolution: ask Arjun to stop the private mentoring sessions and have HR monitor the situation for 3 months.",
                                "correct_rank": 3,
                                "explanation": (
                                    "Informal resolution (conciliation) is allowed under the Act, but only "
                                    "if the complainant requests it. Given the power imbalance (unit head "
                                    "vs. contract employee with pending renewal), informal resolution may "
                                    "not provide adequate protection. Additionally, 'monitoring' puts the "
                                    "burden on HR rather than addressing the behavior directly."
                                ),
                            },
                            {
                                "id": "c",
                                "text": "Dismiss the complaint due to insufficient evidence. Without written proof or witnesses to the specific comments, it's one person's word against another's.",
                                "correct_rank": 4,
                                "explanation": (
                                    "This is the worst approach. Dismissing a complaint solely because "
                                    "evidence is verbal sets a dangerous precedent -- most harassment is "
                                    "verbal and occurs without witnesses. The ICC's role is to conduct a "
                                    "thorough inquiry, not to apply a criminal standard of evidence. "
                                    "Witness corroboration of the pattern is significant evidence."
                                ),
                            },
                            {
                                "id": "d",
                                "text": "Accept Arjun's explanation that he mentors everyone similarly, but recommend that all future mentoring sessions be conducted in open areas during work hours as a precautionary measure.",
                                "correct_rank": 2,
                                "explanation": (
                                    "The operational recommendation is sound (open areas, work hours), "
                                    "but accepting Arjun's defense without completing the inquiry is "
                                    "premature. His claim that he mentors male employees similarly "
                                    "should be verified, not taken at face value. However, this response "
                                    "at least results in some protective action."
                                ),
                            },
                        ],
                        "scoring": "full_match=10, off_by_one=7, off_by_two=4, off_by_three=0",
                    },
                },
            ],
        },
    ],
}
