"""Section 4: T1, T2 from the protocol text, beside readings, counters, splits, collisions, blind spots."""
import json
import sys

import numpy as np

sys.path.insert(0, sys.path[0])
from lib import OUT, P95, B2, B2_WIDE, arm, coll, f, g, med, pmed, stat, load

Q = 5300.0
T = load(OUT + "/test/test.jsonl")
print("arms", len(T), "seeds per arm", {len(v) for v in T.values()}, "seed range", min(min(v) for v in T.values()), max(max(v) for v in T.values()))
O = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v3/opponents.json"))
C = ("X1", "X2")
RULES = list(O["ctrl"])


def a(c, n):
    return T[(f"{c}|{n}", Q)]


def W(c):
    return arm(T, [f"{c}|w{i}" for i in range(5)], Q)


def D(c):
    return arm(T, [f"{c}|d{i}" for i in range(5)], Q)


print("\n== T1 (v3w arm vs baseline-v3 arm)")
for c in C:
    for lab, pct in (("pct 1.25-98.75 (97.5% CI)", B2), ("pct 0.625-99.375 (98.75% CI)", B2_WIDE), ("95%", P95)):
        d, t = stat(W(c), D(c), "all_delay", pct=pct), stat(W(c), D(c), "ttc_net", pct=pct)
        print(c, lab, "delay", f(d, 2), "ttc", f(t, 2), "better", d[1] > 0 and t[0] >= -10)

print("\n== counting opponents (delay within 2 % of p333, point estimate)")
counts = {}
for c in C:
    opp = list(dict.fromkeys(["p333", *O["cells"][c]["forms"].values()]))
    print(c, "opponents", opp)
    for r in opp + ["copy"]:
        e = stat(a(c, r), a(c, "p333"), "all_delay")[0]
        print("  ", r, "delay vs p333", round(e, 2), "counts" if e >= -2 else "out")
    counts[c] = [r for r in opp if stat(a(c, r), a(c, "p333"), "all_delay")[0] >= -2.0]
    # every rule in the test, to see whether any non-opponent would have counted
    others = {r: round(stat(a(c, r), a(c, "p333"), "all_delay")[0], 2) for r in RULES if r not in opp}
    print("  not opponents:", others)
print("counts", counts)


def tuned_one(P, c, pct):
    """Protocol text: against every counting opponent, TTC >= 10 % better with CI lo > 0, per-run lower >= 20; delay >= -2;
    flow >= -0.5; b3_step >= -5; moving full-emergency at most 5 % or 5 per run more; collisions <= opp + 1. Against p333:
    delay >= -5 and flow >= -1."""
    why = {}
    for r in counts[c]:
        Oo = a(c, r)
        t = stat(P, Oo, "ttc_net", pct=pct)
        fails = []
        if t[0] < 10: fails.append("margin %.1f" % t[0])
        if not t[1] > 0: fails.append("ci lo %.1f" % t[1])
        pr = pmed(Oo, P, "ttc_net")
        if pr < 20: fails.append("per run %.1f" % pr)
        dl = stat(P, Oo, "all_delay", pct=pct)[0]
        if dl < -2: fails.append("delay %.2f" % dl)
        fl = stat(P, Oo, "passed", +1, pct=pct)[0]
        if fl < -0.5: fails.append("flow %.2f" % fl)
        br = stat(P, Oo, "b3_step", pct=pct)[0]
        if br < -5: fails.append("brake %.2f" % br)
        ev_pct = stat(P, Oo, "alks_full_moving", pct=pct)[0]
        ev_run = pmed(P, Oo, "alks_full_moving")
        if not (ev_pct >= -5 or ev_run <= 5): fails.append("events")
        if coll(P) > coll(Oo) + 1: fails.append("coll %g>%g+1" % (coll(P), coll(Oo)))
        if fails: why[r] = fails
    p = a(c, "p333")
    d5, f1 = stat(P, p, "all_delay", pct=pct)[0], stat(P, p, "passed", +1, pct=pct)[0]
    if d5 < -5 or f1 < -1: why["p333_anchor"] = ["delay %.2f" % d5, "flow %.2f" % f1]
    return why


