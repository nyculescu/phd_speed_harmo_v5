import json, collections
import numpy as np
R = json.load(open("runs.json"))
c = collections.Counter((r["L"], r["arm"]) for r in R)
print("cells", sorted(c.items()))
seeds = collections.defaultdict(set)
for r in R:
    seeds[(r["L"], r["arm"])].add(r["seed"])
ss = set(range(7492000, 7492480))
print("all seed sets complete:", all(s == ss for s in seeds.values()), "dupes:", sum(c.values()) - sum(len(s) for s in seeds.values()))
print("cell field == L:", all(r["cell"] == r["L"] for r in R))
print("learner field per arm:", sorted({(r["arm"], r["learner"]) for r in R}))
print("road groups sum == ttc_net:", sum(r["road_sum"] != r["ttc_net"] for r in R), "mismatches; m_ttc3_all != ttc_net:", sum(r["m_ttc3_all"] != r["ttc_net"] for r in R))
for L in ("L300", "L600"):
    sub = [r for r in R if r["L"] == L]
    print(L, "vv_m_time present:", sum(r["vv_m_time"] is not None for r in sub), "whole==ttc_net:", sum(r["vv_m_whole"] == r["ttc_net"] for r in sub if r["vv_m_whole"] is not None),
          "half==ttc_half:", sum(r["vv_m_half"] == r["ttc_half"] for r in sub if r["vv_m_half"] is not None),
          "main present:", sum(r["main"] is not None for r in sub), "len3a:", sorted({r["len3a"] for r in sub}), "len4a:", sorted({r["len4a"] for r in sub}),
          "collisions:", sum(r["collisions"] for r in sub))
    print("  main <= ttc_net:", all(r["main"] <= r["ttc_net"] for r in sub), " m_time vs step*0.1 max abs diff:", max(abs(r["vv_m_time"] - 0.1 * r["vv_m_step"]) for r in sub if r["vv_m_time"] is not None) if any(r["vv_m_time"] is not None for r in sub) else None)
