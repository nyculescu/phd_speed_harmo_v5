"""V314: staged no-control sweeps towards the best no-control plant. Only no-control runs are scored, so no controller
result can shape the plant. Stages: A one setting at a time; B random combinations in three families (lane changing;
plus road; plus drivers); C the best of each family on more seeds; D each family's winner against the adopted plant on a
demand ladder. The author picks from D; a frozen plant is then checked on unused seeds.

Usage: python -m v5b.fleet.plant_sweep stages --out DIR --workers 28
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import numpy as np

LC = {"lcStrategic": [0.5, 2, 5], "lcCooperative": [0.5, 0.8], "lcSpeedGain": [0.5, 2, 5, 10], "lcKeepRight": [0, 0.5, 2],
      "lcAssertive": [0.5, 1.5, 2, 3], "lcLookaheadLeft": [1, 4], "lcSpeedGainLookahead": [5, 10], "lcImpatience": [0.5, 1]}
ROAD = {"limit_kmh": [80, 90, 110, 120], "accel_len": [200, 450, 600]}
DRIVER = {"tau_scale": [0.7, 0.9, 1.0], "asl_scale": [0.25, 1.0], "sigma_scale": [0.25, 0.5, 0.75], "accel": [2.0, 3.2], "model": ["IDM", "EIDM"]}
FAMILIES = {"lc": LC, "lc_road": {**LC, **ROAD}, "all": {**LC, **ROAD, **DRIVER}}
SEEDS = {"A": range(7_419_610, 7_419_615), "B": range(7_419_615, 7_419_618), "C": range(7_419_618, 7_419_623), "D": range(7_419_623, 7_419_640)}
LEVELS, LADDER = (4600.0, 5300.0), (4090.0, 4600.0, 5300.0, 6000.0)
N_RANDOM, N_TOP = 100, 5
METRICS = (("flow", "passed", 1), ("ttt", "N", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1))
CLIP = 30.0     # no single metric may decide the score
REF_SPEED = 100.0 / 3.6
ST_DT, ST_DX, ST_T, ST_X = 10.0, 100.0, 150, 65
ST_OFFSET = {"1": 0.0, "2": 3000.0, "3a": 3498.3, "3": 3793.02, "4": 4989.02, "5": 5989.02}


def to_plant(c: dict) -> dict:
    p = {"lc": {k: v for k, v in c.items() if k in LC}}
    for k in ("tau_scale", "asl_scale", "sigma_scale", "accel_len"):
        if k in c:
            p[k] = c[k]
    if "limit_kmh" in c:
        p["limit"] = c["limit_kmh"] / 3.6
    p["hdv"] = {}
    if "accel" in c:
        p["hdv"]["accel"] = c["accel"]
    if "model" in c:
        p["hdv"]["carFollowModel"] = c["model"]
    p["truck"] = {"sigma": 0.5 * c["sigma_scale"]} if "sigma_scale" in c else {}     # trucks use SUMO's default Krauss sigma
    if "human_undertake" in c:
        p["hdv"]["lcOvertakeRight"] = p["truck"]["lcOvertakeRight"] = c["human_undertake"]
    if c.get("smooth"):
        p["smooth"] = True
    if c.get("ease"):
        p["ease"] = True
    for k in ("ease_max", "smooth_s", "tau_rise", "taper_fast", "fix_x"):
        if k in c:
            p[k] = c[k]
    if "geom" in c:
        p["geom"] = c["geom"]
    if c.get("smooth") or c.get("alks_undertake"):
        p["alks"] = {"lcOvertakeRight": 1}
    return p


def run_one(a: tuple) -> dict:
    name, c, q, seed, rd = a
    import libsumo as ls
    from v5b.fleet import b_env as be, control as ct, fleet as fl
    ctrl = c.get("ctrl", {})     # V332: rules on the frozen plant: {"cav_rule": [u, m, d]}, {"zones": [u, m, d]} or {"meter": {"setpoint": %}}
    kw = {"cav": True, "decision": 5.0} if {"cav_rule", "pt", "local_rule", "pattern", "road_levels", "adaptive_4a", "own_state"} & set(ctrl) else {"zones": True, "decision": 10.0, "w_change": 0.1}
    kw |= ctrl.get("env", {})
    if "pt" in ctrl:     # round 1: a policy brings the environment options it acts through, e.g. 3B's base rule
        from v5b.fleet.c_train import act_env
        kw |= act_env(ctrl["pt"])
    env = be.make(alks_asl=0.5, ref_delay=True, share=0.5, levels=(q,), run_dir=rd, seeds=[seed], report_net=True, plant=to_plant(c), **kw)
    rule = be.CavRule(ctrl["cav_rule"], speed=ctrl.get("speed", 0)) if "cav_rule" in ctrl else None
    if "local_rule" in ctrl:
        rule = be.LocalRule(env, **ctrl["local_rule"])
    if "pattern" in ctrl:
        rule = be.ZonePattern(ctrl["pattern"], fix=bool(c.get("fix_x")))
    if "adaptive_4a" in ctrl:
        rule = be.AdaptiveOn4a(env, **ctrl["adaptive_4a"])
    if "own_state" in ctrl:
        rule = be.OwnState(**ctrl["own_state"])
    if "road_levels" in ctrl:
        rule = be.RoadLevels(ctrl["road_levels"])
    if "pt" in ctrl:
        from v5b.fleet.c_train import Greedy
        rule = Greedy(ctrl["pt"])
    meter = bank = None
    S, arr, prev, left, prev_a = defaultdict(float), {}, {}, {}, {}
    road_lane, lane_t, accel_t = {}, {}, {}
    flow_min, v20_min = defaultdict(int), defaultdict(list)
    st = np.zeros((2, ST_T, ST_X)) if ctrl.get("st") else None
    attr = defaultdict(lambda: [0, 0, 0]) if ctrl.get("attrib") else None     # exposure, TTC below 3 s, braking at 3 m/s²
    step0, sec0 = env._sim_step, env._second

    def step():
        step0()
        for v in ls.simulation.getArrivedIDList():
            arr[v] = env.sim.t
        if env.sim.t > env.warm + 1e-9:
            at_step(env.sim.t)

    def at_step(t):
        """V369: the 1-Hz samples below can miss what a 1-Hz actuator causes (V367), so braking and fuel are also read every step."""
        half = abs(t % 1.0 - 0.5) < 1e-6
        dt = env.dt
        for v in ls.vehicle.getIDList():
            a, s = ls.vehicle.getAcceleration(v), ls.vehicle.getSpeed(v)
            alks = v in env.alks_all
            S["dist_step"] += s * dt
            S["fuel_step"] += ls.vehicle.getFuelConsumption(v) * dt
            S["jerk_step"] += abs(a - prev_a.get(v, a))
            if a <= -3.0:
                S["b3_step"] += dt
                S["b45_step"] += dt * (a <= -4.5)
                S["b7_step"] += dt * (a <= -7.0)
                if alks:
                    S["alks_b3_step"] += dt
                    S["alks_b45_step"] += dt * (a <= -4.5)
                    S["alks_b7_step"] += dt * (a <= -7.0)
                    if a <= -8.99 and prev_a.get(v, 0.0) > -8.99:
                        S["alks_full_events"] += 1
                        S["alks_full_moving" if s >= 2.0 else "alks_full_creep"] += 1     # a lane-end crawl reads -9 m/s² at 0.4 m/s (V377)
                    lead = ls.vehicle.getLeader(v, 200.0)
                    if not (lead and lead[0]) or lead[1] / max(s, 1.0) > 3.0:
                        S["free_brake_alks_step"] += dt
            prev_a[v] = a
            if half:
                lead = ls.vehicle.getLeader(v, 200.0)
                if lead and lead[0]:
                    dv = s - ls.vehicle.getSpeed(lead[0])
                    S["ttc_half"] += dv > 0 and (lead[1] + ls.vehicle.getMinGap(v)) / dv < 3.0

    def period(t):
        spec = env.pert.s if env.pert is not None and env.pert.kind == "slowdown" else None
        if spec is None:
            return "rest"
        if t < spec["times"][0]:
            return "before"
        for t0 in spec["times"]:
            if t0 <= t < t0 + spec.get("taper", 0.0):
                return "taper"
            if t0 <= t < t0 + spec["dur"]:
                return "hold"
            if t0 + spec["dur"] <= t < t0 + spec["dur"] + 120.0:
                return "after"
        return "rest"

    def conflicts(t):
        """V378: the 1-Hz TTC count by road, follower speed and period, with two shorter thresholds and a severity count: what the deciding count is made of."""
        per = period(t)
        for v in ls.vehicle.getIDList():
            lead = ls.vehicle.getLeader(v, 200.0)
            if not lead or not lead[0]:
                continue
            s = ls.vehicle.getSpeed(v)
            dv = s - ls.vehicle.getSpeed(lead[0])
            if dv <= 0:
                continue
            gap = lead[1] + ls.vehicle.getMinGap(v)
            road = ls.vehicle.getRoadID(v)
            road = road if road in ("3", "4a") else "ramp2" if road in ("r2", "rj2") else "rest"
            band = "lo" if s < 5.0 else "mid" if s < 10.0 else "hi"
            ttc = gap / dv
            for m, hit in (("ttc3", ttc < 3.0), ("ttc2", ttc < 2.0), ("ttc15", ttc < 1.5), ("sev3", dv * dv / (2.0 * max(gap, 0.1)) >= 3.0)):
                if hit:
                    S[m] += 1
                    S[f"{m}_r_{road}"] += 1
                    S[f"{m}_s_{band}"] += 1
                    S[f"{m}_p_{per}"] += 1

    def pass_kind(v, n, s, t):
        """V369: most counted passes are cars side by side (48-89 per run); only straight driving while closing is an undertake."""
        if t - accel_t.get(v, -99.0) <= 5.0 or t - accel_t.get(n, -99.0) <= 5.0:
            return "pass_merging"
        if t - lane_t.get(v, -99.0) <= 5.0 or t - lane_t.get(n, -99.0) <= 5.0:
            return "pass_lane_change"
        return "pass_straight" if s - ls.vehicle.getSpeed(n) > 1.0 else "pass_side_by_side"

    def sec():
        p0 = env.ep["passed"]
        r = sec0()
        if meter is not None:
            if round(env.sim.t) % 30 == 0:
                bank.read(env.sim.t)
            meter.step(env.sim.t)
        conflicts(env.sim.t)
        if hasattr(env, "lvl"):
            for v in env.alks_all & set(ls.vehicle.getIDList()):
                road = ls.vehicle.getRoadID(v)
                if not road.startswith(":"):
                    S[f"lv_sum_{road}"] += env.lvl.get(v, 0)
                    S[f"lv_n_{road}"] += 1
                tau = ls.vehicle.getTau(v)
                S["tau_mismatch"] += abs(tau - env.v2v_cur.get(v, be.ALKS_TAU0)) > 1e-6
                if v in env.on:
                    S["tau_on_n"] += 1
                    S["tau_on_match"] += abs(tau - env.headways[env.lvl.get(v, 0)]) < 1e-6
        m = int(env.sim.t // 60)
        flow_min[m] += env.ep["passed"] - p0
        v20_min[m].append(ls.lane.getLastStepMeanSpeed("2_0"))
        for v in ls.vehicle.getIDList():
            ln = ls.vehicle.getLaneID(v)
            if not ln.startswith(":"):
                e, i = ln.rsplit("_", 1)
                rl = int(i) - 1 if e in ("3a", "4a") else int(i)
                if road_lane.get(v, rl) != rl:
                    lane_t[v] = env.sim.t
                road_lane[v] = rl
                if ln in ("3a_0", "4a_0"):
                    accel_t[v] = env.sim.t
        for v in ls.vehicle.getIDList():
            x, s, f = ls.vehicle.getAcceleration(v), ls.vehicle.getSpeed(v), ls.vehicle.getFuelConsumption(v)
            S["vs"] += 1
            S["dist"] += s
            S["a2"] += x * x
            S["jerk"] += abs(x - prev.get(v, x))
            prev[v] = x
            S["fuel"] += f
            S["fuel_truck"] += f * (v in trucks)
            S["b45"] += x <= -4.5
            S["b7"] += x <= -7.0
            if attr is not None:
                sp = env.dem.by_id[v]
                lead = ls.vehicle.getLeader(v, 200.0)
                dv = s - ls.vehicle.getSpeed(lead[0]) if lead and lead[0] else 0.0
                gap = lead[1] + ls.vehicle.getMinGap(v) if lead and lead[0] else 1e9
                for key in (sp.cls, f"tau{min(int(sp.tau // 0.4), 3)}" if sp.cls == "hdv_car" else None, f"sigma{min(int(sp.sigma // 0.2), 3)}" if sp.cls == "hdv_car" else None, f"sf{int(sp.sf * 10)}" if sp.cls == "hdv_car" else None):
                    if key:
                        c = attr[key]
                        c[0] += 1
                        c[1] += dv > 0 and gap / dv < 3.0
                        c[2] += x <= -3.0
            if st is not None:
                off = ST_OFFSET.get(ls.vehicle.getRoadID(v))
                if off is not None:
                    i, j = int((env.sim.t - env.warm) // ST_DT), int((off + ls.vehicle.getLanePosition(v)) // ST_DX)
                    if i < ST_T and j < ST_X:
                        st[0, i, j] += s
                        st[1, i, j] += 1
            if v in env.alks_all:
                if x <= -3.0:
                    lead = ls.vehicle.getLeader(v, 200.0)
                    if not (lead and lead[0]) or lead[1] / max(s, 1.0) > 3.0:
                        S["free_brake_alks"] += 1
                if s > 60.0 / 3.6:     # a left-lane leader one second ago is now a left-lane follower: passed on the right
                    for n, _ in ls.vehicle.getNeighbors(v, 0):
                        if n in left.get(v, ()):
                            S["undertakes"] += 1
                            S[pass_kind(v, n, s, env.sim.t)] += 1
                    left[v] = {n for n, _ in ls.vehicle.getNeighbors(v, 2)}
                else:
                    left.pop(v, None)
        lanes = set(ls.lane.getIDList())
        for x in ("3a_0", "3a_1"):
            S["halt_" + x] += ls.lane.getLastStepHaltingNumber(x)
        for x in lanes & {"3a_1", "3a_2", "3a_3", "3_0", "3_1", "3_2", "4a_1", "4a_3"}:
            n = ls.lane.getLastStepVehicleNumber(x)
            S["n_" + x] += n
            S["nv_" + x] += n * ls.lane.getLastStepMeanSpeed(x)
        l3a = ls.lane.getLength("3a_0")
        S["end_stop"] += sum(ls.vehicle.getSpeed(v) < 1.0 and ls.vehicle.getLanePosition(v) > l3a - 30.0 for v in ls.lane.getLastStepVehicleIDs("3a_0"))
        if "4a_0" in lanes:
            l4a = ls.lane.getLength("4a_0")
            S["end_stop2"] += sum(ls.vehicle.getSpeed(v) < 1.0 and ls.vehicle.getLanePosition(v) > l4a - 30.0 for v in ls.lane.getLastStepVehicleIDs("4a_0"))
        S["teleports"] += ls.simulation.getStartingTeleportNumber()
        return r

    env._sim_step, env._second = step, sec
    o = env.reset()[0]
    trucks = {v.vid for v in env.dem.veh if v.cls == "truck"}
    if "meter" in ctrl:
        bank = ct.LoopBank(fl.loop_ids(env.cfg.geom))
        bank.read(env.sim.t)
        meter = ct.SumoMeter(ct.Meter(ct.MeterLaw("alinea", ctrl["meter"]["setpoint"])), bank, "alinea")
    fixed = np.array(ctrl.get("zones", (0, 0, 0)), int)
    while True:
        o, _, _, tr, inf = env.step(rule(o) if rule else fixed)
        if tr:
            break
    length = {r: sum(ls.lane.getLength(f"{e}_0") for e in x[0].split()) for r, x in fl.routes(env.cfg.geom).items()}
    delay, ramp, ramp2 = [], [], []
    planned = done = 0
    for v, r in zip(env.dem.veh, env.dem.route_of):
        if env.warm <= v.depart < env.t_end:
            planned += 1
            t = arr.get(v.vid)
            if t is not None and t <= env.t_end:
                done += 1
                d = t - v.depart - length[r] / (REF_SPEED * v.sf)
                delay.append(d)
                if r == "ramp":
                    ramp.append(d)
                elif r == "ramp2":
                    ramp2.append(d)
    env.close()
    ep = inf["ep"]
    row = {"name": name, "cfg": c, **{k: ep[k] for k in ("q", "seed", "passed", "arrived", "N", "mean_v", "E15", "E30", "out_E30", "brake3", "brake45", "out_b3", "collisions", "contact_steps", "stop_gap", "gap25", "steps")}}
    row |= {k: float(v) for k, v in S.items()}
    row |= {"ttc_net": ep["E30"] + ep["out_E30"], "brake_net": ep["brake3"] + ep["out_b3"], "b45_net": S["b45"], "b7_net": S["b7"], "fuel_km": S["fuel"] / max(S["dist"], 1.0) * 1000.0,
            "delay": float(np.mean(delay)) if delay else None, "delay_p95": float(np.percentile(delay, 95)) if delay else None, "delay_ramp": float(np.mean(ramp)) if ramp else None,
            "finished_pct": 100.0 * done / max(planned, 1), "flow_min": [flow_min[m] for m in sorted(flow_min)], "v20_min": [round(float(np.mean(v20_min[m])), 2) for m in sorted(v20_min)]}
    if ramp2:
        row["delay_ramp2"] = float(np.mean(ramp2))
    row["all_delay"] = ep["N"] - S["dist_step"] / REF_SPEED     # vehicle-seconds; unfinished vehicles and the insertion queue included
    if "dist_s" in ep:     # the same, from 1-s samples, as training computes it (round 1, 2C)
        row["delay_s"] = ep["N"] - ep["dist_s"] / REF_SPEED
    if "lv" in ep:
        row["lv"] = ep["lv"]
    if attr is not None:
        row["attrib"] = dict(attr)
    if st is not None:     # mean speed x 10 and vehicle-seconds per 10-s, 100-m cell along the mainline
        row |= {"st_v": np.round(10.0 * st[0] / np.maximum(st[1], 1.0)).astype(int).ravel().tolist(), "st_n": st[1].astype(int).ravel().tolist()}
    if env.pert is not None:
        row["pert_log"] = env.pert.log
    if meter is not None:
        ms = meter.summary()
        row |= {"meter_wait_p95": ms["wait_p95_s"], "meter_wait_max": ms["wait_max_s"], "meter_served": ms["n_waits"]}
    return row


def matrix(cfgs: dict, levels: tuple, seeds, f: Path, workers: int, rd: str) -> list:
    done = {(r["name"], r["q"], r["seed"]) for r in map(json.loads, f.read_text().splitlines())} if f.exists() else set()
    jobs = [(n, c, q, s, rd) for n, c in cfgs.items() for q in levels for s in seeds if (n, q, s) not in done]
    print(f.name, len(jobs), "jobs", flush=True)
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex, f.open("a") as w:
        futs = {ex.submit(run_one, j): j for j in jobs}
        failed = []
        for fut in as_completed(futs):
            try:
                row = fut.result()
            except BrokenProcessPool:
                raise
            except Exception as x:     # keep the batch's other rows; the name is logged at once
                failed.append(futs[fut][0])
                print("FAILED", futs[fut][0], futs[fut][2], futs[fut][3], repr(x)[:300], flush=True)
                continue
            w.write(json.dumps(row) + "\n")
            w.flush()
    if failed:
        raise RuntimeError(f"{len(failed)} of {len(jobs)} jobs failed, first {failed[0]}")
    return [json.loads(x) for x in f.read_text().splitlines()]


def score(rows: list, base: str = "base") -> dict:
    """Per setting: the mean over levels and metrics of the median paired % improvement on the adopted plant, each clipped."""
    T = defaultdict(dict)
    for r in rows:
        T[(r["name"], r["q"])][r["seed"]] = r
    out = defaultdict(lambda: {"parts": defaultdict(list), "collisions": 0, "n": 0})
    for (n, q), A in T.items():
        B = T.get((base, q), {})
        ds = sorted(set(A) & set(B))
        if not ds:
            continue
        o = out[n]
        o["collisions"] += sum(A[k]["collisions"] for k in ds)
        o["n"] += len(ds)
        for lab, key, sign in METRICS:
            ref = max(float(np.median([B[k][key] for k in ds])), 1.0)
            o["parts"][lab].append(float(np.median([sign * (A[k][key] - B[k][key]) / ref * 100.0 for k in ds])))
    res = {}
    for n, o in out.items():
        parts = {k: float(np.mean(v)) for k, v in o["parts"].items()}
        res[n] = {"S": float(np.mean([np.clip(x, -CLIP, CLIP) for x in parts.values()])), "collisions": o["collisions"], "n": o["n"], **parts}
    return res


def family_of(c: dict) -> str:
    if set(c) & set(DRIVER):
        return "all"
    return "lc_road" if set(c) & set(ROAD) else "lc"


def stages(out: Path, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rd = str(out / "rd")
    cfgs = {"base": {}}
    for k, vals in FAMILIES["all"].items():
        for v in vals:
            cfgs[f"{k}={v}"] = {k: v}
    ra = matrix(cfgs, LEVELS, SEEDS["A"], out / "stage_a.jsonl", workers, rd)
    sa = score(ra)
    (out / "stage_a_score.json").write_text(json.dumps(sa, indent=0))
    good = defaultdict(list)
    for n, s in sa.items():
        if n != "base" and s["S"] > 0:
            k, c = n, cfgs[n]
            good[next(iter(c))].append(next(iter(c.values())))
    print("stage A, values that improve:", dict(good), flush=True)
    rng = np.random.default_rng(20261103)
    cb = {"base": {}}
    for fam, knobs in FAMILIES.items():
        pool = {k: good[k] for k in knobs if good.get(k)}
        for i in range(N_RANDOM):
            c = {}
            for k, vals in pool.items():     # each setting: stay at its default, or one improving value
                j = int(rng.integers(0, len(vals) + 1))
                if j:
                    c[k] = vals[j - 1]
            cb[f"{fam}#{i}"] = c
    (out / "stage_b_cfgs.json").write_text(json.dumps(cb, indent=0))
    rb = matrix(cb, LEVELS, SEEDS["B"], out / "stage_b.jsonl", workers, rd)
    sb = score(rb)
    (out / "stage_b_score.json").write_text(json.dumps(sb, indent=0))
    cc = {"base": {}}
    for fam in FAMILIES:
        ok = sorted((n for n in sb if n.startswith(fam + "#") and not sb[n]["collisions"] and family_of(cb[n]) == fam), key=lambda n: -sb[n]["S"])
        cc |= {n: cb[n] for n in ok[:N_TOP]}
    rc = matrix(cc, LEVELS, SEEDS["C"], out / "stage_c.jsonl", workers, rd)
    sc = score(rc)
    (out / "stage_c_score.json").write_text(json.dumps(sc, indent=0))
    cd = {"base": {}}
    for fam in FAMILIES:
        ok = sorted((n for n in cc if n.startswith(fam + "#")), key=lambda n: (bool(sc[n]["collisions"]), -sc[n]["S"]))
        if ok:
            cd[fam] = cc[ok[0]]
    (out / "stage_d_cfgs.json").write_text(json.dumps(cd, indent=0))
    rd_rows = matrix(cd, LADDER, SEEDS["D"], out / "stage_d.jsonl", workers, rd)
    (out / "stage_d_score.json").write_text(json.dumps(score(rd_rows), indent=0))
    print("done", flush=True)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=("stages",))
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=28)
    a = ap.parse_args(argv)
    stages(Path(a.out), a.workers)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
