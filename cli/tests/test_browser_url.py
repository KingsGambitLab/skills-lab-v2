"""Tests for `_browser_url` — guards the DB-position → frontend-stepIdx
mapping against off-by-one regressions.

Background: the frontend's `parseHash` reads `parts[2]` as a 0-indexed
array index into `state.currentModuleData.steps[]`. The DB stores
`step.position` as 1-indexed (1, 2, 3, …). Earlier impl emitted the
1-indexed value verbatim → clicking an `M1.S1` deep-link landed on
`M1.S2`. This file tests the mapping mechanically + ROUND-TRIP-style:
build URL → parse URL → assert it resolves back to the same step.

Per the 2026-04-27 cli_walk shim invariant II3 — keep the round-trip
assertion in unit-tests so a regression breaks CI, not just an agent
walk.
"""
import os

import pytest

from skillslab.cli import _browser_url


@pytest.fixture(autouse=True)
def _set_web_url(monkeypatch):
    monkeypatch.setenv("SKILLSLAB_WEB_URL", "http://test-host")


def _parse_hash(url: str) -> tuple[str, int | None, int | None]:
    """Mirror of frontend `parseHash` (frontend/index.html). Returns
    (course_id, module_id, step_idx). step_idx is None if the hash has
    fewer than 3 parts.
    """
    assert "#" in url, f"URL missing fragment: {url!r}"
    hash_part = url.split("#", 1)[1]
    parts = [p for p in hash_part.split("/") if p]
    course_id = parts[0]
    module_id = int(parts[1]) if len(parts) >= 2 else None
    step_idx = int(parts[2]) if len(parts) >= 3 else None
    return course_id, module_id, step_idx


def test_first_step_emits_zero_index():
    """The first step of any module (DB position=1) must serialize as
    `/0` in the URL — frontend will use parts[2] as a 0-indexed array
    index. Pre-fix this emitted `/1` and learners landed on the SECOND
    step of the module instead of the first.
    """
    url = _browser_url("created-7fee8b78c742", {
        "module_id": 23189,
        "step_pos": 1,
    })
    assert url.endswith("/23189/0"), f"M1.S1 URL should end /23189/0, got {url!r}"
    _, _, step_idx = _parse_hash(url)
    assert step_idx == 0


def test_second_step_emits_one_index():
    url = _browser_url("created-7fee8b78c742", {
        "module_id": 23189,
        "step_pos": 2,
    })
    _, _, step_idx = _parse_hash(url)
    assert step_idx == 1


def test_round_trip_resolves_to_same_step():
    """Round-trip: build URL → parse URL → look up by parsed stepIdx
    in a position-sorted module → must resolve back to the original
    step we started with.

    This is the test the cli_walk shim's II3 invariant runs as an agent
    behavioral check; here it lives as a fast unit-test so the same
    regression breaks `pytest`, not just an agent walk.
    """
    # Minimal "DB" — list of steps in module, sorted by position
    # (the same shape `state.currentModuleData.steps` is in the frontend).
    module_steps = [
        {"id": 85060, "position": 1, "title": "AI-augmented coding at senior level"},
        {"id": 85061, "position": 2, "title": "Diagnose + fix the failing test"},
        {"id": 85062, "position": 3, "title": "Find the subtle bug"},
        {"id": 85063, "position": 4, "title": "Name the gaps you hit"},
    ]
    course_id = "created-7fee8b78c742"
    module_id = 23189

    for original in module_steps:
        url = _browser_url(course_id, {
            "module_id": module_id,
            "step_pos": original["position"],
        })
        _, parsed_mod_id, parsed_step_idx = _parse_hash(url)
        assert parsed_mod_id == module_id, f"module mismatch on {original['title']!r}"
        assert 0 <= parsed_step_idx < len(module_steps), (
            f"stepIdx {parsed_step_idx} out of bounds 0..{len(module_steps)-1} "
            f"for step pos={original['position']!r}"
        )
        # The frontend's `state.currentModuleData.steps[parsed_step_idx]`
        # MUST resolve to the step the URL claims to point at.
        resolved = module_steps[parsed_step_idx]
        assert resolved["id"] == original["id"], (
            f"URL points at step id={resolved['id']!r} "
            f"({resolved['title']!r}) but the CLI built it for step "
            f"id={original['id']!r} ({original['title']!r}). "
            f"Off-by-one between DB position and frontend stepIdx."
        )


def test_legacy_zero_position_does_not_underflow():
    """Old data with step_pos=0 (legacy bug fixture) shouldn't produce
    a URL like `/23189/-1`. Should clamp to 0.
    """
    url = _browser_url("c", {"module_id": 1, "step_pos": 0})
    assert url.endswith("/1/0")


def test_no_module_id_falls_back_to_course_only():
    url = _browser_url("c", {})
    assert url.endswith("#c")


def test_module_only_no_step_pos():
    url = _browser_url("c", {"module_id": 99})
    assert url.endswith("/99")


def test_string_step_pos_is_handled():
    """Defensive: state.json sometimes stores step_pos as a string
    (JSON deserialization quirk). The function should coerce.
    """
    url = _browser_url("c", {"module_id": 99, "step_pos": "3"})
    assert url.endswith("/99/2")
