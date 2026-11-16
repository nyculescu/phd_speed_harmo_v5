import json, numpy as np
D = json.load(open(__file__.rsplit("/", 1)[0] + "/rows2.json"))
V3 = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500", "lr400_16_1", "grid_lr400_13_1", "p333", "nc"]
A = {a: np.array([D["E30|" + a][s] for s in sorted(D["E30|" + a])], float) for a in [k[4:] for k in D]}
print("wall quantiles (10/50/90) per arm, slow three vs same-class rule:")
for a in ("lr400_16_1", "grid_lr400_13_1", "lr400_13_2", "a4400_10_1", "lr1000_10_1", "lr1000_16_2"):
    print(" ", a, np.percentile(A[a][:, 0], [10, 50, 90]).round(0))
w9 = np.mean([A[a][:, 0].mean() for a in V3]); print("9-arm mean wall %.1f s -> %.0f runs/h on 30 workers; 8704 runs %.1f h" % (w9, 30 * 3600 / w9, 8704 * w9 / 30 / 3600))
# Sum gate: what fall on 3a is needed to pass 80 % on end_stop + end_stop2 if 4a falls by f4?
# hypothetical x600 = (1-f3)*e1 + (1-f4)*e2 per seed; statistic = -median(x600 - x300) / median(x300)
print("share of the sum that is 4a (median of per-seed e2/(e1+e2)), and sum-gate fall if 3a is unchanged and 4a falls 100 % / 91 % (C1 nc) / 99 % (C1 p333):")
for a in V3:
    e1, e2 = A[a][:, 1], A[a][:, 2]; x3 = e1 + e2
    def fall(f3, f4):
        return -np.median(((1 - f3) * e1 + (1 - f4) * e2) - x3) / np.median(x3) * 100
    need = {}
    for f4 in (1.0, 0.99, 0.91):
        f3s = np.linspace(0, 1, 101); ok = [f for f in f3s if fall(f, f4) >= 80.0]
        need[f4] = round(float(ok[0]), 2) if ok else None
    print(f"  {a}: 4a share {np.median(e2 / np.maximum(x3, 1)):.2f}; 3a unchanged -> fall {fall(0,1):.0f} / {fall(0,.91):.0f} / {fall(0,.99):.0f} %; min 3a fall to pass with 4a at 100/99/91 %: {need}")
# C-D5 point, ttc_net vs ttc_half
V3W = V3[:5]
S = {a: sorted(D["E30|" + a]) for a in V3}
for opp in ("lr400_16_1", "grid_lr400_13_1", "p333"):
    for col, key in ((3, "ttc_net"), (4, "ttc_half")):
        R = A[opp][:, col]
        e = [float(np.median(-(A[l][:, col] - R) / np.median(R) * 100)) for l in V3W]
        print(f"C-D5 point v3w vs {opp} on {key}: {np.mean(e):.2f}")
