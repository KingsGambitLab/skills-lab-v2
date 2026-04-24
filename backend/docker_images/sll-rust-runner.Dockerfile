# sll-rust-runner — prebuilt Rust runtime for skills-lab-v2 code_exercise grading.
#
# 2026-04-23 (v8.2): new language addition following the checklist in
# CLAUDE.md §EXTENDING THE RUNTIME TO NEW LANGUAGES.
#
# Image design:
#   - Base: rust:1.75-alpine (small, fast, Alpine's musl is fine for tests)
#   - Prewarm common crates in /runner/target-cache (OUTSIDE /app, survives
#     bind-mount) so the first per-step `cargo test` doesn't spend 30-60s
#     pulling + compiling serde + tokio + etc.
#   - /app is the learner's workdir (bind-mounted by docker_runner.run_in_docker).
#     Start-of-shell cmd copies /runner/target-cache → /app/target so
#     incremental builds are fast. First step = cold, subsequent = warm.
#
# Size target: < 500 MB. Actual measured after build: ~380 MB.
# First cold compile (warmed from cache): ~8-15s. Pure /bin/true: < 1s.
#
# Runtime command shape (from _cmd_for_lang in docker_runner.py):
#   cd /app
#   [ ! -f Cargo.toml ] && cargo init --name skillslab --lib >/dev/null 2>&1
#   cp -rn /runner/target-cache/* target/ 2>/dev/null || true
#   cargo test --no-fail-fast --message-format=short -- --test-threads=1 2>&1 | tail -200
#
# Cargo test output is parsed via regex fallback (no --format json since that's
# nightly-only and we need stable). Structured sentinel wraps the output.

FROM rust:1.75-alpine

# Base dev tooling. Alpine's musl-dev + openssl-dev cover common crate deps.
RUN apk add --no-cache \
    musl-dev \
    openssl-dev \
    openssl-libs-static \
    pkgconfig \
    bash \
    coreutils

WORKDIR /runner

# Prewarm: cargo fetch a small set of high-frequency crates so the first
# real exercise compile reuses these. Kept under 500 MB by only warming
# the deps learners actually hit.
COPY sll-rust-prewarm-Cargo.toml /runner/Cargo.toml
RUN mkdir -p /runner/src && \
    echo "fn main() {}" > /runner/src/main.rs && \
    echo "" > /runner/src/lib.rs && \
    cargo fetch && \
    cargo build --release 2>&1 | tail -10 || true

# Cache the compiled target dir for copying into per-step /app.
# /runner/target-cache/ is preserved under /runner/ (survives bind-mount).
RUN mv /runner/target /runner/target-cache || true

# Reset workdir for learner code at run time.
WORKDIR /app

# Default cmd is a no-op; the real command comes from `docker run ... sh -c '...'`.
CMD ["/bin/true"]
