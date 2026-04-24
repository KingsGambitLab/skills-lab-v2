# Beginner stream walkthrough — Go Basics: Writing Your First Programs
Date: 2026-04-22
Course: http://127.0.0.1:8001/#created-6b695b950f9c
Reviewer persona: beginner programmer, Go is target language, first walk through.

## Course shape
- Title: "Go Basics: Writing Your First Programs" — Beginner badge
- 5 modules, 4 steps each → 20 steps. Structure per module: 1 concept + 2 code_exercise + 1 code_review.
  1. Go Foundations: Variables, Types, and Functions
  2. Collections: Slices and Maps
  3. Structs, Methods, and Interfaces
  4. Errors the Go Way
  5. Concurrency Capstone: Goroutines, Channels, and a Real Pipeline
- Narrative: StreamFlow Analytics / Marcus Chen building a 3-stage goroutine log pipeline.

## Headline finding — the course is mis-wired as Python
- Every `code_exercise` briefing talks about Go (function signatures like `parseConfig(raw string) (host string, port int, err error)`, packages `strings`, `strconv`, `fmt.Errorf`, etc.), BUT
- Every `code_exercise` ships a **Python** starter (`from __future__ import annotations`, `def solve(inputs: dict[str, Any]) -> dict[str, Any]`).
- Language label above the editor literally says "python".
- Validation for every exercise is a bare `{"must_contain": ["def ", "return"]}` — no hidden Go tests, no per-exercise expected output.
- Result: a real Go submission (`func parseConfig...`) crashes with a Python SyntaxError inside the Docker runner. A 1-line stub `def solve(x): return {}` gets 100%. Confirmed on 5 different exercises across 4 modules.
- The error trace even leaks an unrelated exercise's filename (`from solution import classify_temp`), suggesting the hidden-test runner isn't loading any fixtures for this course and is falling back to another course's pytest suite — then failing to import, which apparently still scores 100 when `must_contain` passes.

---

## Step 1.1 — "Why Go Feels Different: Zero Values & Short Declarations" — concept
- Briefing clarity: 4 — the StreamFlow context + nil-map panic framing is evocative; explains zero values vs make() clearly.
- time on step: ~2 min
- No submission needed; viewing auto-completes the dot.
- Interactive widget: a `<select>` of 6 declaration forms with "Test This Declaration" and "Test Operation" buttons. Clicking "Test Operation" without first choosing did nothing visible, and after selecting, the "Results" panel stayed at "Click 'Test This Declaration' to see what happens…". I couldn't produce any output from the widget across several combinations. **UI feels partially wired**.
- Verdict: ✅ passed (auto-complete on view)
- UI notes: interactive "Declaration Playground" didn't produce output when I exercised it. Confusing to a learner expecting feedback.

## Step 1.2 — "Parse a Config: Multiple Return Values" — code_exercise
- Briefing clarity: 4 — "split host:port using strings.Split and strconv.Atoi, return (host, port, err)" is clear and Go-shaped.
- time on step: ~4 min
- Attempt 1 (wrong — beginner literally writes Go because the briefing says Go):
  ```
  func parseConfig(raw string) (string, int, error) {
    return "", 0, nil
  }
  ```
  - Score: **0%**
  - Feedback verbatim: "0/1 hidden tests passed in Docker. Output tail: ... /app/solution.py line 1 SyntaxError: invalid syntax ... `from solution import classify_temp`"
  - Did this help me? **no** — it reveals two dealbreakers: (a) the grader is running Python, not Go, and (b) it references `classify_temp`, an identifier that's nowhere in this course. A beginner would be flat-out confused.
- Attempt 2 (right — I pivot and match the Python starter):
  ```
  def solve(inputs):
      raw = inputs.get('raw', '')
      parts = raw.split(':')
      if len(parts) != 2: return {'error': 'invalid format'}
      host = parts[0]
      try: port = int(parts[1])
      except ValueError: return {'error': 'bad port'}
      return {'host': host, 'port': port}
  ```
  - Score: **100%**
  - Feedback verbatim: "Your code uses the required constructs and runs successfully."
  - Did this help me? **no** — it's generic; never mentions host/port, never confirms tuple returns or Go idioms the briefing stressed.
- Verdict: ⚠ partial — the exercise "passes" but teaches nothing about Go. A Go-literal beginner gets stuck; a non-beginner pivots to Python.
- UI notes: the editor's language label says "python". Hint button (💡 Hint) works — it reveals the briefing one-liner.

