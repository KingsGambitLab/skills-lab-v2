# MEMORY — design discussions to revisit

Park-bench notes that aren't ready to ship but shouldn't be forgotten.
Append-only; date entries; cross-link to related code/issues.

---

## 2026-04-27 — Org-grounded course customization

**Context**: User asked what documents an organization could upload to make Creator-generated courses ground in their stack, domain, and curriculum. Answer was YES, fully feasible today on the existing UI with 3 small structural adds.

### Three input axes that matter

| Axis | Best documents to upload | Why |
|---|---|---|
| **Tech stack + versions** | `pyproject.toml` / `package.json` / `pom.xml` / `Cargo.toml`; `Dockerfile`/`docker-compose.yml`; `.github/workflows/*.yml`; READMEs of 2-3 most-touched repos | Version pins ARE the grounding — deterministic, no LLM guessing |
| **Domain space** | 5-10 anonymized postmortems / RFCs / design docs; internal wiki exports (Confluence/Notion); sanitized PR descriptions; onboarding "first 90 days" handbook; service catalog | Captures the kinds of problems engineers face + names of systems to reference |
| **Module skeleton** | Curriculum / learning roadmap (1-pager, 4-7 modules); skill matrix / job ladder; existing internal training catalog | Structural shape of the course — what to teach in what order |

### What's already in place (works today, no changes needed)

- `/api/creator/upload` accepts PDF/DOCX/PPTX/TXT/MD; extracts text; feeds as `source_material`
- `_extract_canonical_entities()` pulls names/numbers/IDs from source; LLM is forbidden from inventing alternates
- 7 grounding rules in the per-step prompt ("don't invent names; quote source; don't rename frameworks")
- `_runtime_deps_brief(language)` injects pinned versions for the runner image
- Per-tool verified-facts blocks: `_claude_code_reference_facts`, `tech_schema_data.py`, `tech_docs/aider.md`
- Title-hint matching surfaces the right tool facts when course title mentions the tool

So: an org that uploads `pom.xml` + 5 postmortems + a 1-page outline TODAY gets a course where every exercise mentions their actual systems with their actual stack — at "good guess" quality, not deterministic.

### The 3 structural adds (1-2 days each, when we revisit)

1. **Org Profile schema** — accept tech stack + domain + module outline as STRUCTURED fields, not just blob source_material. Creator prompt has explicit slots ("the org's pinned stack: …", "the org's named systems: …", "the requested module outline: …") instead of "go find the relevant bits in this prose."

2. **Per-org KB** — extend the `tech_schema` pattern to `org_schema_data.py` keyed by `org_slug`. Holds:
   - allowlist (system names the LLM CAN reference)
   - forbidden_examples (e.g. "we don't use Stripe Connect")
   - drift regexes
   Plus `backend/org_facts/<org_slug>.md` for canonical doc text.

3. **Module-skeleton hard contract at outline stage** — `_llm_refined_outline` validates that the generated outline matches the requested module count + scope. Today it's a soft suggestion; we'd make it a HARD reject-and-retry if the outline drifts from what was requested.

### Knowledge base evolution model (already proven)

Same pattern we use for Claude Code + Aider:
- Canonical doc text in `backend/tech_docs/<tool>.md`
- Allowlist + forbidden_examples in `backend/tech_schema_data.py`
- Refresh job: re-extract from official docs, diff, human-in-the-loop merge

For per-org KB: same shape, keyed by org_slug. Refresh job re-ingests their wiki on a cadence. New facts diff against current KB before merge.

### UI implication

**No UI changes** for this. The existing `/api/creator/start` flow accepts the structured fields as additional optional inputs. The wizard upload step gets one extra section ("Upload your org profile") with file slots. Creator API knows how to consume them. Same render, same generate flow, same dashboard.

### Open questions when we revisit

- How does an org REGISTER itself + claim a slug? (today there's no org concept; courses are owned by `creator_user_id`)
- Multi-tenancy: does each org get its own tag-filtered catalog view, or do all courses live in one global pool?
- Privacy/compliance: org's uploaded docs probably contain proprietary info → at-rest encryption, retention policy, who-can-read access controls
- Revenue model: per-seat? per-course-generated? unlimited under contract?

### Code references for next session

- `backend/main.py:_extract_canonical_entities` — entity pull
- `backend/main.py:_runtime_deps_brief` — pattern for stack injection
- `backend/main.py:_claude_code_reference_facts` — pattern for tool facts
- `backend/tech_schema_data.py` — registry pattern to mirror for org KB
- `backend/main.py:_llm_refined_outline` — where outline contract would tighten
- `frontend/index.html` — wizard upload step (no changes; just one new section)

---
