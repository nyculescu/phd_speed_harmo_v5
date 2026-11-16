# Independent re-derivation from stored E30 rows; writes a compact per-(arm, seed) table for later use.
import json, collections, pickle
import numpy as np
P='/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
T={}
n=0
for line in open(P):
    r=json.loads(line); n+=1
    arm=r['name'].split('|',1)[1]
    mr=r.get('m_road_ttc3') or {}; mv=r.get('m_road_vs') or {}
    d={'net':r['ttc_net'],'ttc3':r['ttc3'],'mall':r['m_ttc3_all'],'lc':r['m_ttc3_lc'],
       'lo':r.get('ttc3_s_lo',0),'mid':r.get('ttc3_s_mid',0),'hi':r.get('ttc3_s_hi',0),
       'es1':r['end_stop'],'es2':r['end_stop2'],'halt3a0':r.get('halt_3a_0',0),'vs':r['vs'],'passed':r['passed'],
       'c_r_4a':r.get('ttc3_r_4a',0),'c_r_3':r.get('ttc3_r_3',0),'c_r_ramp2':r.get('ttc3_r_ramp2',0),'c_r_rest':r.get('ttc3_r_rest',0)}
    for g,per in mr.items():
        d['g_'+g]=sum(per.values())
        for p,x in per.items(): d[f'gp_{g}_{p}']=x
    for g,per in mv.items():
        d['vs_'+g]=sum(per.values())
    for x in ('3a_1','3_0','4a_1'):
        d['n_'+x]=r.get('n_'+x,0); d['nv_'+x]=r.get('nv_'+x,0)
    d['mp1']=r.get('m_mergepos_m1'); d['mp2']=r.get('m_mergepos_m2')
    T[(arm,r['seed'])]=d
print('rows',n,'keys',len(T))
pickle.dump(T,open('rows.pkl','wb'))
