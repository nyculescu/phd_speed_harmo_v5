"""IEEE double arithmetic of SUMO's stored acceleration at the decel limit (no simulation):
vNext = v - 4.5*TS (minNextSpeed), a = (vNext - v)/TS, TS = 100/1000.; then carry-over steps v' = v + a*TS."""
import numpy as np
TS = np.float64(100) / np.float64(1000)
dec = np.float64(4.5) * TS
rng = np.random.default_rng(1)
print('TS', repr(float(TS)), '4.5*TS', repr(float(dec)), 'vs 0.45', repr(0.45))
for lo, hi in ((0.5, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 40)):
    v = rng.uniform(lo, hi, 200000)
    vn = v - dec
    a = (vn - v) / TS
    lt, eq, gt = (a < -4.5).mean(), (a == -4.5).mean(), (a > -4.5).mean()
    # carry-over: next step keeps a (non-action step): v2 = vn + a*TS; a2 = (v2 - vn)/TS
    v2 = vn + a * TS
    a2 = (v2 - vn) / TS
    lt2 = (a2 < -4.5).mean()
    # chain of 5 carry-over steps (action step 0.5 s)
    vv, aa = vn.copy(), a.copy()
    lt_chain = []
    for k in range(4):
        v3 = vv + aa * TS
        aa = (v3 - vv) / TS
        vv = v3
        lt_chain.append((aa < -4.5).mean())
    print(f'v {lo:5.1f}-{hi:5.1f} m/s ({lo*3.6:5.1f}-{hi*3.6:5.1f} km/h): a<-4.5 {lt:.3f}  ==-4.5 {eq:.3f}  >-4.5 {gt:.3f} | carry1 a<-4.5 {lt2:.3f} | chain {np.round(lt_chain,3)}')
