"""Same network, two read-outs: sw's policy part (decisions past x_from only) and the v3w learner with the same checkpoint.
X1 minus X2 confidence, entropy and reversal share per learner (paired over 40 seeds)."""
import json, numpy as np
from base import *
rows, T = load()
J = json.load(open("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/job_test.json"))["arms"]
def pt(a):
    c = J[f"X1|{a}"]["ctrl"]; return c.get("pt") or c.get("switch", {}).get("pt")
for i in range(5):
    w = ARMS["v3w"][i]; s = f"s{i}u500"
    out = [f"learner {i}: {w} {pt(w).split('/')[-1]} | {s} {pt(s).split('/')[-1]}"]
    for a in [w, s]:
        for k in ["conf_med", "ent", "rev_share"]:
            A = {sd: derived(r)[k] for sd, r in T[("X1", a, 5300.0)].items()}; B = {sd: derived(r)[k] for sd, r in T[("X2", a, 5300.0)].items()}
            d, _ = paired_diff(A, B); out.append(f"   {a} {k} X1 {np.median(list(A.values())):.3f} X2 {np.median(list(B.values())):.3f} X1-X2 {fmt(d)}")
    print("\n".join(out))
