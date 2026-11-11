"""EXPLORATORY: stored S6 rows, already read for a verdict. No traffic simulation."""
import json, numpy as np
J = json.load(open("/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json"))
T = J["cells"]["TRUCK"]
f = lambda e: "%+.2f [%+.2f, %+.2f]" % (e["effect"], e["ci_m"][0], e["ci_m"][1])
f95 = lambda e: "%+.2f [%+.2f, %+.2f]" % (e["effect"], e["ci95"][0], e["ci95"][1])
print("m =", J["m"])
lbs = {o: T["map"][o]["delay"]["ci_m"][0] for o in T["map"]}
print("TRUCK delay lower bounds (ci_m), min:", min(lbs, key=lbs.get), round(min(lbs.values()), 3), "| count lb > -2:", sum(v > -2 for v in lbs.values()), "of", len(lbs), "| count lb > -1:", sum(v > -1 for v in lbs.values()))
for o in ("3E-C_TRUCK", "os0_10_10", "p333", "3E-D_TRUCK"):
    print("TRUCK", o, "cf", f(T["map"][o]["cf"]), "| delay", f(T["map"][o]["delay"]))
S = J["S"]
slb = {o: S["map"][o]["delay"]["ci_m"][0] for o in S["map"]}
print("S delay lower bounds min:", min(slb, key=slb.get), round(min(slb.values()), 3), "| count lb > -2:", sum(v > -2 for v in slb.values()), "of", len(slb))
for o in ("3E-C_TRUCK", "os0_10_10", "p333"):
    print("S", o, "cf", f(S["map"][o]["cf"]), "| delay", f(S["map"][o]["delay"]))
scf = {o: S["map"][o]["cf"] for o in S["map"]}
print("S: opponents with cf point < 10 or lb <= 0:", sorted(o for o, e in scf.items() if e["effect"] < 10 or e["ci_m"][0] <= 0))
tcf = {o: T["map"][o]["cf"] for o in T["map"]}
print("TRUCK: opponents with cf point < 10 or lb <= 0:", sorted(o for o, e in tcf.items() if e["effect"] < 10 or e["ci_m"][0] <= 0))
print("TRUCK cf points sorted:", sorted((round(e["effect"], 2), o) for o, e in tcf.items())[:4])
R = T["map_report_only"]
for o in ("3E-C_TRUCK", "p333", "nc"):
    for k in ("jam_share", "congested_share", "congested_km_mean", "osc_kmh", "events_ge45", "ttc15", "ttc2", "sev3", "robust_braking", "b45_step", "delay_ramp", "delay_ramp2", "ttc3_lc_share"):
        e = R[o].get(k)
        if e and "effect" in e: print("report-only TRUCK", o, k, f95(e), "(95 %)", "ci_m [%+.2f, %+.2f]" % tuple(e["ci_m"]) if "ci_m" in e else "")
print("no_control keys:", list(T["no_control"]))
print({k: (v if not isinstance(v, dict) else {a: b for a, b in v.items() if not isinstance(b, (dict, list)) or len(b) < 4}) for k, v in T["no_control"].items()})

Z = np.load("../../../critic_F/s6_scalars.npz"); KEYS = list(Z["keys"]); n = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda cell, arm, key: Z[f"{cell}|{arm}"][:, KEYS.index(key)]
pooled = lambda cell, key: np.mean([col(cell, l, key) for l in LEARN], axis=0)
rng = np.random.default_rng(20261110); IDX = rng.integers(0, n, (10_000, n))
def eff(P, O, pct=(1.25, 98.75)):
    d = -(P - O) / np.median(O) * 100.0
    b = np.median(d[IDX], axis=1)
    return float(np.median(d)), *map(float, np.percentile(b, pct))
g = lambda t: "%+.2f [%+.2f, %+.2f]" % tuple(t)
print("\nrecount, pooled, 97.5 %:")
for o in ("3E-C_TRUCK", "os0_10_10", "p333"):
    print(" TRUCK vs", o, "cf", g(eff(pooled("TRUCK", "ttc_net"), col("TRUCK", o, "ttc_net"))), "| delay", g(eff(pooled("TRUCK", "all_delay"), col("TRUCK", o, "all_delay"))))
