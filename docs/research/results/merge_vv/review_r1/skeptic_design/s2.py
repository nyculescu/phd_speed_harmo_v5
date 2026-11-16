import numpy as np
Z = np.load("cols.npz"); arms = list(Z["arms"]); A = {a: i for i, a in enumerate(arms)}
V = [a for a in arms if a.split("|")[1][0] == "w"]
def c(a, k): return Z[k][A[a]]
rng = np.random.default_rng(1); n = Z["ttc_net"].shape[1]; B = 4000
IDX = rng.integers(0, n, (B, n))
def edge(opp, f, idx=IDX):
    O = f(opp); m = np.median(O)
    D = [-(f(w) - O) / m * 100 for w in V]
    pt = np.mean([np.median(d) for d in D]); b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    return pt, b
def show(lbl, pt, b):
    print("%-40s %+.2f SE %.2f  97.5%%[%+.2f,%+.2f] 98.75%%[%+.2f,%+.2f]" % (lbl, pt, b.std(), *np.percentile(b, [1.25, 98.75]), *np.percentile(b, [0.625, 99.375])))
K = lambda k: (lambda a: c(a, k))
for opp in ["E30|lr400_16_1", "E30|grid_lr400_13_1"]:
    print("==", opp)
    for k in ["ttc_net", "ttc_half", "away", "m1", "m2"]:
        show(k, *edge(opp, K(k)))
    # paired difference ttc_half edge minus ttc_net edge
    p1, b1 = edge(opp, K("ttc_net")); p2, b2 = edge(opp, K("ttc_half"))
    print("  ttc_half-ttc_net edge diff %+.2f SE %.2f" % (p2 - p1, (b2 - b1).std()))
    es = lambda a: c(a, "es") + c(a, "es2")
    show("end_stop+end_stop2", *edge(opp, es))
    show("periods taper+hold", *edge(opp, K("p_th"))); show("after", *edge(opp, K("p_after")))
    print("  medians opp: th %.1f after %.1f; v3w mean of medians th %.1f after %.1f" % (np.median(c(opp,"p_th")), np.median(c(opp,"p_after")), np.mean([np.median(c(w,"p_th")) for w in V]), np.mean([np.median(c(w,"p_after")) for w in V])))
    # edge without lane-change samples
    show("ttc_net minus lc", *edge(opp, lambda a: c(a, "ttc_net") - c(a, "lc")))
for a in arms:
    print("%-22s med ttc %.1f m1 %.1f m2 %.1f away %.1f es %.1f es2 %.1f es+es2 %.1f lcshare %.3f merge share %.3f" % (a, *(np.median(c(a, k)) for k in ["ttc_net","m1","m2","away","es","es2"]), np.median(c(a,"es")+c(a,"es2")), c(a,"lc").sum()/c(a,"all3").sum(), (c(a,"m1")+c(a,"m2")).sum()/c(a,"ttc_net").sum()))
print("ttc_net==m1+m2+away+jn:", np.array_equal(Z["ttc_net"], Z["m1"]+Z["m2"]+Z["away"]+Z["jn"]))
# merge scaling model (D1): merges multiplied by k in both arms, away and junction unchanged
for opp in ["E30|lr400_16_1", "E30|grid_lr400_13_1"]:
    for k in [1.0, 0.34, 0.2, 0.1, 0.02]:
        f = lambda a: k * (c(a, "m1") + c(a, "m2")) + c(a, "away") + c(a, "jn")
        pt, b = edge(opp, f); lo = np.percentile(b, 1.25); hi = np.percentile(b, 98.75)
        print("model %s k=%.2f edge %+.2f SE %.2f 97.5%% [%+.2f,%+.2f]" % (opp, k, pt, b.std(), lo, hi))
