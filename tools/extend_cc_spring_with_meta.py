"""Extend cc-spring (created-ebd82a5fdec6) with the 6 meta exercises +
fix the malformed exercise_slugs the Creator emitted on first gen.

Per user directive 2026-04-28: "All meta exercises are crucial to build
claude code understanding support. Create a new model for all of them
if required. But implement all of them, directly is okay."

Two operations:

(1) FIX malformed exercise_slugs on existing hands_on steps. The Creator
    invented elaborate slugs that don't match real branches:
      05/concurrency-race-fix (archetype name)        → 05/investigate-vague-symptom (real branch)
      07/migrate-error-responses-to-spring-boot-3-3-problemdetail → 07/migration
      08/anti-exercise-when-not-to-use-claude         → 08/when-not-to-use-claude
      09/workflow-warmup-toyfix (no real branch)      → DROP step
                                                         (it was a capstone warmup
                                                         the LLM invented; the real
                                                         exercise/09 is confident-but-wrong
                                                         which is in M4.S5 already)

(2) ADD a new module "M6 — Claude Code Mastery: Meta-skills" with 6
    hands_on steps pointing at meta/01..06 with kind=meta:
      - meta/01-build-claude-md       (archetype: claude-md-authoring)
      - meta/02-hooks-and-commands    (archetype: hooks-wiring + slash-command-authoring combined)
      - meta/03-custom-subagent       (archetype: subagent-authoring)
      - meta/04-open-ended-feature    (archetype: feature-implement-from-spec applied to AI workflow)
      - meta/05-mcp-servers           (archetype: mcp-wiring-and-consume)
      - meta/06-prompting-tactics     (archetype: workflow-tour applied to prompting craft)

Usage:
    set -a && source .env && set +a
    python -m tools.extend_cc_spring_with_meta [--course-id ...] [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# Slug normalization — Creator-emitted slug → real inspiration-repo branch slug
SLUG_FIXES: dict[tuple[str, str], str] = {
    ("05", "concurrency-race-fix"):                                   "investigate-vague-symptom",
    ("07", "migrate-error-responses-to-spring-boot-3-3-problemdetail"): "migration",
    ("08", "anti-exercise-when-not-to-use-claude"):                   "when-not-to-use-claude",
}

# Steps to DROP (the LLM invented exercises that don't exist)
DROP_STEP_KEYS: set[tuple[str, str]] = {
    ("09", "workflow-warmup-toyfix"),  # not a real branch; redundant with capstone
}

# Meta exercises to ADD as a new module. Each entry produces ONE hands_on step.
META_EXERCISES = [
    {
        "nn": "01",
        "slug": "build-claude-md",
        "title": "Author CLAUDE.md from scratch — give Claude its operating manual",
        "archetype": "claude-md-authoring",
        "slide_html": (
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            "<h3 style='margin:0 0 6px 0;'>Why CLAUDE.md is load-bearing</h3>"
            "<p style='margin:0;color:#c9d1df;'>Claude Code reads CLAUDE.md on every session start. A good CLAUDE.md compresses your team's conventions, stack, file layout, and review rules into ~50-150 lines so Claude follows them WITHOUT being prompted. A missing or vague CLAUDE.md = Claude making safe-but-wrong defaults (e.g. <code>@Autowired</code> field injection when your team uses constructor injection).</p></div>"
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
            "<h3 style='margin:0 0 6px 0;'>What you'll do</h3>"
            "<p style='margin:0;color:#c9d1df;'>You'll write CLAUDE.md for the TaskManager repo so Claude reaches for Spring conventions automatically: constructor injection, <code>@Valid</code> on DTOs, <code>@Transactional</code> on services, <code>GlobalExceptionHandler</code> for errors, RFC 7807 ProblemDetail for API errors. The hidden grader asserts your CLAUDE.md is structurally sound (≥6 H2 sections, package name referenced, conventions encoded).</p></div>"
        ),
    },
    {
        "nn": "02",
        "slug": "hooks-and-commands",
        "title": "Wire hooks + slash commands — automate Claude's discipline",
        "archetype": "hooks-wiring",
        "slide_html": (
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            "<h3 style='margin:0 0 6px 0;'>Hooks + slash commands = team-shaped Claude</h3>"
            "<p style='margin:0;color:#c9d1df;'>Hooks fire on Claude's tool calls — auto-format on every <code>Edit</code>, run tests on every save, block writes to <code>application-prod.properties</code>. Slash commands package reusable prompts as <code>/controller-review</code> with <code>$ARGUMENTS</code>. Both are stored in <code>.claude/</code> at the repo root, so the team's discipline travels with the codebase.</p></div>"
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
            "<h3 style='margin:0 0 6px 0;'>What you'll wire</h3>"
            "<p style='margin:0;color:#c9d1df;'>Three hooks (PreToolUse blocker, PreToolUse spotless, PostToolUse mvnw test) + one slash command. Hidden grader parses <code>.claude/settings.json</code> for the right matcher patterns + verifies the slash command file shape.</p></div>"
        ),
    },
    {
        "nn": "03",
        "slug": "custom-subagent",
        "title": "Build a custom subagent — Claude that knows YOUR conventions",
        "archetype": "subagent-authoring",
        "slide_html": (
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            "<h3 style='margin:0 0 6px 0;'>Why subagents beat one-shot prompts</h3>"
            "<p style='margin:0;color:#c9d1df;'>A custom subagent (<code>.claude/agents/&lt;name&gt;.md</code>) packages a system prompt + tool whitelist + system instructions specific to one task. Instead of remembering to say \"use MockitoExtension, jakarta imports, constructor injection\" every time, you delegate to <code>@mockito-test-writer</code> and the subagent enforces your team's modern Mockito conventions automatically.</p></div>"
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
            "<h3 style='margin:0 0 6px 0;'>What you'll build</h3>"
            "<p style='margin:0;color:#c9d1df;'>A <code>mockito-test-writer</code> subagent that produces JUnit 5 + MockitoExtension tests with jakarta imports. Hidden grader parses YAML frontmatter + body to assert your subagent encodes the right conventions.</p></div>"
        ),
    },
    {
        "nn": "04",
        "slug": "open-ended-feature",
        "title": "Open-ended feature implementation — Claude as a senior pair programmer",
        "archetype": "feature-implement-from-spec",
        "slide_html": (
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            "<h3 style='margin:0 0 6px 0;'>From scoped exercise → real product work</h3>"
            "<p style='margin:0;color:#c9d1df;'>Earlier exercises had crisp specs + hidden tests. Real product work doesn't. This exercise gives you an open-ended feature request (\"add tag-based task filtering\") and you do the full senior-engineer flow with Claude: clarify → plan → implement → test → review. The hidden grader checks BEHAVIOR (the feature works) without telling you the exact API shape — your call.</p></div>"
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
            "<h3 style='margin:0 0 6px 0;'>What you'll practice</h3>"
            "<p style='margin:0;color:#c9d1df;'>Plan mode + Explore agent + iterative test-driven implementation. The grader asserts feature behavior, NOT specific code shape. Push back on Claude when its proposal doesn't match what your team would actually build.</p></div>"
        ),
    },
    {
        "nn": "05",
        "slug": "mcp-servers",
        "title": "Wire an MCP server — Claude with custom data sources",
        "archetype": "mcp-wiring-and-consume",
        "slide_html": (
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            "<h3 style='margin:0 0 6px 0;'>MCP = Claude + your tools</h3>"
            "<p style='margin:0;color:#c9d1df;'>The Model Context Protocol lets Claude talk to your team's tools — ticket trackers, internal APIs, databases — via tool-use. You configure once in <code>~/.claude.json</code> or <code>.mcp.json</code>, and Claude picks up the new tools on session start. <code>claude mcp list</code> verifies the wiring.</p></div>"
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
            "<h3 style='margin:0 0 6px 0;'>What you'll wire</h3>"
            "<p style='margin:0;color:#c9d1df;'>The <code>team-tickets</code> MCP server (provided as a stdio transport). After registration, you'll have Claude pick the next ticket tagged <code>payments-api</code> using the MCP's <code>list_recent_tickets</code> tool. Hidden grader runs <code>claude mcp list --json</code> and asserts the connection.</p></div>"
        ),
    },
    {
        "nn": "06",
        "slug": "prompting-tactics",
        "title": "Prompting tactics — get Claude to do its best work",
        "archetype": "workflow-tour",
        "slide_html": (
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            "<h3 style='margin:0 0 6px 0;'>Prompts as a craft, not a chore</h3>"
            "<p style='margin:0;color:#c9d1df;'>Same model, same code, different prompt → wildly different output quality. The tactics that move the needle: chain-of-thought (\"walk me through your reasoning\"), constraint specification (\"do NOT use field injection\"), example-driven (\"like the existing OrderService.java but for Tasks\"), self-critique (\"now review your own change for X\"), plan-mode-first.</p></div>"
            "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
            "<h3 style='margin:0 0 6px 0;'>What you'll practice</h3>"
            "<p style='margin:0;color:#c9d1df;'>The full prompting tactics palette applied to one feature. Hidden grader checks the artifact you produce; the journey to producing it is in your prompt log (which the grader reads + scores).</p></div>"
        ),
    },
]

META_MODULE_TITLE = "M5 — Claude Code Mastery: Meta-skills"
META_MODULE_DESCRIPTION = (
    "The 6 meta-skills that turn Claude Code from a smart autocomplete into a "
    "team-aware pair programmer: writing CLAUDE.md, wiring hooks + slash commands, "
    "building custom subagents, doing open-ended feature work, configuring MCP "
    "servers, and the prompting tactics that move the needle. Each step is a "
    "real exercise on the cc-spring TaskManager repo — slide explains the "
    "concept, you do the work in your editor, hidden grader attests."
)


META_INTRO_SLIDE_CONTENT = (
    "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
    "<h3 style='margin:0 0 6px 0;'>From \"using Claude\" → \"shaping Claude\"</h3>"
    "<p style='margin:0;color:#c9d1df;'>The first 4 modules taught you to use Claude Code on real bugs and features. This module teaches the META-LAYER: how to configure Claude itself so it follows YOUR team's conventions automatically. Six exercises, each a self-contained drill on the same TaskManager codebase. Together they're the difference between Claude as a generic AI helper and Claude as a team-aware pair programmer.</p></div>"
    "<div style='background:#1e2538;color:#e8ecf4;border:1px solid #2a3352;border-radius:8px;padding:14px 18px;'>"
    "<h3 style='margin:0 0 6px 0;'>The 6 meta-skills</h3>"
    "<ul style='margin:0;padding-left:24px;color:#c9d1df;'>"
    "<li><strong>CLAUDE.md authoring</strong> — Claude's operating manual for this repo</li>"
    "<li><strong>Hooks + slash commands</strong> — automate discipline (auto-format, test, block writes)</li>"
    "<li><strong>Custom subagents</strong> — package conventions as a delegate</li>"
    "<li><strong>Open-ended features</strong> — Claude as a senior pair programmer on real product work</li>"
    "<li><strong>MCP servers</strong> — Claude with your team's tools (tickets, APIs, DBs)</li>"
    "<li><strong>Prompting tactics</strong> — chain-of-thought, constraint specification, plan mode, self-critique</li>"
    "</ul></div>"
)


async def fix_slugs_and_add_meta_module(
    course_id: str,
    *,
    target_slug: str,
    dry_run: bool = False,
) -> dict:
    from sqlalchemy import select, func
    from backend.database import async_session_factory, Step, Module, Course

    fixed_slugs = 0
    dropped_steps = 0
    added_steps = 0
    new_module_id: int | None = None

    async with async_session_factory() as db:
        course = await db.get(Course, course_id)
        if not course:
            raise SystemExit(f"course_id={course_id} not found")
        log.info("course %s asset_slug=%s", course_id, course.asset_slug)

        # ── (1) Fix malformed exercise_slugs ──
        q = (
            select(Step)
            .join(Module, Module.id == Step.module_id)
            .where(Module.course_id == course_id)
            .where(Step.exercise_type == "hands_on")
            .order_by(Module.position, Step.position)
        )
        hands_on_steps = (await db.execute(q)).scalars().all()
        log.info("hands_on steps: %d", len(hands_on_steps))

        for step in list(hands_on_steps):
            dd = dict(step.demo_data or {})
            if not isinstance(dd, dict):
                continue
            cur_nn = str(dd.get("exercise_nn", "")).zfill(2)
            cur_slug = dd.get("exercise_slug")
            key = (cur_nn, str(cur_slug or ""))

            if key in SLUG_FIXES:
                new_slug = SLUG_FIXES[key]
                log.info("  fix slug step=%s %s/%s → %s/%s",
                         step.id, cur_nn, cur_slug, cur_nn, new_slug)
                if not dry_run:
                    dd["exercise_slug"] = new_slug
                    step.demo_data = dd
                fixed_slugs += 1
                continue

            if key in DROP_STEP_KEYS:
                log.info("  drop step=%s (%s/%s) — invented; not a real branch",
                         step.id, cur_nn, cur_slug)
                if not dry_run:
                    await db.delete(step)
                dropped_steps += 1
                continue

        # ── (2) Add the M5 meta module + intro slide + 6 hands_on steps ──
        # Determine the next module position for this course.
        max_pos = (await db.execute(
            select(func.max(Module.position)).where(Module.course_id == course_id)
        )).scalar() or 0
        new_mod_pos = max_pos + 1
        log.info("adding meta module at position %d", new_mod_pos)

        if not dry_run:
            new_module = Module(
                course_id=course_id,
                position=new_mod_pos,
                title=META_MODULE_TITLE,
                subtitle=META_MODULE_DESCRIPTION[:200],  # Module has subtitle, not description
                step_count=1 + len(META_EXERCISES),
            )
            db.add(new_module)
            await db.flush()  # populate new_module.id
            new_module_id = new_module.id
        else:
            new_module_id = -1  # placeholder

        # Intro concept slide (S1)
        if not dry_run:
            intro = Step(
                module_id=new_module_id,
                position=1,
                title="From using Claude → shaping Claude (the meta-skills)",
                exercise_type="concept",
                content=META_INTRO_SLIDE_CONTENT,
                demo_data=None,
                validation=None,
                code=None,
                expected_output=None,
            )
            db.add(intro)
            added_steps += 1

        # 6 meta hands_on steps (S2 .. S7)
        for i, ex in enumerate(META_EXERCISES, start=2):
            log.info("  add hands_on step S%d: meta/%s-%s", i, ex["nn"], ex["slug"])
            if not dry_run:
                step = Step(
                    module_id=new_module_id,
                    position=i,
                    title=ex["title"],
                    exercise_type="hands_on",
                    content=ex["slide_html"],
                    demo_data={
                        "course_slug": target_slug,
                        "exercise_nn": ex["nn"],
                        "exercise_slug": ex["slug"],
                        "exercise_kind": "meta",
                        "archetype": ex["archetype"],
                    },
                    validation={},
                    code=None,
                    expected_output=None,
                )
                db.add(step)
            added_steps += 1

        if not dry_run:
            await db.commit()
            log.info("Committed.")

    return {
        "course_id": course_id,
        "fixed_slugs": fixed_slugs,
        "dropped_steps": dropped_steps,
        "added_meta_module_id": new_module_id,
        "added_steps": added_steps,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course-id", default="created-ebd82a5fdec6")
    ap.add_argument("--target-slug", default="cc-spring")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = asyncio.run(fix_slugs_and_add_meta_module(
        course_id=args.course_id,
        target_slug=args.target_slug,
        dry_run=args.dry_run,
    ))
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
