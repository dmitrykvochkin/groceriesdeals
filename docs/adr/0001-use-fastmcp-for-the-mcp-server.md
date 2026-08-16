# ADR 0001: Use FastMCP for the MCP server

- Status: Accepted
- Date: 2026-07-23

## Context

The project needs an MCP server so AI clients can access its capabilities
through the Model Context Protocol. We need a framework that supports typed
Python tools, generates MCP schemas, and can run locally or over HTTP while
fitting the project's existing Python and `uv` setup.

## Decision

We will use FastMCP as the framework for the project's MCP server.

The server will live in the `groceriesdeals` Python package. Local development
will use the `stdio` transport by default, with FastMCP's HTTP transport
available when a network-accessible MCP endpoint is needed.

## Consequences

### Positive

- MCP tools can be declared as typed Python functions.
- The server integrates with the existing Python and `uv` toolchain.
- Both local `stdio` and HTTP transports are available.
- FastMCP handles MCP protocol details and tool schema generation.

### Negative

- The project depends on FastMCP and its transitive dependencies.
- Framework upgrades may require application changes.
- Production use will require deliberate choices around authentication,
  deployment, observability, and version upgrades.

## References

- [FastMCP quickstart](https://gofastmcp.com/getting-started/quickstart)
- [`groceriesdeals.mcp_server`](../../src/groceriesdeals/mcp_server.py)
