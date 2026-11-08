"""Per-seed arm values from the stored S0 test rows (X1/X2 at 5,300, read-only), with the extra fields of the Plan B v0 rule."""
import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_test.jsonl")
OUT = Path(__file__).resolve().parent / "arms2.pkl"
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
OTHER = {f"{p}{i}{s}" for i in range(5) for p, s in (("t", ""), ("s", "u500"), ("d", "u500"))}
KEYS = ("all_delay", "ttc_net", "passed", "collisions", "fm", "ev4_all", "ev4_vkm")


def derive(r):
    pk = {c: np.asarray(r[f"m_peak_{c}"]) for c in ("car", "alks", "truck")}
    ev = float(pk["car"][2:].sum() + pk["alks"][2:].sum() + pk["truck"][1:].sum())
    vkm = sum(float(r[f"m_dist_m_{c}"]) for c in ("car", "alks", "truck")) / 1000.0
    return {"all_delay": float(r["all_delay"]), "ttc_net": float(r["ttc_net"]), "passed": float(r["passed"]),
            "collisions": float(r.get("collisions") or 0), "fm": float(r.get("alks_full_moving") or 0),
            "ev4_all": ev, "ev4_vkm": ev / vkm * 1000.0}


def load():
    if OUT.exists():
        return pickle.load(open(OUT, "rb"))
    T = defaultdict(dict)
    for line in open(DATA):
        r = json.loads(line)
        cell, arm = r["name"].split("|")
        T[(cell, arm)][r["seed"]] = derive(r)
    cells = {}
    for cell in sorted({c for c, _ in T}):
        arms = sorted({a for c, a in T if c == cell})
        seeds = sorted(set.intersection(*(set(T[(cell, a)]) for a in arms)))
        A = {a: {k: np.array([T[(cell, a)][s][k] for s in seeds]) for k in KEYS} for a in arms}
        A["v3w"] = {k: np.mean([A[l][k] for l in V3W], axis=0) for k in KEYS}
        rules = [a for a in arms if a not in V3W and a not in OTHER and a != "nc"]
        cells[cell] = {"seeds": seeds, "arms": A, "rules": rules}
    pickle.dump(cells, open(OUT, "wb"))
    return cells


if __name__ == "__main__":
    for k, v in load().items():
        print(k, len(v["seeds"]), len(v["rules"]), v["rules"])
