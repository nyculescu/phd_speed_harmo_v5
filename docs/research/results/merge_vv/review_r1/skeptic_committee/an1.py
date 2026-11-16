import pickle, collections, numpy as np, json
T=pickle.load(open('rows.pkl','rb'))
arms=sorted({a for a,_ in T}); seeds=sorted({s for _,s in T})
print(len(arms),'arms',len(seeds),'seeds',seeds[0],seeds[-1])
def col(a,k): return np.array([float(T[(a,s)].get(k,0) or 0) for s in seeds])
# C14: counters equal
eq=sum(T[k]['net']==T[k]['ttc3'] for k in T); eq2=sum(T[k]['net']==T[k]['mall'] for k in T)
print('ttc3==ttc_net',eq,'of',len(T),'; m_ttc3_all==ttc_net',eq2)
# plant_sweep road split vs measure road split
bad=sum(T[k]['c_r_4a']!=T[k].get('g_4a',0) for k in T); bad3=sum(T[k]['c_r_3']!=T[k].get('g_3',0) for k in T)
print('conflicts r_4a != m_road 4a in',bad,'rows; r_3 != g_3 in',bad3)
print('\nper arm medians: net, es1, es2, share lo/mid/hi, share 3a+4a, share lc')
L=['w0u250','w1u500','w2u250','w3u500','w4u500']
es1=[];sh=[];lo=[];mid=[]
for a in arms:
    net=col(a,'net'); e1=col(a,'es1'); e2=col(a,'es2')
    s34=(col(a,'g_3a').sum()+col(a,'g_4a').sum())/col(a,'mall').sum()
    slo=col(a,'lo').sum()/net.sum(); smid=col(a,'mid').sum()/net.sum()
    es1.append(np.median(e1)); sh.append(s34); lo.append(slo); mid.append(smid)
    print(f"{a:18s} net {np.median(net):7.1f} es1 {np.median(e1):6.1f} es2 {np.median(e2):6.1f} lo {slo:.3f} mid {smid:.3f} 3a+4a {s34:.3f} lc {col(a,'lc').sum()/col(a,'mall').sum():.3f} es1_zero_share {np.mean(e1==0):.2f}")
print('es1 median range',min(es1),max(es1),'3a+4a share range',round(min(sh),3),round(max(sh),3),'lo',round(min(lo),3),round(max(lo),3),'mid',round(min(mid),3),round(max(mid),3))
# paired decomposition v3w (mean of learners) vs opp, own rng, means and medians
rng=np.random.default_rng(777)
def v3(k): return np.mean([col(l,k) for l in L],axis=0)
def boot(d,f=np.median,B=4000):
    idx=rng.integers(0,len(d),(B,len(d))); b=f(d[idx],axis=1); return np.percentile(b,[2.5,97.5])
out={}
for opp in ('lr400_16_1','grid_lr400_13_1','nc','p333'):
    print('\n==',opp,'(opp - v3w; positive = v3w fewer)')
    other=lambda a: (col(a,'mall')-col(a,'g_3a')-col(a,'g_4a')) if isinstance(a,str) else None
    parts={'net':(col(opp,'net'),v3('net')),'g4a':(col(opp,'g_4a'),v3('g_4a')),'g3a':(col(opp,'g_3a'),v3('g_3a')),
           'other':(col(opp,'mall')-col(opp,'g_3a')-col(opp,'g_4a'), v3('mall')-v3('g_3a')-v3('g_4a')),
           'lc':(col(opp,'lc'),v3('lc')),'nlc':(col(opp,'mall')-col(opp,'lc'),v3('mall')-v3('lc')),
           'lo':(col(opp,'lo'),v3('lo')),'mid':(col(opp,'mid'),v3('mid')),'hi':(col(opp,'hi'),v3('hi')),
           'es1':(col(opp,'es1'),v3('es1')),'es2':(col(opp,'es2'),v3('es2')),
           'ramp2':(col(opp,'g_ramp2'),v3('g_ramp2')),'g3':(col(opp,'g_3'),v3('g_3')),'g4':(col(opp,'g_4'),v3('g_4')),'g2':(col(opp,'g_2'),v3('g_2')),'g1':(col(opp,'g_1'),v3('g_1')),'junc':(col(opp,'g_junction'),v3('g_junction'))}
    for k,(a,b) in parts.items():
        d=a-b; ci=boot(d); cim=boot(d,np.mean)
        print(f"{k:6s} med_opp {np.median(a):7.1f} med_v3w {np.median(b):7.1f} med_diff {np.median(d):7.1f} [{ci[0]:.1f},{ci[1]:.1f}] rel {100*np.median(d)/max(np.median(a),1e-9):5.1f}% | mean_diff {d.mean():7.1f} [{cim[0]:.1f},{cim[1]:.1f}] mean_rel {100*d.mean()/a.mean():5.1f}%")
