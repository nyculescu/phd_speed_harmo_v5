"""Step 0 (exploratory, read only): C1's E30 rows, v3w (mean of five learners' effects) and the rules against p333 and no control."""
import sys
import numpy as np
sys.path.insert(0, "/home/catalin/work/phd/wt/c1/docs/research/c1")
import read_c1 as rc
R = "/home/catalin/work/phd/v5b1_runs/c1_remote"
T = rc.load([f"{R}/c1_pilot/s6_rows.jsonl", f"{R}/c1_screen/s6_rows.jsonl"])
seeds = list(range(7_490_000, 7_490_960))
idx = np.random.default_rng(rc.read6.RNG).integers(0, len(seeds), (20000, len(seeds)))
keys = ("ttc_net", "ttc_away", "b45_step", "events_ge45", "all_delay")
print("positive = the arm has less than the opponent; [97.5 %]")
for opp in ("p333", "nc", "3E-C_TRUCK"):
    for k in keys:
        x = rc.reading(rc.learner_diffs(T, "E30", opp, k, seeds), idx)
        print(f"v3w vs {opp:10s} {k:12s} {x['pt']:+7.2f} [{x['lo']:+7.2f}, {x['hi']:+7.2f}]")
for a, opp in (("3E-C_TRUCK", "p333"), ("p333", "nc"), ("3E-C_TRUCK", "nc")):
    for k in keys:
        d = rc.diffs(rc.col(T, "E30", a, seeds, k), rc.col(T, "E30", opp, seeds, k))
        lo, hi = rc.ci(np.median(d[idx], axis=1), rc.L975)
        print(f"{a:10s} vs {opp:10s} {k:12s} {np.median(d):+7.2f} [{lo:+7.2f}, {hi:+7.2f}]")
print("medians per run:", {a: {k: round(float(np.median(rc.col(T, 'E30', a, seeds, k))), 1) for k in keys} for a in ("nc", "p333", "3E-C_TRUCK", "w0u250")})
