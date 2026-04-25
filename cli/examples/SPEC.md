# SPEC — Module 1: User Service with Bearer-Token Auth

> The technical contract. PRD.md is the WHY; this is the HOW.

## File-level contract

You will modify exactly these files:

- `auth.py` — add `POST /api/auth/cli_token` + extend
  `session_middleware` to accept `Authorization: Bearer <token>`
- `tests/test_cli_token.py` — NEW; tests for the new endpoint +
  middleware behavior
- `tests/test_cookie_auth_regression.py` — NEW; regression test
  proving cookie callers still work

You will NOT modify:

- `database.py` — the `auth_sessions` table already has every column
  we need (`id`, `user_id`, `expires_at`, `user_agent`)
- Any frontend file
- Any config file
- The `User` model

## Endpoint contract

```http
POST /api/auth/cli_token
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "hunter2",
  "label": "cli@laptop"          # optional, default "cli"
}
```

**On success (200):**

```json
{
  "token": "<opaque-string>",
  "user_id": 42,
  "email": "alice@example.com",
  "expires_at": "2026-07-25T14:30:00Z",
  "label": "cli@laptop"
}
```

**On invalid credentials (401):**

```json
{ "detail": "Invalid email or password" }
```

## Middleware contract

`session_middleware` must:

1. Accept `Authorization: Bearer <token>` headers, look up the matching
   `auth_sessions` row, attach the user to `request.state.user`.
2. Fall back to the existing `sll_session` cookie path when no Bearer
   header is present.
3. Return 401 on invalid tokens (don't fall through to anonymous).
4. Allow anonymous on routes marked with `@allow_anonymous`.

Order: Bearer first (fail fast on bad tokens), then cookie, then
anonymous.

## Test contract

`tests/test_cli_token.py` MUST cover:

| Test | Asserts |
|---|---|
| `test_issue_token_with_valid_creds` | 200 + valid JWT-shaped response |
| `test_issue_token_with_wrong_password` | 401 |
| `test_issue_token_with_unknown_email` | 401 |
| `test_token_works_on_protected_endpoint` | bearer-auth `GET /api/auth/me` returns 200 |
| `test_invalid_token_is_rejected` | bearer with `XYZ` token returns 401 |

`tests/test_cookie_auth_regression.py` MUST cover:

| Test | Asserts |
|---|---|
| `test_cookie_auth_still_works` | login via existing flow, cookie request returns 200 |

## Acceptance

The CLI will run `pytest tests/test_cli_token.py tests/test_cookie_auth_regression.py -v`
in cwd. Exit 0 = pass. The full output is captured into the rubric
submission so the grader can see EXACTLY which tests passed.

## Hints (open in order, only when stuck)

1. The existing `verify_password` function lives in `backend/auth.py` —
   reuse, don't reimplement.
2. `AuthSession.new_for_user(user_id, ttl_hours=...)` already exists;
   it returns an unsaved session you can populate then commit.
3. The middleware is currently a function, not a class — add the
   bearer check at the top, before the cookie lookup.
4. The regression test should mint a session via the existing
   cookie-login endpoint, NOT by faking the cookie value directly.

## Anti-patterns to avoid

- Don't add a new database table. `auth_sessions` already supports
  everything you need.
- Don't put the bearer-parsing logic in a separate middleware. Keep it
  in `session_middleware` — the existing tests assume one middleware.
- Don't return the password back in the response. Even hashed.
- Don't log the token. Anywhere.

## Skill being practiced

- Reading existing code before writing new code.
- Backwards-compatible API extension.
- Regression tests that actually run the OLD path through.
- Pushing back on AI suggestions that violate the SPEC (e.g. claude
  will likely propose adding a new table — the SPEC says no).
