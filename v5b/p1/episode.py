"""P1 episode: one SUMO run per process (docs/research/protocols/p1_incident_information.md).

Screen D2's episode shape, unchanged (v5b/d2/episode.py @ 72ba8f2): BN4, constant demand q, 40 s uncontrolled warm-up,
900 s control with 1-s ticks, the D2 incident layer, all-green assertion without a meter, uncontrolled all-green drain
(t_drain_max 7200 s), av_share 0.1, the D2 metrics (delay = mean over all generated vehicles of tripinfo departDelay +
timeLoss). Per tick: incident.tick -> switch (scheduled) -> VSL tick -> queue sample -> meter.step -> advance 1 s.
For a D2 spec (pre in D2's G, post, back) the run is the D2 run: the added reads do not change the simulation
(tested on a smoke seed).

A run spec (all fields are part of the run key and of the resume check):
- pre: 'NC', a member of G, a PI controller or an AD controller (v5b/p1/family.py), run from the start of control;
- post (G or None), back: the plan switched in at the incident onset (D2-A12 'g' or 'g+back');
- d, c: detection delay and clearance detection delay (page §4; v5b/p1/meters.switch_schedule);
- fa: false alarm on a clean day (incident 'none'): 'post' runs from the alarm tick for 240 s, then pre (= N);
- k: replicate index (page §7, A3(a)): k >= 1 redraws the SUMO seed and the demand; the incident window stays;
- vsl_b: posted VSL target on gantry edges 2-3 from onset to clearance (page §3 TV);
- rep: T3 repeat index (None outside T3).
New outputs: max_queue (largest origin backlog + vehicles on edges 1-2 over the 1-s control ticks), entered_e4_incident
(vehicles entering edge 4 between the incident's on and off ticks, counted every 0.5-s step), entered_e4_ext120 (the
same from the on tick to the off tick + 120 s; addendum 2026-10-19, D3), AD's n_hat log and T-AD deviation, the VSL log.
The meter signal ('d2' or 'continuous', v5b/p1/meters.py) is not part of the spec or key: the runner passes it with
every run ('signal' in the run JSON, required, no default) and refuses to reuse a run made with another signal.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1 import plant
from v5b.d1.episode import parse_tripinfo
from v5b.d1.sumo_runner import SumoSim
from v5b.d2.episode import emergency_by_edge
from v5b.d2.incidents import CONDITIONS, NONE, Incident, incident_window
from v5b.p1 import family as fam
from v5b.p1.meters import (SIGNALS, ADMeter, FBSignalMeter, PIMeter, PostedVSL, ad_max_dev, fa_schedule, fa_window,
                           replicate_seeds, switch_schedule)

SPEC_FIELDS = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep")
EXT_S = 120.0   # entered_e4_ext120: the count window runs to the off tick + 120 s (addendum 2026-10-19, D3)


def _num(x) -> str:
    return f"{x:g}".replace(".", "p")


def run_key(pre: str, post=None, back: bool = False, incident: str = NONE, q: float = 2000.0, seed: int = 0,
            k: int = 0, d: float = 0.0, c: float = 0.0, fa: bool = False, vsl_b=None, rep=None) -> str:
    key = f"{pre}" + (f"-{post}" if post else "") + ("+back" if back else "")
    key += (f"_d{_num(d)}" if d else "") + (f"_c{_num(c)}" if c else "") + ("_fa" if fa else "")
    key += (f"_v{_num(vsl_b)}" if vsl_b is not None else "") + f"_{incident}_q{int(q)}_s{seed}"
    return key + (f"_k{k}" if k else "") + (f"_rep{rep}" if rep is not None else "")


def make_spec(pre, post=None, back=False, incident=NONE, q=2000.0, seed=0, k=0, d=0.0, c=0.0, fa=False, vsl_b=None,
              rep=None) -> dict:
    s = {"pre": pre, "post": post, "back": bool(back), "incident": incident, "q": float(q), "seed": int(seed),
         "k": int(k), "d": float(d), "c": float(c), "fa": bool(fa), "vsl_b": None if vsl_b is None else float(vsl_b),
         "rep": rep}
    check_spec(s)
    s["key"] = run_key(**{f: s[f] for f in SPEC_FIELDS})
    return s


def check_spec(s: dict) -> None:
    pre, post, inc = s["pre"], s["post"], s["incident"]
    if pre != fam.NC:
        fam.parse(pre)
    if inc not in CONDITIONS:
        raise ValueError(inc)
    if s["k"] < 0 or s["d"] < 0 or s["c"] < 0:
        raise ValueError("k, d, c must be >= 0")
    if post is not None:
        if post not in fam.G or pre not in fam.G:
            raise ValueError("switch runs go from a member of G to a member of G")
        if inc == NONE and not s["fa"]:
            raise ValueError("no incident, no onset: nothing to switch at (except a false alarm)")
    if s["back"] and (post is None or s["fa"]):
        raise ValueError("back needs a switch at onset (a false alarm always returns to pre)")
    if (s["d"] or s["c"]) and (post is None or inc == NONE):
        raise ValueError("detection delays need a switch run with an incident")
    if s["c"] and not s["back"]:
        raise ValueError("a clearance delay applies to back plans only")
    if s["fa"] and (inc != NONE or post is None):
        raise ValueError("a false alarm is a clean-day run with a plan")
    if s["vsl_b"] is not None and inc == NONE:
        raise ValueError("VSL runs from onset to clearance: it needs an incident")


class _Sim(SumoSim):
    """SumoSim with a per-step hook (counting entries into edge 4); the simulation itself is unchanged."""
    hook = None

    def step(self, n: int = 1) -> None:
        for _ in range(n):
            SumoSim.step(self, 1)
            if self.hook is not None:
                self.hook()


def schedule(spec: dict, onset: float, duration: float) -> tuple:
    if spec["post"] is None:
        return None, None
    if spec["fa"]:
        return fa_schedule(spec["seed"])
    return switch_schedule(onset, duration, spec["d"], spec["c"], spec["back"])


def run_episode(spec: dict, run_dir: Path, *, signal: str, warmup_s: float = 40.0, control_s: float = 900.0,
                t_drain_max: float = 7200.0, av_share: float = 0.1, keep_files: bool = False) -> dict:
    check_spec(spec)
    if signal not in SIGNALS:
        raise ValueError(f"signal must be one of {SIGNALS}: {signal!r}")
    pre, post, inc_kind, q, seed = spec["pre"], spec["post"], spec["incident"], float(spec["q"]), int(spec["seed"])
    t_wall0 = time.time()
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    files = plant.files()
    seeds = replicate_seeds(seed, spec["k"])
    dem = plant.demand(seeds["demand_seed"], [(0.0, warmup_s + control_s, q)], av_share=av_share)
    tag = run_key(**{f: spec[f] for f in SPEC_FIELDS}) + f"_pid{os.getpid()}"
    rou, trip = run_dir / f"routes_{tag}.rou.xml", run_dir / f"tripinfo_{tag}.xml"
    dem.write(rou)
    sim = _Sim(files["net"], rou, run_dir, dem, additional=[files["add"]], step_length=plant.STEP_LENGTH,
               checkpoint_s=300.0, seed=seeds["sumo_seed"], extra_args=["--tripinfo-output", str(trip)])
    onset, duration = incident_window(seed, warmup_s, control_s)   # always from the evaluation seed (A3(a))
    inc = Incident(inc_kind, onset, duration, api=ls)
    t_sw_plan, t_bk_plan = schedule(spec, onset, duration)
    vsl = PostedVSL(spec["vsl_b"]) if spec["vsl_b"] is not None else None
    log = []   # meter updates: (t, n read, q before the update)
    meter = None

    def reader(edge):
        def r(t: float):
            n = ls.edge.getLastStepVehicleNumber(edge)
            log.append((round(t, 2), int(n), round(meter.q, 3)))
            return float(n)
        return r

    sim.start()
    plant.set_all_green()
    sim.asserts.append(plant.assert_all_green)
    sim.asserts.append(inc.assert_state)
    if vsl is not None:
        sim.asserts.append(vsl.assert_state)
    if pre != fam.NC:   # the TLS is driven by the meter, not held at all-green
        p = fam.parse(pre)
        if p[0] == "const":
            meter = FBSignalMeter(read=reader("4"), K_F=0.0, q0=p[1], signal=signal)
        elif p[0] == "fb":
            meter = FBSignalMeter(read=reader("4"), K_F=p[1], n_crit=p[2], signal=signal)
        elif p[0] == "pi":
            meter = PIMeter(p[1], p[2], p[3], read=reader(p[4]), signal=signal)
        else:
            meter = ADMeter(p[1], p[2], p[3], read=reader("4"), cum_out=lambda t: sim.arrived, signal=signal)
        sim.asserts.remove(plant.assert_all_green)
    sim.run_until(sim.t + warmup_s)   # uncontrolled warm-up
    t_ctrl0, arr0 = sim.t, sim.arrived
    e4 = {"prev": set(ls.edge.getLastStepVehicleIDs("4")), "n": 0, "n_ext": 0}

    def count_e4():
        ids = set(ls.edge.getLastStepVehicleIDs("4"))
        new = len(ids - e4["prev"])
        if inc.on:
            e4["n"] += new
        if inc.on or (inc.t_off is not None and sim.t <= inc.t_off + EXT_S + 1e-9):
            e4["n_ext"] += new
        e4["prev"] = ids

    sim.hook = count_e4
    t_switch = q_at_switch = t_back = q_at_back = None
    max_queue = 0
    while sim.t < t_ctrl0 + control_s - 1e-9:
        t = sim.t
        inc.tick(t)
        if t_sw_plan is not None and abs(t - t_sw_plan) < 1e-6:
            if not spec["fa"] and not inc.on:
                raise RuntimeError(f"scheduled switch at {t} while the incident is off")
            q_at_switch = round(meter.q, 3)
            fam.switch(meter, post)
            t_switch = t
        elif t_bk_plan is not None and abs(t - t_bk_plan) < 1e-6:
            q_at_back = round(meter.q, 3)
            fam.switch(meter, pre)
            t_back = t
        if vsl is not None:
            vsl.tick(t, inc.on)
        nq = len(ls.simulation.getPendingVehicles()) + ls.edge.getLastStepVehicleNumber("1") + \
            ls.edge.getLastStepVehicleNumber("2")
        max_queue = max(max_queue, int(nq))
        if meter is not None:
            meter.step(t)
        sim.run_until(t + 1.0)
    sim.hook = None
    if post is not None and not spec["fa"]:   # the schedule must agree with the incident's own ticks
        if spec["d"] == 0 and t_switch != inc.t_on or spec["back"] and spec["c"] == 0 and t_switch is not None \
                and t_back != inc.t_off:
            raise RuntimeError(f"switch schedule {t_switch}/{t_back} != incident ticks {inc.t_on}/{inc.t_off}")
    ctrl_s = sim.t - t_ctrl0
    still_on = inc.on
    inc.clear(sim.t)
    m = {"served_ctrl_vph": (sim.arrived - arr0) * 3600.0 / ctrl_s, "ttt_ctrl_vehh": sim.tts_system / 3600.0,
         "n_system_ctrl_end": ls.vehicle.getIDCount() + len(ls.simulation.getPendingVehicles())}
    nhat_log = getattr(meter, "nhat_log", None)
    if meter is not None:   # uncontrolled drain: all-green, meter off, run until empty
        plant.set_all_green()
        meter = None
    if vsl is not None:
        vsl.restore()
        sim.asserts.remove(vsl.assert_state)
    sim.demand_end_t = sim.t
    drained = sim.drain(t_drain_max)
    gen = sim._total
    m.update({"ttt_full_vehh": sim.tts_system / 3600.0, "mean_time_in_system_s": sim.tts_system / max(gen, 1)})
    res = sim.close(drained=drained)
    trips = parse_tripinfo(trip)
    delays = [dd + tl for dd, tl in trips]
    valid = bool(drained) and len(trips) == gen and res["health"]["status"] != "FAIL"
    n_eb = sum(v for k_, v in res["sumo_warning_categories"].items() if "emergency" in k_)
    try:
        eb_edge = emergency_by_edge(sim.log_file.read_text(errors="replace").splitlines(), inc.t_on, inc.t_off)
    except OSError:
        eb_edge = None
    out = {**{f: spec[f] for f in SPEC_FIELDS}, "sumo_seed": seeds["sumo_seed"], "demand_seed": seeds["demand_seed"],
           "onset_s": onset, "duration_s": duration, "t_on": inc.t_on, "t_off": inc.t_off,
           "fa_time_s": fa_window(seed)[0] if spec["fa"] else None,
           "incident_on_at_control_end": still_on, "incident_log": inc.log,
           "t_switch_plan": t_sw_plan, "t_back_plan": t_bk_plan,
           "t_switch": t_switch, "q_at_switch": q_at_switch, "t_back": t_back, "q_at_back": q_at_back,
           "delay_s": float(np.mean(delays)) if delays else float("nan"),
           "depart_delay_s": float(np.mean([d for d, _ in trips])) if trips else float("nan"),
           **m, "max_queue": max_queue, "entered_e4_incident": e4["n"] if inc.t_on is not None else None,
           "entered_e4_ext120": e4["n_ext"] if inc.t_on is not None else None, "signal": signal,
           "generated": gen, "n_trips": len(trips), "drained": drained, "valid": valid,
           "teleports": res["teleports"], "collisions": res["collisions"], "emergency_stops": res["emergency_stops"],
           "emergency_warnings": n_eb, "emergency_by_edge": eb_edge, "health": res["health"]["status"],
           "health_codes": sorted(res["health"]["by_code"]), "hash": res["hash"], "sim_wall_s": res["wall_s"],
           "meter_log": log, "nhat_log": nhat_log,
           "ad_max_dev": ad_max_dev(nhat_log, inc.t_on, inc.t_off) if nhat_log else None,
           "vsl_log": vsl.log if vsl is not None else None}
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
    ap.add_argument("--spec", required=True, help="JSON spec (make_spec fields, key, code_commit)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--keep-files", action="store_true")
    a = ap.parse_args(argv)
    spec = json.loads(a.spec)
    if spec.get("signal") not in SIGNALS:
        raise SystemExit(f"the spec must carry 'signal' in {SIGNALS} (no default: author decision)")
    res = run_episode({f: spec.get(f) for f in SPEC_FIELDS}, Path(a.run_dir), signal=spec["signal"],
                      keep_files=a.keep_files)
    res["key"] = spec.get("key")
    res["code_commit"] = spec.get("code_commit")   # checked before any reuse (resume)
    out = Path(a.out)
    tmp = out.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(res))
    tmp.replace(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
