"""Track A + Track B validator — Opus's hybrid for the bug class.

For each LLM-emitted step candidate, runs:
  - Track B (closed-set facts): cross-check every literal in candidate
    against the course_assets registry. If LLM emitted a registry KEY
    where it should have emitted the registry VALUE → reject.
  - Track A (open-set facts):
    * Path-validity:  every path-shaped string in cli_commands must
      resolve via `gh api repos/X/Y/contents/<path>?ref=<branch>`.
    * Class-name:     every Java class name in cli_commands must exist
      in the actual repo's git tree.
    * GHA job:        validation.gha_workflow_check.grading_job must
      appear in the actual workflow file's `jobs:` keys.
    * CLI flag:       every flag in cli_commands must appear in
      verified_facts_data.py for the matching tool.

Returns ValidationResult(ok, reason). Used at:
  - Per-step regen (per_step.py:regenerate_single_step) — runs after
    LLM emits, before persist; reject + retry feedback on failure.
  - Course-gen pipeline (main.py:_llm_generate_step_content retry loop)
    — same shape, integrated as one of the gate steps.

Tested via tools/test_mutation_suite.py — initially 0/6, each track
build flips one or more tests green. When 6/6 the bug class is closed.
"""
from __future__ import annotations
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class ValidationResult:
    ok: bool
    reason: str = "ok"


# ── Helpers — extract validator-relevant strings from candidate ──


def _flatten_candidate_text(candidate: dict) -> str:
    """Concatenate every string-valued field in the candidate so simple
    substring checks (Track B) can scan the whole emission at once."""
    return json.dumps(candidate or {}, ensure_ascii=False)


def _extract_cli_command_strings(candidate: dict) -> list[str]:
    cmds: list[str] = []
    val = (candidate or {}).get("validation") or {}
    for c in val.get("cli_commands") or []:
        if isinstance(c, str):
            cmds.append(c)
        elif isinstance(c, dict):
            cmd = c.get("cmd") or c.get("command") or ""
            if cmd:
                cmds.append(str(cmd))
    return cmds


# Path-shaped: starts with src/ or app/ or backend/ etc. + has a slash;
# ends with a directory or a Java/Python/etc file extension. We DON'T
# match every regex with a slash — only directory-shaped paths.
_PATH_PATTERN = re.compile(
    r"\b(?:src|app|backend|frontend|lib|tests|test|docs?)/[a-zA-Z0-9._/-]+"
)
# Java class name: a CamelCase identifier referenced as a -Dtest= arg
# or appearing in a `class FooTest` style import. Conservative — only
# flags identifiers ending in Test / Tests / IntegrationTest / IT.
_JAVA_TEST_CLASS_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z0-9]*?(?:Test|Tests|IntegrationTest|IT))\b"
)
# CLI flag: -<single-letter> or --<word> at a word boundary.
_FLAG_PATTERN = re.compile(r"(?:^|\s)(-{1,2}[a-zA-Z][a-zA-Z0-9-]*)")


# ─────────────────────────────────────────────────────────────────────
# Track B — closed-set: registry-derivable facts
# ─────────────────────────────────────────────────────────────────────


def _track_b_check_branch_keys_not_used_as_values(
    candidate: dict, course_slug: str
) -> ValidationResult:
    """Bug class: LLM reads registry KEY (`first-fix`) and writes it
    in prose as if it were the branch value. Detect by scanning for
    any module_branches KEY appearing in `git checkout X` constructs.
    """
    try:
        from backend.course_assets import get_course_assets
    except Exception:
        return ValidationResult(True, "course_assets unavailable")
    asset = get_course_assets(course_slug)
    if not asset:
        return ValidationResult(True, "no asset registered")

    text = _flatten_candidate_text(candidate)
    keys = list(asset.module_branches.keys())  # e.g. ["preflight", "first-fix", ...]
    branch_values = set(asset.module_branches.values())  # e.g. {"module-0-preflight", ...}

    bad_keys_seen: list[str] = []
    for key in keys:
        # If the key happens to also be a real branch value (degenerate
        # registry), skip — can't distinguish.
        if key in branch_values:
            continue
        # Look for `checkout <key>` or `branch <key>` shapes — these are
        # places where ONLY a real branch name should appear.
        for ctx in (
            rf"\bcheckout\s+{re.escape(key)}\b",
            rf"\bbranch\s+{re.escape(key)}\b",
            rf"\borigin/{re.escape(key)}\b",
        ):
            if re.search(ctx, text):
                bad_keys_seen.append(key)
                break

    if bad_keys_seen:
        return ValidationResult(
            False,
            f"Track B: candidate uses registry KEY(s) {bad_keys_seen!r} as if they were branch names. "
            f"For {course_slug}, valid branch values are {sorted(branch_values)}. "
            f"Use `{{MODULE_BRANCH}}` token (substituted from registry) OR quote the real branch value verbatim.",
        )
    return ValidationResult(True)


