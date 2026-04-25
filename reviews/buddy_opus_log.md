
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

