"""Round 4: evaluate a trained policy exactly like the classical controllers (door-to-door incl. drain, SUMO tripinfo
stops) on given main peaks x seeds. One process per (policy, peak, seed); JSON per episode.

python -m vsl_lab.jobs.r4_eval_rl --model final_model.zip --main-peak 3900 --seed 7120300 --out-root DIR --tag drl0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--main-peak", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args(argv)
    try:
        from stable_baselines3 import PPO
        from vsl_lab.envs.mrg3_env import MRG3Env
        import torch
        torch.set_num_threads(1)
        env = MRG3Env(mode="direct", plant="v3", driver="H5", geom="lanedrop", step=0.2, stop_weight=40.0,
                      main_peak=(a.main_peak, a.main_peak), ramp_peak=(0.0, 0.0), eval_seeds=[a.seed], eval_p_nc=0.3,
                      drain_after=True, trip_stops=True, tag=f"r4eval_{a.tag}")
        model = PPO.load(a.model, device="cpu")
        obs, _ = env.reset()
        done, info = False, {}
        while not done:
            act, _ = model.predict(obs, deterministic=True)
            obs, r, done, _, info = env.step(act)
        m = info["episode_metrics"]
        out = {"ctrl": f"rl:{a.tag}", "seed": a.seed, "main_peak": a.main_peak, "health": info.get("health"),
               "health_codes": info.get("health_codes")} | m
        d = Path(a.out_root) / a.tag
        d.mkdir(parents=True, exist_ok=True)
        (d / f"m{int(a.main_peak)}_s{a.seed}_pid{os.getpid()}.json").write_text(json.dumps(out, indent=1, default=str))
        env.close()
        print(json.dumps({k: out.get(k) for k in ("ctrl", "seed", "main_peak", "mean_time_in_system_s", "stops_per_veh", "health")}))
        return 0
    except Exception as exc:   # never fail silently
        import traceback
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-1500:]}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
