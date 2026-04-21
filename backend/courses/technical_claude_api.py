"""
Technical Skill Course: Claude API & Prompt Engineering
Covers API basics, prompt patterns, and tool use with realistic exercises.
"""

COURSE = {
    "id": "claude-api",
    "title": "Claude API & Prompt Engineering",
    "subtitle": "Build production-ready AI features with Claude",
    "icon": "🤖",
    "course_type": "technical",
    "level": "Beginner",
    "tags": ["claude", "api", "prompt-engineering", "python", "ai"],
    "estimated_time": "~1.5 hours",
    "description": (
        "Learn to integrate Claude into real applications. You'll make API calls, "
        "master prompt engineering patterns, and build a tool-using agent -- all "
        "with hands-on code exercises using insurance industry examples."
    ),
    "modules": [
        # ── Module 1: Your First API Call ──────────────────────────────
        {
            "position": 1,
            "title": "Your First API Call",
            "subtitle": "From zero to working Claude integration",
            "estimated_time": "25 min",
            "objectives": [
                "Understand the Claude Messages API request/response format",
                "Make a successful API call with correct parameters",
                "Build a real classification function powered by Claude",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "What Is the Claude API?",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.api-demo { background: #151b2e; border: 1px solid #2a3352; border-radius: 12px; padding: 24px; margin: 16px 0; font-family: 'Inter', system-ui, sans-serif; }
.api-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.api-demo .hook { background: linear-gradient(135deg, #1e2538, #252e45); border-left: 4px solid #2dd4bf; padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }
.api-demo .hook p { color: #e8ecf4; margin: 4px 0; line-height: 1.6; }
.api-demo .hook strong { color: #2dd4bf; }
.api-demo .try-area { background: #1e2538; border: 1px solid #2a3352; border-radius: 8px; padding: 20px; margin-top: 16px; }
.api-demo label { color: #8b95b0; font-size: 0.85em; display: block; margin-bottom: 6px; }
.api-demo textarea { width: 100%; background: #151b2e; color: #e8ecf4; border: 1px solid #2a3352; border-radius: 6px; padding: 12px; font-family: 'Fira Code', monospace; font-size: 0.9em; resize: vertical; min-height: 48px; box-sizing: border-box; }
.api-demo textarea:focus { outline: none; border-color: #4a7cff; }
.api-demo .btn-send { background: #4a7cff; color: #fff; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 10px; transition: background 0.2s; }
.api-demo .btn-send:hover { background: #3a6cef; }
.api-demo .btn-send:disabled { background: #2a3352; cursor: not-allowed; }
.api-demo .request-box, .api-demo .response-box { background: #0d1117; border: 1px solid #2a3352; border-radius: 8px; padding: 14px; margin-top: 14px; font-family: 'Fira Code', monospace; font-size: 0.82em; overflow-x: auto; white-space: pre-wrap; display: none; }
.api-demo .request-box { border-left: 3px solid #4a7cff; }
.api-demo .response-box { border-left: 3px solid #2dd4bf; }
.api-demo .section-label { color: #8b95b0; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; margin-top: 16px; margin-bottom: 4px; }
.api-demo .param-bar { display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap; }
.api-demo .param-bar select, .api-demo .param-bar input { background: #151b2e; color: #e8ecf4; border: 1px solid #2a3352; border-radius: 6px; padding: 8px 12px; font-size: 0.85em; }
.api-demo .typing { display: inline-block; }
.api-demo .typing span { animation: blink 1s infinite; color: #2dd4bf; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.2; } }
.api-demo .stat { display: inline-block; background: #1e2538; border: 1px solid #2a3352; border-radius: 4px; padding: 3px 10px; margin: 4px 4px 0 0; font-size: 0.78em; color: #8b95b0; }
.api-demo .stat b { color: #2dd4bf; }
</style>

<div class="api-demo">
  <h2>Try the Claude API -- Right Now</h2>
  <div class="hook">
    <p><strong>The problem:</strong> You have 500 insurance claims landing in your inbox every day. Each one needs to be classified by type and urgency -- manually, that takes a team of 6 people.</p>
    <p><strong>The solution:</strong> One API call to Claude does it in 200ms. Let's see how.</p>
  </div>

  <div class="try-area">
    <label>Type a prompt for Claude (or use the example):</label>
    <textarea id="apiPrompt">Classify this insurance claim: "I was rear-ended at a stoplight yesterday. My bumper is crushed and my neck hurts." Return JSON with claim_type, urgency, and a one-line summary.</textarea>

    <div class="param-bar">
      <select id="apiModel">
        <option value="claude-sonnet-4-20250514">claude-sonnet-4-20250514</option>
        <option value="claude-haiku-4-20250514">claude-haiku-4-20250514</option>
      </select>
      <input type="number" id="apiTokens" value="256" min="64" max="4096" style="width:90px;" />
      <span style="color:#8b95b0;font-size:0.85em;align-self:center;">max tokens</span>
    </div>

    <button class="btn-send" id="apiSendBtn" onclick="sendApiDemo()">Send API Call</button>

    <div class="section-label" id="reqLabel" style="display:none;">REQUEST</div>
    <div class="request-box" id="apiRequest"></div>

    <div class="section-label" id="resLabel" style="display:none;">RESPONSE</div>
    <div class="response-box" id="apiResponse"></div>
  </div>
</div>

<script>
(function(){
  const mockResponses = {
    'rear-ended': '{"claim_type": "auto_collision", "urgency": "high", "summary": "Rear-end collision with vehicle damage and potential neck injury."}',
    'windshield': '{"claim_type": "auto_comprehensive", "urgency": "low", "summary": "Windshield damage from road debris, no injuries."}',
    'flood': '{"claim_type": "property_water_damage", "urgency": "medium", "summary": "Water damage to property from flooding event."}',
    'stolen': '{"claim_type": "auto_theft", "urgency": "high", "summary": "Vehicle theft report, location and time documented."}',
    'fire': '{"claim_type": "property_fire", "urgency": "high", "summary": "Fire damage to insured property requiring immediate assessment."}',
    'default': '{"claim_type": "general", "urgency": "medium", "summary": "Claim received and queued for classification review."}'
  };

  window.sendApiDemo = function() {
    const prompt = document.getElementById('apiPrompt').value.trim();
    const model = document.getElementById('apiModel').value;
    const tokens = document.getElementById('apiTokens').value;
    const btn = document.getElementById('apiSendBtn');
    if (!prompt) return;

    const reqJSON = JSON.stringify({model: model, max_tokens: parseInt(tokens), messages: [{role: "user", content: prompt}]}, null, 2);
    document.getElementById('apiRequest').textContent = 'POST /v1/messages' + String.fromCharCode(10,10) + reqJSON;
    document.getElementById('apiRequest').style.display = 'block';
    document.getElementById('reqLabel').style.display = 'block';

    btn.disabled = true;
    btn.textContent = 'Calling API...';
    document.getElementById('resLabel').style.display = 'block';
    document.getElementById('apiResponse').style.display = 'block';
    document.getElementById('apiResponse').innerHTML = '<span class="typing"><span>|</span></span>';

    const lowerPrompt = prompt.toLowerCase();
    let mockKey = 'default';
    for (const k of Object.keys(mockResponses)) {
      if (k !== 'default' && lowerPrompt.includes(k)) { mockKey = k; break; }
    }
    const responseText = mockResponses[mockKey];
    const inputTokens = Math.floor(prompt.split(/ +/).length * 1.3);
    const outputTokens = Math.floor(responseText.length / 4);

    setTimeout(function() {
      const resObj = {id: "msg_01X" + Math.random().toString(36).slice(2,8), type: "message", role: "assistant", content: [{type: "text", text: responseText}], model: model, stop_reason: "end_turn", usage: {input_tokens: inputTokens, output_tokens: outputTokens}};
      document.getElementById('apiResponse').textContent = JSON.stringify(resObj, null, 2);
      btn.disabled = false;
      btn.textContent = 'Send API Call';
      const statsHtml = '<span class="stat"><b>' + inputTokens + '</b> input tokens</span><span class="stat"><b>' + outputTokens + '</b> output tokens</span><span class="stat">latency <b>~210ms</b></span><span class="stat">stop: <b>end_turn</b></span>';
      document.getElementById('apiResponse').insertAdjacentHTML('afterend', '<div id="apiStats" style="margin-top:6px;">' + statsHtml + '</div>');
      const old = document.querySelectorAll('#apiStats');
      if (old.length > 1) old[0].remove();
    }, 1200);
  };
})();
</script>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — fill_in_blank
                {
                    "position": 2,
                    "title": "Complete Your First API Call",
                    "step_type": "exercise",
                    "exercise_type": "fill_in_blank",
                    "content": """
<p>Fill in the blanks to make a working Claude API call. You need to specify
the correct model name, set a token limit, and provide the user message.</p>
""",
                    "code": """import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="____",
    max_tokens=____,
    messages=[
        {
            "role": "user",
            "content": "____"
        }
    ]
)

print(response.content[0].text)
""",
                    "expected_output": None,
                    "validation": {
                        "blanks": [
                            {
                                "index": 0,
                                "answer": "claude-sonnet-4-20250514",
                                "hint": "Use the latest Sonnet model ID: claude-sonnet-4-20250514",
                                "alternatives": ["claude-haiku-4-20250514"],
                            },
                            {
                                "index": 1,
                                "answer": "1024",
                                "hint": "A common default is 1024 tokens -- enough for most short responses",
                                "alternatives": ["512", "2048", "256"],
                            },
                            {
                                "index": 2,
                                "answer": "Explain what an insurance deductible is in one sentence.",
                                "hint": "Write any clear question or instruction for Claude",
                                "accept_any": True,
                            },
                        ]
                    },
                    "demo_data": None,
                },
                # Step 3 — code (read & run)
                {
                    "position": 3,
                    "title": "Run a Working Example",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Here's a complete, working API call. Run it and observe the response structure.
Notice how the response comes back as a <code>Message</code> object with a
<code>content</code> list.</p>
""",
                    "code": """import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[
        {
            "role": "user",
            "content": "What are the 3 most common types of auto insurance claims? Be brief."
        }
    ]
)

# The response object
print("Stop reason:", response.stop_reason)
print("Tokens used:", response.usage.input_tokens, "in /", response.usage.output_tokens, "out")
print()
print("Response:")
print(response.content[0].text)
""",
                    "expected_output": """Stop reason: end_turn
Tokens used: 28 in / 94 out

Response:
The three most common types of auto insurance claims are:
1. **Collision claims** -- damage from hitting another vehicle or object
2. **Comprehensive claims** -- theft, weather damage, vandalism, or animal strikes
3. **Liability claims** -- injuries or property damage you cause to others""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 4 — code_exercise
                {
                    "position": 4,
                    "title": "Build a Claims Classifier",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build a function that takes a free-text claim description and uses Claude to
classify it. The function should return a dictionary with <code>claim_type</code>,
<code>urgency</code> (low/medium/high), and a brief <code>summary</code>.</p>
<p><strong>Hint:</strong> Use a system prompt to constrain Claude's output format
to valid JSON.</p>
""",
                    "code": """import anthropic
import json

def classify_claim(description: str) -> dict:
    \"\"\"Classify an insurance claim using Claude.

    Args:
        description: Free-text claim description from the customer.

    Returns:
        dict with keys: claim_type, urgency, summary
    \"\"\"
    client = anthropic.Anthropic()

    # TODO: Define a system prompt that instructs Claude to return JSON
    # with exactly three keys: claim_type, urgency, summary
    system_prompt = ""

    # TODO: Make the API call with the system prompt and description
    response = None

    # TODO: Parse the JSON response and return it as a dict
    result = {}

    return result


# Test it
test_claim = (
    "I was rear-ended at a stoplight yesterday. The other driver fled the scene. "
    "My bumper is crushed and my neck hurts badly. I got the license plate."
)
print(json.dumps(classify_claim(test_claim), indent=2))
""",
                    "expected_output": """{
  "claim_type": "collision - hit and run",
  "urgency": "high",
  "summary": "Rear-end collision with fleeing driver. Vehicle damage to bumper and possible neck injury. License plate captured."
}""",
                    "validation": {
                        "must_contain": [
                            "client.messages.create",
                            "system",
                            "json",
                        ],
                        "must_return_keys": ["claim_type", "urgency", "summary"],
                        "test_cases": [
                            {
                                "input": "My windshield cracked from a rock on the highway.",
                                "expected_type": "comprehensive",
                                "expected_urgency": "low",
                            }
                        ],
                    },
                    "demo_data": None,
                },
            ],
        },
        # ── Module 2: Prompt Engineering Patterns ──────────────────────
        {
            "position": 2,
            "title": "Prompt Engineering Patterns",
            "subtitle": "Techniques that make Claude responses reliable and accurate",
            "estimated_time": "30 min",
            "objectives": [
                "Apply few-shot prompting to improve classification accuracy",
                "Use chain-of-thought prompting for complex reasoning",
                "Structure prompts for consistent, parseable outputs",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "The Prompt Engineering Toolkit",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>Three Patterns That Matter</h2>

<h3>1. Few-Shot Prompting</h3>
<p>Give Claude examples of the input/output pattern you want. This is the single
most effective way to improve accuracy for classification and extraction tasks.</p>
<pre><code>Here are examples of claim classifications:

Input: "My car was stolen from the parking lot"
Output: {"type": "theft", "urgency": "high"}

Input: "A tree branch fell on my roof during the storm"
Output: {"type": "weather_damage", "urgency": "medium"}

Now classify this claim:
Input: "{user_claim}"</code></pre>

<h3>2. Chain-of-Thought</h3>
<p>Ask Claude to reason step-by-step before giving a final answer. This dramatically
improves accuracy on complex decisions.</p>
<pre><code>Analyze this claim step by step:
1. What type of incident is described?
2. Are there injuries mentioned?
3. Is there potential fraud risk?
4. What is the appropriate urgency level?

Then provide your final classification as JSON.</code></pre>

<h3>3. System Prompts</h3>
<p>The <code>system</code> parameter sets Claude's role, constraints, and output
format. It's processed before the conversation and has strong influence on behavior.</p>

<h3>When to Use Each</h3>
<ul>
  <li><strong>Few-shot</strong>: When you need consistent output format or domain-specific classifications</li>
  <li><strong>Chain-of-thought</strong>: When the task requires multi-step reasoning</li>
  <li><strong>System prompt</strong>: Always -- it sets the ground rules for every call</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — parsons
                {
                    "position": 2,
                    "title": "Assemble a Production Prompt",
                    "step_type": "exercise",
                    "exercise_type": "parsons",
                    "content": """
<p>Arrange these code blocks in the correct order to build a well-structured
prompt for claim classification. The prompt should follow best practices:
system message first, then few-shot examples, then the user query, then
output format instructions.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "lines": [
                            'system = "You are a claims classifier. Return only valid JSON."',
                            'examples = \'Claim: "Car stolen" → {"type": "theft", "urgency": "high"}\'',
                            'prompt = f"{examples}\\nNow classify: {claim_text}"',
                            'response = client.messages.create(',
                            '    model="claude-sonnet-4-20250514", max_tokens=256,',
                            '    system=system,',
                            '    messages=[{"role": "user", "content": prompt}]',
                            ')',
                        ],
                        "distractors": [
                            '    messages=[{"role": "system", "content": system}]',
                            'response = client.completions.create(',
                        ],
                    },
                },
                # Step 3 — code (run & compare)
                {
                    "position": 3,
                    "title": "Compare Prompt Strategies",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this code to see how different prompting strategies affect Claude's output.
We'll classify the same ambiguous claim three ways: naive, few-shot, and
chain-of-thought. Notice the difference in quality and consistency.</p>
""",
                    "code": """import anthropic
import json

client = anthropic.Anthropic()

claim = (
    "My neighbor's kid threw a baseball through my car window while it was "
    "parked in my driveway. The window is shattered and there are glass "
    "fragments on the seats. I have their name but no police report yet."
)

# Strategy 1: Naive prompt
r1 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": f"Classify this insurance claim: {claim}"}]
)
print("=== NAIVE ===")
print(r1.content[0].text)
print()

# Strategy 2: Few-shot with system prompt
r2 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    system="You are a claims classifier. Return ONLY valid JSON with keys: claim_type, urgency, summary.",
    messages=[{"role": "user", "content": f\"""Example:
Claim: "A deer ran into my car on Route 9."
Classification: {{"claim_type": "collision_animal", "urgency": "medium", "summary": "Animal strike on highway"}}

Now classify:
Claim: "{claim}"
Classification:\"""}]
)
print("=== FEW-SHOT ===")
print(r2.content[0].text)
print()

# Strategy 3: Chain-of-thought
r3 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=512,
    system="You are a senior claims adjuster. Think step-by-step, then provide your final answer as JSON.",
    messages=[{"role": "user", "content": f\"""Analyze this claim step by step:
1. What type of incident?
2. Who is liable?
3. Any documentation gaps?
4. Urgency assessment?

Claim: "{claim}"

After your analysis, provide: {{"claim_type": "...", "urgency": "...", "summary": "...", "next_steps": ["..."]}}\"""}]
)
print("=== CHAIN-OF-THOUGHT ===")
print(r3.content[0].text)
""",
                    "expected_output": """=== NAIVE ===
This appears to be a comprehensive/vandalism claim. The damage was caused by a third party (neighbor's child) to a parked vehicle. The claimant should file a police report and may have a subrogation claim against the neighbor's homeowner's insurance.

=== FEW-SHOT ===
{"claim_type": "vandalism_third_party", "urgency": "medium", "summary": "Third-party property damage to parked vehicle window by neighbor's child, no police report filed"}

=== CHAIN-OF-THOUGHT ===
Let me analyze this step by step:

1. **Type of incident**: Third-party property damage / vandalism. A neighbor's child broke the car window with a baseball while the vehicle was parked.

2. **Liability**: The neighbor (as parent/guardian) is likely liable. This could be claimed under the claimant's comprehensive coverage or pursued through the neighbor's homeowner's insurance.

3. **Documentation gaps**: No police report has been filed yet. This should be done promptly to document the incident.

4. **Urgency**: Medium -- the vehicle is drivable but has a broken window exposing the interior.

{"claim_type": "third_party_property_damage", "urgency": "medium", "summary": "Neighbor's child broke parked car window with baseball, glass on seats", "next_steps": ["File police report", "Get repair estimate", "Contact neighbor's homeowner's insurance", "Document damage with photos"]}""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 4 — code_exercise
                {
                    "position": 4,
                    "title": "Extract Structured Data from Claim Descriptions",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build a function that extracts structured fields from a free-text claim
description. Use few-shot examples and a strict output schema to ensure
consistent results. The function should extract: <code>incident_date</code>,
<code>vehicle_info</code>, <code>damage_description</code>,
<code>injuries</code>, <code>third_parties</code>, and <code>documents_mentioned</code>.</p>
""",
                    "code": """import anthropic
import json

def extract_claim_fields(description: str) -> dict:
    \"\"\"Extract structured fields from a claim description.

    Returns:
        dict with keys: incident_date, vehicle_info, damage_description,
                       injuries, third_parties, documents_mentioned
    \"\"\"
    client = anthropic.Anthropic()

    # TODO: Write a system prompt defining the extraction task and output schema
    system_prompt = ""

    # TODO: Build a user message with at least 2 few-shot examples
    # followed by the actual claim description
    user_message = ""

    # TODO: Make the API call
    response = None

    # TODO: Parse and return the JSON
    return {}


# Test
test = (
    "On March 15, 2025, my 2022 Honda Civic was hit by a red pickup truck "
    "that ran a red light at the intersection of Main St and Oak Ave. "
    "The front bumper and hood are dented, and the airbag deployed. "
    "I have a mild concussion and whiplash. A witness named Sarah Chen "
    "saw everything and gave me her number. I filed a police report (#PR-2025-4471) "
    "and took photos at the scene."
)
print(json.dumps(extract_claim_fields(test), indent=2))
""",
                    "expected_output": """{
  "incident_date": "2025-03-15",
  "vehicle_info": {"year": 2022, "make": "Honda", "model": "Civic"},
  "damage_description": "Front bumper and hood dented, airbag deployed",
  "injuries": ["mild concussion", "whiplash"],
  "third_parties": [{"type": "witness", "name": "Sarah Chen"}, {"type": "at_fault_driver", "vehicle": "red pickup truck"}],
  "documents_mentioned": ["police report #PR-2025-4471", "photos"]
}""",
                    "validation": {
                        "must_contain": [
                            "client.messages.create",
                            "system",
                            "json",
                        ],
                        "must_return_keys": [
                            "incident_date",
                            "vehicle_info",
                            "damage_description",
                            "injuries",
                            "third_parties",
                            "documents_mentioned",
                        ],
                    },
                    "demo_data": None,
                },
            ],
        },
        # ── Module 3: Tool Use & Function Calling ─────────────────────
        {
            "position": 3,
            "title": "Tool Use & Function Calling",
            "subtitle": "Let Claude call your functions to get real-time data",
            "estimated_time": "35 min",
            "objectives": [
                "Understand how Claude's tool use protocol works",
                "Run a tool-use conversation loop",
                "Build a multi-tool agent for claims investigation",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "How Tool Use Works",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>Claude Can Call Your Functions</h2>
<p>Tool use (also called "function calling") lets Claude decide when to call
functions you define. Instead of hallucinating data, Claude can look up real
policy numbers, query databases, or trigger workflows.</p>

<h3>The Tool Use Loop</h3>
<ol>
  <li><strong>Define tools</strong> -- describe your functions with JSON Schema for parameters</li>
  <li><strong>Send the message</strong> -- Claude decides if it needs a tool</li>
  <li><strong>Check stop_reason</strong> -- if <code>"tool_use"</code>, Claude wants to call a function</li>
  <li><strong>Execute the tool</strong> -- run your function with Claude's provided arguments</li>
  <li><strong>Return the result</strong> -- send a <code>tool_result</code> message back</li>
  <li><strong>Repeat</strong> -- Claude may call more tools or give a final response</li>
</ol>

<h3>Tool Definition Structure</h3>
<pre><code>{
    "name": "lookup_policy",
    "description": "Look up an insurance policy by policy number",
    "input_schema": {
        "type": "object",
        "properties": {
            "policy_number": {
                "type": "string",
                "description": "The policy number, e.g. POL-12345"
            }
        },
        "required": ["policy_number"]
    }
}</code></pre>

<h3>Why This Matters</h3>
<p>Without tools, Claude can only work with information in the prompt. With tools,
Claude becomes an <em>agent</em> that can gather information, make decisions, and
take actions -- the foundation of AI-powered claims processing.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — code (run tool-use example)
                {
                    "position": 2,
                    "title": "Run a Tool-Use Conversation",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this complete tool-use loop. Claude will decide to call the
<code>lookup_policy</code> tool, we'll execute it and return the result,
then Claude will give a final answer using the real data.</p>
""",
                    "code": """import anthropic
import json

client = anthropic.Anthropic()

# Our mock database
POLICIES = {
    "POL-78432": {
        "holder": "Maria Santos",
        "vehicle": "2023 Toyota Camry",
        "coverage": "comprehensive",
        "deductible": 500,
        "status": "active",
        "premium_current": True,
    }
}

def lookup_policy(policy_number: str) -> dict:
    if policy_number in POLICIES:
        return POLICIES[policy_number]
    return {"error": f"Policy {policy_number} not found"}

# Define the tool for Claude
tools = [
    {
        "name": "lookup_policy",
        "description": "Look up an insurance policy by its policy number to get coverage details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_number": {
                    "type": "string",
                    "description": "The policy number, e.g. POL-78432"
                }
            },
            "required": ["policy_number"]
        }
    }
]

# Start the conversation
messages = [
    {"role": "user", "content": "What coverage does policy POL-78432 have? Is the premium paid up?"}
]

print("User:", messages[0]["content"])
print()

# First API call -- Claude will request the tool
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=512,
    tools=tools,
    messages=messages,
)

print(f"Claude wants to use tool: {response.content[0].type}")

# Extract tool call
tool_block = next(b for b in response.content if b.type == "tool_use")
print(f"  Tool: {tool_block.name}({json.dumps(tool_block.input)})")

# Execute the tool
tool_result = lookup_policy(**tool_block.input)
print(f"  Result: {json.dumps(tool_result)}")
print()

# Send the result back to Claude
messages.append({"role": "assistant", "content": response.content})
messages.append({
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": tool_block.id,
            "content": json.dumps(tool_result),
        }
    ]
})

# Second API call -- Claude gives final answer
response2 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=512,
    tools=tools,
    messages=messages,
)

print("Claude:", response2.content[0].text)
""",
                    "expected_output": """User: What coverage does policy POL-78432 have? Is the premium paid up?

Claude wants to use tool: tool_use
  Tool: lookup_policy({"policy_number": "POL-78432"})
  Result: {"holder": "Maria Santos", "vehicle": "2023 Toyota Camry", "coverage": "comprehensive", "deductible": 500, "status": "active", "premium_current": true}

Claude: Policy POL-78432 belongs to Maria Santos and covers a 2023 Toyota Camry. Here are the details:

- **Coverage type**: Comprehensive
- **Deductible**: $500
- **Policy status**: Active
- **Premium**: Paid up and current

Everything looks good -- the policy is active with current premiums.""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 — code_exercise (multi-tool agent)
                {
                    "position": 3,
                    "title": "Build a Claims Investigation Agent",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build an agent that has two tools: <code>lookup_policy</code> and
<code>check_fraud_indicators</code>. The agent should handle the full
tool-use loop, potentially calling multiple tools, and return a final
investigation summary.</p>
<p>The <code>check_fraud_indicators</code> tool takes a <code>claim_id</code>
and returns a risk assessment.</p>
""",
                    "code": """import anthropic
import json

client = anthropic.Anthropic()

# Mock databases
POLICIES = {
    "POL-78432": {
        "holder": "Maria Santos",
        "vehicle": "2023 Toyota Camry",
        "coverage": "comprehensive",
        "deductible": 500,
        "status": "active",
    },
    "POL-91205": {
        "holder": "James Reed",
        "vehicle": "2021 BMW X5",
        "coverage": "liability_only",
        "deductible": 1000,
        "status": "lapsed",
    },
}

FRAUD_CHECKS = {
    "CLM-2025-001": {
        "claim_id": "CLM-2025-001",
        "policy_number": "POL-91205",
        "risk_score": 0.82,
        "flags": ["policy_lapsed_before_incident", "high_value_claim", "no_police_report"],
        "recommendation": "flag_for_siu",
    },
}

def lookup_policy(policy_number: str) -> dict:
    return POLICIES.get(policy_number, {"error": "Policy not found"})

def check_fraud_indicators(claim_id: str) -> dict:
    return FRAUD_CHECKS.get(claim_id, {"error": "Claim not found"})


def investigate_claim(query: str) -> str:
    \"\"\"Run the investigation agent. Returns Claude's final summary.\"\"\"

    # TODO: Define both tools with proper input_schema
    tools = []

    # TODO: Create the messages list with the user query
    messages = []

    # TODO: Implement the tool-use loop:
    #   1. Call Claude with tools
    #   2. If stop_reason is "tool_use", execute the requested tool
    #   3. Append the assistant response and tool result to messages
    #   4. Call Claude again
    #   5. Repeat until stop_reason is "end_turn"
    #   6. Return the final text response

    return ""


# Test
result = investigate_claim(
    "Investigate claim CLM-2025-001 filed against policy POL-91205. "
    "Check the policy status and run a fraud check."
)
print(result)
""",
                    "expected_output": """Based on my investigation of claim CLM-2025-001:

**Policy Status (POL-91205)**:
- Holder: James Reed
- Vehicle: 2021 BMW X5
- Coverage: Liability only
- Status: LAPSED

**Fraud Assessment**:
- Risk Score: 0.82/1.00 (HIGH)
- Red Flags:
  1. Policy had lapsed before the incident occurred
  2. High-value claim amount
  3. No police report was filed

**Recommendation**: This claim should be immediately flagged for the Special Investigations Unit (SIU). The combination of a lapsed policy and high fraud risk score warrants a thorough in-person investigation before any payout is considered.""",
                    "validation": {
                        "must_contain": [
                            "tools",
                            "tool_use",
                            "tool_result",
                            "while",
                        ],
                        "must_define_tools": ["lookup_policy", "check_fraud_indicators"],
                    },
                    "demo_data": None,
                },
                # Step 4 — system_build (capstone)
                {
                    "position": 4,
                    "title": "Deploy: Claude-Powered API Service",
                    "step_type": "exercise",
                    "exercise_type": "system_build",
                    "content": """
<h2>Mission: Deploy a Production Claude API Service</h2>
<p>You have made API calls, engineered prompts, and built a multi-tool agent.
Now you ship a <strong>production-grade API service</strong> that wraps Claude
with caching, rate limiting, and structured output -- the kind of service your
team would put behind their internal tools.</p>

<h3>What You Are Building</h3>
<p>A <strong>FastAPI service</strong> that exposes Claude-powered endpoints for
insurance claim processing. The service adds the production concerns that
a raw API call lacks: response caching, per-client rate limiting, input
validation, structured JSON output, and observability.</p>

<h3>Requirements</h3>
<ul>
  <li><strong>POST /classify</strong> -- accepts <code>{"description": "...", "priority": true}</code>,
      returns <code>{"claim_type": "...", "urgency": "...", "summary": "...", "processing_time": 0.8}</code></li>
  <li><strong>POST /extract</strong> -- accepts <code>{"description": "..."}</code>, returns structured
      fields: <code>incident_date</code>, <code>vehicle_info</code>, <code>damage_description</code>,
      <code>injuries</code>, <code>third_parties</code>, <code>documents_mentioned</code></li>
  <li><strong>POST /investigate</strong> -- accepts <code>{"query": "...", "tools": ["lookup_policy", "check_fraud"]}</code>,
      runs the tool-use agent loop, returns the investigation summary</li>
  <li><strong>GET /health</strong> -- returns <code>{"status": "ok", "cache_size": N, "model": "..."}</code></li>
  <li><strong>Response caching</strong> -- identical inputs return cached results (TTL 5 min)</li>
  <li><strong>Rate limiting</strong> -- max 20 requests/minute per API key, return 429 when exceeded</li>
  <li><strong>Structured output</strong> -- all Claude responses parsed to validated JSON; malformed responses trigger one retry</li>
  <li>Graceful error handling -- Claude API errors return 503, invalid inputs return 422</li>
</ul>

<h3>Phases</h3>
<ol>
  <li><strong>Local Build</strong> -- implement the FastAPI app with all four endpoints, test locally with curl or pytest</li>
  <li><strong>Containerize</strong> -- write a Dockerfile, build and run the image, verify all endpoints in Docker</li>
  <li><strong>Deploy</strong> -- deploy to AWS Lambda (via Mangum) or Railway/Fly.io, confirm the public URL responds</li>
  <li><strong>Load Test</strong> -- use <code>locust</code> or <code>hey</code> to verify rate limiting works and the service handles sustained traffic gracefully</li>
</ol>

<h3>Evaluation</h3>
<p>Mark each phase complete as you finish it. Check off the production checklist
items below. When all phases are done, paste your deployed endpoint URL --
we will validate it with a live POST to <code>/classify</code>.</p>
""",
                    "code": """\"\"\"Claude-Powered Claims API -- Starter Code

A production wrapper around the Claude API with caching, rate limiting,
and structured output. Deploy to AWS Lambda or Railway.
\"\"\"

import os
import time
import json
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import anthropic


# ── Configuration ────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CACHE_TTL_SECONDS = 300  # 5 minutes
RATE_LIMIT_PER_MINUTE = 20


# ── Clients ──────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ── In-memory cache & rate limiter ───────────────────────────
_cache: dict[str, dict] = {}  # key -> {"response": ..., "expires": datetime}
_rate_counts: dict[str, list[datetime]] = defaultdict(list)


def cache_key(prefix: str, payload: str) -> str:
    return f"{prefix}:{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


def get_cached(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and entry["expires"] > datetime.utcnow():
        return entry["response"]
    if entry:
        del _cache[key]
    return None


def set_cached(key: str, response: dict):
    _cache[key] = {
        "response": response,
        "expires": datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS),
    }


def check_rate_limit(client_id: str):
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=1)
    # Prune old entries
    _rate_counts[client_id] = [
        t for t in _rate_counts[client_id] if t > window_start
    ]
    if len(_rate_counts[client_id]) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_PER_MINUTE} requests/minute.",
        )
    _rate_counts[client_id].append(now)


# ── Schemas ──────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    description: str
    priority: bool = False

class ClassifyResponse(BaseModel):
    claim_type: str
    urgency: str
    summary: str
    processing_time: float
    cached: bool = False

class ExtractRequest(BaseModel):
    description: str

class InvestigateRequest(BaseModel):
    query: str
    tools: list[str] = Field(default_factory=lambda: ["lookup_policy", "check_fraud"])

class HealthResponse(BaseModel):
    status: str
    cache_size: int
    model: str


# ── Claude helpers ───────────────────────────────────────────
def call_claude_json(system_prompt: str, user_message: str, max_retries: int = 1) -> dict:
    \"\"\"Call Claude and parse the response as JSON. Retry once on parse failure.\"\"\"
    for attempt in range(max_retries + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt < max_retries:
                continue
            raise HTTPException(
                status_code=503,
                detail="Claude returned non-JSON response after retry.",
            )


# TODO: Define mock tool functions for the /investigate endpoint
# lookup_policy(policy_number) -> dict
# check_fraud(claim_id) -> dict
MOCK_POLICIES = {
    "POL-78432": {
        "holder": "Maria Santos", "vehicle": "2023 Toyota Camry",
        "coverage": "comprehensive", "deductible": 500, "status": "active",
    },
    "POL-91205": {
        "holder": "James Reed", "vehicle": "2021 BMW X5",
        "coverage": "liability_only", "deductible": 1000, "status": "lapsed",
    },
}

MOCK_FRAUD = {
    "CLM-2025-001": {
        "risk_score": 0.82,
        "flags": ["policy_lapsed_before_incident", "high_value_claim"],
        "recommendation": "flag_for_siu",
    },
}

def lookup_policy(policy_number: str) -> dict:
    return MOCK_POLICIES.get(policy_number, {"error": "Policy not found"})

def check_fraud(claim_id: str) -> dict:
    return MOCK_FRAUD.get(claim_id, {"error": "Claim not found", "risk_score": 0.0})


# ── App ──────────────────────────────────────────────────────
app = FastAPI(title="Claude Claims Processing API", version="1.0.0")


def get_client_id(request: Request) -> str:
    \"\"\"Extract client ID from X-API-Key header or fall back to IP.\"\"\"
    return request.headers.get("x-api-key", request.client.host)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        cache_size=len(_cache),
        model=MODEL,
    )


@app.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest, request: Request):
    client_id = get_client_id(request)
    check_rate_limit(client_id)

    # Check cache
    ck = cache_key("classify", req.description)
    cached = get_cached(ck)
    if cached:
        return ClassifyResponse(**cached, cached=True)

    start = time.perf_counter()

    system_prompt = (
        "You are an insurance claims classifier. Return ONLY valid JSON with "
        "exactly three keys: claim_type (string), urgency (low|medium|high), "
        "summary (one sentence).\\n"
        "Examples:\\n"
        'Input: "My car was stolen" -> {"claim_type": "theft", "urgency": "high", '
        '"summary": "Vehicle theft reported"}\\n'
        'Input: "Small scratch on bumper" -> {"claim_type": "collision_minor", '
        '"urgency": "low", "summary": "Minor cosmetic damage to bumper"}'
    )

    # TODO: Call Claude with the system prompt and claim description
    result = call_claude_json(system_prompt, req.description)

    elapsed = round(time.perf_counter() - start, 3)
    response_data = {
        "claim_type": result["claim_type"],
        "urgency": result["urgency"],
        "summary": result["summary"],
        "processing_time": elapsed,
    }

    set_cached(ck, response_data)
    return ClassifyResponse(**response_data)


@app.post("/extract")
async def extract(req: ExtractRequest, request: Request):
    client_id = get_client_id(request)
    check_rate_limit(client_id)

    ck = cache_key("extract", req.description)
    cached = get_cached(ck)
    if cached:
        return {**cached, "cached": True}

    system_prompt = (
        "You are an insurance claim data extractor. Extract structured fields "
        "from the claim description. Return ONLY valid JSON with these keys: "
        "incident_date (ISO format or null), vehicle_info (object with year, "
        "make, model or null), damage_description (string), injuries (list of "
        "strings), third_parties (list of objects), documents_mentioned (list "
        "of strings)."
    )

    # TODO: Call Claude and return structured extraction
    result = call_claude_json(system_prompt, req.description)
    set_cached(ck, result)
    return result


@app.post("/investigate")
async def investigate(req: InvestigateRequest, request: Request):
    client_id = get_client_id(request)
    check_rate_limit(client_id)

    # TODO: Implement the tool-use agent loop
    # 1. Define tool schemas based on req.tools
    # 2. Send initial message to Claude with tools
    # 3. Loop: if stop_reason == "tool_use", execute tool, return result
    # 4. When stop_reason == "end_turn", return the final text

    tool_defs = []
    tool_fns = {"lookup_policy": lookup_policy, "check_fraud": check_fraud}

    if "lookup_policy" in req.tools:
        tool_defs.append({
            "name": "lookup_policy",
            "description": "Look up an insurance policy by policy number.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "e.g. POL-78432"}
                },
                "required": ["policy_number"],
            },
        })
    if "check_fraud" in req.tools:
        tool_defs.append({
            "name": "check_fraud",
            "description": "Check fraud indicators for a claim.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "e.g. CLM-2025-001"}
                },
                "required": ["claim_id"],
            },
        })

    messages = [{"role": "user", "content": req.query}]

    for _ in range(10):  # max iterations safety
        response = client.messages.create(
            model=MODEL, max_tokens=1024, tools=tool_defs, messages=messages,
        )

        if response.stop_reason == "end_turn":
            text_block = next((b for b in response.content if hasattr(b, "text")), None)
            return {"summary": text_block.text if text_block else "", "tool_calls": len(messages) // 2}

        # Handle tool use
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = tool_fns.get(block.name)
                if fn:
                    result = fn(**block.input)
                else:
                    result = {"error": f"Unknown tool: {block.name}"}
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
        messages.append({"role": "user", "content": tool_results})

    raise HTTPException(status_code=503, detail="Agent loop exceeded max iterations")


# ── Lambda adapter (for AWS deployment) ─────────────────────
# Uncomment when deploying to Lambda:
# from mangum import Mangum
# handler = Mangum(app, lifespan="off")
""",
                    "expected_output": None,
                    "deployment_config": {
                        "platform": "aws",
                        "service": "lambda",
                        "dockerfile": """FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["app.handler"]""",
                        "requirements": (
                            "fastapi>=0.115.0\n"
                            "mangum>=0.19.0\n"
                            "anthropic>=0.39.0\n"
                            "pydantic>=2.0.0\n"
                        ),
                    },
                    "validation": {
                        "endpoint_check": {
                            "method": "POST",
                            "path": "/classify",
                            "body": {
                                "description": "Rear-ended at a stoplight, bumper damage and neck pain",
                                "priority": True,
                            },
                            "expected_status": 200,
                            "expected_fields": ["claim_type", "urgency", "summary", "processing_time"],
                        },
                        "phases": [
                            {"name": "Local Build", "description": "Implement and test all four endpoints locally"},
                            {"name": "Containerize", "description": "Create Dockerfile, build and run the container"},
                            {"name": "Deploy", "description": "Deploy to AWS Lambda or Railway with a public URL"},
                            {"name": "Load Test", "description": "Verify rate limiting and sustained traffic handling"},
                        ],
                    },
                    "demo_data": {
                        "phases": [
                            {"id": 1, "title": "Local Build", "description": "Implement the FastAPI app and verify /classify, /extract, /investigate, and /health work locally"},
                            {"id": 2, "title": "Containerize", "description": "Write a Dockerfile, build the image, and run the container with environment variables"},
                            {"id": 3, "title": "Deploy", "description": "Deploy to AWS Lambda with Mangum or to Railway/Fly.io with a public URL"},
                            {"id": 4, "title": "Load Test", "description": "Verify rate limiting returns 429 and service handles sustained traffic"},
                        ],
                        "checklist": [
                            {"id": "classify_endpoint", "label": "POST /classify returns claim_type, urgency, summary, and processing_time"},
                            {"id": "extract_endpoint", "label": "POST /extract returns all six structured fields from claim descriptions"},
                            {"id": "investigate_endpoint", "label": "POST /investigate runs the tool-use loop and returns an investigation summary"},
                            {"id": "health_endpoint", "label": "GET /health returns status, cache_size, and model"},
                            {"id": "caching", "label": "Identical requests return cached responses within TTL"},
                            {"id": "rate_limiting", "label": "Exceeding 20 req/min returns HTTP 429"},
                            {"id": "structured_output", "label": "Malformed Claude responses trigger a retry and never leak to the client"},
                            {"id": "error_handling", "label": "Claude API errors return 503, invalid inputs return 422"},
                            {"id": "dockerfile", "label": "Dockerfile builds and container runs successfully"},
                            {"id": "deployed", "label": "Service is live at a public URL"},
                        ],
                    },
                },
            ],
        },
    ],
}
