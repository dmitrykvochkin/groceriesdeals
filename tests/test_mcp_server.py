import asyncio
import json
import logging
import unittest
import uuid

from fastmcp import Client
from fastmcp.exceptions import ToolError
from sqlmodel import Session, select

from groceriesdeals.config import get_settings
from groceriesdeals.db.models import User
from groceriesdeals.db.session import engine
from groceriesdeals.identity import derive_anonymous_key
from groceriesdeals.mcp_audit import _redact, logger
from groceriesdeals.mcp_server import mcp

_TEST_META = {"openai/subject": "v1/test-mcp-server-subject"}


class MCPServerTests(unittest.TestCase):
    def test_greet_tool(self) -> None:
        async def call_greet() -> str:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "greet",
                    {"name": "World"},
                    meta=_TEST_META,
                )
                return result.data

        with self.assertLogs(logger, level=logging.INFO):
            result = asyncio.run(call_greet())
        self.assertEqual(result, "Hello, World!")

    def test_audit_log_captures_client_request_session_and_response(self) -> None:
        async def call_greet() -> None:
            async with Client(mcp) as client:
                await client.call_tool(
                    "greet",
                    {"name": "World"},
                    meta=_TEST_META,
                )

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
        self.assertEqual(tool_call["mcp"]["message"]["arguments"], {"name": "World"})
        self.assertIsNotNone(tool_call["mcp"]["request_id"])
        self.assertIsNotNone(tool_call["mcp"]["session_id"])
        self.assertEqual(
            tool_call["client"]["implementation"],
            initialize["client"]["implementation"],
        )
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
        self.assertEqual(
            redacted["arguments"]["nested"]["password"], "[REDACTED]"
        )

    def test_tools_call_rejects_missing_subject(self) -> None:
        async def call_greet() -> None:
            async with Client(mcp) as client:
                await client.call_tool("greet", {"name": "World"})

        with self.assertRaises(ToolError) as ctx:
            asyncio.run(call_greet())
        self.assertIn("Anonymous subject required", str(ctx.exception))

    def test_tools_call_creates_and_reuses_user(self) -> None:
        subject = f"v1/user-tracking-{uuid.uuid4()}"
        secret = get_settings().anonymous_key_secret
        key = derive_anonymous_key(secret, subject)

        with Session(engine) as session:
            existing = session.exec(
                select(User).where(User.anonymous_key == key)
            ).first()
            if existing is not None:
                session.delete(existing)
                session.commit()

        async def call_greet() -> str:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "greet",
                    {"name": "World"},
                    meta={"openai/subject": subject},
                )
                return result.data

        with self.assertLogs(logger, level=logging.INFO):
            first = asyncio.run(call_greet())
            second = asyncio.run(call_greet())

        self.assertEqual(first, "Hello, World!")
        self.assertEqual(second, "Hello, World!")

        with Session(engine) as session:
            users = session.exec(select(User).where(User.anonymous_key == key)).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].tool_request_count, 2)


if __name__ == "__main__":
    unittest.main()
