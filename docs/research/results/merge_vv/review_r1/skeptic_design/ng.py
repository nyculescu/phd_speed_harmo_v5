# Lane-ID transitions at the I-80 and US-101 on-ramps: where along the road (Local_Y, feet) and across (Local_X) they happen.
import pandas as pd, numpy as np
src = "/home/catalin/work/phd/v5b1_data/ngsim/ngsim_8ect-6jqj.csv"
cols = ["Vehicle_ID", "Frame_ID", "Global_Time", "Local_X", "Local_Y", "Lane_ID", "Location", "v_Vel"]
parts = []
for ch in pd.read_csv(src, usecols=cols, chunksize=2_000_000):
    ch = ch[ch.Location.isin(["i-80", "us-101"])]
    parts.append(ch)
d = pd.concat(parts).drop_duplicates(["Location", "Vehicle_ID", "Global_Time"])
d = d.sort_values(["Location", "Vehicle_ID", "Global_Time"])
print(d.groupby("Location").size())
print(d.groupby(["Location", "Lane_ID"]).Local_Y.agg(["count", "min", "max"]))
d["pl"] = d.groupby(["Location", "Vehicle_ID"]).Lane_ID.shift()
d["px"] = d.groupby(["Location", "Vehicle_ID"]).Local_X.shift()
t = d[(d.pl.notna()) & (d.pl != d.Lane_ID)]
for loc, a, b in [("i-80", 7, 6), ("us-101", 6, 5), ("us-101", 7, 6)]:
    x = t[(t.Location == loc) & (t.pl == a) & (t.Lane_ID == b)]
    print(loc, a, "->", b, "n", len(x), "Local_Y quantiles", np.round(np.percentile(x.Local_Y, [0, 5, 25, 50, 75, 95, 100]), 1), "Local_X med prev/now", round(x.px.median(), 2), round(x.Local_X.median(), 2))
    print("   Global_Time span (min):", round((x.Global_Time.max() - x.Global_Time.min()) / 6e4, 1))
d.to_pickle("ng.pkl")
