"""Inspect what a trained BN4 policy does: per-slot AV caps over time vs the bottleneck state.

python -m vsl_lab.eval.inspect_bn4_policy --model PATH --algo ppo --env-kwargs '{"action_map":"nocap_center"}' \
       --inflows 1600 2000 2400 --seeds 7110300 7110301 --out docs/lab/f1_policy_inspection.json
Reports, per lane-piece slot: share of decisions with a cap (< 22 m/s), mean cap when capped, and the
correlation of the slot cap with the vehicle count on segment 4 (the bottleneck). Validation seeds only.
"""
from __future__ import annotations

import argparse
import json

import libsumo as ls
import numpy as np

from vsl_lab.envs.bn4_env import BN4Env


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--algo", default="ppo")
    ap.add_argument("--env-kwargs", default="{}")
    ap.add_argument("--inflows", type=float, nargs="+", default=[1600.0, 2000.0, 2400.0])
    ap.add_argument("--seeds", type=int, nargs="+", default=[7110300, 7110301])
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.algo == "trpo":
        from sb3_contrib import TRPO as A
    else:
        from stable_baselines3 import PPO as A
    model = A.load(a.model, device="cpu")
    kw = json.loads(a.env_kwargs)
    caps, n4s = [], []
    slots = None
    for q in a.inflows:
        for s in a.seeds:
            env = BN4Env(inflow=(q, q), eval_seeds=[s], warmup_s=40, control_s=900, tag="inspect", **kw)
            slots = env.act_slots
            obs, _ = env.reset()
            done = False
            while not done:
                act, _ = model.predict(obs, deterministic=True)
                obs, r, done, _, info = env.step(act)
                if not done:
                    caps.append(env.slot_caps.copy())
                    n4s.append(ls.edge.getLastStepVehicleNumber("4"))
            env.close()
    C = np.array(caps)
    n4 = np.array(n4s, dtype=float)
    out = {"model": a.model, "n_decisions": int(len(C)), "slots": []}
    for j, sl in enumerate(slots):
        c = C[:, j]
        capped = c < 22.0
        corr = float(np.corrcoef(c, n4)[0, 1]) if np.std(c) > 1e-9 and np.std(n4) > 1e-9 else None
        out["slots"].append({"edge": sl[0], "lane": sl[1], "piece": sl[2], "share_capped": round(float(capped.mean()), 3),
                             "mean_cap_when_capped": round(float(c[capped].mean()), 2) if capped.any() else None,
                             "corr_cap_vs_n_seg4": None if corr is None else round(corr, 3)})
    out["share_any_cap"] = round(float((C < 22.0).any(axis=1).mean()), 3)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"share_any_cap": out["share_any_cap"],
                      "most_capped": sorted(out["slots"], key=lambda x: -x["share_capped"])[:5]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
