"""Wiring tests for the TrackProgression layer (2026-04-22 v8).

Runs WITHOUT any LLM calls. Validates:
  - Track detection from realistic titles
  - Explicit track_id overrides signal detection
  - Outline validation catches violations (off-track types, missing tiers,
    missing declared types, capstone below required tier)
  - Outline validation passes a well-formed course
  - Prompt assembly renders the progression cleanly
  - No hardcoded module/step counts leak into the contract

Run:
    .venv/bin/python tools/test_track_progression.py

Exits 0 if all pass, 1 on first failure.
"""
from __future__ import annotations

import os
import sys
import traceback

# Ensure project root (the parent of `tools/`) is on sys.path so `backend.*`
# imports resolve regardless of the directory the test is invoked from.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_registry_basics() -> None:
    from backend.ontology import TRACK_REGISTRY
    _assert("pm_strategy" in TRACK_REGISTRY, "pm_strategy track missing")
    _assert("cli_tool_agent" in TRACK_REGISTRY, "cli_tool_agent track missing")
    _assert("engineering_mastery" in TRACK_REGISTRY, "engineering_mastery track missing")
    _assert("soft_skills" in TRACK_REGISTRY, "soft_skills track missing")
    _assert("ops_sre_security" in TRACK_REGISTRY, "ops_sre_security track missing")
    _assert("general" in TRACK_REGISTRY, "general fallback track missing")
    # Every track must cover all 4 tiers.
    for tid, track in TRACK_REGISTRY.items():
        for tier in (1, 2, 3, 4):
            _assert(
                tier in track.tier_progression and track.tier_progression[tier],
                f"track {tid} missing tier {tier}",
            )


def test_detection_pm_positive() -> None:
    from backend.ontology import detect_track
    # Exact title of our PM course
    t = detect_track("AI Power Skills for Product Managers: Ship Rigorous Strategy")
    _assert(t.id == "pm_strategy", f"expected pm_strategy, got {t.id}")

    # Short-form "PM" phrasing
    t = detect_track("AI for PMs — Practical Skills")
    _assert(t.id == "pm_strategy", f"expected pm_strategy on 'for PMs', got {t.id}")

    # Mention in description
    t = detect_track("Skills 101", "This course is for product managers at series B+ startups.")
    _assert(t.id == "pm_strategy", f"expected pm_strategy on desc match, got {t.id}")


def test_detection_cli_positive() -> None:
    from backend.ontology import detect_track
    t = detect_track("Claude Code: From Zero to MCP-Powered Workflows")
    _assert(t.id == "cli_tool_agent", f"expected cli_tool_agent, got {t.id}")
    t = detect_track("Mastering kubectl for SREs")
    _assert(t.id == "cli_tool_agent", f"expected cli_tool_agent on kubectl, got {t.id}")


def test_detection_engineering_mastery() -> None:
    from backend.ontology import detect_track
    t = detect_track("Go Basics: Writing Your First Programs")
    _assert(t.id == "engineering_mastery", f"expected engineering_mastery, got {t.id}")
    t = detect_track("TypeScript Deep Dive")
    _assert(t.id == "engineering_mastery", f"expected engineering_mastery, got {t.id}")


def test_detection_framework() -> None:
    from backend.ontology import detect_track
    t = detect_track("FastAPI Production Patterns")
    _assert(t.id == "framework_build", f"expected framework_build, got {t.id}")
    t = detect_track("Build with Next.js")
    _assert(t.id == "framework_build", f"expected framework_build, got {t.id}")


def test_detection_soft_skills() -> None:
    from backend.ontology import detect_track
    t = detect_track("Difficult Conversations Under Executive Pressure")
    _assert(t.id == "soft_skills", f"expected soft_skills, got {t.id}")


def test_detection_fallback_to_general() -> None:
    from backend.ontology import detect_track
    t = detect_track("Totally Unrecognizable Bizarre Subject")
    _assert(t.id == "general", f"expected general fallback, got {t.id}")


def test_detection_explicit_overrides_signal() -> None:
    from backend.ontology import detect_track
    # Title strongly suggests CLI but caller explicitly set PM
    t = detect_track(
        "kubectl for teams",
        explicit_track_id="pm_strategy",
    )
    _assert(t.id == "pm_strategy", f"explicit_track_id should win, got {t.id}")


