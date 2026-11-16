import json
J = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json"))
T = J["cells"]["TRUCK"]
def keys(d, n=60): return list(d.keys())[:n] if isinstance(d, dict) else type(d).__name__
for k in ("map", "location", "pr28", "map_report_only", "no_control", "overfit_vs_p333", "comparisons", "closest", "gate"):
    v = T[k]
    print(k, "->", keys(v))
    if isinstance(v, dict):
        k0 = list(v.keys())[0]
        print("   ", k0, "->", keys(v[k0]) if isinstance(v[k0], dict) else str(v[k0])[:300])
        if isinstance(v[k0], dict):
            k1 = list(v[k0].keys())[0]
            print("      ", k1, "->", str(v[k0][k1])[:400])
print("S ->", keys(J["S"]))
for k in J["S"]:
    v = J["S"][k]
    print("  S.", k, "->", keys(v) if isinstance(v, dict) else str(v)[:200])
print("space_time ->", keys(J["space_time"]))
print("pr28:", json.dumps(T["pr28"])[:1500])
