import sys
import numpy as np
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3")
from common1 import load, Q, RULE, LEARNERS
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
for cell in ("X2",):
    for name in [RULE, "p333", "nc", "w0", "w2", "d0"]:
        R = T[(f"{cell}|{name}", Q)]
        L = {len(r["v20_min"]) for r in R.values()}
        V = np.array([r["v20_min"][:26] for r in R.values()])
        F = np.array([r["flow_min"][:26] for r in R.values()])
        mins = list(range(5, 31))
        print(name, "lens", L)
        print("  v20 (lane 2_0 m/s) median by minute start(s):", " ".join(f"{m*60}:{x:.0f}" for m, x in zip(mins, np.median(V, 0))))
        print("  flow/min median:", " ".join(f"{m*60}:{x:.0f}" for m, x in zip(mins, np.median(F, 0))))
