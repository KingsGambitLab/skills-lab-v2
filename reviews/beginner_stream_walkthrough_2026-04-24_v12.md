# Beginner Walkthrough — TypeScript v12: Types, Zod, API Clients
**Learner profile**: TypeScript beginner with some JS exposure, enrolled via catalog.
**Course URL**: http://127.0.0.1:8001/#created-bd2b52794db2
**Run date**: 2026-04-24

Course shape: 5 modules × 4 steps = 20 steps. "Intermediate" badge.
- M1 Type System Foundations (interface, type, satisfies)
- M2 Discriminated Unions & Exhaustive Matching
- M3 Type Derivations: Pick, Partial, Omit & Friends
- M4 Runtime Validation with Zod 3.24
- M5 Capstone: Typed fetchJson<T> with Result<T, ApiError>

---

## Step 1.0 — "Why Types Fail in Real Codebases" — concept
- Briefing clarity: 4/5 | ~2 min
- Tabbed widget (Approach 1 / 2 / 3) showing three broken PaymentProvider config attempts with the fix per tab.
- No submission; auto-complete on Next.
- Verdict: ✅ passed
- UI notes: Clean. "Compare All Three Approaches" button at the end — did not click (inferred content already delivered). Good intro hook.

## Step 1.1 — "Model a Feature-Flag Registry with satisfies" — code_exercise (TypeScript)
- Briefing clarity: 4/5 | ~6 min
- Starter: `FlagConfig` interface + `FLAGS = { } satisfies Record<string, FlagConfig>` + 3 throw-stubs.
- **Hint button toggles yellow but NO popup/tooltip renders on the page.** I clicked 💡 Hint repeatedly; no visible panel, no tooltip, nothing in any hidden container I could find in the DOM. A beginner relying on hints is effectively blocked.
- Attempt 1 (wrong, casual): one flag + lazy always-true stubs.
  - Score: 0%. Feedback: "0% on this attempt. 2 more retries before the full breakdown reveals. Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully."
  - **After submit, the page auto-advanced me to step 1.3 with the 0% banner shown there.** I had to manually go back to step 1.1.
  - Feedback helpfulness: NO. No mention of which function failed which test, no count of passed/total. A beginner has zero information to iterate from.
- Attempt 2 (proper): 3 flags + `name in FLAGS` guard + `Object.keys` lister.
  - Score: 100%. Feedback: "All 8 hidden tests passed in Docker (ts)."
- Verdict: ✅ passed
- UI notes: ❌ Hint button appears non-functional. ⚠ Auto-advance on wrong submit surprising.

## Step 1.2 — "interface vs type: Which for This API?" — categorization
- Briefing clarity: 4/5 | ~4 min
- 8 items, 3 bins (INTERFACE / TYPE ALIAS / EITHER WORKS).
- Attempt 1 (wrong, casual): all 8 in INTERFACE.
  - Score: 25% (2 correct · 6 wrong). Feedback: "25% on this attempt. 2 more retries before the full breakdown reveals. 6 of your responses did not match the expected answer."
  - Did this help? Partially — numerical count is informative (2/8), but doesn't name which are wrong.
- Attempt 2 (proper): interface = CustomerHealth + PluginConfig; type alias = ConfigValue + MetricName + HealthStatus; either = CustomerRecord + ApiResponse<T> + DatabaseError.
  - Score: 100% (8/8).
- Verdict: ✅ passed

## Step 1.3 — "Refactor: Collapse Parallel Definitions" — code_exercise ❌ STUCK
- Briefing clarity: 2/5 (briefing contradicts the starter) | ~8 min
- **P0 CONTENT BUG**: TypeScript course, but this step's starter + hidden tests are **Python**:
  - Language pill shows "python".
  - First line of starter: `// solution.ts - Kestrel Analytics User type consolidation` — comment says `.ts`, then next line is `from typing import Literal, TypedDict, Any`.
  - Body: `class User:`, `def make_user(...) -> User:`, `raise NotImplementedError('TODO: …')`.
  - Briefing talks about `readonly` tuples, `satisfies`, `expectTypeOf` — pure TypeScript vocabulary.
