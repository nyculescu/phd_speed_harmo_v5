"""Per-step ALKS deceleration against the 1-Hz metric, with and without the smooth rule, one seed, no controller."""
import json, sys, collections as C
import numpy as np, libsumo as ls
from v5b.fleet import b_env as be, plant_sweep as ps
name, cfg = sys.argv[1], json.loads(sys.argv[2])
rd = "/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp/trace_" + name
env = be.make(alks_asl=0.5, ref_delay=True, share=0.5, levels=(5300.0,), run_dir=rd, seeds=[7419640], report_net=True, plant=ps.to_plant(cfg), zones=True, decision=10.0, w_change=0.1)
orig = env._sim_step
cnt = C.Counter(); phase = C.Counter(); edges = C.Counter(); ev = []; prev = {}; run = C.Counter()
def step():
    orig()
    t = env.sim.t
    if t < env.warm:
        return
    on_sec = abs(t - round(t)) < 1e-6
    for v in ls.vehicle.getIDList():
        a = ls.vehicle.getAcceleration(v)
        cl = "alks" if v in env.alks_all else env.dem.by_id[v].cls
        for th in (3.0, 4.5, 7.0, 8.99):
            if a <= -th:
                cnt[f"{cl}_step_{th}"] += 1
                if on_sec:
                    cnt[f"{cl}_sec_{th}"] += 1
        if a <= -8.99 and prev.get(v, 0.0) > -8.99:
            cnt[f"{cl}_starts"] += 1
            if cl == "alks":
                phase[round(t % 1, 1)] += 1
                edges[ls.vehicle.getLaneID(v)] += 1
                s, ms = ls.vehicle.getSpeed(v), ls.vehicle.getMaxSpeed(v)
                capped = ms < 55.0
                cnt["starts_capped"] += capped
                cnt["starts_speed_over_cap"] += (s + 0.9 > ms)
                lead = ls.vehicle.getLeader(v, 200.0)
                g = lead[1] if lead and lead[0] else None
                cnt["starts_close_leader_2s"] += (g is not None and g / max(s, 1.0) < 2.0)
                if len(ev) < 12:
                    ev.append((round(t, 1), v, ls.vehicle.getLaneID(v), round(s, 2), round(ms, 2), None if g is None else round(g, 1), None if not (lead and lead[0]) else round(ls.vehicle.getSpeed(lead[0]), 2)))
        prev[v] = a
    cnt["steps"] += 1
env._sim_step = step
env.reset()
fixed = np.zeros(3, int)
while True:
    *_, tr, inf = env.step(fixed)
    if tr:
        break
env.close()
print(json.dumps({"name": name, "counts": dict(cnt), "phase": sorted(phase.items()), "lanes": edges.most_common(8), "examples": ev}))
