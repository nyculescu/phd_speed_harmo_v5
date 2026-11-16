"""Named fields of read6_v23.json only (no raw dump)."""
import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
print("top keys:", list(J))
C = J["cells"]["TRUCK"]
print("cell keys:", list(C))
m = C["map"]
print("map opp keys sample:", list(m)[:30])
e = m["3E-C_TRUCK"]
print("measures for 3E-C_TRUCK:", list(e))
f = lambda d: ("%+.2f [%+.2f, %+.2f] (95) / [%+.2f, %+.2f] (m)" % (d["effect"], *d["ci95"], *d["ci_m"])) if isinstance(d, dict) and "effect" in d and d.get("ci95") else str(d)[:200]
for opp in ("3E-C_TRUCK", "p333", "os0_10_10"):
    print("\n==", opp)
    for k, v in m[opp].items():
        print("  %-22s %s" % (k, f(v)))
for k in ("no_control", "overfit_vs_p333", "provenance"):
    v = C.get(k) or J.get(k)
    if v is None: print(k, "absent"); continue
    print("\n", k, "keys:", list(v)[:40])
o = C.get("overfit_vs_p333") or {}
for a in ("3E-C_TRUCK", "3E-D_TRUCK", "3e"):
    if a in o: print("overfit_vs_p333", a, {kk: [round(x, 2) for x in vv] for kk, vv in o[a].items()})
