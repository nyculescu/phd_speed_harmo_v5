import sys
sys.path.insert(0, ".")
import numpy as np
from mylib import *
T = load()
print("tail vs nc cf B4500", fmt(eff(arm(T, "B", "tail", 4500, "ttc_net"), arm(T, "B", "nc", 4500, "ttc_net"))))
print("v3w vs nc cf B4500", fmt(eff(arm(T, "B", "v3w", 4500, "ttc_net"), arm(T, "B", "nc", 4500, "ttc_net"))))
print("tail vs nc cf X2", fmt(eff(arm(T, "X2", "tail", 5300, "ttc_net"), arm(T, "X2", "nc", 5300, "ttc_net"))))
print("sw vs 3ex2 cf X2", eff(arm(T, "X2", "sw", 5300, "ttc_net"), arm(T, "X2", "3ex2", 5300, "ttc_net")))
print("tail vs 3ex2 delay X2", fmt(eff(arm(T, "X2", "tail", 5300, "all_delay"), arm(T, "X2", "3ex2", 5300, "all_delay"))))
fl = []
for a in ("3e","3ex1","a4400_10_1","copy","lr1000_10_1","lr1000_16_2","lr400_13_2","lr400_16_1","os0_10_10","os1_10_0","os1_15_10","p333","r4a1","z33133","nc"):
    t = eff(arm(T, "X1", "v3w", 5300, "passed"), arm(T, "X1", a, 5300, "passed"), sign=1)
    fl.append((round(t[0], 2), round(t[1], 2), a))
print("X1 flow v3w vs each", sorted(fl))
fp = lambda r: float(r["finished_pct"]) if r.get("finished_pct") is not None else float("nan")
A = arm(T, "B", "v3w", 5000, "finished_pct"); P = arm(T, "B", "p333", 5000, "finished_pct")
print("fin 5000 v3w-p333 pp", mdiff(A, P))
print("B3500 flow vs 3e", eff(arm(T, "B", "v3w", 3500, "passed"), arm(T, "B", "3e", 3500, "passed"), sign=1))
print("B5000 flow vs os1", eff(arm(T, "B", "v3w", 5000, "passed"), arm(T, "B", "os1_15_10", 5000, "passed"), sign=1))
print("B7000 b45 vs 3e", fmt(eff(arm(T, "B", "v3w", 7000, "b45_step"), arm(T, "B", "3e", 7000, "b45_step"))))
