"""Per-vehicle fleet sampling (V156 dimensions, V158 sourced rows, V159 UK speeds, V160-V161 mix,
V164 default ACC gains).

Every vehicle gets its own vType, drawn from the episode seed (CRN: every arm of a seed sees the same vehicles). Each
attribute group has its own RNG stream, so adding a group does not change the others. Sources are the reference numbers
of docs/research/driver_params_hdv_cav_v0.md.

Classes (share of all vehicles, V160-V161): hdv_car 42.5 %, truck 7.5 % (human, trailer class), acc 12.5 %, cacc 12.5 %,
alks 25 % (the only commanded class).
Placeholders, labelled in every report: the HDV-car tau shape (beta matched to [1]'s moments until Fig. 5 is
digitised), the ALKS gap above 60 km/h (R157 60 km/h row, V159), the speedFactor truncation bounds (not sourced).
Not modelled yet: CACC latency and loss (SUMO's CACC communicates ideally), detector faults.
"""
from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass, field
from pathlib import Path
from unittest import mock

import numpy as np

from v5b.fleet import corridor
from v5b.p1c import plant as pl

LIMIT = 100.0 / 3.6
STEP = 0.1
TRUCK_MAX = 25.0

CLASSES = ("hdv_car", "truck", "acc", "cacc", "alks")
SHARES = (0.425, 0.075, 0.125, 0.125, 0.25)
COMMANDED = ("alks",)

# (EU-27 2020 share %, mean m, sd m): ICCT shares x Laveneziana et al. 2025 Fig. 21 (V156)
CAR_SEGMENTS = ((38.3, 4.40, 0.18), (22.6, 4.40, 0.12), (17.8, 4.00, 0.08), (6.6, 3.55, 0.10),
                (6.2, 4.75, 0.10), (5.4, 5.00, 0.20), (2.0, 4.95, 0.05), (1.1, 4.80, 0.30))
CAR_LEN_CLIP = (3.0, 6.0)
CAR_WIDTH = (1.78, 0.03, 1.65, 1.92)
TRUCK_LEN, TRUCK_WIDTH = (15.5, 16.5), (2.50, 2.55)

# speedFactor x 100 km/h: UK motorway free-flow bins [90] (V159); the clip bounds are not sourced
CAR_SF = (0.98, 0.12, 0.56, 1.40)
TRUCK_SF = (0.878, 0.055, 0.60, 1.20)

# HDV-car Krauss: tau placeholder = beta on [0.2, 2.0] matched to mean 1.15 s, SD 0.43 s [1]
TAU_RANGE, TAU_MEAN, TAU_SD = (0.2, 2.0), 1.15, 0.43
# piecewise-linear quantiles through [50] Table 4 (P0 = lower bound, P10, P50, upper value read as P95, P100 = bound)
ASL_Q = ((0.0, 0.10, 0.50, 0.95, 1.0), (0.1, 0.10, 0.30, 0.90, 1.0))
SIGMA_Q = ((0.0, 0.10, 0.50, 0.95, 1.0), (0.1, 0.12, 0.30, 0.75, 1.0))

ACC_TAU = ((1.1, 0.504), (1.6, 0.185), (2.2, 0.311))                     # [18]
CACC_TAU = ((0.6, 0.57), (0.7, 0.24), (0.9, 0.07), (1.1, 0.12))          # [18]
ALKS_TAU = 1.6                                                           # R157 60 km/h row [22], placeholder above
# the ACC class uses SUMO's default gains (V164); the original controller (modes iii and iv reset, SUMO ACC docs)
# collided 92-202 times per smoke run (V162) and is kept for the behaviour test and smoke variants
ACC_GAINS: dict = {}
ACC_ORIGINAL = {"gapClosingControlGainSpeed": 0.07, "gapClosingControlGainSpace": 0.23,
                "collisionAvoidanceGainSpeed": 0.07, "collisionAvoidanceGainSpace": 0.23,
                "collisionAvoidanceOverride": 100}

# variant knob (V168 test): followers of a CAV assume it may brake this hard (SUMO apparentDecel); None = SUMO default
CAV_APPARENT_DECEL: float | None = None

# CAV car-following models; IDM variants for the V169/V171 tests (SUMO's ACC brakes hard at queue tails)
CAV_MODELS = {"acc": "ACC", "cacc": "CACC", "alks": "ACC"}

