"""Smoke test: spawns server over stdio, lists tools, calls both."""
import asyncio, sys, pathlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    p = StdioServerParameters(command=sys.executable, args=[str(pathlib.Path(__file__).parent / "server.py")])
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print("tools:", [t.name for t in (await s.list_tools()).tools])
            res = await s.call_tool("search_knowledge", {"query": "redis noeviction", "top_k": 1})
            print(res.content[0].text[:200])
            res = await s.call_tool("make_diagram", {"components": [
                {"id": "a", "label": "Infisical", "col": 0, "row": 0, "color": "green"},
                {"id": "b", "label": "Postgres", "col": 1, "row": 0, "color": "orange"}],
                "edges": [{"from": "a", "to": "b", "label": "SQL"}], "filename": "smoke.excalidraw"})
            print(res.content[0].text)
asyncio.run(main())
