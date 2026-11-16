# When do the edge-1 samples happen? m_road_ttc3["1"] by period, per arm (means per run), plus edge 2 for context.
import json, collections
src = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
want = {"E30|w1u500", "E30|w0u250", "E30|p333", "E30|lr400_16_1", "E30|grid_lr400_13_1", "E30|nc"}
acc = collections.defaultdict(lambda: collections.defaultdict(float)); n = collections.Counter(); spec = None
with open(src) as f:
    for line in f:
        if '"name": "E30|' not in line[:40]: pass
        r = json.loads(line)
        if r["name"] not in want: continue
        if spec is None: spec = (r.get("cell_spec"), r.get("pert_log"))
        n[r["name"]] += 1
        for road in ("1", "2"):
            for per, v in r.get("m_road_ttc3", {}).get(road, {}).items(): acc[r["name"]][(road, per)] += v
print("cell_spec, pert_log of one row:", json.dumps(spec)[:700])
for a in sorted(want):
    print(a, {f"{k[0]}:{k[1]}": round(v / n[a], 1) for k, v in sorted(acc[a].items())})
