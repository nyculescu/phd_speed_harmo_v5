"""x1_exposure: where and when the policies' close-following excess over no control sits (X1, X2), exposure-normalised rates,
a speed-band rate/exposure decomposition and per-seed relations. Report-only; reads the stored rows and fields."""
import json

import numpy as np

import lib

T = lib.load()
SPLITS = {"r": ("3", "4a", "ramp2", "rest"), "s": ("lo", "mid", "hi"), "p": lib.PERIODS}
BANDS = ("lo", "mid", "hi")


def derive(r: dict) -> None:
    g = lambda k: lib.val(r, k)
    r["rate_km"] = g("ttc_net") / g("dist") * 1000.0
    r["rate_vs"] = g("ttc_net") / g("vs")
    r["rate_mov5"] = g("ttc_net") / g("e_mov5")
    r["ttc_mov18"] = g("ttc3_s_mid") + g("ttc3_s_hi")
    r["e_mov18"] = g("e_mid") + g("e_hi")
    r["rate_mov18"] = r["ttc_mov18"] / r["e_mov18"]
    for b in BANDS:
        r[f"rate_{b}"] = g(f"ttc3_s_{b}") / g(f"e_{b}")
    r["rate_served"] = g("ttc_net") / g("passed")
    r["rate_arrived"] = g("ttc_net") / g("arrived")
    r["jam_share"] = g("st_jam") / g("st_vs")
    for e in ("3", "4a"):
        r[f"rate_r_{e}"] = g(f"ttc3_r_{e}") / g(f"st_vs_e_{e}")
        r[f"rate_r_{e}_mov18"] = g(f"ttc3_r_{e}") / max(g(f"st_mov18_e_{e}"), 1.0)
    for p in lib.PERIODS:
        r[f"rate_p_{p}"] = g(f"ttc3_p_{p}") / max(g(f"st_vs_p_{p}"), 1.0)
        r[f"rate_p_{p}_mov18"] = g(f"ttc3_p_{p}") / max(g(f"st_mov18_p_{p}"), 1.0)
    r["mainline_ttc"] = g("ttc_net") - g("ttc3_r_ramp2")


for A in T.values():
    for r in A.values():
        derive(r)

NCOMP = {"n": 0}


def eff(A, B, key, sign=-1):
    NCOMP["n"] += 1
    return [round(x, 2) for x in lib.raw(A, B, key, sign)]


def rnd(t, k=1):
    return [round(x, k) for x in t]


def kitagawa(cell: str, nm: list) -> dict:
    """Per learner and seed against no control: TTC difference over the three speed bands = rate part + exposure part,
    averaged over learners per seed."""
    nc = T[(f"{cell}|nc", lib.Q)]
    seeds = sorted(nc)
    rate, expo, tot = np.zeros(len(seeds)), np.zeros(len(seeds)), np.zeros(len(seeds))
    per_band = {b: [np.zeros(len(seeds)), np.zeros(len(seeds))] for b in BANDS}
    for n in nm:
        P = T[(f"{cell}|{n}", lib.Q)]
        for i, s in enumerate(seeds):
            for b in BANDS:
                rp, rn = P[s][f"rate_{b}"], nc[s][f"rate_{b}"]
                ep, en = P[s][f"e_{b}"], nc[s][f"e_{b}"]
                ra, ex = (rp - rn) * (ep + en) / 2.0, (ep - en) * (rp + rn) / 2.0
                rate[i] += ra / len(nm)
                expo[i] += ex / len(nm)
                per_band[b][0][i] += ra / len(nm)
                per_band[b][1][i] += ex / len(nm)
            tot[i] += (lib.val(P[s], "ttc3") - lib.val(nc[s], "ttc3")) / len(nm)
    assert np.allclose(rate + expo, tot, atol=1e-6), "decomposition does not add up"
    NCOMP["n"] += 4
    return {"total_mean": rnd(lib.ci(tot, np.mean)), "rate_part_mean": rnd(lib.ci(rate, np.mean)), "exposure_part_mean": rnd(lib.ci(expo, np.mean)),
            "rate_share": rnd(lib.ratio_ci(rate, tot), 3),
            "per_band": {b: {"rate_mean": rnd(lib.ci(x[0], np.mean)), "exposure_mean": rnd(lib.ci(x[1], np.mean))} for b, x in per_band.items()}}