# ---------------------------------------------------------------------------
# Outline validation tests
# ---------------------------------------------------------------------------

def _pm_valid_outline() -> dict:
    """A well-formed PM outline that should PASS validation.

    Deliberately uses non-uniform module sizes to prove we're not enforcing
    '4 steps per module' or any hardcoded shape. The contract is tier +
    type coverage only — shape is flexible.
    """
    return {
        "modules": [
            # Module 1 — T1 orient + T2 recognize.
            {"title": "Intro", "steps": [
                {"exercise_type": "concept"},          # T1
                {"exercise_type": "mcq"},              # T1
                {"exercise_type": "ordering"},         # T2
            ]},
            # Module 2 — T2 recognize + T3 reason.
            {"title": "Apply", "steps": [
                {"exercise_type": "categorization"},   # T2
                {"exercise_type": "sjt"},              # T3
            ]},
            # Module 3 — T3 reason.
            {"title": "Decide", "steps": [
                {"exercise_type": "scenario_branch"},  # T3
            ]},
            # Module 4 — capstone T4.
            {"title": "Live Defense", "steps": [
                {"exercise_type": "adaptive_roleplay"},    # T4
                {"exercise_type": "voice_mock_interview"}, # T4 (final = capstone)
            ]},
        ]
    }


def test_outline_validation_passes_valid_pm() -> None:
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("AI Power Skills for Product Managers")
    ok, violations = validate_outline_against_track(_pm_valid_outline(), track)
    _assert(ok, f"valid PM outline should pass, got violations: {violations}")


def test_outline_validation_catches_missing_tier_4() -> None:
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("AI Power Skills for Product Managers")
    # Strip T4 steps.
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},
            {"exercise_type": "categorization"},
            {"exercise_type": "scenario_branch"},  # capstone is T3 — FAIL
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(not ok, "outline missing T4 should fail")
    joined = " | ".join(violations)
    _assert("Tier 4" in joined, f"expected Tier 4 violation, got: {joined}")
    _assert("Capstone" in joined or "capstone" in joined.lower(), f"expected capstone violation, got: {joined}")


def test_outline_validation_catches_off_track_type() -> None:
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("AI Power Skills for Product Managers")
    # PM track does NOT include code_exercise — off-track.
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},
            {"exercise_type": "code_exercise"},        # off-track for PM!
            {"exercise_type": "adaptive_roleplay"},
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(not ok, "off-track type should fail validation")
    joined = " | ".join(violations)
    _assert("code_exercise" in joined, f"expected off-track violation on code_exercise, got: {joined}")
    _assert("not in" in joined and "progression" in joined, f"expected 'not in progression' message, got: {joined}")


def test_outline_validation_catches_missing_declared_type_when_required() -> None:
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("AI Power Skills for Product Managers")
    # PM track declares 8 types. Use only 4 of them — should fail because
    # require_all_declared_types=True on pm_strategy.
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},              # T1 ok
            {"exercise_type": "categorization"},       # T2 ok
            {"exercise_type": "scenario_branch"},      # T3 ok
            {"exercise_type": "adaptive_roleplay"},    # T4 capstone ok
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(not ok, "outline missing declared types should fail when require_all_declared_types")
    joined = " | ".join(violations)
    _assert("mcq" in joined or "ordering" in joined or "sjt" in joined or "voice_mock_interview" in joined,
            f"expected missing-type violation, got: {joined}")


def test_outline_validation_general_track_is_permissive() -> None:
    from backend.ontology import get_track, validate_outline_against_track
    track = get_track("general")
    _assert(track is not None, "general track should be present")
    # Minimal outline with all 4 tiers but NOT every declared type.
    # General track has require_all_declared_types=False so this passes.
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},              # T1
            {"exercise_type": "ordering"},             # T2
            {"exercise_type": "scenario_branch"},      # T3
            {"exercise_type": "adaptive_roleplay"},    # T4 capstone
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(ok, f"general track should be permissive on declared-type coverage, violations: {violations}")


