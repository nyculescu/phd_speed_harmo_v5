"""P1c plant v2 (gate page §1-§2): BN4 geometry with lane changing on and calibration knobs.

Geometry from the Flow / Vinitsky et al. (2018) bottleneck (as v5b/d1/netgen_bn4.py): nodes x = 0, 100, 410, 550,
830, 985 m; edges 1..5 with 4, 4, 4, 2, 1 lanes; 23 m/s; meter (traffic light) at node 3 across all 4 lanes.

Calibration knobs (gate §2): merge at nodes 4 and 5 ('zip20' zipper with visibility 20 m, 'zip100' zipper with the
default 100 m, 'laneend' dead-end lanes with forced lane changes at priority nodes), car-following model ('IDM' with
Flow's parameters, 'EIDM', 'Krauss' with SUMO defaults), lcCooperative and the speed-factor spread.

CRN (gate §1): depart time, depart lane and speed factor of every vehicle are drawn from the demand seed and written
into the route file, so every arm of a seed runs the same vehicles.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from v5b.d1.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

SPEED = 23.0
NODES = [("1", 0.0), ("2", 100.0), ("3", 410.0), ("4", 550.0), ("5", 830.0), ("6", 985.0)]
EDGES = [("1", "1", "2", 4), ("2", "2", "3", 4), ("3", "3", "4", 4), ("4", "4", "5", 2), ("5", "5", "6", 1)]
ROUTE_EDGES = "1 2 3 4 5"
TLS_ID = "3"
STEP_LENGTH = 0.5
LOOP_PERIOD = 30.0
BLOCK_POS = 180.0   # lane-closure blocker position on lane 4_1 (m from the edge start)
LOOPS = {"e4": ["L4_0", "L4_1"], "e5": ["L5_0"], "exit": ["X5_0"], "e3": ["L3_0", "L3_1", "L3_2", "L3_3"]}


@dataclass(frozen=True)
class Config:
    merge: str = "zip20"          # zip20 | zip100 | laneend
    cf: str = "IDM"               # IDM | EIDM | Krauss
    lc_coop: float = 1.0
    speed_dev: float = 0.10
    step: float = STEP_LENGTH

    def tag(self) -> str:
        return f"{self.merge}_{self.cf}_lc{self.lc_coop:g}_sd{self.speed_dev:g}_st{self.step:g}"


def _net_spec(cfg: Config) -> dict:
    return {"v": 1, "merge": cfg.merge, "nodes": NODES, "edges": EDGES, "speed": SPEED, "loops": LOOPS,
            "period": LOOP_PERIOD}


def build_net(cfg: Config) -> Path:
    spec = _net_spec(cfg)
    h = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]
    d = NET_CACHE / f"p1c_{cfg.merge}_{h}"
    net = d / "net.xml"
    if net.exists() and (d / "add.xml").exists():
        return d
    d.mkdir(parents=True, exist_ok=True)
    zipper = cfg.merge.startswith("zip")
    vis = {"zip20": 20.0, "zip100": 100.0}.get(cfg.merge)
    nod = ["<nodes>"]
    for nid, x in NODES:
        t = "traffic_light" if nid == TLS_ID else ("zipper" if zipper and nid in ("4", "5") else "priority")
        extra = ' tlType="static"' if t == "traffic_light" else (' radius="20"' if t == "zipper" else "")
        nod.append(f'  <node id="{nid}" x="{x}" y="0" type="{t}"{extra}/>')
    (d / "nod.xml").write_text("\n".join(nod + ["</nodes>"]) + "\n")
    edg = ["<edges>"] + [f'  <edge id="{e}" from="{a}" to="{b}" numLanes="{n}" speed="{SPEED}"/>'
                         for e, a, b, n in EDGES] + ["</edges>"]
    (d / "edg.xml").write_text("\n".join(edg) + "\n")
    con = ["<connections>"]
    for i in range(4):
        con.append(f'  <connection from="1" to="2" fromLane="{i}" toLane="{i}"/>')
        con.append(f'  <connection from="2" to="3" fromLane="{i}" toLane="{i}"/>')
    v = f' visibility="{vis}"' if vis else ""
    if zipper:
        for i in range(4):
            con.append(f'  <connection from="3" to="4" fromLane="{i}" toLane="{i // 2}"{v}/>')
        for i in range(2):
            con.append(f'  <connection from="4" to="5" fromLane="{i}" toLane="0"{v}/>')
    else:   # lane end: lanes 3_2, 3_3 and 4_1 end; vehicles must change lanes
        con.append('  <connection from="3" to="4" fromLane="0" toLane="0"/>')
        con.append('  <connection from="3" to="4" fromLane="1" toLane="1"/>')
        con.append('  <connection from="4" to="5" fromLane="0" toLane="0"/>')
    (d / "con.xml").write_text("\n".join(con + ["</connections>"]) + "\n")
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "nod.xml"), "--edge-files", str(d / "edg.xml"),
           "--connection-files", str(d / "con.xml"), "--no-turnarounds", "true", "--tls.default-type", "static",
           "-o", str(net), "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not net.exists():
        raise RuntimeError(f"netconvert failed: {r.stderr[-2000:]}")
    import xml.etree.ElementTree as ET
    L = {ln.get("id"): float(ln.get("length")) for ln in ET.parse(net).getroot().iter("lane")
         if not ln.get("id").startswith(":")}
    add = ["<additional>"]
    for i in range(2):
        add.append(f'  <inductionLoop id="L4_{i}" lane="4_{i}" pos="100" period="{LOOP_PERIOD}" file="NUL"/>')
    add.append(f'  <inductionLoop id="L5_0" lane="5_0" pos="{L["5_0"] / 2:.2f}" period="{LOOP_PERIOD}" file="NUL"/>')
    add.append(f'  <inductionLoop id="X5_0" lane="5_0" pos="{L["5_0"] - 15:.2f}" period="{LOOP_PERIOD}" file="NUL"/>')
    for i in range(4):
        add.append(f'  <inductionLoop id="L3_{i}" lane="3_{i}" pos="{L[f"3_{i}"] - 20:.2f}" period="{LOOP_PERIOD}" '
                   f'file="NUL"/>')
    add += ['  <tlLogic id="3" type="static" programID="allgreen" offset="0">',
            '    <phase duration="1000000" state="GGGG"/>', '  </tlLogic>', "</additional>"]
    (d / "add.xml").write_text("\n".join(add) + "\n")
    (d / "spec.json").write_text(json.dumps({**spec, "lane_lengths": L}, indent=1))
    return d


def vtype_xml(cfg: Config) -> str:
    lc = f'laneChangeModel="LC2013" lcCooperative="{cfg.lc_coop:g}"'
    if cfg.cf == "IDM":
        cf = 'carFollowModel="IDM" accel="1.0" decel="1.5" tau="1.0" minGap="2.0" delta="4"'
    elif cfg.cf == "EIDM":
        cf = 'carFollowModel="EIDM"'
    elif cfg.cf == "Krauss":
        cf = 'carFollowModel="Krauss"'
    else:
        raise ValueError(cfg.cf)
    return f'  <vType id="car" vClass="passenger" length="5" {cf} {lc}/>'


@dataclass
class Vehicle:
    vid: str
    depart: float
    lane: int
    sf: float


class Demand:
    """Poisson arrivals with a piecewise-constant rate; per-vehicle lane and speed factor (CRN). Interface-compatible
    with v5b/d1/sumo_runner.SumoSim (depart_times, counts_by_route, vehicles as (depart, vid, rid, vtype))."""

    def __init__(self, seed: int, profile: list, cfg: Config, blocker: tuple | None = None):
        """blocker = (onset, duration): a stopped vehicle 'blk.0' on lane 4_1 (the lane-closure incident), written
        into the route file so every arm shares it; it counts as route 'blk' for the runner's conservation checks."""
        rng = np.random.default_rng(seed)
        attr = np.random.default_rng(seed + 7919)
        self.cfg, self.seed, self.profile = cfg, seed, profile
        vs, n = [], 0
        for (t0, t1, q) in profile:
            if q <= 0 or t1 <= t0:
                continue
            t = t0
            while True:
                t += rng.exponential(3600.0 / q)
                if t >= t1:
                    break
                dep = round(math.ceil(t / cfg.step - 1e-9) * cfg.step, 3)
                sf = float(np.clip(attr.normal(1.0, cfg.speed_dev), 0.2, 2.0))
                vs.append(Vehicle(f"main.{n}", dep, int(attr.integers(0, 4)), round(sf, 4)))
                n += 1
        self.veh = vs
        self.vehicles = [(v.depart, v.vid, "main", "car") for v in vs]
        self.sf = {v.vid: v.sf for v in vs}
        self.blocker = blocker
        if blocker is not None:
            self.vehicles.append((round(math.ceil(blocker[0] / cfg.step - 1e-9) * cfg.step, 3), "blk.0", "blk", "blocker"))
            self.vehicles.sort(key=lambda v: (v[0], v[1]))

    @property
    def depart_times(self) -> list:
        return [v[0] for v in self.vehicles]

    def counts_by_route(self) -> dict:
        return {"main": len(self.veh), **({"blk": 1} if self.blocker else {})}

    def write(self, path: Path) -> None:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>", vtype_xml(self.cfg),
                 f'  <route id="main" edges="{ROUTE_EDGES}"/>']
        if self.blocker:
            lines.append(f'  <vType id="blocker" vClass="passenger" length="5" color="1,0,0"/>')
            lines.append(f'  <route id="blk" edges="4 5"/>')
        rows = [(v.depart, f'  <vehicle id="{v.vid}" type="car" route="main" depart="{v.depart:.2f}" '
                           f'departLane="{v.lane}" departSpeed="max" speedFactor="{v.sf}"/>') for v in self.veh]
        if self.blocker:
            t0, dur = self.blocker
            dep = round(math.ceil(t0 / self.cfg.step - 1e-9) * self.cfg.step, 3)
            rows.append((dep, f'  <vehicle id="blk.0" type="blocker" route="blk" depart="{dep:.2f}" departLane="1" '
                              f'departPos="{BLOCK_POS}" departSpeed="0"><stop lane="4_1" endPos="{BLOCK_POS + 5}" '
                              f'duration="{dur:.1f}"/></vehicle>'))
        rows.sort(key=lambda r: r[0])
        lines += [r[1] for r in rows]
        lines.append("</routes>")
        path.write_text("\n".join(lines) + "\n")


def config_dict(cfg: Config) -> dict:
    return asdict(cfg)
