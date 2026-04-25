"""Tests for state.py — filesystem layout + step filename construction."""
from pathlib import Path

import pytest

from skillslab import state


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Re-point SKILLSLAB_HOME at a tmp dir for the duration of the test."""
    monkeypatch.setenv("SKILLSLAB_HOME", str(tmp_path))
    return tmp_path


def test_home_creates_directory(tmp_home):
    h = state.home()
    assert h == tmp_home
    assert h.is_dir()


def test_token_roundtrip(tmp_home):
    assert state.get_token() is None
    state.set_token("abc123")
    assert state.get_token() == "abc123"
    state.clear_token()
    assert state.get_token() is None


def test_token_file_is_chmod_600(tmp_home):
    state.set_token("xyz")
    p = state.token_path()
    mode = p.stat().st_mode & 0o777
    assert mode == 0o600


def test_step_filename_format():
    fn = state.step_filename(module_pos=1, step_pos=0, title="What this course is")
    # M0 because module_pos=1 means backend's first module → M0 in human numbering
    assert fn == "M0.S0-what-this-course-is.md"


def test_step_filename_handles_empty_title():
    fn = state.step_filename(module_pos=2, step_pos=3, title="")
    assert fn == "M1.S3-step.md"


def test_step_filename_truncates_long_titles():
    title = "A" * 200
    fn = state.step_filename(module_pos=1, step_pos=0, title=title)
    assert len(fn.split("-")[-1].replace(".md", "")) <= 60


def test_meta_roundtrip(tmp_home):
    state.write_meta("kimi", {"course_id": "created-abc", "cursor": 3})
    out = state.read_meta("kimi")
    assert out["course_id"] == "created-abc"
    assert out["cursor"] == 3


def test_read_meta_missing_returns_empty(tmp_home):
    assert state.read_meta("nonexistent") == {}


def test_course_dir_creates_steps_subdir(tmp_home):
    cdir = state.course_dir("aie")
    assert cdir.is_dir()
    assert (cdir / "steps").is_dir()


def test_api_url_default(tmp_home, monkeypatch):
    monkeypatch.delenv("SKILLSLAB_API_URL", raising=False)
    # No file written yet → falls back to default
    assert state.api_url() == "http://localhost:8001"


def test_api_url_env_overrides_file(tmp_home, monkeypatch):
    state.set_api_url("https://saved.example.com")
    monkeypatch.setenv("SKILLSLAB_API_URL", "https://env.example.com")
    assert state.api_url() == "https://env.example.com"


def test_api_url_persists_to_file(tmp_home, monkeypatch):
    monkeypatch.delenv("SKILLSLAB_API_URL", raising=False)
    state.set_api_url("https://prod.example.com")
    assert state.api_url() == "https://prod.example.com"
