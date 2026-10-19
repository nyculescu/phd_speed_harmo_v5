"""Screen D2 episode: one SUMO run per process (docs/research/protocols/screen_D2_incidents.md).

Reuses screen D1's episode shape unchanged (v5b/d1/episode.py, commit a23613b): BN4 plant, constant demand q,
40 s uncontrolled warm-up, 900 s control with 1-s decisions (meter.step before each 1-s advance), all-green
assertion when no meter, uncontrolled all-green drain until empty (t_drain_max 7200 s), av_share 0.1, the D1
FBMeter law, and the D1 metrics. New: the incident layer (v5b/d2/incidents.py) and the controller switch.

A run is (pre, post, incident, q, seed):
- pre in G or 'NC': the controller from the start of the control period;
- post in G or None: at the incident onset (perfect detection: the tick at which the incident is applied),
  switch to `post` (v5b/d2/controllers.py: switch). None = no switching;
- back (V92(c), page Addendum D2-A12): at the tick the incident clears (onset + duration, perfect detection),
  switch back to `pre` (= N) with the same switch rule. False = keep `post` until the end of control.
Per 1-s tick: incident.tick -> switch (if 'on' and post; back to pre if 'off' and back) -> meter.step -> advance 1 s.
Cross-fit replicate (page Addendum D2-A1): xf=True runs the same demand file and the same incident window (both
from `seed`) with SUMO's own RNG seeded by seed + XF_SUMO_OFFSET (redraws speedFactor and departLane="random").
Emergency braking / stops are also counted by edge from the SUMO log (page Addendum D2-A8; report only).
Primary metric (Rule 4): door-to-door delay = mean over all generated vehicles of tripinfo departDelay
(origin / insertion queue) + timeLoss (incl. waiting at the meter), after the drain.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1 import plant
from v5b.d1.episode import DET_EDGE, FBMeter, parse_tripinfo
from v5b.d1.sumo_runner import SumoSim
from v5b.d2 import controllers as ctl
from v5b.d2.incidents import CONDITIONS, NONE, Incident, incident_window


XF_SUMO_OFFSET = 10_000_000   # SUMO --seed of a cross-fit replicate = seed + this (outside every seed block)
_EMERG = re.compile(r"performs emergency (braking|stop).*?lane '([^']+)'.*?time=([-+\d.]+)")


def run_key(pre: str, post, incident: str, q: float, seed: int, rep=None, xf: bool = False, back: bool = False) -> str:
    k = f"{pre}" + (f"-{post}" if post else "") + ("+back" if back else "") + f"_{incident}_q{int(q)}_s{seed}"
    return k + (f"_rep{rep}" if rep is not None else "") + ("_xf" if xf else "")


def emergency_by_edge(lines, t_on=None, t_off=None) -> dict:
    """SUMO 'performs emergency braking / stop' warnings counted by edge (lane id without its index):
    'all' over the run, 'incident' only those with t_on <= time < t_off (empty without an incident)."""
    out = {"all": {}, "incident": {}}
    for line in lines:
        m = _EMERG.search(line)
        if not m:
            continue
        edge, t = m.group(2).rsplit("_", 1)[0], float(m.group(3).rstrip("."))
        out["all"][edge] = out["all"].get(edge, 0) + 1
        if t_on is not None and t_off is not None and t_on <= t < t_off:
            out["incident"][edge] = out["incident"].get(edge, 0) + 1
    return out


def check_run(pre: str, post, incident: str, back: bool = False) -> None:
    if pre != ctl.NC:
        ctl.parse(pre)
    if incident not in CONDITIONS:
        raise ValueError(incident)
    if post is not None:
        ctl.parse(post)
        if pre == ctl.NC:
            raise ValueError("NC does not switch")
        if incident == NONE:
            raise ValueError("no incident, no onset: nothing to switch at")
    if back and post is None:
        raise ValueError("back needs a switch at onset (post)")


def run_episode(pre: str, post, incident: str, q: float, seed: int, run_dir: Path, warmup_s: float = 40.0,
                control_s: float = 900.0, t_drain_max: float = 7200.0, av_share: float = 0.1,
                keep_files: bool = False, xf: bool = False, back: bool = False) -> dict:
    check_run(pre, post, incident, back)
    t_wall0 = time.time()
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    files = plant.files()
    t_total = warmup_s + control_s
    dem = plant.demand(seed, [(0.0, t_total, q)], av_share=av_share)
    tag = run_key(pre, post, incident, q, seed, xf=xf, back=back) + f"_pid{os.getpid()}"
    sumo_seed = seed + XF_SUMO_OFFSET if xf else seed
    rou = run_dir / f"routes_{tag}.rou.xml"
    trip = run_dir / f"tripinfo_{tag}.xml"
    dem.write(rou)
    sim = SumoSim(files["net"], rou, run_dir, dem, additional=[files["add"]], step_length=plant.STEP_LENGTH,
                  checkpoint_s=300.0, seed=sumo_seed, extra_args=["--tripinfo-output", str(trip)])
    onset, duration = incident_window(seed, warmup_s, control_s)
    inc = Incident(incident, onset, duration, api=ls)
    log = []   # meter updates: (t, n4 = vehicles on edge 4, q before the update)
    meter = None

    def reader(t: float):
        n4 = ls.edge.getLastStepVehicleNumber(DET_EDGE)
        log.append((round(t, 2), int(n4), round(meter.q, 3)))
        return float(n4)

    sim.start()
    plant.set_all_green()
    sim.asserts.append(plant.assert_all_green)
    sim.asserts.append(inc.assert_state)
    if pre != ctl.NC:   # the TLS is driven by the meter, not held at all-green
        meter = FBMeter(read=reader, **ctl.meter_kwargs(pre))
        sim.asserts.remove(plant.assert_all_green)
    sim.run_until(sim.t + warmup_s)   # uncontrolled warm-up
    t_ctrl0, arr0 = sim.t, sim.arrived
    t_switch, q_at_switch, t_back, q_at_back = None, None, None, None
    while sim.t < t_ctrl0 + control_s - 1e-9:
        ev = inc.tick(sim.t)
        if ev == "on" and post is not None:   # perfect, instant detection
            q_at_switch = round(meter.q, 3)
            ctl.switch(meter, post)
            t_switch = sim.t
        elif ev == "off" and back:   # clearance (perfect detection): back to N = pre
            q_at_back = round(meter.q, 3)
            ctl.switch(meter, pre)
            t_back = sim.t
        if meter is not None:
            meter.step(sim.t)
        sim.run_until(sim.t + 1.0)
    ctrl_s = sim.t - t_ctrl0
    still_on = inc.on
    inc.clear(sim.t)   # never needed by construction (onset + duration < control end); recorded if it was
    m = {"served_ctrl_vph": (sim.arrived - arr0) * 3600.0 / ctrl_s,
         "ttt_ctrl_vehh": sim.tts_system / 3600.0,          # fixed window [0, control end], incl. origin queue
         "n_system_ctrl_end": ls.vehicle.getIDCount() + len(ls.simulation.getPendingVehicles())}
    if meter is not None:   # uncontrolled drain: all-green, meter off, run until empty
        plant.set_all_green()
        meter = None
    sim.demand_end_t = sim.t
    drained = sim.drain(t_drain_max)
    gen = sim._total
    m.update({"ttt_full_vehh": sim.tts_system / 3600.0, "mean_time_in_system_s": sim.tts_system / max(gen, 1)})
    res = sim.close(drained=drained)
    trips = parse_tripinfo(trip)
    delays = [dd + tl for dd, tl in trips]
    valid = bool(drained) and len(trips) == gen and res["health"]["status"] != "FAIL"
    n_eb = sum(v for k, v in res["sumo_warning_categories"].items() if "emergency" in k)
    try:
        eb_edge = emergency_by_edge(sim.log_file.read_text(errors="replace").splitlines(), inc.t_on, inc.t_off)
    except OSError:
        eb_edge = None
    out = {"pre": pre, "post": post, "back": bool(back), "incident": incident, "q": q, "seed": seed, "xf": bool(xf), "sumo_seed": sumo_seed,
           "onset_s": onset, "duration_s": duration, "t_on": inc.t_on, "t_off": inc.t_off,
           "incident_on_at_control_end": still_on, "incident_log": inc.log,
           "t_switch": t_switch, "q_at_switch": q_at_switch, "t_back": t_back, "q_at_back": q_at_back,
           "delay_s": float(np.mean(delays)) if delays else float("nan"),
           "depart_delay_s": float(np.mean([d for d, _ in trips])) if trips else float("nan"),
           **m, "generated": gen, "n_trips": len(trips), "drained": drained, "valid": valid,
           "teleports": res["teleports"], "collisions": res["collisions"], "emergency_stops": res["emergency_stops"],
           "emergency_warnings": n_eb, "emergency_by_edge": eb_edge, "health": res["health"]["status"], "health_codes": sorted(res["health"]["by_code"]),
           "hash": res["hash"], "sim_wall_s": res["wall_s"], "meter_log": log}
    if not keep_files:
        for f in (rou, trip):
            try:
                f.unlink()
            except OSError:
                pass
    out["wall_s"] = round(time.time() - t_wall0, 2)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="JSON: pre, post, incident, q, seed [, xf, back, key, code_commit]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--keep-files", action="store_true")
    a = ap.parse_args(argv)
    spec = json.loads(a.spec)
    res = run_episode(spec["pre"], spec.get("post"), spec["incident"], float(spec["q"]), int(spec["seed"]),
                      Path(a.run_dir), keep_files=a.keep_files, xf=bool(spec.get("xf", False)),
                      back=bool(spec.get("back", False)))
    res["key"] = spec.get("key")
    res["code_commit"] = spec.get("code_commit")   # checked before any reuse (resume)
    out = Path(a.out)
    tmp = out.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(res))
    tmp.replace(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
