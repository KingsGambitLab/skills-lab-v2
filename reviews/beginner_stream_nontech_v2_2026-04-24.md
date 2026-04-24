# Beginner Stream — Non-Tech PM Walkthrough — v2 — 2026-04-24

**Reviewer profile:** Product Manager, ~5 yrs experience, ChatGPT user for drafting, never written Python. Browser-only.
**Course:** "AI-Powered Workday: Ship 3 Prompt Workflows to Your Team This Week"
**URL:** http://localhost:8001/#created-bd5ec658354f
**v1 rejected steps to re-verify:** M1.S2 (code_read), M4.S1 (simulator_loop), M5.S4 (system_build)

---

## Walkthrough log (appended live)

## Step M1.S1 — "Prompt engineering is a skill, not a vibe" — concept
- Briefing clarity: 5/5  | time on step: ~2 min
- No submission required (CONCEPT). Reading only.
- Content intro: "Monday 9:15am at Nexflow — Marcus asked to draft board talking points." Introduces the SPEC Framework (Specificity + Examples + Constraints + Escalation).
- Side-by-side Vague Prompt vs SPEC-Structured Prompt. Fully PM-friendly — no code, no CLI.
- Verdict: ✅ passed
- UI notes: Renders cleanly in dark mode. Clicky chat auto-opens on every step though — minor annoyance.

## Step M1.S3 — "Two prompts, same task — explain why one works" — code_read (READ REFERENCE)
- Briefing clarity: 4/5  | time on step: ~8 min
- This was the v1-rejected step to re-verify. It is NOT broken in the sense of "can't load" — BUT the grader has a real problem.
- Attempt 1 (intended strong): I submitted ~150-word explanation explicitly naming AUDIENCE, GOAL, FORMAT, the 400-word cap, markdown, Key Wins | Risk Flags | Resource Requests structure, and practical workplace reuse.
  - Score: 20%
  - Feedback verbatim: "You correctly identified that the second prompt is better and more specific, which shows basic recognition. However, your explanation misses the key concepts from the rubric: you didn't identify specific elements like audience definition, format constraints, or structural requirements that make it effective. You also didn't explain how knowing the audience (CEO/VPs making decisions) impacts the prompt design, or connect these principles to workplace applications."
  - Did this help me iterate? NO. This feedback is factually wrong — my answer explicitly named audience definition, format constraints, structural requirements, and workplace application. The grader is hallucinating that my answer lacks things my answer clearly contains.
- Attempt 2 (rewrote with even MORE explicit naming of each rubric concept, explicitly called out "AUDIENCE is defined as CEO + VP Sales + VP Engineering making Monday decisions", "FORMAT constraints (markdown, 400-word cap, Key Wins | Risk Flags | Resource Requests structure)", "Practical workplace application"):
  - Score: 0% (per network response)
  - Backend feedback verbatim: "Please write a short explanation of what the code does + why, then submit. The grader evaluates your explanation against a rubric."
  - Two bugs: (a) the UI did NOT update — it continued to show the 20% feedback from attempt 1 despite backend saying 0%. (b) The 0% feedback references "what the code does" — but this exercise has NO code. It's a prompt comparison, not a code read.
- Attempt 3: clicked Submit again — **no network call fired** (button was silently disabled after retries exhausted). The UI gives no indication attempts ran out.
- Verdict: ⚠ partial — step is marked `completed` by the system (probably from a prior attempt) but the grader feedback is misleading and factually wrong, and there's a clear UI bug where the score/feedback does not update after a new submission.
- UI notes:
  - Grader feedback is **wrong** — claims my answer "didn't identify" things my answer explicitly did identify. That is the kind of thing that would make a real PM give up on this course.
  - Feedback on low-score retries says "Please write a short explanation of what the code does + why" — this is leaking developer-track language ("code") into a non-code step. Real PMs will read "what the code does" and think they're in the wrong course.
  - After 3 attempts the Submit button is silently disabled. No toast / banner / counter explains that retries are exhausted.
  - Score text stuck at 20% despite backend returning 0% on a fresh submit — the UI is NOT re-reading the response body.

