"""Event-edge samples by period, the K3 analogue, and merge shares of each arm's own samples (read only)."""
import json, pickle
import numpy as np
exec(open("s1.py").read().split("ALLR =")[0])
R = S["readings"]["lr400_16_1"]["away"]; print("away lr400_16_1 stored:", {k: round(v, 2) for k, v in R.items()})
R = S["readings"]["grid_lr400_13_1"]["away"]; print("away grid_lr400_13_1 stored:", {k: round(v, 2) for k, v in R.items()})
def rp(roads, pers=None): return lambda r: rsum(r, "m_road_ttc3", roads, pers)
arms = ("v3w", "nc", "p333", "lr400_16_1", "grid_lr400_13_1", "MPC-F")
mean = lambda a, f: float(np.mean([col(w, f).mean() for w in V3W])) if a == "v3w" else float(col(a, f).mean())
print("mean samples on event edges 1-2 by period")
for per in (("before",), ("taper", "hold"), ("after",), ("rest",)):
    print("  ", "+".join(per).ljust(12), " ".join(f"{a} {mean(a, rp(('1', '2'), per)):6.1f}" for a in arms))
print("mean samples whole network by period: taper+hold", " ".join(f"{a} {mean(a, lambda r: r['ttc3_p_taper'] + r['ttc3_p_hold']):6.1f}" for a in arms))
print("v3w vs nc, event edges during taper+hold:", fm(edge("nc", rp(("1", "2"), ("taper", "hold")))), " whole window event edges:", fm(edge("nc", rp(("1", "2")))))
print("v3w vs nc, whole network taper+hold:", fm(edge("nc", lambda r: r["ttc3_p_taper"] + r["ttc3_p_hold"])))
print("share of each arm's own mean samples at merge 2 / merges 1+2")
for a in arms:
    t = mean(a, "ttc_net"); print("  ", a.ljust(16), f"{100 * mean(a, rp(('4a', 'ramp2'))) / t:4.0f}% {100 * mean(a, rp(('4a', 'ramp2', '3a', 'ramp1'))) / t:4.0f}%")
# split merge 2 into mainline edge 4a (all lanes incl. the accelerating lane) and the ramp itself
print("mean samples on 4a vs ramp2 (r2, rj2):", " ".join(f"{a} {mean(a, rp(('4a',))):6.1f}/{mean(a, rp(('ramp2',))):5.1f}" for a in arms))
print("E on ramp2 only vs lr400_16_1", fm(edge("lr400_16_1", rp(("ramp2",)))), " on 4a only", fm(edge("lr400_16_1", rp(("4a",)))))
