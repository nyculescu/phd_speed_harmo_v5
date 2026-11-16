"""Post hoc (not in the plan): the reader's deficit form checked on my data; the 300->600 change with edge-1 samples left out."""
import json
import numpy as np
exec(open("stats.py").read().split("res = {")[0])
out = {}
for rule in RULES:
    for g in ("merge", "e1", "rest"):
        P = np.stack([vec("L600", l, g) for l in LEARNERS]); Rv = vec("L600", rule, g)
        out[f"deficit600 pooled-median {rule} {g}"] = float(np.median(P.mean(0) - Rv))
        out[f"deficit600 cd5-form {rule} {g}"] = float(np.mean(np.median(P - Rv, axis=1)))
    e3, _ = edges("L300", rule, "ttc_ex1"); e6, _ = edges("L600", rule, "ttc_ex1")
    b = boot(e6) - boot(e3)
    out[f"change_no_edge1 {rule}"] = {"pt": stat(e6) - stat(e3), "ci95": pct(b, 2.5, 97.5)}
    t3 = vec("L300", rule, "ttc_net"); t6 = vec("L600", rule, "ttc_net")
    out[f"rule {rule} ttc_net 600 mean/median"] = [float(t6.mean()), float(np.median(t6))]
    out[f"rule {rule} share of 600 runs with ttc_net > 2*median"] = float((t6 > 2 * np.median(t6)).mean())
Pm = np.stack([vec("L600", l, "ttc_net") for l in LEARNERS])
out["v3w ttc_net 600 mean / median of learner medians"] = [float(Pm.mean()), float(np.mean(np.median(Pm, axis=1)))]
json.dump(out, open("posthoc_A.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
