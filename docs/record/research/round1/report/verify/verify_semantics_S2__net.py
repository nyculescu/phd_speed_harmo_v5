import sys, numpy as np
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1"); sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3")
from common1 import load, val, Q
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
d = [abs(val(r, "ttc_net") - val(r, "ttc3")) for (n, q), R in T.items() if n.startswith("X") for r in R.values()]
print("rows", len(d), "max |ttc_net - ttc3|", max(d))
