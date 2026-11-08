"""Spot checks of draft numbers against the data (critic)."""
import json
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from clib import D, arm, diff_mean, load, med, raw, v

T = load("test")
S = load("s1")
B = load("band")
Q = 5300.0
k = lambda key: (lambda r: v(r, key))

print("1. X1 v3w vs nc ttc_net (draft 16.6 more [8.4, 25.1]):", raw(arm(T, "X1", "v3w", Q, k("ttc_net")), arm(T, "X1", "nc", Q, k("ttc_net"))))
print("   X1 v3w vs nc all_delay (draft 27.3):", raw(arm(T, "X1", "v3w", Q, k("all_delay")), arm(T, "X1", "nc", Q, k("all_delay"))))

ev45 = lambda r: sum(sum((r.get(f"m_peak_{c}") or [0] * 10)[3:]) for c in ("car", "alks", "truck"))
for a in ("v3w", "nc", "3e", "tail", "sw", "bv3", "p333"):
    print(f"2. X1 ev45 median {a}:", med(arm(T, "X1", a, Q, ev45)))

print("3. X1 ttc3_r_4a mean diff v3w-nc (draft +272.3 [229.4, 311.6]):", diff_mean(arm(T, "X1", "v3w", Q, k("ttc3_r_4a")), arm(T, "X1", "nc", Q, k("ttc3_r_4a"))))
print("4. X1 sev3_r_4a mean diff (draft +12.7 [8.2, 17.2]):", diff_mean(arm(T, "X1", "v3w", Q, k("sev3_r_4a")), arm(T, "X1", "nc", Q, k("sev3_r_4a"))))
print("5. X1 end_stop2 mean diff (draft +461 [357, 558]); nc median:", diff_mean(arm(T, "X1", "v3w", Q, k("end_stop2")), arm(T, "X1", "nc", Q, k("end_stop2"))), med(arm(T, "X1", "nc", Q, k("end_stop2"))))

for q, ref, txt in ((7000.0, "3e", "+4.5 [-0.7, +6.2]"), (7000.0, "p333", "+3.7 [2.6, 5.2]"), (3500.0, "p333", "-0.2 [-0.9, +0.1]")):
    print(f"6. S1 {q} v3w vs {ref} all_delay (draft {txt}):", raw(arm(S, "B", "v3w", q, k("all_delay")), arm(S, "B", ref, q, k("all_delay"))))
for q in (3500.0, 7000.0):
    print(f"   S1 {q} unpaired median all_delay p333 / v3w / nc:", med(arm(S, "B", "p333", q, k("all_delay"))), med(arm(S, "B", "v3w", q, k("all_delay"))), med(arm(S, "B", "nc", q, k("all_delay"))))

print("7. band 5000 v3w vs p333 all_delay (draft -3.2 [-5.3, +1.4]):", raw(arm(B, "B", "v3w", 5000.0, k("all_delay")), arm(B, "B", "p333", 5000.0, k("all_delay"))))
print("   band 5000 unpaired medians p333 / v3w:", med(arm(B, "B", "p333", 5000.0, k("all_delay"))), med(arm(B, "B", "v3w", 5000.0, k("all_delay"))))

share3 = lambda r: (r["m_dec_level_s"][3] / sum(r["m_dec_level_s"])) if r.get("m_dec_level_s") and sum(r["m_dec_level_s"]) else float("nan")
print("8. X1 p333 share3 median (draft 0.934):", med(arm(T, "X1", "p333", Q, share3)))
print("   X1 v3w share3 median (draft 0.731), X2 (0.775):", med(arm(T, "X1", "v3w", Q, share3)), med(arm(T, "X2", "v3w", Q, share3)))

print("9. nc X1 vs X2 ttc_net (draft +7.3 [-4.1, +20.6], positive = X1 fewer):", raw(arm(T, "X1", "nc", Q, k("ttc_net")), arm(T, "X2", "nc", Q, k("ttc_net"))))

ev5a = lambda r: sum((r.get("m_peak_alks") or [0] * 10)[4:8])
arms_x1 = sorted({a for (c, a, q) in T if c == "X1"})
res = {}
for a in arms_x1:
    res[a] = med(arm(T, "X1", a, Q, ev5a))
grp = {g: med(arm(T, "X1", g, Q, ev5a)) for g in ("v3w", "tail", "sw", "bv3")}
rules = {a: x for a, x in res.items() if not a[0] in "wtsd" or a in ("z33133",)}
print("10. X1 ev5_alks medians, groups:", grp)
print("    rules:", sorted(((round(x, 1), a) for a, x in res.items() if a[:1] not in ("w", "t", "s", "d")), key=lambda t: t[0]))

ev4 = lambda r: sum(sum((r.get(f"m_peak_{c}") or [0] * 10)[2:]) for c in ("car", "alks", "truck"))
ev4_served = lambda r: ev4(r) / max(v(r, "passed"), 1)
print("11. X1 ev4_all per served v3w vs nc (draft 1.7 % more [0.5, 6.5]):", raw(arm(T, "X1", "v3w", Q, ev4_served), arm(T, "X1", "nc", Q, ev4_served)))
ev4ca = lambda r: sum(sum((r.get(f"m_peak_{c}") or [0] * 10)[2:]) for c in ("car", "alks"))
print("    X1 ev4 cars+ALKS v3w vs nc (draft 7.2 % more [4.8, 11.5]):", raw(arm(T, "X1", "v3w", Q, ev4ca), arm(T, "X1", "nc", Q, ev4ca)))
print("    X1 ev4_all v3w vs nc raw (verifier 7.9 % more):", raw(arm(T, "X1", "v3w", Q, ev4), arm(T, "X1", "nc", Q, ev4)))

print("12. S1 7000 v3w vs nc ttc_net abs mean diff and medians:", diff_mean(arm(S, "B", "v3w", 7000.0, k("ttc_net")), arm(S, "B", "nc", 7000.0, k("ttc_net"))), med(arm(S, "B", "nc", 7000.0, k("ttc_net"))))
