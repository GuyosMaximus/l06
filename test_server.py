"""Smoke test: start the gmail-calendar server over stdio, list tools, call list_events(1)."""
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parent
PRIVATE_DIR = r"C:\Users\Guy\.gemini\antigravity\scratch\gmail-calendar-agent"


async def main() -> int:
    env = {**os.environ, "GOOGLE_PRIVATE_DIR": PRIVATE_DIR}
    params = StdioServerParameters(
        command="uv",
        args=["--directory", str(PROJECT_DIR), "run", "server.py"],
        env=env,
    )
    print(f"GOOGLE_PRIVATE_DIR={PRIVATE_DIR}")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"Connected to server: {init.serverInfo.name}\n")

            tools = (await session.list_tools()).tools
            print(f"Tools ({len(tools)}):")
            for tool in tools:
                args = ", ".join(tool.inputSchema.get("properties", {}))
                summary = " ".join((tool.description or "").split())
                print(f"  - {tool.name}({args}): {summary}")

            print("\nCalling list_events(days_ahead=1) ...")
            result = await session.call_tool("list_events", {"days_ahead": 1})
            if result.isError:
                text = " ".join(c.text for c in result.content if hasattr(c, "text"))
                print(f"ERROR: {text}")
                return 1
            data = result.structuredContent or {}
            events = data.get("result", [])
            print(f"{len(events)} event(s) in the next 24 hours:")
            for ev in events:
                print(f"  - {ev['start']} -> {ev['end']}  {ev['title']}")
            if not events:
                print(json.dumps(data, ensure_ascii=False))
            return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
