# Pre-built image for Skills Lab v2 code_exercise / hidden_tests grading.
# Built once, pulled everywhere; gets per-run time from ~8s (slim + pip install)
# down to ~1-2s (test execution only).
#
# Build: docker build -t sll-python-runner:latest -f backend/docker_images/sll-python-runner.Dockerfile backend/docker_images/
# Push:  (optional) docker tag sll-python-runner:latest ghcr.io/kingsgambitlab/sll-python-runner:latest
#        docker push ghcr.io/kingsgambitlab/sll-python-runner:latest
#
# The docker_runner prefers this image when:
#   - language is python/py
#   - no additional `requirements` were emitted by the Creator
# Otherwise falls back to python:3.11-slim + pip install.

FROM python:3.11-slim

# Disable pip version check + wheel cache to keep image small.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pre-install the libraries that solver agents and Creator-generated exercises
# repeatedly reach for. Empirical list from the Apr-21 SWE review + Apr-22
# stress tests. Keep it broad — missing a lib means falling back to the slim
# image + per-run pip install (8-12s overhead).
# ══════════════════════════════════════════════════════════════════════════
# v8.5 PHASE B (2026-04-23): HARNESS-CLOSURE INVARIANT via two-env isolation.
# The harness's test-runner (pytest + plugins) lives in its OWN venv at
# /opt/harness-venv. LLM's emitted `requirements.txt` installs to the global
# site-packages (/usr/local/lib/python3.11/site-packages). The harness
# invokes `/opt/harness-venv/bin/pytest` directly — NEVER global pytest —
# so no LLM-level `pip install` can uninstall, downgrade, or shadow the
# harness test runner.
#
# Why two envs, not one venv with system-site-packages = False:
#   Tests must be able to `import asyncpg`/`import fastapi`/etc., which
#   live in GLOBAL site-packages (LLM installs them there). The harness
#   venv is created WITH --system-site-packages so sys.path = [venv, global]:
#   venv's pytest wins on import (it's first), but tests can still import
#   asyncpg from global. Global pip install never touches venv.
# ══════════════════════════════════════════════════════════════════════════

# 1. GLOBAL layer — libs the LLM's solution/tests import. LLM's pip install
#    adds to this layer. These are the "available libs" promised to the
#    LLM in _runtime_deps_brief(). A subset (app frameworks + core stacks)
#    is prebaked for speed; everything else installs on-demand at grade time.
#    NOTE: pytest/pytest-plugins NOT installed here. They live in /opt/harness-venv.
RUN pip install \
    fastapi==0.115.6 uvicorn==0.34.0 httpx==0.28.1 pydantic==2.10.4 \
      pydantic-settings==2.7.0 \
    sqlalchemy==2.0.36 aiosqlite==0.20.0 asyncpg==0.30.0 alembic==1.14.0 \
      aiofiles==24.1.0 \
    bcrypt==4.2.1 pyjwt==2.10.1 passlib==1.7.4 python-multipart==0.0.20 \
    aiohttp==3.11.11 redis==5.2.1 tenacity==9.0.0 orjson==3.10.12 \
    opentelemetry-api==1.29.0 opentelemetry-sdk==1.29.0 \
      opentelemetry-instrumentation-fastapi==0.50b0 \
      opentelemetry-instrumentation-httpx==0.50b0 \
      opentelemetry-exporter-otlp-proto-http==1.29.0 \
    strawberry-graphql==0.256.0 \
    slowapi==0.1.9 \
    numpy==2.2.1 pandas==2.2.3 \
    confluent-kafka==2.6.1 \
    psycopg2-binary==2.9.10 \
    hypothesis==6.122.3 freezegun==1.5.1 \
 && python -c "import fastapi, sqlalchemy, bcrypt, jwt, aiohttp, strawberry, slowapi, opentelemetry, numpy, pandas, asyncpg, alembic, aiofiles, tenacity, orjson, freezegun, pydantic_settings; print('global preload ok')"

# 2. HARNESS VENV — isolated test runner + plugins. LLM cannot mutate this
#    layer: the venv has its own site-packages at /opt/harness-venv/lib/.
#    Even if LLM `pip install pytest==1.0`, it installs to global site-
#    packages; our harness venv's pytest is first on sys.path when invoked
#    via /opt/harness-venv/bin/pytest.
RUN python -m venv --system-site-packages /opt/harness-venv \
 && /opt/harness-venv/bin/pip install --disable-pip-version-check \
      pytest==8.3.4 pytest-asyncio==0.25.0 pytest-mock==3.14.0 \
      pytest-json-report==1.5.0 \
 && /opt/harness-venv/bin/python -c "import pytest, pytest_asyncio; print('harness-venv preload ok:', pytest.__version__)"

# Snapshot the harness-venv state so verify_baked can assert immutability.
# Format: `pkgname==version` one per line, LOWERCASE names. Read at
# grade-time to compare against current state.
RUN /opt/harness-venv/bin/pip freeze --disable-pip-version-check \
      | grep -iE '^(pytest|pytest-asyncio|pytest-mock|pytest-json-report|pytest-metadata|pluggy|iniconfig|packaging)==' \
      | tr '[:upper:]' '[:lower:]' \
      > /opt/harness-venv-snapshot.txt \
 && cat /opt/harness-venv-snapshot.txt

# v8.5 Phase 1 HARNESS-LEVEL DEP MANAGEMENT (2026-04-23):
# Bake the snapshot-diff verify script to /opt. Must NOT live at /app
# (bind-mount overlay wipes anything there at docker-run time). The
# grader invokes `python /opt/verify_baked.py` AFTER the LLM's
# requirements install; it exits 127 with DEP_DRIFT: lines if any
# protected package was mutated by the install.
COPY verify_baked_python.py /opt/verify_baked.py
RUN chmod +x /opt/verify_baked.py && python /opt/verify_baked.py && echo "verify_baked: OK"

WORKDIR /app
# No CMD — the grader passes its own command via `docker run ... sh -c '...'`.
