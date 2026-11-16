import json, sys, numpy as np
sc=json.load(open('/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json'))
mine=json.load(open(sys.argv[1]))
mk={frozenset((c['q'],c['r'])):c for c in mine}; sk={frozenset((c['q'],c['r'])):c for c in sc['chords']}
print('mine',len(mk),'screen',len(sk),'same pair set',set(mk)==set(sk))
print('screen chord keys',list(sc['chords'][0].keys()))
mx={k:0 for k in ['pt','lo','hi','se','w']}; wci=0; flipped=0
for k,c in sk.items():
    m=mk[k]
    same=(m['q']==c['q'])
    if not same: flipped+=1
    for kk in ['pt','lo','hi','se']: mx[kk]=max(mx[kk],abs(m[kk]-c[kk]))
    w=m['w'] if same else 1-m['w']; mx['w']=max(mx['w'],abs(w-c['w']))
    wc=m['w_ci'] if same else [1-m['w_ci'][1],1-m['w_ci'][0]]
    wci=max(wci,abs(wc[0]-c['w_ci'][0]),abs(wc[1]-c['w_ci'][1]))
print('max abs diff',mx,'w_ci',wci,'orientation flipped',flipped)
srt=sorted(sc['chords'],key=lambda c:c['lo'])
print('\n20 smallest lower-bound chords (screen | mine)')
for c in srt[:20]:
    m=mk[frozenset((c['q'],c['r']))]
    print(f"{c['q']:>14s}~{c['r']:<18s} sc {c['pt']:+6.2f} [{c['lo']:+6.2f},{c['hi']:+6.2f}] w {c['w']:.3f} [{c['w_ci'][0]:.2f},{c['w_ci'][1]:.2f}] null {c['null']['rate']:.4f} | mine {m['pt']:+6.2f} [{m['lo']:+6.2f},{m['hi']:+6.2f}] w({m['q']}->{m['r']}) {m['w']:.3f} share w=0 {m['share_w0']:.2f} w=1 {m['share_w1']:.2f}")
print('min lo mine',min((c['lo'],c['q'],c['r']) for c in mine)); print('min lo screen',srt[0]['lo'], 'smallest_lower_bound',sc['smallest_lower_bound'])
print('all mine lo>0',all(c['lo']>0 for c in mine),'any hi<5',[ (c['q'],c['r'],c['hi']) for c in mine if c['hi']<5])
print('min hi mine',min(c['hi'] for c in mine))
comp=set(sc['competitors']); tp=set(sc['trade_points'])
# trade-point end: full-sample w clamped to an end that is a trade point
te=[(c['q'],c['r'],c['w']) for c in mine if (c['w']==0 and c['q'] in tp) or (c['w']==1 and c['r'] in tp)]
print('chords whose full-sample w sits at a trade-point end:',te)
ce=[(c['q'],c['r'],c['w']) for c in mine if c['w'] in (0,1)]
print('chords with full-sample w at any end:',len(ce))
print('chord nulls: n',len(sc['chords']),'max rate',max(c['null']['rate'] for c in sc['chords']),'min',min(c['null']['rate'] for c in sc['chords']), 'swaps set',set(c['null'].get('swaps') for c in sc['chords']), 'all ok',all(c['null']['ok'] for c in sc['chords']))
allr=[v['rate'] for v in sc['nulls'].values()]+[c['null']['rate'] for c in sc['chords']]
print('all nulls count',len(allr),'range',min(allr),max(allr),'mean',np.mean(allr))
print('E nulls range',min(v['rate'] for k,v in sc['nulls'].items() if k.startswith('E ')),max(v['rate'] for k,v in sc['nulls'].items() if k.startswith('E ')))
print('reads counter',{v:list(sc['decision']['reads'].values()).count(v) for v in set(sc['decision']['reads'].values())}, len(sc['decision']['reads']))
