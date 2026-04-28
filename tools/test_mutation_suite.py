"""Mutation suite — Opus's regression seal for the bug class.

Each test introduces a single fabrication into a synthetic LLM step output
and asserts the pipeline catches it. Initially most fail (Track A + B
not built yet); each track build flips one or more tests green.

Pass-rate over time = "% of bug class structurally closed". When all 5
green, ship the next regen sweep with confidence that the platform won't
silently accept these fabrications again.

Categories:
  - Closed-set facts (registry-derivable) → Track B token substitution
    catches via gate-time rejection of literal values + post-LLM swap.
  - Open-set facts (repo-state-derivable) → Track A gh-api validator
    catches by hitting actual GitHub + asserting the reference exists.

Run as:  python3 -m tools.test_mutation_suite
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Test fixtures: synthetic LLM step outputs containing fabrications ──

# Mutation 1 — Closed-set: LLM emits semantic-key instead of branch name
# (the v7 NEW-P0-A bug class — `git checkout first-fix` in prose).
# Track B catches: gate REJECTS literal "first-fix" because it's a registry
# KEY not a value. Or the substitutor swaps {{MODULE_BRANCH}} for the
# correct branch deterministically.
MUTATION_1_SEMANTIC_KEY_AS_BRANCH = {
    "name": "MUT-1: kimi step prose says `git checkout first-fix` instead of `module-1-starter`",
    "course_slug": "kimi",
    "module_position": 2,  # M1 — "Feel the Pain"
    "candidate_step": {
        "demo_data": {
            "instructions": (
                "<h3>Phase 1: Set up</h3>"
                "<p>Clone the starter repo, then check out the branch:</p>"
                "<pre>git clone https://github.com/tusharbisht/kimi-eng-course-repo && "
                "cd kimi-eng-course-repo && "
                "git checkout first-fix</pre>"  # ← BUG: "first-fix" is a registry key, not a branch
                "<p>Then run aider…</p>"
            ),
        },
        "validation": {
            "cli_commands": [
                {"cmd": "git rev-parse --abbrev-ref HEAD",
                 "expect": "first-fix", "label": "On the M1 branch"},  # ← BUG: same issue
            ],
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["first-fix", "branch"],
}


# Mutation 2 — Open-set: LLM hallucinates a path that doesn't exist in the
# actual repo on the relevant branch. (jspring 85115 v7: `orders/` plural
# vs real `order/` singular.)
# Track A catches: gh api contents/<path>?ref=<branch> returns 404 → reject.
MUTATION_2_PATH_DRIFT = {
    "name": "MUT-2: jspring step references com/skillslab/jspring/orders/ (plural; real is order/)",
    "course_slug": "jspring",
    "module_position": 2,  # M1 — module-1-starter branch
    "candidate_step": {
        "validation": {
            "cli_commands": [
                {
                    "cmd": "grep -rE '@EntityGraph' src/main/java/com/skillslab/jspring/orders/",
                    "expect": "@EntityGraph",
                    "label": "Eager-load applied",
                },
            ],
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": [
        "com/skillslab/jspring/orders/",  # the path that doesn't exist
        "404",  # OR similar evidence the validator hit github
    ],
}


# Mutation 3 — Open-set: LLM invents a CLI flag for Claude Code that
# doesn't exist. (jspring 85133 v7: `claude --message`; real is `claude -p`.)
# Track A catches: every <flag> in cli_commands cross-checked against
# verified_facts_data; --message not in Claude Code's verified flag list.
MUTATION_3_FABRICATED_CLAUDE_FLAG = {
    "name": "MUT-3: cli_command uses `claude --message` (real flag is `claude -p` / `--print`)",
    "course_slug": "jspring",
    "module_position": 6,  # M5 — MCP module
    "candidate_step": {
        "validation": {
            "cli_commands": [
                {
                    "cmd": 'claude --message "use the team-tickets MCP to plan next ticket"',
                    "expect": "team-tickets|payments-api",
                    "label": "MCP-aware planning",
                },
            ],
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["--message", "claude"],
}


# Mutation 4 — Open-set: LLM invents a Java test class name. (jspring 85136 v7:
# `OrdersControllerTest`; real class is `OrdersControllerIntegrationTest`.)
# Track A catches: grep the actual repo's src/test/java for the class name.
# Not present → reject.
MUTATION_4_FABRICATED_CLASS_NAME = {
    "name": "MUT-4: cli_command references OrdersControllerTest (real is OrdersControllerIntegrationTest)",
    "course_slug": "jspring",
    "module_position": 7,  # M6 — capstone
    "candidate_step": {
        "validation": {
            "cli_commands": [
                {
                    "cmd": "./mvnw test -Dtest=OrdersControllerTest",
                    "expect": "BUILD SUCCESS",
                    "label": "Tests pass",
                },
            ],
            "must_contain": ["OrdersControllerTest"],
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["OrdersControllerTest"],
}


# Mutation 5 — Open-set: LLM invents a GHA grading_job name that doesn't
# match the actual workflow file. (kimi 85166 v7: `test-orders` vs real `grade`.)
# Track A catches: fetch lab-grade.yml from repo + parse YAML for jobs[*]
# keys → assert grading_job in that set.
MUTATION_5_FABRICATED_GHA_JOB = {
    "name": "MUT-5: gha_workflow_check.grading_job is `test-orders` (real workflow job is `grade`)",
    "course_slug": "kimi",
    "module_position": 7,  # M6 — capstone
    "candidate_step": {
        "validation": {
            "gha_workflow_check": {
                "repo_template": "tusharbisht/kimi-eng-course-repo",
                "workflow_file": "lab-grade.yml",
                "expected_conclusion": "success",
                "grading_job": "test-orders",  # ← BUG: real job is `grade`
            },
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["test-orders", "grading_job"],
}


# ── Negative controls — known-good outputs that MUST pass ──

NEGATIVE_1_CORRECT_BRANCH = {
    "name": "NEG-1: prose says `git checkout module-1-starter` (correct value, not key)",
    "course_slug": "kimi",
    "module_position": 2,
    "candidate_step": {
        "demo_data": {
            "instructions": (
                "<pre>git clone https://github.com/tusharbisht/kimi-eng-course-repo "
                "&& cd kimi-eng-course-repo "
                "&& git checkout module-1-starter</pre>"
            ),
        },
    },
    "expected": "ACCEPT",
}


# Mutation 6 — Tool-invocation pattern: LLM emits `claude code "<prompt>"`
# treating `code` as a subcommand. Real Claude Code is INTERACTIVE — you
# type `claude` to start a session, then type the prompt at the > prompt.
# `claude code "..."` doesn't exist; closest is `claude -p "..."` for
# one-shot non-interactive mode. (jspring M1.S2 v7 user-reported.)
# Track A would catch via subcommand whitelist (verified_facts extension).
MUTATION_6_FABRICATED_CLAUDE_SUBCOMMAND = {
    "name": "MUT-6: instructions/cli_commands use `claude code \"<prompt>\"` (real: `claude -p \"<prompt>\"` for one-shot, OR `claude` interactive)",
    "course_slug": "jspring",
    "module_position": 2,
    "candidate_step": {
        "demo_data": {
            "instructions": (
                "<h4>Step 3: Use Claude Code to fix the bug</h4>"
                "<pre>$ claude code \"Fix the N+1 query bug in OrderService.getRecentOrders()\"</pre>"
            ),
        },
        "validation": {
            "cli_commands": [
                {"cmd": 'claude code "Fix the N+1 query bug"', "expect": "EntityGraph", "label": "Claude fixes the bug"},
            ],
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["claude code", "subcommand", "claude -p"],
}


# Mutation 7 — Rubric coherence: rubric demands TWO unrelated deliverables
# (the N+1 fix AND a free-text style-observations.txt file). The two are
# different pedagogical surfaces and the partial-credit ladder mixes them.
# Per CLAUDE.md §"PREFER terminal_exercise / system_build / code_exercise
# — hands-on > read-and-answer", rubrics that grade subjective "your
# observations" prose-paste are an anti-pattern: they're rubric-graded LLM
# judgments masquerading as objective tests.
MUTATION_7_INCOHERENT_RUBRIC_TWO_DELIVERABLES = {
    "name": "MUT-7: rubric mixes objective N+1 fix with subjective style-observations.txt grading",
    "course_slug": "jspring",
    "module_position": 2,
    "candidate_step": {
        "validation": {
            "rubric": (
                "The output should show: (1) learner is on the first-fix branch, "
                "(2) OrderService.java contains @EntityGraph or JOIN FETCH to fix the "
                "N+1, (3) style-observations.txt file exists with meaningful content "
                "documenting Claude's style choices. Full credit (1.0) for all three; "
                "partial (0.7) if N+1 fix present but observations are minimal."
            ),
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["DEPRECATED", "subjective", "objective"],
}


# Mutation 8 — Subjective grading anti-pattern: rubric grades on
# "observations / writing style / documenting" — exactly the read-and-answer
# pedagogy CLAUDE.md flags as low-priority. Detection: scan rubric prose
# for subjective-judgment markers ("your observations", "documenting",
# "writing style", "your notes"). Reject; force the rubric to objective
# checks (file presence, regex match, test pass/fail).
MUTATION_8_SUBJECTIVE_GRADING_ANTIPATTERN = {
    "name": "MUT-8: rubric grades on 'your observations' / 'writing style' / 'documenting' (subjective, not objective)",
    "course_slug": "jspring",
    "module_position": 2,
    "candidate_step": {
        "validation": {
            "rubric": (
                "Full credit if the learner documents Claude's style choices in their "
                "notes file with meaningful observations about the conventions Claude "
                "missed. Partial credit if observations are minimal. Zero if no "
                "documentation provided."
            ),
        },
    },
    "expected": "REJECT",
    "expected_failure_reason_contains": ["subjective", "observations"],
}


# Negative control 2 — instructions HTML using the CORRECT real branch name
# (proves Track B's instructions-HTML scope catches issue #1 from user).
NEGATIVE_2_INSTRUCTIONS_HTML_CORRECT_BRANCH = {
    "name": "NEG-2: instructions HTML correctly uses real branch name `module-1-starter`",
    "course_slug": "jspring",
    "module_position": 2,
    "candidate_step": {
        "demo_data": {
            "instructions": (
                "<h4>Step 1: Clone</h4>"
                "<pre>$ git clone https://github.com/tusharbisht/jspring-course-repo "
                "&& cd jspring-course-repo "
                "&& git checkout module-1-starter</pre>"
            ),
        },
    },
    "expected": "ACCEPT",
}


ALL_MUTATIONS = [
    MUTATION_1_SEMANTIC_KEY_AS_BRANCH,
    MUTATION_2_PATH_DRIFT,
    MUTATION_3_FABRICATED_CLAUDE_FLAG,
    MUTATION_4_FABRICATED_CLASS_NAME,
    MUTATION_5_FABRICATED_GHA_JOB,
    MUTATION_6_FABRICATED_CLAUDE_SUBCOMMAND,
    MUTATION_7_INCOHERENT_RUBRIC_TWO_DELIVERABLES,
    MUTATION_8_SUBJECTIVE_GRADING_ANTIPATTERN,
    NEGATIVE_1_CORRECT_BRANCH,
    NEGATIVE_2_INSTRUCTIONS_HTML_CORRECT_BRANCH,
]


def run_pipeline_check(test: dict) -> tuple[str, str]:
    """Runs the (in-progress) pipeline against a synthetic candidate step.

    Returns:
      (verdict, reason) where verdict is "ACCEPT" / "REJECT" / "ERROR"
    """
    try:
        from backend.output_validator import validate_step_candidate
    except ImportError:
        return "ERROR", "backend.output_validator not yet built (Track A pending)"
    try:
        result = validate_step_candidate(
            candidate=test["candidate_step"],
            course_slug=test["course_slug"],
            module_position=test["module_position"],
        )
        if result.ok:
            return "ACCEPT", "all checks passed"
        return "REJECT", result.reason
    except Exception as e:
        return "ERROR", f"pipeline raised: {e}"


def main() -> int:
    print(f"Mutation suite — {len(ALL_MUTATIONS)} test cases")
    print()
    passed = 0
    failed = 0
    for t in ALL_MUTATIONS:
        verdict, reason = run_pipeline_check(t)
        expected = t["expected"]
        ok = (verdict == expected)
        if ok and expected == "REJECT":
            # Also assert the rejection reason names the offending fact
            keywords = t.get("expected_failure_reason_contains", [])
            missing = [k for k in keywords if k not in reason]
            if missing:
                ok = False
                reason = f"REJECTED but reason missing keywords {missing}: {reason!r}"
        flag = "✅" if ok else "❌"
        print(f"  {flag} {t['name']}")
        print(f"     expected={expected} got={verdict}: {reason[:200]}")
        if ok:
            passed += 1
        else:
            failed += 1
    print()
    print(f"=== {passed}/{passed + failed} PASS — bug class closure: {100 * passed // (passed + failed)}% ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
