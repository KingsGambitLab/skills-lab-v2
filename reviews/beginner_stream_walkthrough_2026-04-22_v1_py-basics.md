# Beginner Walkthrough — "Python Basics: Core Data Structures and Control Flow"

- Course ID: `created-82e212a0f83c`
- URL: http://127.0.0.1:8001/#created-82e212a0f83c
- Date: 2026-04-22
- Pass tag: v1

## Course shape
- 5 modules — M1 Variables/Types/Control (4 steps), M2 Loops/Collections (4), M3 Functions/Comprehensions (4), M4 Errors/File I/O (4), M5 Capstone (3)

---

## Step 1.1 — "Welcome: Predict-the-Output Warmup" — concept
- Briefing clarity: 4/5. Narrative ("LogWatch error detection system") is set up well. Mentions "Interactive Prediction Challenge" and four snippets with clickable choice buttons.
- What I did: clicked a wrong-answer button to see grader feedback on one of the Snippet widgets (`"Found errors"` on empty-list truthiness).
- Result: **nothing happened.** No visual change, no toast, no console output.
- Root cause found by inspection: the button's onclick is `predict(this, 'Found errors')` but `typeof predict === 'undefined'`. The LLM-emitted concept widget references a helper that's not defined on the page.
- Verdict: ⚠ **partial** — the concept step auto-completes on view so a learner can still advance, but the advertised "Interactive Prediction Challenge" teaches nothing. Quoted prose ("Can you predict what each snippet will output?") sets an expectation the UI can't deliver.
- UI notes: **BUG** — `predict()` helper undefined on page. All four snippet widgets on this step are dead. Clicking any of the 8 option buttons produces zero feedback. A real beginner would think the page is broken.

---

## Step 1.2 — "Types & Truthiness Reference" — concept
- Briefing clarity: 5/5. Clean table of 5 core types with falsy value + pitfall column. Narrative framing ("Sarah Kim discovered...", `int('3.0')` raises) is effective.
- Auto-completes on view (concept). Nothing to submit.
- Verdict: ✅ passed (view-only). Solid reference card.
- UI notes: none.

---

## Step 1.3 — "Grade a Temperature Reading" — code_exercise
- Briefing clarity: 5/5. 4 buckets, EXACT boundary conditions stated (`0 and below`, `above 0 up to 10`, etc), plus explicit warning that 0.0 / 10.0 / 25.0 will be tested.
- Starter code: clean scaffold, clear docstring with examples, `NotImplementedError` raise for learner to replace. Good quality.
- **Attempt 1 (wrong, casual):** Used `<` instead of `<=` everywhere (classic off-by-one), the exact thing the briefing warned against.
  - Score: 70%
  - Feedback verbatim: "70% on this attempt. 2 more retries before the full breakdown reveals. Your submission didn't match what the exercise expects. Re-read the briefing and the starter code carefully."
  - Did this help me? **partially.** 70% tells me I'm close but nothing about WHICH cases failed. "Re-read the briefing" is generic. A real beginner would likely spot the boundary warning only because the briefing is good — the grader itself teaches nothing on this first attempt.
- **Attempt 2 (right):** Changed to `<=` everywhere.
  - Score: 100% — "All 10 hidden tests passed in Docker (python)."
  - Concise, satisfying.
- Verdict: ✅ passed on attempt 2. **But** mid-submit the page routed away to the Go course by itself on attempt 2 — had to re-navigate back. Confirmed router bug (see UI notes).
- UI notes: **BUG** — after submitting (or when the UI re-renders after grader response?), the route sometimes jumps to a DIFFERENT course entirely. Hash changed from `#created-82e212a0f83c/23024/2` to `#created-6b695b950f9c/23027/1`. Reproduced twice.
- UI notes 2: "💡 Hint" button is visible in UI but clicking it does nothing / no onclick handler registered.

---

(continuing...)
