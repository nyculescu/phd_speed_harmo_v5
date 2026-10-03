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
    meter = ctrl.startswith("meter") or ctrl.startswith("evsched")
    if ctrl.startswith(("vsl:", "mtfcb:")):
        kw.setdefault("actuator", "posted_vsl")
    if ctrl.startswith(("madapt:", "msfix:")):
        kw.setdefault("actuator", "meter_sched")
    mpcf = None
    if ctrl == "mpcf" or ctrl.startswith("mpcf:"):   # Addendum D/D2: fitted-model MPC over the 4 lookup settings
        kw.setdefault("actuator", "meter_sched")
        kw.setdefault("meter_grid", ["40:6", "40:8", "20:12", "5:8"])
        kw.setdefault("allow_off", False)
        kw.setdefault("decision_s", 30.0)
    if kw.get("actuator", "av_caps") != "av_caps":
        kw.setdefault("decision_s", 10.0 if kw["actuator"] == "posted_vsl" else 30.0)
    env = BN4Env(meter=meter, **kw)
    if ctrl.startswith("meter") and ":" in ctrl:
        _, kf, nc = ctrl.split(":")
        env_meter_params = (float(kf), float(nc))
    else:
        env_meter_params = None
    model, recurrent = None, False
    if kw.get("actuator") == "meter_sched" and (ctrl == "mpcf" or ctrl.startswith("mpcf:")):
        from vsl_lab.jobs.mpcf import MPCF, MODEL as _MP
        mpcf = MPCF(Path(ctrl.split(":", 1)[1]) if ":" in ctrl else _MP)
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
    evs = None
    if ctrl.startswith("evsched:"):
        # T1-M H step (docs/lab/t1_meter_gscan_protocol.md, Addendum A): non-learning event-detecting scheduler of the
        # feedback meter. Every 30 s: slowdown if the 60-s mean speed on bottleneck edge 5 < v_slow; blockage if a vehicle
        # on edge 4 lane 1 has been halted >= t_block s while lane 0 moves (> 2 m/s); surge if the 120-s departure rate
        # > f_surge x the rate measured over the first 300 s of control. State -> (K_F, n_crit) from the frozen lookup
        # (docs/lab/t1_meter_lookup.json) for the inflow nearest to the measured base rate; normal = lookup 'none'.
        import json as _json
        from vsl_lab.config import REPO_ROOT as _RR
        _, v_sl, t_bl, f_su = ctrl.split(":")
        _lk = _json.loads((_RR / "docs/lab/t1_meter_lookup.json").read_text())["lookup"]
        evs = {"v_slow": float(v_sl), "t_block": float(t_bl), "f_surge": float(f_su), "lk": _lk, "v5": [], "halt": {},
               "dep": [], "base": None, "t_last": None, "state": "none", "states": {}}
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
    if evs is not None:   # start in the lookup's 'none' setting for the nominal inflow
        _qk = min(evs["lk"], key=lambda k: abs(float(k) - inflow))
        env.meter.K_F, env.meter.n_crit = (float(x) for x in evs["lk"][_qk]["per_kind"]["none"].split(":")[1:3])
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
        elif mpcf is not None:
            act = mpcf.choose(env, obs)
        elif evs is not None:
            t_now = env.sim.t
            evs["v5"].append(_ls.lane.getLastStepMeanSpeed("5_0") if _ls.lane.getLastStepVehicleNumber("5_0") else 23.0)
            evs["v5"] = evs["v5"][-60:]
            for vid in _ls.lane.getLastStepVehicleIDs("4_1"):
                evs["halt"][vid] = evs["halt"].get(vid, 0.0) + 1.0 if _ls.vehicle.getSpeed(vid) < 0.1 else 0.0
            evs["halt"] = {v: h for v, h in evs["halt"].items() if v in set(_ls.lane.getLastStepVehicleIDs("4_1"))}
            evs["dep"].append((t_now, env.sim.departed))
            if evs["base"] is None and t_now - env._t_ctrl0 >= 300.0:
                d0 = [x for x in evs["dep"] if x[0] >= env._t_ctrl0]
                evs["base"] = (d0[-1][1] - d0[0][1]) * 3600.0 / max(d0[-1][0] - d0[0][0], 1.0)
            if evs["t_last"] is None or t_now - evs["t_last"] >= 30.0 - 1e-9:
                evs["t_last"] = t_now
                v_mean = float(np.mean(evs["v5"])) if evs["v5"] else 23.0
                lane0 = _ls.lane.getLastStepMeanSpeed("4_0") if _ls.lane.getLastStepVehicleNumber("4_0") else 23.0
                recent = [x for x in evs["dep"] if x[0] >= t_now - 120.0]
                rate = (recent[-1][1] - recent[0][1]) * 3600.0 / max(recent[-1][0] - recent[0][0], 1.0) if len(recent) > 1 else 0.0
                if evs["halt"] and max(evs["halt"].values()) >= evs["t_block"] and lane0 > 2.0:
                    st = "block"
                elif v_mean < evs["v_slow"]:
                    st = "slow"
                elif evs["base"] is not None and rate > evs["f_surge"] * evs["base"]:
                    st = "surge"
                else:
                    st = "none"
                evs["state"] = st
                evs["states"][st] = evs["states"].get(st, 0) + 1
                base = evs["base"] if evs["base"] is not None else inflow
                qk = min(evs["lk"], key=lambda k: abs(float(k) - base))
                kf_, nc_ = (float(x) for x in evs["lk"][qk]["per_kind"][st].split(":")[1:3])
                env.meter.K_F, env.meter.n_crit = kf_, nc_
            act = const
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
    if evs is not None:
        m["evsched_states"] = evs["states"]
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
