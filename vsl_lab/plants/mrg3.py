"""MRG3 plant (Track 2): posted VSL at an on-ramp merge with partial compliance.

Vehicles: SUMO defaults (Krauss, sigma 0.5, tau 1, LC2013) for cars; trucks (length 12, accel 1.3, maxSpeed 25 m/s,
share `truck_share`). Compliance with the posted limit is modelled by speedFactor groups (desired speed =
speedFactor x lane max speed): compliant ~ normc(1.0, 0.05, 0.8, 1.2); non-compliant ~ normc(1.15, 0.05, 0.95, 1.4)
with share `p_noncompliant` (a hidden condition candidate). Posted VSL = lane.setMaxSpeed on the VSL area lanes.
Demand: piecewise-constant mainline and ramp profiles (rise, peak, fall), explicit Poisson vehicles.
"""
from __future__ import annotations

import json
from pathlib import Path

import libsumo as ls
import numpy as np

from vsl_lab.netgen import mrg3 as net
from vsl_lab.sim.demand import Demand, Route

STEP_LENGTH = 0.5
V_LIMIT = 33.33


def vtypes_xml(p_noncompliant: float = 0.3, truck_share: float = 0.1, model: str = "krauss") -> str:
    """model='krauss' = MRG3-v1 (SUMO defaults); model='idm' = MRG3-v2 (Treiber-style IDM, pre-registered 2026-10-02)."""
    pc = (1.0 - p_noncompliant) * (1.0 - truck_share)
    pn = p_noncompliant * (1.0 - truck_share)
    if model == "idm":
        car = 'carFollowModel="IDM" accel="1.0" decel="1.5" tau="1.0" minGap="2.0" delta="4" length="5" '
        trk = 'carFollowModel="IDM" accel="0.6" decel="1.5" tau="1.5" minGap="2.5" delta="4" length="12" maxSpeed="25" '
    else:
        car = ""
        trk = 'length="12" accel="1.3" decel="4.0" maxSpeed="25" '
    return (
        '  <vTypeDistribution id="mix">\n'
        f'    <vType id="car_c" probability="{pc:.4f}" {car}speedFactor="normc(1.0,0.05,0.8,1.2)"/>\n'
        f'    <vType id="car_n" probability="{pn:.4f}" {car}speedFactor="normc(1.15,0.05,0.95,1.4)"/>\n'
        f'    <vType id="truck" vClass="truck" probability="{truck_share:.4f}" {trk}'
        'speedFactor="normc(1.0,0.05,0.8,1.2)"/>\n'
        '  </vTypeDistribution>')


def demand(seed: int, main_profile: list, ramp_profile: list, p_noncompliant: float = 0.3,
           truck_share: float = 0.1, model: str = "krauss") -> Demand:
    d = Demand(vtypes_xml=vtypes_xml(p_noncompliant, truck_share, model),
               routes=[Route("main", net.MAIN_ROUTE, main_profile, depart_lane="best", depart_speed="max"),
                       Route("ramp", net.RAMP_ROUTE, ramp_profile, depart_lane="0", depart_speed="max")],
               step_length=STEP_LENGTH, seed=seed, human_type="mix", av_type="mix")
    d.generate()
    return d


def profile(q_base: float, q_peak: float, t_rise: float, t_peak: float, t_fall: float, t_end: float,
            step: float = 60.0) -> list:
    """Piecewise-constant trapezoid: base until t_rise, linear ramp to peak by t_peak, peak until t_fall,
    linear back to base by t_fall + (t_peak - t_rise), base until t_end. Resolution `step` seconds."""
    out = []
    t = 0.0
    up = t_peak - t_rise
    while t < t_end - 1e-9:
        tm = t + step / 2
        if tm < t_rise:
            q = q_base
        elif tm < t_peak:
            q = q_base + (q_peak - q_base) * (tm - t_rise) / up
        elif tm < t_fall:
            q = q_peak
        elif tm < t_fall + up:
            q = q_peak - (q_peak - q_base) * (tm - t_fall) / up
        else:
            q = q_base
        out.append((t, min(t + step, t_end), q))
        t += step
    return out


def files() -> dict:
    d = net.build()
    return {"net": d / "mrg3.net.xml", "add": d / "mrg3.det.add.xml", "dir": d,
            "lanes": json.loads((d / "lanes.json").read_text())}


class Sensors:
    """Last-interval E1/E2 readings (getLastInterval*; the just-started interval is never read)."""

    def __init__(self, lanes: dict):
        self.lanes = lanes

    @staticmethod
    def flow_vph_per_lane(edge: str, n_lanes: int = 3) -> float:
        n = sum(ls.inductionloop.getLastIntervalVehicleNumber(f"e1_{edge}_{i}") for i in range(n_lanes))
        per = 30.0
        return n * 3600.0 / per / n_lanes

    @staticmethod
    def speed_kmh(edge: str, n_lanes: int = 3) -> float:
        vs = [ls.inductionloop.getLastIntervalMeanSpeed(f"e1_{edge}_{i}") for i in range(n_lanes)]
        vs = [v for v in vs if v >= 0]
        return float(np.mean(vs)) * 3.6 if vs else -1.0

    def density_merge_vkl(self) -> float:
        """Bottleneck density (veh/km/lane) from current vehicle counts on the merge lanes 1-3 (+ acc. lane)."""
        n = sum(ls.lanearea.getLastStepVehicleNumber(f"e2_merge_{i}") for i in range(4))
        L = self.lanes["merge_1"] / 1000.0
        return n / (L * 3.0)

    def density_down_vkl(self) -> float:
        n = sum(ls.lanearea.getLastStepVehicleNumber(f"e2_down_{i}") for i in range(3))
        return n / (0.3 * 3.0)


def set_vsl(edges, v_ms: float) -> None:
    for e in edges:
        for i in range(3):
            ls.lane.setMaxSpeed(f"{e}_{i}", v_ms)
