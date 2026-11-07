import sys
sys.dont_write_bytecode = True
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1"
sys.path.insert(0, R)
import common1 as c1
import decide1 as dc
OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl"
T = c1.load(OUT)
c1.check_rows(T, len(c1.SEEDS_TEST))
w = [f"w{i}" for i in range(5)]
d = [f"d{i}" for i in range(5)]
print("bonferroni(2) =", dc.bonferroni(2), "coverage %", dc.bonferroni(2)[1] - dc.bonferroni(2)[0])
for pct in [(1.25, 98.75), (0.625, 99.375), (2.5, 97.5)]:
    print("pct", pct, "two-sided coverage", pct[1] - pct[0])
    for c in c1.PRIMARY:
        b = dc.better(T, c, w, d, pct)
        r = lambda t: tuple(round(x, 2) for x in t)
        t2 = dc.tuned(T, c, c1.OPPONENTS, w, pct)
        t2i = dc.tuned(T, c, c1.OPPONENTS, d, pct)
        print(" ", c, "T1 delay", r(b["delay_vs_incumbent"]), "ttc", r(b["ttc_vs_incumbent"]), "better", b["better"], "| T2 v3w", t2["tuned"], "counts", t2["counts"], "| T2 inc", t2i["tuned"])
