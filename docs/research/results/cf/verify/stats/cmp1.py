import json, sys, numpy as np
sc=json.load(open('/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json'))
print('level',sc['level'])
def load(f):
    z=np.load(f); return {k:z[k] for k in z.files}
A=load(sys.argv[1]); Bz=load(sys.argv[2])
R=list(A['R']); M=list(A['M']); n=480
def eff(z,variant):
    # point and resamples, percent
    X=z['Q'][:,:,None,:]-z['P'][:,None,:,:]
    pt_raw=np.median(X,axis=-1).mean(-1)          # (3,26)
    den=np.median(z['Q'],axis=-1)                 # full-sample median(R)
    pt=pt_raw/den*100
    rs=z['raw'].mean(2)                           # (3,26,B)
    if variant=='full': bs=rs/den[:,:,None]*100
    else: bs=rs/z['medR']*100
    return pt,bs
key={'all_delay':'D','ttc_net':'E','b45_step':'brake'}
res={}
for variant in ['full','resample']:
    for nm,z in [('A',A),('B',Bz)]:
        pt,bs=eff(z,variant)
        lo,hi=np.percentile(bs,[1.25,98.75],axis=-1); lo95,hi95=np.percentile(bs,[2.5,97.5],axis=-1); se=bs.std(-1,ddof=1)
        res[(variant,nm)]=(pt,lo,hi,lo95,hi95,se)
# compare with screen.json
for variant in ['full','resample']:
    for nm in 'AB':
        pt,lo,hi,lo95,hi95,se=res[(variant,nm)]
        mx={k:0 for k in ['pt','lo','hi','lo95','hi95','se']}
        for mi,m in enumerate(M):
            for ri,r in enumerate(R):
                s=sc['readings'][r][key[m]]
                for k,v in zip(['pt','lo','hi','lo95','hi95','se'],[pt,lo,hi,lo95,hi95,se]):
                    mx[k]=max(mx[k],abs(v[mi,ri]-s[k]))
        print(variant,nm,'max abs diff vs screen.json',{k:round(v,4) for k,v in mx.items()})
pt,lo,hi,lo95,hi95,se=res[('full','A')]; ptB,loB,hiB,_,_,seB=res[('full','B')]
print('\nD table (mine A full | mine B | screen)')
comp=[];trade=[]
for ri,r in enumerate(R):
    s=sc['readings'][r]['D']
    cls='competitor' if (lo[0,ri]<=1 or r=='p333') else 'trade'
    clsB='competitor' if (loB[0,ri]<=1 or r=='p333') else 'trade'
    (comp if cls=='competitor' else trade).append(r)
    sc_cls='competitor' if r in sc['competitors'] else ('trade' if r in sc['trade_points'] else 'none')
    print(f"{r:18s} D {pt[0,ri]:+7.2f} [{lo[0,ri]:+7.2f},{hi[0,ri]:+7.2f}] | B [{loB[0,ri]:+7.2f},{hiB[0,ri]:+7.2f}] | sc {s['pt']:+7.2f} [{s['lo']:+7.2f},{s['hi']:+7.2f}] {cls:10s} {clsB:10s} sc:{sc_cls}{'  <<< MISMATCH' if cls!=sc_cls or clsB!=sc_cls else ''}")
print('competitors',len(comp),'trade',len(trade), 'nc in which?', 'nc' in comp, 'nc' in trade, 'nc in sc comp/trade', 'nc' in sc['competitors'], 'nc' in sc['trade_points'])
print('\nE table for all rules')
for ri,r in enumerate(R):
    s=sc['readings'][r]['E']; b=sc['readings'][r]['brake']
    print(f"{r:18s} {'C' if r in comp else 't'} E {pt[1,ri]:+7.2f} [{lo[1,ri]:+7.2f},{hi[1,ri]:+7.2f}] se {se[1,ri]:.2f} | B [{loB[1,ri]:+7.2f},{hiB[1,ri]:+7.2f}] | sc {s['pt']:+7.2f} [{s['lo']:+7.2f},{s['hi']:+7.2f}] || brake {pt[2,ri]:+6.2f} [{lo[2,ri]:+6.2f},{hi[2,ri]:+6.2f}] B[{loB[2,ri]:+6.2f},{hiB[2,ri]:+6.2f}] sc {b['pt']:+6.2f} [{b['lo']:+6.2f},{b['hi']:+6.2f}]")
ri=R.index('p333'); print('\ndelay vs p333 mine',pt[0,ri],lo[0,ri],hi[0,ri],lo95[0,ri],hi95[0,ri],se[0,ri]); print('screen',sc['delay_vs_p333'])
ri=R.index('3E-C_TRUCK'); print('brake vs 3E-C_TRUCK mine',pt[2,ri],lo[2,ri],hi[2,ri],lo95[2,ri],hi95[2,ri],se[2,ri]); print('screen',sc['braking_vs_3E-C_TRUCK'])
# resample-denominator variant for the closest
pt2,lo2,hi2,_,_,se2=res[('resample','A')]
for r in ['lr400_16_1','p333','3ex2','os1_15_10']:
    ri=R.index(r); print(r,'E resample-denominator variant',round(pt2[1,ri],2),round(lo2[1,ri],2),round(hi2[1,ri],2))
print('min E lower bound among competitors (A,full):',min((lo[1,R.index(r)],r) for r in comp), ' B:',min((loB[1,R.index(r)],r) for r in comp))
print('min E lower bound among competitors (resample denominators):',min((lo2[1,R.index(r)],r) for r in comp))
