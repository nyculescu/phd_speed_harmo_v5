"""D8: ttc3 by period and road, v3w and os1_15_10 minus nc in X1; per-second rates and shares relative to nc (my addition).
Period lengths from plant_sweep.period(): window 300-1800 s; X1 times 600, 1200; taper 20; dur 120; after 120."""
import numpy as np
from base import *
rows, T = load()
LEN = {"before": 300, "taper": 40, "hold": 200, "after": 240, "rest": 720}
nc = T[("X1", "nc", 5300.0)]
for gname, names in [("v3w", ARMS["v3w"]), ("tail", ARMS["tail"]), ("sw", ARMS["sw"]), ("bv3", ARMS["bv3"]), ("os1_15_10", ["os1_15_10"]), ("p333", ["p333"]), ("3e", ["3e"])]:
    print(gname)
    for p in LEN:
        k = f"ttc3_p_{p}"
        A = arm_series(T, "X1", names, 5300.0, lambda r: g(r, k)); B = {s: g(r, k) for s, r in nc.items()}
        d, n = paired_diff(A, B); e, _ = effect(A, B)
        mB = np.median(list(B.values()))
        print(f"  {p:6s} diff {fmt(d,0)} TTC-s/run; nc med {mB:.0f}; diff/s {d[0]/LEN[p]:+.3f}; effect vs nc {fmt(e,1)} %")
    for rd in ["3", "4a", "ramp2", "rest"]:
        k = f"ttc3_r_{rd}"
        A = arm_series(T, "X1", names, 5300.0, lambda r: g(r, k)); B = {s: g(r, k) for s, r in nc.items()}
        d, n = paired_diff(A, B); e, _ = effect(A, B)
        print(f"  road {rd:6s} diff {fmt(d,0)}; nc med {np.median(list(B.values())):.0f}; effect {fmt(e,1)} %")
# check the period sums to ttc3
mx = 0
for r in rows:
    if r["name"].startswith("X1"):
        mx = max(mx, abs(sum(g(r, f"ttc3_p_{p}") for p in LEN) - g(r, "ttc3")))
print("max |sum of periods - ttc3| in X1:", mx)
# lv by road
for gname, names in [("v3w", ARMS["v3w"]), ("os1_15_10", ["os1_15_10"]), ("p333", ["p333"]), ("3e", ["3e"])]:
    s = []
    for rd in ["r2", "rj2", "4a", "4", "3"]:
        A = arm_series(T, "X1", names, 5300.0, lambda r: g(r, f"lv_sum_{rd}") / max(g(r, f"lv_n_{rd}"), 1))
        B = arm_series(T, "X2", names, 5300.0, lambda r: g(r, f"lv_sum_{rd}") / max(g(r, f"lv_n_{rd}"), 1))
        d, _ = paired_diff(A, B)
        s.append(f"{rd} X1 {np.median(list(A.values())):.2f} (X1-X2 {fmt(d)})")
    print(gname, "; ".join(s))
