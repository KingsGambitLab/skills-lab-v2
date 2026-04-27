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
import uuid
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

# Course-progression #5 (2026-04-27): anonymous learner identity. Without
# this every guest writes to the shared user_id="default" bucket on
# UserProgress, which (a) leaks progress between unrelated guests, and
# (b) makes it impossible to migrate their work to a real user_id when
# they sign up. The middleware below issues an `sll_anon` cookie on
# first request and the progress endpoints use it as the fallback user_id.
ANON_COOKIE_NAME = "sll_anon"
ANON_TTL_DAYS = 365


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


def _set_anon_cookie(response: Response, anon_id: str) -> None:
    response.set_cookie(
        key=ANON_COOKIE_NAME,
        value=anon_id,
        max_age=ANON_TTL_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def _clear_anon_cookie(response: Response) -> None:
    response.delete_cookie(key=ANON_COOKIE_NAME, path="/")


# ── Middleware: load session into request.state ───────────────────────────

async def session_middleware(request: Request, call_next):
    """Attach request.state.user + request.state.session + request.state.anon_id.

    Three identity layers supported:
      1. `sll_session` cookie (browser flow) — authenticated user
      2. `Authorization: Bearer <token>` header (CLI flow) — authenticated user
      3. `sll_anon` cookie (browser flow) — anonymous learner identity
         (course-progression #5). Issued on first request; persists 1 year.
         Lets us track guest progress separately per browser/device and
         migrate it to a real user_id at sign-up time.

    Both authenticated paths resolve through the same `auth_sessions` table.
    The anon path is independent — anon_id is set even when a session is
    present, so the progress endpoints can still see the anon cookie if a
    pre-signup migration is pending.
    """
    request.state.user = None
    request.state.session = None
    request.state.anon_id = None
    request.state._issue_anon_cookie = False  # internal: tells the post-call_next stage to set the cookie

    # 1) Cookie flow (browser)
    token = request.cookies.get(COOKIE_NAME)
    # 2) Bearer flow (CLI)
    if not token:
        auth_hdr = request.headers.get("authorization") or request.headers.get("Authorization") or ""
        if auth_hdr.lower().startswith("bearer "):
            token = auth_hdr.split(None, 1)[1].strip()

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

    # 3) Anonymous identity. Set even for authenticated users — register/
    #    login handlers consume it to migrate pre-signup progress.
    anon_id = request.cookies.get(ANON_COOKIE_NAME)
    if not anon_id:
        anon_id = uuid.uuid4().hex
        request.state._issue_anon_cookie = True
    request.state.anon_id = anon_id

    response = await call_next(request)
    if getattr(request.state, "_issue_anon_cookie", False):
        # Mint the cookie on the way out so it's bound to the response
        # the browser is about to receive.
        _set_anon_cookie(response, anon_id)
    return response


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


async def _migrate_anon_progress(db: AsyncSession, anon_id: str, user_id: int) -> int:
    """Transfer guest progress from anon_id to authenticated user_id.

    Course-progression #5 (2026-04-27): runs at register + login so a
    learner who solved a few steps as a guest doesn't lose them on signup.

    Conflict resolution when both anon and user already have a row for the
    same step: take MAX(score), SUM(attempts), OR(completed). Prefer the
    user's completed_at when set, else take anon's. Anon rows are deleted
    after merge so re-running is idempotent.

    Returns count of step-rows migrated (transferred + merged).
    """
    if not anon_id or anon_id == "default":
        return 0

    from backend.database import UserProgress as _UP, Certificate as _Cert

    new_user_id = str(user_id)
    anon_rows = (await db.execute(
        select(_UP).where(_UP.user_id == anon_id)
    )).scalars().all()
    if not anon_rows:
        return 0

    # Index user's existing rows by step_id so the conflict path is one
    # dict lookup, not a per-row select.
    user_existing = (await db.execute(
        select(_UP).where(_UP.user_id == new_user_id)
    )).scalars().all()
    by_step = {row.step_id: row for row in user_existing}

    migrated = 0
    for arow in anon_rows:
        urow = by_step.get(arow.step_id)
        if urow is None:
            arow.user_id = new_user_id
        else:
            # Merge.
            urow.attempts = (urow.attempts or 0) + (arow.attempts or 0)
            if (arow.score is not None) and (urow.score is None or arow.score > urow.score):
                urow.score = arow.score
            if arow.completed and not urow.completed:
                urow.completed = True
                urow.completed_at = arow.completed_at or urow.completed_at
            elif arow.completed and urow.completed and arow.completed_at and (
                urow.completed_at is None or arow.completed_at < urow.completed_at
            ):
                # Preserve the earlier completion time when both completed.
                urow.completed_at = arow.completed_at
            if arow.response_data and not urow.response_data:
                urow.response_data = arow.response_data
            await db.delete(arow)
        migrated += 1

    # Move any anon Certificates the user doesn't already have.
    anon_certs = (await db.execute(
        select(_Cert).where(_Cert.user_id == anon_id)
    )).scalars().all()
    for cert in anon_certs:
        existing = (await db.execute(
            select(_Cert).where(_Cert.user_id == new_user_id, _Cert.course_id == cert.course_id)
        )).scalar_one_or_none()
        if existing is None:
            cert.user_id = new_user_id
        else:
            await db.delete(cert)

    await db.flush()
    return migrated


@router.post("/register", response_model=UserOut)
async def register(req: RegisterRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
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
    # Migrate any pre-signup guest progress before issuing the session
    # cookie — failure is logged but not fatal (registration still succeeds).
    anon_id = getattr(request.state, "anon_id", None)
    if anon_id:
        try:
            n = await _migrate_anon_progress(db, anon_id, user.id)
            if n:
                logger.info("migrated %d anon progress rows from %s to user %s", n, anon_id, user.id)
        except Exception:
            logger.exception("anon-progress migration failed at register; continuing")
    # Fresh session auto-logged-in.
    sess = AuthSession.new_for_user(user.id, ttl_hours=SESSION_TTL_DAYS * 24)
    db.add(sess)
    await db.flush()
    _set_session_cookie(response, sess.id)
    _clear_anon_cookie(response)  # subsequent requests use the session cookie
    await db.commit()
    return _user_to_out(user)


@router.post("/login", response_model=UserOut)
async def login(req: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    email = req.email.lower()
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    # Intentionally vague error to avoid email enumeration.
    if user is None or user.disabled_at is not None or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    sess = AuthSession.new_for_user(user.id, ttl_hours=SESSION_TTL_DAYS * 24)
    db.add(sess)
    await db.flush()
    user.last_login_at = datetime.utcnow()
    # Same migration as register — covers the case where a returning user
    # browsed as a guest before logging back in.
    anon_id = getattr(request.state, "anon_id", None)
    if anon_id:
        try:
            n = await _migrate_anon_progress(db, anon_id, user.id)
            if n:
                logger.info("migrated %d anon progress rows from %s to user %s on login", n, anon_id, user.id)
        except Exception:
            logger.exception("anon-progress migration failed at login; continuing")
    _set_session_cookie(response, sess.id)
    _clear_anon_cookie(response)
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


# ── CLI token (bearer, long-lived) ────────────────────────────────────────
# 2026-04-25 — issued via the existing logged-in session OR password.
# The CLI runs `skillslab login` which (a) opens the user's browser to
# /cli-login (a small page that POSTs to this endpoint with the user's
# session cookie + a label), or (b) accepts email+password directly for
# headless flows. Either way it returns a bearer token the CLI stores at
# `~/.skillslab/token`. session_middleware accepts the same token via
# Authorization: Bearer.

class CliTokenRequest(BaseModel):
    label: str = Field(default="cli", min_length=1, max_length=80)
    # Optional credentials for headless / first-time flows where the
    # user has no browser session. If both are provided, validates them
    # and issues regardless of cookie state.
    email: str | None = None
    password: str | None = None
    ttl_days: int = Field(default=90, ge=1, le=365)


class CliTokenResponse(BaseModel):
    token: str
    user_id: int
    email: str
    expires_at: str
    label: str


@router.post("/cli_token", response_model=CliTokenResponse)
async def issue_cli_token(
    body: CliTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user: User | None = getattr(request.state, "user", None)
    if user is None:
        # Fall back to email+password validation for headless flows
        if not (body.email and body.password):
            raise HTTPException(401, "Sign in via cookie session OR provide email+password")
        u = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
        if u is None or u.disabled_at is not None:
            raise HTTPException(401, "Invalid credentials")
        if not verify_password(body.password, u.password_hash):
            raise HTTPException(401, "Invalid credentials")
        user = u
    sess = AuthSession.new_for_user(user.id, ttl_hours=body.ttl_days * 24)
    sess.user_agent = f"skillslab-cli/{body.label}"
    db.add(sess)
    await db.commit()
    return CliTokenResponse(
        token=sess.id,
        user_id=user.id,
        email=user.email,
        expires_at=sess.expires_at.isoformat(),
        label=body.label,
    )


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
    """List the learner's enrolled courses with progress + last-activity
    timestamps.

    `last_activity_at` is MAX(UserProgress.completed_at) for this user/course
    — used by the surface-aware-split (Phase 3 v8.7) so the CLI can detect
    when the browser has advanced state since the CLI's last sync. Compared
    against meta.json's `last_active_at`; mismatch = "browser advanced;
    run `skillslab progress`".
    """
    from .database import UserProgress, Module, Step
    from sqlalchemy import func

    user = await require_user(request)
    enrolled = (await db.execute(
        select(Enrollment).where(Enrollment.user_id == user.id)
    )).scalars().all()
    out = []
    for e in enrolled:
        c = (await db.execute(select(Course).where(Course.id == e.course_id))).scalar_one_or_none()
        if c is None or c.archived_at is not None:
            continue
        # Compute last_activity_at = max completed_at across this user's
        # progress on any step in this course. SQLite needs the join chain
        # course → modules → steps → user_progress.
        last_activity_q = (
            select(func.max(UserProgress.completed_at))
            .join(Step, Step.id == UserProgress.step_id)
            .join(Module, Module.id == Step.module_id)
            .where(Module.course_id == c.id)
            .where(UserProgress.user_id == str(user.id))
        )
        last_activity = (await db.execute(last_activity_q)).scalar()
        out.append({
            "course_id": c.id,
            "title": c.title,
            "progress_percent": e.progress_percent,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "last_activity_at": last_activity.isoformat() if last_activity else None,
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


@router.get("/creator/courses/{course_id}/aggregate-stats")
async def creator_course_aggregate_stats(course_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Course-wide engagement signals for the creator dashboard.

    Course-progression #6 (2026-04-27): per-step pass rate (so the
    creator can see which exercises are choking learners), per-module
    funnel (% of enrolled who reached / completed each module), and a
    last-active distribution (engagement freshness). Depends on the
    persisted `UserProgress.attempts` (#4) and the normalized 0-1
    `UserProgress.score` scale (#3).

    Auth: creator-or-admin scoped to the requested course.
    """
    user = await require_role("creator", "admin")(request)
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if course is None:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and course.creator_user_id != user.id:
        raise HTTPException(403, "You are not the creator of this course")

    from sqlalchemy import case, func as _func, distinct
    from backend.database import Module, Step, UserProgress as _UP

    modules = (await db.execute(
        select(Module).where(Module.course_id == course_id).order_by(Module.position)
    )).scalars().all()
    module_step_ids: dict[int, list[int]] = {}
    step_meta: dict[int, dict] = {}
    for m in modules:
        steps = (await db.execute(
            select(Step).where(Step.module_id == m.id).order_by(Step.position)
        )).scalars().all()
        module_step_ids[m.id] = [s.id for s in steps]
        for pos, s in enumerate(steps):
            step_meta[s.id] = {
                "step_id": s.id,
                "module_id": m.id,
                "module_position": m.position,
                "module_title": m.title,
                "position": pos,
                "title": s.title,
                "exercise_type": s.exercise_type or "concept",
            }
    all_step_ids = [sid for ids in module_step_ids.values() for sid in ids]

    # Per-step rollup: attempts, completed_count, avg_score, distinct learner count.
    step_stats: dict[int, dict] = {sid: {"attempts": 0, "completed": 0, "learners": 0, "avg_score": None}
                                    for sid in all_step_ids}
    if all_step_ids:
        rows = (await db.execute(
            select(
                _UP.step_id,
                _func.coalesce(_func.sum(_UP.attempts), 0).label("attempts"),
                _func.sum(case((_UP.completed.is_(True), 1), else_=0)).label("completed"),
                _func.count(distinct(_UP.user_id)).label("learners"),
                _func.avg(_UP.score).label("avg_score"),
            )
            .where(_UP.step_id.in_(all_step_ids))
            .group_by(_UP.step_id)
        )).all()
        for r in rows:
            sid = r.step_id
            if sid in step_stats:
                step_stats[sid] = {
                    "attempts": int(r.attempts or 0),
                    "completed": int(r.completed or 0),
                    "learners": int(r.learners or 0),
                    "avg_score": float(r.avg_score) if r.avg_score is not None else None,
                }

    # Per-module funnel: distinct learners who have ≥1 progress row on any
    # step of the module (regardless of completion).
    per_module = []
    for m in modules:
        sids = module_step_ids.get(m.id, [])
        # Reach: distinct user_ids with any progress in this module
        reach_q = select(_func.count(distinct(_UP.user_id))).where(_UP.step_id.in_(sids)) if sids else None
        reached = int((await db.execute(reach_q)).scalar() or 0) if reach_q is not None else 0
        # Module completion: distinct user_ids who completed ALL steps in the module
        if sids:
            sub_q = (
                select(_UP.user_id)
                .where(_UP.step_id.in_(sids), _UP.completed.is_(True))
                .group_by(_UP.user_id)
                .having(_func.count(_UP.step_id) >= len(sids))
            )
            completed_users = (await db.execute(sub_q)).scalars().all()
            mod_completed = len(completed_users)
        else:
            mod_completed = 0
        # Aggregate per-step stats for this module
        m_attempts = sum(step_stats[sid]["attempts"] for sid in sids)
        m_completed = sum(step_stats[sid]["completed"] for sid in sids)
        per_module.append({
            "module_id": m.id,
            "position": m.position,
            "title": m.title,
            "step_count": len(sids),
            "reached_learners": reached,
            "completed_learners": mod_completed,
            "total_attempts": m_attempts,
            "total_step_completions": m_completed,
            "steps": [
                {
                    **step_meta[sid],
                    **step_stats[sid],
                    # Pass rate = completed / attempts. Useful when attempts > 0.
                    "pass_rate": (
                        step_stats[sid]["completed"] / step_stats[sid]["attempts"]
                        if step_stats[sid]["attempts"] else None
                    ),
                }
                for sid in sids
            ],
        })

    # Last-active distribution + course-wide enrollment summary.
    enrollments = (await db.execute(
        select(Enrollment).where(Enrollment.course_id == course_id)
    )).scalars().all()
    now = datetime.utcnow()
    buckets = {"day": 0, "week": 0, "month": 0, "older": 0, "never": 0}
    completed_courses = 0
    progress_percents: list[int] = []
    for e in enrollments:
        if e.completed_at is not None:
            completed_courses += 1
        progress_percents.append(int(e.progress_percent or 0))
        last = e.last_active_at
        if last is None:
            buckets["never"] += 1
            continue
        delta = (now - last).total_seconds()
        if delta <= 86_400:
            buckets["day"] += 1
        elif delta <= 7 * 86_400:
            buckets["week"] += 1
        elif delta <= 30 * 86_400:
            buckets["month"] += 1
        else:
            buckets["older"] += 1

    avg_pct = (sum(progress_percents) / len(progress_percents)) if progress_percents else 0.0
    median_pct = (
        sorted(progress_percents)[len(progress_percents) // 2]
        if progress_percents else 0
    )

    return {
        "course_id": course_id,
        "course_title": course.title,
        "total_steps": len(all_step_ids),
        "module_count": len(modules),
        "summary": {
            "enrolled": len(enrollments),
            "completed_course": completed_courses,
            "avg_progress_percent": round(avg_pct, 1),
            "median_progress_percent": median_pct,
            "last_active_distribution": buckets,
        },
        "modules": per_module,
    }
