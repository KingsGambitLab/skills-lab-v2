# Beginner walkthrough — AI-Powered Workday (aipw_v1)

Persona: Senior PM at B2B SaaS, 5 yrs, no CLI experience. Browser Claude only.
Course: "AI-Powered Workday: Ship 3 Prompt Workflows to Your Team This Week"
URL: http://localhost:8001/#created-bd5ec658354f
Date: 2026-04-24

---

## Per-step notes

### M0.1 — "What this course is (and what it deliberately isn't)" — concept
- Briefing clarity 5/5. Clean intro, before/after demo. No input required. OK.

### M0.2 — "Opening Claude on Monday 9am: which task wins?" — scenario (2 decisions, MCQ-style)
- Attempt 1 (mixed): clicked option 2 (inbox prioritize) for D1, then option 1 (document template) for D2.
  - Score: 50%. Feedback: "50% on this attempt. 2 more retries before the full breakdown reveals. 3 of your responses did not match the expected answer. Look at which..." (truncated)
  - BUG: feedback message says "3 of your responses did not match" but there were only 2 decisions. Off-by-one / wrong counter.
  - Feedback narrative ("executive-visible use cases first") was genuinely teaching — good.
- Verdict: passed through ⚠ (misleading counter text).

### M1.1 — SPEC framework concept
- Clear briefing, well-paced. ✅

### M1.2 — "sort 15 PM-ops-CS tasks" — categorization (DELEGATE / PAIR / NEVER-DELEGATE)
- Only 8 items visible but briefing says 15. Partial content rendering.
- Submit with nothing categorized auto-advanced silently (no "please categorize first" block).
- Verdict: ⚠ partial (briefing says 15, UI shows 8; lenient grader passes empty submission).

### M1.3 — "Two prompts, same task: why one works" — **code_read shape (wrong shape for audience)**
- ❌ BEGINNER-HOSTILE. The exercise renders prompt text inside a CODE EDITOR with line numbers 1-39, "text / read-only reference" header, and the input textarea has placeholder "What does this code do? What are the important design choices a learner should notice?" — placeholder literally says "code."
- A non-coder PM sees "code," thinks "I'm in the wrong course," and bounces.
- The content itself (comparing a weak prompt vs a SPEC-structured prompt) is useful; the widget shape is the problem.
- Verdict: ❌ beginner-hostile shape mismatch.

### M2.1 — Why LLMs hallucinate — concept
- Strong plain-English explanation ("smart intern locked in a room with no internet"). 5/5.

### M3.2 — "fill the 6 slots" — **fill_in_blank template builder**
- 7 `tmpl-fib-input` fields for the 6-slot template (AUDIENCE, GOAL, FORMAT, EXAMPLES×2, CONSTRAINTS, ESCALATION). Exactly the right shape.
- Slot reference is listed above with concrete examples. A non-coder can fill it.
- Verdict: ✅ teachable, appropriate shape. This is the course's best step.

### M4.2 — "Work the inbox" — inbox simulator — **BROKEN**
- ❌ SHOWSTOPPER 1: The dashboard renders the message list as `[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object]` for INBOX, same for INTERRUPTIONS (3x) and CEO_EMAIL. The simulator is NOT rendering message subject/body — it is calling toString() on raw JS objects.
- ❌ SHOWSTOPPER 2: Clicking "Begin Simulation" returns HTTP 400 from the backend. Button swaps to "Retry — Start failed: 400". Retry also fails with 400. Simulator never starts.
- Event stream says "No events yet. Actions below advance time." but the only action button is "Advance 5 ticks (no action)" — a test harness leftover.
- The Monday-9am inbox simulator — a headline objective of the course ("Work the inbox WITH Claude under realistic interruption load") — is completely broken.
- Verdict: ❌ stuck (course-fatal).

