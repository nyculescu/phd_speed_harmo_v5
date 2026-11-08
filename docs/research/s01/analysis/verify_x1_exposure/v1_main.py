"""F0-F4, F6, F8-F10 re-computation from rows_test.jsonl."""
import json
import sys

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import BANDS, arms_for, effect, field, fmt, g, load, mean_ci, per_seed  # noqa: E402

OUT = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure"
T = load()
res = {"n_comparisons": 0}


def cnt():
    res["n_comparisons"] += 1


# F0: definitions checks
mx = 0.0
split_err = {}
for name, A in T.items():
    for s, r in A.items():
        mx = max(mx, abs(g(r, "ttc_net") - g(r, "ttc3")), abs(g(r, "ttc_net") - g(r, "E30") - g(r, "out_E30")))
        for m in ("ttc3", "ttc2", "ttc15", "sev3"):
            for kind, parts in (("r", ("3", "4a", "ramp2", "rest")), ("s", BANDS), ("p", ("before", "taper", "hold", "after", "rest"))):
                e = abs(sum(g(r, f"{m}_{kind}_{p}") for p in parts) - g(r, m))
                split_err[(m, kind)] = max(split_err.get((m, kind), 0), e)
        assert r["steps"] == 1500
ratio = [r["e_tot"] / r["vs"] for A in T.values() for r in A.values()]
print("F0 max|ttc_net-ttc3|, |ttc_net-E30-out_E30|:", mx, " split errors:", {f"{a}_{b}": v for (a, b), v in split_err.items()})
print("F0 step-hist vehicle-s / vs: min %.5f max %.5f" % (min(ratio), max(ratio)))
res["F0"] = {"max_diff": mx, "split_err": {f"{a}_{b}": v for (a, b), v in split_err.items()}, "vh_vs_ratio": [min(ratio), max(ratio)]}

# Pack vs round-2 rows (same seeds, run without the pack)
r2 = {}
for f in ("/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl",):
    with open(f) as fh:
        for line in fh:
            r = json.loads(line)
            r2[(r["name"], r["q"], r["seed"])] = r
keys = ("ttc_net", "all_delay", "passed", "b3_step", "dist", "vs", "N", "E30", "out_E30", "b45_step", "collisions")
nm = mism = 0
miss = 0
mism_keys = {}
for name, A in T.items():
    for s, r in A.items():
        o = r2.get((name, r["q"], s))
        if o is None:
            miss += 1
            continue
        nm += 1
        for k in keys:
            if abs(g(r, k) - g(o, k)) > 1e-9:
                mism += 1
                mism_keys[k] = mism_keys.get(k, 0) + 1
print(f"pack vs round2: {nm} pairs matched by (name,q,seed), {miss} missing, mismatching key-values {mism} {mism_keys}")
res["pack_vs_round2"] = {"pairs": nm, "missing": miss, "mismatch": mism, "keys": keys}

CMP = ["v3w", "tail", "sw", "inc", "p333", "3e", "3ex", "os1_15_10"]
SPL = [f"ttc3_r_{x}" for x in ("3", "4a", "ramp2", "rest")] + [f"ttc3_s_{b}" for b in BANDS] + [f"ttc3_p_{p}" for p in ("before", "taper", "hold", "after", "rest")] + ["E30", "out_E30"]


def rate(num, den):
    return lambda r: g(r, num) / max(g(r, den), 1e-9) if isinstance(num, str) else None


def kit(cell, arm):
    """Per seed: mean over learners of the Kitagawa parts against nc (same seed)."""
    names = [f"{cell}|{n}" for n in arms_for(cell)[arm]]
    nc = T[f"{cell}|nc"]
    seeds = sorted(nc)
    out = {"rate": [], "exp": [], "total": [], "rate_b": {b: [] for b in BANDS}, "exp_b": {b: [] for b in BANDS}}
    for s in seeds:
        acc = {"rate": 0, "exp": 0, "total": 0, **{f"r{b}": 0 for b in BANDS}, **{f"e{b}": 0 for b in BANDS}}
        for n in names:
            p, o = T[n][s], nc[s]
            for b in BANDS:
                eP, eN = p[f"e_{b}"], o[f"e_{b}"]
                rP, rN = g(p, f"ttc3_s_{b}") / eP, g(o, f"ttc3_s_{b}") / eN
                rp_ = (rP - rN) * (eP + eN) / 2
                ep_ = (eP - eN) * (rP + rN) / 2
                acc["rate"] += rp_ / len(names)
                acc["exp"] += ep_ / len(names)
                acc[f"r{b}"] += rp_ / len(names)
                acc[f"e{b}"] += ep_ / len(names)
            acc["total"] += (g(p, "ttc3") - g(o, "ttc3")) / len(names)
        assert abs(acc["rate"] + acc["exp"] - acc["total"]) < 1e-6
        for k in ("rate", "exp", "total"):
            out[k].append(acc[k])
        for b in BANDS:
            out["rate_b"][b].append(acc[f"r{b}"])
            out["exp_b"][b].append(acc[f"e{b}"])
    return out


