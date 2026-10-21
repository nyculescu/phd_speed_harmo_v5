"""P1c plant v2 (gate page §1-§2; V138, V141): geometry 'bn4' (Flow / Vinitsky et al. 2018 bottleneck, closed for
lane-closure incidents in V140) or 'wz' (work zone, V141), with lane changing on and calibration knobs.

Both geometries use edge ids 1..5 on the route "1 2 3 4 5", the meter (traffic light) at node 3 across every lane of
edge 2, the lane-closure blocker on lane 4_1 and the slowdown on the bottleneck edge.
  bn4: lanes 4/4/4/2/1, nodes x = 0, 100, 410, 550, 830, 985 m; zipper drops 4->2 and 2->1; bottleneck edge 5.
  wz:  lanes 3/3/3/2/2, nodes x = 0, 200, 800, 1000, 1400, 1600 m; zipper drop 3->2 at node 4; the 2-lane work-zone
       bottleneck is edge 4 (400 m); the blocker closes one of its two lanes, so capacity really falls to one lane.

Calibration knobs (gate §2): merge ('zip20', 'zip100', 'laneend'), car-following ('IDM' Flow parameters, 'EIDM',
'Krauss' SUMO defaults), lcCooperative, speed-factor spread. CRN: depart time, depart lane and speed factor of every
vehicle come from the demand seed and are written into the route file.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from v5b.d1.config import NET_CACHE, NETCONVERT_BIN, clean_sumo_env

SPEED = 23.0
ROUTE_EDGES = "1 2 3 4 5"
TLS_ID = "3"
STEP_LENGTH = 0.5
LOOP_PERIOD = 30.0
BLOCK_LANE = "4_1"

GEOMS = {
    "bn4": {"nodes": [("1", 0.0), ("2", 100.0), ("3", 410.0), ("4", 550.0), ("5", 830.0), ("6", 985.0)],
            "lanes": {"1": 4, "2": 4, "3": 4, "4": 2, "5": 1}, "drops": ("4", "5"), "bott_edge": "5",
            "block_pos": 180.0, "loops": {"e4": [("4", 100.0)], "e5": [("5", "mid")], "exit": [("5", -15.0)],
                                           "e3": [("3", -20.0)]}},
    "wz": {"nodes": [("1", 0.0), ("2", 200.0), ("3", 800.0), ("4", 1000.0), ("5", 1400.0), ("6", 1600.0)],
           "lanes": {"1": 3, "2": 3, "3": 3, "4": 2, "5": 2}, "drops": ("4",), "bott_edge": "4",
           "block_pos": 250.0, "loops": {"e4": [("4", 100.0)], "e5": [("5", "mid")], "exit": [("5", -15.0)],
                                          "e3": [("3", -20.0)]}},
}
EDGE_NODES = {"1": ("1", "2"), "2": ("2", "3"), "3": ("3", "4"), "4": ("4", "5"), "5": ("5", "6")}


@dataclass(frozen=True)
class Config:
    merge: str = "zip20"          # zip20 | zip100 | laneend
    cf: str = "IDM"               # IDM | EIDM | Krauss
    lc_coop: float = 1.0
    speed_dev: float = 0.10
    step: float = STEP_LENGTH
    geom: str = "bn4"             # bn4 | wz

    def tag(self) -> str:
        return f"{self.geom}_{self.merge}_{self.cf}_lc{self.lc_coop:g}_sd{self.speed_dev:g}_st{self.step:g}"


def lanes(geom: str, edge: str) -> int:
    return GEOMS[geom]["lanes"][edge]


def loop_ids(geom: str) -> dict:
    g = GEOMS[geom]
    out = {}
    for name, spots in g["loops"].items():
        out[name] = [f"{name}_{e}_{i}" for e, _ in spots for i in range(g["lanes"][e])]
    return out


def _connections(geom: str, merge: str) -> list:
    g = GEOMS[geom]
    L = g["lanes"]
    vis = {"zip20": 20.0, "zip100": 100.0}.get(merge)
    v = f' visibility="{vis}"' if vis else ""
    con = []
    for e_from, e_to in (("1", "2"), ("2", "3"), ("3", "4"), ("4", "5")):
        nf, nt = L[e_from], L[e_to]
        node = EDGE_NODES[e_from][1]
        if nf == nt:
            con += [f'  <connection from="{e_from}" to="{e_to}" fromLane="{i}" toLane="{i}"/>' for i in range(nf)]
        elif merge == "laneend":          # the extra lanes end; vehicles must change lanes
            con += [f'  <connection from="{e_from}" to="{e_to}" fromLane="{i}" toLane="{i}"/>' for i in range(nt)]
        else:                              # zipper: every lane connects, surplus lanes merge into the last lane(s)
            for i in range(nf):
                to = i // 2 if (nf == 4 and nt == 2) else min(i, nt - 1)
                con.append(f'  <connection from="{e_from}" to="{e_to}" fromLane="{i}" toLane="{to}"{v}/>')
    return con


def build_net(cfg: Config) -> Path:
    g = GEOMS[cfg.geom]
    spec = {"v": 2, "geom": cfg.geom, "merge": cfg.merge, "g": g, "speed": SPEED, "period": LOOP_PERIOD}
    h = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]
    d = NET_CACHE / f"p1c_{cfg.geom}_{cfg.merge}_{h}"
    net = d / "net.xml"
    if net.exists() and (d / "add.xml").exists():
        return d
    d.mkdir(parents=True, exist_ok=True)
    zipper = cfg.merge.startswith("zip")
    nod = ["<nodes>"]
    for nid, x in g["nodes"]:
        if nid == TLS_ID:
            t, extra = "traffic_light", ' tlType="static"'
        elif zipper and nid in g["drops"]:
            t, extra = "zipper", ' radius="20"'
        else:
            t, extra = "priority", ""
        nod.append(f'  <node id="{nid}" x="{x}" y="0" type="{t}"{extra}/>')
    (d / "nod.xml").write_text("\n".join(nod + ["</nodes>"]) + "\n")
    edg = ["<edges>"] + [f'  <edge id="{e}" from="{EDGE_NODES[e][0]}" to="{EDGE_NODES[e][1]}" numLanes="{n}" '
                         f'speed="{SPEED}"/>' for e, n in g["lanes"].items()] + ["</edges>"]
    (d / "edg.xml").write_text("\n".join(edg) + "\n")
    (d / "con.xml").write_text("\n".join(["<connections>"] + _connections(cfg.geom, cfg.merge) + ["</connections>"]) + "\n")
    cmd = [NETCONVERT_BIN, "--node-files", str(d / "nod.xml"), "--edge-files", str(d / "edg.xml"),
           "--connection-files", str(d / "con.xml"), "--no-turnarounds", "true", "--tls.default-type", "static",
           "-o", str(net), "--log", str(d / "netconvert.log")]
    r = subprocess.run(cmd, env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0 or not net.exists():
        raise RuntimeError(f"netconvert failed: {r.stderr[-2000:]}")
    LL = {ln.get("id"): float(ln.get("length")) for ln in ET.parse(net).getroot().iter("lane")
          if not ln.get("id").startswith(":")}
    add = ["<additional>"]
    for name, spots in g["loops"].items():
        for e, pos in spots:
            for i in range(g["lanes"][e]):
                ln = f"{e}_{i}"
                p = LL[ln] / 2 if pos == "mid" else (pos if pos >= 0 else LL[ln] + pos)
                add.append(f'  <inductionLoop id="{name}_{e}_{i}" lane="{ln}" pos="{p:.2f}" period="{LOOP_PERIOD}" '
                           f'file="NUL"/>')
    n2 = g["lanes"]["2"]
    add += ['  <tlLogic id="3" type="static" programID="allgreen" offset="0">',
            f'    <phase duration="1000000" state="{"G" * n2}"/>', '  </tlLogic>', "</additional>"]
    (d / "add.xml").write_text("\n".join(add) + "\n")
    (d / "spec.json").write_text(json.dumps({**spec, "lane_lengths": LL}, indent=1))
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
    """Poisson arrivals with a piecewise-constant rate; per-vehicle lane and speed factor (CRN). blocker = (onset,
    duration): the lane-closure vehicle 'blk.0' on lane 4_1, in the route file so every arm shares it (route 'blk').
    Interface-compatible with v5b/d1/sumo_runner.SumoSim."""

    def __init__(self, seed: int, profile: list, cfg: Config, blocker: tuple | None = None):
        rng = np.random.default_rng(seed)
        attr = np.random.default_rng(seed + 7919)
        self.cfg, self.seed, self.profile, self.blocker = cfg, seed, profile, blocker
        n_in = lanes(cfg.geom, "1")
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
                vs.append(Vehicle(f"main.{n}", dep, int(attr.integers(0, n_in)), round(sf, 4)))
                n += 1
        self.veh = vs
        self.sf = {v.vid: v.sf for v in vs}
        self.vehicles = [(v.depart, v.vid, "main", "car") for v in vs]
        if blocker is not None:
            self.blk_dep = round(math.ceil(blocker[0] / cfg.step - 1e-9) * cfg.step, 3)
            self.vehicles.append((self.blk_dep, "blk.0", "blk", "blocker"))
            self.vehicles.sort(key=lambda v: (v[0], v[1]))

    @property
    def depart_times(self) -> list:
        return [v[0] for v in self.vehicles]

    def counts_by_route(self) -> dict:
        return {"main": len(self.veh), **({"blk": 1} if self.blocker else {})}

    def write(self, path: Path) -> None:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>", vtype_xml(self.cfg),
                 f'  <route id="main" edges="{ROUTE_EDGES}"/>']
        rows = [(v.depart, f'  <vehicle id="{v.vid}" type="car" route="main" depart="{v.depart:.2f}" '
                           f'departLane="{v.lane}" departSpeed="max" speedFactor="{v.sf}"/>') for v in self.veh]
        if self.blocker:
            pos = GEOMS[self.cfg.geom]["block_pos"]
            lines += ['  <vType id="blocker" vClass="passenger" length="5" color="1,0,0"/>',
                      '  <route id="blk" edges="4 5"/>']
            rows.append((self.blk_dep, f'  <vehicle id="blk.0" type="blocker" route="blk" depart="{self.blk_dep:.2f}" '
                                       f'departLane="1" departPos="{pos}" departSpeed="0"><stop lane="{BLOCK_LANE}" '
                                       f'endPos="{pos + 5}" duration="{self.blocker[1]:.1f}"/></vehicle>'))
        rows.sort(key=lambda r: r[0])
        lines += [r[1] for r in rows] + ["</routes>"]
        path.write_text("\n".join(lines) + "\n")


def config_dict(cfg: Config) -> dict:
    return asdict(cfg)