### M5.5 — "Ship Your Team Prompt Library" — capstone — **PROMISE VIOLATED**
- ❌ SHOWSTOPPER 3: The capstone is NOT a markdown-writing exercise. It is a GITHUB REPO + GIT + GITHUB ACTIONS submission.
- Briefing literally shows a shell command sequence:
  ```
  git init team-prompt-library
  echo "# Team Prompt Library" > TEAM_PROMPT_LIBRARY.md
  git add .
  git commit -m "Ship team prompt library with 3 templates"
  gh repo create team-prompt-library --public
  git push -u origin main
  ```
- Acceptance checklist includes: "Create GitHub repo named 'team-prompt-library' with public visibility", "Commit and push to main branch", "Verify repo is publicly accessible".
- Grading is GitHub Actions: "Fork the starter repo. Push your solution to a branch. GitHub Actions runs validate-library.yml automatically. Paste the run URL below."
- Submission input is a URL field expecting `https://github.com/you/your-fork/actions/runs/1234567890`.
- There is no in-browser markdown editor. None.
- The course description promises "NO API keys, NO code, NO terminal" and "browser Claude only". The capstone demands git CLI, `gh` CLI, GitHub account, GitHub Actions, and a forked repo URL. Full contradiction of course premise.
- Verdict: ❌ course-fatal for the stated audience.

---

## Explicit question answers

**(a) Does ANY step show a Python code editor when it shouldn't?**
- M1.3 renders prompt text inside a read-only code-reader widget with line numbers and a "What does this code do?" textarea. Not a Python editor, but the same widget shape. Wrong shape for the audience.
- M3's template builder (M3.2) uses fill_in_blank correctly. Good.
- Shape usage across non-system_build steps: 1 confirmed miss (M1.3). Likely more in M1.4/M2/M3 I didn't probe.

**(b) Does the Monday-9am inbox simulator feel real?**
- NO. It's fully broken. Message list renders as `[object Object]` placeholders. "Begin Simulation" returns 400. The simulator cannot be started, let alone played.

**(c) Is the capstone a markdown doc (not code)?**
- NO. The capstone requires creating a GitHub repo, running git/gh CLI commands, pushing a branch, triggering a GitHub Actions workflow, and pasting the run URL. A Senior PM with no CLI experience cannot complete this. The promised markdown doc exists in the acceptance criteria, but the SUBMISSION mechanism is git + GitHub Actions, not a text area.

**(d) Is prompt-template-building teachable via fill_in_blank shape?**
- YES. M3.2 ("fill the 6 slots") uses `tmpl-fib-input` fields for AUDIENCE/GOAL/FORMAT/EXAMPLES×2/CONSTRAINTS/ESCALATION with a slot reference giving concrete example phrasings. This is the course's best-designed step. Extend this shape to M1.3 and the capstone and a huge fraction of the problems go away.

---

## Verdict: ❌ REJECT

**Top 3 issues:**
1. **M4 inbox simulator is broken** — backend returns 400 on start, message list renders as `[object Object]` literals. The M4 module cannot be completed. This is the course's marquee interactive moment.
2. **Capstone is a git/GitHub Actions submission, not a markdown doc** — directly contradicts the course's "no code, no terminal, browser-only" promise. A non-coder cannot submit. Ship-blocker.
3. **M1.3 uses a code-reader widget with line numbers + "What does this code do?" placeholder for prompt text** — shape/audience mismatch. A PM sees "code" and assumes they're in the wrong course. Change to mcq, fill_in_blank, or plain textarea.

**Could a non-coder complete this without quitting?** — NO. They quit at M1.3 (code-editor shape shock) or at M4.2 (broken simulator). If they somehow push past both, they cannot physically submit the capstone without a git + GitHub account. Three independent failure modes each kill completion on their own.

The M0, M2, M3, and M5.1 CONCEPT content is genuinely good — the ideas (SPEC framework, DELEGATE/PAIR/NEVER rubric, 6-slot anatomy, hallucination red flags, team multiplier effect) are exactly right for the audience. The SHAPE choices and the submission plumbing are what kills it. Rework M1.3 shape, fix the M4 simulator, and replace the M5 capstone with an in-browser markdown textarea + rubric grader, and this is a strong course.
