"""CORR2 plant (Track 4): freeway corridor with two metered on-ramps, an off-ramp and two posted-VSL areas.

Network: vsl_lab/netgen/corr2.py (geometry, detectors, meter TLS). Vehicles: MRG3's vtypes_xml with driver "H5"
(EIDM with every EIDM-specific parameter at its SUMO default; 30 % non-compliant speedFactor group; 10 % trucks).
Step 0.2 s. Demand: explicit Poisson vehicles (vsl_lab/sim/demand.py), one Route per origin-destination stream:
  main_ex  (mainline origin -> exit)       rate (1 - off_share) x q_main(t)
  main_off (mainline origin -> off-ramp O1) rate off_share x q_main(t)
  r1_ex / r1_off (on-ramp R1 -> exit / O1)  rates (1 - off_share) / off_share x q_r1(t)
  r2_ex    (on-ramp R2 -> exit)             rate q_r2(t)
Splitting a Poisson stream by independent Bernoulli(off_share) choices gives independent Poisson streams with the
split rates, so this equals "20 % of mainline-origin and R1 vehicles exit at O1". Each profile is MRG3's trapezoid
(base = 50 % of peak until 600 s, linear rise to the peak by 1200 s, peak to 3000 s, linear fall by 3600 s, base to
3900 s). departSpeed "avg" everywhere; departLane "best" on the mainline and "0" on the ramps.

Ramp meters (Meter): one-vehicle-per-green signals at the downstream end of R1 / R2. A metering rate r (veh/h) is
implemented as a green every C = 3600 / r s (fractional clock, so the long-run number of greens equals r although
states change on the 0.2 s step grid; a new rate takes effect at the next green); C <= 2 s (r >= 1800 veh/h) means
permanent green. Green = 2 s, extended ("passage-terminated green", default extend=True) until the head vehicle
that was waiting within 15 m of the stop line at green start has left the ramp lane, at most 4 s; between greens
the signal shows YELLOW (no red, default red=False), at least 1 s.
Why no red (smoke check 2026-10-03, seed 7140000): with G 2 s / y 1 s / r, vehicles approaching at 25 m/s with the
EIDM decel of 1.5 m/s^2 (comfortable braking distance ~208 m) commit on green or yellow, are caught by the red and
SUMO stops them at the lane end with decel 9-14 m/s^2 ("emergency stop ... because of a red traffic light"; 7 such
warnings in 360 s at r = 600 veh/h). SUMO's yellow rule is "stop if the vehicle can brake before the stop line with
its decel, else drive on", so a yellow after the green acts as a red for every vehicle that can stop comfortably
(all queued, slow vehicles) and lets pass only vehicles already unable to stop comfortably (0 warnings in the
re-check). Consequence: with no queue, a vehicle arriving at speed can pass without stopping, so the realised ramp
flow is about min(arrivals, r) plus some leakage; with a queue the discharge is one vehicle per green.
Why the extension (same check): with a fixed 2 s green a queued EIDM vehicle starting from rest (EIDM's default
start-up dynamics) sometimes does not cross the stop line within 2 s and stops again at the yellow; at r = 400
veh/h with a standing queue only ~5.3 of 6.67 greens per minute released a vehicle.
"""
from __future__ import annotations

import json

import libsumo as ls
import numpy as np

from vsl_lab.netgen import corr2 as net
from vsl_lab.plants import mrg3 as _mrg3
from vsl_lab.sim.demand import Demand, Route

STEP_LENGTH = 0.2
V_LIMIT = 33.33
OFF_SHARE = 0.2
GROUPS = {"main": ("main_ex", "main_off"), "r1": ("r1_ex", "r1_off"), "r2": ("r2_ex",),
          "offramp": ("main_off", "r1_off"), "through_main": ("main_ex",)}
RAMP_ROUTES = {"R1": ("r1_ex", "r1_off"), "R2": ("r2_ex",)}
profile = _mrg3.profile
vtypes_xml = _mrg3.vtypes_xml
DRIVERS = _mrg3.DRIVERS


def files() -> dict:
    d = net.build()
    lanes = json.loads((d / "lanes.json").read_text())
    return {"net": d / "corr2.net.xml", "add": d / "corr2.det.add.xml", "dir": d, "lanes": lanes}


def _scaled(prof: list, s: float) -> list:
    return [(a, b, q * s) for a, b, q in prof]


