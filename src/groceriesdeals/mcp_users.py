"""Middleware that tracks anonymous users for MCP tool calls."""

from __future__ import annotations

from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.base import ToolResult
import mcp.types as mt

from groceriesdeals.config import get_settings
from groceriesdeals.db.session import get_session
from groceriesdeals.identity import (
    derive_anonymous_key,
    extract_openai_subject,
    record_tool_request,
)


class UserTrackingMiddleware(Middleware):
    """Ensure a User exists for each tools/call with openai/subject."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: Any,
    ) -> ToolResult:
        fastmcp_context = context.fastmcp_context
        meta = None
        if fastmcp_context is not None and fastmcp_context.request_context is not None:
            meta = fastmcp_context.request_context.meta

        subject = extract_openai_subject(meta)
        if subject is None:
            raise ToolError("Anonymous subject required")

        settings = get_settings()
        anonymous_key = derive_anonymous_key(settings.anonymous_key_secret, subject)
        with get_session() as session:
            record_tool_request(session, anonymous_key)

        return await call_next(context)
