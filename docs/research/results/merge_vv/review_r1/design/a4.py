import pickle, numpy as np, sys
D = sys.argv[1]
rows = pickle.load(open(D + "/rows.pkl", "rb")); seeds = sorted({s for a, s in rows})
V3W = ["E30|w0u250", "E30|w1u500", "E30|w2u250", "E30|w3u500", "E30|w4u500"]
col = lambda a, k: np.array([rows[(a, s)].get(k, 0.0) for s in seeds], float)
def edge(f, opp, B=4000):
    P = np.array([f(w) for w in V3W]); R = f(opp)
    d = -(P - R) / max(np.median(R), 1e-9) * 100
    idx = np.random.default_rng(20261108).integers(0, 480, (B, 480))
    b = np.mean([np.median(x[idx], axis=1) for x in d], axis=0)
    return np.mean(np.median(d, axis=1)), *np.percentile(b, (1.25, 98.75)), np.median(R), np.mean([np.median(p) for p in P])
for opp in ("E30|lr400_16_1", "E30|grid_lr400_13_1"):
    print("==", opp, "(edge %, 97.5 % interval, opponent median, v3w mean of medians)")
    for lbl, f in (("speed <5 m/s", lambda a: col(a, "ttc3_s_lo")), ("5-10 m/s", lambda a: col(a, "ttc3_s_mid")), (">=10 m/s", lambda a: col(a, "ttc3_s_hi")),
                   ("before", lambda a: col(a, "ttc3_p_before")), ("taper+hold", lambda a: col(a, "ttc3_p_taper") + col(a, "ttc3_p_hold")), ("after+rest", lambda a: col(a, "ttc3_p_after") + col(a, "ttc3_p_rest")),
                   ("end_stop+end_stop2 (veh-s)", lambda a: col(a, "end_stop") + col(a, "end_stop2")), ("end_stop merge1", lambda a: col(a, "end_stop")), ("all_delay", lambda a: col(a, "all_delay"))):
        print(f"  {lbl:28s}", " ".join(f"{x:+9.2f}" for x in edge(f, opp)))
# no-effect behaviour of the stop gate: two disjoint halves of the same arm (no length change) -> ratio of medians
rng = np.random.default_rng(3)
for a in ("E30|lr400_16_1", "E30|w1u500", "E30|nc"):
    s = col(a, "end_stop") + col(a, "end_stop2")
    cuts = []
    for _ in range(2000):
        p = rng.permutation(480); cuts.append(1 - np.median(s[p[:240]]) / np.median(s[p[240:]]))
    print(a, "unpaired null of the cut in median stops between two random halves (n=240 each): 2.5/50/97.5 %:", np.percentile(cuts, [2.5, 50, 97.5]).round(3))
# P0 context
nc, p3 = col("E30|nc", "all_delay"), col("E30|p333", "all_delay")
print("p333 vs nc delay, median paired % of median nc:", round(float(np.median((nc - p3) / np.median(nc) * 100)), 2))
