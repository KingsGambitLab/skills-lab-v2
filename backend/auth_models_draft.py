"""DRAFT — User / Session / Enrollment models for v8 multi-user support.

NOT WIRED IN YET. This file is a reference sketch that I'll merge into
backend/database.py once we've decided on schema + Postgres migration is
complete. Keeping it separate so I can iterate without touching the
live DB models.

Schema rationale
----------------

UserRole: enum {learner, creator, admin}. A single user may act in one or
more roles over time. Simplest is "pick your role at signup"; future
"multi-role" work (a learner who also creates their own courses) needs a
join table. For v8 we pick one role per user.

User: email-as-primary-key (lowercased, unique). Password hashed via
argon2 (per 2026 OWASP guidance — bcrypt is still fine, argon2id is the
new gold standard). created_at + last_login_at for audit.

Session: opaque token (256-bit random) → user_id + expires_at. Stored
in DB so logout can invalidate. Sent to client as HTTP-only Secure
cookie `sll_session`. No JWT — session-in-DB is easier to rotate/revoke.

Enrollment: (user_id, course_id) pair with enrolled_at + last_active_at
+ progress_percent (cached aggregate, recomputed on progress updates).

Course gets new columns:
  - creator_user_id: FK to User(id). Null for pre-user-model courses.
  - is_published: bool. False = creator-only visible draft; True = in catalog.
  - published_at: timestamp when flipped to true.

UserProgress gets:
  - user_id (already exists, currently defaults to "default") now points
    to User.id via FK. Historic "default" rows migrate to a singleton
    system user.
"""
from __future__ import annotations

import enum
import secrets
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import from backend.database so we use the same Base declarative class.
# Keeps the Alembic autogenerate story simple — every model is in one metadata.
from backend.database import Base


class UserRole(str, enum.Enum):
    learner = "learner"
    creator = "creator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Email is unique + case-insensitive (lowercased at write). Primary natural key.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(
        Enum(UserRole, native_enum=False), nullable=False, default=UserRole.learner,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Soft-delete. Courses + progress survive user deletion.
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )


class Session(Base):
    __tablename__ = "sessions"

    # 256-bit random base64url token. Client gets this as sll_session cookie.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Optional user-agent + IP for audit. Never PII-heavy.
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # On logout, row is deleted. No `is_revoked` flag — just hard-delete.

    user: Mapped["User"] = relationship(back_populates="sessions")

    @staticmethod
    def new_for_user(user_id: int, ttl_hours: int = 24 * 14) -> "Session":
        """Factory — build a fresh Session with a secure random token."""
        return Session(
            id=secrets.token_urlsafe(48),  # ~64 chars
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    course_id: Mapped[str] = mapped_column(
        String, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Cached aggregate, recomputed on every /progress/complete. Avoids
    # N+1 progress-query storm for "my enrolled courses" dashboard.
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="enrollments")


# ── Changes to existing models (additions only, no column renames) ─────────
#
# backend/database.py Course class adds:
#
#   creator_user_id: Mapped[int | None] = mapped_column(
#       Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
#   )
#   is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
#   published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
#
# Migration of existing courses:
#   - creator_user_id stays NULL (pre-user-model content)
#   - is_published = True (existing courses are catalog-visible by default;
#     only NEW courses created after this deploy land in draft state)
#   - published_at = created_at
#
# backend/database.py UserProgress.user_id stays String (FK to User.id via
# User.email? no — FK must be the unique PK. Safer: keep user_id as String
# but index it; future pass normalizes to Integer FK if we care enough).
# For now: keep as-is, populate with User.id (stringified) on writes.


__all__ = ["UserRole", "User", "Session", "Enrollment"]
