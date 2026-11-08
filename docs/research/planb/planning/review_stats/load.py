"""Per-seed arm values from stored S0 rows (read-only), for the statistics review of plan_b_v0."""
import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).resolve().parent / "arms.pkl"
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
OTHER = {f"{p}{i}{s}" for i in range(5) for p, s in (("t", ""), ("s", "u500"), ("d", "u500"))}
KEYS = ("all_delay", "ttc_net", "passed", "collisions", "fm", "ev4_vkm", "ev4", "N", "finished_pct")


def derive(r):
    pk = {c: np.asarray(r[f"m_peak_{c}"]) for c in ("car", "alks", "truck")}
    ev = float(pk["car"][2:].sum() + pk["alks"][2:].sum() + pk["truck"][1:].sum())
    vkm = sum(float(r[f"m_dist_m_{c}"]) for c in ("car", "alks", "truck")) / 1000.0
    return {"all_delay": float(r["all_delay"]), "ttc_net": float(r["ttc_net"]), "passed": float(r["passed"]),
            "collisions": float(r.get("collisions") or 0), "fm": float(r.get("alks_full_moving") or 0),
            "ev4_vkm": ev / vkm * 1000.0, "ev4": ev, "N": float(r["N"]), "finished_pct": float(r.get("finished_pct") or 0),
            "pert": str(r.get("pert_log"))[:80]}


def load():
    if OUT.exists():
        return pickle.load(open(OUT, "rb"))
    T = defaultdict(dict)
    perts = defaultdict(set)
    for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
        for line in open(D / f):
            r = json.loads(line)
            cell, arm = r["name"].split("|")
            key = f"{cell}@{int(r['q'])}"
            d = derive(r)
            perts[key].add(d.pop("pert"))
            T[(key, arm)][r["seed"]] = d
    cells = {}
    for cell in sorted({c for c, _ in T}):
        arms = sorted({a for c, a in T if c == cell})
        seeds = sorted(set.intersection(*(set(T[(cell, a)]) for a in arms)))
        A = {a: {k: np.array([T[(cell, a)][s][k] for s in seeds]) for k in KEYS} for a in arms}
        A["v3w"] = {k: np.mean([A[l][k] for l in V3W], axis=0) for k in KEYS}
        rules = [a for a in arms if a not in V3W and a not in OTHER and a != "nc"]
        cells[cell] = {"seeds": seeds, "arms": A, "rules": rules, "perts": sorted(perts[cell])[:3]}
    pickle.dump(cells, open(OUT, "wb"))
    return cells


if __name__ == "__main__":
    for k, v in load().items():
        print(k, len(v["seeds"]), len(v["rules"]), v["rules"], v["perts"])
