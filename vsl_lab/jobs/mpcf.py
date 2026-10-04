"""MPC-F: fitted-model MPC baseline for BN4 meter scheduling (docs/lab/t1_meter_gscan_protocol.md, Addendum D/D2).

Data (gen): BN4 episodes at inflow ~ U(1400, 1800) with one perturbation kind, on separate seeds 7,110,200-7,110,299;
the meter setting (one of the 4 lookup settings) is held for 10 decisions (300 s) at a time, chosen at random, with a random
initial offset. Each hold gives a sample (S-VIN observation at hold start, measured 120-s inflow, setting index, veh-s in
the system over the next 300 s). The model is never given the true model or the perturbation kind.
Model (fit): MLP (inputs standardised: observation + inflow + setting one-hot; 2 x 64 tanh), MSE, 80/20 split, early stop.
Controller (MPCF, used by jobs/bn4_eval.py `mpcf:<model.pt>`): every 30 s predict the 300-s cost of each setting from
the current state and pick the minimum (receding horizon, constant input over the prediction horizon).

python -m vsl_lab.jobs.mpcf genall --gate-ok        # data generation (scheduler)
python -m vsl_lab.jobs.mpcf fit                      # fit and freeze docs/lab/t1_mpcf_model.pt (+ fit report)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT

GRID = ["40:6", "40:8", "20:12", "5:8"]
KINDS = {"none": None, "slow": {"kind": "slow", "dur": 300, "v_mps": 5.0}, "block": {"kind": "block", "dur": 180},
         "surge": {"kind": "surge", "dur": 300, "factor": 1.3}}
SEEDS = list(range(7110200, 7110300))
HOLD = 10
MODEL = REPO_ROOT / "docs" / "lab" / "t1_mpcf_model.pt"
DATA_ROOT = RUNS_ROOT / "t1" / "mpcf_data"


def inflow_rate(env, hist: list) -> float:
    hist.append((env.sim.t, env.sim.departed))
    while hist and hist[0][0] < env.sim.t - 120.0 - 1e-9:
        hist.pop(0)
    return (hist[-1][1] - hist[0][1]) * 3600.0 / max(hist[-1][0] - hist[0][0], 1.0) if len(hist) > 1 else 0.0


def gen_one(seed: int, kind: str, rep: int, out: Path, grid=None, perturb=None, q_range=(1400.0, 1800.0)) -> int:
    """grid: settings in env-action order; "off" (if present) must be first (meter_sched allow_off)."""
    from vsl_lab.envs.bn4_env import BN4Env
    grid = grid or GRID
    rng = np.random.default_rng(seed * 10 + rep)
    q = float(rng.uniform(*q_range))
    on = [g for g in grid if g != "off"]
    env = BN4Env(inflow=(q, q), actuator="meter_sched", meter_grid=on, allow_off=("off" in grid), decision_s=30,
                 eval_seeds=[seed], perturb=(KINDS[kind] if perturb is None else perturb), tag=f"mpcf_gen_{os.getpid()}")
    obs, _ = env.reset()
    X, A, Q, Y = [], [], [], []
    hist: list = []
    k, a, start = 0, int(rng.integers(0, len(grid))), None
    off = int(rng.integers(0, HOLD))
    done = False
    while not done:
        qin = inflow_rate(env, hist)
        if (k - off) % HOLD == 0 and k >= off:
            if start is not None:
                Y.append(env.sim.tts_system - start)
            a = int(rng.integers(0, len(grid)))
            X.append(obs.copy()); A.append(a); Q.append(qin)
            start = env.sim.tts_system
        obs, r, done, _, info = env.step(a)
        k += 1
    if start is not None and len(Y) < len(X):
        X, A, Q = X[:len(Y)], A[:len(Y)], Q[:len(Y)]
    env.close()
    np.savez(out, X=np.asarray(X, np.float32), A=np.asarray(A), Q=np.asarray(Q, np.float32), Y=np.asarray(Y, np.float32))
    return len(Y)


class Net:
    def __init__(self, n_in: int):
        import torch
        self.torch = torch
        self.m = torch.nn.Sequential(torch.nn.Linear(n_in, 64), torch.nn.Tanh(), torch.nn.Linear(64, 64), torch.nn.Tanh(),
                                     torch.nn.Linear(64, 1))


def features(obs: np.ndarray, qin: float, a: int, n_act: int | None = None) -> np.ndarray:
    oh = np.zeros(n_act or len(GRID), np.float32)
    oh[a] = 1.0
    return np.concatenate([obs.astype(np.float32), np.asarray([qin / 2000.0], np.float32), oh]).astype(np.float32)


class MPCF:
    """Receding-horizon setting choice from the frozen fitted model."""

    def __init__(self, path: Path = MODEL):
        import torch
        torch.set_num_threads(1)
        ck = torch.load(path, map_location="cpu", weights_only=False)
        self.mu, self.sd, self.ymu, self.ysd = ck["mu"], ck["sd"], ck["ymu"], ck["ysd"]
        self.net = Net(len(self.mu)).m
        self.net.load_state_dict(ck["state"])
        self.net.eval()
        self.torch = torch
        self.hist: list = []
        self.n_act = len(ck.get("grid", GRID))

    def choose(self, env, obs: np.ndarray) -> int:
        qin = inflow_rate(env, self.hist)
        F = np.stack([features(obs, qin, a, self.n_act) for a in range(self.n_act)]).astype(np.float32)   # float64 bug fix
        with self.torch.no_grad():
            y = self.net(self.torch.from_numpy((F - self.mu) / self.sd)).numpy().reshape(-1)
        return int(np.argmin(y))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["gen", "genall", "fit"])
    ap.add_argument("--seed", type=int)
    ap.add_argument("--kind")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--spec", default=None, help="Lead 1: JSON with grid, conds {name: perturb}, seeds [a, b], q, data_root, model")
    ap.add_argument("--cond", default=None, help="gen: condition name in --spec")
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.spec).read_text()) if a.spec else None
    global DATA_ROOT, MODEL, SEEDS
    if spec:
        DATA_ROOT, MODEL = Path(spec["data_root"]), REPO_ROOT / spec["model"]
        SEEDS = list(range(spec["seeds"][0], spec["seeds"][1] + 1))
    if a.what == "gen":
        try:
            n = 0
            for rep in range(a.reps):
                name = a.cond if spec else a.kind
                out = DATA_ROOT / f"{name}_s{a.seed}_r{rep}.npz"
                out.parent.mkdir(parents=True, exist_ok=True)
                if spec:
                    n += gen_one(a.seed, "none", rep, out, grid=spec["grid"], perturb=spec["conds"][a.cond],
                                 q_range=(spec["q"], spec["q"]))
                else:
                    n += gen_one(a.seed, a.kind, rep, out)
            print(json.dumps({"seed": a.seed, "kind": a.kind, "samples": n}))
            return 0
        except Exception as exc:   # never fail silently
            import traceback
            print(json.dumps({"error": repr(exc), "traceback": traceback.format_exc()[-1500:]}))
            return 2
    if a.what == "genall":
        from vsl_lab.ops.scheduler import Job, run_batch
        if spec:
            jobs = [Job(jid=f"mpcf2_{c}_{s}", argv=["vsl_lab.jobs.mpcf", "gen", "--seed", str(s), "--cond", c, "--reps",
                                                    str(a.reps), "--spec", a.spec]) for s in SEEDS for c in spec["conds"]]
        else:
            jobs = [Job(jid=f"mpcf_{k}_{s}", argv=["vsl_lab.jobs.mpcf", "gen", "--seed", str(s), "--kind", k, "--reps", str(a.reps)])
                    for s in SEEDS for k in KINDS]
        run_batch(jobs, DATA_ROOT / "batch", a.workers, gate_ok=a.gate_ok)
        return 0
    import torch
    torch.manual_seed(7110299)
    torch.set_num_threads(4)
    fs = sorted(DATA_ROOT.glob("*.npz"))
    X, Y, G = [], [], []
    for f in fs:
        d = np.load(f)
        n_act = len(spec["grid"]) if spec else len(GRID)
        for x, aa, q, y in zip(d["X"], d["A"], d["Q"], d["Y"]):
            X.append(features(x, float(q), int(aa), n_act)); Y.append(float(y)); G.append(f.name.rsplit("_r", 1)[0])
    X, Y = np.asarray(X, np.float32), np.asarray(Y, np.float32)
    groups = sorted(set(G))
    rng = np.random.default_rng(7110299)
    val_groups = set(rng.choice(groups, size=max(1, len(groups) // 5), replace=False))
    vm = np.array([g in val_groups for g in G])
    mu, sd = X[~vm].mean(0), X[~vm].std(0) + 1e-6
    ymu, ysd = float(Y[~vm].mean()), float(Y[~vm].std() + 1e-6)
    Xt = torch.from_numpy((X - mu) / sd)
    Yt = torch.from_numpy((Y - ymu) / ysd).reshape(-1, 1)
    net = Net(X.shape[1]).m
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-5)
    best, best_state, bad = np.inf, None, 0
    idx_tr = np.nonzero(~vm)[0]
    for ep in range(400):
        net.train()
        perm = rng.permutation(idx_tr)
        for i in range(0, len(perm), 256):
            b = perm[i:i + 256]
            opt.zero_grad()
            loss = torch.nn.functional.mse_loss(net(Xt[b]), Yt[b])
            loss.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            vl = float(torch.nn.functional.mse_loss(net(Xt[vm]), Yt[vm]))
        if vl < best - 1e-5:
            best, best_state, bad = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= 30:
                break
    net.load_state_dict(best_state)
    with torch.no_grad():
        pv = net(Xt[vm]).numpy().reshape(-1) * ysd + ymu
    yv = Y[vm]
    r2 = 1.0 - float(np.sum((pv - yv) ** 2) / np.sum((yv - yv.mean()) ** 2))
    torch.save({"state": net.state_dict(), "mu": mu, "sd": sd, "ymu": ymu, "ysd": ysd, "grid": spec["grid"] if spec else GRID},
               MODEL)
    rep = {"n_samples": int(len(Y)), "n_val": int(vm.sum()), "val_mse_std": best, "val_R2": r2, "epochs": ep + 1,
           "data_seeds": f"{SEEDS[0]}-{SEEDS[-1]}", "frozen": time.strftime("%Y-%m-%d %H:%M")}
    (REPO_ROOT / "docs" / "lab" / (spec["fit_report"] if spec else "t1_mpcf_fit.json")).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
