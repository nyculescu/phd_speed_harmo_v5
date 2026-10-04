"""BN4 plant: Vinitsky et al. (2018) bottleneck in SUMO 1.27.

AV speedFactor is exactly 1 (speedDev="0"; SUMO's default speedDev 0.1 had silently applied until fix v3).
Humans and AVs use IDM with Flow's default parameters (a = 1 m/s^2, b = 1.5 m/s^2, T = 1 s,
s0 = 2 m, delta = 4). Desired speed ~ N(limit, 20 %) via speedFactor. Lane changing disabled for
everyone, as in the paper ("lane changing is disabled for all the vehicles in this system").
The variant BN4-L (lane_changing=True) re-enables LC2013 defaults.
"""
from __future__ import annotations

from pathlib import Path

import libsumo as ls

from vsl_lab.netgen import bn4 as net
from vsl_lab.sim.demand import Demand, Route

ROUTE_EDGES = "1 2 3 4 5"
TLS_ID = "3"
ALL_GREEN = "GGGG"
STEP_LENGTH = 0.5


def vtypes_xml(lane_changing: bool = False) -> str:
    lc = "" if lane_changing else ' lcStrategic="-1" lcSpeedGain="0" lcCooperative="0" lcKeepRight="0"'
    common = 'carFollowModel="IDM" accel="1.0" decel="1.5" tau="1.0" minGap="2.0" delta="4" length="5"'
    return (f'  <vType id="human" {common} speedFactor="normc(1,0.2,0.2,2.0)"{lc} color="1,1,1"/>\n'
            f'  <vType id="av" {common} speedFactor="1.0" speedDev="0"{lc} color="1,0,0"/>')


def demand(seed: int, profile: list, av_share: float = 0.1, lane_changing: bool = False) -> Demand:
    d = Demand(vtypes_xml=vtypes_xml(lane_changing),
               routes=[Route("main", ROUTE_EDGES, profile, av_share=av_share, depart_lane="random",
                             depart_speed="10")],
               step_length=STEP_LENGTH, seed=seed)
    d.generate()
    return d


def files() -> dict:
    d = net.build()
    return {"net": d / "bn4.net.xml", "add": d / "bn4.det.add.xml", "dir": d}


def set_all_green() -> None:
    ls.trafficlight.setProgram(TLS_ID, "allgreen")


def assert_all_green(t: float):
    s = ls.trafficlight.getRedYellowGreenState(TLS_ID)
    return (s == ALL_GREEN, "H-R7", f"TLS {TLS_ID} state {s} != {ALL_GREEN}")


def exit_loop_count() -> int:
    return ls.inductionloop.getLastIntervalVehicleNumber("exit_5_0")


# ---- gate_ctx_r6 S1 (docs/lab/gate_ctx_r6/s1_protocol.md §1): driver variants on BN4 geometry, lane changing off ------
VARIANTS = ("B0", "B2", "B3")
LC_OFF = ' lcStrategic="-1" lcSpeedGain="0" lcCooperative="0" lcKeepRight="0"'
# B3 classes at the nominal centre (§1.1): weight among cars, accel, decel, tau, minGap, speedFactor
B3_CLASSES = {"timid": (0.30, 2.0, 4.0, 1.3, 3.0, "normc(0.95,0.08,0.6,1.3)"),
              "normal": (0.40, 2.6, 4.5, 1.0, 2.5, "normc(1.00,0.10,0.6,1.5)"),
              "assertive": (0.30, 3.2, 5.0, 0.8, 1.8, "normc(1.08,0.10,0.7,1.6)")}
B3_TRUCK = (1.2, 3.5, 1.5, 3.0, "normc(0.95,0.05,0.8,1.1)")
B3_NC_SPEED = "normc(1.20,0.10,0.8,1.8)"
B3_CENTRE = {"truck_share": 0.10, "p_nc": 0.20, "weights": {k: v[0] for k, v in B3_CLASSES.items()}}
B3_N_SAMPLED = 20          # sampled vTypes per (class x compliance) cell and for trucks, if SUMO cannot sample natively
B3_JITTER = (0.85, 1.15)   # per-vehicle factor on accel, decel, tau, minGap


def b3_vtypes_xml(seed: int, av_share: float = 0.1, pop: dict | None = None) -> str:
    """vTypeDistribution 'human' of sampled EIDM vTypes (ids '<class>_<c|nc>_<k>', 'truck_<k>') + AV type 'av'.
    Probabilities: trucks pop.truck_share / (1 - av_share) of non-AVs; cars split by class weight x compliance."""
    import numpy as _np
    pop = pop or B3_CENTRE
    rng = _np.random.default_rng(seed + 7)
    p_truck = pop["truck_share"] / max(1.0 - av_share, 1e-9)
    lines, members = [], []

    def jit(x):
        return x * rng.uniform(*B3_JITTER)

    for cls, (_, a, b, tau, mg, sf) in B3_CLASSES.items():
        w = pop["weights"][cls]
        for comp, share, spd in (("c", 1.0 - pop["p_nc"], sf), ("nc", pop["p_nc"], B3_NC_SPEED)):
            for k in range(B3_N_SAMPLED):
                vid = f"{cls}_{comp}_{k}"
                lines.append(f'    <vType id="{vid}" carFollowModel="EIDM" accel="{jit(a):.3f}" decel="{jit(b):.3f}" '
                             f'tau="{jit(tau):.3f}" minGap="{jit(mg):.3f}" speedFactor="{spd}"{LC_OFF} '
                             f'probability="{(1.0 - p_truck) * w * share / B3_N_SAMPLED:.6f}"/>')
                members.append(vid)
    a, b, tau, mg, sf = B3_TRUCK
    for k in range(B3_N_SAMPLED):
        lines.append(f'    <vType id="truck_{k}" vClass="truck" carFollowModel="EIDM" length="12" maxSpeed="25" '
                     f'accel="{jit(a):.3f}" decel="{jit(b):.3f}" tau="{jit(tau):.3f}" minGap="{jit(mg):.3f}" '
                     f'speedFactor="{sf}"{LC_OFF} probability="{p_truck / B3_N_SAMPLED:.6f}"/>')
    return ('  <vTypeDistribution id="human">\n' + "\n".join(lines) + "\n  </vTypeDistribution>\n"
            f'  <vType id="av" carFollowModel="EIDM" speedFactor="1.0" speedDev="0"{LC_OFF} color="1,0,0"/>')


