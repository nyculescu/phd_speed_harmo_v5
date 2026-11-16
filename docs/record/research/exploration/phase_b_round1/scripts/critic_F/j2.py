import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
C = J["cells"]["TRUCK"]
R = C["map_report_only"]
print("map_report_only type", type(R).__name__, "keys:", list(R)[:30])
def f(d):
    if isinstance(d, dict) and "effect" in d:
        s = "%+.2f" % d["effect"] if d["effect"] is not None else "None"
        for k in ("ci95", "ci_m"):
            if d.get(k): s += " %s[%+.2f, %+.2f]" % (k, *d[k])
        return s
    return str(d)[:160]
for opp in ("3E-C_TRUCK", "p333", "os0_10_10", "nc"):
    e = R.get(opp)
    if e is None: print(opp, "absent"); continue
    print("\n==", opp, "(positive = v3w better)")
    for k, v in e.items():
        if any(k.startswith(p) for p in ("ttc", "sev", "gap25", "b45", "b3", "events", "robust", "collisions", "alks_full", "cf", "contact", "delay", "alks_past")):
            print("  %-24s %s" % (k, f(v)))
print("\nplateau:", json.dumps(J["provenance"]["plateau"])[:600])
print("pct:", C["pct"], "| m:", J["m"])
print("S.map 3E-C_TRUCK:", {k: f(v) for k, v in J["S"]["map"].get("3E-C_TRUCK", {}).items() if k in ("delay", "cf")})
print("S keys:", list(J["S"]))
