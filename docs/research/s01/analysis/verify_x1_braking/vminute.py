from vlib import *
import numpy as np
def mspeed(part, i):
    def f(r):
        mm = r['m_minute']; n = mm[f'm2_{part}_n'][i]
        return 3.6 * mm[f'm2_{part}_vs'][i] / n if n > 0 else np.nan
    return f
for cell in ('X1',):
    for part, lab in (('acc', '4a'), ('up', 'edge3')):
        print(cell, lab, 'minute start t, median km/h  nc | v3w | 3e  and v3w-nc paired median [CI]')
        for i in range(25):
            A = {a: arm(cell, a, mspeed(part, i)) for a in ('nc', 'v3w', '3e')}
            t = comp(A['v3w'], A['nc'])
            print(f'  {300+60*i:5d}  {np.nanmedian(list(A["nc"].values())):5.1f} | {np.nanmedian(list(A["v3w"].values())):5.1f} | {np.nanmedian(list(A["3e"].values())):5.1f}   d {t[2]:+5.1f} [{t[3]:+5.1f}, {t[4]:+5.1f}]')
