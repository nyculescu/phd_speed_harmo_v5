"""On-ramp corridor 'ramp32' (V190): a metered on-ramp merge, then a 3 -> 2 lane-end drop about 1.5 km downstream.

Edges (mainline x in m): 1 entry 0-3,000 and 2 3,000-3,500 (3 lanes); 3a 3,500-3,800 (4 lanes: lane 0 is the
acceleration lane, which ends); 3 3,800-5,000 (3 lanes); drop at 5,000 (the left lane ends); 4 bottleneck 5,000-6,000
(2 lanes); 5 exit 6,000-6,500. Ramp r 400 m, 1 lane, joining lane 0 of 3a, with the meter signal at its end (TLS "rm").
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from v5b.d1.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

NAME = "ramp32"
METER = "rm"
ROUTES = {"main": "1 2 3a 3 4 5", "ramp": "r rj 3a 3 4 5"}
RAMP_SHARE = 0.15
ENTRY_LANES = {"main": 3, "ramp": 1}
NODES = [("n1", 0.0, 0.0), ("n2", 3000.0, 0.0), ("m", 3500.0, 0.0), ("ae", 3800.0, 0.0), ("d", 5000.0, 0.0),
         ("b", 6000.0, 0.0), ("x", 6500.0, 0.0), ("r0", 3080.0, -40.0), ("rm", 3470.0, -4.0)]
EDGES = [("1", "n1", "n2", 3), ("2", "n2", "m", 3), ("3a", "m", "ae", 4), ("3", "ae", "d", 3), ("4", "d", "b", 2),
         ("5", "b", "x", 2), ("r", "r0", "rm", 1)]
# loop name -> [(edge, position; negative = from the lane end)]; 'up' 1 km before the drop (V186),
# 'merge_up' just before the merge, 'ramp_q' near the ramp start (queue override), 'ramp_out' at the meter;
# E1 (V213): 'alinea' 100 m past the merge area, 'drop' 150 m and 'dropend' 20 m before the lane end
LOOPS = {"up": [("3", 200.0)], "merge_up": [("2", -50.0)], "e4": [("4", 100.0)], "exit": [("5", -15.0)],
         "ramp_q": [("r", 30.0)], "ramp_out": [("r", -5.0)], "alinea": [("3", 100.0)], "drop": [("3", -150.0)],
         "dropend": [("3", -20.0)]}
LOOP_PERIOD = 30.0


def build(speed: float) -> Path:
    spec = {"v": 1, "name": NAME, "nodes": NODES, "edges": EDGES, "loops": LOOPS, "speed": speed}
    h = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]
    d = NET_CACHE / f"{NAME}_{h}"
    if (d / "net.xml").exists() and (d / "add.xml").exists():
        return d
    final, d = d, NET_CACHE / f"{NAME}_{h}.tmp{os.getpid()}"     # built aside, then renamed: parallel first builds
    d.mkdir(parents=True, exist_ok=True)
    nod = ["<nodes>"] + [f'  <node id="{n}" x="{x}" y="{y}" type="{"traffic_light" if n == "rm" else "priority"}"'
                         + (' tlType="static"' if n == "rm" else "") + "/>" for n, x, y in NODES] + ["</nodes>"]
    edg = ["<edges>"] + [f'  <edge id="{e}" from="{a}" to="{b}" numLanes="{k}" speed="{speed}"/>'
                         for e, a, b, k in EDGES]
    edg += ['  <edge id="rj" from="rm" to="m" numLanes="1" speed="%s"/>' % speed, "</edges>"]
    con = ["<connections>",
           '  <connection from="r" to="rj" fromLane="0" toLane="0"/>',
           '  <connection from="rj" to="3a" fromLane="0" toLane="0"/>']
    con += [f'  <connection from="2" to="3a" fromLane="{i}" toLane="{i + 1}"/>' for i in range(3)]
    con += [f'  <connection from="3a" to="3" fromLane="{i + 1}" toLane="{i}"/>' for i in range(3)]
    con += [f'  <connection from="3" to="4" fromLane="{i}" toLane="{i}"/>' for i in range(2)]
    con += [f'  <connection from="1" to="2" fromLane="{i}" toLane="{i}"/>' for i in range(3)]
    con += [f'  <connection from="4" to="5" fromLane="{i}" toLane="{i}"/>' for i in range(2)]
    con += ["</connections>"]
    for f, lines in (("nod.xml", nod), ("edg.xml", edg), ("con.xml", con)):
        (d / f).write_text("\n".join(lines) + "\n")
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "nod.xml"), "--edge-files", str(d / "edg.xml"),
           "--connection-files", str(d / "con.xml"), "--no-turnarounds", "true", "--tls.default-type", "static",
           "-o", str(d / "net.xml"), "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not (d / "net.xml").exists():
        raise RuntimeError(f"netconvert failed: {r.stderr[-2000:]}")
    lens = {ln.get("id"): float(ln.get("length")) for ln in ET.parse(d / "net.xml").getroot().iter("lane")
            if not ln.get("id").startswith(":")}
    tls = [t.get("id") for t in ET.parse(d / "net.xml").getroot().iter("tlLogic")]
    add = ["<additional>"]
    for name, spots in LOOPS.items():
        for e, pos in spots:
            for i in range(dict((x[0], x[3]) for x in EDGES)[e]):
                ln = f"{e}_{i}"
                p = pos if pos >= 0 else lens[ln] + pos
                add.append(f'  <inductionLoop id="{name}_{e}_{i}" lane="{ln}" pos="{p:.2f}" period="{LOOP_PERIOD}" '
                           f'file="NUL"/>')
    add.append("</additional>")
    (d / "add.xml").write_text("\n".join(add) + "\n")
    (d / "spec.json").write_text(json.dumps({**spec, "lane_lengths": lens, "tls": tls}, indent=1))
    try:
        d.rename(final)
    except OSError:                    # another process won the race
        shutil.rmtree(d, ignore_errors=True)
    return final


def loop_ids() -> dict:
    lanes = {e: k for e, _, _, k in EDGES}
    return {name: [f"{name}_{e}_{i}" for e, _ in spots for i in range(lanes[e])] for name, spots in LOOPS.items()}


# V199 incident calibration roads: one straight 5 km edge "a"; loops relative to the crash position
STRAIGHT = {"inc3": 3, "inc2": 2}
STRAIGHT_LEN, STRAIGHT_CRASH = 5000.0, 3000.0
STRAIGHT_LOOPS = {"dn": 300.0, "upq": -500.0}


def build_straight(name: str, speed: float) -> Path:
    n = STRAIGHT[name]
    spec = {"v": 1, "name": name, "lanes": n, "len": STRAIGHT_LEN, "crash": STRAIGHT_CRASH, "loops": STRAIGHT_LOOPS,
            "speed": speed}
    h = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]
    d = NET_CACHE / f"{name}_{h}"
    if (d / "net.xml").exists() and (d / "add.xml").exists():
        return d
    d.mkdir(parents=True, exist_ok=True)
    (d / "nod.xml").write_text(f'<nodes>\n  <node id="s" x="0" y="0"/>\n  <node id="e" x="{STRAIGHT_LEN}" y="0"/>\n'
                               '</nodes>\n')
    (d / "edg.xml").write_text(f'<edges>\n  <edge id="a" from="s" to="e" numLanes="{n}" speed="{speed}"/>\n</edges>\n')
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "nod.xml"), "--edge-files", str(d / "edg.xml"),
           "--no-turnarounds", "true", "-o", str(d / "net.xml"), "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not (d / "net.xml").exists():
        raise RuntimeError(f"netconvert failed: {r.stderr[-2000:]}")
    add = ["<additional>"] + [f'  <inductionLoop id="{k}_a_{i}" lane="a_{i}" pos="{STRAIGHT_CRASH + x:.2f}" '
                              f'period="60" file="NUL"/>' for k, x in STRAIGHT_LOOPS.items() for i in range(n)]
    (d / "add.xml").write_text("\n".join(add + ["</additional>"]) + "\n")
    (d / "spec.json").write_text(json.dumps(spec, indent=1))
    return d


def straight_loop_ids(name: str) -> dict:
    return {k: [f"{k}_a_{i}" for i in range(STRAIGHT[name])] for k in STRAIGHT_LOOPS}