print("\n== T2, per learner, at percentiles 1.25-98.75 and 0.625-99.375")
for c in C:
    for pfx in ("w", "d", "f"):
        for lab, pct in (("B2", B2), ("wide", B2_WIDE)):
            res = [tuned_one(a(c, f"{pfx}{i}"), c, pct) for i in range(5)]
            print(c, pfx, lab, "passed", sum(not r for r in res), "of 5", res)

print("\n== detail per learner vs counting opponents (point estimates; CI at B2)")
for c in C:
    for pfx in ("w", "d"):
        for i in range(5):
            P = a(c, f"{pfx}{i}")
            parts = []
            for r in counts[c]:
                t = stat(P, a(c, r), "ttc_net")
                parts.append("%s ttc %s delay %.2f flow %.2f brake %.2f perrun %.0f coll %g/%g" % (r, f(t), stat(P, a(c, r), "all_delay")[0], stat(P, a(c, r), "passed", 1)[0], stat(P, a(c, r), "b3_step")[0], pmed(a(c, r), P, "ttc_net"), coll(P), coll(a(c, r))))
            print(c, f"{pfx}{i}", " | ".join(parts))

print("\n== beside readings (v3w learners)")
for c in C:
    p, nc = a(c, "p333"), a(c, "nc")
    pol = [a(c, f"w{i}") for i in range(5)]
    # replication: clears p333 at margin 30 with the same limits
    repl = 0
    for P in pol:
        t = stat(P, p, "ttc_net")
        ok = t[0] >= 30 and t[1] > 0 and pmed(p, P, "ttc_net") >= 20 and stat(P, p, "all_delay")[0] >= -2 and stat(P, p, "passed", 1)[0] >= -0.5 \
            and stat(P, p, "b3_step")[0] >= -5 and (stat(P, p, "alks_full_moving")[0] >= -5 or pmed(P, p, "alks_full_moving") <= 5) and coll(P) <= coll(p) + 1
        repl += ok
    dop_name = min((O["cells"][c]["delay_opponent"], "p333"), key=lambda r: med(a(c, r), "all_delay"))
    dop = a(c, dop_name)
    dw = 0
    for P in pol:
        d = stat(P, dop, "all_delay")
        ok = d[0] >= 5 and d[1] > 0 and stat(P, dop, "passed", 1)[0] >= -0.5 and stat(P, dop, "ttc_net")[0] >= -10 and stat(P, dop, "b3_step")[0] >= -10 and coll(P) <= coll(dop) + 1
        dw += ok
    sev = [all(pmed(P, a(c, r), "sev3") <= 0 for r in counts[c]) for P in pol]
    sev_detail = [{r: pmed(P, a(c, r), "sev3") for r in counts[c]} for P in pol]
    worse_nc = [stat(P, nc, "ttc_net") for P in pol]
    ncmore = sorted(stat(nc, P, "all_delay", +1)[0] for P in pol)
    strongest = min(counts[c], key=lambda r: med(a(c, r), "ttc_net"))
    gains = [stat(P, a(c, strongest), "ttc_net") for P in pol]
    print(c, "replication", repl, "| delay opponent", dop_name, "delay wins", dw, "| severe ok per learner", sev, sev_detail)
    print(c, "TTC vs nc per learner (97.5 % CI):", [f(x) for x in worse_nc], "clearly worse:", sum(x[2] < 0 for x in worse_nc), "clearly better:", sum(x[1] > 0 for x in worse_nc))
    print(c, "nc extra delay per learner (sign +1, ref = policy median):", [round(x, 2) for x in ncmore], "median", round(ncmore[2], 2))
    print(c, "strongest", strongest, "gains", [f(x) for x in gains], "range %.1f-%.1f" % (min(x[0] for x in gains), max(x[0] for x in gains)))
    Wc = W(c)
    print(c, "arm: v3w vs nc TTC 95%", f(stat(Wc, nc, "ttc_net", pct=P95)), "delay 95%", f(stat(Wc, nc, "all_delay", pct=P95)), "nc extra delay vs arm", round(stat(nc, Wc, "all_delay", +1, pct=P95)[0], 2))
    for r in ("os1_15_10", "p333", O["cells"][c]["delay_opponent"], dop_name):
        print(c, "arm delay vs", r, "95%", f(stat(Wc, a(c, r), "all_delay", pct=P95)))

