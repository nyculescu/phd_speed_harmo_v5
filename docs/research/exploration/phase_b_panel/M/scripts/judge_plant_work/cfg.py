import json, sys, collections
p = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
seen = {}
cells = collections.Counter()
with open(p) as f:
    for i, line in enumerate(f):
        if '"p333"' not in line and '"os0_10_10"' not in line and '"z33133"' not in line and i > 3:
            # cheap prefilter; still count names below for the first rows only
            pass
        r = json.loads(line)
        k = (r.get("cell"), r.get("arm") or r.get("name"))
        cells[k] += 1
        if k not in seen and (str(k[1]).endswith("p333") or "os0_10_10" in str(k[1]) or "z33133" in str(k[1])):
            c = r.get("cfg", {})
            seen[k] = {"ctrl": c.get("ctrl"), "plant_keys": sorted(x for x in c if x != "ctrl")[:40], "tau_rise": c.get("tau_rise"), "q": r.get("q"), "perturb": c.get("perturb")}
        if i == 0:
            print("row keys sample:", [x for x in r if not x.startswith(("m_", "lv_", "n_", "nv_"))][:60])
for k, v in seen.items():
    print(k, json.dumps(v)[:600])
names = sorted({k[1] for k in cells})
print(len(names), "arm names; cells:", sorted({str(k[0]) for k in cells}))
print("S arms:", sorted(k[1] for k in cells if str(k[0]) == "S" or str(k[1]).startswith("S|"))[:80])
print(collections.Counter(cells.values()).most_common(5))