for cell in ("X1", "X2"):
    res[cell] = {}
    seeds, nc_ttc = per_seed(T, cell, "nc", field("ttc_net"))
    print(f"\n=== {cell}: nc median ttc_net {np.median(nc_ttc):.0f}, E30 {np.median(per_seed(T, cell, 'nc', field('E30'))[1]):.1f}, ttc3_r_rest {np.median(per_seed(T, cell, 'nc', field('ttc3_r_rest'))[1]):.1f}")
    for arm in CMP:
        R = res[cell][arm] = {}
        # F1 effects
        for k, sign in (("ttc_net", -1), ("all_delay", -1), ("passed", 1), ("ttc2", -1), ("ttc15", -1), ("sev3", -1), ("ttc_half", -1), ("stop_gap", -1), ("b45_step", -1)):
            _, p = per_seed(T, cell, arm, field(k))
            _, o = per_seed(T, cell, "nc", field(k))
            R[f"eff_{k}"] = effect(p, o, sign)
            cnt()
        # F2 splits: mean paired difference
        for k in SPL + ["ttc3"]:
            _, p = per_seed(T, cell, arm, field(k))
            _, o = per_seed(T, cell, "nc", field(k))
            R[f"dmean_{k}"] = mean_ci(p - o)
            cnt()
        # F3 exposure change and rates (round-2 sign: negative = arm has more per exposure)
        for k in ("dist", "vs", "e_stop5", "e_lo", "e_mid", "e_hi", "passed"):
            _, p = per_seed(T, cell, arm, field(k))
            _, o = per_seed(T, cell, "nc", field(k))
            R[f"exp_{k}"] = effect(p, o, 1)
            cnt()
        rates = {
            "per_dist": lambda r: g(r, "ttc_net") / r["dist"],
            "per_vs": lambda r: g(r, "ttc_net") / r["vs"],
            "per_mov5": lambda r: g(r, "ttc_net") / (r["e_tot"] - r["e_stop5"]),
            "per_passed": lambda r: g(r, "ttc_net") / r["passed"],
            "midhi": lambda r: (g(r, "ttc3_s_mid") + g(r, "ttc3_s_hi")) / (r["e_mid"] + r["e_hi"]),
            "lo": lambda r: g(r, "ttc3_s_lo") / r["e_lo"],
            "lo_mov": lambda r: g(r, "ttc3_s_lo") / (r["e_lo"] - r["e_stop5"]),
            "mid": lambda r: g(r, "ttc3_s_mid") / r["e_mid"],
            "hi": lambda r: g(r, "ttc3_s_hi") / r["e_hi"],
        }
        for k, fn in rates.items():
            _, p = per_seed(T, cell, arm, fn)
            _, o = per_seed(T, cell, "nc", fn)
            R[f"rate_{k}"] = effect(p, o, -1)
            cnt()
        K = kit(cell, arm)
        R["kit"] = {k: mean_ci(K[k]) for k in ("total", "rate", "exp")}
        R["kit_b"] = {f"{x}_{b}": mean_ci(K[f"{x}_b"][b]) for x in ("rate", "exp") for b in BANDS}
        res["n_comparisons"] += 3 + 6
        print(f"\n{cell} {arm}: ttc_net {fmt(R['eff_ttc_net'], 2)}  delay {fmt(R['eff_all_delay'], 2)}  passed {fmt(R['eff_passed'], 2)}")
        print("  ttc2 %s ttc15 %s sev3 %s ttc_half %s stop_gap %s b45_step %s" % tuple(fmt(R[f'eff_{k}']) for k in ("ttc2", "ttc15", "sev3", "ttc_half", "stop_gap", "b45_step")))
        print("  dmean: " + "; ".join(f"{k.replace('ttc3_', '')} {fmt(R['dmean_' + k])}" for k in SPL + ["ttc3"]))
        print("  exposure %: " + "; ".join(f"{k} {fmt(R['exp_' + k], 2)}" for k in ("dist", "vs", "e_stop5", "e_lo", "e_mid", "e_hi")))
        print("  rates (neg = more): " + "; ".join(f"{k} {fmt(R['rate_' + k])}" for k in rates))
        print("  kitagawa: " + "; ".join(f"{k} {fmt(v)}" for k, v in R["kit"].items()) + " | " + "; ".join(f"{k} {fmt(v)}" for k, v in R["kit_b"].items()))

# X1 minus X2 contrast for v3w (paired by seed number)
c = {}
for k in ("ttc3", "E30", "out_E30"):
    d = {}
    for cell in ("X1", "X2"):
        s, p = per_seed(T, cell, "v3w", field(k))
        _, o = per_seed(T, cell, "nc", field(k))
        d[cell] = dict(zip(s, p - o))
    common = sorted(set(d["X1"]) & set(d["X2"]))
    c[k] = mean_ci([d["X1"][s] - d["X2"][s] for s in common])
    cnt()
print("\nX1-X2 contrast v3w excess:", {k: fmt(v) for k, v in c.items()})
res["X1_minus_X2"] = c

# F9: ALKS headway exposure per arm (all ALKS-seconds, V2V off counted at tau0 = 1.6 s)
H = (1.6, 1.2, 1.0, 0.8)
for cell in ("X1", "X2"):
    for arm in CMP:
        def mtau(r):
            ls_, off = r.get("m_dec_level_s"), r.get("m_dec_off_s")
            if ls_ is None:
                return np.nan
            tot = sum(ls_) + off
            return (sum(a * b for a, b in zip(ls_, H)) + 1.6 * off) / tot

        def sh3(r):
            ls_, off = r.get("m_dec_level_s"), r.get("m_dec_off_s")
            return np.nan if ls_ is None else ls_[3] / (sum(ls_) + off)
        _, a = per_seed(T, cell, arm, mtau)
        _, b = per_seed(T, cell, arm, sh3)
        res[cell][arm]["mean_tau"] = float(np.nanmedian(a))
        res[cell][arm]["share_l3_all"] = float(np.nanmedian(b))
    print(cell, "median ALKS mean tau / share of all ALKS-s at 0.8 s:", {a: (round(res[cell][a]["mean_tau"], 3), round(res[cell][a]["share_l3_all"], 3)) for a in CMP})

json.dump(res, open(f"{OUT}/v1_main.json", "w"), indent=1, default=float)
print("comparisons:", res["n_comparisons"])
