# Pass 3: tracks, lane sequences, merges per period. Exploratory, before protocol approval.
import sys, collections, pickle
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
S = sys.argv[1]
FT = 0.3048
SITES = {"us-101": dict(src=6, dst=5, ramp=7, off=8, bounds=["08:05", "08:20"]), "i-80": dict(src=7, dst=6, ramp=7, off=None, bounds=["16:30", "17:15"])}
out = {}
for loc, g in SITES.items():
    d = pd.read_pickle(f"{S}/{loc}.pkl").sort_values(["Vehicle_ID", "Total_Frames", "Global_Time"]).reset_index(drop=True)
    new = (d["Vehicle_ID"].diff() != 0) | (d["Total_Frames"].diff() != 0) | (d["Global_Time"].diff() != 100)
    d["trk"] = new.cumsum()
    print("=====", loc, "tracks (split at time gaps):", d["trk"].nunique())
    # duplicates of one vehicle across tracks: same time, lane and position
    dup = d.duplicated(["Global_Time", "Lane_ID", "Local_Y", "Local_X"], keep=False)
    print("rows sharing time+lane+position with another row:", int(dup.sum()))
    first = d.groupby("trk").first(); last = d.groupby("trk").last()
    seq = d.loc[(d["Lane_ID"] != d["Lane_ID"].shift()) | new, ["trk", "Lane_ID"]].groupby("trk")["Lane_ID"].agg(lambda s: "-".join(map(str, s)))
    vc = seq[seq.str.contains(str(g["ramp"])) | seq.str.contains(str(g["src"]))].value_counts()
    print("lane sequences that touch the ramp/aux lanes (top 30 of", len(vc), "):"); print(vc.head(30).to_string())
    # raw transitions src->dst and back
    prev_lane = d["Lane_ID"].shift(); same = ~new
    tr = d[same & (prev_lane != d["Lane_ID"])].assign(frm=prev_lane[same & (prev_lane != d["Lane_ID"])].astype(int))
    print("lane-change counts (from,to):"); print(tr.groupby(["frm", "Lane_ID"]).size().to_string())
    m = tr[(tr["frm"] == g["src"]) & (tr["Lane_ID"] == g["dst"])]
    per_trk = m.groupby("trk").size()
    print("raw src->dst transitions:", len(m), "tracks with one:", int((per_trk == 1).sum()), "with more than one (flicker or re-entry):", int((per_trk > 1).sum()))
    back = tr[(tr["frm"] == g["dst"]) & (tr["Lane_ID"] == g["src"])]
    print("dst->src transitions:", len(back), "tracks:", back["trk"].nunique())
    # where the ramp label changes to the aux label (us-101) and aux to off-ramp
    if loc == "us-101":
        for a, b in ((7, 6), (6, 8), (5, 6), (6, 5)):
            y = tr[(tr["frm"] == a) & (tr["Lane_ID"] == b)]["Local_Y"]
            print(f"Local_Y at {a}->{b}: n={len(y)} min={y.min():.0f} p05={y.quantile(.05):.0f} p50={y.median():.0f} p95={y.quantile(.95):.0f} max={y.max():.0f} ft")
    else:
        y = m["Local_Y"]
        print(f"Local_Y at 7->6: n={len(y)} min={y.min():.0f} p05={y.quantile(.05):.0f} p50={y.median():.0f} p95={y.quantile(.95):.0f} max={y.max():.0f} ft")
        r = d[d["Lane_ID"] == 7]
        b = (r["Local_Y"] // 50 * 50).astype(int)
        l6 = d[d["Lane_ID"] == 6]; b6 = (l6["Local_Y"] // 50 * 50).astype(int)
        print("lane 7 and lane 6 median Local_X by 50-ft Local_Y bin (ramp angle, taper):")
        print(pd.DataFrame({"x7_p50": r.groupby(b)["Local_X"].median(), "n7": r.groupby(b).size(), "x6_p50": l6.groupby(b6)["Local_X"].median(), "x6_p95": l6.groupby(b6)["Local_X"].quantile(.95)}).round(1).to_string())
    print("first-seen lane of tracks:", first["Lane_ID"].value_counts().sort_index().to_dict())
    print("first Local_Y of tracks first seen on ramp lane", g["ramp"], ":", first[first["Lane_ID"] == g["ramp"]]["Local_Y"].describe().round(1).to_dict())
    print("first Local_Y of tracks first seen on src lane", g["src"], ":", first[first["Lane_ID"] == g["src"]]["Local_Y"].describe().round(1).to_dict())
    d.to_pickle(f"{S}/{loc}_trk.pkl")
