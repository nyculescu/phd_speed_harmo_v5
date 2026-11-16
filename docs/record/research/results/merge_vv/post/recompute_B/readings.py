"""Recomputer B: V2, V3a, V3b, change, standing cut and edge-1-out readings from the screen rows.

Written from merge_vv.md v1.1 and c1_confirm.md section 1 only; the run's reader was not opened first.
"""
import json
import time

import numpy as np
import pandas as pd

HERE = '/home/catalin/work/phd/v5b1_runs/vv_post/recompute_B/'
LEARNERS = ['w0u250', 'w1u500', 'w2u250', 'w3u500', 'w4u500']
RULES = ['lr400_16_1', 'grid_lr400_13_1']
ARMS = LEARNERS + RULES + ['p333', 'nc']
SEEDS = np.arange(7492000, 7492480)
N = len(SEEDS)
B = 20000
RNG_SEED = 20261108
CHUNK = 2000

df = pd.read_pickle(HERE + 'rows.pkl')
df['merge_area'] = df[['road_3a', 'road_4a', 'road_ramp1', 'road_ramp2']].sum(axis=1)
df['edge1'] = df['road_1']
df['rest'] = df['ttc_net'] - df['merge_area'] - df['edge1']
df['no_edge1'] = df['ttc_net'] - df['edge1']


def wide(cell, col):
    w = df[df.cell == cell].pivot(index='seed', columns='arm', values=col)
    return w.reindex(index=SEEDS, columns=ARMS)


rng = np.random.default_rng(RNG_SEED)
IDX = rng.integers(0, N, size=(B, N))


def boot_median(v, idx=IDX):
    out = np.empty(idx.shape[0])
    for a in range(0, idx.shape[0], CHUNK):
        out[a:a + CHUNK] = np.median(v[idx[a:a + CHUNK]], axis=1)
    return out


def edges(cell, col, rule):
    """Per-seed edges d[l, s] = -(P_l - R)/median(R) x 100, the full-sample denominator fixed."""
    w = wide(cell, col)
    r = w[rule].to_numpy(float)
    den = np.median(r)
    d = np.stack([-(w[l].to_numpy(float) - r) / den * 100 for l in LEARNERS])
    return d, r, den, w


def cd5(cell, col, rule):
    d, r, den, w = edges(cell, col, rule)
    if den == 0:
        return None
    assert not np.isnan(d).any(), (cell, col, rule)
    per_l = np.median(d, axis=1)
    boot = np.mean([boot_median(d[i]) for i in range(len(LEARNERS))], axis=0)
    # Sensitivity: denominator recomputed on each resample.
    rb = boot_median(r)
    alt = np.mean([boot_median(r - w[l].to_numpy(float)) for l in LEARNERS], axis=0) / rb * 100
    return {'point': float(per_l.mean()), 'per_learner': per_l.tolist(), 'den': float(den),
            'boot': boot, 'boot_altden': alt}


def pct(x, q):
    return [float(v) for v in np.atleast_1d(np.percentile(x, q))]


res = {'conventions': {'B': B, 'rng': RNG_SEED, 'idx': 'default_rng(20261108).integers(0, 480, size=(20000, 480))',
                       'percentile': 'numpy linear', 'denominator': 'full-sample median of the rule, fixed'}}
t0 = time.time()
E = {}
for cell in ('L300', 'L600'):
    for col in ('ttc_net', 'vv_ttc3_main', 'vv_m_time', 'no_edge1', 'merge_area', 'edge1', 'rest'):
        if cell == 'L600' and col == 'vv_m_time':
            continue
        if cell == 'L600' and col == 'vv_ttc3_main':
            pass
        for rule in RULES:
            E[(cell, col, rule)] = cd5(cell, col, rule)
print('bootstraps done %.0f s' % (time.time() - t0), flush=True)


