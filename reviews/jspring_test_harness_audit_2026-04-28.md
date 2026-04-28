# jspring Course — Behavioral Test Harness Migration Plan (2026-04-28)

## Context

Per today's CLAUDE.md addition `🧪 BEHAVIORAL TEST HARNESS`, every code-shape
course step's grading should collapse to "test class fails on starter,
passes on canonical fix; LMS grades exit code 0". This audit walks all 13
jspring exercises and proposes the specific test-class upgrade per step.

Course: `created-e54e7d6f51cf` (jspring-course)
Repo: `tusharbisht/jspring-course-repo` (7 module branches + capstone)

## Tier classification

| Tier | Meaning | Steps |
|---|---|---|
| **A** | Real behavior assertion in test class (Hibernate Statistics, MockMvc, etc.) | 85115, 85121, 85136 |
| **B** | File-shape / structured-data assertion (YAML/JSON/MD parser, no regex) | 85124, 85125, 85128, 85131 |
| **C** | First-party exit code only (no test class needed) | 85112, 85135 |
| **D** | GHA workflow check (already objective) | 85137 |
| **E** | Pedagogy anti-pattern — needs redesign or deprecation | 85117, 85119, 85133 |

---

## Per-step migration recipe

### Tier A — Behavioral test class

#### 85115 (M2.S2) — Fix N+1 in OrderService.getRecentOrders (no CLAUDE.md)
**Current rubric**: tests pass + grep canonical pattern (already cleaned today).
**Hole**: `OrderServiceTest` is `assertTrue(true)` — tests pass even with N+1 in place.
**Upgrade**: replace test class with Hibernate `Statistics.getPrepareStatementCount()` assertion.
```java
@SpringBootTest
@Testcontainers
class OrderServiceTest {
    @Container static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource static void props(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", pg::getJdbcUrl);
        r.add("spring.datasource.username", pg::getUsername);
        r.add("spring.datasource.password", pg::getPassword);
    }

    @Autowired EntityManagerFactory emf;
    @Autowired OrderService orderService;
    @Autowired DataLoader dataLoader;   // seeds 100 orders × 3 items

    @BeforeEach void seed() { dataLoader.seed(100, 3); }

    @Test void getRecentOrders_atMostTwoQueries() {
        Statistics s = emf.unwrap(SessionFactory.class).getStatistics();
        s.setStatisticsEnabled(true);
        s.clear();
        List<Order> orders = orderService.getRecentOrders(100);
        assertThat(orders).hasSize(100);
        // 1 query for orders + 1 for items via JOIN FETCH = 2 max
        // N+1 would show 1 + 100 = 101
        assertThat(s.getPrepareStatementCount())
            .as("getRecentOrders should issue ≤ 2 queries (currently issues N+1)")
            .isLessThanOrEqualTo(2);
    }
}
```
**New cli_commands**: `[{ cmd: "./mvnw test -Dtest=OrderServiceTest", expect_exit_code: 0 }]`
**Migration cost**: 1 test file + DataLoader helper + DB seed fixture (~120 LOC).

