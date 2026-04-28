#!/usr/bin/env bash
# Remove staged hidden grading tests after grading.
# Idempotent — safe to run on EXIT trap even if staging never happened.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Find all .../grading/ test dirs under src/test/java/ and remove them.
# Defensive: only delete dirs literally named 'grading' to avoid accidents.
find "$ROOT_DIR/src/test/java" -type d -name 'grading' 2>/dev/null | while read -r d; do
    rm -rf "$d"
    echo "→ unstaged $d"
done

exit 0
