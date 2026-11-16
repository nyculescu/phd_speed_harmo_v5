"""Local exposure: vehicle-seconds by road, and close-following per vehicle-second at merge 2 (read only)."""
import json, pickle
import numpy as np
exec(open("s1.py").read().split("ALLR =")[0])
arms = ("v3w", "p333", "lr400_16_1", "grid_lr400_13_1", "MPC-F", "nc")
vs = lambda *roads: (lambda r: rsum(r, "m_road_vs", roads))
tt = lambda *roads: (lambda r: rsum(r, "m_road_ttc3", roads))
med = lambda a, f: float(np.median([np.median(col(w, f)) for w in V3W])) if a == "v3w" else float(np.median(col(a, f)))
print("median vehicle-seconds by road group")
for nm, roads in (("1", ("1",)), ("2", ("2",)), ("3a", ("3a",)), ("3", ("3",)), ("4a", ("4a",)), ("4+5", ("4", "5")), ("ramp1", ("ramp1",)), ("ramp2", ("ramp2",)),
                  ("pend_main", ("pending_main",)), ("pend_r1", ("pending_ramp",)), ("pend_r2", ("pending_ramp2",))):
    print("  ", nm.ljust(10), " ".join(f"{a} {med(a, vs(*roads)):9.0f}" for a in arms))
print("C-D5 edges (positive = v3w lower), 97.5 %")
for nm, f in (("veh-s on 4a", vs("4a")), ("veh-s on ramp2", vs("ramp2")), ("veh-s on 3", vs("3")), ("veh-s on 1", vs("1")),
              ("TTC on 4a per veh-s on 4a", lambda r: tt("4a")(r) / max(vs("4a")(r), 1.0)),
              ("TTC m2 per veh-s on 4a+ramp2", lambda r: tt("4a", "ramp2")(r) / max(vs("4a", "ramp2")(r), 1.0)),
              ("TTC m1 per veh-s on 3a+ramp1", lambda r: tt("3a", "ramp1")(r) / max(vs("3a", "ramp1")(r), 1.0)),
              ("TTC on 4a (raw)", tt("4a"))):
    print("  ", nm.ljust(30), " | ".join(f"{a} {fm(edge(a, f))}" for a in ("lr400_16_1", "p333", "MPC-F", "grid_lr400_13_1")), flush=True)
