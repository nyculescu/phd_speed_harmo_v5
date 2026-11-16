import json, collections
p = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
n = collections.Counter(); keys = None; ctrl = {}
with open(p) as f:
    for line in f:
        r = json.loads(line)
        n[r["name"]] += 1
        if r["name"].startswith("S|") and r["name"] not in ctrl:
            c = r["cfg"].get("ctrl", {})
            ctrl[r["name"]] = json.dumps({k: v for k, v in c.items() if k not in ("measure",)})[:150]
        if keys is None and r["name"] == "S|p333":
            keys = sorted(k for k in r if not isinstance(r[k], (list, dict)))
S = sorted(k for k in n if k.startswith("S|"))
print(len(S), "arms in S;", sorted(set(n[k] for k in S)), "rows each")
for k in S:
    print(k, ctrl[k])
print("scalar keys with accel/4a/3a/ramp/pend/stuck:", [k for k in keys if any(s in k for s in ("4a", "3a_0", "accel", "ramp", "pend", "stuck", "tau", "lv_"))])
