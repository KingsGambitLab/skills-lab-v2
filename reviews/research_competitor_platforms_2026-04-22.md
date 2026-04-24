# Competitor Platform Research — 2026-04-22

Research scope: observation-only survey of interactive coding-course platforms to inform our Claude Code course. Primary deep-dive on Educative's `learn-vibe-coding` (the page the user flagged). Secondary survey on seven other platforms and the AI-coding-tool course landscape.

Constraint respected: zero edits to any file under `/Users/tushar/Desktop/codebases/skills-lab-v2/`.

---

## 1. Deep-dive: Educative "Learn Vibe Coding"

URL: https://www.educative.io/courses/learn-vibe-coding/what-is-vibe-coding
Course root: https://www.educative.io/courses/learn-vibe-coding

### What it is
A 1-hour, 10-lesson free course teaching non-programmers to ship real apps by prompting AI tools (Lovable in-browser, Claude Code in-terminal). Published by "MAANG Engineers." Updated aggressively (page says "Updated: Today" on 2026-04-22 fetch).

### Full TOC (extracted directly)

**Module 1 — Thinking Before Building**
- What Is Vibe Coding?
- How Software Actually Works?
- Thinking Before Prompting

**Module 2 — From Prototype to Working Product**
- Your First Build
- Prompt Craft
- Reading AI Output and Debugging
- When Your Project Needs More than a Browser Tab

**Module 3 — Connecting to the Real World**
- How Models Actually Work
- Real Data and Auth with Supabase
- APIs, Deployment, and What Vibe Coding Can't Do

Stated learning outcomes: vibe-coding concepts, systematic debug across frontend/backend/db, Supabase + Stripe integration, LLM mechanics (tokens, context windows), deploy to Vercel. Course project = "PawPals" (booking app built in Lovable, extended in Claude Code).

### Page shape (lesson UI)
- **Single scrolling page per lesson**, NOT paginated slides. Left sidebar = module/lesson outline with progress. Top = breadcrumb + "Claim your Certificate."
- Lessons mix **narrative prose + screenshots of Lovable/Claude Code + toggle comparisons + an MCQ at the end** ("Can you pick the better follow-up?"). No runnable code widget inside the lesson itself — the learner is pushed *out* to Lovable.dev or their terminal for the actual doing.
- No paywall on any of the 10 lessons I fetched. Content is freely readable. Certificate + "AI Code Mentor" presumably gated.

### Teaching patterns observed (concrete)

1. **Karpathy-anchored narrative hook.** "What Is Vibe Coding?" opens with a real-feel anecdote: "A person with no programming background... sat down on a Saturday morning... by Sunday evening they had a live product... a Stripe integration collecting real money, and three paying users." Credits Andrej Karpathy for coining the term. Teaching lesson: lead with aspirational, low-jargon narrative BEFORE any definition.

2. **Metaphor over diagram.** "How Software Actually Works" teaches frontend/backend/db via a **restaurant metaphor** (dining room / kitchen / pantry) rather than an architecture diagram. No interactive layer-visualizer. Teaching lesson: for total beginners, they trust a strong metaphor more than a schematic.

3. **Rule-of-thumb crystallization.** "Prompt Craft" distills its lesson to one memorable rule: *"One thing. Sometimes two if they are closely related, but almost never three."* Then the rest of the lesson is four sub-skills with explicit names (Scope control / Precise targeting / Outcome-focused language / Feature protection). Teaching lesson: name the skills, give them a chantable core rule.

4. **Failure-first examples.** "Prompt Craft" opens with a scenario where the dev asks for 3 features at once (favorites + filter bar + profile pages) and gets cascading breakage. Debugging lesson opens with *"The AI was not lying. It built what it described"* — then teaches "silent failure" as the central mental model. Teaching lesson: show the anti-pattern concretely, then derive the rule.

5. **"Right-click View Source" as the only interactive step.** The only hands-on moment in the "how software works" lesson is telling the learner to inspect a real webpage's source. No sandbox. Teaching lesson: small in-situ real-world pokes beat constructed toy exercises for some concepts.

6. **Out-of-platform hand-off is explicit.** "Your First Build" sends the learner to lovable.dev with account setup as part of the lesson. "When Your Project Needs More than a Browser Tab" hands off to Claude Code in terminal. They don't try to sandbox Lovable or Claude Code inside Educative. Teaching lesson: they own the narrative, the AI tool owns the doing.

### Interactive elements explicitly present
- Toggle comparisons (e.g. 2022 vs 2026 capability, traditional vs vibe coding)
- MCQs embedded mid-lesson ("Can you spot the stronger prompt?")
- Screenshots of the external tool (Lovable)
- Outline sidebar with progress tracking

### Interactive elements explicitly ABSENT (notable)
- No embedded runnable code
- No terminal emulator
- No live diagram / animated reveal
- No AI mentor chat visible on the free lesson page (likely gated)
- No auto-graded code submission