# calibration knobs (V177): HDV-car tau scale (shape kept) and accel; None = SUMO default
HDV_TAU_SCALE = 1.0
HDV_ACCEL: float | None = None
HDV_ASL_SCALE = 1.0
# V192 test: LC2013 lcAssertive for vehicles entering by the on-ramp; None = SUMO default
RAMP_LC_ASSERTIVE: float | None = None
# V199: tau factor for human drivers passing an active crash (v5b/fleet/incident.py); 1.0 = off
INCIDENT_TAU_FACTOR = 1.0

# diagnosis knobs (V178): fix every HDV car's action step or sigma; None = sourced draw
HDV_ASL_FIXED: float | None = None
HDV_TAU_FIXED: float | None = None
# Krauss dawdling redraw interval for humans (SUMO sigmaStep; default = step length); V178 test
HDV_SIGMA_STEP: float | None = None
HDV_SIGMA_FIXED: float | None = None

STREAMS = {"class": 1, "dims": 2, "speed": 3, "cf": 4, "lane": 5, "route": 6}


def _beta_ab(lo: float, hi: float, mean: float, sd: float) -> tuple:
    m, v = (mean - lo) / (hi - lo), (sd / (hi - lo)) ** 2
    k = m * (1 - m) / v - 1
    return m * k, (1 - m) * k


TAU_AB = _beta_ab(*TAU_RANGE, TAU_MEAN, TAU_SD)


def _rng(seed: int, stream: str) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(STREAMS[stream],)))


def _normc(r, mean, sd, lo, hi) -> float:
    while True:
        x = r.normal(mean, sd)
        if lo <= x <= hi:
            return float(x)


def _quantile(r, q) -> float:
    return float(np.interp(r.random(), q[0], q[1]))


def _discrete(r, table) -> float:
    vals, p = zip(*table)
    return float(r.choice(vals, p=np.array(p) / sum(p)))


@dataclass
class VehSpec:
    vid: str
    cls: str
    depart: float
    lane: int
    length: float
    width: float
    sf: float
    tau: float | None = None
    sigma: float | None = None
    asl: float | None = None
    resampled: int = 0
    extra: dict = field(default_factory=dict)
    lc: dict = field(default_factory=dict)

    @property
    def desired(self) -> float:
        v = self.sf * LIMIT
        return min(v, TRUCK_MAX) if self.cls == "truck" else v

    def vtype_xml(self) -> str:
        a = {"id": f"t.{self.vid}", "length": f"{self.length:.3f}", "width": f"{self.width:.3f}",
             "laneChangeModel": "LC2013", "lcCooperative": "1", **{k: f"{v:g}" for k, v in self.lc.items()}}
        if self.cls == "hdv_car":
            a |= {"vClass": "passenger", "carFollowModel": "Krauss", "tau": f"{self.tau:.3f}",
                  "sigma": f"{self.sigma:.3f}", "actionStepLength": f"{self.asl:.1f}"}
            if HDV_ACCEL is not None:
                a["accel"] = f"{HDV_ACCEL:g}"
        elif self.cls == "truck":
            a |= {"vClass": "trailer", "carFollowModel": "Krauss", "maxSpeed": f"{TRUCK_MAX:g}"}
        else:
            a |= {"vClass": "passenger", "carFollowModel": CAV_MODELS[self.cls], "tau": f"{self.tau:g}"}
        if self.cls in ("hdv_car", "truck") and HDV_SIGMA_STEP is not None:
            a["sigmaStep"] = f"{HDV_SIGMA_STEP:g}"
        if self.cls in ("acc", "cacc", "alks") and CAV_APPARENT_DECEL is not None:
            a["apparentDecel"] = f"{CAV_APPARENT_DECEL:g}"
        if self.cls != "acc" or CAV_MODELS["acc"] == "ACC":     # ACC gains exist only in SUMO's ACC model
            a |= {k: f"{v:g}" for k, v in self.extra.items()}
        return "  <vType " + " ".join(f'{k}="{v}"' for k, v in a.items()) + "/>"


