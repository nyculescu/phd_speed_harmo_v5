"""D-check (roadmap §2, "what data is really needed?"): is merge breakdown predictable 5 min ahead from richer
detector features than the bottleneck density that MTFC uses?

Samples: every 30 s of NC MRG3 runs while not yet broken down (5-min mean speed at up0b >= 60 km/h).
Label: breakdown onset within the next `horizon_s` (default 300 s).
Feature sets: F0 = [rho_merge] (MTFC's information); F1 = F0 + [rho_down, q_up0a, q_up0b, v_up0b, q_ramp];
F2 = all 30 s features + their 2-min trends (difference over 4 steps).
Model: L2 logistic regression (numpy/scipy); evaluation: AUC on held-out SEEDS (grouped k-fold).
Pre-registered reading: precursors are informative if AUC(F2) - AUC(F0) >= 0.05.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


def load_run(d: Path):
    with open(d / "features.csv") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    s = json.loads((d / "summary.json").read_text())
    keys = [k for k in rows[0].keys() if k != "t"]
    X = np.array([[float(r[k]) for k in keys] for r in rows])
    t = np.array([float(r["t"]) for r in rows])
    return {"t": t, "X": X, "keys": keys, "seed": s["seed"], "capdrop": s.get("capdrop") or {}}


def samples(run, horizon_s: float, sets: dict):
    t, X, keys = run["t"], run["X"], run["keys"]
    k = {n: i for i, n in enumerate(keys)}
    cd = run["capdrop"]
    onset = cd.get("onset_t") if cd.get("breakdown") else None
    out = {name: [] for name in sets}
    y = []
    for j in range(4, len(t)):
        if onset is not None and t[j] >= onset:
            break                                    # only pre-breakdown states
        y.append(1 if (onset is not None and onset - t[j] <= horizon_s) else 0)
        for name, cols in sets.items():
            if cols == "ALL+TREND":
                base = X[j]
                trend = X[j] - X[j - 4]
                out[name].append(np.concatenate([base, trend]))
            else:
                out[name].append(np.array([X[j][k[c]] for c in cols]))
    return out, y


def fit_logreg(X, y, lam=1.0):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    Z1 = np.hstack([Z, np.ones((len(Z), 1))])

    def f(w):
        z = Z1 @ w
        ll = np.sum(np.logaddexp(0, z) - y * z)
        return ll + lam * np.sum(w[:-1] ** 2), Z1.T @ (1 / (1 + np.exp(-z)) - y) + np.r_[2 * lam * w[:-1], 0.0]
    w = minimize(f, np.zeros(Z1.shape[1]), jac=True, method="L-BFGS-B").x
    return lambda Xn: np.hstack([(Xn - mu) / sd, np.ones((len(Xn), 1))]) @ w


def auc(score, y):
    y = np.asarray(y)
    pos, neg = score[y == 1], score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    r = np.argsort(np.argsort(np.concatenate([pos, neg]))) + 1
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="directory containing MRG3 NC run dirs with features.csv")
    ap.add_argument("--horizon-s", type=float, default=300.0)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sets = {"F0_density": ["rho_merge"],
            "F1_local": ["rho_merge", "rho_down", "up0a_q", "up0b_q", "up0b_v", "q_ramp"],
            "F2_all_trend": "ALL+TREND"}
    runs = [r for r in (load_run(p.parent) for p in Path(a.root).rglob("features.csv")) if r]
    per_seed = {}
    for r in runs:
        xs, y = samples(r, a.horizon_s, sets)
        if y:
            per_seed[r["seed"]] = (xs, y)
    seeds = sorted(per_seed)
    folds = [seeds[i::a.folds] for i in range(a.folds)]
    res = {}
    for name in sets:
        scores, ys = [], []
        for fold in folds:
            tr = [s for s in seeds if s not in fold]
            Xtr = np.vstack([np.array(per_seed[s][0][name]) for s in tr])
            ytr = np.concatenate([per_seed[s][1] for s in tr])
            if ytr.sum() == 0 or ytr.sum() == len(ytr):
                continue
            model = fit_logreg(Xtr, ytr)
            for s in fold:
                Xte = np.array(per_seed[s][0][name])
                scores.append(model(Xte))
                ys.append(np.array(per_seed[s][1]))
        if scores:
            res[name] = {"auc": auc(np.concatenate(scores), np.concatenate(ys)), "n": int(sum(len(y) for y in ys)),
                         "n_pos": int(sum(int(np.sum(y)) for y in ys))}
    gain = (res.get("F2_all_trend", {}).get("auc", np.nan) - res.get("F0_density", {}).get("auc", np.nan))
    out = {"n_runs": len(runs), "n_seeds": len(seeds), "horizon_s": a.horizon_s, "results": res,
           "auc_gain_F2_minus_F0": gain, "precursors_informative": bool(gain >= 0.05)}
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