def demand(seed: int, q_main: float, q_r1: float, q_r2: float, off_share: float = OFF_SHARE,
           p_noncompliant: float = 0.3, truck_share: float = 0.1, driver: str = "H5",
           step_length: float = STEP_LENGTH, t_end: float = 3900.0, base_frac: float = 0.5) -> Demand:
    pm = profile(base_frac * q_main, q_main, 600.0, 1200.0, 3000.0, t_end)
    p1 = profile(base_frac * q_r1, q_r1, 600.0, 1200.0, 3000.0, t_end)
    p2 = profile(base_frac * q_r2, q_r2, 600.0, 1200.0, 3000.0, t_end)
    R = net.ROUTES
    routes = [Route("main_ex", R["main_ex"], _scaled(pm, 1.0 - off_share), depart_lane="best", depart_speed="avg"),
              Route("main_off", R["main_off"], _scaled(pm, off_share), depart_lane="best", depart_speed="avg"),
              Route("r1_ex", R["r1_ex"], _scaled(p1, 1.0 - off_share), depart_lane="0", depart_speed="avg"),
              Route("r1_off", R["r1_off"], _scaled(p1, off_share), depart_lane="0", depart_speed="avg"),
              Route("r2_ex", R["r2_ex"], p2, depart_lane="0", depart_speed="avg")]
    d = Demand(vtypes_xml=vtypes_xml(p_noncompliant, truck_share, driver=driver), routes=routes,
               step_length=step_length, seed=seed, human_type="mix", av_type="mix")
    d.generate()
    return d


def set_vsl(edges, v_ms: float) -> None:
    for e in edges:
        for i in range(net.N_LANES[e]):
            ls.lane.setMaxSpeed(f"{e}_{i}", v_ms)


class Meter:
    """One-vehicle-per-green ramp meter on TLS `tls` (exactly one controlled link, from lane `<ramp>_0`).

    Phases: G (green) then y (yellow) until the next green; red=True replaces the post-green yellow by y 1 s + r.
    Green start: every C = 3600 / r s on a fractional clock (missed starts are skipped, never made up), and never
    earlier than Y_MIN_S after the previous green ended. extend=True ("passage-terminated green"): if a head vehicle
    is waiting within HEAD_ZONE_M of the stop line at green start, the green lasts until it has left the ramp lane,
    at least GREEN_S and at most G_MAX_S; with no waiting vehicle the green is GREEN_S.
    """
    GREEN_S = 2.0
    YELLOW_S = 1.0       # red=True variant only
    G_MAX_S = 4.0
    Y_MIN_S = 1.0
    HEAD_ZONE_M = 15.0

    def __init__(self, tls: str, ramp: str | None = None, lane_len: float | None = None, red: bool = False,
                 extend: bool = True):
        self.tls = tls
        self.lane = f"{ramp}_0" if ramp else None
        self.lane_len = lane_len
        self.red = red
        self.extend = extend and ramp is not None
        self.cycle = None          # None = permanent green
        self.rate = None
        self.t_green = 0.0         # start of the current / last green
        self.t_gend = -1e9         # end of the last green
        self.in_green = False
        self.head = None           # waiting head vehicle at green start (extend mode)
        self.state = None
        self.n_greens = 0
        self.n_head_greens = 0     # greens that started with a waiting head vehicle
        self.n_head_passed = 0     # ... whose head vehicle left the ramp lane during the green
        self.green_s_sum = 0.0

    def _set(self, st: str) -> None:
        if st != self.state:
            ls.trafficlight.setRedYellowGreenState(self.tls, st)
            self.state = st

    def all_green_program(self) -> None:
        ls.trafficlight.setProgram(self.tls, "allgreen")
        self.state, self.cycle, self.rate, self.in_green = "G", None, None, False

    def release(self) -> None:
        if self.in_green:
            self._end_green(None)
        self.cycle, self.rate = None, None
        self._set("G")

    def _waiting_head(self):
        if self.lane is None:
            return None
        best, best_pos = None, -1.0
        for v in ls.lane.getLastStepVehicleIDs(self.lane):
            pos = ls.vehicle.getLanePosition(v)
            if pos > best_pos:
                best, best_pos = v, pos
        if best is not None and self.lane_len - best_pos <= self.HEAD_ZONE_M:
            return best
        return None

    def _start_green(self, t: float) -> None:
        self.in_green = True
        self.n_greens += 1
        self.head = self._waiting_head() if self.extend else None
        if self.head is not None:
            self.n_head_greens += 1
        self._set("G")

    def _end_green(self, t: float | None) -> None:
        self.in_green = False
        if t is not None:
            self.green_s_sum += t - self.t_green
            self.t_gend = t
        self._set("y")

    def set_rate(self, r: float, t: float) -> None:
        self.rate = float(r)
        c = 3600.0 / max(r, 1e-6)
        if c <= self.GREEN_S + 1e-9:
            self.cycle = None
            self.in_green = False
            self._set("G")
            return
        if self.cycle is None:         # metering starts: a green begins now
            self.cycle = c
            self.t_green = t
            self._start_green(t)
            return
        self.cycle = c

    def _head_gone(self) -> bool:
        try:
            return ls.vehicle.getLaneID(self.head) != self.lane
        except ls.TraCIException:
            return True

    def tick(self, t: float) -> None:
        if self.cycle is None:
            return
        tau = t - self.t_green
        if self.in_green:
            if self.head is not None:
                gone = self._head_gone()
                done = (tau >= self.GREEN_S - 1e-9 and gone) or tau >= self.G_MAX_S - 1e-9
                if done and gone:
                    self.n_head_passed += 1
            else:
                done = tau >= self.GREEN_S - 1e-9
            if done:
                self._end_green(t)
            return
        nxt = self.t_green + self.cycle
        if t >= nxt - 1e-9 and t - self.t_gend >= self.Y_MIN_S - 1e-9:
            while t - nxt >= self.cycle - 1e-9:      # starts missed by a long green are skipped
                nxt += self.cycle
            self.t_green = nxt
            self._start_green(t)
            return
        if self.red and t - self.t_gend >= self.YELLOW_S - 1e-9:
            self._set("r")


