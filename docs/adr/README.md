# Architecture Decision Records

Architecture Decision Records (ADRs) document important technical decisions
made in this project and the reasoning behind them.

## Conventions

- Use the next four-digit sequence number for each ADR.
- Use lowercase, hyphen-separated filenames:
  `NNNN-short-decision-title.md`.
- Record one decision per ADR.
- Do not rewrite an accepted decision when it changes. Add a new ADR that
  supersedes the old one.

## Decisions

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-use-fastmcp-for-the-mcp-server.md) | Use FastMCP for the MCP server | Accepted |
| [0002](0002-anonymous-user-tracking.md) | Track anonymous MCP users via HMAC'd openai/subject | Accepted |
