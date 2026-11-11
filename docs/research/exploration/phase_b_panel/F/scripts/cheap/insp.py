import json, numpy as np
Z = np.load("../../../critic_F/s6_scalars.npz")
keys = list(Z["keys"]); print("n keys", len(keys)); print(keys[:80])
print("seeds", Z["seeds"][:3], Z["seeds"][-3:], len(Z["seeds"]))
arms = sorted(k for k in Z.files if "|" in k)
print(len(arms)); print([a for a in arms if a.startswith("TRUCK|")])
print([a for a in arms if a.startswith("S|")])
J = json.load(open("/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json"))
def show(d, depth=0, maxd=2, pre=""):
    if isinstance(d, dict):
        for k, v in list(d.items())[:60]:
            t = type(v).__name__
            n = len(v) if hasattr(v, "__len__") and not isinstance(v, str) else ""
            print("  " * depth + f"{k}: {t} {n}")
            if depth < maxd: show(v, depth + 1, maxd)
show(J, 0, 1)
