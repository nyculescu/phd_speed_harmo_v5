# Field base rate of the plant's counted quantity at 1 Hz on main lanes; raw speeds and speeds from 1-s position differences.
import pandas as pd, numpy as np, json
FT=0.3048; out={}
for loc,mx in (('us-101',5),('i-80',6)):
    d=pd.read_pickle(f'{loc}.pkl')
    out[loc]={'lane_vmed_ms':{int(k):round(float(v)*FT,2) for k,v in d.groupby('Lane_ID')['v_Vel'].median().items()}}
    # speed from position: (y(t) - y(t-1 s)) per vehicle
    d=d.sort_values(['Vehicle_ID','Global_Time'])
    d['t1']=d['Global_Time']-1000
    prev=d[['Vehicle_ID','Global_Time','Local_Y']].rename(columns={'Global_Time':'t1','Local_Y':'y1'})
    d=d.merge(prev,on=['Vehicle_ID','t1'],how='left'); d['vp']=(d['Local_Y']-d['y1'])
    s=d[d['Global_Time']%1000==0]
    lead=s[['Vehicle_ID','Global_Time','v_Vel','vp','v_length','Lane_ID','Local_Y']].rename(columns={'Vehicle_ID':'Preceding','v_Vel':'lv','vp':'lvp','v_length':'ll','Lane_ID':'llane','Local_Y':'ly'})
    m=s.merge(lead,on=['Preceding','Global_Time'],how='left')
    m=m[m['Lane_ID'].between(1,mx)]
    ok=(m['Preceding']>0)&m['lv'].notna()&(m['llane']==m['Lane_ID'])
    gap=(m['Space_Headway']-m['ll'])*FT
    gap2=(m['ly']-m['ll']-m['Local_Y'])*FT     # from positions: leader front minus its length minus own front
    r={'samples':int(len(m)),'with_leader':round(float(ok.mean()),3),'gap_vs_pos_gap_median_diff_m':round(float((gap-gap2)[ok].median()),3)}
    for name,dv,sp in (('raw',(m['v_Vel']-m['lv'])*FT,m['v_Vel']*FT),('pos1s',(m['vp']-m['lvp'])*FT,m['vp']*FT)):
        hit=ok&(dv>0)&(gap/dv.where(dv>0)<3.0)&(gap>=0)
        hit_all=ok&(dv>0)&(gap/dv.where(dv>0)<3.0)
        band=np.where(sp<5,'lo',np.where(sp<10,'mid','hi'))
        r[name]={'rate':round(float(hit_all.mean()),4),'rate_gap_ge0':round(float(hit.mean()),4),**{b:round(float(hit_all[band==b].mean()),4) for b in ('lo','mid','hi')},
                 'share_samples':{b:round(float((band==b).mean()),3) for b in ('lo','mid','hi')}}
    out[loc].update(r)
print(json.dumps(out,indent=1)); json.dump(out,open('ng_rate.json','w'),indent=1)
