# Own chunked load of NGSIM (us-101, i-80) with lateral position; writes one parquet-free pickle per site.
import pandas as pd, numpy as np, json
P='/home/catalin/work/phd/v5b1_data/ngsim/ngsim_8ect-6jqj.csv'
cols=['Vehicle_ID','Frame_ID','Total_Frames','Global_Time','Local_X','Local_Y','v_length','v_Vel','Lane_ID','Preceding','Space_Headway','Location']
parts={'us-101':[],'i-80':[]}
n=0
for ch in pd.read_csv(P,usecols=cols,chunksize=1_500_000):
    n+=len(ch)
    ch=ch[ch['Location'].isin(list(parts))]
    for loc,g in ch.groupby('Location'):
        parts[loc].append(g.drop(columns='Location'))
out={'rows_total':n}
for loc,ps in parts.items():
    d=pd.concat(ps,ignore_index=True)
    r={'rows':len(d)}
    r['dup_all12']=int(d.duplicated().sum())
    d=d.drop_duplicates()
    r['rows_dedup']=len(d)
    r['dup_id_frame']=int(d.duplicated(['Vehicle_ID','Frame_ID']).sum())
    r['dup_id_time']=int(d.duplicated(['Vehicle_ID','Global_Time']).sum())
    r['dup_id_tf_time']=int(d.duplicated(['Vehicle_ID','Total_Frames','Global_Time']).sum())
    ut=np.sort(d['Global_Time'].unique()); cuts=np.where(np.diff(ut)>60_000)[0]
    st=[ut[0]]+[ut[i+1] for i in cuts]; en=[ut[i] for i in cuts]+[ut[-1]]
    r['blocks_utc']=[(str(pd.to_datetime(s,unit='ms')),round((e-s)/60000,1)) for s,e in zip(st,en)]
    r['lane_rows']=d['Lane_ID'].value_counts().sort_index().to_dict()
    d.to_pickle(f'{loc}.pkl')
    out[loc]=r
print(json.dumps(out,indent=1,default=str)); json.dump(out,open('ng_load.json','w'),indent=1,default=str)
