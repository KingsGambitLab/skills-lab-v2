#!/usr/bin/env python3
"""Update .devcontainer/devcontainer.json on every working branch of every
course-repo to install Skillslab from the bundled-vsix URL on prod.

Idempotent: skips branches whose devcontainer.json already has the new
postCreateCommand. Safe to re-run.

Auth: relies on `gh` having a valid token (via env / `gh auth login`).
"""
from __future__ import annotations
import base64, json, subprocess, sys

OWNER = "tusharbisht"
REPOS_BRANCHES = {
    "kimi-eng-course-repo": [
        "module-0-preflight", "module-1-starter", "module-2-claudemd",
        "module-3-agents", "module-4-hooks", "module-5-mcp",
        "module-6-capstone",
    ],
    "aie-course-repo": [
        "module-0-preflight", "module-1-starter", "module-2-retry",
        "module-3-iterate", "module-4-mcp", "module-5-team",
        "module-6-agent-harness", "module-6-final",
    ],
    "jspring-course-repo": [
        "module-0-preflight", "module-1-starter", "module-2-claudemd",
        "module-3-agents", "module-4-hooks", "module-5-mcp",
        "module-6-capstone",
    ],
}

# v0.1.9 — install the bundled .vsix from the prod URL after container creation.
# Best-effort: if curl fails, postCreateCommand still succeeds so container
# is usable for the CLI flow; learner can install manually.
INSTALL_PREAMBLE = (
    "(curl -fsSL http://52.88.255.208/dl/skillslab.vsix -o /tmp/skillslab.vsix "
    "&& code --install-extension /tmp/skillslab.vsix) "
    "|| echo '[skillslab] vsix install skipped (network or server) — install manually'"
)

NEW_POST_CREATE_TAIL = " && skillslab --version && claude --version && echo Ready"


def gh_api(method: str, path: str, body: dict | None = None) -> dict:
    args = ["gh", "api", "-X", method, path]
    inp = None
    if body is not None:
        inp = json.dumps(body).encode()
        args += ["--input", "-"]
    out = subprocess.run(args, input=inp, capture_output=True, check=True).stdout
    return json.loads(out) if out.strip() else {}


def update_branch(repo: str, branch: str) -> str:
    """Returns 'updated' / 'skipped' / 'error <msg>'."""
    path = ".devcontainer/devcontainer.json"
    try:
        meta = gh_api("GET", f"repos/{OWNER}/{repo}/contents/{path}?ref={branch}")
    except subprocess.CalledProcessError as e:
        return f"error fetching: {e.stderr.decode()[:200]}"

    sha = meta["sha"]
    content_b64 = meta["content"]
    content_text = base64.b64decode(content_b64).decode("utf-8")
    try:
        cfg = json.loads(content_text)
    except json.JSONDecodeError as e:
        return f"error parsing JSON: {e}"

    # Idempotent skip: already has the v0.1.9 install command
    existing_pc = cfg.get("postCreateCommand", "")
    if "/dl/skillslab.vsix" in existing_pc:
        return "skipped (already updated)"

    # Compose new postCreateCommand: install .vsix first, then preserve any
    # tail the original config had (toolchain version checks).
    tail = ""
    if existing_pc and "skillslab" in existing_pc.lower():
        # Original had a toolchain check — preserve it via " && existing_pc"
        # but strip a leading "skillslab --version" since we keep that anyway.
        tail = " && " + existing_pc
    else:
        tail = NEW_POST_CREATE_TAIL
    cfg["postCreateCommand"] = INSTALL_PREAMBLE + tail

    # Add Python tooling to extensions (kept tusharbisht1391.skillslab for
    # eventual marketplace publish; harmless when not on marketplace —
    # VS Code logs a warning + skips).
    custom = cfg.setdefault("customizations", {}).setdefault("vscode", {})
    exts = custom.setdefault("extensions", [])
    for e in ["ms-python.python", "ms-python.vscode-pylance"]:
        if e not in exts:
            exts.append(e)

    new_text = json.dumps(cfg, indent=2) + "\n"
    new_b64 = base64.b64encode(new_text.encode("utf-8")).decode("ascii")

    try:
        gh_api(
            "PUT",
            f"repos/{OWNER}/{repo}/contents/{path}",
            body={
                "message": (
                    "feat: devcontainer installs Skillslab .vsix from prod URL "
                    "(v0.1.9 bundled-vsix flow)"
                ),
                "content": new_b64,
                "sha": sha,
                "branch": branch,
            },
        )
    except subprocess.CalledProcessError as e:
        return f"error updating: {e.stderr.decode()[:200]}"
    return "updated"


def main() -> None:
    total_updated = total_skipped = total_error = 0
    for repo, branches in REPOS_BRANCHES.items():
        print(f"\n=== {repo} ===")
        for br in branches:
            res = update_branch(repo, br)
            print(f"  {br:30s} → {res}")
            if res == "updated":
                total_updated += 1
            elif res.startswith("skipped"):
                total_skipped += 1
            else:
                total_error += 1
    print(f"\n--- Summary ---")
    print(f"  updated: {total_updated}")
    print(f"  skipped: {total_skipped}")
    print(f"  errors:  {total_error}")
    sys.exit(1 if total_error else 0)


if __name__ == "__main__":
    main()
