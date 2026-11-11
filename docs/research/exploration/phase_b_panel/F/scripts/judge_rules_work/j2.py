import json
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
T = J['cells']['TRUCK']
print('TRUCK keys', list(T.keys()))
def show(name, d):
    if isinstance(d, dict):
        print(name, {k: (v if not isinstance(v, (dict, list)) or (isinstance(v, list) and len(v) <= 4) else type(v).__name__ + str(len(v))) for k, v in d.items()})
    else:
        print(name, d)
m = T['map']
print('map opp', list(m.keys()))
show('TRUCK map 3E-C_TRUCK', m['3E-C_TRUCK'])
for k, v in m['3E-C_TRUCK'].items():
    show('  ' + k, v)
for k, v in m['os0_10_10'].items():
    show('  os0 ' + k, v)
S = J['S']['map']
for o in ('3E-C_TRUCK', 'os1_15_10', 'p333', 'os0_10_10', 'grid_z31333', 'lr400_16_1'):
    if o in S:
        for k, v in S[o].items():
            show('  S ' + o + ' ' + k, v)
print(J['provenance']['plateau'])
print(J['m'])
