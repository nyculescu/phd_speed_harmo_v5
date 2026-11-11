"""EXPLORATORY: skeptic's recomputation for screen F from the stored S6 TRUCK rows (already read for a verdict). No simulation."""
import numpy as np
S = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB"
Z = np.load(f"{S}/critic_F/s6_scalars.npz")
KEYS = list(Z["keys"]); N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
RULES = sorted(f.split("|")[1] for f in Z.files if f.startswith("TRUCK|") and f.split("|")[1] not in LEARN + ["nc"])
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
L = {k: np.array([col(l, k) for l in LEARN]) for k in ("ttc_net", "all_delay")}
P = {k: L[k].mean(0) for k in L}
r0 = np.random.default_rng(20261120)
IDX = r0.integers(0, N0, (20000, N0))
def eff(p, o, lo=1.25, hi=98.75):
    d = -(p - o) / np.median(o) * 100
    b = np.median(d[IDX], axis=1)
    return np.median(d), np.percentile(b, lo), np.percentile(b, hi)
print("rules", len(RULES))
print("## stored, 240 seeds, 97.5 %: delay effect of pooled v3w against each rule, sorted by lower bound; then cf")
rows = []
for o in RULES:
    d = eff(P["all_delay"], col(o, "all_delay")); c = eff(P["ttc_net"], col(o, "ttc_net"))
    pl = [eff(L["all_delay"][i], col(o, "all_delay"))[0] for i in range(5)]
    rows.append((d[1], o, d, c, pl))
for lb, o, d, c, pl in sorted(rows):
    print("%-18s delay %+.2f [%+.2f, %+.2f] | cf %+.2f [%+.2f, %+.2f] | per-learner delay points %s mean %+.2f" % (o, *d, *c, " ".join("%+.2f" % v for v in pl), np.mean(pl)))
print("\n## pooled-arm offset = pooled effect minus the mean of the 5 single-learner effects, with a 95 % bootstrap interval (seeds resampled, 4000)")
r = np.random.default_rng(20261121)
for key, opps in (("ttc_net", ["3E-C_TRUCK", "p333", "os0_10_10"]), ("all_delay", ["os0_10_10", "p333", "3E-D_TRUCK", "3E-C_TRUCK"])):
    for o in opps:
        O = col(o, key)
        def off(s):
            den = np.median(O[s])
            pe = -np.median(P[key][s] - O[s]) / den * 100
            le = np.mean([-np.median(L[key][i][s] - O[s]) / den * 100 for i in range(5)])
            return pe - le, pe, le
        base = off(np.arange(N0))
        bs = np.array([off(r.integers(0, N0, N0))[0] for _ in range(4000)])
        print("%-9s vs %-11s pooled %+.2f, learner mean %+.2f, offset %+.2f [%+.2f, %+.2f], share of resamples below 0: %.3f" % (key, o, base[1], base[2], base[0], np.percentile(bs, 2.5), np.percentile(bs, 97.5), (bs < 0).mean()))
