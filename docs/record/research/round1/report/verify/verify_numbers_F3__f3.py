import sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
from common1 import LEARNERS, OPPONENTS, PRIMARY, Q, arm_mean, load, med, raw, collisions
import decide1 as dc
d3 = dc.d3
P95 = (2.5, 97.5)
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
for c in PRIMARY:
    A = lambda n: T[(f"{c}|{n}", Q)]
    arm = arm_mean(T, [f"{c}|w{i}" for i in range(LEARNERS)], Q)
    dopp = OPPONENTS["cells"][c]["delay_opponent"]
    print(c, "delay opp", dopp, "med delay", round(med(A(dopp), "all_delay")), "p333 med", round(med(A("p333"), "all_delay")), "arm med", round(med(arm, "all_delay")), "n seeds", len(arm))
    for ref in ("p333", dopp, "os1_15_10"):
        e = raw(arm, A(ref), "all_delay", pct=P95)
        e2 = raw(arm, A(ref), "all_delay")  # 97.5 two-sided default (1.25,98.75)
        print("  arm vs", ref, "95%", [round(x, 2) for x in e], "98.75%", [round(x, 2) for x in e2])
    dop = min((dopp, "p333"), key=lambda r: med(A(r), "all_delay"))
    print("  reading opponent", dop)
    for i in range(LEARNERS):
        P = A(f"w{i}")
        d = raw(P, A(dop), "all_delay")
        dd = raw(P, A(dopp), "all_delay")
        print(f"  w{i} vs {dop} delay(98.75)", [round(x, 2) for x in d], "clears", d3.delay_clears(P, A(dop)), f"| vs {dopp}", [round(x, 2) for x in dd],
              "flow", round(raw(P, A(dop), "passed", 1)[0], 2), "ttc", round(raw(P, A(dop), "ttc_net")[0], 1), "b3", round(raw(P, A(dop), "b3_step")[0], 1))
