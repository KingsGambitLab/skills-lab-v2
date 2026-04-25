# skillslab — single image carrying everything the 3 AI-enablement courses need
# at the terminal: Python 3.11 (CLI runtime + pytest), Java 21 + Maven (jspring),
# Node 20 + npm (any frontend bits), git/curl, plus the BYO-key LLM CLIs
# (claude + aider). One image, every course's toolchain inside.
#
# Design rule: the learner mounts their course-repo at /work and runs
# `skillslab login` / `skillslab start <course>` / `skillslab check` from
# inside the container. ~/.skillslab/ is mounted from the host so token +
# cursor + step files survive container restarts.
#
# Image size budget: ~1.8GB. Big but it's the SUM of (java jdk + node + python
# + mvn + 2 LLM CLIs). Cached locally after first pull; rebuilds only when
# pinned deps move. Course-specific layers can extend FROM this base.

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_VERSION=20 \
    MAVEN_VERSION=3.9.9 \
    M2_HOME=/opt/maven \
    PATH=/opt/maven/bin:/root/.local/bin:$PATH

# ── System deps ──────────────────────────────────────────────────────────
# - default-jdk-headless        : jspring-course (Bookworm ships JDK 17,
#                                  which Spring Boot 3.x fully supports)
# - nodejs + npm + claude CLI   : aie-course (BYO-key)
# - python tooling already there from the base image
# - git/curl/ca-certificates/jq/less : everyday CLI ergonomics
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl wget gnupg2 git jq less openssh-client \
        build-essential pkg-config \
        default-jdk-headless \
        vim nano \
    && rm -rf /var/lib/apt/lists/*

# GitHub CLI — `gh repo fork --clone` is the immersive fork path so the
# learner never has to leave the container to set up a fork. Installed
# from the official cli/cli apt repo.
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/* \
    && gh --version

# JAVA_HOME resolves dynamically (different on amd64 vs arm64). Set it
# from the actual link target so `mvn`, `javac` etc. find their JDK.
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH

# ── Maven (no apt package — install upstream binary) ──────────────────────
RUN curl -fsSL "https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz" \
        | tar -xz -C /opt/ \
    && ln -s /opt/apache-maven-${MAVEN_VERSION} /opt/maven \
    && mvn -v

# ── Node 20 (NodeSource) + npm-installed claude CLI ──────────────────────
RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code \
    && claude --version

# ── Python deps: pytest for jspring/Kimi tests + aider for Kimi course ───
RUN pip install --no-cache-dir \
        pytest>=8.3 \
        pytest-asyncio>=0.24 \
        ipython \
        aider-chat>=0.85 \
    && pytest --version \
    && aider --version

# ── Skillslab CLI itself ─────────────────────────────────────────────────
# COPY at build time (so `docker run skillslab:latest` works standalone
# without any volume mounts), THEN install editable from /skillslab-cli.
#
# Upgrade story (2026-04-25 — keep this in sync with the README):
#   * Source-only changes (Python files under src/skillslab/): NO REBUILD
#     needed if you `docker compose run` — docker-compose.yml bind-mounts
#     `./:/skillslab-cli` over this build-time copy, so the in-container
#     `skillslab` binary picks up host changes the moment you `git pull`.
#   * Dependency changes (pyproject.toml, system deps in apt-get, npm
#     packages, pinned aider/pytest versions): REBUILD with
#     `docker compose build` so the new versions land.
#
# For ad-hoc `docker run skillslab:latest` (no compose), the build-time
# copy is what runs — rebuild for any source change.
COPY . /skillslab-cli
RUN pip install --no-cache-dir -e /skillslab-cli \
    && skillslab --version

# ── Workdir + helper banner ──────────────────────────────────────────────
WORKDIR /work

# State volume: ~/.skillslab gets mounted here. We pre-create the dir so a
# fresh `docker run` works without a host-side bind-mount when learners just
# want to try the CLI ephemerally.
RUN mkdir -p /root/.skillslab \
    && echo '. /etc/skillslab-banner.sh' >> /root/.bashrc

COPY <<'EOF' /etc/skillslab-banner.sh
echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
echo "  │  skillslab — AI-augmented engineering, in your terminal     │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  Immersive flow (everything stays in this container):       │"
echo "  │                                                             │"
echo "  │    skillslab login              — sign in (BYO bearer)      │"
echo "  │    skillslab start <kimi|aie|jspring>                       │"
echo "  │    skillslab status             — current step + repo URL   │"
echo "  │    skillslab clone --fork       — fork & clone into /work   │"
echo "  │    skillslab spec               — read the step briefing    │"
echo "  │    # ...edit code with claude / aider...                    │"
echo "  │    skillslab check              — grade + advance on pass   │"
echo "  │                                                             │"
echo "  │  Toolchain inside this image:                               │"
echo "  │    python java node | claude aider mvn pytest gh git vim    │"
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""
EOF
RUN chmod +x /etc/skillslab-banner.sh

# Default to an interactive shell — learners drop into /work and run
# `skillslab` directly. Override with `docker run skillslab <subcommand>` to
# script things headlessly.
CMD ["/bin/bash"]