def sample(n: int, seed: int, n_lanes: int, departs: list) -> list:
    """n vehicle specs in departure order; the draw order inside each stream is fixed."""
    rc, rd, rs, rf, rl = (_rng(seed, s) for s in ("class", "dims", "speed", "cf", "lane"))
    seg_p = np.array([s[0] for s in CAR_SEGMENTS]) / sum(s[0] for s in CAR_SEGMENTS)
    out = []
    for i in range(n):
        cls = CLASSES[int(rc.choice(len(CLASSES), p=SHARES))]
        if cls == "truck":
            length, width = float(rd.uniform(*TRUCK_LEN)), float(rd.uniform(*TRUCK_WIDTH))
            sf = _normc(rs, *TRUCK_SF)
        else:
            k = int(rd.choice(len(CAR_SEGMENTS), p=seg_p))
            length = float(np.clip(rd.normal(CAR_SEGMENTS[k][1], CAR_SEGMENTS[k][2]), *CAR_LEN_CLIP))
            width = _normc(rd, *CAR_WIDTH)
            sf = 1.0 if cls == "alks" else _normc(rs, *CAR_SF)
        v = VehSpec(f"main.{i}", cls, departs[i], int(rl.integers(0, n_lanes)), round(length, 3), round(width, 3),
                    round(sf, 4))
        if cls == "hdv_car":
            while True:                       # tau >= actionStepLength per vehicle (note §4)
                tau = HDV_TAU_SCALE * (TAU_RANGE[0] + (TAU_RANGE[1] - TAU_RANGE[0]) * float(rf.beta(*TAU_AB)))
                asl = max(0.1, round(HDV_ASL_SCALE * _quantile(rf, ASL_Q) * 10) / 10)
                sig = _quantile(rf, SIGMA_Q)
                if tau >= asl:
                    break
                v.resampled += 1
            v.tau, v.sigma, v.asl = round(tau, 3), round(sig, 3), asl
            if HDV_ASL_FIXED is not None:
                v.asl = HDV_ASL_FIXED
            if HDV_SIGMA_FIXED is not None:
                v.sigma = HDV_SIGMA_FIXED
            if HDV_TAU_FIXED is not None:
                v.tau = HDV_TAU_FIXED
        elif cls == "acc":
            v.tau, v.extra = _discrete(rf, ACC_TAU), dict(ACC_GAINS)
        elif cls == "cacc":
            v.tau = _discrete(rf, CACC_TAU)
        elif cls == "alks":
            v.tau = ALKS_TAU
        out.append(v)
    return out


# BN4 with a 3 km longer entry edge (V169): the peak queues (up to about 1.2 km in V168) stay inside the network
UPSTREAM_EXTRA = 3000.0
pl.GEOMS.setdefault("bn4x", {**pl.GEOMS["bn4"], "nodes": [(n, x if n == "1" else x + UPSTREAM_EXTRA)
                                                          for n, x in pl.GEOMS["bn4"]["nodes"]]})




def _lane_drop(n: int) -> dict:
    """V184 corridor: entry 3,000 m, 310 m, approach 1,000 m (n lanes), drop, bottleneck 1,000 m, exit 500 m (n-1).
    Breakdown loops 'up' at the start of the approach (V186), outside the lane-change zone before the drop."""
    x = (0.0, 3000.0, 3310.0, 4310.0, 5310.0, 5810.0)
    return {"nodes": [(str(i + 1), v) for i, v in enumerate(x)],
            "lanes": {"1": n, "2": n, "3": n, "4": n - 1, "5": n - 1}, "drops": ("4",), "bott_edge": "4",
            "block_pos": 250.0, "loops": {"e4": [("4", 100.0)], "e5": [("5", "mid")], "exit": [("5", -15.0)],
                                          "e3": [("3", -20.0)], "up": [("3", 10.0)]}}   # V186: ~1 km before the drop


pl.GEOMS.setdefault("ld32", _lane_drop(3))
pl.GEOMS.setdefault("ld43", _lane_drop(4))


PLANTS = {"v188": {"geom": "ld32", "merge": "laneend", "tau_scale": 0.8, "asl_scale": 0.5,
                   "cav_models": {"acc": "IDM", "cacc": "IDM", "alks": "IDM"}}}
PLANTS["v190"] = {**PLANTS["v188"], "geom": corridor.NAME, "teleport": False}   # teleporting off: V197
PLANTS["v199"] = {**PLANTS["v190"], "incident_tau_factor": 3.0}   # passing zone calibrated in V200


