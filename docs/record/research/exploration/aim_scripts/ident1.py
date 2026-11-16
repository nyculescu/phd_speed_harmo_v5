"""EXPLORATORY: how far the EPYC replays of the v3w learners are from the stored S6 rows (keys and sizes only)."""
import json, sys, glob
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
rep = {}
for f in glob.glob('/home/catalin/work/phd/v5b1_runs/v505_remote/m2_ident/*rows*.jsonl'):
    for line in open(f):
        r = json.loads(line); c, a = r["name"].split("|", 1)
        if a in L: rep[(r["name"], r["seed"])] = r
want = set(rep)
s6 = {}
for line in open('/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'):
    if '"seed": 748040' not in line and '"seed":748040' not in line: continue
    r = json.loads(line)
    if (r["name"], r["seed"]) in want: s6[(r["name"], r["seed"])] = r
print("replays", len(rep), "matched", len(s6))
KEYS = ["all_delay", "ttc_net", "passed", "b45_step", "fuel_km", "collisions", "m_dec_entropy_mean"]
def flat(v):
    if isinstance(v, (int, float)): return [float(v)]
    if isinstance(v, list): return [x for y in v for x in flat(y)]
    if isinstance(v, dict): return [x for k in sorted(v) for x in flat(v[k])]
    return []
ndiff_traffic = 0
for k in sorted(rep):
    a, b = rep[k], s6.get(k)
    if b is None: continue
    dk = [key for key in a if key in b and key not in ("cfg",) and a[key] != b[key]]
    rel = {}
    for key in KEYS:
        if key in a and key in b and isinstance(a[key], (int, float)) and b[key]:
            rel[key] = (a[key] - b[key]) / abs(b[key])
    traffic = [key for key in dk if not key.startswith("m_dec") and not key.startswith("lv")]
    ndiff_traffic += bool(traffic)
    if len(dk) > 1 or traffic:
        print(k, "keys differing:", len(dk), "non-decision keys:", traffic[:6], {x: "%.2e" % y for x, y in rel.items() if y})
    else:
        ent = rel.get("m_dec_entropy_mean", 0)
        print(k, "only", dk, "rel %.1e" % ent)
print("replays with any traffic key different:", ndiff_traffic)