print("\n== counters (medians; arm = per-seed mean of 5 learners)")
K = ("all_delay", "passed", "ttc_net", "ttc3", "sev3", "b3_step", "b7_step", "alks_full_moving", "brake_net", "ttc_half")
for c in C:
    arms = {"v3w": W(c), "baseline-v3": D(c), "p333": a(c, "p333"), "os1_15_10": a(c, "os1_15_10"), "nc": a(c, "nc")}
    for n, X in arms.items():
        print(c, n, {k: round(med(X, k), 2) for k in K}, "coll", round(coll(X), 2))
    print(c, "b7_step medians every arm:", {n.split("|")[1]: round(med(A_, "b7_step"), 2) for (n, q), A_ in T.items() if n.startswith(c + "|")})
    print(c, "alks_full_moving max over all rows:", max(g(r, "alks_full_moving") for (n, q), A_ in T.items() if n.startswith(c + "|") for r in A_.values()),
          "median per arm max:", max(med(A_, "alks_full_moving") for (n, q), A_ in T.items() if n.startswith(c + "|")))
    print(c, "collisions per arm:", {n.split("|")[1]: coll(A_) for (n, q), A_ in T.items() if n.startswith(c + "|")})
    print(c, "v3w arm coll", coll(W(c)), "d arm coll", coll(D(c)))

print("\n== splits")
SPL = ("r_3", "r_4a", "r_ramp2", "r_rest", "s_lo", "s_mid", "s_hi", "p_before", "p_taper", "p_hold", "p_after", "p_rest")
for c, rule in (("X1", "p333"), ("X2", "os1_15_10")):
    for n, X in (("v3w", W(c)), (rule, a(c, rule)), ("nc", a(c, "nc"))):
        print(c, n, {s: round(med(X, "ttc3_" + s), 1) for s in SPL})
# totals: per row, ttc3 == ttc_net, and each split family sums to ttc3
bad = {"ttc3!=ttc_net": 0, "road": 0, "speed": 0, "period": 0}
mx = {"road": 0, "speed": 0, "period": 0}
nrow = 0
for (n, q), A_ in T.items():
    for r in A_.values():
        nrow += 1
        t3, tn = g(r, "ttc3"), g(r, "ttc_net")
        bad["ttc3!=ttc_net"] += abs(t3 - tn) > 1e-6
        for fam, keys in (("road", SPL[0:4]), ("speed", SPL[4:7]), ("period", SPL[7:12])):
            s = sum(g(r, "ttc3_" + k) for k in keys)
            bad[fam] += abs(s - t3) > 1e-6
            mx[fam] = max(mx[fam], abs(s - t3))
print("rows", nrow, "mismatches", bad, "max abs diff", mx)
# arms: ttc3 median vs ttc_net median
print("arms where median ttc3 != median ttc_net:", [n for (n, q), A_ in T.items() if abs(med(A_, "ttc3") - med(A_, "ttc_net")) > 1e-9])

print("\n== final policies f_i vs chosen d_i rows")
diffs = 0
for c in C:
    for i in range(5):
        F, Dd = a(c, f"f{i}"), a(c, f"d{i}")
        for s in Dd:
            ks = set(F[s]) | set(Dd[s])
            diffs += sum(g(F[s], k) != g(Dd[s], k) for k in ks)
print("numeric key differences f vs d:", diffs)

print("\n== blind spots, every test arm and the two policy arms")
out = []
allarms = dict(T)
for c in C:
    allarms[(c + "|v3w arm", Q)] = W(c)
    allarms[(c + "|d arm", Q)] = D(c)
worst_b, worst_t = 0, 0
for (n, q), A_ in allarms.items():
    b, s, t, h = med(A_, "brake_net"), med(A_, "b3_step"), med(A_, "ttc_net"), med(A_, "ttc_half")
    if s >= 50: worst_b = max(worst_b, abs(b / s - 1))
    if h >= 50: worst_t = max(worst_t, abs(t / h - 1))
    if (s >= 50 and abs(b / s - 1) > 0.05) or (h >= 50 and abs(t / h - 1) > 0.05):
        out.append((n, q, round(b / s, 3), round(t / h, 3)))
print("over 5 %:", out, "largest deviations: braking %.4f TTC %.4f" % (worst_b, worst_t))
