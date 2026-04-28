#!/usr/bin/env bash
# Java/Spring grading runner — universal contract per
# tools/grading-skeletons/README.md.
#
# Usage:
#   bash .grading/run-grading.sh <exercise-dir>
#   bash .grading/run-grading.sh exercise-01-fix-n-plus-one
#
# Contract:
#   - Stages hidden tests from .grading/<exercise-dir>/ into src/test/java/.../grading/
#   - Runs `timeout 120s mvn -B -q test` (or `verify.sh` if present)
#   - Emits RESULT: PASS|FAIL on stdout (last line)
#   - Writes grading-result.json (machine-readable)
#   - Exit 0 on PASS, non-0 on FAIL
#   - Always unstages tests via EXIT trap
#
# Wired by backend/course_assets.py via:
#   grading_runner="bash .grading/run-grading.sh"

set -uo pipefail

EXERCISE_DIR="${1:-}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -z "$EXERCISE_DIR" ]; then
    echo "ERROR: exercise-dir required. Usage: bash .grading/run-grading.sh <exercise-dir>" >&2
    echo "RESULT: FAIL"
    exit 2
fi

SRC=".grading/$EXERCISE_DIR"
if [ ! -d "$SRC" ]; then
    echo "ERROR: exercise dir not found: $SRC" >&2
    echo "FAILED: setup - exercise dir '$EXERCISE_DIR' missing in .grading/"
    echo "RESULT: FAIL"
    exit 2
fi

# Detect dispatch: verify.sh OR test-class staging.
if [ -f "$SRC/verify.sh" ]; then
    # Verify-script exercise (e.g. slash command, MCP wiring, hooks edit)
    chmod +x "$SRC/verify.sh"
    set +e
    timeout 120s bash "$SRC/verify.sh" 2>&1
    EXIT=$?
    set -e
    if [ $EXIT -eq 0 ]; then
        echo "RESULT: PASS"
        cat > grading-result.json <<EOF
{"exercise":"$EXERCISE_DIR","status":"passed","via":"verify.sh","exitCode":0,"timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
        exit 0
    else
        echo "FAILED: verify.sh exited $EXIT"
        echo "RESULT: FAIL"
        cat > grading-result.json <<EOF
{"exercise":"$EXERCISE_DIR","status":"failed","via":"verify.sh","exitCode":$EXIT,"timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
        exit $EXIT
    fi
fi

# Test-class staging path (mvn test against staged Hidden*GradingTest.java)
echo "→ staging hidden tests from $SRC"
bash "$ROOT_DIR/.grading/scripts/stage-tests.sh" "$EXERCISE_DIR"
trap 'bash "$ROOT_DIR/.grading/scripts/unstage-tests.sh" || true' EXIT

# Clear stale surefire reports
rm -rf "$ROOT_DIR/target/surefire-reports" 2>/dev/null

echo "→ running mvn test (120s timeout)"
set +e
timeout 120s ./mvnw -B -q test 2>&1
MVN_EXIT=$?
set -e

# Parse surefire XML → grading-result.json + RESULT protocol
bash "$ROOT_DIR/.grading/scripts/parse-surefire.sh" "$EXERCISE_DIR" "$MVN_EXIT"
PARSE_EXIT=$?

# Final exit: 0 iff parser said PASS
exit $PARSE_EXIT
