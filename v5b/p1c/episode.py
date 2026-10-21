"""P1c episode (gate §1): one SUMO run per process.

Run = warm-up (all green) -> control window -> drain with control still active, until empty (cap 7,200 s).
Incidents: 'slow' (edge 5 at 5 m/s) or 'close' (lane 4_1 closed to all traffic; vehicles must change lanes), window
from v5b/d2/incidents.incident_window (rng(seed + 3301), same for every arm of a seed).
Arms: 'NC' (all green) or a meter plan id (v5b/p1c/meter.py); optional 'post' plan switched in at incident onset.
Outputs: per-vehicle delay against nominal free flow (route length / (speed factor x 23 m/s)), window TTT, served
flow, safety counters (teleports, collisions incl. junctions, emergency stops, emergency-braking warnings by edge),
30-s series (exit flow, edge-3/4 speeds, commanded rate).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1.config import SUMO_BIN
from v5b.d1.sumo_runner import SumoSim
from v5b.d2.incidents import incident_window
from v5b.p1c import plant as pl
from v5b.p1c.meter import Meter

SLOW_MPS = 5.0
_EMERG = re.compile(r"Vehicle '([^']+)' performs emergency (braking|stop).*?lane='([^']+)'.*?time=([\d.]+)")


class Sim(SumoSim):
    def start(self) -> None:
        self.log_file = self.run_dir / f"sumo_pid{os.getpid()}.log"
        self.stat_file = self.run_dir / f"stats_pid{os.getpid()}.xml"
        args = [SUMO_BIN, "-n", str(self.net_file), "-r", str(self.route_file), "--step-length", str(self.dt),
                "--seed", str(self.seed), "--route-steps", "0", "--time-to-teleport", "300",
                "--collision.action", "warn", "--collision.check-junctions", "true",
                "--no-step-log", "true", "--duration-log.disable", "true",
                "--log", str(self.log_file), "--statistic-output", str(self.stat_file)]
        if self.additional:
            args += ["-a", ",".join(self.additional)]
        args += self.extra_args
        ls.start(args)
        self.loaded += ls.simulation.getLoadedNumber()
        self._started = True
        self._wall0 = time.time()


class Incident:
    def __init__(self, kind, onset, duration, slow_edge):
        self.kind, self.onset, self.duration, self.slow_edge = kind, onset, duration, slow_edge
        self.on = self.done = False
        self.t_on = self.t_off = None

    def tick(self, t):
        if self.kind == "none" or self.done:
            return
        if not self.on and t >= self.onset - 1e-9:
            if self.kind == "slow":
                ls.edge.setMaxSpeed(self.slow_edge, SLOW_MPS)
            self.on, self.t_on = True, t   # 'close': the blocker vehicle in the route file acts by itself
        elif self.on and t >= self.onset + self.duration - 1e-9:
            self.clear(t)

    def clear(self, t):
        if not self.on:
            return
        if self.kind == "slow":
            ls.edge.setMaxSpeed(self.slow_edge, pl.SPEED)
        self.on, self.done, self.t_off = False, True, t


def _mean(ids, fn):
    return float(np.mean([max(fn(i), 0.0) for i in ids]))


def _trips(path: Path, sf: dict) -> list:
    out = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "tripinfo" and not el.get("id").startswith("blk"):
            vid = el.get("id")
            tot = float(el.get("duration")) + float(el.get("departDelay"))
            ideal = float(el.get("routeLength")) / (sf[vid] * pl.SPEED)
            out.append((tot - ideal, float(el.get("departDelay")), float(el.get("timeLoss"))))
            el.clear()
    return out


def run(cfg: pl.Config, arm: str, incident: str, profile: list, seed: int, run_dir: Path, *, post: str | None = None,
        r_min: float = 600.0, warmup: float = 300.0, control: float = 900.0, t_cap: float = 7200.0,
        series: bool = True, keep_files: bool = False) -> dict:
    t_w0 = time.time()
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    d = pl.build_net(cfg)
    onset, dur = incident_window(seed, warmup, control)
    dem = pl.Demand(seed, profile, cfg, blocker=(onset, dur) if incident == "close" else None)
    tag = f"{cfg.tag()}_{arm}{'-' + post if post else ''}_{incident}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = Sim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=cfg.step, seed=seed,
              extra_args=["--tripinfo-output", str(trip)])
    inc = Incident(incident, onset, dur, pl.GEOMS[cfg.geom]["bott_edge"])
    loops = pl.loop_ids(cfg.geom)
    sim.start()
    ls.trafficlight.setProgram(pl.TLS_ID, "allgreen")
    meter = None
    if arm != "NC":
        meter = Meter(arm, read_occ=lambda e: _mean(loops[e], ls.inductionloop.getLastIntervalOccupancy),
                      set_state=lambda s: ls.trafficlight.setRedYellowGreenState(pl.TLS_ID, s), r_min=r_min,
                      n_lanes=pl.lanes(cfg.geom, "2"))
    sim.run_until(warmup)
    tts0, arr0 = sim.tts_system, sim.arrived
    ser = []
    t_switch = None
    cr = {"prev": set(ls.edge.getLastStepVehicleIDs("2")), "n": 0, "ctrl": 0}
    end_ctrl = warmup + control

    def tick(t):
        nonlocal t_switch
        inc.tick(t)
        if post and inc.on and t_switch is None:
            meter.set_plan(post)
            t_switch = t
        ids2 = set(ls.edge.getLastStepVehicleIDs("2"))
        cr["n"] += len(cr["prev"] - ids2)
        cr["prev"] = ids2
        if t < end_ctrl:
            cr["ctrl"] = cr["n"]
        if meter is not None:
            meter.step(t, cr["n"])
        if series and abs((t / pl.LOOP_PERIOD) - round(t / pl.LOOP_PERIOD)) < 1e-6:
            ser.append((round(t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                        round(_mean(loops["e4"], ls.inductionloop.getLastIntervalMeanSpeed), 2),
                        round(_mean(loops["e3"], ls.inductionloop.getLastIntervalMeanSpeed), 2),
                        None if meter is None else round(meter.r, 1)))

    while sim.t < end_ctrl - 1e-9:
        tick(sim.t)
        sim.run_until(sim.t + 1.0)
    inc.clear(sim.t)
    ttt_win = (sim.tts_system - tts0) / 3600.0
    served = (sim.arrived - arr0) * 3600.0 / control
    n_left = ls.vehicle.getIDCount() + len(ls.simulation.getPendingVehicles())
    drained = False
    while sim.t < t_cap - 1e-9:                       # drain with control active
        if sim.departed == sim._total and ls.vehicle.getIDCount() == 0 and not ls.simulation.getPendingVehicles():
            drained = True
            break
        tick(sim.t)
        sim.run_until(sim.t + 1.0)
    res = sim.close(drained=drained)
    trips = _trips(trip, dem.sf)
    em = {"braking": {}, "stop": {}}
    try:
        for line in sim.log_file.read_text(errors="replace").splitlines():
            m = _EMERG.search(line)
            if m:
                e = m.group(3).rsplit("_", 1)[0]
                em[m.group(2)][e] = em[m.group(2)].get(e, 0) + 1
    except OSError:
        pass
    out = {"cfg": pl.config_dict(cfg), "arm": arm, "post": post, "incident": incident, "seed": seed,
           "profile": profile, "r_min": r_min, "onset": onset, "duration": dur, "t_on": inc.t_on, "t_off": inc.t_off,
           "t_switch": t_switch, "crossings_ctrl": cr["ctrl"], "discharge_ctrl_vph": cr["ctrl"] * 3600.0 / control,
           "n_red_onsets": meter.n_red if meter is not None else 0,
           "commanded_final": meter.r if meter is not None else None, "generated": dem.counts_by_route()["main"], "n_trips": len(trips),
           "delay_s": float(np.mean([x[0] for x in trips])) if trips else None,
           "timeloss_delay_s": float(np.mean([x[1] + x[2] for x in trips])) if trips else None,
           "ttt_window_vehh": ttt_win, "served_ctrl_vph": served, "n_left_ctrl_end": n_left,
           "drained": drained, "teleports": res["teleports"], "collisions": res["collisions"],
           "emergency_stops": res["emergency_stops"], "emerg_by_edge": em, "health": res["health"]["status"],
           "health_codes": sorted(res["health"]["by_code"]), "hash": res["hash"], "series": ser,
           "blocker_depart_delay": None, "valid": bool(drained) and len(trips) == dem.counts_by_route()["main"] and res["teleports"] == 0
           and res["collisions"] == 0, "wall_s": round(time.time() - t_w0, 1)}
    if not keep_files:
        for f in (rou, trip, sim.log_file, sim.stat_file):
            try:
                f.unlink()
            except OSError:
                pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="JSON: cfg, arm, incident, profile, seed, post, r_min, out")
    ap.add_argument("--run-dir", required=True)
    a = ap.parse_args(argv)
    j = json.loads(a.job)
    res = run(pl.Config(**j["cfg"]), j["arm"], j["incident"], j["profile"], j["seed"], Path(a.run_dir),
              post=j.get("post"), r_min=j.get("r_min", 600.0), series=j.get("series", True))
    out = Path(j["out"])
    tmp = out.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(res))
    tmp.replace(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
