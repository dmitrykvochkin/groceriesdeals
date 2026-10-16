"""Smoke-test a deployed MCP server without loading production configuration."""

import argparse
import asyncio
import sys
from urllib.parse import urlsplit

from fastmcp import Client


async def check(url: str, timeout: float) -> None:
    async with Client(url, timeout=timeout, init_timeout=timeout) as client:
        print("PASS: connected and initialized MCP", flush=True)
        tools = await client.list_tools()
        if not any(tool.name == "greet" for tool in tools):
            raise RuntimeError("tool discovery did not return 'greet'")
        print("PASS: discovered greet tool", flush=True)
        result = await client.call_tool(
            "greet",
            {"name": "deployment-smoke-check"},
            meta={"openai/subject": "v1/deployment-smoke-check"},
        )
        if result.data != "Hello, deployment-smoke-check!":
            raise RuntimeError("greet returned an unexpected response")
        print("PASS: greet returned the expected response", flush=True)


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