## Step 1.3 — "Named Returns & Defer: Spot the Bugs" — code_review
- Briefing clarity: 3 — bug categories (Variable Shadowing / Named Return Logic / Defer Timing / Error Handling / Resource Management) are listed, but the code is 46 lines and the learner isn't told how many bugs to find or how the grader marks them.
- time on step: ~5 min
- Attempt 1 (wrong — guess lightly): flagged lines 22, 27, 33, 45.
  - Score: **65% (3 correct · 1 wrong)** — but the same feedback also says "2 of your responses did not match the expected answer", which contradicts "3 correct · 1 wrong" if I picked 4. The two counters don't reconcile.
  - Feedback verbatim: "Score: 65% (3 correct · 1 wrong) 65% on this attempt. 2 more retries before the full breakdown reveals. 2 of your responses did not match the expected answer. Look at which items you chose vs what the exercise asked for and try again."
  - Did this help me? **no** — doesn't say which lines were right or wrong, and the "3 correct · 1 wrong" vs "2 responses didn't match" inconsistency is disorienting.
- Verdict: ⚠ partial — reached a passing-ish score on attempt 1 but never learned which picks mattered.
- UI notes: **Bug A:** when I clicked into /23027/2 the FIRST render showed the next step's Python starter textarea below the Go code block — stale/leaked editor from Step 1.4. Went away after a hash re-set. **Bug B:** counter inconsistency (see above). **Bug C:** when I clicked Submit from the code_review, the URL auto-advanced to /23027/3 even though I was still mid-step — I had to hash back to stay.

## Step 1.4 — "Implement DivMod with Named Returns" — code_exercise
- Briefing clarity: 4 — "divmod(a,b int) (quotient, remainder int, err error) with named returns and a naked return, check b==0". Clear Go.
- time on step: ~1 min
- Attempt 1 (right — pattern established, I wrote Python immediately):
  ```
  def solve(inputs):
      a = inputs.get('a',0); b = inputs.get('b',1)
      if b == 0: return {'error': 'divide by zero'}
      return {'quotient': a//b, 'remainder': a%b}
  ```
  - Score: **100%** — generic pass message.
- Verdict: ⚠ partial (grader is lenient — same Python-stub-passes pattern).
- UI notes: identical "python" lang label, identical generic feedback.

## Step 2.1 — "Slice Headers, Backing Arrays, and the append Trap" — concept
- Briefing clarity: 4 — 24-byte slice header + when append reallocates is explained well with the StreamFlow sharing-array bug.
- time on step: ~2 min
- Interactive "append first event" buttons clicked; result area stayed blank. Simulator did not render any state changes across 4 button clicks.
- Verdict: ✅ passed (auto-complete).
- UI notes: Slice Visualizer interactive **does nothing visible** when buttons clicked — dead widget.

## Step 2.2 — "Dedup a Slice of User IDs" — code_exercise
- Briefing clarity: 4 (Go-shaped: "dedup(ids []string) []string using map[string]struct{} preserving order").
- time on step: ~30 s
- Attempt 1 (casual stub): `def solve(inputs): return {}`
  - Score: **100%**
  - Feedback: "Your code uses the required constructs and runs successfully."
  - Did this help me? **no** — proves the grader is checking only that the source contains `def ` and `return`. There is no fidelity check.
- Verdict: ⚠ partial — grader too lenient.
- UI notes: "python" lang label again.

## Step 2.4 — "Find the Slice/Map Bugs" — code_review
- Briefing clarity: 3 — four bug categories (Map Safety, Slice Memory, Map Iteration, Bounds Safety) but no count of how many lines to flag.
- time on step: ~4 min
- Attempt 1 (wrong / guess): flagged lines 20, 22.
  - Score: **0% (0 correct · 2 wrong), "6 of your responses did not match"**
  - The 0-correct/2-wrong vs 6-didn't-match counter mismatch again. Also, "6 did not match" is odd when I only chose 2 items — I think the grader counts the expected-but-not-picked as "did not match" too, but no copy explains that to a learner.
- Attempt 2 (right-ish): flagged lines 17, 26, 30, 33, 36, 42 — shotgunning at the lines that look suspicious (nil map, write-to-nil-map, etc.).
  - Score: **10% (2 correct · 4 wrong), "6 of your responses did not match"**
  - Feedback verbatim: "1 more retry before the full breakdown reveals. 6 of your responses did not match the expected answer."
  - Did this help me? **no** — doesn't say which 2 were correct. With only 1 more attempt, I can't guess which to drop.
- Verdict: ❌ stuck (beginner-hostile) — I'm using attempts without learning anything; "full breakdown" gating is too late.
- UI notes: per-item correctness never shown. Also the same inconsistent-counter wording as 1.3.