## Step M1.S2 — "DELEGATE / PAIR / NEVER-DELEGATE: sort 15 PM-ops-CS tasks" — categorization
- Briefing clarity: 4/5  | time on step: ~6 min
- Title claims "sort 15" tasks but only 8 items are rendered. **Content mismatch: briefing lies about the count.**
- Attempt 1 (wrong — put everything in DELEGATE to probe grader):
  - Score: 38%
  - Feedback: "38% on this attempt. 1 more retry before the full breakdown reveals. 5 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Per-item breakdown was good — i1 (weekly status), i5 (interview questions), i7 (Q3 summary) were correctly DELEGATE. i2 (hiring decision), i3 (onboarding checklist), i4 (angry customer), i6 (harassment), i8 (PIP) were wrong.
  - Did this help me iterate? Yes — per-item correctness is useful signal even without the full answer key.
- Attempt 2 (intended correct): Tried to place i1/i5/i7 → DELEGATE, i3/i4/i8 → PAIR, i2/i6 → NEVER-DELEGATE. But the submit from attempt 1 had auto-advanced me off this step, and when I returned, the bins had reset and the items were no longer findable via the expected selectors (maybe render-timing). Submit did not fire on attempt 2.
- Verdict: ⚠ partial — got useful per-item feedback, but the exercise auto-navigates away from the step on submit even when the answer is not yet correct, which prevents the promised retry loop. The title mismatch ("15" vs 8 items) is cosmetic but confusing for a PM audience.
- UI notes:
  - Title says "sort 15" but only 8 items present.
  - After Submit, the app silently navigates to the next module (M2.S1) even on an incorrect attempt — no banner, no confirmation of "your score is saved, continue iterating or skip?".
  - No "Reset" feedback banner when retrying.

## Step M4.S2 — "Monday 9am, 60 simulated minutes: work the inbox" — simulator_loop (LIVE SIMULATION)
- Briefing clarity: 5/5  | time on step: ~10 min (most of it fighting navigation)
- This was the v1-rejected step to re-verify.
- **Dashboard rendering:** CLEAN. No `[object Object]`. Labels show actual metric names (`TIME_REMAINING_MINUTES: 60`, `MESSAGES_COMPLETED: 0`, `QUALITY_SCORE: 0`, `FOCUS_TOKENS: 10`, `CEO_EMAIL_HANDLED: 0`, `COLLEAGUE_PINGED: 0`) and a `Tick: 0 / 60` counter. Event stream reads "No events yet. Actions below advance time." — clean.
- **Severe navigation bug:** Clicking "Begin Simulation" consistently navigates the user off this step and into M5.S1 or M5.S2 (the capstone module). After multiple attempts with different entry paths (sidebar M4 click, `goToStep(1)`, direct hash navigation to `#.../23199/1`), the simulator could not be started without being immediately hijacked to a different module. The underlying `getSteps()` state appears to point to M5 even when the UI shows M4, so `simloopStart(1)` starts a simloop against the wrong step.
- **When I DID manage to fire a single action (`simloopAction('reply_template_low', 1)`) while the state was still correct:** The network call returned 200 OK — but before I could see the dashboard update, the page navigated away.
- **Metric labels:** cosmetic issue — `TIME_REMAINING_MINUTES` / `MESSAGES_COMPLETED` in SCREAMING_SNAKE_CASE feels very dev-y for a PM audience. Should be Title Case ("Time Remaining", "Messages Completed").
- **Verdict: ⚠ partial** — the dashboard renders fine, but the simulator is effectively un-startable because Begin Simulation navigates away. On v1 this step was rejected; the `[object Object]` rendering issue appears fixed, but a new (or carried-over) navigation bug now makes the step un-runnable for a typical user who just clicks around.
- UI notes:
  - The start button warps the user to a different module. Un-usable.
  - Metric labels should be human-readable.
  - Ticks are also labeled with technical identifiers like `respond_slack_ping`, `fact_check_before_ship` — readable but stylistically inconsistent with the briefing's PM-friendly tone.

