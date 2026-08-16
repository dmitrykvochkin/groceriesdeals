# Genymotion SaaS launcher

Small Python/uv project for starting a Genymotion virtual Android device in
the cloud using Genymotion's supported `gmsaas` CLI.

## Setup

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

Start Postgres, the MCP HTTP server, and the landing site together:

```bash
make up
```

- Postgres via docker compose (host port `5438`)
- MCP at `http://localhost:8438/mcp`
- Landing at `http://localhost:3438`

Stop MCP and the landing site with Ctrl+C. Stop Postgres with:

```bash
make down
```

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
