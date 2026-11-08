from vlib import *
import numpy as np
# exactly -4.5 steps, event seconds vs b3_step
bad = 0; ex = {'alks': [], 'all': []}
for (n, s), r in T.items():
    es = sum(r[f'm_event_s_{c}'] for c in CL)
    if abs(es - r['b3_step']) > 1e-6 * max(1, r['b3_step']) + 1e-6:
        bad += 1
    le = round(r['alks_b45_step'] * 10)
    lt = sum(r['m_ah_alks'][:11])
    ex['alks'].append((le - lt, le))
    le = round(r['b45_step'] * 10); lt = sum(sum(r[f'm_ah_{c}'][:11]) for c in CL)
    ex['all'].append((le - lt, le))
print('event_s != b3_step rows:', bad, 'of', len(T))
for k, v in ex.items():
    v = np.array(v); print(k, 'exact -4.5 steps share of <=-4.5 steps: %.4f' % (v[:, 0].sum() / v[:, 1].sum()), 'min diff', v[:, 0].min())
# accel histograms around -4.5 and -7, arm medians of per-seed learner means
def ahb(c, i):
    return lambda r: r[f'm_ah_{c}'][i]
for cell in ('X1', 'X2'):
    for a in ('nc', 'v3w', '3e', 'p333', 'os1_15_10'):
        out = []
        for c in ('car', 'alks', 'truck'):
            vals = [np.median(list(arm(cell, a, ahb(c, i)).values())) for i in (5, 6, 9, 10, 11, 12)]
            out.append(f"{c}: [-7.5,-7) {vals[0]:.0f} [-7,-6.5) {vals[1]:.0f} [-5.5,-5) {vals[2]:.0f} [-5,-4.5) {vals[3]:.0f} [-4.5,-4) {vals[4]:.0f} [-4,-3.5) {vals[5]:.0f}")
        print(cell, a, ' | '.join(out))
