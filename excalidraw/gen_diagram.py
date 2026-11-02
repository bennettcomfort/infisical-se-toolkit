#!/usr/bin/env python3
"""Generate an importable .excalidraw file from a simple YAML/JSON spec.

Spec:
  title: "My design"
  nodes: [{id, label, col, row, color?, w?, h?}]
  edges: [{from, to, label?}]
Colors: blue green orange red purple gray yellow
Usage: python gen_diagram.py spec.yaml out.excalidraw
"""
import json, random, sys, time, pathlib

COLORS = {"blue": "#a5d8ff", "green": "#b2f2bb", "orange": "#ffd8a8", "red": "#ffc9c9",
          "purple": "#d0bfff", "gray": "#e9ecef", "yellow": "#ffec99"}
CW, RH, BW, BH, X0, Y0 = 300, 170, 230, 90, 60, 120

def _id(): return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16))

def _base(t, x, y, w, h, **kw):
    e = {"id": _id(), "type": t, "x": x, "y": y, "width": w, "height": h, "angle": 0,
         "strokeColor": "#1e1e1e", "backgroundColor": "transparent", "fillStyle": "solid",
         "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100,
         "groupIds": [], "frameId": None, "roundness": None, "seed": random.randint(1, 2**31),
         "version": 1, "versionNonce": random.randint(1, 2**31), "isDeleted": False,
         "boundElements": [], "updated": int(time.time() * 1000), "link": None, "locked": False}
    e.update(kw); return e

def _text(s, x, y, w, h, size=16, container=None, align="center"):
    lines = str(s).split("\n")
    return _base("text", x, y, w, h, text=s, originalText=s, fontSize=size, fontFamily=1,
                 textAlign=align, verticalAlign="middle", containerId=container,
                 lineHeight=1.25, autoResize=True, baseline=size)

def load(path):
    p = pathlib.Path(path); raw = p.read_text()
    if p.suffix in (".yaml", ".yml"):
        import yaml; return yaml.safe_load(raw)
    return json.loads(raw)

def build(spec):
    els, pos = [], {}
    if spec.get("title"):
        els.append(_text(spec["title"], X0, 30, 900, 40, size=28, align="left"))
    for n in spec.get("nodes", []):
        w, h = n.get("w", BW), n.get("h", BH)
        x, y = X0 + n.get("col", 0) * CW, Y0 + n.get("row", 0) * RH
        r = _base("rectangle", x, y, w, h, backgroundColor=COLORS.get(n.get("color", "gray"), "#e9ecef"),
                  roundness={"type": 3})
        t = _text(n.get("label", n["id"]), x + 5, y + 5, w - 10, h - 10, container=r["id"])
        r["boundElements"].append({"type": "text", "id": t["id"]})
        els += [r, t]; pos[n["id"]] = r
    for e in spec.get("edges", []):
        a, b = pos.get(e["from"]), pos.get(e["to"])
        if not a or not b: raise SystemExit(f"edge references unknown node: {e}")
        ax, ay = a["x"] + a["width"] / 2, a["y"] + a["height"] / 2
        bx, by = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        # start/end at box edges
        def edge_pt(r, cx, cy, tx, ty):
            dx, dy = tx - cx, ty - cy
            if dx == 0 and dy == 0: return cx, cy
            sx = (r["width"] / 2) / abs(dx) if dx else 1e9
            sy = (r["height"] / 2) / abs(dy) if dy else 1e9
            s = min(sx, sy); return cx + dx * s, cy + dy * s
        sx_, sy_ = edge_pt(a, ax, ay, bx, by); ex, ey = edge_pt(b, bx, by, ax, ay)
        dash = "dashed" if e.get("dashed") else "solid"
        arr = _base("arrow", sx_, sy_, abs(ex - sx_), abs(ey - sy_), points=[[0, 0], [ex - sx_, ey - sy_]],
                    lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow",
                    startBinding={"elementId": a["id"], "focus": 0, "gap": 4},
                    endBinding={"elementId": b["id"], "focus": 0, "gap": 4},
                    strokeStyle=dash, roundness={"type": 2}, elbowed=False)
        a["boundElements"].append({"type": "arrow", "id": arr["id"]})
        b["boundElements"].append({"type": "arrow", "id": arr["id"]})
        els.append(arr)
        if e.get("label"):
            lt = _text(e["label"], sx_ + (ex - sx_) / 2 - 60, sy_ + (ey - sy_) / 2 - 12, 120, 24,
                       size=13, container=arr["id"])
            arr["boundElements"].append({"type": "text", "id": lt["id"]}); els.append(lt)
    for nt in spec.get("notes", []):
        els.append(_text(nt["text"], X0 + nt.get("col", 0) * CW, Y0 + nt.get("row", 0) * RH, 260, 60,
                         size=14, align="left"))
    return {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
            "elements": els, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}

def write(spec, out):
    doc = build(spec); pathlib.Path(out).write_text(json.dumps(doc, indent=1)); return out

if __name__ == "__main__":
    if len(sys.argv) != 3: print(__doc__); sys.exit(1)
    print("wrote", write(load(sys.argv[1]), sys.argv[2]))
