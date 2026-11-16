"""Post hoc, descriptive: skew of the 600-m counts, the rest group by edge, and edge-1 samples in the V1 traces.

usage: extra.py runs.pkl TRACE_ROWS TRACE_ST_DIR OUT.json"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import tables, V3W, RULES, ARMS, PERIODS, r2  # noqa: E402

Q = (10, 25, 50, 75, 90, 95, 99)


def period(t: float, onset: float, dur: float) -> str:
    return "before" if t < onset else "taper" if t < onset + 20 else "hold" if t < onset + dur else "after" if t < onset + dur + 120 else "rest"


def main(runs: str, trows: str, tst: str, out: str) -> None:
    T = tables(pd.read_pickle(runs))
    res = {"note": "post hoc, descriptive"}
    # quantiles per run at 600 m and 300 m
    qs = {}
    for c in ("L300", "L600"):
        qs[c] = {a: {k: [r2(x) for x in np.percentile(T[c][a][k], Q)] for k in ("merge", "ttc_net", "e1")} for a in ARMS + V3W}
    res["quantiles"] = {"q": Q, "by": qs}
    # paired differences on the total, split by the rule's merge-area count (terciles at 600 m)
    split = {}
    for c in ("L300", "L600"):
        split[c] = {}
        for r in RULES:
            R = T[c][r]
            cut = np.percentile(R["merge"], (100 / 3, 200 / 3))
            lab = np.digitize(R["merge"], cut)
            d = {}
            for i, name in enumerate(("low", "mid", "high")):
                m = lab == i
                diffs = {w: (R["ttc_net"] - T[c][w]["ttc_net"])[m] for w in V3W}
                d[name] = {"n": int(m.sum()), "rule_merge_range": [r2(R["merge"][m].min()), r2(R["merge"][m].max())],
                           "mean_R_minus_P_total": r2(np.mean([x.mean() for x in diffs.values()])),
                           "median_R_minus_P_total": r2(np.mean([x.median() for x in diffs.values()])),
                           "mean_R_minus_P_merge": r2(np.mean([(R["merge"] - T[c][w]["merge"])[m].mean() for w in V3W])),
                           "mean_R_minus_P_e1": r2(np.mean([(R["e1"] - T[c][w]["e1"])[m].mean() for w in V3W])),
                           "share_learner_runs_fewer_total": r2(np.mean([(x > 0).mean() for x in diffs.values()]))}
            split[c][r] = d
            split[c][r + "_share_learner_runs_fewer"] = {k: r2(np.mean([((R[k] - T[c][w][k]) > 0).mean() for w in V3W])) for k in ("ttc_net", "no_e1", "merge")}
            split[c][r + "_share_learner_runs_more"] = {k: r2(np.mean([((R[k] - T[c][w][k]) < 0).mean() for w in V3W])) for k in ("ttc_net", "no_e1", "merge")}
    res["by_rule_merge_tercile"] = split
    # the rest group by edge, means per run
    rest = {}
    for c in ("L300", "L600"):
        rest[c] = {a: {f"{g}|{p}": r2(T[c][a][f"t|{g}|{p}"].mean()) for g in ("2", "3", "4", "5", "junction") for p in PERIODS
                       if T[c][a][f"t|{g}|{p}"].mean() >= 0.5} for a in ARMS}
    res["rest_by_edge_mean"] = rest
    # V1 traces: edge-1 samples by period, distance to the edge-1 end, follower and leader type, follower speed
    tr = {}
    with open(trows) as fh:
        for line in fh:
            r = json.loads(line)
            if not r["name"].endswith("~trace"):
                continue
            onset, dur = r["pert_log"][0][1], r["pert_log"][0][2]
            e1 = [s for s in r["vv_trace"] if s[5] == "1"]
            key = f"{r['name'].replace('~trace', '')} {r['seed']}"
            dist = [3000.0 - s[7] for s in e1]
            tr[key] = {"ttc_net": r["ttc_net"], "edge1": len(e1), "onset": round(onset, 1), "dur": round(dur, 1),
                       "by_period": dict(Counter(period(s[0], onset, dur) for s in e1)),
                       "dist_to_end_m": [r2(x) for x in np.percentile(dist, (0, 25, 50, 75, 100))] if dist else None,
                       "follower_type": dict(Counter(s[3] for s in e1)), "leader_type": dict(Counter(s[4] for s in e1)),
                       "leader_road": dict(Counter(s[9] for s in e1)),
                       "follower_speed_kmh": [r2(x * 3.6) for x in np.percentile([s[15] for s in e1], (0, 50, 100))] if e1 else None,
                       "leader_speed_kmh": [r2(x * 3.6) for x in np.percentile([s[16] for s in e1], (0, 50, 100))] if e1 else None,
                       "t_after_onset_s": [r2(x) for x in np.percentile([s[0] - onset for s in e1], (0, 50, 100))] if e1 else None,
                       "follower_lane": dict(Counter(s[6] for s in e1)),
                       "distinct_followers": len({s[1] for s in e1})}
    res["trace_edge1"] = tr
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print("written", out)


if __name__ == "__main__":
    main(*sys.argv[1:5])
