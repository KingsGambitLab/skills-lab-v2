# AIE v3 — Mid-career engineer re-walk (2026-04-24)

Course: `created-7fee8b78c742` — "AI-Augmented Engineering: Ship Production Features with Claude Code + API"

Scope: focused verification of the v3 claimed deltas vs v2 —
1. Switching-UX fields on every `terminal_exercise` (new M5 steps especially).
2. Six Claude-Code factual-accuracy fixes (M0.S1 auth, M4 MCP wiring, M5 subagent tool names, M5 hook contract, M5 settings.json layout).
3. M5.S1 conversion `code_exercise` → `terminal_exercise` (markdown-authoring shape).

## Environment constraint note

Preview browser failed to load `http://127.0.0.1:8001/` — `chrome-error://chromewebdata/` on every nav. The UI walkthrough was swapped for API-driven content inspection via the learner-facing endpoints (`GET /api/courses/{id}` + `GET /api/courses/{id}/modules/{mid}`), which serve the same sanitized payloads the frontend renders. This still honors the no-peek-at-`/raw` rule.

## v3 deltas — explicit check results

### (a) M0.S1 hint: any `claude auth`?
`terminal_exercise` — "Verify your toolchain on your own machine". Searched entire step payload (content + hint + demo_data + validation).
`'claude auth'` appears **0 times**. ✅ FIXED.

### (b) M4.S2 terminal instructions: `claude mcp add`?
`terminal_exercise` — "Ship a feature with the team-tickets MCP". `demo_data.instructions` includes:
```
$ claude mcp add team-tickets /path/to/aie-team-tickets-mcp/server.py --transport stdio
```
✅ FIXED.

### (c) M5.S1 paste-slot flow works?
Step is now `terminal_exercise` ✅ (conversion landed). BUT `demo_data.paste_slots` is `null`. No labeled slots; learner has nowhere to paste the subagent markdown they author. Fallback textarea still works (back-compat concat), but the advertised structured-paste-slot flow of v3 is not wired for this step. ❌ BROKEN.

## Six factual-accuracy fixes — verdict

| # | Fix | Status | Evidence |
|---|---|---|---|
| 1 | M0.S1 no `claude auth` | ✅ | Full-step grep, 0 occurrences. Hint references Docker Desktop only. |
| 2 | M4.S2 `claude mcp add` with `--transport stdio` | ✅ | Verbatim in instructions. |
| 3 | M5 subagent tool names capitalized | ✅ | `Read`/`Edit`/`Bash` present. Lowercase `read_file`/`write_file`/`bash_tool`/`edit_file` = 0. Rubric enforces "CAPITALIZED tool names". |
| 4 | M5 hook contract (stdin JSON, exit 2 blocks) | ⚠ partial | M5.S2 starter: "Exit code 2 = BLOCK ... Tool input is provided via STDIN as JSON". But M5.S3 solution encodes `PreToolUse` as a STRING PATH (`"~/.claude/security_hook.sh"`) — real contract is an array of `{matcher, hooks:[{type:"command",command:…}]}`. Contract documented correctly in one place, wired wrong in the other. |
| 5 | M5 settings.json layout | ⚠ partial | `mcpServers` correctly split into `~/.claude.json` (docstring says so, solution puts it there). `permissions`/`hooks` in `settings.json`. But the hooks SHAPE in the solution is wrong (see #4). |
| 6 | MCP transport `stdio` | ✅ | Present in M4.S2 and M5.S3. |

## Switching-UX audit — all 9 `terminal_exercise` steps

v3 promised ALL terminal_exercise steps including new M5 ones would have `paste_slots` + `bootstrap_command` + `dependencies` + `step_slug` + `step_task`.

| Step | paste_slots | bootstrap | deps | slug | task | Verdict |
|---|---|---|---|---|---|---|
| M0.S1 | ✗ | ✗ | ✗ | ✗ | ✗ | ❌ empty |
| M1.S1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ full |
| M2.S3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ full |
| M3.S2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ full |
| M4.S2 | ✗ | ✗ | ✗ | ✗ | ✗ | ❌ empty |
| M5.S3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ full |
| M5.S4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ full |
| M6.S1 (subagent) | ✗ | ✗ | ✗ | ✗ | ✗ | ❌ empty (the M5.S1 under test) |
| M6.S5 (ship .claude/) | ✓ | ✗ | ✗ | ✗ | ✗ | ⚠ partial (slots yes, rest no) |

4/9 terminal steps are missing the switching-UX primitives promised by v3. M0.S1 (preflight — BYO-key first-touch step) and M4.S2 (MCP capstone) are the most painful: these are exactly the steps where a learner most needs a bootstrap command + dependency check + clean paste slot to avoid losing their place.

## Summary block

Verdict: **⚠ CONDITIONAL**

Top 3 remaining issues:
1. **Switching-UX backfill is partial.** M0.S1, M4.S2, M6.S1 (the new "M5.S1") have ZERO of the 5 promised UX fields. Root cause likely: `course_asset_backfill.py` was run once but skips steps whose `step_slug` doesn't match the asset registry's expected slug set, and the new/old-label-mismatch (M5 vs M6 renumbering) made the matcher miss these three.
2. **M5.S1 paste-slot flow is the advertised v3 fix but doesn't exist on that step** (`paste_slots: null`). The rubric asks for a `.claude/agents/test-fixer.md` paste, the template would render a generic textarea. Works, but the labeled-slot UX upgrade is not applied.
3. **M5.S3 encodes `hooks.PreToolUse` as a string path** rather than the real array-of-matcher-object contract. Technically Claude Code will accept a string path in older builds, but the reference facts block describes the full contract and the course should match. Hook contract is documented correctly in M5.S2 comments but wired wrong in M5.S3's reference solution.

### Pass/stuck/partial tally (content audit)
- Factual fixes: 4 ✅ full + 2 ⚠ partial (hooks shape) = 6/6 addressed, 2 incomplete.
- Switching-UX: 4 ✅ full + 1 ⚠ partial + 4 ❌ empty out of 9.

### Recommendation
Re-run `backend/course_asset_backfill.py` for the 4 empty/partial terminal steps (M0.S1, M4.S2, M6.S1, M6.S5) after matching the step_slug registry to the actual step IDs. Narrow-scope regen M5.S3's solution to emit the array-of-matcher hooks shape. Both are small fixes, neither blocks learner value. Ship with followup ticket.
