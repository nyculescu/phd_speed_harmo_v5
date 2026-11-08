"""Operating map: v3w, tail and sw against every non-learning controller present, per cell and level (report-only).
Statistic: round 2's common1.raw (conf3/common.py) at 95 %; arm value per seed = arm_mean over its 5 learners."""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

R2 = "/home/catalin/work/phd/wt/r2-metrics/docs/research/round2"
sys.path.insert(0, R2)
import decide2 as dc  # noqa: E402
from common1 import arm_mean, med, paired_median, raw  # noqa: E402

DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).resolve().parent
P95 = (2.5, 97.5)
KEEP = ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "dist", "finished_pct", "collisions", "teleports")
METRICS = (("all_delay", -1, "delay"), ("ttc_net", -1, "close-following"), ("passed", 1, "flow"), ("b3_step", -1, "b3"),
           ("b45_step", -1, "b45"))

v = json.load(open("/home/catalin/work/phd/v5b1_runs/round2/val/validation.json"))
ARMS = {"v3w": dc.names("v3w", {int(i): c for i, c in v["chosen"]["v3w"].items()}),
        "tail": dc.names("tail", None),
        "sw": dc.names("sw", {int(i): c for i, c in v["chosen"]["sw"].items()})}
LEARNER = {n for nm in ARMS.values() for n in nm} | {f"d{i}u500" for i in range(5)}


def load(f):
    T = defaultdict(dict)
    for line in open(f):
        r = json.loads(line)
        T[(r["name"], r["q"])][r["seed"]] = {"seed": r["seed"], **{k: r.get(k) for k in KEEP}}
    return T


def classify(lo, hi):
    return "A" if lo > 0 else ("R" if hi < 0 else "=")


def front(points):
    """Names not weakly dominated on (delay, ttc), both minimised."""
    out = []
    for a, (d, t) in points.items():
        dom = any((d2 <= d and t2 <= t and (d2 < d or t2 < t)) for b, (d2, t2) in points.items() if b != a)
        if not dom:
            out.append(a)
    return out


def analyse(T, label):
    res = {}
    for cell, q in sorted({(n.split("|")[0], q) for n, q in T}):
        names = sorted({n.split("|")[1] for n, qq in T if qq == q and n.startswith(cell + "|")})
        rules = [n for n in names if n not in LEARNER]
        A = {k: dc.arm(T, cell, nm, q) for k, nm in ARMS.items() if all((f"{cell}|{x}", q) in T for x in nm)}
        R = {r: T[(f"{cell}|{r}", q)] for r in rules}
        seeds = sorted(set.intersection(*[set(x) for x in [*A.values(), *R.values()]]))
        assert all(len(x) == len(seeds) for x in [*A.values(), *R.values()]), (cell, q)
        cmp = {}
        for a, X in A.items():
            for r, Y in R.items():
                for key, sign, lab in METRICS:
                    pt, lo, hi = raw(X, Y, key, sign, P95)
                    cmp[f"{a}|{r}|{key}"] = {"pt": pt, "lo": lo, "hi": hi, "cls": classify(lo, hi),
                                             "pmed": paired_median(X, Y, key)}
        meds = {n: {key: med(X, key) for key, _, _ in METRICS} for n, X in [*R.items(), *A.items()]}
        extra = {n: {"collisions": float(sum((x["collisions"] or 0) for x in X.values())),
                     "teleports": float(sum((x["teleports"] or 0) for x in X.values())),
                     "finished_pct_med": med(X, "finished_pct")} for n, X in [*R.items(), *A.items()]}
        ident = {}
        for i, a in enumerate(rules):
            for b in rules[i + 1:]:
                if all(all(R[a][s][k] == R[b][s][k] for k in KEEP) for s in seeds):
                    ident.setdefault(a, []).append(b)
        pts_all = {r: (meds[r]["all_delay"], meds[r]["ttc_net"]) for r in rules}
        pts_nonc = {r: p for r, p in pts_all.items() if r != "nc"}
        fronts = {}
        for tag, pts in (("with_nc", pts_all), ("without_nc", pts_nonc)):
            fr = front(pts)
            pos = {}
            for a in A:
                d, t = meds[a]["all_delay"], meds[a]["ttc_net"]
                by = [r for r, (d2, t2) in pts.items() if d2 <= d and t2 <= t and (d2 < d or t2 < t)]
                over = [r for r in fr if d <= pts[r][0] and t <= pts[r][1] and (d < pts[r][0] or t < pts[r][1])]
                status = "inside (dominated)" if by else ("beyond (dominates front points)" if over else "on (non-dominated, dominates no front point)")
                # paired cross-check: median of paired differences rule - arm, per metric
                pby = [r for r in pts if paired_median(R[r], A[a], "all_delay") <= 0 and paired_median(R[r], A[a], "ttc_net") <= 0
                       and (paired_median(R[r], A[a], "all_delay") < 0 or paired_median(R[r], A[a], "ttc_net") < 0)]
                pd = {r: (paired_median(R[r], A[a], "all_delay"), paired_median(R[r], A[a], "ttc_net")) for r in fr}
                pover = [r for r, (dd, dt) in pd.items() if dd >= 0 and dt >= 0 and (dd > 0 or dt > 0)]
                pos[a] = {"status": status, "dominated_by": by, "dominates_front": over, "paired_dominated_by": pby,
                          "paired_dominates_front": pover}
            fronts[tag] = {"front": sorted(fr, key=lambda r: pts[r][0]), "pos": pos}
        best = {}
        for key, sign, lab in METRICS:
            order = sorted(rules, key=lambda r: -sign * meds[r][key])
            order_nonc = [r for r in order if r != "nc"]
            best[key] = {"best_rule": order[0], "best_rule_not_nc": order_nonc[0]}
        res[f"{cell}|{q:.0f}"] = {"file": label, "cell": cell, "q": q, "n_seeds": len(seeds), "seed_range": [seeds[0], seeds[-1]],
                                  "rules": rules, "arms": list(A), "cmp": cmp, "meds": meds, "extra": extra, "identical": ident,
                                  "fronts": fronts, "best": best}
    return res


if __name__ == "__main__":
    out = {}
    for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
        out |= analyse(load(DATA / f), f)
    (OUT / "results.json").write_text(json.dumps({"arms": ARMS, "cells": out}, indent=0))
    n = sum(len(c["cmp"]) for c in out.values())
    print("cells/levels:", list(out), "comparisons:", n)
    for k, c in out.items():
        print(k, "n", c["n_seeds"], "rules", len(c["rules"]), "arms", c["arms"], "identical", c["identical"])
