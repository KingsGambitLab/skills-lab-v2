"""Celery app for skills-lab-v2 background workers.

Why celery: `/api/creator/generate` does 5-15 min of LLM + Docker work per
course. Running it as an `asyncio.create_task` on the uvicorn event loop
starves other endpoints (/budget, /status) even with asyncio.to_thread
wraps — CPU-bound async-body work between awaits still dominates. Moving
the whole job to a separate WORKER PROCESS isolates the event loop
completely.

Broker choice — filesystem transport:
  We don't want to add Redis as a runtime dep for local dev. kombu's
  filesystem transport works fine for single-machine single-worker setups
  and has zero external services. Messages are just files in a directory
  the worker polls. Trade-off: slower than Redis (~100ms delivery latency)
  and not multi-worker-scalable without shared FS. When we move to ECR +
  horizontal scale (per CLAUDE.md deferred-backlog), swap this for Redis.

Backend (result store): same filesystem transport. Task state + return
values live next to the broker messages. The /status endpoint reads from
here.

Worker startup:
  cd /Users/tushar/Desktop/codebases/skills-lab-v2 && \\
  .venv/bin/celery -A backend.celery_app worker --loglevel=warning --concurrency=1 --pool=solo
"""

from __future__ import annotations

import os
from celery import Celery


# Redis broker — after the filesystem transport proved flaky (2026-04-22
# v7.8: heartbeat events + flower both dumping to mailbox, task messages
# getting lost in the noise). Redis is the standard production choice:
# proper queues, task TTLs, no file-accumulation issues. Runs local for
# dev; same URL format for production ECR deploy (just point at ElastiCache
# or equivalent there).
_REDIS_URL = os.environ.get("SLL_REDIS_URL", "redis://127.0.0.1:6379/0")


celery_app = Celery(
    "skills_lab_v2",
    broker=_REDIS_URL,
    backend=_REDIS_URL,
    include=["backend.tasks"],
)

celery_app.conf.update(
    # Don't pretty-print JSON; save bytes.
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Reasonable defaults for our workload: one long task at a time, no
    # prefetch (so a slow job doesn't hog the queue). Result TTL 1 day so
    # we can inspect finished course ids later.
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=86400,
    # Kill tasks that run forever (should never happen but safety net).
    task_time_limit=1800,  # 30 min hard kill
    task_soft_time_limit=1500,  # 25 min soft kill (task can cleanup)
    # Timezone (matches what main.py uses)
    timezone="UTC",
    enable_utc=True,
    # ═════════════════════════════════════════════════════════════════════
    # 2026-04-22 v8 FIX — silent worker wedge after task RuntimeError
    # ═════════════════════════════════════════════════════════════════════
    # Symptom: After the intentional `RuntimeError: code_exercise gen FAILED`
    # (thrown by the retry-exhausted path post-fallback-removal on v7.1),
    # the solo-pool worker went to 0% CPU, stopped polling redis, and never
    # picked up newly enqueued tasks. `celery inspect active` timed out.
    # Redis CLIENT LIST showed a stale connection sitting in `cmd=exec`
    # state (a MULTI/EXEC pipeline that never committed) for an hour.
    #
    # Root cause: asyncio.run(_runner()) on Python 3.14, when _runner()
    # raises, tears down the event loop. During teardown, aiosqlite + the
    # anthropic httpx pool + asyncio.to_thread executor shutdown all issue
    # their own network I/O. Meanwhile celery's trace is writing the
    # FAILURE state to the redis result backend. With task_acks_late=True
    # and solo pool (task execution + broker polling on the SAME thread),
    # a protocol race leaves the broker's primary connection mid-MULTI.
    # Next BRPOPLPUSH on that corrupt connection blocks forever. Silent.
    #
    # Fixes (defense in depth):
    # 1. `broker_connection_retry_on_startup=True` — keep trying to
    #    reconnect if broker isn't up at boot.
    # 2. `broker_heartbeat=30` — worker sends a PING every 30s; broker
    #    drops silent clients; worker gets a reconnect signal.
    # 3. `worker_cancel_long_running_tasks_on_connection_loss=True` —
    #    if the broker connection dies, cancel in-flight tasks rather
    #    than continuing to process against a corrupt channel.
    # 4. `broker_transport_options` with a SHORT visibility timeout (5 min)
    #    so unacked messages come back visible on worker death instead of
    #    sitting invisible for the default 1 hour.
    # 5. Keep solo pool (tasks need a clean event loop each invocation;
    #    `--pool=threads` has its own asyncio issues on 3.14). The
    #    connection-level fixes above address the actual corruption site.
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    broker_transport_options={
        "visibility_timeout": 300,   # 5 min — was default 1 hr
        "socket_keepalive": True,
        "socket_connect_timeout": 10,
        "health_check_interval": 30,
    },
    # Result backend uses a separate connection pool; same hygiene there.
    result_backend_transport_options={
        "socket_keepalive": True,
        "health_check_interval": 30,
    },
)
