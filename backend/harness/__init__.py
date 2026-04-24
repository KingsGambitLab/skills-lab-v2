"""skills-lab-v2 testing harness package.

Exports reusable primitives for spawning test agents against generated courses.
Current modules:
  - beginner_agent: RL-style learner walkthrough prompt builder.
  - domain_expert: senior-practitioner review prompt builder
    (v8 dual-agent gate for AI-enablement courses).
"""
from .beginner_agent import build_prompt, ARTIFACT_DIR, default_artifact_path
from . import domain_expert

__all__ = [
    "build_prompt",
    "ARTIFACT_DIR",
    "default_artifact_path",
    "domain_expert",
]
