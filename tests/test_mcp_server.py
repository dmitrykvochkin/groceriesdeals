from __future__ import annotations

import asyncio
import json
import logging
import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

os.environ.setdefault("ANONYMOUS_KEY_SECRET", "test-anonymous-key-secret")
os.environ.setdefault("POSTHOG_PROJECT_TOKEN", "test-project-token")
os.environ.setdefault("POSTHOG_HOST", "https://eu.i.posthog.com")

from fastmcp import Client
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import MiddlewareContext

from groceriesdeals.identity import derive_anonymous_key
from groceriesdeals.mcp_audit import _redact, logger
from groceriesdeals.mcp_posthog import (
    EVENT_NAME,
    TOOL_CALL_EVENT_NAME,
    PostHogTrackingMiddleware,
)
from groceriesdeals.mcp_server import create_mcp

_SECRET = "test-anonymous-key-secret"
_TEST_META = {"openai/subject": "v1/test-mcp-server-subject"}


class RecordingPostHogClient:
    def __init__(self, *, fail_capture: bool = False, fail_alias: bool = False):
        self.events: list[dict[str, Any]] = []
        self.aliases: list[dict[str, str]] = []
        self.shutdown_count = 0
        self.fail_capture = fail_capture
        self.fail_alias = fail_alias

    def capture(
        self,
        event: str,
        *,
        distinct_id: str,
        properties: dict[str, Any],
        timestamp: datetime,
    ) -> None:
        if self.fail_capture:
            raise RuntimeError("capture failed")
        self.events.append(
            {
                "event": event,
                "distinct_id": distinct_id,
                "properties": properties,
                "timestamp": timestamp,
            }
        )

    def alias(self, *, previous_id: str, distinct_id: str) -> None:
        if self.fail_alias:
            raise RuntimeError("alias failed")
        self.aliases.append(
            {"previous_id": previous_id, "distinct_id": distinct_id}
        )

    def shutdown(self) -> None:
        self.shutdown_count += 1


def test_server(recording: RecordingPostHogClient):
    server = create_mcp(lambda: recording, anonymous_key_secret=_SECRET)

    @server.tool
    def explode() -> str:
        raise RuntimeError("private failure detail")

    @server.resource("test://item")
    def item() -> str:
        return "resource payload"

    @server.prompt
    def welcome(name: str) -> str:
        return f"Welcome, {name}"

    return server


