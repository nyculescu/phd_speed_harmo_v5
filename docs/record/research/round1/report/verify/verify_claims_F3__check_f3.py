import sys
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
from common1 import load, arm_mean, effect, med, LEARNERS, Q, check_rows, SEEDS_TEST
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
check_rows(T, len(SEEDS_TEST))
for c in ("X1", "X2"):
    nc = T[(f"{c}|nc", Q)]
    arm = arm_mean(T, [f"{c}|w{i}" for i in range(LEARNERS)], Q)
    print(c, "nc medians", {k: round(med(nc, k), 1) for k in ("ttc_net", "all_delay", "b3_step", "b7_step", "sev3")})
    print(c, "v3w arm medians", {k: round(med(arm, k), 1) for k in ("ttc_net", "all_delay", "b3_step", "b7_step", "sev3")})
    for pct, lab in (((2.5, 97.5), "95"), ((1.25, 98.75), "98.75")):
        print(c, "arm vs nc", lab, {k: effect(arm, nc, k, -1, pct) for k in ("ttc_net", "all_delay", "b3_step", "b7_step", "sev3")})
    for i in range(LEARNERS):
        L = T[(f"{c}|w{i}", Q)]
        print(c, f"w{i} vs nc 98.75", {k: effect(L, nc, k, -1, (1.25, 98.75)) for k in ("ttc_net", "all_delay", "b3_step", "b7_step")})
