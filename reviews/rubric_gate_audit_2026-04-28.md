# Rubric-Gate Retroactive Audit — 2026-04-28

## Context

User directive (verbatim, 2026-04-28): *"Deprecate this type of judge from
the evaluation ontology, writing observations is a poor way to evaluate."*

This audit ran the just-deployed hardened validator gate (Track A
`_track_a_check_rubric_no_subjective_grading` + Opus's whitelist signal:
"rubric MUST reference at least one captured-output marker") retroactively
over every `terminal_exercise` step in prod.

Per Buddy-Opus's verdict (2026-04-28): the audit is the gating artifact —
it tells us (1) how leaky the gate is, (2) the exact migration scope for
Option C, (3) what patterns are missing from `_DEPRECATED_RUBRIC_PATTERNS`.

## Summary

| Metric | Count | % |
|---|---|---|
| Total `terminal_exercise` steps in prod | 43 | 100% |
| Without `validation.rubric` field | 1 | 2% |
| With rubric — PASS clean | 25 | 58% |
| With rubric — **FAIL deprecated pattern** | **1** | **2%** |
| With rubric — FAIL no-captured-output ref | 16 | 37% |

## Findings

### F1: 1 step with explicit deprecated patterns (the migration scope)

**Step 85115** (jspring `created-e54e7d6f51cf` M2.S2) — 4 deprecated hits:
- `observations.txt` → deprecated deliverable
- `documenting Claude's style` → subjective grading on documenting LLM behavior
- `style-observations.txt` → deprecated deliverable
- `your observations` (implicit via documenting + meaningful)

This is the same step the v7 reviewer + the M1.S2 walkthrough already
flagged. Today's earlier regen sweep didn't fully clean it. **Re-regen
triggered under the hardened gate (with the above feedback as the retry
prompt) — see /api/courses/created-e54e7d6f51cf/steps/85115/regenerate
result.**

### F2: 16 steps fail Opus's whitelist but are pedagogically OK

Spot-check of the 16 "no captured-output reference" failures shows they
mostly say things like:
- "The output should show Ruby 3.3+ version, Rails 8.x version, the chirp project files exist..."
- "The output should show a successful analysis run..."

These DO grade on captured tool output — they just don't use the regex-
matched literal words ("stdout", "exit code", "git diff", "pytest", etc.).
**My captured-output whitelist regex is too narrow.** This is a measurement
bug, not a content bug.

**Action**: extend the whitelist to include:
- Language-version markers: `<lang> [\d.]+`, `version`, `installed`
- File-existence markers: `file(s) exist`, `directory contains`, `project files`
- Generic execution markers: `successful run`, `analysis run`, `script generates`

### F3: Mutation suite is the right gate; Track A blacklist alone catches the disease

**Only 1 step out of 43 actually carried the deprecated patterns.** The
mutation suite (10/10 PASS post-deploy) catches MUT-1..8 deterministically.
The validator deploy is sufficient for the bug class as it stands today.

## Verdict — what to ship next (in priority order)

1. ✅ **DONE** — Re-regen step 85115 under the hardened gate with feedback
   payload listing the deprecated patterns + redirect to objective grading.
2. **NEXT** — Loosen `_CAPTURED_OUTPUT_MARKERS` regex to include language-
   version / file-existence / execution-success markers. Re-run the audit.
   Target: 0 false-positives in the no-captured-output bucket.
3. **NEXT** — Per Opus, flip the ontology gate (Option C): remove
   `llm_rubric` from `terminal_exercise` / `system_build` / `code_exercise`
   `grade_primitives` whitelist in `backend/ontology.py`. Force
   `must_contain` / `hidden_tests` / `gha_workflow_check` /
   `cli_command.expect`. Migration cost: 1 regen (step 85115) since the
   other 42 steps already grade on objective signals.
4. **DEFERRED** — Audit `code_read` rubrics (Opus flagged: most
   `code_read` steps grade comprehension prose, which is the exact
   anti-pattern; current ontology lists `code_read` as `llm_rubric`-only).
   This is a separate audit pass — not the hot path today.

## Why this matters (per CLAUDE.md North Star)

Subjective-observation grading was the #1 source of false-positive grades
in the 2026-04 cohort. A learner who didn't actually run pytest could
score 60-100% by writing convincing-sounding "observations" prose. The
gate-time + emit-time + ontology-gate triple lock makes the bug class
structurally impossible to ship, not just hard to catch.

## Validator stack (post-2026-04-28)

```
LLM emits step candidate
    │
    ▼
[Track A blacklist] _track_a_check_rubric_no_subjective_grading
    │ — 14 deprecated patterns; mutation suite proves catch
    ▼
[Track A facts] gh-api / class-name / CLI-flag / GHA-job verification
    │
    ▼
[Track B] token substitution: branch keys ≠ branch values
    │
    ▼
[Ontology gate (NEXT)] llm_rubric forbidden for objective exercise types
    │
    ▼
DB persist + serve to learner
```

The Track A blacklist is the bug-class seal. The Ontology gate (Option C)
is the structural eradication. Both ship — A first (already done),
C next session.

## References

- `backend/output_validator.py` — Track A + B implementation
- `tools/test_mutation_suite.py` — 10/10 PASS regression seal
- `backend/ontology.py:367-401` — terminal_exercise grade_primitives
- Audit script: `/tmp/audit_terminal_rubrics.py` (re-runnable on prod)
- Raw audit JSON: `/tmp/rubric_audit_2026-04-28.json`
