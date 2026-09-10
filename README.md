# Genymotion SaaS launcher

Small Python/uv project for starting a Genymotion virtual Android device in
the cloud using Genymotion's supported `gmsaas` CLI.

## Setup

Install the optional Genymotion tooling:

```bash
uv sync --extra genymotion
```

Create an API token in Genymotion SaaS and export it without committing it:

```bash
export GENYMOTION_API_TOKEN="your-token"
```

Find the recipe you want to launch:

```bash
uv run gmsaas recipes list
```

## Start a device

```bash
uv run genymotion-cloud <recipe-uuid>
```

The device is automatically limited to 60 minutes. Override this and connect
ADB when needed:

```bash
uv run genymotion-cloud <recipe-uuid> \
  --name groceries-test \
  --max-run-duration 30 \
  --adb-connect
```

You can also invoke the Python script directly through uv:

```bash
uv run scripts/run_genymotion.py <recipe-uuid>
```

To avoid passing the recipe each time, set `GENYMOTION_RECIPE_UUID`.

## MCP server

Install the locked project dependencies:

```bash
uv sync
```

Run the FastMCP server locally with the default `stdio` transport:

```bash
cp .env.example .env
# Fill in ANONYMOUS_KEY_SECRET, POSTHOG_PROJECT_TOKEN, and POSTHOG_HOST.
uv run groceries-mcp
```

You can also run it through the FastMCP CLI:

```bash
uv run fastmcp run src/groceriesdeals/mcp_server.py:mcp
```

For an HTTP server instead, run:

```bash
uv run fastmcp run src/groceriesdeals/mcp_server.py:mcp \
  --transport http \
  --port 8438
```

The HTTP MCP endpoint is `http://localhost:8438/mcp`. The starter server
exposes a single `greet` tool that accepts a `name` string.

The installed project also provides an HTTP entry point intended for
containers. Its bind address, port, and MCP path can be overridden with
`MCP_HOST`, `MCP_PORT`, and `MCP_PATH`:

```bash
uv run groceries-mcp-http
```

### Production deployment

The repository includes a production image, Docker Compose stack, Caddy HTTPS
proxy, GHCR publishing workflow, and immutable release script. The MCP server
has no database dependency; usage analytics are sent to PostHog.

Follow the complete [AWS Lightsail deployment guide](docs/deployment/lightsail.md).

### MCP request audit logs

The server writes one-line JSON audit records for every MCP request, response,
and error. Request records include:

- the complete serializable MCP message;
- the client implementation name/version and capabilities declared during
  MCP initialization;
- MCP request and session IDs;
- request `_meta`, including a client-provided `client_id` when present;
- HTTP method, URL, peer address, HTTP version, and headers for HTTP transports;
- authenticated OAuth client ID, scopes, expiry, resource, and token claims.

Authorization headers, cookies, passwords, secrets, and token-shaped fields are
redacted. The bearer token itself is never logged. A human user ID is available
only when authentication supplies one in token claims (usually `sub`) or a
trusted gateway explicitly supplies it. Client names, user agents, forwarded
headers, and request `_meta` are client assertions and must not be treated as
authenticated identity.

Audit output is emitted to stderr both from the `groceries-mcp` entry point and
when the server is launched through the FastMCP CLI.

### PostHog usage tracking

The server sends sanitized PostHog events through the Python server SDK. Normal
MCP operations use `mcp message processed`; tool calls use the dedicated `mcp
tool called` event so they are visible in Activity. Events include MCP operation
names, safe component names, outcome, duration, client/protocol versions, and
UUIDv7 activity session IDs. Tool calls also include `tool_name`, bounded
`tool_parameters`, a UI-friendly `tool_parameters_json` string, and a canonical
`tool_call` string combining the name and parameters for breakdowns. Keys that
look like passwords, tokens, secrets, credentials, email addresses, phone
numbers, or private keys are replaced with `[REDACTED]`. Results, complete
headers, raw metadata, IP addresses, raw `openai/subject` values, and error
messages are never included.

The server reads `openai/subject` from request metadata or the ChatGPT
`x-openai-subject` header as soon as it is available, HMACs it into a stable
PostHog distinct ID, and rejects conflicting identities within one connection.
`ANONYMOUS_KEY_SECRET` must remain unchanged across deployments or the same
subject will derive a new ID. Events without either identity source use a
connection-scoped anonymous identity; tool calls still require a subject.
PostHog delivery is best-effort after startup and cannot interrupt MCP traffic.

To analyze usage in PostHog, select `mcp tool called`, count events for total
calls, count unique users for callers, and break down by `tool_name`. Break down
by `tool_call` for exact tool-plus-parameter combinations, or inspect/query
`tool_parameters` and `tool_parameters_json`. Filter `identity_status =
stable_user` when anonymous pre-identity traffic should not count as a user.

### Add the server to Codex

Start the HTTP server from the repository root:

```bash
uv run fastmcp run src/groceriesdeals/mcp_server.py:mcp \
  --transport http \
  --port 8438
```

Keep that process running. In another terminal, add its URL to Codex:

```bash
codex mcp add groceries-deals --url http://localhost:8438/mcp
```

Confirm that the server was added:

```bash
codex mcp list
```

Restart Codex after adding the server. In a Codex conversation, use `/mcp` to
check that `groceries-deals` is connected and that its `greet` tool is
available.

The equivalent entry in `~/.codex/config.toml` is:

```toml
[mcp_servers."groceries-deals"]
url = "http://localhost:8438/mcp"
```

The Codex desktop app and IDE extension also provide an **MCP servers**
settings screen. Choose **Streamable HTTP** and enter
`http://localhost:8438/mcp`.

The URL works only while the HTTP server process is running. If Codex should
start and stop the server automatically instead, configure it as a local
`stdio` server:

```bash
codex mcp add groceries-deals -- \
  uv --directory "$PWD" run groceries-mcp
```

To remove the server later:

```bash
codex mcp remove groceries-deals
```

## Local development

Start the MCP HTTP server and landing site together:

```bash
make up
```

- MCP at `http://localhost:8438/mcp`
- Landing at `http://localhost:3438`

Stop both processes with Ctrl+C.

## Landing site

The marketing landing page is a standalone Next.js app in `apps/landing`.

```bash
cd apps/landing
npm install
npm run dev
```

## Architecture decisions

Important technical decisions are recorded in
[`docs/adr`](docs/adr/README.md).