# ─────────────────────────────────────────────────────────────────────
# Track A — open-set: repo-state-derivable facts
# ─────────────────────────────────────────────────────────────────────


def _gh_api_path_exists(repo: str, path: str, ref: str) -> tuple[bool, str | None]:
    """gh api contents check. Returns (exists, error_msg). Cheap HEAD
    via the contents endpoint. 404 → not exists; 200 → exists.

    Auth: reads GITHUB_TOKEN env var; falls back to unauthenticated
    (60 req/hr rate limit). Validator should be auth'd in prod.
    """
    import os
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    req = urllib.request.Request(url, method="GET")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "404"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"net error: {e}"


_TREE_CACHE: dict[tuple[str, str], list[str] | None] = {}


def _gh_api_repo_tree(repo: str, ref: str) -> list[str] | None:
    """Fetch the full recursive git-tree of <repo>@<ref>. Returns a list
    of file paths (e.g. `src/test/java/.../OrdersControllerIntegrationTest.java`)
    or None on error. Cached per (repo, ref) for the duration of the
    process so repeat calls are instant.

    Auth: reads GITHUB_TOKEN env var. Public repos work unauth'd up to
    60 req/hr (the tree endpoint counts as 1 call regardless of repo
    size — much more efficient than per-file contents calls).
    """
    import os
    cache_key = (repo, ref)
    if cache_key in _TREE_CACHE:
        return _TREE_CACHE[cache_key]
    url = f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            paths = [t.get("path", "") for t in data.get("tree", []) if t.get("type") == "blob"]
            _TREE_CACHE[cache_key] = paths
            return paths
    except urllib.error.HTTPError as e:
        # 401/403/404 — couldn't verify; cache as None so we don't retry
        _TREE_CACHE[cache_key] = None
        return None
    except Exception:
        _TREE_CACHE[cache_key] = None
        return None


def _track_a_check_paths_resolve(
    candidate: dict, course_slug: str, module_position: int
) -> ValidationResult:
    """Path-shape strings in cli_commands must resolve to real files in
    the course repo at the relevant module's branch."""
    try:
        from backend.course_assets import get_course_assets, module_key_for_position
    except Exception:
        return ValidationResult(True, "course_assets unavailable")
    asset = get_course_assets(course_slug)
    if not asset:
        return ValidationResult(True, "no asset registered")
    mod_key = module_key_for_position(course_slug, module_position)
    if not mod_key:
        return ValidationResult(True, "module position out of range")
    branch = asset.module_branches.get(mod_key)
    if not branch:
        return ValidationResult(True, "no branch for module")

    # Extract repo "owner/name" from the URL for gh api use.
    m = re.search(r"github\.com/([^/]+/[^/?#]+?)(?:\.git)?/?$", asset.course_repo)
    if not m:
        return ValidationResult(True, "course_repo not a parsable github URL")
    repo = m.group(1)

    cmds = _extract_cli_command_strings(candidate)
    bad_paths: list[str] = []
    for cmd in cmds:
        for path in _PATH_PATTERN.findall(cmd):
            # Trim trailing slash for the API call but report the original
            api_path = path.rstrip("/")
            exists, err = _gh_api_path_exists(repo, api_path, branch)
            if not exists and err == "404":
                bad_paths.append(f"{path} (404 on {repo}@{branch})")
    if bad_paths:
        return ValidationResult(
            False,
            f"Track A: cli_commands reference path(s) that don't exist on the actual "
            f"repo branch — {bad_paths}. Each path returned 404 from gh api contents.",
        )
    return ValidationResult(True)


