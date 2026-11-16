import json
d=json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
T=d['cells']['TRUCK']
def s(o,n=600):
    return json.dumps(o,sort_keys=True)[:n]
print('overfit 3E-D', s(T['overfit_vs_p333']['3E-D_TRUCK'],900))
print('overfit 3E-C', s(T['overfit_vs_p333']['3E-C_TRUCK'],900))
for k in ['copy','3ex1','3e','MPC-F','os0_10_10','os1_15_10','lr1000_16_2']:
    print('overfit',k, s(T['overfit_vs_p333'][k],500))
print('S.map p333 delay', s(d['S']['map']['p333']['delay']))
print('S.map p333 cf', s(d['S']['map']['p333']['cf']))
print('S.map 3E-C cf', s(d['S']['map']['3E-C_TRUCK']['cf']))
print('S.map 3E-C delay', s(d['S']['map']['3E-C_TRUCK']['delay']))
print('no_control', s(T['no_control'],1200))
print('AG', s(T['adaptation_gain'],1200))
print('closest', s(T['closest'],900))
print('plateau', s(d['provenance']['plateau']))
print('learner_signs', s(T['learner_signs'],800))
m=T['map']
print('map keys per opp', sorted(m['p333'].keys()))
rows=[]
for k,v in m.items():
    rows.append((k, v['delay'], v['cf']))
for k,dl,cf in sorted(rows,key=lambda r:json.dumps(r[2])):
    print(k,'delay',s(dl,200),'cf',s(cf,200))
