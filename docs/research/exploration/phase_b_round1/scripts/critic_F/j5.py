import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
L = J["cells"]["TRUCK"]["location"]
for a in ("v3w", "3E-C_TRUCK", "p333", "nc"):
    d = {k: v for k, v in L[a].items() if k.startswith("cf|")}
    tot = sum(v for v in d.values() if isinstance(v, (int, float)))
    print(a, "sum of cf location medians %.1f |" % tot, ", ".join("%s=%.1f" % (k[3:], v) for k, v in d.items() if v))
    other = [k for k in L[a] if not k.startswith(("cf|", "brk|"))]
    if a == "v3w": print("  other keys:", other[:20])