def _track_a_check_gha_grading_job(
    candidate: dict, course_slug: str
) -> ValidationResult:
    """validation.gha_workflow_check.grading_job must appear as a `jobs:`
    key in the actual workflow file."""
    val = (candidate or {}).get("validation") or {}
    gha = val.get("gha_workflow_check")
    if not isinstance(gha, dict):
        return ValidationResult(True)
    job_name = gha.get("grading_job")
    if not job_name:
        return ValidationResult(True)
    repo = gha.get("repo_template")
    workflow_file = gha.get("workflow_file") or "lab-grade.yml"
    if not repo:
        return ValidationResult(True, "no repo_template; skip")

    # Fetch the workflow YAML from the capstone branch (last registered)
    try:
        from backend.course_assets import get_course_assets
    except Exception:
        return ValidationResult(True)
    asset = get_course_assets(course_slug)
    capstone_branch = None
    if asset:
        # Heuristic: last entry in module_branches is the capstone branch.
        keys = list(asset.module_branches.keys())
        if keys:
            capstone_branch = asset.module_branches[keys[-1]]
    if not capstone_branch:
        return ValidationResult(True)

    raw_url = f"https://raw.githubusercontent.com/{repo}/{capstone_branch}/.github/workflows/{workflow_file}"
    try:
        with urllib.request.urlopen(raw_url, timeout=10) as r:
            yaml_text = r.read().decode("utf-8", errors="replace")
    except Exception:
        # Soft-fail — couldn't fetch workflow; don't block
        return ValidationResult(True, f"couldn't fetch {raw_url}")

    # Parse out top-level `jobs:` keys via regex (avoid pyyaml dep). The
    # job names sit at 2-space indent under `jobs:`, key followed by `:`.
    in_jobs = False
    job_keys: list[str] = []
    for line in yaml_text.splitlines():
        stripped = line.rstrip()
        if not in_jobs:
            if stripped.startswith("jobs:"):
                in_jobs = True
            continue
        # Job entries are at exactly 2-space indent: `  job-name:`
        m = re.match(r"^  ([a-zA-Z0-9_-]+):\s*$", line)
        if m:
            job_keys.append(m.group(1))
        elif line and not line.startswith(" "):
            # Out of `jobs:` block
            break

    if not job_keys:
        return ValidationResult(True, "couldn't parse jobs: from workflow")
    if job_name not in job_keys:
        return ValidationResult(
            False,
            f"Track A: gha_workflow_check.grading_job is {job_name!r}, but the "
            f"actual {workflow_file} on {repo}@{capstone_branch} only defines "
            f"jobs {job_keys!r}. Pick one of those.",
        )
    return ValidationResult(True)