#### 85121 (M3.S4) — Retry M1's N+1 fix WITH CLAUDE.md
**Current rubric**: regex-grades evidence of CLAUDE.md presence + git activity + BUILD SUCCESS.
**Hole**: same as 85115 — test class is decorative; rubric grades the journey ("Recent git activity").
**Upgrade**: SAME test class as 85115 (it's the same N+1 fix; CLAUDE.md is just authoring context).
**New cli_commands**: `[{ cmd: "test -f CLAUDE.md", expect_exit_code: 0 }, { cmd: "./mvnw test -Dtest=OrderServiceTest", expect_exit_code: 0 }]`
**Migration cost**: 0 (reuses 85115's test class on the same OR a fresh starter branch).

#### 85136 (M7.S3) — Implement OrdersController + OrdersControllerTest
**Current rubric**: 6 must_contain regex (`@RestController`, `@Valid`, `Idempotency-Key`, etc.).
**Hole**: regex-on-source-code; learner can pass by sprinkling annotations without correct behavior.
**Upgrade**: `OrdersControllerIntegrationTest` with `@WebMvcTest` + MockMvc:
```java
@WebMvcTest(OrdersController.class)
class OrdersControllerIntegrationTest {
    @Autowired MockMvc mvc;

    @Test void post_orders_validation_400_on_missing_field() throws Exception {
        mvc.perform(post("/orders").contentType(APPLICATION_JSON).content("{}"))
           .andExpect(status().isBadRequest())
           .andExpect(jsonPath("$.errors").exists());
    }

    @Test void post_orders_idempotency_key_returns_same_response() throws Exception {
        String key = "ABC-123";
        String body = "{\"customerId\":1,\"items\":[{\"sku\":\"X\",\"qty\":1}]}";
        MvcResult first = mvc.perform(post("/orders").header("Idempotency-Key", key)
                .contentType(APPLICATION_JSON).content(body))
            .andExpect(status().isCreated()).andReturn();
        MvcResult second = mvc.perform(post("/orders").header("Idempotency-Key", key)
                .contentType(APPLICATION_JSON).content(body))
            .andExpect(status().isCreated()).andReturn();
        assertThat(first.getResponse().getContentAsString())
            .isEqualTo(second.getResponse().getContentAsString());
    }

    @Test void post_orders_201_on_happy_path() throws Exception { /* ... */ }
}
```
**New cli_commands**: `[{ cmd: "./mvnw test -Dtest=OrdersControllerIntegrationTest", expect_exit_code: 0 }]`
**Migration cost**: 1 test file (~80 LOC); already a course-repo file, just needs proper assertions.

---

### Tier B — Structured-data assertion (no regex)

#### 85124 (M4.S2) — Write /controller-review slash command
**Current rubric**: regex `$ARGUMENTS`, `@Valid`, `jakarta`, `security` in captured output.
**Hole**: regex on a markdown file's content; learner can satisfy by copy-pasting the words.
**Upgrade**: tiny verifier script `tools/verify_slash_command.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
F=.claude/commands/controller-review.md
[ -f "$F" ] || { echo "MISSING: $F"; exit 1; }
grep -q '\$ARGUMENTS' "$F" || { echo "missing \$ARGUMENTS placeholder"; exit 1; }
# Must have ≥4 H2 sections (audit areas)
H2_COUNT=$(grep -c '^## ' "$F")
[ "$H2_COUNT" -ge 4 ] || { echo "expected ≥4 audit sections (## headers); found $H2_COUNT"; exit 1; }
echo "OK: $F has \$ARGUMENTS + $H2_COUNT audit sections"
```
**New cli_commands**: `[{ cmd: "bash tools/verify_slash_command.sh", expect_exit_code: 0 }]`
**Migration cost**: 1 verify script (10 LOC); ship it in the `.starter` branch.

#### 85125 (M4.S3) — Build mockito-test-writer subagent
**Current rubric**: regex on YAML frontmatter keys.
**Hole**: substring match on `name:`/`description:`/`tools:`; learner can satisfy with junk values.
**Upgrade**: `tools/verify_subagent.sh` parses YAML with `yq` (or python+pyyaml):
```bash
#!/usr/bin/env bash
F=.claude/agents/mockito-test-writer.md
yq '.name, .description, .tools, .model' "$F" > /tmp/fields
# Each field must be non-empty
[ "$(yq '.name | length' "$F")" -gt 0 ] || exit 1
[ "$(yq '.description | length' "$F")" -gt 20 ] || exit 1
# Body must mention the modern testing stack
sed -n '/^---$/,/^---$/!p' "$F" | grep -qE 'MockitoExtension' || exit 1
sed -n '/^---$/,/^---$/!p' "$F" | grep -qE 'jakarta' || exit 1
echo "OK: subagent has frontmatter + modern stack references"
```
**New cli_commands**: `[{ cmd: "bash tools/verify_subagent.sh", expect_exit_code: 0 }]`
**Migration cost**: 1 verify script + maybe install `yq` in dev container (or `python3 -c "import yaml..."`).

#### 85128 (M5.S2) — Wire 3 hooks in .claude/settings.json
**Current rubric**: regex on file contents.
**Hole**: same as 85125 — substring match.
**Upgrade**: `tools/verify_hooks.py` parses JSON + asserts hook shape:
```python
import json, sys, pathlib
s = json.loads(pathlib.Path('.claude/settings.json').read_text())
hooks = s.get('hooks', {})
pre = hooks.get('PreToolUse', [])
post = hooks.get('PostToolUse', [])
assert any('application-prod.properties' in str(h.get('matcher','')) for h in pre), "no prod-properties blocker"
assert any('Edit' in h.get('matcher','') and 'spotless:apply' in json.dumps(h) for h in pre), "no spotless auto-fmt"
assert any('Edit' in h.get('matcher','') and 'mvnw test' in json.dumps(h) for h in post), "no test runner"
print("OK: 3 hooks wired correctly")
```
**New cli_commands**: `[{ cmd: "python3 tools/verify_hooks.py", expect_exit_code: 0 }]`
**Migration cost**: 1 verify script (15 LOC).

#### 85131 (M6.S2) — Wire team-tickets MCP
**Current rubric**: regex on captured `claude mcp list` output.
**Upgrade**: `claude mcp list --json | jq` for structured assertion:
```bash
claude mcp list --json | jq -e '.mcpServers["team-tickets"].connected == true' > /dev/null
# Or check tools[] non-empty
claude mcp list --json | jq -e '.mcpServers["team-tickets"].tools | length >= 1' > /dev/null
```
**New cli_commands**: `[{ cmd: "claude mcp list --json | jq -e '.mcpServers[\"team-tickets\"].tools | length >= 1'", expect_exit_code: 0 }]`
**Migration cost**: 0; just changes the cli_command.
**Caveat**: Verify `claude mcp list` supports `--json`. If not, we still parse the prose output via Python instead of regex.

---

### Tier C — First-party exit codes (no test class)

#### 85112 (M1.S2) — Preflight: claude/java/maven version checks
**Current rubric**: regex `claude`, `java`, `maven` in version output.
**Upgrade**: just exit codes — every `--version` exits 0 iff installed:
```yaml
cli_commands:
  - cmd: "claude --version"
    expect_exit_code: 0
  - cmd: "java -version"
    expect_exit_code: 0
  - cmd: "./mvnw -v"
    expect_exit_code: 0
```
**Migration cost**: 0; just rubric simplification.

#### 85135 (M7.S2) — Fork and baseline
**Current rubric**: 4 regex checks (remote URL, branch name, BUILD SUCCESS, files exist).
**Upgrade**: gh-api for fork + `./mvnw test`:
```yaml
cli_commands:
  - cmd: 'gh api repos/$(git config user.username)/jspring-course-repo --jq .name'
    expect_exit_code: 0   # confirms fork exists
  - cmd: "./mvnw test"
    expect_exit_code: 0   # confirms baseline tests pass
```
**Migration cost**: 0; just changes cli_commands shape.

---

### Tier D — GHA workflow check (already objective)

#### 85137 (M7.S4) — Push branch + pass lab-grade.yml
**Current rubric**: empty (none).
**State**: this is a `system_build` with `gha_workflow_check` — already objective per F24.
**Action**: NONE. This step is the gold-standard shape; the others should converge toward it.

---

### Tier E — Anti-pattern, redesign or deprecate

#### 85117 (M2.S4) — Name 3 conventions you wish Claude had known
**Current rubric**: "150+ words" + Gap 1/2/3 headers in `claude-gaps-reflection.md`.
**Anti-pattern**: this IS the observation/reflection-prose anti-pattern §"Deprecate this type of judge from the evaluation ontology". Grading on free prose the learner wrote ABOUT the tool.
**Verdict**: **deprecate or redesign.** Two options:
  - **Option 1 (deprecate)**: drop the step. Module 2 already has 85115 (the actual fix); the reflection-step adds no behavior signal.
  - **Option 2 (redesign as concept-step)**: convert from `terminal_exercise` to `concept` (no grading), so the reflection happens but isn't graded on prose quality.
**Recommendation**: Option 2. Reflection has pedagogical value; grading prose on it is the disease.

#### 85119 (M3.S2) — Draft CLAUDE.md → Testcontainers
**Current rubric**: 50+ lines, 6 sections (Project Overview, Tech Stack, etc.), package-name reference.
**Anti-pattern**: shape-grading on a learner-written markdown file. Borderline — at least the "package name" check is grounded in the actual repo.
**Upgrade**: `tools/verify_claude_md.py` parses the MD, asserts ≥6 H2 sections by name, asserts package name appears (objective check on the repo's actual package). Then ALSO runs `claude` against a deterministic prompt and asserts the output references one of the conventions in CLAUDE.md (e.g. "respond with JUST the package name" → check output equals `com.skillslab.jspring`).
**Caveat**: claude is non-deterministic; the second step may flake. Could relax to "presence of CLAUDE.md with required structure" only.
**Recommendation**: Tier B-style structural verifier; skip the claude-behavior assertion until we have a deterministic eval harness.

#### 85133 (M6.S4) — Consume MCP: plan next ticket tagged payments-api
**Current rubric**: regex on captured Claude session ("MCP tool calls + synthesized recommendation").
**Anti-pattern**: grading a non-deterministic LLM call's output.
**Upgrade**: have the MCP server emit a **deterministic** signal that ONLY appears if the learner correctly invoked the right tool. E.g. `team-tickets-mcp` could log `TOOL_CALLED: list_recent_tickets at <timestamp>` to a file the verifier checks; learner's task = trigger the right MCP tool, not write good prose.
**Migration cost**: requires editing the team-tickets MCP server (separate repo). Defer to a separate sprint.

---

## Migration order (smallest unit first → ship + verify → repeat)

| Order | Step | Cost | Risk |
|---|---|---|---|
| 1 | **85112** preflight → exit codes only | trivial (rubric) | low |
| 2 | **85115** N+1 → Hibernate Statistics test | medium (1 test class + DataLoader + DB fixture) | medium — first test that requires Testcontainers |
| 3 | **85121** N+1 retry → reuse 85115 test class | trivial | low |
| 4 | **85124** slash command → verify script | trivial | low |
| 5 | **85125** subagent → verify script + yaml/yq | trivial | low |
| 6 | **85128** hooks → JSON parser script | trivial | low |
| 7 | **85131** MCP list → `claude mcp list --json` | trivial (depends on flag availability) | low |
| 8 | **85135** fork+baseline → gh-api + ./mvnw test | trivial | low |
| 9 | **85136** OrdersController → @WebMvcTest | medium (1 test class) | medium |
| 10 | **85117** reflection → concept step | trivial (exercise_type change) | low |
| 11 | **85119** CLAUDE.md → structured verifier | medium | medium |
| 12 | **85133** MCP consume → deferred (needs MCP-side change) | high | high |

After 1-9, the course is deterministic, no-regex, behavior-graded. 10-12 close the
remaining anti-pattern surface.

## Reusable artifacts to create in the course-repo

```
tools/
├── verify_slash_command.sh       # 85124
├── verify_subagent.sh            # 85125
├── verify_hooks.py               # 85128
├── verify_claude_md.py           # 85119
└── verify_module_invariants.sh   # CI: every starter branch's tests must FAIL; every solution branch's tests must PASS

src/test/java/com/skillslab/jspring/order/
├── OrderServiceTest.java         # rewrite with Hibernate Statistics (85115/85121)
└── OrdersControllerIntegrationTest.java  # rewrite with MockMvc (85136)

src/test/java/com/skillslab/jspring/test/
└── DataLoader.java               # seed fixtures for performance tests
```

## What to ship next session

If user greenlights, ship in order 1-9. Each is a small commit:
- (1) one-line rubric simplification (LMS regen)
- (2,3) test class + DataLoader + pom.xml verify (no new deps needed; all present)
- (4-8) verify scripts (~10-20 LOC each)
- (9) one MockMvc test class

Ship-as-you-win order means each commit is independently shippable + reversible.