def summ(e, extra=()):
    b = e['boot']
    out = {'point': e['point'], 'per_learner': e['per_learner'], 'rule_median': e['den'],
           'q1.25': pct(b, 1.25)[0], 'q98.75': pct(b, 98.75)[0], 'q2.5': pct(b, 2.5)[0],
           'q97.5': pct(b, 97.5)[0], 'q0.625': pct(b, 0.625)[0], 'q99.375': pct(b, 99.375)[0],
           'se': float(b.std(ddof=1)),
           'altden_q1.25': pct(e['boot_altden'], 1.25)[0], 'altden_q99.375': pct(e['boot_altden'], 99.375)[0]}
    return out


# V2: 0.1-s edge minus 1-Hz edge at 300 m.
v2 = {}
for rule in RULES:
    a = E[('L300', 'vv_m_time', rule)]
    h = E[('L300', 'ttc_net', rule)]
    diff = a['boot'] - h['boot']
    lo, hi = pct(diff, [2.5, 97.5])
    v2[rule] = {'edge_01s': a['point'], 'edge_01s_95': pct(a['boot'], [2.5, 97.5]),
                'edge_1hz': h['point'], 'edge_1hz_95': pct(h['boot'], [2.5, 97.5]),
                'diff': a['point'] - h['point'], 'diff_95': [lo, hi], 'within_3': bool(lo > -3 and hi < 3)}
v2['reading'] = 'MET' if all(v2[r]['within_3'] for r in RULES) else 'LIMIT'
d3 = df[df.cell == 'L300']
v2['missed_share'] = {}
for arm in ARMS:
    x = d3[d3.arm == arm]
    v2['missed_share'][arm] = {
        'ratio_of_sums': float((x.vv_m_time.sum() - x.ttc_net.sum()) / x.vv_m_time.sum()),
        'median_per_run': float(((x.vv_m_time - x.ttc_net) / x.vv_m_time).median())}
res['V2'] = v2

# V3a replication and main-lane sensitivity at 300 m; V3b at 600 m.
res['V3a_replication'] = {r: summ(E[('L300', 'ttc_net', r)]) for r in RULES}
res['V3a_main'] = {r: summ(E[('L300', 'vv_ttc3_main', r)]) for r in RULES}
res['V3b'] = {r: summ(E[('L600', 'ttc_net', r)]) for r in RULES}
res['V3a_replication']['bounds_positive'] = all(res['V3a_replication'][r]['q1.25'] > 0 for r in RULES)
res['V3a_main']['bounds_positive'] = all(res['V3a_main'][r]['q1.25'] > 0 for r in RULES)
res['V3b']['holds_bounds'] = all(res['V3b'][r]['q1.25'] > 0 for r in RULES)
res['V3b']['worse_bounds'] = {r: res['V3b'][r]['q99.375'] < 0 for r in RULES}

# The change: 600-m edge minus 300-m edge, same resamples.
res['change'] = {}
for rule in RULES:
    a = E[('L600', 'ttc_net', rule)]
    h = E[('L300', 'ttc_net', rule)]
    diff = a['boot'] - h['boot']
    res['change'][rule] = {'point': a['point'] - h['point'], 'ci95': pct(diff, [2.5, 97.5]),
                           'excludes_0': bool(np.percentile(diff, 2.5) > 0 or np.percentile(diff, 97.5) < 0)}

# Edge-1 left out, and road groups (printed).
res['no_edge1'] = {c: {r: summ(E[(c, 'no_edge1', r)]) for r in RULES} for c in ('L300', 'L600')}
res['groups'] = {}
for c in ('L300', 'L600'):
    for g in ('merge_area', 'edge1', 'rest'):
        for r in RULES:
            e = E[(c, g, r)]
            w = wide(c, g)
            if e is None:
                res['groups']['%s|%s|%s' % (c, g, r)] = {'point': None, 'rule_median': 0.0,
                    'learner_minus_rule_median_samples': float(np.mean([np.median(w[l] - w[r]) for l in LEARNERS])),
                    'learner_minus_rule_mean_samples': float(np.mean([np.mean(w[l] - w[r]) for l in LEARNERS]))}
                continue
            deficit = float(np.mean([np.median(w[l] - w[r]) for l in LEARNERS]))
            mean_diff = float(np.mean([np.mean(w[l] - w[r]) for l in LEARNERS]))
            res['groups']['%s|%s|%s' % (c, g, r)] = {
                'point': e['point'], 'ci95': pct(e['boot'], [2.5, 97.5]), 'rule_median': e['den'],
                'learner_minus_rule_median_samples': deficit, 'learner_minus_rule_mean_samples': mean_diff}

