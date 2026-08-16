"""FastMCP server for the groceriesdeals project."""

import logging

from fastmcp import FastMCP

from groceriesdeals.mcp_audit import MCPAuditMiddleware
from groceriesdeals.mcp_users import UserTrackingMiddleware

mcp = FastMCP("Groceries Deals")
mcp.add_middleware(MCPAuditMiddleware())
mcp.add_middleware(UserTrackingMiddleware())


@mcp.tool
def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"


def main() -> None:
    """Run the MCP server using the local stdio transport."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
