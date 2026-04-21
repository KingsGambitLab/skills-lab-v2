"""Seed a dedicated course showcasing adaptive_roleplay exercise type.

Creates 'Negotiation with an Adaptive VP' — a 2-module course where the
capstone is a live AI-driven negotiation with hidden state (patience / trust / flexibility).
"""
import asyncio
from sqlalchemy import select
from backend.database import Course, Module, Step, async_session_factory


COURSE_ID = "roleplay-negotiation-vp"

COURSE_DATA = {
    "id": COURSE_ID,
    "title": "Live Negotiation: Defending Scope Under Pressure",
    "subtitle": "Adaptive-roleplay training — the VP argues back",
    "description": "Practice negotiation with an AI VP that has hidden state (patience, trust, flexibility). The VP's tone and position shift based on your actual words — not multiple-choice picks. Score on state trajectory, not final answer.",
    "course_type": "case_study",
    "level": "Intermediate",
    "estimated_time": "45 min",
    "module_count": 2,
    "tags": ["negotiation", "leadership", "roleplay", "soft-skills"],
    "icon": "💼",
}

MODULE_1 = {
    "position": 1,
    "title": "Negotiation Foundations",
    "estimated_time": "20 min",
    "objectives": [
        "Identify BATNA and anchoring in your own proposals",
        "Recognize when data reframes a deadline conversation",
        "Practice keeping emotional temperature low under pressure",
    ],
    "step_count": 3,
    "steps": [
        {
            "position": 1,
            "title": "Why Most Tech Leads Lose Scope Negotiations",
            "step_type": "concept",
            "exercise_type": None,
            "content": """<h2>The 3 Failure Modes</h2>
<p>Most senior engineers and tech leads lose scope arguments with executives not because they're wrong on the merits — but because they break one of three rules:</p>
<ol>
  <li><strong>They concede too fast.</strong> The VP says "it has to ship by Q2" and they start negotiating internally about how to make it fit. Opening move signals weakness.</li>
  <li><strong>They argue with emotion, not data.</strong> "The team is burnt out" is true but unanchored. "Our burn-down shows a 14-week minimum with current velocity and 3 unresolved dependencies" is unarguable.</li>
  <li><strong>They never explore BATNA.</strong> What if you don't ship on time? The VP doesn't want to answer — but your job is to make them sit with the question.</li>
</ol>
<h3>The skill you'll practice next</h3>
<p>In the capstone, you'll face a VP in real-time text chat. No multiple-choice. The VP has hidden patience/trust/flexibility meters that move based on your actual words. You have 15 turns. Win condition: the VP either concedes (flexibility ≥ 7, trust ≥ 6) or walks away (patience hits 0, they escalate to CEO).</p>
""",
        },
        {
            "position": 2,
            "title": "Categorize the Moves",
            "step_type": "exercise",
            "exercise_type": "categorization",
            "content": """<p>Each of these negotiation moves fits into one of three buckets: <strong>Anchoring</strong> (claim value), <strong>Collaborative reframe</strong> (grow the pie), or <strong>Concession</strong> (give value away). Sort them.</p>""",
            "demo_data": {
                "categories": ["Anchoring", "Collaborative reframe", "Concession"],
                "items": [
                    {"id": "m1", "text": "Here's our burn-down — 14 weeks minimum", "correct_category": "Anchoring"},
                    {"id": "m2", "text": "What if we cut scope by 30% and ship on time?", "correct_category": "Collaborative reframe"},
                    {"id": "m3", "text": "OK, we'll see what we can do", "correct_category": "Concession"},
                    {"id": "m4", "text": "What's the business cost of a 4-week slip vs. shipping broken?", "correct_category": "Collaborative reframe"},
                    {"id": "m5", "text": "Fine, we'll skip the code review step", "correct_category": "Concession"},
                    {"id": "m6", "text": "Our error budget is already at 80% — shipping unfinished burns it", "correct_category": "Anchoring"},
                ],
            },
            "validation": {"correct_mapping": {"m1": "Anchoring", "m2": "Collaborative reframe", "m3": "Concession", "m4": "Collaborative reframe", "m5": "Concession", "m6": "Anchoring"}},
        },
        {
            "position": 3,
            "title": "The Stakes",
            "step_type": "concept",
            "exercise_type": None,
            "content": """<h2>What the VP wants</h2>
<p>You are about to negotiate with Diana, VP of Engineering. She has a competing commitment to the CEO that the payments platform migration ships by end of Q2. She is under pressure. If you push back, she will push back harder. If you capitulate, she will push you further.</p>
<p><strong>Your internal view:</strong> Current velocity + unresolved vendor dependencies put the minimum at 14 weeks. Q2 ends in 10 weeks.</p>
<p><strong>Diana's known public position:</strong> "Make it work."</p>
<p><strong>Her hidden state (you won't see this):</strong> She is actually open to a phased rollout if you propose one credibly. But she will not initiate it. She also has a limit — if you are disrespectful or stall without offering alternatives, she will escalate to the CEO and you will lose credibility.</p>
<p>Next step: live roleplay. Your words matter.</p>
""",
        },
    ],
}

