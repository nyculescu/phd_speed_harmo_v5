"""Additive mean-difference shares by follower speed band and period (descriptive)."""
import sys, json
sys.path.insert(0, sys.argv[1])
import numpy as np
from cd5 import T, V3W
s = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
def md(a, k):
    f = (lambda g: g[k]) if isinstance(k, str) else k
    return float(np.mean([np.mean(f(T[a]).to_numpy(float) - f(T[w]).to_numpy(float)) for w in V3W]))
parts = {"lo<5": "ttc3_s_lo", "mid5-10": "ttc3_s_mid", "hi>=10": "ttc3_s_hi", "before": "ttc3_p_before",
         "taper+hold": lambda g: g.ttc3_p_taper + g.ttc3_p_hold, "after120": "ttc3_p_after", "rest": "ttc3_p_rest"}
print("arm".ljust(16), " ".join(k.rjust(16) for k in parts), "total".rjust(8))
for a in s["competitors"]:
    tot = md(a, "ttc3")
    print(a.ljust(16), " ".join(f"{md(a, f):7.1f} ({100*md(a, f)/tot:4.0f}%)" for f in parts.values()), f"{tot:8.1f}")
