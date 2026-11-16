import pickle, sys, collections, json, numpy as np
d=pickle.load(open(sys.argv[1],'rb')); rows=d['rows']
arms=collections.Counter(r['arm'] for r in rows)
print('n arms',len(arms), 'counts set', set(arms.values()))
print(sorted(arms))
seeds=sorted(set(r['seed'] for r in rows)); print('seeds',len(seeds),seeds[0],seeds[-1], seeds==list(range(7489160,7489640)))
pairs=collections.Counter((r['arm'],r['seed']) for r in rows); print('dups',sum(v>1 for v in pairs.values()), 'pairs',len(pairs))
print('commit',collections.Counter(r['commit'] for r in rows))
print('cell',collections.Counter(r['cell'] for r in rows),'q',collections.Counter(r['q'] for r in rows))
print('cpu field',collections.Counter(r['cpu'] for r in rows))
print('learner',collections.Counter((r['arm'],r['learner']) for r in rows if r['learner']))
print('name==cell|arm', all(r['name']==f"E30|{r['arm']}" for r in rows))
for k in ['all_delay','ttc_net','b45_step','passed','arrived','N','E30','out_E30','ttc3','m_ttc3_all','m_stuck_n','collisions','teleports','events_ge45','steps','m_dropped']:
    vals=[r[k] for r in rows]; nn=sum(v is None for v in vals)
    ok=[v for v in vals if v is not None]
    print(k,'None',nn, 'min',min(ok) if ok else None,'max',max(ok) if ok else None, 'nan',sum(isinstance(v,float) and v!=v for v in ok))
bad=[r for r in rows if (r['E30'] or 0)+(r['out_E30'] or 0)!=r['ttc_net']]; print('ttc_net != E30+out_E30:',len(bad))
bad=[r for r in rows if r['ttc3']!=r['ttc_net']]; print('ttc3 != ttc_net:',len(bad))
bad=[r for r in rows if r['m_ttc3_all']!=r['ttc_net']]; print('m_ttc3_all != ttc_net:',len(bad))
# same draw per seed across arms
bys=collections.defaultdict(set)
for r in rows: bys[r['seed']].add(r['draw'])
print('seeds with >1 distinct draw',sum(len(v)>1 for v in bys.values()))
dr=np.array([list(v)[0][1:] for v in bys.values()],float); print('onset range',dr[:,0].min(),dr[:,0].max(),'dur range',dr[:,1].min(),dr[:,1].max())
print('draw kind',collections.Counter(r['draw'][0] for r in rows))
# files per learner
for a in ['w0u250','w1u500','w2u250','w3u500','w4u500','MPC-F','p333','nc']:
    print(a, d['files'][a], len(d['cfg'][a]))
print('cfg variants per arm >1:',{a:len(v) for a,v in d['cfg'].items() if len(v)>1})
print('ctrl_sha per arm >1:', {a:n for a,n in ((a,len(set(r['ctrl_sha256'] for r in rows if r['arm']==a))) for a in arms) if n>1})
print('stuck rows per arm',{a:sum(1 for r in rows if r['arm']==a and (r['m_stuck_n'] or 0)>0) for a in sorted(arms)})
print('collisions rows per arm',{a:sum(1 for r in rows if r['arm']==a and (r['collisions'] or 0)>0) for a in sorted(arms)})
print('teleports rows per arm',{a:sum(1 for r in rows if r['arm']==a and (r['teleports'] or 0)>0) for a in sorted(arms)})
