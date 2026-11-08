"""Operating map: policy arms against p333, 3E-T, os1_15_10 and nc on six metrics, every setting; tallies."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from lib import ARMS, SETTINGS, SIGN, arm, eff, load, verdict  # noqa: E402

OUT = Path(__file__).parent
T = {k: load(k) for k in ("s1", "band", "test")}
res, med = {}, {}
for kind, cell, q, lab in SETTINGS:
    for key in SIGN:
        A = {}
        for a, mem in ARMS.items():
            try:
                A[a] = arm(T[kind], cell, q, mem, key)
            except KeyError:
                pass
        for a in A:
            med[f"{lab}|{a}|{key}"] = float(np.median(list(A[a].values())))
        for p in ("v3w", "tail", "sw", "inc", "p333", "3e", "os1"):
            if p not in A:
                continue
            for o in ("p333", "3e", "os1", "nc"):
                if o == p or o not in A:
                    continue
                res[f"{lab}|{p}|{o}|{key}"] = eff(A[p], A[o], SIGN[key])
        if key == "finished_pct":
            for p in ("v3w", "tail", "sw"):
                if p in A:
                    ss = sorted(set(A[p]) & set(A["p333"]))
                    d = np.array([A[p][s] - A["p333"][s] for s in ss])
                    idx = np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))
                    lo, hi = np.percentile(np.median(d[idx], axis=1), (2.5, 97.5))
                    res[f"{lab}|{p}|p333|finished_pp"] = (float(np.median(d)), float(lo), float(hi), len(ss))
json.dump({"res": res, "med": med}, open(OUT / "opmap_v.json", "w"), indent=0)

labs = [s[3] for s in SETTINGS]
lines = []
for key in SIGN:
    lines.append(f"\n== {key} (effect %, positive = first arm better)")
    for p in ("v3w", "tail", "sw"):
        for o in ("p333", "3e", "os1", "nc"):
            cells = []
            for lab in labs:
                t = res.get(f"{lab}|{p}|{o}|{key}")
                cells.append("     -     " if t is None else f"{t[0]:+.1f}[{t[1]:+.1f},{t[2]:+.1f}]")
            lines.append(f"{p}-{o}: " + " | ".join(f"{lab} {c}" for lab, c in zip(labs, cells)))
    lines.append("medians v3w/p333/3e/os1/nc: " + " | ".join(
        f"{lab} " + "/".join(f"{med.get(f'{lab}|{a}|{key}', float('nan')):.4g}" for a in ("v3w", "p333", "3e", "os1", "nc")) for lab in labs))
tal = {}
for k, t in res.items():
    lab, p, o, key = k.split("|")
    if key == "finished_pp":
        continue
    tal.setdefault(f"{p}|{o}", {"P": 0, "O": 0, "=": 0})[verdict(t)] += 1
lines.append("\n== tallies (P = first arm better, CI excludes 0)")
for k, v in tal.items():
    lines.append(f"{k}: {v}  n={sum(v.values())}")
lines.append("\n== O-wins (second arm better) for policy arms")
for k, t in res.items():
    lab, p, o, key = k.split("|")
    if p in ("v3w", "tail", "sw") and key != "finished_pp" and verdict(t) == "O":
        lines.append(f"{k}: {t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]")
lines.append("\n== finished_pct in pp vs p333")
for k, t in res.items():
    if k.endswith("finished_pp"):
        lines.append(f"{k}: {t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]")
open(OUT / "opmap_v.txt", "w").write("\n".join(lines))
print("\n".join(lines))
