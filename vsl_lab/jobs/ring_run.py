"""RING22 job: one ring episode with a classical AV controller (plant checks, baseline tuning).

python -m vsl_lab.jobs.ring_run --L 260 --seed 7130000 --ctrl fs --U 4.5 --tag smoke
Metrics over [t_warm, t_end): mean speed of all vehicles (closed ring: throughput = N/L * mean speed),
Stern's sigma (std of all speed samples), share of time the slowest vehicle is < 1 m/s (stop-and-go),
mean across-vehicle speed std, AV mean speed, minimum bumper gap.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import RUNS_ROOT
from vsl_lab.plants import ring as R


def run(L, seed, ctrl, U, noise, t_warm, t_end, tag, out_root: Path, vcatch: float = 1.0, window: float = 38.0) -> dict:
    pi_tag = f"vc{vcatch:g}w{window:g}" if ctrl == "pi" else ""
    run_id = f"ring_L{int(L)}_s{seed}_{ctrl}{'' if U is None else f'U{U:g}'}{pi_tag}_{noise}_pid{os.getpid()}"
    run_dir = out_root / tag / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    t0w = time.time()
    plant = R.RingPlant(L, seed, noise=noise, run_dir=run_dir)
    plant.start()
    fs = R.FollowerStopper(U) if ctrl == "fs" else None
    pi = R.PISaturation(window_s=window, v_catch=vcatch) if ctrl == "pi" else None
    speeds, mins, stds, av_v, gaps = [], [], [], [], []
    while plant.t < t_end - 1e-9:
        st = plant.state()
        acc = None
        if plant.t >= t_warm - 1e-9 and ctrl != "nc":
            v, vl, gap = st[R.AV_ID]
            vc = fs.v_cmd(v, vl, gap) if fs else pi.v_cmd(v, vl, gap)
            acc = float(np.clip((vc - v) / R.DT, -3.0, 1.5))
        plant.step_all(acc, st)
        if plant.t >= t_warm - 1e-9:
            sp = np.array([st[v][0] for v in plant.ids])
            speeds.append(sp.mean())
            stds.append(sp.std())
            mins.append(sp.min())
            av_v.append(st[R.AV_ID][0])
            gaps.append(min(st[v][2] for v in plant.ids))
    health = plant.close()
    allv = np.array(speeds)
    out = {
        "job": "ring_run", "run_id": run_id, "L": plant.L, "L_target": L, "seed": seed, "ctrl": ctrl, "U": U,
        "noise": noise, "vcatch": vcatch if ctrl == "pi" else None, "window": window if ctrl == "pi" else None,
        "mean_speed": round(float(allv.mean()), 4),
        "throughput_vph": round(float(R.N_VEH / plant.L * allv.mean() * 3600.0), 1),
        "mean_across_std": round(float(np.mean(stds)), 4),
        "stop_share": round(float(np.mean(np.array(mins) < 1.0)), 4),
        "av_mean_speed": round(float(np.mean(av_v)), 4), "min_gap": round(float(np.min(gaps)), 3),
        "health": health["status"], "health_issues": health["issues"], "safe_stops": health["safe_stops"],
        "wall_s": round(time.time() - t0w, 2),
    }
    out["hash"] = hashlib.sha1(json.dumps({k: out[k] for k in ("mean_speed", "mean_across_std", "stop_share",
                                                               "min_gap")}).encode()).hexdigest()[:16]
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=float, default=260.0)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--ctrl", default="nc", choices=["nc", "fs", "pi"])
    ap.add_argument("--U", type=float, default=None)
    ap.add_argument("--noise", default="sqrt_dt", choices=["sqrt_dt", "per_step"])
    ap.add_argument("--t-warm", type=float, default=75.0)
    ap.add_argument("--t-end", type=float, default=375.0)
    ap.add_argument("--vcatch", type=float, default=1.0)
    ap.add_argument("--window", type=float, default=38.0)
    ap.add_argument("--tag", default="smoke")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t3"))
    a = ap.parse_args(argv)
    out = run(a.L, a.seed, a.ctrl, a.U, a.noise, a.t_warm, a.t_end, a.tag, Path(a.out_root), a.vcatch, a.window)
    print(json.dumps({k: out[k] for k in ("run_id", "mean_speed", "throughput_vph", "mean_across_std", "stop_share",
                                            "av_mean_speed", "min_gap", "health", "safe_stops", "hash", "wall_s")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
