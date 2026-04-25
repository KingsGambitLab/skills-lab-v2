
---

## 2026-04-24 — Consult #10: TS capstone attractor persists despite 9 fixes

### Brief (what I sent)

TS `code_exercise` "Ship fetchJson<T>" cannot pass the solution/starter invariant. 20+ retry attempts across 5 regen runs (v16→v20) with escalating fixes: contrastive exemplar, Phase D compiler grounding, retry-order Sonnet→Opus, aggressive dict coerce, partial-JSON coerce, 16k max_tokens, flat tool_use schema. All hit TS2339 (`result.error` access without `if (!r.ok)` guard).

Key data: Opus at attempt 3 ALSO failed with the attractor, confirming it's not a capability issue.

### Opus's verdict (abridged)

**"Contrastive exemplars are ~5 tokens of counter-signal against billions of tokens of prior. You cannot out-prompt this; you must remove the decision from the LLM."**

4 root-cause hypotheses (ranked):
1. **Task shape IS the attractor** — test-writing "assert error details" has overwhelming prior for unguarded `.error`
2. **Single tool_use conflates solution + tests** — attention splits; tests fall to cached patterns
3. **Feedback-induced anchoring** — longer feedback containing the failing code re-primes the attractor
4. **Temperature>0 variance** — lucky passes are noise, not signal

**Recommendation: Ship `expectErr`/`expectOk` helpers in starter code.**

```typescript
export function expectErr<T, E>(r: Result<T, E>, check: (e: E) => void): void {
  expect(r.ok).toBe(false);
  if (!r.ok) check(r.error);
}
```

Then brief adds: "Tests MUST use `expectErr`/`expectOk`; direct `.error`/`.data` access is forbidden." Architecturally neutralizes the attractor.

### Opus's "don't do yet" list

