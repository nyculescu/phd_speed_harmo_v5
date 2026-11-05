"""Second trace: braking by sampling phase, free-road share, speed lost per event, and speed series of two vehicles."""
import json, sys, collections as C
import numpy as np, libsumo as ls
from v5b.fleet import b_env as be, plant_sweep as ps
name, cfg, q, seed = sys.argv[1], json.loads(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
rd = "/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp/trace2_" + name
env = be.make(alks_asl=0.5, ref_delay=True, share=0.5, levels=(q,), run_dir=rd, seeds=[seed], report_net=True, plant=ps.to_plant(cfg), zones=True, decision=10.0, w_change=0.1)
orig = env._sim_step
cnt = C.Counter(); ph = {th: C.Counter() for th in (3.0, 4.5, 7.0)}; prev = {}; open_ev = {}; drops = []; speeds = []; series = {}
WATCH = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else set()
def step():
    orig()
    t = env.sim.t
    if t < env.warm:
        return
    p = round(t % 1, 1) % 1
    for v in ls.vehicle.getIDList():
        a = ls.vehicle.getAcceleration(v)
        s = ls.vehicle.getSpeed(v)
        alks = v in env.alks_all
        cl = "alks" if alks else env.dem.by_id[v].cls
        if a <= -3.0:
            for th in ph:
                if a <= -th and alks:
                    ph[th][p] += 1
                if a <= -th:
                    cnt[f"{cl}_{th}"] += 1
            if alks:
                lead = ls.vehicle.getLeader(v, 200.0)
                free = not (lead and lead[0]) or lead[1] / max(s, 1.0) > 3.0
                if free:
                    cnt["alks_free_3.0"] += 1
                    if p == 0:
                        cnt["alks_free_3.0_at_whole_second"] += 1
        if alks:
            cnt["alks_steps"] += 1
            if a <= -8.99 and prev.get(v, 0.0) > -8.99:
                open_ev[v] = [t, s, s, ls.vehicle.getMaxSpeed(v)]
                cnt["starts"] += 1
            if v in open_ev:
                e = open_ev[v]
                e[2] = min(e[2], s)
                if t - e[0] >= 1.0:
                    drops.append(e[1] - e[2])
                    speeds.append(e[1])
                    del open_ev[v]
        prev[v] = a
        if v in WATCH and len(series.setdefault(v, [])) < 900:
            series[v].append((round(t, 1), round(s, 2), round(a, 2), round(ls.vehicle.getMaxSpeed(v), 2), ls.vehicle.getLaneID(v)))
env._sim_step = step
env.reset()
fixed = np.zeros(3, int)
while True:
    *_, tr, inf = env.step(fixed)
    if tr:
        break
ep = inf["ep"]
env.close()
d = np.array(drops) if drops else np.array([0.0])
out = {"name": name, "q": q, "seed": seed, "passed": ep["passed"], "counts": dict(cnt), "by_phase": {str(k): sorted(v.items()) for k, v in ph.items()}, "drop": {"n": len(drops), "median": float(np.median(d)), "p10": float(np.quantile(d, .1)), "p90": float(np.quantile(d, .9)), "max": float(d.max())}, "start_speed_median": float(np.median(speeds)) if speeds else None}
json.dump(out, open(f"t2_{name}.json", "w"))
json.dump(series, open(f"t2_{name}_series.json", "w"))
