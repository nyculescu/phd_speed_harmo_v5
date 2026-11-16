import json, numpy as np
keys = None; es, es2, h2 = [], [], np.zeros(10); n = 0
with open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl") as f:
    for line in f:
        if '"name": "E30|nc"' not in line:
            continue
        r = json.loads(line); n += 1
        if keys is None:
            keys = sorted(k for k in r if any(s in k.lower() for s in ("merge", "stop", "lag", "gap", "human", "hdv")))
        es.append(r["end_stop"]); es2.append(r["end_stop2"]); h2 += np.array(r["m_mergepos_m2"], float)
print("nc rows", n, "merge/stop/gap keys:", keys)
print("end_stop mean", round(np.mean(es), 1), "end_stop2 mean", round(np.mean(es2), 1))
print("m2 pooled share per tenth", np.round(h2 / h2.sum(), 3).tolist())
