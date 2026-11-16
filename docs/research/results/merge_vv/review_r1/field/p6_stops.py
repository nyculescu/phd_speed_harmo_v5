# Pass 6: are I-80 on-ramp stops lane-end waits beside moving traffic, or part of a queue? Exploratory, before protocol approval.
import sys
import numpy as np, pandas as pd
S = sys.argv[1]; FT = 0.3048
d = pd.read_pickle(f"{S}/i-80_trk.pkl")
k = 5; same = (d["trk"].shift(k) == d["trk"]) & (d["trk"].shift(-k) == d["trk"])
d["v_s"] = ((d["Local_Y"].shift(-k) - d["Local_Y"].shift(k)) / (2 * k * 0.1)).where(same) * FT
first = d.groupby("trk")["Lane_ID"].first()
r = d[d["trk"].isin(first[first == 7].index) & (d["Local_X"] >= 72.5) & (d["Global_Time"] % 1000 == 0)]     # 1-Hz samples before the lateral crossing
print("on-ramp vehicle-seconds right of x = 72.5 ft (1 Hz):", len(r), "; below 1 m/s:", int((r["v_s"] < 1.0).sum()), "; vehicles with any:", r[r["v_s"] < 1.0]["trk"].nunique(), "of", r["trk"].nunique())
st = r[r["v_s"] < 1.0]
print("Local_Y of stopped samples (ft) p05/p25/p50/p75/p95:", np.round(st["Local_Y"].quantile([.05, .25, .5, .75, .95]), 0).tolist(), "; share past 566 ft (last 100 ft before the label end 666):", round(float((st["Local_Y"] > 566).mean()), 3))
l6 = d[(d["Lane_ID"] == 6) & (d["Local_X"] < 72.5) & d["Global_Time"].isin(st["Global_Time"].unique())][["Global_Time", "Local_Y", "v_s"]]
g6 = {t: (a["Local_Y"].to_numpy(), a["v_s"].to_numpy()) for t, a in l6.groupby("Global_Time")}
adj = []
for t, y in zip(st["Global_Time"].to_numpy(), st["Local_Y"].to_numpy()):
    if t in g6:
        yy, vv = g6[t]; m = np.abs(yy - y) < 30.0 / FT
        adj.append(np.nanmean(vv[m]) if m.any() and np.isfinite(vv[m]).any() else np.nan)
    else:
        adj.append(np.nan)
adj = np.array(adj)
print("stopped samples with lane-6 vehicles within 30 m:", int(np.isfinite(adj).sum()), "of", len(adj), "; lane-6 mean speed there, m/s p25/p50/p75/p95:", np.round(np.nanquantile(adj, [.25, .5, .75, .95]), 2).tolist())
print("share of stopped ramp samples beside lane-6 traffic above 2 m/s:", round(float((adj > 2.0).sum() / np.isfinite(adj).sum()), 3), "; above 5 m/s:", round(float((adj > 5.0).sum() / np.isfinite(adj).sum()), 3))
allr = r.copy()
print("ramp samples per speed band (m/s) <1, 1-5, 5-10, >10:", [int(((allr["v_s"] >= a) & (allr["v_s"] < b)).sum()) for a, b in ((-9, 1), (1, 5), (5, 10), (10, 99))])