def apply_plant(name: str, cfg: pl.Config) -> pl.Config:
    """Set the module knobs of an adopted plant (V188) and return its config."""
    global HDV_TAU_SCALE, HDV_ASL_SCALE, INCIDENT_TAU_FACTOR
    p = PLANTS[name]
    HDV_TAU_SCALE, HDV_ASL_SCALE = p["tau_scale"], p["asl_scale"]
    INCIDENT_TAU_FACTOR = p.get("incident_tau_factor", 1.0)
    CAV_MODELS.update(p["cav_models"])
    return dataclasses.replace(cfg, geom=p["geom"], merge=p["merge"])


def build_net(cfg: pl.Config) -> Path:
    """The p1c geometry (or the V190 on-ramp corridor) with a 100 km/h limit on every edge (V156)."""
    if cfg.geom == corridor.NAME:
        return corridor.build(LIMIT)
    if cfg.geom in corridor.STRAIGHT:
        return corridor.build_straight(cfg.geom, LIMIT)
    with mock.patch.object(pl, "SPEED", LIMIT):
        return pl.build_net(cfg)


def loop_ids(geom: str) -> dict:
    if geom in corridor.STRAIGHT:
        return corridor.straight_loop_ids(geom)
    return corridor.loop_ids() if geom == corridor.NAME else pl.loop_ids(geom)


def all_green(geom: str) -> None:
    """No control: the p1c mainline signal or the V190 ramp meter stays green."""
    import libsumo as ls
    for tls in ls.trafficlight.getIDList():
        if geom == corridor.NAME or tls == pl.TLS_ID:
            ls.trafficlight.setRedYellowGreenState(tls, "G" * len(ls.trafficlight.getRedYellowGreenState(tls)))


def routes(geom: str) -> dict:
    """route id -> (edges, share of vehicles, entry lanes)."""
    if geom == corridor.NAME:
        return {r: (e, corridor.RAMP_SHARE if r == "ramp" else 1 - corridor.RAMP_SHARE, corridor.ENTRY_LANES[r])
                for r, e in corridor.ROUTES.items()}
    if geom in corridor.STRAIGHT:
        return {"main": ("a", 1.0, corridor.STRAIGHT[geom])}
    return {"main": (pl.ROUTE_EDGES, 1.0, pl.lanes(geom, "1"))}


class FleetDemand:
    """Poisson arrivals as in p1c (same rng(seed) arrival stream), with the sampled fleet; interface-compatible with
    v5b/d1/sumo_runner.SumoSim."""

    def __init__(self, seed: int, profile: list, cfg: pl.Config):
        rng = np.random.default_rng(seed)
        deps = []
        for (t0, t1, q) in profile:
            if q <= 0 or t1 <= t0:
                continue
            t = t0
            while True:
                t += rng.exponential(3600.0 / q)
                if t >= t1:
                    break
                deps.append(round(math.ceil(t / cfg.step - 1e-9) * cfg.step, 3))
        self.cfg, self.seed, self.profile = cfg, seed, profile
        self.routes = routes(cfg.geom)
        names = list(self.routes)
        rr = _rng(seed, "route")
        self.route_of = [names[int(rr.choice(len(names), p=[self.routes[n][1] for n in names]))]
                         for _ in deps]
        self.veh = sample(len(deps), seed, max(v[2] for v in self.routes.values()), deps)
        for v, r in zip(self.veh, self.route_of):
            v.lane = v.lane % self.routes[r][2]
            if r == "ramp" and RAMP_LC_ASSERTIVE is not None:
                v.lc = {"lcAssertive": RAMP_LC_ASSERTIVE}
        self.by_id = {v.vid: v for v in self.veh}
        self.vehicles = [(v.depart, v.vid, r, f"t.{v.vid}") for v, r in zip(self.veh, self.route_of)]

    @property
    def depart_times(self) -> list:
        return [v[0] for v in self.vehicles]

    def counts_by_route(self) -> dict:
        return {"main": len(self.veh)}

    def write(self, path: Path) -> None:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>"]
        lines += [f'  <route id="{r}" edges="{e[0]}"/>' for r, e in self.routes.items()]
        lines += [v.vtype_xml() for v in self.veh]
        lines += [f'  <vehicle id="{v.vid}" type="t.{v.vid}" route="{r}" depart="{v.depart:.2f}" departLane="{v.lane}" '
                  f'departSpeed="max" speedFactor="{v.sf}"/>' for v, r in zip(self.veh, self.route_of)]
        path.write_text("\n".join(lines + ["</routes>"]) + "\n")
