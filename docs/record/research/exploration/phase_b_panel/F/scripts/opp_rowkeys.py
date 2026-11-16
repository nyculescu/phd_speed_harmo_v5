import json
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
seen = {}
with open(ROWS) as f:
    for i, line in enumerate(f):
        r = json.loads(line)
        nm = r["name"]
        if nm in ("TRUCK|p333", "TRUCK|nc", "TRUCK|w0u250") and nm not in seen:
            seen[nm] = r
        if len(seen) == 3: break
r = seen["TRUCK|p333"]
ks = sorted(r.keys())
print(len(ks), "keys")
import re
groups = {}
for k in ks:
    g = re.sub(r"[0-9]+(\.[0-9]+)?$", "#", k)
    g = re.sub(r"_(car|alks|truck|hdv)$", "_<cls>", g)
    groups.setdefault(g, []).append(k)
print("; ".join(f"{g}({len(v)})" if len(v) > 1 else g for g, v in groups.items()))
for nm, r in seen.items():
    print(nm, {k: (r[k] if not isinstance(r[k], (list, dict)) else (type(r[k]).__name__, len(r[k]))) for k in ks if k.startswith(("tau", "lv_", "gap_", "hw", "thw"))})
