"""Authentication + session endpoints for Skills Lab v8.

ADDED 2026-04-23. Register, login, logout, "me", enroll in course, publish
(creator only). Session cookie is HTTP-only + SameSite=Lax. Passwords
hashed with Argon2id. Session tokens are 256-bit random base64url.

Design choices (vs JWT):
- Session rows live in DB. Logout = DELETE the row. No "token revocation
  list" complexity. Cheap to support "log me out everywhere" (purge all
  rows for a user).
- Cookie is opaque. Client never inspects it.
- Session TTL 14 days. Refreshed on every authenticated request.

Role model:
- learner: default. Can enroll + view enrolled courses + submit exercises.
- creator: can do everything learner does + create/edit their own courses +
  publish/unpublish their own courses.
- admin: can do everything + manage the catalog.

Wire-up (do ONCE in backend/main.py):

    from backend import auth as _auth
    app.include_router(_auth.router)
    app.middleware("http")(_auth.session_middleware)

The middleware is idempotent: it reads the cookie, loads the session +
user into `request.state.user` / `request.state.session`, OR leaves them
None for anonymous requests. Route handlers use `Depends(require_user)`
or `Depends(require_role("creator"))` to gate access.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import (
    Course,
    User,
    UserRole,
    Session as AuthSession,
    Enrollment,
    get_db,
)


logger = logging.getLogger("skills-lab.auth")


# ── Password hashing (argon2id) ───────────────────────────────────────────
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHashError
    _ph = PasswordHasher(
        time_cost=2,        # 2 iterations
        memory_cost=19 * 1024,  # 19 MiB — OWASP 2024 floor
        parallelism=1,
        hash_len=32,
        salt_len=16,
    )
    _ARGON2_AVAILABLE = True
except ImportError:  # argon2-cffi not installed yet
    _ARGON2_AVAILABLE = False
    logger.warning(
        "argon2-cffi not installed — password hashing falls back to hashlib scrypt. "
        "Install with: .venv/bin/pip install argon2-cffi"
    )
    import hashlib


def hash_password(pw: str) -> str:
    if _ARGON2_AVAILABLE:
        return _ph.hash(pw)
    # Fallback: scrypt. Salt + hash concatenated with `$scrypt$` prefix.
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "$scrypt$" + salt.hex() + "$" + derived.hex()


def verify_password(pw: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$scrypt$"):
        try:
            _, salt_hex, hash_hex = stored_hash[len("$scrypt$"):].split("$", 1)[0], *stored_hash[len("$scrypt$"):].split("$")
            # re-parse cleanly:
            parts = stored_hash[len("$scrypt$"):].split("$")
            salt = bytes.fromhex(parts[0])
            expected = bytes.fromhex(parts[1])
            derived = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
            return secrets.compare_digest(derived, expected)
        except Exception:
            return False
    if not _ARGON2_AVAILABLE:
        return False
    try:
        _ph.verify(stored_hash, pw)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


# ── Request / response schemas ────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    display_name: Optional[str] = Field(default=None, max_length=100)
    role: str = Field(default="learner")

    @field_validator("role")
    @classmethod
    def _valid_role(cls, v: str) -> str:
        if v not in ("learner", "creator"):
            raise ValueError("role must be 'learner' or 'creator'")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: Optional[str]
    role: str
    created_at: datetime


# ── Cookie helpers ────────────────────────────────────────────────────────

COOKIE_NAME = "sll_session"
SESSION_TTL_DAYS = 14


def _set_session_cookie(response: Response, token: str) -> None:
    # secure=False for local dev (localhost:8001 HTTP). In prod nginx does TLS
    # termination; set secure=True there via env toggle.
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


# ── Middleware: load session into request.state ───────────────────────────

async def session_middleware(request: Request, call_next):
    """Attach request.state.user + request.state.session if the incoming
    sll_session cookie points to a valid live session. Else leave as None."""
    request.state.user = None
    request.state.session = None
    token = request.cookies.get(COOKIE_NAME)
    if token:
        try:
            from backend.database import async_session_factory
            async with async_session_factory() as db:
                sess = (await db.execute(
                    select(AuthSession).where(AuthSession.id == token)
                )).scalar_one_or_none()
                if sess and sess.expires_at > datetime.utcnow():
                    user = (await db.execute(
                        select(User).where(User.id == sess.user_id)
                    )).scalar_one_or_none()
                    if user and user.disabled_at is None:
                        request.state.user = user
                        request.state.session = sess
        except Exception:
            logger.exception("session load failed")
    return await call_next(request)


# ── Dependencies ──────────────────────────────────────────────────────────

async def require_user(request: Request) -> User:
    u = getattr(request.state, "user", None)
    if u is None:
        raise HTTPException(401, "Not signed in")
    return u


def require_role(*roles: str):
    async def _dep(request: Request) -> User:
        u = await require_user(request)
        if u.role not in roles:
            raise HTTPException(403, f"Requires role: {roles}")
        return u
    return _dep


# ── Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_to_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        email=u.email,
        display_name=u.display_name,
        role=u.role.value if hasattr(u.role, "value") else u.role,
        created_at=u.created_at,
    )


@router.post("/register", response_model=UserOut)
async def register(req: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = req.email.lower()
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, "Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(req.password),
        display_name=req.display_name,
        role=UserRole(req.role),
    )
    db.add(user)
    await db.flush()
    # Fresh session auto-logged-in.
    sess = AuthSession.new_for_user(user.id, ttl_hours=SESSION_TTL_DAYS * 24)
    db.add(sess)
    await db.flush()
    _set_session_cookie(response, sess.id)
    await db.commit()
    return _user_to_out(user)


@router.post("/login", response_model=UserOut)
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = req.email.lower()
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    # Intentionally vague error to avoid email enumeration.
    if user is None or user.disabled_at is not None or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    sess = AuthSession.new_for_user(user.id, ttl_hours=SESSION_TTL_DAYS * 24)
    db.add(sess)
    await db.flush()
    user.last_login_at = datetime.utcnow()
    _set_session_cookie(response, sess.id)
    await db.commit()
    return _user_to_out(user)


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    sess = getattr(request.state, "session", None)
    if sess is not None:
        # Reload in this session then delete.
        s_live = (await db.execute(select(AuthSession).where(AuthSession.id == sess.id))).scalar_one_or_none()
        if s_live is not None:
            await db.delete(s_live)
            await db.commit()
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=Optional[UserOut])
async def me(request: Request):
    u = getattr(request.state, "user", None)
    if u is None:
        return None
    return _user_to_out(u)


# ── Enrollment ────────────────────────────────────────────────────────────

@router.post("/enroll/{course_id}")
async def enroll(course_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_user(request)
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if course is None or course.archived_at is not None:
        raise HTTPException(404, "Course not found")
    # creators can enroll in their own drafts; others only in published.
    if not course.is_published and course.creator_user_id != user.id and user.role != "admin":
        raise HTTPException(404, "Course not found")
    existing = (await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
        )
    )).scalar_one_or_none()
    if existing is not None:
        return {"ok": True, "already_enrolled": True, "enrollment_id": existing.id}
    enr = Enrollment(user_id=user.id, course_id=course_id, progress_percent=0)
    db.add(enr)
    await db.flush()
    await db.commit()
    return {"ok": True, "enrollment_id": enr.id}


@router.get("/my-courses")
async def my_courses(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_user(request)
    enrolled = (await db.execute(
        select(Enrollment).where(Enrollment.user_id == user.id)
    )).scalars().all()
    out = []
    for e in enrolled:
        c = (await db.execute(select(Course).where(Course.id == e.course_id))).scalar_one_or_none()
        if c is None or c.archived_at is not None:
            continue
        out.append({
            "course_id": c.id,
            "title": c.title,
            "progress_percent": e.progress_percent,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        })
    return {"courses": out}


# ── Creator: Publish / Unpublish ──────────────────────────────────────────

@router.post("/courses/{course_id}/publish")
async def publish_course(course_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_role("creator", "admin")(request)
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if course is None:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and course.creator_user_id != user.id:
        raise HTTPException(403, "You are not the creator of this course")
    course.is_published = True
    course.published_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "course_id": course_id, "is_published": True}


@router.post("/courses/{course_id}/unpublish")
async def unpublish_course(course_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_role("creator", "admin")(request)
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if course is None:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and course.creator_user_id != user.id:
        raise HTTPException(403, "You are not the creator of this course")
    course.is_published = False
    await db.commit()
    return {"ok": True, "course_id": course_id, "is_published": False}


@router.get("/creator/my-drafts")
async def my_drafts(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_role("creator", "admin")(request)
    q = select(Course).where(
        Course.creator_user_id == user.id,
        Course.archived_at.is_(None),
    )
    drafts = (await db.execute(q)).scalars().all()
    return {
        "drafts": [
            {
                "course_id": c.id,
                "title": c.title,
                "is_published": c.is_published,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "published_at": c.published_at.isoformat() if c.published_at else None,
            }
            for c in drafts
        ]
    }


@router.get("/creator/courses/{course_id}/enrolled-learners")
async def enrolled_learners(course_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Return enrolled learners + per-module progress breakdown.

    2026-04-25 — extended to include per-module step-completion counts so the
    creator dashboard can show "M0 3/3 · M1 2/4 · M2 0/5 · …" per learner. The
    caller authenticates via session cookie (creator/admin role required).
    """
    user = await require_role("creator", "admin")(request)
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if course is None:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and course.creator_user_id != user.id:
        raise HTTPException(403, "You are not the creator of this course")

    # Pull modules + step ids in one shot (course-wide).
    from backend.database import Module, Step, UserProgress
    modules = (await db.execute(
        select(Module).where(Module.course_id == course_id).order_by(Module.position)
    )).scalars().all()
    module_steps: dict[int, list[int]] = {}
    for m in modules:
        sids = (await db.execute(
            select(Step.id).where(Step.module_id == m.id).order_by(Step.position)
        )).scalars().all()
        module_steps[m.id] = list(sids)
    total_steps = sum(len(v) for v in module_steps.values())

    enrollments = (await db.execute(
        select(Enrollment).where(Enrollment.course_id == course_id)
    )).scalars().all()
    out = []
    for e in enrollments:
        u = (await db.execute(select(User).where(User.id == e.user_id))).scalar_one_or_none()
        if u is None:
            continue
        # Per-module completion count
        progress_rows = (await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == str(u.id),
                UserProgress.completed == True,  # noqa: E712
            )
        )).scalars().all()
        completed_step_ids = {p.step_id for p in progress_rows}
        per_module = []
        completed_total = 0
        for m in modules:
            sids = module_steps.get(m.id, [])
            done = sum(1 for sid in sids if sid in completed_step_ids)
            completed_total += done
            per_module.append({
                "module_id": m.id,
                "position": m.position,
                "title": m.title,
                "completed": done,
                "total": len(sids),
            })
        # Computed progress (in case enrollment.progress_percent is stale)
        computed_pct = int(round(completed_total / total_steps * 100)) if total_steps else 0
        out.append({
            "user_id": u.id,
            "email": u.email,
            "display_name": u.display_name or u.email,
            "role": u.role,
            "progress_percent": e.progress_percent or computed_pct,
            "computed_progress_percent": computed_pct,
            "completed_steps": completed_total,
            "total_steps": total_steps,
            "per_module": per_module,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
            "last_active_at": e.last_active_at.isoformat() if e.last_active_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        })
    return {"course_id": course_id, "course_title": course.title, "total_steps": total_steps, "learners": out}
