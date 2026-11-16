# Independent stream: road/period keys, edge-1 by period, slowdown spec, per-arm groups.
import json, collections
src = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
want = {"E30|" + a for a in ("w0u250","w1u500","w2u250","w3u500","w4u500","lr400_16_1","grid_lr400_13_1","p333","nc")}
roads = set(); pers = set(); spec = None
acc = collections.defaultdict(lambda: collections.defaultdict(float)); n = collections.Counter()
rows = {}
with open(src) as f:
    for line in f:
        r = json.loads(line)
        rt = r.get("m_road_ttc3", {})
        roads |= set(rt); [pers.update(v) for v in rt.values()]
        if r["name"] not in want: continue
        if spec is None: spec = {k: r.get(k) for k in ("cell_spec", "pert_log", "cell")}
        n[r["name"]] += 1
        for road, d in rt.items():
            for p, v in d.items(): acc[r["name"]][(road, p)] += v
        rows[(r["name"], r["seed"])] = {road: sum(d.values()) for road, d in rt.items()} | {"tot": r["ttc_net"]}
print("roads", sorted(roads), "periods", sorted(pers))
print("spec", json.dumps(spec)[:900])
for a in sorted(want):
    m = {f"{k[0]}:{k[1]}": round(v / n[a], 1) for k, v in sorted(acc[a].items()) if k[0] in ("1", "2")}
    print(a, n[a], m)
json.dump({f"{a}#{s}": v for (a, s), v in rows.items()}, open("rows9.json", "w"))
