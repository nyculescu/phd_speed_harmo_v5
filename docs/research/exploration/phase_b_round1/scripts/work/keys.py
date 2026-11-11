import json, sys
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
seen = {}
with open(ROWS) as f:
    for i, line in enumerate(f):
        r = json.loads(line)
        if r["name"] in ("S|p333", "S|nc") and r["name"] not in seen:
            seen[r["name"]] = r
        if len(seen) == 2 or i > 3000:
            break
names = set()
for n, r in seen.items():
    print(n, len(r))
    for k in sorted(r):
        v = r[k]
        t = type(v).__name__
        d = f"len {len(v)}" if isinstance(v, (list, dict, str)) else ""
        print("  ", k, t, d)
    break
