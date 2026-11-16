# Pass 2: lanes, positions, periods per site. Exploratory, before protocol approval.
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
S = sys.argv[1]
for loc in ("us-101", "i-80"):
    d = pd.read_pickle(f"{S}/{loc}.pkl")
    print("=====", loc, "rows", len(d))
    t = np.sort(d["Global_Time"].unique())
    gaps = np.where(np.diff(t) > 100)[0]
    print("distinct times", len(t), "step ms mode", pd.Series(np.diff(t)).mode().tolist(), "gaps >100 ms:", [(int(t[i]), int(t[i + 1]), (t[i + 1] - t[i]) / 60000.0) for i in gaps])
    print("time range", t[0], t[-1], pd.to_datetime([t[0], t[-1]], unit="ms", utc=True).tz_convert("America/Los_Angeles").strftime("%Y-%m-%d %H:%M:%S").tolist(), "span min", (t[-1] - t[0]) / 60000.0)
    # 15-min periods by clock
    d["per"] = pd.to_datetime(d["Global_Time"], unit="ms", utc=True).dt.tz_convert("America/Los_Angeles").dt.floor("15min").dt.strftime("%H:%M")
    print(d.groupby("per").agg(rows=("Vehicle_ID", "size"), veh=("Vehicle_ID", "nunique"), t0=("Global_Time", "min"), t1=("Global_Time", "max")))
    # vehicle identity: (Vehicle_ID, Total_Frames)
    g = d.groupby(["Vehicle_ID", "Total_Frames"])
    print("distinct Vehicle_ID", d["Vehicle_ID"].nunique(), "distinct (Vehicle_ID, Total_Frames)", g.ngroups)
    sz = g.size().reset_index(name="n")
    print("tracks whose row count != Total_Frames:", int((sz["n"] != sz["Total_Frames"]).sum()), "of", len(sz))
    span = g["Global_Time"].agg(["min", "max"])
    print("tracks with time span/100+1 != rows:", int((((span["max"] - span["min"]) // 100 + 1).values != sz["n"].values).sum()))
    print(d.groupby("Lane_ID").agg(rows=("Vehicle_ID", "size"), veh=("Vehicle_ID", "nunique"), y_min=("Local_Y", "min"), y01=("Local_Y", lambda s: s.quantile(0.01)), y50=("Local_Y", "median"), y99=("Local_Y", lambda s: s.quantile(0.99)), y_max=("Local_Y", "max"),
                                     x01=("Local_X", lambda s: s.quantile(0.01)), x50=("Local_X", "median"), x99=("Local_X", lambda s: s.quantile(0.99)), v50=("v_Vel", "median")).round(1))
    print("v_Class counts (rows):", d["v_Class"].value_counts().to_dict())
    print("units check: v_Vel quantiles", d["v_Vel"].quantile([0.01, 0.5, 0.99]).round(2).tolist(), "v_Acc quantiles", d["v_Acc"].quantile([0.001, 0.01, 0.5, 0.99, 0.999]).round(2).tolist(), "share |v_Acc|>=11.2:", round(float((d["v_Acc"].abs() >= 11.19).mean()), 4))
    print("v_length quantiles", d["v_length"].quantile([0.01, 0.5, 0.99]).tolist())