### How the course is clearly AI-authored
The **consistency of structure** across all 10 lessons is suspicious in a good way: every lesson has (a) anecdotal hook, (b) 1-sentence core rule, (c) 3-4 named sub-skills, (d) a named anti-pattern, (e) MCQ. This is a prompt template. The "MAANG Engineers" authorship plus "Updated: Today" rolling timestamp strongly suggests these are generated + lightly edited. Lesson length is uniform (~5-7 min read each).

---

## 2. Platform-by-platform survey

### Educative.io (general widget vocabulary)

Sources: Educative Widget Workshop (`/educative-widget-workshop/widgets-and-visuals`), Quiz Widget docs, Code Widget docs.

**Widget types they support:**

| Widget | What it does | Typical use |
|---|---|---|
| **Code** | Executable snippets in 40+ languages, line-highlighting, file inputs, stdin accepted. Max 55s run. | "Run this to see the result" |
| **SPA (Single Page App)** | Full frontend + backend apps; React/Jupyter/Node/CLI; Docker + GitHub import. | Complete interactive apps mid-lesson |
| **Terminal** | Ubuntu 16.04 live terminal, startup script, Docker integration. | Mongo/Postgres, CLI tools, anything needing shell |
| **GUI** | Java Swing / Python Tkinter windowed apps; file upload + Docker. | Teaching GUI programming |
| **Quiz** | MCQ, Fill-in-the-Blank, True/False. Per-option **Explanation** field. Multiple-correct mode. Question randomization pool. | Comprehension checks |
| **Drawing Tool** | UML / Venn / flowcharts / infographics, uploadable images. | Non-interactive diagrams |

**AI layer: "AI Code Mentor"** — 1:1 tutor-style feedback on submitted code, flags errors, explains time/space complexity. Separately, their "AI-assisted feedback" pitch is about comparing AI feedback with peer/mentor review *side-by-side* as a pedagogical tool, not just replacement.

**Course-authoring shape.** Courses are divided into modules → lessons. Lessons mix markdown prose + any of the above widgets inline. No fixed template — authors drop widgets where needed. This is more flexible than our exercise-type-per-step model.

### Codecademy (Learn the Command Line, Learn Git)

Sources: course pages for `/learn/learn-the-command-line`, `/learn/learn-git`, Codecademy Help Center articles.

**Learn the Command Line** (4h, 236k+ enrollees): 4 sections (Navigate / View+Change / Redirect / Configure), 3 named guided projects ("Bicycle World", "Artusi", "Athletica"). **Yes, real in-browser terminal.** Free tier gets core lessons + basic projects; Plus/Pro gates certificates, assessments, guided projects.

**Learn Git**: 6 lessons, 9 projects, 8 quizzes. Narrative projects ("SnapFit Robots" drafts customer docs; "Manhattan Zoo" tracks document changes; "ASCII Portfolio" practices commits). Projects get mentor-worthy pretense — they're not toy repos, they're pretend business scenarios.

**Lesson UI (three-panel):**
- Left: narrative + numbered step instructions
- Middle: code editor (or file tree if a terminal lesson)
- Right: output / terminal / preview

**Grading = SCT (Submission Correctness Tests).** Per-step checks. Wrong submission triggers an inline error message. Flow on stuck: **"Stuck? Get a Hint!"** button bottom-left of instructions. If still stuck → "Solution" reveal. Forum per-lesson for community help. "Get Unstuck" widget bottom-right spawns the AI Learning Assistant, which gives directional feedback (does NOT just reveal the answer — same Socratic-ish ethos as Boot.dev).

**Key pattern.** Each step is **TINY** — sometimes one line of code. 49-exercise courses mean each "exercise" takes 2-3 minutes. Step atomicity is their hallmark.

### Scrimba (scrims)

Sources: scrimba.com articles, podcast transcript, product reviews.

**The scrim primitive.** A scrim is NOT a video. It's a **recording of IDE events replayed** (keystrokes, cursor moves, file edits) with voice overlay. The player IS the IDE. Viewer can **pause at any moment and edit the instructor's code**. Resuming doesn't overwrite your edits. You can fork the instructor's state and run your own version.

**Course shape.** Scrims chunked into 2-5 min units. Module = sequence of scrims interleaved with **"Challenge" scrims** where the instructor says "now you take the keyboard" and the scrim hands control over. Many scrims have a solution scrim attached ("show me the answer").

**AI feedback.** Scrimba Pro's "Instant Feedback" checks solutions in real-time and gives directional guidance, not pass/fail. They explicitly frame this as "not cheating" — same Socratic philosophy.

**React course** (Bob Ziroll, 15h free): learners build 8 interactive React apps inside scrims. **Vibe Coding with Claude Code** (Scrimba's direct competitor to Educative's course) is in-browser scrim format — teaches hooks, slash commands, agents, MCP, builds a calendar app. Rated the "best interactive experience" for intermediate learners per Scrimba's own comparative article.

