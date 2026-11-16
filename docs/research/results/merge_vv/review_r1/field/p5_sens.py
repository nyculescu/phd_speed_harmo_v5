# Pass 5: sensitivity of the merge quantities to the extraction rule; sampling noise of period medians. Exploratory, before protocol approval.
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
S = sys.argv[1]; FT = 0.3048
rng = np.random.default_rng(20261115)
def boot(x, f=np.median, n=2000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 5: return (np.nan, np.nan)
    b = [f(rng.choice(x, len(x))) for _ in range(n)]
    return tuple(np.round(np.quantile(b, [.025, .975]), 2))
for loc in ("i-80",):
    m = pd.read_pickle(f"{S}/{loc}_merges.pkl"); m = m[m["merged"] & (m["cls"] != 1)].copy()
    d = pd.read_pickle(f"{S}/{loc}_trk.pkl")
    print("=====", loc, "merges (motorcycles out):", len(m))
    for thr in (0.5, 1.0, 2.0):
        print(f"  share with min raw speed < {thr} m/s in the 10 s before the label merge, per period:", m.groupby("per").apply(lambda a: round(float((a["vmin10"] < thr / FT).mean()), 3), include_groups=False).tolist(),
              "; 1-s smoothed:", m.groupby("per").apply(lambda a: round(float((a["vsmin10"] < thr / FT).mean()), 3), include_groups=False).tolist())
    m["rel_ms"] = (m["vs_m"] - m["fol_vs"]) * FT
    print("  merger speed minus target-lane follower speed at the merge, m/s, per period p10/p50/p90:", [np.round(np.nanquantile(a["rel_ms"], [.1, .5, .9]), 2).tolist() for _, a in m.groupby("per")])
    print("  share merging below 2 m/s:", m.groupby("per").apply(lambda a: round(float((a["vs_m"] * FT < 2.0).mean()), 3), include_groups=False).tolist(),
          "; share merging more than 3 m/s slower than the follower:", m.groupby("per").apply(lambda a: round(float((a["rel_ms"] < -3.0).mean()), 3), include_groups=False).tolist())
    m["lag_s"] = np.where(m["fol_vs"] > 1.0 / FT, m["lag_gap_ft"] / m["fol_vs"], np.nan)
    dv = m["fol_vs"] - m["vs_m"]
    m["ttc"] = np.where((dv > 0) & (m["lag_gap_ft"] > 0), m["lag_gap_ft"] / dv, np.nan)
    for per, a in m.groupby("per"):
        print(f"  period {per}: n={len(a)} lag time gap median {np.nanmedian(a['lag_s']):.2f} boot95 {boot(a['lag_s'])} (n={int(a['lag_s'].notna().sum())}); lag gap m median {np.nanmedian(a['lag_gap_ft']) * FT:.1f} boot95 {tuple(np.round(np.array(boot(a['lag_gap_ft'])) * FT, 1))};"
              f" follower TTC, closing pairs only: n={int(a['ttc'].notna().sum())} median {np.nanmedian(a['ttc']):.1f} boot95 {boot(a['ttc'])}; TTC<3 s count {int((a['ttc'] < 3).sum())}; TTC<3 s with raw v_Vel: {int((((a['fol_v'] - a['v_m']) > 0) & (a['lag_gap_ft'] > 0) & (a['lag_gap_ft'] / (a['fol_v'] - a['v_m']).clip(lower=1e-9) < 3)).sum())}")
    if loc == "i-80":
        k = 5; same = (d["trk"].shift(k) == d["trk"]) & (d["trk"].shift(-k) == d["trk"])
        d["v_s"] = ((d["Local_Y"].shift(-k) - d["Local_Y"].shift(k)) / (2 * k * 0.1)).where(same)
        idx = d.set_index(["Vehicle_ID", "Global_Time"])[["Local_Y", "Local_X", "v_s", "v_length", "Lane_ID", "Preceding", "Following"]]
        byt = {t: g for t, g in d[d["trk"].isin(m["trk"])].groupby("trk")}
        for xl in (70.5, 72.5, 74.5):
            ys, neg, lag, n = [], 0, [], 0
            for _, o in m.iterrows():
                t = byt[o["trk"]]; x = t["Local_X"].to_numpy()
                run = np.convolve((x < xl).astype(int), np.ones(10, int), "valid") == 10
                if not run.any(): continue
                j = int(np.argmax(run)); r = t.iloc[j]; n += 1
                ys.append((r["Local_Y"], o["per"], r["Lane_ID"]))
                f = int(r["Following"])
                if f > 0 and (f, r["Global_Time"]) in idx.index:
                    fr = idx.loc[(f, r["Global_Time"])]
                    gap = r["Local_Y"] - r["v_length"] - fr["Local_Y"]
                    neg += gap < 0
                    if fr["v_s"] > 1.0 / FT: lag.append((gap / fr["v_s"], o["per"]))
            y = pd.DataFrame(ys, columns=["y", "per", "lane"]); lg = pd.DataFrame(lag, columns=["lag", "per"])
            print(f"  lateral rule x < {xl} ft held 1 s: found {n}; still labelled lane 7 at crossing: {int((y['lane'] == 7).sum())}; Local_Y median per period (ft) {y.groupby('per')['y'].median().round(0).tolist()}; share crossing past 666 ft {round(float((y['y'] > 666).mean()), 3)};"
                  f" negative lag gaps {int(neg)}; lag time gap median per period {lg.groupby('per')['lag'].median().round(2).tolist()}")
