"""x1_exposure, second pass: period exposure and jam, fine speed composition, slow-but-moving rate, shorter thresholds and
severity, the shared-no-control null for per-seed correlations, braking-event link, per-learner spread."""
import json

import numpy as np

import lib

T = lib.load()
S = json.load(open(lib.DATA / "summary_rows_test.json"))
for (n, q), A in T.items():
    for s, r in A.items():
        m = S[f"{n}|{q:.0f}"][str(s)]
        r["ev45"] = sum(m[f"events_ge45_{c}"] for c in ("car", "alks", "truck"))
        r["ev_all"] = sum(m[f"events_{c}"] for c in ("car", "alks", "truck"))
        r["jams_n"] = m["waves"]["jams"]
        r["lvl3"] = m["dec"]["level_share_on"][-1] if "dec" in m and m["dec"].get("level_share_on") else np.nan
        r["jam_share"] = r["st_jam"] / r["st_vs"]
        r["rate_lo_mov"] = lib.val(r, "ttc3_s_lo") / max(r["e_lo"] - r["e_stop5"], 1.0)
        r["stop_share_lo"] = r["e_stop5"] / r["e_lo"]
NC = {"n": 0}


def eff(A, B, k, sign=-1):
    NC["n"] += 1
    return [round(x, 2) for x in lib.raw(A, B, k, sign)]


def rnd(t, k=1):
    return [round(x, k) for x in t]


def shuffled_null(dt_p, dt_n, dj_p, dj_n, n_perm=10000):
    """Spearman of (P - nc) differences when nc rows come from another seed: keeps the shared-nc term, breaks the pairing."""
    rng = np.random.default_rng(lib.RNG + 2)
    out = []
    for _ in range(n_perm):
        pi = rng.permutation(len(dt_n))
        out.append(lib.spearman(dt_p - dt_n[pi], dj_p - dj_n[pi]))
    return np.array(out)


