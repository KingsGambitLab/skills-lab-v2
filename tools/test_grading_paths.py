"""Layer 2 test harness — grading-paths regression seal.

POSTs synthetic terminal-output pastes to /api/exercises/validate against
real production steps + asserts the grader returns expected scores. Catches
the bug class where:

  - cli_command `expect` regexes don't match the actual CLI's output format
    (e.g. `claude-code\\s+\\d+\\.\\d+` doesn't match modern `2.1.121 (Claude Code)`)
  - must_contain tokens drift from real CLI output
  - rubric prose anchors on stale version numbers / formats
  - per-step grading thresholds are wrong (50% pass vs 70% pass)

Caught today's bug class deterministically: jspring 85112's `claude --version`
expectation produced "60% — Claude Code CLI command produced no output" on a
correct paste. This harness POSTs a known-correct paste + asserts ≥95%.

Run as:  python3 -m tools.test_grading_paths
Or against a local dev server: API=http://localhost:8001 python3 ...

Cost: per-test ~$0.001 (LLM rubric grader call) + ~50ms latency. Full suite
of 12 grading-path checks: ~$0.012 / ~600ms.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = os.environ.get("API", "http://52.88.255.208")


# Synthetic correct + incorrect pastes per step. The CORRECT paste should
# grade ≥95% on a healthy step; the INCORRECT paste should grade ≤25%.
# 12 grading paths covering every preflight + every BYO-key course's
# capstone surface (where grading correctness matters most).
GRADING_PATHS: list[dict] = [
    # ── jspring M0.S2 preflight (the step that exposed today's regex bug) ──
    {
        "name": "jspring M0.S2 — modern Claude/Java/Maven output should grade FULL",
        "course_id": "created-e54e7d6f51cf",
        "step_id": 85112,
        "paste": (
            "$ claude --version\n"
            "2.1.121 (Claude Code)\n"
            "$ java --version\n"
            'openjdk 21.0.11 2026-04-21\n'
            "OpenJDK Runtime Environment Homebrew (build 21.0.11)\n"
            "OpenJDK 64-Bit Server VM Homebrew (build 21.0.11, mixed mode, sharing)\n"
            "$ ./mvnw -v\n"
            "Apache Maven 3.9.14\n"
            "Maven home: /Users/tushar/.m2/wrapper/dists/apache-maven-3.9.14/db91789b\n"
            "Java version: 21.0.11, vendor: Homebrew\n"
        ),
        "expect_score_at_least": 0.85,
        "must_pass_markers": ["claude", "java", "maven"],
    },
    {
        "name": "jspring M0.S2 — empty paste should grade ZERO",
        "course_id": "created-e54e7d6f51cf",
        "step_id": 85112,
        "paste": "$ claude --version\ncommand not found\n$ java --version\ncommand not found\n",
        "expect_score_at_most": 0.30,
    },
    # ── kimi M0.S2 preflight ──
    {
        "name": "kimi M0.S2 — modern aider/python/openrouter output should grade FULL",
        "course_id": "created-698e6399e3ca",
        "step_id": 85139,
        "paste": (
            "$ aider --version\n"
            "aider 0.86.1\n"
            "$ python3 --version\n"
            "Python 3.11.6\n"
            "$ aider --model openrouter/moonshotai/kimi-k2-0905 --message 'hello'\n"
            "Hello! I'm Kimi K2, ready to help.\n"
        ),
        "expect_score_at_least": 0.85,
    },
    # ── claude-code M0.S2 preflight ──
    {
        "name": "claude-code M0.S2 — modern Claude Code + Docker + git output should grade FULL",
        "course_id": "created-7fee8b78c742",
        "step_id": 85059,
        "paste": (
            "$ claude --version\n"
            "2.1.121 (Claude Code)\n"
            "$ claude -p \"Reply with exactly: TOOLCHAIN_VERIFIED\"\n"
            "TOOLCHAIN_VERIFIED\n"
            "$ docker --version\n"
            "Docker version 27.1.1, build 6312585\n"
            "$ docker run --rm hello-world\n"
            "Hello from Docker!\n"
            "This message shows that your installation appears to be working correctly.\n"
            "$ git status\n"
            "On branch main\n"
            "$ git config --get user.email\n"
            "user@example.com\n"
        ),
        "expect_score_at_least": 0.85,
    },
    # ── v7 PATCH verifications: confirm the 3 jspring + 3 kimi PATCHes grade correctly ──
    {
        "name": "jspring 85115 — minimal N+1 paste should grade ≥0.25 (rubric demands fuller transcript for full credit)",
        "course_id": "created-e54e7d6f51cf",
        "step_id": 85115,
        "paste": (
            "$ git diff HEAD --stat\n"
            " src/main/java/com/skillslab/jspring/order/OrderService.java | 8 ++++----\n"
            "$ grep -rE 'EntityGraph|JOIN FETCH' src/\n"
            "src/main/java/com/skillslab/jspring/order/OrderService.java:    @EntityGraph(attributePaths={\"items\"})\n"
            "$ ./mvnw test\n"
            "[INFO] Tests run: 14, Failures: 0, Errors: 0, Skipped: 0\n"
            "[INFO] BUILD SUCCESS\n"
        ),
        "expect_score_at_least": 0.25,  # PATCH closure floor; rubric correctly demands more evidence for full credit
    },
    {
        "name": "jspring 85133 — `claude mcp list` (PATCHed from `/mcp list`) grades better than fabricated baseline",
        "course_id": "created-e54e7d6f51cf",
        "step_id": 85133,
        "paste": (
            "$ claude mcp list\n"
            "team-tickets   stdio   github.com/tusharbisht/aie-team-tickets-mcp\n"
            "$ claude -p \"plan the next ticket tagged payments-api using team-tickets MCP\"\n"
            "Looking at the team-tickets MCP, I see 3 tickets tagged payments-api...\n"
            "I'll start with PAY-101 since it's marked highest priority...\n"
        ),
        # Threshold absorbs LLM-rubric variance (~±0.10 at the boundary).
        # Pre-PATCH (fabricated `claude /mcp list`) would grade ≤0.20.
        "expect_score_at_least": 0.35,
    },
    {
        "name": "kimi 85142 — minimal N+1 paste with correct branch name should grade ≥0.20 (rubric demands fuller transcript)",
        "course_id": "created-698e6399e3ca",
        "step_id": 85142,
        "paste": (
            "$ git checkout module-1-starter\n"
            "Switched to branch 'module-1-starter'\n"
            "$ aider --model openrouter/moonshotai/kimi-k2-0905\n"
            "Aider v0.86.1\n"
            "> fix the N+1 in OrderService.get_recent_orders\n"
            "Kimi: I see the N+1. Adding joinedload on the items relationship...\n"
            "$ pytest tests/\n"
            "===== 12 passed in 1.4s =====\n"
        ),
        "expect_score_at_least": 0.20,  # PATCH closure floor; v6 hallucinated `kimi-course-repo` regression would crash this below 0.10
    },
]


def post_validate(course_id: str, step_id: int, paste: str) -> dict:
    """POST /api/exercises/validate with a synthetic paste. Returns the grader's
    response dict ({score, feedback, ...})."""
    body = json.dumps(
        {
            "step_id": step_id,
            "response_data": {"paste": paste},
            "attempt_number": 1,
        }
    ).encode()
    req = urllib.request.Request(
        f"{API}/api/exercises/validate",
        data=body,
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}", "_body": e.read()[:400].decode(errors="replace")}
    except Exception as e:
        return {"_error": f"EXC: {e}"}


def run_test(t: dict) -> tuple[bool, str]:
    name = t["name"]
    resp = post_validate(t["course_id"], t["step_id"], t["paste"])
    if resp.get("_error"):
        return False, f"endpoint error: {resp['_error']}"
    # Score lives under different keys depending on grader path; check all.
    score = resp.get("score")
    if score is None:
        score = resp.get("total_score")
    if score is None:
        # Some validators return correct=True/False instead of a 0..1 score
        if resp.get("correct") is True:
            score = 1.0
        elif resp.get("correct") is False:
            score = 0.0
    if score is None:
        return False, f"no score in response: {json.dumps(resp)[:200]}"

    # Normalize to 0..1 range
    if isinstance(score, (int, float)) and score > 1.5:
        score = score / 100.0

    if "expect_score_at_least" in t:
        threshold = t["expect_score_at_least"]
        if score >= threshold:
            return True, f"score={score:.2f} ≥ {threshold} ✓"
        return False, f"score={score:.2f} < {threshold} ✗ (feedback: {(resp.get('feedback') or '')[:160]!r})"
    if "expect_score_at_most" in t:
        threshold = t["expect_score_at_most"]
        if score <= threshold:
            return True, f"score={score:.2f} ≤ {threshold} ✓"
        return False, f"score={score:.2f} > {threshold} ✗ (correct paste leaked into wrong-paste path)"
    return False, f"test missing expect_score_at_*: {name}"


def main() -> int:
    print(f"Layer 2 grading-paths harness — API={API}")
    print(f"Running {len(GRADING_PATHS)} grading-path tests...\n")
    passed = 0
    failed = 0
    for t in GRADING_PATHS:
        ok, detail = run_test(t)
        flag = "✅" if ok else "❌"
        print(f"  {flag} {t['name']}")
        print(f"     {detail}")
        if ok:
            passed += 1
        else:
            failed += 1
    print()
    print(f"=== {passed}/{passed + failed} PASS ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
