"""Desk arithmetic, no simulation: the rear gap LC2013 asks of an IDM follower against the gap that follower holds.
Formulas: MSLaneChanger.cpp:863-879 (rear gap < follower secure gap x safety factor blocks), MSLCM_LC2013.cpp:2056-2057 (factor = 1 / lcAssertive),
MSCFModel_IDM.cpp:218-221 (secure gap = v*tau + v*dv / (2*sqrt(accel*decel))), MSCFModel.cpp:178-184 (Krauss merger's front gap, equal decel: about v*tau_h).
Plant values: ALKS accel 2.6, decel 4.5, minGap 2.5 (b_merge.py:41); lcAssertive 1.4 on every type (fleet.py:179, baseline_v1/plant_p0.json)."""
import math
A, B, S0, LC = 2.6, 4.5, 2.5, 1.4
K = 2 * math.sqrt(A * B)
LEN, TAU_H = 4.5, 0.93     # merger length (assumed); human tau mean about 0.93 s (V187)
def rear(v, tau, dv):      # follower at v, merger at v - dv
    return max(0.0, v * tau + v * dv / K) / LC
for v in (27.78, 20.0):
    for dv in (0.0, 3.0, -3.0):
        r08, r16 = rear(v, 0.8, dv), rear(v, 1.6, dv)
        print(f"v {v:5.2f} m/s, merger slower by {dv:+.0f} m/s: rear gap needed 0.8 s {r08:5.1f} m, 1.6 s {r16:5.1f} m, ratio {r08 / r16 if r16 else float('nan'):.2f}")
    print(f"v {v:5.2f}: stopped merger (dv = v): 0.8 s {rear(v, 0.8, v):6.1f} m, 1.6 s {rear(v, 1.6, v):6.1f} m")
    for tau in (0.8, 1.2, 1.6, 2.0, 2.5):
        held = S0 + v * tau                         # IDM steady gap far below the desired speed (larger near it)
        need = rear(v, tau, 0.0) + LEN + v * TAU_H / LC
        print(f"   tau {tau:.1f}: gap held {held:5.1f} m, needed for an equal-speed human merger {need:5.1f} m, surplus {held - need:+6.1f} m")
print(f"share of each added metre of ALKS gap that counts toward acceptance: 1 - 1/lcAssertive = {1 - 1 / LC:.3f} at 1.4, {1 - 1 / 1.0:.3f} at 1.0")
