import json, sys, collections, pickle
src='/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
keep=['name','arm','learner','seed','all_delay','ttc_net','b45_step','passed','arrived','N','commit','cell','q','E30','out_E30','ttc3','m_ttc3_all','events_ge45','m_stuck_n','collisions','teleports','ctrl_sha256','cpu','wall_s','m_dropped','steps','brake45','b45']
rows=[]; specs=collections.Counter(); perts=collections.Counter(); nkeys=collections.Counter(); files=collections.defaultdict(set); cfgk=collections.defaultdict(set)
n=0
with open(src) as f:
    for line in f:
        r=json.loads(line); n+=1
        nkeys[len(r)]+=1
        d={k:r.get(k) for k in keep}
        d['draw']=tuple(r['pert_log'][0]) if r.get('pert_log') else None
        d['pert_log']=json.dumps(r.get('pert_log'))
        specs[json.dumps(r.get('cell_spec'),sort_keys=True)]+=1
        c=r.get('cfg',{})
        p=(c.get('ctrl') or {}).get('env',{}).get('perturb') if isinstance(c.get('ctrl'),dict) else None
        if p is None: p=c.get('perturb')
        perts[json.dumps(p,sort_keys=True)]+=1
        files[r.get('arm')].add(json.dumps(r.get('files'),sort_keys=True))
        cc=dict(c); 
        cfgk[r.get('arm')].add(json.dumps(cc,sort_keys=True))
        d['has_ev45']='events_ge45' in r
        rows.append(d)
print('rows',n); print('nkeys',dict(nkeys)); print('specs',specs); print('perts',perts)
pickle.dump(dict(rows=rows,files={k:sorted(v) for k,v in files.items()},cfg={k:sorted(v) for k,v in cfgk.items()}),open(sys.argv[1],'wb'))