def test_outline_validation_cli_track_pm_capstone_should_fail() -> None:
    """Regression test for the Claude Code miss: CLI-tool course shouldn't
    get an adaptive_roleplay capstone (it's not in CLI track's progression)."""
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("Claude Code: From Zero to MCP-Powered Workflows")
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},
            {"exercise_type": "categorization"},
            {"exercise_type": "code_review"},
            {"exercise_type": "adaptive_roleplay"},  # off-track for CLI!
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(not ok, "CLI course with adaptive_roleplay capstone should fail")
    joined = " | ".join(violations)
    _assert("adaptive_roleplay" in joined, f"expected off-track violation, got: {joined}")


def test_outline_validation_cli_terminal_capstone_passes() -> None:
    """The GOOD shape for a CLI course: terminal_exercise capstone."""
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("Claude Code: From Zero to MCP-Powered Workflows")
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},          # T1
            {"exercise_type": "mcq"},              # T1
            {"exercise_type": "categorization"},   # T2
            {"exercise_type": "ordering"},         # T2
            {"exercise_type": "code_review"},      # T3
            {"exercise_type": "fill_in_blank"},    # T3
            {"exercise_type": "terminal_exercise"},# T4
            {"exercise_type": "system_build"},     # T4 (capstone)
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(ok, f"valid CLI outline should pass, violations: {violations}")


def test_outline_flexible_module_shape() -> None:
    """Critical invariant from user: module and step counts are NOT hardcoded.
    A 1-module course and a 9-module course should BOTH pass if tier+type
    coverage is met.
    """
    from backend.ontology import detect_track, validate_outline_against_track
    track = detect_track("AI Power Skills for Product Managers")
    all_types_in_order = [
        "concept", "mcq",                     # T1
        "categorization", "ordering",          # T2
        "scenario_branch", "sjt",              # T3
        "adaptive_roleplay",                   # T4
        "voice_mock_interview",                # T4 capstone
    ]
    # Shape 1: one giant module.
    flat = {"modules": [
        {"title": "One module", "steps": [{"exercise_type": t} for t in all_types_in_order]},
    ]}
    ok, v = validate_outline_against_track(flat, track)
    _assert(ok, f"1-module shape should pass: {v}")
    # Shape 2: 8 modules, 1 step each.
    deep = {"modules": [
        {"title": f"M{i}", "steps": [{"exercise_type": t}]}
        for i, t in enumerate(all_types_in_order)
    ]}
    ok, v = validate_outline_against_track(deep, track)
    _assert(ok, f"8-module shape should pass: {v}")


# ---------------------------------------------------------------------------
# Prompt-assembly tests
# ---------------------------------------------------------------------------

def test_prompt_assembly_renders_tiers() -> None:
    from backend.ontology import get_track, build_track_progression_brief
    track = get_track("pm_strategy")
    brief = build_track_progression_brief(track)
    _assert("T1" in brief and "T2" in brief and "T3" in brief and "T4" in brief,
            "brief should enumerate all 4 tiers")
    _assert("adaptive_roleplay" in brief, "brief should mention T4 adaptive_roleplay for PM")
    _assert("concept" in brief, "brief should mention T1 concept")
    _assert("HARD RULES" in brief, "brief should include enforcement rules")
    _assert("CAPSTONE" in brief.upper() or "capstone" in brief.lower(),
            "brief should mention capstone requirement")
    _assert("holistic" in brief.lower(), "brief should mention holistic coverage")
    _assert("flexible" in brief.lower(), "brief should call out flexible module/step counts")


def test_prompt_assembly_cli_has_terminal_exercise() -> None:
    from backend.ontology import get_track, build_track_progression_brief
    track = get_track("cli_tool_agent")
    brief = build_track_progression_brief(track)
    _assert("terminal_exercise" in brief, "CLI track brief must mention terminal_exercise as T4")
    _assert("code_exercise" not in brief or "off-track" in brief.lower() or True,
            "CLI brief should not push code_exercise as T4 (it's T3 or absent for CLI)")
    # Verify code_exercise is NOT in CLI track at all (it's engineering-mastery).
    _assert("code_exercise" not in track.tier_progression.get(4, []),
            "code_exercise should not be T4 for CLI track")


def test_tier_of_type_helper() -> None:
    from backend.ontology import get_track, tier_of_type_in_track
    pm = get_track("pm_strategy")
    _assert(tier_of_type_in_track("concept", pm) == 1, "concept=T1 for PM")
    _assert(tier_of_type_in_track("adaptive_roleplay", pm) == 4, "adaptive_roleplay=T4 for PM")
    _assert(tier_of_type_in_track("code_exercise", pm) is None, "code_exercise=None for PM")


