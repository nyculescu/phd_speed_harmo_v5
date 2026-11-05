"""Smoke in training mode: the plant flags act and the reward varies. usage: smoke_train.py env.json tmp_dir. Exit 1 on failure."""
import json
import sys

import libsumo as ls
import numpy as np

from v5b.fleet import b_env as be, c_train as ct

if __name__ == "__main__":
    env_kw = json.load(open(sys.argv[1]))
    env_kw = {k: v for k, v in env_kw.items() if k not in ("seed0", "seeds_per_worker")}
    env_kw["perturb"] = {"kind": "slowdown", "edge": "4", "limit_kmh": 25, "dur": 120.0, "times": [400.0], "taper": 20.0}
    env = be.make(**{**ct.ENV, **env_kw, "share": 0.5, "levels": (5300.0,), "seeds": [7_440_065], "run_dir": sys.argv[2]})
    o, info = env.reset()
    assert env.ref is env.plant_ref and set(env.ref) == {4090.0, 4600.0, 5300.0}, env.ref
    rng = np.random.default_rng(1)
    limit, steps, rises, on, rew, targets = [], [], 0, 0, [], 0
    last_tau = {}
    orig = env._sim_step

    def step():
        orig()
        limit.append(ls.lane.getMaxSpeed("4_0"))

    env._sim_step = step
    while env.sim.t < 480.0:
        ids = o[0]
        o, r, term, trunc, inf = env.step({v: int(rng.integers(0, 4)) for v in ids})
        rew += list(r.values())
        targets += sum(x < be.FREE_MAX_SPEED for x in env.smooth_target.values())
        for v in o[0]:
            t = ls.vehicle.getTau(v)
            if v in last_tau and t > last_tau[v] + 0.2 + 1e-6:
                rises += 1
            last_tau[v] = t
    env.close()
    d = np.abs(np.diff(limit))
    step_max = float(d[d < 5].max()) if len(d) else 0.0
    res = {"reward sd": round(float(np.std(rew)), 3), "smooth targets active": targets, "tau rises over 0.2 s": rises, "largest limit step in taper": round(step_max, 3), "lowest limit": round(min(limit), 2)}
    print(res, flush=True)
    ok = res["reward sd"] > 0.01 and targets > 0 and rises == 0 and step_max < 0.11 and res["lowest limit"] < 7.0
    print("smoke ok" if ok else "SMOKE FAILED", flush=True)
    sys.exit(0 if ok else 1)
