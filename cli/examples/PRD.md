# PRD — Module 1: User Service with Bearer-Token Auth

> This file lives at the root of a course-repo's module branch (e.g.
> `module-1-bearer-auth`). It tells the learner WHAT they're building
> and WHY. SPEC.md tells them the technical contract. .skillslab.yml
> tells the CLI how to grade.

## Context

You are joining a B2B SaaS team mid-sprint. The product has a working
`UserService` that authenticates via session cookies — fine for the
browser, useless for our new CLI clients. Your task: extend the
service to issue + accept bearer tokens, **without breaking existing
cookie-auth callers**.

This module mirrors the EXACT change we shipped on the LMS itself
two days ago (`2026-04-25 — backend/auth.py: cli_token + bearer
middleware`). When you finish, you'll have re-derived a real
production change from a real codebase.

## What "done" looks like

A learner completing this module ships:

1. A new endpoint `POST /api/auth/cli_token` that accepts
   `{email, password, label}` and returns a bearer token.
2. A middleware update that accepts `Authorization: Bearer <token>`
   alongside the existing cookie path.
3. Tests proving:
   - The new endpoint returns a token + expiry on valid creds
   - The middleware rejects invalid tokens with 401
   - Cookie-auth callers still work (regression test)
4. A `git diff` against `module-1-starter` that ONLY touches
   `auth.py` + the new test files (no scope creep).

## Why this matters

Bearer-token auth is the on-ramp to every "API for our product"
conversation. It's small enough to write in 30 minutes, but the
backwards-compat middleware split is the kind of detail that bites
in production if you skip the regression test. This is your first
exposure to the pattern; later modules build on it.

## Out of scope

- OAuth / OIDC / Auth0 integration
- Token revocation / introspection endpoints
- Database schema changes (the `auth_sessions` table already exists)
- Frontend wiring

## How the AI tooling fits in

You'll use `claude` (or `aider`, depending on which course you're
taking) as your pair. The intended workflow:

1. Read this PRD. Read SPEC.md. Read the existing `auth.py`.
2. Ask `claude` to summarize the existing middleware's flow.
3. Have `claude` propose the diff. Read it. **Push back when the
   proposal is wrong** — that's the actual skill we're teaching.
4. Apply, run `skillslab check`, iterate.

The grader will see your `git diff` AND your test output. Both matter.
