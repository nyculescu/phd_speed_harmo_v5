# Field base rate of the plant's counted quantity: share of 1-Hz vehicle samples with a closing same-lane leader and TTC < 3 s,
# by follower speed band. Bumper gap = Space_Headway (front to front, VERIFY) - leader length. Descriptive feasibility check only.
import pandas as pd, numpy as np, json
P = '/home/catalin/work/phd/v5b1_data/ngsim/ngsim_8ect-6jqj.csv'
FT = 0.3048
cols = ['Vehicle_ID', 'Frame_ID', 'Global_Time', 'v_length', 'v_Vel', 'Lane_ID', 'Preceding', 'Space_Headway', 'Location']
parts = {'us-101': [], 'i-80': []}
for ch in pd.read_csv(P, usecols=cols, chunksize=2_000_000):
    ch = ch[ch['Location'].isin(parts) & (ch['Global_Time'] % 1000 == 0)].drop_duplicates()
    for loc, g in ch.groupby('Location'):
        parts[loc].append(g.drop(columns='Location'))
out = {}
for loc, ps in parts.items():
    d = pd.concat(ps, ignore_index=True).drop_duplicates(['Vehicle_ID', 'Global_Time'])
    lead = d[['Vehicle_ID', 'Global_Time', 'v_Vel', 'v_length', 'Lane_ID']].rename(columns={'Vehicle_ID': 'Preceding', 'v_Vel': 'lv', 'v_length': 'll', 'Lane_ID': 'llane'})
    m = d.merge(lead, on=['Preceding', 'Global_Time'], how='left')
    main = m[m['Lane_ID'].between(1, 5 if loc == 'us-101' else 6)]
    s = main['v_Vel'] * FT
    ok = (main['Preceding'] > 0) & main['lv'].notna() & (main['llane'] == main['Lane_ID'])
    dv = (main['v_Vel'] - main['lv']) * FT
    gap = (main['Space_Headway'] - main['ll']) * FT
    hit = ok & (dv > 0) & (gap / dv.where(dv > 0) < 3.0)
    band = np.where(s < 5, 'lo', np.where(s < 10, 'mid', 'hi'))
    r = {'samples': int(len(main)), 'with_leader': float(ok.mean()), 'rate_all': float(hit.mean()), 'neg_gap_share': float((ok & (gap < 0)).mean())}
    for b in ('lo', 'mid', 'hi'):
        k = band == b
        r[b] = dict(share_of_samples=float(k.mean()), rate=float(hit[k].mean()), share_of_hits=float(hit[k].sum() / max(hit.sum(), 1)))
    out[loc] = r
print(json.dumps(out, indent=1))
json.dump(out, open('ng3.json', 'w'), indent=1)
