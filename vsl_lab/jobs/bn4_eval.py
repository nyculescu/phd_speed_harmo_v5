"""BN4 evaluation job: one episode of one controller through the SAME env code path for every controller.

Controllers: nc | cap:<m/s> | meter[:K_F:n_crit] | rl:<model.zip>[:algo]
Episode: 40 s uncontrolled warm-up (Vinitsky 2018), 900 s control, then an uncontrolled drain until empty (all vehicles counted).
Primary metric: mean time in system per vehicle, incl. origin/insertion queue (door-to-door).
Co-headline: outflow over the control window; also served by the end of control.

python -m vsl_lab.jobs.bn4_eval --ctrl cap:11 --inflow 2000 --seed 7110100 --tag r2_tune
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import RUNS_ROOT
from vsl_lab.envs.bn4_env import V_MIN, SPEED, BN4Env


def run(ctrl: str, inflow: float, seed: int, tag: str, out_root: Path, control_s: float = 900.0,
        warmup_s: float = 40.0, env_kwargs: dict | None = None) -> dict:
    kw = dict(inflow=(inflow, inflow), eval_seeds=[seed], warmup_s=warmup_s, control_s=control_s,
              drain_after=True, tag=f"eval_{tag}", reward="out")
    kw.update(env_kwargs or {})
    meter = ctrl.startswith("meter")
    env = BN4Env(meter=meter, **kw)
    if meter and ":" in ctrl:
        _, kf, nc = ctrl.split(":")
        env_meter_params = (float(kf), float(nc))
    else:
        env_meter_params = None
    model, recurrent = None, False
    if ctrl.startswith("rl:"):
        parts = ctrl.split(":")
        path, algo = parts[1], (parts[2] if len(parts) > 2 else "ppo")
        if algo == "recurrentppo":
            from sb3_contrib import RecurrentPPO as A
            recurrent = True
        elif algo == "trpo":
            from sb3_contrib import TRPO as A
        else:
            from stable_baselines3 import PPO as A
        model = A.load(path, device="cpu")
    n_act = env.action_space.shape[0]
    if ctrl == "nc" or meter:
        const = np.ones(n_act, dtype=np.float32)            # cap = 23 m/s = no cap
    elif ctrl.startswith("cap:"):
        c = float(ctrl.split(":")[1])
        const = np.full(n_act, 2.0 * (c - V_MIN) / (SPEED - V_MIN) - 1.0, dtype=np.float32)
    else:
        const = None
    t0 = time.time()
    obs, _ = env.reset()
    if env_meter_params is not None:
        env.meter.K_F, env.meter.n_crit = env_meter_params
    state, start = None, np.ones((1,), dtype=bool)
    done, info = False, {}
    while not done:
        if model is None:
            act = const
        elif recurrent:
            act, state = model.predict(obs, state=state, episode_start=start, deterministic=True)
            start = np.zeros((1,), dtype=bool)
        else:
            act, _ = model.predict(obs, deterministic=True)
        obs, r, done, _, info = env.step(act)
    m = info["episode_metrics"]
    out = {"job": "bn4_eval", "ctrl": ctrl, "inflow": inflow, "seed": seed, "health": info.get("health"),
           "health_codes": info.get("health_codes"), "wall_s": round(time.time() - t0, 2)} | m
    run_dir = out_root / tag
    run_dir.mkdir(parents=True, exist_ok=True)
    safe = ctrl.replace(":", "_").replace("/", "_")[-60:]
    (run_dir / f"{safe}_q{int(inflow)}_s{seed}_pid{os.getpid()}.json").write_text(json.dumps(out, indent=1))
    env.close()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctrl", required=True)
    ap.add_argument("--inflow", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--tag", default="eval")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t1" / "eval"))
    ap.add_argument("--env-kwargs", default="{}")
    a = ap.parse_args(argv)
    out = run(a.ctrl, a.inflow, a.seed, a.tag, Path(a.out_root), env_kwargs=json.loads(a.env_kwargs))
    print(json.dumps({k: out.get(k) for k in ("ctrl", "inflow", "seed", "mean_time_in_system_s", "outflow_ctrl_vph",
                                               "served_ctrl_end", "drained", "health", "wall_s")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
