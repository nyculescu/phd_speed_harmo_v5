from vlib import *
import numpy as np
def lvm(road):
    return lambda r: r.get(f'lv_sum_{road}', 0) / r[f'lv_n_{road}'] if r.get(f'lv_n_{road}') else np.nan
def ls_share(i):
    return lambda r: r['m_dec_level_s'][i] / sum(r['m_dec_level_s']) if r.get('m_dec_level_s') and sum(r['m_dec_level_s']) else np.nan
def on_share(r):
    on = sum(r['m_dec_level_s']); return on / (on + r['m_dec_off_s'])
for cell in ('X1', 'X2'):
    for a in ('v3w', 'tail', 'sw', 'bv3', '3e', '3ex1' if cell == 'X1' else '3ex2', 'p333', 'os1_15_10'):
        md = lambda f: np.nanmedian(list(arm(cell, a, f).values()))
        print(cell, f'{a:10s}', 'lv3 %.2f lv4a %.2f lv1 %.2f' % (md(lvm('3')), md(lvm('4a')), md(lvm('1'))),
              'level_s shares', ' '.join('%.3f' % md(ls_share(i)) for i in range(4)), 'on %.3f' % md(on_share),
              'tau_on_match %.3f' % md(lambda r: r['tau_on_match'] / r['tau_on_n']), 'tau_mismatch %.0f' % md('tau_mismatch' if 'tau_mismatch' in M else (lambda r: r['tau_mismatch'])),
              'chg/veh %.2f rev %.2f' % (md(lambda r: r['m_dec_totals_changed'] / r['m_dec_vehicles']), md(lambda r: r['m_dec_totals_reversals'] / r['m_dec_totals_changed'])))