class Sensors:
    """Last-interval E1/E2 readings (getLastInterval*; the running interval is never read)."""

    def __init__(self, lanes: dict):
        self.lanes = lanes
        self._space = {}

    @staticmethod
    def flow_vph_per_lane(edge: str, period: float = 30.0) -> float:
        n_l = net.N_LANES[edge]
        n = sum(ls.inductionloop.getLastIntervalVehicleNumber(f"e1_{edge}_{i}") for i in range(n_l))
        return n * 3600.0 / period / n_l

    @staticmethod
    def speed_kmh(edge: str, lanes=None) -> float:
        idx = range(net.N_LANES[edge]) if lanes is None else lanes
        vs = [ls.inductionloop.getLastIntervalMeanSpeed(f"e1_{edge}_{i}") for i in idx]
        vs = [v for v in vs if v >= 0]
        return float(np.mean(vs)) * 3.6 if vs else -1.0

    @staticmethod
    def alinea_occ_pct(ramp: str) -> float:
        """Downstream occupancy (%) for ALINEA: mean over the mainline lanes of the 60 s loops 40 m past the merge."""
        e = net.ALINEA_LOOPS[ramp]
        return float(np.mean([ls.inductionloop.getLastIntervalOccupancy(f"e1a_{e}_{i}")
                              for i in range(net.N_LANES[e])]))

    @staticmethod
    def alinea_flow_vph(ramp: str, period: float = 60.0) -> float:
        e = net.ALINEA_LOOPS[ramp]
        return sum(ls.inductionloop.getLastIntervalVehicleNumber(f"e1a_{e}_{i}")
                   for i in range(net.N_LANES[e])) * 3600.0 / period

    @staticmethod
    def loop_vph(loop: str, period: float = 30.0) -> float:
        return ls.inductionloop.getLastIntervalVehicleNumber(loop) * 3600.0 / period

    def ramp_fill(self, ramp: str) -> tuple:
        """(fill, n_veh): fill = sum over vehicles on the storage edge of (length + minGap) / storage length.
        Speed-independent, so creeping vehicles in a metered queue count (a jam-length measure flickers)."""
        ids = ls.lanearea.getLastStepVehicleIDs(f"e2_{ramp}_0")
        s = 0.0
        for v in ids:
            vt = ls.vehicle.getTypeID(v)
            if vt not in self._space:
                self._space[vt] = ls.vehicletype.getLength(vt) + ls.vehicletype.getMinGap(vt)
            s += self._space[vt]
        return s / self.lanes[f"{ramp}_0"], len(ids)


def meters_state() -> dict:
    return {r: ls.trafficlight.getRedYellowGreenState(net.TLS[r]) for r in net.RAMPS}


def assert_meters_green(t: float):
    st = meters_state()
    return (all(s == "G" for s in st.values()), "H-R7", f"meter states {st} (expected all green)")


def assert_meter_links(t: float):
    """Each meter TLS controls exactly one link, from its ramp edge (the mainline is never signalised)."""
    bad = {}
    for r in net.RAMPS:
        links = ls.trafficlight.getControlledLinks(net.TLS[r])
        lanes_in = {lk[0][0] for lk in links if lk}
        if len(links) != 1 or lanes_in != {f"{r}_0"}:
            bad[r] = sorted(lanes_in)
    return (not bad, "H-R7", f"meter links wrong: {bad}")
