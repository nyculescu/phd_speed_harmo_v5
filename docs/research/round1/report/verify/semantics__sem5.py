import json
from collections import defaultdict
T = [json.loads(x) for x in open("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")]
R = defaultdict(dict)
for r in T:
    R[r["name"]][r["seed"]] = r
for c in ("X1", "X2"):
    same = 0; n = 0
    for i in range(5):
        for s, a in R[f"{c}|d{i}"].items():
            b = R[f"{c}|f{i}"][s]
            ks = [k for k in a if k not in ("name", "cfg")]
            n += 1
            same += all(a[k] == b.get(k) for k in ks)
    print(c, "f vs d rows identical on every non-config key:", same, "of", n)
    print(c, "baseline-v3 collisions total", sum(r.get("collisions", 0) for i in range(5) for r in R[f"{c}|d{i}"].values()))
    rules = {n.split("|")[1]: sum(r.get("collisions", 0) for r in R[n].values()) for n in R if n.startswith(c + "|") and n.split("|")[1][0] not in "wdf" or n in (f"{c}|z33133",)}
    print(c, "rule/nc collisions", rules)
res = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1/report/test_result.json"))
print("final_vs_chosen", res["final_vs_chosen_incumbent"])
