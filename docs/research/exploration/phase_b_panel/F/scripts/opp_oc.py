"""EXPLORATORY (S6 rows already read for a verdict). Operating characteristic of the draft's per-learner rules, by resampling stored seeds. No traffic simulation."""
import numpy as np, sys
B = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/"
Z = np.load(B + "panel/F/opp_t0.npz"); K = list(Z["keys"]); n = len(Z["seeds"])
S6 = np.load(B + "s6/s6_safety.npz"); K6 = list(S6["keys"])
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda c, a, k: Z[f"{c}|{a}"][:, K.index(k)]
c6 = lambda c, a, k: S6[f"{c}|{a}"][:, K6.index(k)]
STUD, NB = 1500, 500
def oc(Pl, O, true, m, lev=97.5, need=4, pt_min=None, lb_min=0.0, seed=20261112):
    """Pl: 5 x n learner values, O: n opponent values; lower is better. Each learner is shifted so that its stored statistic equals `true`
    (true = None: no shift, the stored effect). Pass = at least `need` learners with the lower bound above lb_min (and the point at least pt_min)."""
    r = np.random.default_rng(seed)
    medO = np.median(O)
    Ps = []
    for p in Pl:
        base = float(np.median(-(p - O) / medO * 100.0))
        Ps.append(p if true is None else p + (base - true) / 100.0 * medO)
    Ps = np.array(Ps)
    npass = 0; arm_pass = 0
    for _ in range(STUD):
        s = r.integers(0, n, m)
        o = O[s]; mo = np.median(o)
        bi = r.integers(0, m, (NB, m))
        ok = 0
        for p in Ps:
            d = -(p[s] - o) / mo * 100.0
            lo = np.percentile(np.median(d[bi], axis=1), (100 - lev) / 2)
            ok += (lo > lb_min) and (pt_min is None or np.median(d) >= pt_min)
        npass += ok >= need
        d = -(Ps[:, s].mean(axis=0) - o) / mo * 100.0
        lo = np.percentile(np.median(d[bi], axis=1), (100 - lev) / 2)
        arm_pass += (lo > lb_min) and (pt_min is None or np.median(d) >= pt_min)
    return npass / STUD, arm_pass / STUD
cf = lambda c, a: col(c, a, "ttc_net")
dl = lambda c, a: col(c, a, "all_delay")
offm = lambda c, a: sum(c6(c, a, f"rt_{r}") for r in ("1", "2", "3", "4", "5"))
nolc = lambda c, a: col(c, a, "m_ttc3_all") - col(c, a, "m_ttc3_lc")
PL = lambda fn, c: np.array([fn(c, l) for l in L])
which = sys.argv[1]
if which == "cf":
    print("close-following rule: at least 4 of 5 learners with the 97.5 %% lower bound > 0 and the point >= 10 %%; %d studies, %d resamples" % (STUD, NB))
    print("cell | noise of opponent | seeds | true edge %% | P(pass, 4 of 5 learners) | P(pass, pooled arm) | same without the 10 %% point rule: learners, arm")
    for c, o, ms in (("TRUCK", "3E-C_TRUCK", (240,)), ("S", "3E-C_TRUCK", (240, 480)), ("S", "p333", (240,))):
        for m in ms:
            for true in (0.0, 5.0, 10.0, 12.0, 15.0, 20.0, 30.0):
                a = oc(PL(cf, c), cf(c, o), true, m, pt_min=10.0); b = oc(PL(cf, c), cf(c, o), true, m)
                print("%-5s | %-10s | %3d | %4.1f | %.3f | %.3f | %.3f, %.3f" % (c, o, m, true, a[0], a[1], b[0], b[1]), flush=True)
elif which == "delay":
    print("delay non-inferiority: at least 4 of 5 learners with the 97.5 %% lower bound above -margin; true = the learners' delay effect (negative = worse)")
    print("cell | opponent | seeds | margin | true %% | P(pass, learners) | P(pass, arm)")
    for c, o in (("TRUCK", "p333"), ("TRUCK", "os0_10_10"), ("TRUCK", "3E-C_TRUCK"), ("S", "p333"), ("S", "os0_10_10")):
        for margin in (2.0,):
            for true in (0.0, -1.0, -2.0, -3.0):
                a = oc(PL(dl, c), dl(c, o), true, 240, lb_min=-margin)
                print("%-5s | %-10s | 240 | %.0f | %+.1f | %.3f | %.3f" % (c, o, margin, true, a[0], a[1]), flush=True)
    for c, o in (("TRUCK", "p333"), ("TRUCK", "os0_10_10"), ("S", "p333"), ("S", "os0_10_10")):
        a = oc(PL(dl, c), dl(c, o), None, 240, lb_min=-2.0)
        print("%-5s | %-10s | 240 | 2 | stored effect | %.3f | %.3f" % (c, o, a[0], a[1]), flush=True)
else:
    print("location clauses at the stored effect (no shift) and at a true 0: at least 4 of 5 learners with the 97.5 % lower bound > 0, 240 seeds")
    for c, o in (("TRUCK", "3E-C_TRUCK"), ("S", "3E-C_TRUCK")):
        for tag, fn in (("outside both merge sections", offm), ("outside lane-change windows", nolc), ("deciding count", cf)):
            a = oc(PL(fn, c), fn(c, o), None, 240); b = oc(PL(fn, c), fn(c, o), 0.0, 240)
            print("%-5s vs %-10s %-28s stored effect: learners %.3f, arm %.3f | true 0: learners %.3f, arm %.3f" % (c, o, tag, a[0], a[1], b[0], b[1]), flush=True)
