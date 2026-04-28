#!/usr/bin/env bash
# Stage hidden grading tests for a given exercise into the project's test path.
# Maven picks them up alongside the visible tests.
#
# Usage: bash .grading/scripts/stage-tests.sh <exercise-dir>

set -euo pipefail

EXERCISE_DIR="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT_DIR/.grading/$EXERCISE_DIR"

# Detect Java package from existing main source layout. Fallback to
# com.skillslab.<course>.grading if main src is empty (shouldn't happen
# in a properly-scaffolded course-repo).
MAIN_PKG_DIR="$(find "$ROOT_DIR/src/main/java" -mindepth 3 -maxdepth 5 -type d \
    -not -name 'META-INF' 2>/dev/null | head -1)"

if [ -z "$MAIN_PKG_DIR" ]; then
    echo "ERROR: cannot locate src/main/java/<package>/ to derive test package" >&2
    exit 1
fi

# Strip up to src/main/java/ → relative package path
PKG_REL="${MAIN_PKG_DIR#$ROOT_DIR/src/main/java/}"
DEST="$ROOT_DIR/src/test/java/$PKG_REL/grading"

if [ ! -d "$SRC" ]; then
    echo "ERROR: grading source dir not found: $SRC" >&2
    exit 1
fi

mkdir -p "$DEST"
# Only copy .java files (skip verify.sh etc. — those are dispatched separately)
shopt -s nullglob
copied=0
for f in "$SRC"/*.java; do
    cp "$f" "$DEST/"
    copied=$((copied + 1))
done
shopt -u nullglob

if [ "$copied" -eq 0 ]; then
    echo "ERROR: no .java files in $SRC" >&2
    exit 1
fi

echo "→ staged $copied hidden test file(s) from $SRC into $DEST"
