# ADR 0002: Track anonymous MCP users via HMAC'd openai/subject

- Status: Accepted
- Date: 2026-07-24

## Context

AI clients (ChatGPT) send an anonymized `openai/subject` on tool calls. We need
a durable visitor identity in our DB before signup, without treating that value
as authenticated identity.

## Decision

On each `tools/call`, require `openai/subject`. Derive
`User.anonymous_key = HMAC-SHA256(ANONYMOUS_KEY_SECRET, "openai:" + subject)`
and get-or-create a `User` row. Missing subject rejects the call. Other MCP
methods (e.g. `initialize`) are unaffected. Tracking lives in dedicated
middleware, separate from audit logging.

## Consequences

### Positive

- Repeat callers map to one `User` without signup.
- Raw OpenAI subjects are not stored; a leaked DB does not expose them.
- Identity is centralized for later usage limits.

### Negative

- Local/non-ChatGPT clients must supply `openai/subject` or tool calls fail.
- Subject rotation or omission creates a new anonymous user.
- Relies on a server secret that must stay stable and private.

## References

- [`docs/blog/user-identity-without-signup.md`](../blog/user-identity-without-signup.md)
- [`groceriesdeals.mcp_users`](../../src/groceriesdeals/mcp_users.py)
- [`groceriesdeals.identity`](../../src/groceriesdeals/identity.py)
