"""B DRL training on m32 (V263, V265): PPO on the merge coordinator, CPU, L learners × E envs ≤ 27 workers.

Usage: python -m v5b.fleet.b_train smoke --out DIR
       python -m v5b.fleet.b_train train --out DIR --learner 0 [--updates 500] [--n-envs 8]
       python -m v5b.fleet.b_train eval --out DIR --model FILE [--seeds 20] [--workers 24]
       python -m v5b.fleet.b_train sweep --out DIR [--seeds 20] [--workers 24]
Validation and evaluation here are exploratory: a claim needs its own pre-registered evaluation on fresh seeds (V263).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

SHARE = 0.5
LEVELS = (4090.0, 4300.0, 4600.0)
VAL_SEEDS = list(range(7_419_800, 7_419_900))
N_STEPS_TOTAL = 3072


def make_env(worker: int, run_dir: str, share: float, levels: tuple):
    def _f():
        from v5b.fleet.b_env import MergeEnv
        return MergeEnv(share=share, levels=levels, worker=worker, run_dir=run_dir)
    return _f


def train(out: Path, learner: int, updates: int, n_envs: int, share: float, levels: tuple, stem: str = "") -> Path:
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor
    torch.set_num_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    name = f"L{learner}{stem}"
    workers = [learner * n_envs + i for i in range(n_envs)]
    if max(workers) > 23:
        raise ValueError("worker ids above 23 leave the training seeds")
    env = VecMonitor(SubprocVecEnv([make_env(w, str(out / "rd"), share, levels) for w in workers], start_method="spawn"))
    n_steps = N_STEPS_TOTAL // n_envs
    model = PPO("MlpPolicy", env, n_steps=n_steps, batch_size=768, n_epochs=10, learning_rate=3e-4, gamma=0.99,
                gae_lambda=0.95, ent_coef=0.01, clip_range=0.2, device="cpu", seed=20261102 + learner, verbose=0)
    log = (out / f"{name}_episodes.jsonl").open("a")

    class Cb(BaseCallback):
        def __init__(self):
            super().__init__()
            self.t0 = time.time()

        def _on_step(self) -> bool:
            for i in self.locals["infos"]:
                if "ep" in i:
                    log.write(json.dumps({**i["ep"], "ret": float(i["episode"]["r"]) if "episode" in i else None,
                                          "ts": self.num_timesteps, "wall": round(time.time() - self.t0, 1)}) + "\n")
                    log.flush()
            if self.num_timesteps % (50 * N_STEPS_TOTAL) < n_envs:
                self.model.save(out / f"{name}_ts{self.num_timesteps}")
            return True
    model.learn(total_timesteps=updates * n_steps * n_envs, callback=Cb(), progress_bar=False)
    f = out / f"{name}_final"
    model.save(f)
    (out / f"{name}_config.json").write_text(json.dumps({"learner": learner, "updates": updates, "n_envs": n_envs,
                                                         "n_steps": n_steps, "share": share, "levels": levels,
                                                         "workers": workers, "seed": 20261102 + learner}))
    env.close()
    log.close()
    return f


def _eval_one(a: tuple) -> dict:
    model_path, share, q, seed, run_dir = a
    import torch
    from stable_baselines3 import PPO
    from v5b.fleet import b_env as be
    torch.set_num_threads(1)
    model = PPO.load(model_path, device="cpu") if isinstance(model_path, str) else None
    env = be.MergeEnv(share=share, levels=(q,), run_dir=run_dir, seeds=[seed], report_net=True)
    o, _ = env.reset()
    fixed = np.full(be.K, model_path or 0, int)
    while True:
        act = model.predict(o, deterministic=True)[0] if model is not None else fixed
        o, r, _, tr, inf = env.step(act)
        if tr:
            break
    env.close()
    return {"policy": bool(model_path), **{k: v for k, v in inf["ep"].items()}}


def evaluate(out: Path, model: str, n_seeds: int, workers: int, share: float, levels: tuple) -> dict:
    seeds = VAL_SEEDS[:n_seeds]
    jobs = [(p, share, q, s, str(out / "rd")) for q in levels for s in seeds for p in (model, None)]
    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(workers, mp_context=ctx, max_tasks_per_child=1) as ex:
        rows = list(ex.map(_eval_one, jobs))
    rep = {"model": model, "n": n_seeds}
    for q in levels:
        pol = {r["seed"]: r for r in rows if r["q"] == q and r["policy"]}
        nc = {r["seed"]: r for r in rows if r["q"] == q and not r["policy"]}
        row = {}
        for k in ("E15", "E30", "brake3", "brake45", "N", "out_E30", "out_b3", "arrived"):
            d = np.array([(nc[s][k] - pol[s][k]) for s in seeds])
            base = np.median([nc[s][k] for s in seeds])
            rng = np.random.default_rng(20261102)
            bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
            row[k] = {"nc_per_s": float(base / pol[seeds[0]]["steps"]), "rel": float(np.median(d) / base) if base else None,
                      "rel_ci": [float(x / base) for x in np.percentile(bs, [2.5, 97.5])] if base else None,
                      "better": int((d > 0).sum())}
        row["collisions"] = {"policy": sum(pol[s]["collisions"] for s in seeds), "nc": sum(nc[s]["collisions"] for s in seeds)}
        row["commands"] = float(np.median([pol[s]["commands"] for s in seeds]))
        row["mismatch"] = sum(pol[s]["restore_mismatch"] + pol[s]["lock_mismatch"] for s in seeds)
        rep[f"{q:g}"] = row
    return rep


def smoke(out: Path) -> list:
    """V231 for training: the env echoes its inputs, zero actions repeat exactly and issue no commands, capped vehicles
    reach the cap and are restored, a short PPO run saves a model and logs episodes."""
    import libsumo as ls
    from v5b.fleet import b_env as be
    bad = []
    env = be.MergeEnv(share=SHARE, levels=LEVELS[:1], episode=300.0, warm=120.0, run_dir=str(out / "rd"), seeds=[7419899])
    runs = []
    for act in (np.zeros(be.K, int), np.zeros(be.K, int), np.full(be.K, len(be.OFFSETS_KMH) - 1)):
        o, info = env.reset()
        if info != {"seed": 7419899, "q": LEVELS[0], "share": SHARE}:
            bad.append(f"reset echo {info}")
        track = []
        while True:
            o, r, _, tr, inf = env.step(act)
            if not env.observation_space.contains(o) or not np.isfinite(r):
                bad.append("observation or reward out of bounds")
            for v, h in env.held.items():
                track.append(ls.vehicle.getMaxSpeed(v) - h["cap"])
            if tr:
                break
        runs.append((inf["ep"], track))
    a, b, c = runs[0][0], runs[1][0], runs[2][0]
    if (a["N"], a["E30"], a["brake3"]) != (b["N"], b["E30"], b["brake3"]) or a["commands"] or b["commands"]:
        bad.append(f"zero action not repeatable or issued commands: {a} {b}")
    if not c["commands"] or not runs[2][1] or c["restore_mismatch"] or c["lock_mismatch"]:
        bad.append(f"cap action: {c}")
    if runs[2][1] and min(runs[2][1]) > 1e-6:
        bad.append("no capped vehicle reached its cap")
    if a["N"] == c["N"]:
        bad.append("cap action changed nothing")
    env.close()
    f = train(out / "ppo", 0, 2, 2, SHARE, LEVELS, stem="_smoke")
    if not f.with_suffix(".zip").exists():
        bad.append("no model file")
    return bad


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=("smoke", "train", "eval", "sweep"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--learner", type=int, default=0)
    ap.add_argument("--updates", type=int, default=500)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--model")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--offsets", default="1,2,3,4,5")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.phase == "smoke":
        out.mkdir(parents=True, exist_ok=True)
        bad = smoke(out)
        print("smoke:", "ok" if not bad else bad, flush=True)
        return 1 if bad else 0
    if a.phase == "train":
        print("model:", train(out, a.learner, a.updates, a.n_envs, SHARE, LEVELS), flush=True)
        return 0
    if a.phase == "sweep":
        from v5b.fleet import b_env as be
        out.mkdir(parents=True, exist_ok=True)
        for i in map(int, a.offsets.split(",")):
            rep = evaluate(out, i, a.seeds, a.workers, SHARE, LEVELS)
            (out / f"eval_const{be.OFFSETS_KMH[i]:g}.json").write_text(json.dumps(rep, indent=1))
        return 0
    rep = evaluate(out, a.model, a.seeds, a.workers, SHARE, LEVELS)
    (out / f"eval_{Path(a.model).stem}.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: {m: (v[m]["rel"], v[m]["better"]) for m in ("E15", "E30", "brake3", "N")} for k, v in rep.items()
                      if isinstance(v, dict)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