- Attempt 1 (legitimate TS solution following the briefing): full TypeScript with `as const`, `typeof USER_ROLES[number]`, `interface User { readonly ... }`, projection helpers, `export`.
  - Score: 0%. Feedback: generic "didn't match what the exercise expects".
  - This feedback is misleading and actively harmful — it tells me to "re-read the briefing and the starter code carefully" but the two are in different languages.
- Attempt 2 (Python solution matching the starter): Python `User` class, `make_user` factory, `user_to_row/dto/from_input` helpers.
  - Score: 100%. Feedback: "All 7 hidden tests passed in Docker (python)."
- Verdict: ❌ **stuck (beginner-hostile, P0 content bug)**. A real TypeScript beginner:
  1. Writes TS based on the briefing → 0% with generic feedback.
  2. Re-reads starter, sees Python, cannot reconcile with briefing → confused.
  3. Even if they recognize Python, they enrolled in a TS course — they don't know Python → give up.
- Root cause: Creator drifted language on this step. The course-level language invariant (`course_type = typescript → every code_exercise.language must be 'ts'`) isn't being enforced. Comment `// solution.ts` in the starter confirms the LLM was prompted for TS but emitted Python body — classic language-drift failure.

## Step 2.0 — "From Optional Fields to Tagged Unions" — concept
- Briefing clarity: 4/5 | ~2 min
- Story: 3AM crisis at Kestrel, mixed-bag `{ok?, error?, data?}` response causing runtime crashes. Refactored to `{kind: 'success', data: T} | {kind: 'error', error: E}`. Good before/after contrast.
- Interactive demo: Mixed Bag / Tagged Union toggle ("Click a button to see the difference"). Didn't deep-test the widget.
- Verdict: ✅ passed

## Step 2.1 — "Webhook Event Handler" — code_exercise ❌ language drift
- Briefing: discriminated union of webhook event types.
- Starter: Python (`from typing import Union, Literal`, `class PaymentSucceeded(TypedDict):`, `Union of the three types`).
- Did not re-attempt. Same P0 pattern as step 1.3. Marking as language-drift.

## Step 2.2 — "Exhaustive `assertNever` Pattern" — fill_in_blank (TypeScript)
- Briefing clarity: 4/5 | ~4 min
- 6 blanks in a TS switch+assertNever pattern. The displayed code is legitimately TypeScript.
- Attempt 1 (wrong, casual): junk values (`a`, `string`, `void`, `error`, `fail`, `x`).
  - Score: 0% (0 correct · 6 wrong). Feedback: generic "6 of your responses did not match."
- Attempt 2 (proper): `x`, `never`, `never`, `validation_error`, `server_error`, `response`.
  - Score: 100% (6/6). Feedback: "6/6 blanks correct. Blank 1: Correct Blank 2: Correct … Blank 6: Correct". **This IS the per-blank feedback a learner wants on failure too — but the grader only emits it on success.**
- Verdict: ✅ passed

## Step 2.3 — "Spot the Narrowing Bug" — code_review (TypeScript) ⚠ partial
- Briefing clarity: 3/5 | ~10 min
- Code rendered with a **visible double-blank-line issue between every source line** (known bug per CLAUDE.md "code_review alternate-line issue" backlog). Eyesight fatigue — the code reads roughly 3× taller than it should. Real bug to triage.
- Attempt 1 (wrong, casual): clicked line 1 (type declaration, obviously clean).
  - Score: 0% (0 correct · 1 wrong). But feedback said "6 of your responses did not match" — **display-copy drift**: the count is for an imagined per-item set, not the 1 line I actually clicked.
- Attempt 2 (3 candidate buggy lines 18, 20, 36): Score: 50% (3 correct · 1 wrong). But text below says "3 of your responses did not match" — the counter and the prose contradict each other.
- Attempt 3 (just 18 + 36): Score: 10% (1 correct · 5 wrong). Feedback finally reveals full answer: "Found 1/5 bugs. False positives on lines: [1] (-10% penalty) Missed bugs on lines: [18, 31, 36, 39]".
  - **The False-positive line 1 carry-over is a state bug**: I didn't click line 1 on attempt 3. The grader appears to be accumulating click state across attempts (or maybe clicking again untoggles — hard to tell).
  - The "10% (1 correct · 5 wrong)" label is again confusing: 5 bugs total, I hit 1, so 1/5 = 20%, minus 10% FP = 10%. The "(5 wrong)" only makes sense if it means "5 bugs you missed" — but that's not what "wrong" means. Counter-display copy is misleading.
