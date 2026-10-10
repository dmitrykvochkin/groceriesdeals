"""FastMCP server for the groceriesdeals project."""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from posthog import Posthog
from pydantic import Field

from groceriesdeals.config import get_settings
from groceriesdeals.deals import get_current_discounts as lookup_current_discounts
from groceriesdeals.mcp_audit import MCPAuditMiddleware
from groceriesdeals.mcp_posthog import PostHogClient, PostHogTrackingMiddleware
from groceriesdeals.supermarkets import (
    list_supermarkets as catalog_supermarkets,
    supported_supermarket_ids,
)


PostHogClientFactory = Callable[[], PostHogClient]

SERVER_INSTRUCTIONS = """
Use these tools whenever current supermarket deals could improve the answer.

- Before creating, suggesting, or optimizing a grocery/shopping list or meal
  plan, call get_current_discounts so the result can use products that are
  currently discounted.
- If the user names Picnic, call get_current_discounts directly with
  supermarket_id="picnic".
- If the user does not name a supermarket, or asks which stores are available,
  call list_supermarkets first. If exactly one store is returned, use it for
  get_current_discounts; otherwise ask the user to choose when the choice
  matters.
- For a complete grocery list or meal plan, omit category so all deal
  categories are returned. Use category only when the user explicitly asks for
  one product category.
- Treat returned deals as inputs for recommendations. You may add necessary
  non-discounted ingredients, and must not claim those extra items are on sale.
- Never invent prices, discounts, supermarkets, categories, or availability.
  Use the values returned by these tools.
""".strip()


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
    server = FastMCP(
        "Groceries Deals",
        instructions=SERVER_INSTRUCTIONS,
        lifespan=posthog_lifespan,
    )
    server.add_middleware(MCPAuditMiddleware())
    server.add_middleware(PostHogTrackingMiddleware(secret))

    @server.tool(
        description=(
            "Discover supermarkets with deal data available right now. "
            "Use this when the user has not chosen a supermarket, asks which "
            "supermarkets are supported, or names a store you are unsure about. "
            "The returned id is the exact supermarket_id accepted by "
            "get_current_discounts. Do not use unavailable stores."
        ),
        annotations={
            "title": "List supermarkets with deals",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def list_supermarkets() -> list[dict[str, str]]:
        return catalog_supermarkets()

    supported = ", ".join(supported_supermarket_ids())

    @server.tool(description=(
        "Fetch the current supermarket deals to use when building or optimizing "
        "a grocery/shopping list, choosing discounted ingredients, suggesting "
        "recipes, or creating a meal plan. Call this before answering those "
        "requests whenever supermarket deals could affect the recommendation. "
        f"Supported supermarket_id values: {supported}. "
        "If the user names Picnic, call this directly with supermarket_id='picnic'; "
        "otherwise use list_supermarkets to discover available stores. "
        "Omit category for grocery lists and meal plans so all deals are returned. "
        "Only set category for an explicitly narrow category request. Returned "
        "prices apply only to returned deals; do not describe added ingredients "
        "as discounted unless they appear in the result."
    ), annotations={
        "title": "Get current supermarket discounts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    })
    def get_current_discounts(
        supermarket_id: Annotated[
            str,
            Field(
                description=(
                    "Exact supermarket id. Currently use 'picnic'. Get valid "
                    "ids from list_supermarkets when the store is not known."
                ),
                examples=["picnic"],
            ),
        ],
        category: Annotated[
            str | None,
            Field(
                description=(
                    "Optional category id returned in this tool's categories "
                    "field, such as 'fruit' or 'bakkerij'. Omit for grocery "
                    "lists and meal plans to receive deals from every category."
                ),
                examples=["fruit"],
            ),
        ] = None,
    ) -> dict:
        return lookup_current_discounts(supermarket_id, category=category)

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