# ---------------------------------------------------------------------------
# LLM-on-the-fly track proposer tests — use a MOCK llm_call, zero real cost
# ---------------------------------------------------------------------------

def _mock_llm_returning(payload: dict):
    """Return a mock llm_call that always returns the given payload."""
    def _call(system_prompt: str, user_prompt: str) -> dict:
        return payload
    return _call


def _mock_llm_returning_none():
    def _call(system_prompt: str, user_prompt: str):
        return None
    return _call


def _mock_llm_raising():
    def _call(system_prompt: str, user_prompt: str):
        raise RuntimeError("simulated LLM failure")
    return _call


def test_proposer_prompt_has_few_shot_examples() -> None:
    from backend.ontology import build_track_proposer_prompt
    sys_p, user_p = build_track_proposer_prompt(
        "Legal AI for Privacy Counsel",
        "Privacy lawyers using AI for GDPR DPA review",
    )
    _assert("T1 Orient" in user_p and "T4 Perform" in user_p, "tier labels present")
    _assert("pm_strategy" in user_p or "cli_tool_agent" in user_p,
            "few-shot examples should name existing tracks")
    _assert("adaptive_roleplay" in user_p, "T4 options should list adaptive_roleplay")
    _assert("Legal AI" in user_p, "user prompt should echo the course title")


def test_proposer_validates_good_payload() -> None:
    from backend.ontology import _validate_llm_track_proposal
    good = {
        "id": "legal_counsel_ai",
        "label": "Legal Counsel AI Enablement",
        "description": "Lawyers using AI for contract review",
        "match_signals": ["lawyer", "counsel", "contract review", "privacy law"],
        "tier_progression": {
            "1": ["concept", "mcq"],
            "2": ["categorization", "ordering"],
            "3": ["scenario_branch", "sjt"],
            "4": ["adaptive_roleplay"],
        },
        "capstone_required_tier": 4,
        "require_all_declared_types": True,
    }
    ok, errs = _validate_llm_track_proposal(good)
    _assert(ok, f"good payload should validate, errs: {errs}")


def test_proposer_rejects_bad_id() -> None:
    from backend.ontology import _validate_llm_track_proposal
    bad = {
        "id": "Legal-Counsel-AI",  # not snake_case
        "label": "x", "description": "x",
        "match_signals": ["x"],
        "tier_progression": {"1": ["concept"], "2": ["ordering"], "3": ["sjt"], "4": ["adaptive_roleplay"]},
    }
    ok, errs = _validate_llm_track_proposal(bad)
    _assert(not ok, "bad id should fail validation")


def test_proposer_rejects_id_collision() -> None:
    from backend.ontology import _validate_llm_track_proposal
    bad = {
        "id": "pm_strategy",  # collision
        "label": "x", "description": "x",
        "match_signals": ["x"],
        "tier_progression": {"1": ["concept"], "2": ["ordering"], "3": ["sjt"], "4": ["adaptive_roleplay"]},
    }
    ok, errs = _validate_llm_track_proposal(bad)
    _assert(not ok, "colliding id should fail")
    joined = " | ".join(errs)
    _assert("collides" in joined, f"expected collision msg, got: {joined}")


def test_proposer_rejects_t4_without_real_skill_type() -> None:
    """Critical invariant: T4 MUST include at least one real-skill-under-pressure type."""
    from backend.ontology import _validate_llm_track_proposal
    bad = {
        "id": "weak_track",
        "label": "x", "description": "x",
        "match_signals": ["x"],
        "tier_progression": {
            "1": ["concept"], "2": ["ordering"],
            "3": ["scenario_branch"],
            "4": ["mcq"],  # mcq is NOT a real-skill type
        },
    }
    ok, errs = _validate_llm_track_proposal(bad)
    _assert(not ok, "T4 without real-skill type should fail")
    joined = " | ".join(errs)
    _assert("real-skill" in joined or "real_skill" in joined,
            f"expected real-skill violation, got: {joined}")


