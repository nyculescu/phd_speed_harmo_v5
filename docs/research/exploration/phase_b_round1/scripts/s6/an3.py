"""EXPLORATORY. Shares of v3w's close-following reduction by speed band and road; rare events; rank correlations; recorded read6 v2.3 entries."""
import json
import numpy as np
from scipy.stats import spearmanr
exec(open("an1.py").read().split("FIELDS = [")[0])
ARMS = sorted({k.split("|")[1] for k in Z if "|" in k})
for cell in ("TRUCK", "S"):
    print(f"\n#### {cell}")
    # rare events: totals over all runs
    for f in ("collisions", "contact_steps", "gap25", "teleports", "m_stuck_n", "alks_full_moving"):
        tot = {a: float(val(cell, a, f).sum()) for a in ARMS}
        nz = {a: v for a, v in tot.items() if v}
        lw = {l: tot[l] for l in LEARN}
        rules = sum(tot[o] for o in OPP)
        print(f"  {f}: learners (sum over 240 runs each) {lw}; 23 rules total {rules:.0f} over {23 * n} runs; nc {tot['nc']:.0f}; runs with >0: v3w {sum(int((val(cell, l, f) > 0).sum()) for l in LEARN)} of {5 * n}, rules {sum(int((val(cell, o, f) > 0).sum()) for o in OPP)} of {23 * n}")
    # shares of the reduction (difference of means over seeds), ratio bootstrapped
    for o in ("p333", "3E-C_TRUCK", "nc"):
        tot = val(cell, o, "ttc3") - pooled(cell, "ttc3")
        print(f"  reduction of mean ttc3 vs {o}: {tot.mean():.1f} per run")
        for lab, parts in (("speed", ("ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi")), ("road", ("ttc3_r_4a", "ttc3_r_3", "ttc3_r_ramp2", "ttc3_r_rest")), ("road group", ("rt_3a", "rt_4a", "rt_3", "rt_ramp2", "rt_junction"))):
            out = []
            for p in parts:
                d = val(cell, o, p) - pooled(cell, p)
                b = d[IDX].mean(axis=1) / tot[IDX].mean(axis=1) * 100
                out.append("%s %.1f %% [%.1f, %.1f]" % (p, d.mean() / tot.mean() * 100, *np.percentile(b, (2.5, 97.5))))
            print(f"    by {lab}: " + "; ".join(out))
    # composition of each arm's own ttc3
    for a in ("v3w", "p333", "3E-C_TRUCK", "nc"):
        g = (lambda f: pooled(cell, f)) if a == "v3w" else (lambda f: val(cell, a, f))
        t = g("ttc3").mean()
        print(f"  {a} own ttc3 composition (means): lo {g('ttc3_s_lo').mean() / t * 100:.1f} %, mid {g('ttc3_s_mid').mean() / t * 100:.1f} %, hi {g('ttc3_s_hi').mean() / t * 100:.1f} %; 4a {g('ttc3_r_4a').mean() / t * 100:.1f} %, 3 {g('ttc3_r_3').mean() / t * 100:.1f} %, ramp2 {g('ttc3_r_ramp2').mean() / t * 100:.1f} %, rest {g('ttc3_r_rest').mean() / t * 100:.1f} %")
    # rank correlation of per-seed paired differences (pooled v3w - p333): does a measure move with the rewarded count?
    d0 = pooled(cell, "ttc3") - val(cell, "p333", "ttc3")
    cs = []
    for f in ("ttc_half", "ttc2", "ttc15", "sev3", "brake_net", "b3_step", "b45_step", "ev45_all", "ev45_car", "stop_gap", "arms_1hz", "arms_car", "jerk_1hz", "jerk_step_rate", "mild_s_all", "fuel_km", "undertakes", "end_stop2", "end_stop", "m_cong_vs", "all_delay"):
        d = pooled(cell, f) - val(cell, "p333", f)
        cs.append("%s %.2f" % (f, spearmanr(d0, d).statistic))
    print("  Spearman of paired differences (v3w - p333) with the ttc3 difference: " + ", ".join(cs))
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
for cell, M in (("TRUCK", J['cells']['TRUCK']['map_report_only']), ("S", J['S']['map_report_only'])):
    print(f"\n#### recorded read6 v2.3 map_report_only, {cell}: effect [ci95], positive = v3w lower; medians P/O")
    for k in ("ttc2", "ttc15", "sev3", "gap25", "events_ge45", "robust_per_served", "b45_step", "b3_step", "robust_braking", "alks_past_limit", "contact_steps", "ttc3_lc_share", "osc_kmh", "osc_kmh_nc", "jam_share", "jams", "congested_km_mean", "congested_share", "m_cong_vs"):
        out = []
        for o in ("p333", "os0_10_10", "3E-C_TRUCK", "nc"):
            e = M[o].get(k)
            if e is None: out.append(f"{o} absent"); continue
            if e.get("effect") is None: out.append(f"{o} n/a ({e.get('why')}; P {e.get('median_P')}, O {e.get('median_O')})"); continue
            out.append("%s %+.2f [%+.2f, %+.2f] (%.4g/%.4g)" % (o, e["effect"], *e["ci95"], e["median_P"], e["median_O"]))
        print(f"  {k}: " + " | ".join(out))