# Lane-end standing cut per merge (VV-D12): several forms, since the plan does not fix the form.
cut = {}
for merge, col in (('merge1', 'end_stop'), ('merge2', 'end_stop2')):
    s3 = wide('L300', col).to_numpy(float)
    s6 = wide('L600', col).to_numpy(float)
    # Pooled over all 9 arms: 1 - sum(600)/sum(300), seeds resampled jointly.
    pt = 1 - s6.sum() / s3.sum()
    a3 = s3.sum(axis=1)
    a6 = s6.sum(axis=1)
    bs = np.array([1 - a6[IDX[i]].sum() / a3[IDX[i]].sum() for i in range(B)])
    cut[merge] = {'pooled9_ratio_of_sums': {'point': float(pt * 100), 'lo95': float(np.percentile(bs, 2.5) * 100)}}
    per_arm = {}
    for j, arm in enumerate(ARMS):
        x3 = s3[:, j]
        x6 = s6[:, j]
        p_ratio = 1 - x6.sum() / x3.sum()
        b_ratio = 1 - x6[IDX].sum(axis=1) / x3[IDX].sum(axis=1)
        m3 = np.median(x3)
        dd = (x3 - x6) / m3 * 100 if m3 > 0 else np.full(N, np.nan)
        per_arm[arm] = {'mean300': float(x3.mean()), 'mean600': float(x6.mean()),
                        'median300': float(m3), 'median600': float(np.median(x6)),
                        'ratio_of_sums': {'point': float(p_ratio * 100), 'lo95': float(np.percentile(b_ratio, 2.5) * 100)},
                        'median_paired_pct': {'point': float(np.median(dd)),
                                              'lo95': float(np.percentile(boot_median(dd), 2.5)) if m3 > 0 else None}}
    # v3w as mean of the five learners (C-D5 style) on the paired cut.
    dl = []
    for j, arm in enumerate(LEARNERS):
        m3 = np.median(s3[:, j])
        dl.append((s3[:, j] - s6[:, j]) / m3 * 100)
    dl = np.stack(dl)
    bl = np.mean([boot_median(dl[i]) for i in range(5)], axis=0)
    per_arm['v3w_cd5_form'] = {'point': float(np.median(dl, axis=1).mean()), 'lo95': float(np.percentile(bl, 2.5))}
    cut[merge]['per_arm'] = per_arm
    vveh3 = wide('L300', 'stand_n_' + ('3a_0' if merge == 'merge1' else '4a_0')).mean()
    vveh6 = wide('L600', 'stand_n_' + ('3a_0' if merge == 'merge1' else '4a_0')).mean()
    cut[merge]['distinct_vehicles_mean'] = {'L300': vveh3.to_dict(), 'L600': vveh6.to_dict()}
res['standing_cut'] = cut

json.dump(res, open(HERE + 'readings_B.json', 'w'), indent=1)
np.savez_compressed(HERE + 'edges_B.npz', **{'%s|%s|%s' % k: np.stack(edges(*k)[0]) for k in
                                              [('L300', 'ttc_net', r) for r in RULES] + [('L600', 'ttc_net', r) for r in RULES]
                                              + [('L300', 'vv_ttc3_main', r) for r in RULES]})
print('done %.0f s' % (time.time() - t0))
