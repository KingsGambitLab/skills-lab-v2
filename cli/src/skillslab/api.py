"""Thin LMS API client. All endpoints accept Authorization: Bearer <token>
since the cli_token middleware shipped 2026-04-25.
"""
from __future__ import annotations

import json
import sys
from typing import Any

import httpx

from .state import api_url, get_token


class ApiError(RuntimeError):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"API {status}: {body[:200]}")


def _client(*, with_auth: bool = True, timeout: float = 30.0) -> httpx.Client:
    headers = {"Accept": "application/json"}
    if with_auth:
        tok = get_token()
        if not tok:
            raise ApiError(401, "Not signed in. Run `skillslab login` first.")
        headers["Authorization"] = f"Bearer {tok}"
    return httpx.Client(base_url=api_url(), headers=headers, timeout=timeout)


def _check(r: httpx.Response) -> Any:
    if r.status_code >= 400:
        raise ApiError(r.status_code, r.text)
    if not r.content:
        return None
    if r.headers.get("content-type", "").startswith("application/json"):
        return r.json()
    return r.text


def login_with_password(email: str, password: str, label: str = "cli") -> dict[str, Any]:
    """Issue a bearer token via headless email+password.
    Returns: {token, user_id, email, expires_at, label}
    """
    with _client(with_auth=False) as c:
        r = c.post("/api/auth/cli_token", json={"email": email, "password": password, "label": label})
    return _check(r)


def whoami() -> dict[str, Any] | None:
    with _client() as c:
        r = c.get("/api/auth/me")
    if r.status_code == 401:
        return None
    return _check(r)


def my_courses() -> list[dict[str, Any]]:
    with _client() as c:
        r = c.get("/api/auth/my-courses")
    body = _check(r) or {}
    return body.get("courses", [])


def all_courses() -> list[dict[str, Any]]:
    """Public catalog (no auth needed) — used to surface courses the
    learner could enroll in via `skillslab courses`.
    """
    with _client() as c:
        r = c.get("/api/courses")
    return _check(r) or []


def enroll(course_id: str) -> dict[str, Any]:
    with _client() as c:
        r = c.post(f"/api/auth/enroll/{course_id}")
    return _check(r)


def get_modules_with_steps(course_id: str) -> list[dict[str, Any]]:
    """Fetches every module + its steps for the course. The CLI uses this
    to write per-step markdown files locally on `start`.
    """
    with _client() as c:
        # First — the course itself (lightweight, has module list)
        r_course = c.get(f"/api/courses/{course_id}")
        course = _check(r_course)
        modules = course.get("modules", [])
        out = []
        for m in modules:
            r_mod = c.get(f"/api/courses/{course_id}/modules/{m['id']}")
            mod = _check(r_mod)
            out.append(mod)
    return out


def mark_step_complete(step_id: int, score: int | float | None = None,
                       response_data: dict | None = None) -> dict[str, Any]:
    """Wires the CLI's `check` pass to the same /api/progress/complete the
    browser uses. Bearer-auth means it's attributed to the right user.
    """
    body = {"step_id": step_id}
    if score is not None:
        body["score"] = score
    if response_data:
        body["response_data"] = response_data
    with _client() as c:
        r = c.post("/api/progress/complete", json=body)
    return _check(r)


def validate_exercise(step_id: int, exercise_type: str, response_data: dict) -> dict[str, Any]:
    """Bridge mode: when a step has a rubric but no native cli_check spec,
    the CLI captures stdout / git diff into response_data and posts to
    the existing LLM-rubric grader. Same payload shape the browser sends.
    """
    body = {"step_id": step_id, "exercise_type": exercise_type, "response_data": response_data}
    with _client() as c:
        r = c.post("/api/exercises/validate", json=body)
    return _check(r)
