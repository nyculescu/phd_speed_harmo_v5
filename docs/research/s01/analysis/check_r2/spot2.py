"""Past-limit ALKS events (bins -5 to -9, without the -9 bin), 7,000 abs, 3,500 b45, X1-vs-X2 per arm."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib2 import *
T = load()
pl = lambda r: sum(r["m_peak_alks"][4:8])
def opps(cell):
    return sorted({a for (c, a, q) in T if c == cell and q == 5300 and a not in DRL})
for cell in ("X1", "X2"):
    P = arm(T, cell, "v3w", 5300, pl)
    for o in ("nc", "3e", "p333"):
        O = arm(T, cell, o, 5300, pl)
        print(cell, "past-limit v3w vs", o, f1(mdiff(P, O), 2), "medians", np.median(list(P.values())), np.median(list(O.values())))
    meds = sorted((round(float(np.median(list(arm(T, cell, g, 5300, pl).values()))), 2), g) for g in list(GROUPS) + opps(cell))
    print(cell, "medians", meds)
car5 = lambda r: sum(r["m_peak_car"][4:8])
print("car past -5 X1 v3w/nc medians", np.median(list(arm(T, "X1", "v3w", 5300, car5).values())), np.median(list(arm(T, "X1", "nc", 5300, car5).values())))
P = arm(T, "B", "os1_15_10", 7000, "ttc_net"); O = arm(T, "B", "nc", 7000, "ttc_net")
print("7000 os1 abs", mdiff(P, O))
print("3500 b45 medians nc", np.median(list(arm(T, "B", "nc", 3500, "b45_step").values())),
      {o: (np.median(list(arm(T, "B", o, 3500, "b45_step").values())), np.mean(list(arm(T, "B", o, 3500, "b45_step").values())) - np.mean(list(arm(T, "B", "nc", 3500, "b45_step").values()))) for o in ("v3w", "p333", "3e")})
print("3500 flow v3w vs 3e 99%:", eff(arm(T, "B", "v3w", 3500, "passed"), arm(T, "B", "3e", 3500, "passed"), 1, (0.5, 99.5)))
print("X2 os0 vs p333 ref os0:", eff(arm(T, "X2", "p333", 5300, "all_delay"), arm(T, "X2", "os0_10_10", 5300, "all_delay"), 1))
