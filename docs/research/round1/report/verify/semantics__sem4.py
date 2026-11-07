"""T1/T2 at the code's level (1.25, 98.75) and at a true two-sided 98.75 % level (0.625, 99.375); aggregates only."""
import json, sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
from common1 import load, OPPONENTS, LEARNERS, PRIMARY
import decide1 as dc
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
w = [f"w{i}" for i in range(LEARNERS)]; d = [f"d{i}" for i in range(LEARNERS)]
for pct in ((1.25, 98.75), (0.625, 99.375)):
    for c in PRIMARY:
        b = dc.better(T, c, w, d, pct)
        t = dc.tuned(T, c, OPPONENTS, w, pct)
        print(pct, c, "T1", b["better"], [round(x, 2) for x in b["delay_vs_incumbent"]], "| T2 tuned", t["tuned"], "won", t["won"], "blocked", t["blocked"])
