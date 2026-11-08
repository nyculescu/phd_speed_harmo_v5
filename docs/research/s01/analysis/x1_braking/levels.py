"""What the controlled ALKS do: mean headway level by road (lv_sum_<road> / lv_n_<road>, 1-Hz ALKS samples, level 0 = 1.6 s ... 3 = 0.8 s,
the level the vehicle holds, acting only with V2V on), V2V-on share and level shares (m_dec_level_s, m_dec_off_s), level changes per
ALKS; event durations (m_dur_*). Per arm, seed-medians of the arm value (mean over learners). Then, across individual controlled runs'
arms (each learner and rule separately), Spearman between the arm's median level on each road and its median -4.5 event count."""
import pickle
from pathlib import Path

import numpy as np
from scipy import stats as sst

OUT = Path(__file__).resolve().parent
T = pickle.load(open(OUT / "test_rows.pkl", "rb"))
G = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": ["t0", "t1", "t2", "t3", "t4"], "sw": ["s0u500", "s1u500", "s2u500", "s3u500", "s4u500"],
     "bv3": ["d0u500", "d1u500", "d2u500", "d3u500", "d4u500"]}
ROADS = ["1", "2", "3a", "3", "4a", "4", "5", "r2", "rj2"]


def per_run(r):
    o = {f"lvl_{x}": (r.get(f"lv_sum_{x}", 0.0) / r[f"lv_n_{x}"]) if r.get(f"lv_n_{x}") else np.nan for x in ROADS}
    if "m_dec_level_s" in r:
        ls_, off = np.asarray(r["m_dec_level_s"], float), r["m_dec_off_s"]
        tot = ls_.sum() + off
        o["v2v_on"] = ls_.sum() / tot if tot else np.nan
        for i in range(4):
            o[f"share_l{i}_all"] = ls_[i] / tot if tot else np.nan     # share of all ALKS-seconds acting at level i
        o["chg_per_alks"] = r["m_dec_totals"]["changed"] / r["m_dec_vehicles"] if r["m_dec_vehicles"] else np.nan
        o["rev_share"] = r["m_dec_totals"]["reversals"] / max(r["m_dec_totals"]["changed"], 1)
    for c in ("car", "alks"):
        o[f"ev_s_mean_{c}"] = r[f"m_event_s_{c}"] / max(r[f"m_events_{c}"], 1)
        d = np.asarray(r[f"m_dur_{c}"], float)
        o[f"dur_ge2_{c}"] = d[3:].sum() / max(d.sum(), 1)     # share of events lasting >= 2 s
    o["ev45"] = sum(sum(r[f"m_peak_{c}"][3:]) for c in ("car", "alks", "truck"))
    o["ev45_car"], o["ev45_alks"] = sum(r["m_peak_car"][3:]), sum(r["m_peak_alks"][3:])
    o["ev5_alks"] = sum(r["m_peak_alks"][4:8])
    return o


def arm_vals(cell, names):
    seeds = sorted({s for (n, s) in T if n == f"{cell}|{names[0]}"})
    out = []
    for s in seeds:
        rs = [per_run(T[(f"{cell}|{a}", s)]) for a in names]
        out.append({k: np.nanmean([x[k] for x in rs]) if any(k in x for x in rs) else np.nan for k in rs[0]})
    return out


KEYS = ["lvl_2", "lvl_3a", "lvl_3", "lvl_4a", "lvl_4", "lvl_5", "lvl_r2", "v2v_on", "share_l0_all", "share_l3_all", "chg_per_alks", "rev_share",
        "ev_s_mean_car", "ev_s_mean_alks", "dur_ge2_car", "dur_ge2_alks", "ev45", "ev45_car", "ev45_alks", "ev5_alks"]
for cell in ("X1", "X2"):
    print(f"--- {cell}: seed-medians")
    print("arm       " + " ".join(f"{k[:12]:>12s}" for k in KEYS))
    rules = ["nc", "3e", "3ex1" if cell == "X1" else "3ex2", "p333", "os1_15_10"]
    for lab, names in [*[(g, G[g]) for g in G], *[(r, [r]) for r in rules]]:
        A = arm_vals(cell, names)
        print(f"{lab:9s} " + " ".join(f"{np.nanmedian([a[k] for a in A]) if not all(np.isnan(a.get(k, np.nan)) for a in A) else float('nan'):12.4g}" for k in KEYS))
    # learner/rule-level association
    singles = [n for g in G.values() for n in g] + ["3e", "3ex1" if cell == "X1" else "3ex2", "p333", "os1_15_10", "os0_10_10", "os1_10_0", "copy", "a4400_10_1",
                                                     "r4a1", "z33133", "lr1000_10_1", "lr1000_16_2", "lr400_13_2", "lr400_16_1"]
    M = {n: arm_vals(cell, [n]) for n in singles}
    for x in ("lvl_3", "lvl_4a", "lvl_2", "v2v_on", "share_l3_all"):
        xs = [np.nanmedian([a[x] for a in M[n]]) for n in singles]
        for y in ("ev45", "ev45_car", "ev45_alks", "ev5_alks"):
            ys = [np.nanmedian([a[y] for a in M[n]]) for n in singles]
            ok = [i for i in range(len(xs)) if np.isfinite(xs[i])]
            rho, pv = sst.spearmanr([xs[i] for i in ok], [ys[i] for i in ok])
            print(f"  {cell} across {len(ok)} controlled arms (learners and rules): Spearman({x}, {y}) = {rho:.2f} (p {pv:.3f})")
