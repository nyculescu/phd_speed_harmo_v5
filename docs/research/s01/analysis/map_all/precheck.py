import json, numpy as np
from collections import defaultdict
base = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/"
K = ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "collisions", "teleports", "finished_pct")
bad_ttc = 0; n = 0
for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
    T = defaultdict(lambda: defaultdict(list))
    for line in open(base + f):
        r = json.loads(line); n += 1
        if abs(r["ttc_net"] - (r["E30"] + r["out_E30"])) > 1e-6:
            bad_ttc += 1
        g = (r["name"].split("|")[0], r["q"])
        nm = r["name"].split("|")[1]
        if nm[0] in "wtsd" and nm not in ("nc",):
            nm = nm[0] + "*"
        for k in K:
            T[(g, nm)][k].append(float(r.get(k) or 0.0))
    print("==", f)
    for (g, nm), d in sorted(T.items()):
        print(g, nm, " ".join(f"{k}={np.median(v):.4g}" + (f"(zeros {sum(x == 0 for x in v)}/{len(v)})" if k == "b45_step" else "") for k, v in d.items() if k in K[:5]),
              "coll", sum(d["collisions"]), "tele", sum(d["teleports"]), "fin_min", min(d["finished_pct"]))
print("ttc_net != E30+out_E30 rows:", bad_ttc, "of", n)
