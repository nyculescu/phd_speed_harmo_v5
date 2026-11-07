import json, statistics as st, collections, sys
base = "/home/catalin/work/phd/v5b1_runs/round1_remote/out/"
for f in ("test/test.jsonl", "test/band.jsonl", "val/validation.jsonl"):
    rows = [json.loads(l) for l in open(base + f) if l.strip()]
    steps = collections.Counter(r.get("steps") for r in rows)
    keys = set(rows[0].keys())
    print(f, "rows", len(rows), "steps values", dict(steps), "has passed", "passed" in keys, "has arrived", "arrived" in keys)
    # medians of passed for selected names at q=5300
    g = collections.defaultdict(list)
    for r in rows:
        g[(r.get("name"), r.get("q"))].append(r)
    for (n, q), R in sorted(g.items(), key=lambda x: (str(x[0][0]), x[0][1] or 0)):
        if f.startswith("test/test") and any(n.endswith(s) for s in ("|nc", "|p333", "|w0", "|d0", "|os1_15_10")):
            p = st.median(r["passed"] for r in R); a = st.median(r["arrived"] for r in R)
            print("  ", n, q, "n", len(R), "median passed", p, "-> veh/h", round(p * 3600 / 1500), "median arrived", a, "-> veh/h", round(a * 3600 / 1500))
        if f.startswith("test/band") and n in ("B|nc",):
            p = st.median(r["passed"] for r in R)
            print("  ", n, q, "n", len(R), "median passed", p, "-> veh/h", round(p * 3600 / 1500), "ratio to q", round(p * 3600 / 1500 / q, 3))
