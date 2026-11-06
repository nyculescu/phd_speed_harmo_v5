"""V397: report-only replays of confirmatory 3's X2 cell at 5,300 on the evaluation seeds, frozen code d2b2ecc.
A wrapper adds read-only counters after each second: TTC below 3 s by lane at merge 2 and by follower and leader class.
base: must reproduce every stored number. long: runs to 3,000 s, with a snapshot at 1,800 s. usage: rerun.py base|long out.jsonl workers [arm seed]"""
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

O = "/home/catalin/work/phd/v5b1_runs/conf3/"
ARMS = ["d0", "d1", "d2", "d3", "d4", "os1_15_10", "r4a1", "lr1000_16_2", "p333", "nc"]
SEEDS = range(7_440_200, 7_440_220)
SNAP = 1800.0


def stored():
    return {(r["name"], r["seed"]): r for r in map(json.loads, open(O + "eval_primary.jsonl")) if r["q"] == 5300.0}


def job(a):
    name, c, seed, rd, long = a
    import libsumo as ls
    from v5b.fleet import b_env as be, plant_sweep as ps
    ex = defaultdict(float)
    snap = {}
    make0 = be.make

    def cls(env, v):
        s = env.dem.by_id.get(v)
        return s.cls if s is not None else "other"

    def observe(env, t):
        w = "" if t <= SNAP + 1e-9 else "late_"
        l4a = ls.lane.getLength("4a_0")
        for v in ls.vehicle.getIDList():
            lead = ls.vehicle.getLeader(v, 200.0)
            if not lead or not lead[0]:
                continue
            s = ls.vehicle.getSpeed(v)
            dv = s - ls.vehicle.getSpeed(lead[0])
            hit = dv > 0 and (lead[1] + ls.vehicle.getMinGap(v)) / dv < 3.0
            f, l = cls(env, v), cls(env, lead[0])
            road, lane = ls.vehicle.getRoadID(v), ls.vehicle.getLaneID(v)
            zone = "m2" if road in ("4a", "r2", "rj2") else "r3" if road == "3" else "other"
            ex[f"{w}exp_{f}_{l}"] += 1
            if hit:
                ex[f"{w}ttc_all"] += 1
                ex[f"{w}ttc_{f}_{l}"] += 1
                ex[f"{w}ttc_{zone}_{f}"] += 1
                ex[f"{w}ttc_fast" if s >= 5.0 else f"{w}ttc_slow"] += 1
            if lane == "4a_0":
                ex[f"{w}ttc_4a0"] += hit
                if ls.vehicle.getLanePosition(v) > l4a - 50.0:
                    ex[f"{w}ttc_4a0_end50"] += hit
            elif road == "4a":
                ex[f"{w}ttc_4a_main"] += hit
        if abs(t - SNAP) < 1e-6:
            snap.update(passed=env.ep["passed"], N=env.ep["N"], E30=env.ep["E30"] + env.ep.get("out_E30", 0.0), live=ls.vehicle.getIDCount(), pending=len(ls.simulation.getPendingVehicles()))

    def make(*args, **kw):
        env = make0(*args, **kw)
        sec_orig = env._second

        def wrapped():
            r = sec_orig()
            if env.sim.t > env.warm + 1e-9:
                observe(env, env.sim.t)
            return r
        env._second = wrapped
        return env

    be.make = make
    row = ps.run_one((name, c, 5300.0, seed, rd))
    row["extra"] = dict(ex)
    row["snap"] = snap
    row["long"] = long
    return row


if __name__ == "__main__":
    mode, out, w = sys.argv[1], sys.argv[2], int(sys.argv[3])
    S = stored()
    long = mode == "long"
    pick = [(sys.argv[4], int(sys.argv[5]))] if len(sys.argv) > 5 else [(a, s) for a in ARMS for s in SEEDS]
    jobs = []
    for a, s in pick:
        c = json.loads(json.dumps(S[(f"X2|{a}", s)]["cfg"]))
        if long:
            c.setdefault("ctrl", {}).setdefault("env", {})["episode"] = 2700.0
        jobs.append((f"X2|{a}", c, s, f"/home/catalin/work/phd/v5b1_runs/phase3/scratch/rerun/rd_{mode}", long))
    with ProcessPoolExecutor(w, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex, open(out, "a") as fo:
        futs = [ex.submit(job, j) for j in jobs]
        for f in as_completed(futs):
            fo.write(json.dumps(f.result()) + "\n")
            fo.flush()
    print("done", len(jobs), flush=True)
