"""EXPLORATORY: per-learner point estimates (single run against single run), min to max, and the count of learner CIs on each side."""
import numpy as np
exec(open("an1.py").read().split("FIELDS = [")[0])
ROWS = ["ttc_net", "ttc2", "ttc15", "sev3", "b45_step", "ev45_all", "ev45_car", "E30", "arms_alks", "arms_car", "jerk_step_rate", "mild_s_all", "undertakes", "pass_straight", "end_stop", "end_stop2", "fuel_km", "all_delay"]
for cell in ("TRUCK", "S"):
    print("####", cell, "| per-learner median effect min..max (CI>0 / CI<0) vs p333 | os0_10_10 | 3E-C_TRUCK | nc ; learner medians")
    for f in ROWS:
        L = [val(cell, l, f) for l in LEARN]
        out = []
        for o in ("p333", "os0_10_10", "3E-C_TRUCK", "nc"):
            O = val(cell, o, f)
            per = [eff(l, O) for l in L]
            if per[0] is None: out.append("n/a"); continue
            out.append("%+.1f..%+.1f (%d/%d)" % (min(p[0] for p in per), max(p[0] for p in per), sum(p[1] > 0 for p in per), sum(p[2] < 0 for p in per)))
        print(f, "|", " | ".join(out), "; learner medians %.4g..%.4g, pooled %.4g" % (min(np.median(l) for l in L), max(np.median(l) for l in L), np.median(np.mean(L, axis=0))))
