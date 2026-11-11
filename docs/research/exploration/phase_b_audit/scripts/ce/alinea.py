import gzip, json
from collections import defaultdict
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/"
T = defaultdict(dict)
for l in gzip.open(R + "phase1/step1_test.jsonl.gz", "rt"):
    r = json.loads(l); T[(r["name"], r["q"])][r["seed"]] = r
for a in ("alinea16", "alinea24"):
    for q in (4600.0, 5300.0):
        if (a, q) not in T: print(a, q, "absent"); continue
        A, B = T[(a, q)], T[("p0", q)]
        same = sum(all(A[s][k] == B[s][k] for k in ("delay", "N", "dist", "passed", "ttc_net")) for s in A)
        print(a, q, "seeds", len(A), "identical to no control on delay, N, dist, passed, ttc_net:", same, "| ctrl", json.dumps(next(iter(A.values()))["cfg"].get("ctrl")))
