"""EXPLORATORY, read-only: key names and shapes of one stored S6 row and of the band and S1 rows. No values printed beyond names, shapes and config scalars."""
import json, collections
ROWS = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
for line in open(ROWS):
    if '"name": "S|p333"' in line:
        r = json.loads(line)
        break
def shape(v):
    if isinstance(v, dict):
        return "dict(%d): %s" % (len(v), list(v)[:8])
    if isinstance(v, list):
        return "list(%d)" % len(v)
    return type(v).__name__
for k in sorted(r):
    if k.startswith("m_") or k in ("lv", "cfg", "flow_min", "v20_min", "N", "steps"):
        print(k, shape(r[k]))
print("m_minute keys:", list(r["m_minute"])[:40])
print("cfg:", json.dumps(r["cfg"])[:600])
print("N", r["N"], "all_delay", r["all_delay"])
for p in ("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl", "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_s1.jsonl"):
    c = collections.Counter(); pert = collections.Counter(); keys = None
    for line in open(p):
        r = json.loads(line)
        nm = str(r["name"])
        c[(r.get("q"), nm.split("|")[0] if "|" in nm else "-")] += 1
        cf = r.get("cfg", {})
        pert[json.dumps(cf.get("perturb"))[:80]] += 1
        keys = keys or sorted(k for k in r if k.startswith("m_"))[:60]
    print(p.split("/")[-1], "rows by (q, cell):", dict(sorted(c.items(), key=str)))
    print("  perturb:", dict(pert))
    print("  has m_road_vs:", "m_road_vs" in keys, "m_minute:", "m_minute" in keys)