- More exemplar tuning (diminishing returns)
- Split-generation (do ONLY if helpers don't hit >90%)
- Post-gen AST check (belt-and-suspenders — add AFTER helpers ship)

### False assumptions flagged

- "v17 attempt 0 worked → prompt close" → n=1 at temp>0 is NOISE. Base rate ~20%.
- "Bigger feedback helps" → OPPOSITE: v18+ regressions followed feedback growth.
- "Opus will rescue Sonnet's failures" → Attempt 3 disproves this. Attractor ≈ model-independent when task shape triggers it.

### Cost

~$0.10 for the Opus consult. Saved me another $20+ of exemplar-engineering roulette.

### Adoption

- [ ] **SHIP** — Add `expectErr`/`expectOk` helpers to the TS runtime-deps brief as mandatory imports for any Result<T,E> exercise
- [ ] **SHIP** — Update brief to forbid direct `.error`/`.data` access; require helpers
- [ ] **SHIP** — Regenerate TS capstone with helpers in starter
- [ ] **PARK** — Split-generation (measure pass rate after helpers first)
- [ ] **PARK** — Post-gen AST check (safety net, later)

### Key lesson for future

**When 4+ attempts hit the same attractor with progressively bigger prompt hammers, the task shape is wrong — not the prompt.** Change the task API (encapsulate the decision in a helper), don't tune the prompt harder.

### Result — CONVERGED on attempt 0

v24 (post-Opus recommendations shipped):
- Flat tool_use schema ✓
- Verbatim `expectErr`/`expectOk`/`isResultOk` helpers in TS brief ✓
- Language-agnostic malformed-JSON regex recovery in reshape ✓

**Attempt 0 converged.** Capstone step 84992 now has:
- 3658 chars clean `solution_code` (no if-guards needed — helpers encapsulate)
- 3737 chars `hidden_tests` using helpers (8× expectErr, 2× expectOk)
- 0 unguarded `.error` / `.data` access
- quality_flag: None (not dead-lettered)

Total cost of consult + implementation + retry: ~$4 (as Opus predicted).

Lesson validated: **"Contrastive exemplars are ~5 tokens of counter-signal against billions of tokens of prior. You cannot out-prompt this; you must remove the decision from the LLM."** Encapsulation kills the attractor.

### Side win: language-agnostic reshape recovery

The malformed-JSON regex recovery (`_unstringify` in `_reshape_flat_code_exercise`) is GENERIC — works for any language because the field names (`hidden_tests`, `solution_code`, `must_contain`, `requirements`, `hint`, `language`) are language-agnostic. Future LLM truncation / escape-bugs in any language's code_exercise will benefit.

---

## 2026-04-25 — surface classification (web vs terminal)

### Brief

Concept-shaped step (Kimi M0.S1, id=85138) with `<style>` + `<script>`
widget content classified as `learner_surface=terminal` in DB. CLI then
routed the learner into a paste-flow for a step that's purely a browser
widget. Old classifier checked only `<script>`; resolver honored declared
LLM value over the classifier for non-structural exercise types.

### Question to Opus

Three options:
- (A) run the renderer's stripper, classify by what survives
- (B) renderer manifest of supported features, mechanically derive
- (C) ban free-form HTML in concept content, force registered slide types
- (4th) don't store surface at all, derive on read

### Verdict

Opus: **A's mechanism + 4th's framing**. Run the stripper (single source
of truth), make surface DERIVED from `(exercise_type, content)` rather
than stored/declared. C is v9 north-star (too disruptive now). B is the
right invariant; A is the right implementation per §EXECUTION IS GROUND
TRUTH (don't enumerate, observe).

### What landed

- Created `backend/markdown_strip.py` — canonical browser-only stripper.
- Updated `_resolve_learner_surface` to drop "honor declared values" path.
- v4 classifier briefly used the renderer-derived approach.
- **User overrode v4 with a much simpler rule (v5)**: `terminal_exercise`
  → terminal, `system_build`+GHA → terminal, else → web. The user's
  insight: surface follows GRADING SHAPE, not look-and-feel.
- Backfilled all 85,166 steps with the v5 rule. 15 transitioned terminal
  → web (concept widgets that were misclassified).
- Step 85138 now correctly = web.

### Adopted from Opus

- The "stop trusting LLM-declared surface; the runtime is the source of
  truth" framing.
- The shared `markdown_strip.py` module — kept for the renderer's own
  use even though v5 doesn't consult it for classification.
- §EXECUTION IS GROUND TRUTH discipline: run, don't enumerate.

### Net

Buddy-Opus consult was useful for framing (drop declared, use runtime
truth) but the user's directive simplified the implementation
substantially. The renderer-derived approach was correct in principle
but flapped on minor styling drift. The v5 grading-shape rule is robust
because it depends only on shapes the system explicitly emits
(exercise_type + validation keys), not on prose-content the LLM
generates freely.


---

## 2026-04-25 (overnight) — Kimi + Claude Code (AIE) iterated to SHIP

### User directive
*"Make claude and kimi courses pass both user testing and expert testing. For both, make sure they attempt and solve each assignment, web + terminal. User agent should open up a terminal and solve as is. Do this till you exhaust total $450 USD, OR if you fix everything perfectly. Keep iterating till you fix everything."*

### Iterations

**v5 round 1 — REJECT both courses**:
- Kimi beg: REJECT (9 P0s) — broken capstone pyproject, M4/M5 hallucinated repo + missing harness files, npm-vs-Python MCP, invented MCP tool names, tests-path drift across 3 steps, must_contain too lax against pytest.fail starter
- Kimi sr: SHIP-WITH-FIXES (1/2) — duplicate bugs[] line, missing pydantic_idempotency briefing
- AIE beg: REJECT (6 P0s) — hallucinated `skillslab-xyz/techtickets-broken`, scenario_branch grader broken, missing branches, fictional CLI flags
- AIE sr: REJECT (11 P0s) — async-fixture bug breaks half the course's CI, 6 hallucinated repos/branches/npm, 4 fictional CLI subcommands, wrong MCP wiring schema

**v5 round 1 fixes** (in commit `ff13bba` + repo pushes + commit `174eea8`):

13 step regens with explicit ground-truth feedback:
  AIE: 85061, 85067, 85070, 85074, 85075, 85082, 85083, 85086
  Kimi: 85148, 85151, 85155, 85159, 85161 (+ already-fixed 85163-85166)

3 repo fixes:
  - tusharbisht/aie-course-repo: pyproject.toml asyncio_mode=auto on
    6 module branches (unblocked M1-M4 CI)
  - tusharbisht/aie-course-repo: 2 missing branches created
    (health-endpoint-challenge + module-6-final)
  - tusharbisht/kimi-eng-course-repo: hatch wheel packages=['app']
    on 6 module branches (unblocked M6 capstone CI)
  - tusharbisht/jspring-course-repo: lab-grade.yml propagated to all
    6 non-capstone branches

1 frontend bug fix:
  - scenario_branch grader: `_strip_item_result` was dropping
    explanation + label fields. Frontend rendered green/red color
    but no rationale. Added `explanation` + `label` to strip
    safe-list (gate already filters to user-picks-only, so no
    answer-key leak risk).

**v6 verification — both SHIP**:
- Kimi v6: SHIP (10/10 P0s closed, 0 new P0s)
- AIE v6: SHIP-WITH-FIXES (11/11 P0s closed; 2 minor P1s flagged)

**Round 2 closure** (in commit `c1a10e2`):
- 85114 (jspring M1.S1 com.crateflow x2 fictional package) — regen
  with canonical com.tusharbisht.jspring. 0x crateflow refs in DB now.
- 85086 (AIE M7.S5 fictional settings.json keys default_agent +
  permissions.file_operations.*) — regen with REAL Claude Code keys
  (hooks.PreToolUse with matcher+command, permissions.allow/deny
  glob arrays).
- AIE branch-rename drift (module-3-config → module-3-iterate,
  module-5-ci → module-5-team) — SQL grep across all step content
  found ZERO references to old names. P1 closed by absence.

**Structural prevention layer** (commit `c1a10e2`):

`_course_repo_facts(course_title)` injects per-course CANONICAL state
into the Creator prompt. Three sections per course:
  1. Canonical repo URL + valid branches (from course_assets registry)
  2. Key file paths + real test function names (hardcoded for the
     3 CLI courses; stable surface)
  3. NEVER reference catalog — accumulated registry of past
     hallucinations. Each entry was a real bug caught by reviewers
     (skillslab-xyz/techtickets-broken, @skillslab/team-tickets-mcp,
     claude --list-agents, test_create_ticket_with_priority,
     app/schemas/*, ...). Adding to this list prevents future regens
     from re-emitting the same hallucination.

Robust slug matching with priority-ordered tokens (jspring tokens
first since "Claude Code for Spring Boot" matches both jspring and
claude-code; jspring is the semantic owner).

### Budget
Started: $311.97 spent / $450 cap → $138 remaining
Ended:   $313.43 spent / $450 cap → $137 remaining
Net:     $1.46 burnt across ~25 LLM calls (regens + verifier sniff
checks). Well within budget; no need to stop.

### Net delivered
- 2 courses moved from REJECT → SHIP-class via 1 round of fixes
- 13 step regens + 4 repo fixes + 1 frontend fix
- Hallucinated-URL prevention layer shipped (preventive, structural)
- 2 commits to origin/main: ff13bba, 174eea8, c1a10e2
- 4 v6 verifier artifacts streamed + persisted

