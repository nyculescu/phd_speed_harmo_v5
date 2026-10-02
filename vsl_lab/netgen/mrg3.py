"""MRG3: on-ramp merge bottleneck (Track 2, TM20 posted VSL; ramps_v2-like geometry, rebuilt cleanly).

Mainline (3 lanes, 33.33 m/s):  up3 (1000 m) - up2 (1000 m) - up1 (1000 m) - up0a (500 m) - up0b (500 m)
  VSL application area: up1 + up0a (1.5 km);  acceleration area: up0b (500 m, VSL rate 0.9 when MTFC active)
Merge (4 lanes, 250 m): lane 0 is the acceleration lane fed by the 1-lane on-ramp (300 m, 25 m/s); it ends,
  forcing merges; lanes 1-3 continue.   Downstream: down (3 lanes, 1000 m).
Detectors (period 60 s for control, matching Carlson's T_c; plus 30 s loops for state):
  E1 at the end of each mainline edge per lane, ramp end, network exit; E2 over the merge edge (all lanes)
  and over the first 300 m of `down` (bottleneck density for MTFC).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from vsl_lab.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

SPEC = {
    "name": "MRG3", "v_main": 33.33, "v_ramp": 25.0, "version": 1,
    "main": [("up3", 0.0, 1000.0), ("up2", 1000.0, 2000.0), ("up1", 2000.0, 3000.0), ("up0a", 3000.0, 3500.0),
             ("up0b", 3500.0, 4000.0)],
    "merge": ("merge", 4000.0, 4250.0), "down": ("down", 4250.0, 5250.0), "ramp_len": 300.0,
    "loop_period": 30.0, "e2_down_len": 300.0,
}
# D-4 lane-drop geometry (round2_protocol.md): same mainline, edge `merge` has 3 lanes whose lane 0 ends (a 3 -> 2
# lane drop, no ramp demand; the ramp edge is kept, unused, so detector ids stay valid), `down` has 2 lanes.
LD_SPEC = dict(SPEC, name="LD3", geom="lanedrop")
VSL_AREA = ("up1", "up0a")
ACC_AREA = ("up0b",)
MAIN_ROUTE = "up3 up2 up1 up0a up0b merge down"
RAMP_ROUTE = "ramp merge down"


def spec_hash(spec=SPEC) -> str:
    return hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]


def build(spec=SPEC, force=False) -> Path:
    d = NET_CACHE / f"{'ld3' if spec.get('geom') == 'lanedrop' else 'mrg3'}_{spec_hash(spec)}"
    net = d / "mrg3.net.xml"
    if net.exists() and (d / "mrg3.det.add.xml").exists() and not force:
        return d
    d.mkdir(parents=True, exist_ok=True)
    nodes = ['<nodes>']
    xs = [0.0, 1000.0, 2000.0, 3000.0, 3500.0, 4000.0, 4250.0, 5250.0]
    ids = ["n0", "n1", "n2", "n3", "n3b", "n4", "n5", "n6"]
    for i, x in zip(ids, xs):
        t = "dead_end" if i in ("n0", "n6") else "priority"
        nodes.append(f'  <node id="{i}" x="{x}" y="0" type="{t}"/>')
    nodes.append(f'  <node id="r0" x="{4000.0 - spec["ramp_len"] * 0.96:.1f}" y="-{spec["ramp_len"] * 0.28:.1f}" type="dead_end"/>')
    nodes.append("</nodes>")
    (d / "mrg3.nod.xml").write_text("\n".join(nodes) + "\n")
    vm, vr = spec["v_main"], spec["v_ramp"]
    ld = spec.get("geom") == "lanedrop"
    n_merge, n_down = (3, 2) if ld else (4, 3)
    edges = ["<edges>",
             f'  <edge id="up3" from="n0" to="n1" numLanes="3" speed="{vm}"/>',
             f'  <edge id="up2" from="n1" to="n2" numLanes="3" speed="{vm}"/>',
             f'  <edge id="up1" from="n2" to="n3" numLanes="3" speed="{vm}"/>',
             f'  <edge id="up0a" from="n3" to="n3b" numLanes="3" speed="{vm}"/>',
             f'  <edge id="up0b" from="n3b" to="n4" numLanes="3" speed="{vm}"/>',
             f'  <edge id="merge" from="n4" to="n5" numLanes="{n_merge}" speed="{vm}"/>',
             f'  <edge id="down" from="n5" to="n6" numLanes="{n_down}" speed="{vm}"/>',
             f'  <edge id="ramp" from="r0" to="n4" numLanes="1" speed="{vr}"/>',
             "</edges>"]
    (d / "mrg3.edg.xml").write_text("\n".join(edges) + "\n")
    con = ["<connections>"]
    for a, b in (("up3", "up2"), ("up2", "up1"), ("up1", "up0a"), ("up0a", "up0b")):
        for i in range(3):
            con.append(f'  <connection from="{a}" to="{b}" fromLane="{i}" toLane="{i}"/>')
    for i in range(3):
        con.append(f'  <connection from="up0b" to="merge" fromLane="{i}" toLane="{i if ld else i + 1}"/>')
    for i in range(n_down):
        con.append(f'  <connection from="merge" to="down" fromLane="{i + 1}" toLane="{i}"/>')
    con.append('  <connection from="ramp" to="merge" fromLane="0" toLane="0"/>')
    con.append("</connections>")
    (d / "mrg3.con.xml").write_text("\n".join(con) + "\n")
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "mrg3.nod.xml"), "--edge-files", str(d / "mrg3.edg.xml"),
           "--connection-files", str(d / "mrg3.con.xml"), "--no-turnarounds", "true", "-o", str(net),
           "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not net.exists():
        raise RuntimeError(r.stderr[-1500:])
    import xml.etree.ElementTree as ET
    lanes = {ln.get("id"): float(ln.get("length")) for ln in ET.parse(net).getroot().iter("lane")
             if not ln.get("id").startswith(":")}
    per = spec["loop_period"]
    add = ["<additional>"]
    for e in ("up3", "up2", "up1", "up0a", "up0b", "down"):
        for i in range(n_down if e == "down" else 3):
            L = lanes[f"{e}_{i}"]
            add.append(f'  <inductionLoop id="e1_{e}_{i}" lane="{e}_{i}" pos="{L - 5.0:.2f}" period="{per}" file="NUL"/>')
    add.append(f'  <inductionLoop id="e1_ramp_0" lane="ramp_0" pos="{lanes["ramp_0"] - 5.0:.2f}" period="{per}" file="NUL"/>')
    for i in range(n_merge):
        add.append(f'  <laneAreaDetector id="e2_merge_{i}" lane="merge_{i}" pos="0" length="{lanes[f"merge_{i}"]:.2f}" '
                   f'period="{per}" file="NUL"/>')
    for i in range(n_down):
        add.append(f'  <laneAreaDetector id="e2_down_{i}" lane="down_{i}" pos="0" length="{spec["e2_down_len"]:.2f}" '
                   f'period="{per}" file="NUL"/>')
    add.append("</additional>")
    (d / "mrg3.det.add.xml").write_text("\n".join(add) + "\n")
    (d / "spec.json").write_text(json.dumps(spec, indent=1))
    (d / "lanes.json").write_text(json.dumps(lanes, indent=1))
    return d


if __name__ == "__main__":
    print(build(force=True))
