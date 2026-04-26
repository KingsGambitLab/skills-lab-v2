"""SQLite → PostgreSQL migration for skills-lab.

Strategy:
  1. Use SQLAlchemy on both ends — model-driven, types are translated.
  2. Build target schema in PG via `Base.metadata.create_all`.
  3. Read all rows from SQLite per-table; INSERT into PG preserving PKs.
  4. After all tables migrated, advance PG sequences for SERIAL columns
     so the next inserted row doesn't collide with a migrated PK.
  5. Run inside a single PG transaction per table (rollback-safe).

Run: python3 migrate_sqlite_to_pg.py
Env: SRC_URL (default: sqlite path) + DST_URL (Postgres URL with creds).
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, text

sys.path.insert(0, "/home/ec2-user/skills-lab-v2")

from backend.database import (
    Base,
    Course, Module, Step, UserProgress, Certificate, ReviewSchedule,
    CourseReview, User, Session, Enrollment,
)

SRC_URL = os.environ.get(
    "SRC_URL", "sqlite+aiosqlite:////home/ec2-user/skills-lab-v2/skills_lab.db"
)
DST_URL = os.environ["DST_URL"]  # required, contains password

# Order matters — parents first so FKs resolve cleanly.
MIGRATION_ORDER = [
    User, Session, Course, Module, Step, Enrollment,
    UserProgress, Certificate, ReviewSchedule, CourseReview,
]

# For tables with auto-increment integer PKs, advance the sequence after
# the migration so the next INSERT picks up where the dump left off.
SEQ_TABLES = {
    "users": "users_id_seq",
    "sessions": None,  # token-PK, no seq
    "modules": "modules_id_seq",
    "steps": "steps_id_seq",
    "enrollments": "enrollments_id_seq",
    "user_progress": "user_progress_id_seq",
    "certificates": "certificates_id_seq",
    "review_schedule": "review_schedule_id_seq",
    "course_reviews": "course_reviews_id_seq",
    # courses: id is VARCHAR (created-XXX), no sequence
}


async def migrate():
    src = create_async_engine(SRC_URL)
    dst = create_async_engine(DST_URL)

    print(f"SRC: {SRC_URL[:80]}...")
    print(f"DST: {DST_URL.split('@')[1] if '@' in DST_URL else DST_URL}")

    # 1. Create schema in destination.
    print("\n=== Creating schema in PG ===")
    async with dst.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("schema OK")

    # 2. Migrate per-table.
    # Track which IDs we've actually migrated PER TABLE so we can null-out
    # FK references that point at rows that don't exist in the source
    # (artifact of past INSERT-OR-REPLACE migrations onto SQLite, which
    # doesn't enforce FK constraints by default; PG does).
    migrated_user_ids: set[int] = set()
    nulled_fk_count = 0

    total_rows = 0
    for model in MIGRATION_ORDER:
        tablename = model.__tablename__
        async with src.connect() as src_conn:
            res = await src_conn.execute(select(model))
            # SQLAlchemy 2.x: convert each Row to a dict of column→value.
            rows = res.all()
            data = []
            for row in rows:
                obj = row[0] if isinstance(row, tuple) else row
                d = {c.name: getattr(obj, c.name, None) for c in model.__table__.columns}

                # FK sanitization: any column ending in `_user_id` or
                # `creator_user_id` MUST reference a user we just migrated.
                # If the referenced user is missing, NULL the FK (the column
                # is nullable in our schema; old SQLite data had dangling
                # refs from past cross-host migrations that didn't carry
                # the user table along).
                for fk_col in ("creator_user_id", "user_id"):
                    if fk_col in d and d[fk_col] is not None:
                        if d[fk_col] not in migrated_user_ids:
                            d[fk_col] = None
                            nulled_fk_count += 1
                data.append(d)
        if not data:
            print(f"  {tablename}: 0 rows (skipped)")
            continue
        async with dst.begin() as dst_conn:
            await dst_conn.execute(model.__table__.insert(), data)
        # After users finish migrating, snapshot their IDs for FK lookup
        # by later tables (courses, sessions, enrollments, user_progress).
        if model is User:
            migrated_user_ids = {d["id"] for d in data}
            print(f"  {tablename}: {len(data)} rows migrated  [user IDs: {sorted(migrated_user_ids)}]")
        else:
            print(f"  {tablename}: {len(data)} rows migrated")
        total_rows += len(data)
    if nulled_fk_count:
        print(f"  [warn] nulled {nulled_fk_count} dangling FK refs (rows kept; ownership lost)")

    # 3. Advance sequences.
    print("\n=== Advancing sequences ===")
    async with dst.begin() as conn:
        for tablename, seq in SEQ_TABLES.items():
            if not seq:
                continue
            try:
                # setval uses the current MAX from the table; if the table
                # has rows, advance to MAX+1; if empty, leave alone.
                await conn.execute(text(
                    f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {tablename}), 1), true)"
                ))
                print(f"  {seq}: advanced to MAX(id) of {tablename}")
            except Exception as e:
                print(f"  {seq}: SKIPPED — {e!r}")

    # 4. Verify counts match.
    print("\n=== Verification: row counts SQLite → PG ===")
    for model in MIGRATION_ORDER:
        tablename = model.__tablename__
        async with src.connect() as src_conn:
            src_count = (await src_conn.execute(text(f"SELECT count(*) FROM {tablename}"))).scalar()
        async with dst.connect() as dst_conn:
            dst_count = (await dst_conn.execute(text(f"SELECT count(*) FROM {tablename}"))).scalar()
        match = "✓" if src_count == dst_count else "✗ MISMATCH"
        print(f"  {tablename:20s}  {src_count:6} → {dst_count:6}  {match}")

    print(f"\nTotal rows migrated: {total_rows}")
    await src.dispose()
    await dst.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
