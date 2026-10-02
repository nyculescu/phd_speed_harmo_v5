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
from vsl_lab.controllers.mtfc import MTFC
from vsl_lab.envs.bn4_env import V_MIN, SPEED, BN4Env


def run(ctrl: str, inflow: float, seed: int, tag: str, out_root: Path, control_s: float = 900.0,
        warmup_s: float = 40.0, env_kwargs: dict | None = None) -> dict:
    kw = dict(inflow=(inflow, inflow), eval_seeds=[seed], warmup_s=warmup_s, control_s=control_s,
              drain_after=True, tag=f"eval_{tag}", reward="out")
    kw.update(env_kwargs or {})
    meter = ctrl.startswith("meter")
    if ctrl.startswith(("vsl:", "mtfcb:")):
        kw.setdefault("actuator", "posted_vsl")
    if ctrl.startswith(("madapt:", "msfix:")):
        kw.setdefault("actuator", "meter_sched")
    if kw.get("actuator", "av_caps") != "av_caps":
        kw.setdefault("decision_s", 10.0 if kw["actuator"] == "posted_vsl" else 30.0)
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
    n_act = env.action_space.shape[0] if env.action_space.shape else 1   # Discrete (meter_sched) has shape ()
    if ctrl == "nc" or meter:
        const = np.ones(n_act, dtype=np.float32)            # cap = 23 m/s = no cap
    elif ctrl.startswith("cap:"):
        c = float(ctrl.split(":")[1])
        const = np.full(n_act, 2.0 * (c - V_MIN) / (SPEED - V_MIN) - 1.0, dtype=np.float32)
    else:
        const = None
    avfb = None
    if ctrl.startswith("avfb:"):
        # Lagrangian analogue of Vinitsky's feedback meter, on the SAME AV actuator as the DRL policy:
        # every T = 30 s, cap <- clip(cap + K (n_crit - n_hat), V_MIN, 23), n_hat = vehicles on segment 4;
        # one uniform cap for all controlled lane-pieces (the env applies its rate limits).
        _, k_v, n_c = ctrl.split(":")
        avfb = {"K": float(k_v), "n_crit": float(n_c), "cap": SPEED, "t_last": None}
    def vsl_action(b):
        b = np.asarray(b, dtype=np.float64)
        if env.action_map == "nocap_center":
            return np.where(b >= 1.0 - 1e-9, 0.0, (b - 1.0) / 0.8).astype(np.float32)
        return ((b - 0.6) / 0.4).astype(np.float32)
    vsl_const, mtfcb, madapt, msfix = None, None, None, None
    if ctrl.startswith("vsl:"):
        vsl_const = [float(x) for x in ctrl.split(":")[1:3]]
    elif ctrl.startswith("mtfcb:"):
        rho, kp, ki, ki2 = (float(x) for x in ctrl.split(":")[1:5])
        mtfcb = {"c": MTFC(rho_set=rho, kp=kp, ki=ki, ki2=ki2, q_min=100.0, q_max=2400.0), "b": [1.0, 1.0],
                 "t_last": None}
    elif ctrl.startswith("madapt:"):
        th, k = ctrl.split(":")[1:3]
        madapt = {"theta": float(th), "k": int(k), "on": False, "dep": []}
    elif ctrl.startswith("msfix:"):
        msfix = int(ctrl.split(":")[1])
    t0 = time.time()
    obs, _ = env.reset()
    if env_meter_params is not None:
        env.meter.K_F, env.meter.n_crit = env_meter_params
    state, start = None, np.ones((1,), dtype=bool)
    done, info = False, {}
    import libsumo as _ls
    while not done:
        if vsl_const is not None:
            act = vsl_action(vsl_const)
        elif mtfcb is not None:
            t_now = env.sim.t
            if mtfcb["t_last"] is None or t_now - mtfcb["t_last"] >= 20.0 - 1e-9:
                rho_out = _ls.edge.getLastStepVehicleNumber("4") / (0.24 * 2.0)
                q_c = sum(_ls.inductionloop.getLastIntervalVehicleNumber(f"merge_3_{i}") for i in range(4)) * 180.0 / 4.0
                b_app, b_acc = mtfcb["c"].step(rho_out, q_c)
                mtfcb["b"] = [b_app, b_acc]
                mtfcb["t_last"] = t_now
            act = vsl_action(mtfcb["b"])
        elif madapt is not None:
            madapt["dep"].append((env.sim.t, env.sim.departed))
            while madapt["dep"] and madapt["dep"][0][0] < env.sim.t - 60.0 - 1e-9:
                madapt["dep"].pop(0)
            q_in = (madapt["dep"][-1][1] - madapt["dep"][0][1]) * 3600.0 / max(madapt["dep"][-1][0] - madapt["dep"][0][0], 1.0)
            if not madapt["on"] and q_in >= madapt["theta"]:
                madapt["on"] = True
            elif madapt["on"] and q_in < madapt["theta"] - 100.0:
                madapt["on"] = False
            act = madapt["k"] if madapt["on"] else 0
        elif msfix is not None:
            act = msfix
        elif avfb is not None:
            t_now = env.sim.t
            if avfb["t_last"] is None or t_now - avfb["t_last"] >= 30.0 - 1e-9:
                n_hat = _ls.edge.getLastStepVehicleNumber("4")
                avfb["cap"] = float(np.clip(avfb["cap"] + avfb["K"] * (avfb["n_crit"] - n_hat), V_MIN, SPEED))
                avfb["t_last"] = t_now
            act = np.full(n_act, 2.0 * (avfb["cap"] - V_MIN) / (SPEED - V_MIN) - 1.0, dtype=np.float32)
        elif model is None:
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
    try:
        return _main(argv)
    except Exception as exc:   # never fail silently: the scheduler reads the last JSON line of stdout
        import traceback
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-1500:]}))
        return 2


def _main(argv=None) -> int:
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
