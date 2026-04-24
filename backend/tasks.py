"""Celery tasks for skills-lab-v2.

Currently one task: `generate_course`. Wraps the existing async
`_creator_generate_impl` in a sync celery-task shell by running it via
`asyncio.run`. The worker process runs ONE event loop per task
invocation; the main FastAPI process's event loop is untouched.

Session state crossing:
  The Creator workflow stashes per-session data in `_creator_sessions`
  (in-memory dict on the FastAPI process). The worker process can't see
  that dict. For now we pass the session snapshot into the task args at
  enqueue time, so the worker has everything it needs without shared
  state. Longer term: move `_creator_sessions` to SQLite/Redis so all
  processes can read it.
"""

from __future__ import annotations

import asyncio
import gc
import logging
from typing import Any

from backend.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_isolated(coro_factory):
    """Run `coro_factory()` on a brand-new event loop, guaranteeing the
    loop is CLOSED before this function returns — even if the coroutine
    raised. Replacement for `asyncio.run()` with stricter cleanup semantics.

    Why: on Python 3.14, asyncio.run()'s shutdown path runs alongside
    pending I/O from aiosqlite + anthropic httpx + the to_thread executor.
    When the inner coroutine raises, the overlap can leave celery's redis
    broker connection mid-MULTI, wedging the worker's next poll (silent
    hang at 0% CPU for an hour+ until visibility_timeout).

    This helper:
      1. Builds a fresh loop (no shared state from any previous task).
      2. Runs the coroutine to completion OR failure.
      3. Explicitly awaits `shutdown_asyncgens` + `shutdown_default_executor`
         BEFORE closing, so their cleanup isn't racing anything else.
      4. Runs a gc.collect() to prompt __del__ finalizers for httpx pools
         and aiosqlite connections while the loop is still alive.
      5. Closes the loop.

    Exceptions from the coroutine propagate. The cleanup is best-effort —
    individual cleanup errors are logged, never re-raised, so callers see
    the ORIGINAL exception.
    """
    loop = asyncio.new_event_loop()
    try:
        try:
            return loop.run_until_complete(coro_factory())
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                logger.exception("shutdown_asyncgens failed")
            try:
                loop.run_until_complete(loop.shutdown_default_executor())
            except Exception:
                logger.exception("shutdown_default_executor failed")
            # Give aiosqlite / httpx __del__ a chance to run before loop close
            gc.collect()
    finally:
        try:
            loop.close()
        except Exception:
            logger.exception("loop.close failed")
        asyncio.set_event_loop(None)


@celery_app.task(bind=True, name="skills_lab.start_course")
def start_course(self, session_id: str, req_dump: dict[str, Any]) -> dict[str, Any]:
    """Run creator/start on a worker: LLM outline + clarifying questions.

    Returns {"response": <CreatorStartResponse as dict>, "session": <full
    session dict>}. The FastAPI /status endpoint, when task SUCCESS, syncs
    `session` into its own _creator_sessions so subsequent /refine + /generate
    calls on FastAPI can look up the session by session_id.
    """
    from backend.schemas import CreatorStartRequest
    from backend import main as _main

    req = CreatorStartRequest.model_validate(req_dump)

    async def _runner():
        resp = await _main._creator_start_impl(req, session_id)
        session = _main._creator_sessions.get(session_id, {})
        # Convert datetime + response model to JSON-safe dict
        return {
            "response": resp.model_dump() if hasattr(resp, "model_dump") else dict(resp),
            "session": _main._json_safe_session(session),
        }

    try:
        return _run_isolated(_runner)
    except Exception:
        logger.exception("start_course failed: session=%s", session_id)
        raise
    finally:
        _main._creator_sessions.pop(session_id, None)


@celery_app.task(bind=True, name="skills_lab.refine_course")
def refine_course(
    self,
    session_id: str,
    session_snapshot: dict[str, Any],
    req_dump: dict[str, Any],
) -> dict[str, Any]:
    """Run creator/refine on a worker: LLM refines outline based on answers.

    Returns {"response": dict, "session": dict} — same shape as start_course.
    """
    from backend.schemas import CreatorRefineRequest
    from backend import main as _main

    # Re-hydrate the session on the worker from the snapshot we got at enqueue.
    _main._creator_sessions[session_id] = dict(session_snapshot)
    req = CreatorRefineRequest.model_validate(req_dump)

    async def _runner():
        resp = await _main._creator_refine_impl(req)
        session = _main._creator_sessions.get(session_id, {})
        return {
            "response": resp.model_dump() if hasattr(resp, "model_dump") else dict(resp),
            "session": _main._json_safe_session(session),
        }

    try:
        return _run_isolated(_runner)
    except Exception:
        logger.exception("refine_course failed: session=%s", session_id)
        raise
    finally:
        _main._creator_sessions.pop(session_id, None)


@celery_app.task(bind=True, name="skills_lab.generate_course")
def generate_course(
    self,
    session_id: str,
    session_snapshot: dict[str, Any],
    req_dump: dict[str, Any],
) -> dict[str, Any]:
    """Run the Creator generation pipeline for `session_id` in a worker.

    Args:
        session_id: the id the HTTP caller polls by.
        session_snapshot: full `_creator_sessions[session_id]` dict at
            enqueue time (title, description, source_material, course_type,
            level, refined outline, etc.). Passed by value so the worker
            doesn't need access to the main process's in-memory state.
        req_dump: `CreatorGenerateRequest.model_dump()` at enqueue time.

    Returns:
        {"course_id": str} on success. On failure, the task is marked
        FAILURE by celery; the exception's str is in the result backend.
    """
    from backend.schemas import CreatorGenerateRequest
    from backend.database import async_session_factory
    # Re-hydrate the in-memory session dict so `_creator_generate_impl`
    # sees everything it expects.
    from backend import main as _main
    _main._creator_sessions[session_id] = dict(session_snapshot)

    req = CreatorGenerateRequest.model_validate(req_dump)

    async def _runner():
        async with async_session_factory() as db:
            resp = await _main._creator_generate_impl(req, db)
        course_id = getattr(resp, "course_id", None)
        return course_id

    try:
        course_id = _run_isolated(_runner)
        logger.warning("task complete: session=%s course_id=%s", session_id, course_id)
        return {"course_id": course_id, "session_id": session_id}
    except Exception as e:
        logger.exception("task failed: session=%s", session_id)
        # Celery will mark FAILURE + store the exception string in the backend
        raise
    finally:
        # Clean up the in-memory session on the worker side so repeated runs
        # don't accumulate.
        _main._creator_sessions.pop(session_id, None)
