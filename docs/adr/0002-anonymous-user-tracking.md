# ADR 0002: Track anonymous MCP activity in PostHog

- Status: Accepted
- Date: 2026-07-24

## Context

AI clients (ChatGPT) send an anonymized `openai/subject` on tool calls. We need
a stable analytics identity before signup without operating a database or
treating that value as authenticated identity.

## Decision

Use the PostHog Python server SDK to capture one sanitized event for each MCP
operation. Use `mcp tool called` for tool calls and `mcp message processed` for
other operations. Resolve `openai/subject` from request metadata or the
`x-openai-subject` HTTP header as soon as either is available, derive
`HMAC-SHA256(ANONYMOUS_KEY_SECRET, "openai:" + subject)`, and use it as the
stable PostHog distinct ID. Alias any earlier connection-anonymous events into
that user. Reject tool calls without a subject and reject disagreeing or changed
identity sources within a connection.

Create UUIDv7 PostHog activity-session IDs locally. Reuse an ID until 30 minutes
of inactivity or 24 hours of total activity, then rotate it. Keep all state on
the in-memory FastMCP session. PostHog failures are logged and fail open.

Capture tool names, bounded tool arguments, and a canonical combined tool-call
property so usage can be analyzed by tool and input. Redact values whose keys
indicate passwords, tokens, secrets, credentials, email addresses, phone
numbers, credit cards, or private keys.
Never capture results, complete headers, raw request metadata, IP addresses,
raw subjects, or error messages.

## Consequences

### Positive

- Repeat callers merge into one PostHog person without signup.
- The service can deploy without PostgreSQL or migrations.
- Raw OpenAI subjects do not leave the process.
- Total tool calls, unique callers, tool names, and argument combinations are
  directly queryable in PostHog.

### Negative

- Local/non-ChatGPT clients must supply `openai/subject` or tool calls fail.
- Subject rotation or omission rejects tool calls.
- Relies on a server secret that must stay stable and private.
- Non-sensitive tool arguments may contain personal data, so tool schemas and
  PostHog retention/access controls require review as tools are added.
- PostHog is append-only analytics and cannot enforce transactional quotas.

## References

- [`docs/blog/user-identity-without-signup.md`](../blog/user-identity-without-signup.md)
- [`groceriesdeals.identity`](../../src/groceriesdeals/identity.py)
- [`groceriesdeals.mcp_posthog`](../../src/groceriesdeals/mcp_posthog.py)