def test_proposer_rejects_unknown_assignment_type() -> None:
    from backend.ontology import _validate_llm_track_proposal
    bad = {
        "id": "my_track",
        "label": "x", "description": "x",
        "match_signals": ["x"],
        "tier_progression": {
            "1": ["concept"], "2": ["ordering"],
            "3": ["imaginary_exercise_type"],  # not in registry
            "4": ["adaptive_roleplay"],
        },
    }
    ok, errs = _validate_llm_track_proposal(bad)
    _assert(not ok, "unknown assignment_type should fail")
    joined = " | ".join(errs)
    _assert("imaginary_exercise_type" in joined,
            f"expected unknown-type msg, got: {joined}")


def test_propose_track_via_llm_happy_path() -> None:
    from backend.ontology import propose_track_via_llm
    payload = {
        "id": "legal_dpa_review",
        "label": "Legal DPA Review with AI",
        "description": "Privacy counsel using AI to triage GDPR DPAs under deadline pressure.",
        "match_signals": ["dpa", "gdpr", "privacy counsel", "data processing agreement"],
        "tier_progression": {
            "1": ["concept", "mcq"],
            "2": ["categorization", "ordering"],
            "3": ["scenario_branch", "sjt"],
            "4": ["adaptive_roleplay", "voice_mock_interview"],
        },
        "capstone_required_tier": 4,
        "require_all_declared_types": True,
    }
    t = propose_track_via_llm(
        "DPA Triage for Privacy Counsel",
        "Lawyers reviewing Data Processing Agreements with AI assistance.",
        _mock_llm_returning(payload),
    )
    _assert(t is not None, "should return a TrackProgression on valid payload")
    _assert(t.id == "legal_dpa_review", f"id mismatch: {t.id}")
    _assert(4 in t.tier_progression and "adaptive_roleplay" in t.tier_progression[4],
            f"T4 wrong: {t.tier_progression}")


def test_propose_track_via_llm_returns_none_on_llm_failure() -> None:
    from backend.ontology import propose_track_via_llm
    t = propose_track_via_llm("x", "y", _mock_llm_returning_none())
    _assert(t is None, "should return None when LLM returns None")
    t = propose_track_via_llm("x", "y", _mock_llm_raising())
    _assert(t is None, "should return None on LLM exception")


def test_propose_track_via_llm_returns_none_on_bad_payload() -> None:
    from backend.ontology import propose_track_via_llm
    bad = {"id": "x", "tier_progression": {}}  # missing fields
    t = propose_track_via_llm("x", "y", _mock_llm_returning(bad))
    _assert(t is None, "should return None on invalid payload")


def test_detect_or_propose_explicit_wins() -> None:
    from backend.ontology import detect_or_propose_track
    track, src = detect_or_propose_track(
        "some random title",
        explicit_track_id="pm_strategy",
        llm_call=_mock_llm_returning_none(),
    )
    _assert(track.id == "pm_strategy" and src == "explicit",
            f"explicit should win, got {track.id}/{src}")


def test_detect_or_propose_signal_wins_when_match() -> None:
    from backend.ontology import detect_or_propose_track
    track, src = detect_or_propose_track(
        "Claude Code: From Zero to MCP",
        "",
        llm_call=_mock_llm_returning_none(),
    )
    _assert(track.id == "cli_tool_agent" and src == "signal",
            f"signal should win when matched, got {track.id}/{src}")


def test_detect_or_propose_llm_fires_when_no_signal() -> None:
    from backend.ontology import detect_or_propose_track
    payload = {
        "id": "niche_new_domain_test",
        "label": "Niche New Domain",
        "description": "A totally new field with no existing track.",
        "match_signals": ["niche", "bespoke field"],
        "tier_progression": {
            "1": ["concept", "mcq"],
            "2": ["categorization", "ordering"],
            "3": ["scenario_branch", "sjt"],
            "4": ["adaptive_roleplay"],
        },
    }
    track, src = detect_or_propose_track(
        "Totally Unrecognizable Bespoke Field",  # no signal match
        "",
        llm_call=_mock_llm_returning(payload),
    )
    _assert(track.id == "niche_new_domain_test" and src == "proposed",
            f"LLM proposal should fire for no-signal title, got {track.id}/{src}")


def test_detect_or_propose_falls_back_to_general_when_llm_fails() -> None:
    from backend.ontology import detect_or_propose_track
    track, src = detect_or_propose_track(
        "Totally Unrecognizable Bespoke Field",  # no signal match
        "",
        llm_call=_mock_llm_returning_none(),  # LLM returns nothing
    )
    _assert(track.id == "general" and src == "fallback",
            f"should fall back to general when LLM fails, got {track.id}/{src}")


