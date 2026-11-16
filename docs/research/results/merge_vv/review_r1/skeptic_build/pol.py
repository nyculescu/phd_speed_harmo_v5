import json
for k in range(5):
    c = json.load(open(f"/home/catalin/work/phd/v5b1_runs/baseline_v4/policies/C{k}_config.json"))
    def find(x, p=""):
        if isinstance(x, dict):
            for a, b in x.items():
                if a in ("fix_x", "geom", "accel_len", "accel2_len"): print(k, p + "/" + a, b)
                find(b, p + "/" + a)
    find(c)
# the E30 policy arms: which pt path and cfg
seen = set()
for line in open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"):
    if '"pt"' not in line[:4000]: continue
    r = json.loads(line)
    if r["name"] in seen: continue
    seen.add(r["name"]); print(r["name"], r["cfg"]["ctrl"].get("pt"), {k: v for k, v in r["cfg"].items() if k != "ctrl"})
    if len(seen) == 5: break
# x map at 300 vs 600 (edges 3,4,5 kept, both lanes 594.72), raw built x as _x_base computes it
L3 = {"3a": 294.72, "3": 1194.3, "4a": 294.72, "4": 996.0, "5": 500.0}
for la in (294.72, 594.72):
    L = {**L3, "3a": la, "4a": la}
    b = {"3a": 0.0}; b["3"] = L["3a"]; b["4a"] = b["3"] + L["3"]; b["4"] = b["4a"] + L["4a"]; b["5"] = b["4"] + L["4"]
    print(la, {k: (round(v, 2), round(v + L[k], 2)) for k, v in b.items()})