**AI Engineer Path** (11.4h, Pro): agents, RAG, MCP, context engineering, multimodality. JS-native. Free intro course "Intro to AI Engineering" (2.5h) opens by building a stock-analysis app from lesson 1 — **no preamble before hands-on**.

### Exercism

Sources: `/tracks/python`, `/tracks/python/concepts/strings`.

**Two-element model: Concepts + Exercises.** Python track = 17 concepts + 146 exercises. Concept pages = long-form narrative theory with inline code samples and external "Learn More" links. No interactivity on the concept page itself — "Unlock 4 more exercises to practice Strings" is a gate to the hands-on part.

**Exercises** are presented as narrative problems ("Creating a zipper for a binary tree", "Building a shopping cart MVP for the Mecha Munch grocery app"). Dual feedback: **automated code analyzer + human volunteer mentor** (6,598 mentors worldwide). Mentor feedback is the differentiator — written prose from a real developer.

**100% free forever.** No paid tier.

**Difficulty progression.** Concepts are gated behind prerequisite concepts. Each exercise tags difficulty + associated concepts. This is a dependency graph, not a linear sequence — learners can branch.

### Boot.dev

Sources: boot.dev/courses, lesson page e4fac74c-..., catalog.

**Catalog:** 50+ courses. Long courses: Python 179 lessons/30h, Go 189/20h, SQL 126/30h. Backend + DevOps tilt. "Guided Projects" = Pokedex CLI, blog aggregator, web scrapers, **AI agents (plural!)**, static site generators.

**UI per lesson:**
- Top/middle: lesson explanation text
- Code editor panel
- **Boots AI mentor** tab (below explanation, or a phone-bottom tab on mobile)
- Distinguished **Run** vs **Submit** buttons — explicitly documented: "Run the code (don't submit the code)" is step 1 of exercises, "ask Boots what's wrong" is step 2.
- No explicit hint/solution toggles. **Boots IS the hint system.** Using Boots before completion costs 1 salmon OR 50% XP (gamified penalty for pre-solve help).

**Gamification.** XP, levels, leaderboards, guilds. Platform total: 7.4B XP earned.

**Boots mentor.** Socratic method, trained NOT to give answers. Split 50/50 between GPT-4o and Sonnet 3.5 per conversation (A/B testing for pedagogical quality). Can auto-submit your feedback on the lesson. Best-in-class AI-mentor pedagogy we observed.

### DataCamp (exercise-type taxonomy)

Sources: Instructor Support Center, multiple articles.

**This is the most comprehensive public exercise-type catalog we found.** They define:

1. **Video Exercise** — slide deck + script recorded into a video. (Primary "lecture" unit.)
2. **Coding Exercise** — write and submit code; single step. Most common.
3. **Iterative Exercise** — variations on a single concept side-by-side. Good for "try these 5 variants of the same pattern."
4. **Sequential Exercise** — multi-step code that builds on itself; learner sees output between steps.
5. **Multiple Choice** — 3-5 options, **per-option feedback message**.
6. **Multiple Choice with Console** — MCQ + live code console as sandbox to test the hypothesis.
7. **Drag-and-Drop (Classify)** — sort items into buckets.
8. **Drag-and-Drop (Order)** — arrange items by criteria.
9. **Drag-and-Drop (Parsons)** — mixed code lines to arrange + indent.

**BI-course-specific types:**
10. **Conceptual Video** — slides + dynamic visuals.
11. **Demo Video** — screen-record of the BI software.
12. **Remote Desktop (VM) Exercise** — learner operates an actual **VM instance of the BI tool** (Tableau/PowerBI), then answers assessment questions. This is wild — they ship a remote desktop per exercise.

**Per-option feedback.** DataCamp explicitly says: hints should get the student 50% of the way; each Drag-and-Drop item has per-position error feedback; each MCQ option has its own explanation. **This is the most structured feedback taxonomy we saw.**

### freeCodeCamp

Sources: freecodecamp.org news posts on 2022+ curriculum redesign.

**Curriculum module = Lessons + Workshops + Labs + Review + Quiz.**
- **Lesson**: intro with new interactive editor for previewing code + 3 comprehension-check MCQs at the end.
- **Workshop**: guided step-by-step project.
- **Lab**: "list of user stories" + a test suite the learner must pass. Self-directed coding against specs.
- **Review**: consolidation page.
- **Quiz**: 20 MCQs, must score 18/20 to pass.

