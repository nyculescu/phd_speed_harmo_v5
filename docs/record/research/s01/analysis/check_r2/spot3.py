"""Section 3.2 road split and 3.5 E30 split: means of paired v3w - nc differences, X1 and X2."""
import json
import numpy as np
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_test.jsonl"
K = ["ttc3_r_4a", "ttc3_r_3", "ttc3_r_ramp2", "ttc_net", "E30", "out_E30", "passed", "m_peak_car", "m_peak_alks", "m_peak_truck", "dist_step"]
V = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
R = {}
for line in open(D):
    r = json.loads(line)
    c, a = r["name"].split("|")
    if a in V or a == "nc":
        R.setdefault((c, a), {})[r["seed"]] = {k: r.get(k) for k in K}
def val(x, k):
    if k == "rest":
        return x["ttc_net"] - sum(float(x[k] or 0) for k in ("ttc3_r_4a", "ttc3_r_3", "ttc3_r_ramp2"))
    if k == "ev40":
        return sum(sum(x[f"m_peak_{c}"][2:]) for c in ("car", "alks", "truck"))
    if k == "ev40_served":
        return val(x, "ev40") / x["passed"]
    return float(x[k] or 0)
def armv(c, a, k):
    names = V if a == "v3w" else [a]
    seeds = sorted(R[(c, names[0])])
    return np.array([np.mean([val(R[(c, n)][s], k) for n in names]) for s in seeds])
def bmean(d):
    rng = np.random.default_rng(20261104)
    bs = d[rng.integers(0, len(d), (20000, len(d)))].mean(axis=1)
    return d.mean(), *np.percentile(bs, (2.5, 97.5))
def bmed(d):
    rng = np.random.default_rng(20261104)
    bs = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    return np.median(d), *np.percentile(bs, (2.5, 97.5))
for c in ("X1", "X2"):
    for k in ("ttc3_r_4a", "ttc3_r_3", "ttc3_r_ramp2", "rest", "ttc_net", "E30", "out_E30"):
        d = armv(c, "v3w", k) - armv(c, "nc", k)
        print(c, k, "mean diff %.1f [%.1f, %.1f]" % bmean(d))
d1 = armv("X1", "v3w", "ttc_net") - armv("X1", "nc", "ttc_net"); d2 = armv("X2", "v3w", "ttc_net") - armv("X2", "nc", "ttc_net")
print("X1-X2 excess %.1f [%.1f, %.1f]" % bmean(d1 - d2))
e1 = armv("X1", "v3w", "E30") - armv("X1", "nc", "E30"); e2 = armv("X2", "v3w", "E30") - armv("X2", "nc", "E30")
print("X1-X2 E30 part %.1f [%.1f, %.1f]" % bmean(e1 - e2))
p = armv("X1", "v3w", "ev40_served"); o = armv("X1", "nc", "ev40_served")
d = (p - o) / np.median(o) * 100
print("ev40 per served X1 %.1f [%.1f, %.1f]" % bmed(d))
