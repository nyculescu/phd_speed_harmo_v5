"""Standing-cut variants and the per-group deficit in samples per run (printed items, definitions mine)."""
import json
import numpy as np
exec(open("stats.py").read().split("res = {")[0])     # reuse loaders and IDX only
res = json.load(open("results_A.json"))

def cuts(a3, a6):
    d = {}
    # (b) ratio of medians
    m3 = np.median(a3[IDX], axis=1); m6 = np.median(a6[IDX], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        bs = 1 - m6 / m3
    d["cut_median"] = float(1 - np.median(a6) / np.median(a3)) if np.median(a3) > 0 else None
    d["cut_median_ci95"] = pct(bs[np.isfinite(bs)], 2.5, 97.5)
    # (c) C-D5 single-arm form: median over seeds of (a3 - a6) / median(a3)
    if np.median(a3) > 0:
        e = (a3 - a6) / np.median(a3)
        d["cut_cd5"] = float(np.median(e))
        d["cut_cd5_ci95"] = pct(np.median(e[IDX], axis=1), 2.5, 97.5)
    return d

out = {}
for arm in LEARNERS + RULES + OTHERS + ["v3w_pooled", "v3w_learner_mean"]:
    for m, k in (("m1", "end_stop"), ("m2", "end_stop2")):
        if arm == "v3w_learner_mean":
            per = [cuts(vec("L300", l, k), vec("L600", l, k)) for l in LEARNERS]
            out[f"{arm}|{m}"] = {"cut_cd5_point": float(np.mean([p["cut_cd5"] for p in per]))}
            # joint resample of the mean of learner C-D5 cuts
            E = np.stack([(vec("L300", l, k) - vec("L600", l, k)) / np.median(vec("L300", l, k)) for l in LEARNERS])
            bs = np.median(E[:, IDX], axis=2).mean(axis=0)
            out[f"{arm}|{m}"]["cut_cd5_ci95"] = pct(bs, 2.5, 97.5)
            continue
        if arm == "v3w_pooled":
            a3 = np.mean([vec("L300", l, k) for l in LEARNERS], axis=0); a6 = np.mean([vec("L600", l, k) for l in LEARNERS], axis=0)
        else:
            a3 = vec("L300", arm, k); a6 = vec("L600", arm, k)
        out[f"{arm}|{m}"] = cuts(a3, a6)
res["standing_variants"] = out

# deficit by group at each length, samples per run: mean over learners of median over seeds of (P_l - R); and of mean differences
defi = {}
for rule in RULES + OTHERS:
    for L in ("L300", "L600"):
        for g in ("merge", "e1", "rest", "m1", "m2", "ttc_net"):
            Rv = vec(L, rule, g)
            P = np.stack([vec(L, l, g) for l in LEARNERS])
            defi[f"{L}|{rule}|{g}"] = {"median_diff": float(np.mean(np.median(P - Rv, axis=1))), "mean_diff": float(np.mean(P - Rv)),
                                       "rule_mean": float(Rv.mean()), "v3w_mean": float(P.mean())}
res["deficit_samples_per_run"] = defi
json.dump(res, open("results_A.json", "w"), indent=1)
for k, v in out.items():
    print(k, {a: (round(b, 3) if isinstance(b, float) else [round(x, 3) for x in b] if isinstance(b, list) else b) for a, b in v.items()})
for k, v in defi.items():
    if "L600" in k and k.split("|")[1] in RULES:
        print(k, {a: round(b, 1) for a, b in v.items()})
