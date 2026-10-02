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


PLANTS = {"v1": ("krauss", "max"), "v2": ("idm", "max"), "v3": ("idm", "avg")}   # (car model, departSpeed)

# Plant-realism gate driver variants (docs/lab/t2_realism_protocol.md). Values are vType attributes (cars, trucks)
# plus extra SUMO options. SUMO silently ignores unknown vType attributes, so every variant is also checked
# behaviourally (its NC run must differ from H0's).
_IDM_CAR = 'carFollowModel="IDM" accel="1.0" decel="1.5" tau="1.0" minGap="2.0" delta="4" length="5"'
_IDM_TRK = 'carFollowModel="IDM" accel="0.6" decel="1.5" tau="1.5" minGap="2.5" delta="4" length="12" maxSpeed="25"'
_EIDM_IMP = 'sigmaleader="0.2" sigmagap="0.2" sigmaerror="0.3" treaction="0.6"'
DRIVERS = {
    "H0": {"car": _IDM_CAR, "trk": _IDM_TRK, "args": []},
    "H1": {"car": _IDM_CAR + ' actionStepLength="1.0"', "trk": _IDM_TRK + ' actionStepLength="1.0"', "args": []},
    "H2": {"car": _IDM_CAR, "trk": _IDM_TRK,
           "args": ["--device.driverstate.probability", "1.0", "--device.driverstate.initialAwareness", "0.7"]},
    "H3": {"car": 'carFollowModel="W99" length="5"', "trk": 'carFollowModel="W99" length="12" maxSpeed="25"', "args": []},
    "H4": {"car": _IDM_CAR.replace('"IDM"', '"EIDM"') + " " + _EIDM_IMP,
           "trk": _IDM_TRK.replace('"IDM"', '"EIDM"') + " " + _EIDM_IMP, "args": []},
    # Addendum A: EIDM with every EIDM-specific parameter at its SUMO default (errors included per the SUMO vType table)
    "H5": {"car": _IDM_CAR.replace('"IDM"', '"EIDM"'), "trk": _IDM_TRK.replace('"IDM"', '"EIDM"'), "args": []},
}


def cav_vtype_xml(cav_model: str = "CACC") -> str:
    """Round 3 CAV (round3_tm21_protocol.md): SUMO ACC/CACC with every model parameter at its default. maxSpeed = the
    120 km/h limit and speedFactor 1.5, so the lane limit never binds: the set speed (setMaxSpeed, managed by
    controllers/cav_staircase.py) alone sets the desired speed (exact compliance when it equals the posted limit)."""
    return (f'  <vType id="cav" carFollowModel="{cav_model}" length="5" maxSpeed="{V_LIMIT}" speedFactor="1.5" '
            'speedDev="0"/>')


def vtypes_xml(p_noncompliant: float = 0.3, truck_share: float = 0.1, model: str = "krauss",
               driver: str | None = None, cav_share: float = 0.0, cav_model: str = "CACC") -> str:
    """model='krauss' = MRG3-v1 (SUMO defaults); model='idm' = MRG3-v2/v3 (Treiber-style IDM). driver=H0..H5
    overrides the car/truck models with a realism-gate variant (DRIVERS). cav_share > 0 adds the `cav` vType; the
    human mix's truck weight is rescaled so that trucks stay `truck_share` of ALL vehicles."""
    if cav_share > 0:
        truck_share = truck_share / (1.0 - cav_share)
    pc = (1.0 - p_noncompliant) * (1.0 - truck_share)
    pn = p_noncompliant * (1.0 - truck_share)
    if driver is not None:
        car, trk = DRIVERS[driver]["car"] + " ", DRIVERS[driver]["trk"] + " "
    elif model == "idm":
        car, trk = _IDM_CAR + " ", _IDM_TRK + " "
    else:
        car = ""
        trk = 'length="12" accel="1.3" decel="4.0" maxSpeed="25" '
    return (
        '  <vTypeDistribution id="mix">\n'
        f'    <vType id="car_c" probability="{pc:.4f}" {car}speedFactor="normc(1.0,0.05,0.8,1.2)"/>\n'
        f'    <vType id="car_n" probability="{pn:.4f}" {car}speedFactor="normc(1.15,0.05,0.95,1.4)"/>\n'
        f'    <vType id="truck" vClass="truck" probability="{truck_share:.4f}" {trk}'
        'speedFactor="normc(1.0,0.05,0.8,1.2)"/>\n'
        '  </vTypeDistribution>' + ("\n" + cav_vtype_xml(cav_model) if cav_share > 0 else ""))


def demand(seed: int, main_profile: list, ramp_profile: list, p_noncompliant: float = 0.3,
           truck_share: float = 0.1, model: str = "krauss", depart_speed: str = "max", driver: str | None = None,
           cav_share: float = 0.0, cav_model: str = "CACC", step_length: float | None = None) -> Demand:
    # av_share draws one rng.random() per vehicle whatever its value, so arrival times are identical across cav_share
    d = Demand(vtypes_xml=vtypes_xml(p_noncompliant, truck_share, model, driver, cav_share, cav_model),
               routes=[Route("main", net.MAIN_ROUTE, main_profile, av_share=cav_share, depart_lane="best",
                             depart_speed=depart_speed),
                       Route("ramp", net.RAMP_ROUTE, ramp_profile, av_share=cav_share, depart_lane="0",
                             depart_speed=depart_speed)],
               step_length=step_length or STEP_LENGTH, seed=seed, human_type="mix",
               av_type="cav" if cav_share > 0 else "mix")
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
