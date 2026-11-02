#!/usr/bin/env python3
"""Minimal MCP stdio server for the Infisical self-hosting toolkit.
Tools: search_knowledge(query), make_diagram(components, edges, title, filename)
"""
import math
import pathlib
import re
import sys
try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

KIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT / "excalidraw"))
import gen_diagram  # noqa: E402

mcp = FastMCP("infisical-kit")

def _sections():
    text = (KIT / "KNOWLEDGE.md").read_text()
    parts = re.split(r"(?m)^## ", text)
    return [("## " + p).strip() for p in parts[1:]]

@mcp.tool()
def search_knowledge(query: str, top_k: int = 3) -> str:
    """Keyword-search KNOWLEDGE.md (Infisical self-hosting facts). Returns best-matching sections."""
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    secs = _sections()
    idf = {t: math.log((1 + len(secs)) / (1 + sum(t in x.lower() for x in secs))) + 1 for t in terms}
    scored = []
    for s in secs:
        low = s.lower()
        score = sum(idf[t] * (low.count(t) + 5 * (t in low.splitlines()[0])) for t in terms if t in low)
        score *= sum(t in low for t in terms)
        if score: scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return "\n\n---\n\n".join(s for _, s in scored[:top_k]) or "No match in KNOWLEDGE.md - treat as unverified."

@mcp.tool()
def make_diagram(components: list[dict], edges: list[dict] | None = None,
                 title: str = "Infisical design", filename: str = "live_design.excalidraw") -> str:
    """Write an .excalidraw file. components: [{id,label,col,row,color?}] (col 0-4,row 0-5;
    colors blue/green/orange/red/purple/gray). edges: [{from,to,label?,dashed?}]. Returns file path."""
    out_dir = KIT / "excalidraw" / "generated"; out_dir.mkdir(exist_ok=True)
    out = out_dir / pathlib.Path(filename).name
    gen_diagram.write({"title": title, "nodes": components, "edges": edges or []}, out)
    return f"Wrote {out.relative_to(KIT)} - drag onto excalidraw.com (or Menu > Open)."

if __name__ == "__main__":
    mcp.run()
