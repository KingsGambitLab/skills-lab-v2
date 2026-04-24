#!/bin/bash
# Wrapper so celery worker inherits ANTHROPIC_API_KEY + other env from .env.
# Without this the worker starts with an empty env and every LLM call
# silently falls back to mock mode — courses ship with template content
# instead of real Go/Python/etc. Learned 2026-04-22 v7.7 after shipping
# a "6-second" Go course that was pure fallback stubs.
cd "$(dirname "$0")/.."
set -a
[ -f .env ] && . ./.env
set +a
# --concurrency=1 + --pool=solo: one task at a time in-process, matches
# our workload (single long-running gen). Bump later if we add parallel
# step-level tasks (level 2 split from earlier design note).
exec ./.venv/bin/celery -A backend.celery_app worker \
    --loglevel=warning \
    --concurrency=1 \
    --pool=solo
