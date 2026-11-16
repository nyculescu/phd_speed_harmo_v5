import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
L = J["cells"]["TRUCK"]["location"]
def show(name, d, depth=0):
    if isinstance(d, dict):
        flat = all(not isinstance(v, (dict, list)) for v in d.values())
        if flat:
            print("  " * depth + name + ": " + ", ".join("%s=%s" % (k, ("%.1f" % v) if isinstance(v, float) else v) for k, v in d.items()))
        else:
            print("  " * depth + name + ":")
            for k, v in d.items(): show(k, v, depth + 1)
    else:
        print("  " * depth + "%s: %s" % (name, str(d)[:200]))
for a in ("v3w", "3E-C_TRUCK", "p333", "nc"):
    if a in L: show(a, L[a])
    else: print(a, "absent from location")