- Verdict: ⚠ partial — solvable if you persist, but the grader's own reporting is confusing and the UI renders code in a visually-noisy alternating-blank-lines style.

## Step 3.1 — "Advanced Type Derivations" — code_exercise ❌ language drift
- Starter: Python (`from typing import TypedDict, NotRequired`, `from typing_extensions import Required`).
- Skipped attempt; same P0 language-drift pattern as 1.3/2.1.

## Step 3.2 — "Order the Derivation Pipeline" — ordering ⚠ partial
- Briefing clarity: 4/5 | ~5 min
- 6 items (Omit/Pick/Readonly/Brand/Validate/Export) to order as a type-derivation pipeline.
- Attempt 1 (reverse order, casual): Score: 33% (0 correct · 6 wrong). **Contradictory display**: 33% partial credit but "0 correct" — probably LCS-similarity scoring for positional, but the "0 correct" label is misleading.
- Attempt 2 (my best guess: omit, pick, readonly, brand, validate, export): Score: 83% (4 correct · 2 wrong). Feedback: generic "re-read".
- Attempt 3 (tried moving validate to front): Score: 83% **(0 correct · 6 wrong)** — the counter flipped to "0 correct" despite 83% score. **Counter display bug for ordering with partial-credit LCS.** Also the prose said "0/6 items in the correct position. Review the order and try again." — harsh for 83%.
- Verdict: ⚠ partial (hit 83% but counter displays wildly inconsistent numbers)

## Step 3.3 — "When NOT to Derive" — mcq
- Briefing clarity: 4/5 | ~3 min
- 4 options; correct = the messy multi-Omit+Pick chain coupling unrelated types.
- Attempt 1 (wrong, option 0 - Pick for dashboard): Score: 0% **(1 correct · 3 wrong)** — **display-copy bug for MCQ**: for a single-select radio, "1 correct · 3 wrong" doesn't make sense. Feedback prose: "4 of your responses did not match" — even more wrong (I submitted only 1 choice).
- Attempt 2 (right, option 1): Score: 100% **(0 correct · 4 wrong)** + "Correct!" banner. **Confirmed display-copy bug** — 100% says Correct, but "(0 correct · 4 wrong)" is nonsensical for a single-select. Backend logic OK; frontend label logic broken for MCQ.
- Verdict: ✅ passed (but the display copy for MCQ is clearly broken)

## Step 4.0 — "Zod at the Boundary, TS Inside" — concept
- Briefing clarity: 5/5 | ~3 min
- Strong concept: "trust zone" diagram, three validation boundaries (request body, external API, env vars). Well-written, no bugs, no drift.
- Verdict: ✅ passed

## Step 4.1 — code_exercise ❌ language drift
- Starter: `// solution.py\nfrom typing import Dict, Any, Union\nfrom dataclasses import dataclass\nfrom enum import …`
- Same pattern as 1.3/2.1/3.1. Skipped attempt.

## Step 5.2 — Capstone "fetch_json" — code_exercise ❌ language drift
- Starter: Python docstring `"""Kestrel Analytics — customer-health fetch_json capstone."""`, `class ApiError(Exception):`. The course-capstone, which is supposed to be "Typed fetchJson<T> with Result<T, ApiError>" in TS, is Python.

---

## SUMMARY

### Pass / stuck / partial tally by exercise type
| Type | Steps tried | Pass | Stuck (content bug) | Partial |
|---|---|---|---|---|
| concept | 3 | 3 | 0 | 0 |
| code_exercise (genuine TS) | 1 (M1.S1) | 1 | 0 | 0 |
| code_exercise (drifted to Python) | 5 sampled (M1.S3, M2.S1, M3.S1, M4.S1, M5.S2) | — | 5 | 0 |
| categorization | 1 | 1 | 0 | 0 |
| fill_in_blank | 1 | 1 | 0 | 0 |
| ordering | 1 | 0 | 0 | 1 |
| mcq | 1 | 1 | 0 | 0 |
| code_review | 1 | 0 | 0 | 1 |

### Beginner-hostile patterns (what would make me quit)

