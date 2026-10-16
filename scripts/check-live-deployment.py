"""Smoke-test a deployed MCP server without loading production configuration."""

import argparse
import asyncio
import json
import sys
from urllib.parse import urlsplit

from fastmcp import Client


async def check(url: str, timeout: float) -> None:
    async with Client(url, timeout=timeout, init_timeout=timeout) as client:
        print("PASS: connected and initialized MCP", flush=True)
        tools = await client.list_tools()
        print(f"Total tools: {len(tools)}", flush=True)
        for tool in sorted(tools, key=lambda tool: tool.name):
            print(f"  - {tool.name}", flush=True)
            print("Input schema:", flush=True)
            print(json.dumps(tool.inputSchema, indent=2, ensure_ascii=False), flush=True)
            print("Output schema:", flush=True)
            if tool.outputSchema is None:
                print("  Not provided", flush=True)
            else:
                print(json.dumps(tool.outputSchema, indent=2, ensure_ascii=False), flush=True)
        if not any(tool.name == "list_supermarkets" for tool in tools):
            raise RuntimeError("tool discovery did not return 'list_supermarkets'")
        result = await client.call_tool(
            "list_supermarkets",
            {},
            meta={"openai/subject": "v1/deployment-smoke-check"},
        )
        supermarkets = result.data
        print("list_supermarkets result:", flush=True)
        print(json.dumps(supermarkets, indent=2, ensure_ascii=False), flush=True)
        if not isinstance(supermarkets, list) or not all(
            isinstance(store, dict)
            and isinstance(store.get("id"), str)
            and isinstance(store.get("name"), str)
            for store in supermarkets
        ):
            raise RuntimeError("list_supermarkets returned an unexpected response")
        print(f"PASS: list_supermarkets returned {len(supermarkets)} supermarket(s)", flush=True)
        if not any(tool.name == "get_current_discounts" for tool in tools):
            raise RuntimeError("tool discovery did not return 'get_current_discounts'")
        for store in supermarkets:
            arguments = {"supermarket_id": store["id"]}
            print(f"Calling get_current_discounts: {json.dumps(arguments)}", flush=True)
            result = await client.call_tool(
                "get_current_discounts",
                arguments,
                meta={"openai/subject": "v1/deployment-smoke-check"},
            )
            if not isinstance(result.data, dict):
                raise RuntimeError(
                    f"get_current_discounts returned an unexpected response for {store['id']}"
                )
            print("get_current_discounts result lengths:", flush=True)
            for key, value in result.data.items():
                length = len(value) if isinstance(value, (str, list, dict)) else "n/a"
                print(f"  {key}: {length}", flush=True)
            print(f"PASS: get_current_discounts completed for {store['id']}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public MCP URL, e.g. https://example.com/mcp")
    parser.add_argument(
        "--timeout", type=float, default=30, help="Overall timeout in seconds (default: 30)"
    )
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme not in {"http", "https"} or not url.hostname:
        parser.error("url must be an absolute HTTP or HTTPS URL")
    if not 0 < args.timeout < float("inf"):
        parser.error("--timeout must be a finite positive number")
    try:
        asyncio.run(asyncio.wait_for(check(args.url, args.timeout), args.timeout))
    except TimeoutError:
        print(f"FAIL: check timed out after {args.timeout:g}s", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("Deployment is responding correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
