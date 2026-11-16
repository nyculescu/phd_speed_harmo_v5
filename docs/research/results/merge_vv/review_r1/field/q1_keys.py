import sys, json, collections
names = collections.Counter(); first = None
with open(sys.argv[1]) as f:
    for i, line in enumerate(f):
        r = json.loads(line)
        names[r["name"]] += 1
        if first is None:
            first = r
print(len(names), "arm names:", dict(names))
ks = sorted(first)
print(len(ks), "keys")
print([k for k in ks if any(s in k for s in ("merge", "end_stop", "pass_", "halt", "m_", "n_", "nv_", "r2_", "ttc", "accel", "lane"))])
print({k: first[k] for k in ks if k in ("name", "cfg", "q", "seed", "end_stop", "end_stop2", "pass_merging", "m_mergepos_m1", "m_mergepos_m2", "c1_t0")})
