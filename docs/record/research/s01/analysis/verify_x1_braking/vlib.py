"""Own statistic and arm pooling, written from the round-2 convention text (not imported)."""
import pickle
import numpy as np

T = pickle.load(open('/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_braking/test.pkl', 'rb'))
SEEDS = sorted({k[1] for k in T})
ARMS = {'v3w': ['w0u250', 'w1u500', 'w2u250', 'w3u500', 'w4u500'], 'tail': [f't{i}' for i in range(5)],
        'sw': [f's{i}u500' for i in range(5)], 'bv3': [f'd{i}u500' for i in range(5)],
        'nc': ['nc'], '3e': ['3e'], '3ex1': ['3ex1'], '3ex2': ['3ex2'], 'p333': ['p333'], 'os1_15_10': ['os1_15_10']}
CL = ('car', 'alks', 'truck')


def pk(r, c, lo, hi=None):
    return float(sum(r[f'm_peak_{c}'][lo:hi]))


def g(r, k):
    v = r.get(k)
    return 0.0 if v is None else float(v)


def km(r, c=None):
    return (sum(r[f'm_dist_m_{x}'] for x in CL) if c is None else r[f'm_dist_m_{c}']) / 1000.0


M = {}
for c in CL:
    M[f'ev45_{c}'] = (lambda c: lambda r: pk(r, c, 3))(c)
    M[f'ev4_{c}'] = (lambda c: lambda r: pk(r, c, 2))(c)
    M[f'ev5_{c}'] = (lambda c: lambda r: pk(r, c, 4, 8))(c)
    M[f'ev3_{c}'] = (lambda c: lambda r: g(r, f'm_events_{c}'))(c)
    M[f'ev45_{c}_per_km'] = (lambda c: lambda r: pk(r, c, 3) / km(r, c))(c)
    M[f'ev4_{c}_per_km'] = (lambda c: lambda r: pk(r, c, 2) / km(r, c))(c)
    M[f'cshare_{c}'] = (lambda c: lambda r: g(r, f'm_cascade_{c}') / g(r, f'm_events_{c}'))(c)
    M[f'km_{c}'] = (lambda c: lambda r: km(r, c))(c)
M['ev45_all'] = lambda r: sum(pk(r, c, 3) for c in CL)
M['ev4_all'] = lambda r: sum(pk(r, c, 2) for c in CL)
M['ev45_all_per_km'] = lambda r: M['ev45_all'](r) / km(r)
M['ev45_all_per_served'] = lambda r: M['ev45_all'](r) / g(r, 'passed')
M['ev4_all_per_km'] = lambda r: M['ev4_all'](r) / km(r)
M['cshare_all'] = lambda r: sum(g(r, f'm_cascade_{c}') for c in CL) / sum(g(r, f'm_events_{c}') for c in CL)
for k in ('b3_step', 'b45_step', 'b7_step', 'alks_b3_step', 'alks_b45_step', 'alks_b7_step', 'free_brake_alks_step', 'passed', 'all_delay', 'ttc_net', 'dist_step'):
    M[k] = (lambda k: lambda r: g(r, k))(k)
M['nonalks_b45_step'] = lambda r: g(r, 'b45_step') - g(r, 'alks_b45_step')
M['b45_step_per_km'] = lambda r: g(r, 'b45_step') / km(r)
M['alks_b45_step_per_km'] = lambda r: g(r, 'alks_b45_step') / km(r, 'alks')
M['nonalks_b45_step_per_km'] = lambda r: (g(r, 'b45_step') - g(r, 'alks_b45_step')) / (km(r, 'car') + km(r, 'truck'))
M['km_all'] = lambda r: km(r)
M['b45_step_per_served'] = lambda r: g(r, 'b45_step') / g(r, 'passed')


def arm(cell, a, f):
    """seed -> mean over the arm's learners of f(row)."""
    if isinstance(f, str):
        f = M[f]
    return {s: float(np.mean([f(T[(f'{cell}|{n}', s)]) for n in ARMS[a]])) for s in SEEDS}


_IDX = np.random.default_rng(20261104).integers(0, 40, (20000, 40))


def comp(P, O, sign=-1):
    """Returns (median P, median O, median paired diff [CI], effect % [CI]); sign -1 = lower is better."""
    s = sorted(set(P) & set(O))
    assert len(s) == 40
    p = np.array([P[k] for k in s]); o = np.array([O[k] for k in s])
    d = p - o
    ref = max(np.median(o), 1e-9)
    e = sign * d / ref * 100
    rng = np.random.default_rng(20261104)
    idx = rng.integers(0, len(d), (20000, len(d)))
    bd = np.median(d[idx], axis=1); be = np.median(e[idx], axis=1)
    return (np.median(p), np.median(o), np.median(d), *np.percentile(bd, (2.5, 97.5)), np.median(e), *np.percentile(be, (2.5, 97.5)))


def fmt(t):
    return f'P {t[0]:.4g} O {t[1]:.4g} d {t[2]:+.4g} [{t[3]:+.4g}, {t[4]:+.4g}] eff {t[5]:+.1f}% [{t[6]:+.1f}, {t[7]:+.1f}]'
M['ev4_truck'] = lambda r: pk(r, 'truck', 2)
M['ev35_truck'] = lambda r: pk(r, 'truck', 1)
M['ev4_carlike'] = lambda r: pk(r, 'car', 2) + pk(r, 'alks', 2)
M['ev3_all'] = lambda r: sum(g(r, f'm_events_{c}') for c in CL)
M['ev3_all_per_km'] = lambda r: sum(g(r, f'm_events_{c}') for c in CL) / km(r)
M['ev4_all_per_served'] = lambda r: M['ev4_all'](r) / g(r, 'passed')
M['ev45_lim_band'] = lambda r: pk(r, 'car', 3, 4) + pk(r, 'alks', 3, 4)
for k in ('ttc3_r_4a', 'ttc3_r_3', 'ttc3_r_ramp2', 'ttc3_r_rest', 'ttc3_p_rest', 'ttc3_p_after', 'ttc3_p_hold', 'sev3_r_4a', 'ttc3_s_lo', 'ttc3_s_mid', 'ttc3_s_hi'):
    M[k] = (lambda k: lambda r: g(r, k))(k)
M['ev35_truck_per_km'] = lambda r: pk(r, 'truck', 1) / km(r, 'truck')
