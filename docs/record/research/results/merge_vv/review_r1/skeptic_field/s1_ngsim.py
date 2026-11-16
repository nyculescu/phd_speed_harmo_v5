import sys, numpy as np, pandas as pd
f = "/home/catalin/work/phd/v5b1_data/ngsim/ngsim_8ect-6jqj.csv"
cols = ["Vehicle_ID", "Global_Time", "Local_X", "Local_Y", "Lane_ID", "v_Class", "v_Vel", "Location"]
us, i80 = [], []
for ch in pd.read_csv(f, usecols=cols, chunksize=2_000_000, dtype={"Location": "category"}):
    us.append(ch[ch.Location == "us-101"].drop(columns="Location"))
    i80.append(ch[ch.Location == "i-80"].drop(columns="Location"))
us = pd.concat(us); i80 = pd.concat(i80)
print("us rows", len(us), "dup full(loaded cols)", us.duplicated().sum(), "dup (veh,time)", us.duplicated(["Vehicle_ID", "Global_Time"]).sum())
print("i80 rows", len(i80), "dup full", i80.duplicated().sum(), "dup (veh,time)", i80.duplicated(["Vehicle_ID", "Global_Time"]).sum())
us = us.drop_duplicates()
for name, d in (("us-101", us), ("i-80", i80)):
    d = d.sort_values(["Vehicle_ID", "Global_Time"]).reset_index(drop=True)
    newtrk = (d.Vehicle_ID.diff() != 0) | (d.Global_Time.diff() != 100)
    d["trk"] = newtrk.cumsum()
    print(name, "distinct Vehicle_ID", d.Vehicle_ID.nunique(), "tracks", d.trk.nunique())
    for ln in sorted(d.Lane_ID.unique()):
        s = d[d.Lane_ID == ln]
        print(f"  lane {ln}: Local_Y min {s.Local_Y.min():.0f} max {s.Local_Y.max():.0f} Local_X p50 {s.Local_X.median():.1f}")
    same = d.trk.values[1:] == d.trk.values[:-1]
    a, b = d.Lane_ID.values[:-1], d.Lane_ID.values[1:]
    m76 = same & (a == 7) & (b == 6)
    y = d.Local_Y.values[1:][m76]; x = d.Local_X.values[1:][m76]
    print(f"  7->6 label changes n={m76.sum()} Local_Y q05/50/95 {np.percentile(y,[5,50,95]).round(0)} share>=660 {np.mean(y>=660):.3f} Local_X q25/50/75 {np.percentile(x,[25,50,75]).round(1)}")
    if name == "i-80":
        # lateral crossing: first frame after which Local_X < 72.5 for 10 frames, on tracks first seen in lane 7
        first = d.groupby("trk").head(1); ramp = set(first.trk[first.Lane_ID == 7])
        r = d[d.trk.isin(ramp)]
        out = []
        for t, g in r.groupby("trk"):
            xs = g.Local_X.values; ys = g.Local_Y.values; ts = g.Global_Time.values; ls = g.Lane_ID.values
            ok = xs < 72.5
            run = np.convolve(ok.astype(int), np.ones(10, int), "valid") == 10
            iL = np.argmax(run) if run.any() else -1
            ch = np.where((ls[:-1] == 7) & (ls[1:] == 6))[0]
            iC = ch[0] + 1 if len(ch) else -1
            if iL >= 0 and iC >= 0:
                out.append((ys[iL], ys[iC], (ts[iL] - ts[iC]) / 1000))
        o = np.array(out)
        print(f"  ramp tracks {len(ramp)} with both {len(o)}: lateral Local_Y p50 {np.median(o[:,0]):.0f}; label Local_Y p50 {np.median(o[:,1]):.0f}; lateral minus label s q10/50/90 {np.percentile(o[:,2],[10,50,90]).round(1)}")