OUT = {}
for cell in ("X1", "X2"):
    nc = T[(f"{cell}|nc", lib.Q)]
    seeds = sorted(nc)
    C = {}
    for name, nm in lib.arms(cell).items():
        if name == "nc":
            continue
        A = lib.arm_mean(T, [f"{cell}|{n}" for n in nm])
        R = {}
        # period exposure and jam (field, mainline), change in % of nc's median (+ = more)
        R["period_change_pct"] = {k: eff(A, nc, k, 1) for p in lib.PERIODS for k in (f"st_vs_p_{p}", f"st_jam_p_{p}", f"st_lo_p_{p}")}
        R["period_edge_jam_diff"] = {f"{p}_{e}": rnd(lib.ci(lib.paired(A, nc, f"st_jam_pe_{p}_{e}"), np.mean)) for p in lib.PERIODS for e in ("3", "4a", "4")}
        R["nc_period_edge_jam_med"] = {f"{p}_{e}": round(float(np.median([nc[s][f"st_jam_pe_{p}_{e}"] for s in seeds])), 0) for p in lib.PERIODS for e in ("3", "4a", "4")}
        R["nc_jam_edge_med"] = {e: round(float(np.median([nc[s][f"st_jam_e_{e}"] for s in seeds])), 0) for e in lib.EDGES}
        R["arm_jam_edge_med"] = {e: round(float(np.median([A[s][f"st_jam_e_{e}"] for s in seeds])), 0) for e in lib.EDGES}
        NC["n"] += 15
        # slow-but-moving rate and stopped share of the slow band
        R["rate_lo_mov"] = eff(A, nc, "rate_lo_mov")
        R["stop_share_lo"] = {"nc_med": round(float(np.median([nc[s]["stop_share_lo"] for s in seeds])), 3),
                              "arm_med": round(float(np.median([A[s]["stop_share_lo"] for s in seeds])), 3), "diff": rnd(lib.ci(lib.paired(A, nc, "stop_share_lo")), 3)}
        NC["n"] += 1
        # shorter thresholds, severity, half-second sampling, small gaps
        R["thresholds"] = {k: eff(A, nc, k) for k in ("ttc3", "ttc2", "ttc15", "sev3", "ttc_half", "gap25", "stop_gap", "ttc3_s_hi", "ttc2_s_hi", "ttc15_s_hi",
                                                       "ttc3_s_mid", "ttc2_s_mid", "ttc15_s_mid", "ttc3_s_lo", "ttc2_s_lo", "ttc15_s_lo", "sev3_s_hi", "sev3_s_mid")}
        R["nc_med"] = {k: float(np.median([lib.val(nc[s], k) for s in seeds])) for k in ("gap25", "stop_gap", "sev3", "sev3_s_hi", "sev3_s_mid", "ttc_half")}
        # braking events and jam clusters
        R["events"] = {k: eff(A, nc, k) for k in ("ev45", "ev_all", "jams_n")}
        # per-seed correlation with the shared-nc null
        if name in ("v3w", "tail", "sw", "baseline-v3", "3E-T", "p333"):
            ttc_p, ttc_n = np.array([A[s]["ttc3"] for s in seeds]), np.array([nc[s]["ttc3"] for s in seeds])
            corr = {}
            for k in ("jam_share", "e_stop5", "all_delay", "ev45"):
                x_p, x_n = np.array([A[s][k] for s in seeds]), np.array([nc[s][k] for s in seeds])
                rho = lib.spearman(ttc_p - ttc_n, x_p - x_n)
                null = shuffled_null(ttc_p, ttc_n, x_p, x_n)
                corr[k] = {"rho_paired": round(rho, 3), "shuffled_nc_null_median": round(float(np.median(null)), 3),
                           "null_2.5_97.5": [round(float(np.percentile(null, 2.5)), 3), round(float(np.percentile(null, 97.5)), 3)],
                           "p_rho_ge_null": round(float((null >= rho).mean()), 4),
                           "within_nc_rho": round(lib.spearman(ttc_n, x_n), 3), "within_arm_rho": round(lib.spearman(ttc_p, x_p), 3)}
                NC["n"] += 1
            R["per_seed_null"] = corr
        if name in lib.LEARNERS:
            R["per_learner_ttc_net"] = {n: eff(T[(f"{cell}|{n}", lib.Q)], nc, "ttc_net") for n in nm}
            R["per_learner_rate_mov18"] = {n: eff({s: T[(f"{cell}|{n}", lib.Q)][s] for s in seeds}, nc, "rate_mov18") for n in nm}
            lv = np.array([A[s]["lvl3"] for s in seeds])
            R["lvl3_med"] = round(float(np.nanmedian(lv)), 3)
            R["rho_dttc_lvl3"] = lib.corr_ci(lib.paired(A, nc, "ttc3"), lv)
            NC["n"] += 1
        C[name] = R
    # fine speed composition: vehicle-seconds per 5 km/h bin, v3w minus nc (mean over seeds)
    for name in ("v3w", "p333", "3E-T"):
        nm = lib.arms(cell)[name]
        P = np.array([np.mean([T[(f"{cell}|{n}", lib.Q)][s]["vh_all"] for n in nm], axis=0) for s in seeds])
        N = np.array([nc[s]["vh_all"] for s in seeds])
        d = P - N
        C[name]["vh_bins_kmh"] = [f"{5*i}-{5*i+5}" for i in range(30)]
        C[name]["vh_nc_mean"] = np.round(N.mean(0), 0).tolist()
        C[name]["vh_diff_mean"] = np.round(d.mean(0), 0).tolist()
        C[name]["vh_diff_ci"] = [rnd(lib.ci(d[:, i], np.mean), 0) for i in range(30)]
        NC["n"] += 30
    OUT[cell] = C
OUT["comparisons_with_ci"] = NC["n"]
json.dump(OUT, open(lib.HERE / "deeper.json", "w"), indent=1)
print("written deeper.json; CIs/tests:", NC["n"])