# ─────────────────────────────────────────────────────────────────────
# Track A — DEPRECATED rubric anti-patterns (2026-04-28 user directive)
# ─────────────────────────────────────────────────────────────────────
#
# User directive (verbatim, 2026-04-28): "Deprecate this type of judge
# from the evaluation ontology, writing observations is a poor way to
# evaluate."
#
# Subjective text-paste judging masquerades as grading: rubric asks the
# learner to "document observations" / "describe their style choices" /
# "reflect on" something, then an LLM-rubric grader makes a free-form
# call on whether the prose is "meaningful". The grading variance is
# huge, the pedagogy is read-and-answer (CLAUDE.md §"PREFER hands-on >
# read-and-answer"), and the learner can't iterate to a known-pass.
#
# Forbidden in rubric prose for any new step. Existing steps with these
# patterns are flagged for regen with OBJECTIVE replacements:
# - file existence (`test -f X.md`)
# - exact-content regex (`grep -E '<canonical>' X`)
# - test pass/fail (`pytest`, `mvn test`, `lab-grade.yml`)
# - LLM rubric ON A SPECIFIC FACT (e.g. "the diff includes @EntityGraph")
#   NOT on subjective prose quality.
_DEPRECATED_RUBRIC_PATTERNS: list[tuple[str, str]] = [
    # (regex pattern, learner-facing reason)
    # ── "observations" — banned in the rubric verb position ──
    (r"\b(?:your|meaningful|detailed|thoughtful|comprehensive|minimal)\s+observations?\b",
     "subjective grading on free-prose 'observations' — replace with objective check (file presence + canonical-content regex)"),
    (r"\bobservations?\s+(?:about|on|of|regarding|describing|documenting)",
     "subjective grading on 'observations about <X>' — deprecated; replace with objective deliverable check"),
    (r"\bobservations?[.-]txt\b",
     "deprecated `observations.txt` deliverable — subjective text-paste grading is banned in the eval ontology (2026-04-28)"),
    # ── "documenting <LLM>'s style/choices" — read-and-answer pedagogy ──
    (r"\b(?:documenting|documents?|documented)\s+(?:claude'?s?|kimi'?s?|aider'?s?|the\s+llm'?s?|the\s+model'?s?|chatgpt'?s?)\s*(?:style|choices|approach|conventions|reasoning|behavior|output|response|answers?)",
     "subjective grading on documenting LLM behavior — replace with objective conventions check (e.g. grep for canonical tokens)"),
    (r"\bdocumentation\s+(?:provided|present|missing|absent|of\s+claude|of\s+kimi|of\s+aider)",
     "subjective grading on 'documentation provided' — deprecated; objective only"),
    # ── "notes about / notes file" ──
    (r"\b(?:your\s+)?notes?\s+(?:about|on|describing|documenting|file\s+(?:with|containing))",
     "subjective grading on learner notes — replace with objective deliverable test"),
    # ── style-observations.txt and similar invented deliverables ──
    (r"\b(?:style[-_]observations?|style[-_]choices)[.-]?(?:txt|md)?\b",
     "deprecated `style-observations` / `style-choices` deliverable — subjective text-paste grading"),
    # ── "meaningful content" / "meaningful X" qualitative grading ──
    (r"\bmeaningful\s+(?:content|observations?|notes?|reflection|response|prose|writing|description)",
     "subjective 'meaningful X' qualitative grading — replace with objective signal"),
    # ── "writing style" / "your writing" ──
    (r"\bwriting\s+style\b|\byour\s+writing\b",
     "subjective grading on 'writing style' — pure read-and-answer pedagogy; deprecated"),
    # ── reflective essay / reflect on ──
    (r"\breflect\s+on\b",
     "subjective grading on reflective prose — replace with objective deliverable"),
    (r"\b(?:reflections?|reflective)\s+(?:on|about|essay|response)",
     "subjective reflective-essay grading — deprecated; objective only"),
    (r"\bdescribe\s+(?:in\s+(?:your\s+)?own\s+words|how\s+you\s+felt)\b",
     "subjective free-prose grading — deprecated"),
    # ── "explain in your own words" — commonly slips through ──
    (r"\bexplain\s+(?:in\s+your\s+own\s+words|why\s+you|how\s+you\s+would)",
     "subjective free-prose explanation grading — deprecated"),
]
_DEPRECATED_RUBRIC_REGEX = [
    (re.compile(pat, re.IGNORECASE), reason)
    for pat, reason in _DEPRECATED_RUBRIC_PATTERNS
]


def _track_a_check_rubric_no_subjective_grading(candidate: dict) -> ValidationResult:
    """Reject any step whose rubric grades on subjective free-prose.
    User directive 2026-04-28: writing-observations as a grading judge is
    deprecated from the evaluation ontology."""
    val = (candidate or {}).get("validation") or {}
    rubric = val.get("rubric") or ""
    if not isinstance(rubric, str) or not rubric.strip():
        return ValidationResult(True)
    hits: list[str] = []
    for rx, reason in _DEPRECATED_RUBRIC_REGEX:
        m = rx.search(rubric)
        if m:
            hits.append(f"{m.group(0)!r} → {reason}")
    if hits:
        return ValidationResult(
            False,
            f"Track A: rubric uses DEPRECATED subjective-grading pattern(s) — "
            f"{hits}. Per the 2026-04-28 evaluation-ontology rule, rubrics "
            f"must grade on OBJECTIVE signals only: file existence, exact "
            f"regex match against canonical content, or test pass/fail. "
            f"NOT free-form prose like 'document your observations' — that "
            f"is read-and-answer pedagogy, not skill-transfer.",
        )
    return ValidationResult(True)


