"""CORR2: 9.5 km freeway corridor with two metered on-ramps, one off-ramp and two VSL areas (Track 4).

Mainline (3 lanes, 33.33 m/s), x in metres:
  m0 (0-1500) - m1 (1500-2500, VSL area 1) - m2 (2500-3000) - merge1 (3000-3250, 4 lanes) - m3 (3250-4500)
  - [diverge at 4500: off-ramp O1, 1 lane, 300 m, 25 m/s, from the right lane] - m4 (4500-5500, VSL area 2)
  - m5 (5500-6000) - merge2 (6000-6250, 4 lanes) - m6 (6250-7500) - down (7500-9500)
merge1 / merge2: lane 0 is the acceleration lane of on-ramp R1 / R2; it ends (no successor), forcing merges;
  mainline lanes 0-2 feed merge lanes 1-3, which continue as lanes 0-2 downstream (as MRG3's `merge` edge).
On-ramps (1 lane, 25 m/s): origin edge R1o / R2o (200 m, so queues beyond the storage stay visible) -> storage edge
  R1 / R2 (400 m) -> merge1 / merge2. Ramp meter = a traffic light at the DOWNSTREAM end of R1 / R2 (nodes nm1 /
  nm2, TLS ids meter_R1 / meter_R2). The merge nodes are TLS nodes, but every mainline connection through them is
  written with uncontrolled="true", so each TLS controls exactly one link (the ramp) and the mainline is never
  signalised (checked in tests/test_corr2_build.py and at run time). netconvert's default program for the meters is
  replaced by an all-green program "allgreen" loaded from the additional file (as BN4 does); metering controllers
  switch states online (plants/corr2.py Meter).
Detectors (additional file):
  e1_<edge>_<i>    E1 per lane at L-5 m of every mainline edge (incl. the acceleration lane 0 of merge edges), 30 s
  e1a_m3_<i>, e1a_m6_<i>   E1 per mainline lane 40 m downstream of the merge1 / merge2 end (ALINEA), 60 s
  e1_<R>in_0, e1_<R>out_0  E1 at the ramp entrance (R start + 5 m) and ramp end (R end - 1 m), 30 s
  e1_O1_0          E1 at the off-ramp end, 30 s
  e2_<R>_0, e2_<R>o_0      E2 over the whole storage edge and the whole origin edge of each ramp (queue), 30 s
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from vsl_lab.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

SPEC = {
    "name": "CORR2", "version": 2, "v_main": 33.33, "v_ramp": 25.0,
    # v2: every edge gets an explicit nominal `length` (v1 geometric lengths: the 16 deg ramp junctions cut ~31-37 m,
    # e.g. R1 363.8 m instead of 400 m, m4 963.1 m instead of 1000 m); internal junction lanes (3-20 m) stay geometric
    # mainline edges: (id, x_from, x_to, n_lanes)
    "main": [("m0", 0.0, 1500.0, 3), ("m1", 1500.0, 2500.0, 3), ("m2", 2500.0, 3000.0, 3),
             ("merge1", 3000.0, 3250.0, 4), ("m3", 3250.0, 4500.0, 3), ("m4", 4500.0, 5500.0, 3),
             ("m5", 5500.0, 6000.0, 3), ("merge2", 6000.0, 6250.0, 4), ("m6", 6250.0, 7500.0, 3),
             ("down", 7500.0, 9500.0, 3)],
    "ramps": {"R1": {"merge": "merge1", "x": 3000.0}, "R2": {"merge": "merge2", "x": 6000.0}},
    "ramp_len": 400.0, "ramp_origin_len": 200.0,
    "off": {"id": "O1", "x": 4500.0, "len": 300.0, "from": "m3"},
    "loop_period": 30.0, "alinea_period": 60.0, "alinea_offset": 40.0,
}
MAIN_EDGES = tuple(e[0] for e in SPEC["main"])
N_LANES = {e[0]: e[3] for e in SPEC["main"]}
MERGES = ("merge1", "merge2")
RAMPS = ("R1", "R2")
TLS = {"R1": "meter_R1", "R2": "meter_R2"}
ALINEA_LOOPS = {"R1": "m3", "R2": "m6"}             # loops e1a_<edge>_<i>, 40 m past the merge end
VSL_AREAS = {1: ("m1",), 2: ("m4",)}
# routes (edge lists)
ROUTES = {
    "main_ex": "m0 m1 m2 merge1 m3 m4 m5 merge2 m6 down",
    "main_off": "m0 m1 m2 merge1 m3 O1",
    "r1_ex": "R1o R1 merge1 m3 m4 m5 merge2 m6 down",
    "r1_off": "R1o R1 merge1 m3 O1",
    "r2_ex": "R2o R2 merge2 m6 down",
}
# the ramp direction vector (unit length: 0.96^2 + 0.28^2 = 1), as MRG3's ramp node placement
_DX, _DY = 0.96, 0.28


def spec_hash(spec=SPEC) -> str:
    return hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]


def _node_id(x: float) -> str:
    return {0.0: "n0", 1500.0: "n1", 2500.0: "n2", 3000.0: "nm1", 3250.0: "nm1e", 4500.0: "nd1", 5500.0: "n4e",
            6000.0: "nm2", 6250.0: "nm2e", 7500.0: "n6", 9500.0: "n7"}[x]


def _write_plain(d: Path, spec: dict) -> None:
    vm, vr = spec["v_main"], spec["v_ramp"]
    xs = sorted({e[1] for e in spec["main"]} | {e[2] for e in spec["main"]})
    meter_nodes = {_node_id(r["x"]): k for k, r in spec["ramps"].items()}
    nodes = ["<nodes>"]
    for x in xs:
        nid = _node_id(x)
        if nid in meter_nodes:
            nodes.append(f'  <node id="{nid}" x="{x}" y="0" type="traffic_light" tl="{TLS[meter_nodes[nid]]}" '
                         'tlType="static"/>')
        else:
            t = "dead_end" if x in (xs[0], xs[-1]) else "priority"
            nodes.append(f'  <node id="{nid}" x="{x}" y="0" type="{t}"/>')
    L, Lo = spec["ramp_len"], spec["ramp_origin_len"]
    for k, r in spec["ramps"].items():
        xb, yb = r["x"] - L * _DX, -L * _DY
        nodes.append(f'  <node id="{k.lower()}b" x="{xb:.2f}" y="{yb:.2f}" type="priority"/>')
        nodes.append(f'  <node id="{k.lower()}a" x="{xb - Lo * _DX:.2f}" y="{yb - Lo * _DY:.2f}" type="dead_end"/>')
    o = spec["off"]
    nodes.append(f'  <node id="o1e" x="{o["x"] + o["len"] * _DX:.2f}" y="{-o["len"] * _DY:.2f}" type="dead_end"/>')
    nodes.append("</nodes>")
    (d / "corr2.nod.xml").write_text("\n".join(nodes) + "\n")

    edges = ["<edges>"]
    for eid, x0, x1, nl in spec["main"]:
        edges.append(f'  <edge id="{eid}" from="{_node_id(x0)}" to="{_node_id(x1)}" numLanes="{nl}" speed="{vm}" '
                     f'length="{x1 - x0:.2f}"/>')
    for k, r in spec["ramps"].items():
        edges.append(f'  <edge id="{k}o" from="{k.lower()}a" to="{k.lower()}b" numLanes="1" speed="{vr}" '
                     f'length="{Lo:.2f}"/>')
        edges.append(f'  <edge id="{k}" from="{k.lower()}b" to="{_node_id(r["x"])}" numLanes="1" speed="{vr}" '
                     f'length="{L:.2f}"/>')
    edges.append(f'  <edge id="{o["id"]}" from="{_node_id(o["x"])}" to="o1e" numLanes="1" speed="{vr}" '
                 f'length="{o["len"]:.2f}"/>')
    edges.append("</edges>")
    (d / "corr2.edg.xml").write_text("\n".join(edges) + "\n")

    con = ["<connections>"]
    main = spec["main"]
    merge_of = {r["merge"]: k for k, r in spec["ramps"].items()}
    for (a, _, _, na), (b, _, _, nb) in zip(main[:-1], main[1:]):
        if b in merge_of:            # mainline into a merge edge: lanes i -> i+1, never TLS-controlled
            for i in range(na):
                con.append(f'  <connection from="{a}" to="{b}" fromLane="{i}" toLane="{i + 1}" uncontrolled="true"/>')
        elif a in merge_of:          # merge edge -> downstream: lanes 1..3 -> 0..2; lane 0 (acceleration lane) ends
            for i in range(nb):
                con.append(f'  <connection from="{a}" to="{b}" fromLane="{i + 1}" toLane="{i}"/>')
        else:
            for i in range(min(na, nb)):
                con.append(f'  <connection from="{a}" to="{b}" fromLane="{i}" toLane="{i}"/>')
    for k, r in spec["ramps"].items():
        con.append(f'  <connection from="{k}o" to="{k}" fromLane="0" toLane="0"/>')
        con.append(f'  <connection from="{k}" to="{r["merge"]}" fromLane="0" toLane="0"/>')
    con.append(f'  <connection from="{o["from"]}" to="{o["id"]}" fromLane="0" toLane="0"/>')
    con.append("</connections>")
    (d / "corr2.con.xml").write_text("\n".join(con) + "\n")


def lane_lengths(net_file: Path) -> dict:
    return {ln.get("id"): float(ln.get("length")) for ln in ET.parse(net_file).getroot().iter("lane")
            if not ln.get("id").startswith(":")}


def _write_additional(d: Path, spec: dict, lanes: dict) -> None:
    per, pa, off = spec["loop_period"], spec["alinea_period"], spec["alinea_offset"]
    add = ["<additional>"]
    for e in MAIN_EDGES:
        for i in range(N_LANES[e]):
            L = lanes[f"{e}_{i}"]
            add.append(f'  <inductionLoop id="e1_{e}_{i}" lane="{e}_{i}" pos="{L - 5.0:.2f}" period="{per}" file="NUL"/>')
    for r, e in ALINEA_LOOPS.items():
        for i in range(N_LANES[e]):
            add.append(f'  <inductionLoop id="e1a_{e}_{i}" lane="{e}_{i}" pos="{off:.2f}" period="{pa}" file="NUL"/>')
    for r in RAMPS:
        L = lanes[f"{r}_0"]
        add.append(f'  <inductionLoop id="e1_{r}in_0" lane="{r}_0" pos="5.00" period="{per}" file="NUL"/>')
        add.append(f'  <inductionLoop id="e1_{r}out_0" lane="{r}_0" pos="{L - 1.0:.2f}" period="{per}" file="NUL"/>')
        add.append(f'  <laneAreaDetector id="e2_{r}_0" lane="{r}_0" pos="0" length="{L:.2f}" period="{per}" '
                   'file="NUL"/>')
        Lo = lanes[f"{r}o_0"]
        add.append(f'  <laneAreaDetector id="e2_{r}o_0" lane="{r}o_0" pos="0" length="{Lo:.2f}" period="{per}" '
                   'file="NUL"/>')
    o = spec["off"]["id"]
    add.append(f'  <inductionLoop id="e1_{o}_0" lane="{o}_0" pos="{lanes[f"{o}_0"] - 5.0:.2f}" period="{per}" '
               'file="NUL"/>')
    # netconvert's default static program would meter every no-control run: load an all-green program per meter
    for r in RAMPS:
        add.append(f'  <tlLogic id="{TLS[r]}" type="static" programID="allgreen" offset="0">')
        add.append('    <phase duration="1000000" state="G"/>')
        add.append('  </tlLogic>')
    add.append("</additional>")
    (d / "corr2.det.add.xml").write_text("\n".join(add) + "\n")


def check_net(net_file: Path) -> dict:
    """Structural checks used by the test and by build(): lane counts, meter TLS link sets, mainline not signalised."""
    root = ET.parse(net_file).getroot()
    n_lanes = {}
    for e in root.iter("edge"):
        if e.get("function") == "internal":
            continue
        n_lanes[e.get("id")] = len(e.findall("lane"))
    tl_links = {}
    for c in root.iter("connection"):
        if c.get("tl") is not None and not c.get("from").startswith(":"):
            tl_links.setdefault(c.get("tl"), []).append((c.get("from"), c.get("to"), c.get("fromLane"), c.get("toLane")))
    tls_ids = sorted(t.get("id") for t in root.iter("tlLogic"))
    main_controlled = [l for links in tl_links.values() for l in links if l[0] in MAIN_EDGES]
    return {"n_lanes": n_lanes, "tl_links": tl_links, "tls_ids": tls_ids, "main_controlled": main_controlled}


def build(spec=SPEC, force=False) -> Path:
    d = NET_CACHE / f"corr2_{spec_hash(spec)}"
    net = d / "corr2.net.xml"
    if net.exists() and (d / "corr2.det.add.xml").exists() and (d / "lanes.json").exists() and not force:
        return d
    d.mkdir(parents=True, exist_ok=True)
    _write_plain(d, spec)
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "corr2.nod.xml"), "--edge-files", str(d / "corr2.edg.xml"),
           "--connection-files", str(d / "corr2.con.xml"), "--no-turnarounds", "true",
           "--tls.default-type", "static", "-o", str(net), "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not net.exists():
        raise RuntimeError(f"netconvert failed: {r.stderr[-2000:]}")
    chk = check_net(net)
    if chk["main_controlled"] or sorted(chk["tl_links"]) != sorted(TLS.values()) or \
            any(len(v) != 1 for v in chk["tl_links"].values()):
        raise RuntimeError(f"CORR2 meter/TLS structure wrong: {chk['tl_links']}")
    lanes = lane_lengths(net)
    _write_additional(d, spec, lanes)
    (d / "spec.json").write_text(json.dumps(spec, indent=1))
    (d / "lanes.json").write_text(json.dumps(lanes, indent=1))
    return d


if __name__ == "__main__":
    print(build(force=True))
