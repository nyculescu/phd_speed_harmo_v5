import sys
import numpy as np
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3")
from common1 import load, arm_mean, med, val, Q, RULE, LEARNERS
T = load("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl")
rng = np.random.default_rng(1)
def boot(d):
    d = np.asarray(d); b = np.median(rng.choice(d, (4000, len(d))), axis=1)
    return np.percentile(b, [2.5, 97.5])
SPL = {"road": ["r_3", "r_4a", "r_ramp2", "r_rest"], "speed": ["s_lo", "s_mid", "s_hi"], "period": ["p_before", "p_taper", "p_hold", "p_after", "p_rest"]}
for cell in ("X2", "X1"):
    W = arm_mean(T, [f"{cell}|w{i}" for i in range(LEARNERS)], Q)
    print("cell", cell, "seeds", len(W), "Q", Q)
    # consistency: splits sum to ttc3
    for g, ks in SPL.items():
        err = max(abs(sum(val(r, "ttc3_" + k) for k in ks) - val(r, "ttc3")) for r in W.values())
        print(" sum check", g, round(err, 3))
    for ref in (RULE, "p333", "nc"):
        R = T[(f"{cell}|{ref}", Q)]
        ds = sorted(set(W) & set(R))
        tot = [val(R[s], "ttc3") - val(W[s], "ttc3") for s in ds]
        print(f" ref {ref}: total ttc3 gain dmed={med(R,'ttc3')-med(W,'ttc3'):.1f} paired={np.median(tot):.1f} mean={np.mean(tot):.1f}")
        for g, ks in SPL.items():
            out = []
            means = {k: np.mean([val(R[s], "ttc3_" + k) - val(W[s], "ttc3_" + k) for s in ds]) for k in ks}
            tm = sum(means.values())
            for k in ks:
                d = [val(R[s], "ttc3_" + k) - val(W[s], "ttc3_" + k) for s in ds]
                lo, hi = boot(d)
                out.append(f"{k}: dmed={med(R,'ttc3_'+k)-med(W,'ttc3_'+k):.0f} pm={np.median(d):.0f} [{lo:.0f},{hi:.0f}] meanshare={100*means[k]/tm:.0f}%")
            print("  ", g, "; ".join(out))
