# Grading Skeletons — universal grader contract for code-shape courses

This directory hosts per-language reusable grading scaffolds. Each
skeleton implements the **same contract** so the LMS, GHA workflows,
and the VS Code extension can grade any course in any language by
executing one command and reading one stdout line.

## The universal contract

Every `run-grading.sh` (regardless of language) MUST:

1. **Accept an exercise-dir argument**: `bash .grading/run-grading.sh exercise-NN-<slug>`.
   The LMS-emitted cli_command always passes the exercise dir explicitly;
   the runner does NOT auto-detect from branch.

2. **Stage the exercise's hidden tests** from `.grading/<exercise-dir>/`
   into the project's test path. Trap on EXIT to always unstage.

3. **Run the language-default test runner** wrapped in `timeout 120s`.
   For `java-spring`: `timeout 120s mvn -B -q test`. For `python-pytest`:
   `timeout 120s pytest tests/ --json-report ...`. Etc.

4. **Emit the RESULT protocol** to stdout (the LMS reads ONLY this — no
   language-specific parsing needed at the LMS layer):
   ```
   RESULT: PASS                          # final line; exactly one
   RESULT: FAIL                          # OR this; exactly one
   FAILED: <test_name> - <one-line msg>  # 0 or more, before RESULT line
   ```
   Plus `grading-result.json` (machine-readable detail) for richer UIs.

5. **Exit 0 if RESULT: PASS, non-0 if RESULT: FAIL.** Exit code is the
   redundant signal for callers that don't read stdout.

6. **Support `verify.sh` exercises**: if `.grading/<exercise-dir>/verify.sh`
   exists, run it directly (exit code is the signal). This handles
   non-test-framework exercises (slash commands, MCP wiring, hooks
   editing, JSON shape validation) without a per-type LMS exercise
   variant.

7. **Stay hidden by default**: directory is dot-prefixed (`.grading/`)
   and `.gitattributes` marks it `linguist-vendored` so it collapses
   in GitHub's UI. Social contract: learners don't peek. Encryption is
   a Phase 2 concern.

## What lives where

| Layer | Lives in | Reused across |
|---|---|---|
| **Pattern** | this `tools/grading-skeletons/README.md` | every language, every course |
| **Per-language skeleton** | `tools/grading-skeletons/<lang>/` | every course in that language |
| **Per-course `.grading/`** | course-repo `<root>/.grading/` | every exercise in that course |
| **Per-exercise hidden test** | course-repo `<root>/.grading/<exercise-dir>/` | one exercise |

## Adding a new language

1. Create `tools/grading-skeletons/<lang>/` with: `run-grading.sh`,
   `scripts/{stage,unstage,parse-<runner>}.sh`, `exercise-template/`
   showing what a hidden test looks like in this language.
2. The `parse-<runner>.sh` MUST consume the test runner's structured
   output (JUnit XML, pytest --json-report, jest --json, go test -json,
   cargo --message-format=json) — never regex on prose.
3. The `parse-<runner>.sh` MUST emit the RESULT protocol to stdout +
   write `grading-result.json` with the machine-readable detail.
4. Add a smoke test that runs the skeleton against a fixture and
   asserts the RESULT lines + exit code.

## Adding a new course (in an existing language)

1. Copy `tools/grading-skeletons/<lang>/` → `course-repo/.grading/`.
2. Write `<course-repo>/.grading/<exercise-NN-slug>/Hidden*GradingTest.<ext>`
   per code-fix exercise.
3. Write `<course-repo>/.grading/<exercise-NN-slug>/verify.sh` per
   non-test-framework exercise (slash command, MCP, hooks, etc.).
4. Push to all module branches.
5. Register in `backend/course_assets.py`:
   ```python
   CourseAsset(
       slug="<course>",
       course_repo="<gh-owner>/<repo>",
       module_branches={...},
       grading_runner="bash .grading/run-grading.sh",
       grading_test_lang="java",  # or python, node, go, rust, ruby
   )
   ```
6. The Creator prompt's rule #14 picks up `grading_runner` and emits
   the generic shape for every code-fix `terminal_exercise` step.

## CI invariant (per course-repo)

Every course-repo's GHA workflow MUST run
`.grading/scripts/verify-invariants.sh` on PRs:
- For every `module-N-starter` branch: hidden tests MUST FAIL (proves
  the bug exists).
- For every `module-N-solution` branch: hidden tests MUST PASS (proves
  the canonical fix works).

Without this, decorative test classes (`assertTrue(true)`) can drift
into the repo and the LMS rubric becomes meaningless. CI catches it
before merge.

## Why this architecture

See `CLAUDE.md`:
- §"BEHAVIORAL TEST HARNESS — the test class IS the rubric"
- §"OUTCOME, NOT JOURNEY"
- §"NO REGEX UNLESS WHITELISTED"
- §"EXECUTION IS GROUND TRUTH"

These rules collectively say: grading is a deterministic property of
running the test runner against the SUT; the LMS rubric is plumbing,
not pedagogy. This directory's skeletons are how that principle becomes
infrastructure.

## References

- Inspiration: github.com/tusharbisht/claude-code-springboot-exercises
- Buddy-Opus design review: 2026-04-28 (see chat transcript)
