"""Structured audit logging for incoming MCP traffic."""

from __future__ import annotations

import dataclasses
import json
import logging
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any

from fastmcp.server.dependencies import (
    get_access_token,
    get_http_headers,
    get_http_request,
)
from fastmcp.server.middleware import Middleware, MiddlewareContext
from pydantic import BaseModel

logger = logging.getLogger("groceriesdeals.mcp.audit")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "api-key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "proxy-authorization",
    "secret",
    "set-cookie",
    "token",
}


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("_", "-")
    return (
        normalized in _SENSITIVE_KEYS
        or normalized.endswith("-password")
        or normalized.endswith("-secret")
        or normalized.endswith("-token")
    )


def _jsonable(value: Any) -> Any:
    """Convert framework objects to JSON-compatible values without failing."""
    if isinstance(value, BaseModel):
        try:
            return value.model_dump(mode="json", by_alias=True)
        except Exception:
            return _jsonable(value.model_dump(mode="python", by_alias=True))
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _REDACTED if _is_sensitive_key(key) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _sensitive_values(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        found: list[str] = []
        for key, item in value.items():
            if _is_sensitive_key(key) and isinstance(item, (str, int, float)):
                found.append(str(item))
            else:
                found.extend(_sensitive_values(item))
        return found
    if isinstance(value, list):
        return [secret for item in value for secret in _sensitive_values(item)]
    return []


def _redact_error(error: Exception, unredacted_message: Any) -> str:
    text = str(error)
    for sensitive_value in _sensitive_values(_jsonable(unredacted_message)):
        if sensitive_value:
            text = text.replace(sensitive_value, _REDACTED)
    return text


def _client_details(context: MiddlewareContext[Any]) -> dict[str, Any] | None:
    message = context.message
    initialize_params = getattr(message, "params", None)
    if context.method == "initialize" and initialize_params is not None:
        return {
            "implementation": _jsonable(
                getattr(initialize_params, "clientInfo", None)
            ),
            "capabilities": _jsonable(
                getattr(initialize_params, "capabilities", None)
            ),
            "requested_protocol_version": getattr(
                initialize_params, "protocolVersion", None
            ),
        }

    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None:
        return None

    try:
        client_params = fastmcp_context.session.client_params
    except RuntimeError:
        client_params = None

    if client_params is None:
        return None
    return {
        "implementation": _jsonable(client_params.clientInfo),
        "capabilities": _jsonable(client_params.capabilities),
        "requested_protocol_version": client_params.protocolVersion,
    }


def _mcp_details(context: MiddlewareContext[Any]) -> dict[str, Any]:
    details: dict[str, Any] = {
        "method": context.method,
        "source": context.source,
        "message_kind": context.type,
        "message_type": type(context.message).__name__,
        "received_at": context.timestamp.isoformat(),
        "message": _jsonable(context.message),
    }
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None:
        return details

    details["transport"] = fastmcp_context.transport
    details["task_id"] = fastmcp_context.task_id
    details["origin_request_id"] = fastmcp_context.origin_request_id

    request_context = fastmcp_context.request_context
    if request_context is not None:
        details["request_id"] = fastmcp_context.request_id
        details["request_meta"] = _jsonable(request_context.meta)
        # This is request metadata named client_id, not authenticated identity.
        details["request_meta_client_id"] = fastmcp_context.client_id

    # During HTTP initialization the transport has not assigned its response
    # Mcp-Session-Id yet. Reading ctx.session_id at that point would generate
    # and cache a different fallback ID, hiding the real transport ID later.
    if request_context is not None:
        try:
            details["session_id"] = fastmcp_context.session_id
        except RuntimeError:
            details["session_id"] = None
    else:
        details["session_id"] = None

    return details


def _http_details() -> dict[str, Any] | None:
    try:
        request = get_http_request()
    except RuntimeError:
        return None

    scope = request.scope
    return {
        "method": request.method,
        "url": str(request.url),
        "client": _jsonable(scope.get("client")),
        "server": _jsonable(scope.get("server")),
        "http_version": scope.get("http_version"),
        "scheme": scope.get("scheme"),
        "root_path": scope.get("root_path"),
        "headers": _redact(get_http_headers(include_all=True)),
    }


def _authentication_details() -> dict[str, Any]:
    token = get_access_token()
    if token is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "oauth_client_id": token.client_id,
        "scopes": _jsonable(token.scopes),
        "expires_at": token.expires_at,
        "resource": token.resource,
        "claims": _redact(_jsonable(token.claims)),
        # The bearer token itself is intentionally never logged.
    }


def request_snapshot(context: MiddlewareContext[Any]) -> dict[str, Any]:
    """Build the complete safe, serializable view of an MCP request."""
    return _redact(
        {
            "event": "mcp_request",
            "mcp": _mcp_details(context),
            "client": _client_details(context),
            "http": _http_details(),
            "authentication": _authentication_details(),
        }
    )


class MCPAuditMiddleware(Middleware):
    """Log MCP requests, results, and failures as one-line JSON records."""

    async def on_message(self, context: MiddlewareContext[Any], call_next: Any) -> Any:
        snapshot = request_snapshot(context)
        logger.info(json.dumps(snapshot, separators=(",", ":"), ensure_ascii=False))

        try:
            result = await call_next(context)
        except Exception as exc:
            logger.error(
                json.dumps(
                    {
                        "event": "mcp_error",
                        "method": context.method,
                        "request_id": snapshot["mcp"].get("request_id"),
                        "session_id": snapshot["mcp"].get("session_id"),
                        "error_type": type(exc).__name__,
                        "error": _redact_error(exc, context.message),
                    },
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
            )
            raise

        logger.info(
            json.dumps(
                _redact(
                    {
                        "event": "mcp_response",
                        "method": context.method,
                        "request_id": snapshot["mcp"].get("request_id"),
                        "session_id": snapshot["mcp"].get("session_id"),
                        "result_type": type(result).__name__,
                        "result": _jsonable(result),
                    }
                ),
                separators=(",", ":"),
                ensure_ascii=False,
            )
        )
        return result
