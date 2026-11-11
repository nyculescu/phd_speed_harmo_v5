"""Screen F's KILL rule applied to the recorded maps (read6_v23.json), 97.5 % intervals (ci_m). EXPLORATORY re-reading of recorded fields."""
import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
for cell, M in (("TRUCK", J["cells"]["TRUCK"]["map"]), ("S", J["S"]["map"])):
    print("\n##", cell, "opponents:", len(M))
    kills, excl = [], []
    for o, e in sorted(M.items(), key=lambda t: t[1]["cf"]["effect"]):
        d, c = e["delay"], e["cf"]
        counted = not (d["ci_m"][0] > 2.0)      # opponent's delay shown worse than v3w's by more than 2 %
        kill = counted and (c["effect"] < 10.0 or c["ci_m"][0] <= 0.0)
        if not counted: excl.append(o)
        if kill: kills.append(o)
        if kill or c["effect"] < 16 or not counted:
            print("  %-18s delay %+.2f [%+.2f, %+.2f] | cf %+.2f [%+.2f, %+.2f] | counted %s | KILL %s" % (o, d["effect"], *d["ci_m"], c["effect"], *c["ci_m"], counted, kill))
    print("  excluded by the delay filter:", excl)
    print("  KILL fires against:", kills)
    ni = {m: [o for o, e in M.items() if e["delay"]["ci_m"][0] <= -m] for m in (1.0, 2.0, 3.0, 5.0)}
    print("  v3w delay non-inferiority NOT shown (97.5 % lower bound <= -margin):", {m: v for m, v in ni.items()})
    print("  v3w shown worse on delay (upper bound < 0):", [o for o, e in M.items() if e["delay"]["ci_m"][1] < 0])