class MCPServerTests(unittest.TestCase):
    def test_greet_tool(self) -> None:
        recording = RecordingPostHogClient()

        async def call_greet() -> str:
            async with Client(test_server(recording)) as client:
                result = await client.call_tool(
                    "greet", {"name": "World"}, meta=_TEST_META
                )
                return result.data

        with self.assertLogs(logger, level=logging.INFO):
            result = asyncio.run(call_greet())
        self.assertEqual(result, "Hello, World!")
        self.assertEqual(recording.shutdown_count, 1)

    def test_audit_log_captures_client_request_session_and_response(self) -> None:
        recording = RecordingPostHogClient()

        async def call_greet() -> None:
            async with Client(test_server(recording)) as client:
                await client.call_tool("greet", {"name": "World"}, meta=_TEST_META)

        with self.assertLogs(logger, level=logging.INFO) as captured:
            asyncio.run(call_greet())

        records = [json.loads(line.split(":", 2)[2]) for line in captured.output]
        initialize = next(
            record
            for record in records
            if record["event"] == "mcp_request"
            and record["mcp"]["method"] == "initialize"
        )
        tool_call = next(
            record
            for record in records
            if record["event"] == "mcp_request"
            and record["mcp"]["method"] == "tools/call"
        )
        tool_response = next(
            record
            for record in records
            if record["event"] == "mcp_response"
            and record["method"] == "tools/call"
        )

        self.assertEqual(initialize["client"]["implementation"]["name"], "mcp")
        self.assertEqual(tool_call["mcp"]["message"]["name"], "greet")
        self.assertIsNotNone(tool_call["mcp"]["session_id"])
        self.assertEqual(tool_response["session_id"], tool_call["mcp"]["session_id"])

    def test_audit_log_redacts_sensitive_tool_arguments(self) -> None:
        redacted = _redact(
            {
                "arguments": {
                    "name": "World",
                    "api_token": "do-not-log",
                    "nested": {"password": "also-do-not-log"},
                }
            }
        )

        self.assertEqual(redacted["arguments"]["name"], "World")
        self.assertEqual(redacted["arguments"]["api_token"], "[REDACTED]")
        self.assertEqual(redacted["arguments"]["nested"]["password"], "[REDACTED]")

    def test_all_supported_traffic_emits_sanitized_events(self) -> None:
        recording = RecordingPostHogClient()
        subject = "v1/metadata-only-user"

        async def exercise() -> None:
            async with Client(test_server(recording)) as client:
                await client.list_tools()
                await client.list_resources()
                await client.read_resource("test://item")
                await client.list_prompts()
                await client.get_prompt("welcome", {"name": "Private Name"})
                await client.call_tool(
                    "greet",
                    {"name": "Sensitive Tool Value"},
                    meta={"openai/subject": subject},
                )

        with self.assertLogs(logger, level=logging.INFO):
            asyncio.run(exercise())

        methods = {event["properties"]["mcp_method"] for event in recording.events}
        self.assertTrue(
            {
                "initialize",
                "tools/list",
                "resources/list",
                "resources/read",
                "prompts/list",
                "prompts/get",
                "tools/call",
            }.issubset(methods)
        )
        self.assertTrue(
            all(
                event["event"]
                == (
                    TOOL_CALL_EVENT_NAME
                    if event["properties"]["mcp_method"] == "tools/call"
                    else EVENT_NAME
                )
                for event in recording.events
            )
        )
        serialized = json.dumps(recording.events, default=str)
        self.assertNotIn(subject, serialized)
        self.assertIn("Sensitive Tool Value", serialized)
        self.assertNotIn("Private Name", serialized)
        self.assertNotIn("resource payload", serialized)

    def test_generic_middleware_captures_server_notification_metadata(self) -> None:
        recording = RecordingPostHogClient()
        session = SimpleNamespace(client_params=None)
        fastmcp_context = SimpleNamespace(
            lifespan_context={"posthog_client": recording},
            session=session,
            request_context=None,
            transport="stdio",
        )
        context = MiddlewareContext(
            message=SimpleNamespace(),
            source="server",
            type="notification",
            method="notifications/resources/list_changed",
            fastmcp_context=fastmcp_context,
        )

        async def exercise() -> None:
            middleware = PostHogTrackingMiddleware(_SECRET)
            await middleware.on_message(context, lambda _context: asyncio.sleep(0))

        asyncio.run(exercise())

        self.assertEqual(len(recording.events), 1)
        properties = recording.events[0]["properties"]
        self.assertEqual(properties["mcp_source"], "server")
        self.assertEqual(properties["mcp_message_kind"], "notification")
        self.assertEqual(
            properties["mcp_method"], "notifications/resources/list_changed"
        )

    def test_subject_header_identifies_initialization_across_connections(self) -> None:
        recording = RecordingPostHogClient()
        subject = "v1/header-user"
        expected_user = derive_anonymous_key(_SECRET, subject)

        async def initialize_once() -> None:
            session = SimpleNamespace(client_params=None)
            fastmcp_context = SimpleNamespace(
                lifespan_context={"posthog_client": recording},
                session=session,
                request_context=None,
                transport="streamable-http",
            )
            context = MiddlewareContext(
                message=SimpleNamespace(params=None),
                source="client",
                type="request",
                method="initialize",
                fastmcp_context=fastmcp_context,
            )
            middleware = PostHogTrackingMiddleware(_SECRET)
            await middleware.on_message(context, lambda _context: asyncio.sleep(0))

        request = SimpleNamespace(headers={"x-openai-subject": subject})
        with patch(
            "groceriesdeals.mcp_posthog.get_http_request", return_value=request
        ):
            asyncio.run(initialize_once())
            asyncio.run(initialize_once())

        self.assertEqual(
            [event["distinct_id"] for event in recording.events],
            [expected_user, expected_user],
        )
        self.assertTrue(
            all(
                event["properties"]["identity_status"] == "stable_user"
                for event in recording.events
            )
        )
        self.assertNotIn(subject, json.dumps(recording.events, default=str))

    def test_subject_header_and_metadata_must_agree(self) -> None:
        recording = RecordingPostHogClient()
        context = MiddlewareContext(
            message=SimpleNamespace(name="greet", arguments={}),
            source="client",
            type="request",
            method="tools/call",
            fastmcp_context=SimpleNamespace(
                lifespan_context={"posthog_client": recording},
                session=SimpleNamespace(client_params=None),
                request_context=SimpleNamespace(
                    meta={"openai/subject": "v1/metadata-user"}
                ),
                transport="streamable-http",
                request_id="1",
                session_id="session-1",
            ),
        )

        async def exercise() -> None:
            middleware = PostHogTrackingMiddleware(_SECRET)
            await middleware.on_message(context, lambda _context: asyncio.sleep(0))

        request = SimpleNamespace(
            headers={"x-openai-subject": "v1/different-header-user"}
        )
        with patch(
            "groceriesdeals.mcp_posthog.get_http_request", return_value=request
        ):
            with self.assertRaises(ToolError) as raised:
                asyncio.run(exercise())

        self.assertIn("sources disagree", str(raised.exception))
        serialized = json.dumps(recording.events, default=str)
        self.assertNotIn("v1/metadata-user", serialized)
        self.assertNotIn("v1/different-header-user", serialized)

    def test_tool_arguments_are_bounded_and_redacted_for_analysis(self) -> None:
        recording = RecordingPostHogClient()
        context = MiddlewareContext(
            message=SimpleNamespace(
                name="greet",
                arguments={
                    "name": "Dmitry",
                    "api_token": "never-send-this",
                    "accessToken": "camel-case-secret",
                    "nested": {"password": "also-secret", "count": 3},
                    "long": "x" * 1000,
                },
            ),
            source="client",
            type="request",
            method="tools/call",
            fastmcp_context=SimpleNamespace(
                lifespan_context={"posthog_client": recording},
                session=SimpleNamespace(client_params=None),
                request_context=SimpleNamespace(
                    meta={"openai/subject": "v1/argument-user"}
                ),
                transport="stdio",
                request_id="1",
                session_id="session-1",
            ),
        )

        async def exercise() -> None:
            middleware = PostHogTrackingMiddleware(_SECRET)
            await middleware.on_message(context, lambda _context: asyncio.sleep(0))

        asyncio.run(exercise())

        self.assertEqual(recording.events[0]["event"], TOOL_CALL_EVENT_NAME)
        arguments = recording.events[0]["properties"]["tool_parameters"]
        parameters_json = recording.events[0]["properties"]["tool_parameters_json"]
        tool_call = recording.events[0]["properties"]["tool_call"]
        self.assertEqual(arguments["name"], "Dmitry")
        self.assertEqual(arguments["api_token"], "[REDACTED]")
        self.assertEqual(arguments["accessToken"], "[REDACTED]")
        self.assertEqual(arguments["nested"]["password"], "[REDACTED]")
        self.assertEqual(arguments["nested"]["count"], 3)
        self.assertLess(len(arguments["long"]), 1000)
        self.assertIn('"tool":"greet"', tool_call)
        self.assertIn('"name":"Dmitry"', tool_call)
        self.assertIn('"name":"Dmitry"', parameters_json)
        self.assertNotIn("never-send-this", json.dumps(recording.events, default=str))
        self.assertNotIn("camel-case-secret", json.dumps(recording.events, default=str))

    def test_pre_tool_identity_is_aliased_once_and_session_is_reused(self) -> None:
        recording = RecordingPostHogClient()
        subject = "v1/stable-user"
        expected_user = derive_anonymous_key(_SECRET, subject)

        async def exercise() -> None:
            async with Client(test_server(recording)) as client:
                await client.list_tools()
                await client.call_tool(
                    "greet", {"name": "One"}, meta={"openai/subject": subject}
                )
                await client.call_tool(
                    "greet", {"name": "Two"}, meta={"openai/subject": subject}
                )

        with self.assertLogs(logger, level=logging.INFO):
            asyncio.run(exercise())

        self.assertEqual(len(recording.aliases), 1)
        self.assertTrue(
            recording.aliases[0]["previous_id"].startswith("mcp-anonymous:")
        )
        self.assertEqual(recording.aliases[0]["distinct_id"], expected_user)

        tool_events = [
            event
            for event in recording.events
            if event["properties"]["mcp_method"] == "tools/call"
        ]
        self.assertEqual(
            [event["distinct_id"] for event in tool_events], [expected_user] * 2
        )
        self.assertEqual(
            len({event["properties"]["$session_id"] for event in recording.events}), 1
        )

    def test_same_subject_uses_same_user_across_mcp_connections(self) -> None:
        recording = RecordingPostHogClient()
        subject = "v1/repeat-user"
        expected_user = derive_anonymous_key(_SECRET, subject)

        async def call_once(name: str) -> None:
            async with Client(test_server(recording)) as client:
                await client.call_tool(
                    "greet", {"name": name}, meta={"openai/subject": subject}
                )

        with self.assertLogs(logger, level=logging.INFO):
            asyncio.run(call_once("First"))
            asyncio.run(call_once("Second"))

        tool_events = [
            event
            for event in recording.events
            if event["properties"].get("mcp_method") == "tools/call"
        ]
        self.assertEqual(len(tool_events), 2)
        self.assertEqual(
            [event["distinct_id"] for event in tool_events],
            [expected_user, expected_user],
        )
        self.assertEqual(
            [event["properties"]["tool_name"] for event in tool_events],
            ["greet", "greet"],
        )
        self.assertEqual(
            [
                event["properties"]["tool_parameters"]["name"]
                for event in tool_events
            ],
            ["First", "Second"],
        )

    def test_tools_call_rejects_missing_subject_and_tracks_failure(self) -> None:
        recording = RecordingPostHogClient()

        async def call_greet() -> None:
            async with Client(test_server(recording)) as client:
                await client.call_tool("greet", {"name": "World"})

        with self.assertRaises(ToolError) as ctx:
            asyncio.run(call_greet())
        self.assertIn("Anonymous subject required", str(ctx.exception))
        failed = next(
            event
            for event in recording.events
            if event["properties"].get("error_type") == "ToolError"
        )
        self.assertEqual(failed["properties"]["outcome"], "error")
        self.assertTrue(failed["distinct_id"].startswith("mcp-anonymous:"))

    def test_tools_call_rejects_subject_change(self) -> None:
        recording = RecordingPostHogClient()

        async def exercise() -> None:
            async with Client(test_server(recording)) as client:
                await client.call_tool(
                    "greet", {"name": "One"}, meta={"openai/subject": "v1/user-a"}
                )
                await client.call_tool(
                    "greet", {"name": "Two"}, meta={"openai/subject": "v1/user-b"}
                )

        with self.assertRaises(ToolError) as ctx:
            asyncio.run(exercise())
        self.assertIn("changed within MCP session", str(ctx.exception))
        self.assertEqual(len(recording.aliases), 1)

    def test_tool_failure_is_captured_without_error_message(self) -> None:
        recording = RecordingPostHogClient()
        subject = "v1/failing-tool-user"

        async def call_tool() -> None:
            async with Client(test_server(recording)) as client:
                await client.call_tool(
                    "explode", {}, meta={"openai/subject": subject}
                )

        with self.assertRaises(ToolError):
            asyncio.run(call_tool())

        failed = next(
            event
            for event in recording.events
            if event["properties"].get("tool_name") == "explode"
        )
        self.assertEqual(failed["properties"]["outcome"], "error")
        self.assertEqual(failed["properties"]["error_type"], "ToolError")
        self.assertNotIn("private failure detail", json.dumps(failed, default=str))

    def test_posthog_failures_do_not_break_tool_calls(self) -> None:
        recording = RecordingPostHogClient(fail_capture=True, fail_alias=True)

        async def call_greet() -> str:
            async with Client(test_server(recording)) as client:
                result = await client.call_tool(
                    "greet", {"name": "World"}, meta=_TEST_META
                )
                return result.data

        result = asyncio.run(call_greet())

        self.assertEqual(result, "Hello, World!")
        self.assertEqual(recording.shutdown_count, 1)


if __name__ == "__main__":
    unittest.main()
