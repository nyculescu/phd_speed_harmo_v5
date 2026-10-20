"""P1b episode: one SUMO run per process (p1b_addendum.md, approved V108, on top of the P1 page).

P1's episode (v5b/p1/episode.py) with these changes only:
- the meter is v5b/p1b/meters.P1bMeter: amber 3 s and red >= 2 s (B1, R2), q clipped to [200, 2618] in every law,
  plans may be PI-law controllers (B3, R1, R3);
- spec field 'rs' (runner share, B2 / R4 / R5): rs > 0 marks runners per vehicle in the route file
  (v5b/p1b/runners.py); allowed on main runs (k = 0) without delays, false alarm or VSL only;
- new per-run outputs (B1, B4, R4, R6, R7), all during the 900-s control period:
  crossings of the meter stop line (a vehicle leaving edge 2, checked every 0.5-s step) by signal state G / y / r and
  by runner / other; red_cross_share = crossings on r / all crossings; commanded_mean_vph = the mean commanded q over
  the control ticks; discharge_vph = crossings per state x 3600 / control length; emergency stops / braking warnings
  at the meter (SUMO log, edge 2 and node 3's internal lanes); approach speeds at red: at every r onset, per lane of
  edge 2, the speed of the lane leader within APPROACH_M = 100 m of the stop line if it is still on edge 2 at the next
  green onset (it stopped at that red);
  max_queue_veh (P1's max_queue: origin backlog + vehicles on edges 1-2), max_queue_halted_veh (halted, speed < 0.1
  m/s, on edges 1-2) and max_queue_m (R7: the distance from the stop line to the last halted vehicle on edges 1-2),
  sampled at the 1-s control ticks; AVAIL_M = the length of edges 1-2.
The 'signal' field is always 'amber' (no P1 signal modes here).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1 import plant
from v5b.d1.episode import parse_tripinfo
from v5b.d2.episode import emergency_by_edge
from v5b.d2.incidents import CONDITIONS, NONE, Incident, incident_window
from v5b.p1 import family as fam
from v5b.p1.episode import _num, _Sim
from v5b.p1.meters import PostedVSL, ad_max_dev, fa_schedule, fa_window, replicate_seeds, switch_schedule
from v5b.p1b import family as fb
from v5b.p1b import runners as rn
from v5b.p1b.meters import SIGNAL, P1bMeter

SPEC_FIELDS = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep", "rs")
EXT_S = 120.0
METER_EDGE, QUEUE_EDGES = "2", ("1", "2")
HALT_MPS = 0.1
APPROACH_M = 100.0   # approach zone: lane leaders within 100 m of the stop line at r onset


def run_key(pre: str, post=None, back: bool = False, incident: str = NONE, q: float = 2000.0, seed: int = 0,
            k: int = 0, d: float = 0.0, c: float = 0.0, fa: bool = False, vsl_b=None, rep=None, rs: float = 0.0) -> str:
    key = f"{pre}" + (f"-{post}" if post else "") + ("+back" if back else "")
    key += (f"_d{_num(d)}" if d else "") + (f"_c{_num(c)}" if c else "") + ("_fa" if fa else "")
    key += (f"_v{_num(vsl_b)}" if vsl_b is not None else "") + (f"_rs{_num(rs)}" if rs else "")
    key += f"_{incident}_q{int(q)}_s{seed}"
    return key + (f"_k{k}" if k else "") + (f"_rep{rep}" if rep is not None else "")


def make_spec(pre, post=None, back=False, incident=NONE, q=2000.0, seed=0, k=0, d=0.0, c=0.0, fa=False, vsl_b=None,
              rep=None, rs=0.0) -> dict:
    s = {"pre": pre, "post": post, "back": bool(back), "incident": incident, "q": float(q), "seed": int(seed),
         "k": int(k), "d": float(d), "c": float(c), "fa": bool(fa), "vsl_b": None if vsl_b is None else float(vsl_b),
         "rep": rep, "rs": float(rs)}
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
        if pre not in fam.G or not fb.is_plan(post):
            raise ValueError("switch runs go from a member of G (N) to a controller of G u PI")
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
    rs = s.get("rs", 0.0)
    if not 0.0 <= rs <= 1.0:
        raise ValueError("runner share must be in [0, 1]")
    if rs and (s["k"] or s["d"] or s["c"] or s["fa"] or s["vsl_b"] is not None):
        raise ValueError("runner rows are main runs without replicates, delays, false alarm or VSL (R5)")


def schedule(spec: dict, onset: float, duration: float) -> tuple:
    if spec["post"] is None:
        return None, None
    if spec["fa"]:
        return fa_schedule(spec["seed"])
    return switch_schedule(onset, duration, spec["d"], spec["c"], spec["back"])


def lane_count(edge: str) -> int:
    return ls.edge.getLaneNumber(edge)


def queue_now(len1: float, len2: float) -> tuple:
    """(halted vehicles on edges 1-2, metres from the stop line to the last halted one; R7)."""
    n_h, far = 0, 0.0
    for e, off, L in (("2", 0.0, len2), ("1", len2, len1)):
        if ls.edge.getLastStepHaltingNumber(e) == 0:
            continue
        for v in ls.edge.getLastStepVehicleIDs(e):
            if ls.vehicle.getSpeed(v) < HALT_MPS:
                n_h += 1
                far = max(far, off + L - ls.vehicle.getLanePosition(v))
    return n_h, far


def run_episode(spec: dict, run_dir: Path, *, warmup_s: float = 40.0, control_s: float = 900.0,
                t_drain_max: float = 7200.0, av_share: float = 0.1, keep_files: bool = False) -> dict:
    check_spec(spec)
    pre, post, inc_kind, q, seed = spec["pre"], spec["post"], spec["incident"], float(spec["q"]), int(spec["seed"])
    t_wall0 = time.time()
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    files = plant.files()
    seeds = replicate_seeds(seed, spec["k"])
    dem = plant.demand(seeds["demand_seed"], [(0.0, warmup_s + control_s, q)], av_share=av_share)
    runners = rn.apply_runners(dem, seeds["demand_seed"], spec["rs"])
    tag = run_key(**{f: spec[f] for f in SPEC_FIELDS}) + f"_pid{os.getpid()}"
    rou, trip = run_dir / f"routes_{tag}.rou.xml", run_dir / f"tripinfo_{tag}.xml"
    dem.write(rou)
    sim = _Sim(files["net"], rou, run_dir, dem, additional=[files["add"]], step_length=plant.STEP_LENGTH,
               checkpoint_s=300.0, seed=seeds["sumo_seed"], extra_args=["--tripinfo-output", str(trip)])
    onset, duration = incident_window(seed, warmup_s, control_s)
    inc = Incident(inc_kind, onset, duration, api=ls)
    t_sw_plan, t_bk_plan = schedule(spec, onset, duration)
    vsl = PostedVSL(spec["vsl_b"]) if spec["vsl_b"] is not None else None
    log = []
    meter = None

    def read(edge, t):
        n = ls.edge.getLastStepVehicleNumber(edge)
        log.append((round(t, 2), int(n), round(meter.q, 3)))
        return float(n)

    sim.start()
    plant.set_all_green()
    sim.asserts.append(plant.assert_all_green)
    sim.asserts.append(inc.assert_state)
    if vsl is not None:
        sim.asserts.append(vsl.assert_state)
    if pre != fam.NC:
        meter = P1bMeter(pre, read=read, cum_out=lambda t: sim.arrived)
        sim.asserts.remove(plant.assert_all_green)
    sim.run_until(sim.t + warmup_s)
    t_ctrl0, arr0 = sim.t, sim.arrived
    len1, len2 = ls.lane.getLength("1_0"), ls.lane.getLength(f"{METER_EDGE}_0")
    avail_m = len1 + len2
    n_lanes2 = lane_count(METER_EDGE)
    e4 = {"prev": set(ls.edge.getLastStepVehicleIDs("4")), "n": 0, "n_ext": 0}
    cr = {"prev": set(ls.edge.getLastStepVehicleIDs(METER_EDGE)), "state": "G" if meter is None else None,
          "n": {"G": 0, "y": 0, "r": 0}, "runner": {"G": 0, "y": 0, "r": 0}}

    def hook():
        ids = set(ls.edge.getLastStepVehicleIDs("4"))
        new = len(ids - e4["prev"])
        if inc.on:
            e4["n"] += new
        if inc.on or (inc.t_off is not None and sim.t <= inc.t_off + EXT_S + 1e-9):
            e4["n_ext"] += new
        e4["prev"] = ids
        ids2 = set(ls.edge.getLastStepVehicleIDs(METER_EDGE))
        st_ = cr["state"] or "G"
        for v in cr["prev"] - ids2:   # left edge 2 in this step: crossed the stop line (in the state of this step)
            cr["n"][st_] += 1
            if v in runners:
                cr["runner"][st_] += 1
        cr["prev"] = ids2

    sim.hook = hook
    t_switch = q_at_switch = t_back = q_at_back = None
    max_queue = max_halted = 0
    max_queue_m = 0.0
    q_sum, n_ticks = 0.0, 0
    approach, red_leaders, last_state = [], None, None
    while sim.t < t_ctrl0 + control_s - 1e-9:
        t = sim.t
        inc.tick(t)
        if t_sw_plan is not None and abs(t - t_sw_plan) < 1e-6:
            if not spec["fa"] and not inc.on:
                raise RuntimeError(f"scheduled switch at {t} while the incident is off")
            q_at_switch = round(meter.q, 3)
            meter.set_law(post)
            t_switch = t
        elif t_bk_plan is not None and abs(t - t_bk_plan) < 1e-6:
            q_at_back = round(meter.q, 3)
            meter.set_law(pre)
            t_back = t
        if vsl is not None:
            vsl.tick(t, inc.on)
        nq = len(ls.simulation.getPendingVehicles()) + ls.edge.getLastStepVehicleNumber("1") + \
            ls.edge.getLastStepVehicleNumber("2")
        max_queue = max(max_queue, int(nq))
        nh, qm = queue_now(len1, len2)
        max_halted, max_queue_m = max(max_halted, nh), max(max_queue_m, qm)
        if meter is not None:
            s_ = meter.step(t)
            cr["state"] = s_
            q_sum += meter.q
            n_ticks += 1
            if s_ == "r" and last_state != "r":          # r onset: the lane leaders on edge 2
                red_leaders = {}
                for i in range(n_lanes2):
                    vs = ls.lane.getLastStepVehicleIDs(f"{METER_EDGE}_{i}")
                    if vs:
                        lead = max(vs, key=ls.vehicle.getLanePosition)
                        if len2 - ls.vehicle.getLanePosition(lead) <= APPROACH_M:
                            red_leaders[lead] = ls.vehicle.getSpeed(lead)
            elif s_ == "G" and last_state != "G" and red_leaders is not None:
                on2 = set(ls.edge.getLastStepVehicleIDs(METER_EDGE))
                approach += [round(v, 3) for vid, v in red_leaders.items() if vid in on2]
                red_leaders = None
            last_state = s_
        sim.run_until(t + 1.0)
    sim.hook = None
    if post is not None and not spec["fa"]:
        if spec["d"] == 0 and t_switch != inc.t_on or spec["back"] and spec["c"] == 0 and t_switch is not None \
                and t_back != inc.t_off:
            raise RuntimeError(f"switch schedule {t_switch}/{t_back} != incident ticks {inc.t_on}/{inc.t_off}")
    ctrl_s = sim.t - t_ctrl0
    still_on = inc.on
    inc.clear(sim.t)
    m = {"served_ctrl_vph": (sim.arrived - arr0) * 3600.0 / ctrl_s, "ttt_ctrl_vehh": sim.tts_system / 3600.0,
         "n_system_ctrl_end": ls.vehicle.getIDCount() + len(ls.simulation.getPendingVehicles())}
    nhat_log = meter.nhat_log if meter is not None else None
    if meter is not None:
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
    eb_meter = None if eb_edge is None else sum(v for e, v in eb_edge["all"].items()
                                                 if e == METER_EDGE or e.startswith(":3"))
    n_cross = sum(cr["n"].values())
    n_run_cross = sum(cr["runner"].values())
    out = {**{f: spec[f] for f in SPEC_FIELDS}, "sumo_seed": seeds["sumo_seed"], "demand_seed": seeds["demand_seed"],
           "onset_s": onset, "duration_s": duration, "t_on": inc.t_on, "t_off": inc.t_off,
           "fa_time_s": fa_window(seed)[0] if spec["fa"] else None,
           "incident_on_at_control_end": still_on, "incident_log": inc.log,
           "t_switch_plan": t_sw_plan, "t_back_plan": t_bk_plan,
           "t_switch": t_switch, "q_at_switch": q_at_switch, "t_back": t_back, "q_at_back": q_at_back,
           "delay_s": float(np.mean(delays)) if delays else float("nan"),
           "depart_delay_s": float(np.mean([d for d, _ in trips])) if trips else float("nan"),
           **m, "max_queue": max_queue, "max_queue_halted_veh": max_halted, "max_queue_m": round(max_queue_m, 2),
           "avail_m": round(avail_m, 2),
           "entered_e4_incident": e4["n"] if inc.t_on is not None else None,
           "entered_e4_ext120": e4["n_ext"] if inc.t_on is not None else None, "signal": SIGNAL,
           "n_runners": len(runners), "runner_hash": hashlib.sha1(" ".join(sorted(runners)).encode()).hexdigest()[:16],
           "crossings": cr["n"], "runner_crossings": cr["runner"],
           "red_cross_share": cr["n"]["r"] / n_cross if n_cross else None,
           "runner_red_cross_share": cr["runner"]["r"] / n_run_cross if n_run_cross else None,
           "discharge_vph": {s_: v * 3600.0 / ctrl_s for s_, v in cr["n"].items()},
           "commanded_mean_vph": q_sum / n_ticks if n_ticks else None,
           "approach_red_mps": {"n": len(approach), "median": float(np.median(approach)) if approach else None,
                                "max": float(max(approach)) if approach else None,
                                "n_ge_10": int(sum(v >= 10.0 for v in approach))},
           "emergency_meter": eb_meter,
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
    res = run_episode({f: spec.get(f, 0.0 if f == "rs" else None) for f in SPEC_FIELDS}, Path(a.run_dir),
                      keep_files=a.keep_files)
    res["key"] = spec.get("key")
    res["code_commit"] = spec.get("code_commit")
    out = Path(a.out)
    tmp = out.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(res))
    tmp.replace(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
