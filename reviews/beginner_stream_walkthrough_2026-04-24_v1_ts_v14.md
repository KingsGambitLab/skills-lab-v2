# Beginner Walkthrough — TypeScript v14: Types, Zod, API Clients
- Start: 2026-04-24
- Reviewer persona: beginner Python programmer exploring TypeScript for the first time; has done a bit of Python, knows basic types, never written production TypeScript.
- Course URL: http://127.0.0.1:8001/#created-14d9215508b7
- Artifact policy: rewritten after every step; no prior reviews read.

## Course structure I can see from the sidebar

- Module 1 — Type Fundamentals: interface, type, and satisfies (4 steps)
- Module 2 — Discriminated Unions & Exhaustive Matching (4 steps)
- Module 3 — Type Derivations: Pick, Partial, Omit & Mapped Types (4 steps)
- Module 4 — Runtime Validation with Zod 3.24 (4 steps)
- Module 5 — Capstone: Typed fetchJson Client with Result<T,E> (5 steps)

## Walkthrough log

## Step 1.0 — "Why TypeScript teams still argue about interface vs type" — concept
- Briefing clarity: 4/5  | time on step: ~3 min
- Experience: Concept step with a "Production Bug Alert" framing — very motivating opener. The page shows (a) a problematic Express route config with `method: string` widening, (b) an interactive widget letting me switch between Plain object / interface / type alias / satisfies to see the resulting type, (c) a "Test Route Registration" button to simulate the runtime bug. As a beginner I understood the problem: if TypeScript widens `method: 'POST'` to `method: string`, Express gets passed a string that might be `'DELETE'` or whatever, defeating type safety. The `satisfies` option preserves literal types without widening.
- Verdict: passed (auto-complete on view, Next enabled, Previous disabled because it's step 0)
- UI notes: Concept banner shown ("📖 CONCEPT"). Widget has Approach selector + Test button + Reset. Dark theme clean. No layout glitches. "Spot the Bug" label is a visual pill, not a button learners need to click. Layout appears to render correctly — no overlapping panels.

## Step 1.1 — "interface vs type: pick the right tool" — table_compare
- Briefing clarity: 4/5  | time on step: ~2 min
- Experience: Side-by-side table comparing interface vs type on four axes (declaration merging / inheritance / unions / mapped types). Well-written, each row shows code snippets for both sides. The "Veridian's Library Architecture Decision" paragraph gives a clear rule: "use interface for extensible base shapes, type for discriminated unions and generic utilities." As a learner I got a useful mental model from this.
- Verdict: passed (auto-complete — no submit button)
- UI notes: **Minor UI bug** — the step-type banner displays the raw slide-type id "TABLE_COMPARE" instead of a pretty label like "Concept" or "Compare". Functionally fine, but shows the ontology id through the UI — inconsistent with other steps whose banners say "📖 CONCEPT" / "🔎 Code Review". Also sidebar still shows "0/4 steps" for Module 1 after viewing Step 1.0 and moving to 1.1 — so concept-auto-complete may not be writing progress for these rendered steps (OR progress is only computed for logged-in users; I was not logged in).

## Meta-observation — routing instability
- During the walkthrough I repeatedly observed the URL hash **auto-changing** between evaluations, sometimes jumping me to a totally different course (`created-9b979553bf97` — "Go for Production: HTTP Services"). When I set `location.hash = '#created-14d9215508b7/23168/2'` directly and waited, the hash stayed stable for 3+ seconds. But **clicking the built-in Next button or interacting with certain widgets** sometimes popped me into a different course. I could never reproduce the exact trigger — but a real learner in a fresh tab would encounter this as "I clicked Next and ended up in a Go course I didn't enroll in". This is either a deep-link router bug (hash restoration from a prior session without the `#created-<id>` prefix being stable) or a "Next" button bug that falls off the end of the course. Definitely a P1 UX issue.
- A second auto-complete anomaly: Module 3 sidebar showed `1/4 steps` even though I had never interacted with module 3 content. That means either the Next button or the auto-navigate ticked completions I didn't mean to tick.

## Step 5.0 — "Architecture: Result<T,E> + ApiError union" — concept (capstone intro)
- Briefing clarity: 4/5  | time on step: ~2 min
- Experience: Good high-level pipeline diagram showing fetch → timeout → status → JSON → Zod validation, with each stage mapped to a specific ApiError variant (NetworkError / TimeoutError / HttpError / ParseError / ValidationError). Introduces the Result<T,E> pattern clearly. For a learner who made it through modules 1-4, this synthesizes the capstone story well. I understood what I'm about to build.
- Verdict: passed (auto-complete)
- UI notes: Content rendered cleanly. Pipeline diagram reads top-to-bottom. Dark theme intact.

