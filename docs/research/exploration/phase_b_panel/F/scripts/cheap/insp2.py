import json
J = json.load(open("/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json"))
T = J["cells"]["TRUCK"]
for k, v in T.items():
    t = type(v).__name__
    n = len(v) if hasattr(v, "__len__") and not isinstance(v, str) else v if not isinstance(v, str) else v[:80]
    print(k, t, n)
m = T["map"]
print(list(m)[:30])
o = m["3E-C_TRUCK"]; print({k: (v if not isinstance(v, dict) else list(v)) for k, v in o.items()})
mr = T["map_report_only"]; print(list(mr)[:30])
o = mr["3E-C_TRUCK"]; print(list(o))
print(J["must_carry"][:1200])
print(J["provenance"]["plateau"])