## Step 3.2 — "Implement Stringer for Money" — code_exercise
- Briefing clarity: 4.
- time on step: ~30 s
- Attempt 1 (stub): `def solve(x): return {"ok": True}`
  - Score: **100%** — generic pass.
- Verdict: ⚠ partial — grader lenient.

## Step 4.2 — "Build a ValidationError Type" — code_exercise (with hint test)
- Briefing clarity: 4 — `ValidationError{Field, Reason string}` with `Error() string`, plus `errors.As` notes. Fully Go-specific.
- Hint button works on click — expands to reveal the briefing one-liner (Go-flavored). Good.
- time on step: ~1 min
- Ran the ▶ Run button on a `print('hello'); return {...}` snippet — output area shows "(no output)" despite the print. Run button appears non-functional.
- Verdict: ⚠ partial (didn't submit; noted Run issue).

## Step 5.1 — "Channels, select, and Leak-Free Shutdown" — concept
- Briefing clarity: 4 — producer→worker→collector, done-channel broadcast pattern is clean.
- Interactive "Pipeline Simulator" with Start Pipeline / Shutdown buttons — clicked Start, no visible animation / state change. Same dead-widget issue as Module 1 and 2.
- Verdict: ✅ passed (auto-complete).
- UI notes: interactive simulator doesn't animate / render anything.

## Step 5.4 — "Capstone: Build a 3-Stage Event-Processing Pipeline" — code_exercise
- Briefing clarity: 4 — but this is the CAPSTONE (top of course's learning arc) and it STILL accepts a trivial stub.
- Attempt 1: `def solve(x): return {"status": "ok"}`
  - Score: **100%** — generic pass. Capstone completed without implementing any pipeline.
- Verdict: ⚠ partial — capstone is entirely bypassed by any 1-liner.

---

## Skipped/skimmed (pattern already proven)
- 2.3 Count Events by Type, 3.3 Value vs Pointer Receiver code_review, 3.4 Safe Type Assertions, 4.1 concept, 4.3 Wrap & Unwrap DB Error, 4.4 Swallowed Errors code_review, 5.2 fan-out Squares warm-up, 5.3 Spot the Concurrency Bugs code_review. All code_exercises would repeat the Python-stub-passes; code_reviews would repeat the per-line opacity issue.

## Pass / stuck / partial tally by exercise type
- concept (5 steps): 5 ✅ passed (auto-complete on view), but 3/5 concepts shipped a widget (Slice Visualizer, Pipeline Simulator, Declaration Playground) that **does nothing observable** — dead interactives.
- code_exercise (10 steps): sampled 5 (1.2, 1.4, 2.2, 3.2, 5.4). All "pass" with 100%, all with Python-stub. Verdict for type: ⚠ partial — grader is broken.
- code_review (5 steps): sampled 2 (1.3, 2.4). One ⚠ partial (65% on first try), one ❌ stuck (no per-line feedback, counter mismatch).

## Beginner-hostile steps (blockers)
- 1.2, 1.4, 2.2, 3.2, 4.2, 5.4 code_exercise — a learner who takes the briefing at face value and writes Go gets a Python SyntaxError plus a leaked reference to `classify_temp` from a totally different course. Huge credibility hit.
- 2.4 code_review — no per-line feedback and counter wording is internally contradictory; realistic learner runs out of attempts without understanding why.
- Any concept with the "interactive" widget — learners expect feedback from clicking, get silence.

## Too lenient
- Every code_exercise. Trivial `def solve(x): return {}` earns 100%.

## Too harsh
- code_review's "full breakdown reveals after 2 more retries" gating combined with opaque per-item feedback — a learner who burns 2 wrong attempts never recovers.

## Other bugs
- URL hash auto-advances (was on /23027/2, clicked Submit, URL jumped to /23027/3 mid-step). Also observed hash mysteriously flipping the whole course context to a different created-... Python course (`created-82e212a0f83c`) after several interactions — unclear trigger but happened repeatedly. Frequently had to hash-set back.
- Code_review page briefly shows next step's Python starter textarea embedded below the Go code.
- Run button reports "(no output)" on runs that should print.
- Error trace on Attempt 1 of 1.2 leaked `classify_temp` — strong smell that the grader is loading the wrong test module.

## Would a real learner quit?
Yes. First exercise. As soon as they see "python" on the editor of a Go course and their Go submission fails with `from solution import classify_temp`, confidence evaporates. The only way forward is the non-beginner realization that the grader accepts any Python stub. Learning value: ~zero.

## Verdict
❌ **REJECT** — the course is authored as Go but shipped as Python, the grader runs generic Python `must_contain` with no hidden tests, capstone-level work can be bypassed with a 1-line stub, concept interactives are dead, code_review feedback is opaque. This is unshippable in its current state.
