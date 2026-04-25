"""Tests for check.py — native cli_check kinds + .skillslab.yml parsing.

Bridge mode + LLM-rubric paths are NOT tested here (they require live
LMS / live claude CLI). Native deterministic kinds are fully covered.
"""
from pathlib import Path

import pytest
import yaml

from skillslab import check


# ── _read_skillslab_yml ────────────────────────────────────────────────────

def test_read_skillslab_yml_returns_empty_when_missing(tmp_path):
    out = check._read_skillslab_yml(str(tmp_path))
    assert out == {}


def test_read_skillslab_yml_parses_acceptance_command(tmp_path):
    (tmp_path / ".skillslab.yml").write_text(yaml.dump({
        "acceptance_command": "pytest -q",
        "git_diff": "staged",
    }))
    out = check._read_skillslab_yml(str(tmp_path))
    assert out["acceptance_command"] == "pytest -q"
    assert out["git_diff"] == "staged"


def test_read_skillslab_yml_handles_invalid_yaml(tmp_path):
    (tmp_path / ".skillslab.yml").write_text("[invalid yaml: {")
    out = check._read_skillslab_yml(str(tmp_path))
    assert out == {}


# ── paste_contains ─────────────────────────────────────────────────────────

def test_paste_contains_passes_when_all_tokens_present():
    spec = {"tokens": ["foo", "bar"]}
    out = check._check_paste_contains(spec, "this contains foo and bar both")
    assert out["correct"] is True
    assert out["score"] == 1.0


def test_paste_contains_partial_score_on_missing():
    spec = {"tokens": ["foo", "bar", "baz"]}
    out = check._check_paste_contains(spec, "only foo here")
    assert out["correct"] is False
    assert 0 < out["score"] < 1
    assert "bar" in out["feedback"]
    assert "baz" in out["feedback"]


def test_paste_contains_empty_tokens_list():
    spec = {"tokens": []}
    out = check._check_paste_contains(spec, "anything")
    assert out["correct"] is True


def test_paste_contains_must_contain_alias():
    spec = {"must_contain": ["foo"]}
    out = check._check_paste_contains(spec, "foo bar")
    assert out["correct"] is True


# ── command_exit_zero ──────────────────────────────────────────────────────

def test_command_exit_zero_passes_on_true(tmp_path):
    out = check._check_command_exit_zero({"command": "true"}, str(tmp_path))
    assert out["correct"] is True


def test_command_exit_zero_fails_on_false(tmp_path):
    out = check._check_command_exit_zero({"command": "false"}, str(tmp_path))
    assert out["correct"] is False


def test_command_exit_zero_missing_command_field(tmp_path):
    out = check._check_command_exit_zero({}, str(tmp_path))
    assert out["correct"] is False
    assert "missing" in out["feedback"].lower()


# ── file_exists ────────────────────────────────────────────────────────────

def test_file_exists_passes_when_file_present(tmp_path):
    (tmp_path / "hello.txt").write_text("hi")
    out = check._check_file_exists({"path": "hello.txt"}, str(tmp_path))
    assert out["correct"] is True


def test_file_exists_fails_when_missing(tmp_path):
    out = check._check_file_exists({"path": "nope.txt"}, str(tmp_path))
    assert out["correct"] is False


# ── git_diff_contains (no real git, just empty diff path) ──────────────────

def test_git_diff_contains_fails_on_no_repo(tmp_path):
    """tmp_path isn't a git repo so `git diff` returns empty; missing tokens
    therefore reported."""
    out = check._check_git_diff_contains({"tokens": ["foo"]}, str(tmp_path))
    assert out["correct"] is False
    assert "foo" in out["feedback"]


# ── gha_workflow_check (URL parsing only — no live HTTP) ──────────────────

def test_gha_check_rejects_invalid_url():
    out = check._check_gha({}, "this is not a url")
    assert out["correct"] is False
    assert "github.com" in out["feedback"].lower()


def test_gha_check_rejects_empty_paste():
    out = check._check_gha({}, None)
    assert out["correct"] is False


# ── _parse_rubric_json ─────────────────────────────────────────────────────

def test_parse_rubric_json_direct_json():
    out = check._parse_rubric_json('{"score": 0.85, "correct": true, "feedback": "Solid work"}')
    assert out["correct"] is True
    assert out["score"] == 0.85
    assert "Solid" in out["feedback"]


def test_parse_rubric_json_extracts_from_prose():
    text = 'Sure, here is my judgement:\n{"score": 0.5, "correct": false, "feedback": "Half there"}\nThanks!'
    out = check._parse_rubric_json(text)
    assert out["correct"] is False
    assert out["score"] == 0.5


def test_parse_rubric_json_infers_correct_from_score():
    out = check._parse_rubric_json('{"score": 0.8, "feedback": "Great"}')
    # No `correct` field → infer from score >= 0.7
    assert out["correct"] is True


def test_parse_rubric_json_handles_garbage():
    out = check._parse_rubric_json("the model went off the rails entirely")
    assert out["correct"] is False
    assert "parse" in out["feedback"].lower() or "raw" in out["feedback"].lower()


def test_parse_rubric_json_handles_empty():
    out = check._parse_rubric_json("")
    assert out["correct"] is False
    assert "empty" in out["feedback"].lower()


# ── run_check dispatch ─────────────────────────────────────────────────────

def test_run_check_dispatches_to_native_kind(tmp_path):
    step = {
        "id": 1,
        "exercise_type": "code_exercise",
        "validation": {"cli_check": {"kind": "file_exists", "path": "exists.txt"}},
    }
    (tmp_path / "exists.txt").write_text("y")
    out = check.run_check(step, cwd=str(tmp_path))
    assert out["correct"] is True


def test_run_check_falls_back_to_must_contain(tmp_path):
    step = {
        "id": 1,
        "exercise_type": "concept",
        "validation": {"must_contain": ["IMPORTANT"]},
    }
    out = check.run_check(step, cwd=str(tmp_path), paste="this is IMPORTANT")
    assert out["correct"] is True


def test_run_check_no_grading_hook_returns_useful_message(tmp_path):
    step = {"id": 1, "exercise_type": "concept", "validation": {}}
    out = check.run_check(step, cwd=str(tmp_path))
    assert out["correct"] is False
    assert "no cli_check" in out["feedback"] or "concept-only" in out["feedback"]


def test_run_check_attaches_debug_for_native(tmp_path):
    """--verbose mode renders the _debug field. Verify every dispatch path
    populates it so learners always have a signal to iterate from."""
    step = {
        "id": 1,
        "exercise_type": "code_exercise",
        "validation": {"cli_check": {"kind": "file_exists", "path": "missing.txt"}},
    }
    out = check.run_check(step, cwd=str(tmp_path))
    assert "_debug" in out
    assert out["_debug"]["dispatch"] == "cli_check:file_exists"
    assert "submission" in out["_debug"]
    assert "accept_rc" in out["_debug"]


def test_run_check_attaches_debug_for_must_contain(tmp_path):
    step = {
        "id": 1, "exercise_type": "concept",
        "validation": {"must_contain": ["FOO", "BAR"]},
    }
    out = check.run_check(step, cwd=str(tmp_path), paste="only FOO here")
    assert out["_debug"]["dispatch"] == "must_contain"
    assert "FOO" in out["_debug"]["submission"]


def test_run_check_attaches_debug_for_no_hook(tmp_path):
    step = {"id": 1, "exercise_type": "concept", "validation": {}}
    out = check.run_check(step, cwd=str(tmp_path))
    assert out["_debug"]["dispatch"] == "no_hook"