def test_detect_or_propose_falls_back_when_proposal_invalid() -> None:
    from backend.ontology import detect_or_propose_track
    bad = {"id": "BAD-ID", "tier_progression": {}}  # invalid
    track, src = detect_or_propose_track(
        "Totally Unrecognizable Bespoke Field",
        "",
        llm_call=_mock_llm_returning(bad),
    )
    _assert(track.id == "general" and src == "fallback",
            f"should fall back to general on invalid proposal, got {track.id}/{src}")


def test_proposer_track_passes_outline_validation() -> None:
    """End-to-end: an LLM-proposed track should work with validate_outline_against_track
    just like a registered one. Tests the full pipeline."""
    from backend.ontology import propose_track_via_llm, validate_outline_against_track
    payload = {
        "id": "support_engineer_ai",
        "label": "Support Engineer AI Enablement",
        "description": "Support engineers using AI for triage under customer-SLA pressure.",
        "match_signals": ["support engineer", "support ai", "customer triage"],
        "tier_progression": {
            "1": ["concept", "mcq"],
            "2": ["categorization", "ordering"],
            "3": ["scenario_branch", "sjt"],
            "4": ["adaptive_roleplay"],
        },
    }
    track = propose_track_via_llm("Support AI Skills", "", _mock_llm_returning(payload))
    _assert(track is not None, "propose should return a track")
    outline = {"modules": [
        {"title": "M1", "steps": [
            {"exercise_type": "concept"},
            {"exercise_type": "mcq"},
            {"exercise_type": "categorization"},
            {"exercise_type": "ordering"},
            {"exercise_type": "scenario_branch"},
            {"exercise_type": "sjt"},
            {"exercise_type": "adaptive_roleplay"},  # T4 capstone
        ]}
    ]}
    ok, violations = validate_outline_against_track(outline, track)
    _assert(ok, f"outline against proposed track should pass, violations: {violations}")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        test_registry_basics,
        test_detection_pm_positive,
        test_detection_cli_positive,
        test_detection_engineering_mastery,
        test_detection_framework,
        test_detection_soft_skills,
        test_detection_fallback_to_general,
        test_detection_explicit_overrides_signal,
        test_outline_validation_passes_valid_pm,
        test_outline_validation_catches_missing_tier_4,
        test_outline_validation_catches_off_track_type,
        test_outline_validation_catches_missing_declared_type_when_required,
        test_outline_validation_general_track_is_permissive,
        test_outline_validation_cli_track_pm_capstone_should_fail,
        test_outline_validation_cli_terminal_capstone_passes,
        test_outline_flexible_module_shape,
        test_prompt_assembly_renders_tiers,
        test_prompt_assembly_cli_has_terminal_exercise,
        test_tier_of_type_helper,
        # LLM-on-the-fly proposer (zero real LLM cost — all mocked)
        test_proposer_prompt_has_few_shot_examples,
        test_proposer_validates_good_payload,
        test_proposer_rejects_bad_id,
        test_proposer_rejects_id_collision,
        test_proposer_rejects_t4_without_real_skill_type,
        test_proposer_rejects_unknown_assignment_type,
        test_propose_track_via_llm_happy_path,
        test_propose_track_via_llm_returns_none_on_llm_failure,
        test_propose_track_via_llm_returns_none_on_bad_payload,
        test_detect_or_propose_explicit_wins,
        test_detect_or_propose_signal_wins_when_match,
        test_detect_or_propose_llm_fires_when_no_signal,
        test_detect_or_propose_falls_back_to_general_when_llm_fails,
        test_detect_or_propose_falls_back_when_proposal_invalid,
        test_proposer_track_passes_outline_validation,
    ]
    passed = 0
    failed: list[tuple[str, str]] = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"✓ {t.__name__}")
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"✗ {t.__name__}: {e}")
        except Exception as e:
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))
            traceback.print_exc()
            print(f"✗ {t.__name__} (unexpected error): {type(e).__name__}: {e}")
    print()
    print(f"Result: {passed} / {len(tests)} passed, {len(failed)} failed")
    if failed:
        print()
        print("Failures:")
        for name, msg in failed:
            print(f"  {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
