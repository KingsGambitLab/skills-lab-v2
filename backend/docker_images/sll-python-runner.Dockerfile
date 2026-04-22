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
RUN pip install \
    pytest==8.3.4 pytest-asyncio==0.25.0 hypothesis==6.122.3 \
    fastapi==0.115.6 uvicorn==0.34.0 httpx==0.28.1 pydantic==2.10.4 \
    sqlalchemy==2.0.36 aiosqlite==0.20.0 \
    bcrypt==4.2.1 pyjwt==2.10.1 passlib==1.7.4 \
    aiohttp==3.11.11 redis==5.2.1 \
    opentelemetry-api==1.29.0 opentelemetry-sdk==1.29.0 \
      opentelemetry-instrumentation-fastapi==0.50b0 \
      opentelemetry-instrumentation-httpx==0.50b0 \
      opentelemetry-exporter-otlp-proto-http==1.29.0 \
    strawberry-graphql==0.256.0 \
    slowapi==0.1.9 \
    numpy==2.2.1 pandas==2.2.3 \
    confluent-kafka==2.6.1 \
    psycopg2-binary==2.9.10 \
 && python -c "import pytest, fastapi, sqlalchemy, bcrypt, jwt, aiohttp, strawberry, slowapi, opentelemetry, numpy, pandas; print('preload ok')"

WORKDIR /app
# No CMD — the grader passes its own command via `docker run ... sh -c '...'`.
