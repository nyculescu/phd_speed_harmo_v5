"""Proxy for plan_b_v0 §8.5 (R) and §7.3 G1a from confirmatory 3's stored rows (r2m3, 5,300, seeds 7,440,200-219), the only
stored rows that pair a perturbed cell with steady traffic (S) on the same seeds per controller. Arms: baseline-v3 DRL
(d = per-seed mean of d0-d4; NOT v3w), p333, lr400_13_2, no control. Planning proxy only; never evidence."""
import json
from collections import defaultdict

import numpy as np

D = "/home/catalin/work/phd/v5b1_runs/conf3/"
T = defaultdict(dict)
for f in ("eval_map.jsonl", "eval_primary.jsonl"):
    for line in open(D + f):
        r = json.loads(line)
        if r.get("q") != 5300.0:
            continue
        cell, arm = r["name"].split("|")
        T[(cell, arm)][r["seed"]] = float(r["all_delay"])
seeds = sorted(T[("S", "p333")])
get = lambda c, a: np.array([T[(c, a)][s] for s in seeds])
rng = np.random.default_rng(20261108)
B = 20000
z = {}


def boot_med(x, B=B, n=None, r=rng):
    n = n or len(x)
    J = r.integers(0, len(x), (B, n))
    return np.median(x[J], axis=1)


out = {}
for cell in ("X1", "X2", "H1"):
    dS = np.mean([get("S", f"d{i}") for i in range(5)], axis=0)
    dC = np.mean([get(cell, f"d{i}") for i in range(5)], axis=0)
    loss_d = dC - dS
    loss_nc = get(cell, "nc") - get("S", "nc")
    print(f"== {cell} (n = {len(seeds)}), nc median loss {np.median(loss_nc):.0f} veh-s; nc G1a {np.median(get(cell,'nc')-get('S','nc'))/np.median(get('S','nc'))*100:+.1f} %"
          f"; p333 G1a {np.median(get(cell,'p333')-get('S','p333'))/np.median(get('S','p333'))*100:+.1f} %")
    for o in ("p333", "lr400_13_2"):
        oS, oC = get("S", o), get(cell, o)
        loss_o = oC - oS
        x = loss_o - loss_d
        R = float(np.median(x))
        bm = boot_med(x)
        lo, hi = np.percentile(bm, [2.5 / 3, 100 - 2.5 / 3])
        # level effects in the cell and in S (% of the opponent's median)
        eC = float(np.median(oC - dC) / np.median(oC) * 100)
        eS = float(np.median(oS - dS) / np.median(oS) * 100)
        corr_o = float(np.corrcoef(oC, oS)[0, 1])
        corr_diff = float(np.corrcoef(oC - dC, oS - dS)[0, 1])
        sd_cell = float(np.std(oC - dC, ddof=1)); sd_R = float(np.std(x, ddof=1))
        # sign-flip null: false 'better' (lower bound > 0) rate at m = 3, n = 20 and n = 120 (resampled)
        fr = {}
        for n in (20, 120):
            hits = 0
            reps = 1000
            r2 = np.random.default_rng(7 + n)
            for _ in range(reps):
                idx = r2.integers(0, len(x), n) if n != len(x) else np.arange(n)
                xs = x[idx] * np.where(r2.random(n) < 0.5, -1, 1)
                J = r2.integers(0, n, (4000, n))
                if np.percentile(np.median(xs[J], axis=1), 2.5 / 3) > 0:
                    hits += 1
            fr[n] = hits / reps
        # power at n = 120 under the stored R
        r3 = np.random.default_rng(99)
        pw = 0
        for _ in range(400):
            idx = r3.integers(0, len(x), 120)
            J = r3.integers(0, 120, (4000, 120))
            pw += np.percentile(np.median(x[idx][J], axis=1), 2.5 / 3) > 0
        pw /= 400
        out[f"{cell}|{o}"] = dict(R=R, lo=lo, hi=hi, R_pct_nc_loss=R / np.median(loss_nc) * 100, e_cell=eC, e_S=eS, corr_o_cell_S=corr_o,
                                  corr_paired_diff_cell_S=corr_diff, sd_cell_diff=sd_cell, sd_R=sd_R, null_false=fr, power120=pw)
        print(f"  vs {o:11s} level effect cell {eC:+5.1f} %  S {eS:+5.1f} %  | R = {R:+7.0f} veh-s [{lo:+.0f}, {hi:+.0f}] ({R/np.median(loss_nc)*100:+.1f} % of nc loss)"
              f" | corr(cell,S) of o {corr_o:.2f}, of paired diff {corr_diff:.2f}; SD diff cell {sd_cell:.0f}, SD R {sd_R:.0f}"
              f" | sign-flip false rate n20 {fr[20]:.3f} n120 {fr[120]:.3f} (nominal 0.0083) | power n120 {pw:.2f}")
json.dump(out, open("resil.json", "w"), indent=1, default=float)
