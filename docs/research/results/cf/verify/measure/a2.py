"""Where and how severe: per-group statistic and additive mean-difference shares (descriptive)."""
import sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from cd5 import T, V3W, edge, fmt
import json
s = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
COMP = s["competitors"]
R = lambda *roads: (lambda g: sum(g.get(f"m_road_ttc3|{r}", 0.0) for r in roads))
GROUPS = {"merge1 (3a,ramp1)": R("3a", "ramp1"), "merge2 (4a,ramp2)": R("4a", "ramp2"), "between (3)": R("3"),
          "event (1,2)": R("1", "2"), "junction": R("junction")}
def mdiff(a, f):
    O = T[a][f].to_numpy(float) if isinstance(f, str) else f(T[a]).to_numpy(float)
    return float(np.mean([np.mean(O - (T[w][f].to_numpy(float) if isinstance(f, str) else f(T[w]).to_numpy(float))) for w in V3W]))
print("medians per arm (v3w = median over learners of medians) of TTC<3 s samples by group")
hdr = list(GROUPS) + ["total"]
print("arm".ljust(16), " ".join(h[:12].rjust(12) for h in hdr))
def med(a, f):
    return float(np.median(f(T[a]) if callable(f) else T[a][f]))
for a in ["v3w"] + COMP + ["nc"]:
    fs = list(GROUPS.values()) + ["ttc_net"]
    vals = [np.median([med(w, f) for w in V3W]) if a == "v3w" else med(a, f) for f in fs]
    print(a.ljust(16), " ".join(f"{v:12.1f}" for v in vals))
print("\nadditive decomposition: mean over learners of mean(opp - v3w) per group, and share of the total mean difference")
print("arm".ljust(16), " ".join(h[:12].rjust(16) for h in hdr))
for a in COMP:
    tot = mdiff(a, "ttc_net")
    parts = [mdiff(a, f) for f in GROUPS.values()]
    print(a.ljust(16), " ".join(f"{p:8.1f} ({100*p/tot:4.0f}%)" for p in parts), f"{tot:8.1f}")
print("\nC-D5 statistic per group (positive = v3w lower); merge1, merge2, between, event, junction")
for a in COMP:
    print(a.ljust(16), "  ".join(fmt(edge(a, f)) for f in GROUPS.values()), flush=True)
