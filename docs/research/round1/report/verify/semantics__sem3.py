import json
import numpy as np
B = [json.loads(x) for x in open("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/band.jsonl")]
for q in (4500.0, 5000.0, 5250.0, 5500.0, 6000.0):
    P = {r["seed"]: r for r in B if r["name"] == "B|p333" and r["q"] == q}
    O = {r["seed"]: r for r in B if r["name"] == "B|os1_15_10" and r["q"] == q}
    N = {r["seed"]: r for r in B if r["name"] == "B|nc" and r["q"] == q}
    same = sum(P[s]["ttc_net"] == O[s]["ttc_net"] and P[s]["all_delay"] == O[s]["all_delay"] for s in P)
    ref = np.median([N[s]["ttc_net"] for s in N])
    dp = sorted(-(P[s]["ttc_net"] - N[s]["ttc_net"]) / ref * 100 for s in P)
    do = sorted(-(O[s]["ttc_net"] - N[s]["ttc_net"]) / ref * 100 for s in O)
    print(q, "seeds where p333 == os1_15_10 (ttc and delay):", same, "of", len(P), "| median paired p333", round(float(np.median(dp)), 1), "os1", round(float(np.median(do)), 1))
