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

# v0.1.9.1 — install moved to postAttachCommand (runs every VS Code attach,
# idempotent). postCreateCommand keeps the existing toolchain smoke (runs
# once at container creation).
#
# Why the move: at postCreateCommand time the default Dev Containers shell
# is /bin/sh (dash on Debian-based images), which doesn't source .bashrc
# or .profile, so the `code` CLI VS Code Server adds to PATH via shell rc
# isn't visible. Got "/bin/sh: 1: code: not found" on the first deploy.
#
# Two robustness layers:
#   1. Use bash -c (not /bin/sh) so we have a richer shell.
#   2. Locate `code` via PATH first, then fall back to known dev-container
#      install locations (/vscode/bin/<commit>/, ~/.vscode-server/bin/<commit>/)
#      so we don't depend on PATH being right.
#
# postAttachCommand fires every time VS Code attaches to the container,
# which is when `code` is reliably available. Idempotency check via
# `code --list-extensions | grep -qx tusharbisht1391.skillslab` skips the
# curl on subsequent attaches.
POST_CREATE_TOOLCHAIN_SMOKE = "skillslab --version && claude --version && echo Ready"

POST_ATTACH_INSTALL_SCRIPT = (
    # v0.1.9.2 — wider search + retry-loop + find-fallback + diagnostics.
    # The 4-path lookup in v0.1.9.1 still missed `code` on at least one
    # learner's container. Now we (a) retry every 2s for 30s in case
    # VS Code Server hadn't bootstrapped yet, (b) check more locations
    # including `code-tunnel`-style paths, (c) fall back to a depth-bounded
    # `find` over common parent dirs, (d) on FINAL failure emit
    # diagnostics so the next iteration can extend the lookup.
    'find_code() { '
    '  command -v code 2>/dev/null && return 0; '
    '  for p in '
    '    /vscode/bin/*/bin/remote-cli/code '
    '    /vscode/cli/*/bin/code '
    '    /vscode/server/*/bin/remote-cli/code '
    '    /home/*/.vscode-server/bin/*/bin/remote-cli/code '
    '    /home/*/.vscode-server/cli/*/bin/code '
    '    /root/.vscode-server/bin/*/bin/remote-cli/code '
    '    /root/.vscode-server/cli/*/bin/code '
    '    /opt/vscode-server/bin/code '
    '    /usr/local/bin/code '
    '    /usr/bin/code; '
    '  do ls $p 2>/dev/null | head -1 && return 0; done; '
    '  find /vscode /opt /root /home -maxdepth 7 -name code -type f -executable 2>/dev/null '
    '    | grep -E "remote-cli|/bin/code$" | head -1; '
    '}; '
    # Retry up to 15 × 2s = 30s in case VS Code Server is still bootstrapping.
    'CODE=""; '
    'for try in $(seq 1 15); do '
    '  CODE=$(find_code); '
    '  [ -n "$CODE" ] && break; '
    '  sleep 2; '
    'done; '
    'if [ -z "$CODE" ]; then '
    '  echo "[skillslab] code CLI not found after 30s wait — diagnostics:"; '
    '  echo "  USER=$(whoami) HOME=$HOME"; '
    '  echo "  /vscode/* : $(ls /vscode 2>&1 | head -3 | tr \\\\n \\\\  )"; '
    '  echo "  $HOME/.vscode-server/* : $(ls $HOME/.vscode-server 2>&1 | head -3 | tr \\\\n \\\\  )"; '
    '  echo "  PATH=$PATH"; '
    '  echo "  Manual install: download http://52.88.255.208/dl/skillslab.vsix and run code --install-extension <path>"; '
    '  exit 0; '
    'fi; '
    # Idempotency: skip the download if extension is already installed.
    'if "$CODE" --list-extensions 2>/dev/null | grep -qx tusharbisht1391.skillslab; then '
    '  echo "[skillslab] extension already installed (using $CODE)"; '
    '  exit 0; '
    'fi; '
    # Fresh install path.
    'echo "[skillslab] using $CODE — downloading + installing extension..."; '
    'curl -fsSL http://52.88.255.208/dl/skillslab.vsix -o /tmp/skillslab.vsix '
    '&& "$CODE" --install-extension /tmp/skillslab.vsix '
    '|| echo "[skillslab] install failed (network or download issue); install manually"'
)

# Array form so the JSON encoder handles all quoting cleanly + bash sees a
# single -c arg without shell-meta interpretation.
POST_ATTACH_COMMAND = ["bash", "-c", POST_ATTACH_INSTALL_SCRIPT]


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

    # Idempotent skip: only if the script body byte-for-byte matches the
    # current POST_ATTACH_INSTALL_SCRIPT. Lets the script self-update across
    # bug-fix iterations (v0.1.9 → v0.1.9.1 → v0.1.9.2) without manual
    # branch surgery — every re-run propagates the latest install logic.
    existing_pac = cfg.get("postAttachCommand")
    if (
        isinstance(existing_pac, list)
        and len(existing_pac) >= 3
        and existing_pac[2] == POST_ATTACH_INSTALL_SCRIPT
    ):
        return "skipped (already up-to-date)"

    # v0.1.9.1 surgery:
    #   1. postCreateCommand → just the toolchain smoke (no .vsix install)
    #   2. postAttachCommand → the array-form install script with PATH fallback
    cfg["postCreateCommand"] = POST_CREATE_TOOLCHAIN_SMOKE
    cfg["postAttachCommand"] = POST_ATTACH_COMMAND

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
                    "fix: devcontainer postAttachCommand installs .vsix with "
                    "code-CLI PATH fallback (v0.1.9.1 — fixes /bin/sh: code: not found)"
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
