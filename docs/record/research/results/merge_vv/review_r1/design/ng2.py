import pandas as pd, numpy as np, sys
D = sys.argv[1]
df = pd.read_pickle(D + "/ng.pkl").sort_values(["Location", "Vehicle_ID", "Global_Time"]).reset_index(drop=True)
FT = 0.3048
# trajectory id: same location and vehicle id, consecutive frames (gap <= 1 s)
new = (df["Location"] != df["Location"].shift()) | (df["Vehicle_ID"] != df["Vehicle_ID"].shift()) | (df["Global_Time"].diff() > 1000) | (df["Global_Time"].diff() < 0)
df["traj"] = new.cumsum()
SITE = {"us-101": dict(frm=6, to=5, ramp=7, lane=(630.0, 1332.0)), "i-80": dict(frm=7, to=6, ramp=7, lane=(291.0, 662.0))}
out = []
for loc, g in df.groupby("Location", observed=True):
    s = SITE[loc]; t0 = g["Global_Time"].min()
    pos = g.set_index(["Vehicle_ID", "Global_Time"])[["Local_Y", "v_Vel", "Lane_ID"]]
    pos = pos[~pos.index.duplicated()]
    for tid, h in g.groupby("traj"):
        ln = h["Lane_ID"].to_numpy()
        if s["ramp"] not in ln:
            continue
        i = np.where((ln[:-1] == s["frm"]) & (ln[1:] == s["to"]))[0]
        if len(i) == 0:
            continue
        i = i[0] + 1
        r = h.iloc[i]; t = r["Global_Time"]
        pre = h.iloc[max(0, i - 100):i]
        fol = int(r["Following"]); lag_s = lag_t = np.nan
        if fol > 0 and (fol, t) in pos.index:
            f = pos.loc[(fol, t)]
            if f["Lane_ID"] == s["to"]:
                lag_s = (r["Local_Y"] - r["v_length"] - f["Local_Y"]) * FT
                lag_t = lag_s / max(f["v_Vel"] * FT, 0.1)
        m = (t - t0) / 60000.0
        per = (int(m // 15) if loc == "us-101" else (0 if m < 30 else 1 + int((m - 60.4) // 15.3)))
        out.append(dict(loc=loc, per=min(per, 2), y=r["Local_Y"], share=(r["Local_Y"] - s["lane"][0]) / (s["lane"][1] - s["lane"][0]), v=r["v_Vel"] * FT,
                        vmin10=pre["v_Vel"].min() * FT, npre=len(pre), lag_s=lag_s, lag_t=lag_t, cls=r["v_Class"]))
M = pd.DataFrame(out); M.to_pickle(D + "/ng_merges.pkl")
print("merges found:", len(M))
T = M.groupby(["loc", "per"], observed=True).agg(n=("y", "size"), pos_share_med=("share", "median"), v_merge_med=("v", "median"), stop_share=("vmin10", lambda x: float(np.mean(x < 1.0))),
                                    slow5_share=("vmin10", lambda x: float(np.mean(x < 5.0))), lag_t_med=("lag_t", "median"), lag_n=("lag_t", "count"), lag_s_med=("lag_s", "median")).round(3)
print(T.to_string())
q = {"merge position share": T["pos_share_med"], "stopped share (<1 m/s in 10 s before)": T["stop_share"], "lag time gap median": T["lag_t_med"], "merge speed median": T["v_merge_med"]}
print("\nleave-one-out: is each field period inside the range of the other five?")
tot = 0
for k, v in q.items():
    v = v.to_numpy(); inside = [(np.delete(v, i).min() <= v[i] <= np.delete(v, i).max()) for i in range(len(v))]
    tot += sum(inside)
    print(f"  {k:42s} values {np.round(v, 3)} range [{v.min():.3f}, {v.max():.3f}] inside (LOO): {sum(inside)}/6; within-site spread: us-101 {np.ptp(v[3:]):.3f}, i-80 {np.ptp(v[:3]):.3f}; between-site gap of means {abs(v[:3].mean() - v[3:].mean()):.3f}")
print("  all quantities:", tot, "of", 6 * len(q))
# sampling error of a period's value: bootstrap of merges within period
rng = np.random.default_rng(0)
for (loc, per), h in M.groupby(["loc", "per"], observed=True):
    b = [h.sample(len(h), replace=True, random_state=int(rng.integers(1 << 31))) for _ in range(300)]
    print(loc, per, "n", len(h), "bootstrap SE: pos share median %.3f, stop share %.3f, lag_t median %.3f" % (np.std([x["share"].median() for x in b]), np.std([np.mean(x["vmin10"] < 1.0) for x in b]), np.std([x["lag_t"].median() for x in b])))
