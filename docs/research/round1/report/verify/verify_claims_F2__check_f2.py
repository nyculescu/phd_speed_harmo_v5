"""F2: the test's CI level. Recompute T1/T2 at (1.25, 98.75) and at (0.625, 99.375); aggregates only."""
import json
import sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
from common1 import LEARNERS, OPPONENTS, PRIMARY, load, check_rows, SEEDS_TEST
import decide1 as dc

O = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
T = load(O + "/test/test.jsonl")
check_rows(T, len(SEEDS_TEST))
v = json.load(open(O + "/val/validation.json"))
print("finalists", v["finalists"], "bonferroni(m)", dc.bonferroni(len(v["finalists"]) * len(PRIMARY)))
stored = json.load(open(O + "/test/test_result.json"))
print("stored pct", stored["pct"])
w = [f"w{i}" for i in range(LEARNERS)]
d = [f"d{i}" for i in range(LEARNERS)]
for pct in [(1.25, 98.75), (0.625, 99.375)]:
    two_sided = 100 - 2 * pct[0]
    for c in PRIMARY:
        b = dc.better(T, c, w, d, pct)
        t2 = dc.tuned(T, c, OPPONENTS, w, pct)
        t2i = dc.tuned(T, c, OPPONENTS, d, pct)
        print(f"pct={pct} two-sided={two_sided}% {c} T1 delay={tuple(round(x, 2) for x in b['delay_vs_incumbent'])} "
              f"ttc={tuple(round(x, 2) for x in b['ttc_vs_incumbent'])} better={b['better']} | T2 v3w {t2['tuned']}/5 won={t2['won']} "
              f"counts={t2['counts']} | inc {t2i['tuned']}/5")
st = stored["finalists"]["v3w"]
for c in PRIMARY:
    print("stored", c, "T1", [round(x, 2) for x in st[c]["T1"]["delay_vs_incumbent"]], [round(x, 2) for x in st[c]["T1"]["ttc_vs_incumbent"]],
          "T2", st[c]["T2"]["tuned"], "inc", st[c]["T2_incumbent_chosen"]["tuned"])
