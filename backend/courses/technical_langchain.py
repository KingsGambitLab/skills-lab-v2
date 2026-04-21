"""
Technical Skill Course: LangChain & AI Application Patterns
Covers chains, agents, memory, RAG, and building production AI apps.
"""

COURSE = {
    "id": "langchain-patterns",
    "title": "LangChain & AI Application Patterns",
    "subtitle": "Build production AI apps with chains, RAG, and agents",
    "icon": "🔗",
    "course_type": "technical",
    "level": "Intermediate",
    "tags": ["langchain", "rag", "agents", "chains", "memory", "python", "ai"],
    "estimated_time": "~2 hours",
    "description": (
        "Master LangChain's core abstractions for building AI-powered applications. "
        "You'll compose chains with prompt templates and output parsers, implement "
        "retrieval-augmented generation for grounded answers, and build autonomous "
        "agents with memory -- all with hands-on exercises using insurance industry examples."
    ),
    "modules": [
        # ── Module 1: Chains & Composition ────────────────────────────
        {
            "position": 1,
            "title": "Chains & Composition",
            "subtitle": "Compose LLM calls into reliable, testable pipelines",
            "estimated_time": "30 min",
            "objectives": [
                "Understand prompt templates and why they beat raw f-strings",
                "Build sequential chains that pipe output between steps",
                "Parse LLM output into structured data with output parsers",
            ],
            "steps": [
                # Step 1 -- concept
                {
                    "position": 1,
                    "title": "What Are Chains?",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.chain-demo { background: #151b2e; border: 1px solid #2a3352; border-radius: 12px; padding: 24px; margin: 16px 0; font-family: 'Inter', system-ui, sans-serif; }
.chain-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.chain-demo .hook { background: linear-gradient(135deg, #1e2538, #252e45); border-left: 4px solid #2dd4bf; padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }
.chain-demo .hook p { color: #e8ecf4; margin: 4px 0; line-height: 1.6; }
.chain-demo .hook strong { color: #2dd4bf; }
.chain-demo .workspace { display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap; }
.chain-demo .toolbox { background: #1e2538; border: 1px solid #2a3352; border-radius: 8px; padding: 16px; min-width: 180px; flex: 0 0 auto; }
.chain-demo .toolbox h3 { color: #8b95b0; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-top: 0; }
.chain-demo .component { background: #151b2e; border: 2px solid #2a3352; border-radius: 8px; padding: 10px 14px; margin: 8px 0; cursor: grab; user-select: none; transition: all 0.2s; display: flex; align-items: center; gap: 8px; font-size: 0.88em; }
.chain-demo .component:hover { border-color: #4a7cff; transform: translateX(4px); }
.chain-demo .component.used { opacity: 0.35; cursor: default; pointer-events: none; }
.chain-demo .component .icon { font-size: 1.3em; }
.chain-demo .component .name { color: #e8ecf4; font-weight: 600; }
.chain-demo .component .desc { color: #8b95b0; font-size: 0.8em; }
.chain-demo .pipeline { flex: 1; min-width: 280px; }
.chain-demo .pipeline h3 { color: #8b95b0; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-top: 0; }
.chain-demo .drop-zone { min-height: 52px; border: 2px dashed #2a3352; border-radius: 8px; margin: 6px 0; padding: 12px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; position: relative; }
.chain-demo .drop-zone.active { border-color: #4a7cff; background: rgba(74,124,255,0.05); }
.chain-demo .drop-zone.filled { border-style: solid; border-color: #2dd4bf; background: rgba(45,212,191,0.06); }
.chain-demo .drop-zone .placeholder { color: #3a4560; font-size: 0.82em; }
.chain-demo .drop-zone .placed { color: #e8ecf4; font-weight: 600; display: flex; align-items: center; gap: 8px; width: 100%; }
.chain-demo .drop-zone .remove-btn { margin-left: auto; background: none; border: 1px solid #f97066; color: #f97066; border-radius: 4px; padding: 2px 8px; cursor: pointer; font-size: 0.75em; }
.chain-demo .pipe-arrow { text-align: center; color: #4a7cff; font-size: 1.4em; line-height: 1; }
.chain-demo .btn-run { background: #2dd4bf; color: #151b2e; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-weight: 700; margin-top: 12px; width: 100%; font-size: 0.95em; transition: background 0.2s; }
.chain-demo .btn-run:hover { background: #1dc4af; }
.chain-demo .btn-run:disabled { background: #2a3352; color: #8b95b0; cursor: default; }
.chain-demo .run-output { background: #0d1117; border: 1px solid #2a3352; border-radius: 8px; padding: 14px; margin-top: 14px; font-family: 'Fira Code', monospace; font-size: 0.82em; white-space: pre-wrap; display: none; }
.chain-demo .step-trace { padding: 6px 0; border-bottom: 1px solid #1e2538; }
.chain-demo .step-trace .label { color: #4a7cff; }
.chain-demo .step-trace .arrow { color: #2dd4bf; }
.chain-demo .step-trace .data { color: #e8ecf4; }
.chain-demo .success-msg { background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.3); color: #2dd4bf; padding: 12px 16px; border-radius: 8px; margin-top: 12px; font-size: 0.88em; display: none; }
</style>

<div class="chain-demo">
  <h2>Build a Chain in 60 Seconds</h2>
  <div class="hook">
    <p><strong>The problem:</strong> Your claims processing code is a 200-line mess of string concatenation, API calls, and JSON parsing -- impossible to test, debug, or reuse.</p>
    <p><strong>The fix:</strong> LangChain breaks it into snap-together components. Drag the 3 pieces below into the pipeline to build a working chain.</p>
  </div>

  <div class="workspace">
    <div class="toolbox">
      <h3>Components</h3>
      <div class="component" data-id="prompt" onclick="placeComponent(this)" draggable="false">
        <span class="icon">📝</span>
        <div><div class="name">PromptTemplate</div><div class="desc">Fills in variables</div></div>
      </div>
      <div class="component" data-id="llm" onclick="placeComponent(this)" draggable="false">
        <span class="icon">🧠</span>
        <div><div class="name">ChatModel (LLM)</div><div class="desc">Processes the prompt</div></div>
      </div>
      <div class="component" data-id="parser" onclick="placeComponent(this)" draggable="false">
        <span class="icon">📦</span>
        <div><div class="name">OutputParser</div><div class="desc">Extracts structured data</div></div>
      </div>
    </div>

    <div class="pipeline">
      <h3>Your Chain: prompt | llm | parser</h3>
      <div class="drop-zone" data-slot="0" onclick="focusSlot(this)"><span class="placeholder">Click a component to place it here (Step 1)</span></div>
      <div class="pipe-arrow">|</div>
      <div class="drop-zone" data-slot="1" onclick="focusSlot(this)"><span class="placeholder">Step 2</span></div>
      <div class="pipe-arrow">|</div>
      <div class="drop-zone" data-slot="2" onclick="focusSlot(this)"><span class="placeholder">Step 3</span></div>

      <button class="btn-run" id="chainRunBtn" onclick="runChain()" disabled>Run Chain on: "Rear-ended at stoplight, neck hurts"</button>
      <div class="run-output" id="chainOutput"></div>
      <div class="success-msg" id="chainSuccess"></div>
    </div>
  </div>
</div>

<script>
(function(){
  const correctOrder = ["prompt", "llm", "parser"];
  const slots = [null, null, null];
  let activeSlot = 0;
  const icons = {prompt:"📝", llm:"🧠", parser:"📦"};
  const names = {prompt:"PromptTemplate", llm:"ChatModel (LLM)", parser:"OutputParser"};

  function updateUI() {
    document.querySelectorAll('.chain-demo .drop-zone').forEach((dz, i) => {
      if(slots[i]) {
        dz.classList.add('filled');
        dz.innerHTML = '<span class="placed"><span>'+icons[slots[i]]+'</span> '+names[slots[i]]+' <button class="remove-btn" onclick="event.stopPropagation();removeFromSlot('+i+')">remove</button></span>';
      } else {
        dz.classList.remove('filled');
        dz.innerHTML = '<span class="placeholder">'+(i===activeSlot?'Click a component...':'Step '+(i+1))+'</span>';
      }
      dz.classList.toggle('active', i === activeSlot && !slots[i]);
    });
    document.querySelectorAll('.chain-demo .component').forEach(c => {
      c.classList.toggle('used', slots.includes(c.dataset.id));
    });
    const allFilled = slots.every(s => s !== null);
    document.getElementById('chainRunBtn').disabled = !allFilled;
  }

  window.focusSlot = function(el) {
    activeSlot = parseInt(el.dataset.slot);
    updateUI();
  };

  window.placeComponent = function(el) {
    const id = el.dataset.id;
    if(slots.includes(id)) return;
    if(slots[activeSlot] !== null) {
      for(let i=0;i<3;i++){if(slots[i]===null){activeSlot=i;break;}}
    }
    if(slots[activeSlot] !== null) return;
    slots[activeSlot] = id;
    for(let i=0;i<3;i++){if(slots[i]===null){activeSlot=i;break;}}
    updateUI();
  };

  window.removeFromSlot = function(i) {
    slots[i] = null;
    activeSlot = i;
    document.getElementById('chainOutput').style.display = 'none';
    document.getElementById('chainSuccess').style.display = 'none';
    updateUI();
  };

  window.runChain = function() {
    const isCorrect = slots[0]===correctOrder[0] && slots[1]===correctOrder[1] && slots[2]===correctOrder[2];
    const out = document.getElementById('chainOutput');
    const suc = document.getElementById('chainSuccess');
    out.style.display = 'block';

    if(isCorrect) {
      out.innerHTML = '<div class="step-trace"><span class="label">PromptTemplate</span> <span class="arrow">-></span> <span class="data">"Classify this claim: Rear-ended at stoplight, neck hurts. Return JSON."</span></div>'
        + '<div class="step-trace"><span class="label">ChatModel</span> <span class="arrow">-></span> <span class="data">\'{"claim_type":"auto_collision","urgency":"high","summary":"Rear-end collision with injury"}\'</span></div>'
        + '<div class="step-trace"><span class="label">OutputParser</span> <span class="arrow">-></span> <span class="data">{"claim_type": "auto_collision", "urgency": "high", "summary": "Rear-end collision with injury"}</span></div>';
      suc.style.display = 'block';
      suc.innerHTML = '<strong>Chain complete.</strong> Each component did one job: the template filled in variables, the LLM processed the prompt, and the parser extracted structured JSON. That one-liner -- <code>prompt | llm | parser</code> -- replaces 50+ lines of brittle code.';
    } else {
      out.innerHTML = '<span style="color:#f97066;">Error: Chain failed.</span><br><br>The correct order is: <strong>PromptTemplate | ChatModel | OutputParser</strong><br><br>Why? Data flows left to right:<br>1. PromptTemplate fills in the claim text<br>2. ChatModel (LLM) processes the completed prompt<br>3. OutputParser converts raw text to structured JSON<br><br>Try rearranging the components!';
      suc.style.display = 'none';
    }
  };

  updateUI();
})();
</script>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- code (prompt templates demo)
                {
                    "position": 2,
                    "title": "Prompt Templates & Chain Basics",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this example to see how prompt templates and chain invocation work.
We simulate LangChain's <code>PromptTemplate</code> and chain pattern.
Notice how templates make prompts reusable and type-safe.</p>
""",
                    "code": """# Simulating LangChain's PromptTemplate + Chain pattern
# In production: from langchain.prompts import PromptTemplate

class PromptTemplate:
    \"\"\"Mirrors LangChain's PromptTemplate behavior.\"\"\"
    def __init__(self, template: str, input_variables: list):
        self.template = template
        self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        result = self.template
        for var in self.input_variables:
            result = result.replace("{" + var + "}", str(kwargs[var]))
        return result


# Define a reusable prompt for claim classification
classify_prompt = PromptTemplate(
    template=(
        "You are an insurance claims classifier.\\n\\n"
        "Classify this claim into one of: auto, property, health, life.\\n"
        "Also rate urgency as: low, medium, high.\\n\\n"
        "Claim: {claim_text}\\n\\n"
        "Respond as JSON: {{\\\"claim_type\\\": ..., \\\"urgency\\\": ...}}"
    ),
    input_variables=["claim_text"]
)

# Fill in the template with actual data
claim = "My car was rear-ended at a red light. Bumper damage and neck pain."
formatted = classify_prompt.format(claim_text=claim)

print("=== Formatted Prompt ===")
print(formatted)
print()

# Simulate what the LLM would return
llm_response = '{"claim_type": "auto", "urgency": "high"}'
print("=== LLM Response ===")
print(llm_response)
print()

# Parse the response (output parser step)
import json
result = json.loads(llm_response)
print("=== Parsed Output ===")
print(f"Type: {result['claim_type']}")
print(f"Urgency: {result['urgency']}")
""",
                    "expected_output": """=== Formatted Prompt ===
You are an insurance claims classifier.

Classify this claim into one of: auto, property, health, life.
Also rate urgency as: low, medium, high.

Claim: My car was rear-ended at a red light. Bumper damage and neck pain.

Respond as JSON: {"claim_type": ..., "urgency": ...}

=== LLM Response ===
{"claim_type": "auto", "urgency": "high"}

=== Parsed Output ===
Type: auto
Urgency: high""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 -- fill_in_blank (sequential chain)
                {
                    "position": 3,
                    "title": "Build a Sequential Chain",
                    "step_type": "exercise",
                    "exercise_type": "fill_in_blank",
                    "content": """
<p>Fill in the blanks to create a two-step sequential chain. Step 1 classifies
a claim, and Step 2 uses that classification to generate an action plan.
This mirrors LangChain's <code>SequentialChain</code> pattern.</p>
""",
                    "code": """import json

# Step 1: Classification chain
def classify_chain(claim_text: str) -> dict:
    # In production: prompt | llm | JsonOutputParser
    prompt = f"Classify this claim: {claim_text}"
    print(f"Step 1 prompt: {prompt[:50]}...")
    return {"claim_type": "auto", "urgency": "high"}

# Step 2: Action plan chain -- uses output from Step 1
def action_plan_chain(classification: dict) -> str:
    claim_type = classification["____"]
    urgency = classification["____"]
    prompt = f"Generate action plan for {claim_type} claim with {urgency} urgency"
    print(f"Step 2 prompt: {prompt}")
    return f"1. Assign adjuster\\n2. Contact policyholder\\n3. Schedule inspection"

# Sequential chain: pipe Step 1 output into Step 2
def claims_pipeline(claim_text: str) -> str:
    step1_result = ____(claim_text)
    step2_result = ____(step1_result)
    return step2_result

# Run the pipeline
result = claims_pipeline("Water pipe burst, flooded the basement, ruined furniture.")
print(f"\\nFinal action plan:\\n{result}")
""",
                    "expected_output": None,
                    "validation": {
                        "blanks": [
                            {
                                "index": 0,
                                "answer": "claim_type",
                                "hint": "Access the claim_type key from the classification dict",
                            },
                            {
                                "index": 1,
                                "answer": "urgency",
                                "hint": "Access the urgency key from the classification dict",
                            },
                            {
                                "index": 2,
                                "answer": "classify_chain",
                                "hint": "Call the first chain function to classify the claim",
                            },
                            {
                                "index": 3,
                                "answer": "action_plan_chain",
                                "hint": "Call the second chain function with the classification result",
                            },
                        ]
                    },
                    "demo_data": None,
                },
                # Step 4 -- code_exercise (output parser chain)
                {
                    "position": 4,
                    "title": "Build an Output Parser Chain",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build a chain that parses unstructured claim notes into a structured
<code>ClaimReport</code>. Implement the <code>parse_output</code> function
that extracts fields from the LLM's raw text response. This mirrors
LangChain's <code>PydanticOutputParser</code> pattern.</p>
""",
                    "code": """import json

# Simulating LangChain's structured output parsing pattern
CLAIM_SCHEMA = {
    "policyholder": "string",
    "incident_date": "string",
    "damage_type": "string",
    "estimated_cost": "number",
    "witnesses": "list[string]"
}

def build_extraction_prompt(raw_notes: str) -> str:
    schema_str = json.dumps(CLAIM_SCHEMA, indent=2)
    return (
        f"Extract structured data from these claim notes.\\n"
        f"Return JSON matching this schema:\\n{schema_str}\\n\\n"
        f"Notes: {raw_notes}"
    )

def simulate_llm(prompt: str) -> str:
    \"\"\"Simulates the LLM returning a JSON response.\"\"\"
    return json.dumps({
        "policyholder": "David Park",
        "incident_date": "2025-03-20",
        "damage_type": "water damage",
        "estimated_cost": 15000,
        "witnesses": ["neighbor Jim Torres", "plumber Ana Ruiz"]
    })

def parse_output(raw_response: str) -> dict:
    \"\"\"Parse the LLM's raw text into a validated dict.

    Should:
    1. Parse the JSON string
    2. Validate all required keys are present
    3. Raise ValueError if any key from CLAIM_SCHEMA is missing

    Returns:
        dict with all schema fields
    \"\"\"
    # TODO: Parse the JSON from raw_response
    parsed = {}

    # TODO: Validate that every key in CLAIM_SCHEMA exists in parsed
    # Raise ValueError with a message listing missing keys if any are absent

    return parsed


def extraction_chain(raw_notes: str) -> dict:
    \"\"\"Full chain: prompt -> LLM -> parser.\"\"\"
    prompt = build_extraction_prompt(raw_notes)
    raw_response = simulate_llm(prompt)
    return parse_output(raw_response)


# Test it
notes = (
    "David Park called about his basement flooding on March 20, 2025. "
    "A pipe burst in the wall. Damage to flooring, drywall, and furniture. "
    "Estimated repairs around $15,000. His neighbor Jim Torres and the "
    "plumber Ana Ruiz can confirm the damage."
)
result = extraction_chain(notes)
print(json.dumps(result, indent=2))
""",
                    "expected_output": """{
  "policyholder": "David Park",
  "incident_date": "2025-03-20",
  "damage_type": "water damage",
  "estimated_cost": 15000,
  "witnesses": ["neighbor Jim Torres", "plumber Ana Ruiz"]
}""",
                    "validation": {
                        "must_contain": [
                            "json.loads",
                            "CLAIM_SCHEMA",
                            "ValueError",
                        ],
                        "hint": "Use json.loads() to parse the response, then check each key from CLAIM_SCHEMA is present in the result",
                    },
                    "demo_data": None,
                },
                # Step 5 -- parsons (LCEL pipe composition)
                {
                    "position": 5,
                    "title": "Arrange an LCEL Chain",
                    "step_type": "exercise",
                    "exercise_type": "parsons",
                    "content": """
<p>Arrange these lines to build a LangChain Expression Language (LCEL) chain
that classifies a claim and returns structured output. The chain should
follow the pattern: imports, template, model, parser, compose, invoke.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "lines": [
                            "from langchain.prompts import ChatPromptTemplate",
                            "from langchain.chat_models import ChatAnthropic",
                            "from langchain.output_parsers import JsonOutputParser",
                            "prompt = ChatPromptTemplate.from_template(\"Classify: {claim}\")",
                            "model = ChatAnthropic(model=\"claude-sonnet-4-20250514\")",
                            "parser = JsonOutputParser()",
                            "chain = prompt | model | parser",
                            "result = chain.invoke({\"claim\": claim_text})",
                        ],
                        "distractors": [
                            "chain = parser | model | prompt",
                            "result = chain.run(claim_text)",
                        ],
                    },
                },
            ],
        },
        # ── Module 2: RAG -- Retrieval Augmented Generation ──────────
        {
            "position": 2,
            "title": "RAG -- Retrieval Augmented Generation",
            "subtitle": "Ground LLM answers in your own documents",
            "estimated_time": "35 min",
            "objectives": [
                "Understand the RAG architecture and why it reduces hallucination",
                "Split documents and create embeddings for retrieval",
                "Build a complete question-answering chain over insurance documents",
            ],
            "steps": [
                # Step 1 -- concept
                {
                    "position": 1,
                    "title": "Why RAG?",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>The Problem RAG Solves</h2>
<p>LLMs are trained on general data -- they don't know your company's policies,
claims history, or internal procedures. <strong>RAG</strong> fixes this by
retrieving relevant documents and injecting them into the prompt at query time.</p>

<h3>The RAG Pipeline</h3>
<ol>
  <li><strong>Load</strong> -- ingest documents (PDFs, databases, web pages)</li>
  <li><strong>Split</strong> -- chunk documents into manageable pieces (500-1000 tokens)</li>
  <li><strong>Embed</strong> -- convert each chunk into a vector (numerical representation)</li>
  <li><strong>Store</strong> -- save vectors in a vector database (FAISS, Chroma, Pinecone)</li>
  <li><strong>Retrieve</strong> -- find the most relevant chunks for a user's question</li>
  <li><strong>Generate</strong> -- pass retrieved chunks + question to the LLM</li>
</ol>

<h3>RAG vs. Fine-Tuning</h3>
<table>
  <tr><th>Aspect</th><th>RAG</th><th>Fine-Tuning</th></tr>
  <tr><td>Data freshness</td><td>Always up-to-date</td><td>Frozen at training time</td></tr>
  <tr><td>Cost</td><td>Low (no training required)</td><td>High (GPU hours)</td></tr>
  <tr><td>Transparency</td><td>Can cite source documents</td><td>Black box</td></tr>
  <tr><td>Best for</td><td>Factual Q&A, search</td><td>Style, tone, specialized tasks</td></tr>
</table>

<h3>Insurance Use Cases</h3>
<ul>
  <li>Policy Q&A: "What does my comprehensive coverage exclude?"</li>
  <li>Claims guidance: "What documents do I need for a water damage claim?"</li>
  <li>Compliance search: "What are the state regulations for claim processing timelines?"</li>
</ul>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- code (document splitting & embedding)
                {
                    "position": 2,
                    "title": "Split Documents & Create Embeddings",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this example to see how document splitting and embedding work.
We simulate LangChain's <code>RecursiveCharacterTextSplitter</code> and
an embedding model to show the full indexing pipeline.</p>
""",
                    "code": """import hashlib

# --- Simulating LangChain's document loading & splitting ---

# Sample insurance policy document
POLICY_DOC = \"\"\"
SECTION 1: COMPREHENSIVE COVERAGE
Comprehensive coverage protects against non-collision damage including theft,
vandalism, natural disasters, falling objects, and animal strikes. The
deductible is $500 per incident. Glass damage has a separate $100 deductible.

SECTION 2: COLLISION COVERAGE
Collision coverage pays for damage when your vehicle hits another object,
regardless of fault. This includes other vehicles, guardrails, trees, and
poles. The deductible is $1,000 per incident.

SECTION 3: LIABILITY COVERAGE
Liability coverage pays for injuries and property damage you cause to others.
The minimum coverage is $50,000 per person / $100,000 per accident for bodily
injury, and $25,000 for property damage. This does not cover your own injuries.

SECTION 4: CLAIMS PROCESS
To file a claim: 1) Report the incident within 72 hours. 2) Provide photos
and a police report if applicable. 3) An adjuster will be assigned within
2 business days. 4) Repairs must use an approved shop for direct billing.
\"\"\"

def text_splitter(text: str, chunk_size: int = 200, overlap: int = 30) -> list:
    \"\"\"Simulates RecursiveCharacterTextSplitter.\"\"\"
    chunks = []
    paragraphs = [p.strip() for p in text.strip().split("\\n\\n") if p.strip()]
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i:i + chunk_size])
    return chunks

def fake_embed(text: str) -> list:
    \"\"\"Simulates an embedding model -- returns a 4-dim 'vector'.\"\"\"
    h = hashlib.md5(text.encode()).hexdigest()
    return [int(h[i:i+8], 16) / 0xFFFFFFFF for i in range(0, 16, 4)]

# Split the document
chunks = text_splitter(POLICY_DOC)
print(f"Document split into {len(chunks)} chunks\\n")

# Embed each chunk
for i, chunk in enumerate(chunks):
    vector = fake_embed(chunk)
    preview = chunk[:70].replace("\\n", " ")
    print(f"Chunk {i+1}: [{vector[0]:.3f}, {vector[1]:.3f}, ...] \\\"{preview}...\\\"")

print(f"\\nEach chunk is now a searchable vector in the store.")
""",
                    "expected_output": """Document split into 4 chunks

Chunk 1: [0.547, 0.231, ...] "SECTION 1: COMPREHENSIVE COVERAGE Comprehensive coverage protects ag..."
Chunk 2: [0.812, 0.445, ...] "SECTION 2: COLLISION COVERAGE Collision coverage pays for damage when..."
Chunk 3: [0.193, 0.678, ...] "SECTION 3: LIABILITY COVERAGE Liability coverage pays for injuries an..."
Chunk 4: [0.634, 0.119, ...] "SECTION 4: CLAIMS PROCESS To file a claim: 1) Report the incident wi..."

Each chunk is now a searchable vector in the store.""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 -- code_exercise (retrieval + QA)
                {
                    "position": 3,
                    "title": "Build a Retrieval QA Chain",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build a simple RAG pipeline. Implement the <code>retrieve</code> function
to find the most relevant chunks for a query, and the <code>generate_answer</code>
function to produce an answer grounded in the retrieved context.</p>
""",
                    "code": """import json

# Pre-indexed document chunks (simulating a vector store)
CHUNKS = [
    {
        "id": 1,
        "text": "Comprehensive coverage protects against non-collision damage including "
                "theft, vandalism, natural disasters, falling objects, and animal strikes. "
                "The deductible is $500 per incident.",
        "keywords": ["comprehensive", "theft", "vandalism", "natural disaster", "deductible"],
    },
    {
        "id": 2,
        "text": "Collision coverage pays for damage when your vehicle hits another object. "
                "This includes other vehicles, guardrails, trees, and poles. "
                "The deductible is $1,000 per incident.",
        "keywords": ["collision", "vehicle", "damage", "hit", "deductible"],
    },
    {
        "id": 3,
        "text": "Liability coverage pays for injuries and property damage you cause to "
                "others. Minimum coverage is $50,000 per person / $100,000 per accident "
                "for bodily injury, and $25,000 for property damage.",
        "keywords": ["liability", "injuries", "property damage", "bodily injury"],
    },
    {
        "id": 4,
        "text": "To file a claim: 1) Report the incident within 72 hours. 2) Provide "
                "photos and a police report if applicable. 3) An adjuster will be assigned "
                "within 2 business days.",
        "keywords": ["claim", "file", "report", "adjuster", "photos", "police report"],
    },
]

def retrieve(query: str, top_k: int = 2) -> list:
    \"\"\"Find the most relevant chunks for a query.

    Uses keyword matching to simulate vector similarity search.
    Score each chunk by counting how many of its keywords appear in the query.
    Return the top_k chunks sorted by score (highest first).

    Args:
        query: The user's question
        top_k: Number of chunks to return

    Returns:
        List of chunk dicts, sorted by relevance
    \"\"\"
    # TODO: Score each chunk by counting keyword matches with the query
    # TODO: Sort by score descending and return top_k chunks
    return []


def generate_answer(query: str, context_chunks: list) -> str:
    \"\"\"Generate an answer using retrieved context.

    Builds a prompt with context and returns a grounded answer.

    Args:
        query: The user's question
        context_chunks: Retrieved document chunks

    Returns:
        A string answer grounded in the provided context
    \"\"\"
    # TODO: Build the context string from chunk texts
    context = ""

    # TODO: Build the full prompt: instructions + context + question
    prompt = ""

    # Simulate LLM response based on context
    print(f"=== RAG Prompt (sent to LLM) ===")
    print(prompt[:300])
    print("...")
    print()

    # Simulated answer -- in production the LLM generates this
    if "deductible" in query.lower() and any("comprehensive" in c["text"].lower() for c in context_chunks):
        return "Based on your policy, the comprehensive coverage deductible is $500 per incident."
    elif "file" in query.lower() or "claim" in query.lower():
        return "To file a claim, report the incident within 72 hours and provide photos and a police report."
    return "I could not find relevant information in your policy documents."


# Test the RAG pipeline
query = "What is my deductible for comprehensive coverage?"
print(f"Question: {query}\\n")

retrieved = retrieve(query, top_k=2)
print(f"Retrieved {len(retrieved)} chunks:")
for chunk in retrieved:
    print(f"  - Chunk {chunk['id']}: {chunk['text'][:60]}...")
print()

answer = generate_answer(query, retrieved)
print(f"Answer: {answer}")
""",
                    "expected_output": """Question: What is my deductible for comprehensive coverage?

Retrieved 2 chunks:
  - Chunk 1: Comprehensive coverage protects against non-collision damage...
  - Chunk 2: Collision coverage pays for damage when your vehicle hits an...

=== RAG Prompt (sent to LLM) ===
Answer the question using ONLY the context below.

Context:
Comprehensive coverage protects against non-collision damage including theft, vandalism, natural disasters, falling objects, and animal strikes. The deductible is $500 per incident.

Collision coverage pays for damage when your vehicle hits another object. This includes other vehicles, guardrails, trees, and poles. The deductible is $1,000 per incident.

Question: What is my deductible for comprehensive coverage?
...

Answer: Based on your policy, the comprehensive coverage deductible is $500 per incident.""",
                    "validation": {
                        "must_contain": [
                            "keywords",
                            "sorted",
                            "top_k",
                            "context",
                        ],
                        "hint": "For retrieve(): loop over CHUNKS, count how many keywords appear in query.lower(), sort by score descending. For generate_answer(): join chunk texts into context, build a prompt with 'Answer using ONLY the context below.'",
                    },
                    "demo_data": None,
                },
                # Step 4 -- mcq (RAG architecture decisions)
                {
                    "position": 4,
                    "title": "RAG Architecture Decisions",
                    "step_type": "exercise",
                    "exercise_type": "mcq",
                    "content": """
<p>You're building a RAG system for an insurance company's policy
documents. The documents are updated quarterly, and agents need
precise answers about coverage limits and exclusions.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "correct_answer": "C",
                        "explanation": (
                            "Smaller chunks (300-500 tokens) with overlap give the most "
                            "precise retrieval for factual Q&A about specific coverage details. "
                            "Large chunks dilute relevance, and no overlap risks splitting "
                            "key information across chunk boundaries."
                        ),
                    },
                    "demo_data": {
                        "question": (
                            "What chunk size strategy would give the BEST retrieval accuracy "
                            "for precise policy questions like 'What is excluded from flood coverage?'"
                        ),
                        "options": [
                            {"id": "A", "text": "Large chunks (2000+ tokens) so each chunk has full context"},
                            {"id": "B", "text": "One chunk per PDF page with no overlap"},
                            {"id": "C", "text": "Small chunks (300-500 tokens) with 50-token overlap between chunks"},
                            {"id": "D", "text": "Store entire documents as single chunks for maximum context"},
                        ],
                    },
                },
                # Step 5 -- parsons (RAG pipeline assembly)
                {
                    "position": 5,
                    "title": "Assemble a RAG Pipeline",
                    "step_type": "exercise",
                    "exercise_type": "parsons",
                    "content": """
<p>Arrange these lines to build a complete LangChain RAG pipeline.
The pipeline should load documents, split them, create a vector store,
build a retrieval chain, and answer a question.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "lines": [
                            "loader = PyPDFLoader(\"policy_handbook.pdf\")",
                            "docs = loader.load()",
                            "splitter = RecursiveCharacterTextSplitter(chunk_size=500)",
                            "chunks = splitter.split_documents(docs)",
                            "vectorstore = FAISS.from_documents(chunks, embeddings)",
                            "retriever = vectorstore.as_retriever(search_kwargs={\"k\": 3})",
                            "qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)",
                            "answer = qa_chain.invoke(\"What does comprehensive cover?\")",
                        ],
                        "distractors": [
                            "vectorstore = FAISS.from_texts(docs, embeddings)",
                            "qa_chain = LLMChain(llm=llm, prompt=prompt)",
                        ],
                    },
                },
            ],
        },
        # ── Module 3: Agents & Memory ────────────────────────────────
        {
            "position": 3,
            "title": "Agents & Memory",
            "subtitle": "Build autonomous AI agents that remember conversations",
            "estimated_time": "40 min",
            "objectives": [
                "Understand agent types and when to use each",
                "Equip agents with tools that call external systems",
                "Add conversation memory so agents maintain context across turns",
            ],
            "steps": [
                # Step 1 -- concept
                {
                    "position": 1,
                    "title": "Agents: LLMs That Take Action",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>From Chains to Agents</h2>
<p>A <strong>chain</strong> follows a fixed sequence of steps. An <strong>agent</strong>
decides <em>at runtime</em> which tools to call and in what order. The LLM acts as
the reasoning engine, choosing actions based on the user's request.</p>

<h3>Agent Types</h3>
<table>
  <tr><th>Agent Type</th><th>How It Works</th><th>Best For</th></tr>
  <tr><td><strong>ReAct</strong></td><td>Reason-Act loop: think, pick a tool, observe result, repeat</td><td>Multi-step research tasks</td></tr>
  <tr><td><strong>Tool Calling</strong></td><td>Uses native function-calling to select tools</td><td>Structured tool use with Claude/GPT</td></tr>
  <tr><td><strong>Plan-and-Execute</strong></td><td>Plans all steps first, then executes them</td><td>Complex multi-step workflows</td></tr>
</table>

<h3>Memory Types</h3>
<table>
  <tr><th>Memory Type</th><th>What It Stores</th><th>Use Case</th></tr>
  <tr><td><code>ConversationBufferMemory</code></td><td>Full conversation history</td><td>Short conversations (&lt;10 turns)</td></tr>
  <tr><td><code>ConversationSummaryMemory</code></td><td>Running summary of conversation</td><td>Long conversations (20+ turns)</td></tr>
  <tr><td><code>ConversationBufferWindowMemory</code></td><td>Last K exchanges only</td><td>Balanced cost/context</td></tr>
  <tr><td><code>VectorStoreRetrieverMemory</code></td><td>Embeddings of past conversations</td><td>Semantic recall across sessions</td></tr>
</table>

<h3>Insurance Agent Example</h3>
<p>Imagine a claims assistant agent with these tools:</p>
<ul>
  <li><strong>lookup_policy</strong> -- check coverage details</li>
  <li><strong>search_claims</strong> -- find related past claims</li>
  <li><strong>check_fraud_score</strong> -- run fraud risk assessment</li>
  <li><strong>schedule_adjuster</strong> -- book an inspection appointment</li>
</ul>
<p>The agent decides which tools to call based on the customer's question,
rather than following a fixed script.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 -- code (ReAct agent simulation)
                {
                    "position": 2,
                    "title": "See a ReAct Agent in Action",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this simulation of a ReAct agent processing an insurance inquiry.
Watch how the agent reasons about which tool to call, observes the result,
and decides its next action -- just like LangChain's agent loop.</p>
""",
                    "code": """# Simulating LangChain's ReAct agent pattern

# Tool definitions
def lookup_policy(policy_id: str) -> dict:
    policies = {
        "POL-55123": {
            "holder": "Sarah Kim",
            "type": "auto",
            "coverage": "comprehensive",
            "deductible": 500,
            "status": "active"
        }
    }
    return policies.get(policy_id, {"error": "Policy not found"})

def check_claim_status(claim_id: str) -> dict:
    claims = {
        "CLM-8891": {
            "policy": "POL-55123",
            "type": "windshield",
            "status": "pending_adjuster",
            "filed_date": "2025-03-15",
            "estimated_payout": 850
        }
    }
    return claims.get(claim_id, {"error": "Claim not found"})

TOOLS = {
    "lookup_policy": lookup_policy,
    "check_claim_status": check_claim_status,
}

# Simulate the ReAct loop
query = "What's the status of claim CLM-8891? Is the policy still active?"

print(f"User: {query}")
print("=" * 60)

# Step 1: Agent reasons
print("\\nThought: I need to check the claim status first, then verify")
print("         the policy is active. Let me start with the claim.")
print("Action: check_claim_status")
print('Action Input: {"claim_id": "CLM-8891"}')

result1 = check_claim_status("CLM-8891")
print(f"Observation: {result1}")

# Step 2: Agent reasons again
print("\\nThought: The claim is on policy POL-55123. I need to check")
print("         if that policy is still active.")
print("Action: lookup_policy")
print('Action Input: {"policy_id": "POL-55123"}')

result2 = lookup_policy("POL-55123")
print(f"Observation: {result2}")

# Step 3: Agent gives final answer
print("\\nThought: I now have all the information I need.")
print("Final Answer: Claim CLM-8891 is currently pending adjuster")
print("assignment (filed March 15, 2025) for windshield damage with")
print("an estimated payout of $850. The underlying policy POL-55123")
print("for Sarah Kim is active with comprehensive coverage.")
""",
                    "expected_output": """User: What's the status of claim CLM-8891? Is the policy still active?
============================================================

Thought: I need to check the claim status first, then verify
         the policy is active. Let me start with the claim.
Action: check_claim_status
Action Input: {"claim_id": "CLM-8891"}
Observation: {'policy': 'POL-55123', 'type': 'windshield', 'status': 'pending_adjuster', 'filed_date': '2025-03-15', 'estimated_payout': 850}

Thought: The claim is on policy POL-55123. I need to check
         if that policy is still active.
Action: lookup_policy
Action Input: {"policy_id": "POL-55123"}
Observation: {'holder': 'Sarah Kim', 'type': 'auto', 'coverage': 'comprehensive', 'deductible': 500, 'status': 'active'}

Thought: I now have all the information I need.
Final Answer: Claim CLM-8891 is currently pending adjuster
assignment (filed March 15, 2025) for windshield damage with
an estimated payout of $850. The underlying policy POL-55123
for Sarah Kim is active with comprehensive coverage.""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 -- fill_in_blank (memory)
                {
                    "position": 3,
                    "title": "Add Conversation Memory",
                    "step_type": "exercise",
                    "exercise_type": "fill_in_blank",
                    "content": """
<p>Fill in the blanks to implement a conversation memory system. This mirrors
LangChain's <code>ConversationBufferWindowMemory</code> -- it keeps the last
K exchanges to stay within token limits while maintaining context.</p>
""",
                    "code": """class ConversationMemory:
    \"\"\"Keeps the last K conversation turns (like LangChain's BufferWindowMemory).\"\"\"

    def __init__(self, k: int = 3):
        self.k = k
        self.history = []

    def add_exchange(self, user_msg: str, ai_msg: str):
        self.history.append({"user": user_msg, "ai": ai_msg})
        # Keep only last K exchanges
        self.history = self.history[-self.____:]

    def get_context(self) -> str:
        lines = []
        for turn in self.____:
            lines.append(f"Customer: {turn['user']}")
            lines.append(f"Agent: {turn['ai']}")
        return "\\n".join(lines)

    def build_prompt(self, new_question: str) -> str:
        context = self.____.____()
        return (
            f"Previous conversation:\\n{context}\\n\\n"
            f"Customer: {new_question}\\n"
            f"Agent:"
        )

# Test it
memory = ConversationMemory(k=2)

memory.add_exchange(
    "I need to file a claim for my car.",
    "I can help with that. What is your policy number?"
)
memory.add_exchange(
    "It's POL-55123.",
    "Got it. Can you describe what happened?"
)
memory.add_exchange(
    "A rock hit my windshield on the highway.",
    "I've started claim CLM-8891 for windshield damage."
)

prompt = memory.build_prompt("What's my deductible for this?")
print(prompt)
print()
print(f"Memory contains {len(memory.history)} turns (window size: {memory.k})")
""",
                    "expected_output": None,
                    "validation": {
                        "blanks": [
                            {
                                "index": 0,
                                "answer": "k",
                                "hint": "Use the window size parameter to slice the history list",
                            },
                            {
                                "index": 1,
                                "answer": "history",
                                "hint": "Iterate over the stored conversation history",
                            },
                            {
                                "index": 2,
                                "answer": "get_context",
                                "hint": "Call the method that formats conversation history as a string. Two blanks here: object.method()",
                                "accept_any": False,
                            },
                        ]
                    },
                    "demo_data": None,
                },
                # Step 4 -- code_exercise (full agent with tools + memory)
                {
                    "position": 4,
                    "title": "Build a Conversational Claims Agent",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build a complete agent that combines tools and memory. The agent should:
decide which tool to call based on the query, execute the tool,
remember past conversation turns, and use that memory to handle
follow-up questions.</p>
""",
                    "code": """import json
import re

# ---- Tools ----
def lookup_policy(policy_id: str) -> dict:
    db = {
        "POL-55123": {"holder": "Sarah Kim", "coverage": "comprehensive", "deductible": 500},
    }
    return db.get(policy_id, {"error": "Not found"})

def file_claim(policy_id: str, description: str) -> dict:
    return {"claim_id": "CLM-9042", "status": "filed", "policy": policy_id}

TOOLS = {
    "lookup_policy": {"fn": lookup_policy, "params": ["policy_id"]},
    "file_claim": {"fn": file_claim, "params": ["policy_id", "description"]},
}

# ---- Memory ----
class Memory:
    def __init__(self):
        self.turns = []

    def add(self, role: str, content: str):
        self.turns.append({"role": role, "content": content})

    def context(self) -> str:
        return "\\n".join(f"{t['role']}: {t['content']}" for t in self.turns[-4:])


def select_tool(query: str, memory_context: str) -> tuple:
    \"\"\"Decide which tool to call based on the query and conversation context.

    Returns:
        (tool_name, kwargs) or (None, None) if no tool is needed.

    Logic:
        - If query mentions 'file' or 'claim' AND a policy ID is in
          the query or memory context, call file_claim
        - If query mentions 'policy' or 'coverage' or 'deductible',
          call lookup_policy
        - Extract policy_id by finding 'POL-' followed by digits
    \"\"\"
    # TODO: Implement tool selection logic
    # Search for a policy ID pattern (POL-XXXXX) in query + memory_context
    # Decide which tool to call based on keywords in the query
    # Return (tool_name, {kwargs}) or (None, None)
    return (None, None)


def agent_respond(query: str, memory: Memory) -> str:
    \"\"\"Process a query: select tool, execute, build response.\"\"\"
    memory.add("Customer", query)
    ctx = memory.context()

    # TODO: Call select_tool to decide what to do
    tool_name, kwargs = (None, None)

    if tool_name and tool_name in TOOLS:
        # TODO: Execute the selected tool and build a response
        result = {}
        response = f"Tool {tool_name} returned: {json.dumps(result)}"
    else:
        response = "How can I help you with your insurance needs?"

    memory.add("Agent", response)
    return response


# Test conversation
memory = Memory()

print("Turn 1:")
print(agent_respond("Can you look up policy POL-55123?", memory))
print()

print("Turn 2:")
print(agent_respond("What's the deductible on that policy?", memory))
print()

print("Turn 3:")
print(agent_respond("Please file a claim - a tree fell on my car.", memory))
print()

print(f"Memory has {len(memory.turns)} entries")
""",
                    "expected_output": """Turn 1:
Policy POL-55123: Sarah Kim, comprehensive coverage, $500 deductible.

Turn 2:
Based on your policy POL-55123, your deductible is $500.

Turn 3:
Claim CLM-9042 has been filed against policy POL-55123 for tree damage.

Memory has 6 entries""",
                    "validation": {
                        "must_contain": [
                            "select_tool",
                            "TOOLS",
                            "memory",
                            "POL-",
                        ],
                        "hint": "In select_tool: use re.search(r'POL-\\d+', ...) to find policy IDs in query + memory_context. Check keywords like 'file', 'claim', 'policy', 'deductible' to pick the tool. In agent_respond: call select_tool(query, ctx), then execute TOOLS[tool_name]['fn'](**kwargs).",
                    },
                    "demo_data": None,
                },
                # Step 5 -- mcq (agent architecture)
                {
                    "position": 5,
                    "title": "Choosing the Right Memory Pattern",
                    "step_type": "exercise",
                    "exercise_type": "mcq",
                    "content": """
<p>You're designing an AI agent for an insurance call center. The agent
needs to handle multi-turn conversations, look up policies, file claims,
and escalate to human agents. Conversations can last 20+ turns.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "correct_answer": "B",
                        "explanation": (
                            "ConversationSummaryMemory is the best choice for long conversations "
                            "(20+ turns). Buffer memory would exceed token limits, window memory "
                            "loses early context (like the policy number mentioned in turn 1), "
                            "and no memory means the agent can't handle follow-up questions. "
                            "Summary memory compresses the conversation while retaining key facts."
                        ),
                    },
                    "demo_data": {
                        "question": (
                            "Which memory type should you use for a 20+ turn call center "
                            "conversation where early details (like the policy number) matter "
                            "throughout the entire conversation?"
                        ),
                        "options": [
                            {"id": "A", "text": "ConversationBufferMemory -- store every message verbatim"},
                            {"id": "B", "text": "ConversationSummaryMemory -- maintain a running summary of key facts"},
                            {"id": "C", "text": "ConversationBufferWindowMemory(k=3) -- keep only the last 3 exchanges"},
                            {"id": "D", "text": "No memory -- re-send the full conversation each time"},
                        ],
                    },
                },
                # Step 6 -- system_build (capstone: RAG API to Vercel)
                {
                    "position": 6,
                    "title": "Deploy: Production RAG API on Vercel",
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
  <h2>Mission: Production RAG API for Insurance Knowledge Search</h2>
  <div class="objective">
    <strong>Business context:</strong> The claims team answers 2,400 policy-coverage questions per day. Each takes 6-8 minutes of manual doc lookup. You are deploying a LangChain-powered RAG API that grounds Claude's answers in the live Weaviate policy index, returns inline citations, and tracks per-query cost so finance can budget production usage.
  </div>

  <h3>Production Constraints</h3>
  <div class="constraints">
    <div class="pill"><strong>Latency SLA</strong><span>p95 &lt; 2.5s</span></div>
    <div class="pill"><strong>Scale Target</strong><span>50 req/s sustained</span></div>
    <div class="pill"><strong>Cost Budget</strong><span>&lt; $0.012 / query</span></div>
    <div class="pill"><strong>Platform</strong><span>Vercel serverless</span></div>
    <div class="pill"><strong>Retrieval</strong><span>Weaviate (top-4 chunks)</span></div>
    <div class="pill"><strong>Generation</strong><span>Claude 3.5 Sonnet</span></div>
  </div>

  <h3>Acceptance Criteria</h3>
  <ul class="accept">
    <li><strong>POST /ask</strong> accepts <code>{query, session_id}</code> and returns <code>{answer, sources[], cost}</code></li>
    <li>Every answer includes at least one citation with <code>{doc_id, snippet, score}</code></li>
    <li>Conversation history is persisted per <code>session_id</code> and injected into the prompt (last 4 turns)</li>
    <li>Per-query cost is computed from input/output token counts and reported back in the response</li>
    <li>Structured JSON logs for every request: session, latency, cost, retrieval_k, tokens_in, tokens_out</li>
    <li>Invalid input returns 422 with Pydantic detail; Weaviate/Claude outages return 503</li>
    <li>Cold-start on Vercel &lt; 3s, warm p95 &lt; 2.5s under 50 req/s load test</li>
    <li>Secrets (<code>ANTHROPIC_API_KEY</code>, <code>WEAVIATE_URL</code>, <code>WEAVIATE_API_KEY</code>) come from Vercel environment -- never checked in</li>
  </ul>
</div>
""",
                    "code": """\"\"\"Production RAG API -- Starter Code

FastAPI + LangChain app that retrieves from Weaviate and generates with Claude.
Deploy to Vercel serverless. Extend the TODOs to meet the acceptance criteria.
\"\"\"

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

import weaviate
from anthropic import Anthropic, APIError


# ── Configuration ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
WEAVIATE_URL = os.environ["WEAVIATE_URL"]
WEAVIATE_API_KEY = os.environ["WEAVIATE_API_KEY"]
WEAVIATE_CLASS = os.environ.get("WEAVIATE_CLASS", "PolicyChunk")

MODEL_ID = os.environ.get("MODEL_ID", "claude-3-5-sonnet-20241022")
TOP_K = int(os.environ.get("TOP_K", "4"))
HISTORY_WINDOW = int(os.environ.get("HISTORY_WINDOW", "4"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "800"))

# Claude 3.5 Sonnet pricing (USD per 1K tokens) -- keep in sync with provider pricing page.
PRICE_IN_PER_1K = 0.003
PRICE_OUT_PER_1K = 0.015


# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
)
logger = logging.getLogger("rag-api")


def jlog(event: str, **fields: Any) -> None:
    \"\"\"Emit a structured JSON log line.\"\"\"
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, default=str))


# ── Clients ────────────────────────────────────────────────────
claude = Anthropic(api_key=ANTHROPIC_API_KEY)
wv_client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
)


# ── In-process conversation memory ────────────────────────────
# In production, swap for Redis or Upstash so state survives serverless cold-starts.
_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=HISTORY_WINDOW * 2))


# ── Schemas ────────────────────────────────────────────────────
class AskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1200)
    session_id: str = Field(min_length=1, max_length=80)


class Source(BaseModel):
    doc_id: str
    snippet: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    cost: float
    latency_ms: int
    session_id: str


# ── Retrieval ─────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a careful insurance policy analyst. Answer ONLY from the provided "
    "context passages. If the answer is not in the context, respond: "
    "'I cannot find that in the referenced policies.' Always cite the doc_id "
    "inline in the form [DOC-XYZ] immediately after any claim that depends on a source."
)


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    \"\"\"Fetch top-k policy chunks from Weaviate with hybrid search.\"\"\"
    try:
        result = (
            wv_client.query
            .get(WEAVIATE_CLASS, ["doc_id", "text", "section"])
            .with_hybrid(query=query, alpha=0.5)
            .with_limit(k)
            .with_additional(["score"])
            .do()
        )
    except Exception as exc:  # network, auth, schema errors
        jlog("retrieval_error", error=str(exc))
        raise HTTPException(status_code=503, detail="Retrieval backend unavailable")

    objs = result.get("data", {}).get("Get", {}).get(WEAVIATE_CLASS, []) or []
    return [
        {
            "doc_id": o.get("doc_id", "UNKNOWN"),
            "text": o.get("text", ""),
            "score": float(o.get("_additional", {}).get("score", 0.0)),
        }
        for o in objs
    ]


def build_context(passages: list[dict]) -> str:
    return "\\n\\n".join(
        f"[{p['doc_id']}] (score={p['score']:.3f})\\n{p['text']}"
        for p in passages
    )


def render_history(session_id: str) -> list[dict]:
    return list(_history[session_id])


def compute_cost(tokens_in: int, tokens_out: int) -> float:
    return round(
        (tokens_in / 1000) * PRICE_IN_PER_1K + (tokens_out / 1000) * PRICE_OUT_PER_1K,
        6,
    )


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="Insurance RAG API", version="1.0.0")


@app.exception_handler(ValidationError)
async def _on_validation_error(_: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": MODEL_ID, "top_k": TOP_K}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    req_id = str(uuid.uuid4())
    started = time.perf_counter()

    # 1) Retrieve
    passages = retrieve(req.query)
    if not passages:
        jlog("no_passages", request_id=req_id, session_id=req.session_id)

    # 2) Build prompt with history + context
    context_block = build_context(passages)
    history_msgs = render_history(req.session_id)
    user_msg = (
        f"Context:\\n{context_block}\\n\\nQuestion: {req.query}\\n\\n"
        "Answer concisely. Cite inline with [DOC-ID] from the context."
    )
    messages = history_msgs + [{"role": "user", "content": user_msg}]

    # 3) Generate
    try:
        resp = claude.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
    except APIError as exc:
        jlog("claude_error", request_id=req_id, error=str(exc))
        raise HTTPException(status_code=503, detail="LLM backend unavailable")

    answer = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    tokens_in = resp.usage.input_tokens
    tokens_out = resp.usage.output_tokens
    cost = compute_cost(tokens_in, tokens_out)

    # 4) Persist turn for the session
    _history[req.session_id].append({"role": "user", "content": req.query})
    _history[req.session_id].append({"role": "assistant", "content": answer})

    latency_ms = int((time.perf_counter() - started) * 1000)
    jlog(
        "ask_completed",
        request_id=req_id,
        session_id=req.session_id,
        latency_ms=latency_ms,
        cost=cost,
        retrieval_k=len(passages),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    return AskResponse(
        answer=answer,
        sources=[
            Source(doc_id=p["doc_id"], snippet=p["text"][:240], score=p["score"])
            for p in passages
        ],
        cost=cost,
        latency_ms=latency_ms,
        session_id=req.session_id,
    )


# ── Vercel entrypoint ─────────────────────────────────────────
# File layout expected by Vercel Python runtime: `api/index.py` exporting `app`.
# Set the Vercel project to use the Python runtime and point Framework Preset to "Other".
""",
                    "expected_output": None,
                    "deployment_config": {
                        "platform": "vercel",
                        "service": "serverless-python",
                        "dockerfile": """# Local parity container -- Vercel itself builds a serverless bundle.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/

ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
""",
                        "requirements": (
                            "fastapi>=0.115.0\n"
                            "uvicorn[standard]>=0.30.0\n"
                            "pydantic>=2.6.0\n"
                            "anthropic>=0.39.0\n"
                            "weaviate-client>=3.25.0,<4\n"
                            "langchain>=0.2.0\n"
                            "langchain-anthropic>=0.1.15\n"
                        ),
                        "infra_hint": (
                            "Layout the repo as `api/index.py` (exports `app`) + `requirements.txt` "
                            "+ `vercel.json`. In vercel.json set "
                            '{"builds": [{"src": "api/index.py", "use": "@vercel/python"}], '
                            '"routes": [{"src": "/(.*)", "dest": "api/index.py"}]}. '
                            "Add ANTHROPIC_API_KEY, WEAVIATE_URL, WEAVIATE_API_KEY as Vercel env vars "
                            "(Production + Preview). Use Upstash Redis for session history once you "
                            "outgrow the in-process deque."
                        ),
                    },
                    "demo_data": {
                        "phases": [
                            {"id": "local", "title": "Local Build"},
                            {"id": "docker", "title": "Containerize"},
                            {"id": "deploy", "title": "Deploy to Vercel"},
                            {"id": "test", "title": "Load Test (50 req/s)"},
                        ],
                        "checklist": [
                            {"id": "check_endpoint", "label": "POST /ask returns {answer, sources[], cost} with at least one citation"},
                            {"id": "check_retrieval", "label": "Weaviate hybrid retrieval returns top-4 chunks with doc_id + score"},
                            {"id": "check_history", "label": "Conversation history (last 4 turns) is injected per session_id"},
                            {"id": "check_cost", "label": "Per-query cost is computed from token usage and returned in the response"},
                            {"id": "check_errors", "label": "Validation errors return 422, Weaviate/Claude outages return 503"},
                            {"id": "check_logs", "label": "Structured JSON logs emitted per request (session, latency, cost, tokens)"},
                            {"id": "check_docker", "label": "Dockerfile builds and serves /ask on localhost:8000 for parity"},
                            {"id": "check_vercel", "label": "Deployed to Vercel with secrets set; public URL answers /health"},
                            {"id": "check_load", "label": "Sustained 50 req/s with p95 < 2.5s (documented with k6/hey/locust)"},
                            {"id": "check_cost_budget", "label": "Average query cost stays below $0.012 at TOP_K=4"},
                        ],
                    },
                    "validation": {
                        "endpoint_check": {
                            "method": "POST",
                            "path": "/ask",
                            "body": {
                                "query": "What is the deductible on policy POL-55123 for hail damage?",
                                "session_id": "demo-session-001",
                            },
                            "expected_status": 200,
                            "expected_fields": ["answer", "sources", "cost", "latency_ms", "session_id"],
                        },
                    },
                },
            ],
        },
    ],
}
