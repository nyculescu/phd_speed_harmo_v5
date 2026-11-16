"""Named fields from the recorded v2.3 reading: steady-traffic stage 0 counts and the location rows (no dump)."""
import json
J = json.load(open('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json'))
S = J['S']
print('S keys', sorted(S))
M = S['map']
k1 = [(a, round(v['cf']['effect'], 2), [round(x, 2) for x in v['cf']['ci_m']]) for a, v in M.items() if v['cf']['effect'] < 10 or v['cf']['ci_m'][0] <= 0]
k2 = [(a, round(v['delay']['ci_m'][0], 2)) for a, v in M.items() if v['delay']['ci_m'][0] <= -1]
print('steady: K1 fires against', len(k1), k1)
print('steady: K2 (margin 1) fires against', len(k2), 'of', len(M), sorted(k2, key=lambda t: t[1])[:5])
k22 = [(a, round(v['delay']['ci_m'][0], 2)) for a, v in M.items() if v['delay']['ci_m'][0] <= -2]
print('steady: margin 2 fires against', len(k22))
C = J['cells']['TRUCK']
loc = C['location']
print('location keys', sorted(loc)[:20] if isinstance(loc, dict) else type(loc))
print('no_control', {k: (v if not isinstance(v, (dict, list)) or len(str(v)) < 200 else type(v).__name__) for k, v in C['no_control'].items()})
print('outcome', C['outcome'], 'n_seeds', C['n_seeds'], 'learner_signs n', C['n_learner_signs'])
print('closest', C['closest'] if len(str(C['closest'])) < 600 else str(C['closest'])[:600])
