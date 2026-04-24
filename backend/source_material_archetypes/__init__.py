"""Source-material archetype library.

Reusable course-shape templates with {{slot}} substitution. A creator picks
an archetype + fills a small number of stack-specific slots; the archetype
renders as a full source_material spec ready to paste into `/api/creator/start`.

User directive (2026-04-24): "Aligned on A+B" — Option A = archetype library
(this module), Option B = LLM-drafting endpoint on top of the library.

See `registry.py` for the list of available archetypes + their slot contracts.
"""
from .registry import (
    Archetype,
    ArchetypeSlot,
    get_archetype,
    list_archetypes,
    materialize_archetype,
)

__all__ = [
    "Archetype",
    "ArchetypeSlot",
    "get_archetype",
    "list_archetypes",
    "materialize_archetype",
]
