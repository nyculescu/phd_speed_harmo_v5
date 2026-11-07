"""F4: severe-conflict gate, and v3w against no control on sev3, b3, b7 (aggregates only)."""
import json
import sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
from common1 import OPPONENTS, LEARNERS, Q, arm_mean, load, med, paired_median, raw, effect, check_rows

OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
T = load(OUT + "/test/test.jsonl")
check_rows(T, 40)
P95 = (2.5, 97.5)
r = json.load(open(OUT + "/test/test_result.json"))
for c in ("X1", "X2"):
    A = lambda n: T[(f"{c}|{n}", Q)]
    p333 = A("p333")
    names = list(dict.fromkeys(["p333", *OPPONENTS["cells"][c]["forms"].values()]))
    counts = [n for n in names if raw(A(n), p333, "all_delay")[0] >= -2.0]
    print(c, "counts", counts, "beside.severe_ok", r["finalists"]["v3w"][c]["beside"]["severe_ok"], "T2 tuned", r["finalists"]["v3w"][c]["T2"]["tuned"])
    for i in range(LEARNERS):
        P = A(f"w{i}")
        print(" w%d sev3 paired med vs counts" % i, {n: paired_median(P, A(n), "sev3") for n in counts},
              "vs nc", paired_median(P, A("nc"), "sev3"), "b7 vs nc", paired_median(P, A("nc"), "b7_step"))
    W = arm_mean(T, [f"{c}|w{i}" for i in range(LEARNERS)], Q)
    nc = A("nc")
    for k in ("sev3", "b3_step", "b7_step", "ttc_net", "all_delay"):
        print(" v3w arm vs nc", k, "eff95", effect(W, nc, k, -1, P95), "med arm", round(med(W, k), 1), "med nc", round(med(nc, k), 1), "paired med", round(paired_median(W, nc, k), 2))
    # per-learner sev3 vs nc at 95 and 98.75
    for i in range(LEARNERS):
        P = A(f"w{i}")
        print(" w%d vs nc sev3 eff95" % i, effect(P, nc, "sev3", -1, P95), "b3", effect(P, nc, "b3_step", -1, P95), "b7", effect(P, nc, "b7_step", -1, P95))
