# Light pass: rows, duplicate rows, lanes, time span and vehicle-id reuse per location (us-101, i-80).
import pandas as pd, numpy as np, collections, json
P = '/home/catalin/work/phd/v5b1_data/ngsim/ngsim_8ect-6jqj.csv'
cols = ['Vehicle_ID','Frame_ID','Global_Time','Local_Y','v_Vel','Lane_ID','v_Class','Location']
parts = collections.defaultdict(list)
n_all = collections.Counter()
for ch in pd.read_csv(P, usecols=cols, chunksize=2_000_000, dtype={'Location': 'category'}):
    n_all.update(ch['Location'].astype(str).value_counts().to_dict())
    ch = ch[ch['Location'].isin(['us-101', 'i-80'])]
    for loc, g in ch.groupby('Location', observed=True):
        parts[str(loc)].append(g.drop(columns='Location'))
print('rows per location', dict(n_all))
out = {}
for loc, ps in parts.items():
    d = pd.concat(ps, ignore_index=True)
    dup = int(d.duplicated().sum())
    d = d.drop_duplicates()
    kdup = int(d.duplicated(['Vehicle_ID', 'Frame_ID']).sum())
    t = d['Global_Time']
    # periods: split where the sorted unique time jumps by more than 10 minutes
    ut = np.sort(t.unique()); cuts = np.where(np.diff(ut) > 600_000)[0]
    starts = [ut[0]] + [ut[i + 1] for i in cuts]; ends = [ut[i] for i in cuts] + [ut[-1]]
    per = [(pd.to_datetime(s, unit='ms').strftime('%Y-%m-%d %H:%M'), round((e - s) / 60000, 1)) for s, e in zip(starts, ends)]
    out[loc] = dict(rows=len(d), dup_rows=dup, same_id_frame_dup=kdup, lanes=d['Lane_ID'].value_counts().sort_index().to_dict(),
                    periods_utc=per, vel_med_fts=float(d['v_Vel'].median()), local_y_max_ft=float(d['Local_Y'].max()))
    by_lane = d.groupby('Lane_ID')['v_Vel'].median().round(1).to_dict()
    out[loc]['vel_med_by_lane_fts'] = by_lane
    d.to_parquet(f'{loc}.parquet') if False else d.to_pickle(f'{loc}.pkl')
print(json.dumps(out, indent=1, default=str))
json.dump(out, open('ng1.json', 'w'), indent=1, default=str)