# ─────────────────────────────────────────────────────────────────────
# Track A — fabricated tool subcommand detection
# ─────────────────────────────────────────────────────────────────────
#
# Verified subcommand surface per tool. The LLM was emitting
# `claude code "<prompt>"` treating `code` as a subcommand — Claude
# Code has NO `code` subcommand. (jspring M1.S2 v7 user-reported.)
# Real Claude Code subcommands: `mcp` (mcp list/add/remove), `agents`,
# `commands`, plus slash-commands inside an interactive session
# (/login, /logout, /clear, etc).
_TOOL_SUBCOMMANDS: dict[str, set[str]] = {
    # Tool → set of valid first-positional-token (subcommand). Empty set =
    # tool takes no subcommand (e.g. `aider` is a one-shot launcher).
    "claude": {
        # Real subcommands (verified):
        "mcp", "config", "doctor", "update", "migrate-installer",
        # Slash-commands aren't subcommands but are common typos —
        # slash-prefixed strings are skipped from this check.
    },
    # `aider` doesn't have subcommands; first positional after flags is
    # treated as a file. Empty = "no subcommands; positional ≠ subcommand".
    "aider": set(),
}


def _track_a_check_tool_subcommands(candidate: dict) -> ValidationResult:
    """Reject cli_commands or instructions that use a fabricated
    subcommand for a known tool. Example: `claude code "..."` is wrong;
    Claude Code uses `claude -p "..."` for one-shot or `claude` for
    interactive REPL."""
    text_blocks: list[str] = []
    cmds = _extract_cli_command_strings(candidate)
    text_blocks.extend(cmds)
    instr = ((candidate or {}).get("demo_data") or {}).get("instructions")
    if isinstance(instr, str):
        text_blocks.append(instr)

    bad_invocations: list[str] = []
    for text in text_blocks:
        # Find every `<tool> <token>` shape where <tool> is in our registry.
        # `<token>` must be a non-flag, non-quote, non-slash word.
        for tool, valid_subs in _TOOL_SUBCOMMANDS.items():
            # Look for "tool word" — word doesn't start with -, /, ", '
            for m in re.finditer(rf"\b{re.escape(tool)}\s+([a-z][a-z0-9-]*)\b", text):
                first_pos = m.group(1)
                if valid_subs == set():
                    # Tool has NO subcommands; first positional is a
                    # filename or interactive prompt — only flag the
                    # specific-known-bad case here. For now, no rejection.
                    continue
                if first_pos not in valid_subs:
                    bad_invocations.append(f"{tool} {first_pos}")
    if bad_invocations:
        # Dedup
        bad_invocations = sorted(set(bad_invocations))
        return ValidationResult(
            False,
            f"Track A: candidate uses fabricated subcommand(s) for known "
            f"tools — {bad_invocations}. For 'claude': real subcommands are "
            f"{sorted(_TOOL_SUBCOMMANDS['claude'])}. To send a one-shot prompt "
            f"to Claude Code, use `claude -p \"<prompt>\"` (NOT `claude code "
            f"\"...\"`). To start interactive Claude, use `claude` alone "
            f"and then type the prompt at the > prompt.",
        )
    return ValidationResult(True)


# ── Verified facts: per-tool flag whitelist ──
# Loaded lazily from backend.verified_facts_data when present.
_TOOL_FLAGS: dict[str, set[str]] = {
    # Tool name → set of valid flags. Conservative starting set — extend
    # via verified_facts_data.py over time. Empty set = "we don't know
    # this tool's flags; skip the check."
    "claude": {
        "-p", "--print",
        "-h", "--help",
        "--version",
        "-d", "--debug",
        "--model",
        "--output-format",
        "--allowedTools",
        "--permission-mode",
    },
    "aider": {
        "--version", "-h", "--help",
        "--model",
        "--message", "-m",
        "--message-file",
        "--no-stream",
        "--read",
        "--auto-test",
        "--test-cmd",
        "--auto-lint",
        "--lint-cmd",
        "--config",
        "--openai-api-base",
    },
}


def _track_a_check_cli_flags(candidate: dict) -> ValidationResult:
    """Every flag in cli_commands must appear in the verified_facts whitelist
    for its tool. Conservative: only checks tools we have facts for; unknown
    tools pass through."""
    cmds = _extract_cli_command_strings(candidate)
    bad_flags: list[str] = []
    for cmd in cmds:
        # First non-flag token is the tool
        toks = cmd.strip().split()
        if not toks:
            continue
        tool = toks[0].lstrip("./").split("/")[-1]  # `./mvnw` → `mvnw`
        flags_for_tool = _TOOL_FLAGS.get(tool)
        if flags_for_tool is None:
            continue  # don't have facts for this tool; skip
        # Extract every flag-shape token in the command
        for flag_match in _FLAG_PATTERN.findall(cmd):
            # Strip the equals-arg if any: --model=foo → --model
            flag = flag_match.split("=")[0]
            if flag not in flags_for_tool:
                bad_flags.append(f"{tool} {flag!r}")
    if bad_flags:
        return ValidationResult(
            False,
            f"Track A: cli_command(s) reference flag(s) not in the verified "
            f"facts list — {bad_flags}. Either the flag is fabricated, or "
            f"verified_facts_data needs an update.",
        )
    return ValidationResult(True)


