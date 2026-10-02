"""BN4: the Flow / Vinitsky et al. (2018) two-stage zipper bottleneck, rebuilt for SUMO 1.27.

Geometry is copied from the public Flow code (flow/networks/bottleneck.py):
nodes at x = 0, 100, 410, 550 (zipper), 830 (zipper), 985 m;
edges "1"..."5" with 4, 4, 4, 2, 1 lanes (scaling = 1); speed limit 23 m/s;
lanes merge 4 -> 2 (lane i -> i // 2) and 2 -> 1.
Node "3" carries a traffic light (Flow's "light" node) used only by the metering baseline;
all other controllers hold it at all-green.

The network is generated once per spec hash into NET_CACHE and is read-only afterwards.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from vsl_lab.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

SPEC = {
    "name": "BN4",
    "speed": 23.0,
    "nodes": [("1", 0.0, "priority"), ("2", 100.0, "priority"), ("3", 410.0, "traffic_light"),
              ("4", 550.0, "zipper"), ("5", 830.0, "zipper"), ("6", 985.0, "priority")],
    "edges": [("1", "1", "2", 4), ("2", "2", "3", 4), ("3", "3", "4", 4), ("4", "4", "5", 2), ("5", "5", "6", 1)],
    "zipper_radius": 20.0,
    # E1 loops: exit of the network (edge 5) and entry to the first merge (end of edge 3, per lane)
    "exit_loop_pos_from_end": 15.0,
    "merge_loop_pos_from_end": 10.0,
    "loop_period_s": 20.0,  # Vinitsky reward window
    "version": 2,  # v2: all-green TLS program for node 3
}

EDGE_LANES = {e[0]: e[3] for e in SPEC["edges"]}


def spec_hash(spec: dict = SPEC) -> str:
    return hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]


def _write_plain(d: Path, spec: dict) -> None:
    nodes = ["<nodes>"]
    for nid, x, ntype in spec["nodes"]:
        extra = f' radius="{spec["zipper_radius"]}"' if ntype == "zipper" else ""
        extra += ' tlType="static"' if ntype == "traffic_light" else ""
        nodes.append(f'  <node id="{nid}" x="{x}" y="0" type="{ntype}"{extra}/>')
    nodes.append("</nodes>")
    (d / "bn4.nod.xml").write_text("\n".join(nodes) + "\n")

    edges = ["<edges>"]
    for eid, fr, to, nl in spec["edges"]:
        edges.append(f'  <edge id="{eid}" from="{fr}" to="{to}" numLanes="{nl}" speed="{spec["speed"]}"/>')
    edges.append("</edges>")
    (d / "bn4.edg.xml").write_text("\n".join(edges) + "\n")

    con = ["<connections>"]
    for i in range(4):
        con.append(f'  <connection from="1" to="2" fromLane="{i}" toLane="{i}"/>')
        con.append(f'  <connection from="2" to="3" fromLane="{i}" toLane="{i}"/>')
        con.append(f'  <connection from="3" to="4" fromLane="{i}" toLane="{i // 2}"/>')
    for i in range(2):
        con.append(f'  <connection from="4" to="5" fromLane="{i}" toLane="0"/>')
    con.append("</connections>")
    (d / "bn4.con.xml").write_text("\n".join(con) + "\n")


def _write_detectors(d: Path, spec: dict, lane_lengths: dict) -> None:
    per = spec["loop_period_s"]
    add = ["<additional>"]
    l5 = lane_lengths["5_0"]
    add.append(f'  <inductionLoop id="exit_5_0" lane="5_0" pos="{l5 - spec["exit_loop_pos_from_end"]:.2f}" '
               f'period="{per}" file="NUL"/>')
    for i in range(4):
        l3 = lane_lengths[f"3_{i}"]
        add.append(f'  <inductionLoop id="merge_3_{i}" lane="3_{i}" pos="{l3 - spec["merge_loop_pos_from_end"]:.2f}" '
                   f'period="{per}" file="NUL"/>')
    # netconvert's default program for node 3 is GGGG 80 s / yyyy 5 s / rrrr 5 s, which would meter
    # every "no-control" run. Load an all-green program; runners also assert the state (health H-R7).
    add.append('  <tlLogic id="3" type="static" programID="allgreen" offset="0">')
    add.append('    <phase duration="1000000" state="GGGG"/>')
    add.append('  </tlLogic>')
    add.append("</additional>")
    (d / "bn4.det.add.xml").write_text("\n".join(add) + "\n")


def lane_lengths_from_net(net_file: Path) -> dict:
    import xml.etree.ElementTree as ET
    out = {}
    for lane in ET.parse(net_file).getroot().iter("lane"):
        lid = lane.get("id")
        if not lid.startswith(":"):
            out[lid] = float(lane.get("length"))
    return out


def build(spec: dict = SPEC, force: bool = False) -> Path:
    """Generate (or reuse) the BN4 network; returns the cache directory."""
    d = NET_CACHE / f"bn4_{spec_hash(spec)}"
    net = d / "bn4.net.xml"
    if net.exists() and (d / "bn4.det.add.xml").exists() and not force:
        return d
    d.mkdir(parents=True, exist_ok=True)
    _write_plain(d, spec)
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "bn4.nod.xml"), "--edge-files", str(d / "bn4.edg.xml"),
           "--connection-files", str(d / "bn4.con.xml"), "--no-turnarounds", "true",
           "--tls.default-type", "static", "-o", str(net), "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not net.exists():
        raise RuntimeError(f"netconvert failed: {r.stderr[-2000:]}")
    _write_detectors(d, spec, lane_lengths_from_net(net))
    (d / "spec.json").write_text(json.dumps(spec, indent=1))
    return d


if __name__ == "__main__":
    print(build(force=True))
