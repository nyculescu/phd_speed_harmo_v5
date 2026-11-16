# Own merge extraction with lateral position, per 15-min period. Lane codes are an assumption [VERIFY in NGSIM docs].
import pandas as pd, numpy as np, json
FT=0.3048
out={}
def prep(loc):
    d=pd.read_pickle(f'{loc}.pkl').sort_values(['Vehicle_ID','Global_Time']).reset_index(drop=True)
    gap=d.groupby('Vehicle_ID')['Global_Time'].diff()
    d['traj']=((gap.isna())|(gap>1000)).cumsum()
    d['y']=d['Local_Y']*FT; d['x']=d['Local_X']*FT; d['v']=d['v_Vel']*FT
    return d
def period(loc,t):
    # 15-min periods by local clock start (us-101 07:50, 08:05, 08:20; i-80 16:00, 17:00, 17:15), read from the time blocks
    return t
for loc,moves in (('us-101',[(7,6),(6,5)]),('i-80',[(7,6)])):
    d=prep(loc)
    t0=d['Global_Time'].min()
    if loc=='us-101':
        d['per']=np.minimum(((d['Global_Time']-t0)//(15.4*60000)).astype(int),2)
    else:
        blk2=d['Global_Time']>t0+40*60000
        t1=d.loc[blk2,'Global_Time'].min()
        d['per']=np.where(~blk2,0,1+np.minimum(((d['Global_Time']-t1)//(16.4*60000)).astype(int),1))
    r={'trajs':int(d['traj'].nunique()),'per_rows':d['per'].value_counts().sort_index().to_dict()}
    first_lane=d.groupby('traj')['Lane_ID'].first(); last_lane=d.groupby('traj')['Lane_ID'].last()
    prev=d.groupby('traj')['Lane_ID'].shift()
    # lane extents (1st-99th pct of y) and lateral centre by lane
    ext={}
    for ln in sorted(d['Lane_ID'].unique()):
        s=d.loc[d['Lane_ID']==ln]
        ext[int(ln)]=[round(float(s['y'].quantile(q)),1) for q in (0.01,0.5,0.99)]+[round(float(s['x'].median()),2)]
    r['lane_y_p1_p50_p99_xmed']=ext
    g=d.groupby('traj')
    for a,b in moves:
        idx=np.where((prev.values==a)&(d['Lane_ID'].values==b))[0]
        mv=d.iloc[idx].groupby('traj').head(1)
        if (a,b)==(6,5) and loc=='us-101':
            keep=first_lane.loc[mv['traj']].values==7
            r['6->5 n_all']=int(len(mv)); mv=mv[keep]
        # lateral position at transition, 2 s before and 2 s after
        key=d.set_index(['traj','Global_Time'])['x']
        xb=key.reindex(list(zip(mv['traj'],mv['Global_Time']-2000))).values
        xa=key.reindex(list(zip(mv['traj'],mv['Global_Time']+2000))).values
        # min speed in the 10 s before
        mins=[]
        for tr,t in zip(mv['traj'],mv['Global_Time']):
            s=g.get_group(tr); s=s[(s['Global_Time']>=t-10000)&(s['Global_Time']<=t)]
            mins.append(s['v'].min())
        mins=np.array(mins)
        q=lambda s,qs=(10,50,90):[round(float(np.nanpercentile(s,k)),2) for k in qs]
        rr={'n':int(len(mv)),'y_p10_50_90':q(mv['y']),'x_at':q(mv['x']),'x_2s_before':q(xb),'x_2s_after':q(xa),
            'v_merge_p10_50_90':q(mv['v']),'crawl_share':round(float(np.mean(mins<1.0)),4)}
        byp={}
        for p,s in mv.groupby('per'):
            m=mins[(mv['per']==p).values]
            byp[int(p)]={'n':int(len(s)),'y_med':round(float(s['y'].median()),1),'v_med':round(float(s['v'].median()),2),'crawl':round(float(np.mean(m<1.0)),4)}
        rr['by_period']=byp
        r[f'{a}->{b}']=rr
    if loc=='i-80':
        y7=d.loc[d['Lane_ID']==7,'y']; e=float(y7.quantile(0.99))
        mv=d.iloc[np.where((prev.values==7)&(d['Lane_ID'].values==6))[0]].groupby('traj').head(1)
        r['lane7_y_min_p99_max']=[round(float(y7.min()),1),round(e,1),round(float(y7.max()),1)]
        r['7->6 share_within_5m_of_p99']=round(float((mv['y']>e-5).mean()),3)
        r['7->6 y hist 10m']=np.histogram(mv['y'],bins=np.arange(30,231,10))[0].tolist()
        # of lane-7 starters: how many reach lane 6
        st7=first_lane[first_lane==7].index
        r['lane7_starters']=int(len(st7)); r['lane7_starters_ever_lane6']=int(d[d['traj'].isin(st7)&(d['Lane_ID']==6)]['traj'].nunique())
        # lateral profile of lane 7 and 6 near the end: median x by 10-m y bin
        for ln in (6,7):
            s=d[(d['Lane_ID']==ln)&(d['y']>120)&(d['y']<260)]
            r[f'lane{ln}_xmed_by_y10']={int(k):round(float(v),2) for k,v in s.groupby((s['y']//10*10).astype(int))['x'].median().items()}
    if loc=='us-101':
        r['first7']=int((first_lane==7).sum()); r['main_to_8']=int(((first_lane<=5)&(last_lane==8)).sum())
        mv=d.iloc[np.where((prev.values==6)&(d['Lane_ID'].values==5))[0]].groupby('traj').head(1)
        r['6->5 by first lane']={int(k):int(v) for k,v in first_lane.loc[mv['traj']].value_counts().items()}
        r['6->5 y hist 20m']=np.histogram(mv['y'],bins=np.arange(180,441,20))[0].tolist()
    out[loc]=r
print(json.dumps(out,indent=1)); json.dump(out,open('ng_merge.json','w'),indent=1)
