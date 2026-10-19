"""Screen D1 episode: one SUMO run per process (docs/research/protocols/screen_D1_detector_faults.md).

Port: claude/vsl-lab-core@2a79e5e
- vsl_lab/envs/bn4_env.py: FBMeter (unchanged control law; changes: the reading is injectable and a missing
  reading holds the rate), and the meter path of BN4Env.reset/step (40 s uncontrolled warm-up, 1-s decisions,
  meter.step before each 1-s advance, all-green assertion when no meter, uncontrolled drain until empty);
- vsl_lab/jobs/bn4_eval.py: episode shape (warm-up 40 s, control 900 s, drain_after=True, t_drain_max 7200 s,
  av_share 0.1, inflow constant at q). The gym spaces, AV caps, VSL, perturbations and DRL code are dropped.

Arms (Rule 3): O meter on true readings (fault ignored); FX on fault switch to a constant rate q_fx;
RF on fault fill edge 4 from edge 3 x ratio; NV the meter keeps using the faulty reading; NC no meter.
Primary metric (Rule 4): door-to-door delay = mean over all generated vehicles of SUMO tripinfo
departDelay (insertion / origin queue) + timeLoss (incl. waiting at the meter), after the drain.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1 import netgen_bn4 as net
from v5b.d1 import plant
from v5b.d1.faults import ANY, DetectorFault, onset_time, rf_fill, saturated_count
from v5b.d1.sumo_runner import SumoSim

ARMS = ("O", "FX", "RF", "NV", "NC")
DET_EDGE, UP_EDGE = "4", "3"


class FBMeter:
    """Vinitsky et al. (2018) Sec. III-E feedback ramp meter at node 3 (140 m before the bottleneck):
    q(k+1) = q(k) + K_F (n_crit - n_hat), n_hat = vehicles on segment 4, updated every T s; cycle =
    fixed 6 s green + variable red, c = 2 M 3600 / q (2 vehicles per lane per green, M = 4 lanes).
    Paper values T = 30, K_F = 20, n_crit = 8 ("tuned empirically ... there may be better values").
    D1 changes: read(t) supplies n_hat (default: the archive's edge-4 count); read(t) -> None (no data) holds q."""

    def __init__(self, K_F=20.0, n_crit=8.0, T=30.0, green=6.0, q0=1500.0, q_min=200.0, q_max=4000.0, M=4,
                 read=None):
        self.K_F, self.n_crit, self.T, self.green, self.M = K_F, n_crit, T, green, M
        self.q, self.q_min, self.q_max = q0, q_min, q_max
        self.t_update = None
        self.t_cycle0 = None
        self.read = read or (lambda t: ls.edge.getLastStepVehicleNumber(DET_EDGE))

    def cycle(self) -> float:
        return max(self.green, 2.0 * self.M * 3600.0 / self.q)

    def step(self, t: float) -> None:
        if self.t_update is None:
            self.t_update, self.t_cycle0 = t, t
        if t - self.t_update >= self.T - 1e-9:
            n_hat = self.read(t)
            if n_hat is not None:
                self.q = float(np.clip(self.q + self.K_F * (self.n_crit - n_hat), self.q_min, self.q_max))
            self.t_update = t
        c = self.cycle()
        phase_t = (t - self.t_cycle0) % c
        ls.trafficlight.setRedYellowGreenState(plant.TLS_ID, "GGGG" if phase_t < self.green else "rrrr")


def parse_tripinfo(path: Path) -> list:
    """[(departDelay, timeLoss), ...] per finished vehicle."""
    out = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "tripinfo":
            out.append((float(el.get("departDelay")), float(el.get("timeLoss"))))
            el.clear()
    return out


def run_episode(arm: str, fault: str, q: float, seed: int, run_dir: Path, q_fx: float | None = None,
                ratio: float | None = None, kf: float = 20.0, ncrit: float = 8.0, warmup_s: float = 40.0,
                control_s: float = 900.0, t_drain_max: float = 7200.0, av_share: float = 0.1,
                keep_files: bool = False) -> dict:
    if arm not in ARMS:
        raise ValueError(arm)
    if arm == "FX" and q_fx is None or arm == "RF" and ratio is None:
        raise ValueError("FX needs q_fx, RF needs ratio")
    if arm == "NV" and fault in ("none", ANY):
        raise ValueError("NV needs a concrete fault type")
    t_wall0 = time.time()
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    files = plant.files()
    lane_len = net.lane_lengths_from_net(files["net"])
    t_total = warmup_s + control_s
    dem = plant.demand(seed, [(0.0, t_total, q)], av_share=av_share)
    tag = f"{arm}_{fault}_q{int(q)}_s{seed}" + (f"_fx{int(q_fx)}" if arm == "FX" else "") + \
          (f"_r{ratio:.4f}" if arm == "RF" else "") + f"_pid{os.getpid()}"
    rou = run_dir / f"routes_{tag}.rou.xml"
    trip = run_dir / f"tripinfo_{tag}.xml"
    dem.write(rou)
    sim = SumoSim(files["net"], rou, run_dir, dem, additional=[files["add"]], step_length=plant.STEP_LENGTH,
                  checkpoint_s=300.0, seed=seed, extra_args=["--tripinfo-output", str(trip)])
    onset = onset_time(seed, warmup_s, control_s)
    flt = DetectorFault(fault, onset, saturated_count(lane_len, DET_EDGE), seed)
    log = []   # meter updates: (t, n4 true, n3, value used or None, q before the update)
    meter = None

    def reader(t: float):
        n4 = ls.edge.getLastStepVehicleNumber(DET_EDGE)
        n3 = ls.edge.getLastStepVehicleNumber(UP_EDGE)
        if arm == "O" or arm == "FX" or not flt.active(t):
            v = float(n4)   # FX after onset: K_F = 0, the value is unused
        elif arm == "NV":
            v = flt.read(t, n4)
        else:               # RF
            v = rf_fill(ratio, n3)
        log.append((round(t, 2), int(n4), int(n3), None if v is None else round(v, 4), round(meter.q, 3)))
        return v

    sim.start()
    plant.set_all_green()
    sim.asserts.append(plant.assert_all_green)
    if arm != "NC":   # the TLS is driven by the meter, not held at all-green
        meter = FBMeter(K_F=kf, n_crit=ncrit, read=reader)
        sim.asserts.remove(plant.assert_all_green)
    sim.run_until(sim.t + warmup_s)   # uncontrolled warm-up
    t_ctrl0, arr0 = sim.t, sim.arrived
    t_fx = None
    while sim.t < t_ctrl0 + control_s - 1e-9:
        if arm == "FX" and t_fx is None and flt.active(sim.t):   # perfect, instant detection
            meter.q, meter.K_F, t_fx = float(q_fx), 0.0, sim.t
        if meter is not None:
            meter.step(sim.t)
        sim.run_until(sim.t + 1.0)
    ctrl_s = sim.t - t_ctrl0
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
    out = {"arm": arm, "fault": fault, "q": q, "seed": seed, "q_fx": q_fx, "ratio": ratio, "kf": kf, "ncrit": ncrit,
           "onset_s": onset, "t_fx": t_fx,
           "delay_s": float(np.mean(delays)) if delays else float("nan"),
           "depart_delay_s": float(np.mean([d for d, _ in trips])) if trips else float("nan"),
           **m, "generated": gen, "n_trips": len(trips), "drained": drained, "valid": valid,
           "teleports": res["teleports"], "collisions": res["collisions"], "emergency_stops": res["emergency_stops"],
           "health": res["health"]["status"], "health_codes": sorted(res["health"]["by_code"]),
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
    ap.add_argument("--spec", required=True, help="JSON: arm, fault, q, seed [, q_fx, ratio, kf, ncrit]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--keep-files", action="store_true")
    a = ap.parse_args(argv)
    spec = json.loads(a.spec)
    kw = {k: spec[k] for k in ("q_fx", "ratio", "kf", "ncrit") if spec.get(k) is not None}
    res = run_episode(spec["arm"], spec["fault"], float(spec["q"]), int(spec["seed"]), Path(a.run_dir),
                      keep_files=a.keep_files, **kw)
    res["key"] = spec.get("key")
    res["code_commit"] = spec.get("code_commit")   # Addendum A6: checked before any reuse
    out = Path(a.out)
    tmp = out.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(res))
    tmp.replace(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
