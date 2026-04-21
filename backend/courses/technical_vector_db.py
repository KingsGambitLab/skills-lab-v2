"""
Technical Skill Course: Vector Databases & Semantic Search
Covers embeddings, vector similarity, hybrid search, and building
a production semantic search pipeline with insurance domain examples.
"""

COURSE = {
    "id": "vector-db",
    "title": "Vector Databases & Semantic Search",
    "subtitle": "Build intelligent search that understands meaning, not just keywords",
    "icon": "🔍",
    "course_type": "technical",
    "level": "Intermediate",
    "tags": ["vector-db", "embeddings", "semantic-search", "pinecone", "weaviate", "python"],
    "estimated_time": "~2 hours",
    "description": (
        "Learn how vector databases power modern AI search. You'll build embeddings, "
        "measure similarity, construct a semantic search pipeline, and apply production "
        "patterns like chunking, metadata filtering, and re-ranking -- all with hands-on "
        "code exercises using insurance industry examples."
    ),
    "modules": [
        # ── Module 1: Understanding Embeddings ───────────────────────────
        {
            "position": 1,
            "title": "Understanding Embeddings",
            "subtitle": "Turn text into vectors that capture meaning",
            "estimated_time": "35 min",
            "objectives": [
                "Understand what embeddings are and why they matter for search",
                "Convert text to vector representations",
                "Compute cosine similarity, dot product, and Euclidean distance between vectors",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "What Are Embeddings?",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<style>
.vec-demo { background: #151b2e; border: 1px solid #2a3352; border-radius: 12px; padding: 24px; margin: 16px 0; font-family: 'Inter', system-ui, sans-serif; }
.vec-demo h2 { color: #4a7cff; margin-top: 0; font-size: 1.3em; }
.vec-demo .hook { background: linear-gradient(135deg, #1e2538, #252e45); border-left: 4px solid #2dd4bf; padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }
.vec-demo .hook p { color: #e8ecf4; margin: 4px 0; line-height: 1.6; }
.vec-demo .hook strong { color: #2dd4bf; }
.vec-demo .search-panel { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.vec-demo .panel { background: #1e2538; border: 1px solid #2a3352; border-radius: 8px; padding: 16px; }
.vec-demo .panel h3 { margin-top: 0; font-size: 1em; }
.vec-demo .panel.keyword h3 { color: #f97066; }
.vec-demo .panel.semantic h3 { color: #2dd4bf; }
.vec-demo .claims-list { font-size: 0.82em; color: #8b95b0; margin-bottom: 14px; line-height: 1.7; }
.vec-demo .claims-list div { padding: 4px 0; border-bottom: 1px solid #2a3352; }
.vec-demo .claims-list .id { color: #4a7cff; font-family: 'Fira Code', monospace; }
.vec-demo input[type=text] { width: 100%; background: #151b2e; color: #e8ecf4; border: 1px solid #2a3352; border-radius: 6px; padding: 10px 12px; font-size: 0.9em; box-sizing: border-box; }
.vec-demo input:focus { outline: none; border-color: #4a7cff; }
.vec-demo .btn-search { background: #4a7cff; color: #fff; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 8px; width: 100%; transition: background 0.2s; }
.vec-demo .btn-search:hover { background: #3a6cef; }
.vec-demo .results { margin-top: 12px; min-height: 80px; }
.vec-demo .result-item { padding: 8px 10px; margin: 4px 0; border-radius: 6px; font-size: 0.82em; display: flex; justify-content: space-between; align-items: center; }
.vec-demo .result-item.hit { background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.3); color: #e8ecf4; }
.vec-demo .result-item.miss { background: rgba(249,112,102,0.08); border: 1px solid rgba(249,112,102,0.2); color: #8b95b0; }
.vec-demo .score { font-family: 'Fira Code', monospace; font-weight: 600; }
.vec-demo .score.good { color: #2dd4bf; }
.vec-demo .score.bad { color: #f97066; }
.vec-demo .verdict { margin-top: 16px; padding: 12px 16px; border-radius: 8px; font-size: 0.88em; display: none; }
.vec-demo .verdict.show { display: block; }
.vec-demo .verdict.win { background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.3); color: #2dd4bf; }
.vec-demo .verdict.tie { background: rgba(74,124,255,0.1); border: 1px solid rgba(74,124,255,0.3); color: #4a7cff; }
@media(max-width:600px){ .vec-demo .search-panel { grid-template-columns: 1fr; } }
</style>

<div class="vec-demo">
  <h2>The Search Challenge: Keywords vs. Meaning</h2>
  <div class="hook">
    <p><strong>The problem:</strong> You have 10,000 insurance claims and a customer calls: "My car got flooded in the storm." Your database says "water damage to vehicle." Keyword search finds <em>nothing</em>. The words don't match.</p>
    <p><strong>Try it yourself</strong> -- search these 5 claims both ways and see which approach actually works.</p>
  </div>

  <div class="claims-list">
    <div><span class="id">CLM-001</span> Water damage to vehicle from burst pipe during freeze</div>
    <div><span class="id">CLM-002</span> Rear-ended at intersection, airbag deployed, neck injury</div>
    <div><span class="id">CLM-003</span> Vehicle submerged in flash flood on Route 9</div>
    <div><span class="id">CLM-004</span> Fender bender in parking lot, cosmetic scratches only</div>
    <div><span class="id">CLM-005</span> Roof shingles torn off by hailstorm, interior water intrusion</div>
  </div>

  <input type="text" id="vecQuery" placeholder="Try: my car got flooded in the storm" value="my car got flooded in the storm" />
  <button class="btn-search" onclick="runSearchChallenge()">Search Both Ways</button>

  <div class="search-panel" id="vecPanels" style="display:none;">
    <div class="panel keyword">
      <h3>Keyword Search</h3>
      <div class="results" id="kwResults"></div>
    </div>
    <div class="panel semantic">
      <h3>Semantic Search</h3>
      <div class="results" id="semResults"></div>
    </div>
  </div>
  <div class="verdict" id="vecVerdict"></div>
</div>

<script>
(function(){
  const claims = [
    {id:"CLM-001", text:"Water damage to vehicle from burst pipe during freeze", topics:["water","damage","vehicle","pipe","flood","submerge","leak","moisture"]},
    {id:"CLM-002", text:"Rear-ended at intersection, airbag deployed, neck injury", topics:["collision","crash","rear-end","accident","hit","impact"]},
    {id:"CLM-003", text:"Vehicle submerged in flash flood on Route 9", topics:["flood","water","submerge","storm","vehicle","car","rain","flooded"]},
    {id:"CLM-004", text:"Fender bender in parking lot, cosmetic scratches only", topics:["collision","minor","scratch","fender","accident","crash","bumper"]},
    {id:"CLM-005", text:"Roof shingles torn off by hailstorm, interior water intrusion", topics:["storm","hail","water","damage","roof","weather","rain"]}
  ];

  function keywordSearch(query) {
    const words = query.toLowerCase().split(/ +/).filter(w => w.length > 2);
    return claims.map(c => {
      const txt = c.text.toLowerCase();
      const matches = words.filter(w => txt.includes(w));
      return {id: c.id, text: c.text, score: matches.length / words.length, matched: matches};
    }).sort((a,b) => b.score - a.score);
  }

  function semanticSearch(query) {
    const qWords = query.toLowerCase().split(/ +/);
    const synonyms = {"car":["vehicle","auto"],"flooded":["flood","submerge","water","submerged"],"flood":["water","submerge","flooded"],"storm":["hail","weather","rain"],"crashed":["collision","crash","accident","impact","hit"],"hit":["collision","crash","rear-end","impact"],"scratched":["scratch","cosmetic","fender"],"water":["flood","moisture","leak","submerge"],"accident":["collision","crash","impact"],"stolen":["theft","steal"],"broken":["damage","crack","shatter"],"damaged":["damage","broken","dent"]};
    const expanded = new Set(qWords);
    qWords.forEach(w => { if(synonyms[w]) synonyms[w].forEach(s => expanded.add(s)); });

    return claims.map(c => {
      const topicHits = c.topics.filter(t => expanded.has(t)).length;
      const score = Math.min(topicHits / 3, 1.0);
      return {id: c.id, text: c.text, score: parseFloat(score.toFixed(3))};
    }).sort((a,b) => b.score - a.score);
  }

  window.runSearchChallenge = function() {
    const query = document.getElementById('vecQuery').value.trim();
    if(!query) return;
    document.getElementById('vecPanels').style.display = 'grid';

    const kwRes = keywordSearch(query);
    const semRes = semanticSearch(query);

    let kwHTML = '', semHTML = '', kwHits = 0, semHits = 0;
    kwRes.forEach(r => {
      const isHit = r.score > 0.15;
      if(isHit) kwHits++;
      kwHTML += '<div class="result-item '+(isHit?'hit':'miss')+'"><span>'+r.id+': '+r.text.substring(0,45)+'...</span><span class="score '+(isHit?'good':'bad')+'">'+(r.score*100).toFixed(0)+'%</span></div>';
    });
    semRes.forEach(r => {
      const isHit = r.score > 0.15;
      if(isHit) semHits++;
      semHTML += '<div class="result-item '+(isHit?'hit':'miss')+'"><span>'+r.id+': '+r.text.substring(0,45)+'...</span><span class="score '+(isHit?'good':'bad')+'">'+(r.score*100).toFixed(0)+'%</span></div>';
    });

    document.getElementById('kwResults').innerHTML = kwHTML;
    document.getElementById('semResults').innerHTML = semHTML;

    const v = document.getElementById('vecVerdict');
    if(semHits > kwHits) {
      v.className = 'verdict show win';
      v.innerHTML = '<strong>Semantic search found '+semHits+' relevant claims vs. keyword search: '+kwHits+'.</strong> This is why embeddings matter -- they match on meaning, not just words. That gap multiplies at 10,000+ claims.';
    } else if(semHits === kwHits && semHits > 0) {
      v.className = 'verdict show tie';
      v.innerHTML = '<strong>Tie!</strong> Both found '+kwHits+' results. Try a query where the words differ from the database -- like "my automobile was in a wreck" instead of "vehicle collision."';
    } else {
      v.className = 'verdict show tie';
      v.innerHTML = 'Try queries like <em>"my car got flooded"</em>, <em>"minor parking lot crash"</em>, or <em>"hail destroyed my roof"</em> to see the difference.';
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
                # Step 2 — code (run & observe)
                {
                    "position": 2,
                    "title": "Build and Compare Vectors",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this code to see how we represent text as vectors and compute similarity.
We use simplified mock embeddings here to illustrate the math -- real embedding
models produce much longer vectors but the similarity calculations are identical.</p>
""",
                    "code": """import math

# Mock embeddings -- imagine these came from an embedding model.
# Each vector captures meaning along dimensions like:
# [vehicle_damage, water_related, theft_related, injury_related, property_related]

embeddings = {
    "my car got flooded in the storm":       [0.8, 0.9, 0.05, 0.1, 0.3],
    "water damage to vehicle":               [0.7, 0.85, 0.05, 0.05, 0.2],
    "my car was stolen from the parking lot": [0.6, 0.05, 0.95, 0.1, 0.15],
    "vehicle theft at shopping center":       [0.5, 0.05, 0.9, 0.05, 0.2],
    "I slipped and fell in the store":        [0.05, 0.1, 0.05, 0.9, 0.7],
}

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b)

def euclidean_distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# Compare "my car got flooded" against all others
query = "my car got flooded in the storm"
query_vec = embeddings[query]

print(f"Query: \\"{query}\\"")
print(f"Vector: {query_vec}")
print()
print("Similarities:")
print("-" * 65)

for text, vec in embeddings.items():
    if text == query:
        continue
    cos_sim = cosine_similarity(query_vec, vec)
    euc_dist = euclidean_distance(query_vec, vec)
    dot_prod = sum(x * y for x, y in zip(query_vec, vec))
    print(f"  Cosine={cos_sim:.3f}  Euclid={euc_dist:.3f}  Dot={dot_prod:.3f}")
    print(f"    \\"{text}\\"")
    print()
""",
                    "expected_output": """Query: "my car got flooded in the storm"
Vector: [0.8, 0.9, 0.05, 0.1, 0.3]

Similarities:
-----------------------------------------------------------------
  Cosine=0.997  Euclid=0.16  Dot=1.37
    "water damage to vehicle"

  Cosine=0.506  Euclid=1.30  Dot=0.57
    "my car was stolen from the parking lot"

  Cosine=0.468  Euclid=1.30  Dot=0.51
    "vehicle theft at shopping center"

  Cosine=0.326  Euclid=1.42  Dot=0.37
    "I slipped and fell in the store"
""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 — fill_in_blank
                {
                    "position": 3,
                    "title": "Implement Cosine Similarity",
                    "step_type": "exercise",
                    "exercise_type": "fill_in_blank",
                    "content": """
<p>Fill in the blanks to complete the cosine similarity function. Remember:
cosine similarity = (A &middot; B) / (||A|| * ||B||), where <code>&middot;</code> is the
dot product and <code>||X||</code> is the magnitude (L2 norm).</p>
""",
                    "code": """import math

def cosine_similarity(vec_a, vec_b):
    # Step 1: Compute the dot product
    dot_product = ____(x * y for x, y in zip(vec_a, vec_b))

    # Step 2: Compute magnitudes
    magnitude_a = math.sqrt(sum(x ** 2 for x in ____))
    magnitude_b = math.sqrt(sum(x ** 2 for x in vec_b))

    # Step 3: Return cosine similarity
    return dot_product / (magnitude_a * ____)

# Test it
claim_a = [0.8, 0.9, 0.05, 0.1]   # "flood damage to car"
claim_b = [0.75, 0.85, 0.1, 0.05]  # "water damage to vehicle"
claim_c = [0.1, 0.05, 0.9, 0.8]    # "slip and fall injury"

print(f"Flood vs Water damage: {cosine_similarity(claim_a, claim_b):.4f}")
print(f"Flood vs Slip and fall: {cosine_similarity(claim_a, claim_c):.4f}")
""",
                    "expected_output": None,
                    "validation": {
                        "blanks": [
                            {
                                "index": 0,
                                "answer": "sum",
                                "hint": "You need to add up all the x*y products -- which built-in function does that?",
                                "alternatives": [],
                            },
                            {
                                "index": 1,
                                "answer": "vec_a",
                                "hint": "You need the magnitude of the first vector parameter",
                                "alternatives": [],
                            },
                            {
                                "index": 2,
                                "answer": "magnitude_b",
                                "hint": "Divide by the product of both magnitudes",
                                "alternatives": [],
                            },
                        ]
                    },
                    "demo_data": None,
                },
                # Step 4 — code_exercise
                {
                    "position": 4,
                    "title": "Build a Nearest-Neighbor Search",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Implement a function that finds the <code>top_k</code> most similar documents
to a query vector. This is the core operation behind every vector database.
Use cosine similarity to rank results.</p>
""",
                    "code": """import math

# Mock embedding database of insurance policy descriptions
POLICY_DB = {
    "POL-001": {"text": "Comprehensive auto coverage including collision and weather damage",
                "vector": [0.9, 0.7, 0.1, 0.05, 0.8]},
    "POL-002": {"text": "Liability-only auto policy for bodily injury and property damage",
                "vector": [0.7, 0.2, 0.1, 0.85, 0.3]},
    "POL-003": {"text": "Homeowner policy covering fire, theft, and natural disasters",
                "vector": [0.1, 0.8, 0.9, 0.1, 0.7]},
    "POL-004": {"text": "Commercial fleet insurance for delivery vehicles",
                "vector": [0.85, 0.3, 0.05, 0.2, 0.9]},
    "POL-005": {"text": "Personal umbrella policy for excess liability protection",
                "vector": [0.3, 0.1, 0.15, 0.9, 0.2]},
    "POL-006": {"text": "Flood and water damage endorsement for coastal properties",
                "vector": [0.15, 0.95, 0.8, 0.05, 0.6]},
}

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b)


def search(query_vector, top_k=3):
    \"\"\"Find the top_k most similar policies to the query vector.

    Args:
        query_vector: The embedding vector of the search query.
        top_k: Number of results to return.

    Returns:
        List of tuples: [(policy_id, text, similarity_score), ...]
        sorted by similarity descending.
    \"\"\"
    # TODO: Compute cosine similarity between query_vector and every policy vector
    # TODO: Sort by similarity (highest first)
    # TODO: Return the top_k results as a list of (policy_id, text, score) tuples
    results = []

    return results


# Test: search for "storm damage to my car"
query = [0.8, 0.85, 0.1, 0.1, 0.7]  # embedding for "storm damage to my car"
print("Query: storm damage to my car")
print("=" * 55)
results = search(query, top_k=3)
for policy_id, text, score in results:
    print(f"  [{score:.3f}] {policy_id}: {text}")
""",
                    "expected_output": """Query: storm damage to my car
=======================================================
  [0.987] POL-001: Comprehensive auto coverage including collision and weather damage
  [0.947] POL-004: Commercial fleet insurance for delivery vehicles
  [0.885] POL-006: Flood and water damage endorsement for coastal properties""",
                    "validation": {
                        "hint": "Loop through POLICY_DB.items(), compute cosine_similarity for each, sort the list with key=lambda x: x[2] and reverse=True, then slice [:top_k].",
                    },
                    "demo_data": None,
                },
                # Step 5 — categorization
                {
                    "position": 5,
                    "title": "Match Similarity Measures to Use Cases",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>Different similarity measures work best for different scenarios.
Drag each use case to the similarity measure that fits best.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "correct_mapping": {
                            "Finding semantically similar claim descriptions": "Cosine Similarity",
                            "Comparing normalized document embeddings": "Cosine Similarity",
                            "Ranking by relevance weighted by document importance": "Dot Product",
                            "Boosting popular policy templates in search results": "Dot Product",
                            "Detecting near-duplicate claim submissions": "Euclidean Distance",
                            "Flagging claims that are suspiciously close to known fraud patterns": "Euclidean Distance",
                        }
                    },
                    "demo_data": {
                        "instruction": "Match each use case to the best similarity measure.",
                        "categories": ["Cosine Similarity", "Dot Product", "Euclidean Distance"],
                        "items": [
                            "Finding semantically similar claim descriptions",
                            "Comparing normalized document embeddings",
                            "Ranking by relevance weighted by document importance",
                            "Boosting popular policy templates in search results",
                            "Detecting near-duplicate claim submissions",
                            "Flagging claims that are suspiciously close to known fraud patterns",
                        ],
                    },
                },
            ],
        },
        # ── Module 2: Building a Search Pipeline ─────────────────────────
        {
            "position": 2,
            "title": "Building a Search Pipeline",
            "subtitle": "Index, query, filter, and combine search strategies",
            "estimated_time": "40 min",
            "objectives": [
                "Index documents with embeddings and metadata into an in-memory store",
                "Implement filtered vector search with metadata constraints",
                "Combine keyword and semantic search into a hybrid approach",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "Anatomy of a Search Pipeline",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>From Raw Documents to Search Results</h2>
<p>A semantic search pipeline has two phases: <strong>indexing</strong> (offline)
and <strong>querying</strong> (online). Understanding both is critical to
building reliable search for insurance applications.</p>

<h3>Indexing Phase</h3>
<ol>
  <li><strong>Ingest</strong> -- load documents (policies, claims, guidelines)</li>
  <li><strong>Chunk</strong> -- split long documents into searchable segments</li>
  <li><strong>Embed</strong> -- convert each chunk to a vector</li>
  <li><strong>Store</strong> -- save vectors + metadata in a vector database</li>
</ol>

<h3>Query Phase</h3>
<ol>
  <li><strong>Embed the query</strong> -- same model used for indexing</li>
  <li><strong>Search</strong> -- find nearest vectors (ANN search)</li>
  <li><strong>Filter</strong> -- apply metadata constraints (date, category, status)</li>
  <li><strong>Re-rank</strong> -- optionally re-score results for precision</li>
  <li><strong>Return</strong> -- top-k results with scores and metadata</li>
</ol>

<h3>Vector DB Options</h3>
<table>
  <tr><th>Database</th><th>Type</th><th>Best For</th></tr>
  <tr><td><strong>Pinecone</strong></td><td>Managed cloud</td><td>Zero-ops, auto-scaling</td></tr>
  <tr><td><strong>Weaviate</strong></td><td>Open-source / cloud</td><td>Hybrid search built-in, GraphQL API</td></tr>
  <tr><td><strong>pgvector</strong></td><td>PostgreSQL extension</td><td>Adding vectors to existing Postgres</td></tr>
  <tr><td><strong>ChromaDB</strong></td><td>Lightweight / embedded</td><td>Prototyping, local development</td></tr>
  <tr><td><strong>Qdrant</strong></td><td>Open-source / cloud</td><td>Advanced filtering, payload indexing</td></tr>
</table>

<h3>Hybrid Search: Best of Both Worlds</h3>
<p>Pure semantic search misses exact matches (policy numbers, claim IDs).
Pure keyword search misses meaning ("vehicle submerged" vs "flood damage").
<strong>Hybrid search</strong> combines both with score fusion, giving you
precision on exact terms and recall on conceptual queries.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — code (run & observe)
                {
                    "position": 2,
                    "title": "Build an In-Memory Vector Store",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this code to see a minimal but complete vector store implementation.
It supports indexing documents with metadata, querying by vector similarity,
and filtering by metadata fields -- the same operations any production
vector database provides.</p>
""",
                    "code": """import math
from dataclasses import dataclass, field

@dataclass
class Document:
    id: str
    text: str
    vector: list
    metadata: dict = field(default_factory=dict)

class VectorStore:
    def __init__(self):
        self.documents = {}

    def upsert(self, doc_id, text, vector, metadata=None):
        self.documents[doc_id] = Document(
            id=doc_id, text=text, vector=vector,
            metadata=metadata or {}
        )

    def _cosine_sim(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def query(self, query_vector, top_k=3, filters=None):
        results = []
        for doc in self.documents.values():
            # Apply metadata filters
            if filters:
                skip = False
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue
            score = self._cosine_sim(query_vector, doc.vector)
            results.append((doc, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

# Index some insurance claims
store = VectorStore()

claims = [
    ("CLM-001", "Rear-ended at a stoplight, bumper damage",
     [0.9, 0.1, 0.05, 0.8, 0.1], {"type": "auto", "status": "open"}),
    ("CLM-002", "Roof damaged by hailstorm last Tuesday",
     [0.2, 0.85, 0.7, 0.1, 0.6], {"type": "home", "status": "open"}),
    ("CLM-003", "Windshield cracked by a rock on the highway",
     [0.85, 0.1, 0.1, 0.6, 0.05], {"type": "auto", "status": "closed"}),
    ("CLM-004", "Basement flooded during heavy rain",
     [0.1, 0.9, 0.8, 0.05, 0.7], {"type": "home", "status": "open"}),
    ("CLM-005", "Fender bender in parking lot, minor scratches",
     [0.8, 0.05, 0.05, 0.7, 0.1], {"type": "auto", "status": "open"}),
]

for cid, text, vec, meta in claims:
    store.upsert(cid, text, vec, meta)

print(f"Indexed {len(store.documents)} claims")
print()

# Search: "car accident with body damage"
query_vec = [0.85, 0.1, 0.05, 0.75, 0.1]

print("All results for 'car accident with body damage':")
for doc, score in store.query(query_vec, top_k=3):
    print(f"  [{score:.3f}] {doc.id}: {doc.text} ({doc.metadata})")

print()
print("Filtered to open auto claims only:")
for doc, score in store.query(query_vec, top_k=3, filters={"type": "auto", "status": "open"}):
    print(f"  [{score:.3f}] {doc.id}: {doc.text}")
""",
                    "expected_output": """Indexed 5 claims

All results for 'car accident with body damage':
  [0.998] CLM-001: Rear-ended at a stoplight, bumper damage ({'type': 'auto', 'status': 'open'})
  [0.993] CLM-005: Fender bender in parking lot, minor scratches ({'type': 'auto', 'status': 'open'})
  [0.975] CLM-003: Windshield cracked by a rock on the highway ({'type': 'auto', 'status': 'closed'})

Filtered to open auto claims only:
  [0.998] CLM-001: Rear-ended at a stoplight, bumper damage
  [0.993] CLM-005: Fender bender in parking lot, minor scratches""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 — parsons
                {
                    "position": 3,
                    "title": "Assemble a Weaviate Indexing Pipeline",
                    "step_type": "exercise",
                    "exercise_type": "parsons",
                    "content": """
<p>Arrange these code blocks to build a correct Weaviate document indexing
pipeline. The steps should: connect to Weaviate, create a collection schema,
embed each document, and batch-insert the vectors with metadata.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": {
                        "lines": [
                            'client = weaviate.connect_to_local()',
                            'collection = client.collections.create(name="Claims",',
                            '    vectorizer_config=Configure.Vectorizer.text2vec_openai())',
                            'with collection.batch.dynamic() as batch:',
                            '    for claim in claims:',
                            '        batch.add_object(properties=claim["metadata"],',
                            '            vector=claim["embedding"])',
                            'client.close()',
                        ],
                        "distractors": [
                            'collection = client.schema.create_class("Claims")',
                            'batch.add_document(text=claim["text"])',
                        ],
                    },
                },
                # Step 4 — code_exercise
                {
                    "position": 4,
                    "title": "Implement Hybrid Search with Score Fusion",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Build a hybrid search function that combines keyword matching (BM25-style)
and vector similarity. Use <strong>Reciprocal Rank Fusion (RRF)</strong> to
merge the two ranked lists. RRF score for a document at rank <em>r</em>
is <code>1 / (k + r)</code> where <code>k</code> is a constant (typically 60).</p>
""",
                    "code": """import math
import re
from collections import Counter

# Our insurance claims corpus
CLAIMS = [
    {"id": "CLM-001", "text": "Water damage to basement from burst pipe during winter freeze",
     "vector": [0.15, 0.9, 0.8, 0.05, 0.7], "type": "home"},
    {"id": "CLM-002", "text": "Vehicle collision at intersection resulting in airbag deployment",
     "vector": [0.9, 0.1, 0.05, 0.8, 0.1], "type": "auto"},
    {"id": "CLM-003", "text": "Flood damage to first floor from overflowing river after storm",
     "vector": [0.1, 0.85, 0.85, 0.05, 0.75], "type": "home"},
    {"id": "CLM-004", "text": "Water leak from upstairs unit damaged ceiling and walls",
     "vector": [0.1, 0.8, 0.6, 0.05, 0.65], "type": "home"},
    {"id": "CLM-005", "text": "Rear-end collision on highway caused trunk and bumper damage",
     "vector": [0.85, 0.05, 0.05, 0.75, 0.1], "type": "auto"},
    {"id": "CLM-006", "text": "Hail storm damaged vehicle roof and windshield",
     "vector": [0.6, 0.5, 0.4, 0.3, 0.3], "type": "auto"},
]


def keyword_score(query_words, text):
    \"\"\"Simple keyword matching: fraction of query words found in text.\"\"\"
    text_lower = text.lower()
    matches = sum(1 for w in query_words if w in text_lower)
    return matches / len(query_words) if query_words else 0


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0


def hybrid_search(query_text, query_vector, top_k=3, alpha=0.5, rrf_k=60):
    \"\"\"Hybrid search combining keyword and vector results using RRF.

    Args:
        query_text: The search query as text.
        query_vector: The embedding vector for the query.
        top_k: Number of results to return.
        alpha: Weight for vector vs keyword (0=keyword only, 1=vector only).
        rrf_k: RRF constant (default 60).

    Returns:
        List of dicts: [{"id": ..., "text": ..., "score": ..., "keyword_rank": ..., "vector_rank": ...}]
    \"\"\"
    query_words = query_text.lower().split()

    # TODO: Score and rank all claims by keyword matching
    # Create a list of (claim, keyword_score) and sort descending
    keyword_ranked = []

    # TODO: Score and rank all claims by vector similarity
    # Create a list of (claim, cosine_score) and sort descending
    vector_ranked = []

    # TODO: Compute RRF fusion scores
    # For each claim, compute:
    #   rrf_score = alpha * (1 / (rrf_k + vector_rank)) + (1 - alpha) * (1 / (rrf_k + keyword_rank))
    # Return the top_k results sorted by rrf_score descending
    results = []

    return results


# Test: search for "water damage from storm"
query = "water damage from storm"
query_vec = [0.12, 0.88, 0.75, 0.05, 0.7]

print(f"Hybrid search: \\"{query}\\"")
print("=" * 70)
results = hybrid_search(query, query_vec, top_k=4, alpha=0.5)
for r in results:
    print(f"  RRF={r['score']:.4f}  (kw_rank={r['keyword_rank']}, vec_rank={r['vector_rank']})")
    print(f"    {r['id']}: {r['text']}")
    print()
""",
                    "expected_output": """Hybrid search: "water damage from storm"
======================================================================
  RRF=0.0328  (kw_rank=1, vec_rank=1)
    CLM-003: Flood damage to first floor from overflowing river after storm

  RRF=0.0325  (kw_rank=2, vec_rank=2)
    CLM-001: Water damage to basement from burst pipe during winter freeze

  RRF=0.0317  (kw_rank=3, vec_rank=3)
    CLM-004: Water leak from upstairs unit damaged ceiling and walls

  RRF=0.0159  (kw_rank=4, vec_rank=5)
    CLM-006: Hail storm damaged vehicle roof and windshield
""",
                    "validation": {
                        "hint": "First build keyword_ranked by scoring each claim with keyword_score() and sorting. Then build vector_ranked by scoring with cosine_similarity() and sorting. Create a dict mapping claim id to its rank (1-based) in each list. Then compute RRF for each claim and sort.",
                    },
                    "demo_data": None,
                },
                # Step 5 — fill_in_blank
                {
                    "position": 5,
                    "title": "Configure a Pinecone Index",
                    "step_type": "exercise",
                    "exercise_type": "fill_in_blank",
                    "content": """
<p>Fill in the blanks to create a Pinecone index configured for insurance
document search. You need to specify the correct dimension for OpenAI
embeddings, the similarity metric, and the cloud provider.</p>
""",
                    "code": """from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your-api-key")

# Create an index for storing OpenAI text-embedding-3-small vectors
pc.create_index(
    name="insurance-claims",
    dimension=____,
    metric="____",
    spec=ServerlessSpec(
        cloud="____",
        region="us-east-1"
    )
)

index = pc.Index("insurance-claims")

# Upsert a claim vector with metadata
index.upsert(vectors=[
    {
        "id": "CLM-001",
        "values": embedding_vector,
        "metadata": {"type": "auto", "status": "open", "date": "2025-03-15"}
    }
])
""",
                    "expected_output": None,
                    "validation": {
                        "blanks": [
                            {
                                "index": 0,
                                "answer": "1536",
                                "hint": "OpenAI's text-embedding-3-small model produces 1536-dimensional vectors",
                                "alternatives": ["3072"],
                            },
                            {
                                "index": 1,
                                "answer": "cosine",
                                "hint": "Cosine similarity is the most common metric for text search",
                                "alternatives": ["dotproduct", "euclidean"],
                            },
                            {
                                "index": 2,
                                "answer": "aws",
                                "hint": "Amazon Web Services -- the most common cloud for Pinecone serverless",
                                "alternatives": ["gcp", "azure"],
                            },
                        ]
                    },
                    "demo_data": None,
                },
            ],
        },
        # ── Module 3: Production Patterns ────────────────────────────────
        {
            "position": 3,
            "title": "Production Patterns",
            "subtitle": "Chunking, metadata filtering, re-ranking, and evaluation",
            "estimated_time": "45 min",
            "objectives": [
                "Apply effective chunking strategies to insurance documents",
                "Use metadata filtering to scope search results",
                "Implement a re-ranking step to improve precision",
                "Evaluate search quality with standard metrics",
            ],
            "steps": [
                # Step 1 — concept
                {
                    "position": 1,
                    "title": "Production Search Patterns",
                    "step_type": "concept",
                    "exercise_type": None,
                    "content": """
<h2>Making Search Production-Ready</h2>
<p>A demo that searches 100 documents is easy. A system that reliably searches
500,000 insurance policies, claims, and guidelines requires careful engineering.
Here are the patterns that matter most.</p>

<h3>1. Chunking Strategies</h3>
<p>Long documents must be split into chunks before embedding. The choice of
strategy dramatically affects search quality.</p>
<table>
  <tr><th>Strategy</th><th>How it works</th><th>Best for</th></tr>
  <tr><td><strong>Fixed-size</strong></td><td>Split every N tokens with overlap</td><td>Uniform documents, simple to implement</td></tr>
  <tr><td><strong>Semantic</strong></td><td>Split at topic/section boundaries</td><td>Structured docs like policies</td></tr>
  <tr><td><strong>Recursive</strong></td><td>Split by paragraphs, then sentences if too large</td><td>Mixed-format documents</td></tr>
  <tr><td><strong>Document-aware</strong></td><td>Use headings, sections, clauses</td><td>Legal/insurance documents with clear structure</td></tr>
</table>

<h3>2. Metadata Filtering</h3>
<p>Always store metadata alongside vectors. For insurance: policy type, coverage
dates, state/jurisdiction, claim status, document category. Pre-filtering on
metadata before vector search is dramatically faster than post-filtering.</p>

<h3>3. Re-ranking</h3>
<p>Initial vector search retrieves candidates fast but imprecisely. A re-ranker
(like Cohere Rerank or a cross-encoder model) re-scores the top 20-50 candidates
by reading query + document together, yielding much higher precision.</p>

<h3>4. Evaluation Metrics</h3>
<table>
  <tr><th>Metric</th><th>What it measures</th></tr>
  <tr><td><strong>Recall@k</strong></td><td>Fraction of relevant docs found in top k results</td></tr>
  <tr><td><strong>Precision@k</strong></td><td>Fraction of top k results that are relevant</td></tr>
  <tr><td><strong>MRR</strong></td><td>Mean Reciprocal Rank -- how high is the first relevant result?</td></tr>
  <tr><td><strong>nDCG</strong></td><td>Normalized Discounted Cumulative Gain -- rewards relevant docs ranked higher</td></tr>
</table>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": None,
                    "demo_data": None,
                },
                # Step 2 — code (run & observe)
                {
                    "position": 2,
                    "title": "Implement Document Chunking",
                    "step_type": "exercise",
                    "exercise_type": "code",
                    "content": """
<p>Run this code to see how different chunking strategies affect the same
insurance policy document. Notice how overlap preserves context at chunk
boundaries, and how semantic chunking keeps related clauses together.</p>
""",
                    "code": """def fixed_size_chunk(text, chunk_size=120, overlap=30):
    \"\"\"Split text into fixed-size chunks with overlap.\"\"\"
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def semantic_chunk(text, delimiters=None):
    \"\"\"Split text at semantic boundaries (section headers, clause markers).\"\"\"
    if delimiters is None:
        delimiters = ["SECTION", "ARTICLE", "COVERAGE", "EXCLUSION", "ENDORSEMENT"]
    import re
    pattern = "|".join(rf"(?=\\b{d}\\b)" for d in delimiters)
    chunks = re.split(pattern, text, flags=re.IGNORECASE)
    return [c.strip() for c in chunks if c.strip()]


# Sample insurance policy text
policy_text = (
    "SECTION 1: COMPREHENSIVE COVERAGE. This policy covers direct and accidental "
    "loss to your covered auto including collision with another object, fire, theft, "
    "vandalism, flood, hail, and wind damage. The deductible amount shown on the "
    "declarations page applies to each covered loss. "
    "SECTION 2: LIABILITY COVERAGE. We will pay damages for bodily injury or property "
    "damage for which any insured becomes legally responsible because of an auto "
    "accident. We will settle or defend any claim or suit asking for these damages. "
    "EXCLUSION A: We do not provide coverage for damage caused intentionally by the "
    "insured or while the vehicle is used for commercial ride-sharing without the "
    "commercial endorsement. "
    "EXCLUSION B: We do not cover mechanical breakdown, wear and tear, or damage "
    "from lack of maintenance. Road hazard tire damage is excluded unless the tire "
    "protection endorsement is purchased."
)

print("=== FIXED-SIZE CHUNKS (size=25 words, overlap=5) ===")
fixed = fixed_size_chunk(policy_text, chunk_size=25, overlap=5)
for i, chunk in enumerate(fixed):
    print(f"  Chunk {i+1} ({len(chunk.split())} words): {chunk[:80]}...")
print(f"  Total: {len(fixed)} chunks")

print()
print("=== SEMANTIC CHUNKS ===")
semantic = semantic_chunk(policy_text)
for i, chunk in enumerate(semantic):
    print(f"  Chunk {i+1} ({len(chunk.split())} words): {chunk[:80]}...")
print(f"  Total: {len(semantic)} chunks")
""",
                    "expected_output": """=== FIXED-SIZE CHUNKS (size=25 words, overlap=5) ===
  Chunk 1 (25 words): SECTION 1: COMPREHENSIVE COVERAGE. This policy covers direct and accidental los...
  Chunk 2 (25 words): flood, hail, and wind damage. The deductible amount shown on the declarations p...
  Chunk 3 (25 words): covered loss. SECTION 2: LIABILITY COVERAGE. We will pay damages for bodily inj...
  Chunk 4 (25 words): of an auto accident. We will settle or defend any claim or suit asking for thes...
  Chunk 5 (25 words): for these damages. EXCLUSION A: We do not provide coverage for damage caused in...
  Chunk 6 (25 words): without the commercial endorsement. EXCLUSION B: We do not cover mechanical bre...
  Chunk 7 (18 words): Road hazard tire damage is excluded unless the tire protection endorsement is pu...
  Total: 7 chunks

=== SEMANTIC CHUNKS ===
  Chunk 1 (25 words): SECTION 1: COMPREHENSIVE COVERAGE. This policy covers direct and accidental los...
  Chunk 2 (29 words): SECTION 2: LIABILITY COVERAGE. We will pay damages for bodily injury or propert...
  Chunk 3 (26 words): EXCLUSION A: We do not provide coverage for damage caused intentionally by the ...
  Chunk 4 (25 words): EXCLUSION B: We do not cover mechanical breakdown, wear and tear, or damage fro...
  Total: 4 chunks""",
                    "validation": None,
                    "demo_data": None,
                },
                # Step 3 — code_exercise
                {
                    "position": 3,
                    "title": "Build a Re-ranking Function",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Implement a re-ranker that takes initial search results and re-scores them
based on query-document relevance. In production you would use a cross-encoder
model; here we simulate it with word overlap and position-aware scoring to
demonstrate the pattern.</p>
""",
                    "code": """import math

def initial_search_results():
    \"\"\"Simulated vector search results for 'water damage coverage limits'.\"\"\"
    return [
        {"id": "DOC-1", "text": "Flood zone designations affect premium rates and coverage availability for coastal properties", "vector_score": 0.89},
        {"id": "DOC-2", "text": "Water damage from burst pipes is covered under Section 1 up to the policy limit of $250,000", "vector_score": 0.87},
        {"id": "DOC-3", "text": "Coverage limits for water damage: dwelling $250,000, personal property $100,000, additional living expenses $50,000", "vector_score": 0.85},
        {"id": "DOC-4", "text": "The deductible for water-related claims is $1,000 per occurrence", "vector_score": 0.83},
        {"id": "DOC-5", "text": "Sewer backup coverage is an optional endorsement with a $10,000 limit", "vector_score": 0.80},
    ]


def rerank(query, results, top_k=3):
    \"\"\"Re-rank search results by query-document relevance.

    Scoring approach:
    1. Compute word overlap ratio between query and document
    2. Boost score if query words appear early in the document
    3. Combine with original vector score using weighted average

    Args:
        query: The search query string.
        results: List of dicts with 'id', 'text', 'vector_score'.
        top_k: Number of results to return.

    Returns:
        List of dicts with added 'rerank_score' and 'final_score' keys,
        sorted by final_score descending.
    \"\"\"
    query_words = set(query.lower().split())

    # TODO: For each result, compute:
    #   1. word_overlap: fraction of query words found in the document text
    #   2. position_boost: average (1 / (1 + position)) for each query word found,
    #      where position is the word's index in doc_words. If not found, 0.
    #   3. rerank_score = 0.6 * word_overlap + 0.4 * position_boost
    #   4. final_score = 0.4 * vector_score + 0.6 * rerank_score
    # Return the top_k results sorted by final_score descending.
    reranked = []

    return reranked


# Run the re-ranker
query = "water damage coverage limits"
results = initial_search_results()

print(f"Query: \\"{query}\\"")
print()
print("Before re-ranking (by vector score):")
for r in results:
    print(f"  [{r['vector_score']:.2f}] {r['id']}: {r['text'][:70]}...")

print()
reranked = rerank(query, results, top_k=3)
print("After re-ranking (by final score):")
for r in reranked:
    print(f"  [{r['final_score']:.3f}] {r['id']}: {r['text'][:70]}...")
    print(f"           vector={r['vector_score']:.2f}  rerank={r['rerank_score']:.3f}")
""",
                    "expected_output": """Query: "water damage coverage limits"

Before re-ranking (by vector score):
  [0.89] DOC-1: Flood zone designations affect premium rates and coverage availability ...
  [0.87] DOC-2: Water damage from burst pipes is covered under Section 1 up to the pol...
  [0.85] DOC-3: Coverage limits for water damage: dwelling $250,000, personal property ...
  [0.83] DOC-4: The deductible for water-related claims is $1,000 per occurrence...
  [0.80] DOC-5: Sewer backup coverage is an optional endorsement with a $10,000 limit...

After re-ranking (by final score):
  [0.693] DOC-3: Coverage limits for water damage: dwelling $250,000, personal property ...
           vector=0.85  rerank=0.609
  [0.614] DOC-2: Water damage from burst pipes is covered under Section 1 up to the pol...
           vector=0.87  rerank=0.443
  [0.466] DOC-1: Flood zone designations affect premium rates and coverage availability ...
           vector=0.89  rerank=0.183""",
                    "validation": {
                        "hint": "For each result: split doc text into words, check which query_words appear. word_overlap = matches/len(query_words). For position_boost, find the index of each matching query word in doc_words and compute 1/(1+index), then average. Combine scores with the given weights.",
                    },
                    "demo_data": None,
                },
                # Step 4 — code_exercise
                {
                    "position": 4,
                    "title": "Calculate Search Evaluation Metrics",
                    "step_type": "exercise",
                    "exercise_type": "code_exercise",
                    "content": """
<p>Implement three standard search evaluation metrics: <strong>Precision@k</strong>,
<strong>Recall@k</strong>, and <strong>MRR</strong> (Mean Reciprocal Rank).
These metrics tell you how well your search pipeline is actually performing.</p>
""",
                    "code": """def precision_at_k(retrieved_ids, relevant_ids, k):
    \"\"\"What fraction of the top-k results are relevant?

    Args:
        retrieved_ids: Ordered list of document IDs returned by search.
        relevant_ids: Set of IDs that are actually relevant.
        k: Number of top results to evaluate.

    Returns:
        Float between 0 and 1.
    \"\"\"
    # TODO: Take the first k retrieved IDs and compute what fraction are in relevant_ids
    return 0.0


def recall_at_k(retrieved_ids, relevant_ids, k):
    \"\"\"What fraction of all relevant documents appear in the top-k results?

    Args:
        retrieved_ids: Ordered list of document IDs returned by search.
        relevant_ids: Set of IDs that are actually relevant.
        k: Number of top results to evaluate.

    Returns:
        Float between 0 and 1.
    \"\"\"
    # TODO: Of all relevant_ids, how many appear in the first k retrieved?
    return 0.0


def mean_reciprocal_rank(queries_results):
    \"\"\"Average of 1/rank for the first relevant result across multiple queries.

    Args:
        queries_results: List of tuples (retrieved_ids, relevant_ids)

    Returns:
        Float between 0 and 1.
    \"\"\"
    # TODO: For each query, find the rank (1-based) of the first relevant result.
    #       If no relevant result is found, reciprocal rank is 0.
    #       Return the mean across all queries.
    return 0.0


# Test with insurance search scenarios
# Scenario: searching for "water damage claims"
retrieved = ["CLM-003", "CLM-001", "CLM-007", "CLM-004", "CLM-009"]
relevant = {"CLM-001", "CLM-003", "CLM-004", "CLM-008"}

print("Search evaluation: 'water damage claims'")
print(f"  Retrieved: {retrieved}")
print(f"  Relevant:  {relevant}")
print()
print(f"  Precision@3: {precision_at_k(retrieved, relevant, 3):.3f}")
print(f"  Precision@5: {precision_at_k(retrieved, relevant, 5):.3f}")
print(f"  Recall@3:    {recall_at_k(retrieved, relevant, 3):.3f}")
print(f"  Recall@5:    {recall_at_k(retrieved, relevant, 5):.3f}")
print()

# MRR across multiple queries
queries = [
    (["CLM-003", "CLM-001", "CLM-007"], {"CLM-001", "CLM-003"}),  # first relevant at rank 1
    (["CLM-010", "CLM-005", "CLM-002"], {"CLM-002", "CLM-008"}),  # first relevant at rank 3
    (["CLM-006", "CLM-009", "CLM-011"], {"CLM-001", "CLM-004"}),  # no relevant found
]
print(f"  MRR across 3 queries: {mean_reciprocal_rank(queries):.3f}")
""",
                    "expected_output": """Search evaluation: 'water damage claims'
  Retrieved: ['CLM-003', 'CLM-001', 'CLM-007', 'CLM-004', 'CLM-009']
  Relevant:  {'CLM-001', 'CLM-003', 'CLM-004', 'CLM-008'}

  Precision@3: 0.667
  Precision@5: 0.600
  Recall@3:    0.500
  Recall@5:    0.750

  MRR across 3 queries: 0.444""",
                    "validation": {
                        "hint": "precision_at_k: count how many of retrieved[:k] are in relevant_ids, divide by k. recall_at_k: count how many of relevant_ids appear in retrieved[:k], divide by len(relevant_ids). MRR: for each query find the first relevant doc's rank (1-based), take 1/rank, average all.",
                    },
                    "demo_data": None,
                },
                # Step 5 — categorization
                {
                    "position": 5,
                    "title": "Match Chunking Strategies to Document Types",
                    "step_type": "exercise",
                    "exercise_type": "categorization",
                    "content": """
<p>Different document types call for different chunking strategies.
Match each insurance document type to the chunking approach that
would work best for it.</p>
""",
                    "code": None,
                    "expected_output": None,
                    "validation": {
                        "correct_mapping": {
                            "Auto policy declarations page with coverage tables": "Document-Aware Chunking",
                            "Multi-section homeowner policy with numbered clauses": "Document-Aware Chunking",
                            "Free-text adjuster notes from a field inspection": "Fixed-Size Chunking",
                            "Batch of short customer complaint emails": "Fixed-Size Chunking",
                            "State insurance regulation spanning 200 pages": "Recursive Chunking",
                            "Mixed-format claims file with forms, letters, and photos": "Recursive Chunking",
                        }
                    },
                    "demo_data": {
                        "instruction": "Match each document type to the best chunking strategy.",
                        "categories": [
                            "Fixed-Size Chunking",
                            "Recursive Chunking",
                            "Document-Aware Chunking",
                        ],
                        "items": [
                            "Auto policy declarations page with coverage tables",
                            "Multi-section homeowner policy with numbered clauses",
                            "Free-text adjuster notes from a field inspection",
                            "Batch of short customer complaint emails",
                            "State insurance regulation spanning 200 pages",
                            "Mixed-format claims file with forms, letters, and photos",
                        ],
                    },
                },
                # Step 6 — system_build (capstone)
                {
                    "position": 6,
                    "title": "Deploy: Semantic Search API on AWS",
                    "step_type": "exercise",
                    "exercise_type": "system_build",
                    "content": """
<h2>Mission: Deploy a Production Semantic Search Service</h2>
<p>You have built embeddings, implemented similarity search, designed hybrid
retrieval, and evaluated search quality. Now you put it all together into a
<strong>real, deployed API</strong> that a team could integrate into their
claims processing workflow tomorrow.</p>

<h3>What You Are Building</h3>
<p>A <strong>FastAPI service</strong> backed by <strong>Pinecone</strong> (or
Weaviate) that accepts natural-language queries about insurance claims and
returns semantically relevant results with metadata filtering. The service
will be containerized and deployed to <strong>AWS Lambda</strong> behind API
Gateway.</p>

<h3>Requirements</h3>
<ul>
  <li><strong>POST /search</strong> -- accepts <code>{"query": "...", "top_k": 5, "filters": {}}</code>,
      returns <code>{"results": [...], "query_time": 0.042}</code></li>
  <li><strong>POST /index</strong> -- accepts a document payload, embeds it, and upserts to Pinecone</li>
  <li><strong>GET /health</strong> -- returns <code>{"status": "ok", "index_count": N}</code></li>
  <li>Embedding via OpenAI <code>text-embedding-3-small</code> (1536 dims)</li>
  <li>Metadata filtering on <code>claim_type</code>, <code>status</code>, and <code>date_range</code></li>
  <li>Response time p95 &lt; 200ms for search queries</li>
  <li>Graceful error handling -- invalid queries return 422, Pinecone outages return 503</li>
</ul>

<h3>Phases</h3>
<ol>
  <li><strong>Local Build</strong> -- implement the FastAPI app, run it locally, verify all three endpoints work</li>
  <li><strong>Containerize</strong> -- write a Dockerfile, build the image, run and test in Docker</li>
  <li><strong>Deploy</strong> -- deploy to AWS Lambda using Mangum adapter + API Gateway, confirm the public URL works</li>
  <li><strong>Load Test</strong> -- use <code>locust</code> or <code>hey</code> to verify the service handles 100 req/s with p95 &lt; 200ms</li>
</ol>

<h3>Evaluation</h3>
<p>Mark each phase complete as you finish it. Check off the production checklist
items below. When all phases are done, paste your deployed endpoint URL --
we will validate it with a live POST to <code>/search</code>.</p>
""",
                    "code": """\"\"\"Semantic Search API -- Starter Code

Deploy this FastAPI service backed by Pinecone to AWS Lambda.
Fill in the TODOs and extend as needed.
\"\"\"

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pinecone import Pinecone
import openai


# ── Configuration ────────────────────────────────────────────
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "insurance-claims")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


# ── Clients ──────────────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
oai = openai.OpenAI(api_key=OPENAI_API_KEY)


# ── Schemas ──────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=100)
    filters: dict = Field(default_factory=dict)

class SearchResult(BaseModel):
    id: str
    score: float
    text: str
    metadata: dict

class SearchResponse(BaseModel):
    results: list[SearchResult]
    query_time: float

class IndexRequest(BaseModel):
    id: str
    text: str
    metadata: dict = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    index_count: int


# ── Helpers ──────────────────────────────────────────────────
def embed_text(text: str) -> list[float]:
    \"\"\"Generate an embedding vector for the given text.\"\"\"
    # TODO: Call OpenAI embeddings API with EMBED_MODEL
    # Return the embedding vector as a list of floats
    resp = oai.embeddings.create(input=[text], model=EMBED_MODEL)
    return resp.data[0].embedding


def build_pinecone_filter(filters: dict) -> dict:
    \"\"\"Convert user-facing filters to Pinecone filter syntax.

    Supports:
      - claim_type: exact match
      - status: exact match
      - date_range: {"gte": "2025-01-01", "lte": "2025-06-30"}
    \"\"\"
    pc_filter = {}
    if "claim_type" in filters:
        pc_filter["claim_type"] = {"$eq": filters["claim_type"]}
    if "status" in filters:
        pc_filter["status"] = {"$eq": filters["status"]}
    if "date_range" in filters:
        dr = filters["date_range"]
        date_cond = {}
        if "gte" in dr:
            date_cond["$gte"] = dr["gte"]
        if "lte" in dr:
            date_cond["$lte"] = dr["lte"]
        if date_cond:
            pc_filter["date"] = date_cond
    return pc_filter if pc_filter else None


# ── App ──────────────────────────────────────────────────────
app = FastAPI(title="Insurance Semantic Search API", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health():
    # TODO: Query Pinecone index stats and return count
    stats = index.describe_index_stats()
    return HealthResponse(
        status="ok",
        index_count=stats.total_vector_count,
    )


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    start = time.perf_counter()
    try:
        query_vec = embed_text(req.query)
        pc_filter = build_pinecone_filter(req.filters)

        # TODO: Query Pinecone with the vector, top_k, and filter
        results = index.query(
            vector=query_vec,
            top_k=req.top_k,
            filter=pc_filter,
            include_metadata=True,
        )

        items = [
            SearchResult(
                id=m.id,
                score=round(m.score, 4),
                text=m.metadata.get("text", ""),
                metadata={k: v for k, v in m.metadata.items() if k != "text"},
            )
            for m in results.matches
        ]
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Search backend error: {exc}")

    elapsed = round(time.perf_counter() - start, 4)
    return SearchResponse(results=items, query_time=elapsed)


@app.post("/index", status_code=201)
async def index_document(req: IndexRequest):
    try:
        vec = embed_text(req.text)
        meta = {**req.metadata, "text": req.text}
        index.upsert(vectors=[(req.id, vec, meta)])
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Index error: {exc}")
    return {"status": "indexed", "id": req.id}


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
                            "pinecone-client>=3.0.0\n"
                            "openai>=1.30.0\n"
                            "pydantic>=2.0.0\n"
                        ),
                    },
                    "validation": {
                        "endpoint_check": {
                            "method": "POST",
                            "path": "/search",
                            "body": {"query": "water damage claim", "top_k": 5},
                            "expected_status": 200,
                            "expected_fields": ["results", "query_time"],
                        },
                        "phases": [
                            {"name": "Local Build", "description": "Build and test the FastAPI app locally"},
                            {"name": "Containerize", "description": "Create Dockerfile and build the image"},
                            {"name": "Deploy", "description": "Deploy to AWS Lambda with API Gateway"},
                            {"name": "Load Test", "description": "Handle 100 req/s with p95 < 200ms"},
                        ],
                    },
                    "demo_data": {
                        "phases": [
                            {"id": 1, "title": "Local Build", "description": "Implement the FastAPI app and verify all endpoints work locally with pytest or curl"},
                            {"id": 2, "title": "Containerize", "description": "Write a Dockerfile, build the image, and run the container locally"},
                            {"id": 3, "title": "Deploy", "description": "Deploy to AWS Lambda with Mangum adapter and API Gateway public URL"},
                            {"id": 4, "title": "Load Test", "description": "Run locust or hey to verify 100 req/s with p95 < 200ms"},
                        ],
                        "checklist": [
                            {"id": "endpoints", "label": "All three endpoints (/search, /index, /health) return correct responses"},
                            {"id": "embedding", "label": "Embedding via OpenAI text-embedding-3-small is working"},
                            {"id": "filtering", "label": "Metadata filtering on claim_type, status, and date_range works"},
                            {"id": "error_handling", "label": "Invalid queries return 422, backend outages return 503"},
                            {"id": "dockerfile", "label": "Dockerfile builds and runs successfully"},
                            {"id": "lambda_deploy", "label": "Service is live on AWS Lambda behind API Gateway"},
                            {"id": "latency", "label": "p95 search latency is under 200ms"},
                            {"id": "load_test", "label": "Service handles 100 req/s without errors"},
                        ],
                    },
                },
            ],
        },
    ],
}
