"""Explicit, seeded vehicle generation (no per-second insertion cap; cf. v5's 3,600 veh/h truncation).

Arrivals are a Poisson process per route with a piecewise-constant rate. Every vehicle is written
explicitly, with its depart time snapped up to the simulation step grid, so `due(t)` is known exactly
and the health monitor can check vehicle conservation to the vehicle.
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Route:
    rid: str
    edges: str                      # space-separated edge ids
    profile: list                   # [(t_start, t_end, veh_per_hour), ...]
    av_share: float = 0.0
    depart_lane: str = "random"
    depart_speed: str = "10"


@dataclass
class Demand:
    vtypes_xml: str                 # <vType .../> lines
    routes: list
    step_length: float
    seed: int
    human_type: str = "human"
    av_type: str = "av"
    vehicles: list = field(default_factory=list)   # (depart, vid, rid, vtype)

    def generate(self) -> None:
        rng = np.random.default_rng(self.seed)
        vehs = []
        for r in self.routes:
            n = 0
            for (t0, t1, q) in r.profile:
                if q <= 0 or t1 <= t0:
                    continue
                lam = q / 3600.0
                t = t0
                while True:
                    t += rng.exponential(1.0 / lam)
                    if t >= t1:
                        break
                    dep = math.ceil(t / self.step_length - 1e-9) * self.step_length
                    vt = self.av_type if rng.random() < r.av_share else self.human_type
                    vehs.append((round(dep, 3), f"{r.rid}.{n}", r.rid, vt))
                    n += 1
        vehs.sort(key=lambda v: (v[0], v[1]))
        self.vehicles = vehs

    @property
    def depart_times(self) -> list:
        return [v[0] for v in self.vehicles]

    def due(self, t: float) -> int:
        return bisect.bisect_right(self.depart_times, t + 1e-9)

    def counts_by_route(self) -> dict:
        out = {}
        for v in self.vehicles:
            out[v[2]] = out.get(v[2], 0) + 1
        return out

    def write(self, path: Path) -> None:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>", self.vtypes_xml]
        for r in self.routes:
            lines.append(f'  <route id="{r.rid}" edges="{r.edges}"/>')
        rmap = {r.rid: r for r in self.routes}
        for dep, vid, rid, vt in self.vehicles:
            r = rmap[rid]
            lines.append(f'  <vehicle id="{vid}" type="{vt}" route="{rid}" depart="{dep:.2f}" '
                         f'departLane="{r.depart_lane}" departSpeed="{r.depart_speed}"/>')
        lines.append("</routes>")
        path.write_text("\n".join(lines) + "\n")