MODULE_2 = {
    "position": 2,
    "title": "Live Negotiation Capstone",
    "estimated_time": "25 min",
    "objectives": [
        "Hold position under active pushback",
        "Use data and BATNA to move a stuck stakeholder",
        "Propose a phased rollout without conceding the deadline",
    ],
    "step_count": 1,
    "steps": [
        {
            "position": 1,
            "title": "Negotiate with Diana (VP Eng)",
            "step_type": "exercise",
            "exercise_type": "adaptive_roleplay",
            "content": """<p>Diana has just finished the leadership all-hands. She DMs you: "Team, I need a date. End of Q2, payments live. Can you commit or do we need to change ownership?"</p>
<p>You have up to 15 turns. Your goal: get Diana to agree to a phased rollout (or at least to a realistic timeline) without damaging the relationship. Starting state: she is at Patience 7/10, Trust 5/10, Flexibility 4/10.</p>""",
            "demo_data": {
                "scenario_prompt": "Diana, VP of Engineering, is demanding the payments platform migration ship by end of Q2. You believe it needs 14 weeks (Q2 ends in 10). You must either convince her to accept a realistic timeline or a phased rollout, without capitulating or escalating.",
                "turn_limit": 15,
                "counterparty": {
                    "persona_name": "Diana (VP Engineering)",
                    "opening_message": "Team, I need a date. End of Q2, payments live. Can you commit or do we need to change ownership?",
                    "persona_system_prompt": (
                        "You are Diana, VP of Engineering at a mid-size fintech. You are direct, data-driven, under "
                        "pressure from the CEO who has promised the board this migration by end of Q2. "
                        "You respect engineers who bring data, push back constructively, and offer alternatives. "
                        "You have low patience for vague 'we'll try' answers or emotional appeals. "
                        "You will concede to a phased rollout if the engineer proposes one with credible data. "
                        "You will NOT concede the principle that there must be a firm date. "
                        "Keep replies to 2-4 short paragraphs. Be human."
                    ),
                    "hidden_state": {"patience": 7, "trust": 5, "flexibility": 4},
                    "state_update_rules": (
                        "After each learner turn, adjust state: "
                        "(a) If learner brings specific numbers/data → trust +1, flexibility +1. "
                        "(b) If learner proposes a concrete alternative (phased rollout, reduced scope, parallel workstream) → flexibility +2. "
                        "(c) If learner is vague, emotional, or hedges ('we'll see', 'try our best', 'team is burnt out') → patience -1, trust -1. "
                        "(d) If learner is rude, sarcastic, or blame-shifts → patience -2, trust -2. "
                        "(e) If learner offers a phased rollout with specific milestones → flexibility +3 (potential concede). "
                        "(f) If learner capitulates and commits to the impossible date → trust -2 (you now know they'll overpromise). "
                        "Clamp all values to [0, 10]."
                    ),
                    "escalation_triggers": [
                        {"condition": "patience<=0", "action": "escalate"},
                        {"condition": "trust<=1", "action": "walk_away"},
                    ],
                    "win_conditions": [
                        {"condition": "flexibility>=8 and trust>=6", "outcome": "concede"},
                    ],
                },
                "debrief": {
                    "show_state_trajectory": True,
                    "rubric_tags": ["anchoring", "data_use", "emotional_regulation", "BATNA", "collaborative_reframe"],
                },
            },
            "validation": {"llm_judged": True},
        },
    ],
}


async def seed():
    async with async_session_factory() as db:
        # Delete existing if present
        existing = await db.execute(select(Course).where(Course.id == COURSE_ID))
        prior = existing.scalars().first()
        if prior:
            await db.delete(prior)
            await db.flush()

        course = Course(
            id=COURSE_DATA["id"],
            title=COURSE_DATA["title"],
            subtitle=COURSE_DATA["subtitle"],
            description=COURSE_DATA["description"],
            course_type=COURSE_DATA["course_type"],
            level=COURSE_DATA["level"],
            tags=COURSE_DATA["tags"],
            estimated_time=COURSE_DATA["estimated_time"],
            module_count=COURSE_DATA["module_count"],
            icon=COURSE_DATA["icon"],
        )
        db.add(course)
        await db.flush()

        for m_data in (MODULE_1, MODULE_2):
            module = Module(
                course_id=COURSE_ID,
                position=m_data["position"],
                title=m_data["title"],
                objectives=m_data.get("objectives", []),
                estimated_time=m_data.get("estimated_time"),
                step_count=m_data.get("step_count"),
            )
            db.add(module)
            await db.flush()
            for s_data in m_data["steps"]:
                step = Step(
                    module_id=module.id,
                    position=s_data["position"],
                    title=s_data["title"],
                    step_type=s_data["step_type"],
                    exercise_type=s_data.get("exercise_type"),
                    content=s_data.get("content"),
                    code=s_data.get("code"),
                    expected_output=s_data.get("expected_output"),
                    validation=s_data.get("validation"),
                    demo_data=s_data.get("demo_data"),
                )
                db.add(step)
        await db.commit()
        print(f"Seeded course: {COURSE_ID}")


if __name__ == "__main__":
    asyncio.run(seed())
