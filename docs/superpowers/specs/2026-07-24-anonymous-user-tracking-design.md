# Anonymous User Tracking Design

Date: 2026-07-24

## Goal

Track anonymous MCP callers by creating a `User` row for every `tools/call` that includes ChatGPT’s `openai/subject`, using a server-derived HMAC as `anonymous_key`.

## Decisions

- `anonymous_key` = hex(`HMAC-SHA256(ANONYMOUS_KEY_SECRET, "openai:" + openai/subject)`)
- Missing or blank subject on `tools/call` rejects the tool call
- Gate applies only to `tools/call` (not `initialize` or notifications)
- Upsert `User` only — no request/usage counters in this change
- Dedicated `UserTrackingMiddleware` after audit logging; audit stays read-only

## Flow

1. Audit middleware logs the request.
2. User-tracking middleware handles `on_call_tool`.
3. Read `openai/subject` from request `_meta`.
4. If missing, reject with a clear error.
5. Derive `anonymous_key` via HMAC.
6. Get or create `User` by `anonymous_key` (unique violation → re-select).
7. Continue to the tool.

## Components

- `config.Settings.anonymous_key_secret` — required env `ANONYMOUS_KEY_SECRET`
- `identity.py` — extract subject, derive key, ensure user
- `mcp_users.UserTrackingMiddleware` — FastMCP middleware on `tools/call`
- Existing `User` model and `get_session()` — no schema change

## Out of scope

- Request counting / freemium limits
- Attaching `User` to tool context
- mTLS verification that the caller is ChatGPT
