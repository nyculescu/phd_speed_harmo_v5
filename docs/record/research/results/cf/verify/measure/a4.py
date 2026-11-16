"""Headline E without merge 2, and without both merges, for all 14 competitors (C-D5, 97.5 %)."""
import sys, json
sys.path.insert(0, sys.argv[1])
from cd5 import edge, fmt
s = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
R = lambda *roads: (lambda g: sum(g.get(f"m_road_ttc3|{r}", 0.0) for r in roads))
exm2 = lambda g: g.ttc_net - R("4a", "ramp2")(g)
exm12 = lambda g: g.ttc_net - R("4a", "ramp2", "3a", "ramp1")(g)
exm2_tl = lambda g: g.ttc_net - R("4a", "ramp2")(g) - g.get("m_road_ttc3|1|taper", 0) * 0  # placeholder
print("arm".ljust(16), "E (all)".rjust(26), "E without merge 2".rjust(26), "E without both merges".rjust(26))
mins = [99, 99, 99]
for a in s["competitors"]:
    e = [edge(a, f) for f in ("ttc_net", exm2, exm12)]
    mins = [min(m, x[1]) for m, x in zip(mins, e)]
    print(a.ljust(16), " ".join(fmt(x).rjust(26) for x in e), flush=True)
print("smallest lower bounds:", " ".join(f"{m:+.1f}" for m in mins))
