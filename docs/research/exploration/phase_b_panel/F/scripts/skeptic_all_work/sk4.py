"""EXPLORATORY placebo: planb.md:424's pooled statistic applied to a pseudo-arm made of 5 RULES (per-seed mean of 5 single runs)
against a sixth rule, compared with the mean of the 5 single-rule effects. No learner in it. Stored S6 TRUCK rows; no simulation."""
import itertools
import numpy as np
S = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB"
Z = np.load(f"{S}/critic_F/s6_scalars.npz")
KEYS = list(Z["keys"]); N0 = len(Z["seeds"])
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
r = np.random.default_rng(20261124)
def offset(group, opp, key, s):
    O = col(opp, key)[s]; G = np.array([col(g, key)[s] for g in group]); den = np.median(O)
    return -np.median(G.mean(0) - O) / den * 100 - np.mean([-np.median(g - O) / den * 100 for g in G])
SETS = {"all_delay": (["p333", "grid_os1_10_10", "os1_15_10", "3E-D_TRUCK", "lr1000_16_2", "os0_10_10", "grid_lr400_13_1", "lr400_13_2"]),
        "ttc_net": (["os0_10_10", "lr400_16_1", "3ex2", "grid_lr400_13_1", "os1_15_10", "p333", "MPC-F", "grid_os1_10_10"])}
for key, pool in SETS.items():
    offs = []
    for opp in pool:
        rest = [x for x in pool if x != opp]
        for group in itertools.combinations(rest, 5):
            offs.append(offset(group, opp, key, np.arange(N0)))
    offs = np.array(offs)
    print("%-9s pseudo-arms of 5 rules against a sixth, %d combinations: offset (pooled minus mean of singles) median %+.2f, 5th-95th percentile %+.2f to %+.2f, share below 0: %.2f"
          % (key, len(offs), np.median(offs), np.percentile(offs, 5), np.percentile(offs, 95), (offs < 0).mean()))
