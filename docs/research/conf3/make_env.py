"""Training config from the frozen plant and no-control rows; asserts everything the protocol pins. usage: make_env.py rows.jsonl env.json [rows per level]"""
import json
import sys

import numpy as np

from common import ENVS, FIRST_WORKER, LEARNERS, LEVELS, PER_WORKER, PLANT, SEED0, load, val
from v5b.fleet import plant_sweep as ps


def refs(T: dict, n: int = 20) -> dict:
    """V334, V358: median per level of no-control braking, TTC and vehicles in system per second."""
    out = {}
    for q in LEVELS:
        A = T[("S|nc", q)]
        assert len(A) == n, (q, len(A))
        out[str(q)] = [round(float(np.median([val(x, k) / x["steps"] for x in A.values()])), d) for k, d in (("brake3", 3), ("E30", 3), ("N", 1))]
    return out


def make(T: dict, n: int = 20) -> dict:
    return {"hold": 10.0, "w_flow": 0.4, "w_safety": 10.0, "seed0": SEED0, "seeds_per_worker": PER_WORKER, "perturb": {"kind": "random"}, "plant": {**ps.to_plant(PLANT), "ref": refs(T, n)}}


def check(env: dict) -> None:
    p = dict(env["plant"])
    ref = p.pop("ref")
    assert p == ps.to_plant(PLANT), p
    assert sorted(float(k) for k in ref) == sorted(LEVELS)
    assert all(np.isfinite(x) and x >= 0 for v in ref.values() for x in v) and all(v[2] > 0 for v in ref.values()), ref
    assert p["geom"] == "r2m3" and p["ease"] and p["smooth_s"] == 8.0 and p["ease_max"] == 4.4 and p["tau_rise"] == 0.2 and p["taper_fast"] and p["fix_x"]
    assert env["perturb"] == {"kind": "random"} and env["hold"] == 10.0 and env["w_flow"] == 0.4 and env["w_safety"] == 10.0
    workers = [FIRST_WORKER + L * ENVS + i for L in range(LEARNERS) for i in range(ENVS)]
    first, last = env["seed0"] + min(workers) * env["seeds_per_worker"], env["seed0"] + (max(workers) + 1) * env["seeds_per_worker"] - 1
    assert first == 7_456_000 and last <= 7_463_999, (first, last)


if __name__ == "__main__":
    env = make(load(sys.argv[1]), int(sys.argv[3]) if len(sys.argv) > 3 else 20)
    check(env)
    json.dump(env, open(sys.argv[2], "w"), indent=1)
    print("env ok", env["plant"]["ref"], flush=True)
