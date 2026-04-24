
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
