# Merges from the ramp or auxiliary lane into the adjacent lane: count, position, speed at merge, share that crawled (< 1 m/s) in the 10 s before.
# Lane codes assumed (VERIFY in the NGSIM documentation): us-101 7 on-ramp, 6 auxiliary, 5 rightmost main; i-80 7 on-ramp, 6 rightmost main.
import pandas as pd, numpy as np, json
FT = 0.3048
res = {}
for loc, moves in (('us-101', [(7, 6), (6, 5)]), ('i-80', [(7, 6)])):
    d = pd.read_pickle(f'{loc}.pkl').sort_values(['Vehicle_ID', 'Global_Time'])
    # a trajectory = one vehicle id with no time gap above 1 s (ids are reused across periods)
    gap = d.groupby('Vehicle_ID')['Global_Time'].diff().fillna(1e9)
    d['traj'] = (gap > 1000).cumsum()
    d['hour'] = pd.to_datetime(d['Global_Time'], unit='ms').dt.strftime('%H:%M')
    lane_prev = d.groupby('traj')['Lane_ID'].shift()
    r = {'trajectories': int(d['traj'].nunique())}
    for a, b in moves:
        idx = np.where((lane_prev.values == a) & (d['Lane_ID'].values == b))[0]
        rows = d.iloc[idx]
        first = rows.groupby('traj').head(1)
        mins = []
        for _, x in first.iterrows():
            g = d[(d['traj'] == x['traj']) & (d['Global_Time'] >= x['Global_Time'] - 10000) & (d['Global_Time'] <= x['Global_Time'])]
            mins.append(g['v_Vel'].min() * FT)
        mins = np.array(mins)
        v = first['v_Vel'].values * FT
        r[f'{a}->{b}'] = dict(n=int(len(first)), y_med_m=float(np.median(first['Local_Y']) * FT), y_p10_p90_m=[float(np.percentile(first['Local_Y'], q) * FT) for q in (10, 90)],
                              v_merge_med_ms=float(np.median(v)), crawl_share=float(np.mean(mins < 1.0)),
                              by_15min={h: int(c) for h, c in first['hour'].str[:4].value_counts().sort_index().items()})
    res[loc] = r
print(json.dumps(res, indent=1))
json.dump(res, open('ng2.json', 'w'), indent=1)
