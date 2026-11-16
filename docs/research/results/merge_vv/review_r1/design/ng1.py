import pandas as pd, numpy as np, sys
src = "/home/catalin/work/phd/v5b1_data/ngsim/ngsim_8ect-6jqj.csv"
cols = ["Vehicle_ID", "Frame_ID", "Global_Time", "Local_Y", "v_length", "v_Class", "v_Vel", "Lane_ID", "Following", "Location"]
keep = []
nrows = {}
for ch in pd.read_csv(src, usecols=cols, chunksize=1_000_000, dtype={"Location": "category"}):
    for k, v in ch["Location"].value_counts().items():
        nrows[k] = nrows.get(k, 0) + int(v)
    ch = ch[ch["Location"].isin(["us-101", "i-80"]) & (ch["Lane_ID"] >= 5)]
    keep.append(ch)
df = pd.concat(keep, ignore_index=True)
print("rows per location (all lanes):", nrows)
print("kept rows lanes>=5:", len(df))
n0 = len(df); df = df.drop_duplicates(["Location", "Vehicle_ID", "Global_Time"]); print("duplicates dropped:", n0 - len(df))
df.to_pickle(sys.argv[1] + "/ng.pkl")
for loc, g in df.groupby("Location", observed=True):
    t = np.sort(g["Global_Time"].unique()); gaps = np.where(np.diff(t) > 60_000)[0]
    print(loc, "time span min:", (t[-1] - t[0]) / 60000, "breaks >1 min at (min from start):", [(round((t[i] - t[0]) / 60000, 1), round((t[i + 1] - t[0]) / 60000, 1)) for i in gaps], "lanes:", sorted(g["Lane_ID"].unique()))
    for ln, h in g.groupby("Lane_ID"):
        print("   lane", ln, "rows", len(h), "vehicles", h["Vehicle_ID"].nunique(), "Local_Y p1/p50/p99 (ft):", np.percentile(h["Local_Y"], [1, 50, 99]).round(0))
