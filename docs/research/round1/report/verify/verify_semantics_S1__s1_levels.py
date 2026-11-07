"""Re-read T1 and T2 at the stored bounds and at true two-sided 98.75 %; aggregates only."""
import json, sys
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1"
sys.path.insert(0, R + "/docs/research/round1")
sys.path.insert(0, R)
from common1 import LEARNERS, OPPONENTS, PREFIX, PRIMARY, load, check_rows, SEEDS_TEST
import decide1 as dc
O = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
v = json.load(open(O + "/val/validation.json"))
T = load(O + "/test/test.jsonl")
check_rows(T, len(SEEDS_TEST))
stored = json.load(open(O + "/test/test_result.json"))
m = len(v["finalists"]) * len(PRIMARY)
print("finalists", v["finalists"], "m", m, "bonferroni(m)", dc.bonferroni(m), "coverage %", 100 - 2 * dc.bonferroni(m)[0])
for pct in (dc.bonferroni(m), (0.625, 99.375)):
    print("pct", pct, "coverage", round(pct[1] - pct[0], 3))
    for k in v["finalists"]:
        names = [f"{PREFIX[k]}{i}" for i in range(LEARNERS)]
        inc = [f"d{i}" for i in range(LEARNERS)]
        for c in PRIMARY:
            t1 = dc.better(T, c, names, inc, pct)
            t2 = dc.tuned(T, c, OPPONENTS, names, pct)
            t2i = dc.tuned(T, c, OPPONENTS, inc, pct)
            r = lambda x: [round(y, 4) for y in x]
            print(k, c, "T1 delay", r(t1["delay_vs_incumbent"]), "ttc", r(t1["ttc_vs_incumbent"]), "better", t1["better"],
                  "| T2", t2["tuned"], "won", t2["won"], "counts", t2["counts"], "blocked", t2["blocked"], "| inc T2", t2i["tuned"], t2i["blocked"])
            if pct == tuple(stored["pct"]):
                s = stored["finalists"][k][c]
                print("  matches stored:", r(s["T1"]["delay_vs_incumbent"]) == r(t1["delay_vs_incumbent"]), s["T2"]["tuned"] == t2["tuned"])
