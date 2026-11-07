"""Section 5: the band at 95 %, reading B, and the band blind-spot statements."""
import sys

sys.path.insert(0, sys.path[0])
from lib import OUT, P95, arm, f, med, pmed, stat, load

TB = load(OUT + "/test/band.jsonl")
print("arms", len(TB), "seeds", {len(v) for v in TB.values()}, min(min(v) for v in TB.values()), max(max(v) for v in TB.values()))
LV = (4500.0, 5000.0, 5250.0, 5500.0, 6000.0)
shown = {"v3w": [], "inc": []}
for q in LV:
    nc = TB[("B|nc", q)]
    Wq = arm(TB, [f"B|w{i}" for i in range(5)], q)
    Dq = arm(TB, [f"B|d{i}" for i in range(5)], q)
    out = []
    for lab, X in (("v3w", Wq), ("inc", Dq)):
        t, d = stat(X, nc, "ttc_net", pct=P95), stat(X, nc, "all_delay", pct=P95)
        pr = pmed(nc, X, "ttc_net")
        ben = t[0] >= 10 and t[1] > 0 and pr >= 20
        if q in (5000.0, 5250.0, 5500.0):
            shown[lab].append(ben)
        out.append(f"{lab} ttc {f(t, 2)} delay {f(d, 2)} perrun {pr:.1f} benefit {ben}")
    for r in ("p333", "os1_15_10"):
        out.append(f"{r} ttc {stat(TB[('B|' + r, q)], nc, 'ttc_net', pct=P95)[0]:+.2f}")
    print(q, "nc ttc median", med(nc, "ttc_net"), "|", " | ".join(out))
print("shown v3w", all(shown["v3w"]), shown["v3w"], "inc", all(shown["inc"]), shown["inc"])

print("\nblind spots in the band (single arms and the two policy arms)")
allarms = dict(TB)
for q in LV:
    allarms[("B|v3w arm", q)] = arm(TB, [f"B|w{i}" for i in range(5)], q)
    allarms[("B|d arm", q)] = arm(TB, [f"B|d{i}" for i in range(5)], q)
flag = []
for (n, q), A in sorted(allarms.items()):
    b, s, t, h = med(A, "brake_net"), med(A, "b3_step"), med(A, "ttc_net"), med(A, "ttc_half")
    fb = s >= 50 and abs(b / s - 1) > 0.05
    ft = h >= 50 and abs(t / h - 1) > 0.05
    if fb or ft:
        flag.append((n, q, round(b / s, 4), round(t / h, 4) if h else None, "brake" if fb else "", "ttc" if ft else "", "ttc_half med", h, "ttc_net med", t))
for x in flag:
    print(x)
print("braking-flagged:", sum(1 for x in flag if x[4]), "ttc-flagged:", sum(1 for x in flag if x[5]))
print("braking ratios of flagged:", sorted(x[2] for x in flag if x[4]))
print("v3w arm at 4500 ttc_net median", med(allarms[("B|v3w arm", 4500.0)], "ttc_net"), "w1 4500 ttc_net/ttc_half medians", med(TB[("B|w1", 4500.0)], "ttc_net"), med(TB[("B|w1", 4500.0)], "ttc_half"))
