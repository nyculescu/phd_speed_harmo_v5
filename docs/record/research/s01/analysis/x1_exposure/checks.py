"""Definition checks: ttc3 = ttc_net, the splits add up, the pack did not change the runs, exposure sums agree."""
import json
import sys
from collections import defaultdict

import numpy as np

import lib

T = lib.load()
out = {}
# 1. ttc3 (plant_sweep.conflicts) against ttc_net (b_env E30 + out_E30)
d = [r["ttc_net"] - r["ttc3"] for A in T.values() for r in A.values()]
out["ttc_net_minus_ttc3"] = {"n": len(d), "max_abs": float(np.max(np.abs(d)))}
# 2. splits add up
for m in ("ttc3", "ttc2", "ttc15"):
    for s, parts in (("r", ("3", "4a", "ramp2", "rest")), ("s", ("lo", "mid", "hi")), ("p", lib.PERIODS)):
        e = [r[m] - sum(lib.val(r, f"{m}_{s}_{p}") for p in parts) for A in T.values() for r in A.values()]
        out[f"{m}_{s}_sum_err_max"] = float(np.max(np.abs(e)))
# 3. step-resolution vehicle-seconds against the 1-Hz count vs; field vehicle-seconds (mainline) against vs
rat = [r["e_all"] / r["vs"] for A in T.values() for r in A.values()]
out["e_all_over_vs"] = [float(np.min(rat)), float(np.max(rat))]
rat = [r["st_vs"] / r["vs"] for A in T.values() for r in A.values()]
out["st_vs_over_vs"] = [float(np.min(rat)), float(np.median(rat)), float(np.max(rat))]
# 4. jam share recomputed from the field against summary_rows_test waves.jam_share
S = json.load(open(lib.DATA / "summary_rows_test.json"))
err = []
for (n, q), A in T.items():
    for s, r in A.items():
        j = S[f"{n}|{q:.0f}"][str(s)]["waves"]["jam_share"]
        err.append(abs(r["st_jam"] / r["st_vs"] - j))
out["jam_share_recomputed_err_max"] = float(np.max(err))
# 5. the pack did not change the runs: round 2's stored rows for the same arm and seed
R2 = {}
with open(lib.R2ROWS) as h:
    for line in h:
        r = json.loads(line)
        R2[(r["name"], r["q"], r["seed"])] = {k: r.get(k) for k in ("ttc_net", "all_delay", "passed", "b3_step", "dist", "vs", "ttc3", "ttc3_s_hi")}
cmp = defaultdict(list)
missing = 0
for (n, q), A in T.items():
    for s, r in A.items():
        o = R2.get((n, q, s))
        if o is None:
            missing += 1
            continue
        for k, v in o.items():
            if v is not None:
                cmp[k].append(abs(r.get(k, 0.0) - v))
out["round2_match"] = {"missing_pairs": missing, **{k: {"n": len(v), "max_abs_diff": float(np.max(v))} for k, v in cmp.items()}}
# 6. how many rows have no leader-closing samples at low speed (counters absent = 0)
out["rows_without_ttc3_s_lo"] = int(sum("ttc3_s_lo" not in r for A in T.values() for r in A.values()))
print(json.dumps(out, indent=1))
json.dump(out, open(lib.HERE / "checks.json", "w"), indent=1)
