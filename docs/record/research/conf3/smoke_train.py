"""Smoke in training mode: the plant flags act and the reward varies, with a fixed slowdown and with the random draw. usage: smoke_train.py env.json tmp_dir. Exit 1 on failure."""
import json
import sys

import libsumo as ls
import numpy as np

from common import PLANT
from v5b.fleet import b_env as be, c_train as ct
from v5b.fleet import plant_sweep as ps


def probe(env_kw: dict, rd: str, seed: int, lane: str, until: float) -> dict:
    """Random levels until `until`; tau read every second, the lane's limit every step."""
    env = be.make(**{**ct.ENV, **env_kw, "share": 0.5, "levels": (5300.0,), "seeds": [seed], "run_dir": rd})
    o, _ = env.reset()
    assert env.ref is env.plant_ref and {float(k): tuple(v) for k, v in env_kw["plant"]["ref"].items()} == env.ref, env.ref
    res = {"limit": [], "tau_over": 0, "tau_rises": 0, "targets": 0, "capped": 0, "reward": []}
    last = {}
    step0, sec0 = env._sim_step, env._second

    def step():
        step0()
        res["limit"].append(ls.lane.getMaxSpeed(lane))

    def sec():
        r = sec0()
        for v in env.alks_all & set(ls.vehicle.getIDList()):
            t = ls.vehicle.getTau(v)
            if v in last and t > last[v] + 1e-6:
                res["tau_rises"] += 1
                res["tau_over"] += t > last[v] + 0.2 + 1e-6
            last[v] = t
            res["capped"] += ls.vehicle.getMaxSpeed(v) < be.FREE_MAX_SPEED - 0.01
        res["targets"] += sum(x < be.FREE_MAX_SPEED for x in env.smooth_target.values())
        return r

    env._sim_step, env._second = step, sec
    rng = np.random.default_rng(1)
    while env.sim.t < until:
        o, r, *_ = env.step({v: int(rng.integers(0, 4)) for v in o[0]})
        res["reward"] += list(r.values())
    env.close()
    d = np.abs(np.diff(res["limit"]))
    return {"reward_sd": round(float(np.std(res["reward"])), 3), "targets": res["targets"], "capped": res["capped"], "tau_rises": res["tau_rises"], "tau_over": res["tau_over"],
            "largest_limit_step": round(float(d[d < 5].max()), 3) if len(d) else 0.0, "lowest_limit": round(min(res["limit"]), 2)}


if __name__ == "__main__":
    kw = json.load(open(sys.argv[1]))
    assert kw["plant"] == {**ps.to_plant(PLANT), "ref": kw["plant"]["ref"]}
    kw = {k: v for k, v in kw.items() if k not in ("seed0", "seeds_per_worker")}
    a = probe({**kw, "perturb": {"kind": "slowdown", "edge": "4", "limit_kmh": 25, "dur": 120.0, "times": [400.0], "taper": 20.0}}, sys.argv[2], 7_440_065, "4_0", 480.0)
    b = probe(kw, sys.argv[2], 7_440_071, "3_0", 560.0)     # this seed's random draw is a slowdown on edge 3, at about 478 s
    print("fixed slowdown", a, flush=True)
    print("random draw", b, flush=True)
    ok = all(x["reward_sd"] > 0.01 and x["targets"] > 0 and x["capped"] > 0 and x["tau_rises"] > 0 and x["tau_over"] == 0 for x in (a, b))
    ok = ok and a["largest_limit_step"] < 0.11 and a["lowest_limit"] < 7.0 and b["largest_limit_step"] < 0.2 and b["lowest_limit"] < 16.7
    print("smoke ok" if ok else "SMOKE FAILED", flush=True)
    sys.exit(0 if ok else 1)
