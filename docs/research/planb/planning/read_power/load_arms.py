"""Per-seed arm values from the S0/S1 rows (read-only), cached as one npz.
v3w = per-seed mean over its 5 learners (round 2's arm_mean); robust braking counts as s01 x1_braking/common_x.py."""
import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).resolve().parent
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
OTHER_LEARNERS = {f"{p}{i}{s}" for i in range(5) for p, s in (("t", ""), ("s", "u500"), ("d", "u500"))}
# key -> sign (round 2's common.raw: positive = policy better)
METRICS = {"all_delay": -1, "ttc_net": -1, "ev4_ca": -1, "ev5_alks": -1, "ev4_all": -1, "b3_step": -1, "b45_step": -1,
           "passed": 1}


def val(r, k):
    v = r.get(k)
    return 0.0 if v is None else float(v)


def derive(r):
    pk = {c: np.asarray(r[f"m_peak_{c}"]) for c in ("car", "alks", "truck")}
    # PEAK_EDGES bins: 2 = (-4.5, -4.0], 4..7 = (-9, -5]
    return {"all_delay": val(r, "all_delay"), "ttc_net": val(r, "ttc_net"),
            "ev4_ca": float(pk["car"][2:].sum() + pk["alks"][2:].sum()),
            "ev5_alks": float(pk["alks"][4:8].sum()),
            "ev4_all": float(sum(pk[c][2:].sum() for c in pk)),
            "b3_step": val(r, "b3_step"), "b45_step": val(r, "b45_step"), "passed": val(r, "passed")}


def build():
    T = defaultdict(dict)
    for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
        for line in open(DATA / f):
            r = json.loads(line)
            cell, arm = r["name"].split("|")
            T[(cell, r["q"], arm)][r["seed"]] = derive(r)
    cells = {}
    for cell, q in sorted({(c, q) for c, q, _ in T}):
        arms = sorted({a for c, qq, a in T if c == cell and qq == q})
        seeds = sorted(set.intersection(*(set(T[(cell, q, a)]) for a in arms)))
        assert all(len(T[(cell, q, a)]) == len(seeds) for a in arms), (cell, q)
        A = {}
        for a in arms:
            A[a] = {k: np.array([T[(cell, q, a)][s][k] for s in seeds]) for k in METRICS}
        A["v3w"] = {k: np.mean([A[l][k] for l in V3W], axis=0) for k in METRICS}
        rules = [a for a in arms if a not in V3W and a not in OTHER_LEARNERS and a != "nc"]
        label = f"{cell}@{q:.0f}" if cell != "B" else f"B@{q:.0f}"
        cells[label] = {"seeds": seeds, "arms": A, "rules": rules, "has_nc": "nc" in arms}
    pickle.dump(cells, open(OUT / "arms.pkl", "wb"))
    return cells


def load():
    p = OUT / "arms.pkl"
    return pickle.load(open(p, "rb")) if p.exists() else build()


if __name__ == "__main__":
    c = build()
    for k, v in c.items():
        print(k, len(v["seeds"]), "rules", len(v["rules"]), v["rules"])