1. **P0 — language drift**: 5/6 code_exercise steps shipped as Python inside a TypeScript course. A TS-course learner could not solve any of these. This is THE course-breaking bug. Root cause: Creator failed to enforce the course-language invariant on code_exercise generation. The "// solution.ts" / "// solution.py" comment headers prove the LLM was prompted for one language and emitted another.
2. **P0 — wrong-answer feedback gives beginners zero iteration signal**: For code_exercise on wrong submission, the grader only says "didn't match what the exercise expects. Re-read the briefing." On a 0% score, no pass/fail count, no test name, no stderr excerpt. Contrast with the 100%-success message "All 8 hidden tests passed in Docker" — same precision on failure (e.g. "3/8 passed, 5 failed: test_returns_flags_list, test_throws_on_unknown_flag, …") would transform the teaching experience.
3. **P1 — per-item counter/prose display is inconsistent across exercise types**:
   - MCQ single-select shows "N correct · M wrong" on radios that only accept one choice.
   - Ordering shows "0 correct" on an 83% answer.
   - code_review shows "3 correct · 1 wrong" alongside prose saying "3 of your responses did not match".
   - A beginner would read these contradictions as "is the grader broken? do I know what I'm looking at?" and lose trust.
4. **P1 — Hint button appears non-functional** (at least on M1.S1 code_exercise): button visually toggles but no popup/panel/tooltip renders anywhere I could find in the DOM. A beginner who can't iterate from feedback and can't read hints is totally stuck.
5. **P2 — UI quirks**: auto-advance after wrong submit (jumps to a different step and shows the score there, learner has to navigate back); code_review code rendered with double-blank-lines between every source line (documented backlog bug, still live); no per-item feedback on success-only categorization (it says 8/8 but doesn't echo which item mapped to which category — useful for celebrating, less for teaching).

### What worked well
- **Concept steps were genuinely good** — scenario hook (Marcus Chen at Kestrel Analytics), narrative continuity across modules, realistic code examples (payment providers, webhook events, `fetchJson`), interactive tabs + toggles. If the code_exercises matched this quality, the course would be strong.
- **The one real TS exercise (M1.S1) was well-designed** — satisfies operator, clear TODO structure, 8 hidden tests, Docker (ts) runtime. Exactly what the course title promises.
- **fill_in_blank on M2.S2 had genuine TypeScript content** (assertNever pattern with `never` type, switch narrowing). The exercise teaches.
- **Feedback ON SUCCESS is good** — "All N tests passed in Docker (ts)" is precise and confidence-inspiring.

### Would I push through as a real learner?
**No.** I'd hit step 1.3 (the Python-in-TS-course exercise) after clearing 1.1 and 1.2, submit TS, get a generic 0%, re-read the starter, see Python, conclude the course is broken, and quit. Even if I pushed past, I'd hit 4 more of the same in subsequent modules. 5 of 8 code_exercises being language-drifted makes the course unfit for learner shipping.

### Verdict: ❌ REJECT

Root causes to fix before re-running gate:
1. **Enforce course-language invariant at Creator / _is_complete level**: for a `typescript` course, every `code_exercise.demo_data.language` must be `ts`; every starter must be syntactically TypeScript (reject if `from typing import` / `def ` / `class X(TypedDict)` / `raise NotImplementedError` etc. appears).
2. **Enrich wrong-answer grader response** for code_exercise from "didn't match" to per-test pass/fail names (the Docker runner already emits this; it's upstream data being dropped at the frontend render).
3. **Fix per-item counter/prose consistency** for MCQ (don't render "N correct · M wrong" for single-select), ordering (LCS partial credit shouldn't label "0 correct"), code_review (align counter label with prose).
4. **Fix or remove the 💡 Hint button** in `code_exercise` template — either wire up the tooltip/panel, or hide it if `validation.hint` is empty.
5. **Regenerate the course** after (1) lands to prove the TS runtime gets every code_exercise. Don't patch steps 1.3/2.1/3.1/4.1/5.2 in-place — fix the Creator invariant and regen.

### Tool-call budget
Used ~120 tool calls across 10+ step explorations. Coverage: every exercise type in the course (concept, code_exercise, categorization, fill_in_blank, ordering, mcq, code_review) plus language-drift pattern confirmed across all 5 modules.
