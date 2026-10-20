import pickle, sys, numpy as np
from collections import Counter
R = pickle.load(open(sys.argv[1], "rb"))
N = {1600.0: "c2000", 2000.0: "c1800"}
Ntc = {1600.0: "f20_8", 2000.0: "c1800"}
bad = Counter(); n = 0; hm = 0; hn = 0
for key, r in R.items():
    if r["post"] is None or r["fa"] or r["rep"] is not None: continue
    seed, q, inc, k = r["seed"], r["q"], r["incident"], r["k"]
    tc = 7400240 <= seed <= 7400259
    Nq = (Ntc if tc else N)[q]
    if r["pre"] != Nq: bad["pre_not_N"] += 1; continue
    ref = f"{Nq}_{inc}_q{int(q)}_s{seed}" + (f"_k{k}" if k else "")
    if ref not in R:
        ref = f"{Nq}-{Nq}_{inc}_q{int(q)}_s{seed}" + (f"_k{k}" if k else "")
    if ref not in R or ref == key: bad["noref"] += 1; continue
    ts = r["t_switch"]
    a = [e for e in r["meter_log"] if ts is None or e[0] < ts - 1e-9]
    b = [e for e in R[ref]["meter_log"] if ts is None or e[0] < ts - 1e-9]
    n += 1
    if a != b: bad["prefix_diff"] += 1
    if ts is not None and r["q_at_switch"] != float(Nq[1:]) and Nq.startswith("c"): bad["q_at_switch"] += 1
    if r["post"] == Nq and not r["back"] and r["d"] == 0:
        hn += 1
        if r["hash"] != R[ref]["hash"]: hm += 1
print("prefix comparisons", n, dict(bad), "N->N vs N hash pairs", hn, "mismatch", hm)