**Atomicity: extreme.** Each "step" in Responsive Web Design is one HTML tag. Learner does hundreds of steps to complete a project. Wrong answer = inline test failure with a short message. No AI mentor (they're purist about this).

### AI-coding-tool courses landscape

Most relevant competitors for our Claude Code course. Summary of the ones I dug into:

| Course | Platform | Format | Key pedagogy | Audience |
|---|---|---|---|---|
| **Claude Code in Action** (Anthropic official) | Skilljar | Video + labs, 4 sections (What/Hands-On/Hooks+SDK/Wrap) | Authoritative, dense, assumes dev skills | Developers integrating AI |
| **Claude Code: Software Engineering w/ Generative AI Agents** (Vanderbilt on Coursera) | Coursera | 6 modules / 5h / video + readings + 2 graded assessments | Framing-heavy: "AI Labor", "Best of N", "Chat/Craft/Scale"; multimodal prompting (sketch→code) | Intermediate SWE, tech leads |
| **Vibe Coding with Claude Code** (Scrimba) | Scrimba | Interactive scrim, in-browser | Learn-by-doing, builds calendar app, covers hooks/slash/agents/MCP | Intermediate |
| **CC for Everyone** (Carl Vellotti) | Self-hosted | **In-Claude-Code lessons** (`/start-1-1` kicks off) | Fully in-product: Claude guides you through inside Claude | Non-technical |
| **CC for PMs** (Carl Vellotti) | Self-hosted | In-Claude-Code, 26 lessons / 5 modules | PM-specific: PRDs, data analysis, competitive strategy; parallel agents + sub-agents | Non-dev PMs |
| **Claude Code for Real Engineers** (AI Hero / Matt Pocock) | Cohort | 2-week live + office hours, $795 | Plan/Execute/Clear, AGENTS.md, multi-phase planning, autonomous loops | Senior devs |
| **Claude Code: Building Faster with AI** (Udemy / Frank Kane) | Udemy | Video + project | Full production flow: prototype → unit tests → security → CI/CD | Production-focused |
| **Jupyter AI: AI Coding in Notebooks** (DeepLearning.AI) | DeepLearning.AI | Video + notebook demo + 3 projects | "Jupyternaut" in-notebook chatbot; build book-research assistant + stock analyzer | Data-coding crowd |
| **Anthropic Prompt Engineering Interactive Tutorial** (GitHub) | Jupyter notebooks | 9 chapters + appendix, beginner→advanced | Each lesson: concept + Example Playground cell + Exercises + Answer Key (Google Sheet) | Self-directed |
| **Anthropic API Fundamentals / Tool Use / Real World / Evals** | GitHub | Jupyter notebooks | Claude 3 Haiku for cost, SDK-centric | Dev |

**Critical pedagogical divergence observed:** the "in-Claude-Code" format (CC for Everyone, CC for PMs) is radical — learner installs Claude Code, clones course repo, types `/start-1-1`, and the AI itself is the teacher. **Zero videos. Zero docs.** The tool teaches use of the tool from inside the tool. This is the most pedagogically interesting format in the AI-coding space and is a direct competitor to us.

**What most AI-coding courses miss:**
- Realistic failure-mode drills (what to do when the agent goes sideways)
- Context-window economics under pressure
- Real multi-turn debugging where the agent misdiagnoses
- Cost-awareness (token economics)
- Security posture (unintended code execution, secrets, supply-chain)
- Team workflows (CLAUDE.md hygiene, branch-per-agent, review culture)

Vanderbilt/Coursera is strongest on framing but weakest on live hands-on. Scrimba is strongest on hands-on but weakest on production realism. AI Hero cohort fills the production gap but at $795 + 2-week commitment.

---

## 3. Cross-platform pattern observations (patterns on 3+ platforms)

### Pattern A: Three-panel lesson UI
**Seen on: Codecademy, Boot.dev, Educative, Scrimba, DataCamp, freeCodeCamp.** Left = narrative/instructions, Middle = editor, Right = output/terminal/preview. This is the *de facto* standard. Our terminal_exercise / code_exercise already ships this shape; good.

### Pattern B: Named AI mentor with Socratic guardrails
**Seen on: Boot.dev (Boots), Codecademy (AI Learning Assistant), Educative (AI Code Mentor), Scrimba (Instant Feedback).** Consistent framing: a personality-branded AI that **does not give the answer**, uses leading questions, often with a gamified cost (Boot.dev charges salmon/XP). This is now **table stakes**.

### Pattern C: Per-option / per-wrong-answer feedback
**Seen on: DataCamp (explicit), Educative (Quiz widget "Explanation" field per option), freeCodeCamp (per-test-case error).** The insight: every wrong path has its own pre-authored teaching moment, not a single "Try again." This is what makes a grader teach rather than gate.

### Pattern D: Atomic steps (one concept per step)
**Seen on: Codecademy (sub-minute steps), freeCodeCamp (hundreds of one-line steps), DataCamp (49 exercises / 4h course).** Step atomicity is the dominant shape for absolute beginners. Our platform tends toward larger steps — this is fine for intermediate/advanced, less great for true onboarding.

### Pattern E: Parsons problems / order-this-code
**Seen on: DataCamp (explicit Parsons type), freeCodeCamp (labs with user stories), Educative (via Drawing + Code), plus known in classic CS-ed literature.** We already have Parsons + Ordering. This is validated as a winning shape.

### Pattern F: Narrative scenario framing for projects
**Seen on: Codecademy (Bicycle World / SnapFit Robots / Manhattan Zoo), Exercism (Mecha Munch grocery app), Boot.dev (Pokedex CLI), Educative (PawPals booking app).** Never "build a todo app" — always "you've been hired by the Manhattan Zoo." This is cheap dressing that massively improves engagement. We do this partially on adaptive_roleplay / incident_console — we should extend it to every code_exercise project.

### Pattern G: Out-of-platform tool hand-off for AI courses
**Seen on: Educative (Lovable), DeepLearning.AI (Jupyter), CC for Everyone (inside Claude Code), Scrimba Vibe Coding (scrim-embedded IDE).** Nobody has solved the "embed Cursor/Claude Code into the lesson page" problem cleanly. Either they frame the learner out to the real tool (Educative, DLAI) or they frame the lesson INTO the tool (CC for Everyone). Cleanest pedagogy wins: going INTO the tool is more immersive.

### Pattern H: Comprehension-check MCQ after each concept
**Seen on: freeCodeCamp (3 MCQs after every lesson), Educative (mid-lesson MCQs), Coursera Claude Code (graded assessments per module), Anthropic API courses (self-check answer key).** Low-friction retention check. Our `mcq` type covers this; we could enforce it more consistently at the end of every concept step.

### Pattern I: Portfolio-oriented capstones with real artifact
**Seen on: Codecademy (96 portfolio projects per path), Boot.dev (guided projects become portfolio pieces), Educative (deploy to Vercel), DataCamp (final "data story" deliverable).** The artifact at the end matters. Our capstones are per-course already; ensuring each ends with a shareable artifact (URL, repo, blog post, Loom) is worth pushing.

### Pattern J: Dependency-graph course progression (not linear)
**Seen on: Exercism (concepts gate exercises via dependency graph), Boot.dev (track branching).** Most platforms are linear. The graph model lets adult learners skip what they know. We currently assume linear; could be worth reconsidering for larger courses.

---

## 4. Gaps vs our platform — concrete proposals

### Gap 1 — "Pair-programming scrim" format
- **What we have today:** `code_exercise` (static TODOs with validation) and `terminal_exercise` (live shell).
- **What they have that's better:** Scrimba's scrim lets the instructor narrate while you watch IDE events replay, then at any moment you take the keyboard, edit the instructor's code, and run your fork without losing state. That temporal blend of "watch → pause → edit → run → resume" is unmatched. For an AI-tools course this is especially strong: imagine watching an instructor prompt Claude Code, pausing mid-prompt to modify it, and seeing your variation run.
- **Where it fits:** NEW exercise type (`scrim_pair`) OR new UI mode on `code_exercise`. Could be simulated: pre-record a script of terminal commands + narration, replay with pause-points where learner mutates and re-runs.
- **Expected impact:** HIGH. No other platform except Scrimba does this and it's loved.
- **Source URLs:** https://scrimba.com/learn/learnreact, https://scrimba.com/vibe-coding-with-claude-code-c06fgn7ib3, https://survivejs.com/blog/scrimba-interview/

### Gap 2 — Per-wrong-answer teaching feedback (not just pass/fail)
- **What we have today:** Graders return correct/incorrect + a general `hint`. For MCQs we do have explanations. For code_exercise the feedback is often "didn't match expected output."
- **What they have that's better:** DataCamp hard-requires per-option MCQ feedback AND per-item drag-and-drop feedback. Educative's Quiz widget has a first-class `Explanation` field per option. freeCodeCamp has per-test-case error messages. The *wrong answer is a teaching moment*, not a gate.
- **Where it fits:** Prompt change — Creator prompt should require, for every code_exercise, a list of 3-5 **common wrong approaches** each with a bespoke explanation. For MCQ, enforce explanations on every option (wrong and correct). For Parsons/Ordering, include a "near-miss" explanation when the learner's arrangement is close but off.
- **Expected impact:** HIGH. Cheap to add (prompt edit), massive quality lift.
- **Source URLs:** https://instructor-support.datacamp.com/en/articles/2360969-exercise-types, https://www.educative.io/courses/author-guide/JY7Ew3NJGKK, https://instructor-support.datacamp.com/en/articles/3039578-drag-and-drop-exercise-anatomy

### Gap 3 — Narrative scenario framing as default, not optional
- **What we have today:** adaptive_roleplay and incident_console use rich scenarios with real names (Alex Chen, TechFlow CFO, Marcus Chen). Our typical `code_exercise` / `terminal_exercise` steps are often generic ("Write a function that returns X").
- **What they have that's better:** Codecademy never names a project generically — it's "SnapFit Robots drafts customer docs," "Manhattan Zoo tracks documents," "Athletica redirects output." Exercism's grocery-app-for-Mecha-Munch framing. Boot.dev's Pokedex CLI. Educative's PawPals booking app. The scenario wrapper makes mechanical exercises feel *like real work*.
- **Where it fits:** Prompt change to Creator — require every non-roleplay exercise to specify a scenario context (company / user / stakes) and reference it in task text, expected-output checks, and success message. Cheap and universal.
- **Expected impact:** MEDIUM-HIGH. Engagement lift across every single exercise type.
- **Source URLs:** https://www.codecademy.com/learn/learn-the-command-line, https://exercism.org/tracks/python, https://www.boot.dev/courses

### Gap 4 — "In-tool lessons" pedagogy for Claude Code course specifically
- **What we have today:** Our Claude Code / terminal_exercise runs in a sandbox the learner never leaves. Good, but Claude Code itself is the subject — and *the tool can narrate its own lessons*.
- **What they have that's better:** "CC for Everyone" (Carl Vellotti) is a course where the learner types `/start-1-1` inside Claude Code and Claude Code itself walks them through each lesson interactively. Course materials = a git repo. Teacher = the product being taught. Immersion: 10/10.
- **Where it fits:** NEW exercise-template pattern — for Claude Code / MCP / agent courses, generate courseware as `.claude/commands/*.md` slash commands + markdown lessons + task validators. The learner uses Claude Code to learn Claude Code. We could ship this as a course-type "in_tool_teach" that outputs a scaffold repo + validator the learner runs locally, with progress reported back.
- **Expected impact:** HIGH (for our Claude Code course specifically; MEDIUM elsewhere).
- **Source URLs:** https://ccforeveryone.com/, https://ccforpms.com/

### Gap 5 — Explicit Socratic AI-mentor layer
- **What we have today:** No in-lesson Claude mentor that guides-without-revealing. We have `adaptive_roleplay` but that's a *counterparty*, not a teacher.
- **What they have that's better:** Boot.dev's Boots (Socratic, trained to NOT give answers, gamified cost to use pre-completion). Codecademy's AI Learning Assistant ("instant, personalized feedback"). Educative's AI Code Mentor. Scrimba's Instant Feedback.
- **Where it fits:** NEW UI pattern — a "Tutor" chat panel attached to every step, with a hard system prompt that forbids answer-giving and enforces leading-question style. Our existing adaptive_roleplay infra can be re-skinned for this. Cost: ~$0.02/turn, same as current roleplay.
- **Expected impact:** MEDIUM-HIGH. Now considered table stakes by all major competitors.
- **Source URLs:** https://www.boot.dev/lessons/e4fac74c-9d67-41ad-a85c-c579cb3ad76f, https://www.boot.dev/blog/news/bootdev-beat-2023-10/

### Gap 6 — "Multiple Choice with Console" hybrid
- **What we have today:** `mcq` (no console) and `code_exercise` (no MCQ). Binary choice.
- **What they have that's better:** DataCamp's **Multiple Choice with Console** — learner sees an MCQ but has a full live Python/R console to experiment with snippets before committing. Pedagogically elegant: "here's a question, but also here's a playground to verify your hypothesis."
- **Where it fits:** NEW exercise type (`mcq_with_console`) OR parameter on existing MCQ. Useful for concept-checking in coding courses where "which of these produces X?" is better answered by trying it than by memorizing.
- **Expected impact:** MEDIUM. Genuinely new shape, not currently in our catalog.
- **Source URLs:** https://instructor-support.datacamp.com/en/articles/2375523-course-multiple-choice-with-console-exercises

### Gap 7 — Iterative exercise ("variations on a theme")
- **What we have today:** Single `code_exercise` with one expected output; if we want 5 variations, we create 5 steps.
- **What they have that's better:** DataCamp's **Iterative exercise** shows 5 variations of the same pattern in a grid, each runnable, each with its own check. The learner sees *the space of solutions* rather than one instance. Good for teaching mini-patterns (e.g., "five ways to handle tool-call retries").
- **Where it fits:** NEW exercise type (`iterative_variations`) — N mini-code-exercises in one step, each checkable independently, presented as a grid.
- **Expected impact:** MEDIUM. Good fit for prompt-engineering and tool-use pedagogy specifically, where pattern variations matter a lot.
- **Source URLs:** https://instructor-support.datacamp.com/en/articles/2360969-exercise-types

### Gap 8 — "Failure-first example" as a Creator prompt pattern
- **What we have today:** Concept steps tend to present the happy path, then exercises test it. Some adaptive_roleplay leads with a stressful scenario.
- **What they have that's better:** Educative's lessons OPEN with the failure case ("The AI was not lying. It built what it described. But the emails never sent"). Only after naming the pain do they teach the remedy. This makes the lesson *actually necessary* in the learner's mind.
- **Where it fits:** Prompt change — Concept-step prompt should require a "failure-first hook" (2-4 sentences: here's what goes wrong if you don't know this) before the explanation.
- **Expected impact:** MEDIUM. Increases concept retention; pure prompt edit.
- **Source URLs:** https://www.educative.io/courses/learn-vibe-coding/reading-ai-output-and-debugging, https://www.educative.io/courses/learn-vibe-coding/prompt-craft

### Gap 9 — Named "core rule" per lesson
- **What we have today:** Concept steps have titles + content but no mandated memorable core rule.
- **What they have that's better:** Educative's Prompt Craft compresses the lesson to: *"One thing. Sometimes two if they are closely related, but almost never three."* A chantable rule. The rest of the lesson is scaffolding for that rule.
- **Where it fits:** Prompt change — every concept step must include a single ≤20-word "core rule" rendered in a highlighted box. Same primitive Educative uses.
- **Expected impact:** MEDIUM. Memorability lift; very cheap to add.
- **Source URLs:** https://www.educative.io/courses/learn-vibe-coding/prompt-craft

### Gap 10 — Gamified cost to use AI help
- **What we have today:** Help/hints are free.
- **What they have that's better:** Boot.dev charges "1 salmon OR 50% XP" to consult Boots before completing a lesson. This tunes the incentive — learners try first, ask second. Codecademy's Solution reveal is a one-way door. Scrimba's solution-scrim is counted against completion.
- **Where it fits:** New UI gating pattern; can be A/B tested. Our existing progress/score tracking can carry this.
- **Expected impact:** LOW-MEDIUM. Mainly for retention mechanics rather than pedagogy per se.
- **Source URLs:** https://www.boot.dev/lessons/e4fac74c-9d67-41ad-a85c-c579cb3ad76f

### Gap 11 — VM / remote-desktop for non-code tools
- **What we have today:** Sandboxed terminal is great for CLI work. Our voice/adaptive_roleplay covers non-code domains.
- **What they have that's better:** DataCamp's **Remote Desktop Exercise** — learner operates an actual VM running Tableau/PowerBI and the lesson grades what they did there. For teaching an IDE, a GUI tool, or *Claude Desktop*, this shape is unbeatable.
- **Where it fits:** NEW exercise type (`vm_gui_exercise`). High infra cost. Probably a "someday" — only worth it if we expand to non-CLI tool courses.
- **Expected impact:** LOW (right now). Would jump to HIGH if we add a GUI-tool course (Claude Desktop, Cursor, VS Code extensions).
- **Source URLs:** https://instructor-support.datacamp.com/en/articles/5445749-overview-of-the-exercise-types-for-bi-courses

### Gap 12 — Answer-key self-check (Anthropic notebook style)
- **What we have today:** Auto-grading with hidden solution.
- **What they have that's better:** Anthropic's Prompt Engineering Interactive Tutorial ships a **Google Sheet answer key** learners can consult for self-grading. Sometimes pedagogy is better served by "here's the answer, check yourself" than by a gatekeeping grader, especially for open-ended prompting exercises where there isn't one right answer.
- **Where it fits:** New exercise variant for prompt-engineering-style steps where *any of many answers are acceptable* — show a reference answer + 2-3 alternative good answers, let learner self-assess.
- **Expected impact:** MEDIUM (specifically for our prompt-engineering / AI-tool lessons).
- **Source URLs:** https://github.com/anthropics/prompt-eng-interactive-tutorial

### Gap 13 — Multi-tool / multi-agent course framing
- **What we have today:** Courses are single-domain; no course I know of teaches "orchestrating 3 agents at once."
- **What they have that's better:** Boot.dev has guided projects titled "AI agents" (plural). Scrimba's AI Engineer Path covers MCP + context engineering + multimodality. Vanderbilt/Coursera Claude Code teaches "AI Labor" (Claude as a team, Best-of-N pattern). CC for PMs covers "parallel agent workflows + custom sub-agents."
- **Where it fits:** NEW course template for Claude Code specifically — a "parallel agents" lesson where the learner spins up 3 sub-agents, coordinates their outputs, then reviews. Fits `simulator_loop` umbrella primitive + a new UI to visualize parallel agent states.
- **Expected impact:** HIGH for the Claude Code course specifically.
- **Source URLs:** https://aihero.dev/cohorts/claude-code-for-real-engineers-2026-04, https://www.coursera.org/learn/claude-code, https://ccforpms.com/

---

## 5. Top 5 actionable ideas (ranked)

1. **Require per-wrong-answer teaching feedback on every gradable step.** Prompt edit to Creator: MCQs get explanations on every option (right AND wrong); code_exercises must pre-author 3-5 common wrong approaches each with a bespoke teaching message; Parsons/Ordering get near-miss feedback. This is THE difference between a grader that gates and a grader that teaches — and 3+ top platforms make it mandatory. Cheap prompt change, transformative quality lift. (Gap 2)

2. **Launch an "in-tool lessons" format for the Claude Code course.** Generate courseware as `.claude/commands/*.md` slash commands + markdown lessons + local validators. Learner types `/start-1-1` inside Claude Code and Claude Code itself teaches Claude Code. This is how CC-for-Everyone and CC-for-PMs work and it's the pedagogical apex of the Claude Code teaching space. (Gap 4)

3. **Add a "scrim pair-programming" exercise type.** Record a scripted narration + terminal command sequence; learner can pause at named checkpoints, mutate the instructor's state, re-run, and resume. Particularly powerful for teaching Claude Code prompting — watch an expert prompt, pause, edit the prompt, see your variation. Scrimba has proven this format wins. No other AI-coding course has it. (Gap 1)

4. **Default every exercise to a named scenario + stakes, not a generic task.** Prompt edit: every code_exercise, terminal_exercise, parsons step gets a scenario wrapper (company name, user, stakes). Codecademy, Exercism, Boot.dev, and Educative all do this by default; we do it inconsistently. Zero engineering, big engagement gain. (Gap 3)

5. **Add a Socratic AI-tutor panel to every lesson.** Reuse our adaptive_roleplay infra with a system prompt that forbids direct answer-giving, pushes Socratic questions, costs score-points to invoke before step completion. Boot.dev's Boots + Codecademy's AI Assistant + Educative's AI Code Mentor + Scrimba's Instant Feedback all converge on this shape — it's now table stakes. Our infra already supports the per-turn LLM cost (~$0.02/turn matches current roleplay). (Gap 5)

---

## Sources

- [Educative — Learn Vibe Coding: What Is Vibe Coding?](https://www.educative.io/courses/learn-vibe-coding/what-is-vibe-coding)
- [Educative — Learn Vibe Coding: Your First Build](https://www.educative.io/courses/learn-vibe-coding/your-first-build)
- [Educative — Learn Vibe Coding: Prompt Craft](https://www.educative.io/courses/learn-vibe-coding/prompt-craft)
- [Educative — Learn Vibe Coding: Reading AI Output and Debugging](https://www.educative.io/courses/learn-vibe-coding/reading-ai-output-and-debugging)
- [Educative — Learn Vibe Coding: How Software Actually Works](https://www.educative.io/courses/learn-vibe-coding/how-software-actually-works)
- [Educative — Widget Workshop (all widget types)](https://www.educative.io/courses/educative-widget-workshop/widgets-and-visuals)
- [Educative — Quiz Widget docs](https://www.educative.io/courses/author-guide/JY7Ew3NJGKK)
- [Codecademy — Learn the Command Line](https://www.codecademy.com/learn/learn-the-command-line)
- [Codecademy — Learn Git](https://www.codecademy.com/learn/learn-git)
- [Codecademy — Full-Stack Engineer Career Path](https://www.codecademy.com/learn/paths/full-stack-engineer-career-path)
- [Scrimba — Vibe Coding with Claude Code / Claude Code tutorials comparison](https://scrimba.com/articles/best-claude-code-tutorials-and-courses-in-2026/)
- [Scrimba — Best AI Agent courses 2026](https://scrimba.com/articles/best-courses-to-learn-ai-agents-and-agentic-ai-in-2026/)
- [Scrimba — Learn React](https://scrimba.com/learn/learnreact)
- [Scrimba interview (SurviveJS)](https://survivejs.com/blog/scrimba-interview/)
- [Exercism — Python track](https://exercism.org/tracks/python)
- [Exercism — Strings concept page](https://exercism.org/tracks/python/concepts/strings)
- [Boot.dev — Course catalog](https://www.boot.dev/courses)
- [Boot.dev — Sample lesson page](https://www.boot.dev/lessons/e4fac74c-9d67-41ad-a85c-c579cb3ad76f)
- [DataCamp — Exercise types](https://instructor-support.datacamp.com/en/articles/2360969-exercise-types)
- [DataCamp — BI course exercise types](https://instructor-support.datacamp.com/en/articles/5445749-overview-of-the-exercise-types-for-bi-courses)
- [DataCamp — Drag and Drop anatomy](https://instructor-support.datacamp.com/en/articles/3039578-drag-and-drop-exercise-anatomy)
- [DataCamp — MCQ with Console](https://instructor-support.datacamp.com/en/articles/2375523-course-multiple-choice-with-console-exercises)
- [Anthropic Skilljar — Claude Code in Action](https://anthropic.skilljar.com/claude-code-in-action)
- [Coursera — Claude Code (Vanderbilt)](https://www.coursera.org/learn/claude-code)
- [CC for Everyone](https://ccforeveryone.com/)
- [CC for PMs](https://ccforpms.com/)
- [AI Hero — Claude Code for Real Engineers](https://www.aihero.dev/cohorts/claude-code-for-real-engineers-2026-04)
- [DeepLearning.AI — ChatGPT Prompt Engineering for Developers](https://learn.deeplearning.ai/courses/chatgpt-prompt-eng/lesson/dfbds/introduction)
- [DeepLearning.AI — Jupyter AI: AI Coding in Notebooks](https://learn.deeplearning.ai/courses/jupyter-ai-coding-in-notebooks)
- [GitHub — anthropics/courses](https://github.com/anthropics/courses)
- [GitHub — anthropics/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial)
