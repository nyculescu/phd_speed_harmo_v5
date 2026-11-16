# Pass 4: merge quantities per site and period. Exploratory, before protocol approval.
import sys, json
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
S = sys.argv[1]
FT = 0.3048
TZ = "America/Los_Angeles"
SITES = {"us-101": dict(main_max=5, side=(6, 7, 8), bounds=["2005-06-15 08:05", "2005-06-15 08:20"], y0=655.0, y1=1310.0),
         "i-80": dict(main_max=6, side=(7,), bounds=["2005-04-13 16:30", "2005-04-13 17:15"], y0=333.0, y1=666.0)}
res = {}
for loc, g in SITES.items():
    d = pd.read_pickle(f"{S}/{loc}_trk.pkl")
    assert not d.duplicated(["Vehicle_ID", "Global_Time"]).any(), "vehicle id not unique at a time"
    d["v_s"] = np.nan
    # 1-s central difference of Local_Y inside a track (ft/s)
    k = 5
    same = (d["trk"].shift(k) == d["trk"]) & (d["trk"].shift(-k) == d["trk"])
    d.loc[same, "v_s"] = ((d["Local_Y"].shift(-k) - d["Local_Y"].shift(k)) / (2 * k * 0.1))[same]
    idx = d.set_index(["Vehicle_ID", "Global_Time"])[["Local_Y", "Local_X", "v_Vel", "v_s", "v_length", "Lane_ID", "Preceding", "v_Class"]]
    first = d.groupby("trk")["Lane_ID"].first()
    ramp_trk = first[first == 7].index
    r = d[d["trk"].isin(ramp_trk)]
    bounds = [pd.Timestamp(b, tz=TZ).value // 10**6 for b in g["bounds"]]
    rows = []
    for trk, t in r.groupby("trk", sort=False):
        lane = t["Lane_ID"].to_numpy(); n = len(t)
        main = lane <= g["main_max"]
        if not main.any():
            rows.append(dict(trk=trk, merged=False, cls=int(t["v_Class"].iloc[0]), t0=int(t["Global_Time"].iloc[0]))); continue
        i = int(np.argmax(main))
        stay = int(main[i:i + 30].sum())     # of the next 3 s
        back = bool((~main[i:]).any())
        y = t["Local_Y"].to_numpy(); x = t["Local_X"].to_numpy(); v = t["v_Vel"].to_numpy(); vs = t["v_s"].to_numpy(); tm = t["Global_Time"].to_numpy()
        j0 = max(0, i - 100)
        o = dict(trk=trk, merged=True, cls=int(t["v_Class"].iloc[0]), t0=int(tm[0]), t_m=int(tm[i]), from_lane=int(lane[i - 1]) if i > 0 else -1, y_m=y[i], x_m=x[i], v_m=v[i], vs_m=vs[i],
                 obs_before_s=i * 0.1, vmin10=float(v[j0:i + 1].min()), vsmin10=float(np.nanmin(vs[j0:i + 1])) if np.isfinite(vs[j0:i + 1]).any() else np.nan,
                 stay3=stay, back=back, y_first=y[0], fol=int(t["Following"].iloc[i]), prec=int(t["Preceding"].iloc[i]), L=float(t["v_length"].iloc[i]))
        if loc == "i-80":     # lateral rule: front centre left of the lane-6 right edge (lane-6 median x + 6 ft), held 1 s
            xl = 72.5
            inside = x < xl
            run = np.convolve(inside.astype(int), np.ones(10, int), "valid") == 10 if n >= 10 else np.array([], bool)
            if run.any():
                jx = int(np.argmax(run)); o |= dict(y_x=y[jx], t_x=int(tm[jx]), ix=jx)
        f = o["fol"]
        if f > 0 and (f, o["t_m"]) in idx.index:
            fr = idx.loc[(f, o["t_m"])]
            gap = (o["y_m"] - o["L"]) - fr["Local_Y"]
            o |= dict(fol_lane=int(fr["Lane_ID"]), fol_prec=int(fr["Preceding"]), lag_gap_ft=float(gap), fol_v=float(fr["v_Vel"]), fol_vs=float(fr["v_s"]), fol_cls=int(fr["v_Class"]))
        p = o["prec"]
        if p > 0 and (p, o["t_m"]) in idx.index:
            pr = idx.loc[(p, o["t_m"])]
            o |= dict(lead_gap_ft=float(pr["Local_Y"] - pr["v_length"] - o["y_m"]), lead_v=float(pr["v_Vel"]))
        rows.append(o)
    m = pd.DataFrame(rows)
    m["per"] = np.searchsorted(bounds, m["t_m"].fillna(m["t0"]).to_numpy(), side="right") + 1
    m.to_pickle(f"{S}/{loc}_merges.pkl")
    print("=====", loc, "on-ramp tracks", len(m), "merged into the main lanes", int(m["merged"].sum()), "not merged (left the view on a side lane)", int((~m["merged"]).sum()))
    mm = m[m["merged"]].copy()
    print("class of merging vehicles (1 motorcycle, 2 car, 3 truck):", mm["cls"].value_counts().to_dict())
    print("from lane:", mm["from_lane"].value_counts().to_dict())
    print("stayed in main all of the next 3 s:", int((mm["stay3"] >= np.minimum(30, 30)).sum()), "went back to a side lane later:", int(mm["back"].sum()))
    mm = mm[mm["cls"] != 1]
    mm["pos_m"] = (mm["y_m"] - g["y0"]) * FT
    mm["pos_share"] = (mm["y_m"] - g["y0"]) / (g["y1"] - g["y0"])
    mm["stop_raw"] = mm["vmin10"] < 1.0 / FT
    mm["stop_s"] = mm["vsmin10"] < 1.0 / FT
    mm["obs10"] = mm["obs_before_s"] >= 10.0
    mm["has_fol"] = mm["lag_gap_ft"].notna()
    mm["lag_m"] = mm["lag_gap_ft"] * FT
    mm["lag_s"] = np.where(mm["fol_vs"] > 1.0 / FT, mm["lag_gap_ft"] / mm["fol_vs"], np.nan)
    dv = mm["fol_vs"] - mm["vs_m"]
    mm["ttc"] = np.where((dv > 0) & (mm["lag_gap_ft"] > 0), mm["lag_gap_ft"] / dv, np.inf)
    mm.loc[~mm["has_fol"], "ttc"] = np.nan
    mm["fol_ok"] = mm["fol_prec"] == d.set_index("trk").loc[mm["trk"]].groupby("trk")["Vehicle_ID"].first().reindex(mm["trk"]).to_numpy()
    print("followers found:", int(mm["has_fol"].sum()), "of", len(mm), "; follower in a main lane:", int((mm["fol_lane"] <= g["main_max"]).sum()), "; follower's Preceding is the merger:", int(mm["fol_ok"].sum()), "; negative net lag gap:", int((mm["lag_gap_ft"] < 0).sum()))
    def q(s, p): return float(np.nanquantile(s, p)) if s.notna().any() else np.nan
    tab = []
    for per, a in list(mm.groupby("per")) + [("all", mm)]:
        tab.append(dict(per=per, n=len(a), pos_m_p50=q(a["pos_m"], .5), pos_share_p10=q(a["pos_share"], .1), pos_share_p50=q(a["pos_share"], .5), pos_share_p90=q(a["pos_share"], .9),
                        v_m_p50_ms=q(a["vs_m"], .5) * FT, obs10_share=a["obs10"].mean(), stop_raw=a["stop_raw"].mean(), stop_smooth=a["stop_s"].mean(), stop_obs10=a.loc[a["obs10"], "stop_s"].mean(),
                        fol_share=a["has_fol"].mean(), lag_m_p50=q(a["lag_m"], .5), lag_s_n=int(a["lag_s"].notna().sum()), lag_s_p50=q(a["lag_s"], .5), fol_v_p50_ms=q(a["fol_vs"], .5) * FT,
                        ttc_closing_share=float(np.isfinite(a["ttc"]).sum() / max(a["has_fol"].sum(), 1)), ttc_lt3_share=float((a["ttc"] < 3.0).sum() / max(a["has_fol"].sum(), 1)),
                        ttc_p50_closing=q(a["ttc"].where(np.isfinite(a["ttc"])), .5)))
    tab = pd.DataFrame(tab).round(3)
    print(tab.T.to_string())
    hist = np.histogram(mm["pos_share"].clip(-0.2, 1.3), bins=np.arange(-0.2, 1.31, 0.1))[0]
    print("merge-position share histogram, bins of 0.1 from -0.2 to 1.3:", hist.tolist())
    print("Local_Y at merge (ft): ", np.round(np.quantile(mm["y_m"], [0, .05, .25, .5, .75, .95, 1]), 0).tolist())
    if loc == "i-80":
        ok = mm["y_x"].notna()
        print("lateral rule found for", int(ok.sum()), "of", len(mm), "; Local_Y at lateral crossing (ft):", np.round(np.quantile(mm.loc[ok, "y_x"], [0, .05, .25, .5, .75, .95, 1]), 0).tolist())
        print("label change minus lateral crossing, s:", np.round(np.quantile((mm.loc[ok, "t_m"] - mm.loc[ok, "t_x"]) / 1000.0, [0, .05, .25, .5, .75, .95, 1]), 1).tolist())
        print("share of label merges at Local_Y >= 660 ft:", round(float((mm["y_m"] >= 660).mean()), 3), "; Local_X at label change quantiles:", np.round(np.quantile(mm["x_m"], [.05, .25, .5, .75, .95]), 1).tolist())
        for per, a in mm[ok].groupby("per"):
            print("  period", per, "n", len(a), "lateral-crossing Local_Y p10/p50/p90:", np.round(np.quantile(a["y_x"], [.1, .5, .9]), 0).tolist())
    # speed noise: raw v_Vel against the 1-s central difference at the merge frame
    e = (mm["v_m"] - mm["vs_m"]).dropna()
    print("raw v_Vel minus 1-s central difference at merge, ft/s: p05/p50/p95", np.round(np.quantile(e, [.05, .5, .95]), 2).tolist())
    res[loc] = tab.to_dict("records")
json.dump(res, open(f"{S}/p4_table.json", "w"), indent=1)
