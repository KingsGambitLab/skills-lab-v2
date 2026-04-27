"""Tests for per-step attempt tracking (state.record_attempt + friends).

Background: backend's /api/exercises/validate gates the answer-key
reveal behind attempt_number >= 3. The CLI was sending no attempt
counter → backend defaulted to 1 → "2 more retries" forever, full
breakdown never revealed. User caught it live on AIE M2.S3
(CLAUDE.md authoring) — submitted same content many times, counter
never decremented.

These tests pin the persist-and-increment semantics so a regression
breaks `pytest`, not just a learner's session.
"""
import json

import pytest

from skillslab import state


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path, monkeypatch):
    """Redirect ~/.skillslab to a tmpdir so tests don't touch the real
    learner state on the dev machine.

    state.home() reads SKILLSLAB_HOME env (with fallback to a module-level
    DEFAULT_HOME computed once at import). Override via env so each test
    gets a fresh dir.
    """
    monkeypatch.setenv("SKILLSLAB_HOME", str(tmp_path / ".skillslab"))
    yield


def test_first_record_returns_one():
    n = state.record_attempt("kimi", 85100)
    assert n == 1


def test_second_record_returns_two():
    state.record_attempt("kimi", 85100)
    n = state.record_attempt("kimi", 85100)
    assert n == 2


def test_third_record_returns_three_revealing_the_gate_trip():
    """Backend's reveal-gate flips at attempt_num >= 3. Confirm we
    actually hit 3 — this is the load-bearing assertion.
    """
    for _ in range(2):
        state.record_attempt("kimi", 85100)
    assert state.record_attempt("kimi", 85100) == 3


def test_attempts_are_per_step():
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85101)
    assert state.get_attempt("kimi", 85100) == 2
    assert state.get_attempt("kimi", 85101) == 1


def test_attempts_are_per_course_slug():
    """Different courses don't share attempt buckets (so an aie attempt
    doesn't leak into kimi's count).
    """
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85100)
    state.record_attempt("aie", 85100)  # same step_id, different course
    assert state.get_attempt("kimi", 85100) == 2
    assert state.get_attempt("aie", 85100) == 1


def test_get_attempt_for_unseen_step_returns_zero():
    assert state.get_attempt("kimi", 99999) == 0


def test_attempts_persist_across_calls():
    """The persistence is the whole point — without it, every CLI
    invocation would start fresh and the counter would never reach 3.
    """
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85100)
    # Simulate: brand-new Python process, same HOME
    n = state.record_attempt("kimi", 85100)
    assert n == 3


def test_reset_attempts_for_specific_step():
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85101)
    state.reset_attempts("kimi", 85100)
    assert state.get_attempt("kimi", 85100) == 0
    assert state.get_attempt("kimi", 85101) == 1  # untouched


def test_reset_attempts_for_whole_course():
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85101)
    state.reset_attempts("kimi")
    assert state.get_attempt("kimi", 85100) == 0
    assert state.get_attempt("kimi", 85101) == 0


def test_persistence_file_is_json_dict():
    """Sanity: the on-disk shape is a flat dict[str, int] so external
    inspection tools can read it. Don't accidentally pickle.
    """
    state.record_attempt("kimi", 85100)
    state.record_attempt("kimi", 85100)
    p = state.course_dir("kimi") / "attempts.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert data == {"85100": 2}


def test_string_step_id_normalized():
    """Step IDs sometimes arrive as strings (JSON deser), sometimes as
    ints (DB). The store should normalize so both look up the same row.
    """
    state.record_attempt("kimi", 85100)      # int
    n = state.record_attempt("kimi", "85100")  # str
    assert n == 2
