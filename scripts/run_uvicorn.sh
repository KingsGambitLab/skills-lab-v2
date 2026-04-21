#!/bin/bash
# Wrapper so preview_start launches uvicorn with ANTHROPIC_API_KEY loaded from .env
cd "$(dirname "$0")/.."
set -a
[ -f .env ] && . ./.env
set +a
exec ./.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8001}"
