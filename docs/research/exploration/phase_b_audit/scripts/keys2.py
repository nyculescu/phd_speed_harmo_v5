import json, sys
f = sys.argv[1]
with open(f) as fh:
    r = json.loads(fh.readline())
print(sorted(k for k in r if k.startswith("m_")))
print("non-m extra:", sorted(k for k in r if not k.startswith(("m_", "lv_", "ttc", "sev", "n_", "nv_"))))
print("m_minute keys", sorted(r["m_minute"]) if "m_minute" in r else None)
for k in ("m_road_vs", "m_road_dist"):
    if k in r:
        print(k, {g: sorted(v) for g, v in r[k].items()})
print("pert_log" in r, r.get("cell"), r.get("cell_spec"), r["name"], r["q"], r["steps"], len(r["flow_min"]))
print({k: v for k, v in r["cfg"].items() if k != "ctrl"})
print(sorted(r["cfg"]["ctrl"]))
