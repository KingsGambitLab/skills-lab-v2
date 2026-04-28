#!/usr/bin/env bash
# Parse target/surefire-reports/*.xml → emit RESULT protocol on stdout
# + write grading-result.json. Per universal contract in
# tools/grading-skeletons/README.md.
#
# Usage: bash .grading/scripts/parse-surefire.sh <exercise-dir> <mvn-exit-code>
#
# RESULT protocol (last line of stdout):
#   RESULT: PASS    — all tests passed AND mvn exited 0
#   RESULT: FAIL    — any test failed/errored OR mvn exited non-0
# Plus FAILED: <test_name> - <message> lines for each failed/errored test.
#
# Exit code: 0 on PASS, 1 on FAIL.

set -uo pipefail

EXERCISE_DIR="${1:-unknown}"
MVN_EXIT="${2:-0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORTS="$ROOT_DIR/target/surefire-reports"

TOTAL=0
FAILURES=0
ERRORS=0
SKIPPED=0
FAILED_TESTS=()

if [ -d "$REPORTS" ]; then
    for f in "$REPORTS"/TEST-*.xml; do
        [ -f "$f" ] || continue
        # <testsuite ...> opening tag — extract counts
        SUITE_LINE="$(grep -m1 -E '<testsuite ' "$f" || true)"
        if [ -n "$SUITE_LINE" ]; then
            T=$(echo "$SUITE_LINE" | sed -nE 's/.*tests="([0-9]+)".*/\1/p')
            F=$(echo "$SUITE_LINE" | sed -nE 's/.*failures="([0-9]+)".*/\1/p')
            E=$(echo "$SUITE_LINE" | sed -nE 's/.*errors="([0-9]+)".*/\1/p')
            S=$(echo "$SUITE_LINE" | sed -nE 's/.*skipped="([0-9]+)".*/\1/p')
            TOTAL=$((TOTAL + ${T:-0}))
            FAILURES=$((FAILURES + ${F:-0}))
            ERRORS=$((ERRORS + ${E:-0}))
            SKIPPED=$((SKIPPED + ${S:-0}))
        fi
        # Extract <testcase>s with <failure> or <error> children
        # Use python for a reliable XML parse — sed can break on multi-line failures.
        python3 - "$f" <<'PYEOF' 2>/dev/null || true
import sys, xml.etree.ElementTree as ET
try:
    tree = ET.parse(sys.argv[1])
    for tc in tree.iter('testcase'):
        name = tc.attrib.get('name', '?')
        cls = tc.attrib.get('classname', '').rsplit('.', 1)[-1]
        for child in tc:
            tag = child.tag
            if tag in ('failure', 'error'):
                msg = (child.attrib.get('message') or child.text or tag).split('\n', 1)[0].strip()[:200]
                print(f"FAILED: {cls}.{name} - {msg}")
                break
except Exception as e:
    print(f"FAILED: parse - could not read {sys.argv[1]}: {e}", file=sys.stderr)
PYEOF
    done
fi

PASSED=$((TOTAL - FAILURES - ERRORS - SKIPPED))
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Status: PASS only if all green AND mvn exited 0 AND we ran ≥1 test.
if [ "$MVN_EXIT" -eq 0 ] && [ "$FAILURES" -eq 0 ] && [ "$ERRORS" -eq 0 ] && [ "$TOTAL" -gt 0 ]; then
    STATUS="passed"
    RESULT="PASS"
    EXIT_CODE=0
else
    STATUS="failed"
    RESULT="FAIL"
    EXIT_CODE=1
    # If mvn failed but no XML reports exist (e.g. compile error), surface that.
    if [ "$TOTAL" -eq 0 ] && [ "$MVN_EXIT" -ne 0 ]; then
        echo "FAILED: build - mvn exited $MVN_EXIT (no test reports found; compile error or build break)"
    fi
fi

# grading-result.json — machine-readable detail for richer UIs
cat > "$ROOT_DIR/grading-result.json" <<EOF
{"exercise":"$EXERCISE_DIR","status":"$STATUS","via":"mvn-surefire","total":$TOTAL,"passed":$PASSED,"failures":$FAILURES,"errors":$ERRORS,"skipped":$SKIPPED,"mavenExitCode":$MVN_EXIT,"timestamp":"$TIMESTAMP"}
EOF

# RESULT protocol — must be last line of stdout
echo "RESULT: $RESULT"
exit $EXIT_CODE
