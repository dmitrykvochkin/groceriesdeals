"""FastMCP server for the groceriesdeals project."""

import asyncio
import logging
import os
from collections.abc import Callable

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from posthog import Posthog

from groceriesdeals.config import get_settings
from groceriesdeals.mcp_audit import MCPAuditMiddleware
from groceriesdeals.mcp_posthog import PostHogClient, PostHogTrackingMiddleware


PostHogClientFactory = Callable[[], PostHogClient]


def _posthog_error(error: Exception, *_args: object) -> None:
    logging.getLogger("groceriesdeals.mcp.posthog").warning(
        "PostHog delivery failed (%s)", type(error).__name__
    )


def create_posthog_client() -> PostHogClient:
    """Create the process-wide buffered PostHog server client."""
    settings = get_settings()
    return Posthog(
        settings.posthog_project_token,
        host=str(settings.posthog_host),
        on_error=_posthog_error,
        sync_mode=False,
        disable_geoip=True,
    )


def create_mcp(
    posthog_client_factory: PostHogClientFactory = create_posthog_client,
    *,
    anonymous_key_secret: str | None = None,
) -> FastMCP:
    """Build the MCP server, allowing a recording analytics client in tests."""

    @lifespan
    async def posthog_lifespan(_server: FastMCP):
        client = posthog_client_factory()
        try:
            yield {"posthog_client": client}
        finally:
            try:
                await asyncio.to_thread(client.shutdown)
            except Exception:
                logging.getLogger("groceriesdeals.mcp.posthog").warning(
                    "PostHog shutdown failed", exc_info=True
                )

    secret = anonymous_key_secret or get_settings().anonymous_key_secret
    server = FastMCP("Groceries Deals", lifespan=posthog_lifespan)
    server.add_middleware(MCPAuditMiddleware())
    server.add_middleware(PostHogTrackingMiddleware(secret))

    @server.tool
    def greet(name: str) -> str:
        """Return a friendly greeting."""
        return f"Hello, {name}!"

    return server


mcp = create_mcp()


def main() -> None:
    """Run the MCP server using the local stdio transport."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


def main_http() -> None:
    """Run the MCP server using Streamable HTTP for container deployments."""
    logging.basicConfig(level=logging.INFO)
    mcp.run(
        transport="http",
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8438")),
        path=os.getenv("MCP_PATH", "/mcp"),
    )


if __name__ == "__main__":
    main()