RES = {}
for cell in ("X1", "X2"):
    nc = T[(f"{cell}|nc", lib.Q)]
    C = {"nc_medians": {}}
    keys_med = ["ttc_net", "ttc2", "ttc15", "sev3", "all_delay", "passed", "dist", "vs", "e_mov5", "e_stop5", "e_lo", "e_mid", "e_hi", "jam_share",
                "rate_km", "rate_vs", "rate_mov5", "rate_mov18", "rate_lo", "rate_mid", "rate_hi", "rate_served"]
    keys_med += [f"ttc3_{s}_{p}" for s, ps in SPLITS.items() for p in ps]
    keys_med += [f"st_vs_e_{e}" for e in ("3", "4a", "4")] + [f"st_vs_p_{p}" for p in lib.PERIODS]
    for name, nm in lib.arms(cell).items():
        A = lib.arm_mean(T, [f"{cell}|{n}" for n in nm])
        R = {"medians": {k: round(float(np.median([lib.val(x, k) for x in A.values()])), 4) for k in keys_med}}
        if name != "nc":
            R["effect_vs_nc"] = {k: eff(A, nc, k) for k in ("ttc_net", "ttc2", "ttc15", "sev3", "all_delay")} | {"passed": eff(A, nc, "passed", 1)}
            # (a) splits: raw units, additive by the mean
            dt = lib.paired(A, nc, "ttc3")
            sp = {}
            for s, ps in SPLITS.items():
                for p in ps:
                    k = f"ttc3_{s}_{p}"
                    d = lib.paired(A, nc, k)
                    NCOMP["n"] += 3
                    sp[k] = {"nc_med": round(float(np.median([lib.val(x, k) for x in nc.values()])), 1),
                             "arm_med": round(float(np.median([lib.val(x, k) for x in A.values()])), 1),
                             "diff_median": rnd(lib.ci(d)), "diff_mean": rnd(lib.ci(d, np.mean)), "share_of_total_mean": rnd(lib.ratio_ci(d, dt), 3)}
            R["splits"] = sp
            R["total_ttc3_diff"] = {"median": rnd(lib.ci(dt)), "mean": rnd(lib.ci(dt, np.mean))}
            # (b) exposure (sign +1: positive = the arm has more) and exposure-normalised rates (round 2's sign: positive = fewer)
            R["exposure_change_pct"] = {k: eff(A, nc, k, 1) for k in ("dist", "vs", "e_mov5", "e_stop5", "e_lo", "e_mid", "e_hi", "e_mov18", "passed", "arrived",
                                                                     "st_jam", "st_vs_e_3", "st_vs_e_4a", "st_vs_e_4", "st_mov18_e_3", "st_mov18_e_4a",
                                                                     "st_mov18_e_4", "st_dense_mov")}
            R["rate_effect"] = {k: eff(A, nc, k) for k in ("rate_km", "rate_vs", "rate_mov5", "rate_mov18", "rate_lo", "rate_mid", "rate_hi", "rate_served",
                                                          "rate_arrived", "rate_r_3", "rate_r_4a", "rate_r_3_mov18", "rate_r_4a_mov18",
                                                          *[f"rate_p_{p}" for p in lib.PERIODS], *[f"rate_p_{p}_mov18" for p in lib.PERIODS])}
            R["kitagawa_speed_band"] = kitagawa(cell, nm)
            # (c) per-seed relation of the TTC excess with the jam-share, delay and exposure differences
            dj, dd = lib.paired(A, nc, "jam_share"), lib.paired(A, nc, "all_delay")
            rel = {"d_ttc_vs_d_jam_share": lib.corr_ci(dt, dj), "d_ttc_vs_d_all_delay": lib.corr_ci(dt, dd),
                   "d_ttc_vs_d_e_mov5": lib.corr_ci(dt, lib.paired(A, nc, "e_mov5")), "d_ttc_vs_d_e_stop5": lib.corr_ci(dt, lib.paired(A, nc, "e_stop5")),
                   "d_ttc_vs_d_e_hi": lib.corr_ci(dt, lib.paired(A, nc, "e_hi")),
                   "d_ttc_vs_nc_jam_share": lib.corr_ci(dt, np.array([nc[s]["jam_share"] for s in sorted(nc)])),
                   "d_ttc_vs_d_dist": lib.corr_ci(dt, lib.paired(A, nc, "dist"))}
            NCOMP["n"] += len(rel)
            R["per_seed"] = rel
            R["per_seed_counts"] = {"seeds_more_ttc": int((dt > 0).sum()), "seeds_less_jam": int((dj < 0).sum()), "seeds_less_delay": int((dd < 0).sum()), "n": len(dt)}
        C[name] = R
    RES[cell] = C
RES["comparisons_with_ci"] = NCOMP["n"]
json.dump(RES, open(lib.HERE / "results.json", "w"), indent=1)
print("written results.json; CIs computed:", NCOMP["n"])
