#!/bin/bash
#
# Deploy Skills Lab v8 to skills.sclr.ac (== 18.236.242.248, same machine).
# Prerequisite: SSH key for the sclr.ac ubuntu account configured locally.
#
# Usage:
#   ./scripts/deploy_sclr.sh                # normal deploy
#   DRY_RUN=1 ./scripts/deploy_sclr.sh      # show what would be rsynced
#   SKIP_RESTART=1 ./scripts/deploy_sclr.sh # rsync only, don't touch systemd
#
# What it does:
#   1. rsync changed files (code + frontend + scripts) to ~/skills-lab-v2/
#   2. SSH in, run: pip install argon2-cffi email-validator
#   3. SSH in, run: set SLL_USE_TRACK_ONTOLOGY=1 in env file
#   4. systemctl restart skills-lab.service
#   5. Smoke test: curl /api/admin/budget + /api/courses
#
# DB handling: the SQLite file ~/skills-lab-v2/skills_lab.db is PRESERVED
# (not rsync'd). On restart, create_tables() + _ensure_column() idempotently
# add the new auth tables + Course columns. Existing courses unaffected.
#
# Per CLAUDE.md: skills.sclr.ac and 18.236.242.248 are the SAME machine.
# One SSH is enough.

set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-ubuntu@skills.sclr.ac}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/skills-lab-v2}"
DRY_RUN="${DRY_RUN:-0}"
SKIP_RESTART="${SKIP_RESTART:-0}"

cd "$(dirname "$0")/.."
LOCAL_ROOT="$PWD"
echo "Deploying from: $LOCAL_ROOT"
echo "To:             $REMOTE_HOST:$REMOTE_DIR"
echo

if [ "$DRY_RUN" = "1" ]; then
    RSYNC_FLAGS="-avn"
else
    RSYNC_FLAGS="-av"
fi

# File set — code + frontend + scripts. Excludes secrets + local-only + data.
echo "[1/5] rsyncing changed files..."
rsync $RSYNC_FLAGS \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='skills_lab.db' \
    --exclude='skills_lab.db-wal' \
    --exclude='skills_lab.db-shm' \
    --exclude='.anthropic_budget.json' \
    --exclude='reviews/' \
    --exclude='node_modules/' \
    --exclude='.DS_Store' \
    --exclude='tools/*.md' \
    backend/ \
    "$REMOTE_HOST:$REMOTE_DIR/backend/"

rsync $RSYNC_FLAGS \
    --exclude='.DS_Store' \
    frontend/ \
    "$REMOTE_HOST:$REMOTE_DIR/frontend/"

rsync $RSYNC_FLAGS \
    scripts/ \
    "$REMOTE_HOST:$REMOTE_DIR/scripts/"

# CLAUDE.md for reference
rsync $RSYNC_FLAGS CLAUDE.md "$REMOTE_HOST:$REMOTE_DIR/CLAUDE.md"
rsync $RSYNC_FLAGS requirements.txt "$REMOTE_HOST:$REMOTE_DIR/requirements.txt" 2>/dev/null || true

if [ "$DRY_RUN" = "1" ]; then
    echo
    echo "DRY RUN — no changes applied. Re-run without DRY_RUN=1 to actually deploy."
    exit 0
fi

echo
echo "[2/5] Installing new Python dependencies on remote..."
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && .venv/bin/pip install argon2-cffi email-validator 2>&1 | tail -3"

echo
echo "[3/5] Ensuring SLL_USE_TRACK_ONTOLOGY=1 in remote .env..."
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && (grep -q SLL_USE_TRACK_ONTOLOGY .env || echo 'SLL_USE_TRACK_ONTOLOGY=1' >> .env) && grep SLL_USE_TRACK_ONTOLOGY .env"

if [ "$SKIP_RESTART" = "1" ]; then
    echo
    echo "SKIP_RESTART=1 — skipping systemctl + smoke-test. Remote files updated."
    exit 0
fi

echo
echo "[4/5] Restarting skills-lab.service..."
ssh "$REMOTE_HOST" "sudo systemctl restart skills-lab.service && sleep 3 && sudo systemctl status skills-lab.service --no-pager | head -10"

echo
echo "[5/5] Smoke test..."
sleep 2
echo "  /api/admin/budget:"
curl -s https://impact:getshitdone@skills.sclr.ac/api/admin/budget | python3 -m json.tool | head -6
echo "  /api/courses (first 3):"
curl -s https://impact:getshitdone@skills.sclr.ac/api/courses | python3 -c "import json,sys; d=json.load(sys.stdin); print('total:', len(d.get('courses',[]))); [print('  ', c.get('id'), '—', c.get('title')) for c in d.get('courses',[])[:3]]"
echo
echo "  /api/auth/me (anon should return null):"
curl -s https://impact:getshitdone@skills.sclr.ac/api/auth/me

echo
echo
echo "✅ Deploy complete. http://skills.sclr.ac/ is live with auth + track ontology."
