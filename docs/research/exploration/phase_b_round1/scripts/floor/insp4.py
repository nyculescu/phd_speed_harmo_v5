import numpy as np, json, gzip, collections
z = np.load("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/B__p333__3500__7440900.npz")
for k in z.files: print(k, z[k].shape, z[k].dtype)
c = collections.Counter(); k0 = None
for line in gzip.open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/r2m3/ladder_rows.jsonl.gz", "rt"):
    r = json.loads(line)
    c[(r["name"], r["q"])] += 1
    if k0 is None: k0 = r; print(sorted(r)[:80]); print(json.dumps(r["cfg"])[:300])
print(sorted(c.items()))
# perturbation status in rows_s1
c = collections.Counter()
for line in open("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_s1.jsonl"):
    r = json.loads(line)
    if r["name"] in ("B|nc", "B|p333"): c[(r["name"], r["q"], "none" if not r.get("pert_log") else "pert")] += 1
print(sorted(c.items()))
