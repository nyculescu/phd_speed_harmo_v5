"""EXPLORATORY: K2 (delay non-inferiority, margin 1 %, 97.5 % two-sided lower bound) at 480 seeds when the stated truth is a tie of the
SINGLE learners with each rule, and with the delay-close stored rules the text drops. Stored S6 TRUCK rows; no simulation."""
import numpy as np
S = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB"
Z = np.load(f"{S}/critic_F/s6_scalars.npz")
KEYS = list(Z["keys"]); N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
Ld = np.array([col(l, "all_delay") for l in LEARN]); Pd = Ld.mean(0)
KEPT = ["p333", "os0_10_10", "3E-D_TRUCK"]
DROPPED = ["grid_os1_10_10", "os1_15_10", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2"]
ALL = KEPT + DROPPED
Od = {o: col(o, "all_delay") for o in ALL}
med0 = {o: np.median(Od[o]) for o in ALL}
pool0 = {o: np.median(-(Pd - Od[o])) for o in ALL}                                    # veh-s, positive = v3w less delay
lear0 = {o: np.mean([np.median(-(Ld[i] - Od[o])) for i in range(5)]) for o in ALL}
N, B, ST = 480, 1000, 1500
r = np.random.default_rng(20261123)
TRUTHS = ("stored", "learner tie", "learner 0.5 worse", "learner 1.0 worse", "pooled tie", "pooled 1.0 worse")
lbs = {t: [] for t in TRUTHS}
for _ in range(ST):
    s = r.integers(0, N0, N); bi = r.integers(0, N, (B, N))
    row = {t: [] for t in TRUTHS}
    for o in ALL:
        m = np.median(Od[o][s])
        d = -(Pd[s] - Od[o][s]) / m * 100
        lb = np.percentile(np.median(d[bi], axis=1), 1.25)
        for t in TRUTHS:
            sh = {"stored": 0.0, "learner tie": lear0[o], "learner 0.5 worse": lear0[o] + 0.005 * med0[o], "learner 1.0 worse": lear0[o] + 0.01 * med0[o],
                  "pooled tie": pool0[o], "pooled 1.0 worse": pool0[o] + 0.01 * med0[o]}[t]
            row[t].append(lb - sh / m * 100)
    for t in TRUTHS:
        lbs[t].append(row[t])
print(f"## K2 passes when every lower bound > -1; n = {N}, {ST} studies, B = {B}; v3w's delay shifted by a constant per rule")
print("truth | P(pass) 3 kept stored rules | P(pass) kept + 5 dropped delay-close rules | per rule: " + " ".join(ALL))
for t in TRUTHS:
    a = np.array(lbs[t]) > -1.0
    print("%-18s | %.3f | %.3f | %s" % (t, a[:, :3].all(1).mean(), a.all(1).mean(), " ".join("%.3f" % v for v in a.mean(0))))