def variant_vtypes_xml(variant: str, seed: int, av_share: float = 0.1) -> str:
    if variant == "B0":
        return vtypes_xml(False)
    if variant == "B2":   # EIDM, every other car-following attribute at SUMO's default; AVs without speed noise
        return (f'  <vType id="human" carFollowModel="EIDM"{LC_OFF} color="1,1,1"/>\n'
                f'  <vType id="av" carFollowModel="EIDM" speedFactor="1.0" speedDev="0"{LC_OFF} color="1,0,0"/>')
    if variant == "B3":
        return b3_vtypes_xml(seed, av_share)
    raise ValueError(variant)


def type_class(type_id: str) -> str:
    """Class of a departed vehicle's type id (B3 health count); AV types may be renamed 'av@<vid>' by SUMO."""
    t = type_id.split("@")[0]
    if t in ("av", "human"):
        return t
    if t.startswith("truck_"):
        return "truck"
    parts = t.split("_")
    return f"{parts[0]}_{parts[1]}" if len(parts) == 3 else t


def demand_variant(seed: int, profile: list, variant: str, av_share: float = 0.1) -> Demand:
    d = Demand(vtypes_xml=variant_vtypes_xml(variant, seed, av_share),
               routes=[Route("main", ROUTE_EDGES, profile, av_share=av_share, depart_lane="random",
                             depart_speed="10")],
               step_length=STEP_LENGTH, seed=seed)
    d.generate()
    return d


class LoopBank:
    """10-s E1 loops of s1_protocol.md §2. Call poll() after every simulation step; it reads each loop's LAST closed
    interval (getLastInterval*) once per interval boundary and keeps the history."""

    def __init__(self):
        self.groups = net.loop_ids()
        self.period = net.LOOP_PERIOD_S
        self.t = []                     # interval end times
        self.data = {lid: [] for g in self.groups.values() for lid, _ in g}   # lid -> [(count, occ_frac, speed)]
        self.arrived_at = []            # network arrivals at each interval end (sensor-read check)
        self._next = self.period

    def poll(self, t: float, arrived: int | None = None) -> bool:
        if t < self._next - 1e-6:
            return False
        self.t.append(self._next)
        for lid in self.data:
            self.data[lid].append((ls.inductionloop.getLastIntervalVehicleNumber(lid),
                                   ls.inductionloop.getLastIntervalOccupancy(lid) / 100.0,
                                   ls.inductionloop.getLastIntervalMeanSpeed(lid)))
        self.arrived_at.append(arrived)
        self._next += self.period
        return True

    def section(self, group: str, i: int = -1, n: int = 1) -> tuple:
        """(count, mean occupancy, section speed) of a group over the last n intervals ending at index i."""
        ids = [lid for lid, _ in self.groups[group]]
        j1 = (len(self.t) if i == -1 else i + 1)
        j0 = max(0, j1 - n)
        cnt, occ, vs = 0, [], 0.0
        for lid in ids:
            for c, o, v in self.data[lid][j0:j1]:
                cnt += c
                occ.append(o)
                if c > 0 and v >= 0:
                    vs += c * v
        mo = sum(occ) / len(occ) if occ else 0.0
        if cnt > 0:
            sp = vs / cnt
        elif occ and mo >= 0.5:
            sp = 0.0
        else:
            sp = float("nan")
        return cnt, mo, sp

    def n_hat_edge4(self, lane_len: dict, l_eff: float = 5.0, n: int = 3) -> float:
        """Loop estimate of the vehicles on edge 4: sum over lanes of L / l_eff x mean 30-s occupancy at L4a/m/e."""
        if not self.t:
            return 0.0
        tot = 0.0
        for lane in (0, 1):
            occ = []
            for g in ("L4a", "L4m", "L4e"):
                lid = self.groups[g][lane][0]
                occ += [o for _, o, _ in self.data[lid][-n:]]
            tot += lane_len[f"4_{lane}"] / l_eff * (sum(occ) / len(occ))
        return tot

    def write_csv(self, path: Path) -> None:
        ids = list(self.data)
        with open(path, "w") as fh:
            fh.write("t,arrived," + ",".join(f"{lid}_{k}" for lid in ids for k in ("n", "occ", "v")) + "\n")
            for j, t in enumerate(self.t):
                row = [f"{t:g}", str(self.arrived_at[j] if self.arrived_at[j] is not None else "")]
                for lid in ids:
                    c, o, v = self.data[lid][j]
                    row += [str(c), f"{o:.4f}", f"{v:.3f}"]
                fh.write(",".join(row) + "\n")
