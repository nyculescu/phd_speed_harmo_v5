import json
from collections import defaultdict
import numpy as np
OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
opp = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/opponents.json"))
print("opponent rules:", len(opp["ctrl"]), sorted(opp["ctrl"]))
print("cells forms:", {c: opp["cells"][c]["forms"] for c in opp["cells"]})
T = [json.loads(x) for x in open(f"{OUT}/test/test.jsonl")]
for cell in ("X1", "X2"):
    for pre in ("w", "d"):
        W = [r for r in T if r["name"] in [f"{cell}|{pre}{i}" for i in range(5)]]
        print(cell, pre, "alks_full_moving total", sum(r.get("alks_full_moving", 0) for r in W), "runs", len(W),
              "b7_step median per run", round(float(np.median([r.get("b7_step", 0) for r in W])), 2))
    nc = [r for r in T if r["name"] == f"{cell}|nc"]
    print(cell, "nc all_delay median", round(float(np.median([r["all_delay"] for r in nc]))), "N median", round(float(np.median([r["N"] for r in nc]))),
          "dist_step/27.78 median", round(float(np.median([r["dist_step"] / (100 / 3.6) for r in nc]))), "mean per-vehicle delay (finished) median", round(float(np.median([r["delay"] for r in nc])), 1))
