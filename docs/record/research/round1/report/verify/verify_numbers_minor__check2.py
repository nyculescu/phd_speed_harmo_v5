"""F9 d3 against p333 in X2; F12 arm counts; F11 all counter-table cells unrounded."""
import json, csv
from check import load, arm, med, eff, OUT, v
T = load(f"{OUT}/test/test.jsonl")
Q = 5300.0
for i in range(5):
    print("X2 d%d vs p333 delay (point, 98.75 CI)" % i, eff(T[("X2|d%d" % i, Q)], T[("X2|p333", Q)], "all_delay", pct=(1.25, 98.75)))
opp = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/opponents.json"))
print("opponents.json keys", list(opp.keys()), "ctrl n", len(opp["ctrl"]), sorted(opp["ctrl"]))
rows = list(csv.DictReader(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1/report/test_table.csv")))
for c in ("X1", "X2"):
    names = [r["name"] for r in rows if r["cell"] == c]
    print(c, "test_table rows", len(names))
keys = ("all_delay", "passed", "ttc_net", "sev3", "b3_step", "b7_step", "alks_full_moving")
for c in ("X1", "X2"):
    arms = {"v3w": arm(T, [f"{c}|w{i}" for i in range(5)], Q), "baseline-v3": arm(T, [f"{c}|d{i}" for i in range(5)], Q),
            "p333": T[(f"{c}|p333", Q)], "os1_15_10": T[(f"{c}|os1_15_10", Q)], "nc": T[(f"{c}|nc", Q)]}
    for n, A in arms.items():
        print(c, n, [round(med(A, k), 3) for k in keys], "->", [round(med(A, k)) if k not in ("b7_step",) else round(med(A, k), 1) for k in keys])
