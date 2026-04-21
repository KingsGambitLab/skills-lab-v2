"""Patch M3 steps 135 (ordering) and 136 (code_review) of UX Research course.

Step 135: ordering has validation.correct_order but no demo_data.items array
Step 136: code_review has demo_data.research_document/bugs_to_find in a non-standard shape
"""

import asyncio
from sqlalchemy import select
from backend.database import Step, async_session_factory


# Step 135: normalize ordering — provide demo_data.items[] with correct_position
STEP_135_DEMO_DATA = {
    "items": [
        {"id": "o1", "text": "Consolidate all research artifacts (interviews, surveys, observations) into a centralized repository", "correct_position": 1},
        {"id": "o2", "text": "Code qualitative data for behaviors, needs, goals, and pain points using affinity mapping", "correct_position": 2},
        {"id": "o3", "text": "Identify behavioral patterns and user segments through clustering analysis", "correct_position": 3},
        {"id": "o4", "text": "Create provisional persona hypotheses based on identified behavioral clusters", "correct_position": 4},
        {"id": "o5", "text": "Layer demographic and psychographic data onto behavioral segments", "correct_position": 5},
        {"id": "o6", "text": "Develop detailed persona narratives with goals, behaviors, and context", "correct_position": 6},
        {"id": "o7", "text": "Validate personas against holdout research data or additional user interviews", "correct_position": 7},
        {"id": "o8", "text": "Refine personas based on validation findings and stakeholder feedback", "correct_position": 8},
    ],
}

STEP_135_VALIDATION = {
    "correct_order": ["o1", "o2", "o3", "o4", "o5", "o6", "o7", "o8"],
}


# Step 136: normalize code_review — "code" is the research document, "bugs" are the planted flaws by line
STEP_136_DEMO_DATA = {
    "code": """Mobile Banking App Research Findings — Q3 2024

1. Summary of Research
2. We interviewed 12 users about their financial planning habits.
3. All users were existing customers, recruited via our in-app prompt.
4. Interviews lasted 30 minutes each.
5.
6. Key Finding #1: Users want automated investing
7. "One user said they wished the app would 'just invest for them.'"
8. Recommendation: Build a robo-advisor module for $2M+ Q4 investment.
9.
10. Key Finding #2: Users are confused by the transfer screen
11. Three participants hesitated on the transfer screen for 10+ seconds.
12. Recommendation: Redesign the entire app navigation system.
13.
14. Key Finding #3: Users need better notifications
15. When we asked "Do you wish the app had smarter notifications?" 11/12 said yes.
16. Recommendation: Implement AI-driven notification prioritization.
17.
18. Key Finding #4: Younger users want crypto features
19. The youngest participant (28yo) mentioned cryptocurrency briefly.
20. Recommendation: Add full crypto trading capabilities as the top priority.
""",
    "bugs": [
        {"line": 8, "description": "Extreme recommendation ($2M robo-advisor) based on ONE user's casual comment — insufficient evidence."},
        {"line": 12, "description": "Solution mismatch — redesigning entire navigation is disproportionate to 3 users hesitating on one screen."},
        {"line": 15, "description": "Leading question ('Do you wish the app had smarter notifications?') biases the answer. Not reliable evidence."},
        {"line": 19, "description": "Single-data-point generalization — one 28-year-old mentioning crypto doesn't justify any product decision."},
        {"line": 20, "description": "Extreme recommendation — 'top priority' for a feature supported by a single brief mention."},
    ],
}

STEP_136_VALIDATION = {
    "bug_lines": [8, 12, 15, 19, 20],
}


PATCHES = [
    (135, {"demo_data": STEP_135_DEMO_DATA, "validation": STEP_135_VALIDATION}),
    (136, {"demo_data": STEP_136_DEMO_DATA, "validation": STEP_136_VALIDATION}),
]


async def patch():
    async with async_session_factory() as db:
        for step_id, fields in PATCHES:
            result = await db.execute(select(Step).where(Step.id == step_id))
            step = result.scalars().first()
            if not step:
                print(f"Step {step_id} NOT FOUND")
                continue
            for k, v in fields.items():
                setattr(step, k, v)
            print(f"Patched step {step_id}: {step.title}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(patch())
