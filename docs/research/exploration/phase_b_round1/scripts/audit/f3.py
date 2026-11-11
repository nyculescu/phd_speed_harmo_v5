import json
d=json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
T=d['cells']['TRUCK']
o=T['overfit_vs_p333']
print('overfit delay, sorted (opp vs p333, 95%):')
for k,v in sorted(o.items(), key=lambda kv:-kv[1]['delay'][0]):
    print('  %-18s %+.2f [%+.2f, %+.2f]  cf %+.2f [%+.2f, %+.2f]'%(k,*v['delay'],*v['cf']))
def g(x): return json.dumps(x,sort_keys=True)[:400]
nc=d['S']['map_report_only']['nc']
print('S nc cf', g(nc['cf'])); print('S nc delay', g(nc['delay']))
tn=T['map_report_only']['nc']
print('T nc cf', g(tn['cf'])); print('T nc delay', g(tn['delay']))
print('per_learner sample', g(T['map']['os0_10_10']['per_learner']))
print('pr28', g(T['pr28']))
print('resilience', g({k:v for k,v in T['resilience'].items() if k!='per_opponent'}))
print('t2', g({k:(v if not isinstance(v,(dict,list)) or len(v)<8 else len(v)) for k,v in T['t2_counting_filter'].items()}))
print('mechG', g(d['provenance']['mechanism_G']))
print('must', d['must_carry'][:600])
