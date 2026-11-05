"""Smoke in training mode for V388: the real training path with normalised inputs. It runs as learner 0, so it uses learner 0's first training seeds (V389). usage: smoke_norm.py env.json out_dir"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

from v5b.fleet import b_env as be, c_train as ct

if __name__ == "__main__":
    env, out = json.load(open(sys.argv[1])), Path(sys.argv[2])
    rows, last = [], {}
    up0 = ct.update

    def update(net, opt, batch, scale, rng):
        lo, gl, a, lp = (torch.from_numpy(x) for x in batch[:4])
        with torch.no_grad():
            ratio = (net.dist(lo).log_prob(a) - lp).exp()
            z = net._scaled(lo, net.lo_mean, net.lo_var).numpy()
        n0 = float(net.n_seen)
        st = up0(net, opt, batch, scale, rng)
        rows.append({"ratio_err": float((ratio - 1).abs().max()), "n_seen_before": n0, "n_seen_after": float(net.n_seen), "n": len(lo), "z_mean": z.mean(0).round(2).tolist(), "z_sd": z.std(0).round(2).tolist(), "r_sd": float(batch[6].std()), "z_max": float(np.abs(z).max())})
        last.update(lo=batch[0], gl=batch[1])
        return st

    ct.update = update
    f = ct.train(out, 0, 3, 3, env, None, 0.933, 0.967, (4090.0, 4600.0, 5300.0), 20261205)
    ck = torch.load(f, map_location="cpu")
    g = ct.Greedy(str(f))
    due = np.ones(len(last["lo"]), dtype=bool)
    acts = g((list(range(len(last["lo"]))), last["lo"], last["gl"], due))
    p = json.load(open(out / "C0_pilot.json"))
    log = [json.loads(x) for x in open(out / "C0_updates.jsonl")]
    bad = []
    for u, r in enumerate(rows):
        print(u, {k: r[k] for k in ("ratio_err", "n_seen_before", "n_seen_after", "n", "r_sd", "z_max")})
        print("  z mean", r["z_mean"], "\n  z sd", r["z_sd"])
        if r["ratio_err"] > 1e-4:
            bad.append(f"update {u}: ratio not 1")
        if r["n_seen_after"] != r["n_seen_before"]:
            bad.append(f"update {u}: statistics moved during the update")
        if r["r_sd"] < 0.05:
            bad.append(f"update {u}: per-vehicle reward does not vary (V294)")
        live = [i for i in range(be.CAV_LOCAL) if i != 11]
        if max(abs(x) for i, x in enumerate(r["z_mean"]) if i in live) > 1.0 or any(not 0.2 < r["z_sd"][i] < 3.0 for i in live):     # one batch may differ from the running statistics (V389)
            bad.append(f"update {u}: inputs are not standard")
    total = p["n"] + sum(r["n"] for r in rows)
    if float(ck["net"]["n_seen"]) != total:
        bad.append("checkpoint statistics do not cover pilot and updates")
    if not all(k in ct.NORM_KEYS or "." in k for k in ck["net"]) or not ct.NORM_KEYS <= set(ck["net"]):
        bad.append("checkpoint lacks statistics")
    if float(ck["net"]["lo_var"][11]) != 0.0:
        bad.append("input 11 is no longer dead: re-read V387")
    if len(set(acts.values())) < 2:
        bad.append("greedy policy gives one action only on this batch")
    ramp = last["lo"][:, 2] > 0.5
    zero14 = float((last["lo"][ramp, 14] == 0.0).mean())
    print("on-ramp decisions", int(ramp.sum()), "with input 14 exactly 0:", round(zero14, 3))
    if zero14 > 0.05:
        bad.append("input 14 is still 0 for merging vehicles")
    if json.load(open(out / "C0_config.json"))["inputs"] != ct.INPUT_NORM:
        bad.append("config lacks the input setting")
    print("log keys", sorted(log[0]), "kl", [round(x["kl"], 4) for x in log], "clipfrac", [round(x["clipfrac"], 3) for x in log], "ev", [round(x["ev"], 3) for x in log], "entropy", [round(x["entropy"], 3) for x in log])
    print("pilot seeds", p["seeds"], "pilot n", p["n"], "lo sd", np.sqrt(p["lo_var"]).round(3).tolist())
    print("SMOKE", "ok" if not bad else bad)
    sys.exit(1 if bad else 0)
