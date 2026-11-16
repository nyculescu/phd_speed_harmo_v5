# I-80: where lane 7 is last seen (its coded extent) and how many 7->6 moves sit at that end; US-101: origin lane of 6->5 movers.
import pandas as pd, numpy as np, json
FT = 0.3048
out = {}
d = pd.read_pickle('i-80.pkl').sort_values(['Vehicle_ID', 'Global_Time'])
d['traj'] = (d.groupby('Vehicle_ID')['Global_Time'].diff().fillna(1e9) > 1000).cumsum()
y7 = d.loc[d['Lane_ID'] == 7, 'Local_Y'] * FT
out['i80_lane7_y_m'] = [round(float(y7.min()), 1), round(float(y7.quantile(0.99)), 1), round(float(y7.max()), 1)]
prev = d.groupby('traj')['Lane_ID'].shift()
mv = d[(prev == 7) & (d['Lane_ID'] == 6)].groupby('traj').head(1)
y = mv['Local_Y'] * FT
out['i80_7to6_share_within_5m_of_lane7_p99'] = float((y > out['i80_lane7_y_m'][1] - 5).mean())
d = pd.read_pickle('us-101.pkl').sort_values(['Vehicle_ID', 'Global_Time'])
d['traj'] = (d.groupby('Vehicle_ID')['Global_Time'].diff().fillna(1e9) > 1000).cumsum()
first_lane = d.groupby('traj')['Lane_ID'].first()
last_lane = d.groupby('traj')['Lane_ID'].last()
prev = d.groupby('traj')['Lane_ID'].shift()
mv = d[(prev == 6) & (d['Lane_ID'] == 5)].groupby('traj').head(1)
fl = first_lane.loc[mv['traj']].value_counts().to_dict()
out['us101_6to5_by_first_lane'] = {int(k): int(v) for k, v in fl.items()}
out['us101_lane6_entrants_ending_lane8'] = int(((first_lane <= 5) & (last_lane == 8)).sum())
out['us101_lane7_entrants'] = int((first_lane == 7).sum())
y6 = d.loc[d['Lane_ID'] == 6, 'Local_Y'] * FT
out['us101_lane6_y_m'] = [round(float(y6.quantile(0.01)), 1), round(float(y6.quantile(0.99)), 1)]
print(json.dumps(out, indent=1)); json.dump(out, open('ng4.json', 'w'), indent=1)
