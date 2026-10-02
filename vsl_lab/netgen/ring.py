"""Single-lane ring road of a given circumference (Stern et al. 2018: 260 m; Flow: 220-270 m).

Four nodes on a circle; each edge carries an arc-shaped polyline. Internal links are disabled so the lap
length equals the sum of the four edge lengths (read back from the net file and used everywhere).
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

from vsl_lab.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

EDGES = ("bottom", "right", "top", "left")
SPEED_LIMIT = 30.0
VERSION = 1


def build(circumference: float) -> Path:
    spec = {"name": "ring", "L": round(float(circumference), 2), "v": VERSION, "speed": SPEED_LIMIT}
    h = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]
    d = NET_CACHE / f"ring_{int(round(circumference))}_{h}"
    net = d / "ring.net.xml"
    if net.exists():
        return d
    d.mkdir(parents=True, exist_ok=True)
    r = circumference / (2 * math.pi)
    angles = [-math.pi / 2, 0.0, math.pi / 2, math.pi]          # bottom, right, top, left nodes
    names = ["n_bottom", "n_right", "n_top", "n_left"]
    nodes = ["<nodes>"]
    for n, a in zip(names, angles):
        nodes.append(f'  <node id="{n}" x="{r * math.cos(a):.4f}" y="{r * math.sin(a):.4f}" type="priority"/>')
    nodes.append("</nodes>")
    (d / "ring.nod.xml").write_text("\n".join(nodes) + "\n")
    edges = ["<edges>"]
    for i, eid in enumerate(EDGES):
        a0, a1 = angles[i], angles[(i + 1) % 4]
        if a1 <= a0:
            a1 += 2 * math.pi
        pts = []
        for k in range(0, 41):
            a = a0 + (a1 - a0) * k / 40
            pts.append(f"{r * math.cos(a):.4f},{r * math.sin(a):.4f}")
        edges.append(f'  <edge id="{eid}" from="{names[i]}" to="{names[(i + 1) % 4]}" numLanes="1" '
                     f'speed="{SPEED_LIMIT}" shape="{" ".join(pts)}"/>')
    edges.append("</edges>")
    (d / "ring.edg.xml").write_text("\n".join(edges) + "\n")
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "ring.nod.xml"), "--edge-files", str(d / "ring.edg.xml"),
           "--no-internal-links", "true", "--no-turnarounds", "true", "-o", str(net), "--log", str(d / "netconvert.log")]
    res = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if res.returncode != 0 or not net.exists():
        raise RuntimeError(res.stderr[-1500:])
    (d / "spec.json").write_text(json.dumps(spec))
    return d


def edge_lengths(net_file: Path) -> dict:
    import xml.etree.ElementTree as ET
    out = {}
    for e in ET.parse(net_file).getroot().iter("edge"):
        if e.get("id") in EDGES:
            out[e.get("id")] = float(e.find("lane").get("length"))
    return out
