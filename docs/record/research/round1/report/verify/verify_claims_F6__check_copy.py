import sys, json
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
from common1 import OPPONENTS, Q, load, med, raw, collisions, arm_mean, paired_median
import decide1 as dc
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
print("ctrl names:", len(OPPONENTS["ctrl"]), sorted(OPPONENTS["ctrl"]))
for cell in ("X1", "X2"):
    print("cell", cell, "forms:", OPPONENTS["cells"][cell]["forms"], "delay_opp", OPPONENTS["cells"][cell].get("delay_opponent"))
print("copy cfg:", json.dumps(OPPONENTS["ctrl"]["copy"])[:300])
pct = (1.25, 98.75)
for cell in ("X1", "X2"):
    A = lambda n: T[(f"{cell}|{n}", Q)]
    print(f"== {cell}: n copy seeds {len(A('copy'))}")
    for n in ("copy", "p333", "os1_15_10", "nc"):
        print(f"  {n}: med ttc_net {med(A(n),'ttc_net'):.1f} med all_delay {med(A(n),'all_delay'):.1f} coll {collisions(A(n))}")
    print("  copy vs p333 delay (95):", [round(x,2) for x in raw(A("copy"), A("p333"), "all_delay", pct=(2.5,97.5))])
    print("  copy vs p333 delay (98.75):", [round(x,2) for x in raw(A("copy"), A("p333"), "all_delay", pct=pct)])
    print("  copy vs p333 ttc (95):", [round(x,2) for x in raw(A("copy"), A("p333"), "ttc_net", pct=(2.5,97.5))])
    print("  copy vs os1 ttc (95):", [round(x,2) for x in raw(A("copy"), A("os1_15_10"), "ttc_net", pct=(2.5,97.5))])
    print("  copy vs os1 delay (95):", [round(x,2) for x in raw(A("copy"), A("os1_15_10"), "all_delay", pct=(2.5,97.5))])
    for pre in ("w", "d"):
        for i in range(5):
            P = A(f"{pre}{i}")
            f = dc.fails(P, A("copy"), 10.0, pct)
            t = raw(P, A("copy"), "ttc_net", pct=pct); d = raw(P, A("copy"), "all_delay", pct=pct)
            print(f"  {pre}{i} vs copy: fails={f} ttc {t[0]:.1f} [{t[1]:.1f},{t[2]:.1f}] delay {d[0]:.1f} [{d[1]:.1f},{d[2]:.1f}] perrun {paired_median(A('copy'),P,'ttc_net'):.0f}")
        K = arm_mean(T, [f"{cell}|{pre}{i}" for i in range(5)])
        t = raw(K, A("copy"), "ttc_net", pct=(2.5,97.5)); d = raw(K, A("copy"), "all_delay", pct=(2.5,97.5))
        print(f"  arm {pre} vs copy (95): ttc {t[0]:.1f} [{t[1]:.1f},{t[2]:.1f}] delay {d[0]:.1f} [{d[1]:.1f},{d[2]:.1f}]")
