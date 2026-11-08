"""(d) Paired comparisons of the space-time metrics and of the plant's period / road splits of the 1-Hz conflict counts, policies vs
rules; and the seed-level association between the excess fast entries and the excess -4.5 events (v3w - nc)."""
import pickle

import numpy as np
from scipy import stats as sst

from common_x import OUT, POLICIES, RULES, Q, arm_mean, diff_ci, effect95, load_T, med, GROUPS

S = pickle.load(open(OUT / "st_rows.pkl", "rb"))
T = load_T()


def armS(cell, g):
    return arm_mean(S, [f"{cell}|{n}" for n in GROUPS.get(g, [g])], Q)


def armT(cell, g):
    return arm_mean(T, [f"{cell}|{n}" for n in GROUPS.get(g, [g])], Q)


STM = ["entries_win", "fast_entries_win", "appr_kmh_win", "in_kmh_win", "queue_m_win", "entries_after", "fast_entries_after", "appr_kmh_after",
       "queue_m_after", "macro_dec_appr_win", "macro_dec_zone_win", "macro_dec_up_win", "macro_dec_appr_after", "macro_dec_up_after", "macro_dec_up_other",
       "macro_dec_appr_other", "macro_dec_zone_other", "macro_dec_down_other"]
PER = ["sev3", "sev3_p_before", "sev3_p_taper", "sev3_p_hold", "sev3_p_after", "sev3_p_rest", "sev3_r_4a", "sev3_r_3", "sev3_r_ramp2", "sev3_r_rest",
       "ttc3", "ttc3_p_before", "ttc3_p_taper", "ttc3_p_hold", "ttc3_p_after", "ttc3_p_rest", "ttc3_r_4a", "ttc3_r_3", "ttc3_r_ramp2", "ttc3_r_rest"]
n = 0
lines = ["cell\tP\tO\tmetric\tmedP\tmedO\teffect_pct\tlo\thi\tdiff\tdlo\tdhi"]
for cell in ("X1", "X2"):
    for p in (*POLICIES, "3e", "p333"):
        for o in ("nc",) if p in ("3e", "p333") else ("nc", "3e"):
            for src, ms, f in (("st", STM, armS), ("row", PER, armT)):
                A, B = f(cell, p), f(cell, o)
                for m in ms:
                    mo = med(B, m)
                    e = effect95(A, B, m) if abs(mo) > 1e-9 else (float("nan"),) * 3
                    d = diff_ci(A, B, m)
                    n += 1
                    lines.append("\t".join([cell, p, o, m, f"{med(A, m):.5g}", f"{mo:.5g}", *[f"{x:.2f}" for x in e], *[f"{x:.5g}" for x in d]]))
(OUT / "st_stats.tsv").write_text("\n".join(lines) + "\n")
print("comparisons:", n)
for ln in lines[1:]:
    f = ln.split("\t")
    if f[1] == "v3w" and f[2] == "nc" or (f[1] in ("3e", "p333") and f[0] == "X1" and f[3] in ("fast_entries_win", "queue_m_win", "appr_kmh_win")):
        print(f"{f[0]} {f[1]:4s} vs {f[2]:3s} {f[3]:22s} medP {float(f[4]):9.4g} medO {float(f[5]):9.4g} eff {f[6]:>8}% [{f[7]:>8},{f[8]:>8}] diff {float(f[9]):9.4g} [{float(f[10]):9.4g},{float(f[11]):9.4g}]")
# seed-level association, X1 and X2: excess fast entries vs excess -4.5 events, v3w - nc and 3e - nc
for cell in ("X1", "X2"):
    for p in ("v3w", "3e", "p333"):
        As, Bs, At, Bt = armS(cell, p), armS(cell, "nc"), armT(cell, p), armT(cell, "nc")
        ds = sorted(set(As) & set(Bs))
        x = np.array([As[s]["fast_entries_win"] - Bs[s]["fast_entries_win"] for s in ds])
        for k in ("ev45_all", "ev45_car", "ev45_alks", "ev5_alks", "ev4_all"):
            y = np.array([At[s][k] - Bt[s][k] for s in ds])
            rho, pv = sst.spearmanr(x, y)
            print(f"{cell} {p} - nc: Spearman(d fast_entries_win, d {k}) = {rho:.2f} (p {pv:.3f}, n {len(ds)})")
    # within nc across seeds
    Bs, Bt = armS(cell, "nc"), armT(cell, "nc")
    ds = sorted(Bs)
    x = np.array([Bs[s]["fast_entries_win"] for s in ds])
    for k in ("ev45_all", "ev45_car", "ev45_alks"):
        rho, pv = sst.spearmanr(x, [Bt[s][k] for s in ds])
        print(f"{cell} nc across seeds: Spearman(fast_entries_win, {k}) = {rho:.2f} (p {pv:.3f})")