print(" 3E-C vs p333 cf", g(eff(col("TRUCK", "3E-C_TRUCK", "ttc_net"), col("TRUCK", "p333", "ttc_net"))), "delay", g(eff(col("TRUCK", "3E-C_TRUCK", "all_delay"), col("TRUCK", "p333", "all_delay"))))
for o in ("3E-C_TRUCK", "os0_10_10", "p333"):
    d = -(pooled("TRUCK", "all_delay") - col("TRUCK", o, "all_delay")) / np.median(col("TRUCK", o, "all_delay")) * 100
    print(" paired delay diff vs", o, "SD %.2f" % d.std(ddof=1), "IQR [%.2f, %.2f]" % tuple(np.percentile(d, (25, 75))))

# operating characteristic of the screen's rule
P_cf, P_dl = pooled("TRUCK", "ttc_net"), pooled("TRUCK", "all_delay")
def oc(opp, true_cf, true_dl, m, level=97.5, margin=2.0, thr=10.0, studies=4000, B=1000, seed=20261112):
    O_cf, O_dl = col("TRUCK", opp, "ttc_net"), col("TRUCK", opp, "all_delay")
    b_cf = float(np.median(-(P_cf - O_cf) / np.median(O_cf) * 100)); b_dl = float(np.median(-(P_dl - O_dl) / np.median(O_dl) * 100))
    Pc = P_cf + (b_cf - true_cf) / 100 * np.median(O_cf); Pd = P_dl + (b_dl - true_dl) / 100 * np.median(O_dl)
    r = np.random.default_rng(seed); k = k_cf = k_dl = 0
    lo_q = (100 - level) / 2
    for _ in range(studies):
        s = r.integers(0, n, m); bi = r.integers(0, m, (B, m))
        dc = -(Pc[s] - O_cf[s]) / np.median(O_cf[s]) * 100; dd = -(Pd[s] - O_dl[s]) / np.median(O_dl[s]) * 100
        a = (np.median(dc) < thr) or (np.percentile(np.median(dc[bi], axis=1), lo_q) <= 0)
        c = np.percentile(np.median(dd[bi], axis=1), lo_q) <= -margin
        k_cf += a; k_dl += c; k += (a or c)
    return k / studies, k_cf / studies, k_dl / studies
print("\nRule: KILL if cf point < 10 or cf lower bound <= 0 or delay lower bound <= -2 (97.5 % two-sided), pooled arm vs a rule with 3E-C_TRUCK's seed noise")
print("true cf edge | true delay | seeds | P(KILL) | by cf | by delay")
for m in (240, 160, 120):
    for e in (0.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0):
        k = oc("3E-C_TRUCK", e, 0.0, m, studies=2500, B=800)
        print("%5.1f | %+.1f | %3d | %.3f | %.3f | %.3f" % (e, 0.0, m, *k))
print("\ndelay non-inferiority alone (margin 2 %, 97.5 % two-sided), by opponent noise; true delay difference (negative = v3w worse)")
for opp in ("3E-C_TRUCK", "os0_10_10", "p333"):
    for m in (240, 120):
        print(opp, m, " ".join("%+.1f:%.3f" % (d, oc(opp, 30.0, d, m, studies=2000, B=600)[2]) for d in (0.0, -0.5, -1.0, -1.5, -2.0, -3.0)))
print("\nselection: SD of the search loss term (close-following % change vs p333, median paired) for 3E-C_TRUCK, by seed count")
A, Rf = col("TRUCK", "3E-C_TRUCK", "ttc_net"), col("TRUCK", "p333", "ttc_net")
Ad, Rd = col("TRUCK", "3E-C_TRUCK", "all_delay"), col("TRUCK", "p333", "all_delay")
r = np.random.default_rng(20261113)
for m in (40, 80, 120, 160, 240):
    v, w = [], []
    for _ in range(4000):
        s = r.integers(0, n, m)
        v.append(100 * np.median(A[s] - Rf[s]) / np.median(Rf[s])); w.append(100 * np.median(Ad[s] - Rd[s]) / np.median(Rd[s]))
    print(m, "loss term mean %.2f SD %.2f | delay %% mean %.2f SD %.2f | share with delay > +2 %%: %.3f" % (np.mean(v), np.std(v), np.mean(w), np.std(w), np.mean(np.array(w) > 2.0)))
