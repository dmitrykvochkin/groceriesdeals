import asyncio
import contextlib
import io
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class LiveDeploymentScriptTests(unittest.TestCase):
    def test_lists_supermarkets_without_greet_and_prints_json(self):
        check = runpy.run_path(str(
            Path(__file__).resolve().parents[1] / "scripts/check-live-deployment.py"
        ))["check"]
        calls = []

        class Client:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def list_tools(self):
                return [SimpleNamespace(
                    name=name,
                    inputSchema={"type": "object", "properties": {}},
                    outputSchema={"type": "object", "title": "DiscountsSchema"}
                    if name == "get_current_discounts" else None,
                ) for name in (
                    "list_supermarkets", "get_current_discounts"
                )]

            async def call_tool(self, name, arguments, **kwargs):
                calls.append((name, arguments))
                if name == "list_supermarkets":
                    return SimpleNamespace(data=[
                        {"id": "picnic", "name": "Picnic"},
                        {"id": "test-store", "name": "Test store"},
                    ])
                return SimpleNamespace(data={
                    "supermarket_id": arguments["supermarket_id"],
                    "deals": [{"description": "Do not print this deal"}],
                    "metadata": {"one": 1},
                    "count": 1,
                    "available": True,
                    "next": None,
                })

        output = io.StringIO()
        with patch.dict(check.__globals__, Client=Client), contextlib.redirect_stdout(output):
            asyncio.run(check("https://example.com/mcp", 30))
        self.assertEqual(calls, [
            ("list_supermarkets", {}),
            ("get_current_discounts", {"supermarket_id": "picnic"}),
            ("get_current_discounts", {"supermarket_id": "test-store"}),
        ])
        self.assertIn("Total tools: 2", output.getvalue())
        self.assertEqual(output.getvalue().count("Input schema:"), 2)
        self.assertEqual(output.getvalue().count("Output schema:"), 2)
        self.assertIn('"properties": {}', output.getvalue())
        self.assertIn('"title": "DiscountsSchema"', output.getvalue())
        self.assertIn("  Not provided", output.getvalue())
        self.assertIn('"supermarket_id": "picnic"', output.getvalue())
        self.assertIn('"supermarket_id": "test-store"', output.getvalue())
        self.assertIn('  deals: 1', output.getvalue())
        self.assertIn('  supermarket_id: 6', output.getvalue())
        self.assertIn('  metadata: 1', output.getvalue())
        for key in ("count", "available", "next"):
            self.assertIn(f"  {key}: n/a", output.getvalue())
        self.assertNotIn("Do not print this deal", output.getvalue())
        self.assertIn('"id": "picnic"', output.getvalue())
        self.assertIn('"name": "Picnic"', output.getvalue())
