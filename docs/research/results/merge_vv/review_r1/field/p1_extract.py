# Pass 1: Location counts; keep us-101 and i-80 rows, drop exact duplicates, save compact files.
import sys, collections
import numpy as np, pandas as pd
src, out = sys.argv[1], sys.argv[2]
cols = ["Vehicle_ID","Frame_ID","Total_Frames","Global_Time","Local_X","Local_Y","v_length","v_Class","v_Vel","v_Acc","Lane_ID","Preceding","Following","Space_Headway","Time_Headway","Location"]
cnt = collections.Counter()
keep = {"us-101": [], "i-80": []}
for ch in pd.read_csv(src, usecols=cols, chunksize=1_000_000, dtype={"Location": "category"}, thousands=","):
    cnt.update(ch["Location"].astype(str).value_counts().to_dict())
    for loc in keep:
        keep[loc].append(ch[ch["Location"].astype(str) == loc].drop(columns="Location"))
print("Location row counts (raw):", dict(cnt))
for loc, parts in keep.items():
    d = pd.concat(parts, ignore_index=True)
    n0 = len(d)
    d = d.drop_duplicates()
    n1 = len(d)
    d2 = d.drop_duplicates(["Vehicle_ID","Total_Frames","Global_Time"])
    print(loc, "raw", n0, "after exact-duplicate drop", n1, "unique (veh,total_frames,time)", len(d2))
    print(d.dtypes.to_string())
    d2.sort_values(["Global_Time","Vehicle_ID"]).reset_index(drop=True).to_pickle(f"{out}/{loc}.pkl")
