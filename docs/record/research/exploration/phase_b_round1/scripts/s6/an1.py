"""EXPLORATORY (rows already read for a verdict). Paired seeds; effect = -median(P - O) / median(O) x 100, positive = v3w lower;
95 % percentile bootstrap over seeds, 10,000 resamples, rng 20261110. Pooled v3w = per-seed mean of the 5 learners (read6's convention)."""
import numpy as np
Z0 = np.load("s6_safety.npz"); Z = {k: Z0[k] for k in Z0.files}
KEYS = list(Z["keys"]); n = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["3E-C_TRUCK", "3E-D_TRUCK", "3e", "3ex1", "3ex2", "MPC-F", "a4400_10_1", "copy", "grid_a41000_10_2", "grid_lr400_13_1", "grid_os1_10_10", "grid_r4a2", "grid_z31333", "lr1000_10_1", "lr1000_16_2", "lr400_13_2", "lr400_16_1", "os0_10_10", "os1_10_0", "os1_15_10", "p333", "r4a1", "z33133"]
IDX = np.random.default_rng(20261110).integers(0, n, (10_000, n))
def raw(cell, arm, key): return Z[f"{cell}|{arm}"][:, KEYS.index(key)]
def val(cell, arm, f):
    g = lambda k: raw(cell, arm, k)
    if f in KEYS: return g(f)
    if f == "ev_all": return sum(g(f"ev_{c}") for c in ("car", "alks", "truck"))
    if f == "ev45_all": return sum(g(f"ev45_{c}") for c in ("car", "alks", "truck"))
    if f == "ev7_all": return sum(g(f"ev7_{c}") for c in ("car", "alks", "truck"))
    if f == "casc_all": return sum(g(f"casc_{c}") for c in ("car", "alks", "truck"))
    if f == "arms_1hz": return np.sqrt(g("a2") / g("vs"))
    if f.startswith("arms_"): return np.sqrt(g("a2_" + f[5:]) / g("n_" + f[5:]))
    if f == "jerk_1hz": return g("jerk") / g("vs")
    if f == "jerk_step_rate": return g("jerk_step") / sum(g(f"n_{c}") for c in ("car", "alks", "truck"))
    if f == "mild_s_all": return 0.1 * sum(g(f"mild_{c}") for c in ("car", "alks", "truck"))
    if f.startswith("mild_s_"): return 0.1 * g("mild_" + f[7:])
    if f.startswith("fuelgkm_"): return g("fuel_" + f[8:]) / g("dist_" + f[8:])
    if f == "lc_share": return g("m_ttc3_lc") / np.maximum(g("m_ttc3_all"), 1)
    if f == "ttc3_not4a": return g("ttc3") - g("ttc3_r_4a")
    if f == "ttc3_ge5": return g("ttc3_s_mid") + g("ttc3_s_hi")
    raise KeyError(f)
def pooled(cell, f): return np.mean([val(cell, l, f) for l in LEARN], axis=0)
def eff(P, O):
    mo = np.median(O)
    if mo <= 0: return None
    d = -(P - O) / mo * 100.0
    b = np.median(d[IDX], axis=1)
    return float(np.median(d)), *map(float, np.percentile(b, (2.5, 97.5)))
def meff(P, O):
    """mean-based, for small counts: -(mean P - mean O) / mean O x 100, ratio resampled"""
    mo = O.mean()
    if mo <= 0: return None
    b = -(P[IDX].mean(axis=1) - O[IDX].mean(axis=1)) / np.maximum(O[IDX].mean(axis=1), 1e-12) * 100.0
    return float(-(P.mean() - mo) / mo * 100.0), *map(float, np.percentile(b, (2.5, 97.5)))
def f3(t): return "n/a" if t is None else "%+.1f [%+.1f, %+.1f]" % t
FIELDS = [("REWARD", ["ttc_net", "ttc3", "brake_net", "collisions"]),
          ("TIED", ["ttc_half", "ttc2", "ttc15", "sev3", "E30", "E15", "b3_step", "alks_b3_step", "b45_net", "b45_step", "alks_b45_step", "b7_net", "b7_step", "alks_b7_step", "alks_full_events", "alks_full_moving", "free_brake_alks_step", "ev_all", "ev_alks", "ev_car", "ev_truck", "ev45_all", "ev45_alks", "ev45_car", "ev7_all", "casc_all", "robust_raw", "contact_steps"]),
          ("INDEP", ["gap25", "stop_gap", "arms_1hz", "arms_alks", "arms_car", "arms_truck", "jerk_1hz", "jerk_step_rate", "mild_s_all", "mild_s_alks", "mild_s_car", "mild_s_truck", "fuel_km", "fuelgkm_alks", "fuelgkm_car", "fuelgkm_truck", "undertakes", "pass_straight", "end_stop", "end_stop2", "halt_3a_0", "m_cong_vs", "lc_share", "teleports", "m_stuck_n"]),
          ("LOC", ["ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi", "ttc3_ge5", "ttc3_r_4a", "ttc3_r_3", "ttc3_r_ramp2", "ttc3_r_rest", "ttc3_not4a", "rt_3a", "rt_4a", "rt_3", "rt_ramp2", "rt_junction", "ttc15_s_lo", "ttc15_s_mid", "ttc15_s_hi", "ttc15_r_4a", "sev3_s_hi", "sev3_r_4a"]),
          ("CTX", ["all_delay", "passed"])]
CMP = ["p333", "os0_10_10", "3E-C_TRUCK", "nc"]
import sys
for cell in ("TRUCK", "S"):
    print(f"\n######## {cell}")
    for grp, fs in FIELDS:
        for f in fs:
            P = pooled(cell, f); L = [val(cell, l, f) for l in LEARN]
            lev = "v3w %.4g/%.4g" % (np.median(P), P.mean()) + " | " + " | ".join("%s %.4g/%.4g" % (o, np.median(val(cell, o, f)), val(cell, o, f).mean()) for o in CMP)
            print(f"\n[{grp}] {f}  levels median/mean per run: {lev}")
            # best of the 23 rules on this field
            meds = {o: (np.median(val(cell, o, f)), val(cell, o, f).mean()) for o in OPP}
            best = min(meds, key=lambda o: (meds[o][0], meds[o][1]))
            for o in CMP + ["BEST:" + best]:
                on = o.split(":")[-1]; O = val(cell, on, f)
                e = eff(P, O); m = meff(P, O)
                per = [eff(l, O) for l in L]; perm = [meff(l, O) for l in L]
                use = per if e is not None and np.median(O) >= 10 else perm
                tag = "med" if use is per else "mean"
                pts = " ".join("n/a" if p is None else "%+.0f" % p[0] for p in use)
                up = sum(p is not None and p[1] > 0 for p in use); dn = sum(p is not None and p[2] < 0 for p in use)
                print(f"   vs {o:22s} median-eff {f3(e):26s} mean-eff {f3(m):26s} learners({tag}) {pts}  CI>0:{up} CI<0:{dn}")