## Step M5.S5 — "Ship the Team Prompt Library doc" — system_build (CAPSTONE)
- Briefing clarity: 5/5  | time on step: ~12 min
- This was the v1-rejected step to re-verify (spec called it M5.S4 but it's actually S5 / last step).
- **Zero-code promise: KEPT** visibly. Briefing explicitly says "Zero-Code Zone: This capstone uses only claude.ai in your browser + a doc editor (Notion/Google Docs/plain markdown). No terminal, no GitHub, no deployments." The submit is literally a paste-your-markdown textarea. No GitHub Actions URL, no fork-a-repo, no `git push`, no CI visible.
- **HOWEVER:** Inspecting the DOM, the template includes a hidden `<div class="tmpl-gha-widget">` with an input placeholder `https://github.com/you/your-fork/actions/runs/...` and a "Check my CI" button. It is correctly hidden via `display: none` for this capstone, but the HTML is still present, meaning a CSS regression would surface "CI" and "GitHub Actions run URL" to a PM audience. Fragile — recommend removing from the template rather than hiding it.
- Attempt 1 (weak — just 3 template titles, no content):
  - Score: 5%
  - Backend feedback: Rubric-aware. Explicitly lists all 4 missing phases + 5 specific missing checklist items + doc rubric 10% + a paragraph of concrete guidance ("templates lack specificity... no examples... no measurement data...").
  - Did this help me iterate? YES. This is **the best-teaching grader feedback I saw in the whole course.**
- Attempt 2 (strong — full 3 templates with goal/audience/format/example input/output/time-saved + 4-paragraph meta-adaptation guide, ~1200 words):
  - Score: 65%
  - Backend feedback: "Strong submission hitting most criteria well. Specificity is excellent - each template names exact audiences like 'Marcus Chen (Head of Operations) + cc CEO + VP Sales' and precise formats like 'max 400 words, three sections in this exact order.' Measurement realism is solid with actual stopwatch data... However, hallucination call-outs are incomplete - while you include HUMAN-VERIFY warnings, they lack the specific 'who' and 'by when' convention you mention in the meta-guide..."
  - Rubric breakdown: Doc rubric 90% (threshold 70%) ✓, Checklist items 6/6 ✓, Phases completed 0/4 ✗
  - Did this help me iterate? YES — the "you mentioned 'who + by when' in your meta-guide but didn't apply it in your HUMAN-VERIFY notes" is a superb observation.
- **Verdict: ✅ passed** — content-wise this step is excellent. Only real issue:
  - **"Phases completed: 0/4" is un-reachable** — the briefing lists 4 phases (Structure / Draft / Validate / Publish) with circle-dot markers, but I could find no UI to check a phase off. So even a 100% doc rubric + 6/6 checklist submission caps out at ~65% because Phases 0/4 drags the score down.
  - No navigation bug. Textarea paste worked. Submit fired. Score + feedback displayed correctly.
- UI notes:
  - Phases list has `○` bullet markers that suggest checkboxes but aren't clickable.
  - Grader feedback is the best in the course — specific, paragraph-long, rubric-backed.
  - Hidden GHA widget in template source is a zero-code-promise landmine.

## Step M2.S2 — "Kelvingrove Corp: flag the fabrications" — categorization
- Briefing clarity: 5/5  | time on step: ~3 min
- Title again promises "15" items but only 8 present (same mismatch as M1.S2).
- Attempt 1 (correct): Put specific-number claims (ARR 47.2→73.8M, NRR 127%, churn 3.2%→4.7%, $23.5M Series B with named investors) in FABRICATED; vague descriptions in GROUNDED.
  - Score: 100% (8 of 8 correct)
- Verdict: ✅ passed
- UI notes: Stayed on the step after submit (no navigation hijack here — good). Score displayed clearly. Grader works for straightforward categorization.

## Step M3.S2 — "Build the weekly-status template: fill the 6 slots" — fill_in_the_blanks
- Briefing clarity: 4/5  | time on step: ~4 min
- Title says 6 slots but there are actually 7 input fields (AUDIENCE + GOAL + FORMAT + EXAMPLE 1 + EXAMPLE 2 + CONSTRAINTS + ESCALATION).
- The pre block uses class `tmpl-fib-code` — it's not actual code, it's a markdown-style template with `**AUDIENCE:**` labels. Class name is misleading but content is fine.
- Attempt 1 (intentionally weak one-line answers like "Marcus Chen", "markdown", "nothing"):
  - Score: 0%
  - Feedback: "0% on this attempt. 2 more retries before the full breakdown reveals. 7 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Did this help me iterate? No — generic stock feedback, no hint what "the expected answer" looks like.
- Attempt 2 (strong, richly-detailed answers — each slot was a full sentence with named audiences, exact word counts, concrete examples, escalation triggers):
  - Score: 0% (!)
  - Feedback: same generic text
  - Item results: all 7 wrong, with NO per-item feedback and NO expected-answer reveal.
- Verdict: ❌ stuck — the grader is effectively a string-exact-match, and the "correct" answer is a secret. Non-coder PM has no way to debug what's wrong.
- UI notes:
  - Title says 6 slots, UI renders 7.
  - `tmpl-fib-code` class name is misleading (there's no code in there, just markdown labels).
  - Grader is exact-match and provides zero signal on what the expected answer is — **this is the single most beginner-hostile grader in the course**. A thoughtful, well-targeted PM answer gets 0%.
  - Feedback generic and unhelpful.

## Step M3.S4 — "Iterate a prompt from meh to ship-quality: order the loop" — ordering
- Briefing clarity: 5/5  | time on step: ~3 min
- Briefing includes the phrase "like editing a document or debugging code" — a passing code metaphor, not a violation.
- Attempt 1 (ordered: test initial → diagnose → add context → add example → add constraints → re-test):
  - Score: 100% (6 of 6 correct)
  - Feedback: "Perfect ordering!"
- Verdict: ✅ passed
- UI notes: Clean. Stayed on step after submit. "Next Module" button appeared.

## Step M4.S4 — "Classify what went wrong in 6 of your drafts" — categorization
- Briefing clarity: 5/5  | time on step: ~3 min
- Six buckets: HALLUCINATED / OFF-TONE / MISSED-STAKEHOLDER / FORMAT-WRONG / WRONG-ACTION / FINE-TO-SHIP. PM-friendly taxonomy.
- Attempt 1: Contract plain-text → FORMAT-WRONG; Weekly update bullets → FINE-TO-SHIP; "2.3M transactions when actual 180K" → HALLUCINATED; full refund against policy → WRONG-ACTION; missing Finance/Legal cc → MISSED-STAKEHOLDER; "Hey there!" → OFF-TONE.
  - Score: 100% (6 of 6 correct)
- Verdict: ✅ passed
- UI notes: Clean. The 6-category taxonomy is genuinely useful as a PM quality-gate checklist.

## Step M5.S2 — "Pick YOUR 3 tasks (the brief)" — fill_in_the_blanks
- Briefing clarity: 3/5 (content is clear but the format is wrong for the audience) | time on step: ~5 min
- **HUGE zero-code violation.** The fill-in block is rendered as Python source code:
  ```
  # TASK 1
  task_1_name = ""
  task_1_audience = ""  # who receives/uses the output?
  task_1_frequency = ""  # Daily/Weekly/Monthly/Quarterly/As-needed
  task_1_current_time_minutes =   # how long it takes you now
  task_1_target_time_minutes =    # realistic AI-assisted target
  ...
  total_weekly_savings_minutes = (
      (task_1_current_time_minutes - task_1_target_time_minutes) *  +  # frequency multiplier
      ...
  )
  print(f"Weekly time savings target: {total_weekly_savings_minutes} minutes")
  ```
  This is literally Python: `snake_case` variable names, assignment syntax, parenthesized multi-line expression, an f-string, and a `print()` call. A PM who was promised "zero code, no Python, no terminal" will bounce the moment they see `print(f"...")`.
- Attempt 1 (sensible PM answers — "Weekly team status compilation", "Marcus Chen (Head of Ops)", "45", "6", etc.):
  - Score: 39% (7 of 18 correct)
  - Feedback: "11 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Did this help me iterate? No — no per-item indicator of which 7 were right or what the expected strings are.
- Verdict: ⚠ partial — the content is valuable (mapping tasks to AI workflows) but the format is inappropriate for the promised audience. Grader is the same exact-match FIB grader that gives no actionable signal.
- UI notes:
  - **Zero-code promise VIOLATED here. Major ship-blocker.**
  - Input field between equals sign and `# comment` is confusing — is the blank the empty string `""` or the raw number? Ambiguous to a non-coder.
  - Same grader issue as M3.S2 — exact-match, no feedback.

---

## Final summary

### Steps tally (15 walked)
- ✅ Passed: M1.S1 (concept), M2.S2 (categorization 100%), M3.S4 (ordering 100%), M4.S4 (categorization 100%), M5.S5 (capstone 65% — good grader)
- ⚠ Partial: M1.S2 (categorization, nav-hijack), M1.S3 (code_read — flagged step, grader wrong), M4.S2 (simulator — flagged step, nav bug prevents start), M5.S2 (Python-syntax FIB)
- ❌ Stuck: M3.S2 (FIB grader is secret exact-match)
- Drive-by visits: M0.S2, M2.S1, M2.S3, M3.S1, M3.S3, M4.S1 (all CONCEPT/SCENARIO, no blockers observed)

### Beginner-hostile issues (ranked)
1. **M5.S2 Python-syntax fill-in-the-blanks** — breaks the zero-code promise directly. `task_1_name = ""`, `print(f"...")`, `total_weekly_savings_minutes = (...)` is Python source code presented to non-coder PMs who were told "browser-only, no Python."
2. **M4.S2 simulator cannot be started** — clicking "Begin Simulation" hijacks the user to a different module (M5.S1 or similar). The dashboard renders fine, but the exercise is effectively un-startable for a click-around user.
3. **M1.S3 (code_read) grader hallucinates** — marks an explanation as "missing audience definition, format constraints, structural requirements" when the explanation explicitly named all of those. Score stuck at 20% on strong answers; backend actually returns 0% with "please write what the code does" (wrong — there is no code in this step) on subsequent attempts, and the UI doesn't re-read the updated response.
4. **M3.S2 / M5.S2 FIB grader is a secret exact-match** — gives 0% with no hint of expected strings. For rubric-style questions (AUDIENCE, GOAL, FORMAT), there are many valid answers; rejecting all but one exact string is beginner-hostile.
5. **M1.S2 briefing says "15 tasks"** but only renders 8. Same with M2.S2 ("15 'facts'"). Cosmetic inconsistency that erodes trust.
6. **Navigation state leak** — clicking a sidebar module (M4) often lands on a different module (M5) because `getSteps()` returns the wrong module's steps. Multiple attempts required to land on the intended step.
7. **Simulator metric labels in SCREAMING_SNAKE_CASE** (`TIME_REMAINING_MINUTES`) — dev-y aesthetic for a PM audience.
8. **Hidden `tmpl-gha-widget`** (GitHub Actions URL input + "Check my CI" button) is present in the DOM on the capstone step, hidden only by `display: none`. A CSS regression would surface "CI" and GitHub URLs to PMs.

### Grader quality
- **Best in course:** M5.S5 capstone grader — rubric-aware, paragraph-long, specific ("you mentioned 'who + by when' in your meta-guide but didn't apply it in your HUMAN-VERIFY notes").
- **Good:** M2.S2, M3.S4, M4.S4 categorization/ordering graders — clear 100% or per-item correctness.
- **Broken:** M1.S3 code_read grader — factually wrong about what my answer contained.
- **Beginner-hostile:** M3.S2 and M5.S2 FIB graders — secret exact-match with no reveal and no hints.

### Did the course keep the "zero code / zero CLI / browser-only" promise?
- **NO, not fully.**
- M5.S5 capstone visibly keeps it (paste a markdown doc).
- M5.S2 visibly breaks it (Python syntax as the fill-in-the-blanks format).
- Hidden GHA widget in DOM is a landmine.
- Some incidental "debugging code" / "what the code does" phrasing leaks into M3.S4 brief and M1.S3 grader feedback.

### Verdict: ❌ REJECT (CONDITIONAL on fixes below)

### Top 3 ship-blockers (ranked)
1. **M5.S2 must be rewritten without Python syntax.** Use a plain markdown table, a structured form with labeled fields, or a natural-language "Here's Task 1 / Here's Task 2" template. The current Python code template fails the course's zero-code promise.
2. **M4.S2 simulator Begin Simulation navigates to the wrong module.** The user cannot start the simulator from a clean sidebar-navigation path. Whatever state leak is causing `getSteps()` to return M5's steps when M4 is visible must be fixed.
3. **M1.S3 code_read grader is flat-out wrong.** Review the rubric logic — it's producing feedback that factually contradicts the submitted answer (claims "you didn't identify X" when X is explicitly named in the answer). This one step alone will make a PM think the course is broken.

### Also recommended (not blockers but close)
- Fix FIB graders (M3.S2, M5.S2) to either use LLM-rubric scoring or reveal expected answers after 2 wrong attempts.
- Fix item-count mismatch in briefings (M1.S2, M2.S2 both say 15 but render 8).
- Rename simulator metric labels to Title Case (PM friendly).
- Delete the hidden GHA widget HTML from the capstone template (not just hide it).
- Add phase-checkbox UI to M5.S5 so capstone can reach 100% instead of being capped at 65%.