def _track_a_check_test_class_names(
    candidate: dict, course_slug: str, module_position: int
) -> ValidationResult:
    """Test class names referenced in cli_commands must exist in the
    actual repo. Walks the git-tree at the relevant module's branch +
    matches `<ClassName>.java` against the file paths."""
    try:
        from backend.course_assets import get_course_assets, module_key_for_position
    except Exception:
        return ValidationResult(True)
    asset = get_course_assets(course_slug)
    if not asset:
        return ValidationResult(True)
    mod_key = module_key_for_position(course_slug, module_position)
    branch = asset.module_branches.get(mod_key) if mod_key else None
    if not branch:
        return ValidationResult(True)
    m = re.search(r"github\.com/([^/]+/[^/?#]+?)(?:\.git)?/?$", asset.course_repo)
    if not m:
        return ValidationResult(True)
    repo = m.group(1)

    tree = _gh_api_repo_tree(repo, branch)
    if tree is None:
        return ValidationResult(True, "couldn't fetch git tree; skip")

    # Build a set of class names that exist in the tree (basename without .java)
    class_files = {p.rsplit("/", 1)[-1].rsplit(".java", 1)[0]
                   for p in tree if p.endswith(".java")}

    cmds = _extract_cli_command_strings(candidate)
    seen: set[str] = set()
    bad_classes: list[str] = []
    for cmd in cmds:
        for cls in _JAVA_TEST_CLASS_PATTERN.findall(cmd):
            if cls in seen:
                continue
            seen.add(cls)
            if cls not in class_files:
                bad_classes.append(cls)
    if bad_classes:
        # List a few similar real names to help retry
        similar = [c for c in class_files if any(
            cls.lower()[:8] in c.lower() for cls in bad_classes
        )][:5]
        hint = f" Real classes that may be what you meant: {similar!r}" if similar else ""
        return ValidationResult(
            False,
            f"Track A: cli_command(s) reference Java class name(s) not found in "
            f"{repo}@{branch}'s git tree — {bad_classes}.{hint}",
        )
    return ValidationResult(True)


# ─────────────────────────────────────────────────────────────────────
# Top-level entry point
# ─────────────────────────────────────────────────────────────────────


def validate_step_candidate(
    candidate: dict,
    course_slug: str,
    module_position: int,
) -> ValidationResult:
    """Run all Track A + Track B checks against an LLM-emitted candidate
    step. Returns the FIRST failure encountered (short-circuit) so the
    retry feedback names the most-actionable specific issue.

    Returns ValidationResult(ok=True) when every check passes.
    """
    # Track B — runs first (cheap, no network).
    r = _track_b_check_branch_keys_not_used_as_values(candidate, course_slug)
    if not r.ok:
        return r

    # Track A — DEPRECATED rubric grading patterns (2026-04-28 user
    # directive). Cheap; no network. Rejects subjective text-grading
    # before any other check.
    r = _track_a_check_rubric_no_subjective_grading(candidate)
    if not r.ok:
        return r

    # Track A — fabricated tool subcommands (e.g. `claude code "..."`).
    # Cheap; no network.
    r = _track_a_check_tool_subcommands(candidate)
    if not r.ok:
        return r

    # Track A — flag check next (cheap, no network).
    r = _track_a_check_cli_flags(candidate)
    if not r.ok:
        return r

    # Track A — gha workflow job check (1 raw fetch).
    r = _track_a_check_gha_grading_job(candidate, course_slug)
    if not r.ok:
        return r

    # Track A — paths exist (gh api per path; auth recommended).
    r = _track_a_check_paths_resolve(candidate, course_slug, module_position)
    if not r.ok:
        return r

    # Track A — Java class names exist (git-tree match per class).
    r = _track_a_check_test_class_names(candidate, course_slug, module_position)
    if not r.ok:
        return r

    return ValidationResult(True)
