import pickle, json
import numpy as np
T, src = pickle.load(open("rows.pkl", "rb"))
ARMS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"],
        "tail": [f"t{i}" for i in range(5)], "sw": [f"s{i}u500" for i in range(5)]}
MET = {"delay": ("all_delay", -1), "cf": ("ttc_net", -1), "flow": ("passed", 1), "b3": ("b3_step", -1), "b45": ("b45_step", -1)}
LEARN = set(sum(ARMS.values(), [])) | {f"d{i}u500" for i in range(5)}

def v(r, k):
    x = r.get(k)
    return 0.0 if x is None else float(x)

def arm_rows(cell, q, names):
    rows = [T[(f"{cell}|{n}", q)] for n in names]
    seeds = sorted(set.intersection(*(set(r) for r in rows)))
    return {s: {k: float(np.mean([v(r[s], k) for r in rows])) for k in ("all_delay", "ttc_net", "passed", "b3_step", "b45_step")} for s in seeds}

def rule_rows(cell, q, n):
    return {s: {k: v(r, k) for k in ("all_delay", "ttc_net", "passed", "b3_step", "b45_step")} for s, r in T[(f"{cell}|{n}", q)].items()}

def eff(A, B, key, sign, seed=20261104, pct=(2.5, 97.5)):
    ds = sorted(set(A) & set(B))
    assert len(ds) == len(A) == len(B)
    ref = max(float(np.median([B[s][key] for s in ds])), 1e-9)
    d = np.array([sign * (A[s][key] - B[s][key]) / ref * 100 for s in ds])
    rng = np.random.default_rng(seed)
    bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(bs, pct)
    return float(np.median(d)), float(lo), float(hi)

cells = sorted({(n.split("|")[0], q) for (n, q) in T})
out = {}
for cell, q in cells:
    rules = sorted({n.split("|")[1] for (n, qq) in T if qq == q and n.startswith(cell + "|")} - LEARN)
    arms = {a: arm_rows(cell, q, nm) for a, nm in ARMS.items() if all((f"{cell}|{x}", q) in T for x in nm)}
    R = {r: rule_rows(cell, q, r) for r in rules}
    key = f"{cell}|{int(q)}"
    out[key] = {"rules": rules, "arms": list(arms), "eff": {}, "med": {}, "pmed": {}, "eff_alt": {}}
    for nm, A in list(arms.items()) + list(R.items()):
        out[key]["med"][nm] = {m: float(np.median([A[s][k] for s in A])) for m, (k, sg) in MET.items()}
    for a, A in arms.items():
        for r, B in R.items():
            for m, (k, sg) in MET.items():
                out[key]["eff"][f"{a}|{r}|{m}"] = eff(A, B, k, sg)
                out[key]["eff_alt"][f"{a}|{r}|{m}"] = [eff(A, B, k, sg, seed=sd) for sd in (1, 2, 3)]
                ds = sorted(A)
                out[key]["pmed"][f"{a}|{r}|{m}"] = float(np.median([B[s][k] - A[s][k] for s in ds]))
json.dump(out, open("mine.json", "w"))
print("done", list(out))
