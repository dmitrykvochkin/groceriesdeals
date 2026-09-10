"""Sanitized PostHog analytics for FastMCP middleware messages."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext

from groceriesdeals.identity import derive_anonymous_key, extract_openai_subject

logger = logging.getLogger("groceriesdeals.mcp.posthog")

EVENT_NAME = "mcp message processed"
TOOL_CALL_EVENT_NAME = "mcp tool called"
_SESSION_STATE_ATTRIBUTE = "_groceriesdeals_posthog_state"
_SESSION_IDLE_TIMEOUT = timedelta(minutes=30)
_SESSION_MAX_DURATION = timedelta(hours=24)
_REDACTED = "[REDACTED]"
_TRUNCATED = "[TRUNCATED]"
_MAX_ARGUMENT_NODES = 200
_MAX_ARGUMENT_DEPTH = 5
_MAX_ARGUMENT_ITEMS = 25
_MAX_ARGUMENT_STRING_LENGTH = 256
_MAX_TOOL_CALL_LENGTH = 1024
_SENSITIVE_ARGUMENT_KEYS = {
    "api-key",
    "apikey",
    "authorization",
    "cookie",
    "credit-card",
    "credential",
    "email",
    "password",
    "phone",
    "private-key",
    "proxy-authorization",
    "secret",
    "set-cookie",
    "token",
}


class PostHogClient(Protocol):
    """The subset of the PostHog client used by the MCP server."""

    def capture(
        self,
        event: str,
        *,
        distinct_id: str,
        properties: dict[str, Any],
        timestamp: datetime,
    ) -> Any: ...

    def alias(self, *, previous_id: str, distinct_id: str) -> Any: ...

    def shutdown(self) -> Any: ...


def uuid7(timestamp: datetime | None = None) -> str:
    """Return a UUIDv7 whose timestamp is at or before its first event."""
    instant = timestamp or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    unix_ts_ms = int(instant.timestamp() * 1000) & ((1 << 48) - 1)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)

    value = unix_ts_ms << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return str(uuid.UUID(int=value))


@dataclass
class SessionTrackingState:
    """Identity and activity-window state owned by one FastMCP session."""

    anonymous_distinct_id: str
    distinct_id: str
    posthog_session_id: str
    session_started_at: datetime
    last_activity_at: datetime
    user_distinct_id: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @classmethod
    def create(cls, timestamp: datetime) -> SessionTrackingState:
        anonymous_id = f"mcp-anonymous:{uuid.uuid4()}"
        return cls(
            anonymous_distinct_id=anonymous_id,
            distinct_id=anonymous_id,
            posthog_session_id=uuid7(timestamp),
            session_started_at=timestamp,
            last_activity_at=timestamp,
        )

    def touch(self, timestamp: datetime) -> None:
        """Rotate the PostHog activity session when its window has expired."""
        idle_for = timestamp - self.last_activity_at
        age = timestamp - self.session_started_at
        if idle_for >= _SESSION_IDLE_TIMEOUT or age >= _SESSION_MAX_DURATION:
            self.posthog_session_id = uuid7(timestamp)
            self.session_started_at = timestamp
        if timestamp > self.last_activity_at:
            self.last_activity_at = timestamp


class PostHogTrackingMiddleware(Middleware):
    """Capture one sanitized event around each public middleware message."""

    def __init__(self, anonymous_key_secret: str) -> None:
        self._anonymous_key_secret = anonymous_key_secret

    async def on_message(
        self,
        context: MiddlewareContext[Any],
        call_next: Any,
    ) -> Any:
        started = time.monotonic()
        timestamp = _utc(context.timestamp)
        client = _posthog_client(context)
        state = _session_state(context, timestamp)

        try:
            distinct_id, posthog_session_id = await self._prepare_identity(
                context, state, client, timestamp
            )
            result = await call_next(context)
        except Exception as exc:
            self._capture(
                client,
                context,
                distinct_id=state.distinct_id,
                posthog_session_id=state.posthog_session_id,
                timestamp=timestamp,
                duration_ms=(time.monotonic() - started) * 1000,
                error=exc,
            )
            raise

        self._capture(
            client,
            context,
            distinct_id=distinct_id,
            posthog_session_id=posthog_session_id,
            timestamp=timestamp,
            duration_ms=(time.monotonic() - started) * 1000,
        )
        return result

    async def _prepare_identity(
        self,
        context: MiddlewareContext[Any],
        state: SessionTrackingState,
        client: PostHogClient,
        timestamp: datetime,
    ) -> tuple[str, str]:
        async with state.lock:
            state.touch(timestamp)
            subject = _request_subject(context)
            if subject is None:
                if context.method == "tools/call":
                    raise ToolError("Anonymous subject required")
                return state.distinct_id, state.posthog_session_id

            user_id = derive_anonymous_key(self._anonymous_key_secret, subject)
            if state.user_distinct_id is not None and state.user_distinct_id != user_id:
                raise ToolError("Anonymous subject changed within MCP session")

            if state.user_distinct_id is None:
                _alias_fail_open(
                    client,
                    previous_id=state.anonymous_distinct_id,
                    distinct_id=user_id,
                )
                state.user_distinct_id = user_id
                state.distinct_id = user_id

            return state.distinct_id, state.posthog_session_id

    def _capture(
        self,
        client: PostHogClient,
        context: MiddlewareContext[Any],
        *,
        distinct_id: str,
        posthog_session_id: str,
        timestamp: datetime,
        duration_ms: float,
        error: Exception | None = None,
    ) -> None:
        properties = _event_properties(
            context,
            posthog_session_id=posthog_session_id,
            duration_ms=duration_ms,
            error=error,
        )
        if not distinct_id.startswith("mcp-anonymous:"):
            properties["$set_once"] = {"identity_source": "openai_subject_hmac"}
            properties["identity_status"] = "stable_user"
        else:
            properties["identity_status"] = "session_anonymous"
        try:
            client.capture(
                (
                    TOOL_CALL_EVENT_NAME
                    if context.method == "tools/call"
                    else EVENT_NAME
                ),
                distinct_id=distinct_id,
                properties=properties,
                timestamp=timestamp,
            )
        except Exception:
            logger.warning("PostHog event capture failed", exc_info=True)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _posthog_client(context: MiddlewareContext[Any]) -> PostHogClient:
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None:
        raise RuntimeError("FastMCP context unavailable for PostHog tracking")
    client = fastmcp_context.lifespan_context.get("posthog_client")
    if client is None:
        raise RuntimeError("PostHog client unavailable in server lifespan")
    return client


def _session_state(
    context: MiddlewareContext[Any], timestamp: datetime
) -> SessionTrackingState:
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None:
        return SessionTrackingState.create(timestamp)
    try:
        session = fastmcp_context.session
    except RuntimeError:
        return SessionTrackingState.create(timestamp)

    state = getattr(session, _SESSION_STATE_ATTRIBUTE, None)
    if state is None:
        state = SessionTrackingState.create(timestamp)
        setattr(session, _SESSION_STATE_ATTRIBUTE, state)
    return state


def _request_meta(context: MiddlewareContext[Any]) -> Any:
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None or fastmcp_context.request_context is None:
        return None
    return fastmcp_context.request_context.meta


def _request_subject(context: MiddlewareContext[Any]) -> str | None:
    """Resolve the subject without ever adding its raw value to analytics."""
    meta_subject = extract_openai_subject(_request_meta(context))
    header_subject = _http_subject()
    if (
        meta_subject is not None
        and header_subject is not None
        and meta_subject != header_subject
    ):
        raise ToolError("Anonymous subject sources disagree")
    return meta_subject or header_subject


def _http_subject() -> str | None:
    try:
        request = get_http_request()
    except (LookupError, RuntimeError):
        return None
    value = request.headers.get("x-openai-subject")
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _alias_fail_open(
    client: PostHogClient, *, previous_id: str, distinct_id: str
) -> None:
    try:
        client.alias(previous_id=previous_id, distinct_id=distinct_id)
    except Exception:
        logger.warning("PostHog identity alias failed", exc_info=True)


def _event_properties(
    context: MiddlewareContext[Any],
    *,
    posthog_session_id: str,
    duration_ms: float,
    error: Exception | None,
) -> dict[str, Any]:
    fastmcp_context = context.fastmcp_context
    client_name, client_version, protocol_version = _client_details(context)
    properties: dict[str, Any] = {
        "$session_id": posthog_session_id,
        "mcp_method": context.method,
        "mcp_source": context.source,
        "mcp_message_kind": context.type,
        "mcp_message_type": type(context.message).__name__,
        "mcp_transport": (
            fastmcp_context.transport if fastmcp_context is not None else None
        ),
        "mcp_session_id": _mcp_session_id(context),
        "mcp_request_id": _mcp_request_id(context),
        "client_name": client_name,
        "client_version": client_version,
        "protocol_version": protocol_version,
        "outcome": "error" if error is not None else "success",
        "duration_ms": round(duration_ms, 3),
    }
    if error is not None:
        properties["error_type"] = type(error).__name__

    if context.method == "tools/call":
        tool_name = getattr(context.message, "name", None)
        tool_arguments = _sanitize_tool_arguments(
            getattr(context.message, "arguments", None)
        )
        properties["tool_name"] = tool_name
        properties["tool_parameters"] = tool_arguments
        properties["tool_parameters_json"] = _bounded_json(tool_arguments)
        properties["tool_call"] = _tool_call_summary(tool_name, tool_arguments)
    elif context.method == "prompts/get":
        properties["prompt_name"] = getattr(context.message, "name", None)

    return {key: value for key, value in properties.items() if value is not None}


def _is_sensitive_argument_key(key: object) -> bool:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", str(key))
    normalized = normalized.lower().replace("_", "-")
    parts = set(normalized.split("-"))
    return (
        normalized in _SENSITIVE_ARGUMENT_KEYS
        or bool(
            parts
            & {
                "cvc",
                "cvv",
                "credential",
                "email",
                "password",
                "phone",
                "secret",
                "token",
            }
        )
        or {"credit", "card"}.issubset(parts)
        or {"private", "key"}.issubset(parts)
        or normalized.endswith("-private-key")
    )


class _ArgumentSanitizer:
    def __init__(self) -> None:
        self.remaining = _MAX_ARGUMENT_NODES

    def sanitize(self, value: Any, depth: int = 0) -> Any:
        if self.remaining <= 0 or depth >= _MAX_ARGUMENT_DEPTH:
            return _TRUNCATED
        self.remaining -= 1

        if isinstance(value, Mapping):
            sanitized: dict[str, Any] = {}
            items = list(value.items())
            for key, item in items[:_MAX_ARGUMENT_ITEMS]:
                safe_key = str(key)[:_MAX_ARGUMENT_STRING_LENGTH]
                sanitized[safe_key] = (
                    _REDACTED
                    if _is_sensitive_argument_key(key)
                    else self.sanitize(item, depth + 1)
                )
            if len(items) > _MAX_ARGUMENT_ITEMS:
                sanitized[_TRUNCATED] = len(items) - _MAX_ARGUMENT_ITEMS
            return sanitized

        if isinstance(value, (list, tuple)):
            items = list(value)
            sanitized_items = [
                self.sanitize(item, depth + 1)
                for item in items[:_MAX_ARGUMENT_ITEMS]
            ]
            if len(items) > _MAX_ARGUMENT_ITEMS:
                sanitized_items.append(_TRUNCATED)
            return sanitized_items

        if isinstance(value, str):
            if len(value) <= _MAX_ARGUMENT_STRING_LENGTH:
                return value
            return value[:_MAX_ARGUMENT_STRING_LENGTH] + _TRUNCATED
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else str(value)
        return f"[{type(value).__name__}]"


def _sanitize_tool_arguments(arguments: Any) -> Any:
    return _ArgumentSanitizer().sanitize(arguments)


def _tool_call_summary(tool_name: Any, tool_arguments: Any) -> str:
    return _bounded_json(
        {"arguments": tool_arguments, "tool": tool_name},
    )


def _bounded_json(value: Any) -> str:
    summary = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    if len(summary) <= _MAX_TOOL_CALL_LENGTH:
        return summary
    return summary[:_MAX_TOOL_CALL_LENGTH] + _TRUNCATED


def _mcp_session_id(context: MiddlewareContext[Any]) -> str | None:
    # Reading FastMCP's session_id during initialize creates and caches a fallback
    # before Streamable HTTP assigns the actual Mcp-Session-Id.
    if context.method == "initialize":
        return None
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None or fastmcp_context.request_context is None:
        return None
    try:
        return fastmcp_context.session_id
    except RuntimeError:
        return None


def _mcp_request_id(context: MiddlewareContext[Any]) -> str | None:
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None or fastmcp_context.request_context is None:
        return None
    try:
        return fastmcp_context.request_id
    except RuntimeError:
        return None


def _client_details(
    context: MiddlewareContext[Any],
) -> tuple[str | None, str | None, str | None]:
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None:
        return None, None, None
    try:
        params = fastmcp_context.session.client_params
    except RuntimeError:
        params = None
    if params is None:
        params = getattr(context.message, "params", None)

    info = getattr(params, "clientInfo", None)
    return (
        getattr(info, "name", None),
        getattr(info, "version", None),
        getattr(params, "protocolVersion", None),
    )
