"""BN4 plant: Vinitsky et al. (2018) bottleneck in SUMO 1.27.

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
            f'  <vType id="av" {common} speedFactor="1.0"{lc} color="1,0,0"/>')


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
